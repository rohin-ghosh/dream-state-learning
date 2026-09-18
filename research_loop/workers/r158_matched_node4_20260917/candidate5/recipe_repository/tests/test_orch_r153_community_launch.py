from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r153_community_launch as launch


class CommunityLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'input_source'
        self.source.mkdir()
        self.now = time.time()
        runtime = b'{"synthetic_cpu_fixture": true}\n'
        native = '''
def adapter(peft):
    return peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05)
def optimizer(torch, parameters):
    return torch.optim.AdamW(parameters, lr=3e-5, betas=(0.9, 0.999), eps=1e-8,
                            weight_decay=0.01, foreach=False, fused=False)
def sleep(self):
    encode_sleep_targets()
    r145_prepare_sleep(self.engine.model, __file__, %r)
    r145_loss_arguments()
''' % launch.digest(runtime)
        self.files = {name: b'' for name in launch.REQUIRED}
        self.files[launch.NATIVE] = native.encode()
        self.files[launch.RUNTIME] = runtime
        self.files['gpu/orch_r153_code_blocks.py'] = ('POLICY = %r\n' % launch.CODE_POLICY).encode()
        self.files['gpu/orch_r153_tool_extension.py'] = b'from gpu.orch_r153_code_blocks import POLICY\n'
        self.files['gpu/__init__.py'] = b''
        self.files['organism_v6/__init__.py'] = b''
        for name, raw in self.files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.pins = {name: launch.digest(raw) for name, raw in self.files.items()}
        self.recipe = dict(schema=launch.native.SCHEMA, base_sha256=launch.native.BASE_SHA256,
            system_prompt=launch.native.SYSTEM, birth_prompt=launch.native.BIRTH,
            presentation_version=launch.VERSION, context_limit=16384, segment_tokens=512,
            segments_per_sleep=2, new_presentations=16, rehearsal_presentations=1,
            anchor_lambda=0.25, max_sleeps=None, seed=0, presleep_variant='free_distillation',
            compaction_invitation=launch.native.PRESLEEP_INVITATIONS['free_distillation'],
            decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
            physical=0, gpu_uuid='GPU-0000', hard_end_unix=self.now + 5000,
            lease_end_unix=self.now + 6000, root='/old/recipe', source_root='/old/source',
            model_dir='/old/model', anchors='/old/anchors', readout_revision=3)
        self.request = dict(schema=launch.SCHEMA, directive='Rohin147 CONFIRMED synthetic CPU fixture only',
            source=dict(root=str(self.source), files=self.pins,
                template_guard=self.reference('template-guard.json', dict(source_pins=self.pins))),
            recipe=self.reference('recipe.json', self.recipe),
            cpu=self.reference('cpu.json', dict(passed=True, returncode=0, tests=239,
                command='synthetic fixture, not a real science receipt', source_files=self.pins)),
            main_completion=self.reference('main.json', dict(speaker='Main', status='SOURCE_COMPLETE',
                source_files=self.pins, code_policy=launch.CODE_POLICY)), nodes={}, agents=[])
        for node, wall in (('ovx2', 3600), ('a40r', 7200)):
            host = launch.digest(node.encode())
            lease = self.reference(node + '-lease.json', dict(node=node, host_sha256=host,
                hard_end_unix=self.now + wall, lease_end_unix=self.now + wall + 600))
            slots = {str(spec[2]): dict(physical=spec[2], retiree=spec[3],
                gpu_uuid='GPU-' + ('aa' if node == 'ovx2' else 'bb') + str(spec[2]),
                minor=spec[2] - 1, root=f'/old/{node}/{spec[3]}')
                for spec in launch.AGENTS.values() if spec[1] == node}
            identity = self.reference(node + '-identity.json', dict(node=node, host_sha256=host,
                lease=lease, confirmed=True, confirmed_by='Rawls' if node == 'ovx2' else 'Main',
                python='/local/venv/bin/python', uid=1234, gid=1234, slots=slots))
            self.request['nodes'][node] = dict(lease=lease, identity=identity)
        for number, (identifier, spec) in enumerate(launch.AGENTS.items(), start=1):
            node = spec[1]
            inputs = dict(model_dir=f'/inputs/{node}/model', anchors=f'/inputs/{node}/anchors')
            inputs['provenance'] = self.reference(identifier + '-inputs.json', dict(node=node,
                host_sha256=launch.digest(node.encode()), **inputs, recipe=self.request['recipe'],
                base_sha256=self.recipe['base_sha256'], equivalent_recipe_inputs=True))
            self.request['agents'].append(dict(id=identifier, node=node, physical=spec[2],
                seed=15300 + number, destination=f'/new/community/{identifier}', inputs=inputs,
                parent=dict(required=True, mode='sparse', speaker='Astra', cadence_responses=3),
                capabilities={}))

    def reference(self, name, value):
        path = self.root / name
        raw = launch.encoded(value)
        path.write_bytes(raw)
        return dict(path=str(path), sha256=launch.digest(raw))

    def update_reference(self, reference, **changes):
        document = json.loads(Path(reference['path']).read_bytes())
        document.update(changes)
        return self.reference(Path(reference['path']).name, document)

    def stage(self):
        request = self.reference('request.json', self.request)
        return launch.stage(request['path'], self.root / 'candidate')

    def validate(self):
        return launch.validate_request(self.request)

    def make_writable(self, path):
        path.chmod(0o755 if path.is_dir() else 0o644)

    def test_five_independent_immutable_bundles_and_inherited_walls(self):
        original = deepcopy(self.request)
        with (patch('subprocess.Popen', side_effect=AssertionError('no processes')),
              patch('subprocess.run', side_effect=AssertionError('no processes'))):
            result = self.stage()
        manifest = launch.verify(result['manifest'], result['sha256'])
        self.assertEqual(self.request, original)
        self.assertFalse(result['launch_attempted'])
        self.assertEqual(manifest['executor']['physical'], 2)
        inodes, plans = set(), {}
        for identifier, agent in manifest['agents'].items():
            bundle = self.root / 'candidate' / identifier
            plan = json.loads((bundle / 'config/PLAN.json').read_bytes())
            guard = json.loads((bundle / 'config/GUARD.candidate.json').read_bytes())
            community = json.loads((bundle / 'config/COMMUNITY.json').read_bytes())
            plans[identifier] = plan
            self.assertEqual(plan['readout_revision'], 3)
            self.assertEqual(plan['seed'], agent['seed'])
            self.assertTrue(plan['root'].endswith(identifier + '/life'))
            self.assertEqual(plan['birth_prompt'], (bundle / 'source/context/R153_STARTUP.md').read_text())
            self.assertFalse(guard['resume'])
            self.assertNotEqual(guard['schema'], 'R125_CONTINUAL_GUARD_V1')
            self.assertNotIn('allocation_path', guard)
            self.assertFalse((bundle / 'life').exists())
            self.assertFalse(community['auto_relay'])
            self.assertFalse(community['capabilities_ready'])
            self.assertEqual(community['workspace'], plan['root'] + '/workspace')
            self.assertEqual(community['service_start_index'], 1)
            self.assertEqual(community['code_policy'], launch.CODE_POLICY)
            self.assertIn('gpu/orch_r153_tool_extension.py', guard['source_pins'])
            native = bundle / 'source' / launch.NATIVE
            inodes.add(native.stat().st_ino)
            self.assertEqual(native.stat().st_nlink, 1)
            self.assertEqual(native.stat().st_mode & 0o777, 0o444)
            self.assertEqual((bundle / 'source').stat().st_mode & 0o777, 0o555)
        self.assertEqual(len(inodes), 5)
        self.assertEqual(plans['C1']['hard_end_unix'], self.now + 3600)
        self.assertEqual(plans['C3']['hard_end_unix'], self.now + 7200)
        self.assertEqual((self.source / launch.NATIVE).read_bytes(), self.files[launch.NATIVE])

    def test_existing_candidate_never_overwritten(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, 'new_output'):
            self.stage()

    def test_rawls_must_confirm_actual_node3_slots(self):
        node = self.request['nodes']['ovx2']
        node['identity'] = self.update_reference(node['identity'], confirmed_by='Main')
        with self.assertRaisesRegex(ValueError, 'Rawls'):
            self.validate()

    def test_main_completion_required_before_any_output(self):
        self.request['main_completion'] = self.update_reference(self.request['main_completion'], status='PENDING')
        with self.assertRaisesRegex(ValueError, 'Main_completion'):
            self.stage()
        self.assertFalse((self.root / 'candidate').exists())

    def test_template_native_must_match_tested_donor(self):
        pins = dict(self.pins, **{launch.NATIVE: '0' * 64})
        self.request['source']['template_guard'] = self.reference('template-guard.json', dict(source_pins=pins))
        with self.assertRaisesRegex(ValueError, 'tested_donor_native_policy_unchanged'):
            self.validate()

    def test_duplicate_seed_rejected(self):
        self.request['agents'][1]['seed'] = self.request['agents'][0]['seed']
        with self.assertRaisesRegex(ValueError, 'distinct_recorded_seeds'):
            self.validate()

    def test_bool_seed_rejected(self):
        self.request['agents'][0]['seed'] = True
        with self.assertRaisesRegex(ValueError, 'distinct_recorded_seeds'):
            self.validate()

    def test_fewer_or_extra_learners_rejected(self):
        for agents in (self.request['agents'][:-1], self.request['agents'] + [self.request['agents'][0]]):
            with self.subTest(count=len(agents)), patch.dict(self.request, agents=agents):
                with self.assertRaisesRegex(ValueError, 'exact_five'):
                    self.validate()

    def test_executor_cannot_be_learner(self):
        self.request['agents'][2]['physical'] = 2
        with self.assertRaisesRegex(ValueError, 'exact_selected_retiree_slot'):
            self.validate()

    def test_donor_label_cannot_be_substituted(self):
        reference = self.request['nodes']['ovx2']['identity']
        identity = json.loads(Path(reference['path']).read_bytes())
        identity['slots']['5']['retiree'] = 'support_none'
        self.request['nodes']['ovx2']['identity'] = self.reference('ovx2-identity.json', identity)
        with self.assertRaisesRegex(ValueError, 'confirmed_exact_donor'):
            self.validate()

    def test_cross_node_lease_cannot_be_copied(self):
        self.request['nodes']['ovx2']['lease'] = self.request['nodes']['a40r']['lease']
        with self.assertRaisesRegex(ValueError, 'same_node_identity_and_lease'):
            self.validate()

    def test_expired_or_marginless_lease_rejected(self):
        for end in (self.now - 1, self.now + 4100):
            with self.subTest(end=end):
                node = self.request['nodes']['ovx2']
                node['lease'] = self.update_reference(node['lease'], hard_end_unix=end)
                node['identity'] = self.update_reference(node['identity'], lease=node['lease'])
                with self.assertRaisesRegex(ValueError, 'inherited_lease_margin'):
                    self.validate()

    def test_donor_roots_preserved(self):
        for path in ('/old/ovx2/support_none', '/old/ovx2/support_none/new', '/old'):
            with self.subTest(path=path):
                self.request['agents'][0]['destination'] = path
                with self.assertRaisesRegex(ValueError, 'preserve_old_roots'):
                    self.validate()

    def test_overlapping_agent_destinations_rejected(self):
        self.request['agents'][1]['destination'] = '/new/community/C1/child'
        with self.assertRaisesRegex(ValueError, 'independent_nonoverlapping'):
            self.validate()

    def test_parent_connection_not_optional_policy(self):
        self.request['agents'][0]['parent']['required'] = False
        with self.assertRaisesRegex(ValueError, 'explicit_sparse_parent'):
            self.validate()

    def test_only_Astra_at_exact_cadence_three_is_automated_parent(self):
        for change in ({'speaker': 'Rohin'}, {'speaker': 'Fable'}, {'cadence_responses': 2},
                       {'cadence_responses': 8}, {'cadence_responses': True}):
            with self.subTest(change=change):
                parent = dict(required=True, mode='sparse', speaker='Astra', cadence_responses=3)
                parent.update(change)
                self.request['agents'][0]['parent'] = parent
                with self.assertRaisesRegex(ValueError, 'explicit_sparse_parent'):
                    self.validate()

    def launch_gate(self, manifest):
        agent = manifest['agents']['C1']
        return dict(speaker='Main', action='EXECUTE_R153_NEW_LIFE', approved=True, agent_id='C1',
            manifest_sha256=launch.digest((self.root / 'candidate/MANIFEST.json').read_bytes()),
            plan_sha256=agent['files']['config/PLAN.json'],
            **{key: agent[key] for key in ('node', 'physical', 'gpu_uuid', 'destination')},
            nonce='a' * 32, expires_unix=self.now + 1200, donor_release_verified=True,
            builder_entry_posted=True, builder_entry='Synthetic Main release gate CPU test fixture',
            retirement=self.reference('release.json', dict(status='SYNTHETIC_FIXTURE')),
            checks={name: True for name in ('cpu_tools', 'kernel_tools', 'exchange_transport',
                                          'sparse_Astra_cadence3', 'filesystem_readout_isolation')})

    def test_prepare_binds_exact_gate_and_returns_real_runtime_command_without_running(self):
        result = self.stage()
        manifest = launch.verify(result['manifest'])
        gate = self.reference('gate.json', self.launch_gate(manifest))
        with patch('subprocess.Popen', side_effect=AssertionError('no execution')):
            prepared = launch.prepare(result['manifest'], 'C1', gate['path'], self.root / 'promotion')
        config = json.loads((self.root / 'promotion/GUARD.json').read_bytes())
        self.assertEqual(config['schema'], 'R125_CONTINUAL_GUARD_V1')
        self.assertFalse(config['resume'])
        self.assertEqual(prepared['status'], 'PREPARED_NOT_EXECUTED')
        self.assertIn('gpu.orch_r153_community_runtime', prepared['execute_argv'])
        self.assertIn('supervise', prepared['execute_argv'])
        self.assertEqual(config['r153_main_gate_sha256'], gate['sha256'])
        self.assertEqual(config['device_containment']['unit'], 'orch-r153-native-' + 'a' * 32)
        self.assertFalse(Path(prepared['attempt_dir']).exists())
        allocation = json.loads((self.root / 'promotion/ALLOCATION.json').read_bytes())
        self.assertTrue(allocation['builder_entry_posted'])
        self.assertFalse(allocation['git_push_performed'])
        self.assertEqual(allocation['legacy_builder_entry_pushed_semantics'],
                         'LOCAL_POSTING_COMPATIBILITY_NOT_GIT_PUSH')

    def test_prepare_rejects_gate_drift_expiry_or_unreleased_donor(self):
        result = self.stage()
        manifest = launch.verify(result['manifest'])
        for change in ({'approved': False}, {'gpu_uuid': 'GPU-wrong'}, {'plan_sha256': '0' * 64},
                       {'expires_unix': self.now - 1}, {'donor_release_verified': False},
                       {'builder_entry_posted': False}, {'agent_id': 'C2'}):
            with self.subTest(change=change):
                gate = dict(self.launch_gate(manifest))
                gate.update(change)
                reference = self.reference('gate.json', gate)
                with self.assertRaises(ValueError):
                    launch.prepare(result['manifest'], 'C1', reference['path'], self.root / 'promotion')
                self.assertFalse((self.root / 'promotion').exists())

    def test_unconnected_startup_truthful(self):
        text = launch.startup_text(self.request['agents'][0], {})
        self.assertIn('connection is not yet verified', text)
        self.assertIn('Not yet verified connected', text)
        self.assertNotIn('experiment service is connected', text)
        self.assertIn('try to make your own reply', text)
        self.assertIn('No automatic thought relay', text)

    def test_python_capability_requires_parser_and_origin_and_interface(self):
        agent = self.request['agents'][0]
        receipt = dict(agent_id=agent['id'], node=agent['node'], destination=agent['destination'],
            capability='python', status='PASS', connected=True, source_files=self.pins,
            interface='Use the first ```python code fence; punctuation normalization is logged.',
            forgiving_first_code=True, origin_verified=True, ascii_punctuation=True)
        reference = self.reference('python.json', receipt)
        agent['capabilities']['python'] = reference
        connected = launch.connected_capabilities(agent, self.pins)
        text = launch.startup_text(agent, connected)
        self.assertIn('ephemeral /work', text)
        self.assertIn(receipt['interface'], text)
        agent['capabilities']['python'] = self.update_reference(reference, origin_verified=False)
        with self.assertRaisesRegex(ValueError, 'parser_and_origin'):
            launch.connected_capabilities(agent, self.pins)

    def bootstrap_receipt(self):
        agent = self.request['agents'][0]
        return dict(agent_id=agent['id'], node=agent['node'], destination=agent['destination'],
            capability='python', status='BOOTSTRAP', source_files=self.pins,
            service_ready=True, waiting_new_root=True, parser_tested=True, sandbox_tested=True,
            transport_tested=True, forgiving_first_code=True, origin_verified=True, ascii_punctuation=True,
            interface='Use a first plain python fence after the service attaches to this new root.')

    def test_bootstrap_can_stage_before_journal_and_parent_delivery_exist(self):
        agent = self.request['agents'][0]
        agent['capabilities']['python'] = self.reference('bootstrap-python.json', self.bootstrap_receipt())
        result = self.stage()
        launch.verify(result['manifest'])
        bundle = self.root / 'candidate/C1'
        text = (bundle / 'source/context/R153_STARTUP.md').read_text()
        self.assertIn('A sparse Astra parent is assigned', text)
        self.assertIn('Only actual attributed turns count as replies', text)
        self.assertIn('Rohin console affordance is staged', text)
        self.assertIn('waiting for your new root', text)
        self.assertIn('Live connection and delivery are not yet verified', text)
        self.assertIn('first plain python/code fence', text)
        self.assertNotIn('experiment service is connected', text)
        self.assertFalse((bundle / 'life/stream').exists())
        community = json.loads((bundle / 'config/COMMUNITY.json').read_bytes())
        self.assertEqual(community['connected_capabilities'], {})
        self.assertEqual(community['bootstrap_capabilities']['python']['status'], 'BOOTSTRAP')

    def test_bootstrap_rejects_unchecked_or_falsely_connected_service(self):
        for key, value in (('parser_tested', False), ('sandbox_tested', False), ('transport_tested', False),
                           ('waiting_new_root', False), ('connected', True)):
            with self.subTest(key=key):
                receipt = dict(self.bootstrap_receipt(), **{key: value})
                self.request['agents'][0]['capabilities']['python'] = self.reference('bootstrap-python.json', receipt)
                with self.assertRaisesRegex(ValueError, 'tested_waiting_root_BOOTSTRAP'):
                    self.validate()

    def test_unknown_capability_not_advertised(self):
        self.request['agents'][0]['capabilities']['browser'] = {}
        with self.assertRaisesRegex(ValueError, 'known_capability'):
            self.validate()

    def test_node_local_inputs_bound_to_selected_recipe(self):
        self.request['agents'][0]['inputs']['anchors'] = '/another/anchor'
        with self.assertRaisesRegex(ValueError, 'node_local_inputs_match'):
            self.validate()

    def test_source_extension_allowed_but_missing_dependency_rejected(self):
        self.assertIn('gpu/orch_r153_tool_extension.py', launch.source_closure(self.request['source']))
        self.pins['gpu/orch_r153_tool_extension.py'] = launch.digest(b'import gpu.not_in_closure\n')
        (self.source / 'gpu/orch_r153_tool_extension.py').write_bytes(b'import gpu.not_in_closure\n')
        with self.assertRaisesRegex(ValueError, 'missing_local_import'):
            launch.source_closure(self.request['source'])

    def test_exact_noncredential_ssh_wrappers_are_pinned_and_copied(self):
        raw = b'#!/bin/bash\nexit 0\n'
        for name in launch.SOURCE_WRAPPERS:
            (self.source / name).write_bytes(raw)
            self.pins[name] = launch.digest(raw)
        self.request['cpu'] = self.update_reference(self.request['cpu'], source_files=self.pins)
        self.request['main_completion'] = self.update_reference(self.request['main_completion'], source_files=self.pins)
        result = self.stage()
        manifest = launch.verify(result['manifest'])
        for identifier in launch.AGENTS:
            for name in launch.SOURCE_WRAPPERS:
                self.assertEqual((self.root / 'candidate' / identifier / 'source' / name).read_bytes(), raw)
                self.assertEqual(manifest['agents'][identifier]['files']['source/' + name], launch.digest(raw))

    def test_other_shell_scripts_hosts_env_and_keys_are_rejected(self):
        for name in ('gpu/a40r_scp.sh', 'gpu/other.sh', 'gpu/hosts.env', 'gpu/id_rsa', 'gpu/key.pem'):
            with self.subTest(name=name):
                source = dict(self.request['source'], files=dict(self.pins, **{name: '0' * 64}))
                with self.assertRaisesRegex(ValueError, 'explicit_source_or_config_only'):
                    launch.source_closure(source)

    def test_package_initializer_cannot_escape_pins(self):
        del self.pins['gpu/__init__.py']
        with self.assertRaisesRegex(ValueError, 'missing_package_initializer'):
            launch.source_closure(self.request['source'])

    def test_source_symlink_rejected(self):
        path = self.source / 'gpu/orch_r153_tool_extension.py'
        path.unlink()
        path.symlink_to(self.source / 'gpu/orch_r153_code_blocks.py')
        with self.assertRaisesRegex(ValueError, 'symlink_rejected'):
            self.validate()

    def test_source_hardlink_rejected(self):
        os.link(self.source / launch.NATIVE, self.root / 'aliased-native.py')
        with self.assertRaisesRegex(ValueError, 'unshared_file'):
            self.validate()

    def test_source_traversal_rejected(self):
        self.pins['../escape.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'safe_relative_source'):
            self.validate()

    def test_modified_source_and_stale_cpu_receipt_rejected(self):
        (self.source / launch.NATIVE).write_text('changed')
        with self.assertRaisesRegex(ValueError, 'source_hash_mismatch'):
            self.validate()

    def test_nonzero_cpu_exit_rejected(self):
        self.request['cpu'] = self.update_reference(self.request['cpu'], returncode=1)
        with self.assertRaisesRegex(ValueError, 'successful_CPU_receipt'):
            self.validate()

    def test_r144_r145_both_required(self):
        for name in ('encode_sleep_targets', 'r145_loss_arguments'):
            with self.subTest(name=name):
                files = dict(self.files)
                files[launch.NATIVE] = files[launch.NATIVE].replace(name.encode(), b'old_implementation')
                with self.assertRaisesRegex(ValueError, 'R144_target_exclusion_and_R145'):
                    launch.runtime_contract(files)

    def test_r145_non_python_runtime_pin_required(self):
        files = dict(self.files, **{launch.RUNTIME: b'changed-runtime'})
        with self.assertRaisesRegex(ValueError, 'R145_runtime_pin'):
            launch.runtime_contract(files)

    def test_frozen_rank_and_optimizer_recipe(self):
        for before, after, error in ((b'r=8', b'r=16', 'LoraConfig'), (b'lr=3e-5', b'lr=1e-3', 'AdamW')):
            with self.subTest(error=error):
                files = dict(self.files)
                files[launch.NATIVE] = files[launch.NATIVE].replace(before, after)
                with self.assertRaisesRegex(ValueError, error):
                    launch.runtime_contract(files)

    def test_preserve_recipe_readouts_and_context_no_new_shutdown(self):
        for key, value in (('max_sleeps', 4), ('context_limit', 8192), ('segments_per_sleep', 3),
                           ('new_presentations', 1)):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'R127_continuous_recipe'):
                launch.recipe_plan(dict(self.recipe, **{key: value}), self.now)
        self.assertEqual(launch.recipe_plan(self.recipe, self.now)['readout_revision'], 3)

    def test_resume_or_wall_extension_not_inherited(self):
        for key in ('authorized_wall_extension', 'initial_adapter', 'resume_checkpoint', 'preupdate_recovery'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'no_resume_or_wall_extension'):
                launch.recipe_plan(dict(self.recipe, **{key: 'old'}), self.now)

    def test_console_command_routes_rohin_and_quotes_text(self):
        result = self.stage()
        text = "Please test this; don't run $(anything)."
        command = launch.console_command(result['manifest'], 'C4', text)
        arguments = shlex.split(command)
        self.assertEqual(arguments[-1], text)
        self.assertEqual(arguments[arguments.index('--speaker') + 1], 'Rohin')
        self.assertEqual(arguments[arguments.index('--root') + 1], '/new/community/C4/life')
        self.assertIn('gpu.orch_r127_pilot_console', arguments)

    def test_manifest_pin_and_extra_file_detection(self):
        result = self.stage()
        with self.assertRaisesRegex(ValueError, 'external_pin'):
            launch.verify(result['manifest'], '0' * 64)
        source = self.root / 'candidate/C1/source'
        self.make_writable(source)
        (source / 'extra.py').write_text('unexpected')
        source.chmod(0o555)
        with self.assertRaisesRegex(ValueError, 'exact_bundle_inventory'):
            launch.verify(result['manifest'])

    def test_mutation_after_freeze_rejected(self):
        result = self.stage()
        path = self.root / 'candidate/C2/source' / launch.NATIVE
        self.make_writable(path)
        path.write_text('changed')
        path.chmod(0o444)
        with self.assertRaisesRegex(ValueError, 'bundle_hash_mismatch'):
            launch.verify(result['manifest'])

    def test_mutable_manifest_rejected(self):
        result = self.stage()
        self.make_writable(Path(result['manifest']))
        with self.assertRaisesRegex(ValueError, 'immutable_manifest_and_root'):
            launch.verify(result['manifest'])

    def test_candidate_guard_cannot_be_promoted_by_accident(self):
        result = self.stage()
        path = self.root / 'candidate/C1/config/GUARD.candidate.json'
        document = json.loads(path.read_bytes())
        self.assertNotEqual(document['schema'], 'R125_CONTINUAL_GUARD_V1')
        self.assertFalse((path.parent / 'ALLOCATION.json').exists())

    def test_strict_containment_is_argv_only_and_uses_minor_not_physical(self):
        policy = dict(uid=1234, gid=1234, minor=4, unit='orch-r153-native-' + 'a' * 32)
        plan = dict(self.recipe, physical=5, hard_end_unix=self.now + 100,
                    lease_end_unix=self.now + 800, source_root='/source')
        command = launch.containment_command(plan, policy, '/venv/python',
                    ['-m', 'gpu.main_admitted_entry', '--config', '/guard'], now=self.now)
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=DeviceAllow=', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia4 rw', command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia5 rw', command)
        self.assertIn('--property=RuntimeMaxSec=100', command)
        self.assertIn('--property=NoNewPrivileges=yes', command)
        self.assertIn('--property=KillMode=control-group', command)
        self.assertIn('PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True', command)
        self.assertFalse(any(item.startswith('PYTORCH_ALLOC_CONF=') for item in command))
        self.assertIn('-i', command)
        self.assertNotIn('/bin/sh', command)
        with self.assertRaisesRegex(ValueError, 'inherited_wall'):
            launch.containment_command(plan, policy, '/venv/python', ['-m', 'entry'], now=self.now + 101)

    def test_no_launch_or_retirement_cli(self):
        for command in ('launch', 'retire'):
            with self.subTest(command=command), patch('sys.stderr'), self.assertRaises(SystemExit):
                launch.main([command])


