"""Explicit sole-scorer continuation, disabled until owner closure gates pass."""

import argparse
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import sys
import time

from ..projected_wire.contract import byte_digest, canonical, decode, digest, require, validate_binding
from ..projected_wire.continuation import reattach_existing_epoch
from ..projected_wire.custody import OwnerStore, load_binding
from ..projected_wire.receiver import ProjectedHub
from .legacy import verify_drain
from .relay import SESSIONS


ORIGINAL_MODULE = 'research_loop.workers.rohin233_ovx4_recovery_20260918.judge_service'
ORIGINAL_SOURCE_SHA256 = 'c5ea88e80e520fe35dc3df9c5b442060bd86ced4453e779c5cfe585cc552ef0c'
ORIGINAL_CONFIG_SHA256 = 'a7f14a4dae4595f1d8056665cb450d78387387b81694c7c3e52286641d4d06c1'
ORIGINAL_MANIFEST_SHA256 = '499831e0fb0330cf916c814ff2a3b7820c9678a1fa7a4839bfd7b1d0455e4797'
ORIGINAL_SCORER_DEADLINE = 1790791170
ORIGINAL_TRANSPORT_DEADLINE = 1790272760


def file_hash(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.resolve() == path,
        'canonical_regular_preserved_file')
    result = hashlib.sha256()
    before = path.stat()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
        'immutable_file_during_closure_read')
    return result.hexdigest()


def reference(value):
    require(file_hash(value['path']) == value['sha256'], 'bound_file_bytes')
    return decode(Path(value['path']).read_bytes())


def verify_tree(tree):
    root = Path(tree['root'])
    require(root.is_dir() and root.resolve() == root, 'canonical_preserved_tree')
    actual = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'no_preserved_tree_symlinks')
        if path.is_file():
            actual[str(path.relative_to(root))] = file_hash(path)
        else:
            require(path.is_dir(), 'only_regular_artifacts_in_state_tree')
    require(actual == tree['files'], 'complete_preserved_tree_not_selected_files')
    return actual


def verify_source(plan):
    manifest = reference(plan['original_source_manifest'])
    require(plan['original_source_manifest']['sha256'] == ORIGINAL_MANIFEST_SHA256 and len(manifest) == 129,
        'actual_deployed_129_file_source_closure')
    root = Path(plan['source_root'])
    for relative, expected in manifest.items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'confined_original_source')
        require(file_hash(root / relative) == expected, 'unchanged_original_dependency')
    require(manifest[ORIGINAL_MODULE.replace('.', '/') + '.py'] == ORIGINAL_SOURCE_SHA256,
        'actual_deployed_not_current_checkout_main')
    additions = reference(plan['candidate_source_manifest'])
    for relative, expected in additions.items():
        require(relative.startswith('research_loop/workers/post_reboot_node3_parents_20260919/')
            and '..' not in Path(relative).parts, 'additive_worker_only_candidate')
        require(file_hash(root / relative) == expected, 'bound_candidate_source')
    worker = 'research_loop/workers/post_reboot_node3_parents_20260919/'
    required = {worker + 'projected_wire/' + name + '.py' for name in
        ('__init__', 'contract', 'custody', 'receiver', 'continuation', 'relay', 'cli')} | {
        worker + 'transactional_ingress/' + name + '.py' for name in
        ('__init__', 'candidate', 'ledger', 'legacy', 'relay')}
    require(required <= set(additions), 'entire_candidate_and_projected_runtime_in_immutable_manifest')
    for module in list(sys.modules.values()):
        source = getattr(module, '__file__', None)
        if not source:
            continue
        for relative in manifest.keys() | additions.keys():
            if str(source).endswith('/' + relative):
                require(Path(source).resolve() == root / relative, 'no_mixed_checkout_imports')
    return manifest


