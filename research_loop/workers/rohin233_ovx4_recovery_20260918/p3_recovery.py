"""Non-material exact P3 service recovery; no learner or parent controls."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def validate(config):
    lease = read(config['lease']['path'])
    assert checksum(config['lease']['path']) == config['lease']['sha256'], 'bound_recorded_allocation'
    assert time.time() < config['deadline_unix'] <= lease['lease_end_unix'] - 21600, 'six_hour_allocation_margin'
    assert config['physical'] == 0, 'original_scorer_device_only'
    assert config['source_files']['gpu/ny_caption_life_service.py'] == '4008f0b9242fa15734a214f3f01ccbd57c6d48ac9705e1754bfc2562abf917b6'
    for name, expected in config['source_files'].items():
        assert checksum(Path(config['source_root']) / name) == expected, 'exact_original_frozen_source'
    state = read(config['resume_state']['path'])
    assert checksum(config['resume_state']['path']) == config['resume_state']['sha256']
    assert state['phase'] == 'COMPLETE' and len(state['seen']) == len(set(state['seen'])) == 48
    assert state['life_root'] == config['arguments']['life_root'] and state['source_mode'] == 'NATIVE_JOURNAL'
    return state


def smoke(config):
    from gpu import ny_caption_data as data
    from gpu.ny_caption_life_service import LifeSession
    from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import restore_contract

    state = validate(config)

    class SavedGame:
        def restore(self, value):
            self.value = value

        def snapshot(self):
            return self.value

    output = Path(config['recovery_root']) / 'CPU_SESSION'
    session = LifeSession(SavedGame(), state['life_root'], output, state['scene_ids'],
        resume_state=state, source_mode=state['source_mode'], session_binding=state['session_binding'])
    evidence = restore_contract(state, session.snapshot())
    load_receipt(config, session, evidence)
    return dict(unix=time.time(), status='CPU_EXACT_48_SEEN_RESTORE_PASS', **evidence, GPU_work=False)


def load_receipt(config, session, evidence):
    from gpu.ny_caption_life_service import restoration_evidence
    return {**evidence, **restoration_evidence(session, config['resume_state']),
        'unix': time.time(), 'pid': os.getpid(), 'original_session': 'R226_session2', 'physical': 0,
        'deadline_unix': config['deadline_unix'], 'native_signals': [], 'parent_publications': [],
        'historical_rescoring': False, 'provider_exact_expiry_claimed': False}


def run(config):
    from gpu import ny_caption_data as data
    from gpu.ny_caption_life_service import load_session, serve, restoration_evidence
    from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import restore_contract

    state = validate(config)
    args = argparse.Namespace(**config['arguments'], output=str(Path(config['recovery_root']) / 'session'),
        resume_state=config['resume_state']['path'], resume_state_sha256=config['resume_state']['sha256'], top_k=50)
    session = load_session(args)
    evidence = restore_contract(state, session.snapshot())
    data.private_write(Path(config['recovery_root']) / 'LOADED_VERIFIED.json', load_receipt(config, session, evidence))
    serve(session, config['socket'], int(config['deadline_unix'] - time.time()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    config = read(args.config)
    if args.smoke:
        print(json.dumps(smoke(config)))
    else:
        run(config)


if __name__ == '__main__':
    main()
