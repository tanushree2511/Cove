import os
import sys

_COVE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _COVE_ROOT not in sys.path:
    sys.path.insert(0, _COVE_ROOT)
