"""Synthetic CPU collection fixtures; no native replay, model imports, or GPU calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location('lr_analysis', '/tmp/astra_l2_lr_analyze_20260913.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
EXAMPLE = Path('/tmp/astra_l2_collection_20260913_attempt1.json')


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir='/tmp', prefix='lr_analysis_cpu_')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.rows = analysis.roster()
        self.reports = {}
        self.entries = []
        for name, row in self.rows.items():
            report = json.loads(EXAMPLE.read_bytes())
            report.update(plan_sha256=row['plan_sha256'], learning_rate=row['learning_rate'],
                          seeds=dict(vocabulary=2026091301, truth=2026091302, learner=row['learner_seed']))
            self.reports[name] = report
        self.persist()

    def persist(self):
        self.entries = []
        for name, report in self.reports.items():
            path = self.home / (name + '.json')
            data = json.dumps(report, allow_nan=False).encode()
            path.write_bytes(data)
            self.entries.append((name, str(path), hashlib.sha256(data).hexdigest()))

    def run_analysis(self):
        self.persist()
        return analysis.analyze(self.entries)

    def change_promote(self, name, correct):
        report = self.reports[name]
        old, new = correct // 2, correct - correct // 2
        report['reports']['report2_PROMOTE'].update(old_correct=old, new_correct=new)
        report['contrasts']['2'].update(old_correct=old - 4, new_correct=new - 4)
        report['endpoint']['cells']['PROMOTE'].update(old_correct=old, new_correct=new,
                                                       observed_correct=correct, accuracy=correct / 16)
        both = min(correct, 8)
        report['endpoint']['paired'].update(both=both, promote_only=correct - both,
                                             shadow_only=8 - both, neither=16 - max(correct, 8), net=correct - 8)

    def test_paired_means_and_three_learner_denominator(self):
        for seed, delta in enumerate((1, -1, 2)):
            self.change_promote(f'seed{seed}_high', 8 + delta)
        result = self.run_analysis()
        self.assertEqual([pair['high_minus_low']['numerator'] for pair in result['paired_learners']], [1, -1, 2])
        self.assertEqual(result['descriptive']['high_minus_low']['mean'], 2 / 48)
        self.assertEqual(result['descriptive']['high_minus_low']['range'], [-1 / 16, 2 / 16])
        self.assertEqual(result['descriptive']['high_minus_low']['planned_learners'], 3)
        self.assertFalse(result['original_seed0_bridge_included_as_replicate'])
        self.assertTrue(result['all_six_complete'])
        self.assertEqual(result['runs']['seed0_low']['native_collection']['exposure'], self.reports['seed0_low']['exposure'])
        self.assertIsNone(result['runs']['seed0_low']['unavailable']['fit_losses'])
        costs = result['runs']['seed0_low']['measured_cost_totals']
        self.assertEqual(costs['work'], dict(calls=128, fits=3, updates=100))
        self.assertEqual(costs['presentations'], 800)
        self.assertEqual(costs['supervised_tokens_seen'], 20 * (104 + 208 + 208))
        self.assertEqual(costs['train_tokens_seen'], 23540 + 47140 + 47140)

    def test_abort_remains_visible_not_accuracy_zero(self):
        report = self.reports['seed1_high']
        for key in ('seeds', 'learning_rate', 'reports', 'endpoint', 'work', 'formation', 'exposure', 'contrasts', 'incomplete'):
            report.pop(key)
        report.update(status='NONREPORTABLE_RUNTIME_ABORT', scientific_replay=False, two_cycle_complete=False,
                      completed=['baseline'], failed_raw_stages_not_scored=True, reason='mocked timeout')
        result = self.run_analysis()
        self.assertIsNone(result['paired_learners'][1]['high_minus_low'])
        self.assertIsNone(result['descriptive']['high_minus_low']['mean'])
        self.assertEqual(result['descriptive']['high_minus_low']['observed_learners'], 2)
        self.assertEqual(result['failures'], {'seed1_high': 'NONREPORTABLE_RUNTIME_ABORT'})
        self.assertIsNone(result['runs']['seed1_high']['measured_cost_totals'])

    def test_shortage_preserves_partial_reports_without_endpoint(self):
        report = self.reports['seed2_low']
        report.update(status='FORMATION_SHORTAGE', two_cycle_complete=False, endpoint=None,
                      completed=list(analysis.STAGES[:3]), incomplete=list(analysis.STAGES[3:]),
                      work=dict(calls=32, fits=0, updates=0), contrasts={'1': None, '2': None})
        report['reports'] = {stage: report['reports'][stage] if stage == 'baseline' else None for stage in analysis.REPORTS}
        formed = report['formation']['fit1']
        formed.update(status='FORMATION_SHORTAGE', admitted=0, rejected=8, candidate_sha256=None)
        report['formation'] = {'fit1': formed}
        report['exposure'] = {stage: report['exposure'][stage] for stage in analysis.STAGES[:2]}
        report['exposure']['fit1'] = dict(fits=0, updates=0, presentations=0)
        result = self.run_analysis()
        self.assertIsNone(result['runs']['seed2_low']['final_promote_minus_shadow'])
        self.assertEqual(result['runs']['seed2_low']['native_collection']['reports']['baseline']['total'], 16)

    def test_identity_substitution_and_count_disagreements_rejected(self):
        original = copy.deepcopy(self.reports['seed0_low'])
        mutations = [lambda report: report.update(root='/wrong/root'),
                     lambda report: report.update(plan_sha256='0' * 64),
                     lambda report: report.update(learning_rate=1e-4),
                     lambda report: report['seeds'].update(learner=True),
                     lambda report: report['reports']['baseline'].update(legal=True),
                     lambda report: report['reports']['baseline'].update(malformed=1),
                     lambda report: report['endpoint']['paired'].update(both=7),
                     lambda report: report['endpoint']['cells']['PROMOTE'].update(accuracy=.75),
                     lambda report: report['work'].update(updates=99),
                     lambda report: report['exposure']['fit1'].update(train_tokens_seen=1),
                     lambda report: report['formation']['fit1'].update(rejected=1),
                     lambda report: report.update(scientific_replay=False),
                     lambda report: report.update(two_cycle_complete=1)]
        for mutate in mutations:
            self.reports['seed0_low'] = copy.deepcopy(original)
            mutate(self.reports['seed0_low'])
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                self.run_analysis()

    def test_missing_duplicate_extra_and_swapped_reports_rejected(self):
        for entries in (self.entries[:-1], self.entries + [self.entries[0]],
                        [self.entries[0]] + self.entries[:-1],
                        [(self.entries[1][0], *self.entries[0][1:]), (self.entries[0][0], *self.entries[1][1:])] + self.entries[2:]):
            with self.assertRaises(ValueError):
                analysis.analyze(entries)

    def test_pins_and_duplicate_json_and_nonfinite_rejected(self):
        name, path, checksum = self.entries[0]
        for data in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'):
            Path(path).write_bytes(data)
            with self.assertRaises(ValueError):
                analysis.read_pinned(path, hashlib.sha256(data).hexdigest())
        with self.assertRaisesRegex(ValueError, 'pin differs'):
            analysis.analyze(self.entries)
        roster = self.home / 'wrong_roster.json'
        roster.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'pin differs'):
            analysis.roster(roster)

    def test_cli_write_once_preserves_inputs(self):
        output = self.home / 'analysis.json'
        arguments = ['--output', str(output)]
        for entry in self.entries:
            arguments.extend(['--collection', *entry])
        before = {path: Path(path).read_bytes() for name, path, checksum in self.entries}
        analysis.main(arguments)
        original_output = output.read_bytes()
        with self.assertRaises(FileExistsError):
            analysis.main(arguments)
        self.assertEqual(output.read_bytes(), original_output)
        self.assertTrue(all(Path(path).read_bytes() == data for path, data in before.items()))


if __name__ == '__main__':
    unittest.main()
