"""State-preserving future-only scorer repair; never signals a learner."""

import hashlib
import json
from pathlib import Path
import subprocess

import adopt as previous


ROOT = Path('/localhome/local-rohing/orch_r226_caption_scorer_20260918')
OLD = Path('/localhome/local-rohing/orch_r224_caption_scorer_20260918/session2')
OLD_PID = 990782
OLD_START = '28571368'
ENDPOINT = Path('/tmp/r224_caption_new.sock')


def read(path):
    return json.loads(Path(path).read_bytes())


def export_current(root, descriptors, *, verify_origin):
    from gpu import ny_caption_data as data

    loaded = read(root / 'LOADED.json')
    initial = data.bound(loaded['resume_state_input'])
    state_bytes = (root / 'SESSION_STATE.private.json').read_bytes()
    state = json.loads(state_bytes)
    previous.require(state['schema'] == 'R223_CAPTION_SESSION_STATE_V1'
        and state['phase'] == 'COMPLETE' and state['life_root'] == loaded['life_root']
        and state['scene_ids'] == descriptors and state['source_mode'] == 'NATIVE_JOURNAL',
        'same_complete_native_session')
    seen = set(initial['seen'])
    expected = dict(game=initial['game'], policy=initial['policy'])
    attempts = []
    for directory in (root / 'attempts').iterdir():
        previous.require(all((directory / name).is_file()
            for name in ('RESULT.json', 'BEFORE.json', 'AFTER.json')), 'complete_attempt_before_export')
        attempts.append((read(directory / 'RESULT.json')['unix'], directory))
    for _, directory in sorted(attempts):
        document = read(directory / 'RESULT.json')
        previous.require(data.digest(read(directory / 'BEFORE.json')) == data.digest(expected),
            'continuous_scoring_state_chain')
        raw = verify_origin(Path(state['life_root']), document['origin'])
        previous.require(raw == document['raw_act'], 'exact_original_act')
        source = document['origin']['record_sha256']
        previous.require(source not in seen, 'once_only_original_act')
        seen.add(source)
        expected = read(directory / 'AFTER.json')
    previous.require(set(state['seen']) == seen and len(state['seen']) == len(seen)
        and data.digest(expected) == data.digest(dict(game=state['game'], policy=state['policy'])),
        'complete_seen_and_state_preserved')
    previous.require((root / 'SESSION_STATE.private.json').read_bytes() == state_bytes,
        'stable_snapshot_during_validation')
    return state, dict(complete_attempts=len(seen), current_attempts=len(attempts),
        state_sha256=hashlib.sha256(state_bytes).hexdigest(),
        game_snapshot_sha256=data.digest(state['game']), policy_snapshot_sha256=data.digest(state['policy']),
        historical_rescoring=False, novelty_reset=False, raw_modified=False)


def quiet(baseline):
    lines = subprocess.check_output(['ss', '-xlnpH'], text=True).splitlines()
    listeners = [line.split() for line in lines if f'pid={OLD_PID},' in line and str(ENDPOINT) in line]
    return len(listeners) == 1 and listeners[0][2] == '0' and previous.process_sockets() <= baseline


def main():
    previous.ROOT = ROOT
    previous.OLD = OLD
    previous.OLD_PID = OLD_PID
    previous.OLD_START = OLD_START
    previous.ENDPOINT = ENDPOINT
    previous.LEGACY = Path('/tmp/r226_caption_legacy.sock')
    previous.BRIDGE = Path('/tmp/r226_caption_bridge.sock')
    previous.TARGET = Path('/tmp/r226_caption_new.sock')
    previous.export_session = export_current
    previous.quiet = quiet
    previous.main()


if __name__ == '__main__':
    main()
