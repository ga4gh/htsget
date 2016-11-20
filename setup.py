from __future__ import division
from __future__ import print_function

from setuptools import setup

with open("README.txt") as f:
    long_description = f.read()

setup(
    name="htsget",
    description="Python API and command line interface for the GA4GH streaming API.",
    long_description=long_description,
    packages=["htsget"],
    author="Jerome Kelleher",
    author_email="jerome.kelleher@well.ox.ac.uk",
    url="http://pypi.python.org/pypi/htsget",
    entry_points={
        'console_scripts': [
            'htsget=htsget.cli:htsget_main',
        ]
    },
    install_requires=["requests", "six"],
    keywords=["BAM", "CRAM", "Streaming"],
    license="Apache 2.0",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Development Status :: 3 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache 2.0",
        "Operating System :: POSIX",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    setup_requires=['setuptools_scm'],
    use_scm_version={"write_to": "htsget/_version.py"},
)