def configure_node5(fixture):
    fixture.request['profile'] = launch.NODE5_PROFILE
    lease = fixture.reference('node5-lease.json', dict(node='ovx3', host_sha256=launch.NODE5_HOST_SHA256,
        hard_end_unix=launch.NODE5_WALL, lease_end_unix=launch.NODE5_LEASE_END, lease_extended=False))
    release = fixture.reference('capacity.json', dict(schema='R154_NODE5_CAPACITY_CUSTODY_RELEASE_V1',
        speaker='Main', approved=True, scope='R153_FIVE_COMMUNITY_ONLY', profile=launch.NODE5_PROFILE,
        node='ovx3', host_sha256=launch.NODE5_HOST_SHA256, physical=list(launch.NODE5_DEVICES),
        agent_slots={identifier: spec[2] for identifier, spec in launch.PROFILES[launch.NODE5_PROFILE].items()},
        lease=lease, r151_unused_reservation_released=True, historical_1_5_capacity_released=True,
        historical_artifacts_preserved=True, additional_children=0, lease_extended=False))
    identity = fixture.reference('node5-identity.json', dict(node='ovx3',
        host_sha256=launch.NODE5_HOST_SHA256, lease=lease, capacity_release=release,
        confirmed=True, confirmed_by='Main', python='/local/venv/bin/python', uid=2524, gid=2524,
        protected_roots=['/old/node5'], slots={str(physical): dict(physical=physical, gpu_uuid=uuid,
        minor=physical) for physical, uuid in launch.NODE5_DEVICES.items()}))
    fixture.request.update(nodes=dict(ovx3=dict(lease=lease, identity=identity)), capacity_release=release)
    for agent in fixture.request['agents']:
        agent.update(node='ovx3', physical=launch.PROFILES[launch.NODE5_PROFILE][agent['id']][2])
        agent['inputs']['provenance'] = fixture.update_reference(agent['inputs']['provenance'],
            node='ovx3', host_sha256=launch.NODE5_HOST_SHA256)


