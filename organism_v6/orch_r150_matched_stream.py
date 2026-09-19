"""Versioned CPU-only matched controls; the original learning contract is unchanged."""

from copy import deepcopy
import time

from organism_v6.orch_r124_train_history import TrainEvent
from organism_v6.orch_r125_continual_stream import (
    SCHEMA as CONTINUAL_SCHEMA, ContinualStream, digest, require, valid_sha256,
)


SCHEMA = 'R150_MATCHED_STREAM_V1'
POLICY_SCHEMA = 'R150_MATCHED_POLICY_V1'
MODES = ('parented_learning', 'parented_frozen', 'unparented_learning')
FROZEN_AUDIT_FIELDS = dict(total_optimizer_steps=0, weight_updates_enabled=False,
    no_update_reason='frozen_control_condition', context_compaction_schedule='SAME_AS_LEARNING_ARMS',
    configured_anchor_lambda=0.25, anchor_mix_applied=False)


def matched_binding(arm, cohort_sha256):
    require(type(arm) is str and arm in MODES, 'known_matched_arm')
    require(valid_sha256(cohort_sha256), 'bound_matched_cohort_required')
    return dict(schema=POLICY_SCHEMA, arm=arm, cohort_sha256=cohort_sha256, lora_rank=8,
        parent_channel='reject' if arm == 'unparented_learning' else 'allow',
        learning='frozen' if arm == 'parented_frozen' else 'lora')


def validate_model_checkpoint(checkpoint, experiment):
    require(type(checkpoint) is dict, 'actual_model_checkpoint_required')
    references = checkpoint.get('checkpoint_sha256')
    require(type(references) is dict and set(references) == {'adapter', 'optimizer', 'rng'}
        and all(valid_sha256(value) for value in references.values()), 'full_actual_checkpoint_hashes')
    require(valid_sha256(checkpoint.get('adapter_state_sha256')), 'actual_adapter_state_hash')
    require(type(checkpoint.get('optimizer_steps')) is int and checkpoint['optimizer_steps'] >= 0,
        'actual_checkpoint_optimizer_steps')
    require(checkpoint.get('experiment') == experiment, 'stream_model_experiment_binding')
    return references


