#!/usr/bin/env python

import unittest, sys, logging
from tests import test_suite
import __builtin__
__builtin__._ = str

logging.basicConfig(level=logging.INFO)


def main():
    runner = unittest.TextTestRunner(stream=sys.stdout, descriptions=False, verbosity=3)
    runner.run(test_suite())


if __name__ == "__main__":
    main()
