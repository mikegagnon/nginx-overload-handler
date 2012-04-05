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
 * ==== TODO ====
 *  - a bunch of things (see todos throughout code)
 *  - most important: use locking to allow safe shared memory
 *
 */

#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>

/**
 * Macro definition
 *****************************************************************************/

#define DEFAULT_NUM_SPARE_BACKENDS 3
#define DEFAULT_ALERT_PIPE_PATH ""
#define MAX_ALERT_PIPE_PATH_BYTES 256

#define NGX_PEER_INVALID ((ngx_uint_t) -1)

// Set to 1 for very fine grained debugging. If you turn FINE_DEBUG on, make
// sure to configure nginx with 'daemon off;'
#define FINE_DEBUG 1

// ddX invocations print to stdout and are useful for figuring how nginx calls
//      the various event handlers during development.
// the dd_logX macros are just aliases for the nginx ngx_log_debugX macros (which also
//      invoke the ddX macros). These are useful for acutally writing messages to logs
#if FINE_DEBUG == 1
    #define dd0(format) \
        printf ("[upstream_overload] " format "\n")
    #define dd1(format, a) \
        printf ("[upstream_overload] " format "\n", a)
    #define dd2(format, a, b) \
        printf ("[upstream_overload] " format "\n", a, b)
    #define dd3(format, a, b, c) \
        printf ("[upstream_overload] " format "\n", a, b, c)
    #define dd4(format, a, b, c, d) \
        printf ("[upstream_overload] " format "\n", a, b, c, d)
    #define dd5(format, a, b, c, d, e) \
        printf ("[upstream_overload] " format "\n", a, b, c, d, e)
    #define dd6(format, a, b, c, d, e, f) \
        printf ("[upstream_overload] " format "\n", a, b, c, d, e, f)
    #define dd7(format, a, b, c, d, e, f, g) \
        printf ("[upstream_overload] " format "\n", a, b, c, d, e, f, g)
    #define dd_list(list, name, peers) ngx_upstream_overload_print_list(list, name, peers)
#else
    #define dd0(format)
    #define dd1(format, a)
    #define dd2(format, a, b)
    #define dd3(format, a, b, c)
    #define dd4(format, a, b, c, d)
    #define dd5(format, a, b, c, d, e)
    #define dd6(format, a, b, c, d, e, f)
    #define dd7(format, a, b, c, d, e, f, g)
    #define dd_list(list, name, peers)
#endif

#define dd_log0(level, log, err, format)                                    \
    do {                                                                    \
        dd0(format);                                                        \
        ngx_log_debug0(level, log, err, "[upstream_overload] " format);     \
    } while (0)

#define dd_log1(level, log, err, format, a)                                 \
    do {                                                                    \
        dd1(format, a);                                                     \
        ngx_log_debug1(level, log, err, "[upstream_overload] " format, a);  \
    } while (0)

#define dd_log2(level, log, err, format, a, b)                                  \
    do {                                                                        \
        dd2(format, a, b);                                                      \
        ngx_log_debug2(level, log, err, "[upstream_overload] " format, a, b);   \
    } while (0)

#define dd_log3(level, log, err, format, a, b, c)                                   \
    do {                                                                            \
        dd3(format, a, b, c);                                                       \
        ngx_log_debug3(level, log, err, "[upstream_overload] " format, a, b, c);    \
    } while (0)

#define dd_error0(level, log, format)                               \
    do {                                                            \
        dd0("          [ERROR] " format);                           \
        ngx_log_error(level, log, "[upstream_overload] " format);   \
    } while (0)

#define dd_error1(level, log, format, a)                                \
    do {                                                                \
        dd1("          [ERROR] " format, a);                            \
        ngx_log_error(level, log, "[upstream_overload] " format, a);    \
    } while (0)

#define dd_error2(level, log, format, a, b)                             \
    do {                                                                \
        dd2("          [ERROR] " format, a, b);                         \
        ngx_log_error(level, log, "[upstream_overload] " format, a, b); \
    } while (0)

#define dd_conf_error0(level, cf, err, format)                                  \
    do {                                                                        \
        dd0("          [CONFIG ERROR] " format);                                \
        ngx_conf_log_error(level, cf, err, "[upstream_overload] " format);      \
    } while (0)

#define dd_conf_error1(level, cf, err, format, a)                               \
    do {                                                                        \
        dd1("          [CONFIG ERROR] " format, a);                             \
        ngx_conf_log_error(level, cf, err, "[upstream_overload] " format, a);   \
    } while (0)

/**
 * Struct definitions
 *****************************************************************************/

