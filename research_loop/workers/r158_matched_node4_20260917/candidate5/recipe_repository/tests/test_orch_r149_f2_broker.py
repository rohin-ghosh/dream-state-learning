from copy import deepcopy
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r149_f2_broker as broker


def fixture():
    original = broker.read(broker.FROZEN/'CONFIG.json')
    config = deepcopy(original)
    config['train_tasks'].update(R149_TRAIN_C97_E0='a'*64, R149_TRAIN_C97_E1='b'*64)
    config['cohort_sha256'] = 'c'*64
    epoch = dict(counters=dict(broker.COUNTERS, child_token_exposures=42, anchor_token_exposures=21),
        parent_high_water=232, next_cycle=97, observed_unix=100, historical_ids=['old', 'claim_only'],
        no_historical_replay=True)
    binding = dict(schema=broker.SCHEMA, service=str(broker.SERVICE), epoch_document=epoch,
        old_train=dict(path=str(broker.QUEUE.parent/'TRAIN.json'), sha256=original['cohort_sha256']))
    for key, filename in (('prepared', 'PREPARED.json'), ('plan', 'RESUME_PLAN.json'),
            ('epoch', 'EPOCH.json'), ('train', 'TRAIN.json'), ('broker_config', 'BROKER_CONFIG.json')):
        binding[key] = dict(path=str(broker.SERVICE/filename), sha256='d'*64)
    binding['train']['sha256'] = config['cohort_sha256']
    return original, config, binding


