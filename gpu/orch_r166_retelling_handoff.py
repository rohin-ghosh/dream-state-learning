"""C1-C5 exact invitation staging; one-shot saved-boundary activation needs Main GO."""

import argparse
from copy import deepcopy
import hashlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import select
import signal
import socket
import subprocess
import time
import uuid

from gpu import orch_r157_community_wall_extension as saved
from gpu import orch_r166_corrected_retelling as retelling


MODULE = 'gpu.orch_r166_retelling_handoff'
RELATIVE = 'gpu/orch_r166_retelling_handoff.py'
TEST_RELATIVE = 'tests/test_orch_r166_retelling_handoff.py'
POLICY_RELATIVE = 'gpu/orch_r166_corrected_retelling.py'
NATIVE_RELATIVE = 'gpu/orch_r125_continual_native.py'
SCHEMA = 'R166_SAVED_RETELLING_HANDOFF_V1'
FOLLOWUP_SHA256 = '47aadbd13882d7925aeede0b487b66eb6d2062b92b01a844c27f8b162a5bce69'
FOLLOWUP_RELATIVE = 'research_loop/workers/r167_object_survival/DIRECTIVE.md'
POLICY_SHA256 = '9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc'
POLICY_TEST_RELATIVE = 'tests/test_orch_r166_corrected_retelling.py'
POLICY_TEST_SHA256 = 'b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e'
ADDENDUM_SHA256 = '8d30ae072fa6ec826b972eb23134e9dff4acc54a5afd4935e72266fd2b6c6735'
ACTIVATION_AGENTS = ('C1', 'C2', 'C4', 'C5')
GO_SCHEMA = 'R166_SAVED_BOUNDARY_MAIN_GO_V1'
RECOVERY_GO_SCHEMA = 'R166_C5_RETIRED_RECOVERY_MAIN_GO_V1'
RECOVERY_BOUNDARY_RULE = 'EXACT_RETIRED_C5_SAVED28_NO_NEW_RECORDS'
RECOVERY_CYCLE = 28
RECOVERY_INDEX = 2899
RECOVERY_STEPS = 2478
RECOVERY_PINS = {
    'REQUEST.json': '610008ad692d4705c119f9cc745364e6140bfdd5c02208b27ead3ac5c63d3df9',
    'ACTIVATION_FAILED.json': '72272c5842ac974bc0c5c405b699b4d182e3c07552ad4c71d9c26e102ff24862',
    'OWNER_RETIRED.json': 'a0e7c8a1545f7de8d97f85f197d8297545bda6ab3f161bdc15eee93e5ccdccc2',
    'ACTUAL_BOUNDARY_READY.json': '0e7a4da6acf27850365784c98b8d2e3c4a19c4574e76641a79d9504115b58755',
    'control/PREPARED.json': '7188cb554add8faad53f070696306cd7f48f3d50aaa18fb1badc0bbb1985ab09',
    'control/SAVED_PROOF.json': 'f961c96566a5f60f56dbd83ab143839d933607b7ef11f9adeda9d8d69b3fc9a4',
    'attempt/NATIVE.log': '853b1a1a060795839fbd9d9f4dce0aecf7f2011115e1da5b7844b7e8e5407c47',
    'attempt/NATIVE_EXIT.json': '32158028b966bed556266c3414056b8bb8a16a916c321902d7c06348c274c706',
    'attempt/LAUNCH.json': 'cf4ef8209693b1f5d022a99e2d721213292b06c0218c4123f08271bcda2790e9',
    'MAIN_DISPATCH.json': '77919fc5cdeb09efdfc5797299bb39fd2f702c608c1af9449b04c439ef28b34b',
}
require = saved.require


def scope(agent, config, plan):
    require(agent in saved.TARGETS, 'C1_C5_only')
    physical, gpu_uuid, unused_pid, unused_ticks = saved.TARGETS[agent]
    root = saved.BASE / ('orch_r153_community_' + agent + '_20260916_attempt1') / 'life'
    require(plan['root'] == str(root) and plan.get('community_agent_id') == agent
            and plan['physical'] == physical and plan['gpu_uuid'] == gpu_uuid,
            'exact_community_root_slot_identity')
    require(config['device_containment']['minor'] == physical
            and config['device_containment']['uid'] == config['device_containment']['gid'] == 2524
            and config['host_sha256'] == hashlib.sha256(saved.HOST.encode()).hexdigest(),
            'unchanged_node5_strict_device_identity')
    require(plan['hard_end_unix'] == config['hard_end_unix'] == saved.NEW_WALL
            and plan['lease_end_unix'] == config['next_reserved_unix'] == saved.CEILING,
            'existing_R157_wall_unchanged')
    require(plan.get('presleep_variant', 'free_distillation') in retelling.VARIANTS
            and not any(plan.get(key) for key in ('preupdate_recovery', 'matched_cohort', 'no_sleep', 'frozen'))
            and plan.get('learning_enabled', True) is True
            and plan.get('parented', True) is True
            and plan.get('mode', 'learning') == 'learning', 'parented_distilling_learning_only')
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1
            and plan['anchor_lambda'] == 0.25, 'unchanged_learning_recipe')
    policy = retelling.validate_scope(dict(schema=retelling.SCHEMA, root=str(root),
        directive_sha256=retelling.DIRECTIVE_SHA256, parented=True,
        presleep_variant=plan.get('presleep_variant', 'free_distillation')))
    return dict(sorted(policy.items()))


