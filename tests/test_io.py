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
Test cases for the io handling code.
"""
from __future__ import print_function
from __future__ import division

import json
import tempfile
import unittest

import mock

import htsget
import htsget.exceptions as exceptions


class MockedResponse(object):
    """
    Mocked response object for requests.
    """
    def __init__(self, ticket, data):
        self.headers = {}
        self.data = data
        self.ticket = ticket
        self.ticket_served = False

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        if self.ticket_served:
            yield self.data
        else:
            yield self.ticket
            self.ticket_served = True


class MockedTicketResponse(object):
    """
    Mocked response for when we make a ticket request
    """
    def __init__(self, ticket, char_by_char=False):
        self.headers = {}
        self.ticket = ticket
        self.char_by_char = char_by_char

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        if self.char_by_char:
            yield self.ticket
        else:
            for j in range(len(self.ticket)):
                # Do this because getting a single value returns an integer
                char = self.ticket[j: j + 1]
                yield char


class MockedRequestsTest(unittest.TestCase):
    """
    Test cases where we mock out requests.get.
    """

    def test_simple_case(self):
        ticket_url = "http://ticket.com"
        data_url = "http://data.url.com"
        headers = {"a": "a", "xyz": "ghj"}
        ticket = {"htsget": {
            "urls": [{"url": data_url, "headers": headers}]}}
        data = b"0" * 1024
        returned_response = MockedResponse(json.dumps(ticket).encode(), data)
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

    def test_bearer_token(self):
        ticket_url = "http://ticket.com"
        ticket = {"htsget": {"urls": []}}
        bearer_token = "x" * 1024
        returned_response = MockedTicketResponse(json.dumps(ticket).encode())
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                htsget.get(ticket_url, f, bearer_token=bearer_token)
                f.seek(0)
                self.assertEqual(f.read(), b"")
            # Because we have no URLs in the returned ticked, it should be called
            # only once.
            self.assertEqual(mocked_get.call_count, 1)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(args[0], ticket_url)
            headers = {"Authorization": "Bearer {}".format(bearer_token)}
            self.assertEqual(kwargs["headers"], headers)
            self.assertEqual(kwargs["stream"], True)

    def test_no_bearer_token(self):
        ticket_url = "http://ticket.com"
        ticket = {"htsget": {"urls": []}}
        returned_response = MockedTicketResponse(json.dumps(ticket).encode())
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                htsget.get(ticket_url, f)
                f.seek(0)
                self.assertEqual(f.read(), b"")
            # Because we have no URLs in the returned ticked, it should be called
            # only once.
            self.assertEqual(mocked_get.call_count, 1)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(args[0], ticket_url)
            headers = {}
            self.assertEqual(kwargs["headers"], headers)
            self.assertEqual(kwargs["stream"], True)

    def test_ticket_char_by_char(self):
        # Tests the streaming code for the ticket response.
        ticket_url = "http://ticket.com"
        ticket = {"htsget": {"urls": []}, "padding": "X" * 10}
        returned_response = MockedTicketResponse(
                json.dumps(ticket).encode(), char_by_char=True)
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                htsget.get(ticket_url, f)
                f.seek(0)
                self.assertEqual(f.read(), b"")
            # Because we have no URLs in the returned ticked, it should be called
            # only once.
            self.assertEqual(mocked_get.call_count, 1)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(args[0], ticket_url)
            headers = {}
            self.assertEqual(kwargs["headers"], headers)
            self.assertEqual(kwargs["stream"], True)

    def test_leading_json_error(self):
        ticket_url = "http://ticket.com"
        ticket = (b" " * 100) + b"0" * 1024
        returned_response = MockedResponse(ticket, b"")
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                self.assertRaises(
                    exceptions.InvalidLeadingJsonError, htsget.get, ticket_url, f)
            self.assertEqual(mocked_get.call_count, 1)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(kwargs["headers"], {})
            self.assertEqual(kwargs["stream"], True)

    def test_undecodable_json(self):
        ticket_url = "http://ticket.com"
        ticket = bytearray([0xff] * 100)
        returned_response = MockedResponse(ticket, b"")
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                self.assertRaises(
                    exceptions.TicketDecodeError, htsget.get, ticket_url, f)
            self.assertEqual(mocked_get.call_count, 1)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(kwargs["headers"], {})
            self.assertEqual(kwargs["stream"], True)

    def test_empty_json_error(self):
        ticket_url = "http://ticket.com"
        ticket = b""
        returned_response = MockedResponse(ticket, b"")
        with mock.patch("requests.get", return_value=returned_response) as mocked_get:
            with tempfile.NamedTemporaryFile("wb+") as f:
                self.assertRaises(
                    exceptions.EmptyTicketError, htsget.get, ticket_url, f)
            self.assertEqual(mocked_get.call_count, 1)
            # Note that we only get the arguments for the last call using this method.
            args, kwargs = mocked_get.call_args
            self.assertEqual(kwargs["headers"], {})
            self.assertEqual(kwargs["stream"], True)
