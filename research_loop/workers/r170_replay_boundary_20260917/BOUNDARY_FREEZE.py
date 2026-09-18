"""Freeze one observed readout boundary; never signal a learner or create GO."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
STAGE = Path('/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1')
LIFE = Path('/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
BOOTSTRAP = STAGE / 'bootstrap'
SCOPE_SHA = '20743f990b673875241023681d811b4e24eefb32a1546174065353648928356b'
APPROVAL_SHA = '870d9a17b5e95c2b69f654904b2a6630dcc327e80884282a3bdf505c00708a7a'
ASSEMBLY_SHA = '3e9da0d121cb53b76ad1411f9c6e942923892363cb5dcde591674c7ac881347e'
READY_SHA = '4ecd0343921c6380a072b480b3d365859d1080d58c5cc7a68a2dce615ba129e6'
SCAFFOLD_SHA = '5dca80d8c01e8bfc05ff12ecdaf074474fcbf1c1b800fb50b28db0afe61e3c12'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference(path):
    require(path.resolve() == path and path.is_file() and not path.is_symlink(), 'canonical_input')
    require(path.stat().st_size <= 16 * 1024 * 1024, 'bounded_input')
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def load(name, checksum):
    path = HERE / name
    require(reference(path)['sha256'] == checksum, 'pinned_dependency')
    specification = importlib.util.spec_from_file_location('r170_' + path.stem, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def freeze(boundary_ref, checkpoint_ref, cycle):
    require(type(cycle) is int and cycle > 0, 'observed_positive_cycle')
    boundary_path = Path(boundary_ref['path'])
    checkpoint_path = LIFE / 'checkpoints' / f'sleep_{cycle:06d}' / 'COMMIT.json'
    require(boundary_path.parent == LIFE / 'stream/records'
            and len(boundary_path.stem) == 20 and boundary_path.stem.isdecimal()
            and boundary_path.suffix == '.json', 'one_life_record')
    require(checkpoint_ref['path'] == str(checkpoint_path), 'same_cycle_commit')
    require(reference(boundary_path) == boundary_ref and reference(checkpoint_path) == checkpoint_ref,
            'observed_byte_refs_unchanged')
    require(HERE == BOOTSTRAP / 'research_loop/workers/r170_replay_boundary_20260917',
            'exact_bootstrap')
    sys.path.insert(0, str(BOOTSTRAP))
    assembly = load('ASSEMBLY_V2.py', ASSEMBLY_SHA).assembly_namespace(
        dict(path=str(HERE / 'APPROVED_RECEIVING_CPU.json'), sha256=APPROVAL_SHA))
    result = assembly['finalize_selection_bundle'](
        scaffold_ref=dict(path=str(STAGE / 'physical1/SCAFFOLD.json'), sha256=SCAFFOLD_SHA),
        boundary_ref=boundary_ref, checkpoint_ref=checkpoint_ref,
        approved_intake_sha256=SCOPE_SHA, now=time.time(), main_go_scope=None)
    require(result['source_cycle'] == cycle and result['target_cycle'] == cycle + 1,
            'observed_same_cycle_only')
    receipt = dict(schema='R170_OBSERVED_BOUNDARY_SELECTION_ONLY_V1',
        source_cycle=cycle, target_cycle=cycle + 1,
        selection_bundle_ref=result['selection_bundle_ref'],
        expected_main_go_scope=result['expected_main_go_scope'],
        boundary_ref=boundary_ref, checkpoint_ref=checkpoint_ref,
        observed_unix=time.time(), main_go_created=False, signals_sent=0,
        model_calls=0, awaiting_explicit_Main_scope=True)
    assembly['_write'](STAGE / 'physical1/SELECTION_FREEZE_RECEIPT.json', receipt)
    return receipt


def opportunity(original, plan, processes):
    saved = original.saved.sleep_boundary(plan['root'])
    if saved is None:
        return None
    if not original.saved.readout_started(plan['root'], saved['cycle'],
            plan.get('readout_revision', 1), processes['timer']['pid']):
        return None
    if original.saved.sleep_boundary(plan['root']) != saved:
        return None
    return saved


def watch(seconds):
    require(type(seconds) is int and 1 <= seconds <= 5400, 'bounded_observation_seconds')
    ready = load('LIFECYCLE_READY.py', READY_SHA)
    adapter = ready.load_operator()
    family = adapter['family_namespace']()
    helper = family['api']()
    config, plan, original = family['old_modules'](adapter['OLD_GUARD'])
    processes = family['old_processes'](ready.EXPECTED_PID, adapter['OLD_GUARD'], config, plan)
    require(processes['actor']['start_ticks'] == ready.EXPECTED_TICKS, 'original_instance')
    deadline = min(time.monotonic() + seconds,
                   time.monotonic() + plan['hard_end_unix'] - time.time() - 1800)
    marker = STAGE / 'physical1/SELECTION_OBSERVER_STARTED.json'
    helper.write(marker, dict(started_unix=time.time(), pid=__import__('os').getpid(),
        seconds=seconds, original_processes=processes, signals_sent=0, model_calls=0))
    while time.monotonic() < deadline:
        require(helper.process_record(ready.EXPECTED_PID) == processes['actor'], 'original_actor_unchanged')
        saved = opportunity(original, plan, processes)
        if saved is None:
            time.sleep(2)
            continue
        boundary_ref = reference(Path(saved['path']))
        checkpoint_ref = reference(LIFE / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json')
        command = [PYTHON, '-I', '-B', str(HERE / 'BOUNDARY_FREEZE.py'), '--assemble',
            json.dumps(dict(boundary_ref=boundary_ref, checkpoint_ref=checkpoint_ref, cycle=saved['cycle']))]
        completed = subprocess.run(command, cwd=BOOTSTRAP,
            env=dict(PATH='/usr/bin:/bin', CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                     HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=120, check=False)
        result = dict(returncode=completed.returncode, stdout=completed.stdout.decode(),
            stderr=completed.stderr.decode(), same_boundary_after=original.saved.sleep_boundary(plan['root']) == saved,
            finished_unix=time.time(), signals_sent=0, model_calls=0, main_go_created=False)
        helper.write(STAGE / 'physical1/SELECTION_OBSERVER_RESULT.json', result)
        require(completed.returncode == 0, 'selection_failed_no_retry')
        return result
    result = dict(status='NO_CURRENT_READOUT_BOUNDARY_OBSERVED', finished_unix=time.time(),
                  signals_sent=0, model_calls=0, main_go_created=False)
    helper.write(STAGE / 'physical1/SELECTION_OBSERVER_RESULT.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--watch', type=int)
    actions.add_argument('--assemble')
    arguments = parser.parse_args()
    result = watch(arguments.watch) if arguments.watch is not None else freeze(**json.loads(arguments.assemble))
    print(json.dumps(result, sort_keys=True))
