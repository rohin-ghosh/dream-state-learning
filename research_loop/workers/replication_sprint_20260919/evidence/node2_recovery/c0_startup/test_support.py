"""Small CPU fixtures; raw observed PLAN bytes remain unchanged."""

import base64
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import c0_kernel as kernel
import c0_startup as startup
import c0_tail as tail


HERE = Path(__file__).resolve().parent
REPO = Path(os.environ['C0_TEST_SOURCE_ROOT']) if 'C0_TEST_SOURCE_ROOT' in os.environ else HERE.parents[5]
WALL = HERE / 'cpu_support'


def load_originals(stack):
    stack.enter_context(patch.dict(sys.modules))
    for name in list(sys.modules):
        if name in ('gpu', 'organism_v6') or name.startswith(('gpu.', 'organism_v6.')):
            del sys.modules[name]
    guard = json.loads((HERE / 'fixtures/ORIGINAL_GUARD.json').read_bytes())
    for path in (HERE / 'source_evidence').rglob('*.py'):
        relative = str(path.relative_to(HERE / 'source_evidence'))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == guard['source_pins'][relative], relative
    for package_name in ('gpu', 'organism_v6'):
        package = ModuleType(package_name)
        package.__path__ = [str(HERE / 'source_evidence' / package_name), str(REPO / package_name)]
        sys.modules[package_name] = package
    result = SimpleNamespace()
    for label, name in [('history', 'organism_v6.orch_r124_train_history'),
            ('stream', 'organism_v6.orch_r125_continual_stream'),
            ('journal', 'gpu.orch_r125_stream_journal'), ('native', 'gpu.orch_r125_continual_native'),
            ('driver', 'gpu.orch_r184_think_act_learn'), ('runtime', 'gpu.r205_runtime'),
            ('wrapper', 'gpu.r233_node2_recovery'), ('guard', 'gpu.orch_r125_continual_guard')]:
        setattr(result, label, importlib.import_module(name))
    return result


