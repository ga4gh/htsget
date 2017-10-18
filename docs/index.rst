.. htsget documentation master file, created by
   sphinx-quickstart on Mon Dec  5 13:29:46 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to htsget's documentation!
==================================

This package is a client implementation of the `GA4GH <https://www.ga4gh.org/>`_
htsget `protocol <http://samtools.github.io/hts-specs/htsget.html>`_. It
provides a simple and reliable way to retrieve genomic data from
servers supporting the protocol.

Slightly confusingly, this package and the protocol that it implements are
both called "htsget". As a member of the GA4GH Streaming API group, I developed
this client as part of the process of contributing to the design and evaluation
of the protocol. I named the Python package "htsget", which was subsequently
also adopted as the name of the protocol. Since no one objected to me
continuing to use the name for my package there didn't seem to be much point
in renaming it.

This is not an "official" GA4GH client for the protocol.

Please report any issues or features requests on `GitHub
<https://github.com/jeromekelleher/htsget/issues>`_

Features:
*********

- Thoroughly `tested <https://codecov.io/gh/jeromekelleher/htsget>`_, production
  ready implementation.
- Robust to transient network errors (failed transfers are retried).
- Easy to :ref:`install <sec-installation>` (pure Python implementation, minimal dependencies).
- Powerful :ref:`command line interface <sec-cli>`.
- Simple :ref:`Python API <sec-api>`.

Contents
********

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   api
   cli

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
