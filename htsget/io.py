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
Main interface for the htsget library.
"""
from __future__ import division
from __future__ import print_function

import logging
import time

import htsget.protocol as protocol
import htsget.exceptions as exceptions

import requests
import humanize

CONTENT_LENGTH = "Content-Length"


def get(
        url, output, reference_name=None, reference_md5=None,
        start=None, end=None, fields=None, tags=None, notags=None,
        data_format=None, max_retries=5, retry_wait=5, timeout=120,
        bearer_token=None):
    """
    Runs a request to the specified URL and write the resulting data to
    the specified file-like object.

    :param str url: The URL of the data to retrieve. This may be composed of a prefix
        such as ``http://example.com/reads/`` and an ID suffix such as
        ``NA12878``. The full URL must be supplied here, i.e., in this example
        ``http://example.com/reads/NA12878``.
    :param file output: A file-like object to write the downloaded data to. To support
       retrying of failed transfers, this file must be seekable. For this reason,
       retry will fail if ``stdout`` is provided.
    :param str reference_name: The reference sequence name, for example "chr1",
        "1", or "chrX". If unspecified, all data is returned.
    :param str reference_md5: The MD5 checksum uniquely representing the reference
        sequence as a lower-case hexadecimal string, calculated as the MD5 of the
        upper-case sequence excluding all whitespace characters (this is equivalent to
        SQ:M5 in SAM).
    :param int start: The start position of the range on the reference, 0-based,
        inclusive. If specified, ``reference_name`` or ``reference_md5`` must also
        be specified.
    :param int end: The end position of the range on the reference, 0-based exclusive.
        If specified, ``reference_name`` or ``reference_md5`` must also be specified.
    :param str data_format: The requested format of the returned data.
    :param int max_retries: The maximum number of times that an individual transfer
        will be retried.
    :param float retry_wait: The amount of time in seconds to wait before retrying
        a failed transfer.
    :param float timeout: The socket timeout for I/O operations.
    :param bearer_token: The OAuth2 Bearer token to present to the htsget ticket server.
        If this value is specified, the token is provided to the ticket server using
        the ``Authorization: Bearer [token]`` header. If ``bearer_token`` is None
        or not specified, no Authorization header is sent to the server. Obtaining
        the bearer token is beyond the scope of htsget; consult the documentation
        for your server for information on authentication and how to obtain a
        valid token.
    """
    manager = SynchronousDownloadManager(
        url, output, reference_name=reference_name,
        reference_md5=reference_md5, start=start, end=end, fields=fields, tags=tags,
        notags=notags, data_format=data_format, max_retries=max_retries, timeout=timeout,
        retry_wait=retry_wait, bearer_token=bearer_token)
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
            if response.status_code in [400, 401, 404]:
                raise exceptions.ClientError(str(he), response.text)
            else:
                raise exceptions.RetryableIOError(he)
        return response

    def _stream(self, url, headers={}):

        response = self.__get(url, headers=headers, stream=True, timeout=self.timeout)
        length = 0
        piece_size = 65536
        try:
            for piece in response.iter_content(piece_size):
                length += len(piece)
                yield piece
        except requests.RequestException as re:
            raise exceptions.RetryableIOError(re)
        if CONTENT_LENGTH in response.headers:
            content_length = int(response.headers[CONTENT_LENGTH])
            if content_length != length:
                raise exceptions.ContentLengthMismatch(
                    "Length mismatch {} != {}".format(content_length, length))

    def _handle_ticket_request(self):
        # TODO Add some mechanism for checking the content type here. Possibly a
        # callback that checks the headers on the ticket response?
        # TODO Check the Content-Type for encoding and use it here, if provided.
        encoding = "utf-8"
        headers = {}
        if self.bearer_token is not None:
            headers["Authorization"] = "Bearer {}".format(self.bearer_token)
        # TODO should we XXXX out the actual token here in case someone leaks
        # the bearer token to logs??
        logging.debug("handle_ticket_request(url={}, headers={})".format(
            self.ticket_request_url, headers))
        stream = iter(self._stream(self.ticket_request_url, headers=headers))
        # Peek at the first few bytes of the result to see if it is probably JSON.
        # If not we can end the transfer early. This is useful when the user mistakenly
        # points to a URL for a very large file. In practise, we will often get
        # UnicodeDecodeError when we do this.
        try:
            first_piece = next(stream, "").decode(encoding)
        except UnicodeDecodeError as ude:
            raise exceptions.TicketDecodeError(ude)
        if len(first_piece) == 0:
            raise exceptions.EmptyTicketError()
        stripped = first_piece.lstrip()
        if stripped[0] != '{':
            raise exceptions.InvalidLeadingJsonError(stripped[0])
        text = "".join([first_piece] + [piece.decode(encoding) for piece in stream])
        self.ticket = protocol.parse_ticket(text)

    def _handle_http_url(self, url, headers):
        logging.debug("handle_http_url(url={}, headers={})".format(url, headers))
        before = time.time()
        start_offset = self.output.tell()
        for piece in self._stream(url, headers):
            self.output.write(piece)
        duration = time.time() - before
        size = self.output.tell() - start_offset
        rate = (size / (2**20)) / duration
        logging.info("Downloaded {} chunk in {:.2f} seconds @ {:.2f} MiB/s".format(
            humanize.naturalsize(size, binary=True), duration, rate))