def bound_file(path, raw):
    path.write_bytes(raw)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def build(root, sources, stack):
    stack.enter_context(patch.dict(sys.modules))
    stack.enter_context(patch.object(sys, 'path', [str(WALL), *sys.path]))
    sys.modules.pop('receiving_fixture', None)
    fixture_support = importlib.import_module('receiving_fixture')
    fixture = fixture_support.build_fixture(root, 'C0', sources)
    plan = fixture.plan
    real_path = Path

    def mapped_path(value, *parts):
        candidate = real_path(value, *parts)
        if candidate == real_path(startup.ROOT) or candidate.is_relative_to(startup.ROOT):
            return root / candidate.relative_to(startup.ROOT)
        return candidate

    for module in (startup, kernel, tail):
        stack.enter_context(patch.object(module, 'Path', mapped_path))
    journal_root = root / 'stream'
    journal_root.mkdir()
    (journal_root / 'records').mkdir()
    (journal_root / 'inbox').mkdir()
    (journal_root / 'WRITER.lock').touch()
    manifest = dict(schema=sources.journal.SCHEMA, journal_id='a' * 32)
    (journal_root / 'JOURNAL.json').write_bytes(sources.journal._encoded(manifest) + b'\n')

    def publish(index, kind, document, previous):
        record = dict(schema=sources.journal.SCHEMA, journal_id=manifest['journal_id'],
            index=index, kind=kind, document=document, previous_sha256=previous)
        record['sha256'] = kernel.digest(record)
        directory = journal_root / 'records'
        (directory / f'{index:020d}.json').write_bytes(sources.journal._encoded(record) + b'\n')
        (directory / f'{index:020d}.intent.json').write_bytes(sources.journal._encoded(
            sources.journal.StreamJournal._intent(record)) + b'\n')
        return record

    prefix = publish(0, 'CPU_FIXTURE_PREFIX', dict(text='hash this prefix; do not replay its body'),
        kernel.digest(manifest))
    document = deepcopy(fixture.complete['document'])
    receipt = {key: value for key, value in document.items() if key != 'resume_state'}
    document['resume_state']['state']['sleep_receipts'] = [dict(status='COMPLETE', cycle=number)
        for number in range(1, 145)] + [receipt]
    document['resume_state']['sha256'] = kernel.digest(document['resume_state']['state'])
    complete = publish(1, 'SLEEP_COMPLETE', document, prefix['sha256'])
    selection = dict(policy=tail.POLICY, root=startup.ROOT + '/stream', journal_id='a' * 32,
        complete_index=1, complete_sha256=complete['sha256'], life_id=startup.TRIAL,
        max_tail_records=256, max_tail_bytes=32 * 1024 * 1024,
        sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=False)],
        persist_complete_anchors=True)
    journal_class = startup.make_journal_class(sources.journal.StreamJournal, selection)
    stream = sources.stream.ContinualStream.restore(document['resume_state'],
        expected_sha256=document['resume_state']['sha256'])
    from gpu.orch_r197_correction_ledger import update_ledger
    with journal_class(journal_root, create=False) as journal:
        ledger = journal.record('R197_CORRECTION_CYCLE', dict(ledger=update_ledger(None,
            life_id=startup.TRIAL, cycle=145, raw_think=['fixture previous thought'],
            raw_act='fixture previous answer', completed_sleeps=144, parent_interventions=[])))
        (journal_root / 'correction_ledger.json').write_text(json.dumps(dict(
            record_index=ledger['index'], record_sha256=ledger['sha256'])))
        for number in range(3):
            stream.step(lambda *args, **kwargs: dict(raw=f'actual fixture answer {number}',
                token_ids=[number + 1], terminal=True, truncated=False), lambda messages: 10,
                journal.record, now=lambda: 1000)
        pending = stream.checkpoint()
        pending_sources = [row['source_sha256'] for row in stream.pending_rows()]
        pending['state']['pending'] = 'sleep:' + kernel.digest(pending_sources)
        pending['sha256'] = kernel.digest(pending['state'])
        pending_ref = journal.record('SLEEP_REQUEST', dict(cycle=146, resume_state=pending))
        journal.record('SLEEP_RECIPE', fixture.recipe['document'])
        journal.record('TARGET_ELIGIBILITY', dict(fixture.eligibility['document'], new_row_sha256=pending_sources))
        for number in range(48):
            journal.record('UPDATE', dict(optimizer_step=8413 + number,
                source_sha256=pending_sources[number % 3], losses=[], finished_unix=1000 + number))
        head = journal._state['index'] - 1

    def read(index):
        return json.loads((journal_root / 'records' / f'{index:020d}.json').read_bytes())

    selection['sidecars'][0]['required'] = True
    fixture.complete, fixture.pending = complete, read(pending_ref['index'])
    fixture.recipe, fixture.eligibility = read(pending_ref['index'] + 1), read(pending_ref['index'] + 2)
    fixture.updates = [read(index) for index in range(pending_ref['index'] + 3, head + 1)]
    envelope = kernel.prepare_candidate(complete, fixture.pending, fixture.updates,
        recipe=fixture.recipe, eligibility=fixture.eligibility, life='C0', plan_bytes=fixture.plan_bytes)
    fake = fixture_support.make_native(fixture)
    fake.NativeChild.tokenizer = 'synthetic CPU tokenizer'
    fake.NativeChild.engine = SimpleNamespace(runtime='CPU_SYNTHETIC_NO_MODEL')
    fake.NativeChild.count_tokens = lambda self, messages: 10
    fake.NativeChild.generate = lambda self, *args, **kwargs: dict(
        raw='Ready to act: make the check' if not any('ACT' in str(message) for message in args[:1])
        else 'The checked answer is 3.', token_ids=[101], terminal=True, truncated=False)
    stack.enter_context(patch.object(sources.native, 'NativeChild', fake.NativeChild))
    execution = kernel.relocated_execution_plan(plan, startup.STAGED_SOURCE)
    staged = root / 'source_fixture'
    staged.mkdir()
    birth_path = staged / Path(plan['startup_context']['path']).relative_to(startup.ORIGINAL_SOURCE)
    birth_path.parent.mkdir(parents=True, exist_ok=True)
    birth_path.write_bytes(plan['birth_prompt'].encode())
    assert hashlib.sha256(birth_path.read_bytes()).hexdigest() == plan['startup_context']['sha256']

    def native_path(value, *parts):
        candidate = real_path(value, *parts)
        if candidate == real_path(startup.STAGED_SOURCE) or candidate.is_relative_to(startup.STAGED_SOURCE):
            return staged / candidate.relative_to(startup.STAGED_SOURCE)
        return candidate

    stack.enter_context(patch.object(sources.native, 'Path', native_path))
    plan_path = root / 'PLAN.json'
    plan_path.write_bytes(json.dumps(execution, sort_keys=True).encode() + b'\n')
    recovered_manifest = dict(schema=startup.SCHEMA, life='C0',
        original_plan=bound_file(root / 'ORIGINAL_PLAN.json', fixture.plan_bytes),
        original_guard=dict(path=str(HERE / 'fixtures/ORIGINAL_GUARD.json'), sha256=startup.GUARD_SHA),
        candidate=bound_file(root / 'CANDIDATE.json', json.dumps(envelope).encode()),
        execution_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        staged_source_root=startup.STAGED_SOURCE, selection=selection,
        source_path_bindings=[dict(field='startup_context.path', original=plan['startup_context']['path'],
            execution=execution['startup_context']['path'], sha256=plan['startup_context']['sha256'])],
        applied_wall=kernel.observed_wall_compatibility(fixture.plan_bytes, 'C0'))
    return SimpleNamespace(fixture=fixture, fake=fake, manifest=recovered_manifest,
        plan_path=plan_path, execution=execution, read=read, journal_root=journal_root,
        journal_class=startup.make_journal_class(sources.journal.StreamJournal, selection),
        envelope=envelope, head=head)
