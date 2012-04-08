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
 * ==== TODO ====
 *  - a bunch of things (see todos throughout code)
 *  - make sure entering / exit logging is used consistently
 *  - consistent naming
 */

#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>
#include <ngx_thread.h>

/**
 * Macro definition
 *****************************************************************************/

#define DEFAULT_NUM_SPARE_BACKENDS 1
#define DEFAULT_ALERT_PIPE_PATH ""
#define STATIC_ALLOC_STR_BYTES 256

#define SPINLOCK_NUM_SPINS 1024
#define SPINLOCK_VALUE ngx_pid

#define MODULE_NAME_STR "upstream_overload"

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
        printf ("[" MODULE_NAME_STR "] " format "\n")
    #define dd1(format, a) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a)
    #define dd2(format, a, b) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a, b)
    #define dd3(format, a, b, c) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a, b, c)
    #define dd4(format, a, b, c, d) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a, b, c, d)
    #define dd5(format, a, b, c, d, e) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a, b, c, d, e)
    #define dd6(format, a, b, c, d, e, f) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a, b, c, d, e, f)
    #define dd7(format, a, b, c, d, e, f, g) \
        printf ("[" MODULE_NAME_STR "] " format "\n", a, b, c, d, e, f, g)
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

// Set to 1 to slow down the module, which helps with testing correct shared
// memory usage
#define SLOW_DOWN_MODULE_DEBUG 0

#if SLOW_DOWN_MODULE_DEBUG == 1

    void ngx_http_upstream_overload_SLOW_DOWN()
    {
        ngx_uint_t i, j, k;
        ngx_uint_t x=3;
        for(i = 0; i < 1000; i++) {
            for(j = 0; j < 1000; j++) {
                for(k = 0; k < 3000; k++) {
                    x *= i * j * k;
                }
            }
        }
        dd1("ngx_http_upstream_overload_SLOW_DOWN: slow_x = %d", x);
    }

    #define DO_SLOW_DOWN() ngx_http_upstream_overload_SLOW_DOWN()
#else
    #define DO_SLOW_DOWN()
#endif

#define dd_log0(level, log, err, format)                                    \
    do {                                                                    \
        dd0(format);                                                        \
        ngx_log_debug0(level, log, err, "[" MODULE_NAME_STR "] " format);   \
    } while (0)

#define dd_log1(level, log, err, format, a)                                     \
    do {                                                                        \
        dd1(format, a);                                                         \
        ngx_log_debug1(level, log, err, "[" MODULE_NAME_STR "] " format, a);    \
    } while (0)

#define dd_log2(level, log, err, format, a, b)                                  \
    do {                                                                        \
        dd2(format, a, b);                                                      \
        ngx_log_debug2(level, log, err, "[" MODULE_NAME_STR "] " format, a, b); \
    } while (0)

#define dd_log3(level, log, err, format, a, b, c)                                   \
    do {                                                                            \
        dd3(format, a, b, c);                                                       \
        ngx_log_debug3(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c);  \
    } while (0)

#define dd_log4(level, log, err, format, a, b, c, d)                                    \
    do {                                                                                \
        dd4(format, a, b, c, d);                                                        \
        ngx_log_debug4(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c, d);   \
    } while (0)

#define dd_error0(level, log, err, format)                                  \
    do {                                                                    \
        dd0("          [ERROR] " format);                                   \
        ngx_log_error(level, log, err, "[" MODULE_NAME_STR "] " format);    \
    } while (0)

#define dd_error1(level, log, err, format, a)                               \
    do {                                                                    \
        dd1("          [ERROR] " format, a);                                \
        ngx_log_error(level, log, err, "[" MODULE_NAME_STR "] " format, a); \
    } while (0)

#define dd_error2(level, log, err, format, a, b)                                \
    do {                                                                        \
        dd2("          [ERROR] " format, a, b);                                 \
        ngx_log_error(level, log, err, "[" MODULE_NAME_STR "] " format, a, b);  \
    } while (0)

#define dd_conf_error0(level, cf, err, format)                                  \
    do {                                                                        \
        dd0("          [CONFIG ERROR] " format);                                \
        ngx_conf_log_error(level, cf, err, "[" MODULE_NAME_STR "] " format);    \
    } while (0)

#define dd_conf_error1(level, cf, err, format, a)                               \
    do {                                                                        \
        dd1("          [CONFIG ERROR] " format, a);                             \
        ngx_conf_log_error(level, cf, err, "[" MODULE_NAME_STR "] " format, a); \
    } while (0)

