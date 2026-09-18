"""Bounded, wrapper-only R133 retirement of reviewed node3 inference lanes.

The live actuator supports reviewed ovx2 L1 physical0, BASE-context math1,
full CODE carry chunks3-6, and GRID carry/ledger boundaries7. No other node
is an actuator target. Training lanes require their own frontier proof, not reuse
of this actuator. No training process, child launcher, or process group is
signalled. A boundary notification is only a hint: the stopped actor must
have no intent or completed work beyond the saved cursor.
"""

import argparse
import base64
import ctypes
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import select
import shlex
import signal
import struct
import subprocess
import sys
import tarfile
import time


BASE = Path('/localhome/local-rohing')
ROOT = BASE / 'orch_r119_l1_generation_20260915_attempt2'
UUID = 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939'
WRAPPER_SHA = '4c402e37027a5fc509a27e33ff2ed82c9fbf48bcd0ac976648d27240c898d107'
GENERATOR_SHA = 'ef49cd1d9fb4b21b36b7eb376dda809b43b9eef9c5fdda18a5425e3948b73c70'
FORKS_SHA = '7e4c676aae449ceb2ca2b30e38f454212003af996e8d7080ee80d8853c0e90c3'
SCHEMA = 'R133_NODE3_GENERATION_RETIREMENT_V1'
MATH_ROOT = BASE / 'orch_math_feedback_uptake_r110_20260915_attempt1'
MATH_LANE = MATH_ROOT / 'campaign_node3_style1'
MATH_OUTPUT = MATH_LANE / 'R119_LEASE_V3'
MATH_SOURCE = BASE / 'orch_math_feedback_uptake_r119_old_source_20260915_v3/gpu'
MATH_UUID = 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'
MATH_WRAPPER_SHA = '4f2f4bef96bb1363beb85338383ede072f587acb51c441450bc1427a544abc88'
MATH_NATIVE_SHA = '37eb46fdc63b43fc8cbab56517ad49546eb97c42ebc71aece5fd7a2086422523'
DEVICES = {0: UUID, 1: MATH_UUID,
           3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
           4: 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4',
           5: 'GPU-bc211959-642d-664b-3581-42a0dbe434e9',
           6: 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8',
           7: 'GPU-319224de-e668-1822-d80b-4b24d15968ae'}
CODE_BASE = BASE / 'orch_r126_code_capacity_20260915_v3'
CODE_DEPENDENCY = BASE / 'orch_r119_code_old_forks_20260915_v3/source'
GRID_ROOT = BASE / 'orch_r118_node3_7_grid_20260915_attempt1'
GRID_SOURCE = BASE / 'orch_r119_grid_lease_source_20260915_v1/gpu'
GRID_OLD_SOURCE = BASE / 'orch_r118_node3_7_grid_recovery_source_20260915_v1'
SHARED_SEED = BASE / 'orch_r116_shared_node5_20260915_attempt1/generation_000000/sleep/checkpoint'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def ref(path):
    path = Path(path)
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def immutable(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    command = (directory / 'cmdline').read_bytes()
    environment = (directory / 'environ').read_bytes().split(b'\0')
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                parent=int(fields[1]), argv=command.rstrip(b'\0').decode().split('\0'),
                command_sha256=hashlib.sha256(command).hexdigest(),
                cvd=[row.decode().split('=', 1)[1] for row in environment
                     if row.startswith(b'CUDA_VISIBLE_DEVICES=')])


