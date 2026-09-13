"""Synthetic metadata and real frozen CPU replay only; never native results."""
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.dont_write_bytecode = True
SOURCE = Path(os.environ.get('ASTRA_SOURCE_ROOT', '/data/home/rohing/dream-state')).absolute()
sys.path[:0] = [str(SOURCE), str(SOURCE/'tests'), '/tmp']
import test_born_rulegame_formation as fixtures
from organism_v6 import born_rulegame_formation as role

SCRIPT = Path('/tmp/astra_projected_formation_analysis_20260913.py')
spec = importlib.util.spec_from_file_location('projected_analysis', SCRIPT)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


class PairedAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = fixtures.BornFormationTests()
        cls.base.setUp()
        cls.addClassCleanup(cls.base.doCleanups)
        cls.templates = {}
        for mode in ('AUTH', 'OFF'):
            binding = role.make_binding(cls.base.pin, expected_birth_pin_sha256=role.diagnostic.value_hash(cls.base.pin),
                                        interface=role.projection.INTERFACE, child_mode=mode)
            counter = iter(1+index*.01 for index in range(1000))
            capture = role.capture_formation(fixtures.RoleBackend(binding), binding,
                expected_binding_sha256=role.diagnostic.value_hash(binding), cutoff=500, clock=lambda: next(counter))
            cls.templates[mode] = cls.make_members(mode, binding, capture)

    @classmethod
    def make_members(cls, mode, binding, capture, plan_updates=None):
        members = {}
        def put(name, value):
            members[analysis.PREFIX+name] = encoded(value)
        normalized = dict(pin=binding['birth'], pin_sha256=role.diagnostic.value_hash(binding['birth']),
                          full_release=True, both_fits_complete=True, released_wall=90)
        put('normalized_birth.json', normalized)
        plan = dict(protocol=analysis.PROTOCOL, phase='formation', root='/native/'+mode, child_mode=mode, child=mode,
            interface=role.projection.INTERFACE, binding=binding, binding_sha256=role.diagnostic.value_hash(binding),
            normalized=normalized, normalized_file_sha256=analysis.sha(members[analysis.PREFIX+'normalized_birth.json']),
            source_root=str(SOURCE), role_sha256=analysis.ROLE_SHA,
            source_hashes={str(SOURCE/'organism_v6'/name): pin for name, pin in binding['sources'].items()},
            model=binding['birth']['child_identity']['model_input'], model_files=binding['birth']['model_files'],
            public_model_binding={'receipt': 'CPU fixture only'}, origin=role.MODEL_ORIGIN, claims='CPU fixture only',
            sidecar_sha256='c'*64, birth_driver_sha256='d'*64, limits=analysis.LIMITS, tokens=analysis.TOKENS,
            members=['formation'], max_calls=60, max_output_tokens=18480, worker_seconds=600, cleanup_seconds=140,
            controller_seconds=900, collection_seconds=300, lease_cutoff=2000, device='0',
            teacher='same fixed base OFF', automatic_pass=False, automatic_progression=False)
        plan.update(plan_updates or {})
        put('plan.json', plan)
        pin = analysis.sha(members[analysis.PREFIX+'plan.json'])
        put('plan.sha256.json', {'sha256': pin})
        put(analysis.DATA+'capture.json', capture)
        for row in capture['calls']:
            stem = analysis.DATA+'calls/'+row['request']['call_id']
            put(stem+'.request.json', dict(request=row['request'], identity=row['identity'], started=row['started']))
            put(stem+'.response.json', dict(envelope=row['envelope'], ended=row['ended']))
        journal = {name[len(analysis.PREFIX+analysis.DATA+'calls/'):]: analysis.sha(value)
                   for name, value in members.items() if name.startswith(analysis.PREFIX+analysis.DATA+'calls/')}
        put(analysis.DATA+'capture_barrier.json', dict(calls=len(capture['calls']), files=journal,
                                                     replay_not_started=True, completed_monotonic=3))
        put(analysis.DATA+'isolation.json', dict(pid=200, parent_pid=100, pgid=200, plan_sha256=pin,
            binding_sha256=plan['binding_sha256'], hard_end=1000, cutoff=500, one_engine=True, prompt_parent=False, online_updates=False))
        put(analysis.DATA+'backend.ready.json', dict(pid=200, ready=.5))
        put(analysis.DATA+'backend.cleanup.json', dict(closed=True, error=None))
        put(analysis.DATA+'manifest.json', {'files': {name[len(analysis.PREFIX+analysis.DATA):]: analysis.sha(value)
            for name, value in members.items() if name.startswith(analysis.PREFIX+analysis.DATA)}})
        put('run/formation/worker/process.json', dict(pid=200, pgid=200, device='0', started=0, timeout=600))
        put('run/formation/worker/supervision.json', dict(error=None, returncode=0, ok=True, owned_group_empty=True,
            gpu_processes_absent=True, reservation_release_verified=True, reserved_seconds=20, device='0'))
        put('run/controller.json', dict(pid=100, pgid=100, session=100, argv=['synthetic'], continuous_reservation=True,
                                       started_wall=101, hard_end=1000))
        costs = dict(calls=len(capture['calls']), input_tokens=0, output_tokens=0, output_token_ceiling=0, call_seconds=0.0)
        for row in capture['calls']:
            costs['input_tokens'] += len(row['envelope']['response']['prompt_token_ids'])
            costs['output_tokens'] += len(row['envelope']['response']['output_token_ids'])
            costs['output_token_ceiling'] += row['request']['max_tokens']
            costs['call_seconds'] += row['ended']-row['started']
        receipt = dict(capture_sha256=analysis.sha(members[analysis.PREFIX+analysis.DATA+'capture.json']),
            manifest_sha256=analysis.sha(members[analysis.PREFIX+analysis.DATA+'manifest.json']),
            binding_sha256=plan['binding_sha256'], costs=costs, replay=role.replay_formation(capture, binding,
                expected_binding_sha256=plan['binding_sha256'], cutoff=500))
        put('run/formation/receipt.json', receipt)
        put('run/result.json', dict(status='COMPLETE_AWAITING_MAIN_AUDIT', plan_sha256=pin,
            receipt_sha256=analysis.sha(members[analysis.PREFIX+'run/formation/receipt.json']),
            supervision_sha256=analysis.sha(members[analysis.PREFIX+'run/formation/worker/supervision.json']),
            controller_seconds=19, ended_wall=120))
        members['metadata/collection/audit.json'] = encoded(dict(phase_complete=True, formation=receipt,
            controller_seconds=19, costs_nested_not_added=True))
        members['metadata/launch/launch.json'] = encoded(dict(plan_sha256=pin, driver_sha256=plan['sidecar_sha256'],
            root=plan['root'], continuous_reservation=True, pid=100, pgid=100, session=100,
            command=['synthetic'], started_wall=100))
        members['metadata/launch/exit.json'] = encoded(dict(returncode=0, ended_wall=121,
            launch_sha256=analysis.sha(members['metadata/launch/launch.json'])))
        return members

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='projection_analysis_cpu_')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def package(self, mode, members=None, validation_updates=None, tar_extra=None):
        members = deepcopy(self.templates[mode] if members is None else members)
        archive = self.root/(mode+'.tgz')
        with tarfile.open(archive, 'w:gz') as bundle:
            for name, data in list(members.items()) + (tar_extra or []):
                item = tarfile.TarInfo(name)
                item.size = len(data)
                bundle.addfile(item, io.BytesIO(data))
        plan = analysis.decode(members[analysis.PREFIX+'plan.json'])
        receipt = dict(protocol=analysis.PROTOCOL, status='COLLECTED_RELEASED', phase_complete=True, full_release=True,
            costs_nested_not_added=True, automatic_progression=False, archived_adapter_bytes=False, collection_seconds=4,
            root=plan['root'], archive_sha256=analysis.sha(archive.read_bytes()),
            archive_files={name: analysis.sha(data) for name, data in members.items()},
            plan_sha256=analysis.sha(members[analysis.PREFIX+'plan.json']), collector_sha256=plan['sidecar_sha256'],
            claims=plan['claims'], terminal_sha256=analysis.sha(members[analysis.PREFIX+'run/result.json']),
            released_wall=125, launch_to_release_seconds=25, final_vacancy={'gpu_uuid': 'CPU-only'}, final_vacancy_sha256='f'*64)
        receipt.update(validation_updates or {})
        validation = self.root/(mode+'.validation.json')
        validation.write_bytes(encoded(receipt))
        return {mode.lower()+'_archive': str(archive), mode.lower()+'_validation': str(validation),
                mode.lower()+'_validation_sha256': analysis.sha(validation.read_bytes())}

    def inputs(self, **kwargs):
        return dict(self.package('AUTH', **kwargs), **self.package('OFF'), source=str(SOURCE), both_closed=True)

    def mutate(self, mode, name, update):
        members = deepcopy(self.templates[mode])
        value = analysis.decode(members[analysis.PREFIX+name])
        update(value)
        members[analysis.PREFIX+name] = encoded(value)
        return members

    def test_complete_pair_real_replay_metrics_and_exact_parent_sources(self):
        result = analysis.analyze_pair(**self.inputs())
        self.assertEqual(result['total_calls'], 120)
        self.assertFalse(result['automatic_pass'])
        self.assertEqual(result['parent_purity'], 'UNREVIEWED_MAIN_JUDGMENT_REQUIRED')
        for mode in ('AUTH', 'OFF'):
            output = result['modes'][mode]
            self.assertTrue(output['replay_verified'])
            self.assertEqual(output['per_arm']['P']['metrics']['original_valid'], {'numerator': 20, 'denominator': 20})
            self.assertEqual(output['per_arm']['P']['metrics']['projection_recovery'], {'numerator': 0, 'denominator': 0})
            self.assertEqual(output['costs']['launch_to_release_seconds'], 25)
            self.assertEqual(output['costs']['worker_reserved_seconds'], 20)
            self.assertEqual(len(output['semantic_audit_extracts']), 4)
            extract = output['semantic_audit_extracts'][0]
            self.assertEqual(len(extract['exact_source_calls']), 5)
            self.assertIn('prompt', extract['parent']['request'])

    def test_closed_declaration_precedes_any_input_reads(self):
        with self.assertRaisesRegex(ValueError, 'BOTH'):
            analysis.analyze_pair(auth_archive='absent', auth_validation='absent', auth_validation_sha256='0'*64,
                off_archive='absent', off_validation='absent', off_validation_sha256='0'*64, source='absent')

    def test_missing_off_argument(self):
        with self.assertRaises(TypeError):
            analysis.analyze_pair(**self.package('AUTH'), source=str(SOURCE), both_closed=True)

    def test_validation_and_archive_tampering(self):
        inputs = self.inputs()
        inputs['auth_validation_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'validation hash'):
            analysis.analyze_pair(**inputs)
        inputs = self.inputs()
        with open(inputs['auth_archive'], 'ab') as stream:
            stream.write(b'tampered')
        with self.assertRaisesRegex(ValueError, 'archive hash'):
            analysis.analyze_pair(**inputs)

    def test_member_hash_missing_extra_duplicate_and_unsafe(self):
        for extra in ('metadata/unknown.json', '../escape', analysis.PREFIX+'plan.json'):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, 'member'):
                analysis.analyze_pair(**self.inputs(tar_extra=[(extra, b'{}')]))
        members = deepcopy(self.templates['AUTH'])
        members['metadata/unknown.json'] = b'{}'
        with self.assertRaisesRegex(ValueError, 'extra archive'):
            analysis.analyze_pair(**self.inputs(members=members))
        pins = {name: analysis.sha(data) for name, data in self.templates['AUTH'].items()}
        pins[analysis.PREFIX+'plan.json'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'member hash'):
            analysis.analyze_pair(**self.inputs(validation_updates={'archive_files': pins}))
        pins = {name: analysis.sha(data) for name, data in self.templates['AUTH'].items()}
        pins['metadata/launch/gpu.xml'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'missing archive'):
            analysis.analyze_pair(**self.inputs(validation_updates={'archive_files': pins}))

    def test_incomplete_release_is_not_promoted(self):
        for field, value in (('phase_complete', False), ('full_release', False), ('status', 'FAILED_PARTIAL'), ('collection_seconds', 301)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                analysis.analyze_pair(**self.inputs(validation_updates={field: value}))

    def test_plan_binding_source_schedule_budget_model_birth_rejected(self):
        changes = [lambda plan: plan.update(child_mode='OFF'), lambda plan: plan.update(max_calls=61),
            lambda plan: plan['model_files'].update(other='e'*64),
            lambda plan: plan['binding']['task_schedule']['formation'].pop(),
            lambda plan: plan['binding']['sources'].update(other='e'*64),
            lambda plan: plan['normalized']['pin'].update(birth_plan_sha256='e'*64)]
        for change in changes:
            members = self.mutate('AUTH', 'plan.json', change)
            members[analysis.PREFIX+'plan.sha256.json'] = encoded({'sha256': analysis.sha(members[analysis.PREFIX+'plan.json'])})
            with self.subTest(change=change), self.assertRaises(ValueError):
                analysis.analyze_pair(**self.inputs(members=members))

    def test_partial_journal_manifest_and_release_negatives(self):
        for name in (analysis.DATA+'calls/0000.response.json', analysis.DATA+'capture_barrier.json', 'run/formation/worker/supervision.json'):
            members = deepcopy(self.templates['AUTH'])
            members.pop(analysis.PREFIX+name)
            with self.subTest(name=name), self.assertRaises((ValueError, KeyError)):
                analysis.analyze_pair(**self.inputs(members=members))
        members = self.mutate('AUTH', 'run/formation/worker/supervision.json', lambda value: value.update(owned_group_empty=False))
        with self.assertRaisesRegex(ValueError, 'terminal receipt'):
            analysis.analyze_pair(**self.inputs(members=members))

    def test_exact_raw_event_replay_not_just_hashes(self):
        inputs = self.inputs()
        bundle = analysis.load_capsule(inputs['auth_archive'], inputs['auth_validation'], inputs['auth_validation_sha256'])
        analysis.verify_capsule(bundle, 'AUTH', role)
        bundle['capture']['events'][0]['raw_response'] = 'invented action'
        with self.assertRaises(ValueError):
            analysis.summarize(bundle, role)

    def test_saved_replay_reducer_tampering(self):
        inputs = self.inputs()
        bundle = analysis.load_capsule(inputs['auth_archive'], inputs['auth_validation'], inputs['auth_validation_sha256'])
        analysis.verify_capsule(bundle, 'AUTH', role)
        bundle['formation_receipt']['replay']['calls'] = 0
        with self.assertRaisesRegex(ValueError, 'saved replay'):
            analysis.summarize(bundle, role)

    def test_duplicate_json_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            analysis.decode(b'{"status":1,"status":2}')

    def test_individually_valid_but_unmatched_pair_rejected(self):
        capture = analysis.decode(self.templates['OFF'][analysis.PREFIX+analysis.DATA+'capture.json'])
        for updates, expected in (({'controller_seconds': 800}, 'controller_seconds'),
                                  ({'public_model_binding': {'different': 'reference'}}, 'public_model_binding')):
            members = self.make_members('OFF', capture['binding'], capture, updates)
            inputs = dict(self.package('AUTH'), **self.package('OFF', members), source=str(SOURCE), both_closed=True)
            with self.subTest(updates=updates), self.assertRaisesRegex(ValueError, 'paired mismatch: '+expected):
                analysis.analyze_pair(**inputs)

    def test_genuine_different_birth_pin_pair_rejected(self):
        pin = deepcopy(self.base.pin)
        pin['birth_plan_sha256'] = 'e'*64
        binding = role.make_binding(pin, expected_birth_pin_sha256=role.diagnostic.value_hash(pin),
                                    interface=role.projection.INTERFACE, child_mode='OFF')
        counter = iter(1+index*.01 for index in range(1000))
        capture = role.capture_formation(fixtures.RoleBackend(binding), binding,
            expected_binding_sha256=role.diagnostic.value_hash(binding), cutoff=500, clock=lambda: next(counter))
        members = self.make_members('OFF', binding, capture)
        inputs = dict(self.package('AUTH'), **self.package('OFF', members), source=str(SOURCE), both_closed=True)
        with self.assertRaisesRegex(ValueError, 'paired mismatch: normalized'):
            analysis.analyze_pair(**inputs)

    def test_actual_projection_recovery_exact_tentative_and_parent_transcript(self):
        class InvalidFirst(fixtures.RoleBackend):
            def generate(self, request):
                envelope = super().generate(request)
                if request['role'] == 'wake' and request['tick'] == 1:
                    envelope['response']['text'] = 'COMPARE'
                    envelope['response']['output_token_ids'] = self.tokenizer.encode('COMPARE')
                return envelope
        inputs = dict(source=str(SOURCE), both_closed=True)
        for mode in ('AUTH', 'OFF'):
            binding = analysis.decode(self.templates[mode][analysis.PREFIX+'plan.json'])['binding']
            counter = iter(1+index*.01 for index in range(1000))
            capture = role.capture_formation(InvalidFirst(binding), binding,
                expected_binding_sha256=role.diagnostic.value_hash(binding), cutoff=500, clock=lambda: next(counter))
            inputs.update(self.package(mode, self.make_members(mode, binding, capture)))
        result = analysis.analyze_pair(**inputs)
        for mode in ('AUTH', 'OFF'):
            output = result['modes'][mode]
            self.assertEqual(output['per_arm']['P']['metrics']['projection_recovery'], {'numerator': 4, 'denominator': 4})
            extract = output['semantic_audit_extracts'][0]
            self.assertIn('UNEXECUTED_PROPOSAL', extract['parent']['request']['prompt'])
            invalid = next(event for event in extract['exact_source_events'] if event['kind'] == 'protocol_invalid')
            self.assertFalse(invalid['executed'])
            self.assertEqual(invalid['raw_response'], 'COMPARE')

    def test_capsule_links_are_rejected_without_extraction(self):
        inputs = self.inputs()
        archive = Path(inputs['auth_archive'])
        name = analysis.PREFIX+'plan.json'
        with tarfile.open(archive, 'w:gz') as bundle:
            member = tarfile.TarInfo(name)
            member.type = tarfile.SYMTYPE
            member.linkname = '/etc/passwd'
            bundle.addfile(member)
        validation = Path(inputs['auth_validation'])
        receipt = analysis.decode(validation.read_bytes())
        receipt['archive_sha256'] = analysis.sha(archive.read_bytes())
        validation.write_bytes(encoded(receipt))
        inputs['auth_validation_sha256'] = analysis.sha(validation.read_bytes())
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            analysis.analyze_pair(**inputs)

    def test_real_cli_parsing_dispatch_and_no_overwrite(self):
        inputs = self.inputs()
        output = self.root/'analysis.json'
        command = [os.path.abspath(sys.executable), '-B', str(SCRIPT), '--both-closed', '--out', str(output)]
        for key, value in inputs.items():
            if key != 'both_closed':
                command.extend(['--'+key.replace('_', '-'), value])
        result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(result.returncode, 0, result.stderr)
        digest = analysis.sha(output.read_bytes())
        self.assertEqual(json.loads(result.stdout)['sha256'], digest)
        repeat = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(repeat.returncode, 0)
        self.assertEqual(analysis.sha(output.read_bytes()), digest)
        help_result = subprocess.run(command[:3]+['--help'], capture_output=True, text=True, timeout=10)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('--off-validation-sha256', help_result.stdout)


if __name__ == '__main__':
    unittest.main()
