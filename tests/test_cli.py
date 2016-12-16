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

import logging
import os
import sys
import tempfile
import unittest

import mock

import htsget.cli as cli
import htsget.exceptions as exceptions


class TestMain(unittest.TestCase):
    """
    Simple tests for the main function.
    """
    with mock.patch("htsget.cli.run") as mocked_run, \
            mock.patch("argparse.ArgumentParser.parse_args") as mocked_parse:
        cli.htsget_main()
        mocked_parse.assert_called_once()
        mocked_run.assert_called_once()


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
        self.assertEqual(args.reference_md5, None)
        self.assertEqual(args.start, None)
        self.assertEqual(args.end, None)
        self.assertEqual(args.output, None)
        self.assertEqual(args.max_retries, 5)
        self.assertEqual(args.retry_wait, 5)
        self.assertEqual(args.timeout, 10)


class TestHtsgetRun(unittest.TestCase):
    """
    Tests to ensure the run function correctly passes along parameters.
    """

    def setUp(self):
        fd, self.output_filename = tempfile.mkstemp(prefix="htsget_cli_test_")
        os.close(fd)

    def tearDown(self):
        os.unlink(self.output_filename)

    def run_cmd(self, cmd):
        parser = cli.get_htsget_parser()
        args = parser.parse_args(cmd.split())
        with mock.patch("htsget.get") as mocked_get, \
                mock.patch("sys.exit") as mocked_exit:
            cli.run(args)
            self.assertEqual(mocked_get.call_count, 1)
            mocked_exit.assert_called_once_with(0)
            return mocked_get.call_args

    def test_defaults(self):
        url = "http://example.com/stuff"
        args, kwargs = self.run_cmd("{}".format(url))
        self.assertEqual(args[0], url)
        self.assertEqual(kwargs["start"], None)
        self.assertEqual(kwargs["end"], None)
        self.assertEqual(kwargs["reference_name"], None)
        self.assertEqual(kwargs["reference_md5"], None)
        self.assertEqual(kwargs["data_format"], None)

    def test_defaults_with_file(self):
        url = "http://example.com/stuff"
        args, kwargs = self.run_cmd("{} -O {}".format(url, self.output_filename))
        self.assertEqual(args[0], url)
        self.assertEqual(args[1].name, self.output_filename)
        self.assertEqual(kwargs["start"], None)
        self.assertEqual(kwargs["end"], None)
        self.assertEqual(kwargs["reference_name"], None)
        self.assertEqual(kwargs["reference_md5"], None)

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
            self.assertEqual(kwargs["reference_md5"], None)

            args, kwargs = self.run_cmd("{} -O {} --reference-name {}".format(
                url, self.output_filename, reference_name))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["start"], None)
            self.assertEqual(kwargs["end"], None)
            self.assertEqual(kwargs["reference_name"], reference_name)
            self.assertEqual(kwargs["reference_md5"], None)

    def test_reference_md5(self):
        url = "http://example.com/otherstuff"
        reference_md5 = "d7866be4ab9deb8b26d38a978b0684e3"
        args, kwargs = self.run_cmd("{} -O {} -m {}".format(
            url, self.output_filename, reference_md5))
        self.assertEqual(args[0], url)
        self.assertEqual(args[1].name, self.output_filename)
        self.assertEqual(kwargs["start"], None)
        self.assertEqual(kwargs["end"], None)
        self.assertEqual(kwargs["reference_name"], None)
        self.assertEqual(kwargs["reference_md5"], reference_md5)

        args, kwargs = self.run_cmd("{} -O {} --reference-md5 {}".format(
            url, self.output_filename, reference_md5))
        self.assertEqual(args[0], url)
        self.assertEqual(args[1].name, self.output_filename)
        self.assertEqual(kwargs["start"], None)
        self.assertEqual(kwargs["end"], None)
        self.assertEqual(kwargs["reference_name"], None)
        self.assertEqual(kwargs["reference_md5"], reference_md5)

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

    def test_format(self):
        url = "http://example.com/otherstuff"
        for fmt in ["bam", "CRAM", "anything"]:
            args, kwargs = self.run_cmd("{} -O {} -f {}".format(
                url, self.output_filename, fmt))
            self.assertEqual(args[0], url)
            self.assertEqual(args[1].name, self.output_filename)
            self.assertEqual(kwargs["data_format"], fmt)

    def test_max_retries(self):
        url = "http://example.com/otherstuff"
        for max_retries in [0, 5, 10]:
            args, kwargs = self.run_cmd("{} -O {} -M {}".format(
                url, self.output_filename, max_retries))
            kwargs["max_retries"] = max_retries

            args, kwargs = self.run_cmd("{} -O {} --max-retries {}".format(
                url, self.output_filename, max_retries))
            kwargs["max_retries"] = max_retries

    def test_retry_wait(self):
        url = "http://example.com/otherstuff"
        for retry_wait in [0, 5, 10, 1.4]:
            args, kwargs = self.run_cmd("{} -O {} -W {}".format(
                url, self.output_filename, retry_wait))
            kwargs["retry_wait"] = retry_wait

            args, kwargs = self.run_cmd("{} -O {} --retry-wait {}".format(
                url, self.output_filename, retry_wait))
            kwargs["retry_wait"] = retry_wait

    def test_timeout(self):
        url = "http://example.com/otherstuff"
        for timeout in [0, 5, 10, 1.4]:
            args, kwargs = self.run_cmd("{} -O {} -r {}".format(
                url, self.output_filename, timeout))
            kwargs["timeout"] = timeout

            args, kwargs = self.run_cmd("{} -O {} --timeout {}".format(
                url, self.output_filename, timeout))
            kwargs["timeout"] = timeout

    def test_stdout_zero_retries(self):
        url = "http://example.com/stuff"
        args, kwargs = self.run_cmd("{}".format(url))
        self.assertEqual(args[0], url)
        self.assertEqual(kwargs["max_retries"], 0)

        # this is true even if we specify it explicitly
        args, kwargs = self.run_cmd("{} --max-retries 10".format(url))
        self.assertEqual(args[0], url)
        self.assertEqual(kwargs["max_retries"], 0)


