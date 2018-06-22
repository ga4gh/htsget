#
# Copyright 2016-2017 University of Oxford
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
Test cases using a simple HTTP server running locally.
"""
from __future__ import print_function
from __future__ import division

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import platform

import mock
from six.moves import BaseHTTPServer
from six.moves import socketserver
from six.moves.urllib.parse import urljoin

import htsget
import htsget.exceptions as exceptions
import htsget.cli as cli

PORT = 6160
SERVER_URL = "http://localhost:{}".format(PORT)

IS_WINDOWS = platform.system() == "Windows"


class TestUrlInstance(object):
    def __init__(self, url, data, headers={}, error_code=None, truncate=False):
        self.url = url
        self.data = data
        self.headers = headers
        self.error_code = error_code
        self.truncate = truncate


class TestServer(socketserver.TCPServer):
    """
    A local test server designed to be run in a thread and shutdown smoothly
    for test cases.
    """
    allow_reuse_address = True
    # This is set by clients to contain the list of TestUrlInstance objects.
    test_instances = []

    def shutdown(self):
        self.socket.close()
        socketserver.TCPServer.shutdown(self)


class TestRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    ticket_path = "/ticket"
    ticket_url = urljoin(SERVER_URL, ticket_path)

    def log_message(self, format, *args):
        # Silence the logger.
        pass

    def do_GET(self):
        url_map = {instance.url: instance for instance in self.server.test_instances}
        if self.path == self.ticket_path:
            self.send_response(200)
            self.end_headers()
            urls = [
                {
                    "url": urljoin(SERVER_URL, test_instance.url),
                    "headers": test_instance.headers
                } for test_instance in self.server.test_instances]
            ticket = {"htsget": {"urls": urls}}
            self.wfile.write(json.dumps(ticket).encode())
        elif self.path in url_map:
            instance = url_map[self.path]
            if instance.error_code is not None:
                self.send_error(instance.error_code)
            else:
                self.send_response(200)
                self.send_header("Content-Length", len(instance.data))
                if instance.truncate:
                    self.end_headers()
                    self.wfile.write(instance.data[:-1])
                    self.wfile.flush()
                else:
                    self.end_headers()
                    self.wfile.write(instance.data)
        else:
            self.send_error(404)


class ServerTest(unittest.TestCase):
    """
    Superclass of tests needing a server running in a thread.
    """
    @classmethod
    def setup_class(cls):
        cls.httpd = TestServer(("", PORT), TestRequestHandler)

        def target():
            # Sometimes the server doesn't shutdown cleanly, but we don't
            # care here.
            try:
                cls.httpd.serve_forever()
            except ValueError:
                pass

        cls.httpd_thread = threading.Thread(target=target)
        cls.httpd_thread.start()

    @classmethod
    def teardown_class(cls):
        cls.httpd.shutdown()
        cls.httpd_thread.join()

    def setUp(self):
        self.output_file = tempfile.NamedTemporaryFile("wb+")


class TestDataTransfers(ServerTest):
    """
    Test cases for various data transfers.
    """
    def assert_data_transfer_ok(self, test_instances, max_retries=0):
        self.httpd.test_instances = test_instances
        htsget.get(
            TestRequestHandler.ticket_url, self.output_file, max_retries=max_retries)
        self.output_file.seek(0)
        all_data = b"".join(test_instance.data for test_instance in test_instances)
        self.assertEqual(self.output_file.read(), all_data)

    def test_simple_data(self):
        instances = [
            TestUrlInstance(url="/data1", data=b"data1"),
            TestUrlInstance(url="/data2", data=b"data2")
        ]
        self.assert_data_transfer_ok(instances)

    def test_binary_data(self):
        instances = []
        for j in range(10):
            instances.append(TestUrlInstance(
                url="/path/to/data/{}".format(j),
                data=bytes(j) * 1024))
        self.assert_data_transfer_ok(instances)

    def test_transfer_with_cli(self):
        test_instances = [
            TestUrlInstance(url="/data1", data=b"data1"),
            TestUrlInstance(url="/data2", data=b"data2")
        ]
        self.httpd.test_instances = test_instances
        try:
            fd, filename = tempfile.mkstemp()
            os.close(fd)
            cmd = [TestRequestHandler.ticket_url, "-O", filename]
            parser = cli.get_htsget_parser()
            args = parser.parse_args(cmd)
            with mock.patch("sys.exit") as mocked_exit:
                cli.run(args)
                mocked_exit.assert_called_once_with(0)
            all_data = b"".join(test_instance.data for test_instance in test_instances)
            with open(filename, "rb") as f:
                self.assertEqual(f.read(), all_data)
        finally:
            os.unlink(filename)

    def test_transfer_with_cli_stdout(self):
        test_instances = [
            TestUrlInstance(url="/data1", data=b"data1"),
            TestUrlInstance(url="/data2", data=b"data2")
        ]
        self.httpd.test_instances = test_instances
        saved = sys.stdout
        sys.stdout = self.output_file
        try:
            cmd = [TestRequestHandler.ticket_url]
            parser = cli.get_htsget_parser()
            args = parser.parse_args(cmd)
            with mock.patch("sys.exit") as mocked_exit:
                cli.run(args)
                mocked_exit.assert_called_once_with(0)
            all_data = b"".join(test_instance.data for test_instance in test_instances)
            self.output_file.seek(0)
            self.assertEqual(self.output_file.read(), all_data)
        finally:
            sys.stdout = saved


class TestSubprocessCli(ServerTest):
    """
    Runs some tests by forking a subprocess and calling the CLI directly.
    """
    def setUp(self):
        fd, self.output_file = tempfile.mkstemp()
        os.close(fd)
        test_instances = [
            TestUrlInstance(url="/data1", data=b"x" * 1024),
            TestUrlInstance(url="/data2", data=b"y" * 1024)
        ]
        self.stored_data = b"".join(instance.data for instance in test_instances)
        self.httpd.test_instances = test_instances

    def tearDown(self):
        os.unlink(self.output_file)

    def test_transfer_with_cli_file(self):
        cmd = [
            sys.executable, "htsget_dev.py", TestRequestHandler.ticket_url,
            "-O", self.output_file]
        subprocess.check_call(cmd)
        with open(self.output_file, "rb") as f:
            data = f.read()
        self.assertEqual(data, self.stored_data)

    def test_transfer_with_cli_stdout(self):
        cmd = [
            sys.executable, "htsget_dev.py", TestRequestHandler.ticket_url,
            "--max-retries", "0"]
        with open(self.output_file, "wb") as stdout:
            subprocess.check_call(cmd, stdout=stdout)
        with open(self.output_file, "rb") as f:
            data = f.read()
        self.assertEqual(data, self.stored_data)

    @unittest.skipIf(IS_WINDOWS, "Pipe tests don't make sense on windows")
    def test_transfer_with_cli_pipe(self):
        cmd = [
            sys.executable, "htsget_dev.py", TestRequestHandler.ticket_url,
            "--max-retries", "0", "| cat"]
        with open(self.output_file, "wb") as stdout:
            subprocess.check_call(" ".join(cmd), shell=True, stdout=stdout)
        with open(self.output_file, "rb") as f:
            data = f.read()
        self.assertEqual(data, self.stored_data)

    # TODO we should have a range of different errors here and verify that we
    # do actually print out the returned error message.
    def test_cli_error(self):
        cmd = [
            sys.executable, "htsget_dev.py", TestRequestHandler.ticket_url + "XXX",
            "-O", self.output_file]
        with tempfile.TemporaryFile("wb+") as stderr, \
                tempfile.TemporaryFile("wb+") as stdout:
            ret = subprocess.call(cmd, stderr=stderr, stdout=stdout)
            self.assertEqual(ret, 1)
            stderr.seek(0)
            stdout.seek(0)
            self.assertGreater(len(stderr.read()), 0)
            self.assertEqual(len(stdout.read()), 0)


class TestErrorHandling(ServerTest):
    """
    Test cases for the error handling in the client.
    """
    def test_missing_path(self):
        self.assertRaises(
            exceptions.ClientError, htsget.get, SERVER_URL + "/nopath",
            self.output_file, max_retries=0)

    def test_bad_port(self):
        self.assertRaises(
            exceptions.RetryableIOError, htsget.get, "http://localhost:66123",
            self.output_file, max_retries=0)

    def test_data_error(self):
        self.httpd.test_instances = [
            TestUrlInstance(url="/fail1", data=b"", error_code=500)
        ]
        self.assertRaises(
            exceptions.RetryableIOError, htsget.get,
            TestRequestHandler.ticket_url, self.output_file, max_retries=0)

    def test_authorisation_error(self):
        self.httpd.test_instances = [
            TestUrlInstance(url="/fail1", data=b"", error_code=401)
        ]
        self.assertRaises(
            exceptions.ClientError, htsget.get,
            TestRequestHandler.ticket_url, self.output_file, max_retries=0)

    def test_data_truncation(self):
        self.httpd.test_instances = [
            TestUrlInstance(url="/fail1", data=b"x" * 8192, truncate=True)
        ]
        self.assertRaises(
            exceptions.ContentLengthMismatch, htsget.get,
            TestRequestHandler.ticket_url, self.output_file, max_retries=0)
