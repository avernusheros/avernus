#!/usr/bin/env python

import unittest, os, sys


test_dir = os.path.dirname(__file__)
root_dir = os.path.dirname(test_dir)

sys.path.insert(0, test_dir)
sys.path.insert(0, root_dir)

def test_suite():
    ignores = ('__init__.py')
    files = [f for f in os.listdir(test_dir) if f.endswith(".py") and f not in ignores]
    modules = [m.replace(".py", "") for m in files]
    return unittest.TestLoader().loadTestsFromNames(modules)

