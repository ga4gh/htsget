from __future__ import division
from __future__ import print_function
"""
Sans IO protocol handling code to the GA4GH streaming API.
"""

from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlunparse
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import parse_qs


def ticket_request_url(
        url, fmt=None, reference_name=None, reference_md5=None,
        start=None, end=None, fields=None, tags=None, notags=None):
    """
    Create a ticket request URL for the specified parameters.
    """
    parsed_url = urlparse(url)
    get_vars = parse_qs(parsed_url.query)
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
    return urlunparse(new_url)
