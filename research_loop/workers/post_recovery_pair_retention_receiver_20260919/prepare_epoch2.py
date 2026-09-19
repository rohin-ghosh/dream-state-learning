"""Local exact-hash pair overlay preparation; no transport, admission or activation."""

import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time

from ports import proposed_ports


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
ROLLOUT = HERE.parent / 'post_recovery_retention_rollout_20260919'
READER = HERE.parent / 'rohin233_recovery_node4_20260918'
PARENT = HERE.parent / 'post_reboot_pair_parents_20260919'
LIVES = ('curriculum_learner', 'curriculum_frozen_sibling')
PORT_FILES = {'gpu/r232_recovery.py', 'gpu/pair_retention_runtime.py', 'gpu/checkpoint_tail_runtime.py'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(Path(path).read_bytes())


def publish(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def document(path, value):
    publish(path, encoded(value))


def seal_source(source):
    for path in source.rglob('*'):
        require(not path.is_symlink(), 'no_sealed_source_symlinks')
        if path.is_file():
            with path.open('rb') as handle:
                os.fsync(handle.fileno())
            path.chmod(0o444)
    directories = sorted([source] + [path for path in source.rglob('*') if path.is_dir()],
        key=lambda path: len(path.parts), reverse=True)
    for path in directories:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        path.chmod(0o555)


def relative_name(name):
    path = PurePosixPath(name)
    require(isinstance(name, str) and name == str(path) and not path.is_absolute()
        and '..' not in path.parts and path.parts, 'safe_exact_relative_source_name')
    return path


def delta(before, after):
    return {name: dict(before=before.get(name), after=after.get(name))
        for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)}


def locate(pins, candidates):
    by_name = {}
    for path in candidates:
        by_name.setdefault(path.name, []).append(path)
    found = {}
    for name, expected in sorted(pins.items()):
        relative_name(name)
        options = sorted(by_name.get(Path(name).name, []), key=lambda path:
            (path != REPOSITORY / name, not str(path).endswith('/' + name), len(str(path)), str(path)))
        for path in options:
            if path.is_symlink() or path.resolve() != path.absolute():
                continue
            content = path.read_bytes()
            if checksum(content) == expected:
                found[name] = dict(path=str(path), sha256=expected, content=content)
                break
        require(name in found, 'missing_exact_source_preimage:' + name)
    return found


def plan_template(old, new_source):
    plan = deepcopy(old)
    startup = Path(old['startup_context']['path']).relative_to(old['source_root'])
    relative_name(str(startup))
    plan['source_root'] = new_source
    plan['startup_context']['path'] = str(Path(new_source) / startup)
    plan.pop('authorized_wall_extension', None)
    restored = deepcopy(plan)
    restored['source_root'] = old['source_root']
    restored['startup_context']['path'] = old['startup_context']['path']
    if 'authorized_wall_extension' in old:
        restored['authorized_wall_extension'] = old['authorized_wall_extension']
    require(restored == old, 'strictly_source_path_and_consumed_authorization_template_only')
    return plan


def check_inputs(staged, observation):
    require(staged['life'] in LIVES and staged['life'] == observation['life'], 'exact_pair_life')
    require(staged['old_guard_sha256'] == observation['guard_sha256']
        and staged['old_source_pins'] == observation['source_pins']
        and staged['journal_id'] == observation['journal_id']
        and staged['journal_root'] == observation['journal_root']
        and staged['native'] == observation['native'], 'same_inventory_and_epoch1_binding')
    require(delta(staged['old_source_pins'], staged['new_source_pins']) == staged['changed'],
        'epoch1_exact_delta')
    require(str(Path(observation['guard_metadata'].get('copy_raw', observation['plan']['root'])) / 'stream')
        == staged['journal_root'], 'actual_copy_raw_journal_mapping')
    source = Path(staged['new_source'])
    require(source.is_absolute() and '..' not in source.parts and source.name == 'source'
        and source.parent.name == 'epoch1', 'exact_immutable_epoch1_path')


def collect_candidates():
    result = subprocess.run(['rg', '--files', '-g', '*.py', 'gpu', 'organism_v6', 'tests',
        'research_loop/workers'], cwd=REPOSITORY, check=True, text=True, capture_output=True)
    return [REPOSITORY / name for name in result.stdout.splitlines()]


def run_checks(source, directory, python):
    scratch = directory / 'scratch'
    scratch.mkdir(parents=True)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), OMP_NUM_THREADS='1', TMPDIR=str(scratch))
    command = [str(python), '-B', str(HERE / 'source_checks.py'), '--source', str(source)]
    started = time.monotonic()
    result = subprocess.run(command, cwd=source, env=environment, capture_output=True, text=True, timeout=120)
    publish(directory / 'SOURCE_TESTS.stdout', result.stdout.encode())
    publish(directory / 'SOURCE_TESTS.stderr', result.stderr.encode())
    require(result.returncode == 0, 'actual_local_source_tests_failed:' + str(directory))
    evidence = json.loads(result.stdout)
    require(evidence['passed'] is True and evidence['synthetic_only'] is True
        and evidence['GPU_calls'] == 0 and evidence['dispatches'] == 0, 'source_CPU_evidence_only')
    return dict(command=command, elapsed_seconds=time.monotonic() - started,
        returncode=result.returncode, result=evidence,
        stdout_sha256=checksum(result.stdout.encode()), stderr_sha256=checksum(result.stderr.encode()))


