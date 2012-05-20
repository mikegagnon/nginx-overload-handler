/**
 * This code is largely copied from Nginx's secure_link module, located in:
 * dependencies/downloads/nginx-1.0.12/src/http/modules/ngx_http_secure_link_module.c
 *
 * Copyright (C) 2002-2012 Igor Sysoev
 * Copyright (C) 2011,2012 Nginx, Inc.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * Modifications that differ from ngx_http_secure_link_module.c are copyrighted
 * and licensed as follows:
 *
 * Copyright 2012 HellaSec, LLC
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
 * ==== doorman module for nginx ====
 */

#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>
#include <ngx_md5.h>


typedef struct {
    ngx_http_complex_value_t  *variable;
    ngx_http_complex_value_t  *md5;
} ngx_http_doorman_conf_t;


typedef struct {
    ngx_str_t                  expires;
} ngx_http_doorman_ctx_t;


static ngx_int_t ngx_http_doorman_expires_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data);
static void *ngx_http_doorman_create_conf(ngx_conf_t *cf);
static char *ngx_http_doorman_merge_conf(ngx_conf_t *cf, void *parent,
    void *child);
static ngx_int_t ngx_http_doorman_add_variables(ngx_conf_t *cf);


static ngx_command_t  ngx_http_doorman_commands[] = {

    { ngx_string("doorman"),
      NGX_HTTP_MAIN_CONF|NGX_HTTP_SRV_CONF|NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
      ngx_http_set_complex_value_slot,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_doorman_conf_t, variable),
      NULL },

    { ngx_string("doorman_md5"),
      NGX_HTTP_MAIN_CONF|NGX_HTTP_SRV_CONF|NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
      ngx_http_set_complex_value_slot,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_doorman_conf_t, md5),
      NULL },

      ngx_null_command
};


static ngx_http_module_t  ngx_http_doorman_module_ctx = {
    ngx_http_doorman_add_variables,    /* preconfiguration */
    NULL,                                  /* postconfiguration */

    NULL,                                  /* create main configuration */
    NULL,                                  /* init main configuration */

    NULL,                                  /* create server configuration */
    NULL,                                  /* merge server configuration */

    ngx_http_doorman_create_conf,      /* create location configuration */
    ngx_http_doorman_merge_conf        /* merge location configuration */
};


ngx_module_t  ngx_http_doorman_module = {
    NGX_MODULE_V1,
    &ngx_http_doorman_module_ctx,      /* module context */
    ngx_http_doorman_commands,         /* module directives */
    NGX_HTTP_MODULE,                       /* module type */
    NULL,                                  /* init master */
    NULL,                                  /* init module */
    NULL,                                  /* init process */
    NULL,                                  /* init thread */
    NULL,                                  /* exit thread */
    NULL,                                  /* exit process */
    NULL,                                  /* exit master */
    NGX_MODULE_V1_PADDING
};


static ngx_str_t  ngx_http_doorman_name = ngx_string("doorman");
static ngx_str_t  ngx_http_doorman_expires_name =
    ngx_string("doorman_expires");


