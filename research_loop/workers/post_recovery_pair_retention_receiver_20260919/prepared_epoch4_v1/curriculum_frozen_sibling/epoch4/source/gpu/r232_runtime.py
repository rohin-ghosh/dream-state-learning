"""Exact-initial R231 sibling: unchanged wake/housekeeping, no weight updates."""

from copy import deepcopy
from pathlib import Path
import time
from types import FunctionType

from gpu import r205_runtime as runtime
from gpu import orch_r125_continual_native as native
from gpu import orch_r125_stream_journal as journal_module
from gpu.r231_runtime import receiving_command
from organism_v6.orch_r125_continual_stream import ContinualStream, digest, require


ROOT = Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')
DEVICE = 'GPU-02917283-de83-a2c7-db03-272dca482162'
POLICY = 'R232_EXACT_INITIAL_FROZEN_SIBLING_V1'
INITIAL = None


def validate_frozen(receipt, previous):
    require(receipt.get('control_policy') == POLICY, 'explicit_R232_only')
    require(receipt.get('optimizer_steps') == receipt.get('total_optimizer_steps')
        == receipt.get('cumulative_optimizer_steps') == previous['optimizer_steps'] == 0,
        'zero_actual_frozen_optimizer_updates')
    require(receipt.get('weight_updates_enabled') is False
        and receipt.get('no_update_reason') == 'R232_frozen_sibling_updates_disabled'
        and receipt.get('presentations') == []
        and receipt.get('child_token_exposures') == receipt.get('anchor_token_exposures') == 0
        and receipt.get('frozen_base_verified') is True, 'honest_no_training_exposures')
    require(receipt['before_adapter_sha256'] == receipt['after_adapter_sha256']
        == previous['adapter_state_sha256'], 'adapter_unchanged_from_same_initial')
    require(receipt['before_optimizer_state_sha256'] == receipt['after_optimizer_state_sha256']
        and len(receipt['before_optimizer_state_sha256']) == 64, 'optimizer_state_unchanged')
    if 'checkpoint' in receipt:
        checkpoint = receipt['checkpoint']
        require(checkpoint['optimizer_steps'] == 0
            and checkpoint['adapter_state_sha256'] == previous['adapter_state_sha256']
            and checkpoint.get('experiment') == previous.get('experiment')
            and checkpoint['checkpoint_sha256'] == receipt['checkpoint_sha256'], 'frozen_saved_checkpoint_bound')


def forbid_step(*args, **kwargs):
    raise ValueError('R232_optimizer_step_forbidden')


class FrozenChild(native.NativeChild):
    def __init__(self, plan, checkpoint=None):
        require(checkpoint is not None and checkpoint['optimizer_steps'] == 0, 'exact_initial_not_current_weights')
        super().__init__(plan, checkpoint)
        require(not self.optimizer.state, 'initial_optimizer_state_empty')
        self.frozen_checkpoint = deepcopy(checkpoint)
        self.frozen_optimizer_digest = runtime.optimizer_digest(self.optimizer, self.torch)
        self.optimizer.step = forbid_step

    def sleep(self, new_rows, old_rows, anchors, record):
        from gpu.orch_r144_sleep_targets import POLICY as target_policy, encode_sleep_targets
        from gpu.orch_r108_guided_native import validate_anchor_inventory
        require(new_rows and self.optimizer_steps == 0, 'nonempty_zero_update_sleep')
        require(not any(parameter.requires_grad for parameter in self.engine.model.parameters()), 'readonly_base_and_adapter')
        validate_anchor_inventory(anchors)
        record('SLEEP_RECIPE', dict(policy='R181_NEW_ONLY_V1', control_policy=POLICY,
            new_presentations=self.plan['new_presentations'], new_rows=len(new_rows),
            available_old_rows=len(old_rows), selected_old_rows=0, anchor_lambda=0.25,
            weight_updates_enabled=False, scheduled_presentations_not_executed=True,
            **native.recipe_fields(self.plan)))
        eligible, unused_old, encoded, rejected = encode_sleep_targets(
            new_rows, [], self.tokenizer, self.plan['context_limit'], native.encode_own)
        record('TARGET_ELIGIBILITY', dict(version=self.plan.get('presentation_version'),
            runtime_policy=target_policy, excluded=rejected,
            new_row_sha256=[row['source_sha256'] for row in eligible], rehearsal_row_sha256=[],
            raw_modified=False, control_policy=POLICY, **native.recipe_fields(self.plan)))
        self.engine.verify_base()
        adapter = self.adapter_hash()
        optimizer = runtime.optimizer_digest(self.optimizer, self.torch)
        require(optimizer == self.frozen_optimizer_digest, 'saved_empty_optimizer_stays_empty')
        receipt = dict(control_policy=POLICY, optimizer_steps=0, total_optimizer_steps=0,
            cumulative_optimizer_steps=0, weight_updates_enabled=False,
            no_update_reason='R232_frozen_sibling_updates_disabled', presentations=[],
            planned_presentations=len(eligible) * self.plan['new_presentations'],
            child_token_exposures=0, anchor_token_exposures=0, frozen_base_verified=True,
            before_adapter_sha256=adapter, after_adapter_sha256=self.adapter_hash(),
            before_optimizer_state_sha256=optimizer,
            after_optimizer_state_sha256=runtime.optimizer_digest(self.optimizer, self.torch),
            eligible_row_sha256=[row['source_sha256'] for row in eligible],
            excluded_rows=rejected, **native.recipe_fields(self.plan))
        validate_frozen(receipt, self.frozen_checkpoint)
        return receipt


