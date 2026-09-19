"""One new diagnostic through original shared claims and transient-unit route."""

import argparse
import json
from pathlib import Path
import subprocess
import time

import execution as common
from construct_candidate import require, sha


def verify_prepared(root, prepared_sha, freeze_sha):
    common.regular(root / 'PREPARED.json', prepared_sha)
    common.regular(root / 'SOURCE_FREEZE.json', freeze_sha)
    prepared = common.read(root / 'PREPARED.json')
    common.regular(root / 'REGISTRY.json', prepared['registry_sha256'])
    require(prepared['source_freeze_sha256'] == freeze_sha, 'reviewed_source_freeze_join')
    document = common.read(root / 'REGISTRY.json')
    common.validate_registry(document)
    common.regular(root / 'PREREGISTRATION.md', common.PREREGISTRATION['sha256'])
    require(prepared['preregistration'] == common.PREREGISTRATION
        == common.read(root / 'SOURCE_FREEZE.json')['preregistration'], 'preparation_preregistration_join')
    require(Path(document['root']) == root and root.resolve() == root, 'canonical_registry_root')
    files = common.read(root / 'SOURCE_FREEZE.json')['files']
    require(set(files) == set(common.RUNTIME_NAMES), 'entire_diagnostic_runtime_closure')
    for name, expected in files.items():
        common.regular(root / 'runtime' / name, expected)
    require({row['job_id'] for row in prepared['jobs']} == {job['job_id'] for job in document['jobs']},
        'complete_three_job_preparation')
    for row in prepared['jobs']:
        job_root = root / 'jobs' / row['job_id']
        common.regular(job_root / 'CONFIG.json', row['config_sha256'])
        common.regular(job_root / 'MOUNTS.json', row['mounts_sha256'])
        require(common.read(job_root / 'CONFIG.json')['runtime_files'] == files, 'role_source_closure_join')
    return document, prepared


def unit_state(unit):
    result = subprocess.run(['systemctl', 'show', unit + '.service',
        '--property=LoadState,ActiveState,SubState,Result,ExecMainStatus,ExecMainPID'],
        capture_output=True, text=True, timeout=10, check=False)
    require(result.returncode == 0, 'own_unit_observation_failed_no_resubmit')
    return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)


def wait_units(specs, deadline, observe=unit_state, sleeper=time.sleep):
    while time.time() < deadline + 20:
        states = {spec['unit']: observe(spec['unit']) for spec in specs}
        require(all(state.get('LoadState') == 'loaded' for state in states.values()), 'submitted_unit_missing_no_retry')
        if all(state.get('ActiveState') in ('inactive', 'failed')
                or (state.get('ActiveState') == 'active' and state.get('SubState') == 'exited')
                for state in states.values()):
            require(all(state.get('Result') == 'success' and state.get('ExecMainStatus') == '0'
                for state in states.values()), 'own_unit_failure_terminal_no_retry')
            return states
        sleeper(2)
    raise TimeoutError('own_units_not_drained_by_fixed_deadline_no_signals_no_retry')


def launch(document, prepared, mode, deadline, original, launch_sha):
    specs = []
    prepared_jobs = {row['job_id']: row for row in prepared['jobs']}
    for job in document['jobs']:
        config_sha = prepared_jobs[job['job_id']]['config_sha256']
        for role in ('judge', 'player'):
            spec = common.command(document, job, role, mode, config_sha, launch_sha, deadline, time.time())
            specs.append(spec)
    return specs


