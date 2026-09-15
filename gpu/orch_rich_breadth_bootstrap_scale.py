"""Explicit764-row supersession; reuse native fitting, masks, and readout."""

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_rich_breadth_bootstrap_run as common
from gpu import orch_l1_bootstrap_transfer_scan as existing_scan
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, LEASE_END, read, sha, write
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_math_rich_source import verify_archive
from organism_v6 import orch_math_scale as scale
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


PACKET_SHA = '257272aeead68cd690b984895e09fad9493d3d1d0e5b7e76b6c27872da2e3d2e'
TASKS_SHA = '2d0df5b1eae71695e21f04cbd1bdaed6de7dce77c80713ada0264d6bef94d1a1'
ROOT = Path('/localhome/local-rohing/orch_rich_breadth_bootstrap_scale764_20260915_attempt1')
CELLS = ('SCALE764_FULL', 'SCALE764_OFF')
DEVICES = dict(SCALE764_FULL=(0, 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'),
    SCALE764_OFF=(1, 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b'))
SECONDS = 43200
GPU_HOURS = 24
MATH_TASKS = 64
MATH_CAP = 1536
LEGACY_CAP = 160
CALLS_PER_CELL = 112
CALLS_TOTAL = 224
LAYOUT = GoalReplayLayout(764, 16)
PROGRAM = 'gpu.orch_rich_breadth_bootstrap_scale'
HOST_SHA = existing_scan.policy.HOST_SHA


def validate_packet(root):
    assert sha(root / 'PACKET/ADMITTED_ROWS.json') == PACKET_SHA
    assert sha(root / 'TASKS_SOURCE.json') == TASKS_SHA
    rows, tasks = read(root / 'PACKET/ADMITTED_ROWS.json'), read(root / 'TASKS_SOURCE.json')
    scale.validate(tasks)
    by_id = {task['id']: task for task in tasks['tasks']}
    assert len(rows) == len({row['target_sha256'] for row in rows}) == 764
    assert Counter(row['kind'] for row in rows) == dict(rich=229, new_record=535)
    gold_reviews = read(root / 'QUALIFICATION_GOLD.json')
    for row in rows:
        assert row['admitted'] and row['semantic_status'] == 'PASS' and row['candidate']
        assert row['outcome_pass'] and row['token_contract_pass'] and 150 <= row['generated_tokens'] <= 400
        review = row['review']
        assert review['status'] == 'PASS' and review['full_text_read'] and review['neutral_prefix_compatible']
        assert review['student_prefix_sha256'] == scale.original.digest(row['student_prefix'])
        assert review['target_sha256'] == row['target_sha256'] == hashlib.sha256(row['target'].encode()).hexdigest()
        assert row['target'] == row['call']['raw'] and row['student_prefix'][-1]['role'] == 'user'
        assert not any(message['role'] == 'system' for message in row['student_prefix'])
        task = by_id[row['task_id']]
        assert row['gold'] == task['gold']
        gold = gold_reviews[row['task_id']]
        assert gold['status'] == 'VALID' and gold['question_sha256'] == task['question_sha256']
        assert scale.original.number(gold['independent_answer']) == scale.original.number(row['gold'])
    return dict(rows=764, tasks=len({row['task_id'] for row in rows}), kinds=dict(rich=229, new_record=535),
        author_only_qualification=True, new_review=False, entire_snapshot=True, old1000_gate_not_applied=True)


def freeze(repository, output):
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / 'COHORT.json').exists()
    source = repository / 'research_notes/analysis/orch_math_scale_20260914_attempt1'
    packet = source / 'progress_20260915T024900Z/ADMITTED_ROWS.json'
    assert sha(packet) == PACKET_SHA and sha(source / 'TASKS.json') == TASKS_SHA
    rows = read(packet)
    needed = {row['task_id']: row for row in rows}
    by_key = {row['task_id'] + ':' + row['kind']: row for row in rows}
    gold, qualification_sources = {}, {}
    found = set()
    for path in sorted((source / 'fulltext_review').glob('batch_*/ACCEPTED_REVIEW.json')):
        document = read(path)
        keys = set(document['reviews']) & set(by_key)
        ids = set(document['gold']) & set(needed)
        if not keys and not ids:
            continue
        for key in keys:
            assert document['reviews'][key] == by_key[key]['review']
            found.add(key)
        for identity in ids:
            if identity in gold:
                assert gold[identity] == document['gold'][identity]
            gold[identity] = document['gold'][identity]
        qualification_sources[str(path.relative_to(repository))] = sha(path)
    assert found == set(by_key) and set(gold) == set(needed)
    (output / 'PACKET').mkdir(exist_ok=False)
    shutil.copyfile(packet, output / 'PACKET/ADMITTED_ROWS.json')
    shutil.copyfile(source / 'TASKS.json', output / 'TASKS_SOURCE.json')
    write(output / 'QUALIFICATION_GOLD.json', gold)
    validate_packet(output)
    tasks = read(source / 'TASKS.json')['held_tasks']
    assert len(tasks) == 64 and not {task['id'] for task in tasks} & set(needed)
    anscombe = repository / 'research_notes/analysis/orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json'
    assert sha(anscombe) == '3530b667828373408ec6de97f9080c9c1e7a692ee617a90930ce8a9aa1adcbe4'
    assert not {task['id'] for task in tasks} & {task['id'] for task in read(anscombe)['tasks']}
    cohort = dict(tasks=tasks, prompts=[scale.original.prompt(task, 'rich')[0] for task in tasks],
        denominator=64, source='Exact previously reserved MATH_SCALE held64; unchanged membership/order/gold.',
        held_outcomes_inspected=False, new_selection=False, native_calls=0,
        families=dict(Counter(task['family'] for task in tasks)))
    write(output / 'COHORT.json', cohort)
    old = repository / 'research_notes/analysis/orch_l2_rich_math_20260915_attempt1'
    prepared = read(old / 'PREPARE.json')
    for name in ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json'):
        assert sha(old / name) == prepared['files'][name]
        shutil.copyfile(old / name, output / name)
    write(output / 'DATA_PROVENANCE.json', dict(packet_path=str(packet.relative_to(repository)),
        packet_sha256=PACKET_SHA, task_source_sha256=TASKS_SHA, cohort_sha256=sha(output / 'COHORT.json'),
        qualification_sources=qualification_sources, qualification_gold_sha256=sha(output / 'QUALIFICATION_GOLD.json'),
        legacy_files={name: sha(output / name) for name in ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json')},
        anscombe_cohort_sha256=sha(anscombe), outcomes_read=False, entire_snapshot=True,
        source_archive_sha256=read(source / 'SOURCE_BINDING.json')['source_archive_sha256'],
        public_data=True, pretraining_contamination_unknown=True))
    print(json.dumps(dict(packet_sha256=PACKET_SHA, cohort_sha256=sha(output / 'COHORT.json'),
        provenance_sha256=sha(output / 'DATA_PROVENANCE.json'), rows=764, updates=LAYOUT.updates)))


def prepare(root):
    assert root == ROOT and socket.gethostname() == 'a4u8g-0147' and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert not (root / 'PREPARE.json').exists()
    validation = validate_packet(root)
    prior = read(Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1/PREPARE.json'))
    manifest = common.portable.read_manifest(prior['bundle'], expected_manifest_sha256=BUNDLE_SHA)
    base = common.portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    identity = common.bridge.AdapterIdentity(str(Path(prior['bundle']) / 'adapter'), common.portable.PARENT_STATE,
        manifest['expected_base_sha256'], tuple(manifest['adapter_files'].items())).verify()
    tokenizer = common.native.source.native.load_local_tokenizer(prior['model_dir'])
    legacy = legacy_encode(root, tokenizer)
    new = []
    for position, row in enumerate(read(root / 'PACKET/ADMITTED_ROWS.json')):
        try:
            new.extend(common.encoding.encode_rows([row], tokenizer))
        except BaseException as error:
            write(root / 'ENCODER_FAILED.json', dict(row=position, task_id=row['task_id'], kind=row['kind'],
                target_sha256=row['target_sha256'], error_type=type(error).__name__, error=str(error),
                target_unchanged=True, native_calls=0))
            raise
    encoded = common.native.assemble_replay(legacy, new, LAYOUT, legacy_reference=legacy,
        eos_token_id=tokenizer.eos_token_id)
    write(root / 'ENCODER_CHECK.json', dict(status='PASS', rows=764, native_calls=0,
        model_loaded=False, row_masks=[asdict(row) for row in new]))
    audit = common.token_audit(encoded, LAYOUT, tokenizer.pad_token_id)
    audit['layout'] = LAYOUT.manifest('FULL_TARGET')
    write(root / 'TOKEN_AUDIT.json', {'764': audit})
    cohort = read(root / 'COHORT.json')
    assert cohort['tasks'] == read(root / 'TASKS_SOURCE.json')['held_tasks']
    assert len(cohort['prompts']) == MATH_TASKS
    lengths = [len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
        return_dict=False)) for messages in cohort['prompts']]
    assert max(lengths) <= 2048
    names = ('COHORT.json', 'TASKS_SOURCE.json', 'DATA_PROVENANCE.json', 'QUALIFICATION_GOLD.json',
        'LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json', 'PROTOCOL.md', 'USER_RELAY.md',
        'SERVICE_IDENTITY.json', 'ENCODER_CHECK.json', 'TOKEN_AUDIT.json')
    provenance = read(root / 'DATA_PROVENANCE.json')
    assert all(sha(root / name) == digest for name, digest in provenance['legacy_files'].items())
    write(root / 'PREPARE.json', dict(status='CPU_PREPARED_NO_MODEL', native_calls=0, fits=0,
        initial=identity.document(), bundle=prior['bundle'], model_dir=prior['model_dir'], base_verification=base,
        recipe=common.RECIPE, cells=CELLS, packet_validation=validation, math_prompt_lengths=lengths,
        files={name: sha(root / name) for name in names}, source_sha256=sha(root / 'source.tar'),
        source_files=verify_archive(root / 'source.tar', root / 'source'),
        updates_per_fit=LAYOUT.updates, seconds=SECONDS, assigned_gpu_hours=GPU_HOURS,
        lease_end_unix=LEASE_END, six_hour_margin_seconds=21600,
        readout_calls=CALLS_TOTAL, training_generation=0, parent_calls=0, prepared_unix=time.time()))
    print(json.dumps(dict(status='CPU_PREPARED_NO_MODEL', prepare_sha256=sha(root / 'PREPARE.json'),
        encoder_sha256=sha(root / 'ENCODER_CHECK.json'), tokens=audit), indent=2))


def validate_inputs(root):
    assert root == ROOT and socket.gethostname() == 'a4u8g-0147' and not root.is_symlink()
    prepared = read(root / 'PREPARE.json')
    assert prepared['status'] == 'CPU_PREPARED_NO_MODEL' and prepared['native_calls'] == 0
    assert sha(root / 'source.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files']
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    validate_packet(root)
    assert prepared['recipe'] == common.RECIPE
    assert prepared['initial']['state_sha256'] == common.portable.PARENT_STATE
    return prepared


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
    existing_scan.policy = sys.modules[__name__]
    return existing_scan.scan(index, service)


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
    common.guard = SimpleNamespace(scan=scan, PYTHON='/localhome/local-rohing/v2/venv/bin/python',
        LEASE_CUTOFF=LEASE_END - 21600)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('freeze', 'prepare', 'train', 'readout', 'launch', 'scan'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--cell', choices=CELLS)
    parser.add_argument('--index', type=int, choices=(0, 1))
    options = parser.parse_args()
    if options.phase == 'freeze':
        freeze(options.repository.resolve(), options.root.resolve())
    elif options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'scan':
        print(json.dumps(scan(options.index, options.root / 'SERVICE_IDENTITY.json')))
    else:
        configure()
        if options.phase == 'launch':
            recovery = options.root / 'PREMODEL_RECOVERY.json'
            started = None
            if recovery.exists():
                record = read(recovery)
                previous = options.root / 'SCANNER_FAILURE'
                assert sha(previous / 'LIFETIME.json') == record['original_lifetime_sha256']
                assert read(previous / 'TERMINAL.json')['cells'] == {}
                assert not any((options.root / cell).exists() for cell in CELLS)
                started = read(previous / 'LIFETIME.json')['started_unix']
                assert record['reason'] == 'pre_model_scanner_host_binding_repair'
            common.launch(options.root, original_started_unix=started)
        elif options.phase == 'train':
            common.train(options.root, options.cell)
        else:
            common.readout(options.root, options.cell)
