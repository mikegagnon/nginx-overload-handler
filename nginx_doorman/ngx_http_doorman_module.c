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
 *
 * Access control for GET requests using the client puzzle algorithm as
 * described in "Client Puzzles: A Cryptographic Countermeasure Against
 * Connection Depletion Attacks." http://www.rsa.com/rsalabs/node.asp?id=2050
 *
 * The general idea is to rate-limit GET requests by forcing clients to pay
 * an "admission fee" in order to have a request admitted. Clients pay
 * admisson by burning their own CPU cycles (in JavaScript). This mechanism
 * rate limits clients according to their CPU resources. This form of rate
 * limiting is desirable when other forms of rate limiting (e.g.
 * HttpLimitReqModule) are undesirable -- such as when the attacker has many IP
 * addresses or legitimate users are being proxied through a single IP address.
 *
 * The mechanism works as follows.
 *   - Let x = hash(s, r), where s is a secret string (only known to the server)
 *     and r is the text of the request
 *   - Let y = hash(x)  (aka meta_hash)
 *   - Let the puzzle be the 4-tuple (r, y, truncate(x), b), where truncate(x) is the
 *     "truncated "version of x (aka trunc_hash), i.e. x but with b bits removed (aka
 *     missing_bits)
 *   - Give the puzzle to the client
 *       - Note, the client does not know the complete value x, but knows an approximate
 *         value of x
 *   - The client solves the puzzle by guessing various values for the value x,
 *     (i.e. a brute force search). We'll call a particular guess x'.
 *   - The client knows they have found the solution when hash(x') = y
 *   - The client re-sends the request, along with the solution x.
 *   - The server can quickly check whether a solution is valid by calculating
 *     hash(s,r); if it matches the given x then the server knows that the
 *     client has spent the CPU time to brute-force the hash
 *   - The protocol also uses nonces to prevent replay attacks
 *
 * Can be configured to:
 *  (1) have static puzzle diffuclty, or
 *  (2) choose dynamic puzzle difficulty depending on the upstream load (as
 *      determined by the nginx_upstream_overload module)
 *
 */

#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>
#include <ngx_md5.h>


// md5 has 16-byte hashes
#define DOORMAN_HASH_LEN 16

typedef struct {
    ngx_http_complex_value_t  *variable;
    ngx_http_complex_value_t  *md5;
    ngx_http_complex_value_t  *orig_uri;
    ngx_http_complex_value_t  *orig_args;
} ngx_http_doorman_conf_t;


typedef struct {
    ngx_str_t                  expires;
    ngx_str_t                  orig_uri;
    ngx_str_t                  orig_args;
    ngx_str_t                  trunc_hash;
    ngx_str_t                  meta_hash;
    ngx_str_t                  missing_bits;
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

    { ngx_string("doorman_orig_uri"),
      NGX_HTTP_MAIN_CONF|NGX_HTTP_SRV_CONF|NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
      ngx_http_set_complex_value_slot,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_doorman_conf_t, orig_uri),
      NULL },

    { ngx_string("doorman_orig_args"),
      NGX_HTTP_MAIN_CONF|NGX_HTTP_SRV_CONF|NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
      ngx_http_set_complex_value_slot,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_doorman_conf_t, orig_args),
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
static ngx_str_t  ngx_http_doorman_expires_name = ngx_string("doorman_expires");
// holds $uri?$args
static ngx_str_t  ngx_http_orig_uri_name = ngx_string("orig_uri");
static ngx_str_t  ngx_http_orig_args_name = ngx_string("orig_args");
static ngx_str_t  ngx_http_trunc_hash_name = ngx_string("trunc_hash");
static ngx_str_t  ngx_http_meta_hash_name = ngx_string("meta_hash");
static ngx_str_t  ngx_http_missing_bits_name = ngx_string("missing_bits");

// buf points to a u_char array of size DOORMAN_HASH_LEN
static void
ngx_http_doorman_hash(ngx_str_t * str, u_char * buf)
{
    ngx_md5_t md5;
    ngx_md5_init(&md5);
    ngx_md5_update(&md5, str->data, str->len);
    ngx_md5_final(buf, &md5);
}

// instantiates the $doorman nginx-variable
static ngx_int_t
ngx_http_doorman_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    u_char                       *p, *last;
    ngx_str_t                     val, hash;
    time_t                        expires;
    ngx_http_doorman_ctx_t   *ctx;
    ngx_http_doorman_conf_t  *conf;
    u_char                        given_hash_buf[DOORMAN_HASH_LEN], actual_hash_buf[DOORMAN_HASH_LEN];

    conf = ngx_http_get_module_loc_conf(r, ngx_http_doorman_module);
    ctx = ngx_pcalloc(r->pool, sizeof(ngx_http_doorman_ctx_t));
    if (ctx == NULL) {
        return NGX_ERROR;
    }
    ngx_http_set_ctx(r, ctx, ngx_http_doorman_module);

    // parse the orig_uri config variable into an nginx variable
    if (ngx_http_complex_value(r, conf->orig_uri, &val) != NGX_OK) {
        return NGX_ERROR;
    }
    ngx_log_debug1(NGX_LOG_DEBUG_HTTP, r->connection->log, 0,
                   "doorman orig_uri: \"%V\"", &val);
    ctx->orig_uri.len = val.len;
    ctx->orig_uri.data = val.data;

    // parse the orig_args variable
    if (ngx_http_complex_value(r, conf->orig_args, &val) != NGX_OK) {
        return NGX_ERROR;
    }
    ngx_log_debug1(NGX_LOG_DEBUG_HTTP, r->connection->log, 0,
                   "doorman orig_args: \"%V\"", &val);
    ctx->orig_args.len = val.len;
    ctx->orig_args.data = val.data;


    ctx->trunc_hash.len = val.len;
    ctx->trunc_hash.data = val.data;
    ctx->meta_hash.len = val.len;
    ctx->meta_hash.data = val.data;
    ctx->missing_bits.len = val.len;
    ctx->missing_bits.data = val.data;
    ctx->expires.len = val.len;
    ctx->expires.data = val.data;

    if (conf->variable == NULL || conf->md5 == NULL || conf->orig_uri == NULL || conf->orig_args == NULL) {
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


        ctx->expires.len = last - p;
        ctx->expires.data = p;
    }

    // val now contains just the hash key

    // a hash with more than 24 chars is auotmatically invalid
    if (val.len > 24) {
        goto not_found;
    }

    hash.len = DOORMAN_HASH_LEN;
    hash.data = given_hash_buf;

    // parse the hash parameter into hash
    if (ngx_decode_base64url(&hash, &val) != NGX_OK) {
        goto not_found;
    }

    if (hash.len != DOORMAN_HASH_LEN) {
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
    ngx_http_doorman_hash(&val, actual_hash_buf);

    // make sure the hash is valid
    if (ngx_memcmp(given_hash_buf, actual_hash_buf, DOORMAN_HASH_LEN) != 0) {
        goto not_found;
    }

    v->data = (u_char *) ((expires && expires < ngx_time()) ? "0" : "1");
    v->len = 1;
    v->valid = 1;
    v->no_cacheable = 0;
    v->not_found = 0;

    return NGX_OK;

not_found:

    // TODO: Create variables for puzzle generation.
    // We already have the x-value (actual_hash_buf)
    // Need to calculate and define variables for y,
    // truncate(x), and b -- so that puzzle SSI
    // can deliver puzzle to visitor


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

static ngx_int_t
ngx_http_doorman_orig_uri_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    ngx_http_doorman_ctx_t  *ctx;

    ctx = ngx_http_get_module_ctx(r, ngx_http_doorman_module);

    if (ctx) {
        v->len = ctx->orig_uri.len;
        v->valid = 1;
        v->no_cacheable = 0;
        v->not_found = 0;
        v->data = ctx->orig_uri.data;

    } else {
        v->not_found = 1;
    }

    return NGX_OK;
}

static ngx_int_t
ngx_http_doorman_orig_args_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    ngx_http_doorman_ctx_t  *ctx;

    ctx = ngx_http_get_module_ctx(r, ngx_http_doorman_module);

    if (ctx) {
        v->len = ctx->orig_args.len;
        v->valid = 1;
        v->no_cacheable = 0;
        v->not_found = 0;
        v->data = ctx->orig_args.data;

    } else {
        v->not_found = 1;
    }

    return NGX_OK;
}

