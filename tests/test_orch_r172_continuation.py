"""Stdlib synthetic contracts only: never Qwen throughput, C2 evidence, or a GPU gate."""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from uuid import UUID

from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from research_loop.workers.rohin172_c2_pilot_20260917.continuation import custody, preflight, runner


class Tokenizer:
    eos_token_id = 2
    pad_token_id = 0
    all_special_ids = [0, 2, 5]

    def apply_chat_template(self, messages, **options):
        assert options['return_dict'] is False
        return [5] + [ord(character) + 10 for message in messages
                      for character in message['role'] + ':' + message['content']]

    def decode(self, tokens, **unused):
        return ''.join(chr(token - 10) for token in tokens)


def fixture(root):
    config = custody.pilot()
    saved = root / 'bound_synthetic_snapshot'
    saved.mkdir()
    for name in ('checkpoint/adapter', 'history', 'workspace/empty', 'workspace/nested'):
        (saved / name).mkdir(parents=True, exist_ok=True)
    write = lambda name, value: custody.write_once(saved / name, value)
    custody.write_once(saved / 'checkpoint/adapter/adapter_config.json', dict(r=8, bias='none'))
    custody.write_once(saved / 'checkpoint/adapter/adapter_model.safetensors', raw=b'CPU fixture not tensor data')
    custody.write_once(saved / 'checkpoint/optimizer_rng.pt', raw=b'CPU fixture not optimizer data')
    custody.write_once(saved / 'workspace/nested/arithmetic.txt', raw=b'fixture only\n', mode=0o640)
    custody.write_once(saved / 'workspace/zero', raw=b'', mode=0o600)
    adapter_files = {path.name: custody.sha(path.read_bytes()) for path in (saved / 'checkpoint/adapter').iterdir()}
    optimizer_sha = custody.sha((saved / 'checkpoint/optimizer_rng.pt').read_bytes())
    original = Path(config['source_life']) / 'checkpoints/sleep_000041'
    commit = dict(schema=custody.native.SCHEMA, base_sha256=custody.native.BASE_SHA256,
        adapter_path=str(original / 'adapter'), adapter_files=adapter_files,
        adapter_state_sha256='a' * 64, optimizer_rng_path=str(original / 'optimizer_rng.pt'),
        checkpoint_sha256=dict(adapter=custody.digest(adapter_files), optimizer=optimizer_sha, rng=optimizer_sha),
        optimizer_steps=4261)
    write('checkpoint/COMMIT.json', commit)
    reference = dict(path=str(original / 'COMMIT.json'), sha256=custody.sha((saved / 'checkpoint/COMMIT.json').read_bytes()))
    plan = dict(base_sha256=custody.native.BASE_SHA256, system_prompt='Synthetic inherited system.',
        birth_prompt='Synthetic inherited birth.', context_limit=16384, new_presentations=16,
        rehearsal_presentations=1, anchor_lambda=0.25, decoder=dict(temperature=0.7, top_p=0.95))
    history = TrainHistory(system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
    parent = TrainEvent(event_id='parent:fixture', actor='parent', text='Synthetic bound Rohin fixture.',
        split='TRAIN', phase='experience', episode_id='fixture', source_id='fixture:parent',
        source_sha256='1' * 64, origin='TRAIN_COLLECTION')
    history.append(parent)
    stream = ContinualStream(history, context_limit=16384, segment_tokens=512, segments_per_sleep=2,
        deadline_unix=14400, model_state_sha256=custody.digest(commit['checkpoint_sha256']))
    for index in range(4):
        text = 'No result yet. My judgment is uncertain. Next, compute one example.' if index == 3 else f'Fixture {index}.'
        event = TrainEvent(event_id=f'child:{index}', actor='child', text=text, split='TRAIN',
            phase='experience', episode_id='fixture', source_id=f'fixture:response:{index}',
            source_sha256=custody.digest(['CPU_FIXTURE_ONLY', index]), origin='TRAIN_COLLECTION')
        history.append(event)
        row = dict(segment=index, split='TRAIN', actor='child', event_id=event.event_id,
            prefix=[dict(role='system', content=plan['system_prompt']), dict(role='user', content=plan['birth_prompt'])],
            target=text, token_ids=[ord(character) + 10 for character in text], append_eos=False,
            prefix_loss=False, target_loss=True, source_sha256=event.source_sha256,
            model_state_sha256=stream.model_state_sha256, terminal=False, truncated=False)
        stream.rows.append(row)
    evidence = TrainEvent(event_id='environment:fixture', actor='environment',
        text='Synthetic tool result: 2 + 2 = 4.', split='TRAIN', phase='feedback', episode_id='fixture',
        source_id='fixture:tool', source_sha256='e' * 64, origin='TRAIN_COLLECTION')
    history.append(evidence)
    write('history/environment.json', dict(event=asdict(evidence), delivered_to_child=True,
        source_kind='actual_environment_execution', CPU_FIXTURE_ONLY=True))
    request = dict(rendered=dict(messages=[dict(role='user', content=parent.text)]))
    write('history/exposure.json', dict(first_response_source_sha256=stream.rows[0]['source_sha256'],
        rohin_inbox_id=config['already_published_guidance']['rohin_inbox_id'], bound_rohin_text=parent.text,
        bound_rohin_text_sha256=custody.sha(parent.text.encode()), request=request,
        request_sha256=custody.digest(request), CPU_FIXTURE_ONLY=True))
    stream.sleep_frontier = len(stream.rows)
    write('stream.json', stream.checkpoint())
    write('plan.json', plan)
    write('anchors.json', dict(CPU_FIXTURE_ONLY=True, not_a_native_anchor_inventory=True))
    write('endpoint.json', dict(first_completed_guided_sleep=True, checkpoint=reference,
        rendered_rohin_inbox_id=config['already_published_guidance']['rohin_inbox_id'],
        committed_response_source_sha256=[row['source_sha256'] for row in stream.rows],
        generated_tokens=sum(len(row['token_ids']) for row in stream.rows), elapsed_seconds=100,
        exposure_receipt='history/exposure.json', CPU_FIXTURE_ONLY=True))
    write('withdrawal.json', dict(adequacy_bound_by='Main', adequate=True, carry_event_id='child:3',
        semantic_spans=dict(zip(custody.FIELDS, ([0, 14], [15, 39], [40, 65]))),
        evidence_event_ids=[evidence.event_id], evidence_receipts={evidence.event_id: 'history/environment.json'},
        CPU_FIXTURE_ONLY=True))
    return dict(schema='R172_MAIN_BOUND_SAVED_BUNDLE_V1', pilot_sha256=custody.PILOT_SHA256,
        source_life=config['source_life'], source_journal_id=config['source_journal_id'], selection_authority='Main',
        first_guided_sleep_bound=True, checkpoint_cycle=41, checkpoint=reference, snapshot_root=str(saved),
        snapshot_complete=True, raw_history_complete=True, workspace_complete=True, inventory=custody.inventory(saved),
        CPU_FIXTURE_ONLY=True)


class Runtime:
    execution_kind = 'CPU_FIXTURE_ONLY'

    def __init__(self, bundle, count=512):
        self.random = random.Random(172)
        self.tokenizer = Tokenizer()
        self.plan = dict(bundle['plan'], hard_end_unix=20000)
        self.steps, self.count = 4261, count
        self.workspace_digest = custody.digest('synthetic_workspace_same')
        self.match = dict(decoder=bundle['plan']['decoder'], rank=8, backend='CPU_FIXTURE_ONLY')
        self.prompts = []

    def capture_rng(self):
        return self.random.getstate()

    def restore_rng(self, state):
        self.random.setstate(state)

    def rng_digest(self, state):
        return custody.digest(state)

    def state(self):
        return dict(adapter_sha256=custody.digest(['adapter', self.steps]),
            optimizer_sha256=custody.digest(['optimizer', self.steps]), optimizer_steps=self.steps,
            rng_sha256=self.rng_digest(self.capture_rng()), base_sha256=custody.native.BASE_SHA256,
            base_frozen=True)

    def generate(self, messages, **kwargs):
        assert kwargs['max_new_tokens'] == 512
        self.prompts.append(messages)
        text = chr(97 + self.random.randrange(26)) * self.count
        return dict(raw=text, token_ids=[ord(character) + 10 for character in text],
                    terminal=False, truncated=self.count == 512)

    def sleep(self, new_rows, old_rows, material, *, updates, record):
        record('TARGET_ELIGIBILITY', material['eligibility'])
        presentations = {}
        if updates:
            for unused_kind, row in material['schedule']:
                self.random.random()
                self.steps += 1
                key = row['source_sha256']
                presentations[key] = presentations.get(key, 0) + 1
        return dict(optimizer_steps=len(material['schedule']) if updates else 0, presentations=presentations)

    def save(self, directory, *, generation_rng):
        result = dict(state=self.state(), generation_rng=generation_rng, CPU_FIXTURE_ONLY=True)
        custody.write_once(directory / 'CPU_STATE.json', result)
        return result


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        scratch = custody.ROOT / 'cpu_scratch'
        scratch.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binding = fixture(self.root)
        self.bundle = custody.load_bundle(self.binding)
        self.pins = custody.source_pins()

    def rewrite(self, name, value):
        path = Path(self.binding['snapshot_root']) / name
        path.chmod(0o600)
        path.write_bytes(custody.encoded(value))
        path.chmod(0o444)
        self.binding['inventory'] = custody.inventory(Path(self.binding['snapshot_root']))

    def run_fixture(self, runtime=None, arm=custody.ARMS[0], **kwargs):
        return runner.run_arm(runtime or Runtime(self.bundle), self.bundle, self.root / arm, arm=arm,
            binding_sha256=custody.digest(self.binding), pins=self.pins, **kwargs)

    def test_exact_pilot_SHA_no_configuration_rewrite(self):
        self.assertEqual(custody.sha(custody.PILOT.read_bytes()), custody.PILOT_SHA256)
        self.assertEqual(custody.pilot()['continuation']['maximum_generated_tokens_per_arm'], 4608)

    def test_stage_exact_bytes_and_disjoint_workspaces_including_empty_files(self):
        binding_path = self.root / 'BINDING.json'
        custody.write_once(binding_path, self.binding)
        staged = self.root / 'staged'
        result = custody.stage(binding_path, custody.sha(binding_path.read_bytes()), staged)
        self.assertFalse(result['tensor_restore_tested'])
        self.assertFalse(result['generation_or_GPU_launch'])
        for name, metadata in self.binding['inventory']['files'].items():
            copies = [staged / arm / 'saved' / name for arm in custody.ARMS]
            self.assertTrue(all(custody.sha(path.read_bytes()) == metadata['sha256'] for path in copies))
            self.assertNotEqual(copies[0].stat().st_ino, copies[1].stat().st_ino)
        workspaces = [custody.materialize_workspace(staged / arm, self.binding) for arm in custody.ARMS]
        self.assertEqual(workspaces[0], workspaces[1])
        self.assertEqual(workspaces[0]['files']['nested/arithmetic.txt']['mode'], 0o640)
        with self.assertRaises(FileExistsError):
            custody.stage(binding_path, custody.sha(binding_path.read_bytes()), staged)

    def test_staging_rejects_unbound_manifest_before_any_copy(self):
        path = self.root / 'BINDING.json'
        custody.write_once(path, self.binding)
        with self.assertRaisesRegex(ValueError, 'explicit_Main_binding'):
            custody.stage(path, '0' * 64, self.root / 'not_created')
        self.assertFalse((self.root / 'not_created').exists())

    def test_no_pre40_source_or_unselected_checkpoint(self):
        self.binding['checkpoint_cycle'] = 40
        with self.assertRaisesRegex(ValueError, 'pre40'):
            custody.validate_binding(self.binding)
        self.binding['checkpoint_cycle'] = 41
        self.binding['first_guided_sleep_bound'] = False
        with self.assertRaisesRegex(ValueError, 'Main_bound_endpoint'):
            custody.validate_binding(self.binding)

    def test_no_live_life_read(self):
        self.binding['snapshot_root'] = self.binding['source_life']
        with self.assertRaisesRegex(ValueError, 'not_live_life'):
            custody.load_bundle(self.binding)

    def test_missing_optimizer_or_complete_history_fails(self):
        del self.binding['inventory']['files']['checkpoint/optimizer_rng.pt']
        with self.assertRaisesRegex(ValueError, 'all_saved_state'):
            custody.validate_binding(self.binding)
        self.binding['inventory']['files']['checkpoint/optimizer_rng.pt'] = {}
        self.binding['raw_history_complete'] = False
        with self.assertRaisesRegex(ValueError, 'complete_snapshot'):
            custody.validate_binding(self.binding)

    def test_extra_file_and_symlink_rejected(self):
        root = Path(self.binding['snapshot_root'])
        (root / 'unlisted').write_text('extra')
        with self.assertRaisesRegex(ValueError, 'exact_complete_snapshot'):
            custody.load_bundle(self.binding)
        (root / 'link').symlink_to(root / 'stream.json')
        with self.assertRaisesRegex(ValueError, 'no_bundle_symlinks'):
            custody.inventory(root)

    def test_no_hardlinks_or_path_traversal(self):
        import os
        root = Path(self.binding['snapshot_root'])
        os.link(root / 'stream.json', root / 'linked')
        with self.assertRaisesRegex(ValueError, 'unshared_regular'):
            custody.inventory(root)
        for name in ('../outside', '/absolute', 'workspace/../outside'):
            with self.assertRaises(ValueError):
                custody.relative(name)

    def test_source_mutation_fails_preserved_staging(self):
        path = self.root / 'BINDING.json'
        custody.write_once(path, self.binding)
        (Path(self.binding['snapshot_root']) / 'workspace/new').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'exact_complete_snapshot'):
            custody.stage(path, custody.sha(path.read_bytes()), self.root / 'failed_stage')
        self.assertTrue((self.root / 'failed_stage/FAILED.json').is_file())

    def test_inadequate_carry_never_invents_or_selects_another(self):
        withdrawal = deepcopy(self.bundle['withdrawal'])
        withdrawal['adequate'] = False
        self.rewrite('withdrawal.json', withdrawal)
        with self.assertRaisesRegex(ValueError, 'inadequate_carry'):
            custody.load_bundle(self.binding)

    def test_missing_carry_semantic_field_fails(self):
        withdrawal = deepcopy(self.bundle['withdrawal'])
        del withdrawal['semantic_spans']['unfinished_next_action']
        self.rewrite('withdrawal.json', withdrawal)
        with self.assertRaisesRegex(ValueError, 'three_carry_fields'):
            custody.load_bundle(self.binding)

    def test_parent_text_is_not_a_carry(self):
        withdrawal = deepcopy(self.bundle['withdrawal'])
        withdrawal['carry_event_id'] = 'parent:fixture'
        self.rewrite('withdrawal.json', withdrawal)
        with self.assertRaisesRegex(ValueError, 'actual_nonempty_child'):
            custody.load_bundle(self.binding)

    def test_offline_score_is_not_delivered_environment_evidence(self):
        name = 'history/environment.json'
        receipt = json.loads((Path(self.binding['snapshot_root']) / name).read_bytes())
        receipt['source_kind'] = 'offline_score'
        self.rewrite(name, receipt)
        with self.assertRaisesRegex(ValueError, 'real_delivered_evidence'):
            custody.load_bundle(self.binding)

    def test_inbox_identity_without_rendered_exposure_fails(self):
        name = 'history/exposure.json'
        exposure = json.loads((Path(self.binding['snapshot_root']) / name).read_bytes())
        exposure['request']['rendered']['messages'] = []
        exposure['request_sha256'] = custody.digest(exposure['request'])
        self.rewrite(name, exposure)
        with self.assertRaisesRegex(ValueError, 'actual_bound_rendered'):
            custody.load_bundle(self.binding)

    def test_endpoint_token_counts_are_actual_not_caps(self):
        endpoint = deepcopy(self.bundle['endpoint'])
        endpoint['generated_tokens'] = 4096
        self.rewrite('endpoint.json', endpoint)
        with self.assertRaisesRegex(ValueError, 'actual_guided_generated_token'):
            custody.load_bundle(self.binding)

    def test_transition_preserves_actual_carry_evidence_omits_parent(self):
        messages, receipt = runner.transition(self.bundle, Tokenizer(), 16384)
        self.assertEqual(messages[2]['content'], self.bundle['carry']['text'])
        self.assertTrue(messages[3]['content'].endswith(self.bundle['evidence'][0]['text']))
        self.assertIn('parent:fixture', receipt['omitted_event_ids'])
        self.assertNotIn('Synthetic bound Rohin', json.dumps(messages))
        self.assertEqual(receipt['transition_count'], 1)

    def test_overflow_does_not_crop_carry_or_add_a_repair_reminder(self):
        bundle = deepcopy(self.bundle)
        bundle['carry']['text'] = 'A' * 2049
        with self.assertRaisesRegex(ValueError, 'over_2048'):
            runner.transition(bundle, Tokenizer(), 16384)
        with self.assertRaisesRegex(ValueError, 'cannot_fit'):
            runner.transition(self.bundle, Tokenizer(), 513)

    def test_fixed_matched_cycles_masking_AND_separate_generation_RNG(self):
        on, off = Runtime(self.bundle), Runtime(self.bundle)
        for runtime, arm in zip((on, off), custody.ARMS):
            result = self.run_fixture(runtime, arm)
            self.assertEqual((result['completed_cycles'], result['generated_tokens']), (3, 4608))
            self.assertEqual(len(runtime.prompts), 9)
            self.assertEqual(len(list((self.root / arm).glob('TRANSITION.json'))), 1)
        self.assertEqual(on.prompts, off.prompts)
        self.assertEqual(on.steps - off.steps, 165)
        on_root, off_root = (self.root / arm for arm in custody.ARMS)
        matched = runner.matched_initial(json.loads((on_root / 'INITIAL.json').read_bytes()),
                                         json.loads((off_root / 'INITIAL.json').read_bytes()))
        self.assertTrue(matched['updates_only_treatment_difference'])
        for path in on_root.glob('*_ACTUAL_OWN_ROW.json'):
            receipt = json.loads(path.read_bytes())['document']
            tokens, labels = receipt['actual_input_ids'], receipt['actual_labels']
            target_count = len(receipt['row']['token_ids'])
            self.assertEqual(labels[:-target_count], [-100] * (len(tokens) - target_count))
            self.assertEqual(labels[-target_count:], tokens[-target_count:])
            self.assertEqual(receipt['history_and_environment_targets'], 0)
        for path in on_root.glob('*_REQUEST.json'):
            document = json.loads(path.read_bytes())['document']
            self.assertFalse(document['new_parent_peer_or_sleep_reminder'])
            self.assertNotIn(custody.pilot()['carry_forward']['invitation'], json.dumps(document['messages']))

    def test_actual_short_outputs_not_4608_or_512_assumption(self):
        result = self.run_fixture(Runtime(self.bundle, count=7))
        self.assertEqual(result['generated_tokens'], 63)

    def test_generation_failure_restores_training_RNG_and_preserves_output(self):
        runtime = Runtime(self.bundle)
        original = runtime.capture_rng()
        def fail(*unused, **kwargs):
            runtime.random.random()
            raise RuntimeError('synthetic generation error')
        runtime.generate = fail
        with self.assertRaisesRegex(RuntimeError, 'synthetic generation'):
            self.run_fixture(runtime)
        self.assertEqual(runtime.capture_rng(), original)
        root = self.root / custody.ARMS[0]
        self.assertTrue((root / 'FAILED.json').exists())
        self.assertTrue((root / 'stopped/CPU_STATE.json').exists())
        self.assertFalse((root / 'RESULT.json').exists())

    def test_fixed_wall_no_extension_or_false_complete(self):
        clock = iter([1000, 1000, 16000])
        with self.assertRaisesRegex(ValueError, 'fixed_wall'):
            self.run_fixture(now=lambda: next(clock))
        failed = json.loads((self.root / custody.ARMS[0] / 'FAILED.json').read_bytes())
        self.assertEqual(failed['completed_cycles'], 0)
        self.assertFalse(failed['auto_extension'])

    def test_native_entry_explicitly_reports_unimplemented_integration(self):
        runtime = Runtime(self.bundle)
        runtime.execution_kind = 'NATIVE'
        with self.assertRaisesRegex(NotImplementedError, 'paired_supervisor_deadline_guard_and_tool_custody'):
            self.run_fixture(runtime)
        self.assertFalse((self.root / custody.ARMS[0]).exists())

    def test_source_pin_mutation_blocks_controller(self):
        self.pins['gpu/orch_r125_continual_native.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source_pin_changed'):
            self.run_fixture()

    def test_receipts_exclusive_and_readonly(self):
        path = self.root / 'RECEIPT.json'
        custody.write_once(path, dict(status='fixture'))
        self.assertEqual(path.stat().st_mode & 0o222, 0)
        with self.assertRaises(FileExistsError):
            custody.write_once(path, dict(status='overwrite'))

    def test_native_admitted_envelope_reuses_original_paths_without_decode_claim(self):
        binding = dict(initializer_commit_sha256=self.binding['checkpoint']['sha256'])
        with patch.object(custody.exact, '_decoded_checkpoint', return_value=({}, {})):
            admitted = custody.admitted_from_saved(Path(self.binding['snapshot_root']), self.binding, binding)
            self.assertEqual(json.loads(admitted.reference_bytes), self.binding['checkpoint'])
            self.assertEqual(admitted.document_bytes,
                             (Path(self.binding['snapshot_root']) / 'checkpoint/COMMIT.json').read_bytes())


