# python/realtime/run_realtime.py
"""
Runner for Meridian v0.1.

This file is intentionally runnable as:
  python python/realtime/run_realtime.py
from repository root.

It patches sys.path so imports work without packaging steps.
"""

import os
import sys

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from realtime.meridian_realtime_agent import RealTimeMeridianAgent  # noqa: E402


if __name__ == "__main__":
    RealTimeMeridianAgent().run()