def prepare(output, *, python=sys.executable):
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(HERE)
        and not output.exists(), 'new_local_worker_output_only')
    inventory_path = ROLLOUT / 'ovx4_INVENTORY2.json'
    inventory = read(inventory_path)
    observations = {row['life']: row for row in inventory['results']}
    manifest_path = READER / 'CHECKPOINT_TAIL_SOURCE_MANIFEST.json'
    reader_path = READER / 'checkpoint_tail_runtime.py'
    reader_hash = checksum(reader_path.read_bytes())
    require(reader_hash == read(manifest_path)['final_source_pins']['gpu/checkpoint_tail_runtime.py'],
        'existing_tested_reader_exact_manifest_pin')
    parent_path = PARENT / 'PARENT_REBIND_CONTRACT.json'
    parent = read(parent_path)
    require(parent['activation_enabled'] is False and parent['actual_rebind_performed'] is False
        and parent['new_native_identity'] is None, 'Kuhn_contract_pending_not_activation')
    staged_receipts = {life: read(ROLLOUT / (life + '_STAGED.json')) for life in LIVES}
    input_hashes = {str(path): checksum(path.read_bytes()) for path in
        [inventory_path, manifest_path, reader_path, parent_path, PARENT / 'PARENT_REBIND_CONTRACT.md',
         READER / 'CHECKPOINT_TAIL_TESTS.log'] + [ROLLOUT / (life + '_STAGED.json') for life in LIVES]
        + [HERE / name for name in ('prepare_epoch2.py', 'source_checks.py', 'ports.py',
            'pair_retention_runtime.py', 'cpu_probe.py', 'receiver.py', 'test_prepare_epoch2.py', 'test_receiver.py')]}
    candidates = collect_candidates()
    resolved = {}
    for life, staged in staged_receipts.items():
        check_inputs(staged, observations[life])
        resolved[life] = locate(staged['new_source_pins'], candidates)
    birth = HERE.parent / 'post_recovery_matched_cohort_runtime_20260918/receiving/source/context/BIRTH_R231.txt'
    birth_bytes = birth.read_bytes()
    output.mkdir(parents=True)
    document(output / 'INPUTS.json', dict(input_sha256=input_hashes,
        local_reconstruction='EVERY_PYTHON_FILE_MATCHES_EPOCH1_RECEIPT',
        reader_owner_confirmation='PENDING_PASTEUR_REVIEW_NO_ACK_INFERRED',
        parent_contract=parent, parent_contract_status='PENDING_DEPENDENCY_NOT_AUTHORIZATION'))
    summaries = {}
    for life, staged in staged_receipts.items():
        observation = observations[life]
        epoch = output / life / 'epoch2'
        source = epoch / 'source'
        source.mkdir(parents=True)
        for name, entry in resolved[life].items():
            publish(source / name, entry['content'])
        proposals, additions = proposed_ports(source, reader_path)
        require(set(additions) == PORT_FILES, 'only_exact_three_reader_port_entries')
        for name, content in proposals.items():
            ast.parse(content, filename=name)
            path = source / name
            if path.exists():
                require(checksum(path.read_bytes()) == additions[name]['before'], 'unmodified_local_preimage')
                path.write_bytes(content)
            else:
                publish(path, content)
        plan = observation['plan']
        startup = Path(plan['startup_context']['path']).relative_to(plan['source_root'])
        require(checksum(birth_bytes) == plan['startup_context']['sha256'], 'exact_retained_startup_bytes')
        publish(source / startup, birth_bytes)
        pins = {str(path.relative_to(source)): checksum(path.read_bytes()) for path in source.rglob('*.py')}
        require(delta(staged['new_source_pins'], pins) == additions, 'only_approved_reader_overlay')
        for path in source.rglob('*.py'):
            ast.parse(path.read_bytes(), filename=str(path))
        remote_source = str(Path(staged['new_source']).parent.parent / 'epoch2/source')
        template = plan_template(plan, remote_source)
        document(epoch / 'control/PLAN.template.json', template)
        document(epoch / 'control/ORIGINAL_GUARD_METADATA.json', observation['guard_metadata'])
        document(epoch / 'control/PARENT_DEPENDENCY_PENDING.json', dict(contract=parent,
            contract_sha256=input_hashes[str(parent_path)], owner='Kuhn', status='PENDING',
            dependency_receipt=None, rebind_receipt=None, parent_rebind_allowed=False))
        document(epoch / 'control/REQUIRED_LIVE_EVIDENCE.json', dict(
            status='NOT_ADMITTED_OR_CANDIDATE_BOUND',
            required=['fresh_exact_native_and_guard_binding', 'exact_COMPLETE_LEARN_intents',
                'consumed_WALL_EXTENDED_record_and_intent', 'actual_checkpoint_optimizer_RNG_CPU_proof',
                'same_journal_read_only_tail_scan_cost_and_parity', 'parent_fence_zero_inflight_ledger_pins',
                'receiving_guard_allocation_lease_validation', 'original_privileged_confinement_admission'],
            source_probe=str(HERE / 'cpu_probe.py'), modes=['checkpoint', 'tail', 'guard'],
            timeout_seconds=120, CUDA_VISIBLE_DEVICES='', persist_complete_anchors=False,
            prefix_hashing_allowed=True, historical_body_replay_fallback=False,
            admission_available=None, admission_granted=False, complete_reserved=False,
            deadline_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix']))
        tests = run_checks(source, epoch / 'cpu', python)
        require(pins == {str(path.relative_to(source)): checksum(path.read_bytes())
            for path in source.rglob('*.py')}, 'CPU_tests_do_not_modify_source')
        cpu = dict(schema='PAIR_EPOCH2_LOCAL_SOURCE_CPU_V1', passed=True, source_pins=pins,
            no_GPU_calls=True, checkpoint_tail_port_passed=True, pair_controls_passed=True,
            synthetic_only=True, actual_checkpoint_validated=False, admission_granted=False,
            live_handoff_authorization=False, tests=tests)
        document(epoch / 'cpu/LOCAL_SOURCE_CPU.json', cpu)
        seal_source(source)
        receipt = dict(schema='PAIR_EPOCH2_LOCAL_PREPARATION_V1', status='LOCAL_PREPARED_NOT_ADMITTED',
            life=life, local_source=str(source), new_source=remote_source, old_guard_sha256=staged['old_guard_sha256'],
            old_source=staged['old_source'], old_source_pins=staged['old_source_pins'],
            epoch1_source=staged['new_source'], epoch1_source_pins=staged['new_source_pins'],
            new_source_pins=pins, changed=delta(staged['old_source_pins'], pins),
            epoch1_to_epoch2_delta=additions, epoch1_preserved=True,
            source_immutability='EXACT_HASH_PINS_FILES_0444_DIRECTORIES_0555',
            source_file_origins={name: {key: value for key, value in entry.items() if key != 'content'}
                for name, entry in resolved[life].items()},
            additional_assets={str(startup): dict(sha256=checksum(birth_bytes), origin=str(birth))},
            plan_template_sha256=checksum(encoded(template)), plan_template_candidate_bound=False,
            metadata_proof_pending=['consumed_WALL_EXTENDED_record_and_intent_at_exact_COMPLETE'],
            journal_id=staged['journal_id'], journal_root=staged['journal_root'],
            copy_raw=observation['guard_metadata'].get('copy_raw', plan['root']),
            deadline_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix'],
            reader_sha256=reader_hash, reader_manifest_sha256=input_hashes[str(manifest_path)],
            parent_dependency_status='PENDING_KUHN_IMPLEMENTATION_AND_EXACT_OWNER_PROOF',
            local_CPU_sha256=checksum(encoded(cpu)), receiving_plan_ready=False,
            live_checkpoint_validated=False, live_binding_reverified=False,
            admission_granted=False, transport_performed=False,
            native_signals=[], reservations=[], dispatches=[], GPU_calls=0)
        document(epoch / 'EPOCH2_SOURCE.json', receipt)
        summaries[life] = dict(receipt=str(epoch / 'EPOCH2_SOURCE.json'),
            receipt_sha256=checksum(encoded(receipt)), source_files=len(pins),
            source_bytes=sum(path.stat().st_size for path in source.rglob('*') if path.is_file()),
            deadline_unix=plan['hard_end_unix'], tests=tests['result'], epoch1_to_epoch2_delta=additions)
    require(all(checksum(Path(path).read_bytes()) == expected for path, expected in input_hashes.items()),
        'all_source_receipts_reader_and_parent_inputs_unchanged')
    summary = dict(schema='PAIR_EPOCH2_LOCAL_PREPARATION_SUMMARY_V1',
        status='LOCAL_PREPARED_CPU_TESTED_NOT_ADMITTED', observed_utc=datetime.now(timezone.utc).isoformat(),
        lives=summaries, parent_dependency_pending=True, reader_owner_ack_pending=True,
        actual_checkpoint_tested=False, native_signals=[], reservations=[], privileged_operations=[], dispatches=[])
    document(output / 'SUMMARY.json', summary)
    publish(output / 'BUILDER_PROVENANCE.md', (
        '# Local builder provenance\n\n[Builder] ' + summary['observed_utc'] +
        ' Non-material same-deadline retention/checkpoint-tail continuity repair. '
        'Both exact epoch2 Python closures reconstructed and source-CPU tested locally; '
        'epoch1 receipts and all input bytes preserved. No live checkpoint/model validation, '
        'native signals, reservations, transport, privileged/service management or dispatch. '
        'Kuhn parent rebind and original admission remain pending. '
        'Hash-prefix cost is measured on synthetic journals only, not a host latency claim.\n').encode())
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    print(json.dumps(prepare(args.output, python=args.python), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
