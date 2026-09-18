"""Use the tested sequential controller without modifying its completed block."""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path('/localhome/local-rohing/orch_post_recovery_c2_age_eval_20260918')
ARMS = ('base', 'c2sleep51', 'c2sleep117')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('batch', 'observe'), required=True)
    options = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'tools'))
    import batch
    batch.ROOT, batch.ARMS = ROOT, ARMS
    batch.DEADLINE = json.loads((ROOT / 'PLAN.json').read_bytes())['deadline_unix']
    if options.mode == 'batch':
        batch.main()
    else:
        import observe
        observe.DEADLINE = batch.DEADLINE
        document = observe.collect()
        document['source_description'] = 'C2 sleep51 versus sleep117 captured at21:58:47UTC; not a claim of current live weights.'
        print(json.dumps(document, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
