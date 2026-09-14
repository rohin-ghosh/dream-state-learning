import copy
import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_oracle_repair_guard import DEVICES, evaluate
from gpu.orch_oracle_repair_native import run_task
from gpu.orch_oracle_repair_reduce import collect
from organism_v6 import orch_oracle_repair as policy


def task():
    question = 'I have 6 apples and buy 4 more. How many apples?'
    return dict(id='synthetic', cohort='TEST', question=question, gold='10',
                prior_raw=' FINAL: 6\n', prior_sha256=policy.text_hash(' FINAL: 6\n'),
                question_sha256=policy.digest(' '.join(question.lower().split())),
                branch_order=['GUIDED', 'RETRY'], shard=0, audit_status='PASS', audited_value='10')


def result(raw='I add four to six to get ten. FINAL: 10\nFINAL: 10', count=201):
    return dict(raw=raw, token_ids=list(range(count)), terminal=True,
                truncated=False, prompt_tokens=100, messages=[])


class OracleRepairTests(unittest.TestCase):
    def test_dynamic_portable_source_contract_is_packaged(self):
        from gpu import astra_portable_actor_bundle as portable
        contract = portable.contract()
        self.assertEqual(len(contract['exporter_sha256']), 64)
        self.assertEqual(len(contract['helpers']['guard']), 64)

    def row(self, branch='GUIDED', kind='repair', raw=None, count=201):
        item = task()
        _, student = policy.prompt(item, branch, kind, 'own repair' if kind == 'record' else None)
        return policy.capture(item, branch, kind, result() if raw is None else result(raw, count), student, [7, 8])

    def decision(self, row):
        return dict(status='PASS', target_sha256=row['target_sha256'],
                    student_prefix_sha256=row['student_prefix_sha256'], full_text_read=True,
                    prefix_read=True, prefix_supported=True, meaningful_revision=True,
                    reason='Synthetic arithmetic test only.', evidence_spans=[row['target']],
                    **{axis: True for axis in policy.AXES})

    def test_exact_pair_diff_only_rejection(self):
        guided, guided_prefix = policy.prompt(task(), 'GUIDED', 'repair')
        retry, retry_prefix = policy.prompt(task(), 'RETRY', 'repair')
        self.assertEqual(guided[:-1], retry[:-1])
        self.assertEqual(guided[-1]['content'], policy.REJECTION + retry[-1]['content'])
        self.assertEqual(guided_prefix, retry_prefix)
        self.assertEqual(guided[1]['content'], task()['prior_raw'])
        self.assertNotIn('150–400', str(guided_prefix))
        self.assertNotIn('checker', str(guided_prefix))

    def test_gold_and_audit_do_not_affect_actor_messages(self):
        changed = dict(task(), gold='938429', audit='HIDDEN_HINT', audited_value='938429')
        self.assertEqual(policy.prompt(changed, 'GUIDED', 'repair'), policy.prompt(task(), 'GUIDED', 'repair'))

    def test_record_is_own_words_without_verdict(self):
        guided, student = policy.prompt(task(), 'GUIDED', 'record', 'actual own repair')
        retry, _ = policy.prompt(task(), 'RETRY', 'record', 'actual own repair')
        self.assertEqual(guided, retry)
        self.assertEqual(student[-1], {'role': 'assistant', 'content': 'actual own repair'})
        self.assertNotIn('checker', str(guided))
        with self.assertRaises(ValueError):
            policy.prompt(task(), 'RETRY', 'record')

    def test_prefix_mask_and_target_exact(self):
        row = self.row()
        self.assertEqual(row['labels'][:2], [-100, -100])
        self.assertEqual(row['labels'][2:], row['call']['token_ids'])
        self.assertEqual(row['target'], row['call']['raw'])
        self.assertFalse(row['teacher_loss'])

    def test_numeric_format_only_not_wrong(self):
        for raw in ('10', ' FINAL: 10\n', '10.0', '20/2'):
            self.assertEqual(policy.prior_number(raw), policy.number('10'))
        self.assertIsNone(policy.prior_number('maybe 10 or 20'))
        self.assertIsNone(policy.prior_number('FINAL: 1/0'))

    def test_roster_frozen_raw_audit_order(self):
        document = dict(tasks=[task()], denominator=1)
        self.assertEqual(len(policy.validate_roster(document)), 1)
        for key, changed in [('prior_raw', 'FINAL: 5'), ('audited_value', '9'),
                             ('branch_order', ['RETRY', 'GUIDED']), ('shard', 1), ('audit_status', 'FAIL')]:
            bad = copy.deepcopy(document)
            bad['tasks'][0][key] = changed
            with self.assertRaises(ValueError):
                policy.validate_roster(bad)

    def test_balanced_each_gpu_and_global_order(self):
        for shard in range(4):
            orders = [policy.branch_order(position)[0] for position in range(24)
                      if policy.shard_for(position) == shard]
            self.assertEqual(orders.count('GUIDED'), 3)
            self.assertEqual(orders.count('RETRY'), 3)

    def test_one_repair_conditional_record_no_retries(self):
        calls = []
        def generate(item, branch, kind, previous=None):
            calls.append((branch, kind, previous))
            return dict(outcome_pass=branch == 'GUIDED', target='own successful repair')
        run_task(task(), generate)
        self.assertEqual(calls, [('GUIDED', 'repair', None),
                                ('GUIDED', 'record', 'own successful repair'), ('RETRY', 'repair', None)])

    def test_token_budgets_and_truncation(self):
        for count, expected in ((150, False), (151, True), (401, True), (402, False)):
            row = self.row(raw='FINAL: 10', count=count)
            self.assertEqual(row['candidate'], expected)
        sample = result('FINAL: 10')
        sample['truncated'] = True
        self.assertFalse(policy.capture(task(), 'GUIDED', 'repair', sample, [], [])['candidate'])
        sample.update(error='failure', truncated=False)
        self.assertFalse(policy.capture(task(), 'GUIDED', 'repair', sample, [], [])['outcome_pass'])

    def test_fulltext_prefix_and_rubric_fail_closed(self):
        row = self.row()
        decision = self.decision(row)
        self.assertTrue(policy.review_row(row, decision)['admitted'])
        for key, value in [('full_text_read', False), ('prefix_read', False),
                           ('target_sha256', 'wrong'), ('student_prefix_sha256', 'wrong'),
                           ('grounded_operations', False), ('no_invented_guidance', False),
                           ('evidence_spans', ['not actual target text'])]:
            with self.assertRaises(ValueError):
                policy.review_row(row, dict(decision, **{key: value}))

    def test_prefix_and_meaningful_revision_separate_gates(self):
        row = self.row()
        for axis in ('prefix_supported', 'meaningful_revision'):
            self.assertFalse(policy.review_row(row, dict(self.decision(row), **{axis: False}))['admitted'])

    def test_correctness_does_not_imply_admission(self):
        row = self.row(raw='FINAL: 10', count=4)
        reviewed = policy.review_row(row, self.decision(row))
        self.assertTrue(reviewed['outcome_pass'])
        self.assertFalse(reviewed['admitted'])

    def test_missing_record_or_duplicate_invalid(self):
        document = dict(tasks=[task()], denominator=1)
        rows = [self.row('GUIDED'), self.row('RETRY')]
        with self.assertRaises(ValueError):
            policy.reduce_rows(document, rows, True)
        with self.assertRaises(ValueError):
            policy.reduce_rows(document, rows + [rows[0]], False)
        self.assertEqual(policy.reduce_rows(document, rows, False)['decision'], 'INCOMPLETE_NO_SCIENTIFIC_CONCLUSION')

    def test_secondary_record_cannot_rescue_primary(self):
        document = dict(tasks=[task()], denominator=1)
        rows = [self.row(branch, kind) for branch in policy.BRANCHES for kind in ('repair', 'record')]
        rows = [policy.review_row(row, self.decision(row)) for row in rows]
        summary = policy.reduce_rows(document, rows, True)
        self.assertEqual(summary['joint_advantage'], 0)
        self.assertEqual(summary['decision'], 'DEALLOCATE_SCREEN')

    def snapshot(self):
        return dict(gpu=dict(index=0, uuid=DEVICES[0], memory_used_mib=1, utilization_percent=0),
                    all_gpu_indices=[str(index) for index in range(8)],
                    all_gpu_uuids=list(DEVICES.values()), compute_processes=[], processes=[])

    def test_ownership_failclosed(self):
        snapshot = self.snapshot()
        self.assertEqual(evaluate(snapshot, 0), [])
        for process in (dict(pid=12, unreadable=True), dict(pid=12, cvd='0'),
                        dict(pid=12, cvd='all'), dict(pid=12, target_device_open=True)):
            snapshot['processes'] = [process]
            self.assertTrue(evaluate(snapshot, 0))
        self.assertTrue(evaluate(self.snapshot(), 4))

    def test_peer_devices_not_borrowed_or_killed(self):
        snapshot = self.snapshot()
        snapshot['processes'] = [dict(pid=100, cvd='6'), dict(pid=101, cvd='7')]
        self.assertEqual(evaluate(snapshot, 0), [])
        self.assertEqual(set(DEVICES), {0, 1, 2, 3})

    def test_persistence_never_exempts_compute_or_cvd(self):
        snapshot = self.snapshot()
        snapshot['processes'] = [dict(pid=12, target_device_open=True, verified_persistence_service=True)]
        self.assertEqual(evaluate(snapshot, 0), [])
        snapshot['compute_processes'] = [dict(pid=12, gpu_uuid=DEVICES[0])]
        self.assertTrue(evaluate(snapshot, 0))
        snapshot['compute_processes'] = []
        snapshot['processes'][0]['cvd'] = '0'
        self.assertTrue(evaluate(snapshot, 0))

    def test_native_replay_detects_prefix_and_label_tampering(self):
        document = dict(tasks=[task()], denominator=1)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'shard0').mkdir()
            row = self.row(raw='FINAL: 6')
            row['call']['messages'], _ = policy.prompt(task(), 'GUIDED', 'repair')
            path = root / 'shard0/CALL_0001.json'
            path.write_text(json.dumps(row))
            rows, complete = collect(root, document)
            self.assertEqual(len(rows), 1)
            self.assertFalse(complete)
            for field, replacement in [('labels', [0]), ('student_prefix', []),
                                       ('target_sha256', 'wrong')]:
                bad = dict(row, **{field: replacement})
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    collect(root, document)


if __name__ == '__main__':
    unittest.main()
