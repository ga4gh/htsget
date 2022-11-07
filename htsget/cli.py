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
import json
import logging
import os
import signal
import sys

from json import JSONDecodeError

import htsget
import htsget.exceptions as exceptions


def error_message(message):
    """
    Writes an error message to stderr.
    """
    print("{}: error: {}".format(sys.argv[0], message), file=sys.stderr)


def run(args):
    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(message)s', level=log_level)

    if args.output is not None:
        output = open(args.output, "wb")
    else:
        # This is an awkard hack to get things to work on Python 2 and 3. In Python 3,
        # if we want to write bytes directly, we need to get the underlying buffer.
        # This isn't a problem in Python 2, which doesn't have a buffer. Also, to
        # facilitate testing, we allow stdout to be swapped out for a different file
        # handle.
        try:
            output = sys.stdout.buffer
        except AttributeError:
            output = sys.stdout
        if args.max_retries != 0:
            logging.warn(
                "Cannot retry failed transfers when writing to stdout. Setting "
                "max_retries to zero")
            args.max_retries = 0

    exit_status = 1

    try:
        headers = json.loads(args.headers) if args.headers else None
        htsget.get(
            args.url, output, reference_name=args.reference_name,
            reference_md5=args.reference_md5, start=args.start,
            end=args.end, data_format=args.format, max_retries=args.max_retries,
            retry_wait=args.retry_wait, timeout=args.timeout,
            bearer_token=args.bearer_token, headers=headers)
        exit_status = 0
    except JSONDecodeError as json_decode_error:
        error_message(
            "Cannot parse the argument value for headers, error: {}".format(str(json_decode_error)))
    except exceptions.ExceptionWrapper as ew:
        error_message(str(ew))
    except exceptions.HtsgetException as he:
        error_message(str(he))
    except KeyboardInterrupt:
        error_message("interrupted")
    finally:
        if output is not sys.stdout:
            output.close()
    sys.exit(exit_status)


def get_htsget_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Command line interface for the GA4GH Streaming API. Provides "
            "a simple method to retrieve data spanning genomic ranges from "
            "servers supporting the protocol."))
    parser.add_argument(
        "-V", "--version", action='version',
        version='%(prog)s {}'.format(htsget.__version__))
    parser.add_argument(
        '--verbose', '-v', action='count', default=0,
        help="Increase verbosity.")
    parser.add_argument(
        "url", type=str, help="The URL of the object to retrieve")
    parser.add_argument(
        "--format", "-f", type=str, default=None,
        help="The format of data to request.")
    parser.add_argument(
        "--reference-name", "-r", type=str, default=None,
        help=(
            "The reference sequence name, for example 'chr1', '1', or 'chrX'. "
            "If unspecified, all data is returned."))
    parser.add_argument(
        "--reference-md5", "-m", type=str, default=None,
        help=(
            "The MD5 checksum uniquely representing the requested reference "
            "sequence as a lower-case hexadecimal string, calculated as the MD5 "
            "of the upper-case sequence excluding all whitespace characters."))
    parser.add_argument(
        "--start", "-s", type=int, default=None,
        help=(
            "The start position of the range on the reference, 0-based, inclusive. "
            "If specified, reference-name or reference-md5 must also be specified."))
    parser.add_argument(
        "--end", "-e", type=int, default=None,
        help=(
            "The end position of the range on the reference, 0-based exclusive. If "
            "specified, reference-name or reference-md5 must also be specified."))
    parser.add_argument(
        "--output", "-O", type=str, default=None,
        help=(
            "The output file path. Defaults to stdout. If output is to stdout, the "
            "max-retries is set to zero, since retries are not supported when writing "
            "to this stream"))
    parser.add_argument(
        "--max-retries", "-M", type=int, default=5,
        help="The maximum number of times to retry a failed transfer.")
    parser.add_argument(
        "--retry-wait", "-W", type=float, default=5,
        help="The number of seconds to wait before retrying a failed transfer.")
    parser.add_argument(
        "--timeout", "-T", type=float, default=120,
        help="The socket timeout for transfers.")
    parser.add_argument(
        "--bearer-token", "-b", default=None,
        help="The OAuth2 bearer token to present to the htsget ticket server.")
    parser.add_argument(
        "--headers", "-H", type=str, default=None,
        help="The stringified JSON of HTTP header name-value mappings.")
    return parser


def htsget_main():
    if os.name == "posix":
        # Set signal handler for SIGPIPE to quietly kill the program.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = get_htsget_parser()
    args = parser.parse_args()
    run(args)
