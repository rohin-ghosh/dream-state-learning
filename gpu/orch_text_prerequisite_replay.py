"""CPU replay of original child commands against the frozen native games."""

import json
from pathlib import Path
import sys

import textworld

from gpu.orch_text_prerequisite_env import public


def main(root):
    bank = json.loads((root / 'games_v2/BANK.json').read_text())
    results = []
    for task in bank['tasks']:
        if task['split'] != 'mining':
            continue
        for arm in ('RICH', 'TERSE'):
            path = root / f"shard{task['shard']}/screen/{task['id']}_{arm}_EPISODE.json"
            record = json.loads(path.read_text())
            environment = textworld.start(str(root / 'games_v2' / task['game']),
                textworld.EnvInfos(description=True, inventory=True, won=True, lost=True, score=True))
            try:
                state = environment.reset()
                assert public(state) == task['initial']
                for turn in record['turns']:
                    assert public(state) == {key: turn['native_before'][key] for key in public(state)}
                    if turn['projection']:
                        state, reward, done = environment.step(turn['projection']['action'])
                        expected = dict(public(state), reward=reward, done=done)
                        assert expected == turn['native_after']
                    else:
                        assert turn['native_after'] is None
                assert bool(state.won) == record['success']
                results.append(dict(task_id=task['id'], arm=arm, turns=len(record['turns']),
                                    success=bool(state.won), byte_exact_native_replay=True))
            finally:
                environment.close()
    receipt = dict(passed=len(results), denominator=16, model_calls=0, fits=0, results=results)
    (root / 'NATIVE_REPLAY.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
