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
 * ==== puzzle.js ====
 */

// c is a single hex digit (string)
function inc_digit(c) {
    if (c == "9") {
        return "a";
    } else if (c == "f") {
        return "0";
    } else {
        return String.fromCharCode(c.charCodeAt() + 1)
    }
}

// x is a string of hex digits
function increment(x) {
    var i = x.length - 1;
    var carry;
    var new_x = x.split("");
    do {
        old_digit = x.charAt(i);
        new_digit = inc_digit(old_digit);
        new_x[i] = new_digit;
        if (new_digit == "0") {
            carry = true;
            i -= 1;
        } else {
            carry = false;
        }
        if (i < 0) {
            carry = false;
        }
    } while (carry);
    return new_x.join("");
}

// request is a url
function redirect(request, key, expire, args) {
    if (args == "") {
        url = request + "?";
    } else {
        url = request + "&";
    }
    url += "key=" + key + "&expire=" + expire;

    window.location = url;
}

// solves the puzzle (in bursts, with sleep time inbetween bursts)
// then calls redirect with the solution.
function solve_puzzle(request, y, x, tries, bits, burst_len, sleep_time, expire, args) {
    var hash_x;
    for (i = 0; i < burst_len; i++) {
        hash_x = hex_md5(x);
        if (hash_x == y) {
            redirect(request, x, expire, args);
            return;
        }
        x = increment(x);
    }
    tries += burst_len;
    percent_done = Math.floor((tries / Math.pow(2, bits)) * 100.0);
    if (percent_done <= 100) {
        document.getElementById("redirect_status").innerHTML = "" + Math.floor((tries / Math.pow(2, bits)) * 100.0);
        var func = function() {
            solve_puzzle(request, y, x, tries, bits, burst_len, sleep_time, expire, args);
        }
        setTimeout(func, sleep_time);
    } else {
        document.getElementById("redirect_status").innerHTML = "ERROR";
    }
}