// instantiates the $doorman nginx-variable
static ngx_int_t
ngx_http_doorman_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    u_char                       *p, *last;
    ngx_str_t                     val, hash;
    time_t                        expires;
    ngx_md5_t                     md5;
    ngx_http_doorman_ctx_t   *ctx;
    ngx_http_doorman_conf_t  *conf;
    u_char                        hash_buf[16], md5_buf[16];

    conf = ngx_http_get_module_loc_conf(r, ngx_http_doorman_module);

    if (conf->variable == NULL || conf->md5 == NULL) {
        goto not_found;
    }

    // perform variable substition in $doorman
    // i.e. if config has doorman $arg_admitkey,$arg_admitkey_expire;
    // and request is index.php?admitkey=foo&admitkey_expire=bar
    // then val == "foo,bar"
    if (ngx_http_complex_value(r, conf->variable, &val) != NGX_OK) {
        return NGX_ERROR;
    }

    ngx_log_debug1(NGX_LOG_DEBUG_HTTP, r->connection->log, 0,
                   "doorman link: \"%V\"", &val);

    // point to end of val
    last = val.data + val.len;

    // p points to the comma in val
    p = ngx_strlchr(val.data, last, ',');
    expires = 0;

    if (p) {
        val.len = p++ - val.data;

        // parse the expiration string
        expires = ngx_atotm(p, last - p);
        if (expires <= 0) {
            goto not_found;
        }

        ctx = ngx_pcalloc(r->pool, sizeof(ngx_http_doorman_ctx_t));
        if (ctx == NULL) {
            return NGX_ERROR;
        }

        ngx_http_set_ctx(r, ctx, ngx_http_doorman_module);

        ctx->expires.len = last - p;
        ctx->expires.data = p;
    }

    // val now contains just the hash key

    // a hash with more than 24 chars is auotmatically invalid
    if (val.len > 24) {
        goto not_found;
    }

    hash.len = 16;
    hash.data = hash_buf;

    // parse the hash parameter into hash
    if (ngx_decode_base64url(&hash, &val) != NGX_OK) {
        goto not_found;
    }

    if (hash.len != 16) {
        goto not_found;
    }

    // perform variable substition in $doorman_md5
    if (ngx_http_complex_value(r, conf->md5, &val) != NGX_OK) {
        return NGX_ERROR;
    }

    ngx_log_debug1(NGX_LOG_DEBUG_HTTP, r->connection->log, 0,
                   "doorman link md5: \"%V\"", &val);

    // TODO: remove the admitkey param from val

    // hash val
    ngx_md5_init(&md5);
    ngx_md5_update(&md5, val.data, val.len);
    ngx_md5_final(md5_buf, &md5);

    // make sure the hash is valid
    if (ngx_memcmp(hash_buf, md5_buf, 16) != 0) {
        goto not_found;
    }

    v->data = (u_char *) ((expires && expires < ngx_time()) ? "0" : "1");
    v->len = 1;
    v->valid = 1;
    v->no_cacheable = 0;
    v->not_found = 0;

    return NGX_OK;

not_found:

    v->not_found = 1;

    return NGX_OK;
}

static ngx_int_t
ngx_http_doorman_expires_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    ngx_http_doorman_ctx_t  *ctx;

    ctx = ngx_http_get_module_ctx(r, ngx_http_doorman_module);

    if (ctx) {
        v->len = ctx->expires.len;
        v->valid = 1;
        v->no_cacheable = 0;
        v->not_found = 0;
        v->data = ctx->expires.data;

    } else {
        v->not_found = 1;
    }

    return NGX_OK;
}


static void *
ngx_http_doorman_create_conf(ngx_conf_t *cf)
{
    ngx_http_doorman_conf_t  *conf;

    conf = ngx_pcalloc(cf->pool, sizeof(ngx_http_doorman_conf_t));
    if (conf == NULL) {
        return NULL;
    }

    /*
     * set by ngx_pcalloc():
     *
     *     conf->variable = NULL;
     *     conf->md5 = NULL;
     */

    return conf;
}


static char *
ngx_http_doorman_merge_conf(ngx_conf_t *cf, void *parent, void *child)
{
    ngx_http_doorman_conf_t *prev = parent;
    ngx_http_doorman_conf_t *conf = child;

    if (conf->variable == NULL) {
        conf->variable = prev->variable;
    }

    if (conf->md5 == NULL) {
        conf->md5 = prev->md5;
    }

    return NGX_CONF_OK;
}


static ngx_int_t
ngx_http_doorman_add_variables(ngx_conf_t *cf)
{
    ngx_http_variable_t  *var;

    var = ngx_http_add_variable(cf, &ngx_http_doorman_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_variable;

    var = ngx_http_add_variable(cf, &ngx_http_doorman_expires_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_expires_variable;

    return NGX_OK;
}


