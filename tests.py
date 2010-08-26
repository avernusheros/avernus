#!/usr/bin/env python

import unittest, sys
from tests import test_suite

def main():
    runner = unittest.TextTestRunner(stream=sys.stdout, descriptions=False, verbosity=3)
    runner.run(test_suite())


if __name__ == "__main__":
    main()
