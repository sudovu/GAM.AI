#!/usr/bin/env python3
import sys
import os
import unittest

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

loader = unittest.TestLoader()
suite = loader.discover(os.path.join(repo_root, "tests"))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