def prove(document, prepared, original):
    root = Path(document['root'])
    with common.shared_lock():
        common.verify_host(document, original)
        require(not (root / 'BLOCK_LAUNCH.json').exists(), 'block_already_attempted_no_retry')
        original.validate_admission(common.original_inventory_config(document), original.gpu_inventory())
        now = time.time()
        deadline = min(now + 2400, document['hard_end_unix'])
        common.reserve(document, deadline, now)
        intent = dict(block_id=document['block_id'], diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'],
            created_unix=now, deadline_unix=deadline, model_dispatch_authorized=False,
            mode='CPU_CUSTODY_PROOF_ONLY', job_configs={row['job_id']: row['config_sha256'] for row in prepared['jobs']},
            no_native_signals=True, prior_histories_preserved=True)
        common.write_once(root / 'BLOCK_LAUNCH.json', intent)
        launch_sha = sha(root / 'BLOCK_LAUNCH.json')
        specs = launch(document, prepared, 'proof', deadline, original, launch_sha)
        for spec in specs:
            common.terminal_submit(spec)
    states = wait_units(specs, deadline)
    proofs = {}
    for job in document['jobs']:
        for role in ('judge', 'player'):
            path = Path(job['root']) / 'view' / (role + '_CUSTODY_PROOF.json')
            proof = common.read(path)
            require(proof['status'] == 'PROVED_NO_MODEL_LOADED'
                and proof['model_loaded'] is False and proof['role'] == role
                and proof['launch_sha256'] == launch_sha
                and proof['config_sha256'] == intent['job_configs'][job['job_id']]
                and proof['diagnostic_epoch_sha256'] == document['diagnostic_epoch_sha256'], 'bound_role_custody_proof')
            proofs[job['job_id'] + ':' + role] = dict(path=str(path), sha256=sha(path))
    common.write_once(root / 'PROOFS_COMPLETE.json', dict(status='CPU_PROOFS_COMPLETE_MAIN_REVIEW_REQUIRED',
        model_loaded=False, proof_files=proofs, unit_states=states, launch_sha256=launch_sha,
        diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], deadline_unix=deadline,
        observed_unix=time.time()))
    return dict(status='CPU_PROOFS_COMPLETE_MAIN_REVIEW_REQUIRED', root=str(root),
        proof_sha256=sha(root / 'PROOFS_COMPLETE.json'), deadline_unix=deadline)


def validate_completion(config, complete, loaded):
    require(complete['actual_generated_tokens'] == 6144 and len(complete['cells']) == 6,
        'six_cells_exact_6144_actual_tokens')
    require(all(cell['generated_tokens'] == 1024 and cell['status'] == 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET'
        for cell in complete['cells']), 'all_cells_complete_not_shortfall')
    scenes = {cell['contest_id'] for cell in complete['cells']}
    require(scenes == set(config['expected_scene_ids']) == set(common.SCENE_IDS), 'pinned_manifest_scene_identity')
    require(len(scenes) == 3 and {(cell['contest_id'], cell['seed']) for cell in complete['cells']}
        == {(scene, seed) for scene in scenes for seed in common.SEEDS}, 'declared_new_seed_cross_product')
    require(complete['diagnostic_epoch_sha256'] == loaded['diagnostic_epoch_sha256']
        == config['diagnostic_epoch_sha256'] and complete['judge_epoch_sha256'] == loaded['judge_epoch_sha256']
        == config['diagnostic_epoch']['judge_epoch_sha256'], 'same_sampling_and_reference_judge_epochs')
    require(complete['source_age'] == loaded['source_age'] == config['source_checkpoint'], 'same_captured_source')
    require(complete['parent_tokens'] == 0 and complete['training_updates'] == 0
        and loaded['parent_tokens'] == 0 and loaded['snapshot_context_used'] is False, 'parent_free_frozen_completion')
    require(complete['unchanged_identity']['all_parameters_frozen'] is True, 'no_parameter_updates')
    for field in ('base_sha256', 'adapter_state_sha256'):
        require(complete['unchanged_identity'].get(field) == loaded['identity'].get(field)
            == config['original_parameter_identity'].get(field), 'same_model_identity')
    for field in ('decoder', 'tokenizer_backend_sha256', 'chat_template_sha256', 'library_versions'):
        require(loaded['identity'][field] == config['original_parameter_identity'][field], 'same_inference_identity:' + field)