def cpu_operator():
    require(socket.gethostname() == saved.HOST and os.getuid() == 2524
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node5_CPU_only_preparation')


def capture_owner(pid, config_path, config, plan):
    actor = saved.identity(pid)
    timer = saved.identity(actor['parent'])
    supervisor = saved.identity(timer['parent'])
    command = [str(saved.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard',
               'native', '--config', str(config_path)]
    require(actor['argv'] == command and timer['argv'][:3] ==
            ['timeout', '--signal=TERM', '--kill-after=5s'] and timer['argv'][4:] == command
            and timer['argv'][3].endswith('s') and timer['argv'][3][:-1].isdigit(),
            'exact_current_native_timeout_argv')
    require(supervisor['argv'] == [str(saved.PYTHON), '-B', '-m', saved.MODULE,
            'contained-native', '--config', str(config_path)]
            and actor['group'] == timer['group'] == timer['pid'], 'existing_R157_supervisor')
    launch = saved.read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == saved.sha(config_path)
            and launch['plan_sha256'] == config['plan_sha256'], 'current_launch_bound')
    pair = dict(actor=actor, timer=timer, supervisor=supervisor)
    for process in pair.values():
        require(process['uid'] == 2524 and process['cwd'] == plan['source_root']
                and process['boot_id'] == actor['boot_id'] and process['cgroup'] ==
                '0::/system.slice/' + config['device_containment']['unit'] + '.service',
                'exact_current_owned_processes')
    readout_pid = None
    if saved.live_children(actor['pid']):
        boundary = saved.saved_boundary(plan['root'])
        require(boundary is not None, 'extra_child_requires_saved_readout_boundary')
        metadata = saved.readout(plan['root'], config, plan, boundary, actor)
        require(metadata and metadata['identity'], 'exact_original_readout_child')
        readout_pid = metadata['identity']['pid']
    saved.check_children(pair, readout_pid)
    return pair


def require_retired(pair):
    for process in pair.values():
        require(not Path('/proc', str(process['pid'])).exists(), 'old_owner_still_present_no_prepare')


def validate_cpu(path):
    receipt = saved.read(path)
    repository = Path(__file__).resolve().parents[1]
    expected = {name: saved.sha(repository / name) for name in
                (RELATIVE, TEST_RELATIVE, POLICY_RELATIVE, saved.RELATIVE)}
    require(receipt.get('passed') is True and receipt.get('returncode') == 0
            and type(receipt.get('tests')) is int and receipt['tests'] > 0
            and receipt.get('files') == expected
            and receipt.get('invitation_tests_sha256') == POLICY_TEST_SHA256
            == saved.sha(repository / POLICY_TEST_RELATIVE)
            and expected[POLICY_RELATIVE] == POLICY_SHA256, 'bound_actual_CPU_receipt')
    return expected


def validate_followup(scope_document, followup_directive):
    document = saved.read(scope_document)
    followup = document.get('followup_scope')
    require(document.get('schema') == 'R166_BUILDER_SCOPE_V1'
            and document.get('directive_sha256') == retelling.DIRECTIVE_SHA256
            and type(followup) is dict, 'R150_preserved_R153_followup_required')
    require(followup.get('directive_sha256') == FOLLOWUP_SHA256 == saved.sha(followup_directive)
            and followup.get('directive_path') == FOLLOWUP_RELATIVE, 'exact_R153_followup_directive')
    require(followup.get('runtime_limit') ==
            'No new children or retirements; native changes limited to pre-sleep invitation; original sources/recipes/controls preserved',
            'R153_runtime_limit_unchanged')
    return dict(scope_document=saved.reference(scope_document),
                directive=saved.reference(followup_directive), declared_scope=deepcopy(followup))


def stage(agent, config_path, native_pid, directive, cpu, output, *, scope_document, followup_directive, addendum,
          candidate_request=None, candidate_sha256=None):
    cpu_operator()
    require(saved.sha(directive) == retelling.DIRECTIVE_SHA256, 'exact_Rohin150_directive')
    followup = validate_followup(scope_document, followup_directive)
    require(saved.sha(addendum) == ADDENDUM_SHA256, 'exact_R154_addendum')
    dependencies = validate_cpu(cpu)
    config, plan = saved.original_validate(config_path)
    policy = scope(agent, config, plan)
    require('r157_request' in config, 'current_R157_provenance_required')
    prior_request = saved.bound(config['r157_request'])
    saved.authorization(prior_request['authorization']['path'], prior_request['provenance']['path'])
    community_path = Path(plan['root']).parent / 'config/COMMUNITY.json'
    birth_config = saved.bound(prior_request['old_config'])
    require(saved.sha(community_path) == birth_config['r153_agent']['files']['config/COMMUNITY.json']
            and saved.read(community_path)['parent']['speaker'] == 'Astra', 'original_parented_community_binding')
    pair = capture_owner(native_pid, config_path, config, plan)
    output = saved.regular(output)
    require(output.parent == saved.BASE and output.name.startswith('orch_r166_retelling_' + agent + '_')
            and not output.exists(), 'new_R166_output_only')
    original_source = saved.regular(plan['source_root'])
    original = saved.files(original_source)
    predecessor = None
    if candidate_request is not None or candidate_sha256 is not None:
        require(candidate_request is not None and candidate_sha256 is not None
                and saved.sha(candidate_request) == candidate_sha256, 'exact_existing_candidate_request')
        predecessor = saved.read(candidate_request)
        require(predecessor['agent'] == agent and predecessor['old_config'] == saved.reference(config_path)
                and predecessor['old_plan'] == saved.reference(config['plan_path'])
                and predecessor['original_files'] == original
                and predecessor['source_files'][POLICY_RELATIVE] == POLICY_SHA256
                and saved.files(Path(predecessor['source_root'])) == predecessor['source_files'],
                'unchanged_R154_predecessor_candidate')
    require(original.get(saved.RELATIVE) == dependencies[saved.RELATIVE], 'exact_reused_R157_helper')
    require(not any(name in original for name in (RELATIVE, TEST_RELATIVE, POLICY_RELATIVE)),
            'no_existing_R166_source_or_reapplication')
    patched = retelling.patch_source((original_source / NATIVE_RELATIVE).read_text(), policy)
    output.mkdir(mode=0o700)
    source = output / 'source'
    shutil.copytree(original_source, source)
    for directory in (source, source / 'gpu', source / 'tests'):
        directory.chmod(0o755)
    native = source / NATIVE_RELATIVE
    native.chmod(0o644)
    native.write_text(patched)
    repository = Path(__file__).resolve().parents[1]
    for name in (RELATIVE, TEST_RELATIVE, POLICY_RELATIVE, POLICY_TEST_RELATIVE):
        shutil.copyfile(repository / name, source / name)
    copied = saved.files(source)
    if predecessor is not None:
        require(set(copied) == set(predecessor['source_files']) | {POLICY_TEST_RELATIVE} and all(
            copied[name] == checksum for name, checksum in predecessor['source_files'].items()
            if name not in (RELATIVE, TEST_RELATIVE)), 'only_activation_operator_added_to_candidate')
    require(set(copied) - set(original) == {RELATIVE, TEST_RELATIVE, POLICY_RELATIVE, POLICY_TEST_RELATIVE} - set(original)
            and copied[POLICY_TEST_RELATIVE] == POLICY_TEST_SHA256
            and all(copied[name] == checksum for name, checksum in original.items()
                    if name != NATIVE_RELATIVE)
            and all(copied[name] == checksum for name, checksum in dependencies.items())
            and saved.files(original_source) == original, 'only_isolated_invitation_patch')
    saved.freeze(source)
    for name, original_path, reference in (
            ('R153_SCOPE.json', scope_document, followup['scope_document']),
            ('R153_DIRECTIVE.md', followup_directive, followup['directive'])):
        shutil.copyfile(original_path, output / name)
        require(saved.sha(output / name) == reference['sha256'], 'followup_copy_without_drift')
        (output / name).chmod(0o444)
    frozen_followup = validate_followup(output / 'R153_SCOPE.json', output / 'R153_DIRECTIVE.md')
    shutil.copyfile(addendum, output / 'R154_ADDENDUM.md')
    require(saved.sha(output / 'R154_ADDENDUM.md') == ADDENDUM_SHA256, 'R154_copy_without_drift')
    (output / 'R154_ADDENDUM.md').chmod(0o444)
    request = dict(schema=SCHEMA, agent=agent, old_config=saved.reference(config_path),
        old_plan=saved.reference(config['plan_path']), old_lease=saved.reference(config['lease_path']),
        prior_request=config['r157_request'], community=saved.reference(community_path),
        directive=saved.reference(directive), followup=frozen_followup,
        addendum=saved.reference(output / 'R154_ADDENDUM.md'),
        followup_origin=followup, cpu=saved.reference(cpu), pair=pair,
        policy_scope=policy, source_root=str(source), original_files=original, source_files=copied,
        created_unix=time.time(), status='STAGED_ONLY_NO_SIGNALS_NO_GO')
    if predecessor is not None:
        request['candidate_predecessor'] = saved.reference(candidate_request)
    saved.write(output / 'REQUEST.json', request)
    return saved.reference(output / 'REQUEST.json')


def proposed_plan(old, source, boundary, stream_path, *, wall_record=None):
    state = boundary['record']['document']['resume_state']['state']
    require(state['deadline_unix'] == old['hard_end_unix']
            and saved.digest(state) == boundary['state_sha256'], 'exact_current_saved_deadline')
    plan = deepcopy(old)
    extension = plan.pop('authorized_wall_extension', None)
    if extension is not None:
        require(extension['new_deadline_unix'] == old['hard_end_unix'], 'applied_wall_extension_only')
        matches = [wall_record] if wall_record is not None else (saved.read(path)
                   for path in (Path(stream_path) / 'records').glob('*.json')
                   if len(path.stem) == 20 and path.stem.isdigit())
        require(any(record['kind'] == 'WALL_EXTENDED' and
                    record['document']['authorization'] == extension for record in matches),
                'prior_wall_extension_must_be_recorded_not_replayed')
    plan['source_root'] = str(source)
    if old.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        plan['startup_context']['path'] = str(Path(source) / relative)
    check_plan_delta(old, plan)
    return plan


def check_plan_delta(old, new):
    normalized = deepcopy(new)
    normalized['source_root'] = old['source_root']
    if old.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        require(new['startup_context']['path'] == str(Path(new['source_root']) / relative),
                'startup_relocation_only')
        normalized['startup_context']['path'] = old['startup_context']['path']
    prior = deepcopy(old)
    prior.pop('authorized_wall_extension', None)
    require(normalized == prior, 'birth_experiment_walls_recipe_readouts_unchanged')


def boundary_cpu(plan_path, boundary_path):
    plan = saved.read(plan_path)
    code = '''import json,sys,random
from pathlib import Path
from gpu import orch_r125_continual_native as native
import torch
plan=native.validate_plan(native.read(sys.argv[1])); boundary=native.read(sys.argv[2])
envelope=boundary['record']['document']['resume_state']
stream=native.ContinualStream.restore(envelope,expected_sha256=envelope['sha256'])
native.verify_experiment_resume(plan,stream.experiment)
native.require(stream.deadline_unix==plan['hard_end_unix'] and stream.pending is None
 and stream.sleep_frontier==len(stream.rows),'saved_same_wall_no_pending')
commit_path=Path(plan['root'])/'checkpoints'/('sleep_%06d'%boundary['cycle'])/'COMMIT.json'
checkpoint=native.read(commit_path)
native.require(checkpoint==boundary['record']['document']['checkpoint'],'record_checkpoint_exact')
native.NativeChild.verify_checkpoint(checkpoint)
native.require(native.digest(checkpoint['checkpoint_sha256'])==stream.model_state_sha256
 and checkpoint.get('experiment')==stream.experiment,'model_history_experiment_binding')
payload=torch.load(checkpoint['optimizer_rng_path'],map_location='cpu',weights_only=False)
native.require(payload['optimizer_steps']==checkpoint['optimizer_steps']>0
 and payload['optimizer']['state'] and payload['optimizer']['param_groups']
 and payload['parameter_names'] and payload.get('experiment')==stream.experiment,'full_saved_AdamW')
native.require(len(payload['cuda_rng'])==1 and payload['cuda_rng'][0].device.type=='cpu','single_saved_cuda_RNG')
torch.Generator(device='cpu').set_state(payload['cpu_rng']); random.Random().setstate(payload['python_rng'])
native.require(not torch.cuda.is_initialized(),'CPU_only')
print(json.dumps(dict(checkpoint_path=str(commit_path),checkpoint_sha256=native.sha(commit_path),
 optimizer_steps=checkpoint['optimizer_steps'],adapter_state_sha256=checkpoint['adapter_state_sha256'],
 bundle_sha256=checkpoint['checkpoint_sha256'],stream_sha256=envelope['sha256'],
 cuda_initialized=False,reset=False,corrected_output_claimed=False)))
'''
    return json.loads(subprocess.check_output([str(saved.PYTHON), '-B', '-c', code,
        str(plan_path), str(boundary_path)], cwd=plan['source_root'],
        env=saved.environment(plan['source_root']), text=True, timeout=180))


def verify_request(output):
    request = saved.read(output / 'REQUEST.json')
    require(request['schema'] == SCHEMA, 'handoff_schema')
    config = saved.bound(request['old_config'])
    plan = saved.bound(request['old_plan'])
    require(scope(request['agent'], config, plan) == request['policy_scope'], 'unchanged_policy_scope')
    require(saved.sha(request['directive']['path']) == retelling.DIRECTIVE_SHA256
            == request['directive']['sha256'], 'directive_still_bound')
    followup = request.get('followup')
    require(type(followup) is dict, 'R153_staged_followup_required')
    require(validate_followup(followup['scope_document']['path'], followup['directive']['path']) == followup,
            'staged_R153_followup_still_bound')
    addendum = request.get('addendum')
    require(type(addendum) is dict and addendum.get('sha256') == ADDENDUM_SHA256
            == saved.sha(addendum['path']), 'staged_R154_addendum_still_bound')
    for name in ('old_lease', 'community', 'cpu', 'prior_request'):
        saved.bound(request[name])
    if request.get('candidate_predecessor'):
        saved.bound(request['candidate_predecessor'])
    dependencies = validate_cpu(request['cpu']['path'])
    require(request['source_files'].get(POLICY_TEST_RELATIVE) == POLICY_TEST_SHA256
            and all(request['source_files'].get(name) == checksum
                for name, checksum in dependencies.items()), 'staged_dependencies_match_CPU')
    prior = saved.bound(request['prior_request'])
    saved.authorization(prior['authorization']['path'], prior['provenance']['path'])
    require(saved.files(Path(plan['source_root'])) == request['original_files']
            and saved.files(Path(request['source_root'])) == request['source_files'], 'full_source_pins')
    for path in (Path(request['source_root']), *Path(request['source_root']).rglob('*')):
        require(not path.is_symlink() and path.stat().st_mode & 0o222 == 0, 'frozen_successor_source')
    require((Path(request['source_root']) / NATIVE_RELATIVE).read_text() == retelling.patch_source(
        (Path(plan['source_root']) / NATIVE_RELATIVE).read_text(), request['policy_scope']), 'exact_patch_recomputed')
    return request, config, plan


def strict_command(config, plan, config_path):
    command = saved.containment_command(dict(config, r157_config_path=str(config_path)), plan)
    require(command[-3:] == ['contained-native', '--config', str(config_path)], 'known_R157_command_shape')
    require(command[-4] == saved.MODULE, 'original_strict_module_position')
    command[-4] = MODULE
    return dict(template=command, executable_as_is=True, main_GO_required=True,
        unchanged_scan_module='gpu.orch_r125_continual_guard',
        unchanged_verify_containment='gpu.orch_r153_community_runtime.verify_containment')


def check_paused(pair):
    for process in pair.values():
        saved.same(process)
    tasks = list((Path('/proc') / str(pair['actor']['pid']) / 'task').iterdir())
    require(tasks and all((path / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't')
                          for path in tasks), 'all_exact_actor_threads_paused')
    saved.check_children(pair)


def recovery_evidence():
    predecessor = saved.BASE / 'orch_r166_retelling_C5_20260917_activation3'
    references = {}
    for name, checksum in RECOVERY_PINS.items():
        require(saved.sha(predecessor / name) == checksum, 'exact_known_premodel_failure_' + name)
        references[name] = saved.reference(predecessor / name)
    original = saved.bound(references['REQUEST.json'])
    require(original['agent'] == 'C5', 'recovery_C5_only')
    require_retired(original['pair'])
    for name in ('attempt/LAUNCH.json', 'MAIN_DISPATCH.json'):
        require_retired(dict(process=saved.bound(references[name])))
    failure = saved.bound(references['ACTIVATION_FAILED.json'])
    require(failure['original_exit_confirmed'] is True and failure['termination_intent_recorded'] is True
            and failure['no_retry'] is True
            and saved.bound(references['attempt/NATIVE_EXIT.json']) == dict(returncode=1, no_retry=True)
            and not (predecessor / 'attempt/DISPATCH_ONCE').exists()
            and (predecessor / 'attempt/DISPATCH_ONCE.json').is_file(), 'confirmed_premodel_marker_failure')
    retired = saved.bound(references['OWNER_RETIRED.json'])
    prepared = saved.bound(references['control/PREPARED.json'])
    require(retired['pair'] == original['pair'] and retired['prepared'] == references['control/PREPARED.json']
            and retired['go'] == saved.read(predecessor / 'EXECUTION_GO.json')['go'],
            'authentic_prior_retirement_not_recreated')
    for name in ('config', 'plan', 'policy', 'proof'):
        saved.bound(prepared[name])
    config = saved.bound(original['old_config'])
    plan = saved.bound(original['old_plan'])
    require(scope('C5', config, plan) == original['policy_scope'], 'original_C5_scope_preserved')
    require(saved.files(Path(original['source_root'])) == original['source_files']
            and saved.files(Path(plan['source_root'])) == original['original_files'], 'all_predecessor_sources_unchanged')
    boundary = saved.saved_boundary(plan['root'])
    ready = saved.bound(references['ACTUAL_BOUNDARY_READY.json'])
    proof = saved.bound(references['control/SAVED_PROOF.json'])
    require(boundary is not None and boundary['cycle'] == RECOVERY_CYCLE and boundary['index'] == RECOVERY_INDEX
            and boundary['reference'] == ready['boundary'] and boundary['state_sha256'] == proof['stream_sha256']
            and proof['optimizer_steps'] == RECOVERY_STEPS and proof['reset'] is False
            and proof['cuda_initialized'] is False, 'exact_saved28_no_new_work_or_reset')
    checkpoint = Path(plan['root']) / 'checkpoints' / ('sleep_%06d' % RECOVERY_CYCLE)
    require(proof['checkpoint_path'] == str(checkpoint / 'COMMIT.json')
            and saved.sha(checkpoint / 'COMMIT.json') == proof['checkpoint_sha256']
            and saved.files(checkpoint) == prepared['checkpoint_files']
            == saved.files(predecessor / 'preserved_checkpoint'), 'full_recovery_checkpoint_custody')
    saved.verify_snapshot(predecessor / 'preserved_stream', plan['root'], boundary)
    evidence = dict(schema='R166_C5_PREMODEL_RECOVERY_CUSTODY_V2', files=references,
        boundary=boundary['reference'], checkpoint=saved.reference(checkpoint / 'COMMIT.json'),
        state_sha256=proof['stream_sha256'], original_pair_sha256=saved.digest(original['pair']),
        original_wall=plan['hard_end_unix'], no_model_before_failure=True)
    return evidence, original, boundary, proof


def validate_recovery_request(output, request):
    evidence, original, boundary, proof = recovery_evidence()
    require(request.get('recovery_custody') == saved.reference(output / 'RECOVERY_CUSTODY.json')
            and saved.bound(request['recovery_custody']) == evidence, 'exact_recovery_failure_custody')
    require(output.parent == saved.BASE and output.name.startswith('orch_r166_retelling_C5_')
            and output != Path(original['source_root']).parent
            and request['source_root'] == str(output / 'source'), 'new_C5_recovery_namespace')
    expected = deepcopy(original)
    for name in ('source_root', 'source_files', 'cpu', 'created_unix', 'status'):
        expected[name] = request[name]
    expected.update(candidate_predecessor=evidence['files']['REQUEST.json'],
                    recovery_custody=request['recovery_custody'])
    require(request == expected, 'only_recovery_source_CPU_namespace_delta')
    inventory = request['source_files']
    require(set(inventory) == set(original['source_files']) and all(
        inventory[name] == checksum for name, checksum in original['source_files'].items()
        if name not in (RELATIVE, TEST_RELATIVE)), 'recovery_no_native_recipe_invitation_drift')
    require(inventory[POLICY_TEST_RELATIVE] == POLICY_TEST_SHA256, 'recovery_invitation_test_closure')
    return evidence, original, boundary, proof


def stage_recovery(cpu, output):
    cpu_operator()
    dependencies = validate_cpu(cpu)
    evidence, original, boundary, proof = recovery_evidence()
    output = saved.regular(output)
    require(output.parent == saved.BASE and output.name.startswith('orch_r166_retelling_C5_')
            and not output.exists(), 'fresh_C5_recovery_output_only')
    output.mkdir(mode=0o700)
    source = output / 'source'
    shutil.copytree(original['source_root'], source)
    for directory in (source, source / 'gpu', source / 'tests'):
        directory.chmod(0o755)
    repository = Path(__file__).resolve().parents[1]
    for name in (RELATIVE, TEST_RELATIVE):
        (source / name).chmod(0o644)
        shutil.copyfile(repository / name, source / name)
    inventory = saved.files(source)
    require(all(inventory[name] == checksum for name, checksum in dependencies.items()), 'recovery_CPU_source_pins')
    saved.freeze(source)
    saved.write(output / 'RECOVERY_CUSTODY.json', evidence)
    request = deepcopy(original)
    request.update(source_root=str(source), source_files=inventory, cpu=saved.reference(cpu),
        candidate_predecessor=evidence['files']['REQUEST.json'],
        recovery_custody=saved.reference(output / 'RECOVERY_CUSTODY.json'), created_unix=time.time(),
        status='STAGED_RETIRED_C5_RECOVERY_NO_GO')
    saved.write(output / 'REQUEST.json', request)
    verify_request(output)
    validate_recovery_request(output, request)
    return saved.reference(output / 'REQUEST.json')


def prepare(output, *, paused_pair=None, recovery_go=None):
    cpu_operator()
    output = saved.regular(output)
    request, old_config, old_plan = verify_request(output)
    if recovery_go is not None:
        require(paused_pair is None, 'recovery_never_pauses_or_retires')
        recovery_binding(output, recovery_go['path'], recovery_go['sha256'])
    if paused_pair is None:
        require_retired(request['pair'])
    else:
        require(paused_pair == request['pair'], 'prepared_exact_paused_owner')
        check_paused(paused_pair)
    require(time.time() + 180 < old_plan['hard_end_unix'], 'original_wall_has_time')
    boundary = saved.saved_boundary(old_plan['root'])
    require(boundary is not None, 'latest_record_must_be_complete_saved_sleep')
    control = output / 'control'
    require(not control.exists(), 'prepare_once_no_overwrite')
    control.mkdir(mode=0o700)
    snapshot = output / 'preserved_stream'
    shutil.copytree(Path(old_plan['root']) / 'stream', snapshot)
    saved.verify_snapshot(snapshot, old_plan['root'], boundary)
    records = {path.stem for path in (snapshot / 'records').glob('*.json')
               if len(path.stem) == 20 and path.stem.isdigit()}
    intents = {path.name[:-12] for path in (snapshot / 'records').glob('*.intent.json')}
    require(records == intents, 'no_unpaired_intent_at_saved_boundary')
    checkpoint = Path(old_plan['root']) / 'checkpoints' / ('sleep_%06d' % boundary['cycle'])
    inventory = saved.files(checkpoint)
    shutil.copytree(checkpoint, output / 'preserved_checkpoint')
    require(saved.files(output / 'preserved_checkpoint') == inventory == saved.files(checkpoint),
            'exact_checkpoint_preservation')
    plan = proposed_plan(old_plan, request['source_root'], boundary, snapshot)
    saved.write(control / 'PLAN.json', plan)
    saved.write(control / 'BOUNDARY.json', boundary)
    saved.write(control / 'EFFECTIVE_POLICY.json', dict(schema=SCHEMA,
        request=saved.reference(output / 'REQUEST.json'), original_plan=request['old_plan'],
        original_directive=request['directive'], followup=request['followup'],
        addendum=request['addendum'],
        scope=request['policy_scope'], invitation=retelling.INVITATION,
        invitation_sha256=hashlib.sha256(retelling.INVITATION.encode()).hexdigest(),
        effective_after_boundary=boundary['reference'], original_stream_sha256=boundary['state_sha256'],
        retired_plan_authorization=old_plan.get('authorized_wall_extension'),
        old_birth_and_experiment_preserved=True, target_rewritten=False,
        actual_runtime_applied=False, corrected_output_claimed=False))
    saved.write(control / 'ALLOCATION.json', dict(cpu_tests_passed=True, builder_entry_pushed=True,
        builder_entry_pushed_semantics='LOCAL_PROSPECTIVE_PREPARATION_NOT_GO_OR_GIT_PUSH',
        declared_unix=time.time(), plan_sha256=saved.sha(control / 'PLAN.json'),
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical']))
    config = deepcopy(old_config)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=saved.sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=saved.sha(control / 'ALLOCATION.json'),
        attempt_dir=str(output / 'attempt'), resume=True,
        source_pins={name: value for name, value in request['source_files'].items() if name.endswith('.py')},
        r166_request=saved.reference(output / 'REQUEST.json'),
        r166_boundary=saved.reference(control / 'BOUNDARY.json'),
        r166_policy=saved.reference(control / 'EFFECTIVE_POLICY.json'))
    config['device_containment']['unit'] = 'orch-r157-native-' + uuid.uuid4().hex
    if paused_pair is not None:
        config['r166_go'] = saved.read(output / 'EXECUTION_GO.json')['go']
    elif recovery_go is not None:
        config['r166_go'] = recovery_go
        config['r166_recovery'] = request['recovery_custody']
    saved.write(control / 'GUARD.json', config)
    proof = boundary_cpu(control / 'PLAN.json', control / 'BOUNDARY.json')
    saved.original_validate(control / 'GUARD.json')
    require(saved.saved_boundary(old_plan['root']) == boundary and saved.files(checkpoint) == inventory,
            'unchanged_boundary_after_CPU_check')
    if paused_pair is None:
        require_retired(request['pair'])
    else:
        check_paused(paused_pair)
    verify_request(output)
    saved.write(control / 'SAVED_PROOF.json', proof)
    saved.write(control / 'EXECUTION_REQUIREMENTS.json', strict_command(config, plan, control / 'GUARD.json'))
    result = dict(status='CPU_PREPARED_STRICT_SUCCESSOR_MAIN_GO_REQUIRED',
        config=saved.reference(control / 'GUARD.json'), plan=saved.reference(control / 'PLAN.json'),
        policy=saved.reference(control / 'EFFECTIVE_POLICY.json'), proof=saved.reference(control / 'SAVED_PROOF.json'),
        checkpoint_files=inventory, no_signals=True, no_launch=True, no_GO=True)
    saved.freeze(snapshot)
    saved.freeze(output / 'preserved_checkpoint')
    saved.write(control / 'PREPARED.json', result)
    return result


def latest_completed_boundary(root):
    paths = sorted((Path(root) / 'stream/records').glob('*.json'), reverse=True)
    for path in paths:
        if len(path.stem) != 20 or not path.stem.isdigit():
            continue
        record = saved.read(path)
        if record['kind'] != 'SLEEP_COMPLETE':
            continue
        require(record['sha256'] == saved.digest({key: value for key, value in record.items()
                if key != 'sha256'}), 'preflight_boundary_hash')
        document = record['document']
        state = document['resume_state']['state']
        require(document['status'] == 'COMPLETE' and document['resume_state']['sha256'] == saved.digest(state)
                and state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
                and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'preflight_completed_saved_state')
        return dict(record=record, reference=saved.reference(path), state_sha256=saved.digest(state),
                    cycle=document['cycle'], index=record['index'])
    raise ValueError('no_completed_checkpoint_for_CPU_preflight')


def preflight(output, *, recovery=False):
    cpu_operator()
    output = saved.regular(output)
    request, config, plan = verify_request(output)
    require(request['agent'] in ACTIVATION_AGENTS, 'Main_activation_scope_C1_C2_C4_C5')
    if recovery:
        evidence, old_request, boundary, prior_proof = validate_recovery_request(output, request)
    else:
        require('recovery_custody' not in request, 'ordinary_preflight_not_recovery')
        for process in request['pair'].values():
            saved.same(process)
    directory = output / 'readiness'
    directory.mkdir(mode=0o700)
    if not recovery:
        boundary = latest_completed_boundary(plan['root'])
    wall_record = None
    if plan.get('authorized_wall_extension') is not None:
        prior_boundary = saved.bound(config['r157_boundary'])
        path = Path(plan['root']) / 'stream/records' / ('%020d.json' % (prior_boundary['index'] + 1))
        wall_record = saved.read(path)
        require(wall_record['previous_sha256'] == prior_boundary['record']['sha256']
                and wall_record['sha256'] == saved.digest({key: value for key, value in wall_record.items()
                                                          if key != 'sha256'}), 'exact_recorded_wall_extension_chain')
    proposed = proposed_plan(plan, request['source_root'], boundary, Path(plan['root']) / 'stream',
                             wall_record=wall_record)
    saved.write(directory / 'PLAN.json', proposed)
    saved.write(directory / 'BOUNDARY.json', boundary)
    proof = boundary_cpu(directory / 'PLAN.json', directory / 'BOUNDARY.json')
    saved.write(directory / 'CPU_PROOF.json', proof)
    envelope = strict_command(config, proposed, output / 'control/GUARD.json')
    require(envelope['executable_as_is'] is True, 'strict_successor_implemented_before_stop')
    if recovery:
        validate_recovery_request(output, request)
        require(proof == prior_proof, 'recovery_identical_adapter_optimizer_RNG_state')
    else:
        for process in request['pair'].values():
            saved.same(process)
    binding = dict(request=saved.reference(output / 'REQUEST.json'),
        plan=saved.reference(directory / 'PLAN.json'), cpu_proof=saved.reference(directory / 'CPU_PROOF.json'),
        source_manifest_sha256=saved.digest(request['source_files']), pair_sha256=saved.digest(request['pair']),
        boundary_rule='NEXT_ACTUAL_SAVED_SLEEP_AT_OR_AFTER_PREFLIGHT_WITH_NEW_CPU_CUSTODY_PROOF',
        earliest_boundary_index=boundary['index'], hard_end_unix=plan['hard_end_unix'],
        max_wait_seconds=600, max_pause_seconds=600)
    result = dict(schema='R166_ACTIVATION_READINESS_V1', status='CPU_PROVEN_EXECUTABLE_NO_SIGNALS_NO_GO',
        required_GO_binding=binding, strict_successor=envelope,
        proof_is_loader_preflight_not_current_resume_authority=True, original_owners_alive=True)
    if recovery:
        binding.update(boundary_rule=RECOVERY_BOUNDARY_RULE, boundary=boundary['reference'],
                       recovery_custody=request['recovery_custody'])
        result.update(schema='R166_C5_RECOVERY_READINESS_V1', original_owners_alive=False,
            prior_retirement_evidence=evidence['files']['OWNER_RETIRED.json'],
            status='CPU_PROVEN_RETIRED_RECOVERY_EXECUTABLE_NEW_GO_REQUIRED')
    saved.write(directory / 'READY.json', result)
    return result


def validate_go(go, expected, now, *, schema=GO_SCHEMA):
    require(go.get('schema') == schema and go.get('issuer') == 'Main' and go.get('decision') == 'GO'
            and go.get('binding') == expected, 'exact_Main_activation_GO')
    require(type(go.get('not_before_unix')) in (int, float) and type(go.get('expires_unix')) in (int, float)
            and go['not_before_unix'] <= now < go['expires_unix'] <= expected['hard_end_unix']
            and go['expires_unix'] - go['not_before_unix'] <= 1800, 'finite_fresh_bounded_GO')


def activation_binding(output, go_path, go_sha256):
    request, config, plan = verify_request(output)
    require('recovery_custody' not in request, 'ordinary_execute_not_retired_recovery')
    require(request['agent'] in ACTIVATION_AGENTS, 'Main_activation_scope_C1_C2_C4_C5')
    ready = saved.read(output / 'readiness/READY.json')
    expected = ready['required_GO_binding']
    require(ready['schema'] == 'R166_ACTIVATION_READINESS_V1'
            and expected['boundary_rule'] == 'NEXT_ACTUAL_SAVED_SLEEP_AT_OR_AFTER_PREFLIGHT_WITH_NEW_CPU_CUSTODY_PROOF'
            and expected['earliest_boundary_index'] == saved.read(output / 'readiness/BOUNDARY.json')['index']
            and expected['request'] == saved.reference(output / 'REQUEST.json')
            and expected['source_manifest_sha256'] == saved.digest(request['source_files'])
            and expected['pair_sha256'] == saved.digest(request['pair'])
            and expected['hard_end_unix'] == plan['hard_end_unix']
            and expected['max_wait_seconds'] == expected['max_pause_seconds'] == 600,
            'readiness_exact_source_owner_wall')
    saved.bound(expected['plan'])
    proof = saved.bound(expected['cpu_proof'])
    require(proof['cuda_initialized'] is False and proof['reset'] is False,
            'actual_CPU_proof_before_any_stop')
    require(saved.sha(go_path) == go_sha256, 'exact_supplied_GO_bytes')
    validate_go(saved.read(go_path), expected, time.time())
    return request, config, plan, expected


def recovery_binding(output, go_path, go_sha256):
    request, config, plan = verify_request(output)
    evidence, original, boundary, proof = validate_recovery_request(output, request)
    ready = saved.read(output / 'readiness/READY.json')
    expected = dict(request=saved.reference(output / 'REQUEST.json'),
        plan=saved.reference(output / 'readiness/PLAN.json'),
        cpu_proof=saved.reference(output / 'readiness/CPU_PROOF.json'),
        source_manifest_sha256=saved.digest(request['source_files']), pair_sha256=saved.digest(request['pair']),
        boundary_rule=RECOVERY_BOUNDARY_RULE, earliest_boundary_index=boundary['index'],
        hard_end_unix=plan['hard_end_unix'], max_wait_seconds=600, max_pause_seconds=600,
        boundary=boundary['reference'], recovery_custody=request['recovery_custody'])
    require(ready['schema'] == 'R166_C5_RECOVERY_READINESS_V1'
            and ready['required_GO_binding'] == expected and ready['original_owners_alive'] is False
            and ready['prior_retirement_evidence'] == evidence['files']['OWNER_RETIRED.json'],
            'exact_recovery_readiness_not_live_owner_fiction')
    require(saved.bound(expected['cpu_proof']) == proof
            and saved.read(output / 'readiness/BOUNDARY.json') == boundary, 'recovery_ready_exact_saved_state')
    check_plan_delta(plan, saved.bound(expected['plan']))
    require(saved.sha(go_path) == go_sha256, 'exact_supplied_recovery_GO_bytes')
    validate_go(saved.read(go_path), expected, time.time(), schema=RECOVERY_GO_SCHEMA)
    return request, config, plan, expected


def validate_successor(config_path, *, before_retirement=False):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    output = Path(config['r166_request']['path']).parent
    recovery = 'r166_recovery' in config
    if recovery:
        require(not before_retirement, 'recovery_has_no_retirement_phase')
        request, old_config, old_plan, expected = recovery_binding(
            output, config['r166_go']['path'], config['r166_go']['sha256'])
        require(config['r166_recovery'] == request['recovery_custody'], 'exact_recovery_config_custody')
    else:
        request, old_config, old_plan, expected = activation_binding(
            output, config['r166_go']['path'], config['r166_go']['sha256'])
    if before_retirement:
        check_paused(request['pair'])
    else:
        require_retired(request['pair'])
    control = output / 'control'
    prepared = saved.read(control / 'PREPARED.json')
    for name in ('config', 'plan', 'policy', 'proof'):
        saved.bound(prepared[name])
    require(prepared['config'] == saved.reference(config_path)
            and prepared['plan'] == saved.reference(config['plan_path'])
            and saved.sha(config['plan_path']) == expected['plan']['sha256'], 'GO_exact_final_plan_and_control')
    boundary = saved.bound(config['r166_boundary'])
    require(saved.saved_boundary(plan['root']) == boundary, 'no_new_unsaved_suffix_before_resume')
    saved.verify_snapshot(output / 'preserved_stream', plan['root'], boundary)
    checkpoint = Path(plan['root']) / 'checkpoints' / ('sleep_%06d' % boundary['cycle'])
    require(saved.files(checkpoint) == prepared['checkpoint_files']
            == saved.files(output / 'preserved_checkpoint'), 'exact_saved_checkpoint_custody')
    check_plan_delta(old_plan, plan)
    normalized = deepcopy(config)
    for name in ('plan_path', 'plan_sha256', 'allocation_path', 'allocation_sha256',
                 'attempt_dir', 'resume', 'source_pins', 'device_containment'):
        if name in old_config:
            normalized[name] = old_config[name]
        else:
            normalized.pop(name, None)
    for name in ('r166_request', 'r166_boundary', 'r166_policy', 'r166_go'):
        normalized.pop(name, None)
    if recovery:
        normalized.pop('r166_recovery', None)
    require(normalized == old_config and config['resume'] is True
            and config['device_containment'] == dict(old_config['device_containment'],
                unit=config['device_containment']['unit'])
            and config['attempt_dir'] == str(output / 'attempt')
            and config['source_pins'] == {name: value for name, value in request['source_files'].items()
                                         if name.endswith('.py')}, 'exact_guard_delta_no_recipe_or_wall_drift')
    require(saved.read(output / 'EXECUTION_GO.json')['go'] == config['r166_go'], 'one_bound_execution_GO')
    if recovery:
        execution = saved.read(output / 'RECOVERY_EXECUTION.json')
        require(execution == dict(schema='R166_C5_RETIRED_RECOVERY_EXECUTION_V1',
            go=config['r166_go'], custody=config['r166_recovery'],
            prepared=saved.reference(control / 'PREPARED.json'),
            prior_retirement=saved.bound(config['r166_recovery'])['files']['OWNER_RETIRED.json'],
            no_retirement_performed=True, no_retry=True), 'bound_recovery_execution_not_fabricated_retirement')
        require(not (output / 'OWNER_RETIRED.json').exists(), 'no_fabricated_recovery_retirement')
        require(saved.bound(prepared['proof']) == saved.read(
            saved.BASE / 'orch_r166_retelling_C5_20260917_activation3/control/SAVED_PROOF.json'),
            'actual_recovery_CPU_state_identical')
    elif not before_retirement:
        switched = saved.read(output / 'OWNER_RETIRED.json')
        require(switched['go'] == config['r166_go'] and switched['prepared'] == saved.reference(control / 'PREPARED.json')
                and switched['pair'] == request['pair'], 'bound_authorized_retirement_and_custody')
    return config, plan


def execute_recovery(output, go_path, go_sha256):
    cpu_operator()
    output = saved.regular(output)
    request, old_config, old_plan, expected = recovery_binding(output, go_path, go_sha256)
    require(Path(__file__).resolve() == Path(request['source_root']) / RELATIVE
            and Path(saved.__file__).resolve() == Path(request['source_root']) / saved.RELATIVE
            and Path(retelling.__file__).resolve() == Path(request['source_root']) / POLICY_RELATIVE,
            'recovery_execute_exact_successor_source')
    lock = os.open(saved.BASE / 'orch_r157_C5_HANDOFF.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    started = False
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'ACTIVATE_ONCE').mkdir()
        started = True
        go = saved.reference(go_path)
        saved.write(output / 'EXECUTION_GO.json', dict(go=go, no_retry=True))
        recovery_binding(output, go_path, go_sha256)
        prepared = prepare(output, recovery_go=go)
        require(prepared['plan']['sha256'] == expected['plan']['sha256'], 'recovery_GO_exact_final_plan')
        saved.write(output / 'RECOVERY_EXECUTION.json', dict(schema='R166_C5_RETIRED_RECOVERY_EXECUTION_V1',
            go=go, custody=request['recovery_custody'], prepared=saved.reference(output / 'control/PREPARED.json'),
            prior_retirement=saved.bound(request['recovery_custody'])['files']['OWNER_RETIRED.json'],
            no_retirement_performed=True, no_retry=True))
        validate_successor(output / 'control/GUARD.json')
        require(time.time() + 300 < saved.read(go_path)['expires_unix'], 'recovery_GO_time_for_strict_successor')
        return supervise(output / 'control/GUARD.json')
    except BaseException as error:
        if started:
            saved.write(output / 'RECOVERY_FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
                no_retry=True, no_retirement_performed=True,
                recovery_disposition='PRESERVE_BOUND_CUSTODY_REVIEW_ACTUAL_ATTEMPT_NO_AUTOMATIC_RETRY'))
        raise
    finally:
        os.close(lock)


def execute(output, go_path, go_sha256):
    cpu_operator()
    output = saved.regular(output)
    request, old_config, old_plan, expected = activation_binding(output, go_path, go_sha256)
    require(Path(__file__).resolve() == Path(request['source_root']) / RELATIVE
            and Path(saved.__file__).resolve() == Path(request['source_root']) / saved.RELATIVE
            and Path(retelling.__file__).resolve() == Path(request['source_root']) / POLICY_RELATIVE,
            'execute_from_exact_successor_source_before_signals')
    pair = request['pair']
    lock = os.open(saved.BASE / ('orch_r157_' + request['agent'] + '_HANDOFF.lock'),
                   os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    descriptors = {}
    started = False
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'ACTIVATE_ONCE').mkdir()
        started = True
        saved.write(output / 'EXECUTION_GO.json', dict(go=saved.reference(go_path), no_retry=True))
        for role, process in pair.items():
            saved.same(process)
            descriptors[role] = os.pidfd_open(process['pid'])
            saved.same(process)
        deadline = min(time.monotonic() + expected['max_wait_seconds'],
            time.monotonic() + saved.read(go_path)['expires_unix'] - time.time() - 120)
        while time.monotonic() < deadline:
            for process in pair.values():
                saved.same(process)
            boundary = saved.saved_boundary(old_plan['root'])
            metadata = saved.readout(old_plan['root'], old_config, old_plan, boundary, pair['actor']) if boundary else None
            if boundary and boundary['index'] >= expected['earliest_boundary_index'] and metadata:
                break
            time.sleep(0.25)
        else:
            raise TimeoutError('no_boundary_old_native_left_running')
        activation_binding(output, go_path, go_sha256)
        saved.check_children(pair, metadata['identity']['pid'] if metadata['identity'] else None)
        with saved.pause_watchdog(descriptors['actor'], expected['max_pause_seconds']) as pause_deadline:
            saved.pause_exact(pair['actor'], descriptors['actor'])
            require(saved.saved_boundary(old_plan['root']) == boundary, 'selected_boundary_raced_no_retry')
            completion = saved.wait_readout(metadata, pause_deadline - 240)
            prepared = prepare(output, paused_pair=pair)
            require(prepared['plan']['sha256'] == expected['plan']['sha256'], 'exact_GO_plan_at_actual_boundary')
            validate_successor(output / 'control/GUARD.json', before_retirement=True)
            saved.write(output / 'ACTUAL_BOUNDARY_READY.json', dict(go=saved.reference(go_path),
                prepared=saved.reference(output / 'control/PREPARED.json'), readout_completion=completion,
                boundary=boundary['reference'], no_reset=True, ready_before_termination=True))
            activation_binding(output, go_path, go_sha256)
            require(time.monotonic() + 90 < pause_deadline
                    and time.time() + 300 < saved.read(go_path)['expires_unix'], 'time_for_strict_successor_before_stop')
            require(saved.saved_boundary(old_plan['root']) == boundary, 'same_final_boundary')
            check_paused(pair)
            saved.write(output / 'TERMINATION_INTENT.json', dict(pair=pair, go=saved.reference(go_path),
                ready=saved.reference(output / 'ACTUAL_BOUNDARY_READY.json'), no_retry=True))
            signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
            signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
            for role in ('actor', 'timer', 'supervisor'):
                require(bool(select.select([descriptors[role]], [], [], 20)[0]), 'natural_exact_owned_exit_' + role)
            saved.write(output / 'OWNER_RETIRED.json', dict(pair=pair, go=saved.reference(go_path),
                prepared=saved.reference(output / 'control/PREPARED.json'), same_life_root=old_plan['root'],
                reset=False, stopped_unix=time.time()))
        return supervise(output / 'control/GUARD.json')
    except BaseException as error:
        if started:
            saved.write(output / 'ACTIVATION_FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
                no_retry=True, termination_intent_recorded=(output / 'TERMINATION_INTENT.json').exists(),
                original_exit_confirmed=(output / 'OWNER_RETIRED.json').exists(),
                recovery_disposition='VERIFY_EXACT_OWNER_AND_SAVED_BOUNDARY_NO_AUTOMATIC_RETRY'))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


