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


class SynchronousTicketRequest(protocol.TicketRequest):

    def run(self):
        print("running sync ticket request.")

        response = requests.get(self.url)
        response.raise_for_status()
        return SynchronousSliceRequest(response.json())


class SynchronousSliceRequest(protocol.SliceRequest):

    def run(self, output_file):
        print("running sync slice request")
        for chunk_request in self.chunk_requests:
            print(chunk_request.parsed_url)
