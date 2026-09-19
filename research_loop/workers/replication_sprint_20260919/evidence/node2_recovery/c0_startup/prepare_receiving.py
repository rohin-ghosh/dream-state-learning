"""Reviewed node2 CPU staging only. No launch, model load, signals or history rewrite."""

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys

import c0_startup as startup
import c0_kernel as kernel


HERE = Path(__file__).resolve().parent
ADDITIONS = ['c0_kernel.py', 'c0_applied_wall_validation.py', 'c0_restart_contract.py',
    'c0_tail.py', 'c0_startup.py', 'gpu/c0_pending_entry.py']
require = startup.require


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def binding(path):
    return dict(path=str(path), sha256=file_sha(path))


def write(path, document):
    kernel._write_once(path, document)


def space_budget(*, source_bytes, checkpoint_bytes, complete_bytes, pending_bytes, addition_bytes):
    state_envelope = max(complete_bytes, pending_bytes) + 4 * 1024**2
    components = dict(pinned_source_and_additions=source_bytes + addition_bytes,
        new_checkpoint_and_temporary_payloads=2 * checkpoint_bytes,
        pending_completion_and_candidate_publication=4 * state_envelope,
        first_THINK_ACT_atomic_record_headroom=8 * state_envelope,
        CPU_payload_small_receipts_and_startup=8 * 1024**2,
        shared_filesystem_unallocated_safety_reserve=2 * 1024**3)
    return dict(components=components, required_bytes=sum(components.values()),
        state_envelope_bytes=state_envelope,
        assumptions=['Same adapter/optimizer tensor shapes; at most two checkpoint payload footprints.',
            'Prior failed artifacts remain allocated and untouched.',
            '4 MiB growth allowance per full state envelope; doubled atomic publication allowance.',
            'Only first post-recovery THINK/ACT is budgeted; indefinite life growth is not guaranteed.',
            'No base-model download or new optimizer/base cache; original offline paths preserved.',
            '2 GiB unallocated reserve protects against shared-node growth; it is not a reservation.'])


