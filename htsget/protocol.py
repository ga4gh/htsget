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
Sans IO protocol handling code to the GA4GH streaming API.
"""
from __future__ import division
from __future__ import print_function

import base64

from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlunparse
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import parse_qs


class TicketRequest(object):
    """
    TODO document.
    """
    def __init__(
            self, url, fmt=None, reference_name=None, reference_md5=None,
            start=None, end=None, fields=None, tags=None, notags=None):
        parsed_url = urlparse(url)
        get_vars = parse_qs(parsed_url.query)
        # TODO error checking
        if fmt is not None:
            get_vars["format"] = fmt.upper()
        if reference_name is not None:
            get_vars["referenceName"] = reference_name
        if reference_md5 is not None:
            get_vars["referenceMd5"] = reference_md5
        if start is not None:
            get_vars["start"] = int(start)
        if end is not None:
            get_vars["end"] = int(end)
        # TODO test these.
        # if fields is not None:
        #     get_vars["fields"] = ",".join(fields)
        # if tags is not None:
        #     get_vars["tags"] = ",".join(tags)
        # if notags is not None:
        #     get_vars["notags"] = ",".join(notags)
        new_url = list(parsed_url)
        new_url[4] = urlencode(get_vars, doseq=True)
        self.url = urlunparse(new_url)


class ChunkRequest(object):
    """
    A chunk is a single retryable chunk of the data slice requested by
    the client. It corresponds to a single URL provided by the ticket
    server.
    """
    def __init__(self, parsed_url):
        self.parsed_url = parsed_url
        self.url = urlunparse(parsed_url)

    def __repr__(self):
        return "<{}(url='{}')>".format(type(self).__name__, self.url)

    def run(self, output_file):
        raise NotImplementedError()


class HttpChunkRequest(ChunkRequest):
    """
    A chunk that is to be obtained from a HTTP resource.
    """
    def __init__(self, parsed_url, headers):
        super(HttpChunkRequest, self).__init__(parsed_url)
        self.headers = headers

    def __repr__(self):
        return "<{}(url='{}', headers='{}')>".format(
            type(self).__name__, self.url, self.headers)


class DataUriChunkRequest(ChunkRequest):
    """
    A chunk that is obtained directly from a data URI.
    """
    def __init__(self, parsed_url):
        super(DataUriChunkRequest, self).__init__(parsed_url)
        # TODO parse out the encoding properly.
        split = parsed_url.path.split(",", 1)
        self.data = base64.b64decode(split[1])

    def run(self, output_file):
        output_file.write(self.data)


class SliceRequest(object):
    """
    A slice request corresponds to a single data request for a
    (reference_name, start, end) slice in the data. Each slice is composed
    of one of more chunks which must be concatenated together to obtain
    the resulting data.
    """
    def __init__(self, ticket, http_chunk_request_class):
        self.format = ticket.get("format", "BAM")
        self.md5 = ticket.get("md5", None)
        self.chunk_requests = []
        for url_object in ticket["urls"]:
            url = urlparse(url_object["url"])
            if url.scheme.startswith("http"):
                headers = url_object.get("headers", "")
                self.chunk_requests.append(http_chunk_request_class(url, headers))
            elif url.scheme == "data":
                self.chunk_requests.append(DataUriChunkRequest(url))
            else:
                raise ValueError("Unsupported URL scheme:{}".format(url.scheme))

    def run(self, output_file):
        for chunk_request in self.chunk_requests:
            chunk_request.run(output_file)

    def __repr__(self):
        return "<{}(format='{}', md5={}, chunk_requests={}>".format(
            type(self).__name__, self.format, self.md5, self.chunk_requests)
