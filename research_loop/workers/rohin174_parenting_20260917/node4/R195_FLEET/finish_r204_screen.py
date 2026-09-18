"""Observe the already-withdrawn MATH-C continuation; never publish or launch."""

import argparse
import time

from math_c import HOME, WALL, read, require, write


def main(physical=6):
    root = HOME if physical == 6 else HOME.parent / f'SCALE_physical{physical}'
    control = root / ('reload_r204/control' if physical == 6 else 'withdrawn/control')
    while time.time() < WALL and not (control / 'EXIT.json').exists():
        time.sleep(3)
    require(read(control / 'EXIT.json')['exit_code'] == 0, 'R204_same_life_screen_successful_exit')
    records = [read(path) for path in sorted((root / 'life/stream/records').glob('[0-9]' * 20 + '.json'))]
    completions = {record['document']['cycle']: record for record in records if record['kind'] == 'SLEEP_COMPLETE'}
    require(set(completions) == {52, 53, 54, 55, 56, 57}, 'exact_three_guided_three_withdrawn')
    require(read(root / 'PARENT_WITHDRAWAL_RECONCILED.json')['no_pending_parent_replay'], 'withdrawal_preserved')
    write(root / 'SCREEN_COMPLETE.json', dict(status='THREE_GUIDED_THREE_WITHDRAWN_COMPLETE',
        completed_unix=time.time(), cycles={str(cycle): record['sha256'] for cycle, record in completions.items()},
        source_changed_to_frozen_R204_at_saved_boundary=True,
        comparison_confound='MATH-C structured THINK; failed guided parent turns; R204 boundary update'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, default=6)
    main(parser.parse_args().physical)