def alive(expected):
    try:
        current = identity(expected['pid'])
        return all(current[key] == expected[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id'))
    except (FileNotFoundError, ProcessLookupError):
        return False


def same(expected):
    require(identity(expected['pid']) == expected, 'identity_drift_no_signal')


def check_pair(actor, supervisor, segment):
    script = str(ROOT / 'orch_r119_l1_generation_resume.py')
    prefix = [str(BASE / 'v2/venv/bin/python'), '-B', '-u', script]
    require(actor['argv'] == prefix + ['generate', '--root', str(ROOT), '--index', '0',
                                      '--segment', str(segment)], 'exact_generation_only_argv')
    require(supervisor['argv'] == prefix + ['supervise', '--root', str(ROOT), '--index', '0'],
            'exact_lane_supervisor_argv')
    require(actor['uid'] == supervisor['uid'] == os.getuid(), 'same_owned_uid')
    require(actor['parent'] == supervisor['pid'], 'exact_parent_child')
    require(actor['cvd'] == [UUID] and supervisor['cvd'] == [''], 'exact_GPU_and_CPU_bindings')


def checkpoint(path):
    path = Path(path)
    commit = read(path / 'COMMIT.json')
    require(commit['metadata']['update'] == 15460, 'unchanged_generation_seed')
    require(commit['metadata']['optimizer_preserved'] is True
            and commit['metadata']['rng_per_rank'] is True, 'AdamW_and_rank_RNG_required')
    require({'optimizer.pt', 'rank0.pt', 'rank1.pt', 'adapter/adapter_model.safetensors'}
            <= commit['files'].keys(), 'complete_saved_training_state')
    for name, digest in commit['files'].items():
        target = path / name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,
                'checkpoint_relative_path')
        require(not target.is_symlink() and sha(target) == digest, 'checkpoint_file_hash:' + name)
    return dict(commit=ref(path / 'COMMIT.json'), files=commit['files'],
                optimizer='SAVED_ANCESTRAL_ADAMW_NOT_ACTIVE_GENERATOR',
                rng='SAVED_ANCESTRAL_RANK_RNG_NOT_LIVE_GENERATION_RNG')


def provenance():
    require(sha(ROOT / 'FORKS.json') == FORKS_SHA, 'frozen_forks')
    forks = read(ROOT / 'FORKS.json')
    require(forks['node'] == 'ovx2' and forks['lanes'] == [0], 'only_authorized_physical0')
    require(forks['uuid_by_index'][0] == UUID, 'bound_uuid')
    require(forks['lease_end_unix'] == 1789689600
            and forks['hard_deadline_unix'] == 1789668000, 'actual_lease_receipt')
    require(time.time() < forks['hard_deadline_unix'] - 600, 'lease_snapshot_headroom')
    wrapper = ROOT / 'orch_r119_l1_generation_resume.py'
    generator = BASE / ('orch_r119_l1_generation_20260915_attempt1/predecessor/'
                        'generation_v3/source/orch_r109_l1_generation_v3.py')
    require(sha(wrapper) == WRAPPER_SHA == forks['wrapper_sha256'], 'reviewed_generation_wrapper')
    require(sha(generator) == GENERATOR_SHA == forks['generator_sha256'], 'reviewed_generator')
    saved = checkpoint(forks['checkpoint'])
    view = Path(forks['origin_view']) / 'input/checkpoint'
    require(sha(view / 'COMMIT.json') == forks['checkpoint_commit_sha256']
            == saved['commit']['sha256'], 'mounted_seed_same_saved_checkpoint')
    checkpoint(view)
    return dict(forks=ref(ROOT / 'FORKS.json'), sources=[ref(wrapper), ref(generator)],
                seed=saved, seed_view=str(view), active_optimizer_updates=0,
                lease_end_utc='2026-09-18T00:00:00Z', hard_end_utc='2026-09-17T18:00:00Z')


def frontier(directory):
    directory = Path(directory)
    progress = read(directory / 'PROGRESS.json')
    intents = {int(path.stem.split('_')[1]): path for path in directory.glob('INTENT_*.json')}
    calls = {int(path.stem.split('_')[1]): path for path in directory.glob('CALL_*.json')}
    require(not list(directory.glob('FAILED_*.json')), 'failed_generation_not_clean_boundary')
    expected = set(range(progress['inherited_calls'] + 1, progress['calls'] + 1))
    require(bool(expected) and intents.keys() == calls.keys() == expected,
            'later_or_missing_work_after_saved_cursor')
    for number in sorted(expected):
        intent, call = read(intents[number]), read(calls[number])
        require(intent['cumulative_call'] == call['cumulative_call'] == number,
                'exact_call_numbers')
        require(all(call[key] == value for key, value in intent.items()), 'intent_response_join')
        require('response' in call and 'outcome' in call and 'error' not in call,
                'complete_native_result_required')
        require(call['finished_unix'] <= progress['finished_unix'], 'result_after_saved_cursor')
    return dict(progress=ref(directory / 'PROGRESS.json'), cursor=progress,
                calls=len(calls), outstanding_intents=0, optimizer_updates=0)


def math_frontier(directory, actor, lane=MATH_LANE):
    directory, lane = Path(directory), Path(lane)
    complete = read(directory / 'COMPLETE.json')
    after = read(directory / 'AFTER.json')
    expected_process = [actor['boot_id'], actor['pid'], int(actor['start_ticks'])]
    require(complete['status'] == 'COMPLETE' and complete['process'] == after['process'] == expected_process,
            'completed_same_resident_phase')
    require(complete['weight_writes'] == 0 and complete['adapter'] is None and complete['optimizer'] is None
            and after['actual_mounted_base_verified'] is True and after['adapter'] is None
            and after['optimizer'] is None
            and after['base_sha256'] == 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992',
            'verified_BASE_only_boundary')
    require(not (directory / 'FAILED.json').exists(), 'failed_phase_not_retirable')
    calls = sorted(directory.glob('CALL_*.json'))
    require(len(calls) == complete.get('new_child_calls', complete['child_calls']) == 8,
            'whole_new_eight_call_phase_only')
    for path in calls:
        call = read(path)
        require('response' in call and 'outcome' in call and 'error' not in call
                and call['process'] == expected_process and call['updates'] == 0
                and call['finished_unix'] <= complete['finished_unix'], 'complete_phase_call')
    ledgers = {}
    for kind in ('NATIVE', 'PARENT'):
        path = lane / f'CALLS_{kind}.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
        require(bool(rows) and all(row['reserved_unix'] <= complete['finished_unix'] for row in rows),
                'later_charge_after_saved_phase')
        if kind == 'NATIVE':
            require(max(row['index'] for row in rows) == max(int(path.stem.split('_')[1]) for path in calls),
                    'latest_native_charge_is_saved_call')
        ledgers[kind] = ref(path)
    state_directory = (directory if complete['phase'] == 'experience'
                       else directory.parent / 'experience')
    state_complete = read(state_directory / 'COMPLETE.json')
    require(sha(state_directory / 'STATE.json') == state_complete['state_sha256'], 'exact_latest_state')
    require(state_complete['process'] == expected_process, 'same_resident_saved_state')
    for path in (lane / 'R119_LEASE_V3').glob('cycle*/*/REQUEST.json'):
        require(read(path)['started_unix'] <= complete['finished_unix'], 'later_phase_request')
    return dict(progress=ref(directory / 'COMPLETE.json'), cursor=complete, calls=len(calls),
                state=ref(state_directory / 'STATE.json'), after=ref(directory / 'AFTER.json'),
                ledgers=ledgers, outstanding_intents=0, optimizer_updates=0)


def math_setup(request):
    plan = read(MATH_OUTPUT / 'PLAN.json')
    require(plan['index'] == 1 and plan['root'] == str(MATH_LANE) and plan['uuid'] == MATH_UUID,
            'exact_math_lane_plan')
    require(plan['context_only'] is True and plan['no_weight_writes'] is True, 'math_inference_only')
    require(plan['clock']['lease_end_unix'] == 1789689600
            and time.time() < plan['clock']['hard_deadline_unix'] - 600, 'math_lease_headroom')
    wrapper = MATH_SOURCE / 'orch_math_feedback_uptake_r119_old.py'
    native = MATH_SOURCE / 'orch_math_feedback_uptake_r119_old_native.py'
    require(sha(wrapper) == MATH_WRAPPER_SHA and sha(native) == MATH_NATIVE_SHA, 'reviewed_math_sources')
    for path, digest in plan['source_files'].items():
        require(sha(path) == digest, 'immutable_math_source')
    require(sha(MATH_ROOT / 'FAMILY_READY.json') == plan['original_lease_receipt_sha256'], 'original_math_lease')
    actor, supervisor = request['actor'], request['supervisor']
    require(actor['argv'] == [str(BASE / 'v2/venv/bin/python'), '-B', str(wrapper), 'resident', '--index', '1']
            and supervisor['argv'] == ['python3', '-B', str(wrapper), 'guard', '--index', '1'],
            'exact_math_resident_guard')
    require(actor['uid'] == supervisor['uid'] == os.getuid() and actor['parent'] == supervisor['pid']
            and actor['cvd'] == [MATH_UUID] and supervisor['cvd'] == [''], 'owned_math_identity_bindings')
    phase = max(MATH_OUTPUT.glob('cycle*/*/REQUEST.json'), key=lambda path: read(path)['started_unix']).parent
    proof = dict(plan=ref(MATH_OUTPUT / 'PLAN.json'), lease=ref(MATH_ROOT / 'FAMILY_READY.json'),
                 sources=[ref(path) for path in plan['source_files']], active_optimizer_updates=0)
    return dict(proof=proof, directory=phase, marker='COMPLETE.json', uuid=MATH_UUID,
                files=[MATH_LANE, MATH_ROOT / 'FAMILY_READY.json', *plan['source_files']],
                boundary=lambda: math_frontier(phase, actor),
                missing=dict(live_generation_RNG='NOT_EXPORTED_BY_ORIGINAL_RUNTIME; NO_BITWISE_RESUME_CLAIM',
                             OWN_CARRY='STATE_MEMORY_EPISODES_DIALOGUE_PRESERVED_IN_FULL',
                             active_AdamW='ABSENT_BY_FROZEN_BASE_RUNTIME', adapter='ABSENT_FROZEN_BASE'))


def checked_reference(record):
    require(sha(record['path']) == record['sha256'], 'reference_hash:' + record['path'])
    return read(record['path'])


def shared_seed():
    require(sha(SHARED_SEED / 'CHECKPOINT.json') ==
            '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d', 'shared_seed_checkpoint')
    document = read(SHARED_SEED / 'CHECKPOINT.json')
    require(document['complete'] is True and document['optimizer_rng_sha256'] ==
            '2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5', 'shared_seed_AdamW_RNG')
    require(sha(SHARED_SEED / 'optimizer_rng.pt') == document['optimizer_rng_sha256'], 'saved_AdamW_RNG_bytes')
    for name, digest in document['adapter']['files']:
        require(Path(name).name == name and sha(SHARED_SEED / 'adapter' / name) == digest, 'saved_shared_adapter')
    return ref(SHARED_SEED / 'CHECKPOINT.json')


def code_command(physical, phase):
    root = CODE_BASE / f'ovx2_{physical}'
    arguments = ['gpu.orch_r126_code_capacity', phase, '--root', str(root)]
    code = (f"import sys,runpy;sys.path.insert(0,{str(CODE_DEPENDENCY)!r});import gpu;"
            f"gpu.__path__.insert(0,{str(CODE_BASE / 'source/gpu')!r});sys.argv={arguments!r};"
            "runpy.run_module('gpu.orch_r126_code_capacity',run_name=\"__main__\")")
    return [str(BASE / 'v2/venv/bin/python'), '-B', '-c', code]


def code_frontier(root, chunk):
    root = Path(root)
    plan = read(root / 'PLAN.json')
    complete_path = root / f'CHUNK_{chunk:03d}_COMPLETE.json'
    complete = read(complete_path)
    carry_path = root / f'CHUNK_{chunk:03d}_CARRY_PRIVATE.json'
    carry = read(carry_path)
    require(complete['chunk'] == chunk and complete['optimizer_updates'] == 0, 'saved_chunk_without_updates')
    cohort = checked_reference(plan['cohorts'])['chunks'][chunk]
    require(cohort['chunk'] == chunk, 'exact_chunk_registry')
    rows = checked_reference(cohort['cohort'])
    last_cycle = max(row['cycle'] for row in rows)
    require(last_cycle == cohort['last_cycle'], 'exact_last_chunk_cycle')
    lane = root / 'campaign_code_parent'
    last = read(lane / f'CYCLE_{last_cycle:03d}_COMPLETE.json')
    context = read(lane / f'CONTEXT_DISTILLATION_C{last_cycle:03d}.json')
    require(last['cycle'] == last_cycle and last['status'] == 'COMPLETE' and last['updates'] == 0,
            'last_cycle_saved')
    require(context['status'] == 'COMPLETE' and context['weight_updates'] == 0
            and carry['own_context'] == context['own_context'] and isinstance(carry['lessons'], list),
            'complete_saved_context_and_lessons')
    require(last['no_adapter'] == read(root / 'ACTOR_READY.json')['model'], 'cycle_verified_readonly_identity')
    cells = [read(path) for path in (lane / 'cells').glob('*.json')]
    require(bool(cells) and all(row['cycle'] <= last_cycle for row in cells), 'later_cycle_work_after_chunk')
    counts = Counter(row['kind'] for row in cells)
    require(set(counts) <= {'NATIVE', 'PARENT'} and complete['cumulative_counts'] ==
            {kind: plan['ancestry'][kind.lower() + '_used'] + counts[kind] for kind in ('NATIVE', 'PARENT')},
            'saved_chunk_charge_frontier')
    for row in cells:
        require(row['started_unix'] <= complete['finished_unix'], 'cell_after_saved_chunk')
        if row['kind'] == 'NATIVE':
            require(row['status'] == 'COMPLETE' and 'response' in row and 'error_type' not in row
                    and row['finished_unix'] <= complete['finished_unix'], 'unfinished_native_after_chunk')
    return dict(progress=ref(complete_path), cursor=complete, carry=ref(carry_path),
                last_cycle=last_cycle, cells=len(cells), pending_parents=sum(row['kind'] == 'PARENT'
                and row['status'] == 'PENDING' for row in cells), optimizer_updates=0)


def code_setup(request):
    physical = request['physical']
    require(physical in (3, 4, 5, 6), 'only_owned_code_lanes')
    root = CODE_BASE / f'ovx2_{physical}'
    plan, armed = read(root / 'PLAN.json'), read(root / 'ARM.json')
    require(plan['root'] == str(root) and plan['physical'] == physical and plan['wrapper'] == 'ovx2'
            and plan['gpu_uuid'] == DEVICES[physical] and plan['optimizer_updates'] == 0,
            'exact_readonly_code_plan')
    require(plan['lease_end_unix'] == 1789689600 and plan['hard_end_unix'] == 1789668000,
            'bound_code_lease')
    require(sha(CODE_BASE / 'source/gpu/orch_r126_code_capacity.py') ==
            'd32303b47954f9fda5093f284e7bc2441d6b93e3955c8f929e4e6649d0b54149'
            and sha(CODE_DEPENDENCY / 'gpu/orch_r119_code_old_fork.py') ==
            'f5891b07fa11de7706c6970369f9c8f22f0e7defa20c44752f1d4c801fcaf889', 'reviewed_readonly_code_sources')
    sources = dict(plan['source_files'], **armed['source_files'])
    require(all(armed['source_files'].get(path, digest) == digest
                for path, digest in plan['source_files'].items()), 'consistent_code_source_pins')
    for path, digest in sources.items():
        require(sha(path) == digest, 'frozen_code_source')
    checked_reference(plan['inputs']['lease'])
    seed = shared_seed()
    for name, digest in plan['adapter']['files']:
        require(Path(name).name == name and sha(Path(plan['adapter']['path']) / name) == digest,
                'mounted_frozen_code_adapter')
    actor, supervisor = request['actor'], request['supervisor']
    require(actor['argv'] == code_command(physical, 'native')
            and supervisor['argv'] == code_command(physical, 'watch'), 'exact_code_native_custodian')
    require(actor['uid'] == supervisor['uid'] == os.getuid() and actor['parent'] == supervisor['pid']
            and actor['cvd'] == [DEVICES[physical]] and supervisor['cvd'] == [''], 'owned_code_bindings')
    chunks = sorted(root.glob('CHUNK_*_COMPLETE.json'))
    chunk = read(chunks[-1])['chunk'] + 1 if chunks else 0
    require(chunk < 64, 'next_existing_chunk_only')
    proof = dict(plan=ref(root / 'PLAN.json'), arm=ref(root / 'ARM.json'), lease=plan['inputs']['lease'],
                 seed=seed, next_chunk=chunk, sources=[ref(path) for path in sources], active_optimizer_updates=0)
    return dict(proof=proof, directory=root, marker=f'CHUNK_{chunk:03d}_COMPLETE.json', uuid=DEVICES[physical],
                files=[root, SHARED_SEED, Path(plan['adapter']['path']).parent, *sources],
                boundary=lambda: code_frontier(root, chunk), missing=dict(
                    active_AdamW='ABSENT_IN_LIVE_ELICITATION; SHARED_ANCESTRAL_AdamW_RNG_COPIED',
                    live_generation_RNG='NOT_EXPORTED; NO_BITWISE_RESUME_CLAIM',
                    OWN_CARRY='EXACT_CHUNK_CARRY_PRIVATE_WITH_LESSONS_AND_FULL_HISTORY',
                    pending_parent_results='PRESERVED_AS_PENDING; ORIGINAL_ROOT_RETAINED_FOR_LATE_RESULTS'))


def grid_frontier(root, cycle):
    root = Path(root)
    marker = root / 'lease_budget_r119_learned' / f'C{cycle:04d}_CONTINUED.json'
    complete = read(marker)
    require(complete['cycle'] == cycle and complete['optimizer_steps'] == 0, 'saved_readonly_grid_cycle')
    require(complete['carry']['path'] == str(root / 'CARRY.json')
            and complete['ledger']['path'] == str(root / 'LEDGER.jsonl'), 'exact_grid_paths')
    carry = checked_reference(complete['carry'])
    require(sha(root / 'LEDGER.jsonl') == complete['ledger']['sha256'], 'later_grid_charge_after_saved_boundary')
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    require(bool(rows) and max(row['cycle'] for row in rows) == cycle, 'exact_grid_last_cycle')
    for row in rows:
        if row['cycle'] == cycle and row['kind'] == 'NATIVE':
            call = read(root / 'calls' / f'N{row["number"]:05d}.json')
            require(call['status'] == 'COMPLETE' and 'response' in call, 'complete_grid_native_results')
    return dict(progress=ref(marker), cursor=dict(complete, finished_unix=complete['observed_unix']),
                carry=complete['carry'], ledger=complete['ledger'], carry_items=len(carry), optimizer_updates=0)


def grid_setup(request):
    wrapper = GRID_SOURCE / 'orch_r119_grid_lease_resume.py'
    for name, digest in {'orch_r119_grid_lease_resume.py': '449d0208a47bc14cf84d70410ebf2950c2fcc40285c6ada3f1b4fa4ac9c3f403',
                         'orch_r119_grid_continuation.py': '9de64111bc02c2db61050e36aa244bc8c558440b7682ac8699f4590515d9439b',
                         'orch_r119_grid_learned_fork.py': '20f403f51196a024e817ca2dc75dda69121768eda66e71da624e15cf3e1c401f'}.items():
        require(sha(GRID_SOURCE / name) == digest, 'reviewed_grid_source')
    config = read(GRID_ROOT / 'CONFIG.json')
    require(config['optimizer_steps'] == 0 and config['physical'] == 7 and config['uuid'] == DEVICES[7]
            and config['lease_end_unix'] == 1789689600, 'exact_inference_grid_config')
    manifest = GRID_OLD_SOURCE / 'R118_NODE3_7_SOURCE_SHA256.json'
    require(sha(manifest) == config['source_manifest_sha256'], 'frozen_grid_dependency_manifest')
    for name, digest in read(manifest).items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and sha(GRID_OLD_SOURCE / name) == digest, 'frozen_grid_dependency')
    for name, digest in config['inputs'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and sha(GRID_ROOT / name) == digest, 'frozen_grid_input')
    lease_path = GRID_ROOT / 'lease_budget_r119_learned/LEASE_BUDGET.json'
    require(sha(lease_path) == '919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770',
            'exact_grid_lease_receipt')
    actor, supervisor, timer = request['actor'], request['supervisor'], request['timer']
    tail = ['--physical', '7', '--old-source', str(GRID_OLD_SOURCE)]
    require(actor['argv'] == [str(BASE / 'v2/venv/bin/python'), '-B', str(wrapper), 'native'] + tail
            and supervisor['argv'] == ['python3', '-B', str(wrapper), 'guard'] + tail,
            'exact_grid_native_and_guard')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and timer['argv'][4:] == actor['argv'], 'exact_own_grid_timeout')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
            and actor['uid'] == timer['uid'] == supervisor['uid'] == os.getuid()
            and actor['cvd'] == timer['cvd'] == [DEVICES[7]] and supervisor['cvd'] == [''], 'own_grid_process_chain')
    seed = shared_seed()
    folder = GRID_ROOT / 'lease_budget_r119_learned'
    loaded = read(folder / 'LOADED.json')
    require(loaded['pid'] == actor['pid'] and loaded['optimizer_steps'] == 0
            and loaded['no_adapter']['local_optimizer'] is None
            and loaded['no_adapter']['mode'] == 'LEARNED_CHILD_FROZEN_LORA_ELICITATION_ONLY',
            'actual_grid_loaded_frozen_fork')
    latest = read(sorted(folder.glob('C*_CONTINUED.json'))[-1])
    cycle = latest['cycle'] + 1
    return dict(proof=dict(config=ref(GRID_ROOT / 'CONFIG.json'), lease=ref(lease_path), seed=seed,
                           next_cycle=cycle, sources=[ref(path) for path in GRID_SOURCE.glob('*.py')],
                           active_optimizer_updates=0), directory=folder, marker=f'C{cycle:04d}_CONTINUED.json',
                uuid=DEVICES[7], helpers=[('timer', timer)], files=[GRID_ROOT, SHARED_SEED, GRID_SOURCE, GRID_OLD_SOURCE],
                boundary=lambda: grid_frontier(GRID_ROOT, cycle), missing=dict(
                    active_AdamW='ABSENT_IN_LIVE_FROZEN_FORK; ANCESTRAL_AdamW_RNG_COPIED',
                    live_generation_RNG='NOT_EXPORTED; NO_BITWISE_RESUME_CLAIM',
                    OWN_CARRY='EXACT_CARRY_AND_ALL_LEDGER_CALL_PARENT_HISTORY_PRESERVED'))


