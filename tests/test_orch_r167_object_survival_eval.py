import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from gpu import orch_r167_object_survival_eval as evaluator


class R167Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.context = dict(system_prompt='Be helpful.', birth_prompt='Begin your work.')

    def event(self, text, actor='child', split='TRAIN'):
        return dict(text=text, actor=actor, split=split, origin='TRAIN_COLLECTION')

    def test_exact_probes_caps_order_and_no_R159(self):
        self.assertEqual(evaluator.PROBES, (
            'What have you been working on? Continue it.',
            'What do you do when you write / build / investigate?',
            'what do you do when you decide what deserves attention?'))
        self.assertEqual(evaluator.ORDER[:2], (8, 25))
        self.assertEqual(set(evaluator.ORDER), {0, *range(8, 26)})
        self.assertEqual(len(evaluator.make_slots()), 38)
        self.assertEqual(evaluator.CALL_CAP, 19 * 3 * 2)
        self.assertEqual(evaluator.TOKEN_CAP, evaluator.CALL_CAP * 512)
        self.assertNotIn('r159', str(evaluator.CAMPAIGN))

    def test_context_is_fresh_per_call_and_no_history(self):
        first = evaluator.messages(self.context, evaluator.PROBES[0])
        first.append(dict(role='assistant', content='PRIVATE OLD OUTPUT'))
        second = evaluator.messages(self.context, evaluator.PROBES[1])
        self.assertEqual(len(second), 3)
        self.assertNotIn('PRIVATE OLD OUTPUT', json.dumps(second))
        self.assertEqual(second[-1]['content'], evaluator.PROBES[1])
        with self.assertRaises(ValueError):
            evaluator.messages(dict(self.context, history='forbidden'), evaluator.PROBES[0])
        with self.assertRaises(ValueError):
            evaluator.messages(self.context, 'Changed probe')

    def test_train_only_fingerprint_parent_not_target(self):
        text = 'We investigate copper bridges carefully. We test silver gears slowly.'
        events = [self.event(text), self.event(text)]
        definition = evaluator.fingerprint(events, self.context, ['investigate', 'test'])
        self.assertTrue(definition['scorable'])
        self.assertEqual(definition, evaluator.fingerprint(events, self.context, ['investigate', 'test']))
        self.assertFalse(evaluator.fingerprint([self.event(text, 'parent')] * 3,
                         self.context, ['investigate'])['scorable'])
        with self.assertRaises(ValueError):
            evaluator.fingerprint([self.event(text, split='HELD')], self.context, ['test'])

    def test_context_object_leak_ineligible(self):
        definition = dict(anchors=[['we', 'test', 'silver', 'gears', 'slowly'],
                                   ['we', 'investigate', 'copper', 'bridges', 'carefully']],
                          training_grams=[], scorable=True)
        context = dict(self.context, birth_prompt='We test silver gears slowly.')
        result = evaluator.score(dict(raw='We test silver gears slowly. We investigate copper bridges carefully.',
                                terminal=True, truncated=False), definition, context, evaluator.PROBES[0])
        self.assertTrue(result['context_leak'])
        self.assertFalse(result['eligible'])

    def test_faithful_repetition_and_truncation_count_as_reappearance(self):
        text = 'We investigate copper bridges carefully. We test silver gears slowly.'
        definition = evaluator.fingerprint([self.event(text)] * 2, self.context, ['investigate', 'test'])
        response = dict(raw=text, terminal=True, truncated=False)
        scored = evaluator.score(response, definition, self.context, evaluator.PROBES[0])
        self.assertTrue(scored['lexical_object_reappearance'])
        self.assertFalse(scored['novel_continuation_candidate'])
        response['raw'] += ' Next compare the weights under rain.'
        self.assertTrue(evaluator.score(response, definition, self.context, evaluator.PROBES[0])['novel_continuation_candidate'])
        response['truncated'] = True
        response['terminal'] = False
        scored = evaluator.score(response, definition, self.context, evaluator.PROBES[0])
        self.assertTrue(scored['eligible'])
        self.assertTrue(scored['lexical_object_reappearance'])
        self.assertTrue(scored['truncated'])
        self.assertEqual(scored['semantic_object_identity'], 'NOT_ADJUDICATED')

    def test_capped_no_hit_unscorable_and_malformed_are_distinct(self):
        from gpu import orch_r130_checkpoint_benchmark as native
        definition = evaluator.fingerprint([self.event('We test silver gears slowly. We investigate copper bridges carefully.')] * 2,
                                           self.context, ['test', 'investigate'])
        response = dict(raw='No shared lexical anchors here.', terminal=False, truncated=True)
        scored = evaluator.score(response, definition, self.context, evaluator.PROBES[0])
        self.assertTrue(scored['eligible'])
        self.assertFalse(scored['lexical_object_reappearance'])
        self.assertTrue(scored['truncated'])
        definition['scorable'] = False
        unknown = evaluator.score(response, definition, self.context, evaluator.PROBES[0])
        self.assertFalse(unknown['eligible'])
        self.assertIsNone(unknown['lexical_object_reappearance'])
        rendered = evaluator.messages(self.context, evaluator.PROBES[0])
        valid = dict(response, messages=rendered, prompt_tokens=3, token_ids=[1] * 512)
        native._validate_response(valid, rendered, 3, 7)
        with self.assertRaises(ValueError):
            native._validate_response(dict(valid, truncated=False), rendered, 3, 7)

    def test_bounded_reader_and_no_symlink(self):
        path = self.root / 'data'
        path.write_bytes(b'abcd')
        reader = evaluator.BoundedReader(self.root, 4)
        self.assertEqual(reader.raw(path), b'abcd')
        with self.assertRaises(ValueError):
            reader.raw(path)
        (self.root / 'link').symlink_to(path)
        with self.assertRaises(ValueError):
            evaluator.BoundedReader(self.root, 4).raw(self.root / 'link')
        with self.assertRaises(ValueError):
            evaluator.BoundedReader(self.root / 'other', 4).raw(path)

    def test_json_witness_and_write_once(self):
        path = self.root / 'receipt.json'
        reference = evaluator.write(path, dict(status='PASS'))
        self.assertEqual(evaluator.bound(reference)['status'], 'PASS')
        with self.assertRaises(FileExistsError):
            evaluator.write(path, {})
        path.write_text('{}')
        with self.assertRaises(ValueError):
            evaluator.bound(reference)
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                evaluator.parse(value)

    def test_chain_and_changed_witness(self):
        manifest = dict(schema='JOURNAL', journal_id='synthetic')
        record = dict(manifest, index=0, previous_sha256=evaluator.digest(manifest),
                      document={}, kind='COMMITTED')
        record['sha256'] = evaluator.digest(record)
        intent = dict(manifest, index=0, previous_sha256=record['previous_sha256'], record_sha256=record['sha256'])
        self.assertEqual(evaluator.verify_record(record, intent, manifest, 0, evaluator.digest(manifest)), record['sha256'])
        intent['record_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            evaluator.verify_record(record, intent, manifest, 0, evaluator.digest(manifest))

    def test_reserve_caps_no_retry_and_three_hour_window(self):
        lease = evaluator.write(self.root / 'lease.json', dict(lease_end_unix=100000))
        config = dict(campaign_root=str(self.root), milestone=8, condition='LORA_ON',
                      plan=dict(sha256='f' * 64), lease=lease, max_job_seconds=900)
        config_path = self.root / 'config.json'
        evaluator.write(config_path, config)
        with patch.object(evaluator.time, 'time', return_value=1000):
            key, path = evaluator.reserve(config_path, config)
            self.assertEqual(key, '8_LORA_ON')
            self.assertEqual(evaluator.read(path)['calls_charged'], 3)
            with self.assertRaises(FileExistsError):
                evaluator.reserve(config_path, config)
        current = evaluator.status(self.root, 'f' * 64)
        self.assertEqual(current['calls_charged'], 3)
        self.assertEqual(current['unresolved'], 1)
        config['condition'] = 'LORA_OFF'
        with patch.object(evaluator.time, 'time', return_value=11700):
            with self.assertRaises(ValueError):
                evaluator.reserve(config_path, config)
        self.assertEqual(evaluator.status(self.root, 'f' * 64)['calls_charged'], 3)

    def test_plan_freeze_unchanged(self):
        methods = evaluator.write(self.root / 'methods.json', evaluator.METHODS)
        freeze = evaluator.write(self.root / 'freeze.json', dict(status='AUDIT_COMPLETE', methods=methods))
        plan = evaluator.make_plan(freeze)
        self.assertEqual(plan['call_cap'], 114)
        self.assertFalse(plan['parent_access'])
        (self.root / 'methods.json').write_text('{}')
        with self.assertRaises(ValueError):
            evaluator.make_plan(freeze)

    def test_wrong_checkpoint_rejected(self):
        freeze = dict(commits={'8': dict(sha256='f' * 64)})
        evaluator.check_checkpoint_binding(dict(commit_sha256='f' * 64), freeze, 8)
        for milestone, checksum in ((8, '0' * 64), (7, 'f' * 64), (True, 'f' * 64)):
            with self.assertRaises(ValueError):
                evaluator.check_checkpoint_binding(dict(commit_sha256=checksum), freeze, milestone)

    def test_no_GO_no_dispatch_or_evaluate(self):
        with self.assertRaises(ValueError):
            evaluator.dispatch(self.root / 'unused', None)
        with self.assertRaises(ValueError):
            evaluator.evaluate(self.root / 'unused', None)

    def test_busy_admission_preserved_without_reservation_or_retry(self):
        from gpu import orch_r130_benchmark_sidecar as sidecar
        config = dict(campaign_root=str(self.root), milestone=8, condition='LORA_ON', physical=0)
        config_path, go_path = self.root / 'config.json', self.root / 'go.json'
        evaluator.write(config_path, config)
        evaluator.write(go_path, {'synthetic': True})
        report = dict(clear=False, blocking_reasons=['synthetic_busy'], scanner_euid=0)
        with patch.object(evaluator, 'validate', return_value=(config, None, None, None, None)), \
             patch.object(evaluator, 'lock', return_value=nullcontext()), patch.object(sidecar, 'scan', return_value=report):
            result = evaluator.dispatch(config_path, go_path)
            self.assertEqual(result['calls_charged'], 0)
            saved = self.root / 'attempts' / '8_LORA_ON' / 'ACTUAL_ADMISSION.private.json'
            self.assertEqual(evaluator.read(saved), report)
            self.assertFalse((self.root / 'ledger').exists())
            with self.assertRaises(FileExistsError):
                evaluator.dispatch(config_path, go_path)

    def test_interrupted_dispatch_or_launch_write_never_falsely_resolves_live_process(self):
        from gpu import orch_r130_benchmark_sidecar as sidecar
        for failure, live, identity_known in (('wait', True, True), ('launch', True, False),
                                             ('wait', False, True), ('wait', False, False)):
            with self.subTest(failure=failure, live=live, identity_known=identity_known):
                root = self.root / f'{failure}_{live}_{identity_known}'
                root.mkdir()
                lease = evaluator.write(root / 'lease.json', dict(lease_end_unix=10 ** 12))
                config = dict(campaign_root=str(root), milestone=8, condition='LORA_ON', physical=0,
                    gpu_uuid='GPU-synthetic', plan=dict(sha256='f' * 64), lease=lease,
                    max_job_seconds=900, source_root=str(root), python='/unused')
                config_path, go_path = root / 'config.json', root / 'go.json'
                evaluator.write(config_path, config)
                evaluator.write(go_path, {})
                process = SimpleNamespace(pid=9876, poll=lambda: None if live else 1)
                def interrupted():
                    raise KeyboardInterrupt()
                process.wait = interrupted
                attempt = root / 'attempts' / '8_LORA_ON'
                original_write = evaluator.write
                def write(path, value):
                    if Path(path).name == 'LAUNCH.json' and failure == 'launch':
                        raise RuntimeError('synthetic_write_failure')
                    return original_write(path, value)
                def popen(*args, **kwargs):
                    if identity_known:
                        (attempt / 'sealed').mkdir()
                        original_write(attempt / 'sealed' / 'PROCESS.json', dict(identity={'pid': 9877}))
                    return process
                with patch.object(evaluator, 'validate', return_value=(config, None, None, None, None)), \
                     patch.object(evaluator, 'lock', side_effect=lambda path: nullcontext()), \
                     patch.object(sidecar, 'scan', return_value=dict(clear=True, blocking_reasons=[])), \
                     patch.object(sidecar, 'identity', return_value={'pid': 9876}), \
                     patch.object(sidecar, 'gone', return_value=not live), \
                     patch.object(evaluator.subprocess, 'Popen', side_effect=popen), \
                     patch.object(evaluator, 'write', side_effect=write):
                    with self.assertRaises((KeyboardInterrupt, RuntimeError)):
                        evaluator.dispatch(config_path, go_path)
                current = evaluator.status(root, 'f' * 64)
                resolved = not live and identity_known
                self.assertEqual(current['failed'], int(resolved))
                self.assertEqual(current['unresolved'], int(not resolved))
                self.assertEqual(current['calls_charged'], 3)
                self.assertEqual((attempt / 'UNRESOLVED.json').exists(), not resolved)
                if not resolved:
                    config['condition'] = 'LORA_OFF'
                    second_path = root / 'second.json'
                    evaluator.write(second_path, config)
                    with patch.object(evaluator, 'validate', return_value=(config, None, None, None, None)), \
                         patch.object(evaluator, 'lock', return_value=nullcontext()), patch.object(sidecar, 'scan') as scan:
                        with self.assertRaisesRegex(ValueError, 'unresolved_previous_physical_owner'):
                            evaluator.dispatch(second_path, go_path)
                        scan.assert_not_called()

    def test_native_three_independent_calls_single_condition_and_fresh_process(self):
        from gpu import orch_r130_checkpoint_benchmark as native
        from gpu import orch_r107_capability_run as paired
        config = dict(milestone=8, condition='LORA_OFF', campaign_root=str(self.root),
                      model_dir='/unused', gpu_uuid='GPU-synthetic')
        config_path = self.root / 'config.json'
        evaluator.write(config_path, config)
        private = dict(context=self.context, definitions={'8': dict(object=dict(anchors=[], training_grams=[], scorable=False),
                        behavior=dict(anchors=[], training_grams=[], scorable=False))})
        freeze = dict(fingerprints=evaluator.write(self.root / 'fingerprints.json', private))
        (self.root / 'ledger').mkdir()
        (self.root / 'attempts' / '8_LORA_OFF').mkdir(parents=True)
        evaluator.write(self.root / 'ledger' / '8_LORA_OFF.RESERVED.json',
                        dict(execution=evaluator.ref(config_path), deadline_unix=10 ** 12))
        calls, conditions = [], []
        tokenizer = SimpleNamespace(eos_token_id=7, apply_chat_template=lambda *args, **kwargs: [1, 2, 3])
        def generate(messages, **kwargs):
            calls.append(json.loads(json.dumps(messages)))
            return dict(raw='Synthetic response', messages=messages, prompt_tokens=3, token_ids=[7], terminal=True, truncated=False)
        engine = SimpleNamespace(model=object(), tokenizer=tokenizer, generate=generate)
        def condition(model, value):
            conditions.append(value)
            return nullcontext()
        checkpoint = dict(commit_sha256='f' * 64)
        with patch.dict(os.environ, {'R167_EXECUTION_SHA256': evaluator.sha(config_path), 'CUDA_VISIBLE_DEVICES': 'GPU-synthetic'}), \
             patch.object(evaluator, 'USED', False), \
             patch.object(evaluator, 'validate', return_value=(config, {}, freeze, private, checkpoint)), \
             patch.object(native, '_load_engine', return_value=engine), \
             patch.object(native, '_snapshot', return_value={'synthetic': True}), \
             patch.object(native, '_require_readonly'), patch.object(paired, 'readonly_condition', side_effect=condition):
            result = evaluator.evaluate(config_path, self.root / 'go')
            self.assertEqual(result, dict(status='COMPLETE', calls=3))
            self.assertEqual([entry[-1]['content'] for entry in calls], list(evaluator.PROBES))
            self.assertEqual(conditions, ['LORA_OFF'] * 3)
            self.assertTrue(all(len(entry) == 3 for entry in calls))
            with self.assertRaises(ValueError):
                evaluator.evaluate(config_path, self.root / 'go')

    def test_missing_controls_not_negative_and_private_appendix(self):
        methods = evaluator.write(self.root / 'methods.json', evaluator.METHODS)
        freeze = evaluator.write(self.root / 'freeze.json', dict(status='AUDIT_COMPLETE', methods=methods))
        plan_path = self.root / 'plan.json'
        evaluator.write(plan_path, evaluator.make_plan(freeze))
        with patch.object(evaluator, 'CAMPAIGN', self.root):
            result = evaluator.reduce_private(plan_path, self.root / 'private_appendices' / 'generation1')
            self.assertFalse(result['answers_or_scores_returned'])
            self.assertEqual(set(result), {'status', 'counts', 'appendix', 'answers_or_scores_returned'})
            appendix = evaluator.read(result['appendix']['path'])
            self.assertFalse(appendix['full_schedule_complete'])
            self.assertIsNone(appendix['first_observed_exploratory_candidate'])
            self.assertEqual(appendix['rows'][0]['cells'][0]['cells']['0_LORA_OFF']['status'], 'MISSING_NOT_NEGATIVE')
            with self.assertRaises(ValueError):
                evaluator.reduce_private(plan_path, self.root / 'COORDINATION')

    def test_primary_prompt_independent_of_secondary_novelty_EOS_and_baseline(self):
        methods = evaluator.write(self.root / 'methods.json', evaluator.METHODS)
        freeze = evaluator.write(self.root / 'freeze.json', dict(status='AUDIT_COMPLETE', methods=methods))
        plan_path = self.root / 'plan.json'
        evaluator.write(plan_path, evaluator.make_plan(freeze))
        (self.root / 'ledger').mkdir()
        for milestone in (0, 8):
            for condition in evaluator.CONDITIONS:
                key = f'{milestone}_{condition}'
                reservation = evaluator.write(self.root / 'ledger' / (key + '.RESERVED.json'),
                    dict(key=key, plan_sha256=evaluator.sha(plan_path), calls_charged=3,
                         execution={'sha256': 'f' * 64}))
                output = self.root / 'attempts' / key / 'sealed'
                output.mkdir(parents=True)
                receipts = {}
                for position in range(3):
                    appearance = position == 0 and (milestone == 0 or condition == 'LORA_ON')
                    values = {str(sleep): dict(eligible=True, lexical_object_reappearance=appearance,
                              truncated=True, novel_5gram=False) for sleep in range(8, 26)}
                    reference = evaluator.write(output / f'{position}.SCORE.private.json', values)
                    receipts[Path(reference['path']).name] = reference['sha256']
                evaluator.write(output / 'COMPLETE.json', dict(execution_sha256='f' * 64, receipts=receipts))
                evaluator.write(self.root / 'ledger' / (key + '.COMPLETE.json'), dict(reservation=reservation))
        with patch.object(evaluator, 'CAMPAIGN', self.root):
            result = evaluator.reduce_private(plan_path, self.root / 'private_appendices' / 'generation1')
        appendix = evaluator.read(result['appendix']['path'])
        self.assertEqual(appendix['first_observed_exploratory_candidate'], 8)
        row = appendix['rows'][0]
        self.assertTrue(row['primary_lexical_candidate'])
        self.assertFalse(row['secondary_lexical_candidate'])
        self.assertTrue(row['cells'][0]['initial_comparator_positive'])
        self.assertFalse(appendix['proof'])


if __name__ == '__main__':
    unittest.main()
