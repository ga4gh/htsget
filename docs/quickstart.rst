.. _sec-quickstart:

==========
Quickstart
==========

************
Installation
************

Install from `PyPI <https://pypi.python.org/pypi/htsget>`_ using

.. code-block:: bash

    $ pip install htsget

See the :ref:`sec-installation` section for more details.

*********
CLI Usage
*********

The ``htsget`` command line downloads data from a URL as follows:

.. code-block:: bash

    $ htsget http://htsnexus.rnd.dnanex.us/v1/reads/BroadHiSeqX_b37/NA12878 \
        --reference-name=2 --start=1000 --end=20000 -O NA12878_2.bam

Full documentation on the command line options is available via ``htsget --help`` or
the :ref:`sec-cli` section.

*********
API Usage
*********

The Python API provides a single function :func:`.get` which supports all of the
arguments provided in the protocol. For example, to duplicate the example above, we can
use the following code:

.. code-block:: python

    import htsget

    url = "http://htsnexus.rnd.dnanex.us/v1/reads/BroadHiSeqX_b37/NA12878"
    with open("NA12878_2.bam", "wb") as output:
        htsget.get(url, output, reference_name="2", start=1000, end=20000)

See the :ref:`sec-api` section for full details.

