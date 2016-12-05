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
Main interface for the htsget library.
"""
from __future__ import division
from __future__ import print_function

import logging

import htsget.protocol as protocol
import htsget.exceptions as exceptions

import requests

CONTENT_LENGTH = "Content-Length"


def get(
        url, output, reference_name=None, reference_md5=None,
        start=None, end=None, fields=None, tags=None, notags=None,
        data_format=None, max_retries=5, timeout=10, retry_wait=5):
    """
    Runs a request to the specified URL and write the resulting data to
    the specified file-like object.
    """
    manager = SynchronousDownloadManager(
        url, output, reference_name=reference_name,
        reference_md5=reference_md5, start=start, end=end, fields=fields, tags=tags,
        notags=notags, data_format=data_format, max_retries=max_retries, timeout=timeout,
        retry_wait=retry_wait)
    manager.run()


class SynchronousDownloadManager(protocol.DownloadManager):
    """
    Class implementing the GA4GH streaming API synchronously using the
    requests library.
    """
    def __get(self, *args, **kwargs):
        try:
            response = requests.get(*args, **kwargs)
        except requests.RequestException as re:
            raise exceptions.RetryableIOError(re)
        try:
            response.raise_for_status()
        except requests.HTTPError as he:
            # TODO classify other errors that we consider unrecoverable.
            if response.status_code == 404:
                raise exceptions.ExceptionWrapper(he)
            else:
                raise exceptions.RetryableIOError(he)
        return response

    def _handle_ticket_request(self):
        logging.debug("handle_ticket_request(url={})".format(self.ticket_request_url))
        response = self.__get(self.ticket_request_url, timeout=self.timeout)
        self.ticket = response.json()

    def _handle_http_url(self, url, headers):
        logging.debug("handle_http_url(url={}, headers={})".format(url, headers))
        response = self.__get(url, headers=headers, stream=True, timeout=self.timeout)
        length = 0
        piece_size = 65536
        try:
            for piece in response.iter_content(piece_size):
                length += len(piece)
                self.output.write(piece)
        except requests.RequestException as re:
            raise exceptions.RetryableIOError(re)
        if CONTENT_LENGTH in response.headers:
            content_length = int(response.headers[CONTENT_LENGTH])
            if content_length != length:
                raise exceptions.ContentLengthMismatch(
                    "Length mismatch {} != {}".format(content_length, length))
