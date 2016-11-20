from __future__ import division
from __future__ import print_function

__version__ = "undefined"
try:
    from . import _version
    __version__ = _version.version
except ImportError:
    pass
