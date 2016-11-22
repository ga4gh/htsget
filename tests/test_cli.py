#
# Copyright 2016 University of Oxford
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Test cases for the htsget CLI.
"""
from __future__ import print_function
from __future__ import division

import unittest

import htsget.cli as cli


class TestHtsgetArgumentParser(unittest.TestCase):
    """
    Tests the parser to ensure it parses input values correctly.
    """
    def parse_args(self, args):
        parser = cli.get_htsget_parser()
        return parser.parse_args(args)

    def test_defaults(self):
        args = self.parse_args(["URL", "ID"])
        self.assertEqual(args.url, "URL")
        self.assertEqual(args.id, "ID")
        self.assertEqual(args.format, None)
        self.assertEqual(args.reference_name, None)
        self.assertEqual(args.start, None)
        self.assertEqual(args.end, None)
        self.assertEqual(args.output, None)
