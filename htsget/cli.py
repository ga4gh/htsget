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
The command line interface for htsget.
"""

from __future__ import division
from __future__ import print_function


import argparse
import os
import logging
import signal

import htsget


def run(args):
    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(message)s', level=log_level)

    with open(args.output, 'w') as f:
        htsget.get(
            args.url, f, reference_name=args.reference_name, start=args.start,
            end=args.end)


def get_htsget_parser():
    parser = argparse.ArgumentParser(
        description="Command line interface for the GA4GH Streaming API.")
    parser.add_argument(
        "-V", "--version", action='version',
        version='%(prog)s {}'.format(htsget.__version__))
    parser.add_argument('--verbose', '-v', action='count', default=0)

    parser.add_argument(
        "url", type=str, help="The URL of the object to retrieve")
    parser.add_argument(
        "--format", "-F", type=str, default=None,
        help="The format of data to request.")
    parser.add_argument(
        "--reference-name", "-r", type=str, default=None,
        help="The reference name. If not specified return all reads")
    parser.add_argument(
        "--start", "-s", type=int, default=None,
        help="The starting coordinate.")
    parser.add_argument(
        "--end", "-e", type=int, default=None,
        help="The end coordinate")
    parser.add_argument(
        "--output", "-O", type=str, default=None,
        help="The output file path. Defaults to stdout")
    return parser


def htsget_main():
    if os.name == "posix":
        # Set signal handler for SIGPIPE to quietly kill the program.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = get_htsget_parser()
    args = parser.parse_args()
    run(args)