/**
 * Struct definitions
 *****************************************************************************/

typedef struct {
    ngx_uint_t                      num_spare_backends;
    char                            alert_pipe_path[STATIC_ALLOC_STR_BYTES];
} ngx_http_upstream_overload_conf_t;

// holds global variables
typedef struct {
    ngx_uint_t                      shared_mem_size;
    ngx_shm_zone_t                 *shared_mem_zone;
} ngx_upstream_overload_global_t;

// During configuration parsing, upstream servers are read into instances of this struct
// These instances are immutable and do not exist in shared memory
typedef struct {
    struct sockaddr                    *sockaddr;
    socklen_t                           socklen;
    ngx_str_t                           name;

    // the index of this peer in the array
    ngx_uint_t                          index;

} ngx_immutable_peer_config_t;

// There is one instance of this struct. It is immutable and does not exist in shared memory
typedef struct {
    ngx_uint_t                         num_peers;
    ngx_immutable_peer_config_t       *peer_config;
} ngx_immutable_peer_config_array_t;

typedef struct ngx_http_upstream_overload_peer_s ngx_http_upstream_overload_peer_t;

// There is one of these structs for every backend server, i.e. for every "peer"
// These instances are mutable, and exist in shared memory
struct ngx_http_upstream_overload_peer_s {

    ngx_immutable_peer_config_t                  *peer_config;

    // busy == 0 if this peer is idle, busy != 0 if this peer is busy
    ngx_uint_t                          busy;

    // peer objects will be stored in an array, but peers can also be
    // linked together in doubly linked lists
    ngx_http_upstream_overload_peer_t  *prev;
    ngx_http_upstream_overload_peer_t  *next;
};

// mutable
typedef struct {
    ngx_http_upstream_overload_peer_t   *head;
    ngx_http_upstream_overload_peer_t   *tail;
    ngx_uint_t                           len;
} ngx_peer_list_t;

// There is only one instance of this struct
// It is mutable and exists in shared memory
typedef struct {

    // the array of mutable peers
    ngx_http_upstream_overload_peer_t   *peer;
    ngx_uint_t                           num_peers;

    // mutable lists of peers
    ngx_peer_list_t                      busy_list;
    ngx_peer_list_t                      idle_list;

    // overload alerts will be writtten to alert_pipe
    ngx_fd_t                             alert_pipe;
    ngx_atomic_t                         lock;
} ngx_http_upstream_overload_peer_state_t;

// There is one of these structs for each upstream block
// in the configuration file
typedef struct {
    ngx_immutable_peer_config_array_t           *config;

    // peer_state contains all shared memory
    ngx_http_upstream_overload_peer_state_t     *state;
} ngx_upstream_overload_peer_data_t;

// Each incoming request gets an instance of one of these structs
typedef struct {
    ngx_http_upstream_overload_peer_state_t * peer_state;

    // The index of the peer that is handling this request
    ngx_uint_t                           peer_index;
} ngx_http_upstream_overload_request_data_t;

/**
 * Function declarations
 *****************************************************************************/

/* For debugging */

static void
ngx_upstream_overload_print_peer_state(
    ngx_http_upstream_overload_peer_state_t *state);

static void ngx_upstream_overload_print_list(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_http_upstream_overload_peer_state_t *state);

/* List operations */

static ngx_uint_t
ngx_peer_list_pop(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_log_t *log);

static void
ngx_peer_list_push(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_http_upstream_overload_peer_t *peer,
    ngx_log_t *log);

static void
ngx_peer_list_remove(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_http_upstream_overload_peer_t *peer,
    ngx_log_t *log);

/* Parse configuration directives */

char *
ngx_http_upstream_overload(
    ngx_conf_t *cf,
    ngx_command_t *cmd,
    void *conf);

char *
ngx_http_upstream_overload_parse_num_spare_backends(
    ngx_conf_t *cf,
    ngx_command_t *cmd,
    void *conf);

char *
ngx_http_upstream_overload_parse_alert_pipe(
    ngx_conf_t *cf,
    ngx_command_t *cmd,
    void *conf);

/* Communcation via alert_pipe */

static void
write_alert(
    ngx_http_upstream_overload_peer_state_t *state,
    char *buf,
    size_t count,
    ngx_log_t *log);