class MatchedStream(ContinualStream):
    def __init__(self, history, *, arm, cohort_sha256, initial_checkpoint, **kwargs):
        binding = matched_binding(arm, cohort_sha256)
        self._arm = binding['arm']
        self._cohort_sha256 = binding['cohort_sha256']
        super().__init__(history, **kwargs)
        require(self.experiment is not None, 'matched_experiment_required')
        references = validate_model_checkpoint(initial_checkpoint, self.experiment)
        require(initial_checkpoint['optimizer_steps'] == 0, 'fresh_initial_optimizer_required')
        require(self.model_state_sha256 == digest(references), 'matched_initial_model_binding')
        self._initial_checkpoint = deepcopy(initial_checkpoint)
        self._check_parent_history()

    @property
    def arm(self):
        return self._arm

    @property
    def cohort_sha256(self):
        return self._cohort_sha256

    @property
    def frozen(self):
        return self.arm == 'parented_frozen'

    def _check_parent_history(self):
        require(self.arm != 'unparented_learning'
            or all(event.actor != 'parent' for event in self.history.events),
            'unparented_parent_channel_forbidden')

    def step(self, generate, token_count, record, *, incoming=(), now=time.time):
        incoming = tuple(incoming)
        self._check_parent_history()
        for event in incoming:
            require(isinstance(event, TrainEvent) and event.actor in ('parent', 'environment'),
                'external_input_never_child_authored')
            require(self.arm != 'unparented_learning' or event.actor != 'parent',
                'unparented_parent_channel_forbidden')
        return super().step(generate, token_count, record, incoming=incoming, now=now)

    def _previous_model_checkpoint(self):
        return self.sleep_receipts[-1]['checkpoint'] if self.sleep_receipts else self._initial_checkpoint

    def frozen_boundary_receipt(self, checkpoint, *, frozen_base_verified, cycle=None):
        require(self.frozen, 'frozen_boundary_only_for_frozen_mode')
        require(frozen_base_verified is True, 'caller_must_verify_frozen_base')
        references = validate_model_checkpoint(checkpoint, self.experiment)
        receipt = dict(kind='FROZEN_CONTROL_BOUNDARY', status='COMPLETE', optimizer_steps=0,
            cumulative_optimizer_steps=0, frozen_base_verified=frozen_base_verified,
            presentations=[], child_token_exposures=0, anchor_token_exposures=0,
            before_adapter_sha256=self._previous_model_checkpoint()['adapter_state_sha256'],
            after_adapter_sha256=checkpoint['adapter_state_sha256'],
            new_row_sha256=[row['source_sha256'] for row in self.pending_rows()],
            checkpoint_sha256=deepcopy(references), checkpoint=deepcopy(checkpoint))
        if cycle is not None:
            receipt['cycle'] = cycle
        self._validate_frozen_receipt(receipt)
        return receipt

    def _validate_frozen_receipt(self, receipt):
        fields = {'kind', 'status', 'optimizer_steps', 'cumulative_optimizer_steps', 'frozen_base_verified',
            'presentations', 'child_token_exposures', 'anchor_token_exposures',
            'before_adapter_sha256', 'after_adapter_sha256', 'new_row_sha256',
            'checkpoint_sha256', 'checkpoint'}
        require(type(receipt) is dict and fields <= set(receipt)
            <= fields | {'cycle'} | set(FROZEN_AUDIT_FIELDS),
            'exact_frozen_boundary_receipt')
        require(all(type(receipt[key]) is type(value) and receipt[key] == value
            for key, value in FROZEN_AUDIT_FIELDS.items() if key in receipt), 'truthful_frozen_audit_fields')
        require(receipt['kind'] == 'FROZEN_CONTROL_BOUNDARY' and receipt['status'] == 'COMPLETE'
            and receipt['frozen_base_verified'] is True,
            'explicit_frozen_control_boundary')
        require(all(type(receipt[key]) is int and receipt[key] == 0 for key in
            ('optimizer_steps', 'cumulative_optimizer_steps', 'child_token_exposures', 'anchor_token_exposures'))
            and type(receipt['presentations']) is list and not receipt['presentations'],
            'frozen_boundary_no_training')
        require('cycle' not in receipt or type(receipt['cycle']) is int and receipt['cycle'] >= 0,
            'actual_boundary_cycle')
        checkpoint = receipt['checkpoint']
        references = validate_model_checkpoint(checkpoint, self.experiment)
        previous = self._previous_model_checkpoint()
        require(receipt['checkpoint_sha256'] == references, 'receipt_actual_checkpoint_binding')
        require(receipt['before_adapter_sha256'] == previous['adapter_state_sha256']
            == receipt['after_adapter_sha256'] == checkpoint['adapter_state_sha256']
            and references['adapter'] == previous['checkpoint_sha256']['adapter'],
            'frozen_adapter_must_be_unchanged')
        require(checkpoint['optimizer_steps'] == previous['optimizer_steps'],
            'frozen_optimizer_must_be_unchanged')
        require(self.sleep_frontier < len(self.rows)
            and receipt['new_row_sha256'] == [row['source_sha256'] for row in self.pending_rows()],
            'sleep_exact_new_child_frontier')

    def commit_sleep(self, receipt, record):
        if not self.frozen:
            require(receipt.get('kind') != 'FROZEN_CONTROL_BOUNDARY', 'learning_cannot_use_frozen_boundary')
            references = validate_model_checkpoint(receipt.get('checkpoint'), self.experiment)
            require(receipt.get('checkpoint_sha256') == references, 'receipt_actual_checkpoint_binding')
            return super().commit_sleep(receipt, record)
        require(self.pending is None, 'no_sleep_during_unresolved_generation')
        self._validate_frozen_receipt(receipt)
        self.sleep_frontier = len(self.rows)
        self.sleep_receipts.append(deepcopy(receipt))
        self.model_state_sha256 = digest(receipt['checkpoint_sha256'])
        try:
            record('SLEEP_COMPLETE', dict(deepcopy(receipt), resume_state=self.checkpoint()))
        except BaseException:
            self.pending = 'sleep:' + digest(receipt)
            raise
        return self.checkpoint()

    def checkpoint(self):
        document = super().checkpoint()
        state = document['state']
        state.update(schema=SCHEMA, matched=matched_binding(self.arm, self.cohort_sha256),
            initial_checkpoint=deepcopy(self._initial_checkpoint))
        return dict(state=state, sha256=digest(state))

    @classmethod
    def restore(cls, document, *, expected_sha256, expected_arm, expected_cohort_sha256):
        require(type(document) is dict and set(document) == {'state', 'sha256'}
            and type(document['state']) is dict, 'exact_matched_checkpoint')
        state = deepcopy(document['state'])
        require(document['sha256'] == expected_sha256 == digest(state), 'bound_stream_checkpoint')
        require(state.get('schema') == SCHEMA, 'known_matched_stream_schema')
        require(state.get('matched') == matched_binding(expected_arm, expected_cohort_sha256),
            'resume_matched_policy_mismatch')
        initial_checkpoint = state.pop('initial_checkpoint')
        state.pop('matched')
        state['schema'] = CONTINUAL_SCHEMA
        core = ContinualStream.restore(dict(state=state, sha256=digest(state)), expected_sha256=digest(state))
        require(core.checkpoint()['state'] == state, 'exact_matched_core_state')
        stream = cls(core.history, arm=expected_arm, cohort_sha256=expected_cohort_sha256,
            initial_checkpoint=initial_checkpoint,
            context_limit=core.context_limit, segment_tokens=core.segment_tokens,
            segments_per_sleep=core.segments_per_sleep, deadline_unix=core.deadline_unix,
            model_state_sha256=digest(initial_checkpoint['checkpoint_sha256']),
            allow_eviction=core.allow_eviction, experiment=core.experiment)
        stream.presentation = deepcopy(core.presentation)
        require(type(core.sleep_receipts) is list, 'matched_sleep_receipts_list')
        for receipt in core.sleep_receipts:
            require(type(receipt) is dict and type(receipt.get('new_row_sha256')) is list
                and receipt['new_row_sha256'], 'matched_receipt_frontier')
            frontier = stream.sleep_frontier + len(receipt['new_row_sha256'])
            require(frontier <= len(core.rows), 'matched_receipt_frontier')
            stream.rows = deepcopy(core.rows[:frontier])
            stream.commit_sleep(receipt, lambda kind, value: None)
        require(stream.sleep_frontier == core.sleep_frontier
            and stream.model_state_sha256 == core.model_state_sha256, 'matched_receipt_state_binding')
        stream.rows = deepcopy(core.rows)
        stream.pending = core.pending
        require(stream.checkpoint() == document, 'exact_matched_restored_state')
        return stream
