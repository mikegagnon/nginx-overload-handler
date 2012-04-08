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

exception BouncerException {
    1: string message
}

// Bouncer process managers must implement this inteface
service BouncerService {

    /**
     * the alert method is called when there is an overload and
     * a FastCGI worker must therefore be killed. alert_message
     * identifies which FastCGI worker to kill. alert_message follows
     * the following format: 'ip_address:port', which contains
     * the ip_address and the port of the FastCGI worker to be killed.
     * For example '127.0.0.1:9002' specifies to kill the FastCGI worker
     * that is listening on port 9002.
     * The Bouncer must throw a BouncerExcpetion if the worker is not
     * successfully killed
     */
    void alert(1: string alert_message) throws (1:BouncerException be),

    /**
     * the heartbeat method is called periodically in order to ensure
     * that there is a good connection to the Bouncer.
     * the Bouncer service must return "OK"
     */
    string heartbeat()
}