static ngx_int_t
init_alert_pipe(
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_log_t *log);

static void
send_overload_alert(
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_http_upstream_overload_peer_t *peer,
    ngx_log_t *log);

/* Module initialization (after configuration parsing)*/

static ngx_int_t
ngx_http_upstream_overload_init_peer_state(
    ngx_immutable_peer_config_array_t *config,
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_log_t *log);

static ngx_int_t
ngx_http_upstream_overload_shared_mem_alloc(
    ngx_upstream_overload_peer_data_t *peer_data,
    ngx_log_t *log);

ngx_int_t
ngx_http_upstream_overload_init_shared_mem_zone(
    ngx_shm_zone_t *shared_mem_zone,
    void *data);

ngx_int_t
ngx_http_upstream_init_overload_once(
    ngx_conf_t *cf,
    ngx_http_upstream_srv_conf_t *us);

/* Event-handling for requests*/

ngx_int_t
ngx_http_upstream_init_overload_peer(
    ngx_http_request_t *r,
    ngx_http_upstream_srv_conf_t *us);

ngx_int_t ngx_http_upstream_get_overload_peer(
    ngx_peer_connection_t *pc,
    void *data);

void ngx_http_upstream_free_overload_peer(
    ngx_peer_connection_t *pc,
    void *data, ngx_uint_t state);

/**
 * Struct instantiations
 *****************************************************************************/

// Creating a global configuration variable (overload_conf) is not the best
// way to setup nginx configurations. However, my efforts to do it "the
// nginix way" have timed out for now.
// TODO: do it the nginx way
static ngx_http_upstream_overload_conf_t overload_conf = {
    .num_spare_backends = DEFAULT_NUM_SPARE_BACKENDS,
    .alert_pipe_path    = DEFAULT_ALERT_PIPE_PATH
};