def run(document, prepared, original, proof_sha):
    require(not document.get('proof_only'), 'cpu_diagnostic_cannot_load_models')
    root = Path(document['root'])
    common.regular(root / 'PROOFS_COMPLETE.json', proof_sha)
    proof = common.read(root / 'PROOFS_COMPLETE.json')
    intent = common.read(root / 'BLOCK_LAUNCH.json')
    require(proof['launch_sha256'] == sha(root / 'BLOCK_LAUNCH.json'), 'review_exact_custody_proof')
    for reference in proof['proof_files'].values():
        common.regular(Path(reference['path']), reference['sha256'])
    require(time.time() + 1500 < intent['deadline_unix'], 'whole_predeclared_block_must_fit_original_window')
    with common.shared_lock():
        common.verify_host(document, original)
        common.verify_claims(document, intent['deadline_unix'])
        original.validate_admission(common.original_inventory_config(document), original.gpu_inventory())
        common.write_once(root / 'GPU_REVIEW.json', dict(reviewed_proof_sha256=proof_sha,
            observed_unix=time.time(), launch_sha256=sha(root / 'BLOCK_LAUNCH.json'),
            diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], one_shot=True))
    completed = []
    prepared_jobs = {row['job_id']: row for row in prepared['jobs']}
    for job in document['jobs']:
        job_root = Path(job['root'])
        with common.shared_lock():
            common.verify_host(document, original)
            common.verify_claims(document, intent['deadline_unix'])
            original.validate_admission(common.original_inventory_config(document), original.gpu_inventory())
            pair = [common.command(document, job, role, 'run', prepared_jobs[job['job_id']]['config_sha256'],
                sha(root / 'BLOCK_LAUNCH.json'), intent['deadline_unix'], time.time()) for role in ('judge', 'player')]
            common.write_once(job_root / 'DISPATCH_INTENT.json', dict(observed_unix=time.time(),
                diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], specifications=pair))
            for spec in pair:
                common.terminal_submit(spec)
        states = wait_units(pair, intent['deadline_unix'])
        config = common.read(job_root / 'CONFIG.json')
        output = job_root / 'view/players' / config['condition']
        complete, loaded = (common.read(output / name) for name in ('COMPLETE.json', 'LOADED.json'))
        validate_completion(config, complete, loaded)
        completed.append(dict(arm=job['arm'], job_id=job['job_id'], unit_states=states,
            complete_sha256=sha(output / 'COMPLETE.json'), loaded_sha256=sha(output / 'LOADED.json')))
        common.write_once(job_root / 'COMPLETION_VERIFIED.json', completed[-1])
    with common.shared_lock():
        common.verify_host(document, original)
        common.verify_claims(document, intent['deadline_unix'])
        original.validate_admission(common.original_inventory_config(document), original.gpu_inventory())
        common.write_once(root / 'BLOCK_COMPLETE.json', dict(status='COMPLETE_THREE_SOURCE_SAMPLING_DIAGNOSTIC',
            observed_unix=time.time(), jobs=completed, diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'],
            original_attempts_unchanged=True, independent_training_lineages=False))
        for device in document['role_devices'].values():
            path = common.CLAIMS / (device['uuid'] + '.json')
            path.rename(path.with_name(path.stem + '.completed.' + document['block_id'] + '.json'))
    return dict(status='COMPLETE_THREE_SOURCE_SAMPLING_DIAGNOSTIC', root=str(root))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prepared-sha256', required=True)
    parser.add_argument('--source-freeze-sha256', required=True)
    parser.add_argument('--proof-sha256')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--prove', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    document, prepared = verify_prepared(args.root, args.prepared_sha256, args.source_freeze_sha256)
    original = common.load_v4()
    common.verify_host(document, original)
    require(not (args.root / 'BLOCK_FAILED.json').exists(), 'failed_block_never_retried')
    if args.check:
        print(json.dumps(dict(status='CPU_VERIFIED_NO_RESERVATION_NO_DISPATCH', registry=document,
            prepared=prepared, inventory=original.gpu_inventory(),
            custody_namespace_proof_pending=not (args.root / 'PROOFS_COMPLETE.json').exists()), sort_keys=True))
        return
    try:
        if args.prove:
            result = prove(document, prepared, original)
        else:
            require(args.proof_sha256 is not None, 'main_reviewed_proof_required')
            result = run(document, prepared, original, args.proof_sha256)
        print(json.dumps(result, sort_keys=True))
    except Exception as error:
        if not (args.root / 'BLOCK_LAUNCH.json').exists():
            common.write_once(args.root / ('ADMISSION_NOT_GRANTED_' + str(time.time_ns()) + '.json'), dict(
                error_type=type(error).__name__, error=str(error), observed_unix=time.time(),
                status='NOT_DISPATCHED_NO_SOURCE_ATTEMPT_CONSUMED', automatic_retry=False))
            raise
        if not (args.root / 'BLOCK_FAILED.json').exists():
            common.write_once(args.root / 'BLOCK_FAILED.json', dict(error_type=type(error).__name__,
                error=str(error), observed_unix=time.time(), status='TERMINAL_NO_RETRY_NO_FALLBACK',
                original_histories_preserved=True, kept_life_signals=[]))
        raise


if __name__ == '__main__':
    main()
