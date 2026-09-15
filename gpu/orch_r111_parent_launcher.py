"""R111 reserved-device release and approval-bound parenting launch surface."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from datetime import datetime, timezone

from gpu import orch_r111_parent_provider as provider


NODE5_HOST_SHA='0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
RELEASE_UUIDS={0:'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',1:'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'}


def require(condition,message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_once(path,value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def process_identity(directory):
    return dict(pid=int(directory.name),uid=directory.stat().st_uid,
        start_ticks=(directory/'stat').read_text().rsplit(')',1)[1].split()[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        command_sha256=sha(directory/'cmdline'))


def completed_native_boundary(root,campaign):
    reservations=[json.loads(line) for line in (root/'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]
    intents=[row for row in reservations if row['kind']=='NATIVE']
    calls=sorted((campaign/'native').glob('CALL_*.json'))
    if len(calls)!=len(intents):
        return False
    return all(read(path).get('status') in ('COMPLETE','FAILED') for path in calls)


def release(index,source_sha,wait_seconds=600,receipt_prefix='R111_V2'):
    require(receipt_prefix=='R111_V2','versioned_release_receipt_only')
    require(index in RELEASE_UUIDS,'only_owned_node5_0_1')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest()==NODE5_HOST_SHA,'hashed_node5_binding')
    root=Path('/localhome/local-rohing/orch_r109_route_node5_20260915_node5_'+str(index)+'_attempt1')
    lane='node5_'+str(index)
    campaign=root/('campaign_'+lane)
    require(root.resolve()==root,'canonical_owned_root')
    launch=read(campaign/'LAUNCH.json')
    require(launch['uuid']==RELEASE_UUIDS[index],'exact_owned_uuid')
    directory=Path('/proc')/str(launch['pid'])
    identity=launch['identity']
    require(identity['uid']==os.getuid() and process_identity(directory)==identity,'exact_owned_process_identity')
    arguments=[part.decode() for part in (directory/'cmdline').read_bytes().split(b'\0') if part]
    require(arguments[-7:]==['-m','gpu.orch_r109_route_node5_run','native','--root',str(root),'--lane',lane],
            'owned_native_command')
    environment=(directory/'environ').read_bytes().split(b'\0')
    require(b'CUDA_VISIBLE_DEVICES='+RELEASE_UUIDS[index].encode() in environment,'owned_uuid_cvd')
    write_once(campaign/(receipt_prefix+'_RELEASE_REQUEST.json'),dict(requested_unix=time.time(),physical=index,identity=identity,
        root=str(root),uuid=RELEASE_UUIDS[index],source_sha256=source_sha,reason='R111_USER_RESERVED_FABLE_HALF',no_restart=True))
    descriptor=os.pidfd_open(launch['pid'])
    stopped=False
    try:
        deadline=time.time()+wait_seconds
        while time.time()<deadline:
            require(process_identity(directory)==identity,'process_identity_stayed_pinned')
            signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
            stopped=True
            for attempt in range(100):
                if (directory/'stat').read_text().rsplit(')',1)[1].split()[0] in ('T','t'):
                    break
                time.sleep(.01)
            require(process_identity(directory)==identity,'stopped_owned_identity')
            try:
                boundary=completed_native_boundary(root,campaign)
            except (json.JSONDecodeError,FileNotFoundError):
                boundary=False
            if boundary:
                break
            signal.pidfd_send_signal(descriptor,signal.SIGCONT)
            stopped=False
            time.sleep(.25)
        require(stopped and boundary,'waiting_for_native_complete_boundary_no_forced_kill')
        files={}
        for path in campaign.rglob('*'):
            if path.is_file() and path.name!='native.log':
                files[str(path.relative_to(root))]=sha(path)
        files['RESERVATIONS.jsonl']=sha(root/'RESERVATIONS.jsonl')
        checkpoints=[dict(path=str(path),sha256=sha(path)) for path in sorted(campaign.glob('CHECKPOINT_C*.json'))]
        reservations=[json.loads(line) for line in (root/'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]
        snapshot=dict(created_unix=time.time(),identity=identity,physical=index,uuid=RELEASE_UUIDS[index],
            status=read(campaign/'STATUS.json'),charged_native=sum(row['kind']=='NATIVE' for row in reservations),
            charged_parent=sum(row['kind']=='PARENT' for row in reservations),files=files,
            existing_checkpoints=checkpoints,all_raw_preserved_in_place=True,no_replay_or_restart=True,
            boundary='NO_NATIVE_CALL_PENDING; current episode may be partial',source_sha256=source_sha)
        write_once(campaign/(receipt_prefix+'_STOP_CHECKPOINT.json'),snapshot)
        require(process_identity(directory)==identity,'pre_signal_identity')
        signal.pidfd_send_signal(descriptor,signal.SIGTERM)
        signal.pidfd_send_signal(descriptor,signal.SIGCONT)
        stopped=False
        deadline=time.time()+60
        while directory.exists() and time.time()<deadline:
            if (directory/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z':
                break
            time.sleep(.25)
        require(not directory.exists() or (directory/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z',
                'graceful_exit_pending_no_kill_escalation')
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor,signal.SIGCONT)
        os.close(descriptor)
    result=subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(root/'source'),'python3','-B','-m','gpu.orch_r109_route_node5_scan','scan',
        '--lane',lane,'--service',str(root/'SERVICE_IDENTITY.json')],capture_output=True,text=True,check=True,timeout=90)
    report=json.loads(result.stdout)
    write_once(campaign/(receipt_prefix+'_RELEASE_SCAN.json'),report)
    receipt=dict(released_unix=time.time(),physical=index,uuid=RELEASE_UUIDS[index],previous_pid=launch['pid'],
        root=str(root),soft_sigterm_after_saved_boundary=True,no_pending_native_at_signal=True,no_restart=True,
        charged_native=snapshot['charged_native'],charged_parent=snapshot['charged_parent'],
        checkpoint_path=str(campaign/(receipt_prefix+'_STOP_CHECKPOINT.json')),checkpoint_sha256=sha(campaign/(receipt_prefix+'_STOP_CHECKPOINT.json')),
        scan_path=str(campaign/(receipt_prefix+'_RELEASE_SCAN.json')),scan_sha256=sha(campaign/(receipt_prefix+'_RELEASE_SCAN.json')),
        strict_clear=report['clear'],blocking_reasons=report['blocking_reasons'],
        owned_process_exited=True,raw_preserved=True,provider_may_finish_archiving_pending_response=True)
    write_once(campaign/(receipt_prefix+'_RELEASE_RECEIPT.json'),receipt)
    print(json.dumps(receipt,sort_keys=True))


GAMES = ('route', 'math', 'code', 'compilergym')
CADENCES = ('paragraph', '100_generated_tokens', 'episode')
HARD_END = '2026-09-15T17:02:00+00:00'
LEASE_END = '2026-09-17T04:04:00+00:00'
REFLECTION_SHA = '1fe38d9fea6bed06f07c3a5eb0ccbb029635d7af148b38367d8cd51dddfc2ceb'


def backend_status(game):
    require(game in GAMES, 'known_game')
    return dict(game=game, gpu_launch_supported=False,
                blockers=['No R111-bound native fresh-rank8 BASE backend is registered.',
                          'Existing contextual BASE loops have no optimizer and cannot implement sleep.',
                          'Existing whole-response cadence cannot be relabelled paragraph/token cadence.',
                          'Fresh-process game/facts/audit readout and every-fourth-sleep ON/OFF panel need integration.',
                          'Continuous two-episode/presleep/reflection/16-presentation/rehearsal lifecycle needs integration.'])


def prepare(*, output, node_root, life_id, physical, game, cadence, style, reflection,
            provider_command_file, parent_prompt, principles, battleplan, cohort,
            parent_cap, native_cap, max_cycles, hard_end=HARD_END, timeout_seconds=180,
            max_stdout_bytes=65536, max_stderr_bytes=65536, max_transcript_bytes=2097152):
    require(physical in (0, 1, 2, 3), 'fable_reserved_half_only')
    require(game in GAMES and cadence in CADENCES, 'known_game_and_honest_cadence')
    require(reflection in ('short', 'long') and bool(style.strip()), 'style_reflection_required')
    require(bool(life_id.strip()), 'life_id_required')
    root = Path(node_root)
    require(root.is_absolute() and str(root).startswith('/localhome/local-rohing/orch_r111_')
            and root == root.resolve(), 'unique_node_local_r111_root_required')
    deadline = datetime.fromisoformat(hard_end.replace('Z', '+00:00'))
    require(deadline.tzinfo is not None, 'timezone_required')
    deadline_unix = deadline.timestamp()
    require(time.time() < deadline_unix <= datetime.fromisoformat(HARD_END).timestamp(), 'original_hard_end')
    require(deadline_unix <= datetime.fromisoformat(LEASE_END).timestamp() - 21600, 'lease_six_hour_margin')
    require(all(type(value) is int and value > 0 for value in
                (parent_cap, native_cap, max_cycles, timeout_seconds, max_stdout_bytes,
                 max_stderr_bytes, max_transcript_bytes)), 'explicit_positive_bounds')
    repository = Path(__file__).resolve().parents[1]
    paths = dict(command=provider_command_file, prompt=parent_prompt, principles=principles,
                 battleplan=battleplan, cohort=cohort, provider_source=Path(provider.__file__),
                 launcher_source=Path(__file__),
                 reflection_helper=repository/'gpu/orch_reflection_repetition_stop.py')
    assets = {name: dict(path=str(Path(path).resolve()), sha256=sha(path)) for name, path in paths.items()}
    require(assets['reflection_helper']['sha256'] == REFLECTION_SHA, 'pinned_reflection_helper')
    require(Path(provider_command_file).read_text().strip() and Path(parent_prompt).read_text().strip(),
            'user_supplied_command_and_prompt_required')
    cohort_data = read(cohort)
    require(set(cohort_data) == {'train_task_ids', 'excluded_task_ids', 'task_sha256'}, 'cohort_schema')
    train_ids = cohort_data['train_task_ids']
    require(bool(train_ids) and len(set(train_ids)) == len(train_ids), 'unique_train_cohort')
    require(not set(train_ids).intersection(cohort_data['excluded_task_ids']), 'held_exclusion_disjoint')
    require(set(cohort_data['task_sha256']) == set(train_ids), 'every_training_task_hash_bound')
    require(all(isinstance(value, str) and len(value) == 64
                and all(character in '0123456789abcdef' for character in value)
                for value in cohort_data['task_sha256'].values()), 'task_hash_format')
    contract = dict(sequential_episodes_per_sleep=2,
                    presleep='long_pure_metacognitive_parent_child_conversation_every_sleep',
                    reflection='multi_angle_same_experience_with_pinned_repetition_stop',
                    child_tokens_only=True, parent_and_prompt_labels_masked=True,
                    presentations_per_row=16, earlier_life_rehearsal=True, optimizer_count=1,
                    checkpoint_every_sleep=True, outcome_or_quality_selection=False,
                    fresh_readout=dict(process='fresh', parent=False, inherited_context=False,
                                       timeout_seconds=180, held_game_tasks=8, old_facts=16,
                                       audit_tasks=2, lora_on_off_panel_every_sleeps=4),
                    triples='every_child_state_parent_intervention_observed_continuation; semantics UNKNOWN pending audit',
                    continuous_same_owned_life=True, repeated_admission_between_cycles=False,
                    actual_ownership_transfer_requires_admission=True, resume_preserves_charges=True,
                    no_l2_to_l1_feed=True)
    manifest = dict(schema='r111_parent_preparation_v1', life_id=life_id, node_root=str(root),
                    wrapper='gpu/ovx3_ssh.sh', host_sha256=NODE5_HOST_SHA, physical=physical,
                    uuid='UNBOUND_REQUIRES_FRESH_PRIVILEGED_SCAN',
                    game=game, cadence=cadence, style=style, reflection=reflection,
                    cadence_unit={'paragraph': 'completed generated paragraph with continuation interruption',
                                  '100_generated_tokens': 'actual generated token IDs across continuation; not responses',
                                  'episode': 'completed TRAIN episode plus mandatory presleep'}[cadence],
                    child=dict(base='Qwen2.5-7B-Instruct', base_frozen=True, lora_rank=8,
                               initial_adapter='fresh_no_l1_seed'), assets=assets, contract=contract,
                    bounds=dict(parent_calls=parent_cap, native_calls=native_cap, cycles=max_cycles,
                                hard_end_unix=deadline_unix, gpu_hours_max=(deadline_unix-time.time())/3600,
                                lease_end_unix=datetime.fromisoformat(LEASE_END).timestamp(), lease_margin_seconds=21600,
                                timeout_seconds=timeout_seconds, max_stdout_bytes=max_stdout_bytes,
                                max_stderr_bytes=max_stderr_bytes, max_transcript_bytes=max_transcript_bytes),
                    reply_format='text_no_implicit_json_plan', backend=backend_status(game),
                    preparation_only=True, approval_required=True, approved=False)
    provider.verify_manifest(manifest)
    write_once(output, manifest)
    return dict(manifest_path=str(output), manifest_sha256=provider.digest(manifest),
                preparation_only=True, provider_invocations=0, gpu_launched=False,
                backend=manifest['backend'])


def launch(manifest, approval):
    configuration = read(manifest)
    if configuration.get('schema') in ('R111V2_F1_MATCHED_GUIDED_ROUTE', 'R113V3_F1_MATCHED_GUIDED_ROUTE'):
        from gpu import orch_r111_route_pair
        return orch_r111_route_pair.launch(Path(configuration['root']))
    provider.verify_manifest(configuration)
    provider.verify_approval(configuration, read(approval))
    raise RuntimeError('R111_GPU_BACKEND_UNSUPPORTED: preparation only; no engine/game is launch-ready. '
                       'Approval does not substitute for native learning/readout integration and fresh admission.')


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='command',required=True)
    retiring=sub.add_parser('release')
    retiring.add_argument('--index',type=int,choices=(0,1),required=True)
    retiring.add_argument('--source-sha',required=True)
    retiring.add_argument('--wait-seconds',type=int,default=600)
    preparing = sub.add_parser('prepare', help='CPU preparation only; never invokes GPU or provider')
    for name in ('output', 'provider-command-file', 'parent-prompt', 'principles', 'battleplan', 'cohort'):
        preparing.add_argument('--'+name, type=Path, required=True)
    preparing.add_argument('--node-root', required=True)
    preparing.add_argument('--life-id', required=True)
    preparing.add_argument('--physical', type=int, choices=(0, 1, 2, 3), required=True)
    preparing.add_argument('--game', choices=GAMES, required=True)
    preparing.add_argument('--cadence', choices=CADENCES, required=True)
    preparing.add_argument('--style', required=True)
    preparing.add_argument('--reflection', choices=('short', 'long'), required=True)
    for name in ('parent-cap', 'native-cap', 'max-cycles'):
        preparing.add_argument('--'+name, type=int, required=True)
    preparing.add_argument('--hard-end', default=HARD_END)
    preparing.add_argument('--timeout-seconds', type=int, default=180)
    preparing.add_argument('--max-stdout-bytes', type=int, default=65536)
    preparing.add_argument('--max-stderr-bytes', type=int, default=65536)
    preparing.add_argument('--max-transcript-bytes', type=int, default=2097152)
    launching = sub.add_parser('launch', help='Fail-closed stub until R111 native backend integration')
    launching.add_argument('--manifest', type=Path, required=True)
    launching.add_argument('--approval', type=Path, required=True)
    route = sub.add_parser('prepare-route', help='Prepare the functioning R111v2 GUIDED route pair')
    for name in ('root', 'assets', 'parent-prompt', 'principles', 'battleplan'):
        route.add_argument('--'+name, type=Path, required=True)
    route.add_argument('--physical', type=int, choices=(0, 4), required=True)
    for name in ('native-calls', 'parent-calls', 'cycles'):
        route.add_argument('--'+name, type=int, required=True)
    route.add_argument('--hard-end-unix', type=float, required=True)
    route.add_argument('--judge-sha256', required=True)
    args=vars(parser.parse_args())
    command = args.pop('command')
    if command == 'prepare-route':
        from gpu import orch_r111_route_pair
        result = orch_r111_route_pair.prepare(**args)
    else:
        result = dict(release=release, prepare=prepare, launch=launch)[command](**args)
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__=='__main__':
    main()