def supervise(config_path):
    config, plan = validate_successor(config_path)
    attempt = saved.regular(config['attempt_dir'])
    attempt.mkdir(mode=0o700)
    (attempt / 'DISPATCH_ONCE').mkdir(mode=0o700)
    saved.write(attempt / 'DISPATCH_ONCE.json', dict(go=config['r166_go'], config=saved.reference(config_path)))
    try:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + plan['source_root'], str(saved.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard',
            'scan', '--config', str(config_path)]
        report = json.loads(subprocess.check_output(command, cwd=plan['source_root'], text=True, timeout=100))
        saved.write(attempt / 'ADMISSION.json', report)
        require(report['clear'] is True and report['scanner_euid'] == 0 and report['blocking_reasons'] == []
                and report['gpu']['uuid'] == plan['gpu_uuid'] and report['gpu']['index'] == plan['physical']
                and report['device_minor'] == plan['physical'], 'original_full_exclusive_admission')
        saved.write(attempt / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
        validate_successor(config_path)
        command = strict_command(config, plan, config_path)['template']
        saved.write(attempt / 'CONTAINED_COMMAND.json', dict(command=command))
        result = subprocess.run(command, check=False)
        saved.write(attempt / 'SERVICE_EXIT.json', dict(returncode=result.returncode, no_retry=True))
        require(result.returncode == 0, 'strict_successor_failed_no_retry')
    except BaseException as error:
        saved.write(attempt / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error), no_retry=True))
        raise


