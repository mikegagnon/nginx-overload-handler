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
 * ==== RPC interface for Bouncer ====
 *
 * This file specifies the interface between the alert_router and
 * the Bouncer process managers.
 *
 * See also README.txt.
 *
 */

// Bouncer process managers must implement this inteface
service BouncerService {

    /**
     * Called by alert_router
     *
     * the alert method is called when there is an overload and
     * a FastCGI worker must therefore be killed. alert_message
     * identifies which FastCGI worker to kill. alert_message follows
     * the following format: 'ip_address:port', which contains
     * the ip_address and the port of the FastCGI worker to be killed.
     * For example '127.0.0.1:9002' specifies to kill the FastCGI worker
     * that is listening on port 9002.
     */
    oneway void alert(1: string alert_message)

    /**
     * Called by alert_router
     *
     * the heartbeat method is called periodically in order to ensure
     * that there is a good connection to the Bouncer.
     * It is also used to ensure that the Bouncer's configuration matches
     * the Alert Router's configuration.
     *
     * The first time a Bouncer instance receives a call to heartbeat()
     * it should return a list of workers it is configured to handle.
     * The alert_router should check this result to make sure it matches
     * it's configuration.
     *
     * On subsequent calls to heartbeat, the Bouncer should return the
     * empty list.
     *
     */
    list<string> heartbeat()

    /**
     * Called by the bouncer itself.
     *
     * For each worker, the bouncer spawns a thread to monitor that worker.
     * When that worker terminates, the montioring thread calls workerCrashed
     * to notify the bouncer that the worker terminated.
     *
     * TODO: Presently anyone can make this call, even though it is really
     * private to the bouncer. Figure out if there is a way to make it
     * officially "private." Otherwise this is probably fine.
     */
    oneway void workerTerminated(1: string worker)
}

