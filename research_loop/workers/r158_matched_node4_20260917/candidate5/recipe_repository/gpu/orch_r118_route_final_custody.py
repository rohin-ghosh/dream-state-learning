"""Resume an unused FINAL budget with the frozen scheduler and original lock."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
from types import FunctionType


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_reference')
    return json.loads(Path(reference['path']).read_bytes())


def load(reference):
    require(sha(reference['path']) == reference['sha256'], 'frozen_scheduler_source')
    spec = importlib.util.spec_from_file_location('frozen_route_final', reference['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exited(identity):
    try:
        fields = (Path('/proc') / str(identity['pid']) / 'stat').read_text().split(') ', 1)[1].split()
        return fields[0] == 'Z' or fields[19] != str(identity['start_ticks'])
    except FileNotFoundError:
        return True


def unused(root):
    root = Path(root)
    for name in ('ATTEMPT.json', 'DISPATCH.json', 'FAILED.json', 'COMPLETED.json',
                 'NOT_RUN_BOUND.json', 'SKIPPED_ALREADY_COMPLETE.json', 'FINAL_INVENTORY_BINDING.json'):
        require(not (root / name).exists(), 'prior_evaluation_attempt_preserved_no_replay')
    ledger = root / 'RESERVATIONS.jsonl'
    require(not ledger.exists() or ledger.stat().st_size == 0, 'unused_original_evaluation_budget')
    require(not (root / 'sealed_final_readouts').exists(), 'no_prior_evaluation_capture')


def verify(control, final):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_custody')
    require(control['source']['sha256'] == sha(__file__), 'custody_source_bound')
    require(control['authorization'] == 'MAIN_FINAL_ONLY_RECOVERY_20260915_AFTER1637', 'evaluation_only_authority')
    cpu = bound(control['cpu'])
    require(cpu['exitcode'] == 0 and cpu['source_sha256'] == sha(__file__)
            and cpu['model_calls'] == cpu['provider_calls'] == cpu['sealed_reads'] == 0,
            'CPU_provenance')
    config = final.validate_config(control['config'])
    require(time.time() < final.START and config['start_unix'] == final.START
            and config['end_unix'] <= final.END and config['native_calls'] == 48,
            'original_FINAL_window_and_budget')
    require(config['source'] == control['scheduler'], 'original_scheduler_only')
    require(config['parent_calls'] == config['optimizer_steps'] == config['training_rows'] == 0,
            'no_parent_optimizer_or_TRAIN')
    retirement = bound(control['retirement'])
    require(retirement['status'] == 'RETIRED_FOR_COORDINATED_SUCCESSOR', 'actual_retirement')
    identity = retirement['identities'][config['branch'] + '_FINAL']
    require(exited(identity), 'old_scheduler_identity_exited')
    started = bound(control['old_started'])
    require(started['pid'] == identity['pid'] and started['config'] == control['config'],
            'old_scheduler_exact_config')
    unused(config['root'])
    release = final.release_evidence(config)
    return dict(branch=config['branch'], release=release, original_root=config['root'],
                native_calls_consumed=0, native_calls_max=48, start_unix=final.START,
                end_unix=config['end_unix'], no_budget_reset=True)


def resume(control, final):
    proof = verify(control, final)
    directory = Path(control['directory'])
    original = Path(proof['original_root']) / 'SCHEDULER_STARTED.json'

    def preserved_write(path, value):
        if Path(path) == original:
            unused(proof['original_root'])
            final.write(directory / 'STARTED.json', dict(value, custody_source=control['source'],
                previous_started=control['old_started'], proof=proof))
        else:
            final.write(path, value)

    waiter = FunctionType(final.wait.__code__, dict(final.wait.__globals__, write=preserved_write),
                          'same_frozen_wait_original_lock', final.wait.__defaults__)
    return waiter(control['config'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', required=True)
    parser.add_argument('--control-sha256', required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    control = bound(dict(path=args.control, sha256=args.control_sha256))
    final = load(control['scheduler'])
    if args.verify_only:
        print(json.dumps(verify(control, final), sort_keys=True))
    else:
        resume(control, final)


if __name__ == '__main__':
    main()
