"""Resident route integration for Herschel's pinned collective consolidation hook."""

from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time

from gpu import orch_r111_route_shared as serial
from gpu import orch_r118_parallel_consolidation as backend
from gpu import orch_r118_route_parallel_boundary as boundary


coordinator = serial.coordinator
require = coordinator.require
read, sha, write = coordinator.read, coordinator.sha, coordinator.write
checkpoint_reference = serial.checkpoint_reference
restore_optimizer = serial.restore_optimizer
TRAIN_END = boundary.TRAIN_END
HARD_END = 1789491720


def activation_location(control, generation):
    directory = Path(control['activation_directory'])
    require(directory.is_absolute(), 'absolute_Main_activation_directory')
    return directory / f'generation_{generation:06d}.ref.json'


def original_bounds(root, plan):
    counts = Counter(row['kind'] for row in boundary.prior.ledger(root))
    bounds = plan['bounds']
    return dict(train_end_unix=min(TRAIN_END, bounds['hard_end_unix'], bounds['lease_end_unix'] - 21600),
                hard_end_unix=min(HARD_END, bounds['hard_end_unix'], bounds['lease_end_unix'] - 21600),
                native_used=counts['NATIVE'], native_cap=bounds['native_calls'],
                parent_used=counts['PARENT'], parent_cap=bounds['parent_calls'])


def validate_campaign(control, common, source_files):
    reference = control['campaign']
    document, unused = backend.campaign_document(reference['path'], reference['sha256'])
    require(document['root'] == str(common)
            and document['activation_directory'] == control['activation_directory']
            and document['deadline_unix'] <= min(TRAIN_END, control['activation_wait_end_unix']),
            'exact_Main_campaign_original_bounds')
    require(all(document['source_files'].get(name) == digest for name, digest in source_files.items()),
            'campaign_pins_actual_route_source')
    return reference