def stopped(expected):
    same(expected)
    directory = Path('/proc') / str(expected['pid']) / 'task'
    return all((task / 'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't')
               for task in directory.iterdir())


def pause(expected, descriptor):
    same(expected)
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    deadline = time.monotonic() + 5
    while not stopped(expected):
        require(time.monotonic() < deadline, 'all_threads_stop_timeout')
        time.sleep(0.01)


def archive(paths, destination):
    paths = [Path(path) for path in paths]
    files = []
    for root in paths:
        files.extend([root] if root.is_file() else sorted(root.rglob('*')))
    require(not any(path.is_symlink() for path in files), 'unresolved_archive_symlink')
    files = sorted({path for path in files if path.is_file()})
    required = sum(path.stat().st_size for path in files)
    space = os.statvfs(destination.parent)
    require(space.f_bavail * space.f_frsize > required * 2 + 1024 ** 3, 'snapshot_disk_headroom')
    manifest = {str(path): ref(path) for path in files}
    with tarfile.open(destination, 'x') as output:
        for path in files:
            output.add(path, arcname=str(path).lstrip('/'), recursive=False)
    with destination.open('rb') as stream:
        os.fsync(stream.fileno())
    with tarfile.open(destination, 'r') as saved:
        require(len(saved.getmembers()) == len(manifest), 'archive_member_count')
        for entry in saved:
            require(entry.isfile(), 'archive_regular_files_only')
            digest = hashlib.sha256()
            with saved.extractfile(entry) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            require(digest.hexdigest() == manifest['/' + entry.name]['sha256'], 'archive_bytes_verified')
    require(all(sha(path) == record['sha256'] for path, record in manifest.items()),
            'source_changed_during_preservation')
    destination.chmod(0o444)
    return dict(archive=ref(destination), files=manifest)


def inspect_remote():
    physical = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid',
                                       '--format=csv,noheader'], text=True).splitlines()
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                   '--format=csv,noheader'], text=True).splitlines()
    processes = {}
    for line in apps:
        device, raw_pid = [part.strip() for part in line.split(',')]
        pid = int(raw_pid)
        chain = []
        for depth in range(3):
            if pid <= 1:
                break
            try:
                record = identity(pid)
            except (FileNotFoundError, ProcessLookupError, PermissionError) as error:
                chain.append(dict(pid=pid, error=type(error).__name__))
                break
            chain.append(record)
            pid = record['parent']
        processes[raw_pid.strip()] = dict(uuid=device, chain=chain)
    return dict(observed_utc=utc(), gpu_map=physical, processes=processes, read_only=True)