class FrozenStream(ContinualStream):
    def commit_sleep(self, receipt, record):
        require(self.pending is None and self.sleep_frontier < len(self.rows), 'clean_frozen_sleep_frontier')
        previous = self.sleep_receipts[-1]['checkpoint'] if self.sleep_receipts else INITIAL
        validate_frozen(receipt, previous)
        require(receipt['status'] == 'COMPLETE' and receipt['new_row_sha256'] ==
            [row['source_sha256'] for row in self.pending_rows()], 'all_actual_rows_accounted')
        self.sleep_frontier = len(self.rows)
        self.sleep_receipts.append(deepcopy(receipt))
        self.model_state_sha256 = digest(receipt['checkpoint_sha256'])
        try:
            record('SLEEP_COMPLETE', dict(deepcopy(receipt), resume_state=self.checkpoint()))
        except BaseException:
            self.pending = 'sleep:' + digest(receipt)
            raise
        return self.checkpoint()


class FrozenJournal(journal_module.StreamJournal):
    def _advance(self, state, kind, document):
        if kind != 'SLEEP_COMPLETE' or document.get('control_policy') != POLICY:
            return super()._advance(state, kind, document)
        require(state['latest'] is not None and state['sleep_request'] is not None
            and state['request'] is None and state['response'] is None, 'actual_pending_frozen_sleep')
        previous = state['latest']['document']['state']
        checkpoint = self._checkpoint(document['resume_state'])
        current = checkpoint['document']['state']
        self._unchanged(previous, current, {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'})
        receipt = {key: value for key, value in document.items() if key != 'resume_state'}
        prior_model = previous['sleep_receipts'][-1]['checkpoint'] if previous['sleep_receipts'] else INITIAL
        validate_frozen(receipt, prior_model)
        rows = previous['rows'][previous['sleep_frontier']:]
        require(rows and current['pending'] is None and current['sleep_frontier'] == len(current['rows'])
            and current['sleep_receipts'] == previous['sleep_receipts'] + [receipt]
            and receipt['new_row_sha256'] == [row['source_sha256'] for row in rows]
            and receipt['status'] == 'COMPLETE' and receipt['cycle'] == state['sleep_request']['cycle']
            and current['model_state_sha256'] == digest(receipt['checkpoint_sha256']), 'exact_frozen_commit_binding')
        state['latest'], state['sleep_request'] = checkpoint, None


def main():
    global INITIAL
    INITIAL = native.read(ROOT / 'raw/checkpoints/initial/COMMIT.json')
    runtime.DEVICES = {1: (DEVICE, '0000:52:00.0')}
    runtime.TRIALS += ('R231_BASE_CURRICULUM_FROM_BIRTH',)
    runtime.MODULE = 'gpu.r232_runtime'
    original_install, original_command = runtime.install_runtime, runtime.contained_command
    verifier = runtime.verify_devices
    require(verifier.__code__.co_consts.count(2524) == 1, 'one_exact_owner_seam')
    runtime.verify_devices = FunctionType(verifier.__code__.replace(co_consts=tuple(
        1352 if value == 2524 else value for value in verifier.__code__.co_consts)), verifier.__globals__)

    def install(plan):
        require(Path(plan['root']) == ROOT / 'raw', 'new_frozen_root_only')
        require(all(scope.get('learn_row_policy') == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
            for scope in (plan, plan['think_act_learn'])), 'no_semantic_exclusions')
        runtime.receive_peer = lambda driver: None
        original_install(plan)
        native.NativeChild, native.ContinualStream = FrozenChild, FrozenStream
        journal_module.StreamJournal = FrozenJournal

    def command(config_path, mode):
        from gpu.orch_r125_continual_guard import validate
        config, plan = validate(config_path)
        require(config['resume'] is True and Path(plan['root']) == ROOT / 'raw', 'initial_snapshot_restore_only')
        return receiving_command(original_command(config_path, mode), mode, plan['hard_end_unix'], time.time())

    runtime.install_runtime, runtime.contained_command = install, command
    runtime.main()


if __name__ == '__main__':
    main()
