/**
 * Copyright 2012 Michael N. Gagnon
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 * ==== upstream_overload ====
 *
 * A basic load-balancing module for nginx.
 *
 * Provides similar functionality to the upstream_fair 3rd-party module (see
 * http://nginx.localdomain.pl/wiki/UpstreamFair ) with weight_mode=peak
 * and all servers have weight=1.
 *
 * upstream_overload will only distribute requests to idle backend servers. If
 * there are no idle servers client will get a 502 error. When the number of idle
 * servers drops below num_spare_backends then upstream_overload will send an alert
 * message to a named pipe that identifies the backend server that has been busy
 * for the longest time. The idea is that a daemon will listen on this pipe and then
 * somehow abort the request being processed by the backend server.
 *
 * upstream_overload is designed to be scalable w.r.t. (a) the number of nginx
 * worker processes and (b) the number of backend worker processes. Makes most
 * load-balancing operations in O(c) time, as opposed to upstream_fair, which
 * has most load-balancing decisions of O(N), where N is the number of backend
 * servers.
 *
 * ==== maturity ====
 *
 * Experimental development. Testing using nginx-1.0.12
 *
 */

#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>

#define DEFAULT_NUM_SPARE_BACKENDS 1

typedef struct {
    ngx_uint_t                      num_spare_backends;
} ngx_http_upstream_overload_conf_t;

typedef struct {
    struct sockaddr                *sockaddr;
    socklen_t                       socklen;
    ngx_str_t                       name;
} ngx_http_upstream_overload_peer_t;

typedef struct {
    ngx_uint_t                          num_peers;
    ngx_http_upstream_overload_peer_t * peer;
} ngx_http_upstream_overload_peers_t;

static void * ngx_http_upstream_overload_create_loc_conf(ngx_conf_t * cf);
static char * ngx_http_upstream_overload_merge_loc_conf(ngx_conf_t * cf, void * parent, void * child);
static char * ngx_http_upstream_overload(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
ngx_int_t ngx_http_upstream_init_overload(ngx_conf_t *cf, ngx_http_upstream_srv_conf_t *us);
static ngx_int_t ngx_http_upstream_init_overload_peer(ngx_http_request_t *r, ngx_http_upstream_srv_conf_t *us);
static ngx_int_t ngx_http_upstream_get_overload_peer(ngx_peer_connection_t *pc, void *data);
static void ngx_http_upstream_free_overload_peer(ngx_peer_connection_t *pc, void *data, ngx_uint_t state);

static ngx_command_t ngx_http_upstream_overload_commands[] = {
    { ngx_string("overload"),
      NGX_HTTP_UPS_CONF|NGX_CONF_NOARGS,
      ngx_http_upstream_overload,
      0,
      0,
      NULL },

    { ngx_string("num_spare_backends"),
      NGX_HTTP_UPS_CONF|NGX_CONF_TAKE1,
      ngx_conf_set_num_slot,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_upstream_overload_conf_t, num_spare_backends),
      NULL },

      ngx_null_command
};

static ngx_http_module_t ngx_http_upstream_overload_module_ctx = {
    NULL,                                  /* preconfiguration */
    NULL,                                  /* postconfiguration */

    NULL,                                  /* create main configuration */
    NULL,                                  /* init main configuration */

    NULL,                                  /* create server configuration */
    NULL,                                  /* merge server configuration */

    ngx_http_upstream_overload_create_loc_conf,   /* create location configuration */
    ngx_http_upstream_overload_merge_loc_conf     /* merge location configuration */
};

ngx_module_t ngx_http_upstream_overload_module = {
    NGX_MODULE_V1,
    &ngx_http_upstream_overload_module_ctx, /* module context */
    ngx_http_upstream_overload_commands,   /* module directives */
    NGX_HTTP_MODULE,               /* module type */
    NULL,                          /* init master */
    NULL,                          /* init module */
    NULL,                          /* init process */
    NULL,                          /* init thread */
    NULL,                          /* exit thread */
    NULL,                          /* exit process */
    NULL,                          /* exit master */
    NGX_MODULE_V1_PADDING
};

