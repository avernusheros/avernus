#!/usr/bin/env python

import unittest, os, sys

# Find the modules to test.
ignores = ('__init__.py', 'alltests.py')
here = os.path.dirname(__file__)
files = [f for f in os.listdir(here) if f.endswith(".py") and f not in ignores]
modules = [m.replace(".py", "") for m in files]
sys.path.append(os.path.join(here, "../../"))

def main():
    runner = unittest.TextTestRunner()
    suite = unittest.TestLoader().loadTestsFromNames(modules)
    runner.run(suite)

if __name__ == "__main__":
    main()
