from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r118_grid_shared_run as run


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='r118_grid_test_')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'F4'
        self.root.mkdir()
        self.config = dict(root=str(self.root), physical=3, life_id='F4_FABLE', uuid='test-uuid',
            model_dir='native-model', hard_end_unix=run.grid.END, train_end_unix=run.grid.TRAIN_END)

    def write(self, relative, value):
        path = self.root / relative
        run.shared.write(path, value)
        return path

    def boundary(self):
        rows = []
        for number in (1, 2):
            row = dict(kind='NATIVE', number=number, cycle=5, reserved_unix=1,
                       task_id='TRAIN' + str(number), split='TRAIN', purpose='episode', attached_readout=False)
            rows.append(row)
            self.write(f'calls/N{number:05d}.json', dict(row, status='COMPLETE'))
        rows.append(dict(kind='PARENT', number=1, cycle=5, reserved_unix=1))
        self.write('parent_received/P0001.json', dict(disposition=dict(guidance=None, status='MISSING')))
        (self.root / 'LEDGER.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
        carry = [dict(split='TRAIN', purpose='reflection', attached_readout=False, trace='own reflection')]
        self.write('CARRY.json', carry)
        self.write('cycles/0005/TRAIN_COMPLETE.json', dict(outcomes=[dict(task_id='TRAIN1', split='TRAIN'),
            dict(task_id='TRAIN2', split='TRAIN')], carry=carry))
        complete = self.write('cycles/0005/CYCLE_COMPLETE.json', dict(cycle=5, finished_unix=2))
        return run.capture_boundary(self.root, complete)


class BoundaryTests(Fixture):
    def test_preserves_all_counters_carry_and_next_cycle(self):
        snapshot = self.boundary()
        self.assertEqual(snapshot['next_cycle'], 6)
        self.assertEqual(snapshot['native_charged'], 2)
        self.assertEqual(snapshot['parent_charged'], 1)
        self.assertEqual(snapshot['old_calls_retried'], 0)
        self.assertEqual(snapshot['carry'], run.grid.ref(self.root / 'CARRY.json'))
        self.assertEqual(len(snapshot['captures']), 3)

    def test_later_reservation_rejects_boundary_without_side_effects(self):
        snapshot = self.boundary()
        with (self.root / 'LEDGER.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(kind='NATIVE', number=3, cycle=6, reserved_unix=3)) + '\n')
        with self.assertRaisesRegex(ValueError, 'inflight'):
            run.capture_boundary(self.root, snapshot['complete']['path'])
        self.assertFalse((self.root / 'shared_boundaries').exists())

    def test_unfinished_capture_and_changed_carry_fail_closed(self):
        snapshot = self.boundary()
        path = self.root / 'calls/N00001.json'
        run.shared.write(path, dict(run.shared.read(path), status='STARTED'), replace=True)
        with self.assertRaisesRegex(ValueError, 'completed_native'):
            run.capture_boundary(self.root, snapshot['complete']['path'])
        run.shared.write(path, dict(run.shared.read(path), status='COMPLETE'), replace=True)
        run.shared.write(self.root / 'CARRY.json', [], replace=True)
        with self.assertRaisesRegex(ValueError, 'same_completed_cycle_carry'):
            run.capture_boundary(self.root, snapshot['complete']['path'])

    def test_disjoint_slots_and_absolute_bounds(self):
        self.assertEqual(run.inherited_bounds(self.config)['parent_wait_seconds'], 600)
        other = dict(self.config, physical=7, life_id='F4_ASTRA')
        self.assertEqual(run.inherited_bounds(other)['parent_wait_seconds'], 120)
        self.assertEqual(run.inherited_bounds(other)['max_native_calls'], 1858)
        self.assertEqual(run.inherited_bounds(other)['max_parent_calls'], 298)
        with self.assertRaisesRegex(ValueError, 'grid_pair'):
            run.branch_for(dict(self.config, physical=5))
        with self.assertRaisesRegex(ValueError, 'absolute_deadlines'):
            run.inherited_bounds(dict(self.config, hard_end_unix=run.grid.END + 1))

    def test_exact_wait600_implementation_and_unchanged_A4(self):
        self.assertIs(run.F4SharedLife.ask, run.wait600.WaitLife.ask)
        self.assertIs(run.life_class('A4'), run.client.SharedLife)
        self.assertIs(run.life_class('A4').ask, run.grid.Life.ask)
        parent = dict(lane_deadline_unix=1120, identifier='P0001')
        with patch.object(run.grid.policy, 'queue_request', return_value=parent):
            result = run.wait600.queue_request('P0001', 'F4_FABLE', 6, 0, 'experience', {}, [], 'source', 1000)
        self.assertEqual(result['lane_deadline_unix'], 1600)

    def test_original_roster_cursor_and_budget_reserve(self):
        roster = [dict(id=str(index), split='TRAIN') for index in range(16)]
        self.assertEqual([task['id'] for task in run.cycle_tasks(roster, 6)], ['5', '13'])
        self.assertEqual([task['id'] for task in run.cycle_tasks(roster, 9)], ['0', '8'])
        self.boundary()
        self.assertTrue(run.can_train(self.root))
        with patch.object(run, 'read_ledger', return_value=[dict(kind='NATIVE')] * 1739):
            self.assertFalse(run.can_train(self.root))


class FakeDecoder(run.client.SharedDecoder):
    def __init__(self, session):
        identity = run.client.native.bridge.AdapterIdentity.from_document(session['adapter'])
        binding = run.client.native.bridge.StageBinding(session['branch'], run.client.native.bridge.ARMS[0],
            session['generation'], 'collection', identity, True, False, session['config_sha256'])
        self.loaded = SimpleNamespace(optimizer=None, binding=binding, engine=SimpleNamespace(),
                                      verify_unchanged=lambda: identity)

    def batch(self, messages, cap):
        return [dict(raw='actual child continuation', token_ids=[7, 8, 9], prompt_tokens=2,
                     terminal=True, truncated=False) for message in messages]


class CollectionTests(Fixture):
    def session(self):
        folder = Path(self.temporary.name) / 'checkpoint'
        adapter = folder / 'adapter'
        adapter.mkdir(parents=True)
        run.shared.write(adapter / 'adapter_config.json', dict(test=True))
        identity = run.client.native.bridge.AdapterIdentity(str(adapter), run.shared.digest('adapter'),
            run.grid.policy.game.BASE_SHA, (('adapter_config.json', run.shared.sha(adapter / 'adapter_config.json')),))
        optimizer = folder / 'optimizer.pt'
        optimizer.write_bytes(b'owner-only test checkpoint')
        path = folder / 'CHECKPOINT.json'
        run.shared.write(path, dict(complete=True, adapter=identity.document(),
            optimizer_rng_sha256=run.shared.sha(optimizer), source_process=['old-boot', 1, 2]))
        checkpoint = dict(path=str(path), path_sha256=run.shared.sha(path),
                          optimizer_path=str(optimizer), optimizer_path_sha256=run.shared.sha(optimizer))
        common = Path(self.temporary.name) / 'common'
        specs = {branch: dict(root=str(self.root if branch == 'F4' else Path(self.temporary.name) / branch),
            train_ids=[branch + '_one', branch + '_two']) for branch in run.shared.BRANCHES}
        run.shared.initialize(common, specs, checkpoint, excluded_ids=['held'],
                              prior_metrics={name: 0 for name in run.shared.METRICS}, initial_history={})
        return run.client.prepare(common, 'F4', config_sha256=run.shared.sha(common / 'CONFIG.json'))

    def test_real_client_two_sequential_train_open_reflection_submission(self):
        session = self.session()
        engine = FakeDecoder(session)
        life = run.F4SharedLife(self.root, engine, self.config, 6, session)
        life.ask = Mock(return_value=dict(disposition=dict(guidance=None)))
        tasks = [dict(id='F4_one', split='TRAIN'), dict(id='F4_two', split='TRAIN')]
        seen = []
        def episode(active, task, ordinal, memory):
            seen.append(task['id'])
            result = active.generate(task, 'episode', [dict(role='user', content='Visible grid observation')], 384)
            return dict(task_id=task['id'], split='TRAIN', final_state={}, last=result['reference'])
        def opened(active, task, state, ordinal, **options):
            self.assertTrue(options['parent'])
            self.assertFalse(options['attached_readout'])
            return active.generate(task, 'open_turn', [dict(role='user', content='Optional TRAIN inspection')], 384)['reference']
        with patch.object(run.grid.policy.game, 'initial', return_value={}), patch.object(
                run.grid.policy, 'public_observation', return_value={'visible': 'grid'}), patch.object(
                run.grid, 'episode', side_effect=episode), patch.object(run.grid, 'open_opportunity', side_effect=opened):
            result = run.client.run_cycle_and_submit(life, tasks, [])
        self.assertEqual(seen, ['F4_one', 'F4_two'])
        self.assertEqual(result['status'], 'SUBMITTED_WAITING_SHARED_GENERATION')
        self.assertEqual(result['branch_optimizer_steps'], 0)
        submitted = run.shared.read(Path(session['shared_root']) / 'generation_000000/F4.json')
        self.assertEqual(submitted['episode_ids'], ['F4_one', 'F4_two'])
        self.assertEqual(len(submitted['rows']), 6)
        self.assertEqual(run.shared.read(Path(session['shared_root']) / 'STATE.json')['generation'], 0)
        self.assertEqual(run.shared.barrier_status(session['shared_root'])['missing'], ['F1', 'F2', 'F3', 'A1', 'A2', 'A3', 'A4'])
        self.assertIsNone(engine.loaded.optimizer)
        self.assertEqual(run.shared.read(self.root / 'CARRY.json')[0]['purpose'], 'reflection')

    def test_readout_has_no_parent_or_training_route(self):
        session = self.session()
        life = run.ReadoutLife(self.root, FakeDecoder(session), self.config, 6, session)
        with self.assertRaisesRegex(ValueError, 'parent_absent'):
            life.ask({}, 0, 'experience')
        with self.assertRaisesRegex(ValueError, 'never_train'):
            life.calls([dict(id='F4_one', split='TRAIN')], 'episode', [[dict(role='user', content='x')]], 384)
        life.calls([dict(id='F4_one', split='TRAIN')], 'open_readout',
                   [[dict(role='user', content='Fresh readout environment')]], 384, attached_readout=True)
        self.assertFalse((self.root / 'calls').exists())
        path = next((self.root / 'readout_calls').glob('*.json'))
        self.assertTrue(run.shared.read(path)['attached_readout'])
        with self.assertRaisesRegex(ValueError, 'only_native_train_directory'):
            run.client.canonical_row(path, session, 6, ['F4_one', 'F4_two'])


class LifecycleTests(Fixture):
    def session(self, generation=0):
        return dict(branch='F4', branch_root=str(self.root), shared_root='common', generation=generation,
                    checkpoint_sha256='checkpoint' + str(generation), config_sha256='config', adapter={})

    def test_actual_resident_cycle_orders_submit_wait_reload_then_fresh_dev(self):
        self.write('TRAIN.json', [dict(id=str(index), split='TRAIN') for index in range(16)])
        self.write('CARRY.json', ['existing own reflection'])
        boundary = dict(next_cycle=6, completed_cycle=5)
        activation = dict(shared_learner=dict(root='common', branch='F4', config_sha256='config'))
        session, successor = self.session(), self.session(1)
        order = []
        engine = Mock()
        factory = Mock(return_value='life')
        def submitted(life, tasks, memory):
            order.append('submit')
            self.assertEqual([task['id'] for task in tasks], ['5', '13'])
            self.assertEqual(memory, ['existing own reflection'])
            return dict(status='SUBMITTED')
        def readout(root, cycle, scope, state):
            order.append(scope)
            self.assertEqual(state['generation'], 1)
        with patch.object(run, 'validate', return_value=(self.config, activation, boundary)), patch.object(
                run, 'can_train', side_effect=[True, False]), patch.object(run.client, 'prepare', return_value=session), patch.object(
                run.client, 'load_shared', return_value=engine), patch.object(run, 'life_class', return_value=factory), patch.object(
                run.client, 'run_cycle_and_submit', side_effect=submitted), patch.object(run.client, 'wait_for_next',
                side_effect=lambda *args, **kwargs: order.append('barrier') or successor), patch.object(
                run.client, 'reload_shared', side_effect=lambda *args: order.append('inplace_reload') or {}), patch.object(
                run, 'spawn_readout', side_effect=readout), patch.object(run.grid.policy, 'FINAL_UNIX', 0), patch.object(
                run.client.native, 'process_identity', return_value=('boot', 7, 8)):
            run.resident(self.root)
        self.assertEqual(order, ['submit', 'barrier', 'inplace_reload', 'dev', 'final_morning'])
        self.assertEqual(run.shared.read(self.root / 'SHARED_COMPLETE.json')['completed_cycle'], 6)
        engine.verify_base.assert_called_once()
        engine.torch.cuda.empty_cache.assert_called_once()

    def test_zero_available_training_budget_does_not_reset_or_repeat_baselines(self):
        self.write('TRAIN.json', [dict(id=str(index), split='TRAIN') for index in range(16)])
        engine = Mock()
        activation = dict(shared_learner=dict(root='common', branch='F4', config_sha256='config'))
        with patch.object(run, 'validate', return_value=(self.config, activation, dict(next_cycle=6, completed_cycle=5))), patch.object(
                run, 'can_train', return_value=False), patch.object(run.client, 'prepare', return_value=self.session()), patch.object(
                run.client, 'load_shared', return_value=engine), patch.object(run, 'spawn_readout') as readout, patch.object(
                run.grid.policy, 'FINAL_UNIX', 0), patch.object(run.client.native, 'process_identity', return_value=('boot', 7, 8)):
            run.resident(self.root)
        readout.assert_called_once_with(self.root, 5, 'final_morning', self.session())
        self.assertFalse((self.root / 'CARRY.json').exists())

    def test_spawn_is_fresh_python_process_without_parent_arguments(self):
        session = self.session()
        with patch.object(run.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as spawn, patch.object(
                run.client.native, 'process_identity', return_value=('boot', 3, 4)):
            run.spawn_readout(self.root, 6, 'dev', session)
        arguments = spawn.call_args.args[0]
        self.assertEqual(arguments[:5], [run.grid.PYTHON, '-B', '-m', run.MODULE, 'readout'])
        self.assertNotIn('--parent', arguments)
        self.assertGreater(spawn.call_args.kwargs['timeout'], 0)
        binding = run.shared.read(self.root / 'shared_readout_bindings/0006_dev.json')
        self.assertEqual(binding['predecessor_processes'], [['boot', 3, 4]])
        self.assertFalse(binding['carry_access'])

    def test_guard_never_stops_predecessors_and_uses_separate_terminal(self):
        self.write('SHARED_CLIENT_READY.json', {})
        self.write('SHARED_ACTIVATION.json', {})
        self.write('TERMINAL.json', dict(historical=True))
        prior = (self.root / 'TERMINAL.json').read_bytes()
        child = Mock(pid=7)
        child.wait.return_value = 0
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''), patch.object(run, 'validate', return_value=(
                self.config, dict(boundary={}), {})), patch.object(run, 'scan', return_value=dict(clear=True,
                scanner_euid=0, blocking_reasons=[])), patch.object(run.subprocess, 'Popen', return_value=child) as launch:
            run.guard(self.root)
        self.assertEqual((self.root / 'TERMINAL.json').read_bytes(), prior)
        self.assertEqual(run.shared.read(self.root / 'SHARED_TERMINAL.json')['status'], 'COMPLETE')
        self.assertEqual(launch.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], self.config['uuid'])
        self.assertIn('timeout', launch.call_args.args[0])
        child.terminate.assert_not_called()
        child.kill.assert_not_called()


if __name__ == '__main__':
    unittest.main()
