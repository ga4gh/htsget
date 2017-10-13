#
# Copyright 2017 University of Oxford
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
Test cases for client error handling.
"""
from __future__ import print_function
from __future__ import division

import unittest
import tempfile

import mock
import requests

import htsget
import htsget.exceptions as exceptions


class MockedErrorResponse(object):
    """
    Mocked response object for requests.
    """
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.text = body

    def raise_for_status(self):
        raise requests.HTTPError()


class ClientErrorTest(unittest.TestCase):
    """
    Tests for client errors that may be raised by the server.
    """

    # TODO add some structured tests here to take the protocol error strings
    # and make sure we're presenting the contents in a reasonable manner.

    def test_404(self):
        body = "XXXX"
        returned_response = MockedErrorResponse(404, body)
        with mock.patch("requests.get", return_value=returned_response):
            with tempfile.TemporaryFile("wb+") as f:
                try:
                    htsget.get("http://some_url", f)
                except exceptions.ClientError as cse:
                    s = str(cse)
                    self.assertIn(body, s)
                else:
                    self.assertFalse(True)