def verify_state(plan, config):
    states = {identifier: reference(value) for identifier, value in plan['session_snapshots'].items()}
    require(set(states) == set(SESSIONS.values()) == set(config['outputs']) == set(plan['bindings'])
        == set(plan['epochs']), 'same_five_native_sessions_no_base_added')
    trees = {tree['root']: tree for tree in plan['preserved_trees']}
    require(len(trees) == len(plan['preserved_trees']), 'unique_preserved_state_roots')
    required_roots = {config['outputs'][identifier] for identifier in states} | {
        str(Path(config['root']) / 'epochs' / identifier) for identifier in states}
    required_roots |= {plan['owner_custody']}
    require(required_roots <= set(trees), 'full_output_attempt_and_epoch_trees_required')
    for tree in trees.values():
        verify_tree(tree)
    for identifier, state in states.items():
        output = Path(config['outputs'][identifier])
        require(state['phase'] == 'COMPLETE' and state['source_mode'] == 'NATIVE_JOURNAL',
            'complete_original_native_session')
        require(file_hash(output / 'SESSION_STATE.private.json') == plan['session_snapshots'][identifier]['sha256'],
            'live_saved_state_equals_immutable_handoff')
        require(len(state['seen']) == len(set(state['seen'])), 'unique_original_seen_ledger')
        attempts = {path.name for path in (output / 'attempts').iterdir()}
        require(attempts == set(state['seen']), 'no_unaccounted_attempt_or_seen_id')
        for identifier_sha256 in attempts:
            attempt = output / 'attempts' / identifier_sha256
            require(attempt.is_dir() and all((attempt / name).is_file()
                for name in ('REQUEST.json', 'BEFORE.json', 'RESULT.json', 'AFTER.json')),
                'every_original_attempt_has_complete_durable_outcome')
        binding = reference(plan['bindings'][identifier])
        validate_binding(binding)
        require(binding['session_id'] == identifier and binding['registry'] == state['session_binding']
            and binding['mirror_root'] == state['life_root'] and binding['transport_epoch'] == plan['transport_epoch']
            and binding['deadline_unix'] == ORIGINAL_TRANSPORT_DEADLINE, 'exact_original_source_and_separate_deadline')
        epoch = plan['epochs'][identifier]
        epoch_path = str(Path(config['root']) / 'epochs' / identifier)
        require(epoch['files'] == trees[epoch_path]['files']
            and epoch['epoch_sha256'] == binding['judge_epoch_sha256'], 'same_full_epoch_ledger_and_binding')
    queue = reference(plan['queue_dispositions'])
    require(queue['unenumerated_legacy_admissions'] is False
        and queue['historical_replay_authorized'] is False, 'all_legacy_queue_lifetimes_resolved_not_replayed')
    seen_origins = set()
    for row in queue['dispositions']:
        require(row['session'] in states and row['disposition'] in ('COMPLETE', 'UNKNOWN_NO_REPLAY',
            'PREPARED_NEVER_DISPATCHED', 'NO_JUDGMENT_EXPIRED'), 'explicit_session_queue_disposition')
        key = (row['session'], row['request']['origin']['record_sha256'])
        require(key not in seen_origins, 'unique_legacy_origin_disposition')
        seen_origins.add(key)
        if row['disposition'] == 'COMPLETE':
            require(key[1] in states[row['session']]['seen'], 'complete_queue_origin_in_original_seen')
    require(queue['origin_request_authority'] == 'ORIGINAL_OWNER_REQUEST_ARTIFACTS'
        and queue['unattributed_connections_disposed'] is True, 'no_invented_metrics_or_missing_legacy_connections')
    return states, queue


def preflight(plan):
    require(plan['schema'] == 'R233_SINGLE_SCORER_CONTINUATION_V1', 'explicit_owner_continuation_plan')
    manifest = verify_source(plan)
    config = reference(plan['original_config'])
    require(plan['original_config']['sha256'] == ORIGINAL_CONFIG_SHA256 and config['kind'] == 'shared'
        and config['physical'] == 4 and config['deadline_unix'] == ORIGINAL_SCORER_DEADLINE,
        'unchanged_exact_original_config_physical4_deadline')
    proof = reference(plan['drain_proof'])
    witness = reference(plan['legacy_code_witness'])
    require(proof['source_witness_sha256'] == plan['legacy_code_witness']['sha256']
        and witness['original_source_manifest_sha256'] == ORIGINAL_MANIFEST_SHA256
        and all(manifest[relative] == value['sha256'] for relative, value in witness['protocol_sources'].items()),
        'drain_lifecycle_bound_to_actual_original_code')
    verdict = verify_drain(proof, plan['old_identity'])
    require(proof['state_closure_sha256'] == digest(plan['preserved_trees'])
        and proof['queue_dispositions_sha256'] == plan['queue_dispositions']['sha256'], 'drain_bound_to_actual_queue_state')
    states, queue = verify_state(plan, config)
    require(plan['transport_epoch'] != plan['previous_transport_epoch'], 'explicit_new_transport_epoch')
    require(reference(plan['original_loaded'])['weight_proofs'] == plan['weight_proofs'], 'original_loaded_weight_proofs')
    for name in ('primary_scalar', 'primary_panels'):
        reference(plan[name])
    require(plan['primary_scalar']['path'] == str(Path(config['root']) / 'primary_scalar.json')
        and plan['primary_panels']['path'] == str(Path(config['root']) / 'PRIMARY_PANEL_SCORES.private.json'),
        'reuse_original_primary_config_and_panels_without_rewriting')
    return config, states, queue, verdict


