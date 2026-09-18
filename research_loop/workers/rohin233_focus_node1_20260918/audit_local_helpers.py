"""Read-only identity check of the four selected lives' historical CPU parents."""

import json
from pathlib import Path
import time

from preserve_ended import identity, reference


def main():
    root = Path(__file__).resolve().parents[1] / 'rohin174_parenting_20260917/node1/R195_FLEET'
    rows = []
    for physical in (2, 4, 5, 7):
        paths = sorted(root.glob(f'*PARENT_PROCESS_{physical}.json'))
        paths += sorted((root / 'R213_NATURAL').glob(f'PARENT_PROCESS_{physical}.json'))
        for path in paths:
            prior = json.loads(path.read_bytes())
            pid = prior.get('pid', prior.get('new_pid'))
            if pid is None:
                raise ValueError('parent_receipt_lacks_pid')
            current = identity(pid)
            ticks = prior.get('start_ticks')
            same = False if current is None else (None if ticks is None else current['start_ticks'] == str(ticks))
            rows.append(dict(physical=physical, receipt=reference(path), pid=pid,
                             start_ticks=None if ticks is None else str(ticks), current=current,
                             same_process_alive=same,
                             disposition=('already_absent' if current is None else
                                          'same_process_running' if same else
                                          'historical_ticks_missing_no_signal' if same is None else
                                          'pid_reused_no_signal')))
    print(json.dumps(dict(node='orchestrator', selected_gpu_slots=[2, 4, 5, 7],
                         observed_unix=time.time(), helper_signals=0, rows=rows), indent=2))


if __name__ == '__main__':
    main()