static void *
ngx_http_upstream_overload_create_loc_conf(ngx_conf_t * cf)
{
    ngx_http_upstream_overload_conf_t * conf;

    conf = ngx_pcalloc(cf->pool, sizeof(ngx_http_upstream_overload_conf_t));
    if (conf == NULL) {
        return NGX_CONF_ERROR;
    }
    conf->num_spare_backends = NGX_CONF_UNSET_UINT;
    return conf;
}

static char *
ngx_http_upstream_overload_merge_loc_conf(ngx_conf_t * cf, void * parent, void * child)
{
    ngx_http_upstream_overload_conf_t * prev = parent;
    ngx_http_upstream_overload_conf_t * conf = child;

    ngx_conf_merge_uint_value(conf->num_spare_backends, prev->num_spare_backends, DEFAULT_NUM_SPARE_BACKENDS);

    return NGX_CONF_OK;
}

static char *
ngx_http_upstream_overload(ngx_conf_t * cf, ngx_command_t * cmd, void * conf)
{
    ngx_http_upstream_srv_conf_t * uscf;

    uscf = ngx_http_conf_get_module_srv_conf(cf, ngx_http_upstream_module);

    uscf->peer.init_upstream = ngx_http_upstream_init_overload;

    uscf->flags = NGX_HTTP_UPSTREAM_CREATE;

    return NGX_CONF_OK;
}

// Called once during initialization of upstream_overload module
ngx_int_t
ngx_http_upstream_init_overload(ngx_conf_t *cf, ngx_http_upstream_srv_conf_t *us)
{
    ngx_uint_t                           i;
    ngx_http_upstream_server_t          *server;
    ngx_http_upstream_overload_peers_t  *peers;

    us->peer.init = ngx_http_upstream_init_overload_peer;

    if (!us->servers) {
        ngx_conf_log_error(NGX_LOG_EMERG, cf, 0,
            "There are no server directives within upstream block.");
        return NGX_ERROR;
    }

    server = us->servers->elts;

    for (i = 0; i < us->servers->nelts; i++) {
        if (server[i].naddrs > 1) {
            ngx_conf_log_error(NGX_LOG_EMERG, cf, 0,
                "server '%s' resolves to multiple addresses. Each server must resolve to exactly one address.",
                server[i].addrs[0].name);
            return NGX_ERROR;
        }
    }

    peers = ngx_pcalloc(cf->pool, sizeof(ngx_http_upstream_overload_peers_t));
    if (peers == NULL) {
        return NGX_ERROR;
    }

    peers->num_peers = us->servers->nelts;
    peers->peer = ngx_pcalloc(cf->pool, sizeof(ngx_http_upstream_overload_peer_t) * peers->num_peers);

    for (i = 0; i < us->servers->nelts; i++) {
        peers->peer[i].sockaddr = server[i].addrs[0].sockaddr;
        peers->peer[i].socklen = server[i].addrs[0].socklen;
        peers->peer[i].name = server[i].addrs[0].name;
    }

    us->peer.data = peers;

    return NGX_OK;
}

// called once per request to initialize the structures used for just this request
static ngx_int_t
ngx_http_upstream_init_overload_peer(ngx_http_request_t *r,
    ngx_http_upstream_srv_conf_t *us)
{
    r->upstream->peer.get = ngx_http_upstream_get_overload_peer;
    r->upstream->peer.free = ngx_http_upstream_free_overload_peer;
    r->upstream->peer.tries = 5;

    return NGX_OK;
}

// called by nginx to determine which backend should receive this request
static ngx_int_t
ngx_http_upstream_get_overload_peer(ngx_peer_connection_t *pc, void *data)
{
    return NGX_ERROR;
}

// called by nginx after a request completes or fails
static void
ngx_http_upstream_free_overload_peer(ngx_peer_connection_t *pc, void *data, ngx_uint_t state)
{
    pc->tries = 0;

}

