"""Successor-only CODE capture and non-owner shared-child barrier client."""

from copy import deepcopy
from pathlib import Path
from types import FunctionType

from gpu import orch_guided_native as native
from gpu import orch_r108_code_parent_r115_engine as decoder
from gpu import orch_r108_code_parent_r115_run as run
from gpu import orch_r109_route_engine as causal
from gpu import orch_r111_route_shared as existing
from gpu import orch_r116_shared_learner as coordinator


require = coordinator.require
BOUND_FIELDS = ('started_unix', 'hard_deadline_unix', 'lease_end_unix',
    'native_cap', 'parent_cap', 'cycles')


def readonly_shared(model):
    require(set(getattr(model, 'peft_config', {})) == {'default'}, 'one_shared_adapter_required')
    require(not any(parameter.requires_grad for parameter in model.parameters()), 'no_local_training')


class Engine:
    generate_batch = FunctionType(decoder.Engine.generate_batch.__code__,
        dict(decoder.Engine.generate_batch.__globals__, assert_no_adapter=readonly_shared), 'generate_batch')
    generate = decoder.Engine.generate

    def __init__(self, loaded):
        require(loaded.optimizer is None, 'CODE_never_owns_optimizer')
        self.underlying = loaded.engine

    def __getattr__(self, name):
        return getattr(self.underlying, name)


def replay_row(call, path, source_sha256, *, spec, exclusions, generation, checkpoint_sha256):
    path = Path(path).resolve(strict=True)
    require(coordinator.sha(path) == source_sha256 and coordinator.read(path) == call,
        'actual_immutable_source_required')
    require(call.get('kind') == 'NATIVE' and call.get('status') == 'COMPLETE', 'completed_native_only')
    require(type(call.get('shared_generation')) is int, 'actual_integer_generation_required')
    row = causal.replay_row(call, path, source_sha256)
    coordinator.validate_row(row, spec, exclusions, generation=generation,
        checkpoint_sha256=checkpoint_sha256)
    return row


class Session(existing.Session):
    def __init__(self, root, plan, *, readout=False):
        self.root = Path(root).resolve(strict=True)
        binding = plan['shared_learner']
        self.branch = binding['branch']
        require(self.branch == {2: 'F3', 6: 'A3'}.get(plan['physical']), 'CODE_exact_branch_slot')
        self.owner = False
        self.shared_root = Path(binding['root']).resolve(strict=True)
        require(coordinator.sha(self.shared_root / 'CONFIG.json') == binding['config_sha256'],
            'bound_shared_config')
        self.config = coordinator.read(self.shared_root / 'CONFIG.json')
        require(self.config['owner'] == 'F1' and set(self.config['branches']) == set(coordinator.BRANCHES),
            'Main_initialized_eight_single_optimizer')
        self.spec = self.config['branches'][self.branch]
        require(Path(self.spec['root']).resolve() == self.root, 'exact_shared_branch_root')
        cohort = coordinator.read(self.root / 'COHORT.json')
        require(set(self.spec['train_ids']) == {task['task_id'] for task in cohort['TRAIN']},
            'exact_CODE_train_cohort')
        exclusions = {task['task_id'] for split in ('DEV', 'FINAL') for task in cohort[split]}
        require(exclusions.issubset(self.config['excluded_ids']), 'all_DEV_FINAL_excluded')
        require(self.config['anchor_sha256'] == coordinator.ANCHOR_SHA
            and self.config['new_presentations'] == 16 and self.config['rehearsal_presentations'] == 1
            and self.config['anchor_loss_weight'] == .25, 'exact_joint_sleep_recipe')
        adoption = Path(binding['adoption_path']).resolve(strict=True)
        require(coordinator.sha(adoption) == binding['adoption_sha256'], 'bound_adoption')
        self.adoption = coordinator.read(adoption)
        require(self.adoption['checkpoint'] == self.config['initial_checkpoint']
            and self.adoption['prior_metrics'] == self.config['pretransition_metrics']
            and self.config['initial_history'].get('F1'), 'preserve_F1_state_history_counters')
        require(self.adoption['branch_bounds'][self.branch] == {key: plan[key] for key in BOUND_FIELDS},
            'original_CODE_bounds_no_reset')
        self.state = coordinator.read(self.shared_root / 'STATE.json')
        require(self.state['config_sha256'] == binding['config_sha256'], 'state_config_binding')
        require(type(self.state['generation']) is int, 'actual_integer_generation')
        self.loaded_reference = deepcopy(coordinator.checked_checkpoint(self.state['checkpoint']))
        self.loaded = False
        if not readout:
            for path in self.root.glob('shared_cycles/*/SHARED_SUBMISSION.json'):
                require((path.parent / 'SHARED_SLEEP.json').exists(), 'unfinished_shared_cycle_needs_recovery')

    def load_engine(self, plan, check, *, readout=False):
        document = coordinator.read(self.loaded_reference['path'])
        identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
        binding = native.bridge.StageBinding(self.root.name, native.bridge.ARMS[0],
            self.state['generation'], 'sealed_readout' if readout else 'collection',
            identity, not readout, True, coordinator.digest(plan))

        def forward_check(phase):
            check(phase)

        loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0',
            gpu_uuid=plan['gpu_uuid'], context=native.StageContext(
                private_guidance=() if readout else ('R116_CODE_PRIVATE_TRAIN_CONTEXT',)),
            check=forward_check, predecessor_processes=(tuple(document['source_process']),))
        require(loaded.optimizer is None and loaded.observed == identity, 'exact_shared_child_no_optimizer')
        self.loaded = True
        return Engine(loaded)

    def finish_cycle(self, engine, episode_ids, source_paths, output, check, **options):
        require(self.loaded and len(set(episode_ids)) == 2, 'loaded_shared_child_two_episodes')
        rows = [replay_row(coordinator.read(path), path, coordinator.sha(path), spec=self.spec,
            exclusions=self.config['excluded_ids'], generation=self.state['generation'],
            checkpoint_sha256=self.loaded_reference['path_sha256']) for path in source_paths]
        return self.sleep(engine, None, (), rows, episode_ids, output, None, check, **options)


