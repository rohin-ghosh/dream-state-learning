"""Wait for the exact existing CPU parent to exit naturally; never signal it."""

import json
import os
from pathlib import Path
import sys
import time

from lease_horizon import cpu_horizon


def main():
    predecessor, start_ticks = int(sys.argv[1]), sys.argv[2]
    root = Path(__file__).resolve().parent
    output = root / 'private/overseer'
    wall = cpu_horizon()
    (output / f'SUCCESSOR_WAIT_{time.time_ns()}.json').write_text(json.dumps(dict(
        pid=os.getpid(), predecessor_pid=predecessor, predecessor_start_ticks=start_ticks,
        cpu_hard_end_unix=wall, native_hard_end_changed=False, signals=[])))
    while time.time() < wall:
        try:
            fields = Path(f'/proc/{predecessor}/stat').read_text().rsplit(') ', 1)[1].split()
        except FileNotFoundError:
            break
        if fields[19] != start_ticks or fields[0] == 'Z':
            break
        time.sleep(2)
    cpu_horizon()
    os.execv(sys.executable, [sys.executable, '-B', str(root / 'overseer.py')])


if __name__ == '__main__':
    main()
