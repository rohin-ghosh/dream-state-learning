"""Collection-only repair; never dispatches generation, fitting or old collection."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time


RUNNER = Path('/tmp/astra_additive_replay_run_20260913.py')
RUNNER_PIN = 'ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5'
ERROR = "'dict' object has no attribute 'score_row'"
SCHEMA = 'astra_additive_replay_collection_repair1_v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_runner():
    import hashlib
    require(hashlib.file_digest(RUNNER.open('rb'), 'sha256').hexdigest() == RUNNER_PIN, 'frozen runner differs')
    specification = importlib.util.spec_from_file_location('additive_collection_repair_frozen', RUNNER)
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def failed_collection(memory, root, plan_sha256):
    original = root.with_name(root.name + '_collected')
    claim = root.with_name(root.name + '.collection_claim.json')
    launcher = root.with_name(root.name + '.launcher')
    require(memory.read(claim) == dict(out=str(original), plan_sha256=plan_sha256, retry=False), 'original claim differs')
    require(sorted(path.name for path in original.iterdir()) == ['collection_failure.json'], 'original collection not exact failed attempt')
    failure_path = original / 'collection_failure.json'
    failure = memory.read(failure_path)
    require(set(failure) == {'error', 'error_type', 'retry', 'time'} and failure['error'] == ERROR and
            failure['error_type'] == 'AttributeError' and failure['retry'] is False, 'not the registered scorer-binding failure')
    files = [claim, failure_path]
    for name, expected in (('controller_exit.json', 0), ('collector_exit.json', 1), ('exit.json', 1)):
        path = launcher / name
        receipt = memory.read(path)
        require(type(receipt['returncode']) is int and receipt['returncode'] == expected, 'native terminal chain differs')
        files.append(path)
    return {str(path): memory.digest(path) for path in files}


def score_cells(memory, plan, bound, arms):
    require(type(bound['material']) is dict and callable(getattr(bound['old_bound']['material'], 'score_row', None)),
            'expected original scorer/material seam differs')
    scoring = dict(bound, material=bound['old_bound']['material'])
    return {arm: memory.score_calls(plan, scoring, arm) for arm in arms}


def recover(root, plan_sha256, completion_sha256, out):
    entry = time.monotonic()
    candidate = load_runner()
    memory = candidate.runtime()
    memory.offline()
    root = Path(root).absolute()
    with memory.budget(candidate.COLLECTION_SECONDS - (time.monotonic() - entry)):
        memory, plan, bound = candidate.verify(root, plan_sha256)
        before = failed_collection(memory, root, plan_sha256)
        require(candidate.digest(root / 'capture_complete.json') == completion_sha256, 'completion pin differs')
        complete = memory.read(root / 'capture_complete.json')
        require(complete['scope'] == candidate.SCOPE and complete['plan_sha256'] == plan_sha256 and complete['scored'] is False and
                complete['stages'] == candidate.validate_completed(memory, plan, plan_sha256, bound) and
                all(type(complete[key]) is int and complete[key] == plan['limits'][key] for key in ('fits', 'updates', 'calls')) and
                type(complete['elapsed_seconds']) in (int, float) and 0 <= complete['elapsed_seconds'] <= candidate.SECONDS,
                'original native completion differs')
        expected_out = root.with_name(root.name + '_collected_repair1')
        require(Path(out).absolute() == expected_out, 'one fixed fresh recovery directory required')
        out = memory.new_external(out, [root, root.with_name(root.name + '_collected'), *candidate.protected(plan['specification'], bound)])
        claim_path = root.with_name(root.name + '.collection_repair1_claim.json')
        claim = dict(schema=SCHEMA, root=str(root), out=str(out), plan_sha256=plan_sha256,
                     completion_sha256=completion_sha256, repair_sha256=memory.digest(__file__), runner_sha256=RUNNER_PIN,
                     original_failure_files=before, collection_attempt=2, scientific_retry=False,
                     generation_calls=0, fits=0, updates=0)
        require(not out.exists() and not claim_path.exists(), 'recovery already attempted')
        memory.write(claim_path, claim)
        out.mkdir()
        try:
            cells = score_cells(memory, plan, bound, candidate.ARMS)
            fits = {arm: memory.read(root / 'run' / (arm + '_fit') / 'adapter/train_manifest.json') for arm in candidate.ARMS}
            training = {arm: {key: value for key, value in memory.read(root / f'training_{arm}.json').items()
                             if key not in ('items', 'encoding', 'epoch_order', 'replay_items', 'replay_encoding')} for arm in candidate.ARMS}
            scores = dict(scope=candidate.SCOPE, claim=candidate.CLAIM, seed=plan['specification']['seed'], parent=plan['parent'],
                plan_sha256=plan_sha256, completion_sha256=completion_sha256, counts=plan['counts'], cells=cells, fits=fits,
                historical_cells=bound['history'], historical_manifests=bound['historical_manifests'],
                reused_endpoints=plan['reused_endpoints'], source_bindings=plan['specification'], input_hashes=plan['input_hashes'],
                training_costs=training, parameter_diagnostics={arm: memory.read(root / 'run' / (arm + '_fit') / 'fit.json')['norms'] for arm in candidate.ARMS},
                screen={arm: bound['old'].screen(plan['specification']['seed'], cells[arm], bound['history']['LR0']) for arm in candidate.ARMS},
                best_constant=bound['old'].constant_diagnostic(bound, cells),
                incremental_cost=dict(calls=complete['calls'], fits=complete['fits'], updates=complete['updates'], historical_calls=0,
                    historical_updates=0, historical_fits=0, new_source_calls=0, teacher_calls=0, controller_seconds=complete['elapsed_seconds']),
                native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None,
                evaluator_note='Fresh MEMORY_ONLY drift versus old EXTRA_MEMORY needs diagnosis before attributing differences to replay; no automatic adoption.')
            memory.write(out / 'scores.json', scores)
            require(before == failed_collection(memory, root, plan_sha256), 'original failure evidence changed')
            require(candidate.digest(root / 'capture_complete.json') == completion_sha256 and
                    complete['stages'] == candidate.validate_completed(memory, plan, plan_sha256, bound), 'native evidence changed during recovery')
            elapsed = time.monotonic() - entry
            require(elapsed <= candidate.COLLECTION_SECONDS, 'recovery collection budget exceeded')
            memory.write(out / 'collection.json', dict(scores_sha256=memory.digest(out / 'scores.json'),
                completion_sha256=completion_sha256, collection_seconds=elapsed))
            memory.write(out / 'recovery.json', dict(schema=SCHEMA, status='COLLECTION_REPAIRED_NOT_SCIENTIFIC_RETRY',
                returncode=0, claim_sha256=memory.digest(claim_path), repair_sha256=memory.digest(__file__), runner_sha256=RUNNER_PIN,
                scores_sha256=memory.digest(out / 'scores.json'), collection_sha256=memory.digest(out / 'collection.json'),
                original_failure_files=before, collection_attempt=2, scientific_retry=False, fits=0, updates=0, generation_calls=0,
                elapsed_seconds=elapsed))
            return dict(status='COLLECTION_REPAIRED_NOT_SCIENTIFIC_RETRY', out=str(out),
                        recovery_sha256=memory.digest(out / 'recovery.json'), scores_sha256=memory.digest(out / 'scores.json'))
        except BaseException as error:
            memory.failure(out / 'collection_failure.json', error)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--completion-sha256', required=True)
    parser.add_argument('--out', required=True)
    print(json.dumps(recover(**vars(parser.parse_args())), sort_keys=True))
