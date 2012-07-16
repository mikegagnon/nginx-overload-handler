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
 * ==== RPC interface for Signature Service ====
 *
 * This file specifies the interface between the alert_router and
 * the Signature Service
 *
 * See also README.txt.
 *
 */

service SignatureService {

    /**
     * a notification that request_str was evicted
     */
    oneway void evicted(1: string request_str)

    /**
     * a notification that request_str completed successfully
     */
    oneway void completed(1: string request_str)

}