def fresh_release(output, physical=0):
    require(physical in DEVICES, 'reviewed_scanner_only')
    if physical == 0:
        forks = read(ROOT / 'FORKS.json')
        suffix = ['PYTHONPATH=' + forks['pythonpath'], 'python3', '-B', forks['node3_scanner']]
    elif physical == 1:
        library = BASE / 'orch_rich_hot_node3_20260915_base107_refill1536/source'
        suffix = ['PYTHONPATH=' + str(library), 'python3', '-B',
                  str(MATH_SOURCE / 'orch_math_feedback_uptake_r119_old_scan.py'), '--index', '1']
    elif physical in (3, 4, 5, 6):
        suffix = ['PYTHONPATH=' + str(CODE_DEPENDENCY)] + code_command(physical, 'scan')
    else:
        suffix = ['PYTHONPATH=' + str(GRID_OLD_SOURCE), 'python3', '-B',
                  str(GRID_SOURCE / 'orch_r119_grid_lease_resume.py'), 'scan', '--physical', '7',
                  '--old-source', str(GRID_OLD_SOURCE)]
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1'] + suffix
    for attempt in range(10):
        result = json.loads(subprocess.check_output(command, text=True, timeout=90))
        result.pop('host', None)
        immutable(output / ('SCAN_' + str(time.time_ns()) + '.json'), result)
        if result['clear'] is True:
            require(result['scanner_euid'] == 0 and result['gpu']['uuid'] == DEVICES[physical]
                    and result['gpu']['index'] == physical, 'privileged_exact_UUID_required')
            return result
        reasons = result.get('blocking_reasons', [])
        retryable = bool(reasons) and all(reason == 'device_not_idle' or reason.startswith(
            ('process_identity_drift:', 'minor_scan_identity_changed:', 'minor_scan_process_drift:'))
            for reason in reasons)
        if not retryable:
            break
        time.sleep(2)
    raise ValueError('privileged_physical_UUID_release_not_proven')


