"""
Test cases for the protocol handling code.
"""
from __future__ import print_function
from __future__ import division

import unittest

from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import parse_qs

import htsget.protocol as protocol

EXAMPLE_URL = "http://example.com"


class TestTicketRequestUrl(unittest.TestCase):
    """
    Tests the ticket request URL generator.
    """
    def test_defaults(self):
        url = protocol.ticket_request_url(EXAMPLE_URL)
        self.assertEqual(url, EXAMPLE_URL)

    def test_reference_name(self):
        full_url = protocol.ticket_request_url(
                "http://example.co.uk/path/to/resource", reference_name="1",
                start=2, end=100)
        parsed = urlparse(full_url)
        self.assertEqual(parsed.scheme, "http")
        self.assertEqual(parsed.netloc, "example.co.uk")
        self.assertEqual(parsed.path, "/path/to/resource")
        query = parse_qs(parsed.query)
        self.assertEqual(query["referenceName"], ["1"])
        self.assertEqual(query["start"], ["2"])
        self.assertEqual(query["end"], ["100"])
        self.assertEqual(len(query), 3)

    def test_reference_md5(self):
        md5 = "b9185d4fade27aa27e17f25fafec695f"
        full_url = protocol.ticket_request_url(
                "https://example.com/resource", reference_md5=md5)
        parsed = urlparse(full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "example.com")
        self.assertEqual(parsed.path, "/resource")
        query = parse_qs(parsed.query)
        self.assertEqual(query["referenceMd5"], [md5])
        self.assertEqual(len(query), 1)

    def test_url_scheme(self):
        full_url = protocol.ticket_request_url("http://a.com")
        self.assertEqual(urlparse(full_url).scheme, "http")
        full_url = protocol.ticket_request_url("https://a.com")
        self.assertEqual(urlparse(full_url).scheme, "https")

    def test_url_netloc(self):
        full_url = protocol.ticket_request_url("http://a.com")
        self.assertEqual(urlparse(full_url).netloc, "a.com")
        full_url = protocol.ticket_request_url("http://a.com/other/stuff")
        self.assertEqual(urlparse(full_url).netloc, "a.com")
        full_url = protocol.ticket_request_url("https://192.168.0.1")
        self.assertEqual(urlparse(full_url).netloc, "192.168.0.1")
        full_url = protocol.ticket_request_url("https://192.168.0.1:8080/xyz")
        self.assertEqual(urlparse(full_url).netloc, "192.168.0.1:8080")

    def test_url_path(self):
        full_url = protocol.ticket_request_url("http://a.com/path/to/resource")
        self.assertEqual(urlparse(full_url).path, "/path/to/resource")
        full_url = protocol.ticket_request_url("http://a.com/")
        self.assertEqual(urlparse(full_url).path, "/")
        full_url = protocol.ticket_request_url("http://a.com")
        self.assertEqual(urlparse(full_url).path, "")

    def test_embedded_query_strings(self):
        full_url = protocol.ticket_request_url("http://a.com/stuff?a=a&b=b")
        query = parse_qs(urlparse(full_url).query)
        self.assertEqual(query["a"], ["a"])
        self.assertEqual(query["b"], ["b"])

        full_url = protocol.ticket_request_url(
            "http://a.com/stuff?a=a&b=b", reference_name="123")
        query = parse_qs(urlparse(full_url).query)
        self.assertEqual(query["a"], ["a"])
        self.assertEqual(query["b"], ["b"])
        self.assertEqual(query["referenceName"], ["123"])


def get_http_ticket(url, headers={}):
    return {"url": url, "headers": headers}


def get_data_uri_ticket(url):
    return {"url": url}


def get_ticket(urls=[], format_=None, md5=None):
    d = {"urls": urls}
    if format_ is not None:
        d["format"] = format_
    if md5 is not None:
        d["md5"] = md5
    return d


class TestSliceRequest(unittest.TestCase):
    """
    Test cases for building a slice request object from a ticket response.
    """
    def test_bad_scheme(self):
        for bad_scheme in ["htt://as", "file:///home", "ftp://x.y/sdf"]:
            ticket = get_ticket(urls=[
                get_http_ticket("http://a.b"),
                get_http_ticket("htp")])
            self.assertRaises(ValueError, protocol.SliceRequest, ticket)

    def test_basic_http_parsing(self):
        headers = {"a": "b", "b": "c"}
        ticket = get_ticket(urls=[get_http_ticket("http://example.com", headers)])
        slice_request = protocol.SliceRequest(ticket)
        self.assertEqual(len(slice_request.chunk_requests), 1)
        chunk_request = slice_request.chunk_requests[0]
        self.assertIsInstance(chunk_request, protocol.HttpChunkRequest)
        self.assertEqual(chunk_request.parsed_url.scheme, "http")
        self.assertEqual(chunk_request.parsed_url.netloc, "example.com")
        self.assertEqual(chunk_request.headers, headers)

    def test_basic_data_uri_parsing(self):
        data_uri = "data:application/vnd.ga4gh.bam;base64,SGVsbG8sIFdvcmxkIQ=="
        ticket = get_ticket(urls=[get_data_uri_ticket(data_uri)])
        slice_request = protocol.SliceRequest(ticket)
        self.assertEqual(len(slice_request.chunk_requests), 1)
        chunk_request = slice_request.chunk_requests[0]
        self.assertIsInstance(chunk_request, protocol.DataUriChunkRequest)
        self.assertEqual(chunk_request.parsed_url.scheme, "data")