// Group all global vars (except overload_conf) into this struct
static ngx_upstream_overload_global_t overload_global = {
    .shared_mem_size = 0,
    .shared_mem_zone = NULL
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
ngx_upstream_overload_print_peer_state(
    ngx_http_upstream_overload_peer_state_t *state)
{
    ngx_uint_t i;

    for (i = 0; i < state->num_peers; i++) {
        printf("[" MODULE_NAME_STR "] [peers] peer[%d] this=%p\n", i, &state->peer[i]);
    }
}

static void
ngx_upstream_overload_print_list(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_http_upstream_overload_peer_state_t *state)
{
    ngx_http_upstream_overload_peer_t *peer = list->head;
    ngx_http_upstream_overload_peer_t *last = NULL;

    if (state != NULL) {
        ngx_upstream_overload_print_peer_state(state);
    }

    printf("[" MODULE_NAME_STR "] [%s] len = %d\n", list_name, list->len);

    if (peer == NULL) {
        printf("[" MODULE_NAME_STR "] [%s] (empty list)\n", list_name);
    }

    while (peer != NULL) {
        printf("[" MODULE_NAME_STR "] [%s] peer[%d] prev=%p, this=%p, next=%p\n",
            list_name, peer->peer_config->index, peer->prev, peer, peer->next);
        last = peer;
        peer = peer->next;
    }

    if (list->tail != last) {
        printf("ERROR ****************** [" MODULE_NAME_STR "] [%s] TAIL IS WRONG!!!\n", list_name);
    }
}

/**
 * remove the head item and return it's index
 * or NGX_PEER_INVALID if the list is empty
 */
static ngx_uint_t
ngx_peer_list_pop(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_log_t *log)
{
    ngx_http_upstream_overload_peer_t *peer;

    if (list->head == NULL) {
        dd3("_list_pop(list=%p, list_name='%s', log=%p): pop failed (list is empty)", list, list_name, log);
        return NGX_PEER_INVALID;
    } else {
        list->len--;
        peer = list->head;
        dd4("_list_pop(list=%p, list_name='%s', log=%p): popping peer[%d]", list, list_name, log, peer->peer_config->index);

        list->head = list->head->next;
        peer->next = NULL;
        if (list->head == NULL) {
            list->tail = NULL;
        } else {
            list->head->prev = NULL;
        }
        return peer->peer_config->index;
    }
}

/**
 * add peer to the head of the list
 * or NGX_PEER_INVALID if the list is empty
 */
static void
ngx_peer_list_push(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_http_upstream_overload_peer_t *peer,
    ngx_log_t *log)
{
    dd5("_list_push(list=%p, list_name='%s', peer=%p, log=%p): pushing peer[%d]", list, list_name, peer, log, peer->peer_config->index);

    list->len++;
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
static void
ngx_peer_list_remove(
    ngx_peer_list_t *list,
    char *list_name,
    ngx_http_upstream_overload_peer_t *peer,
    ngx_log_t *log)
{
    dd5("_list_remove(list=%p, list_name='%s', peer=%p, log=%p): removing peer[%d]", list, list_name, peer, log, peer->peer_config->index);

    if (list->head == peer) {
        ngx_peer_list_pop(list, list_name, log);
    } else if (list->tail == peer) {
        list->len--;
        list->tail = peer->prev;
        list->tail->next = NULL;
        peer->prev = NULL;
    } else {
        list->len--;
        peer->prev->next = peer->next;
        peer->next->prev = peer->prev;
        peer->prev = NULL;
        peer->next = NULL;
    }
}

// parses the "overload" directive in the nginx config file
// this function is also references in the config file for this module
char *
ngx_http_upstream_overload(
    ngx_conf_t *cf,
    ngx_command_t *cmd,
    void *conf)
{
    ngx_http_upstream_srv_conf_t *uscf;

    dd3("ngx_http_upstream_overload(cf=%p, cmd=%p, conf=%p): entering", cf, cmd, conf);

    uscf = ngx_http_conf_get_module_srv_conf(cf, ngx_http_upstream_module);

    uscf->peer.init_upstream = ngx_http_upstream_init_overload_once;

    uscf->flags = NGX_HTTP_UPSTREAM_CREATE;

    dd3("ngx_http_upstream_overload(cf=%p, cmd=%p, conf=%p): exiting --> NGX_CONF_OK", cf, cmd, conf);
    return NGX_CONF_OK;
}

// parses the "num_spare_backends" directive in the nginx config file
char *
ngx_http_upstream_overload_parse_num_spare_backends(
    ngx_conf_t *cf,
    ngx_command_t *cmd,
    void *conf)
{
    ngx_str_t *value = cf->args->elts;

    dd3("_parse_num_spare_backends(cf=%p, cmd=%p, conf=%p): entering", cf, cmd, conf);

    overload_conf.num_spare_backends = ngx_atoi(value[1].data, value[1].len);
    dd4("_parse_num_spare_backends(cf=%p, cmd=%p, conf=%p): num_spare_backends = %d", cf, cmd, conf, overload_conf.num_spare_backends);

    dd3("_parse_num_spare_backends(cf=%p, cmd=%p, conf=%p): exiting --> NGX_CONF_OK", cf, cmd, conf);

    return NGX_CONF_OK;
}

// parses the "alert_pipe" directive in the nginx config file
char *
ngx_http_upstream_overload_parse_alert_pipe(
    ngx_conf_t *cf,
    ngx_command_t *cmd,
    void *conf)
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

// Tries to write bytes to the alert_pipe. On failure, closes the pipe and
// sets alert_pipe = NGX_INVALID_FILE
static void
write_alert(
    ngx_http_upstream_overload_peer_state_t *state,
    char *buf,
    size_t count,
    ngx_log_t *log)
{
    ssize_t bytes_written;

    bytes_written = write(state->alert_pipe, buf, count);

    if (bytes_written == (ssize_t) count) {
        dd_log2(NGX_LOG_DEBUG_HTTP, log, 0, "successfully wrote %d bytes to alert_pipe '%s'", count, overload_conf.alert_pipe_path);
        return;
    }
    else if (bytes_written == -1) {
        dd_error2(NGX_LOG_ERR, log, 0, "Error while writting to alert_pipe '%s'. Error = '%s'.", overload_conf.alert_pipe_path, strerror(errno));
    }
    else {
        dd_error1(NGX_LOG_ERR, log, 0, "Unknown error while writting to alert_pipe '%s'", overload_conf.alert_pipe_path);
    }

    if (ngx_close_file(state->alert_pipe) == NGX_FILE_ERROR) {
        dd_error2(NGX_LOG_ERR, log, 0, "Error while trying to close alert_pipe '%s'. Error = '%s'.", overload_conf.alert_pipe_path, strerror(errno));
    }

    state->alert_pipe = NGX_INVALID_FILE;
}


// Tests to do:
//  - File not exist
//  - File not a named pipe
//  - Wrong permissions
//  - File exists, but not opened for reading on other end
//  - Writing to a pipe that is not opened for reading on the other end
//  - Cause SIGPIPE signal (see man fifo)
//
// If alert_pipe == NGX_INVALID_FILE then tries to open alert_pipe and send 0
// If either fails (or if writing blocks), then closes alert_pipe and leaves it as NGX_INVALID_FILE
static ngx_int_t
init_alert_pipe(
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_log_t *log)
{
    char buf[] = "init\n";

    dd2("_init_alert_pipe(state=%p, log=%p): entering", state, log);

    if (overload_conf.alert_pipe_path[0] == '\0') {
        dd_log0(NGX_LOG_DEBUG_HTTP, log, 0, "not initializing alert_pipe because alert_pipe_path == ''");
        dd2("_init_alert_pipe(state=%p, log=%p): exiting", state, log);
        return NGX_OK;
    }

    if (state->alert_pipe == NGX_INVALID_FILE) {
        state->alert_pipe = ngx_open_file(overload_conf.alert_pipe_path, NGX_FILE_WRONLY | NGX_FILE_NONBLOCK, NGX_FILE_OPEN, 0);
        if (state->alert_pipe == NGX_INVALID_FILE) {
            dd_error2(NGX_LOG_EMERG, log, 0, "Could not open alert_pipe '%s'. Error = '%s'.", overload_conf.alert_pipe_path, strerror(errno));
            dd2("_init_alert_pipe(state=%p, log=%p): exiting", state, log);
            return NGX_ERROR;
        }
        dd_log1(NGX_LOG_DEBUG_HTTP, log, 0, "opened alert_pipe '%s'", overload_conf.alert_pipe_path);

        write_alert(state, buf, ngx_strlen(buf), log);
    }
    dd2("_init_alert_pipe(state=%p, log=%p): exiting", state, log);

    return NGX_OK;
}

// Present strategy is to send an alert from the head of busy list.
// TODO: Consider keeping track of busy peers that we have already sent alerts for.
// Then we will only send an alert to an item from the busy list that hasn't received
// an alert before
static void
send_overload_alert(
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_http_upstream_overload_peer_t *peer,
    ngx_log_t *log)
{
    char buf[STATIC_ALLOC_STR_BYTES];

    if (overload_conf.alert_pipe_path[0] == '\0') {
        dd_log0(NGX_LOG_DEBUG_HTTP, log, 0, "can't send alert because alerts are disabled");
    } else {
        dd_log1(NGX_LOG_DEBUG_HTTP, log, 0, "sending alert for peer %d", peer->peer_config->index);
        init_alert_pipe(state, log);

        if (state->alert_pipe != NGX_INVALID_FILE) {
            ngx_snprintf((u_char *) buf, sizeof(buf), "%s\n", peer->peer_config->name.data);
            write_alert(state, buf, (size_t) ngx_strlen(buf), log);
        }
    }
}

// initializes state by copying the peer configuation into state
static ngx_int_t
ngx_http_upstream_overload_init_peer_state(
    ngx_immutable_peer_config_array_t *config,
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_log_t *log)
{
    ngx_http_upstream_overload_peer_t   *prev;
    ngx_uint_t                           i;
    ngx_int_t                            result;

    dd3("_init_peer_state(config=%p, state=%p, log=%p): entering", config, state, log);

    state->num_peers = config->num_peers;

    state->alert_pipe = NGX_INVALID_FILE;

    state->idle_list.head = &state->peer[0];
    state->idle_list.tail = &state->peer[state->num_peers - 1];
    state->idle_list.len = state->num_peers;

    state->busy_list.head = NULL;
    state->busy_list.tail = NULL;
    state->busy_list.len = 0;

    prev = NULL;

    for (i = 0; i < state->num_peers; i++) {
        state->peer[i].peer_config = &config->peer_config[i];
        state->peer[i].busy = 0;
        state->peer[i].prev = prev;
        if (prev != NULL) {
            prev->next = &state->peer[i];
        }
        prev = &state->peer[i];
    }
    prev->next = NULL;

    dd_list(&state->idle_list, "idle_list", state);
    dd_list(&state->busy_list, "busy_list", NULL);

    result = init_alert_pipe(state, log);

    dd3("_init_peer_state(config=%p, state=%p, log=%p): exiting", config, state, log);
    return result;
}

// allocate shared memory for peer_data->state, then initialize peer_data->state
static ngx_int_t
ngx_http_upstream_overload_shared_mem_alloc(
    ngx_upstream_overload_peer_data_t *peer_data,
    ngx_log_t *log)
{
    ngx_slab_pool_t     *shpool;
    ngx_int_t            result;

    dd2("_shared_mem_alloc(peer_data=%p, log=%p): entering", peer_data, log);

    // shared === state
    // If the shared memory has already been allocated
    if (peer_data->state) {
        dd2("_shared_mem_alloc(peer_data=%p, log=%p): exiting sinc peer_data->state already exists", peer_data, log);
        return NGX_OK;
    }

    shpool = (ngx_slab_pool_t *) overload_global.shared_mem_zone->shm.addr;

    ngx_shmtx_lock(&shpool->mutex);

    peer_data->state = ngx_slab_alloc_locked(shpool,
        sizeof(ngx_upstream_overload_peer_data_t));

    if (peer_data->state == NULL) {
        ngx_shmtx_unlock(&shpool->mutex);
        return NGX_ERROR;
    }

    ngx_spinlock(&peer_data->state->lock, SPINLOCK_VALUE, SPINLOCK_NUM_SPINS);

    peer_data->state->peer = ngx_slab_alloc_locked(shpool,
        sizeof(ngx_http_upstream_overload_peer_t) * peer_data->config->num_peers);

    if (peer_data->state->peer == NULL) {
        ngx_unlock(&peer_data->state->lock);
        ngx_shmtx_unlock(&shpool->mutex);
        return NGX_ERROR;
    }

    result = ngx_http_upstream_overload_init_peer_state(peer_data->config, peer_data->state, log);

    ngx_unlock(&peer_data->state->lock);

    ngx_shmtx_unlock(&shpool->mutex);

    dd2("_shared_mem_alloc(peer_data=%p, log=%p): exiting", peer_data, log);
    return result;
}

ngx_int_t
ngx_http_upstream_overload_init_shared_mem_zone(
    ngx_shm_zone_t *shared_mem_zone,
    void *data)
{
    ngx_upstream_overload_peer_data_t   *peer_data = shared_mem_zone->data;
    ngx_int_t                            result;
    ngx_log_t                           *log = overload_global.shared_mem_zone->shm.log;

    dd2("_init_shared_mem_zone(shared_mem_zone=%p, data=%p): entering", shared_mem_zone, data);

    // the nginx core can call this func multiple times. For instance, reloading nginx will result in
    // this func being invoked again. Each time it is invoked it is given a different instance of
    // shared_mem_zone. BUT, the data parameter is taken from a previous shared_mem_zone->data.
    // This you can tell if this is a "re-invocation" by setting shared_mem_zone->data on the
    // first invocation. Then you cas test the value of data to see if this is the first invocation
    // or a  re-invocation.
    if (data) {
        dd2("_init_shared_mem_zone(shared_mem_zone=%p, data=%p): this is a re-invocation --> return NGX_OK",
            shared_mem_zone, data);
        shared_mem_zone->data = data;
        return NGX_OK;
    }

    dd2("_init_shared_mem_zone(shared_mem_zone=%p, data=%p): this is the first invocation",
        shared_mem_zone, data);

    result = ngx_http_upstream_overload_shared_mem_alloc(peer_data, log);

    shared_mem_zone->data = peer_data;

    return result;
}

// Called once during initialization of upstream_overload module
ngx_int_t
ngx_http_upstream_init_overload_once(
    ngx_conf_t *cf,
    ngx_http_upstream_srv_conf_t *us)
{
    ngx_uint_t                           i;
    ngx_http_upstream_server_t          *server;
    ngx_upstream_overload_peer_data_t   *peer_data;
    ngx_str_t                           *shared_mem_name;

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

    peer_data = ngx_pcalloc(cf->pool, sizeof(ngx_upstream_overload_peer_data_t));
    if (peer_data == NULL) {
        return NGX_ERROR;
    }

    peer_data->config = ngx_pcalloc(cf->pool, sizeof(ngx_immutable_peer_config_array_t));
    if (peer_data->config == NULL) {
        return NGX_ERROR;
    }

    // peer_state is shared memory that must be initialized
    // at a later point
    peer_data->state = NULL;

    peer_data->config->num_peers = us->servers->nelts;
    peer_data->config->peer_config = ngx_pcalloc(cf->pool, sizeof(ngx_immutable_peer_config_t) * peer_data->config->num_peers);
    if (peer_data->config->peer_config == NULL) {
        return NGX_ERROR;
    }

    dd3("_init_overload_once(cf=%p, us=%p): peer_data = %p", cf, us, peer_data);
    dd3("_init_overload_once(cf=%p, us=%p): peer_data->config = %p", cf, us, peer_data->config);
    dd3("_init_overload_once(cf=%p, us=%p): peer_data->config->peer_config = %p", cf, us, peer_data->config->peer_config);
    dd3("_init_overload_once(cf=%p, us=%p): num_peers = %d", cf, us, peer_data->config->num_peers);

    for (i = 0; i < us->servers->nelts; i++) {
        peer_data->config->peer_config[i].sockaddr = server[i].addrs[0].sockaddr;
        peer_data->config->peer_config[i].socklen = server[i].addrs[0].socklen;
        peer_data->config->peer_config[i].name = server[i].addrs[0].name;
        peer_data->config->peer_config[i].index = i;
        dd4("_init_overload_once(cf=%p, us=%p): peer_data->config->peer_config[%d] = '%s'", cf, us, i, peer_data->config->peer_config[i].name.data);
    }
    us->peer.data = peer_data;

    // Setup shared memory zone. Shared mem zone isn't acutally initialized until the nginx core
    // calls ngx_http_upstream_overload_init_shared_mem_zone. Even crazier, the shared memory
    // (itself) isn't even allocated until the first call to ngx_http_upstream_init_overload_peer.
    // The reason for this craziness is best explained by this tutorial:
    // http://www.evanmiller.org/nginx-modules-guide-advanced.html
    shared_mem_name = ngx_palloc(cf->pool, sizeof *shared_mem_name);
    shared_mem_name->len = sizeof(MODULE_NAME_STR) - 1;
    shared_mem_name->data = (u_char *) MODULE_NAME_STR;

    if (overload_global.shared_mem_size == 0) {
        overload_global.shared_mem_size = 8 * ngx_pagesize;
    }

    overload_global.shared_mem_zone = ngx_shared_memory_add(cf, shared_mem_name, overload_global.shared_mem_size,
        &ngx_http_upstream_overload_module);

    if (overload_global.shared_mem_zone == NULL) {
        dd_conf_error0(NGX_LOG_EMERG, cf, 0, "overload_global.shared_mem_zone == NULL");
        return NGX_ERROR;
    }

    overload_global.shared_mem_zone->init = ngx_http_upstream_overload_init_shared_mem_zone;
    overload_global.shared_mem_zone->data = peer_data;
    dd3("_init_overload_once(cf=%p, us=%p): overload_global.shared_mem_zone == %p", cf, us, overload_global.shared_mem_zone);

    dd2("_init_overload_once(cf=%p, us=%p): exiting --> returned NGX_CONF_OK", cf, us);
    return NGX_OK;
}

// called once per request to initialize the structures used for just this request. Well actually, it also allocates and initializes memory, if this is the first request.
ngx_int_t
ngx_http_upstream_init_overload_peer(
    ngx_http_request_t *r,
    ngx_http_upstream_srv_conf_t *us)
{
    ngx_http_upstream_overload_request_data_t *request_data;
    ngx_upstream_overload_peer_data_t *peer_data = us->peer.data;

    dd2("_init_overload_peer(r=%p, us=%p): entering", r, us);

    r->upstream->peer.get = ngx_http_upstream_get_overload_peer;
    r->upstream->peer.free = ngx_http_upstream_free_overload_peer;
    r->upstream->peer.tries = 1;

    request_data = ngx_pcalloc(r->pool, sizeof(ngx_http_upstream_overload_request_data_t));
    dd3("_init_overload_peer(r=%p, us=%p): request_data=%p", r, us, request_data);
    request_data->peer_state = peer_data->state;
    request_data->peer_index = NGX_PEER_INVALID;

    r->upstream->peer.data = request_data;

    dd2("_init_overload_peer(r=%p, us=%p): exiting --> returned NGX_OK", r, us);
    return NGX_OK;
}

// called by nginx to determine which backend should receive this request
ngx_int_t
ngx_http_upstream_get_overload_peer(
    ngx_peer_connection_t *pc,
    void *data)
{
    ngx_http_upstream_overload_request_data_t *request_data = data;
    ngx_http_upstream_overload_peer_state_t *peer_state = request_data->peer_state;
    ngx_http_upstream_overload_peer_t *peer;

    dd_log2(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_get_overload_peer(pc=%p, request_data=%p): entering", pc, request_data);

    ngx_spinlock(&peer_state->lock, SPINLOCK_VALUE, SPINLOCK_NUM_SPINS);

    #if FINE_DEBUG == 1
        DO_SLOW_DOWN();
    #endif

    dd_list(&peer_state->idle_list, "idle_list", peer_state);
    dd_list(&peer_state->busy_list, "busy_list", NULL);

    // grab a peer from the idle list
    request_data->peer_index = ngx_peer_list_pop(&peer_state->idle_list, "idle_list", pc->log);

    if (request_data->peer_index == NGX_PEER_INVALID) {
        dd_log2(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_get_overload_peer(pc=%p, request_data=%p): No peers available; cannot forward request.\n\n", pc, request_data);

        send_overload_alert(peer_state, peer_state->busy_list.head, pc->log);

        ngx_unlock(&peer_state->lock);
        return NGX_BUSY;
    }

    peer = &peer_state->peer[request_data->peer_index];

    // push the peer onto the busy list
    ngx_peer_list_push(&peer_state->busy_list, "busy_list", peer, pc->log);

    dd_list(&peer_state->idle_list, "idle_list", peer_state);
    dd_list(&peer_state->busy_list, "busy_list", NULL);

    dd_log4(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_get_overload_peer(pc=%p, request_data=%p): peer_state->idle_list.len=%d, overload_conf.num_spare_backends=%d\n\n",
        pc, request_data, peer_state->idle_list.len, overload_conf.num_spare_backends);
    if (peer_state->idle_list.len <= overload_conf.num_spare_backends) {
        send_overload_alert(peer_state, peer_state->busy_list.head, pc->log);
    }

    ngx_unlock(&peer_state->lock);

    // the whole point of this function is to set these three values
    pc->sockaddr = peer->peer_config->sockaddr;
    pc->socklen = peer->peer_config->socklen;
    pc->name = &peer->peer_config->name;

    dd_log3(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_get_overload_peer(pc=%p, request_data=%p): exiting with peer_index==%d", pc, request_data, request_data->peer_index);

    return NGX_OK;
}

// called by nginx after a request completes or fails
void
ngx_http_upstream_free_overload_peer(
    ngx_peer_connection_t *pc,
    void *data,
    ngx_uint_t connection_state)
{
    ngx_http_upstream_overload_request_data_t *request_data = data;
    ngx_http_upstream_overload_peer_state_t *peer_state = request_data->peer_state;
    ngx_http_upstream_overload_peer_t *peer;
    ngx_uint_t peer_index = request_data->peer_index;

    dd_log3(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_free_overload_peer(pc=%p, request_data=%p, connection_state=%d): entering",
        pc, request_data, connection_state);

    // If the _get_overload_peer() invocation yielded NGX_BUSY
    if (peer_index == NGX_PEER_INVALID) {
        dd3("_free_overload_peer(pc=%p, request_data=%p, connection_state=%d): peer_index == NGX_PEER_INVALID --> exiting", pc, request_data, connection_state);
        return;
    }

    peer = &peer_state->peer[peer_index];

    dd_log4(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_free_overload_peer(pc=%p, request_data=%p, connection_state=%d): peer_index==%d",
        pc, request_data, connection_state, peer_index);

    ngx_spinlock(&peer_state->lock, SPINLOCK_VALUE, SPINLOCK_NUM_SPINS);

    dd_list(&peer_state->idle_list, "idle_list", peer_state);
    dd_list(&peer_state->busy_list, "busy_list", NULL);

    // remove the peer from the busy list
    ngx_peer_list_remove(&peer_state->busy_list, "busy_list", peer, pc->log);

    // push the peer onto the idle list
    ngx_peer_list_push(&peer_state->idle_list, "idle_list", peer, pc->log);

    dd_list(&peer_state->idle_list, "idle_list", peer_state);
    dd_list(&peer_state->busy_list, "busy_list", NULL);

    ngx_unlock(&peer_state->lock);

    pc->tries = 0;

    dd_log3(NGX_LOG_DEBUG_HTTP, pc->log, 0, "_free_overload_peer(pc=%p, request_data=%p, connection_state=%d): exiting",
        pc, request_data, connection_state);
}

