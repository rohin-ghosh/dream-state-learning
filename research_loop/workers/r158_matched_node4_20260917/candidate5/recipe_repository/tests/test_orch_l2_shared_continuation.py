import json
from pathlib import Path
import shutil
import tarfile
import tempfile
from types import SimpleNamespace
import unittest

from gpu import orch_l2_shared_run as run
from gpu.orch_l2_long_hook import build_parent
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_full_rich as rich


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        archive = Path('research_notes/analysis/orch_l2_long_20260914_attempt1/RESUME_ORIGINAL_001.tar.gz')
        with tarfile.open(archive) as stream:
            stream.extractall(self.root, filter='data')
        self.output = self.root / 'LONG/cycle1/experience'
        self.attempt = self.output / 'CONTINUATION_V5'
        self.attempt.mkdir()
        self.records = [run.source.read(path) for path in sorted(self.output.glob('EPISODE_*.json'))]
        self.worlds = shared.cohort([])['train'][0]
        self.identity = SimpleNamespace(document=lambda: run.source.read(self.output / 'REQUEST.json')['input_adapter'])
        request = run.source.read(self.output / 'REQUEST.json')
        run.write(self.root / 'PREPARE_TEST.json', {'original': True})
        request['runtime_manifest_sha256'] = run.bridge.file_sha256(self.root / 'PREPARE_TEST.json')
        run.write(self.output / 'REQUEST.json', request)
        evidence = Path('research_notes/analysis/orch_l2_guided_20260914_attempt1/parent')
        for identity in ('0001_LONG_C1', '0002_LONG_C1'):
            recovered = evidence / (identity + '.recovered.response.json')
            shutil.copyfile(recovered, self.root / 'parent_queue' / recovered.name)

    def test_exact_boundary_rejects_unrecorded_child_call_and_task_drift(self):
        self.assertEqual(run.continuation_records(self.root, 'LONG', 1, self.output,
            self.identity, self.worlds), self.records)
        extra = self.output / 'CALL_0016.json'
        shutil.copyfile(self.output / 'CALL_0015.json', extra)
        with self.assertRaisesRegex(ValueError, 'partial_child_call'):
            run.continuation_records(self.root, 'LONG', 1, self.output, self.identity, self.worlds)
        extra.unlink()
        changed = json.loads(json.dumps(self.records[0]))
        changed['task']['goal'] = 'different'
        run.write(self.output / 'EPISODE_01.json', changed)
        with self.assertRaisesRegex(ValueError, 'task_drift'):
            run.continuation_records(self.root, 'LONG', 1, self.output, self.identity, self.worlds)

    def test_restore_four_episodes_then_deliver_reserved_pending_parent(self):
        originals = {path: path.read_bytes() for path in self.root.rglob('*.json')}
        ledger_bytes = {path: path.read_bytes() for path in self.root.glob('CALLS_*')}
        transport = run.RecordedParentTransport(self.root, 'LONG', 1, lambda label: None, self.attempt)
        counts = {parent['message']: parent['long_decision']['message_tokens']
            for record in self.records for parent in record['parent_messages']}
        tokenizer = SimpleNamespace(encode=lambda text, **kwargs: [0] * counts.get(text, 120))
        hook = build_parent(root=self.root, cycle=1, tokenizer=tokenizer, transport=transport, emit=lambda event: None)
        previous = []
        for record in self.records:
            run.restore_parent_episode(hook, record, guided.learner_telemetry(previous, 1))
            previous.append(record)
            candidates = [capture for capture in record['captures']
                if rich.row_gate(record, capture)['eligible_for_semantic_review']]
            if candidates:
                response = transport(dict(kind='semantic', episode=record,
                    candidates=[dict(capture_sha256=rich.digest(capture),
                        raw_sha256=rich.digest(capture['response']['raw']), capture=capture) for capture in candidates],
                    rubric=list(rich.RUBRIC)))
                self.assertTrue(response['reviews'])
        self.assertEqual(transport.position, 2)
        self.assertEqual(hook.completed, 4)
        self.assertEqual(hook.parent.decisions[1], 1)
        self.assertEqual(hook.parent.exposures[1], 1)
        task = shared.tasks(self.worlds[2])[0]
        payload = dict(kind='coach', turn=0, task=task,
            public_messages=[dict(role='system', content=rich.SYSTEM),
                dict(role='user', content=rich.readout.display(task['node'], task, list(task['ports'])))],
            prior_parent_messages=[], learner=guided.learner_telemetry(previous, 1))
        transport.restoring = False
        result = hook(payload)
        self.assertTrue(result['speak'])
        self.assertEqual(transport.position, 3)
        self.assertEqual(hook.parent.decisions[1], 2)
        self.assertEqual(hook.parent.messages[1], 2)
        self.assertEqual(hook.parent.exposures[1], 1)
        expected = run.source.read(self.root / 'parent_queue/0002_LONG_C1.recovered.response.json')['result']
        self.assertEqual(result['message'], expected['message'])
        for path, content in {**originals, **ledger_bytes}.items():
            self.assertEqual(path.read_bytes(), content)
        transport.restoring = True
        with self.assertRaisesRegex(ValueError, 'must_not_dispatch'):
            transport(payload)

    def test_payload_drift_fails_without_spend(self):
        transport = run.RecordedParentTransport(self.root, 'LONG', 1, lambda label: None, self.attempt)
        with self.assertRaisesRegex(ValueError, 'request_drift'):
            transport(dict(kind='long_coach', long_request={}))
        self.assertEqual(transport.position, 0)


if __name__ == '__main__':
    unittest.main()
