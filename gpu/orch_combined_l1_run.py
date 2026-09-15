"""Combined L1 native fit, independent held readouts, and immediate child handoff."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import astra_goal_quality_train as route
from gpu import orch_guided_native as native
from gpu import orch_l1_bootstrap_transfer_scan as scanner
from gpu import orch_rich_breadth_bootstrap_run as common
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, LEASE_END, read, sha, write
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_math_rich_source import verify_archive
from organism_v6 import orch_l2_rich_math as math_encoder
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


ROOT = Path('/localhome/local-rohing/orch_combined_l1_20260915_attempt1')
PROGRAM = 'gpu.orch_combined_l1_run'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
CELLS = ('COMBINED_FULL', 'COMBINED_OFF')
DEVICES = dict(COMBINED_FULL=(0, 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'),
    COMBINED_OFF=(1, 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b'))
HOST_SHA = scanner.policy.HOST_SHA
MANIFEST_SHA = 'b1dde49fe8b424ec6bc7ee4eafbeef44a0f4f8e6c08f7d5c749fde82b81cb852'
PACKET_SHA = 'deb5d65cab3b8ae56d63b4b302030f096fa519689b0dfb8bc9281cb9180d683b'
LAYOUT = GoalReplayLayout(2394, 16)
SECONDS = 43200
GPU_HOURS = 24
MATH_TASKS = 64
MATH_CAP = 1536
LEGACY_CAP = 160
CALLS_PER_CELL = 880
CALLS_TOTAL = 1760


def validate_corpus(root):
    assert sha(root / 'CORPUS_MANIFEST.json') == MANIFEST_SHA
    manifest = read(root / 'CORPUS_MANIFEST.json')
    assert all(sha(root / name) == digest for name, digest in manifest['files'].items())
    assert sha(root / 'PACKET/ADMITTED_ROWS.json') == PACKET_SHA
    assert manifest['rows'] == 2394 and manifest['updates'] == 19248
    assert manifest['counts'] == dict(SEQ266=1452, MATH764=764, MATH_RICH19=19,
        MATH_RECORD92=92, INTENSITY56=56, TWO_PASS9=8, FULL_RICH3=3)
    return manifest


def encode_rows(rows, tokenizer):
    assert len(rows) == 2394
    assert all(row['encoding'] == 'terse_route' and row['corpus'] == 'SEQ266' for row in rows[:1452])
    encoded = list(route.encode_new_rows([entry['row'] for entry in rows[:1452]], tokenizer))
    for position, entry in enumerate(rows[1452:], 1452):
        row = entry['row']
        if entry['encoding'] == 'rich_route':
            student = row['student']
            assert student['messages'][-1] == dict(role='assistant', content=student['target'])
            material = dict(student_prefix=student['messages'][:-1], target=student['target'])
        else:
            assert entry['encoding'] == 'math'
            material = row
        try:
            result = math_encoder.encode_rows([material], tokenizer)[0]
            if entry['encoding'] == 'rich_route':
                assert len(result.input_ids) <= 2048
            encoded.append(result)
        except BaseException as error:
            raise ValueError(f'combined_native_encoding_row_{position}_{entry["corpus"]}:{error}') from error
    return tuple(encoded)


def prepare(root):
    assert root == ROOT and socket.gethostname() == 'a4u8g-0147'
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not (root / 'PREPARE.json').exists()
    manifest = validate_corpus(root)
    prior = read(Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1/PREPARE.json'))
    portable = common.portable.read_manifest(prior['bundle'], expected_manifest_sha256=BUNDLE_SHA)
    base = common.portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    identity = common.bridge.AdapterIdentity(str(Path(prior['bundle']) / 'adapter'), common.portable.PARENT_STATE,
        portable['expected_base_sha256'], tuple(portable['adapter_files'].items())).verify()
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    legacy = legacy_encode(root, tokenizer)
    new = encode_rows(read(root / 'PACKET/ADMITTED_ROWS.json'), tokenizer)
    encoded = native.assemble_replay(legacy, new, LAYOUT, legacy_reference=legacy,
        eos_token_id=tokenizer.eos_token_id)
    write(root / 'ENCODER_CHECK.json', dict(status='PASS', rows=len(new), model_loaded=False,
        native_calls=0, row_masks=[asdict(row) for row in new]))
    audit = common.token_audit(encoded, LAYOUT, tokenizer.pad_token_id)
    audit['layout'] = LAYOUT.manifest('FULL_TARGET')
    write(root / 'TOKEN_AUDIT.json', {'2394': audit})
    cohort = read(root / 'COHORT.json')
    assert len(cohort['tasks']) == len(cohort['prompts']) == MATH_TASKS
    lengths = [len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
        return_dict=False)) for messages in cohort['prompts']]
    assert max(lengths) <= 2048
    names = ('CORPUS_MANIFEST.json', 'PROTOCOL.md', 'USER_RELAY.md', 'SERVICE_IDENTITY.json',
        'ENCODER_CHECK.json', 'TOKEN_AUDIT.json', 'ALLOCATION_ESTIMATE.json')
    write(root / 'PREPARE.json', dict(status='CPU_PREPARED_NO_MODEL', native_calls=0, fits=0,
        initial=identity.document(), bundle=prior['bundle'], model_dir=prior['model_dir'], base_verification=base,
        recipe=common.RECIPE, cells=CELLS, corpus=manifest['counts'], math_prompt_lengths=lengths,
        files={name: sha(root / name) for name in names}, source_sha256=sha(root / 'source.tar'),
        source_files=verify_archive(root / 'source.tar', root / 'source'), updates_per_fit=LAYOUT.updates,
        seconds=SECONDS, assigned_gpu_hours=GPU_HOURS, lease_end_unix=LEASE_END,
        lease_margin_seconds=21600, readout_calls=CALLS_TOTAL, parent_calls=0, training_generation=0,
        prepared_unix=time.time()))
    print(json.dumps(dict(status='CPU_PREPARED_NO_MODEL', prepare_sha256=sha(root / 'PREPARE.json'),
        encoder_sha256=sha(root / 'ENCODER_CHECK.json'), tokens={key: value for key, value in audit.items()
            if key.endswith('_tokens')}, updates=LAYOUT.updates), indent=2))


def validate_inputs(root):
    assert root == ROOT and socket.gethostname() == 'a4u8g-0147' and not root.is_symlink()
    prepared = read(root / 'PREPARE.json')
    assert prepared['status'] == 'CPU_PREPARED_NO_MODEL' and prepared['native_calls'] == 0
    assert sha(root / 'source.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files']
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    validate_corpus(root)
    assert prepared['recipe'] == common.RECIPE and prepared['initial']['state_sha256'] == common.portable.PARENT_STATE
    return prepared


def layout_for(cell):
    assert cell in CELLS
    return LAYOUT


def configure():
    common.policy = sys.modules[__name__]
    common.ROOT = ROOT
    common.PROGRAM = PROGRAM
    common.layout_for = layout_for
    common.packet_name = lambda cell: 'ADMITTED_ROWS.json'
    common.validate_inputs = validate_inputs
    common.encoding = SimpleNamespace(encode_rows=encode_rows, digest=math_encoder.digest)


def handoff(root):
    complete = read(root / 'COMBINED_FULL/fit/COMPLETE.json')
    assert complete['status'] == 'COMPLETE' and complete['updates'] == LAYOUT.updates
    adapter = common.bridge.AdapterIdentity.from_document(complete['output_adapter'])
    assert adapter.state_sha256 != complete['input_adapter']['state_sha256']
    path = root / 'FULL_CHILD_HANDOFF.json'
    assert not path.exists()
    write(path, dict(schema='COMBINED_L1_FULL_CHILD_READY_V1', recipient='Anscombe',
        status='FIT_COMPLETE_HELD_SCORES_NOT_REQUIRED', adapter=adapter.document(),
        child_path=adapter.path, input_adapter=complete['input_adapter'],
        complete_path=str(root / 'COMBINED_FULL/fit/COMPLETE.json'),
        complete_sha256=sha(root / 'COMBINED_FULL/fit/COMPLETE.json'),
        prepare_sha256=sha(root / 'PREPARE.json'), source_sha256=sha(root / 'source.tar'),
        corpus_manifest_sha256=MANIFEST_SHA, rows=2394, presentations_per_row=16,
        updates=19248, fresh_optimizer=True, frozen_base=True, held_results_required=False,
        created_unix=time.time(), no_promotion_claim=True))


def train(root, cell):
    configure()
    common.train(root, cell)
    if cell == 'COMBINED_FULL':
        handoff(root)


def readout(root, cell):
    configure()
    prepared, lifetime = validate_inputs(root), read(root / 'LIFETIME.json')
    uuid = DEVICES[cell][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    fit = read(root / cell / 'fit/COMPLETE.json')
    assert fit['status'] == 'COMPLETE' and fit['updates'] == LAYOUT.updates
    assert fit['input_adapter'] == prepared['initial']
    output = root / cell / 'readout'
    output.mkdir(exist_ok=False)
    count, errors = 0, []
    try:
        identity = common.bridge.AdapterIdentity.from_document(fit['output_adapter'])
        binding = common.bridge.StageBinding(root.name, common.bridge.ARMS[1], 0, 'sealed_readout',
            identity, False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=lambda label: common.check_deadline(lifetime, label),
            predecessor_processes=(tuple(fit['process']),), engine_factory=common.ReadoutEngine)
        write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
            uuid=uuid, loaded_unix=time.time(), parent_present=False, predecessor=fit['process']))

        def generate(messages, **metadata):
            nonlocal count
            common.check_deadline(lifetime, 'reserve')
            cap = MATH_CAP if count < MATH_TASKS else LEGACY_CAP
            path, record = common.reserve(output, count, messages, cap, metadata)
            count += 1
            try:
                response = loaded.engine.generate(messages, max_new_tokens=cap)
                record.update(response=response, status='COMPLETE')
                return response
            except BaseException as error:
                errors.append(str(error))
                record.update(status='FAILED', error=dict(type=type(error).__name__, message=str(error)))
                raise
            finally:
                record['finished_unix'] = time.time()
                write(path, record)

        cohort = read(root / 'COHORT.json')
        math_rows = []
        for task, messages in zip(cohort['tasks'], cohort['prompts']):
            response = generate(messages, purpose='math_held', task_id=task['id'])
            math_rows.append(dict(task_id=task['id'], family=task['family'], **common.transfer.score(task, response)))
            write(output / 'MATH_ROWS.json', math_rows)
        assert count == 64
        panels = []
        for position, probe in enumerate(read(root / 'ROUTE_COHORT.json')['probes']):
            runtime = SimpleNamespace(**route.goal.runtime(probe['shard']))
            for condition in ('OWN_TEXT', 'UNAVAILABLE'):
                panel = route.evaluate_goal_world(probe['collection'], condition, generate, output,
                    'COMBINED_HELD', position, runtime)
                panels.append(panel)
                write(output / 'ROUTE_PANELS.json', panels)
        route_calls = count - 64
        assert len(panels) == 32 and route_calls <= 768
        legacy = read(root / 'LEGACY_READOUT.json')
        events = [dict(event=fact['event'], raw=episode['event']['raw'])
            for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
        retention = route.memory.recall(events, generate, output, 'OLD')
        audit = route.memory.audit.collect_cases(legacy['held'],
            lambda messages: generate(messages, purpose='legacy_audit'), coached=False)
        write(output / 'AUDIT.json', audit)
        assert count == 64 + route_calls + 48 and count <= 880 and not errors
        observed = loaded.verify_unchanged()
        write(output / 'AFTER.json', dict(observed=observed.document(), process=loaded.process,
            unchanged=True, finished_unix=time.time()))
        scores = {condition: dict(
            goals_correct=sum(panel['summary']['individual']['correct'] for panel in panels if panel['condition'] == condition),
            goals_denominator=64,
            pairs_correct=sum(panel['summary']['paired']['correct'] for panel in panels if panel['condition'] == condition),
            pairs_denominator=32) for condition in ('OWN_TEXT', 'UNAVAILABLE')}
        write(output / 'COMPLETE.json', dict(status='COMPLETE', calls=count, route_calls=route_calls,
            math_correct=sum(row['outcome_pass'] for row in math_rows), math_denominator=64,
            route=scores, retention=retention, audit=audit['summary'], fits=0, updates=0,
            parent_calls=0, process=loaded.process, finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error),
            calls=count, finished_unix=time.time()))
        raise


def scan(index, service):
    assert index in (0, 1) and socket.gethostname() == 'a4u8g-0147'
    if os.geteuid() != 0:
        response = subprocess.check_output(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
            'python3', '-B', '-m', PROGRAM, 'scan', '--root', str(ROOT), '--index', str(index)],
            text=True, timeout=60)
        snapshot = json.loads(response)
        assert snapshot['gpu']['index'] == index and snapshot['gpu']['uuid'] == dict(DEVICES.values())[index]
        assert snapshot['clear'] == (not snapshot['blocking_reasons'])
        return snapshot
    scanner.policy = SimpleNamespace(DEVICES=DEVICES, HOST_SHA=HOST_SHA)
    return scanner.scan(index, service)


def launch(root):
    prepared = validate_inputs(root)
    assert os.geteuid() != 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    ready, publication = read(root / 'READY.json'), read(root / 'PUBLICATION.json')
    assert ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed']
    assert ready['source_sha256'] == prepared['source_sha256']
    assert ready['cpu_test_log_sha256'] == sha(root / 'CPU_TESTS.log')
    assert publication['ready_sha256'] == sha(root / 'READY.json')
    assert publication['dated_builder_line'].startswith('[Builder — COMBINED_L1] ')
    assert publication['coordination_append_verified'] is True
    assert read(root / 'MATH_RETIREMENT.json')['retired_and_released'] is True
    started = time.time()
    assert started + SECONDS < LEASE_END - 21600
    lifetime = dict(started_unix=started, hard_deadline_unix=started + SECONDS,
        native_deadline_unix=started + SECONDS - 360, assigned_gpu_hours_ceiling=24,
        readout_call_cap=1760, training_generation=0, parent_calls=0, publication=publication)
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, indent=2)
    children, phases, logs = {}, {}, []
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    def spawn(cell, phase):
        common.check_deadline(lifetime, 'launch_' + phase)
        index, uuid = DEVICES[cell]
        log = (root / f'{cell}_{phase}.log').open('x')
        logs.append(log)
        command = [PYTHON, '-B', '-m', PROGRAM, phase, '--root', str(root), '--cell', cell]
        child = subprocess.Popen(command, cwd=root / 'source', stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid,
                PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'))
        identity = common.process_identity(child.pid)
        children[cell], phases[cell] = (child, identity), phase
        write(root / f'{cell}_{phase}_LAUNCH.json', dict(identity=identity, cell=cell, phase=phase,
            uuid=uuid, index=index, command=command, started_unix=time.time()))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cell, (index, uuid) in DEVICES.items():
            snapshot = scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'{cell}_ADMISSION.json', snapshot)
            assert snapshot['clear'], ('fresh_ownership_blocked', cell, snapshot['blocking_reasons'])
        for cell in CELLS:
            spawn(cell, 'train')
        while any(phase in ('train', 'readout') for phase in phases.values()):
            common.check_deadline(lifetime, 'supervise')
            for cell, (child, identity) in list(children.items()):
                if phases[cell] not in ('train', 'readout') or child.poll() is None:
                    continue
                phase = phases[cell]
                write(root / f'{cell}_{phase}_EXIT.json', dict(returncode=child.returncode, finished_unix=time.time()))
                if child.returncode != 0:
                    phases[cell] = 'FAILED'
                elif phase == 'train':
                    if cell == 'COMBINED_FULL':
                        assert read(root / 'FULL_CHILD_HANDOFF.json')['status'] == 'FIT_COMPLETE_HELD_SCORES_NOT_REQUIRED'
                    snapshot = scan(DEVICES[cell][0], root / 'SERVICE_IDENTITY.json')
                    write(root / f'{cell}_READOUT_ADMISSION.json', snapshot)
                    if not snapshot['clear']:
                        phases[cell] = 'OWNERSHIP_BLOCKED'
                    else:
                        spawn(cell, 'readout')
                else:
                    phases[cell] = 'COMPLETE'
            time.sleep(1)
        status = 'COMPLETE' if all(phase == 'COMPLETE' for phase in phases.values()) else 'CELL_FAILURE'
    except BaseException as error:
        write(root / 'LAUNCH_FAILED.json', dict(type=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise
    finally:
        for child, identity in children.values():
            common.stop_owned(child, identity)
        for log in logs:
            log.close()
        releases = {}
        for cell, (index, uuid) in DEVICES.items():
            try:
                snapshot = scan(index, root / 'SERVICE_IDENTITY.json')
                write(root / f'{cell}_RELEASE.json', snapshot)
                releases[cell] = snapshot['clear']
            except Exception as error:
                releases[cell] = False
                write(root / f'{cell}_RELEASE_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        write(root / 'TERMINAL.json', dict(status=status, cells=phases, releases=releases,
            started_unix=started, finished_unix=time.time(),
            conservative_assigned_gpu_hours=2 * (time.time() - started) / 3600,
            readout_calls=sum(len(list((root / cell / 'readout').glob('CALL_*.json'))) for cell in CELLS),
            training_generation=0, parent_calls=0, retries=0, promotion=False))
    assert status == 'COMPLETE' and all(releases.values())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'train', 'readout', 'launch', 'scan'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cell', choices=CELLS)
    parser.add_argument('--index', type=int, choices=(0, 1))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'train':
        train(options.root, options.cell)
    elif options.phase == 'readout':
        readout(options.root, options.cell)
    elif options.phase == 'scan':
        print(json.dumps(scan(options.index, options.root / 'SERVICE_IDENTITY.json')))
    else:
        launch(options.root)