def require_retired(identity):
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == identity['boot_id'],
        'original_real_scorer_host_namespace')
    require(os.readlink('/proc/self/ns/pid') == identity['pid_namespace'], 'real_host_pid_namespace_not_sandbox_absence')
    path = Path('/proc') / str(identity['pid']) / 'stat'
    if path.exists():
        fields = path.read_text().rsplit(')', 1)[1].split()
        require(fields[19] != str(identity['start_ticks']), 'original_scorer_still_present_do_not_load_second_model')


def require_runtime(plan):
    captured = reference(plan['original_environment'])
    require(captured['source_identity'] == plan['old_identity'], 'original_owner_captured_unit_environment')
    environment = captured['environment']
    fields = ('CUDA_VISIBLE_DEVICES', 'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'OMP_NUM_THREADS',
        'MKL_NUM_THREADS', 'TOKENIZERS_PARALLELISM')
    require(environment['CUDA_VISIBLE_DEVICES'].startswith('GPU-')
        and all(os.environ.get(name) == environment[name] for name in fields), 'same_original_gpu_uuid_and_runtime')
    require(os.environ.get('PYTHONPATH') == plan['source_root'], 'new_closed_source_namespace_only')
    status = Path('/proc/self/status').read_text()
    require('NoNewPrivs:\t1' in status, 'original_no_new_privileges_confinement')


class QuarantinedHub:
    def __init__(self, projected, queue):
        self.projected = projected
        self.root, self.sessions, self.registry = projected.root, projected.sessions, projected.registry
        self.quarantine = {(row['session'], row['request']['origin']['record_sha256'])
            for row in queue['dispositions']}

    def native(self, incoming):
        key = (incoming.get('session_id'), incoming.get('request', {}).get('origin', {}).get('record_sha256'))
        require(key not in self.quarantine, 'legacy_origin_quarantined_no_historical_or_ambiguous_replay')
        return self.projected.native(incoming)

    def generation(self, incoming):
        return self.projected.generation(incoming)


def restore_sessions(original, config, plan, states, dual, manifest, primary_panels, old_panels, pixels, encoder, hub):
    evidence = []
    for identifier, state in states.items():
        game = original.build_game(manifest, dual, primary_panels, pixels, encoder, top_k=50,
            agent_id=state['game']['agent_id'], lane=state['game']['lane'],
            relevance_threshold=config['relevance_threshold'])
        game._judge = original.EpochJudge(dual, primary_panels, old_panels, game._judge.relevance, manifest)
        session = original.NativeEpoch(game, state['life_root'], Path(config['outputs'][identifier]),
            state['scene_ids'], resume_state=state, source_mode=state['source_mode'],
            session_binding=state['session_binding'])
        epoch = plan['epochs'][identifier]
        reattach_existing_epoch(session, Path(config['root']) / 'epochs' / identifier,
            epoch['files'], epoch['epoch_sha256'])
        hub.sessions[identifier], hub.registry[identifier] = session, state['session_binding']
        evidence.append(dict(session_id=identifier, epoch_sha256=session.epoch_ledger.epoch_sha256,
            **original.restore_contract(state, session.snapshot())))
    return evidence


