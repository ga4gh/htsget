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
import tempfile
import logging
import os

import mock

import htsget.cli as cli


class TestHtsgetArgumentParser(unittest.TestCase):
    """
    Tests the parser to ensure it parses input values correctly.
    """
    def parse_args(self, args):
        parser = cli.get_htsget_parser()
        return parser.parse_args(args)

    def test_defaults(self):
        args = self.parse_args(["URL"])
        self.assertEqual(args.url, "URL")
        self.assertEqual(args.format, None)
        self.assertEqual(args.reference_name, None)
        self.assertEqual(args.start, None)
        self.assertEqual(args.end, None)
        self.assertEqual(args.output, None)


class TestHtsgetRun(unittest.TestCase):

    def setUp(self):
        fd, self.output_filename = tempfile.mkstemp(prefix="htsget_cli_test_")
        os.close(fd)

    def tearDown(self):
        os.unlink(self.output_filename)

    def run_cmd(self, cmd):
        parser = cli.get_htsget_parser()
        args = parser.parse_args(cmd.split())
        with mock.patch("htsget.get") as mocked_get:
            cli.run(args)
            self.assertEqual(mocked_get.call_count, 1)
            return mocked_get.call_args

    def test_defaults(self):
        url = "http://example.com/stuff"
        args, kwargs = self.run_cmd("{} -O {}".format(url, self.output_filename))
        self.assertEqual(args[0], url)
        self.assertEqual(args[1].name, self.output_filename)
        self.assertEqual(kwargs["start"], None)
        self.assertEqual(kwargs["end"], None)
        self.assertEqual(kwargs["reference_name"], None)

    def test_reference_name(self):
        url = "http://example.com/otherstuff"
        for reference_name in ["chr1", "1", "x" * 100]:
            args, kwargs = self.run_cmd("{} -O {} -r {}".format(
                url, self.output_filename, reference_name))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], None)
            self.assertEqual(kwargs["end"], None)
            self.assertEqual(kwargs["reference_name"], reference_name)

            args, kwargs = self.run_cmd("{} -O {} --reference-name {}".format(
                url, self.output_filename, reference_name))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], None)
            self.assertEqual(kwargs["end"], None)
            self.assertEqual(kwargs["reference_name"], reference_name)

    def test_start(self):
        url = "http://example.com/otherstuff"
        reference_name = "chr2"
        for start in [0, 100, 2**32]:
            args, kwargs = self.run_cmd("{} -O {} -r {} -s {}".format(
                url, self.output_filename, reference_name, start))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], start)
            self.assertEqual(kwargs["end"], None)
            self.assertEqual(kwargs["reference_name"], reference_name)

            args, kwargs = self.run_cmd("{} -O {} -r {} --start {}".format(
                url, self.output_filename, reference_name, start))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], start)
            self.assertEqual(kwargs["end"], None)
            self.assertEqual(kwargs["reference_name"], reference_name)

    def test_end(self):
        url = "http://example.com/otherstuff"
        reference_name = "chr2"
        for end in [0, 100, 2**32]:
            args, kwargs = self.run_cmd("{} -O {} -r {} -e {}".format(
                url, self.output_filename, reference_name, end))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], None)
            self.assertEqual(kwargs["end"], end)
            self.assertEqual(kwargs["reference_name"], reference_name)

            args, kwargs = self.run_cmd("{} -O {} -r {} --end {}".format(
                url, self.output_filename, reference_name, end))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], None)
            self.assertEqual(kwargs["end"], end)
            self.assertEqual(kwargs["reference_name"], reference_name)

    def test_start_end(self):
        url = "http://example.com/otherstuff"
        reference_name = "chr2"
        for start, end in [(0, 1), (100, 200), (5, 2**32)]:
            args, kwargs = self.run_cmd("{} -O {} -r {} -s {} -e {}".format(
                url, self.output_filename, reference_name, start, end))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], start)
            self.assertEqual(kwargs["end"], end)
            self.assertEqual(kwargs["reference_name"], reference_name)


class TestVerbosity(unittest.TestCase):
    """
    Tests to ensure the verbosity settings work.
    """
    def run_cmd(self, cmd):
        parser = cli.get_htsget_parser()
        args = parser.parse_args(cmd.split())
        with mock.patch("htsget.get") as mocked_get, \
                mock.patch("logging.basicConfig") as mocked_log_config:
            cli.run(args)
            self.assertEqual(mocked_get.call_count, 1)
            self.assertEqual(mocked_log_config.call_count, 1)
            return mocked_log_config.call_args[1]["level"]

    def test_defaults(self):
        level = self.run_cmd("http://url.com")
        self.assertEqual(level, logging.WARNING)

    def test_repeats(self):
        level = self.run_cmd("http://url.com -v")
        self.assertEqual(level, logging.INFO)
        level = self.run_cmd("http://url.com --verbose")
        self.assertEqual(level, logging.INFO)
        level = self.run_cmd("http://url.com -vv")
        self.assertEqual(level, logging.DEBUG)
        level = self.run_cmd("http://url.com -v -v")
        self.assertEqual(level, logging.DEBUG)
        level = self.run_cmd("http://url.com --verbose --verbose")
        self.assertEqual(level, logging.DEBUG)
