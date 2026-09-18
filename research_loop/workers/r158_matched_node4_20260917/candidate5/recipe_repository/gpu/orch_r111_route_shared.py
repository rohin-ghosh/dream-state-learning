"""Successor-only route client for the eight-branch single-optimizer barrier."""

from copy import deepcopy
from pathlib import Path
import time

from gpu import orch_guided_native as native
from gpu import orch_r116_shared_learner as coordinator


require = coordinator.require
METRICS = ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures')


def checkpoint_reference(path):
    path = Path(path).resolve(strict=True)
    document = coordinator.read(path)
    require(document.get('complete') is True, 'complete_sleep_checkpoint_required')
    native.bridge.AdapterIdentity.from_document(document['adapter'])
    optimizer = path.parent / 'optimizer_rng.pt'
    require(coordinator.sha(optimizer) == document['optimizer_rng_sha256'], 'optimizer_rng_binding')
    return coordinator.checked_checkpoint(dict(path=str(path), path_sha256=coordinator.sha(path),
        optimizer_path=str(optimizer), optimizer_path_sha256=coordinator.sha(optimizer)))


def adoption_inputs(root):
    root = Path(root).resolve(strict=True)
    cycles = sorted(path.parent for path in root.glob('cycle_*/COMPLETE.json'))
    require(cycles, 'no_complete_F1_cycle_yet')
    reference = checkpoint_reference(cycles[-1] / 'checkpoint' / 'CHECKPOINT.json')
    fields = dict(optimizer_steps='updates', child_token_exposures='child_token_exposure_including_eos',
                  anchor_token_exposures='anchor_token_exposure_including_eos')
    totals = {name: 0 for name in METRICS}
    rows, receipts = [], []
    for cycle in cycles:
        sleep = coordinator.read(cycle / 'SLEEP.json')
        require(sleep['checkpoint_sha256'] == coordinator.sha(cycle / 'checkpoint' / 'CHECKPOINT.json'),
                'historical_sleep_checkpoint_binding')
        for name, field in fields.items():
            value = sleep.get(field)
            totals[name] = None if totals[name] is None or value is None else totals[name] + value
        encoding = coordinator.read(cycle / 'ENCODING.json')
        rejected = {item['source'] for item in encoding['rejected']}
        rows.extend(row for row in coordinator.read(cycle / 'ROWS.json')
                    if row['source_call_sha256'] not in rejected)
        receipts.append(dict(path=str(cycle / 'SLEEP.json'), sha256=coordinator.sha(cycle / 'SLEEP.json')))
    return dict(checkpoint=reference, prior_metrics=totals, initial_history={'F1': rows},
                source_receipts=receipts, no_lifetime_reset=True)


def restore_optimizer(engine, optimizer, reference, *, owner):
    require(owner == 'F1' and optimizer is not None, 'only_F1_restores_optimizer')
    coordinator.checked_checkpoint(reference)
    state = engine.torch.load(reference['optimizer_path'], map_location='cpu', weights_only=False)
    optimizer.load_state_dict(state['optimizer'])
    engine.torch.set_rng_state(state['cpu_rng'])
    engine.torch.cuda.set_rng_state_all(state['cuda_rng'])


def reload_adapter(engine, reference):
    from peft.utils.save_and_load import load_peft_weights, set_peft_model_state_dict

    coordinator.checked_checkpoint(reference)
    document = coordinator.read(reference['path'])
    identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
    require(set(engine.model.peft_config) == {'default'}, 'single_existing_default_adapter')
    parameters = {name: value for name, value in engine.model.named_parameters() if native.is_lora(name)}
    before = {name: id(value) for name, value in parameters.items()}
    engine.verify_base()
    weights = load_peft_weights(identity.path, device='cpu', local_files_only=True)
    result = set_peft_model_state_dict(engine.model, weights, adapter_name='default',
        ignore_mismatched_sizes=False, low_cpu_mem_usage=False)
    require(not result.unexpected_keys, 'unexpected_shared_adapter_keys')
    require(not any(native.is_lora(name) for name in result.missing_keys), 'missing_shared_adapter_keys')
    after = {name: value for name, value in engine.model.named_parameters() if native.is_lora(name)}
    require(before == {name: id(value) for name, value in after.items()}, 'resident_parameter_identity')
    require(native.state_hash(after) == identity.state_sha256, 'loaded_shared_adapter_hash')
    engine.model.requires_grad_(False)
    engine.model.eval()
    engine.verify_base()
    return document