def run(plan):
    config, states, queue, verdict = preflight(plan)
    require_retired(plan['old_identity'])
    store = OwnerStore(plan['candidate_runtime'], os.getuid())
    lock_root = Path(config['root']).parent / 'node3-caption-continuation-owner'
    lock_store = OwnerStore(lock_root, os.getuid())
    lock = os.open('SOLE_SCORER.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=lock_store.directory)
    metadata = os.fstat(lock)
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1 and metadata.st_uid == os.getuid()
        and stat.S_IMODE(metadata.st_mode) == 0o600, 'owner_single_scorer_lock')
    custody = None
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_retired(plan['old_identity'])
        owner_release = reference(plan['sole_writer_release'])
        require(owner_release['old_identity'] == plan['old_identity'] and owner_release['supervisor_hold'] is True
            and owner_release['drain_sha256'] == verdict['drain_sha256']
            and owner_release['candidate_source_sha256'] == plan['candidate_source_manifest']['sha256']
            and owner_release['exclusive_gpu'] == 4 and owner_release['old_writer_retired'] is True
            and owner_release['same_device_and_child_confinement_proved'] is True,
            'owner_coordinated_exclusive_writer_release_not_pid_alone')
        require_runtime(plan)
        original = importlib.import_module(ORIGINAL_MODULE)
        verify_source(plan)
        original.validate(config)
        source = original.verified_source(config['checkpoint_root'], config['checkpoint_complete_sha256'],
            config['checkpoint_adapter_sha256'], config['checkpoint_config_sha256'])
        dual = original.DualScalar(config['old_scalar']['path'], plan['primary_scalar']['path'])
        require(dual.weight_proofs == plan['weight_proofs'], 'same_loaded_weight_values')
        manifest = original.DevelopmentManifest.from_mapping(original.data.bound(config['game_manifest']))
        encoder = original.FrozenCPUEncoder(config['encoder_manifest'], threads=2)
        pixels = original.PixelConfig(**original.data.bound(config['pixel_config']))
        records = original.data.bound(config['reference_panels'])
        old_panels = {record['selected'][0]['scene']: record['scores'] for record in records}
        require(len(records) == len(manifest.contests) == 3 and all(len(record['selected']) == len(record['scores']) == 64
            and all(item['scene'] == record['selected'][0]['scene'] for item in record['selected'])
            for record in records), 'same_original_three_64_reference_panels')
        if config.get('old_panel_scores'):
            require(old_panels == original.data.bound(config['old_panel_scores']), 'same_reference_panel_scores')
        primary_panels = reference(plan['primary_panels'])
        require(set(primary_panels) == set(old_panels), 'same_primary_panel_scenes')
        require_retired(plan['old_identity'])
        verify_state(plan, config)
        sockets = Path(plan['candidate_runtime']) / 'sockets'
        sockets.mkdir(mode=0o700, exist_ok=False)
        hub = original.Hub(sockets, dict(complete=True, rows=[]), None, None, None)
        evidence = restore_sessions(original, config, plan, states, dual, manifest, primary_panels,
            old_panels, pixels, encoder, hub)
        bindings = {identifier: reference(value) for identifier, value in plan['bindings'].items()}
        custody = OwnerStore(plan['owner_custody'], os.getuid())
        projected = ProjectedHub(hub, custody, bindings)
        store.put('LOADED.json', canonical(dict(unix=time.time(), pid=os.getpid(), source=source,
            sessions=evidence, physical=4, transport_epoch=plan['transport_epoch'],
            original_deadline_unix=config['deadline_unix'], original_primary_panels=plan['primary_panels'],
            queue_sha256=plan['queue_dispositions']['sha256'], historical_replay=False,
            original_loaded=plan['original_loaded'], weight_proofs=dual.weight_proofs)))
        require_retired(plan['old_identity'])
        original.serve(QuarantinedHub(projected, queue), config['deadline_unix'])
    finally:
        if custody is not None:
            custody.close()
        os.close(lock)
        lock_store.close()
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner-plan', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--serve-after-owner-retirement', action='store_true')
    args = parser.parse_args()
    plan = load_binding(args.owner_plan, os.getuid(), args.sha256)
    if args.serve_after_owner_retirement:
        run(plan)
    else:
        config, states, queue, verdict = preflight(plan)
        print(json.dumps(dict(status='OFFLINE_PREFLIGHT_ONLY_NO_MODEL_LOADED', sessions=list(states),
            queue_origins=len(queue['dispositions']), verdict=verdict), sort_keys=True))


if __name__ == '__main__':
    main()
