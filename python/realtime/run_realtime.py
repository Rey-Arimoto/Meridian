import os
import sys

# Allow running from repository root:
#   python python/realtime/run_realtime.py
THIS_DIR = os.path.dirname(__file__)
PYTHON_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

from realtime.meridian_realtime_agent import RealTimeMeridianAgent

if __name__ == "__main__":
    RealTimeMeridianAgent().run()