class Driver(run.Driver):
    def __init__(self, root, engine, session):
        super().__init__(root, engine)
        require(session.loaded and session.root == self.root.resolve(), 'loaded_bound_session')
        self.session = session
        self.cycle_sources = {}

    def status(self):
        rows = [run.read(path) for path in (self.root/'reservations').glob('*.json')]
        run.write(self.root/'SHARED_STATUS.json',dict(observed_unix=run.time.time(),
            counts=dict(run.Counter(row['kind']+'_'+row['status'] for row in rows)),
            generated_tokens=sum(len(row.get('response',{}).get('token_ids',[])) for row in rows),
            shared_generation=self.session.state['generation'],local_optimizer_steps=0,
            optimizer_owner='F1',shared_optimizer_steps=self.session.state['shared_optimizer_steps'],
            inherited_plus_shared_optimizer_steps=self.session.state['optimizer_steps'],
            semantic_behavior='UNASSESSED',comparison='SHARED_CHILD_PARENTING_SYSTEMS'))

    def capture(self, identifier, task, phase, cycle, messages, cap, *, evaluation_origin=None):
        if task['split'] != 'TRAIN' or evaluation_origin is not None:
            return super().capture(identifier, task, phase, cycle, messages, cap,
                evaluation_origin=evaluation_origin)
        require(phase in coordinator.PHASES and task['task_id'] in self.session.spec['train_ids'],
            'registered_TRAIN_phase_only')
        metadata = self.session.capture_metadata()
        require(type(metadata['shared_generation']) is int, 'integer_generation_before_dispatch')
        require(isinstance(metadata['shared_checkpoint_sha256'], str)
            and len(metadata['shared_checkpoint_sha256']) == 64, 'checkpoint_hash_before_dispatch')
        path, row = self.reserve(identifier, 'NATIVE', split='TRAIN', phase=phase, cycle=cycle)
        row.update(metadata, task_id=task['task_id'])
        row['routes'].update(sleep=True, optimizer=False, requires_shared_barrier=True)
        run.write(path, row)
        try:
            row['response'] = self.engine.generate(messages, max_new_tokens=cap)
            row.update(status='COMPLETE', requested_generation_cap=cap,
                applied_reflection_settings=self.settings if phase in ('reflection', 'presleep') else None)
            self.cycle_sources.setdefault(cycle, []).append(path)
            return row
        except Exception as error:
            row.update(status='FAILED', error_type=type(error).__name__)
            return row
        finally:
            row['finished_unix'] = run.time.time()
            run.write(path, row)
            self.status()

    def finish_cycle(self, cycle, episode_ids, check, **options):
        output = self.root / 'shared_cycles' / f'C{cycle:03d}'
        return self.session.finish_cycle(self.engine, episode_ids,
            self.cycle_sources.get(cycle, []), output, check, **options)