class AdmissionTests(unittest.TestCase):
    def assignment(self, physical, minor, identifier):
        return dict(physical=physical, capacity_physical=physical, minor=minor, kernel_minor=minor,
            gpu_uuid=identifier, kernel_uuid=identifier, capacity_uuid=identifier,
            cuda_uuid_bytes=list(UUID(identifier.removeprefix('GPU-')).bytes), node='node4',
            host_sha256=preflight.profile.HOST_SHA256, wrapper='gpu/a40r_ssh.sh',
            lease_sha256=preflight.profile.LEASE_SHA256, lease_extended=False,
            hard_end_unix=2000, lease_end_unix=3000, observed_unix=990,
            fd_scan_privileged=True, fd_scan_unreadable=[], fd_owners=[], compute_pids=[],
            memory_used_mib=0, utilization_percent=0, policy='strict', nonroot_uid=1000,
            denied_foreign_minors=sorted(set(range(8)) - {minor}), inherited_gpu_fds=[],
            allowed_device_open_succeeded=True)

    def setUp(self):
        self.pins = custody.source_pins()
        self.assignments = dict(zip(custody.ARMS, (
            self.assignment(6, 5, preflight.profile.GPU_UUID),
            self.assignment(7, 6, 'GPU-11111111-1111-1111-1111-111111111111'))))

    def test_synthetic_receipt_not_launch_and_no_probe(self):
        with patch.object(preflight.profile, 'command', side_effect=AssertionError('no system command')):
            result = preflight.validate_pair(self.assignments, now=1000, pins=self.pins)
        self.assertIn('NOT_LAUNCH_AUTHORITY', result['status'])

    def test_strict_freshness_capacity_lease_and_FD_failures(self):
        cases = [('policy', 'auto'), ('observed_unix', 950), ('fd_scan_privileged', False),
                 ('fd_scan_unreadable', [12]), ('fd_owners', [123]), ('compute_pids', [123]),
                 ('memory_used_mib', 1), ('utilization_percent', 1), ('lease_extended', True),
                 ('hard_end_unix', 16000), ('inherited_gpu_fds', [3]), ('denied_foreign_minors', []),
                 ('allowed_device_open_succeeded', False), ('wrapper', 'ssh'), ('capacity_physical', 5)]
        for field, value in cases:
            with self.subTest(field=field):
                assignments = deepcopy(self.assignments)
                assignments[custody.ARMS[0]][field] = value
                with self.assertRaises(ValueError):
                    preflight.validate_pair(assignments, now=1000, pins=self.pins)

    def test_exact16_byte_UUID_and_distinct_minor_admission(self):
        for raw in ([1] * 15, [256] * 16, [True] * 16, [1] * 16):
            assignments = deepcopy(self.assignments)
            assignments[custody.ARMS[0]]['cuda_uuid_bytes'] = raw
            with self.assertRaises(ValueError):
                preflight.validate_pair(assignments, now=1000, pins=self.pins)
        self.assignments[custody.ARMS[1]]['minor'] = 5
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            preflight.validate_pair(self.assignments, now=1000, pins=self.pins)


if __name__ == '__main__':
    unittest.main()