class Session(serial.Session):
    def __init__(self, root, plan):
        super().__init__(root, plan)
        self.plan = deepcopy(plan)
        self.control = plan['parallel_control']
        require(self.control['backend_source'] == boundary.ref(Path(backend.__file__).resolve()),
                'exact_Herschel_backend_contract')
        require(self.control['train_end_unix'] == TRAIN_END, 'common_TRAIN_cutoff_unchanged')
        require(self.state['generation'] >= 1, 'no_parallel_before_serial_commit')
        require(plan['parent_wait_seconds'] == 120, 'no_parent_transport_change')
        if self.control.get('requires_campaign') or 'campaign' in self.control:
            validate_campaign(self.control, self.shared_root, plan['source_files'])
        self.initial_generation = self.state['generation']

    def capture_metadata(self):
        return dict(super().capture_metadata(), shared_backend_era='R118_PARALLEL_CANDIDATE_V1')

    def bootstrap(self, engine, optimizer):
        require((optimizer is not None) == self.owner, 'only_F1_has_optimizer')
        self.startup_session = dict(path=os.environ['R118_PARALLEL_SESSION'],
                                   sha256=os.environ['R118_PARALLEL_SESSION_SHA256'])
        require(os.environ['R118_PARALLEL_BRANCH'] == self.branch, 'dispatcher_exact_branch')
        document, unused = backend.fresh_session(self.startup_session['path'], self.startup_session['sha256'])
        owner = document['owners'][self.branch]
        envelope = boundary.bound(owner['handoff'])
        require(document['state'] == self.state and envelope['release'] == self.plan['route_boundary_release']
                and envelope['root'] == str(self.root), 'actual_released_branch_and_canonical_state')
        require(owner['source_files'] == self.plan['source_files'] and owner['cwd'] == self.plan['parallel_source'],
                'exact_dispatched_route_source')
        receipt = backend.bootstrap_fresh_actor(root=self.shared_root, branch=self.branch, engine=engine,
            optimizer=optimizer, session_path=self.startup_session['path'],
            session_sha256=self.startup_session['sha256'])
        require(receipt['status'] == 'BOOTSTRAP_VERIFIED' and receipt['identity'] == backend.process_identity()
                and receipt['optimizer_count'] == int(self.owner)
                and receipt['checkpoint_sha256'] == self.loaded_reference['path_sha256'], 'actual_native_fresh_bootstrap')
        return dict(receipt, checkpoint=self.loaded_reference, fresh_EXEC=True, predecessor_object_reused=False,
                    live_optimizer_id=id(optimizer) if self.owner else None, automatic_recovery=False)

    def await_collection(self, check):
        return backend.wait_fresh_collection_go(self.startup_session['path'], self.startup_session['sha256'],
                                                 self.branch, check=check)

    def certificate(self, output, submission):
        state = read(self.shared_root / 'STATE.json')
        require(state == self.state, 'same_collection_state_no_retrospective_tagging')
        submission_path = self.shared_root / f"generation_{state['generation']:06d}" / f'{self.branch}.json'
        require(submission['path'] == str(submission_path) and submission['sha256'] == sha(submission_path),
                'actual_submission_file')
        paths = [self.root / 'PLAN.json', self.root / 'R118_PARALLEL_PLAN.json',
                 self.root / 'RESERVATIONS.jsonl', self.root / 'OWN_CARRY.json',
                 Path(output) / 'ROWS.json', Path(output) / 'SHARED_SUBMISSION.json']
        if (self.root / 'PENDING_TRIPLE.json').exists():
            paths.append(self.root / 'PENDING_TRIPLE.json')
        supervision = read(self.root / 'R118_PARALLEL_SUPERVISION_BINDING.json')
        require(supervision['native_identity'] == backend.process_identity(), 'current_native_supervision')
        result = dict(branch=self.branch, root=str(self.root), generation=state['generation'],
                      checkpoint_sha256=state['checkpoint']['path_sha256'], identity=backend.process_identity(),
                      status='SAFE_FOR_PARALLEL', bounds=original_bounds(self.root, self.plan),
                      submission_sha256=sha(submission_path),
                      preserved_files={str(path.relative_to(self.root)): sha(path) for path in paths},
                      parent_wait_seconds=120, all_native_rows_already_captured=True,
                      launch_device=dict(kind='cuda', physical=self.plan['physical'], uuid=self.plan['uuid'],
                                         cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES', '')),
                      retained_supervision=supervision, ready_unix=time.time())
        backend.validate_launch_participant(result, self.branch, 'CUDA_INPLACE')
        path = Path(output) / 'PARALLEL_PARTICIPANT.json'
        write(path, result)
        return boundary.ref(path)

    def wait_activation(self, certificate, check, *, clock=time.time, pause=time.sleep):
        if self.control.get('requires_campaign') or 'campaign' in self.control:
            reference = validate_campaign(self.control, self.shared_root, self.plan['source_files'])
            return backend.await_campaign_activation(reference['path'], reference['sha256'],
                                                     self.branch, certificate, check=check)
        location = activation_location(self.control, self.state['generation'])
        deadline = min(original_bounds(self.root, self.plan)['train_end_unix'],
                       self.control['activation_wait_end_unix'])
        while clock() < deadline:
            check('parallel_wait_Main_generation_activation')
            if location.exists():
                reference = read(location)
                document = boundary.bound(reference)
                require(document['root'] == str(self.shared_root) and document['generation'] == self.state['generation']
                        and document['participants'][self.branch] == certificate, 'Main_bound_actual_live_certificate')
                require(document.get('launch', {}).get('schema') == backend.LAUNCH_SCHEMA,
                        'exact_Herschel_bounded_launch_contract')
                return reference
            pause(min(1, max(.001, deadline - clock())))
        raise TimeoutError('original_common_TRAIN_deadline_no_activation_no_quota_reset')

    def sleep(self, engine, optimizer, anchors, rows, episode_ids, output, save_callback, check,
              *, launch_call=backend.launch_at_boundary):
        require((optimizer is not None) == self.owner, 'F1_existing_optimizer_A1_none')
        require(len(episode_ids) == len(set(episode_ids)) == 2, 'two_distinct_episodes')
        binding = self.capture_binding()
        for row in rows:
            call = read(row['source_call_path'])
            require(call.get('shared_learner') == binding and call.get('shared_generation') == binding['generation']
                    and call.get('shared_checkpoint_sha256') == binding['checkpoint_sha256'],
                    'actual_captured_generation_checkpoint')
        check('parallel_submit')
        submission = coordinator.submit(self.shared_root, self.branch, self.state['generation'],
                                        self.loaded_reference['path_sha256'], episode_ids, rows)
        output = Path(output)
        write(output / 'SHARED_SUBMISSION.json', submission)
        certificate = self.certificate(output, submission)
        activation = self.wait_activation(certificate, check)
        try:
            check('bounded_Herschel_collective_launch')
            from gpu import orch_r107_base_anchors_inventory as anchor_module
            result = launch_call(activation_path=activation['path'],
                activation_sha256=activation['sha256'], branch=self.branch, engine=engine, optimizer=optimizer,
                anchor_module=anchor_module, anchors=anchors,
                anchor_root=self.control['anchor_root'], save_checkpoint=save_callback if self.owner else None,
                check=check)
            require(result['status'] == 'COMPLETE_ALL8_INPLACE', 'real_parallel_complete')
            following = result['state']
            require(following['generation'] == self.state['generation'] + 1, 'one_committed_generation_advance')
            complete = read(self.shared_root / f"generation_{self.state['generation']:06d}/sleep/COMPLETE.json")
            acknowledgment = self.shared_root / f"generation_{self.state['generation']:06d}/sleep/ALL8_RELOAD.json"
            require(complete['state'] == following == read(self.shared_root / 'STATE.json')
                    and read(acknowledgment)['state'] == following, 'committed_checkpoint_all8_reload_ACK')
            self.state = following
            self.loaded_reference = deepcopy(following['checkpoint'])
            receipt = dict(result, branch=self.branch, optimizer_owner='F1',
                local_optimizer_steps=result['metrics']['optimizer_steps'] if self.owner else 0,
                adopted_plus_shared_totals={name: following[name] for name in serial.METRICS},
                shared_only_totals={name: following['shared_' + name] for name in serial.METRICS},
                activation=activation, participant=certificate, all8_reload=boundary.ref(acknowledgment),
                completed_unix=time.time(), inherited_bounds_unchanged=True,
                serial_adamw_equivalent=False)
            receipt['status'] = 'COMPLETE'
            receipt['backend_status'] = result['status']
            write(output / 'SHARED_SLEEP.json', receipt)
            return receipt
        except BaseException as error:
            write(output / 'PARALLEL_FAILED.json', dict(type=type(error).__name__, error=str(error),
                  automatic_retry=False, counters_preserved=True, failed_unix=time.time()))
            raise
