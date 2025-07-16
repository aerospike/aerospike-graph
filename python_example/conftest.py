# python_example/conftest.py
import os, sys

# Prepend the parent directory (python_example) onto sys.path
here = os.path.abspath(os.path.dirname(__file__))
if here not in sys.path:
    sys.path.insert(0, here)
