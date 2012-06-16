/**
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
 * ==== upstream_overload module for nginx ====
 *
 * See README.txt for description of module and various instructions.
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

// TODO: Make this a config option
// Number of seconds in window used calculating stats
#define THROUGHPUT_WINDOW 20

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
    #define dd_list(list, name, peers, log) ngx_upstream_overload_print_list(list, name, peers, log)
#else
    #define dd_list(list, name, peers, log)
#endif

// Right now printf doesn't work because ngx_uint_t has different sizes on 32-bit and 64-bit
// TODO: If I get something like printf to work, then if FINE_DEBUG is on, then have ddX
// call the printf like function. This is only really useful for doing logging when there is no
// log object.
#define dd0(format)
#define dd1(format, a)
#define dd2(format, a, b)
#define dd3(format, a, b, c)
#define dd4(format, a, b, c, d)
#define dd5(format, a, b, c, d, e)
#define dd6(format, a, b, c, d, e, f)
#define dd7(format, a, b, c, d, e, f, g)

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

#define dd_log0(level, log, err, format)                                            \
    do {                                                                            \
        dd0(format);                                                                \
        if (log) ngx_log_debug0(level, log, err, "[" MODULE_NAME_STR "] " format);  \
    } while (0)

#define dd_log1(level, log, err, format, a)                                             \
    do {                                                                                \
        dd1(format, a);                                                                 \
        if (log) ngx_log_debug1(level, log, err, "[" MODULE_NAME_STR "] " format, a);   \
    } while (0)

#define dd_log2(level, log, err, format, a, b)                                              \
    do {                                                                                    \
        dd2(format, a, b);                                                                  \
        if (log) ngx_log_debug2(level, log, err, "[" MODULE_NAME_STR "] " format, a, b);    \
    } while (0)

#define dd_log3(level, log, err, format, a, b, c)                                               \
    do {                                                                                        \
        dd3(format, a, b, c);                                                                   \
        if (log) ngx_log_debug3(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c);     \
    } while (0)

#define dd_log4(level, log, err, format, a, b, c, d)                                            \
    do {                                                                                        \
        dd4(format, a, b, c, d);                                                                \
        if (log) ngx_log_debug4(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c, d);  \
    } while (0)

#define dd_log5(level, log, err, format, a, b, c, d, e)                                             \
    do {                                                                                            \
        dd5(format, a, b, c, d, e);                                                                 \
        if (log) ngx_log_debug5(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c, d, e);   \
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

#define dd_error3(level, log, err, format, a, b, c)                                 \
    do {                                                                            \
        dd3("          [ERROR] " format, a, b, c);                                  \
        ngx_log_error(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c);   \
    } while (0)

#define dd_error4(level, log, err, format, a, b, c, d)                                 \
    do {                                                                               \
        dd4("          [ERROR] " format, a, b, c, d);                                  \
        ngx_log_error(level, log, err, "[" MODULE_NAME_STR "] " format, a, b, c, d);   \
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

struct ngx_http_upstream_overload_peer_state_s;

extern struct ngx_http_upstream_overload_peer_state_s *upstream_overload_peer_state;

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

// Throughout the docmenation a request is said to be "admitted" if it reaches the load balancer;
// even if the request is rejected by the load balancer (because there are no idle backends)
// it's still considered "admitted." We use this terminolgy because the doorman "admits" requests
// and the load balancer "distributes" requests.
typedef struct {

    ngx_uint_t          window_size;

    // once ngx_time() != current_time it is time to advance window_i and update current_time
    time_t              current_time;

    ngx_uint_t          window_i;

    /**
     * Stats relating to number of evictions
     *******************************/

    // evicted[i] == the number of requests that were evicted during second i
    // sum(evicted) == the number of requests evicted in the past window_size seconds
    ngx_uint_t         *evicted;

    // == sum(evicted), updated every time evicted is updated
    ngx_uint_t          evicted_count;

    /**
     * Stats relating to number of rejected requests (because there are no idle upstream
     * workers)
     *******************************/

    ngx_uint_t         *rejected;
    ngx_uint_t          rejected_count;

    /**
     * Stats relating to throughput of requests
     *******************************/

    // NOTE: throughput_count - evicted_count == number of admissions that did not result in eviction
    // NOTE: throughput_count - rejection_count == number of admissions that did not result in rejection
    ngx_uint_t         *throughput;
    ngx_uint_t          throughput_count;

} ngx_http_upstream_overload_stats_t;



// There is only one instance of this struct
// It is mutable and exists in shared memory
struct ngx_http_upstream_overload_peer_state_s{

    /**
     * Fields needed to load balance
     *******************************************/

    // the array of mutable peers
    ngx_http_upstream_overload_peer_t   *peer;
    ngx_uint_t                           num_peers;

    // mutable lists of peers
    ngx_peer_list_t                      busy_list;
    ngx_peer_list_t                      idle_list;

    // overload alerts will be writtten to alert_pipe
    ngx_fd_t                             alert_pipe;
    ngx_atomic_t                         lock;

    /**
     * Streaming statistics
     *******************************************/
    ngx_http_upstream_overload_stats_t   stats;

};

typedef struct ngx_http_upstream_overload_peer_state_s ngx_http_upstream_overload_peer_state_t;

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

    // freed == 1 if this peer has already been free'd for this
    // request; freed == 0 otherwise. The freed field is only needed
    // because there is a bug in nginx that causes peer.free to be
    // be called multiple times for the same connection
    ngx_uint_t                           freed;

    // The index of the peer that is handling this request
    ngx_uint_t                           peer_index;
} ngx_http_upstream_overload_request_data_t;

/**
 * Function declarations
 *****************************************************************************/

// Call this whenever you want to update your stats
void
ngx_http_upstream_overload_update_stats(
    ngx_log_t *pc,
    ngx_http_upstream_overload_peer_state_t *state,
    ngx_uint_t evicted,     // 1 if you want to increment evicted (or 0 if not)
    ngx_uint_t rejected,    // 1 if you want to increment rejected (or 0 if not)
    ngx_uint_t throughput);  // 1 if you want to increment throughput (or 0 if not)

