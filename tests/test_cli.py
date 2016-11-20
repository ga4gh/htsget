"""
Test cases for the htsget CLI.
"""
from __future__ import print_function
from __future__ import division

import unittest

import htsget.cli as cli


class TestHtsgetArgumentParser(unittest.TestCase):
    """
    Tests the parser to ensure it parses input values correctly.
    """
    def parse_args(self, args):
        parser = cli.get_htsget_parser()
        return parser.parse_args(args)

    def test_defaults(self):
        args = self.parse_args(["URL", "ID"])
        self.assertEqual(args.url, "URL")
        self.assertEqual(args.id, "ID")
        self.assertEqual(args.format, None)
        self.assertEqual(args.reference_name, None)
        self.assertEqual(args.start, None)
        self.assertEqual(args.end, None)
        self.assertEqual(args.output, None)
