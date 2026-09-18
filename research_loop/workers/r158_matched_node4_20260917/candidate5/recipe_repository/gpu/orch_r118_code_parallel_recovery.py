"""CPU-only failed-startup custody export; no actor launch or evidence rewrite."""

import argparse
from copy import deepcopy
from pathlib import Path
import time

from gpu import orch_r118_code_parallel_final as final
from gpu import orch_r118_code_parallel_handoff as handoff


io, require = handoff.io, handoff.require
SESSION_SHA256 = 'e834ff7869f9309d70cf46f682adcc522f3120c8ac293ed7065708a6f50da94b'
CHECKPOINT_SHA256 = '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'
PREP_END = 1789488600
COLLECTION_END = 1789491300


def snapshot(service, session_path, *, clock=time.time):
    service, session_path = Path(service), Path(session_path)
    require(clock() < PREP_END, 'bounded_CPU_recovery_preparation')
    require(io.sha(session_path) == SESSION_SHA256, 'exact_failed_session')
    session = io.read(session_path)
    runtime = io.read(service / 'RUNTIME.json')
    root = Path(runtime['root']).resolve(strict=True)
    branch = io.read(root / 'SHARED_ACTIVATION.json')['shared_learner']['branch']
    require(branch in ('F3', 'A3') and service.resolve().is_relative_to(root), 'own_CODE_service')
    owner = session['owners'][branch]
    require(owner['bootstrap_path'] == str(service / 'FRESH_BOOTSTRAP.json'), 'exact_failed_owner')
    control = session_path.parent / (session_path.stem + '.dispatch')
    failed = io.read(control / 'FAILED.json')
    require(failed['session_sha256'] == SESSION_SHA256 and failed['retry_allowed'] is False,
        'preserve_failed_session_no_retry')
    require(not (control / (branch + '.BOOTSTRAP_START.json')).exists()
        and not (service / 'FRESH_BOOTSTRAP.json').exists()
        and not (service / 'BOOTSTRAP.json').exists() and not (service / 'ACTOR_READY.json').exists(),
        'only_prebootstrap_failure_no_recollection')
    launched = io.read(service / 'LAUNCH.json')
    terminal = io.read(service / 'GUARD_TERMINAL.json')
    require(terminal['identity'] == launched['identity'] and terminal['native_alive'] is False
        and terminal['returncode'] != 0, 'actual_failed_guard_terminal')
    require(not handoff.alive(launched['identity']) and not handoff.alive(launched['guardian']),
        'failed_native_guard_must_exit')
    require((service / 'GUARD_ONCE').is_dir() and (service / 'NATIVE_ONCE').is_dir(),
        'preserve_old_execution_once_markers')
    released = handoff.checked(runtime['handoff'])
    boundary = released['native']['boundary']
    require(boundary['kind'] == 'SETTLED_PENDING_CONSOLIDATION', 'pending_only_recovery')
    common = Path(runtime['common_root'])
    require(io.read(common / 'STATE.json') == boundary['state']
        and boundary['state']['generation'] == 1
        and boundary['state']['checkpoint']['path_sha256'] == CHECKPOINT_SHA256,
        'same_committed_gen1_child')
    checkpoint = io.checked_checkpoint(boundary['state']['checkpoint'])
    for name, expected in session['pins'].items():
        require(io.sha(common / name) == expected, 'no_common_state_or_optimizer_transition')
    require(not (common / 'generation_000001/sleep/START.json').exists(), 'no_sleep_started')
    envelope_path = Path(owner['handoff']['path'])
    envelope = handoff.checked(owner['handoff'])
    for relative, expected in envelope['preserved_files'].items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'root_relative_preserved_evidence')
        require(io.sha(root / relative) == expected, 'all_original_evidence_preserved')
    charged, unused = handoff.ledger(root)
    expected_reservations = {name: expected for name, expected in envelope['preserved_files'].items()
        if name.startswith('reservations/')}
    require(charged['preserved'] == expected_reservations
        and all(charged[name] == envelope['bounds'][name] for name in ('native_used', 'parent_used')),
        'no_new_calls_or_reservation_changes')
    for name, expected in handoff.checked(runtime['source_manifest']).items():
        require(io.sha(Path(runtime['source_root']) / name) == expected, 'actual_actor_source_unchanged')
    cpu = handoff.checked(runtime['cpu_tests'])
    require(cpu['passed'] is True and cpu['cuda_initialized'] is False
        and cpu['source_manifest_sha256'] == runtime['source_manifest']['sha256'], 'bound_actor_CPU_tests')
    final_root = Path(io.read(service / 'FINAL_STAGER_COMPLETE.json')['final_root'])
    final.unused_allocation(final_root)
    timer = io.read(final_root / 'CPU_DISPATCH.json')['identity']
    require(timer['pid'] != 1519259 and handoff.alive(timer), 'own_unused_FINAL_timer_alive')
    return dict(schema='R118_CODE_FAILED_STARTUP_PROOF_V1', branch=branch, root=str(root),
        service=str(service), session=handoff.ref(session_path), failure=handoff.ref(control / 'FAILED.json'),
        runtime=handoff.ref(service / 'RUNTIME.json'), original_release=handoff.ref(envelope_path),
        identities=launched, terminal=handoff.ref(service / 'GUARD_TERMINAL.json'),
        final_root=str(final_root), final_timer=timer, final_plan=handoff.ref(final_root / 'PLAN.json'),
        charges={name: charged[name] for name in ('native_used', 'parent_used')},
        preserved_file_count=len(envelope['preserved_files']), new_calls=0, optimizer_steps=0,
        bootstrap_started=False, loaded_model_disposition='PROCESS_EXITED_NO_READY_MODEL',
        checkpoint=checkpoint,
        historical_optimizer_steps=boundary['state'].get('optimizer_steps'),
        historical_shared_optimizer_steps=boundary['state'].get('shared_optimizer_steps'),
        observed_unix=clock(), collection_end_unix=COLLECTION_END, hard_end_unix=runtime['hard_end_unix'])