class Session:
    def __init__(self, root, plan):
        self.root = Path(root).resolve(strict=True)
        binding = plan['shared_learner']
        self.branch = binding['branch']
        require(self.branch == {0: 'F1', 4: 'A1'}.get(plan['physical']), 'route_branch_physical_binding')
        self.owner = self.branch == 'F1'
        self.shared_root = Path(binding['root']).resolve(strict=True)
        config_path = self.shared_root / 'CONFIG.json'
        require(coordinator.sha(config_path) == binding['config_sha256'], 'shared_config_binding')
        self.config = coordinator.read(config_path)
        require(self.config['owner'] == 'F1' and set(self.config['branches']) == set(coordinator.BRANCHES),
                'exact_shared_eight_single_owner')
        spec = self.config['branches'][self.branch]
        require(Path(spec['root']).resolve() == self.root, 'shared_branch_root_binding')
        cohort = coordinator.read(self.root / 'COHORT.json')
        require(set(spec['train_ids']) == {task['id'] for task in cohort['train']}, 'shared_train_binding')
        final_ids = [task['id'] for task in coordinator.read(self.root / 'SEALED_FINAL.json')['tasks']]
        require(set(plan['held_ids'] + final_ids).issubset(self.config['excluded_ids']),
                'all_route_dev_final_excluded')
        require(self.config['anchor_sha256'] == coordinator.ANCHOR_SHA
                and self.config['anchor_loss_weight'] == .25
                and self.config['new_presentations'] == 16
                and self.config['rehearsal_presentations'] == 1, 'shared_sleep_policy')
        adoption_path = Path(binding['adoption_path']).resolve(strict=True)
        require(coordinator.sha(adoption_path) == binding['adoption_sha256'], 'adoption_binding')
        self.adoption = coordinator.read(adoption_path)
        require(self.adoption['checkpoint'] == self.config['initial_checkpoint'], 'adopt_F1_not_merge')
        require(self.adoption['prior_metrics'] == self.config['pretransition_metrics'], 'baseline_exposure_counts')
        require(self.adoption['branch_bounds'][self.branch] == plan['bounds'], 'no_bound_reset')
        require(self.config['initial_history'].get('F1'), 'adopted_F1_history_required')
        for pending in self.root.glob('cycle_*/SHARED_SUBMISSION.json'):
            require((pending.parent / 'SHARED_SLEEP.json').exists(),
                    'partial_shared_cycle_requires_explicit_recovery_no_replay')
        self.state = coordinator.read(self.shared_root / 'STATE.json')
        require(self.state['config_sha256'] == binding['config_sha256'], 'shared_state_config_binding')
        coordinator.checked_checkpoint(self.state['checkpoint'])
        self.loaded_reference = deepcopy(self.state['checkpoint'])

    def capture_binding(self):
        return dict(branch=self.branch, generation=self.state['generation'],
                    checkpoint_sha256=self.loaded_reference['path_sha256'])

    def capture_metadata(self):
        return dict(shared_learner=self.capture_binding(), shared_generation=self.state['generation'],
                    shared_checkpoint_sha256=self.loaded_reference['path_sha256'])

    def sleep(self, engine, optimizer, anchors, rows, episode_ids, output, save_callback, check,
              *, reload_call=reload_adapter, pause=time.sleep, train_call=coordinator.train):
        require((optimizer is not None) == self.owner, 'F1_optimizer_only_nonowners_none')
        require(len(episode_ids) == 2 and len(set(episode_ids)) == 2, 'exact_two_distinct_route_episodes')
        output = Path(output)
        binding = self.capture_binding()
        for row in rows:
            call = coordinator.read(row['source_call_path'])
            require(call.get('shared_learner') == binding, 'actual_common_child_capture_binding')
            require(call.get('shared_generation') == binding['generation']
                    and call.get('shared_checkpoint_sha256') == binding['checkpoint_sha256'],
                    'actual_common_child_top_level_metadata')
        check('shared_submit')
        submitted = coordinator.submit(self.shared_root, self.branch, self.state['generation'],
            self.loaded_reference['path_sha256'], episode_ids, rows)
        coordinator.write(output / 'SHARED_SUBMISSION.json', submitted)
        while True:
            check('shared_barrier_wait')
            if self.owner:
                result = coordinator.consolidate(self.shared_root, 'F1',
                    self.loaded_reference['path_sha256'], engine, optimizer, anchors, save_callback, check,
                    train_call=train_call)
                if result['status'] == 'COMPLETE':
                    break
            status = coordinator.barrier_status(self.shared_root)
            if status['generation'] > self.state['generation']:
                require(not self.owner, 'owner_generation_changed_externally')
                require(status['generation'] == self.state['generation'] + 1, 'exact_next_shared_generation')
                complete = coordinator.read(self.shared_root /
                    f"generation_{self.state['generation']:06d}" / 'sleep' / 'COMPLETE.json')
                require(complete['state'] == status['state'], 'shared_complete_state_binding')
                result = dict(status='COMPLETE', state=status['state'], metrics=complete['metrics'])
                reload_call(engine, result['state']['checkpoint'])
                break
            pause(1.0)
        coordinator.checked_checkpoint(result['state']['checkpoint'])
        self.state = result['state']
        self.loaded_reference = deepcopy(self.state['checkpoint'])
        receipt = dict(result, branch=self.branch, optimizer_owner='F1',
            local_optimizer_steps=result['metrics']['optimizer_steps'] if self.owner else 0,
            adopted_plus_shared_totals={key: self.state[key] for key in METRICS},
            shared_only_totals={key: self.state['shared_' + key] for key in METRICS}, inherited_bounds_unchanged=True,
            completed_unix=time.time())
        coordinator.write(output / 'SHARED_SLEEP.json', receipt)
        return receipt
