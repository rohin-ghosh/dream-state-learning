import copy
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

import semantic_judge as judge


protocol = judge.protocol


class SemanticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.packet = dict(opaque_id='a' * 48, messages=protocol.messages(
            dict(system_prompt='Help.', birth_prompt='Begin.'), protocol.PROBES[0]),
            response='SYNTHETIC PRIVATE TEXT', truncated=True, terminal=False,
            TRAIN_fingerprint={name: dict(anchors=[['specific', 'test']], training_grams=[['prior', 'work']])
                               for name in ('object', 'behavior')}, instruction='Untrusted evidence')
        self.value = dict(opaque_id=self.packet['opaque_id'], identity='AMBIGUOUS',
            continuation='INSUFFICIENT_VISIBLE_EVIDENCE', cueing='AMBIGUOUS',
            supporting_spans=[dict(source='response', quote='SYNTHETIC')], contradicting_spans=[],
            uncertain_features=['Not enough evidence'], attention=dict(choice='UNCERTAIN', what='UNCERTAIN',
                how='UNCERTAIN', how_much='UNCERTAIN', grounding='UNCERTAIN'))
        self.response = dict(speak=True, message='Private annotation recorded.', rationale=json.dumps(self.value))

    def test_one_packet_only_no_history_or_condition_join(self):
        payload = json.loads(judge.request(self.packet, 'FROZEN RUBRIC'))
        self.assertEqual(set(payload), {'packet', 'frozen_rubric'})
        self.assertNotIn('mapping', json.dumps(payload))
        self.assertNotIn('LORA_ON', json.dumps(payload))
        self.assertEqual(payload['packet']['response'], self.packet['response'])

    def test_condition_or_lexical_fields_refused_before_provider(self):
        for field in ('condition', 'mapping', 'lexical_flags', 'history', 'other_answers'):
            with self.subTest(field=field):
                packet = dict(self.packet, **{field: 'forbidden'})
                provider = Mock()
                with self.assertRaises(ValueError):
                    judge.judge_one(packet, 'rubric', self.root, time.time() + 5, provider, {})
                provider.assert_not_called()

    def test_existing_schema_high_effort_model_and_configuration_recorded(self):
        provider = Mock(return_value=(self.response, judge.MODEL, {'output_tokens': 100}))
        result = judge.judge_one(self.packet, 'rubric', self.root, time.time() + 5, provider, {'sha256': 'config'})
        self.assertEqual(result['judge_model'], judge.MODEL)
        self.assertEqual(result['effort'], 'high')
        self.assertEqual(result['configuration'], {'sha256': 'config'})
        self.assertEqual(provider.call_args.kwargs['instruction'], judge.INSTRUCTION)
        self.assertEqual(provider.call_args.kwargs['reasoning_effort'], 'high')
        self.assertEqual(provider.call_count, 1)

    def test_wrong_model_or_failure_never_retried(self):
        for returned in ((self.response, 'wrong-model', {}), RuntimeError('private')):
            provider = Mock(side_effect=returned) if isinstance(returned, Exception) else Mock(return_value=returned)
            with self.assertRaises((ValueError, RuntimeError)):
                judge.judge_one(self.packet, 'rubric', self.root, time.time() + 5, provider, {})
            self.assertEqual(provider.call_count, 1)

    def test_strict_call_clock_interrupts_slow_provider(self):
        provider = Mock(side_effect=lambda *args, **kwargs: time.sleep(1))
        with self.assertRaises(TimeoutError):
            judge.judge_one(self.packet, 'rubric', self.root, time.time() + .02, provider, {})
        self.assertEqual(provider.call_count, 1)

    def test_fabricated_spans_and_wrong_opaque_id_refused(self):
        for value in (dict(self.value, opaque_id='b' * 48),
                      dict(self.value, supporting_spans=[dict(source='response', quote='not present')])):
            with self.assertRaises(ValueError):
                judge.annotation(dict(self.response, rationale=json.dumps(value)), self.packet)

    def test_labels_do_not_require_novelty_or_EOS(self):
        value = dict(self.value, identity='SPECIFIC_IDENTITY', continuation='FAITHFUL_RECURRENCE')
        result = judge.annotation(dict(self.response, rationale=json.dumps(value)), self.packet)
        self.assertEqual(result['identity'], 'SPECIFIC_IDENTITY')

    def test_private_remote_payload_changed_pin_refused(self):
        plan = dict(transport=dict(path='/transport'))
        with patch.object(judge.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'changed', b'')):
            with self.assertRaises(ValueError):
                judge.remote_read(plan, dict(path='/packet', sha256='0' * 64))

    def test_unblinding_cannot_read_mapping_before_annotation_freeze(self):
        freeze = protocol.write(self.root / 'invalid.json', dict(status='INCOMPLETE', terminals=[]))
        with patch.object(judge, 'remote_read') as fetch:
            with self.assertRaises(ValueError):
                judge.private_appendix({}, {}, self.root, freeze)
            fetch.assert_not_called()

    def test_changed_annotation_after_freeze_blocks_map_read(self):
        terminals = []
        for index in range(60):
            directory = self.root / str(index)
            directory.mkdir()
            annotation = protocol.write(directory / 'annotation.json', {'frozen': True})
            terminals.append(protocol.write(directory / 'COMPLETE.json', dict(status='COMPLETE', annotation=annotation)))
        freeze = protocol.write(self.root / 'freeze.json', dict(status='ANNOTATIONS_FROZEN_BEFORE_UNBLINDING',
            terminals=terminals, unblinded=False))
        (self.root / '0/annotation.json').write_bytes(b'changed')
        with patch.object(judge, 'remote_read') as fetch:
            with self.assertRaises(ValueError):
                judge.private_appendix({}, {}, self.root, freeze)
            fetch.assert_not_called()

    def test_sixty_charge_once_two_concurrent_failure_retained_metadata_only(self):
        plan_path = self.root / 'plan.json'
        protocol.write(plan_path, {})
        go = self.root / 'go.json'
        protocol.write(go, dict(schema=judge.SCHEMA, status='MAIN_SEMANTIC_EXECUTION_GO', plan=protocol.ref(plan_path),
            calls=60, provider_model=judge.MODEL, max_concurrent=2, no_retries=True))
        plan = dict(private_vm_root=str(self.root / 'private'), source_root=str(self.root), provider_config={},
                    private_remote_root='/private/node2')
        inventory = dict(packets=[dict(path=str(judge.PACKET_ROOT / (f'{index:048x}' + '.json')), sha256='a'*64)
                                  for index in range(60)])
        lock = threading.Lock()
        counts = dict(active=0, peak=0, attempts=0)
        def native(command, **kwargs):
            packet_id = command[command.index('--packet-id') + 1]
            with lock:
                counts['active'] += 1
                counts['peak'] = max(counts['peak'], counts['active'])
                counts['attempts'] += 1
            try:
                time.sleep(.005)
                if int(packet_id, 16) == 0:
                    raise subprocess.TimeoutExpired(command, 155)
                protocol.write(Path(plan['private_vm_root']) / packet_id / 'ANNOTATION.private.json', self.value)
                return subprocess.CompletedProcess(command, 0)
            finally:
                with lock:
                    counts['active'] -= 1
        def upload(plan, name, raw):
            return dict(path='/private/node2/' + name, sha256=protocol.hashlib.sha256(raw).hexdigest())
        def appendix(plan, inventory, root, freeze):
            self.assertEqual(len(protocol.bound(freeze)['terminals']), 60)
            return dict(path='/private/node2/APPENDIX.private.md', sha256='c'*64)
        with patch.object(judge, 'validate', return_value=(plan, inventory)), \
                patch.object(judge.subprocess, 'run', side_effect=native), \
                patch.object(judge, 'remote_upload', side_effect=upload), \
                patch.object(judge, 'private_appendix', side_effect=appendix):
            result = judge.dispatch(plan_path, go)
            with self.assertRaises(FileExistsError):
                judge.dispatch(plan_path, go)
        self.assertEqual(counts['attempts'], 60)
        self.assertLessEqual(counts['peak'], 2)
        self.assertEqual((result['calls_charged'], result['complete_annotations'], result['failed_or_uncertain']), (60, 59, 1))
        self.assertNotIn('SYNTHETIC', json.dumps(result))
        self.assertNotIn('AMBIGUOUS', json.dumps(result))

    def test_no_new_GO_no_private_root_or_call(self):
        plan_path = self.root / 'plan.json'
        protocol.write(plan_path, {})
        go = self.root / 'go.json'
        protocol.write(go, dict(status='PREPARATION_ONLY'))
        with patch.object(judge, 'validate', return_value=({}, {})), patch.object(judge.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                judge.dispatch(plan_path, go)
            run.assert_not_called()

    def test_worker_once_blocks_reentry_before_any_fetch(self):
        packet_id = self.packet['opaque_id']
        plan_path = self.root / 'plan.json'
        protocol.write(plan_path, {})
        go = protocol.write(self.root / 'go.json', dict(schema=judge.SCHEMA, status='MAIN_SEMANTIC_EXECUTION_GO',
            plan=protocol.ref(plan_path), calls=60, provider_model=judge.MODEL, max_concurrent=2, no_retries=True))
        root = self.root / 'private'
        directory = root / packet_id
        directory.mkdir(parents=True)
        started = time.time()
        protocol.write(root / 'ONCE.json', dict(go=go, plan=protocol.ref(plan_path), started_unix=started,
                                              deadline_unix=started+5400))
        reference = dict(path=str(judge.PACKET_ROOT / (packet_id+'.json')), sha256='a'*64)
        protocol.write(directory / 'RESERVED.json', dict(packet=reference, calls_charged=1))
        protocol.write(directory / 'WORKER_ONCE.json', {})
        with patch.object(judge, 'validate', return_value=(dict(private_vm_root=str(root)), dict(packets=[reference]))), \
                patch.object(judge, 'remote_read') as fetch:
            with self.assertRaises(FileExistsError):
                judge.worker(plan_path, packet_id, started+5400)
            fetch.assert_not_called()

    def validation_fixture(self):
        source = self.root / 'source'
        (source / 'gpu').mkdir(parents=True)
        (source / 'semantic_judge.py').write_bytes(Path(judge.__file__).read_bytes())
        for name in ('orch_r167_object_survival_eval.py', 'orch_route_parent_campaign_providers.py'):
            (source / 'gpu' / name).write_bytes(b'CPU fixture only')
        pins = {str(path.relative_to(source)):protocol.sha(path) for path in source.rglob('*.py')}
        config = self.root / '.codex/nvidia-astra.config.toml'
        config.parent.mkdir()
        config.write_text('model="openai/openai/gpt-6-astra"\nmodel_provider="existing"\n'
            '[model_providers.existing]\nwire_api="responses"\n'
            'base_url="https://[REDACTED_HOST]/v1"\nenv_key="NVIDIA_API_KEY"\n')
        transport = protocol.write(self.root / 'transport', b'CPU fixture')
        environment = protocol.write(self.root / 'transport.env', b'CPU fixture')
        gate = protocol.write(self.root / 'CPU.json', dict(status='PASS', provider_calls=0,
            source_pins_sha256=protocol.digest(pins)))
        rubric = dict(path=str(judge.PACKET_ROOT.parent / 'RUBRIC.md'),
            sha256='7b630704b1be85abc56698b816e333f318a66004d419e8c6e474e67edf4b4165')
        inventory = protocol.write(self.root / 'INVENTORY.json', dict(count=60, rubric=rubric,
            mapping=dict(path=str(judge.PACKET_ROOT.parent / 'unblinding/MAP.private.json'), sha256='a'*64),
            packets=[dict(path=str(judge.PACKET_ROOT / (f'{index:048x}'+'.json')),sha256='b'*64) for index in range(60)]))
        plan = dict(schema=judge.SCHEMA, source_pins=pins, source_root=str(source), packet_inventory=inventory,
            rubric=rubric, provider_config=protocol.ref(config), transport=transport, transport_environment=environment,
            model=judge.MODEL, effort='high', max_output_tokens=4096, call_cap=60, packet_count=60,
            timeout_seconds=120, concurrency=2, maximum_wall_seconds=5400,
            private_vm_root='/tmp/orch_r167_semantic_CPU_fixture',
            private_remote_root=str(protocol.CAMPAIGN / 'private_appendices/semantic60_generation_test'),
            visibility='PRIVATE_VM_AND_NODE2_EXCLUDED_FROM_ALL_PARENTS_AND_REPO_READER',CPU_gate=gate)
        path = self.root / 'PLAN.json'
        protocol.write(path, plan)
        return path, plan

    def test_config_budget_and_source_pins_fail_closed(self):
        path, plan = self.validation_fixture()
        with patch.object(Path, 'home', return_value=self.root):
            judge.validate(path)
            for field in ('call_cap', 'max_output_tokens', 'concurrency', 'timeout_seconds', 'maximum_wall_seconds'):
                changed = dict(plan, **{field:plan[field]+1})
                path.write_text(json.dumps(changed))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    judge.validate(path)
            path.write_text(json.dumps(plan))
            (Path(plan['source_root'])/'gpu/orch_route_parent_campaign_providers.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                judge.validate(path)

    def test_frozen_CPU_gate_and_existing_key_required(self):
        path, plan = self.validation_fixture()
        with patch.object(Path, 'home', return_value=self.root), patch.dict(judge.os.environ, {'NVIDIA_API_KEY':''}):
            with self.assertRaises(ValueError):
                judge.validate(path, True)
            gate = Path(plan['CPU_gate']['path'])
            gate.write_text(json.dumps(dict(status='PASS', provider_calls=0, source_pins_sha256='wrong')))
            plan['CPU_gate'] = protocol.ref(gate)
            path.write_text(json.dumps(plan))
            with self.assertRaises(ValueError):
                judge.validate(path)


if __name__ == '__main__':
    unittest.main()
