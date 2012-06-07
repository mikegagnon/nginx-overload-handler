#!/usr/bin/env python
#
# Copyright 2012 HellaSec, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==== puzzle_solver_test.py ====
#

import unittest
from puzzle_solver import *

class Test_PuzzleSolver(unittest.TestCase):

    puzzle1 = '''
<html>
    <head>
        <!-- right now assumes only re-directing to get requests -->
        <script type="text/javascript" src="/puzzle_static/md5.js"></script>
        <script type="text/javascript" src="/puzzle_static/puzzle.js"></script>
    </head>
    <body>
        <p>You will be re-directed shortly. </p>

        <p>Loading <span id ="redirect_status">0</span>%</p>
        <script type="text/javascript">
            var request = "/index.php"
            var request1= "/index.php"
            var request2="/index.php"
            var request3="/index.php";
            var request4="/index.php" ;
            var request5 = "/index.php";
            var request6 = "/index.php" ;
            var request7 = '/index.php';
            var request8='/index.php' ;

            var args = ""
            if (args != "") {
                request += "?" + args
            }
            var y = "fde5e1d0aa7504846b60d1fecbfb2c9c";
            var trunc_x = "7cc4a888000000000000000000000000";
            var bits = 99;
            var expire = "1338996785";
            var burst_len = 1;
            var sleep_time = 100;
            var func = function() {
                solve_puzzle(request, y, trunc_x, 0, bits, burst_len, sleep_time, expire, args);
            };
            setTimeout(func, sleep_time);
        </script>
    </body>
</html>
    '''

    solution2 = '/index.php?key=fe8b5b0b5dd14b495f75ec4ec33ba619&expire=1339029905'
    puzzle2 = '''
<html>
    <head>
        <!-- right now assumes only re-directing to get requests -->
        <script type="text/javascript" src="/puzzle_static/md5.js"></script>
        <script type="text/javascript" src="/puzzle_static/puzzle.js"></script>
    </head>
    <body>
        <p>You will be re-directed shortly. </p>
        <p>Loading <span id ="redirect_status">0</span>%</p>
        <script type="text/javascript">
            var request = "/index.php"
            var args = ""
            if (args != "") {
                request += "?" + args
            }
            var y = "ddfeb4973fbe79b616ae1d29a0c3f8fb";
            var trunc_x = "fe8b5b0b5dd14b495f75ec4ec33ba618";
            var bits = 3;
            var expire = "1339029905";
            var burst_len = 2;
            var sleep_time = 1;
            var func = function() {
                solve_puzzle(request, y, trunc_x, 0, bits, burst_len, sleep_time, expire, args);
            };
            setTimeout(func, sleep_time);
        </script>
    </body>
</html>

'''

    def test_get_val(self):
        val = PuzzleSolver.get_val(Test_PuzzleSolver.puzzle1)
        self.assertEquals(val["request"], "/index.php")
        for i in range(1, 9):
            self.assertEquals(val["request"], val["request%d" % i])
        self.assertEquals(val["args"], "")
        self.assertEquals(val["y"], "fde5e1d0aa7504846b60d1fecbfb2c9c")
        self.assertEquals(val["trunc_x"], "7cc4a888000000000000000000000000")
        self.assertEquals(val["bits"], 99)
        self.assertEquals(val["expire"], "1338996785")
        self.assertEquals(val["burst_len"], 1)
        self.assertEquals(val["sleep_time"], 100)

    def test_increment(self):
        self.assertEqual(PuzzleSolver.increment("00"), "01")
        self.assertEqual(PuzzleSolver.increment("01"), "02")
        self.assertEqual(PuzzleSolver.increment("09"), "0a")
        self.assertEqual(PuzzleSolver.increment("0a"), "0b")
        self.assertEqual(PuzzleSolver.increment("0f"), "10")
        self.assertEqual(PuzzleSolver.increment("fe"), "ff")
        self.assertEqual(PuzzleSolver.increment("ff"), "00")

    def test_solve(self):
        solver = PuzzleSolver(Test_PuzzleSolver.puzzle2)
        self.assertEqual(solver.solve(), Test_PuzzleSolver.solution2)

if __name__ == '__main__':
    unittest.main()