typedef struct {
    ngx_uint_t          num_spare_backends;
    char                alert_pipe_path[MAX_ALERT_PIPE_PATH_BYTES];
} ngx_http_upstream_overload_conf_t;


typedef struct ngx_http_upstream_overload_peer_s ngx_http_upstream_overload_peer_t;

// There is one of these structs for every backend server, i.e. "peer"
struct ngx_http_upstream_overload_peer_s {
    struct sockaddr                    *sockaddr;
    socklen_t                           socklen;
    ngx_str_t                           name;

    // busy == 0 if this peer is idle, busy != 0 if this peer is busy
    ngx_uint_t                          busy;

    // the index of this peer in the array
    ngx_uint_t                          index;

    // peer objects will be stored in an array, but peers can also be
    // linked together in doubly linked lists
    ngx_http_upstream_overload_peer_t  *prev;
    ngx_http_upstream_overload_peer_t  *next;
};

typedef struct {
    ngx_http_upstream_overload_peer_t * head;
    ngx_http_upstream_overload_peer_t * tail;
} ngx_peer_list_t;

// There is only one instance of this struct
typedef struct {
    ngx_uint_t                          num_peers;
    ngx_http_upstream_overload_peer_t * peer;

    ngx_peer_list_t                     busy_list;
    ngx_peer_list_t                     idle_list;
} ngx_http_upstream_overload_peers_t;

// Each incoming request gets an instance of one of these structs
typedef struct {
    ngx_http_upstream_overload_peers_t * peers;

    // The index of the peer that is handling this request
    ngx_uint_t                           peer_index;
} ngx_http_upstream_overload_request_data_t;

/**
 * Function declarations
 *****************************************************************************/

