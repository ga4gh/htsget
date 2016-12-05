======
htsget
======

.. image:: https://img.shields.io/travis/jeromekelleher/htsget/master.svg
    :target: https://travis-ci.org/jeromekelleher/htsget

.. image:: https://ci.appveyor.com/api/projects/status/n68yw9qklvdham82/branch/master?svg=true
    :target: https://ci.appveyor.com/project/jeromekelleher/htsget/branch/master

.. image:: https://img.shields.io/codecov/c/github/jeromekelleher/htsget.svg
    :target: https://codecov.io/gh/jeromekelleher/htsget

.. image:: https://readthedocs.org/projects/htsget/badge/?version=latest
    :target: http://htsget.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

``htsget`` is a pure-Python API and command line interface for the GA4GH Streaming API. It
provides a simple and reliable way to retrieve high-throughput sequencing data from
servers supporting the protocol. Full documentation is available on
`read the docs <https://htsget.readthedocs.io/en/stable/>`_.

************
Installation
************

To install ``htsget``, simply run::

    $ pip install htsget

If you wish to install ``htsget`` into a your local Python installation, use::

    $ pip install htsget --user

However, you will need to ensure that the local binary directory (usually something
like ``$HOME/.local/bin``) is in your PATH.

*********
CLI Usage
*********

The ``htsget`` command line downloads data from a URL as follows::

    $ htsget http://htsnexus.rnd.dnanex.us/v1/reads/BroadHiSeqX_b37/NA12878 \
        --reference-name=2 --start=1000 --end=20000 -O NA12878_2.bam

Full documentation on the command line options is available via ``htsget --help`` or
`online <https://htsget.readthedocs.io/en/stable/cli.html>`_.

*********
API Usage
*********

The Python API provides a single function ``get``, which supports all of the
arguments provided in the protocol. For example, we might have::

    import htsget

    with open("NA12878_2.bam", "wb") as output:
        htsget.get(
            "http://htsnexus.rnd.dnanex.us/v1/reads/BroadHiSeqX_b37/NA12878", output,
            reference_name="2", start=1000, end=20000)

 Full API documentation is available on
`read the docs <https://htsget.readthedocs.io/en/stable/api.html>`_.
