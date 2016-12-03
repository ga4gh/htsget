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
Test cases using a simple HTTP server running locally.
"""
from __future__ import print_function
from __future__ import division

import json
import tempfile
import threading
import unittest

from six.moves import BaseHTTPServer
from six.moves import socketserver

import htsget


class TestServer(socketserver.TCPServer):
    allow_reuse_address = True

    def shutdown(self):
        self.socket.close()
        socketserver.TCPServer.shutdown(self)


class TestRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Silence the logger.
        pass

    def do_GET(self):
        if self.path == "/ticket":
            self.send_response(200)
            self.end_headers()
            urls = [
                # FIXME
                {"url": "http://localhost:6160" + url}
                for url in self.server.test_data_map.keys()]
            ticket = {
                "urls": urls
            }
            self.wfile.write(json.dumps(ticket).encode())
        elif self.path in self.server.test_data_map:
            self.send_response(200)
            self.end_headers()
            data = self.server.test_data_map[self.path]
            self.wfile.write(data.encode())
        else:
            self.send_response(404)


class TestStuff(unittest.TestCase):

    port = 6160
    ticket_url = "http://localhost:{}/ticket".format(port)

    @classmethod
    def setup_class(cls):
        cls.httpd = TestServer(("", cls.port), TestRequestHandler)
        cls.httpd_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.httpd_thread.setDaemon(True)
        cls.httpd_thread.start()

    @classmethod
    def teardown_class(cls):
        cls.httpd.shutdown()
        cls.httpd_thread.join()

    def test_stuff(self):
        data_map = {
            "/data1/".format(self.port): "data1",
            "/data2/".format(self.port): "data2",
        }
        self.httpd.test_data_map = data_map
        with tempfile.TemporaryFile("wb+") as f:
            htsget.get(self.ticket_url, f, max_retries=0)
            f.seek(0)
            all_data = "".join(data_map.values()).encode()
            self.assertEqual(f.read(), all_data)