def node5_gate(fixture, manifest):
    gate = fixture.launch_gate(manifest)
    gate.pop('retirement')
    gate.pop('donor_release_verified')
    gate.update(profile=launch.NODE5_PROFILE, capacity_release_verified=True,
                capacity_release=fixture.request['capacity_release'])
    return gate


class Node5LaunchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = CommunityLaunchTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.clock = patch.object(launch.time, 'time', return_value=launch.NODE5_WALL - 3600)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.fixture.now = launch.NODE5_WALL - 3600
        configure_node5(self.fixture)

    def test_exact_five_node5_bundles_and_capacity_promotion(self):
        staged = self.fixture.stage()
        manifest = launch.verify(staged['manifest'])
        self.assertEqual(manifest['profile'], launch.NODE5_PROFILE)
        for identifier, physical in zip(launch.AGENTS, (0, 1, 3, 4, 5)):
            agent = manifest['agents'][identifier]
            self.assertEqual((agent['node'], agent['physical'], agent['gpu_uuid']),
                             ('ovx3', physical, launch.NODE5_DEVICES[physical]))
            self.assertIsNone(agent['retiree'])
            self.assertEqual(agent['capacity_release'], self.fixture.request['capacity_release'])
            plan = json.loads((self.fixture.root / 'candidate' / identifier / 'config/PLAN.json').read_bytes())
            self.assertEqual(plan['hard_end_unix'], launch.NODE5_WALL)
            self.assertEqual(plan['lease_end_unix'], launch.NODE5_LEASE_END)
        gate = self.fixture.reference('gate.json', node5_gate(self.fixture, manifest))
        prepared = launch.prepare(staged['manifest'], 'C1', gate['path'], self.fixture.root / 'promotion')
        config = json.loads((self.fixture.root / 'promotion/GUARD.json').read_bytes())
        self.assertEqual(config['r153_release_kind'], 'capacity_release')
        self.assertFalse(config['resume'])
        self.assertIn('supervise', prepared['execute_argv'])

    def test_protected_or_unassigned_slots_rejected(self):
        for physical in (2, 6, 7):
            with self.subTest(physical=physical):
                self.fixture.request['agents'][0]['physical'] = physical
                with self.assertRaisesRegex(ValueError, 'exact_selected_retiree_slot'):
                    self.fixture.validate()

    def test_wrong_UUID_minor_or_host_rejected(self):
        node = self.fixture.request['nodes']['ovx3']
        original = json.loads(Path(node['identity']['path']).read_bytes())
        for change in ('uuid', 'minor', 'host', 'speaker'):
            identity = deepcopy(original)
            if change == 'uuid':
                identity['slots']['0']['gpu_uuid'] = launch.NODE5_DEVICES[1]
            elif change == 'minor':
                identity['slots']['0']['minor'] = 1
            elif change == 'host':
                identity['host_sha256'] = '0' * 64
            else:
                identity['confirmed_by'] = 'Rawls'
            node['identity'] = self.fixture.reference('node5-identity.json', identity)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.fixture.validate()

    def test_lease_extension_or_copied_wall_rejected(self):
        node = self.fixture.request['nodes']['ovx3']
        original = json.loads(Path(node['lease']['path']).read_bytes())
        for change in ({'hard_end_unix': launch.NODE5_WALL + 1},
                       {'lease_end_unix': launch.NODE5_LEASE_END + 600}, {'lease_extended': True}):
            node['lease'] = self.fixture.reference('node5-lease.json', dict(original, **change))
            node['identity'] = self.fixture.update_reference(node['identity'], lease=node['lease'])
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'exact_existing_node5_lease'):
                self.fixture.validate()

    def test_Main_capacity_release_required_not_donor_attestation(self):
        original = json.loads(Path(self.fixture.request['capacity_release']['path']).read_bytes())
        for change in ({'speaker': 'Rawls'}, {'approved': False}, {'historical_artifacts_preserved': False},
                       {'r151_unused_reservation_released': False}, {'additional_children': 1}):
            release = self.fixture.reference('capacity.json', dict(original, **change))
            self.fixture.request['capacity_release'] = release
            node = self.fixture.request['nodes']['ovx3']
            node['identity'] = self.fixture.update_reference(node['identity'], capacity_release=release)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.fixture.validate()

    def test_old_roots_preserved(self):
        self.fixture.request['agents'][0]['destination'] = '/old/node5/new'
        with self.assertRaisesRegex(ValueError, 'preserve_old_roots'):
            self.fixture.validate()

    def test_exact_profile_and_capacity_gate_required(self):
        staged = self.fixture.stage()
        manifest = launch.verify(staged['manifest'])
        for change in ({'profile': launch.DEFAULT_PROFILE}, {'capacity_release_verified': False},
                       {'capacity_release': dict(path='/irrelevant', sha256='0' * 64)}):
            gate = dict(node5_gate(self.fixture, manifest), **change)
            reference = self.fixture.reference('gate.json', gate)
            with self.subTest(change=change), self.assertRaises(ValueError):
                launch.prepare(staged['manifest'], 'C1', reference['path'], self.fixture.root / 'promotion')

    def test_all_five_use_single_exact_device_strict_envelope(self):
        for physical, uuid in launch.NODE5_DEVICES.items():
            plan = dict(self.fixture.recipe, community_profile=launch.NODE5_PROFILE,
                physical=physical, gpu_uuid=uuid, hard_end_unix=launch.NODE5_WALL,
                lease_end_unix=launch.NODE5_LEASE_END)
            policy = dict(uid=2524, gid=2524, minor=physical, unit='orch-r153-native-' + 'a' * 32)
            command = launch.containment_command(plan, policy, '/venv/python', ['-m', 'entry'])
            self.assertIn('--property=DevicePolicy=strict', command)
            self.assertIn('--property=DeviceAllow=/dev/nvidia' + str(physical) + ' rw', command)
            self.assertEqual(sum(item.startswith('--property=DeviceAllow=/dev/nvidia') and
                                 item[-4].isdigit() for item in command), 1)


if __name__ == '__main__':
    unittest.main()
