"""Verify the selected offline closure and write a non-authorizing Main handoff."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile


WORKER = Path(__file__).resolve().parent.parent
SELECTED = WORKER / 'prepared_epoch4_v5'
BUNDLE = SELECTED / 'C2/epoch4'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def write(name, value):
    path = WORKER / name
    with path.open('x') as output:
        output.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    path.chmod(0o444)
    return dict(path=str(path), sha256=sha(path))


def verify_epoch(bundle, manifest_name):
    manifest = read(bundle / manifest_name)
    expected = dict(manifest['new_source_pins'])
    expected.update({name: entry['sha256'] for name, entry in manifest['additional_assets'].items()})
    actual = {str(path.relative_to(bundle / 'source')): sha(path)
        for path in (bundle / 'source').rglob('*') if path.is_file()}
    require(actual == expected, 'exact_all_source_files:' + str(bundle))
    for name, expected_hash in manifest['helper_pins'].items():
        require(sha(bundle / 'tools' / name) == expected_hash, 'exact_helper:' + name)
    return dict(manifest_sha256=sha(bundle / manifest_name), python_files=len(manifest['new_source_pins']),
        exact_source_and_helpers=True)


def main():
    candidate = read(SELECTED / 'CANDIDATE.json')
    manifest = read(BUNDLE / 'EPOCH4_SOURCE.json')
    require(sha(BUNDLE / 'EPOCH4_SOURCE.json') == candidate['manifest_sha256'], 'selected_manifest_pin')
    require(sha(candidate['archive']) == candidate['archive_sha256'], 'selected_archive_pin')
    verified = verify_epoch(BUNDLE, 'EPOCH4_SOURCE.json')
    for root in (BUNDLE / 'source', BUNDLE / 'tools', BUNDLE / 'provenance'):
        require(all(not path.is_symlink() and not path.stat().st_mode & 0o222
            for path in (root, *root.rglob('*'))), 'sealed_source_tools_provenance')
    with tarfile.open(candidate['archive'], 'r:gz') as archive:
        members = set()
        for member in archive.getmembers():
            require(member.isfile() or member.isdir(), 'regular_archive_members')
            require(not Path(member.name).is_absolute() and '..' not in Path(member.name).parts, 'literal_archive_paths')
            if member.isfile():
                require(hashlib.sha256(archive.extractfile(member).read()).hexdigest() == sha(SELECTED / member.name),
                    'archive_exact_selected_bytes')
                members.add(member.name)
        require(members == {str(path.relative_to(SELECTED)) for path in BUNDLE.rglob('*') if path.is_file()},
            'complete_archive_member_set')
    historical = {}
    for version in ('epoch2', 'epoch3'):
        directory = 'prepared_epoch2_v2' if version == 'epoch2' else 'prepared_epoch3_v1'
        historical[version] = verify_epoch(WORKER / directory / 'C2' / version, version.upper() + '_SOURCE.json')
    checks = {name: read(BUNDLE / 'cpu' / (name + '.json')) for name in candidate['tests']}
    require(all(check['passed'] is True for check in checks.values()), 'all_selected_source_tests_pass')
    preflight = (BUNDLE / 'cpu/PREFLIGHT_TESTS.log').read_text()
    require('Ran 17 tests' in preflight and preflight.endswith('\nOK\n'), '17_focused_preflight_checks')
    sealed_cpu = read('/tmp/C2_EPOCH4_V5_SOURCE_CPU.json')
    require(sealed_cpu['passed'] is True and sealed_cpu['source_pins'] == manifest['new_source_pins']
        and sealed_cpu['manifest_sha256'] == candidate['manifest_sha256'], 'postseal_standalone_source_validation')
    source_receipt = write('EPOCH4_SOURCE_CPU_FINAL.json', sealed_cpu)
    observations = {}
    for filename in ('C2_PREFIX_PRODUCED_1789786161.json', 'C2_PREFIX_FAST_READ_A_1789786189.json',
            'C2_PREFIX_NATIVE_VIEW_1789786184.json'):
        path = WORKER.parent / 'post_recovery_pair_receiving_checks_20260919' / filename
        observations[filename] = dict(path=str(path), sha256=sha(path),
            scope='MAIN_185_FILE_OBSERVER_NOT_THIS_186_FILE_NATIVE_EPOCH')
    blockers = [
        'Main_pinned_production_epoch_authority_and_own_186_python_plus_startup_asset_proof_required',
        'actual_eligible_COMPLETE_LEARN_boundary_not_REQUEST_RESPONSE',
        'C2_executable_owner_fence_drain_identity_locks_ledger_rebind_transport_not_implemented',
        'C2_reserved_coordinator_not_packaged_or_proven_MainRoute_is_capability_contract_only',
        'actual_full_reserved_work_plus_commit_margin_within_unchanged_30_seconds_not_proven',
        'original_r188_allocation_privileged_admission_and_actual_new_consumer_object_checks_required',
        'peer_single_ABI_acknowledgement_and_Main_final_review_pending']
    remote = '/localhome/local-rohing/orch_retention_20260919/C2/epoch4'
    cpu_invocation = ['python3', '-B', remote + '/tools/cpu_check.py', 'source', '--bundle', remote]
    stage = dict(schema='C2_EPOCH4_MAIN_STAGE_MANIFEST_V1', status='OFFLINE_CANDIDATE_NOT_AUTHORIZATION',
        observed_utc=datetime.now(timezone.utc).isoformat(), selected_local_bundle=str(BUNDLE),
        archive=dict(path=candidate['archive'], sha256=candidate['archive_sha256']),
        manifest=dict(path=str(BUNDLE / 'EPOCH4_SOURCE.json'), sha256=candidate['manifest_sha256']),
        source_pins=manifest['new_source_pins'], proof_source_pins=dict(manifest['new_source_pins'],
            **{name: entry['sha256'] for name, entry in manifest['additional_assets'].items()}),
        epoch3_to_epoch4_delta=manifest['epoch3_to_epoch4_delta'], old_live_to_epoch4_delta=manifest['changed'],
        exact_helpers=manifest['helper_pins'], original_admission_module='gpu.r188_node5_confinement',
        hard_end_unix=1789927200, lease_end_unix=1789948800,
        runtime_python_files=186, proof_source_files_including_startup_context=187,
        source_cpu_invocation=cpu_invocation,
        CPU_environment=dict(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1'),
        producer_cli=str(BUNDLE / 'tools/prefix_cli.py'),
        receiver_tool=str(BUNDLE / 'tools/receiving_core.py'),
        preflight_tool=str(BUNDLE / 'tools/prefix_preflight.py'),
        ABI='Kuhn_v4_scan_prefix_proof_and_prefix_admission',
        original_authority_chain='original_guard_allocation_passed_CPU_Main_authority_bounded_receiving_CPU_clause',
        default_unchanged=True, no_prefix_autodiscovery=True, cloned_journal_rejected=True,
        proof_must_be_created_after_actual_stage_sealing=True, observer_proof_reuse_allowed=False,
        static_source_epoch_template=str(BUNDLE / 'control/SOURCE_EPOCH.template.json'),
        historical_default_11502_verified=False, historical_12902_saved_checkpoint_not_handoff=True,
        test_counts=dict(candidate['tests'], bounded_preflight_and_generated_receiver=17),
        total_tests=sum(candidate['tests'].values()) + 17, postseal_source_receipt=source_receipt,
        historical_epochs_verified=historical, blockers=blockers,
        main_observer_evidence_not_production_proof=observations,
        native_signals=[], remote_actions=[], dispatches=[], parent_deliveries=[], GPU_calls=0,
        execution_authorized=False, staging_performed=False)
    stage_reference = write('EPOCH4_MAIN_STAGE.json', stage)
    receipt = write('EPOCH4_HANDOFF_COMPLETE.json', dict(schema='C2_EPOCH4_OFFLINE_HANDOFF_COMPLETE_V1',
        source_candidate_complete=True, operational_integration_complete=False, dispatch_ready=False,
        selected=stage_reference, source_validation=verified, total_tests=stage['total_tests'],
        epoch3_tree_unchanged_during_build=candidate['epoch3_unchanged'],
        source_and_tools_sealed=True, archive_revalidated=True, blocker_details=blockers,
        no_live_actions=True, operator_authority_generated=False))
    print(json.dumps(dict(stage=stage_reference, receipt=receipt), indent=2))


if __name__ == '__main__':
    main()
