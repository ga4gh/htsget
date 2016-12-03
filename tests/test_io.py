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
Test cases for the io handling code.
"""
from __future__ import print_function
from __future__ import division

import tempfile
import unittest

import mock

import htsget


class MockedResponse(object):
    """
    Mocked response object for requests.
    """
    def __init__(self, ticket, data):
        self.ticket = ticket
        self.headers = {}
        self.data = data

    def json(self):
        return self.ticket

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        yield self.data


class MockedRequestsTest(unittest.TestCase):
    """
    Test cases where we mock out requests.get.
    """

    def test_simple_case(self):
        ticket_url = "http://ticket.com"
        data_url = "http://data.url.com"
        headers = {"a": "a", "xyz": "ghj"}
        ticket = {"urls": [
            {"url": data_url, "headers": headers}
        ]}
        data = b"0" * 1024
        returned_response = MockedResponse(ticket, data)
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                htsget.get(ticket_url, f)
                f.seek(0)
                self.assertEqual(f.read(), data)
            self.assertEqual(mocked_get.call_count, 2)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(args[0], data_url)
            self.assertEqual(kwargs["headers"], headers)
            self.assertEqual(kwargs["stream"], True)
