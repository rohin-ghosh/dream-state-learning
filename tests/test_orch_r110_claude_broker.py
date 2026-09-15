import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r110_claude_broker as broker


class LocalStore:
    def shell(self, script, check=True):
        return subprocess.run(script, shell=True, check=check, text=True,
            capture_output=True, timeout=5)

    def copy(self, source, destination):
        shutil.copyfile(str(source).removeprefix('NODE:'), str(destination).removeprefix('NODE:'))

    def exists(self, path):
        return Path(path).exists()

    def hash(self, path):
        return broker.sha(path)


class ClaudeBrokerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='orch_claude_test_', dir='/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.prompts = self.root / 'prompts'
        self.prompts.mkdir()
        self.head_fields = dict(GAME='route worlds', STYLE='training-wheels, supportive',
            NUDGING='No additional nudging.', FOCUS='Notice actual behavior.',
            REFLECTION=dict(mode='short', max_new_tokens=512))
        for branch in broker.FAMILIES:
            (self.prompts / (branch + '.md')).write_text(broker.render_parent_prompt(self.head_fields))
        self.principles = broker.ROOT / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
        self.config = dict(schema=broker.SCHEMA, branch='F1', family='route',
            remote_root=str(self.root / 'native'), life_id='life1', deadline_unix=time.time()+300,
            max_parent_calls=4, max_budget_usd=2.0, max_output_tokens=2048,
            train_tasks={'TRAIN_1': 'a'*64}, excluded_task_ids=['HELD_1'], cohort_sha256='b'*64,
            principles_sha256=broker.PRINCIPLES_V2_SHA256, source_files=broker.source_pins())
        self.launch = dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=True,
            authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='TEST_FIXTURE_NOT_APPROVAL',
            config_sha256=broker.digest(self.config), not_before_unix=time.time()-1)
        payload = dict(schema='r111_train_public_v1', life_id='life1', cycle=1, episode=0,
            phase='experience', game='route', task_id='TRAIN_1',
            task_provenance=dict(split='TRAIN', task_sha256='a'*64, cohort_sha256='b'*64),
            events=[dict(sequence=0, actor='child', text='I should inspect the junction.',
                source_sha256='c'*64, visibility='TRAIN_PUBLIC')])
        self.request = dict(id='cycle1_episode1', payload=payload,
            payload_sha256=broker.digest(payload), lane_deadline_unix=time.time()+120)
        self.reply = dict(guidance='What remains uncertain here?', tag='SHIFT',
            intervention_class='metacognition', rationale='Attention can follow the uncertainty.')
        self.runner = Mock(side_effect=self.fake_runner)
        self.counter = 0

    def envelope(self, reply=None):
        return dict(type='result', subtype='success', is_error=False, num_turns=1,
            result=json.dumps(self.reply if reply is None else reply),
            modelUsage={broker.MODEL: dict(inputTokens=100, outputTokens=20)},
            usage=dict(input_tokens=100, output_tokens=20), total_cost_usd=.02)

    def fake_runner(self, argv, directory, cutoff, output_cap):
        (directory / 'stdout.json').write_text(json.dumps(self.envelope()))
        (directory / 'stderr.txt').write_text('')

    def evaluate(self, **changes):
        self.counter += 1
        options = dict(config=self.config, launch=self.launch, prompt_root=self.prompts,
            principles_path=self.principles, runner=self.runner,
            memory=lambda: broker.backend.MIN_AVAILABLE_BYTES, lock_path=self.root/'lock')
        options.update(changes)
        directory = self.root / ('call' + str(self.counter))
        return broker.evaluate(self.request, directory, self.config['deadline_unix'], **options), directory

    def rebind(self):
        self.request['payload_sha256'] = broker.digest(self.request['payload'])
        self.launch['config_sha256'] = broker.digest(self.config)

    def test_exact_cli_content_not_filename(self):
        argv = broker.command('SYSTEM CONTENT\nnot a filename', 2.5)
        for flag, value in {'--model': broker.MODEL, '--effort': 'max', '--output-format': 'json',
                '--tools': '', '--max-turns': '1', '--max-budget-usd': '2.5',
                '--system-prompt': 'SYSTEM CONTENT\nnot a filename'}.items():
            self.assertEqual(argv[argv.index(flag)+1], value)
        self.assertIn('--no-session-persistence', argv)
        self.assertIn('--safe-mode', argv)
        self.assertIn('--strict-mcp-config', argv)
        self.assertNotIn('--fallback-model', argv)

    def test_cli_cap_must_be_positive_finite(self):
        for value in (0, -1, float('inf'), float('nan'), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                broker.command('text', value)

    def test_parent_effort_candidate_is_bounded_and_keeps_prompt(self):
        original = broker.command('EXACT SYSTEM', 2)
        candidate = broker.command('EXACT SYSTEM', 2, 'high')
        index = original.index('--effort') + 1
        self.assertEqual(original[index], 'max')
        self.assertEqual(candidate[index], 'high')
        candidate[index] = 'max'
        self.assertEqual(candidate, original)
        for value in ('minimal', 'LOW', None, True):
            with self.assertRaisesRegex(ValueError, 'bounded_parent_effort'):
                broker.validate_config(dict(self.config, parent_effort=value))
        self.config['parent_effort'] = 'high'
        with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
            self.evaluate()
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        argv = self.runner.call_args.args[0]
        self.assertEqual(argv[argv.index('--effort')+1], 'high')
        self.assertEqual(json.loads((directory/'DISPATCH.json').read_text())['effort'], 'high')

    def test_low_and_medium_change_only_effort_with_fresh_launch_binding(self):
        for effort in ('low', 'medium'):
            with self.subTest(effort=effort):
                original = broker.command('EXACT SYSTEM', 2, 'high')
                candidate = broker.command('EXACT SYSTEM', 2, effort)
                index = original.index('--effort')+1
                self.assertEqual(candidate[index], effort)
                candidate[index] = 'high'
                self.assertEqual(candidate, original)
                self.config.update(parent_effort=effort, provider_lock_scope='branch',
                    queue_transport='node_local')
                with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
                    self.evaluate()
                self.rebind()
                result, directory = self.evaluate()
                self.assertEqual(result['status'], 'COMPLETE')
                self.assertEqual(result['consumption_status'], 'UNKNOWN')
                self.assertEqual(result['parent_effort'], effort)
                self.assertGreaterEqual(result['timing']['provider_elapsed_seconds'], 0)
                self.assertEqual(json.loads((directory/'DISPATCH.json').read_text())['effort'], effort)
                self.assertEqual(self.runner.call_args.args[2], self.request['lane_deadline_unix']-30)

    def test_async_next_guidance_bound_to_exact_prompt_without_template_changes(self):
        fields = dict(self.head_fields, NEXT_GUIDANCE='Notice how attention is allocated.')
        broker.validate_head_update(self.head_fields, fields)
        self.assertEqual(broker.render_parent_prompt(fields), broker.render_parent_prompt(self.head_fields))
        prompt_path = self.prompts/'F1.md'
        settings_path = prompt_path.with_suffix('.fields.json')
        settings = dict(schema='ORCH_R114_HEAD_FIELDS_V1', prompt_sha256=broker.sha(prompt_path), fields=fields)
        settings_path.write_text(json.dumps(settings))
        result, directory = self.evaluate()
        self.assertIn(fields['NEXT_GUIDANCE'], (directory/'SYSTEM.txt').read_text())
        self.assertFalse(result['prompt_binding']['head_waited'])
        self.assertEqual(result['prompt_binding']['next_guidance_sha256'],
            broker.hashlib.sha256(fields['NEXT_GUIDANCE'].encode()).hexdigest())
        settings['prompt_sha256'] = '0'*64
        settings_path.write_text(json.dumps(settings))
        result, directory = self.evaluate()
        self.assertNotIn(fields['NEXT_GUIDANCE'], (directory/'SYSTEM.txt').read_text())
        self.assertEqual(result['status'], 'COMPLETE')
        with self.assertRaisesRegex(ValueError, 'bounded_next_guidance'):
            broker.render_parent_prompt(dict(fields, NEXT_GUIDANCE='x'*1025))

    def test_expired_low_request_has_no_provider_time_or_consumption_claim(self):
        self.config['parent_effort'] = 'low'
        self.request['lane_deadline_unix'] = time.time()-1
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertFalse(result['provider_dispatched'])
        self.assertIsNone(result['timing']['provider_elapsed_seconds'])
        self.assertEqual(result['consumption_status'], 'UNKNOWN')
        self.assertFalse((directory/'DISPATCH.json').exists())

    def test_future_600_second_lane_keeps_reserve_and_hard_deadline(self):
        self.request['lane_deadline_unix'] = time.time()+600
        self.config['deadline_unix'] = time.time()+1200
        self.rebind()
        self.evaluate()
        self.assertEqual(self.runner.call_args.args[2], self.request['lane_deadline_unix']-30)
        self.config['deadline_unix'] = time.time()+60
        self.rebind()
        self.evaluate()
        self.assertEqual(self.runner.call_args.args[2], self.config['deadline_unix'])

    def test_terminal_filename_is_exact_and_config_bound(self):
        root = Path(self.config['remote_root'])
        self.assertEqual(broker.terminal_path(self.config), root/'TERMINAL.json')
        for name in broker.TERMINAL_FILENAMES:
            candidate = dict(self.config, terminal_filename=name)
            broker.validate_config(candidate)
            self.assertEqual(broker.terminal_path(candidate), root/name)
        for name in ('', None, '../TERMINAL.json', '/tmp/TERMINAL.json', 'IGNORE.json'):
            with self.assertRaisesRegex(ValueError, 'configured_terminal_filename'):
                broker.validate_config(dict(self.config, terminal_filename=name))
        self.config['terminal_filename'] = 'R118_WAIT600_TERMINAL.json'
        with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
            self.evaluate()

    def test_successor_terminal_and_predecessor_config_are_hash_bound(self):
        ledger = Path(self.config['remote_root'])/'parent_claude'
        ledger.mkdir(parents=True)
        prior_path = ledger/'CONFIG.json'
        prior_path.write_text(json.dumps(self.config))
        writer = self.root/'writer.py'
        writer.write_text("TERMINAL = 'GUARD_TERMINAL.json'\n")
        owner = self.root/'OWNER.json'
        owner.write_text('{"status":"PREPARED"}')
        self.config.update(queue_transport='node_local', provider_lock_scope='branch',
            parent_effort='high', predecessor_config=dict(path=str(prior_path), sha256=broker.sha(prior_path)),
            terminal_binding=dict(path='/localhome/local-rohing/owner/service/GUARD_TERMINAL.json',
                owner=dict(path=str(owner), sha256=broker.sha(owner)),
                writer=dict(path=str(writer), sha256=broker.sha(writer))))
        broker.validate_config(self.config)
        self.assertEqual(broker.terminal_path(self.config),
            Path('/localhome/local-rohing/owner/service/GUARD_TERMINAL.json'))
        before = prior_path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'predecessor_caps_and_identity'):
            broker.validate_config(dict(self.config, max_parent_calls=5))
        with self.assertRaisesRegex(ValueError, 'terminal_binding_source'):
            broker.validate_config(dict(self.config, terminal_binding=dict(self.config['terminal_binding'],
                writer=dict(path=str(writer), sha256='0'*64))))
        with self.assertRaisesRegex(ValueError, 'terminal_binding_path'):
            broker.validate_config(dict(self.config, terminal_binding=dict(self.config['terminal_binding'],
                path='/localhome/local-rohing/owner/../GUARD_TERMINAL.json')))
        self.assertEqual(prior_path.read_bytes(), before)

    def test_serve_uses_bound_terminal_and_stops_before_next_request(self):
        root = Path(self.config['remote_root'])
        queue = root/'parent_queue'
        queue.mkdir(parents=True)
        (root/'TERMINAL.json').write_text('{"status":"HISTORICAL"}')
        historical = broker.sha(root/'TERMINAL.json')
        (queue/'P0026.request.json').write_text('{}')
        (queue/'P0027.request.json').write_text('{}')
        self.config.update(queue_transport='node_local', terminal_filename='R118_WAIT600_TERMINAL.json')
        self.rebind()
        config_path = self.root/'CONFIG.json'
        launch_path = self.root/'LAUNCH.json'
        broker.write(config_path, self.config)
        broker.write(launch_path, self.launch)
        seen = []
        def finish(store, config, launch, name, buffer, prompt_root, principles_path):
            seen.append(name)
            broker.write(root/'R118_WAIT600_TERMINAL.json', {'status':'COMPLETE'})
            return 'COMPLETE'
        with patch.object(broker, 'ROOT', self.root), \
                patch.object(broker, 'source_pins', return_value=self.config['source_files']), \
                patch.dict(broker.os.environ, {'CUDA_VISIBLE_DEVICES':''}), \
                patch.object(broker.shutil, 'disk_usage', return_value=Mock(free=20*1024**3)), \
                patch.object(broker, 'process_request', side_effect=finish), \
                patch.object(broker.time, 'sleep'):
            broker.serve(config_path, launch_path, self.prompts, self.principles)
        self.assertEqual(seen, ['P0026.request.json'])
        self.assertEqual(broker.sha(root/'TERMINAL.json'), historical)
        self.assertFalse((root/'parent_claude/RUNNER.lock').exists())

    def test_f4_repair_terminal_preserves_failure_and_stops_next_dispatch(self):
        root = Path(self.config['remote_root'])
        queue = root/'parent_queue'
        queue.mkdir(parents=True)
        historical_path = root/'SHARED_TERMINAL.json'
        historical_path.write_text('{"status":"FAILED","exit_code":1}')
        historical = broker.sha(historical_path)
        for identifier in ('P0037', 'P0038'):
            (queue/(identifier+'.request.json')).write_text('{}')
        self.config.update(branch='F4', family='grid', queue_transport='node_local',
            terminal_filename='R118_SHARED_REPAIR_TERMINAL.json')
        self.rebind()
        config_path = self.root/'CONFIG.json'
        launch_path = self.root/'LAUNCH.json'
        broker.write(config_path, self.config)
        broker.write(launch_path, self.launch)
        seen = []
        def finish(store, config, launch, name, buffer, prompt_root, principles_path):
            seen.append(name)
            broker.write(root/'R118_SHARED_REPAIR_TERMINAL.json', {'status':'COMPLETE'})
            return 'COMPLETE'
        with patch.object(broker, 'ROOT', self.root), \
                patch.object(broker, 'source_pins', return_value=self.config['source_files']), \
                patch.dict(broker.os.environ, {'CUDA_VISIBLE_DEVICES':''}), \
                patch.object(broker.shutil, 'disk_usage', return_value=Mock(free=20*1024**3)), \
                patch.object(broker, 'process_request', side_effect=finish), \
                patch.object(broker.time, 'sleep'):
            broker.serve(config_path, launch_path, self.prompts, self.principles)
        self.assertEqual(seen, ['P0037.request.json'])
        self.assertEqual(broker.sha(historical_path), historical)
        self.assertFalse((root/'parent_claude/RUNNER.lock').exists())

    def test_config_is_exact_and_pinned(self):
        broker.validate_config(self.config)
        self.config['source_files'] = {}
        with self.assertRaisesRegex(ValueError, 'immutable_source_pins'):
            broker.validate_config(self.config)

    def test_r112_rejects_grace_and_silence(self):
        for authorization in ('GRACE_CONFIRMED', 'EXPLICIT_LAUNCH', 'WATCHER_RELAYED_ROHIN_GO', 'SILENCE', ''):
            candidate = dict(self.launch, authorization=authorization)
            with self.subTest(authorization=authorization), self.assertRaises(ValueError):
                broker.validate_launch(self.config, candidate, time.time())

    def test_launch_binds_config_and_window(self):
        broker.validate_launch(self.config, self.launch, time.time())
        for change in ({'authorized': False}, {'config_sha256': 'e'*64},
                {'not_before_unix': time.time()+20}, {'source_reference': ''}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                broker.validate_launch(self.config, dict(self.launch, **change), time.time())

    def test_no_dispatch_without_go(self):
        self.launch['authorized'] = False
        with self.assertRaises(ValueError):
            self.evaluate()
        self.runner.assert_not_called()

    def test_public_oracle_fields_and_events_stripped(self):
        payload = self.request['payload']
        payload['hidden_evaluator_verdict'] = {'gold': 'PRIVATE_ORACLE'}
        payload['events'][0]['hidden_answer_keys'] = 'PRIVATE_ORACLE'
        payload['events'].append(dict(sequence=1, actor='oracle', text='PRIVATE_ORACLE',
            source_sha256='d'*64, visibility='TRAIN_PUBLIC', event_type='hidden_evaluator_verdict'))
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        system = (directory/'SYSTEM.txt').read_text()
        self.assertNotIn('PRIVATE_ORACLE', system)
        self.assertIn('I should inspect the junction.', system)
        self.assertIn('PRIVATE_ORACLE', (directory/'REQUEST.json').read_text())

    def test_child_received_checker_feedback_preserved_exactly(self):
        event = dict(sequence=1, actor='oracle', event_type='checker_output',
            text='Checker says: expected 3; observed 4. The child saw this output.',
            child_received=True, score=0, correct=False, passed=False,
            failure_class='visible_check_failed', feedback={'expected': 3, 'actual': 4},
            source_sha256='d'*64, visibility='TRAIN_PUBLIC')
        self.request['payload']['events'].append(event)
        self.rebind()
        public = broker.validate_request(self.request, self.config)
        self.assertEqual(public['events'][1], event)
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertIn(event['text'], (directory/'SYSTEM.txt').read_text())

    def test_visible_game_feedback_kept_hidden_evaluator_removed(self):
        event = dict(sequence=1, actor='environment', event_type='environment_feedback',
            text='The gate remained shut.', child_received=True, outcome='blocked', score=-1,
            hidden_evaluator_verdict='PRIVATE_FINAL_SCORE', hidden_answer_keys='PRIVATE_KEY',
            source_sha256='d'*64, visibility='TRAIN_PUBLIC')
        self.request['payload']['events'].append(event)
        self.rebind()
        public = broker.validate_request(self.request, self.config)
        self.assertEqual(public['events'][1]['outcome'], 'blocked')
        self.assertEqual(public['events'][1]['score'], -1)
        self.assertNotIn('PRIVATE_', json.dumps(public))

    def test_nested_hidden_only_removed_visible_expected_kept(self):
        feedback = {'expected': 3, 'actual': 4,
            'checks': [{'passed': False, 'hidden_evaluator_verdict': 'PRIVATE_FINAL'}]}
        self.assertEqual(broker.strip_hidden_fields(feedback),
            {'expected': 3, 'actual': 4, 'checks': [{'passed': False}]})

    def test_feedback_without_child_delivery_not_assumed_public(self):
        self.request['payload']['events'].append(dict(sequence=1, actor='environment',
            event_type='checker_output', text='Undelivered checker result', score=0,
            source_sha256='d'*64, visibility='TRAIN_PUBLIC'))
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['error']['code'], 'feedback_requires_child_delivery_provenance')
        self.runner.assert_not_called()

    def test_dev_head_only_final_no_prompt_audience(self):
        broker.validate_audience_split('DEV', 'head')
        for audience in ('parent', 'head', 'exchange'):
            broker.validate_audience_split('TRAIN', audience)
            with self.subTest(audience=audience), self.assertRaises(ValueError):
                broker.validate_audience_split('FINAL', audience)
        for audience in ('parent', 'exchange'):
            with self.subTest(audience=audience), self.assertRaises(ValueError):
                broker.validate_audience_split('DEV', audience)

    def test_dev_and_final_cannot_be_parent_transcripts(self):
        for split in ('DEV', 'FINAL'):
            self.request['payload']['task_provenance']['split'] = split
            self.rebind()
            result, directory = self.evaluate()
            self.assertEqual(result['status'], 'MISSING')
        self.runner.assert_not_called()

    def test_actual_child_words_not_rewritten(self):
        self.request['payload']['events'][0]['text'] = 'I think I was correct; perhaps not.'
        self.rebind()
        public = broker.validate_request(self.request, self.config)
        self.assertEqual(public['events'][0]['text'], 'I think I was correct; perhaps not.')

    def test_held_task_refused(self):
        self.request['payload']['task_id'] = 'HELD_1'
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.runner.assert_not_called()

    def test_sealed_event_refused_not_silently_exposed(self):
        self.request['payload']['events'][0]['visibility'] = 'HELD_SEALED'
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['error']['code'], 'no_held_or_sealed_event')
        self.runner.assert_not_called()

    def test_provenance_wrong_hash_refused(self):
        self.request['payload']['task_provenance']['task_sha256'] = 'f'*64
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.runner.assert_not_called()

    def test_unknown_payload_fields_refused(self):
        self.request['payload']['held_transcript'] = 'secret'
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['error']['code'], 'transcript_allowlist')

    def test_readout_phase_refused(self):
        self.request['payload']['phase'] = 'readout'
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.runner.assert_not_called()

    def test_payload_digest_mismatch(self):
        self.request['payload_sha256'] = 'e'*64
        result, directory = self.evaluate()
        self.assertEqual(result['error']['code'], 'payload_binding')

    def test_reread_fn_each_call(self):
        first, first_dir = self.evaluate()
        (self.prompts/'F1.md').write_text(broker.render_parent_prompt(
            dict(self.head_fields, FOCUS='Changed FOCUS, fresh head-parent text.')))
        second, second_dir = self.evaluate()
        self.assertEqual((first['status'], second['status']), ('COMPLETE', 'COMPLETE'))
        self.assertNotEqual((first_dir/'SYSTEM.txt').read_text(), (second_dir/'SYSTEM.txt').read_text())
        self.assertIn('Changed FOCUS', (second_dir/'SYSTEM.txt').read_text())

    def test_response_exposes_exact_prompt_binding(self):
        result, directory = self.evaluate()
        binding = result['prompt_binding']
        self.assertEqual(binding['prompt_sha256'], broker.sha(self.prompts/'F1.md'))
        self.assertEqual(binding['prompt_sha256'], broker.sha(directory/'PARENT_PROMPT.md'))
        self.assertEqual(binding['system_sha256'], broker.sha(directory/'SYSTEM.txt'))
        self.assertEqual(binding['common_prompt_file'], 'tools/courier/swarm/prompts/F1.md')
        self.assertFalse(binding['child_gate'])

    def test_drifting_prompt_reports_mismatch_never_gates_call(self):
        first, directory = self.evaluate()
        (self.prompts/'F1.md').write_text(broker.render_parent_prompt(
            dict(self.head_fields, FOCUS='Different focus, no child gate.')))
        second, directory = self.evaluate()
        comparison = broker.compare_prompt_bindings(first['prompt_binding'], second['prompt_binding'],
            matched_opportunity=True)
        self.assertEqual(comparison['status'], 'PROMPT_MISMATCH_CONTRAST_LIMITATION')
        self.assertFalse(comparison['child_gate'])
        self.assertFalse(comparison['model_only_contrast_established'])
        self.assertEqual(second['status'], 'COMPLETE')

    def test_shared_policy_version_separate_from_child_transcript(self):
        first, directory = self.evaluate()
        self.request['payload']['events'][0]['text'] = 'Another actual child continuation.'
        self.rebind()
        second, directory = self.evaluate()
        self.assertNotEqual(first['prompt_binding']['system_sha256'], second['prompt_binding']['system_sha256'])
        comparison = broker.compare_prompt_bindings(first['prompt_binding'], second['prompt_binding'],
            matched_opportunity=True)
        self.assertEqual(comparison['status'], 'MATCHED_PARENT_POLICY_VERSION_ONLY')
        self.assertFalse(comparison['model_only_contrast_established'])

    def test_same_cycle_not_sufficient_opportunity_alignment(self):
        result, directory = self.evaluate()
        comparison = broker.compare_prompt_bindings(result['prompt_binding'], result['prompt_binding'])
        self.assertEqual(comparison['status'], 'UNVERIFIED_OPPORTUNITY_ALIGNMENT')
        self.assertFalse(comparison['child_gate'])

    def test_missing_counterpart_does_not_invent_match(self):
        result, directory = self.evaluate()
        comparison = broker.compare_prompt_bindings(result['prompt_binding'], None)
        self.assertEqual(comparison['status'], 'UNVERIFIED_MISSING_BINDING')
        self.assertFalse(comparison['child_gate'])

    def test_hourly_delivery_not_proxy_for_native_training(self):
        rows = [dict(id='first', status='COMPLETE', published_unix=11, late=False,
                    provider_dispatched=True),
                dict(id='second', status='MISSING', published_unix=12, late=True,
                    provider_dispatched=False),
                dict(id='third', status='SILENT', published_unix=13, late=False,
                    provider_dispatched=True)]
        report = broker.summarize_hour(rows, 10, 20)
        self.assertEqual(report['delivered_interventions'], 1)
        self.assertEqual(report['missing_late_slots'], 1)
        self.assertEqual(report['silent_slots'], 1)
        self.assertEqual(report['provider_dispatches'], 2)
        self.assertIsNone(report['native']['child_tokens'])
        self.assertIsNone(report['native']['optimizer_steps'])
        self.assertEqual(report['comparison_label'], 'PARENTING_SYSTEMS')

    def test_hourly_native_counts_need_matching_interval_receipt(self):
        native = dict(start_unix=10, end_unix=20, child_tokens=1200,
            optimizer_steps=16, source_sha256='a'*64)
        report = broker.summarize_hour([], 10, 20, native)
        self.assertEqual(report['native']['child_tokens'], 1200)
        self.assertEqual(report['native']['optimizer_steps'], 16)
        with self.assertRaisesRegex(ValueError, 'native_metric_window_binding'):
            broker.summarize_hour([], 11, 21, native)

    def test_duplicate_delivery_cannot_inflate_hourly(self):
        row = dict(id='same', status='COMPLETE', published_unix=11,
            provider_dispatched=True, late=False)
        with self.assertRaisesRegex(ValueError, 'duplicate_delivery_receipt'):
            broker.summarize_hour([row, row], 10, 20)

    def test_principles_wrong_bytes_no_dispatch(self):
        path = self.root/'wrong.md'
        path.write_text('wrong bytes')
        result, directory = self.evaluate(principles_path=path)
        self.assertEqual(result['error']['code'], 'principles_hash_changed')
        self.runner.assert_not_called()

    def test_memory_floor_inclusive(self):
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        low, directory = self.evaluate(memory=lambda: broker.backend.MIN_AVAILABLE_BYTES-1)
        self.assertEqual(low['error']['code'], 'vm_memory_floor')
        self.assertFalse(low['provider_dispatched'])

    def test_r116_explicit_one_gib_boundary(self):
        self.config['min_available_bytes'] = broker.OPT_IN_MIN_AVAILABLE_BYTES
        self.rebind()
        low, unused = self.evaluate(memory=lambda: broker.OPT_IN_MIN_AVAILABLE_BYTES-1)
        self.assertEqual(low['status'], 'MISSING')
        self.assertFalse(low['provider_dispatched'])
        self.assertEqual(low['memory_admission']['floor_bytes'], 1073741824)
        for extra in (0, 1, 200000000):
            result, unused = self.evaluate(memory=lambda: broker.OPT_IN_MIN_AVAILABLE_BYTES+extra)
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertTrue(result['memory_admission']['lower_floor_opt_in'])
            self.assertTrue(result['memory_admission']['single_call_lock'])
        self.assertEqual(self.runner.call_count, 3)

    def test_r116_default_floor_stays_one_point_five_gib(self):
        result, unused = self.evaluate(memory=lambda: broker.OPT_IN_MIN_AVAILABLE_BYTES)
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['memory_admission']['floor_bytes'], 1610612736)
        self.assertFalse(result['memory_admission']['lower_floor_opt_in'])
        self.runner.assert_not_called()

    def test_r116_memory_opt_in_does_not_change_lock_or_cutoff(self):
        self.config['min_available_bytes'] = broker.OPT_IN_MIN_AVAILABLE_BYTES
        self.rebind()
        with (self.root/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result, unused = self.evaluate(memory=lambda: broker.OPT_IN_MIN_AVAILABLE_BYTES)
        self.assertEqual(result['error']['code'], 'evaluator_busy_no_wait')
        self.runner.assert_not_called()
        result, unused = self.evaluate(memory=lambda: broker.OPT_IN_MIN_AVAILABLE_BYTES)
        self.assertEqual(self.runner.call_args.args[2], self.request['lane_deadline_unix']-30)
        self.assertEqual(result['status'], 'COMPLETE')

    def test_r116_floor_only_two_explicit_values_and_config_bound(self):
        for value in (0, True, 1073741823, 1073741824.0, 1500000000, 2147483648):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'bounded_memory_floor'):
                broker.validate_config(dict(self.config, min_available_bytes=value))
        self.config['min_available_bytes'] = 1073741824
        with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
            self.evaluate()

    def test_busy_lock_missing_without_wait(self):
        with (self.root/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            started = time.monotonic()
            result, directory = self.evaluate()
        self.assertLess(time.monotonic()-started, 1)
        self.assertEqual(result['error']['code'], 'evaluator_busy_no_wait')
        self.runner.assert_not_called()

    def test_r117_branch_lock_requires_node_local_and_exact_scope(self):
        with self.assertRaisesRegex(ValueError, 'branch_lock_node_only'):
            broker.validate_config(dict(self.config, provider_lock_scope='branch'))
        with self.assertRaisesRegex(ValueError, 'provider_lock_scope'):
            broker.validate_config(dict(self.config, provider_lock_scope='unlimited'))
        broker.validate_config(dict(self.config, provider_lock_scope='branch', queue_transport='node_local'))

    def test_r117_four_branch_locks_remain_exclusive_per_branch(self):
        paths = []
        for branch in broker.FAMILIES:
            config = dict(self.config, branch=branch, provider_lock_scope='branch', queue_transport='node_local')
            path = broker.provider_lock_path(config)
            paths.append(path)
            self.assertEqual(path, Path('/tmp/orch_l2_evaluator_' + branch + '.lock'))
            isolated_path = self.root / path.name
            with isolated_path.open('a') as first, isolated_path.open('a') as second:
                fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.assertEqual(len(set(paths)), 4)
        self.assertEqual(broker.provider_lock_path(self.config), broker.backend.LOCK_PATH)

    def test_r117_branch_dispatch_ignores_other_branch_lock(self):
        self.config.update(provider_lock_scope='branch', queue_transport='node_local')
        self.rebind()
        real_provider_lock_path = broker.provider_lock_path
        with patch.object(broker, 'provider_lock_path',
                side_effect=lambda config: self.root / real_provider_lock_path(config).name):
            with (self.root / 'orch_l2_evaluator_F2.lock').open('a') as other:
                fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result, unused = self.evaluate(lock_path=None)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['memory_admission']['provider_lock_scope'], 'branch')
        self.assertEqual(result['memory_admission']['provider_lock_path'],
            str(self.root / 'orch_l2_evaluator_F1.lock'))

    def test_exact_lane_wait_minus_thirty(self):
        result, directory = self.evaluate()
        self.assertEqual(self.runner.call_args.args[2], self.request['lane_deadline_unix']-30)

    def test_expired_slot_no_dispatch(self):
        self.request['lane_deadline_unix'] = time.time()+29
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.runner.assert_not_called()

    def test_timeout_missing_single_attempt(self):
        self.runner.side_effect = subprocess.TimeoutExpired('fixture', 1)
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertTrue(result['provider_dispatched'])
        self.assertFalse(result['retry'])
        self.assertEqual(self.runner.call_count, 1)

    def test_malformed_model_json_missing(self):
        def malformed(argv, directory, cutoff, output_cap):
            (directory/'stdout.json').write_text('{"bad":')
        result, directory = self.evaluate(runner=malformed)
        self.assertEqual(result['status'], 'MISSING')

    def test_silent_is_valid_not_missing(self):
        envelope = self.envelope()
        envelope['result'] = '[SILENT]'
        result = broker.parse_output(json.dumps(envelope), 'math', 'TRAIN_1')
        self.assertEqual(result['status'], 'SILENT')
        self.assertIsNone(result['plan'])
        self.assertIsNone(result['parent_metadata']['intervention_class'])

    def test_route_grid_adapters(self):
        for family in ('route', 'grid'):
            with self.subTest(family=family):
                plan, metadata = broker.adapt_plan(self.reply, family, 'TRAIN_1')
                self.assertEqual(set(plan), {'speak', 'message', 'rationale'})
                self.assertEqual(plan['message'], self.reply['guidance'])
                self.assertNotIn(self.reply['rationale'], plan['message'])
                self.assertEqual(metadata['tag'], 'SHIFT')

    def test_math_code_adapters(self):
        for family in ('math', 'code'):
            with self.subTest(family=family):
                plan, metadata = broker.adapt_plan(self.reply, family, 'TRAIN_1')
                self.assertEqual(plan['order'], ['TRAIN_1'])
                self.assertEqual(plan['episode_guidance'], {'TRAIN_1': ''})
                self.assertEqual(plan['guidance'], self.reply['guidance'])

    def test_grid_class_not_coerced_to_another_behavior(self):
        plan, metadata = broker.adapt_plan(dict(self.reply, intervention_class='self_perception'),
            'grid', 'TRAIN_1')
        self.assertEqual(metadata['intervention_class'], 'self_perception')
        self.assertEqual(metadata['legacy_plan_class'], 'self_perception')
        self.assertTrue(plan['rationale'].startswith('self_perception:'))

    def test_open_turn_accepts_actual_train_events(self):
        self.request['payload']['phase'] = 'open_turn'
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['prompt_binding']['position']['phase'], 'open_turn')

    def test_v4_exact_feedback_and_useful_organization_clause(self):
        prompt = broker.render_parent_prompt(self.head_fields)
        self.assertIn('Use the feedback the child itself received', prompt)
        self.assertIn("allow the child's own useful organisation", prompt)
        self.assertIn('nothing here is a catalogue you must enact', prompt)
        self.assertNotIn('[NUDGING]', prompt)
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual((directory/'PARENT_PROMPT.md').read_text(), prompt)

    def test_fixed_prompt_cannot_silently_revert_to_v2(self):
        path = self.prompts/'F1.md'
        path.write_text(path.read_text().replace('allow the child\'s own useful organisation',
            'always forbid any organisation'))
        result, directory = self.evaluate()
        self.assertEqual(result['error']['code'], 'fixed_v4_parent_prompt_drift')
        self.runner.assert_not_called()

    def test_head_edit_scope_focus_style_reflection(self):
        changed = dict(self.head_fields, FOCUS='Another focus.', STYLE='creative',
            REFLECTION=dict(mode='long', max_new_tokens=2048))
        broker.validate_head_update(self.head_fields, changed)
        for key in ('GAME', 'NUDGING'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'head_may_edit'):
                broker.validate_head_update(self.head_fields, dict(changed, **{key: 'changed'}))

    def test_reflection_settings_bound_not_applied_by_parent_broker(self):
        document = dict(schema='ORCH_R114_HEAD_FIELDS_V1',
            prompt_sha256=broker.sha(self.prompts/'F1.md'), fields=self.head_fields)
        (self.prompts/'F1.fields.json').write_text(json.dumps(document))
        result, directory = self.evaluate()
        settings = result['prompt_binding']['head_settings']
        self.assertEqual(settings['status'], 'BOUND_REQUESTED_SETTINGS')
        self.assertEqual(settings['fields']['REFLECTION'], self.head_fields['REFLECTION'])
        self.assertFalse(settings['reflection_applied_by_broker'])

    def test_stale_head_settings_report_only(self):
        document = dict(schema='ORCH_R114_HEAD_FIELDS_V1', prompt_sha256='e'*64, fields=self.head_fields)
        (self.prompts/'F1.fields.json').write_text(json.dumps(document))
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        settings = result['prompt_binding']['head_settings']
        self.assertEqual(settings['status'], 'SETTINGS_MISMATCH_REPORT_ONLY')
        self.assertNotIn('REFLECTION', settings['fields'])

    def test_r115_missing_fn_uses_exact_section6_fallback_all_lanes(self):
        for branch, family in broker.FAMILIES.items():
            with self.subTest(branch=branch):
                (self.prompts / (branch + '.md')).unlink()
                self.config.update(branch=branch, family=family)
                self.request['payload']['game'] = family
                self.rebind()
                result, directory = self.evaluate()
                self.assertEqual(result['status'], 'COMPLETE')
                binding = result['prompt_binding']
                self.assertEqual(binding['prompt_source'], 'R115_FIXED_SECTION6_FALLBACK')
                self.assertEqual(binding['fallback_source_sha256'], broker.sha(Path(broker.__file__)))
                self.assertEqual((directory/'PARENT_PROMPT.md').read_text(),
                    broker.render_parent_prompt(broker.FALLBACK_PARENT_FIELDS[branch]))
                self.assertEqual(binding['head_settings']['fields']['REFLECTION'],
                    broker.FALLBACK_PARENT_FIELDS[branch]['REFLECTION'])

    def test_r115_fn_appearing_after_fallback_is_reread(self):
        (self.prompts/'F1.md').unlink()
        before, unused = self.evaluate()
        (self.prompts/'F1.md').write_text(broker.render_parent_prompt(self.head_fields))
        after, unused = self.evaluate()
        self.assertTrue(before['prompt_binding']['fallback_used'])
        self.assertFalse(after['prompt_binding']['fallback_used'])
        self.assertEqual(after['prompt_binding']['prompt_source'], 'REREAD_FN_FILE')
        self.assertEqual(after['prompt_binding']['prompt_sha256'], broker.sha(self.prompts/'F1.md'))
        self.assertEqual(self.runner.call_count, 2)

    def test_r115_bad_existing_fn_not_replaced_with_fallback(self):
        (self.prompts/'F1.md').write_text('Unbound replacement policy')
        result, unused = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['error']['code'], 'fixed_v4_parent_prompt_drift')
        self.runner.assert_not_called()

    def test_r115_published_custom_fallback_fields_are_config_bound(self):
        (self.prompts/'F1.md').unlink()
        self.config['fallback_parent_fields'] = dict(self.head_fields, FOCUS='Owner published focus.')
        self.rebind()
        result, unused = self.evaluate()
        self.assertEqual(result['prompt_binding']['head_settings']['fields'],
            self.config['fallback_parent_fields'])
        self.config['fallback_parent_fields']['FOCUS'] = 'Not published'
        with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
            self.evaluate()

    def test_r115_source_user_go_still_requires_exact_config(self):
        self.launch['source_reference'] = 'USER_R115: actual USER GO received; audit complete'
        broker.validate_launch(self.config, self.launch, time.time())
        self.launch['config_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
            broker.validate_launch(self.config, self.launch, time.time())

    def test_class_is_description_not_compulsory_catalogue(self):
        for label in (None, 'useful_self_organisation'):
            with self.subTest(label=label):
                plan, metadata = broker.adapt_plan(dict(self.reply, intervention_class=label),
                    'route', 'TRAIN_1')
                self.assertEqual(metadata['intervention_class'], label)
                self.assertEqual(plan['message'], self.reply['guidance'])
        self.assertNotIn(', '.join(broker.CLASSES), broker.SYSTEM_CONTRACT)

    def test_v4_evaluation_cut_distinct_from_lease_hard_wall(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(broker.MORNING_CUT_UNIX, timezone.utc).isoformat(),
            '2026-09-15T17:00:00+00:00')
        self.assertEqual(datetime.fromtimestamp(broker.NODE5_HARD_WALL_UNIX, timezone.utc).isoformat(),
            '2026-09-16T22:04:00+00:00')
        self.config['deadline_unix'] = broker.MORNING_CUT_UNIX+1
        broker.validate_config(self.config)

    def test_new_lane_may_end_after_evaluation_cut_but_not_lease(self):
        self.config['deadline_unix'] = broker.NODE5_HARD_WALL_UNIX
        broker.validate_config(self.config)
        self.config['deadline_unix'] += 1
        with self.assertRaisesRegex(ValueError, 'node5_lease_hard_wall'):
            broker.validate_config(self.config)

    def test_post_morning_parent_slot_not_stopped_by_evaluation_boundary(self):
        after_cut = broker.MORNING_CUT_UNIX+60
        self.launch['not_before_unix'] = after_cut-1
        self.config['deadline_unix'] = broker.NODE5_HARD_WALL_UNIX
        self.request['lane_deadline_unix'] = after_cut+120
        self.rebind()
        with patch.object(broker.time, 'time', return_value=after_cut):
            result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(self.runner.call_args.args[2], after_cut+90)

    def test_original_earlier_lane_bound_not_extended(self):
        earlier = time.time()+40
        self.config['deadline_unix'] = earlier
        self.rebind()
        result, directory = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(self.runner.call_args.args[2], earlier)
        self.assertEqual(self.config['deadline_unix'], earlier)

    def test_run_cli_bounded_local_stub_no_provider(self):
        directory = self.root/'stub'
        directory.mkdir()
        broker.run_cli(['/bin/sh', '-c', 'printf fixture; printf diagnostic >&2'],
            directory, time.time()+2, 100)
        self.assertEqual((directory/'stdout.json').read_text(), 'fixture')
        self.assertEqual((directory/'stderr.txt').read_text(), 'diagnostic')

    def test_run_cli_kills_only_own_timed_out_stub(self):
        directory = self.root/'timeout_stub'
        directory.mkdir()
        with self.assertRaisesRegex(ValueError, 'provider_timeout'):
            broker.run_cli(['/bin/sh', '-c', 'sleep 5'], directory, time.time()+.1, 100)
        status = json.loads((directory/'CLI_STATUS.json').read_text())
        self.assertEqual(status['error']['code'], 'provider_timeout')
        self.assertTrue(status['cleanup_terminated_process'])
        self.assertIsNone(status['exit_code_before_cleanup'])
        self.assertIsNotNone(status['exit_code_after_cleanup'])
        self.assertFalse(status['retry'])

    def test_cli_exit_and_first_byte_diagnostics_no_extra_attempt(self):
        for exit_code in (0, 7):
            directory = self.root/('exit_stub_'+str(exit_code))
            directory.mkdir()
            argv = ['/bin/sh', '-c', 'printf metadata; printf diagnostic >&2; exit '+str(exit_code)]
            if exit_code:
                with self.assertRaisesRegex(ValueError, 'provider_exit_failure'):
                    broker.run_cli(argv, directory, time.time()+5, 100)
            else:
                broker.run_cli(argv, directory, time.time()+5, 100)
            status = json.loads((directory/'CLI_STATUS.json').read_text())
            self.assertEqual(status['exit_code_before_cleanup'], exit_code)
            self.assertEqual(status['exit_code_after_cleanup'], exit_code)
            self.assertEqual(status['attempts'], 1)
            self.assertFalse(status['cleanup_terminated_process'])
            self.assertIsNotNone(status['first_byte_unix']['stdout'])
            self.assertIsNotNone(status['first_byte_unix']['stderr'])
            self.assertEqual(status['captured_bytes'], {'stdout':8, 'stderr':10})

    def test_run_cli_output_cap(self):
        directory = self.root/'output_stub'
        directory.mkdir()
        with patch.object(broker, 'STDOUT_CAP', 2), self.assertRaisesRegex(ValueError, 'output_bytes_limit'):
            broker.run_cli(['/bin/sh', '-c', 'printf oversized'], directory, time.time()+2, 100)
        self.assertEqual((directory/'stdout.json').stat().st_size, 2)

    def test_captured_auth_exit_metadata_classified_without_retry_or_acceptance(self):
        fixtures = [
            dict(name='F3_C023_E0_PARENT', stdout='',
                stderr='Your organization requires remote managed settings to load, but they could not be loaded. '
                    'Run `claude auth login` to re-authenticate, check your network connection, or contact your administrator.\n',
                expected='provider_required_managed_settings_unavailable'),
            dict(name='F4_P0041', stderr='', stdout=json.dumps(dict(type='result', subtype='success',
                is_error=True, num_turns=1, modelUsage={},
                result='Failed to authenticate: OAuth session expired and could not be refreshed')),
                expected='provider_oauth_session_unavailable'),
        ]
        for fixture in fixtures:
            with self.subTest(fixture=fixture['name']):
                directory = self.root/fixture['name']
                directory.mkdir()
                argv = [sys.executable, '-c',
                    'import sys; sys.stdout.write(sys.argv[1]); sys.stderr.write(sys.argv[2]); sys.exit(1)',
                    fixture['stdout'], fixture['stderr']]
                with self.assertRaisesRegex(ValueError, fixture['expected']):
                    broker.run_cli(argv, directory, time.time()+5, 100)
                status = json.loads((directory/'CLI_STATUS.json').read_text())
                self.assertEqual(status['exit_code_after_cleanup'], 1)
                self.assertEqual(status['error']['code'], fixture['expected'])
                self.assertEqual(status['attempts'], 1)
                self.assertFalse(status['retry'])
                self.assertFalse(status['cleanup_terminated_process'])
                self.assertEqual((directory/'stdout.json').read_text(), fixture['stdout'])
                self.assertEqual((directory/'stderr.txt').read_text(), fixture['stderr'])

    def test_auth_words_in_nonerror_envelope_not_auth_classification(self):
        directory = self.root/'nonerror'
        directory.mkdir()
        (directory/'stderr.txt').write_text('')
        (directory/'stdout.json').write_text(json.dumps(dict(is_error=False,
            result='Failed to authenticate: OAuth session expired and could not be refreshed')))
        self.assertEqual(broker.cli_exit_failure_code(directory), 'provider_exit_failure')

    def test_long_guidance_never_cropped(self):
        reply = dict(self.reply, guidance='word '*201)
        for family in broker.FAMILIES.values():
            with self.subTest(family=family), self.assertRaisesRegex(ValueError, 'no_cropping'):
                broker.adapt_plan(reply, family, 'TRAIN_1')

    def test_family_word_limits_are_explicit_in_actual_system(self):
        for branch, family in broker.FAMILIES.items():
            with self.subTest(family=family):
                config = dict(self.config, branch=branch, family=family)
                transcript = dict(self.request['payload'], game=family)
                system, prompt_bytes, binding = broker.build_system(
                    transcript, config, self.prompts, self.principles)
                limit = 90 if family in ('route', 'grid') else 200
                self.assertIn(f'at most {limit} whitespace-separated words', system)
                self.assertEqual(prompt_bytes, (self.prompts/(branch+'.md')).read_bytes())
                self.assertIn(self.principles.read_text(), system)
                contract = broker.output_transport_contract(family)
                self.assertTrue(contract.startswith(broker.SYSTEM_CONTRACT))
                self.assertEqual(binding['transport_contract_sha256'],
                    broker.hashlib.sha256(contract.encode()).hexdigest())
                if family in ('math', 'code'):
                    self.assertIn('at most 16000 characters', system)
                if family == 'code':
                    self.assertIn('no code fences, backticks', system)

    def test_transport_limits_match_unchanged_validator_boundaries(self):
        for family in broker.FAMILIES.values():
            with self.subTest(family=family):
                limit = 90 if family in ('route', 'grid') else 200
                guidance = ' '.join(['notice'] * limit)
                plan, unused = broker.adapt_plan(dict(self.reply, guidance=guidance), family, 'TRAIN_1')
                self.assertEqual(plan.get('guidance', plan.get('message')), guidance)
                oversized = guidance + ' notice'
                with self.assertRaisesRegex(ValueError, 'lane_guidance_limit_no_cropping'):
                    broker.adapt_plan(dict(self.reply, guidance=oversized), family, 'TRAIN_1')

    def test_serialization_contract_present_without_head_or_prompt_files(self):
        for branch, family in broker.FAMILIES.items():
            for missing_prompt in (False, True):
                with self.subTest(branch=branch, missing_prompt=missing_prompt):
                    prompt_root = self.root/'absent' if missing_prompt else self.prompts
                    system, unused, binding = broker.build_system(self.request['payload'],
                        dict(self.config, branch=branch, family=family), prompt_root, self.principles)
                    contract = broker.output_transport_contract(family)
                    self.assertIn('[a-zA-Z0-9 _-]+', system)
                    self.assertIn('1 through 80 characters', system)
                    self.assertIn('uppercase string "ADD", "STOP", or "SHIFT"', system)
                    self.assertIn(contract + '\n\nTRAIN TRANSCRIPT:', system)
                    self.assertEqual(binding['fallback_used'], missing_prompt)

    def test_serialization_contract_follows_async_head_note(self):
        fields = dict(self.head_fields, NEXT_GUIDANCE='Notice actual uncertainty.')
        prompt = broker.render_parent_prompt(fields)
        (self.prompts/'F1.md').write_text(prompt)
        with patch.object(broker, 'head_binding', return_value=dict(
                status='BOUND_REQUESTED_SETTINGS', fields=fields,
                reflection_applied_by_broker=False, settings_file_sha256='a'*64)):
            system, unused, binding = broker.build_system(self.request['payload'],
                self.config, self.prompts, self.principles)
        self.assertLess(system.index('ASYNCHRONOUS HEAD NEXT_GUIDANCE:'),
            system.index(broker.output_transport_contract('route')))
        self.assertIn('Notice actual uncertainty.', system)

    def test_explicit_class_syntax_preserves_validator_not_normalization(self):
        for label in (None, 'check-as-falsifiable', 'A_z 09', 'a'*80):
            plan, metadata = broker.adapt_plan(dict(self.reply, intervention_class=label),
                'math', 'TRAIN_1')
            self.assertEqual(metadata['intervention_class'], label)
        for label in ('check-as-falsifiable / expectation-before-compute', 'a'*81,
                'check:now', 'révision', ''):
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'parent_tag_class'):
                broker.adapt_plan(dict(self.reply, intervention_class=label), 'math', 'TRAIN_1')

    def test_observed_overflow_lengths_remain_rejected(self):
        for family, words in (('code', 203), ('code', 206), ('grid', 93)):
            reply = dict(self.reply, guidance=' '.join(['notice']*words))
            with self.subTest(family=family, words=words), self.assertRaisesRegex(
                    ValueError, 'lane_guidance_limit_no_cropping'):
                broker.adapt_plan(reply, family, 'TRAIN_1')
            self.assertEqual(len(reply['guidance'].split()), words)

    def test_model_alias_not_fabricated(self):
        envelope = self.envelope()
        envelope['modelUsage'] = {'another-model': {}}
        with self.assertRaisesRegex(ValueError, 'actual_fable_model'):
            broker.parse_output(json.dumps(envelope), 'route', 'TRAIN_1')

    def test_captured_success_two_turn_metadata_with_synthetic_plan(self):
        capture = dict(
            stdout_path='/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/parent_transcripts/P0026/stdout.json',
            stdout_sha256='1c558efff246abb85d60c975b03e36d2cc3efd8eabe9f0b5de843f7cc0c58c67',
            request_sha256='c644725720416c8b49b3129d4916d0cec0682f531fc7167dcd2e8e582fac1159',
            metadata=dict(type='result', subtype='success', is_error=False, num_turns=2,
                duration_ms=94242, duration_api_ms=94902, total_cost_usd=0.45120874999999994,
                modelUsage={
                    'claude-haiku-4-5-20251001': dict(inputTokens=905, outputTokens=14,
                        cacheReadInputTokens=0, cacheCreationInputTokens=0,
                        webSearchRequests=0, costUSD=0.000975, contextWindow=200000,
                        maxOutputTokens=32000, thinkingTokens=0,
                        canonicalModel='claude-haiku-4-5', provider='firstParty', costBasis='list'),
                    'claude-fable-5-1': dict(inputTokens=4, outputTokens=6816,
                        cacheReadInputTokens=4535, cacheCreationInputTokens=5413,
                        webSearchRequests=0, costUSD=0.45023374999999993,
                        contextWindow=1000000, maxOutputTokens=64000, thinkingTokens=6446,
                        canonicalModel='claude-fable-5-1', provider='firstParty', costBasis='list')}))
        envelope = dict(capture['metadata'], result=json.dumps(self.reply))
        result = broker.parse_output(json.dumps(envelope), 'grid', 'TRAIN_1')
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['actual_model'], broker.MODEL)
        self.assertEqual(result['usage']['reported_num_turns'], 2)
        self.assertEqual(result['usage']['model_usage'], capture['metadata']['modelUsage'])
        argv = broker.command('SYNTHETIC TEST SYSTEM', 2, 'high')
        self.assertEqual(argv[argv.index('--max-turns') + 1], '1')
        self.assertEqual(argv[argv.index('--tools') + 1], '')

    def test_reported_turns_are_telemetry_not_cli_turn_limit(self):
        for turns in (1, 2, 3):
            with self.subTest(turns=turns):
                envelope = dict(self.envelope(), num_turns=turns)
                result = broker.parse_output(json.dumps(envelope), 'route', 'TRAIN_1')
                self.assertEqual(result['usage']['reported_num_turns'], turns)
        envelope = dict(self.envelope('[SILENT]'), num_turns=2)
        self.assertEqual(broker.parse_output(json.dumps(envelope), 'route', 'TRAIN_1')['status'],
            'SILENT')

    def test_provider_error_and_invalid_turn_metadata_refused(self):
        for patch_values in ({'is_error': True}, {'subtype': 'error_max_budget_usd'},
                {'subtype': 'error_max_turns', 'num_turns': 2},
                {'num_turns': 0}, {'num_turns': -1}, {'num_turns': 2.0},
                {'num_turns': '2'}, {'num_turns': None}, {'num_turns': True},
                {'modelUsage': {}}, {'num_turns': 2, 'modelUsage': {'another-model': {}}},
                {'num_turns': 2, 'result': None}, {'num_turns': 2, 'result': ''}):
            with self.subTest(patch_values=patch_values), self.assertRaises(ValueError):
                broker.parse_output(json.dumps(dict(self.envelope(), **patch_values)), 'route', 'TRAIN_1')

    def test_high_600_branch_local_dispatch_accepts_reported_two_turns(self):
        self.config.update(parent_effort='high', provider_lock_scope='branch',
            queue_transport='node_local', deadline_unix=time.time()+1200)
        self.request['lane_deadline_unix'] = time.time()+600
        self.rebind()

        def runner(argv, directory, cutoff, output_cap):
            (directory/'stdout.json').write_text(json.dumps(dict(self.envelope(), num_turns=2)))

        self.runner.side_effect = runner
        real_provider_lock_path = broker.provider_lock_path
        with patch.object(broker, 'provider_lock_path',
                side_effect=lambda config: self.root/real_provider_lock_path(config).name):
            with (self.root/'orch_l2_evaluator_F2.lock').open('a') as other:
                fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result, directory = self.evaluate(lock_path=None)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['usage']['reported_num_turns'], 2)
        argv = self.runner.call_args.args[0]
        self.assertEqual(argv[argv.index('--effort')+1], 'high')
        self.assertEqual(argv[argv.index('--max-turns')+1], '1')
        self.assertEqual(argv[argv.index('--tools')+1], '')
        self.assertEqual(self.runner.call_args.args[2], self.request['lane_deadline_unix']-30)
        self.assertEqual(result['memory_admission']['provider_lock_scope'], 'branch')

    def test_duplicate_or_nonfinite_json_rejected(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                broker.loads(raw)

    def test_no_raw_directory_inside_repo(self):
        with self.assertRaisesRegex(ValueError, 'bounded_tmp'):
            broker.evaluate(self.request, broker.ROOT/'never-created', time.time()+10,
                config=self.config, launch=self.launch, prompt_root=self.prompts,
                principles_path=self.principles)

    def prepare_queue(self, contents=None):
        root = Path(self.config['remote_root'])
        (root/'parent_queue').mkdir(parents=True)
        (root/'parent_claude').mkdir()
        (root/'parent_queue/cycle1_episode1.request.json').write_text(
            json.dumps(self.request) if contents is None else contents)
        buffer = self.root/'buffer'
        buffer.mkdir()
        return root, buffer

    def test_queue_archive_verified_and_no_retry(self):
        root, buffer = self.prepare_queue()
        real_evaluate = broker.evaluate
        def fake_evaluate(*args, **kwargs):
            return real_evaluate(*args, **kwargs, runner=self.runner,
                lock_path=self.root/'lock', memory=lambda: broker.backend.MIN_AVAILABLE_BYTES)
        with patch.object(broker, 'evaluate', side_effect=fake_evaluate):
            result = broker.process_request(LocalStore(), self.config, self.launch,
                'cycle1_episode1.request.json', buffer, self.prompts, self.principles)
        self.assertEqual(result, 'COMPLETE')
        response = broker.loads((root/'parent_queue/cycle1_episode1.response.json').read_text())
        self.assertTrue(response['transcript_receipt']['all_verified'])
        self.assertEqual(list(buffer.iterdir()), [])
        self.assertEqual(broker.process_request(LocalStore(), self.config, self.launch,
            'cycle1_episode1.request.json', buffer, self.prompts, self.principles), 'EXISTING')
        self.assertEqual(self.runner.call_count, 1)

    def test_existing_claim_no_retry(self):
        root, buffer = self.prepare_queue()
        (root/'parent_claude/cycle1_episode1.claim').mkdir()
        with self.assertRaisesRegex(ValueError, 'existing_claim_no_retry'):
            broker.process_request(LocalStore(), self.config, self.launch,
                'cycle1_episode1.request.json', buffer, self.prompts, self.principles)

    def test_r117_local_transport_queue_archive_and_no_duplicate(self):
        self.config['queue_transport'] = 'node_local'
        self.rebind()
        root, buffer = self.prepare_queue()
        real_evaluate = broker.evaluate
        def fake_evaluate(*args, **kwargs):
            return real_evaluate(*args, **kwargs, runner=self.runner,
                lock_path=self.root/'lock', memory=lambda: broker.backend.MIN_AVAILABLE_BYTES)
        with patch.object(broker, 'evaluate', side_effect=fake_evaluate), \
                patch.object(broker.Store, 'shell', side_effect=AssertionError('SSH forbidden')):
            store = broker.NodeLocalStore(self.root)
            status = broker.process_request(store, self.config, self.launch,
                'cycle1_episode1.request.json', buffer, self.prompts, self.principles)
            self.assertEqual(status, 'COMPLETE')
            response = broker.loads((root/'parent_queue/cycle1_episode1.response.json').read_text())
            self.assertTrue(response['transcript_receipt']['all_verified'])
            self.assertEqual(len(list((root/'parent_claude').glob('*.claim'))), 1)
            self.assertEqual(broker.process_request(store, self.config, self.launch,
                'cycle1_episode1.request.json', buffer, self.prompts, self.principles), 'EXISTING')
        self.assertEqual(self.runner.call_count, 1)
        self.assertEqual(list(buffer.iterdir()), [])

    def test_r117_local_transport_refuses_relative_copy(self):
        with self.assertRaisesRegex(ValueError, 'absolute_local_transport_paths'):
            broker.NodeLocalStore(self.root).copy('relative.json', self.root/'copy.json')

    def test_r117_transport_config_bound(self):
        self.config['queue_transport'] = 'node_local'
        broker.validate_config(self.config)
        with self.assertRaisesRegex(ValueError, 'launch_config_binding'):
            self.evaluate()
        self.config['queue_transport'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'queue_transport'):
            broker.validate_config(self.config)

    def test_malformed_queue_publishes_missing(self):
        root, buffer = self.prepare_queue('{not-json')
        result = broker.process_request(LocalStore(), self.config, self.launch,
            'cycle1_episode1.request.json', buffer, self.prompts, self.principles)
        self.assertEqual(result, 'MISSING')
        self.runner.assert_not_called()
        self.assertTrue((root/'parent_transcripts/cycle1_episode1/MALFORMED_REQUEST.json').exists())

    def test_archival_hash_mismatch_preserves_local_bytes(self):
        source = self.root/'archive_source'
        source.mkdir()
        (source/'raw.json').write_text('original')
        destination = self.root/'archive_dest'
        destination.mkdir()
        (destination/'raw.json').write_text('conflicting')
        with self.assertRaisesRegex(ValueError, 'native_archive_hash_mismatch'):
            broker.archive(LocalStore(), source, destination)
        self.assertEqual((source/'raw.json').read_text(), 'original')
        self.assertEqual((destination/'raw.json').read_text(), 'conflicting')


if __name__ == '__main__':
    unittest.main()
