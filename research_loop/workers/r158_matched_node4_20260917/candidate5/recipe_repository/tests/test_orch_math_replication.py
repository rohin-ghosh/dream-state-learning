import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_math_replication_guard import LEASE_END, evaluate_snapshot, require_lease
from gpu.orch_math_replication_native import run_task
from gpu.orch_math_replication_reduce import collect_native
from organism_v6 import orch_math_replication as policy


def synthetic_cohort():
    prompts = ('What is 20 percent of 50?', 'Workers do 5 jobs per hour; how many in 2 hours?',
               'Half of 10 apples are red; how many?', 'Each box has 5 apples; how many in 2 boxes?')
    records = [dict(question=f'{question} Case {index}', answer='private rationale\n#### 10')
               for question in prompts for index in range(20)]
    excluded = [f'gsm8k-train-{index + 1000}' for index in range(32)]
    return policy.build_cohort(records, excluded), records, excluded


def result(raw='I compute 10.\nFINAL: 10', count=201):
    return dict(raw=raw, token_ids=list(range(count)), terminal=True, truncated=False,
                prompt_tokens=40, messages=[])


class ReplicationTests(unittest.TestCase):
    def setUp(self):
        self.document, self.records, self.excluded = synthetic_cohort()
        self.task = self.document['tasks'][0]

    def row(self, kind='rich', raw='I compute 10.\nFINAL: 10'):
        return policy.capture(self.task, kind, result(raw), [])

    def test_fixed_balanced_fresh_deterministic(self):
        self.assertEqual(self.document, policy.build_cohort(self.records, self.excluded))
        self.assertEqual(len(policy.validate_cohort(self.document)), 32)
        self.assertFalse(set(self.excluded) & {task['id'] for task in self.document['tasks']})
        self.assertNotIn('private rationale', str(self.document))

    def test_exclusion_changes_selection_without_replacement_leak(self):
        excluded = [self.task['id']] + self.excluded[1:]
        changed = policy.build_cohort(self.records, excluded)
        self.assertNotIn(self.task['id'], [task['id'] for task in changed['tasks']])

    def test_bad_gold_retains_task_and_denominator(self):
        self.records[self.task['source_index']]['answer'] = 'ambiguous no delimiter'
        changed = policy.build_cohort(self.records, self.excluded)
        self.assertEqual([task['id'] for task in changed['tasks']],
                         [task['id'] for task in self.document['tasks']])
        self.assertIsNone(changed['tasks'][0]['gold'])
        self.assertEqual(changed['denominator'], 32)

    def test_missing_rows_not_success_and_not_complete(self):
        summary = policy.reduce_native(self.document, [])
        self.assertEqual(summary['primary']['denominator'], 32)
        self.assertEqual(summary['primary']['rich'], 0)
        self.assertFalse(summary['primary']['complete'])
        self.assertEqual(summary['primary']['exact_mcnemar_two_sided'], 1)

    def test_independent_exact_mcnemar(self):
        rows = []
        for task in self.document['tasks']:
            rows.extend([policy.capture(task, kind, result('FINAL: ' + answer), [])
                         for kind, answer in (('rich', '10'), ('terse', '9'))])
        summary = policy.reduce_native(self.document, rows)
        self.assertEqual(summary['primary']['rich_only'], 32)
        self.assertEqual(summary['primary']['difference'], 1)
        self.assertEqual(summary['primary']['exact_mcnemar_two_sided'], 2 / 2 ** 32)

    def test_duplicate_or_tampered_rows_rejected(self):
        with self.assertRaises(ValueError):
            policy.reduce_native(self.document, [self.row(), self.row()])
        row = self.row()
        row['outcome_pass'] = False
        with self.assertRaises(ValueError):
            policy.reduce_native(self.document, [row])

    def test_oracle_exact_final_line_and_fraction(self):
        self.assertTrue(self.row(raw='FINAL: 20/2')['outcome_pass'])
        self.assertFalse(self.row(raw='FINAL: 10\nMore text')['outcome_pass'])
        self.assertFalse(self.row(raw='FINAL: 10.0001')['outcome_pass'])
        self.assertFalse(self.row(raw='FINAL: 1/0')['outcome_pass'])

    def test_failure_cannot_be_success_or_complete(self):
        failed = result()
        failed['error'] = 'failed_call'
        row = policy.capture(self.task, 'rich', failed, [])
        self.assertFalse(row['outcome_pass'])
        self.assertFalse(row['candidate'])
        summary = policy.reduce_native(self.document, [row, self.row(kind='terse')])
        self.assertEqual(summary['primary']['complete_pairs'], 0)

    def test_lengths_and_terse_never_candidates(self):
        for tokens, expected in ((150, False), (151, True), (401, True), (402, False)):
            self.assertEqual(policy.capture(self.task, 'rich', result(count=tokens), [])['candidate'], expected)
        self.assertFalse(self.row(kind='terse')['candidate'])
        truncated = result()
        truncated['truncated'] = True
        self.assertFalse(policy.capture(self.task, 'rich', truncated, [])['candidate'])

    def test_original_prompt_identity_and_masked_guidance(self):
        from organism_v6.orch_math_rich import prompt
        for kind in policy.KINDS:
            self.assertEqual(policy.prompt(self.task, kind, 'previous child'),
                             prompt(self.task, kind, 'previous child'))
        _, student = policy.prompt(self.task, 'correction', 'previous child')
        self.assertNotIn('exact-answer checker', str(student))
        self.assertNotIn('150–400', str(student))

    def test_paired_order_and_maximum_calls(self):
        calls = []
        def generate(task, kind, previous=None):
            calls.append(kind)
            return self.row(kind=kind, raw='FINAL: 9' if kind == 'rich' else 'FINAL: 10')
        run_task(self.task, 0, generate)
        self.assertEqual(calls, ['terse', 'rich', 'correction', 'record'])
        calls.clear()
        run_task(self.task, 1, generate)
        self.assertEqual(calls[:2], ['rich', 'terse'])
        self.assertEqual(sum(4 * len(range(shard, 32, 3)) for shard in range(3)), 128)

    def test_semantics_not_headings_or_correctness(self):
        row = self.row()
        decision = dict(status='PASS', target_sha256=row['target_sha256'],
                        reason='synthetic validation', evidence_spans=['I compute 10.'], full_text_read=True)
        with self.assertRaises(ValueError):
            policy.review_row(row, decision)
        decision.update({axis: True for axis in policy.AXES})
        self.assertEqual(policy.review_row(row, decision)['semantic_status'], 'PASS')
        decision['target_sha256'] = hashlib.sha256(b'wrong').hexdigest()
        with self.assertRaises(ValueError):
            policy.review_row(row, decision)

    def test_revision_and_record_require_substance(self):
        for kind, extra in (('correction', 'meaningful_revision'), ('record', 'operational_record')):
            row = self.row(kind=kind)
            decision = dict(status='PASS', target_sha256=row['target_sha256'], reason='synthetic',
                            evidence_spans=['I compute 10.'], full_text_read=True,
                            **{axis: True for axis in policy.AXES})
            with self.assertRaises(ValueError):
                policy.review_row(row, decision)
            decision[extra] = True
            self.assertEqual(policy.review_row(row, decision)['semantic_status'], 'PASS')

    def test_allocation_unknown_and_lease_fail_closed(self):
        snapshot = dict(gpu=dict(index=2, uuid='GPU-test', memory_used_mib=0, utilization_percent=0),
                        compute_processes=[], processes=[])
        self.assertEqual(evaluate_snapshot(snapshot, 2, 'GPU-test'), [])
        self.assertTrue(evaluate_snapshot(snapshot, 0, 'GPU-test'))
        for process in (dict(pid=42, unreadable=True), dict(pid=43, cvd='GPU-test'),
                        dict(pid=44, cvd='0,1'), dict(pid=45, target_device_open=True)):
            changed = copy.deepcopy(snapshot)
            changed['processes'] = [process]
            self.assertTrue(evaluate_snapshot(changed, 2, 'GPU-test'))
        snapshot['compute_processes'] = [dict(pid=46, gpu_uuid='GPU-test')]
        self.assertTrue(evaluate_snapshot(snapshot, 2, 'GPU-test'))
        require_lease(LEASE_END - 21600 - 2701)
        with self.assertRaises(ValueError):
            require_lease(LEASE_END - 21600 - 2700)

    def test_partial_native_reduction_preserves_all_denominators(self):
        from gpu import orch_math_replication_native as native
        with tempfile.TemporaryDirectory(prefix='orch_math_replication_') as directory:
            root = Path(directory)
            tasks_path = root / 'TASKS.json'
            policy.write(tasks_path, self.document)
            shards = [root / f'shard{shard}' for shard in range(3)]
            for shard, folder in enumerate(shards):
                folder.mkdir()
                policy.write(folder / 'REQUEST.json', dict(tasks_sha256=policy.sha256(tasks_path),
                    arguments=dict(shard=shard), manifest_sha256=policy.MANIFEST_SHA256,
                    driver_sha256=policy.sha256(Path(native.__file__)),
                    policy_sha256=policy.sha256(Path(policy.__file__)), fits=0, updates=0))
            policy.write(shards[0] / 'CALL_0001.json', self.row())
            rows, provenance = collect_native(self.document, tasks_path, shards)
            summary = policy.reduce_native(self.document, rows)
            self.assertFalse(any(item['complete'] for item in provenance))
            self.assertEqual(summary['primary']['denominator'], 32)
            self.assertEqual(summary['primary']['rich'], 1)
            request = json.loads((shards[0] / 'REQUEST.json').read_text())
            request['tasks_sha256'] = 'wrong'
            (shards[0] / 'REQUEST.json').write_text(json.dumps(request))
            with self.assertRaises(ValueError):
                collect_native(self.document, tasks_path, shards)

    def test_known_persistence_service_does_not_exempt_compute_or_cvd(self):
        snapshot = dict(gpu=dict(index=2, uuid='GPU-test', memory_used_mib=1, utilization_percent=0),
                        compute_processes=[], processes=[dict(pid=2725, target_device_open=True,
                        verified_persistence_service=True, cvd=None)])
        self.assertEqual(evaluate_snapshot(snapshot, 2, 'GPU-test'), [])
        snapshot['processes'][0]['cvd'] = 'GPU-test'
        self.assertTrue(evaluate_snapshot(snapshot, 2, 'GPU-test'))
        snapshot['processes'][0]['cvd'] = None
        snapshot['compute_processes'] = [dict(pid=2725, gpu_uuid='GPU-test')]
        self.assertTrue(evaluate_snapshot(snapshot, 2, 'GPU-test'))


if __name__ == '__main__':
    unittest.main()
