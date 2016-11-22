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
Synchronous IO for htsget using requests.
"""
from __future__ import division
from __future__ import print_function


import requests

import htsget.protocol as protocol

CONTENT_LENGTH = "Content-Length"


class SynchronousHttpChunkRequest(protocol.HttpChunkRequest):

    def run(self, output_file):
        response = requests.get(
            self.url, headers=self.headers, stream=True, timeout=5)
        response.raise_for_status()
        length = 0
        # We download this chunk in small pieces.
        piece_size = 8192
        for piece in response.iter_content(piece_size):
            length += len(piece)
            output_file.write(piece)
        if CONTENT_LENGTH in response.headers:
            content_length = int(response.headers[CONTENT_LENGTH])
            if content_length != length:
                raise ValueError("FIXME")
                # raise ContentLengthMismatch("{} != {}".format(content_length, length))


class SynchronousTicketRequest(protocol.TicketRequest):

    def run(self):
        response = requests.get(self.url)
        response.raise_for_status()
        return protocol.SliceRequest(response.json(), SynchronousHttpChunkRequest)