class TestVerbosity(unittest.TestCase):
    """
    Tests to ensure the verbosity settings work.
    """
    def run_cmd(self, cmd):
        parser = cli.get_htsget_parser()
        args = parser.parse_args(cmd.split())
        with mock.patch("htsget.get") as mocked_get, \
                mock.patch("sys.exit") as mocked_exit, \
                mock.patch("logging.basicConfig") as mocked_log_config:
            cli.run(args)
            self.assertEqual(mocked_get.call_count, 1)
            self.assertEqual(mocked_log_config.call_count, 1)
            mocked_exit.assert_called_once_with(0)
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


class TestRuntimeErrors(unittest.TestCase):
    """
    Test cases to cover the various error conditions that may occur at runtime.
    """
    def assert_exception_writes_error_message(self, exception, message):
        parser = cli.get_htsget_parser()
        args = parser.parse_args(["https://some.url"])
        saved_stderr = sys.stderr
        try:
            with tempfile.TemporaryFile("w+") as tmp_stderr:
                sys.stderr = tmp_stderr
                with mock.patch("htsget.get") as mocked_get, \
                        mock.patch("sys.exit") as mocked_exit, \
                        mock.patch("logging.basicConfig"):
                    mocked_get.side_effect = exception
                    cli.run(args)
                tmp_stderr.seek(0)
                stderr = tmp_stderr.read().strip()
                mocked_exit.assert_called_once_with(1)
        finally:
            sys.stderr = saved_stderr
        self.assertTrue(stderr.endswith(message))

    def test_keyboard_interrupt(self):
        self.assert_exception_writes_error_message(KeyboardInterrupt, "interrupted")

    def test_exception_wrapper(self):
        msg = "some message"
        self.assert_exception_writes_error_message(
            exceptions.ExceptionWrapper(Exception(msg)), msg)

    def test_htsget_exception(self):
        msg = "some other message"
        self.assert_exception_writes_error_message(exceptions.HtsgetException(msg), msg)