def prepare(*, reviewed_source_delta):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_receiving_environment')
    review = json.loads(Path(reviewed_source_delta).read_bytes())
    require(review['reviewed_for_staging'] is True and review['GPU_launch_authorized'] is False,
        'Main_exact_staging_review_not_launch_permission')
    require(review['preparer_sha256'] == file_sha(Path(__file__))
        and review['cut_sha256'] == file_sha(HERE / 'C0_CUT.json'), 'reviewed_preparer_and_preserved_cut')
    additions = {name: file_sha(HERE / Path(name).name) for name in ADDITIONS}
    require(review['additions'] == additions, 'exact_reviewed_addition_bytes')
    original_bytes = Path(startup.ORIGINAL_PLAN).read_bytes()
    wall = kernel.observed_wall_compatibility(original_bytes, 'C0')
    original = json.loads(original_bytes)
    old_guard_bytes = Path(startup.ORIGINAL_GUARD).read_bytes()
    require(hashlib.sha256(old_guard_bytes).hexdigest() == startup.GUARD_SHA, 'original_guard_bytes')
    old_guard = json.loads(old_guard_bytes)
    require(old_guard['plan_sha256'] == wall['original_plan_sha256'], 'original_guard_plan_pin')
    original_source, source, control = map(Path, (startup.ORIGINAL_SOURCE, startup.STAGED_SOURCE, startup.CONTROL))
    require(not source.exists() and not control.exists(), 'unique_empty_staging_no_retry_or_overwrite')
    sources = {str(path.relative_to(original_source)): file_sha(path) for path in original_source.rglob('*.py')}
    require(sources == old_guard['source_pins'], 'entire_unchanged_original_Python_closure')
    require(not (set(sources) & set(additions)), 'additions_do_not_replace_original_code')
    cut = json.loads((HERE / 'C0_CUT.json').read_bytes())
    startup_path = Path(original['startup_context']['path'])
    require(file_sha(startup_path) == original['startup_context']['sha256'], 'same_startup_bytes')
    checkpoint_root = Path(startup.RAW) / 'checkpoints/sleep_000145'
    checkpoint_files = [checkpoint_root / 'COMMIT.json', checkpoint_root / 'optimizer_rng.pt',
        *(checkpoint_root / 'adapter').iterdir()]
    budget = space_budget(source_bytes=sum((original_source / name).stat().st_size for name in sources),
        checkpoint_bytes=sum(path.stat().st_size for path in checkpoint_files),
        complete_bytes=(Path(startup.RAW) / 'stream/records/00000000000000006631.json').stat().st_size,
        pending_bytes=(Path(startup.RAW) / 'stream/records/00000000000000006660.json').stat().st_size,
        addition_bytes=sum((HERE / Path(name).name).stat().st_size for name in ADDITIONS))
    required_space = budget['required_bytes']
    free = shutil.disk_usage(startup.LIFE).free
    require(free >= required_space, 'insufficient_receiving_space_preserve_all_failed_artifacts')
    source.mkdir()
    control.mkdir()
    write(control / 'STAGING_STARTED.json', dict(original_plan_sha256=wall['original_plan_sha256'],
        free_bytes=free, budget=budget, no_automatic_retry=True,
        scope='six source additions, relocation of identical startup bytes, new control only'))
    for relative, expected in sources.items():
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original_source / relative, destination)
        require(file_sha(destination) == expected, 'copied_original_source_bytes')
    relocated = source / startup_path.relative_to(original_source)
    relocated.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(startup_path, relocated)
    require(file_sha(relocated) == original['startup_context']['sha256'], 'copied_startup_bytes')
    for relative, expected in additions.items():
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as output:
            output.write((HERE / Path(relative).name).read_bytes())
        require(file_sha(destination) == expected, 'copied_addition_bytes')
    sys.path.insert(0, str(source))
    native = importlib.import_module('gpu.orch_r125_continual_native')
    journal_module = importlib.import_module('gpu.orch_r125_stream_journal')
    require(Path(native.__file__).resolve().is_relative_to(source), 'receiving_original_native_source')
    execution = kernel.relocated_execution_plan(original, str(source))
    require(native.validate_plan(deepcopy(execution)) == execution, 'actual_original_plan_validator')
    write(control / 'PLAN.json', execution)
    selection = dict(policy=startup.tail.POLICY, root=startup.RAW + '/stream',
        journal_id=cut['head']['journal_id'], complete_index=cut['boundaries']['complete']['index'],
        complete_sha256=cut['boundaries']['complete']['sha256'], life_id=startup.TRIAL,
        max_tail_records=128, max_tail_bytes=1024**3,
        sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)],
        persist_complete_anchors=True)
    journal_class = startup.make_journal_class(journal_module.StreamJournal, selection)
    with journal_class(Path(selection['root']), create=False) as journal:
        audit = journal.checkpoint_tail_audit()
        require(audit['record_count'] == 6711 and audit['head_sha256'] == cut['head']['sha256'],
            'exact_6710_old_head_no_dropped_tail')

        def read_record(index):
            return journal._read_json(journal._records_fd, f'{index:020d}.json')

        records = {name: read_record(reference['index']) for name, reference in cut['boundaries'].items()}
        require(all(records[name]['sha256'] == reference['sha256']
            for name, reference in cut['boundaries'].items()), 'exact_boundary_hashes')
        envelope = kernel.prepare_candidate(records['complete'], records['pending_sleep'],
            [read_record(index) for index in range(6663, 6711)], recipe=records['recipe'],
            eligibility=records['eligibility'], life='C0', plan_bytes=original_bytes)
        require(journal.latest_checkpoint()['document'] == envelope['candidate']['contract']['contract']['preserved_state'],
            'pending146_is_current_tail_state')
        checkpoint = envelope['candidate']['durable_checkpoint']
        saved = Path(startup.RAW) / 'checkpoints/sleep_000145'
        require(file_sha(saved / 'COMMIT.json') == cut['durable_commit_sha256']
            and json.loads((saved / 'COMMIT.json').read_bytes()) == checkpoint, 'exact_original_COMMIT')
        require(checkpoint['checkpoint_sha256'] == cut['checkpoint_hashes'], 'durable_checkpoint_hashes')
        for name, expected in checkpoint['adapter_files'].items():
            require(file_sha(saved / 'adapter' / name) == expected, 'durable_adapter_payload_bytes')
        require(file_sha(saved / 'optimizer_rng.pt') == cut['checkpoint_hashes']['optimizer'],
            'durable_optimizer_RNG_payload_bytes')
        write(control / 'CANDIDATE.json', envelope)
        write(control / 'PRESERVED_STATE_AUDIT.json', dict(audit=audit, cut=cut,
            rows_or_history_modified=False, partial_intent_reconciliation=False,
            live_or_launch_readiness=False, exclusive_lock_released_after_preparation=True))
    delta = dict(schema='C0_EXECUTION_SOURCE_DELTA_V1', original_source_pins=sources,
        additions=additions, original_plan_sha256=wall['original_plan_sha256'],
        execution_plan_sha256=file_sha(control / 'PLAN.json'))
    write(control / 'SOURCE_DELTA.json', delta)
    manifest = dict(schema=startup.SCHEMA, life='C0', original_plan=binding(startup.ORIGINAL_PLAN),
        original_guard=binding(startup.ORIGINAL_GUARD), candidate=binding(control / 'CANDIDATE.json'),
        execution_plan_sha256=delta['execution_plan_sha256'], staged_source_root=str(source),
        applied_wall=wall, selection=dict(selection, root=startup.ROOT + '/stream'),
        source_path_bindings=[dict(field='startup_context.path', original=startup_path.as_posix(),
            execution=relocated.as_posix(), sha256=original['startup_context']['sha256'])],
        source_delta=binding(control / 'SOURCE_DELTA.json'))
    write(control / 'STARTUP.json', manifest)
    startup.validate_manifest(manifest, (control / 'PLAN.json').read_bytes())
    guard = dict(old_guard, plan_path=str(control / 'PLAN.json'), plan_sha256=delta['execution_plan_sha256'],
        attempt_dir=str(control), source_pins=dict(sources, **additions),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256='PENDING_RECEIVING_CPU_AND_MAIN_PUBLICATION',
        pending_sleep_recovery=binding(control / 'STARTUP.json'))
    write(control / 'GUARD_CANDIDATE.json', guard)
    write(control / 'PREPARATION_COMPLETE.json', dict(status='CPU_STAGED_NOT_ADMITTED',
        original_guard_unchanged=file_sha(startup.ORIGINAL_GUARD) == startup.GUARD_SHA,
        original_plan_unchanged=file_sha(startup.ORIGINAL_PLAN) == wall['original_plan_sha256'],
        source_delta=binding(control / 'SOURCE_DELTA.json'),
        blockers=['Receiving CPU tests', 'Truthful Main publication/allocation provenance',
            'Fresh original privileged admission and exclusive WRITER at dispatch'],
        model_loaded=False, launch_attempted=False))
    print(json.dumps(dict(source=str(source), control=str(control), status='CPU_STAGED_NOT_ADMITTED')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviewed-source-delta', type=Path, required=True)
    arguments = parser.parse_args()
    prepare(reviewed_source_delta=arguments.reviewed_source_delta)