def contained_native(config_path):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r153_community_runtime import verify_containment
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = validate_successor(config_path)
    attempt = Path(config['attempt_dir'])
    saved.write(attempt / 'CONTAINMENT_VERIFIED.json', verify_containment(config, plan))
    report = saved.read(attempt / 'ADMISSION.json')
    admitted = saved.read(attempt / 'ADMISSION_TIME.json')['verified_unix']
    require(report['clear'] is True and report['scanner_euid'] == 0 and report['blocking_reasons'] == []
            and report['gpu']['uuid'] == plan['gpu_uuid'] and report['gpu']['index'] == plan['physical']
            and report['device_minor'] == plan['physical'] and 0 <= time.time() - admitted < 100,
            'fresh_unchanged_admission_before_native')
    remaining = int(plan['hard_end_unix'] - time.time() - 10)
    require(remaining > 10, 'original_wall_time_for_resume')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's', str(saved.PYTHON),
               '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            timer = saved.identity(process.pid)
            publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=timer['start_ticks'],
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=saved.sha(attempt / 'ADMISSION.json'), guard_sha256=saved.sha(config_path),
                plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'],
                command_sha256=native.digest(command), hard_end_unix=plan['hard_end_unix'], no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            result = process.wait()
        saved.write(attempt / 'NATIVE_EXIT.json', dict(returncode=result, no_retry=True))
        require(result == 0, 'native_successor_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    staging = commands.add_parser('stage')
    staging.add_argument('--agent', choices=tuple(saved.TARGETS), required=True)
    staging.add_argument('--native-pid', type=int, required=True)
    staging.add_argument('--candidate-request', type=Path)
    staging.add_argument('--candidate-sha256')
    for name in ('config', 'directive', 'cpu', 'output', 'scope-document', 'followup-directive', 'addendum'):
        staging.add_argument('--' + name, type=Path, required=True)
    for action in ('prepare', 'verify', 'preflight'):
        commands.add_parser(action).add_argument('--output', type=Path, required=True)
    recovery_staging = commands.add_parser('stage-recovery')
    recovery_staging.add_argument('--cpu', type=Path, required=True)
    recovery_staging.add_argument('--output', type=Path, required=True)
    commands.add_parser('preflight-recovery').add_argument('--output', type=Path, required=True)
    recovery_operation = commands.add_parser('execute-recovery')
    recovery_operation.add_argument('--output', type=Path, required=True)
    recovery_operation.add_argument('--main-go', type=Path, required=True)
    recovery_operation.add_argument('--main-go-sha256', required=True)
    operation = commands.add_parser('execute')
    operation.add_argument('--output', type=Path, required=True)
    operation.add_argument('--main-go', type=Path, required=True)
    operation.add_argument('--main-go-sha256', required=True)
    commands.add_parser('contained-native').add_argument('--config', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action == 'stage':
        result = stage(args.agent, args.config, args.native_pid, args.directive, args.cpu, args.output,
                       scope_document=args.scope_document, followup_directive=args.followup_directive,
                       addendum=args.addendum, candidate_request=args.candidate_request,
                       candidate_sha256=args.candidate_sha256)
    elif args.action == 'prepare':
        result = prepare(args.output)
    elif args.action == 'preflight':
        result = preflight(args.output)
    elif args.action == 'stage-recovery':
        result = stage_recovery(args.cpu, args.output)
    elif args.action == 'preflight-recovery':
        result = preflight(args.output, recovery=True)
    elif args.action == 'execute-recovery':
        result = execute_recovery(args.output, args.main_go, args.main_go_sha256)
    elif args.action == 'execute':
        result = execute(args.output, args.main_go, args.main_go_sha256)
    elif args.action == 'contained-native':
        result = contained_native(args.config)
    else:
        request, unused_config, unused_plan = verify_request(args.output)
        result = dict(status='STAGED_SOURCE_VERIFIED_NO_EXECUTION', source_root=request['source_root'])
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
