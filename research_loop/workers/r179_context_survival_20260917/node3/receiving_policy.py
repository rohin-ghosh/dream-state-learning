"""CPU actual-cohort journal/history roundtrip; no model construction or CUDA."""

import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest


SOURCE = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(SOURCE))
from gpu import orch_r179_context_survival as policy
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6.orch_r125_plain_context import VERSION


class ActualSourcePolicy(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.journal = StreamJournal(Path(self.directory.name) / 'stream', create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='Purpose', birth_prompt='Object'),
            context_limit=16384, segment_tokens=512, segments_per_sleep=2, deadline_unix=time.time()+60,
            model_state_sha256='a'*64, allow_eviction=True)
        self.stream.set_presentation(dict(version=VERSION, system_prompt='Purpose', birth_prompt='Object'), 16384)
        self.child = SimpleNamespace(count_tokens=lambda messages: 100)
        self.generate = lambda messages, **options: dict(raw='Retain measured CPU object and uncertainty.',
            token_ids=[101, 102, 2], terminal=True, truncated=False)

    def prepare(self):
        external = TrainEvent(event_id='parent1', actor='parent', split='TRAIN', phase='experience',
            episode_id='CPU', source_id='CPU', source_sha256=digest('external'),
            origin='TRAIN_COLLECTION', text='Parent distinction, no sealed result.')
        self.stream.step(self.generate, self.child.count_tokens, self.journal.record, incoming=[external])
        self.stream.step(self.generate, self.child.count_tokens, self.journal.record)
        self.stream.step(self.generate, self.child.count_tokens, self.journal.record)
        self.summary = replace(self.stream.history.events[-2], event_id='compaction:1', phase='compaction')

    def test_real_journal_retained_history_sleep_restore(self):
        self.prepare()
        before = self.stream.history.checkpoint()
        rows = deepcopy(self.stream.rows)
        decision = policy.retain_or_compact(self.child, self.stream, self.journal, self.summary, 1)
        self.assertEqual(decision['action'], 'RETAIN_CONTEXT_ACROSS_SLEEP')
        self.assertEqual(before, self.stream.history.checkpoint())
        self.assertEqual(rows, self.stream.rows)
        pending = self.stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in self.stream.pending_rows()])
        pending['sha256'] = digest(pending['state'])
        self.journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
        checkpoint = self.stream.commit_sleep(dict(status='COMPLETE', cycle=1, optimizer_steps=16,
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='c'*64)), self.journal.record)
        restored = ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
        self.assertEqual(restored.history.checkpoint(), before)
        self.assertIn('Parent distinction', str(restored.history.render(self.child.count_tokens, 16384,
            presentation=restored.presentation)))
        self.journal.close()
        with StreamJournal(Path(self.directory.name) / 'stream', create=False) as reopened:
            self.assertEqual(reopened.latest_checkpoint()['expected_sha256'], checkpoint['sha256'])

    def test_real_threshold_compacts_without_raw_or_target_mutation(self):
        self.prepare()
        rows = deepcopy(self.stream.rows)
        raw = self.stream.history.events
        self.child.count_tokens = lambda messages: 12288
        result = policy.retain_or_compact(self.child, self.stream, self.journal, self.summary, 1)
        self.assertEqual(result['action'], 'COMPACT_AT_CONTEXT_THRESHOLD')
        self.assertEqual(rows, self.stream.rows)
        self.assertEqual(raw, self.stream.history.events)
        self.assertEqual(self.stream.history.operations[-1]['kind'], 'compaction')

    def test_candidate_native_only_exact_compaction_call(self):
        path = SOURCE / 'gpu/orch_r125_continual_native.py'
        source = path.read_text()
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == 'retain_or_compact']
        self.assertEqual(len(calls), 1)
        self.assertEqual([item.id for item in calls[0].args], ['child', 'stream', 'journal', 'summary', 'cycle'])
        self.assertNotIn('torch', sys.modules)

    def test_actual_import_paths(self):
        for name in ('gpu.orch_r179_context_survival', 'gpu.orch_r125_stream_journal',
                     'organism_v6.orch_r124_train_history', 'organism_v6.orch_r125_continual_stream',
                     'organism_v6.orch_r125_plain_context'):
            self.assertEqual(Path(sys.modules[name].__file__).resolve(), SOURCE / (name.replace('.', '/')+'.py'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
