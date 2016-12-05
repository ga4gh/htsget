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
Exceptions for htsget.
"""
from __future__ import division
from __future__ import print_function


class HtsgetException(Exception):
    """
    Superclass of all exceptions that Htsget raises directly.
    """


class ExceptionWrapper(HtsgetException):
    """
    A wrapper for exceptions raised by lower-level libraries. The source
    exception is stored in the ``source`` instance variable.
    """
    def __init__(self, source):
        self.source = source

    def __str__(self):
        return str(self.source)


class RetryableError(HtsgetException):
    """
    The superclass of all errors that we think are worth retrying.
    """


class RetryableIOError(RetryableError, ExceptionWrapper):
    """
    All exceptions thrown by lower level libraries that we consider to be
    retryable are wrapped by this exception.
    """


class ContentLengthMismatch(RetryableError):
    """
    The length of the downloaded content is not the same as the
    length reported in the header.
    """