static void ngx_upstream_overload_print_peers(ngx_http_upstream_overload_peers_t * peers);
static void ngx_upstream_overload_print_list(ngx_peer_list_t * list, char * list_name, ngx_http_upstream_overload_peers_t * peers);
static ngx_uint_t ngx_peer_list_pop(ngx_peer_list_t * list,char * list_name, ngx_log_t * log);
static void ngx_peer_list_push(ngx_peer_list_t * list, char * list_name, ngx_http_upstream_overload_peer_t * peer, ngx_log_t * log);
static void ngx_peer_list_remove(ngx_peer_list_t * list, char * list_name, ngx_http_upstream_overload_peer_t * peer, ngx_log_t * log);
static char * ngx_http_upstream_overload(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
static char * ngx_http_upstream_overload_parse_num_spare_backends(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
static char * ngx_http_upstream_overload_parse_alert_pipe(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
ngx_int_t ngx_http_upstream_init_overload_once(ngx_conf_t *cf, ngx_http_upstream_srv_conf_t *us);
static ngx_int_t ngx_http_upstream_init_overload_peer(ngx_http_request_t *r, ngx_http_upstream_srv_conf_t *us);
static ngx_int_t ngx_http_upstream_get_overload_peer(ngx_peer_connection_t *pc, void *data);
static void ngx_http_upstream_free_overload_peer(ngx_peer_connection_t *pc, void *data, ngx_uint_t state);

/**
 * Struct instantiations
 *****************************************************************************/

// Creating a global configuration variable (overload_conf) is not the best
// way to setup nginx configurations. However, my efforts to do it "the
// nginix way" have timed out for now.
// TODO: do it the nginx way
static ngx_http_upstream_overload_conf_t overload_conf = {
    DEFAULT_NUM_SPARE_BACKENDS,
    DEFAULT_ALERT_PIPE_PATH
};

static ngx_command_t ngx_http_upstream_overload_commands[] = {
    { ngx_string("overload"),
      NGX_HTTP_UPS_CONF|NGX_CONF_NOARGS,
      ngx_http_upstream_overload,
      NGX_HTTP_SRV_CONF_OFFSET,
      0,
      NULL },

    { ngx_string("num_spare_backends"),
      NGX_HTTP_MAIN_CONF|NGX_CONF_TAKE1,
      ngx_http_upstream_overload_parse_num_spare_backends,
      0,
      0,
      NULL },

    { ngx_string("alert_pipe"),
      NGX_HTTP_MAIN_CONF|NGX_CONF_TAKE1,
      ngx_http_upstream_overload_parse_alert_pipe,
      0,
      0,
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

    NULL,                                  /* create location configuration */
    NULL                                   /* merge location configuration */
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

/**
 * Function definitions
 *****************************************************************************/

static void
ngx_upstream_overload_print_peers(ngx_http_upstream_overload_peers_t * peers)
{
    ngx_uint_t i;

    for (i = 0; i < peers->num_peers; i++) {
        printf("[upstream_overload] [peers] peer[%d] this=%p\n", i, &peers->peer[i]);
    }
}

static void
ngx_upstream_overload_print_list(ngx_peer_list_t * list, char * list_name,
    ngx_http_upstream_overload_peers_t * peers)
{
    ngx_http_upstream_overload_peer_t * peer = list->head;
    ngx_http_upstream_overload_peer_t * last = NULL;

    if (peers != NULL) {
        ngx_upstream_overload_print_peers(peers);
    }

    if (peer == NULL) {
        printf("[upstream_overload] [%s] (nil)\n", list_name);
    }

    while (peer != NULL) {
        printf("[upstream_overload] [%s] peer[%d] prev=%p, this=%p, next=%p\n",
            list_name, peer->index, peer->prev, peer, peer->next);
        last = peer;
        peer = peer->next;
    }

    if (list->tail != last) {
        printf("ERROR ****************** [upstream_overload] [%s] TAIL IS WRONG!!!\n", list_name);
    }
}

/**
 * remove the head item and return it's index
 * or NGX_PEER_INVALID if the list is empty
 */
static ngx_uint_t
ngx_peer_list_pop(ngx_peer_list_t * list, char * list_name, ngx_log_t * log)
{
    ngx_http_upstream_overload_peer_t * peer;

    if (list->head == NULL) {
        dd3("_list_pop(list=%p, list_name='%s', log=%p): pop failed (list is empty)", list, list_name, log);
        return NGX_PEER_INVALID;
    } else {
        peer = list->head;
        dd4("_list_pop(list=%p, list_name='%s', log=%p): popping peer[%d]", list, list_name, log, peer->index);

        //beergarden_assert(peer->prev == NULL, log, "pop: peer->prev != NULL");
        list->head = list->head->next;
        peer->next = NULL;
        if (list->head == NULL) {
            list->tail = NULL;
        } else {
            list->head->prev = NULL;
        }
        return peer->index;
    }
}

/**
 * add peer to the head of the list
 * or NGX_PEER_INVALID if the list is empty
 */
static void
ngx_peer_list_push(ngx_peer_list_t * list, char * list_name, ngx_http_upstream_overload_peer_t * peer, ngx_log_t * log)
{
    dd5("_list_push(list=%p, list_name='%s', peer=%p, log=%p): pushing peer[%d]", list, list_name, peer, log, peer->index);

    //beergarden_assert(peer->prev == NULL && peer->next == NULL, log, "ngx_beergarden_list_push: not(peer->prev == NULL && peer->next == NULL)");

    if (list->head == NULL) {
        list->head = peer;
        list->tail = peer;
    } else {
        list->tail->next = peer;
        peer->prev = list->tail;
        list->tail = peer;
    }
}

/**
 * remove a peer from an arbitrary position in the list
 */
static void ngx_peer_list_remove(ngx_peer_list_t * list, char * list_name, ngx_http_upstream_overload_peer_t * peer, ngx_log_t * log)
{
    //dd5("_list_remove(list=%p, list_name='%s', peer=%p, log=%p): removing peer[%d]", list, list_name, peer, log, peer->index);

    if (list->head == peer) {
        ngx_peer_list_pop(list, list_name, log);
        //beergarden_assert(peer->index == index, log, "ngx_beergarden_list_remove: peer->index != index");
    } else if (list->tail == peer) {
        list->tail = peer->prev;
        list->tail->next = NULL;
        peer->prev = NULL;
        //beergarden_assert(peer->next == NULL, log, "ngx_beergarden_list_remove: nopeer->next != NULL");
    } else {
        peer->prev->next = peer->next;
        peer->next->prev = peer->prev;
        peer->prev = NULL;
        peer->next = NULL;
    }
}

// parses the "overload" directive in the nginx config file
// this function is also references in the config file for this module
static char *
ngx_http_upstream_overload(ngx_conf_t * cf, ngx_command_t * cmd, void * conf)
{
    ngx_http_upstream_srv_conf_t * uscf;

    dd3("ngx_http_upstream_overload(cf=%p, cmd=%p, conf=%p): entering", cf, cmd, conf);

    uscf = ngx_http_conf_get_module_srv_conf(cf, ngx_http_upstream_module);

    uscf->peer.init_upstream = ngx_http_upstream_init_overload_once;

    uscf->flags = NGX_HTTP_UPSTREAM_CREATE;

    dd3("ngx_http_upstream_overload(cf=%p, cmd=%p, conf=%p): exiting --> NGX_CONF_OK", cf, cmd, conf);
    return NGX_CONF_OK;
}

// parses the "num_spare_backends" directive in the nginx config file
static char *
ngx_http_upstream_overload_parse_num_spare_backends(ngx_conf_t *cf, ngx_command_t *cmd, void *conf)
{
    ngx_str_t *value = cf->args->elts;

    dd3("_parse_num_spare_backends(cf=%p, cmd=%p, conf=%p): entering", cf, cmd, conf);

    overload_conf.num_spare_backends = ngx_atoi(value[1].data, value[1].len);
    dd4("_parse_num_spare_backends(cf=%p, cmd=%p, conf=%p): num_spare_backends = %d", cf, cmd, conf, overload_conf.num_spare_backends);

    dd3("_parse_num_spare_backends(cf=%p, cmd=%p, conf=%p): exiting --> NGX_CONF_OK", cf, cmd, conf);

    return NGX_CONF_OK;
}

// parses the "alert_pipe" directive in the nginx config file
static char *
ngx_http_upstream_overload_parse_alert_pipe(ngx_conf_t *cf, ngx_command_t *cmd, void *conf)
{
    ngx_str_t *value = cf->args->elts;
    size_t max_bytes = sizeof(overload_conf.alert_pipe_path);

    dd3("_parse_alert_pipe(cf=%p, cmd=%p, conf=%p): entering", cf, cmd, conf);

    // TODO: Use an ngx function instead of strncpy
    strncpy(overload_conf.alert_pipe_path, (char *) value[1].data, max_bytes);

    if (overload_conf.alert_pipe_path[max_bytes - 1] != '\0') {
        overload_conf.alert_pipe_path[0] = '\0';
        dd_conf_error0(NGX_LOG_EMERG, cf, 0, "alert_pipe string has too many characters");
        return NGX_CONF_ERROR;
    }

    dd4("_parse_alert_pipe(cf=%p, cmd=%p, conf=%p): alert_pipe_path = '%s'", cf, cmd, conf, overload_conf.alert_pipe_path);

    return NGX_CONF_OK;
}

// Called once during initialization of upstream_overload module
ngx_int_t
ngx_http_upstream_init_overload_once(ngx_conf_t *cf, ngx_http_upstream_srv_conf_t *us)
{
    ngx_uint_t                           i;
    ngx_http_upstream_server_t          *server;
    ngx_http_upstream_overload_peers_t  *peers;
    ngx_http_upstream_overload_peer_t   *prev;

    dd2("_init_overload_once(cf=%p, us=%p): entering", cf, us);

    us->peer.init = ngx_http_upstream_init_overload_peer;

    if (!us->servers) {
        dd_conf_error0(NGX_LOG_EMERG, cf, 0, "There are no server directives within upstream block.");
        return NGX_ERROR;
    }

    server = us->servers->elts;

    for (i = 0; i < us->servers->nelts; i++) {
        if (server[i].naddrs > 1) {
            dd_conf_error1(NGX_LOG_EMERG, cf, 0, "server '%s' resolves to multiple addresses. "
                "Each server must resolve to exactly one address.", server[i].addrs[0].name.data);
            return NGX_ERROR;
        }
    }

    peers = ngx_pcalloc(cf->pool, sizeof(ngx_http_upstream_overload_peers_t));
    if (peers == NULL) {
        return NGX_ERROR;
    }

    peers->num_peers = us->servers->nelts;
    peers->peer = ngx_pcalloc(cf->pool, sizeof(ngx_http_upstream_overload_peer_t) * peers->num_peers);

    dd3("_init_overload_once(cf=%p, us=%p): peers = %p", cf, us, peers);
    dd3("_init_overload_once(cf=%p, us=%p): peers->num_peers = %d", cf, us, peers->num_peers);
    dd3("_init_overload_once(cf=%p, us=%p): peers->peer = %p", cf, us, peers->peer);

    peers->idle_list.head = &peers->peer[0];
    peers->idle_list.tail = &peers->peer[peers->num_peers - 1];
    peers->busy_list.head = NULL;
    peers->busy_list.tail = NULL;
    prev = NULL;

    for (i = 0; i < us->servers->nelts; i++) {
        peers->peer[i].sockaddr = server[i].addrs[0].sockaddr;
        peers->peer[i].socklen = server[i].addrs[0].socklen;
        peers->peer[i].name = server[i].addrs[0].name;
        peers->peer[i].busy = 0;
        peers->peer[i].index = i;
        peers->peer[i].prev = prev;
        if (prev != NULL) {
            prev->next = &peers->peer[i];
        }
        prev = &peers->peer[i];
        dd4("_init_overload_once(cf=%p, us=%p): peers->peer[%d] = '%s'", cf, us, i, peers->peer[i].name.data);
    }
    prev->next = &peers->peer[peers->num_peers - 1];
    peers->peer[peers->num_peers - 1].next = NULL;

    dd_list(&peers->idle_list, "idle_list", peers);
    dd_list(&peers->busy_list, "busy_list", NULL);

    us->peer.data = peers;

    dd2("_init_overload_once(cf=%p, us=%p): exiting --> returned NGX_CONF_OK", cf, us);
    return NGX_OK;
}

// called once per request to initialize the structures used for just this request
static ngx_int_t
ngx_http_upstream_init_overload_peer(ngx_http_request_t *r,
    ngx_http_upstream_srv_conf_t *us)
{
    ngx_http_upstream_overload_request_data_t * request_data;

    dd2("_init_overload_peer(r=%p, us=%p): entering", r, us);

    r->upstream->peer.get = ngx_http_upstream_get_overload_peer;
    r->upstream->peer.free = ngx_http_upstream_free_overload_peer;
    r->upstream->peer.tries = 1;

    request_data = ngx_pcalloc(r->pool, sizeof(ngx_http_upstream_overload_request_data_t));
    dd3("_init_overload_peer(r=%p, us=%p): request_data=%p", r, us, request_data);
    request_data->peers = us->peer.data;
    request_data->peer_index = NGX_PEER_INVALID;

    r->upstream->peer.data = request_data;

    dd2("_init_overload_peer(r=%p, us=%p): exiting --> returned NGX_OK", r, us);
    return NGX_OK;
}

// called by nginx to determine which backend should receive this request
static ngx_int_t
ngx_http_upstream_get_overload_peer(ngx_peer_connection_t *pc, void *data)
{
    ngx_http_upstream_overload_request_data_t * request_data = data;
    ngx_http_upstream_overload_peers_t * peers = request_data->peers;
    ngx_http_upstream_overload_peer_t * peer;

    dd2("_get_overload_peer(pc=%p, request_data=%p): entering", pc, request_data);

    // grab a peer from the idle list
    request_data->peer_index = ngx_peer_list_pop(&peers->idle_list, "idle_list", pc->log);

    if (request_data->peer_index == NGX_PEER_INVALID) {
        dd_log2(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_get_overload_peer(pc=%p, request_data=%p): No peers available; cannot forward request.\n\n", pc, request_data);
        return NGX_BUSY;
    }

    peer = &peers->peer[request_data->peer_index];

    // push the peer onto the busy list
    ngx_peer_list_push(&peers->busy_list, "busy_list", peer, pc->log);

    // the whole point of this function is to set these three values
    pc->sockaddr = peer->sockaddr;
    pc->socklen = peer->socklen;
    pc->name = &peer->name;

    dd3("_get_overload_peer(pc=%p, request_data=%p): peer_index = %d\n\n", pc, request_data, request_data->peer_index);

    return NGX_OK;
}

// called by nginx after a request completes or fails
static void
ngx_http_upstream_free_overload_peer(ngx_peer_connection_t *pc, void *data, ngx_uint_t state)
{
    ngx_http_upstream_overload_request_data_t * request_data = data;
    ngx_http_upstream_overload_peers_t * peers = request_data->peers;
    ngx_http_upstream_overload_peer_t * peer;
    ngx_uint_t peer_index = request_data->peer_index;

    dd3("_free_overload_peer(pc=%p, request_data=%p, state=%d): entering", pc, request_data, state);

    // If the _get_overload_peer() invocation yielded NGX_BUSY
    if (peer_index == NGX_PEER_INVALID) {
        dd3("_free_overload_peer(pc=%p, request_data=%p, state=%d): peer_index = NGX_PEER_INVALID --> exiting", pc, request_data, state);
        return;
    }

    peer = &peers->peer[peer_index];

    dd4("_free_overload_peer(pc=%p, request_data=%p, state=%d): peer_index = %d", pc, request_data, state, peer_index);

    // remove the peer from the busy list
    ngx_peer_list_remove(&peers->busy_list, "busy_list", peer, pc->log);

    // push the peer onto the idle list
    ngx_peer_list_push(&peers->idle_list, "idle_list", peer, pc->log);

    pc->tries = 0;

    dd4("_free_overload_peer(pc=%p, request_data=%p, state=%d): exiting --> decremented pc->tries to %d\n\n",
        pc, request_data, state, pc->tries);

}

