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
import json
import logging
import time

from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlunparse
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import parse_qs

import htsget.exceptions as exceptions

TICKET_ROOT_KEY = "htsget"


def ticket_request_url(
        url, fmt=None, reference_name=None, reference_md5=None,
        start=None, end=None, fields=None, tags=None, notags=None,
        data_format=None):
    parsed_url = urlparse(url)
    get_vars = parse_qs(parsed_url.query)
    # TODO error checking
    if reference_name is not None:
        get_vars["referenceName"] = reference_name
    if reference_md5 is not None:
        get_vars["referenceMD5"] = reference_md5
    if start is not None:
        get_vars["start"] = int(start)
    if end is not None:
        get_vars["end"] = int(end)
    if data_format is not None:
        get_vars["format"] = data_format.upper()
    # if fields is not None:
    #     get_vars["fields"] = ",".join(fields)
    # if tags is not None:
    #     get_vars["tags"] = ",".join(tags)
    # if notags is not None:
    #     get_vars["notags"] = ",".join(notags)
    new_url = list(parsed_url)
    new_url[4] = urlencode(get_vars, doseq=True)
    return urlunparse(new_url)


def parse_ticket(json_text):
    """
    Parses the specified ticket response and returns a dictionary of the
    contents of the root 'htsget' element.
    """
    try:
        parsed = json.loads(json_text)
    except ValueError as ve:
        raise exceptions.InvalidJsonError(ve)
    if TICKET_ROOT_KEY not in parsed:
        raise exceptions.MalformedJsonError()
    return parsed[TICKET_ROOT_KEY]


class DownloadManager(object):
    """
    Abstract implementation of the protocol.
    """

    def __init__(
            self, url, output, data_format=None, reference_name=None,
            reference_md5=None, start=None, end=None, fields=None, tags=None,
            notags=None, max_retries=5, timeout=10, retry_wait=5, bearer_token=None,
            headers=None):
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_wait = retry_wait
        self.bearer_token = bearer_token
        self.headers = headers
        self.output = output
        self.ticket_request_url = ticket_request_url(
            url, data_format=data_format, reference_name=reference_name,
            reference_md5=reference_md5, start=start, end=end, fields=fields,
            tags=tags, notags=notags)
        self.ticket = None
        self.data_format = format
        self.md5 = None

    def __retry(self, method, *args):
        completed = False
        num_retries = 0
        position_before = None
        try:
            # stdout does not support seek/tell, so we disable retry if this fails
            position_before = self.output.tell()
        except IOError:
            pass
        while not completed:
            try:
                method(*args)
                completed = True
            except exceptions.RetryableError as re:
                if position_before is not None and num_retries < self.max_retries:
                    num_retries += 1
                    sleep_time = self.retry_wait  # TODO exponential backoff
                    logging.warning(
                        "Error: '{}' occured; sleeping {}s before retrying "
                        "(attempt={})".format(re, sleep_time, num_retries))
                    self.output.seek(position_before)
                    time.sleep(sleep_time)
                else:
                    raise re

    def _ticket_request(self):
        raise NotImplementedError()

    def _handle_data_uri(self, parsed_url):
        split = parsed_url.path.split(",", 1)
        # TODO parse out the encoding properly.
        description = split[0]
        data = base64.b64decode(split[1])
        logging.debug("handle_data_uri({}, length={})".format(description, len(data)))
        self.output.write(data)

    def _handle_http_url(url, headers):
        raise NotImplementedError()

    def run(self):
        self.__retry(self._handle_ticket_request)
        self.data_format = self.ticket.get("format", "BAM")
        self.md5 = self.ticket.get("md5", None)
        for url_object in self.ticket["urls"]:
            url = urlparse(url_object["url"])
            if url.scheme.startswith("http"):
                headers = url_object.get("headers", "")
                self.__retry(self._handle_http_url, urlunparse(url), headers)
            elif url.scheme == "data":
                self._handle_data_uri(url)
            else:
                raise ValueError("Unsupported URL scheme:{}".format(url.scheme))
