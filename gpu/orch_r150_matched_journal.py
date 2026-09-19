"""Matched state validation over the unchanged StreamJournal custody machinery."""

from copy import deepcopy
from types import SimpleNamespace

from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r125_continual_stream import digest, require
from organism_v6.orch_r150_matched_stream import MatchedStream, matched_binding


class MatchedJournal(StreamJournal):
    def __init__(self, root, *, arm, cohort_sha256, create=False):
        binding = matched_binding(arm, cohort_sha256)
        self._arm = binding['arm']
        self._cohort_sha256 = binding['cohort_sha256']
        super().__init__(root, create=create)

    @property
    def arm(self):
        return self._arm

    @property
    def cohort_sha256(self):
        return self._cohort_sha256

    def _checkpoint(self, document):
        require(type(document) is dict and set(document) == {'state', 'sha256'}, 'stream_checkpoint_fields')
        require(type(document['state']) is dict and document['sha256'] == digest(document['state']),
            'stream_checkpoint_integrity')
        MatchedStream.restore(document, expected_sha256=document['sha256'], expected_arm=self.arm,
            expected_cohort_sha256=self.cohort_sha256)
        return dict(document=deepcopy(document), expected_sha256=document['sha256'])

    def _inbox_event(self, message, path, source_sha256):
        return self._inbox_event_at(message, path, source_sha256, inbox=self.inbox)

    def _inbox_event_at(self, message, path, source_sha256, *, inbox):
        """Validate original receipt paths on copies without dropping matched policy."""
        event = StreamJournal._inbox_event(SimpleNamespace(inbox=inbox), message, path, source_sha256)
        require(self.arm != 'unparented_learning' or event.actor != 'parent',
            'unparented_parent_channel_forbidden')
        return event

    def _advance(self, state, kind, document):
        require(kind not in ('PRESENTATION', 'WALL_EXTENSION', 'WALL_EXTENDED'),
            'matched_common_configuration_frozen')
        if self.arm == 'parented_frozen':
            require(kind not in ('UPDATE', 'TARGET_ELIGIBILITY'), 'frozen_journal_no_training')
        if kind != 'SLEEP_COMPLETE' or self.arm != 'parented_frozen':
            return super()._advance(state, kind, document)
        require('resume_state' in document, 'authoritative_checkpoint_required')
        checkpoint = self._checkpoint(document['resume_state'])
        current = checkpoint['document']['state']
        previous = state['latest']['document']['state'] if state['latest'] else None
        require(previous is not None and (previous['pending'] is None or state['sleep_request'] is not None)
            and state['request'] is None and state['response'] is None and current['pending'] is None,
            'sleep_cannot_bypass_request')
        require(current.get('experiment') == previous.get('experiment'), 'journal_experiment_configuration_frozen')
        self._unchanged(previous, current, {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'})
        receipt = {key: value for key, value in document.items() if key != 'resume_state'}
        require(receipt.get('checkpoint', {}).get('experiment') == current['experiment'],
            'sleep_model_experiment_binding')
        if state['sleep_request'] is not None and 'cycle' in state['sleep_request']:
            require(receipt.get('cycle') == state['sleep_request']['cycle'], 'sleep_cycle_binding')
        require(current['sleep_receipts'] == previous['sleep_receipts'] + [receipt], 'sleep_frontier_binding')
        stream = MatchedStream.restore(state['latest']['document'],
            expected_sha256=state['latest']['expected_sha256'], expected_arm=self.arm,
            expected_cohort_sha256=self.cohort_sha256)
        if stream.pending is not None:
            require(stream.pending == 'sleep:' + digest([row['source_sha256'] for row in stream.pending_rows()]),
                'sleep_request_frontier_binding')
        stream.pending = None
        expected = stream.commit_sleep(receipt, lambda kind, value: None)
        require(expected == checkpoint['document'], 'sleep_checkpoint_binding')
        state['sleep_request'] = None
        state['latest'] = checkpoint