def prepare(service, session_path, output, successor, *, clock=time.time):
    service, output, successor = Path(service), Path(output), Path(successor)
    proof = snapshot(service, session_path, clock=clock)
    root = Path(proof['root'])
    require(output.is_absolute() and successor.is_absolute() and output != successor
        and output.is_relative_to(root) and successor.is_relative_to(root)
        and not output.exists() and not successor.exists(), 'new_owned_recovery_era_only')
    runtime = io.read(service / 'RUNTIME.json')
    old_envelope = handoff.checked(proof['original_release'])
    old_release = handoff.checked(old_envelope['release'])
    owner = deepcopy(io.read(service / 'OWNER_REQUEST.json'))
    output.mkdir(parents=True)
    io.write(output / 'PROOF.json', proof)
    released = deepcopy(old_release)
    released.update(failed_startup_recovery=handoff.ref(output / 'PROOF.json'),
        original_settled_release=old_envelope['release'], successor_started=False)
    io.write(output / 'HANDOFF.json', released)
    envelope = deepcopy(old_envelope)
    envelope['release'] = handoff.ref(output / 'HANDOFF.json')
    for name in ('identity', 'guardian'):
        identity = deepcopy(proof['identities'][name])
        identity['start_ticks'] = int(identity['start_ticks'])
        envelope['predecessors'].append(identity)
    for parent in (service, output):
        for path in sorted(parent.glob('*.json')):
            envelope['preserved_files'][str(path.relative_to(root))] = io.sha(path)
    envelope['failed_startup'] = handoff.ref(output / 'PROOF.json')
    io.write(output / 'OWNER_RELEASE.json', envelope)
    owner['handoff'] = handoff.ref(output / 'OWNER_RELEASE.json')
    require(owner['command'][-2:] == ['--service', str(service)], 'exact_guard_command_shape')
    owner['command'][-1] = str(successor)
    owner['bootstrap_path'] = str(successor / 'FRESH_BOOTSTRAP.json')
    io.write(output / 'SOURCE_FILES_ABSOLUTE.json', owner['source_files'])
    prepared = dict(schema='R118_CODE_FAILED_STARTUP_OWNER_PREPARED_V1',
        status='CPU_PREPARED_REQUIRES_NEW_MAIN_CAMPAIGN_NOT_DISPATCHABLE', branch=proof['branch'],
        root=str(root), service=str(successor), owner=owner, proof=handoff.ref(output / 'PROOF.json'),
        source_files=handoff.ref(output / 'SOURCE_FILES_ABSOLUTE.json'),
        source_root=runtime['source_root'], source_manifest=runtime['source_manifest'],
        cpu_tests=runtime['cpu_tests'], final_old_root=proof['final_root'],
        final_new_root=str(successor.parent / 'final_3'), old_final_identity=proof['final_timer'],
        pending=owner['boundary']['settled_pending_consolidation'], next_cycle=envelope['next_cycle'],
        first_action='RESUME_EXISTING_PENDING_BEFORE_NEW_CALLS', GPU_started=False,
        actor_source_changed=False, collection_end_unix=COLLECTION_END,
        inherited_settlement_end_unix=envelope['bounds']['train_end_unix'],
        hard_end_unix=envelope['bounds']['hard_end_unix'], observed_unix=clock())
    io.write(output / 'OWNER_PREPARED.json', prepared)
    return prepared


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('service', 'session', 'output', 'successor'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(io.digest(prepare(args.service, args.session, args.output, args.successor)))