def verify_release_remote(request):
    output = Path(request['evidence_root'])
    require(output.parent == BASE / 'orch_r133_retirement_20260916'
            and output.name.startswith(tuple(f'physical{index}_' for index in DEVICES)), 'exact_retirement_evidence_root')
    original = read(output / 'REQUEST.json')['request']
    require(original['node'] == 'ovx2' and original['physical'] in DEVICES, 'only_original_reviewed_lane')
    physical = original['physical']
    require(not alive(original['actor']) and not alive(original['supervisor']), 'both_original_processes_exited')
    require('timer' not in original or not alive(original['timer']), 'own_timer_also_exited')
    saved = read(output / 'PRESERVATION.json')
    require(saved['archive']['path'] == str(output / 'STATE.tar')
            and sha(output / 'STATE.tar') == saved['archive']['sha256'], 'verified_preserved_archive')
    boundary = read(output / 'BOUNDARY.json')
    if physical == 0:
        current = frontier(ROOT / 'gpu0' / f'segment{original["segment"]:04d}' / 'gpu0')
    elif physical == 1:
        current = math_frontier(Path(boundary['progress']['path']).parent, original['actor'])
    elif physical in (3, 4, 5, 6):
        current = code_frontier(CODE_BASE / f'ovx2_{physical}', boundary['cursor']['chunk'])
    else:
        current = grid_frontier(GRID_ROOT, boundary['cursor']['cycle'])
    require(current == boundary, 'no_later_work_after_preserved_boundary')
    result = fresh_release(output, physical)
    receipt = dict(status='RELEASED', uuid=result['gpu']['uuid'], physical=physical, released_utc=utc(),
                   actor=original['actor'], disabled_supervisor=original['supervisor'],
                   scanner_summary={key: result[key] for key in ('clear', 'scanner_euid', 'gpu', 'finished_unix')},
                   preservation=ref(output / 'PRESERVATION.json'), evidence_root=str(output),
                   recovered_verification_only=True, other_lanes_touched=False, launched_children=False)
    immutable(output / 'RELEASED.json', receipt)
    return receipt