class PolicyTests(unittest.TestCase):
    def test_producer_changes_only_train_fields(self):
        original, config, _ = fixture()
        tasks = [dict(id=identifier, question_sha256=value, split='TRAIN')
            for identifier, value in config['train_tasks'].items()]
        training = [tasks[offset:offset+2] for offset in range(0, len(tasks), 2)]
        self.assertEqual(broker.broker_config(original, training, config['cohort_sha256']), config)
        training[-1][0]['split'] = 'HELD'
        with self.assertRaisesRegex(ValueError, 'TRAIN_only'):
            broker.broker_config(original, training, config['cohort_sha256'])

    def test_only_train_extension_allowed(self):
        original, config, _ = fixture()
        broker.validate_delta(original, config)
        for key, value in (('deadline_unix', 1789596121), ('max_parent_calls', 385),
                ('max_budget_usd', 2), ('max_output_tokens', 1024), ('remote_root', '/new'),
                ('fallback_parent_fields', {}), ('source_files', {}), ('excluded_task_ids', []),
                ('parent_model', 'other')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                broker.validate_delta(original, dict(config, **{key: value}))

    def test_old_roster_edit_or_drop_rejected(self):
        original, config, _ = fixture()
        identifier = next(iter(original['train_tasks']))
        config['train_tasks'][identifier] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'exact_old_192'):
            broker.validate_delta(original, config)
        del config['train_tasks'][identifier]
        with self.assertRaises(ValueError):
            broker.validate_delta(original, config)

    def test_no_extension_and_old_hash_rejected(self):
        original, config, _ = fixture()
        for value in (original, dict(config, cohort_sha256=original['cohort_sha256'])):
            with self.assertRaises(ValueError):
                broker.validate_delta(original, value)

    def test_exact_native_binding(self):
        original, config, binding = fixture()
        broker.validate_binding(binding, config, 'd'*64, original)
        for key in ('prepared', 'plan', 'epoch', 'train', 'broker_config'):
            changed = deepcopy(binding)
            changed[key]['path'] = str(broker.ROOT/Path(changed[key]['path']).name)
            with self.subTest(key=key), self.assertRaises(ValueError):
                broker.validate_binding(changed, config, 'd'*64, original)

    def test_no_held_reference(self):
        original, config, binding = fixture()
        for name in ('sealed/TRAIN.json', 'held/TRAIN.json', '../TRAIN.json', 'DEV8.json'):
            changed = deepcopy(binding)
            changed['old_train']['path'] = str(broker.QUEUE/name)
            with self.subTest(name=name), self.assertRaises(ValueError):
                broker.validate_binding(changed, config, 'd'*64, original)

    def test_epoch_baseline_cannot_drift(self):
        _, _, binding = fixture()
        for key, value in (('next_cycle', 96), ('parent_high_water', 231),
                ('observed_unix', float('nan')), ('observed_unix', 0),
                ('historical_ids', ['old', 'old']), ('no_historical_replay', False)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                broker.validate_epoch(dict(binding['epoch_document'], **{key: value}))
        for key in broker.COUNTERS:
            changed = deepcopy(binding['epoch_document'])
            changed['counters'][key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                broker.validate_epoch(changed)

    def test_data_runtime_not_tmp_or_frozen(self):
        for path in ('/tmp/r149/MANIFEST.json', broker.FROZEN/'new/MANIFEST.json'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                broker.data_stage(path)
        self.assertEqual(broker.data_stage(broker.DATA_ROOT/'r149_unique/MANIFEST.json'),
            (broker.DATA_ROOT/'r149_unique/MANIFEST.json').resolve())


class FrozenIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        broker.frozen_metadata()
        cls.active, cls.helper, cls.prior = broker.frozen_imports()

    def test_config_validated_by_actual_frozen_policy(self):
        _, config, _ = fixture()
        self.active.base.validate_config(config)

    def test_loaded_modules_not_live_repository(self):
        self.assertTrue(Path(self.active.__file__).is_relative_to(broker.FROZEN/'source'))
        self.assertEqual(sys.modules['gpu.orch_r149_f2_broker'], broker)
        self.assertEqual(self.active.delivery.STRONG, broker.MODEL)

    def test_exact_existing_eligibility_reused(self):
        _, _, binding = fixture()
        epoch = binding['epoch_document']
        row = dict(id='R121_C000097_E0_experience', response=False, partial=False, claim=False,
            delivered=False, reservation=dict(first=233, count=1, kind='parent', reserved_unix=101,
                metadata=dict(id='R121_C000097_E0_experience')))
        self.assertTrue(self.prior.eligible(row, epoch))
        for key in ('response', 'partial', 'claim', 'delivered'):
            self.assertFalse(self.prior.eligible(dict(row, **{key: True}), epoch))
        self.assertFalse(self.prior.eligible(row, dict(epoch, historical_ids=[row['id']])))
        for key, value in (('first', 232), ('reserved_unix', 100)):
            changed = deepcopy(row)
            changed['reservation'][key] = value
            self.assertFalse(self.prior.eligible(changed, epoch))
        changed = deepcopy(row)
        changed['id'] = changed['reservation']['metadata']['id'] = 'R121_C000096_E0_experience'
        self.assertFalse(self.prior.eligible(changed, epoch))

    def test_original_helper_accepts_data_packets_without_tmp_alias(self):
        def evaluate(request, directory, deadline):
            shared.require(Path(directory).resolve().is_relative_to('/tmp'), 'bounded_tmp_only')
            return request

        require_mock = Mock(side_effect=broker.require)
        base = SimpleNamespace(require=require_mock)
        function = type(evaluate)(evaluate.__code__, dict(evaluate.__globals__, shared=base))
        active = SimpleNamespace(base=base, low_settings=lambda value: value,
            delivery=SimpleNamespace(astra_evaluate=function))
        packets = broker.DATA_ROOT/'synthetic_r149/packets'
        bound = self.helper.data_evaluator(active, packets)
        self.assertEqual(bound({'TRAIN': True}, packets/'request/call', 1), {'TRAIN': True})
        require_mock.assert_called_once_with(True, 'bounded_data_only')
        with self.assertRaisesRegex(ValueError, 'only_private_data_packets'):
            bound({}, '/tmp/escape', 1)

    def test_stage_check_never_reads_auth_or_uses_remote(self):
        original, config, binding = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, binding_path = root/'input.json', root/'binding.json'
            broker.write(config_path, config)
            binding['broker_config']['sha256'] = broker.sha(config_path)
            broker.write(binding_path, binding)
            manifest = root/'stage/MANIFEST.json'
            with patch.object(broker, 'data_stage', side_effect=lambda path: Path(path).resolve()), \
                    patch.object(broker, 'remote_inventory', side_effect=AssertionError('remote access')), \
                    patch.object(subprocess, 'run', side_effect=AssertionError('subprocess access')):
                result = broker.stage(config_path, binding_path, manifest)
                broker.check(manifest, result['manifest']['sha256'])
                self.assertFalse(result['native_prefix_checked'])
                self.assertFalse(broker.read(root/'stage/MAIN_GO_TEMPLATE.json')['authorized'])
                with self.assertRaises(FileExistsError):
                    broker.stage(config_path, binding_path, manifest)
                (root/'stage/CONFIG.json').write_text('{}')
                with self.assertRaisesRegex(ValueError, 'immutable_local_reference'):
                    broker.check(manifest, result['manifest']['sha256'])

    def test_exact_explicit_approval_and_window(self):
        _, config, _ = fixture()
        launch = dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=True,
            authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference=broker.approval_reference('f'*64),
            config_sha256=broker.digest(config), not_before_unix=0)
        with patch.object(broker, 'read', return_value=launch), patch.object(broker.time, 'time', return_value=100):
            broker.authorize(self.active, config, 'unused', 'f'*64)
        for key, value in (('authorized', False), ('source_reference', 'prefix '+launch['source_reference']),
                ('config_sha256', 'other'), ('not_before_unix', 200)):
            with self.subTest(key=key), patch.object(broker, 'read', return_value=dict(launch, **{key: value})), \
                    patch.object(broker.time, 'time', return_value=100), self.assertRaises(ValueError):
                broker.authorize(self.active, config, 'unused', 'f'*64)
        with patch.object(broker, 'read', return_value=launch), \
                patch.object(broker.time, 'time', return_value=config['deadline_unix']), self.assertRaises(ValueError):
            broker.authorize(self.active, config, 'unused', 'f'*64)

    def test_frozen_claim_cap_includes_old_queue_history(self):
        _, config, _ = fixture()
        for count in (232, 384):
            commands = []

            def shell(command):
                commands.append(command)
                if command.startswith('find '):
                    return SimpleNamespace(stdout=str(count))
                if command.startswith('stat '):
                    raise RuntimeError('stop_before_request_content_or_provider')
                return SimpleNamespace(stdout='')

            store = SimpleNamespace(exists=lambda path: False, shell=shell)
            error = RuntimeError if count == 232 else ValueError
            with self.subTest(count=count), self.assertRaises(error):
                self.active.base.process_request(store, config, {}, 'R121_C000097_E0_experience.request.json',
                    Path('/unused'), Path('/unused'), Path('/unused'))
            self.assertIn(str(broker.QUEUE/'parent_claude'), commands[0])
            self.assertIn('"*.claim"', commands[0])
            self.assertEqual(any(command.startswith('mkdir ') for command in commands), count == 232)
class CustodyTests(unittest.TestCase):
    def state(self):
        _, _, binding = fixture()
        epoch = binding['epoch_document']
        state = dict(boundary=epoch, host_sha256=broker.HOST_SHA, counters=epoch['counters'],
            terminal=False, native_started=False, historical_ids=epoch['historical_ids'],
            unfinished_claims=['claim_only.claim'])
        return state, epoch

    def test_historical_unfinished_claim_excluded_not_replayed(self):
        state, epoch = self.state()
        broker.validate_activation(state, epoch)

    def test_missing_claim_only_history_fails(self):
        state, epoch = self.state()
        changed = dict(epoch, historical_ids=['old'])
        with self.assertRaisesRegex(ValueError, 'every_old_request_and_claim'):
            broker.validate_activation(dict(state, boundary=changed), changed)

    def test_terminal_started_and_counter_race_fail(self):
        state, epoch = self.state()
        for key, value in (('terminal', True), ('native_started', True),
                ('counters', dict(epoch['counters'], parent=233)), ('host_sha256', 'other')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                broker.validate_activation(dict(state, **{key: value}), epoch)

    def test_service_mapping_leaves_claims_and_requests_original(self):
        calls = []

        class BaseStore:
            def __init__(self, repository):
                self.repository = repository

            def exists(self, path):
                calls.append(('exists', path))

            def hash(self, path):
                calls.append(('hash', path))

            def copy(self, source, destination):
                calls.append(('copy', source, destination))

            def shell(self, script, check=True):
                calls.append(('shell', script))

        store = broker.mapped_store(SimpleNamespace(Store=BaseStore))
        self.assertEqual(store.repository, broker.WRAPPER_ROOT)
        old_config = broker.QUEUE/'parent_claude/CONFIG.json'
        store.hash(old_config)
        self.assertEqual(calls[-1], ('hash', broker.SERVICE/'BROKER_CONFIG.json'))
        store.exists(broker.ROOT/'TERMINAL.json')
        self.assertEqual(calls[-1], ('exists', broker.SERVICE/'TERMINAL.json'))
        store.shell('cat '+str(old_config))
        self.assertEqual(calls[-1], ('shell', 'cat '+str(broker.SERVICE/'BROKER_CONFIG.json')))
        store.copy('NODE:'+str(old_config), '/local/config')
        self.assertEqual(calls[-1][1], 'NODE:'+str(broker.SERVICE/'BROKER_CONFIG.json'))
        store.copy('/local/config', 'NODE:'+str(old_config))
        self.assertEqual(calls[-1][2], 'NODE:'+str(broker.SERVICE/'BROKER_CONFIG.json'))
        for path in (broker.QUEUE/'parent_claude/old.claim', broker.QUEUE/'parent_queue/new.request.json',
                broker.ROOT/'parent_pending/old.json', broker.ROOT/'parent_delivered/old.json'):
            store.exists(path)
            self.assertEqual(calls[-1], ('exists', path))

    def test_remote_inventory_program_is_metadata_only_and_reuses_frozen_function(self):
        _, config, binding = fixture()
        store = SimpleNamespace(shell=Mock(return_value=SimpleNamespace(stdout='{}')))
        broker.remote_inventory(store, binding, config)
        command = store.shell.call_args.args[0]
        self.assertTrue(command.startswith('CUDA_VISIBLE_DEVICES= python3 -B -c '))
        self.assertIn('def inventory(root):', command)
        self.assertIn("parent_delivered", command)
        self.assertNotIn('settings_path', command)
        self.assertNotIn('FINAL8', command)
        self.assertNotIn('DEV8', command)

    def test_serve_uses_only_inherited_transport_and_serialized_lock(self):
        source = inspect.getsource(broker.serve)
        self.assertIn('prior.eligible(row, epoch)', source)
        self.assertIn('active.base.process_request.__code__', source)
        self.assertIn('helper.data_evaluator(active, packets)', source)
        self.assertIn('fcntl.LOCK_EX | fcntl.LOCK_NB', source)
        self.assertIn('dir=packets', source)
        self.assertNotIn('symlink', source)
        self.assertNotIn('release_runner_lock', source)
        self.assertLess(source.index('authorize('), source.index('remote_inventory('))
        self.assertLess(source.index('validate_activation('), source.index("store.shell('mkdir '"))


class NativeProbeTests(unittest.TestCase):
    def test_prefix_and_metadata_gates_without_remote_or_held_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = root/'service'
            service.mkdir()
            old = [[dict(id=f'C{cycle}_E{episode}', split='TRAIN', question_sha256='a'*64)
                for episode in (0, 1)] for cycle in range(1, 97)]
            training = old+[[dict(id=f'C{cycle}_E{episode}', split='TRAIN', question_sha256='b'*64)
                for episode in (0, 1)] for cycle in range(97, 193)]
            broker.write(root/'TRAIN.json', old)
            broker.write(service/'TRAIN.json', training)
            config = dict(train_tasks={task['id']: task['question_sha256'] for group in training for task in group})
            broker.write(service/'BROKER_CONFIG.json', config)
            broker.write(service/'EPOCH.json', {'epoch': True})
            broker.write(root/'PLAN.json', dict(train=broker.ref(root/'TRAIN.json')))
            broker.write(service/'RESUME_PLAN.json', dict(train=broker.ref(service/'TRAIN.json')))
            broker.write(service/'source.json', {})
            broker.write(service/'tests.json', dict(passed=True))
            broker.write(service/'COHORT.json', dict(passed=False, status='PENDING_INDEPENDENT_CLEARANCE'))
            clearance = dict(passed=True, complete_exclusion_coverage=True, exact_prefix=True,
                train_sha256=broker.sha(service/'TRAIN.json'), original_train_sha256=broker.sha(root/'TRAIN.json'),
                manifest_sha256=broker.sha(service/'COHORT.json'), task_id_collisions=0, question_hash_collisions=0,
                checked_new_task_count=192, excluded_id_count=5846, excluded_question_hash_count=5838,
                exclusion_sources_sha256={key: 'e'*64 for key in ('original_train', 'dev', 'final', 'inherited_registry')})
            broker.write(service/'COLLISION_CLEARANCE.json', clearance)
            prepared = dict(plan=broker.ref(service/'RESUME_PLAN.json'), epoch=broker.ref(service/'EPOCH.json'),
                original_plan=broker.ref(root/'PLAN.json'), source=broker.ref(service/'source.json'),
                tests=broker.ref(service/'tests.json'), cohort=broker.ref(service/'COHORT.json'),
                clearance=broker.ref(service/'COLLISION_CLEARANCE.json'))
            broker.write(service/'PREPARED.json', prepared)
            binding = dict(prepared=broker.ref(service/'PREPARED.json'), plan=prepared['plan'], epoch=prepared['epoch'],
                train=broker.ref(service/'TRAIN.json'), old_train=broker.ref(root/'TRAIN.json'),
                broker_config=broker.ref(service/'BROKER_CONFIG.json'), epoch_document={'epoch': True})
            broker.write(root/'TERMINAL.json', {'status': 'FAILED'})
            import socket

            host_sha = broker.hashlib.sha256(socket.gethostname().encode()).hexdigest()
            with patch.object(broker, 'ROOT', root), patch.object(broker, 'SERVICE', service), \
                    patch.object(broker, 'HOST_SHA', host_sha), \
                    patch.object(broker, 'inventory', return_value={'terminal': True}, create=True):
                state = broker.native_probe(binding, config, True)
                self.assertFalse(state['terminal'])
                broker.write(service/'TERMINAL.json', {'status': 'DONE'})
                self.assertTrue(broker.native_probe(binding, config, False)['terminal'])
                altered = deepcopy(training)
                altered[:2] = reversed(altered[:2])
                documents = {str(service/'TRAIN.json'): altered}
                original_read = broker.read
                with patch.object(broker, 'read', side_effect=lambda path: documents.get(str(path), original_read(path))), \
                        self.assertRaisesRegex(ValueError, 'exact_old96_prefix'):
                    broker.native_probe(binding, config, True)


if __name__ == '__main__':
    unittest.main()
