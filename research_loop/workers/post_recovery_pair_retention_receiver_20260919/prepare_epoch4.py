"""Prepare a new local pair epoch4 only; never produce live authority or dispatch."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from prepare_epoch2 import (HERE, LIVES, checksum, delta, document, plan_template,
    publish, read, require, run_checks, seal_source)
from prepare_epoch3 import EXPECTED_HISTORY, HISTORY, source_files
from prefix_ports import proposed


PEER = HERE.parent / 'post_recovery_prefix_proof_20260919/consumer_context_v4'
PEER_PINS = {
    'checkpoint_tail_runtime.candidate.py': '4e7746a8da7f99cb0354beb8d489a92e8fcb387e1409256901d1a9b0a033803c',
    'immutable_prefix_proof.py': 'ce5542e08f463cac4d795100bdc409480b4aef162632dc2aa6642bed9d08960b',
    'prefix_cli.py': 'bdb5eea3bb2f5af109fcd9c0d9ae0dd85b4605dadf92565d4ed67bd5751547b8',
    'source_port.py': 'e55c28f7dfadc859e2d966077bba027d8f95f5da00de5dc4e75373f955349aa9',
    'context_extension.py': 'ba8c0651923edc482c848fef1df27e643f953e646a736096f920959eadc84ee4',
}
CHANGES = {'gpu/checkpoint_tail_runtime.py', 'gpu/immutable_prefix_proof.py',
    'gpu/pair_prefix_authority.py', 'gpu/pair_retention_runtime.py', 'gpu/r205_runtime.py'}


def peer_bytes():
    contents = {name: (PEER / name).read_bytes() for name in PEER_PINS}
    require({name: checksum(content) for name, content in contents.items()} == PEER_PINS,
        'exact_reviewed_v4_bytes_required_no_moving_peer_dependency')
    return contents


def prefix_checks(source, directory, python):
    directory.mkdir(parents=True)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), OMP_NUM_THREADS='1', TMPDIR=str(directory))
    command = [str(python), '-B', str(HERE / 'prefix_source_checks.py'), '--source', str(source)]
    started = time.monotonic()
    result = subprocess.run(command, cwd=source, env=environment, capture_output=True, text=True, timeout=240)
    publish(directory / 'PREFIX_TESTS.stdout', result.stdout.encode())
    publish(directory / 'PREFIX_TESTS.stderr', result.stderr.encode())
    require(result.returncode == 0, 'prefix_source_tests_failed:' + str(directory))
    evidence = json.loads(result.stdout)
    require(evidence['passed'] and evidence['no_GPU_calls'] and evidence['synthetic_only']
        and evidence['actual_namespace_route_tested'] is False, 'synthetic_only_prefix_evidence')
    return dict(command=command, elapsed_seconds=time.monotonic() - started, returncode=result.returncode,
        result=evidence, stdout_sha256=checksum(result.stdout.encode()), stderr_sha256=checksum(result.stderr.encode()))


def prepare(output, *, python=sys.executable):
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(HERE) and not output.exists(),
        'new_local_worker_epoch4_output_only')
    peer = peer_bytes()
    inputs = {}
    for life in LIVES:
        previous = HERE / 'prepared_epoch3_v1' / life / 'epoch3'
        old = read(previous / 'EPOCH3_SOURCE.json')
        files = source_files(previous / 'source')
        require({name: checksum(content) for name, content in files.items() if name.endswith('.py')}
            == old['new_source_pins'] and old['new_source_pins'][HISTORY] == EXPECTED_HISTORY,
            'exact_preserved_epoch3_with_history_fix')
        ports, changes = proposed(previous / 'source', peer['checkpoint_tail_runtime.candidate.py'],
            peer['immutable_prefix_proof.py'])
        require(set(changes) == CHANGES, 'only_explicit_epoch4_source_allowlist')
        inputs[life] = (previous, old, files, ports, changes)
    for name, content in peer.items():
        publish(output / 'operator_prefix_producer' / name, content)
    document(output / 'INPUTS.json', dict(peer_path=str(PEER), peer_pins=PEER_PINS,
        source_checks_sha256=checksum((HERE / 'source_checks.py').read_bytes()),
        prefix_source_checks_sha256=checksum((HERE / 'prefix_source_checks.py').read_bytes()),
        preparer_sha256=checksum(Path(__file__).read_bytes()), admission_granted=False))
    results = {}
    for life, (previous, old, files, ports, changes) in inputs.items():
        epoch = output / life / 'epoch4'
        source = epoch / 'source'
        revised = dict(files, **ports)
        for name, content in revised.items():
            publish(source / name, content)
        pins = {name: checksum(content) for name, content in revised.items() if name.endswith('.py')}
        require(len(pins) == 211 and delta(old['new_source_pins'], pins) == changes
            and pins[HISTORY] == EXPECTED_HISTORY, 'exact_211_file_epoch4')
        remote = str(Path(old['new_source']).parent.parent / 'epoch4/source')
        plan = plan_template(read(previous / 'control/PLAN.template.json'), remote)
        require(plan['hard_end_unix'] == old['deadline_unix'], 'same_deadline_no_extension')
        document(epoch / 'control/PLAN.template.json', plan)
        document(epoch / 'control/SOURCE_EPOCH.template.json', dict(schema='PAIR_PREFIX_SOURCE_EPOCH_V1',
            epoch_id=life + '-retention-epoch4', source_root=remote, source_pins_sha256=checksum(
                json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()), deadline_unix=old['deadline_unix']))
        document(epoch / 'control/AUTHORITY_PENDING.json', dict(status='PENDING_MAIN_PINNED_ORIGINAL_ADMISSION',
            schema='PAIR_PREFIX_OPERATOR_AUTHORITY_V1', source=dict(root=remote, pins=pins),
            namespace_policy='SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE',
            admission_derivation='EXACT_B_AND_PREAPPROVED_CAPS_IN_ORIGINAL_CPU_ALLOCATION_GUARD_V1',
            deadline_unix=old['deadline_unix'], producer_pin=PEER_PINS['prefix_cli.py'],
            proof=None, producer_receipt=None, life_binding_sha256=None, confinement_sha256=None,
            max_advance_records=None, max_advance_bytes=None, authorizes_handoff=False))
        document(epoch / 'control/PARENT_DEPENDENCY_PENDING.json', dict(status='PENDING_ACTUAL_OWNER_FENCE_AND_REBIND',
            parent_owner='Kuhn', previous_contract=read(previous / 'control/PARENT_DEPENDENCY_PENDING.json'),
            source_epoch_must_be_rebound=True, dependency_receipt=None, rebind_receipt=None))
        tests = run_checks(source, epoch / 'cpu', python)
        prefix = prefix_checks(source, epoch / 'cpu/prefix', python)
        document(epoch / 'cpu/LOCAL_SOURCE_CPU.json', dict(schema='PAIR_EPOCH4_LOCAL_SOURCE_CPU_V1',
            passed=True, source_pins=pins, tests=tests, prefix_tests=prefix, no_GPU_calls=True,
            synthetic_only=True, actual_checkpoint_validated=False, actual_namespace_route_tested=False,
            admission_granted=False, live_handoff_authorization=False))
        require(source_files(previous / 'source') == files and source_files(source) == revised,
            'original_epoch_preserved_and_tested_source_unchanged')
        seal_source(source)
        receipt = dict(schema='PAIR_EPOCH4_LOCAL_PREPARATION_V1', status='LOCAL_PREPARED_NOT_ADMITTED',
            life=life, local_source=str(source), new_source=remote, new_source_pins=pins,
            old_source=old['old_source'], old_source_pins=old['old_source_pins'],
            old_guard_sha256=old['old_guard_sha256'], changed=delta(old['old_source_pins'], pins),
            epoch3_source=old['new_source'], epoch3_source_pins=old['new_source_pins'],
            epoch3_to_epoch4_delta=changes, epoch1_preserved=True, epoch2_preserved=True, epoch3_preserved=True,
            source_immutability='EXACT_HASH_PINS_FILES_0444_DIRECTORIES_0555', additional_assets=old['additional_assets'],
            journal_root=old['journal_root'], journal_id=old['journal_id'], copy_raw=old['copy_raw'],
            deadline_unix=old['deadline_unix'], lease_end_unix=old['lease_end_unix'],
            plan_template_candidate_bound=False, plan_template_sha256=checksum((epoch / 'control/PLAN.template.json').read_bytes()),
            local_CPU_sha256=checksum((epoch / 'cpu/LOCAL_SOURCE_CPU.json').read_bytes()),
            receiving_plan_ready=False, admission_granted=False, actual_namespace_route_tested=False,
            parent_dependency_status='PENDING', live_checkpoint_validated=False, live_binding_reverified=False,
            native_signals=[], reservations=[], dispatches=[], GPU_calls=0, transport_performed=False)
        document(epoch / 'EPOCH4_SOURCE.json', receipt)
        results[life] = dict(receipt=str(epoch / 'EPOCH4_SOURCE.json'), python_files=len(pins),
            source_tests=tests['result'], prefix_tests=prefix['result'], epoch3_to_epoch4_delta=changes)
    seal_source(output / 'operator_prefix_producer')
    summary = dict(schema='PAIR_EPOCH4_LOCAL_PREPARATION_SUMMARY_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        status='LOCAL_PREPARED_CPU_TESTED_NOT_ADMITTED', results=results, native_signals=[],
        reservations=[], dispatches=[], admission_granted=False, actual_namespace_route_tested=False)
    document(output / 'SUMMARY.json', summary)
    publish(output / 'BUILDER_PROVENANCE.md', ('[Builder] ' + summary['observed_utc'] +
        ' Non-material offline exact epoch4 only. Canonical Kuhn v4 prefix ABI, original CPU/allocation/guard-bound '
        'B derivation and opt-in receiving source. Synthetic checks only, no actual confined route proof. '
        'Epoch1/2/3 and deadline unchanged. No native/parent signal, reservation, transport, service management, '
        'GPU/model load or dispatch. Main approval, original objects, bounded real-route timing and owner fence '
        'remain necessary; no runtime authority was generated.\n').encode())
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.output), sort_keys=True, indent=2))
