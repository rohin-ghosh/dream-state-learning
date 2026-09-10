"""One CLONE of run_life_v2 in the fake world (no GPU, no gym venv), for the
clone-coordinator end-to-end test: tests/test_clone_coordinator.py spawns
two of these as subprocesses with --clone-group/--clone-id/--clone-count.

  python3 tests/clone_life_driver.py --life-dir L --arm B --clone-group G \
      --clone-id 0 --clone-count 2 ...   (every run_life_v2 flag passes through)
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import golden_harness as gh  # noqa: E402

if __name__ == "__main__":
    # the barrier and verdict waits use time.monotonic; time.time is frozen
    # by the fake world (deterministic CLOCK lines) and that is fine here
    tr = gh.run_life(sys.argv[1:])
    print(f"CLONE_DRIVER_DONE events={len(tr.events)}")