static ngx_int_t
ngx_http_doorman_trunc_hash_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    ngx_http_doorman_ctx_t  *ctx;

    ctx = ngx_http_get_module_ctx(r, ngx_http_doorman_module);

    if (ctx) {
        v->len = ctx->trunc_hash.len;
        v->valid = 1;
        v->no_cacheable = 0;
        v->not_found = 0;
        v->data = ctx->trunc_hash.data;

    } else {
        v->not_found = 1;
    }

    return NGX_OK;
}

static ngx_int_t
ngx_http_doorman_meta_hash_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    ngx_http_doorman_ctx_t  *ctx;

    ctx = ngx_http_get_module_ctx(r, ngx_http_doorman_module);

    if (ctx) {
        v->len = ctx->meta_hash.len;
        v->valid = 1;
        v->no_cacheable = 0;
        v->not_found = 0;
        v->data = ctx->meta_hash.data;

    } else {
        v->not_found = 1;
    }

    return NGX_OK;
}

static ngx_int_t
ngx_http_doorman_missing_bits_variable(ngx_http_request_t *r,
    ngx_http_variable_value_t *v, uintptr_t data)
{
    ngx_http_doorman_ctx_t  *ctx;

    ctx = ngx_http_get_module_ctx(r, ngx_http_doorman_module);

    if (ctx) {
        v->len = ctx->missing_bits.len;
        v->valid = 1;
        v->no_cacheable = 0;
        v->not_found = 0;
        v->data = ctx->missing_bits.data;

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
     *     conf->orig_uri = NULL;
     *     conf->orig_args = NULL;
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

    if (conf->orig_uri == NULL) {
        conf->orig_uri = prev->orig_uri;
    }

    if (conf->orig_args == NULL) {
        conf->orig_args = prev->orig_args;
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

    var = ngx_http_add_variable(cf, &ngx_http_orig_args_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_orig_args_variable;

    var = ngx_http_add_variable(cf, &ngx_http_orig_uri_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_orig_uri_variable;

    var = ngx_http_add_variable(cf, &ngx_http_trunc_hash_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_trunc_hash_variable;

    var = ngx_http_add_variable(cf, &ngx_http_meta_hash_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_meta_hash_variable;

    var = ngx_http_add_variable(cf, &ngx_http_missing_bits_name, 0);
    if (var == NULL) {
        return NGX_ERROR;
    }

    var->get_handler = ngx_http_doorman_missing_bits_variable;

    return NGX_OK;
}