def retire_remote(request):
    require(request['node'] == 'ovx2' and type(request['physical']) is int
            and request['physical'] in DEVICES, 'unsupported_lane_no_signal')
    require(request['gate']['cpu_passed'] is True and '[Builder]' in request['gate']['builder_line']
            and request['gate']['builder_line'].startswith('2026-09-16'), 'dated_CPU_Builder_gate')
    actor, supervisor = request['actor'], request['supervisor']
    physical = request['physical']
    if physical == 0:
        proof = provenance()
        segment = request['segment']
        check_pair(actor, supervisor, segment)
        directory = ROOT / 'gpu0' / f'segment{segment:04d}' / 'gpu0'
        setup = dict(proof=proof, directory=directory, marker='PROGRESS.json', uuid=UUID,
                     files=[ROOT / 'gpu0', ROOT / 'FORKS.json', Path(proof['seed']['commit']['path']).parent,
                            *(entry['path'] for entry in proof['sources'])], boundary=lambda: frontier(directory),
                     missing=dict(live_generation_RNG='NOT_EXPORTED_BY_ORIGINAL_RUNTIME; NO_BITWISE_RESUME_CLAIM',
                                  OWN_CARRY='NOT_A_FIELD_IN_THIS_GENERATOR; FULL_EPISODES_AND_PROGRESS_PRESERVED',
                                  active_AdamW='ABSENT; ORIGINAL_SAVED_ADAMW_AND_RANK_RNG_COPIED'))
    elif physical == 1:
        setup = math_setup(request)
        proof, directory = setup['proof'], setup['directory']
    else:
        setup = code_setup(request) if physical in (3, 4, 5, 6) else grid_setup(request)
        proof, directory = setup['proof'], setup['directory']
    same(actor)
    same(supervisor)
    helpers = setup.get('helpers', [])
    for label, record in helpers:
        same(record)
    pause_order = [('supervisor', supervisor), *helpers, ('actor', actor)]
    exit_order = [('actor', actor), *reversed(helpers), ('supervisor', supervisor)]
    output = BASE / 'orch_r133_retirement_20260916' / (f'physical{physical}_' + str(time.time_ns()))
    output.mkdir(parents=True, exist_ok=False)
    immutable(output / 'REQUEST.json', dict(request=request, provenance=proof, observed_utc=utc()))
    started = time.time()
    require(1 <= request['wait_seconds'] <= 10800
            and time.time() + request['wait_seconds'] + 600 < 1789668000, 'bounded_wait_inside_lease')
    deadline = time.monotonic() + request['wait_seconds']
    library = ctypes.CDLL(None, use_errno=True)
    watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    require(watch >= 0, 'inotify_available')
    descriptors = {}
    paused = []
    retired = False
    def interrupted(signum, frame):
        raise SystemExit('operator_interrupted_resume_owned_processes')
    old_handlers = {signum: signal.signal(signum, interrupted)
                    for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        require(library.inotify_add_watch(watch, os.fsencode(directory), 0x8 | 0x80) >= 0,
                'watch_exact_saved_cursor_directory')
        for label, record in pause_order:
            descriptors[label] = os.pidfd_open(record['pid'])
            same(record)
        attempt = 0
        while time.monotonic() < deadline:
            readable, _, _ = select.select([watch], [], [], min(1, max(0, deadline-time.monotonic())))
            if not readable:
                same(actor)
                same(supervisor)
                continue
            events = os.read(watch, 65536)
            cursor, boundary_event = 0, False
            while cursor + 16 <= len(events):
                _, mask, _, length = struct.unpack_from('iIII', events, cursor)
                name = events[cursor + 16:cursor + 16 + length].rstrip(b'\0')
                boundary_event |= name == setup['marker'].encode() and bool(mask & (0x8 | 0x80))
                cursor += 16 + length
            if not boundary_event:
                continue
            attempt += 1
            try:
                for label, record in pause_order:
                    paused.append((label, record))
                    pause(record, descriptors[label])
                marker = read(directory / setup['marker'])
                require(marker.get('finished_unix', marker.get('observed_unix', 0)) >= started,
                        'next_boundary_not_historical_checkpoint')
                boundary = setup['boundary']()
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
                immutable(output / f'REJECTED_{attempt:04d}.json', dict(reason=str(error), observed_utc=utc()))
                for label, record in reversed(paused):
                    signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                paused.clear()
                continue
            immutable(output / 'BOUNDARY.json', boundary)
            saved = archive(setup['files'], output / 'STATE.tar')
            require(setup['boundary']() == boundary, 'frontier_unchanged_after_snapshot')
            immutable(output / 'PRESERVATION.json', dict(**saved, **setup['missing'],
                generation_only=True, preserved_utc=utc()))
            for label, record in exit_order:
                same(record)
                signal.pidfd_send_signal(descriptors[label], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                if label != 'supervisor':
                    require(bool(select.select([descriptors[label]], [], [], 30)[0]),
                            'owned_child_exit_before_guard_cleanup')
            exit_deadline = time.monotonic() + 30
            while not all(select.select([descriptor], [], [], 0)[0]
                          for descriptor in descriptors.values()):
                require(time.monotonic() < exit_deadline, 'exit_timeout_no_KILL_escalation')
                time.sleep(0.1)
            paused.clear()
            result = fresh_release(output, physical)
            receipt = dict(status='RELEASED', uuid=setup['uuid'], physical=physical, released_utc=utc(),
                           actor=actor, disabled_supervisor=supervisor,
                           disabled_helpers=[record for label, record in helpers],
                           scanner_summary={key: result[key] for key in ('clear', 'scanner_euid', 'gpu', 'finished_unix')},
                           preservation=ref(output / 'PRESERVATION.json'), evidence_root=str(output),
                           other_lanes_touched=False, launched_children=False)
            immutable(output / 'RELEASED.json', receipt)
            retired = True
            return receipt
        result = dict(status='WAIT_EXPIRED_NO_RETIREMENT', evidence_root=str(output),
                      observed_utc=utc(), attempts=attempt, released=[])
        immutable(output / 'WAIT_EXPIRED.json', result)
        return result
    except BaseException as error:
        immutable(output / 'ERROR.json', dict(error_type=type(error).__name__, error=str(error), observed_utc=utc()))
        raise
    finally:
        for label, record in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(watch)
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        if not retired:
            immutable(output / 'NO_RELEASE_CLAIM.json', dict(observed_utc=utc(),
                note='Inspect raw evidence and fresh GPU occupancy; no release inferred from a signal.'))


def remote(node, operation, request=None):
    require(node in ('ovx2', 'a40r', 'a100'), 'wrappers_only')
    require(operation in ('inspect', 'provenance', 'prepare-math', 'prepare-lane', 'retire', 'verify-release'), 'known_operation')
    require(operation == 'inspect' or node == 'ovx2', 'no_other_live_actuator')
    payload = base64.b64encode(json.dumps(dict(operation=operation, request=request)).encode()).decode()
    command = 'python3 -B - remote ' + shlex.quote(payload)
    result = subprocess.run(['bash', str(Path(__file__).parent / f'{node}_ssh.sh'), command],
                            input=Path(__file__).read_text(), capture_output=True, text=True,
                            timeout=(request['wait_seconds'] + 600 if operation == 'retire' else 600), check=True)
    return json.loads(result.stdout)


def post_release(receipt, output):
    require(receipt['status'] == 'RELEASED' and receipt['physical'] in DEVICES
            and receipt['uuid'] == DEVICES[receipt['physical']], 'only_verified_own_release_post')
    line = (f"\n{utc()} [Builder] R136 ovx2 physical{receipt['physical']} RELEASED "
            f"{receipt['uuid']} verified {receipt['released_utc']}; exact old actor/supervisor exited, "
            f"saved-frontier archive verified before TERM; receipt {output}. Main may allocate with "
            "fresh admission. No other node or child touched; snapshot mirror follows separately.\n")
    descriptor = os.open('research_loop/COORDINATION.md', os.O_WRONLY | os.O_APPEND)
    try:
        raw = line.encode()
        require(os.write(descriptor, raw) == len(raw), 'complete_append_only_release_line')
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def mirror_release(receipt, output):
    evidence = Path(receipt['evidence_root'])
    require(evidence.parent == BASE / 'orch_r133_retirement_20260916', 'exact_snapshot_transport_root')
    bundle = Path(output).with_suffix('.bundle.tar')
    command = 'tar -C ' + shlex.quote(str(evidence)) + ' -cf - .'
    with bundle.open('xb') as stream:
        subprocess.run(['bash', str(Path(__file__).parent / 'ovx2_ssh.sh'), command],
                       stdout=stream, check=True, timeout=600)
        stream.flush()
        os.fsync(stream.fileno())
    with tarfile.open(bundle) as archive_file:
        saved = json.load(archive_file.extractfile('./PRESERVATION.json'))
        digest = hashlib.sha256()
        with archive_file.extractfile('./STATE.tar') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        require(digest.hexdigest() == saved['archive']['sha256'], 'off_lease_state_archive_verified')
    bundle.chmod(0o444)
    immutable(Path(output).with_suffix('.mirror.json'), dict(bundle=ref(bundle),
        state_sha256=digest.hexdigest(), copied_off_lease=True, verified_utc=utc(), files=len(saved['files'])))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'remote':
        options = json.loads(base64.b64decode(sys.argv[2]))
        if options['operation'] == 'inspect':
            result = inspect_remote()
        elif options['operation'] == 'provenance':
            result = provenance()
        elif options['operation'] == 'prepare-math':
            setup = math_setup(options['request'])
            same(options['request']['actor'])
            same(options['request']['supervisor'])
            result = dict(proof=setup['proof'], directory=str(setup['directory']), marker=setup['marker'],
                          uuid=setup['uuid'], missing=setup['missing'], read_only=True)
        elif options['operation'] == 'prepare-lane':
            request = options['request']
            require(request['node'] == 'ovx2' and request['physical'] in (3, 4, 5, 6, 7), 'only_ovx2_owned_old_lane')
            setup = grid_setup(request) if request['physical'] == 7 else code_setup(request)
            for record in (request['actor'], request['supervisor'], *([request['timer']] if 'timer' in request else [])):
                same(record)
            result = dict(proof=setup['proof'], directory=str(setup['directory']), marker=setup['marker'],
                          uuid=setup['uuid'], missing=setup['missing'], read_only=True)
        elif options['operation'] == 'verify-release':
            result = verify_release_remote(options['request'])
        else:
            require(options['operation'] == 'retire', 'known_remote_operation')
            result = retire_remote(options['request'])
        print(json.dumps(result, sort_keys=True))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('inspect', 'provenance', 'prepare-math', 'prepare-lane', 'retire', 'verify-release'))
    parser.add_argument('--node', choices=('ovx2', 'a40r', 'a100'), required=True)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), 'immutable_output_already_exists')
    request = read(options.request) if options.request else None
    if options.operation == 'retire':
        require(request is not None and options.node == request['node'] == 'ovx2', 'bound_request_required')
        require(request['gate']['operator_sha256'] == sha(__file__), 'tested_operator_source')
        require(sha(request['gate']['cpu_log']['path']) == request['gate']['cpu_log']['sha256'], 'CPU_log_bytes')
        require(sha(request['gate']['provenance']['path']) == request['gate']['provenance']['sha256'],
                'CPU_provenance_receipt_bytes')
        require(request['gate']['builder_line'] in Path('research_loop/COORDINATION.md').read_text(),
                'Builder_line_must_already_be_durable')
    try:
        result = remote(options.node, options.operation, request)
    except subprocess.CalledProcessError as error:
        immutable(options.output.with_suffix('.error.json'), dict(stderr=error.stderr,
            returncode=error.returncode, observed_utc=utc(), no_release_claim=True))
        raise
    immutable(options.output, result)
    print(json.dumps(result, sort_keys=True))
    if result.get('status') == 'RELEASED':
        post_release(result, options.output)
        mirror_release(result, options.output)


if __name__ == '__main__':
    main()
