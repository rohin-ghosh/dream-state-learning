"""Reconstruct and seal C2 epoch2 locally from exact staged hashes; no transport."""

import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys
import tarfile
import time


TOOLS = Path(__file__).resolve().parent
WORKER = TOOLS.parent
WORKERS = WORKER.parent
REPOSITORY = WORKER.parents[2]
ROLLOUT = WORKERS / 'post_recovery_retention_rollout_20260919'
PREIMAGE = WORKERS / 'rohin233_recovery_node4_20260918/private/port_C2'
RETENTION = WORKERS / 'post_recovery_retention_ports_20260919/C2'
THREE = {'gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def sha(path):
    return checksum(Path(path).read_bytes())


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(Path(path).read_bytes())


def relative_name(name):
    require(isinstance(name, str), 'relative_source_name_string')
    path = PurePosixPath(name)
    require(name == str(path) and path.parts and not path.is_absolute() and '..' not in path.parts,
        'literal_relative_source_name')
    return path


def publish(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def document(path, value):
    publish(path, encoded(value))


def delta(before, after):
    return {name: dict(before=before.get(name), after=after.get(name))
        for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)}


def locate(pins, roots):
    found = {}
    for name, expected in sorted(pins.items()):
        relative_name(name)
        for root in roots:
            path = root / name
            if path.is_file() and path.resolve() == path.absolute():
                content = path.read_bytes()
                if checksum(content) == expected:
                    found[name] = dict(origin=str(path), sha256=expected, content=content)
                    break
        require(name in found, 'missing_exact_C2_preimage:' + name)
    return found


def check_inputs(stage, observation):
    require(stage['life'] == observation['life'] == 'C2'
        and stage['status'] == 'IMMUTABLE_SOURCE_STAGED_NOT_DISPATCHABLE', 'exact_C2_epoch1_stage')
    require(stage['old_guard_sha256'] == observation['guard_sha256']
        and stage['old_source_pins'] == observation['source_pins']
        and stage['native'] == observation['native']
        and stage['journal_root'] == observation['journal_root']
        and stage['journal_id'] == observation['journal_id'], 'same_C2_inventory_guard_native_and_journal')
    require(delta(stage['old_source_pins'], stage['new_source_pins']) == stage['changed']
        and set(stage['changed']) == THREE, 'epoch1_has_exact_three_retention_changes')
    plan = observation['plan']
    require(plan['source_root'] == stage['old_source'] and plan['hard_end_unix'] == 1789927200
        and plan['lease_end_unix'] == 1789948800 and plan['physical'] == 1
        and plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance'
        and plan['learn_row_policy'] == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1', 'same_learned_C2_frozen_recipe_and_wall')
    require(str(Path(plan['root']) / 'stream') == stage['journal_root']
        and observation['guard_metadata']['copy_raw'] == plan['root'], 'original_life_copy_raw_journal')
    source = Path(stage['new_source'])
    require(source.is_absolute() and '..' not in source.parts and source.name == 'source'
        and source.parent.name == 'epoch1', 'literal_epoch1_source')


def plan_template(old, new_source):
    plan = deepcopy(old)
    startup = Path(old['startup_context']['path']).relative_to(old['source_root'])
    relative_name(str(startup))
    plan['source_root'] = str(new_source)
    plan['startup_context']['path'] = str(Path(new_source) / startup)
    plan.pop('authorized_wall_extension', None)
    restored = deepcopy(plan)
    restored['source_root'] = old['source_root']
    restored['startup_context']['path'] = old['startup_context']['path']
    if 'authorized_wall_extension' in old:
        restored['authorized_wall_extension'] = old['authorized_wall_extension']
    require(restored == old, 'source_relocation_and_consumed_authorization_only')
    return plan


def seal(directory):
    for path in directory.rglob('*'):
        require(not path.is_symlink(), 'no_links_in_immutable_C2_bundle')
        if path.is_file():
            with path.open('rb') as handle:
                os.fsync(handle.fileno())
            path.chmod(0o444)
    for path in sorted([directory, *[item for item in directory.rglob('*') if item.is_dir()]],
            key=lambda item: len(item.parts), reverse=True):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        path.chmod(0o555)


def prepare(output, python=sys.executable):
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(WORKER) and not output.exists(),
        'new_unused_worker_local_output_only')
    stage_path = ROLLOUT / 'C2_STAGED.json'
    inventory_path = ROLLOUT / 'node5_INVENTORY2.json'
    stage = read(stage_path)
    observation = next(row for row in read(inventory_path)['results'] if row['life'] == 'C2')
    check_inputs(stage, observation)
    paths = [stage_path, inventory_path, RETENTION / 'READY.json', RETENTION / 'TEST_RECEIPT.json',
        WORKER / 'READY.json', WORKER / 'TEST_RECEIPT.json', WORKER / 'ports.py',
        WORKER / 'c2_retention_runtime.py', WORKER / 'cpu_probe.py', RETENTION / 'test_retention.py',
        WORKERS / 'post_recovery_retention_boundary_20260918/boundary.py',
        *sorted(TOOLS.glob('*.py'))]
    inputs = {str(path): sha(path) for path in paths}
    retained = locate(stage['new_source_pins'], [RETENTION / 'fork', PREIMAGE])
    startup = Path(observation['plan']['startup_context']['path']).relative_to(observation['plan']['source_root'])
    relative_name(str(startup))
    startup_path = PREIMAGE / startup
    require(startup_path.resolve() == startup_path.absolute()
        and sha(startup_path) == observation['plan']['startup_context']['sha256'], 'exact_C2_startup_bytes')
    specification = importlib.util.spec_from_file_location('c2_epoch2_ports', WORKER / 'ports.py')
    ports = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(ports)
    additions = ports.proposed_ports(PREIMAGE)
    require(set(additions) == {'gpu/orch_r125_continual_native.py', 'gpu/c2_retention_runtime.py'}, 'two_adoption_port_files')
    pins = dict(stage['new_source_pins'])
    pins.update({name: checksum(content) for name, content in additions.items()})
    old_delta, epoch1_delta = delta(stage['old_source_pins'], pins), delta(stage['new_source_pins'], pins)
    require(set(old_delta) == THREE | set(additions) and set(epoch1_delta) == set(additions), 'five_live_deltas_two_epoch1_deltas')
    for name in ('gpu/r188_node5_confinement.py', 'gpu/orch_r125_continual_guard.py',
            'gpu/orch_r125_stream_journal.py', 'gpu/checkpoint_tail_runtime.py', 'gpu/r184_cpu_bridge.py'):
        require(pins[name] == stage['old_source_pins'][name], 'unchanged_confinement_guard_journal_reader_bridge:' + name)
    epoch = output / 'C2/epoch2'
    source = epoch / 'source'
    source.mkdir(parents=True)
    for name, entry in retained.items():
        content = additions.get(name, entry['content'])
        ast.parse(content, filename=name)
        publish(source / name, content)
    for name, content in additions.items():
        if name not in retained:
            ast.parse(content, filename=name)
            publish(source / name, content)
    publish(source / startup, startup_path.read_bytes())
    helpers = {'cpu_check.py': TOOLS / 'cpu_check.py', 'source_checks.py': TOOLS / 'source_checks.py',
        'cpu_probe.py': WORKER / 'cpu_probe.py', 'retention_cases.py': RETENTION / 'test_retention.py',
        'boundary.py': WORKERS / 'post_recovery_retention_boundary_20260918/boundary.py'}
    for name, path in helpers.items():
        publish(epoch / 'tools' / name, path.read_bytes())
    remote_source = Path(stage['new_source']).parent.parent / 'epoch2/source'
    template = plan_template(observation['plan'], remote_source)
    document(epoch / 'control/PLAN.template.json', template)
    document(epoch / 'control/ORIGINAL_GUARD_METADATA.json', observation['guard_metadata'])
    document(epoch / 'control/ORIGINAL_PLAN_OBSERVATION.json', dict(plan=observation['plan'],
        original_guard_plan_sha256=observation['guard_metadata']['plan_sha256'],
        observation_only_not_original_plan_file_bytes=True))
    native = stage['native']
    binding = dict({key: native[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id')},
        command=native['argv'], guard_path=observation['guard_path'], guard_sha256=stage['old_guard_sha256'],
        journal_id=stage['journal_id'], journal_root=stage['journal_root'], source_pins=stage['old_source_pins'],
        hard_end_unix=observation['plan']['hard_end_unix'])
    manifest = dict(schema='C2_EPOCH2_EXACT_LOCAL_SOURCE_V1', status='LOCAL_DECLARATION_NOT_REMOTE_STAGE_RECEIPT',
        life='C2', local_source=str(source), new_source=str(remote_source), old_source=stage['old_source'],
        epoch1_source=stage['new_source'], old_guard_sha256=stage['old_guard_sha256'],
        old_source_pins=stage['old_source_pins'], epoch1_source_pins=stage['new_source_pins'], new_source_pins=pins,
        changed=old_delta, epoch1_to_epoch2_delta=epoch1_delta, historical_life_binding=binding,
        native=native, native_binding_freshly_verified=False, journal_id=stage['journal_id'],
        journal_root=stage['journal_root'], deadline_unix=1789927200, lease_end_unix=1789948800,
        source_file_count=len(pins), original_stage_sha256=inputs[str(stage_path)],
        epoch1_file_origins={name: {key: value for key, value in entry.items() if key != 'content'}
            for name, entry in retained.items()},
        adoption_file_origins={name: dict(overlay=str(WORKER / 'overlay' / name), sha256=checksum(content))
            for name, content in additions.items()},
        additional_assets={str(startup): dict(origin=str(startup_path), sha256=sha(startup_path))},
        helper_pins={name: sha(epoch / 'tools' / name) for name in helpers},
        helper_scope='OUTSIDE_PINNED_SOURCE_TOOLS_NO_ADDITIONAL_RUNTIME_DELTAS',
        plan_template_sha256=sha(epoch / 'control/PLAN.template.json'), plan_template_candidate_bound=False,
        source_seal='FILES_0444_DIRECTORIES_0555_AFTER_LOCAL_CPU_PASS', source_admission_unchanged=True,
        historical_default_checkpoint=dict(complete_index=template['checkpoint_tail_recovery']['complete_index'],
            complete_sha256=template['checkpoint_tail_recovery']['complete_sha256'],
            role='HISTORICAL_CPU_VERIFICATION_ONLY_NOT_CURRENT_HANDOFF_BOUNDARY'),
        remote_staging_performed=False, receiving_plan_ready=False, admission_granted=False,
        native_signals=[], dispatches=[], bridge_changes=[], parent_deliveries=[])
    document(epoch / 'EPOCH2_SOURCE.json', manifest)
    document(epoch / 'SOURCE_PINS.json', pins)
    remote_epoch = remote_source.parent
    node_python = '/localhome/local-rohing/v2/venv/bin/python'
    commands = {mode: ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', node_python, '-B',
        str(remote_epoch / 'tools/cpu_check.py'), mode, '--bundle', str(remote_epoch)]
        for mode in ('source', 'checkpoint', 'tail')}
    commands['synthetic_source_tests'] = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        node_python, '-B', str(remote_epoch / 'tools/source_checks.py'), '--source', str(remote_source),
        '--manifest', str(remote_epoch / 'EPOCH2_SOURCE.json')]
    document(epoch / 'CPU_INVOCATIONS.json', dict(commands=commands, invoked_on_node=False,
        one_shot_no_loop=True, no_GPU_calls=True, timeout_seconds_recommended=120,
        checkpoint_default=manifest['historical_default_checkpoint'],
        changed_checkpoint_requires_both_flags=['--complete-index', '--complete-sha256'],
        tail_refuses_if_no_current_complete_pair=True, CPU_results_are_not_dispatch_authority=True))
    document(epoch / 'control/REQUIRED_LIVE_EVIDENCE.json', dict(
        blockers=['Main_transport_to_new_immutable_epoch2_and_full_pin_verification',
            'fresh_old_native_identity_and_exact_five_delta_source_authority',
            'original_WALL_EXTENDED_record_and_intent', 'current_COMPLETE_LEARN_and_node_checkpoint_tail_guard_CPU',
            'unchanged_r188_privileged_admission_route', 'old_bridge_and_parent_owner_fence_and_rebind_proof',
            'real_prefix_latency_and_uid_access_builder_allocation_checks'],
        no_automatic_parent_adoption=True, original_bridge_unchanged=True, complete_reserved=False,
        deadline_unix=1789927200, admission_granted=False, dispatchable=False))
    document(output / 'INPUTS.json', dict(input_sha256=inputs, startup_sha256=sha(startup_path),
        all_183_epoch1_python_preimages_locally_matched=True, no_remote_observation=True))
    scratch = output / 'scratch'
    scratch.mkdir()
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), TMPDIR=str(scratch), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    command = [str(python), '-B', str(epoch / 'tools/source_checks.py'), '--source', str(source),
        '--manifest', str(epoch / 'EPOCH2_SOURCE.json')]
    started = time.monotonic()
    tested = subprocess.run(command, cwd=source, env=environment, capture_output=True, text=True, timeout=120)
    publish(epoch / 'cpu/SOURCE_TESTS.stdout', tested.stdout.encode())
    publish(epoch / 'cpu/SOURCE_TESTS.stderr', tested.stderr.encode())
    require(tested.returncode == 0, 'source_specific_CPU_tests_failed:' + str(epoch / 'cpu/SOURCE_TESTS.stderr'))
    evidence = json.loads(tested.stdout)
    require(evidence['passed'] is True and evidence['synthetic_only'] is True
        and evidence['source_pins'] == pins and evidence['GPU_calls'] == evidence['dispatches'] == 0,
        'exact_source_specific_synthetic_CPU_proof')
    local_cpu = dict(schema='C2_EPOCH2_LOCAL_SOURCE_CPU_V1', passed=True, source_pins=pins,
        scope='SYNTHETIC_ACTUAL_SOURCE_ONLY', command=command, elapsed_seconds=time.monotonic() - started,
        result=evidence, live_handoff_authorization=False, actual_checkpoint_validated=False,
        actual_guard_validated=False, admission_granted=False,
        stdout_sha256=sha(epoch / 'cpu/SOURCE_TESTS.stdout'), stderr_sha256=sha(epoch / 'cpu/SOURCE_TESTS.stderr'))
    document(epoch / 'cpu/LOCAL_SOURCE_CPU.json', local_cpu)
    verify_command = [str(python), '-B', str(epoch / 'tools/cpu_check.py'), 'source', '--bundle', str(epoch)]
    verification = subprocess.run(verify_command, cwd=source, env=environment, capture_output=True, text=True, timeout=30)
    publish(epoch / 'cpu/SOURCE_VERIFY.stdout', verification.stdout.encode())
    publish(epoch / 'cpu/SOURCE_VERIFY.stderr', verification.stderr.encode())
    require(verification.returncode == 0 and json.loads(verification.stdout)['passed'], 'portable_source_verifier_passed')
    require(all(sha(Path(path)) == expected for path, expected in inputs.items())
        and all(sha(Path(entry['origin'])) == entry['sha256'] for entry in retained.values()),
        'all_inputs_epoch1_and_preimage_bytes_preserved')
    require({str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')} == pins,
        'source_bytes_unchanged_after_CPU_tests')
    now = datetime.now(timezone.utc).isoformat()
    document(epoch / 'LOCAL_PREPARATION.json', dict(schema='C2_EPOCH2_LOCAL_PREPARATION_V1',
        status='LOCAL_SOURCE_CPU_READY_NOT_REMOTELY_STAGED', observed_utc=now,
        source_manifest_sha256=sha(epoch / 'EPOCH2_SOURCE.json'),
        local_CPU_sha256=sha(epoch / 'cpu/LOCAL_SOURCE_CPU.json'), source_tests=evidence['tests_run'],
        helper_pins=manifest['helper_pins'], input_bytes_unchanged=True, source_sealed=True,
        source_file_count=len(pins), source_bytes=sum(path.stat().st_size for path in source.rglob('*') if path.is_file()),
        live_checkpoint_validated=False, live_native_changed=False, old_bridge_changed=False,
        remote_stage_performed=False, native_signals=[], dispatches=[], parent_deliveries=[]))
    seal(source)
    seal(epoch / 'tools')
    archive_path = output / 'C2_EPOCH2_BUNDLE.tar.gz'
    with tarfile.open(archive_path, 'x:gz') as archive:
        archive.add(epoch, arcname='C2/epoch2', recursive=True)
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive.getmembers():
            require(member.isdir() or member.isfile(), 'regular_portable_bundle_members_only')
            require(not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,
                'relative_safe_bundle_members')
            if member.isfile():
                local = output / member.name
                require(checksum(archive.extractfile(member).read()) == sha(local), 'archive_matches_exact_prepared_files')
    summary = dict(schema='C2_EPOCH2_LOCAL_READY_V1', status='LOCAL_IMMUTABLE_CPU_READY_NOT_DISPATCHABLE',
        observed_utc=now, epoch=str(epoch), local_source=str(source), proposed_node_source=str(remote_source),
        manifest=str(epoch / 'EPOCH2_SOURCE.json'), manifest_sha256=sha(epoch / 'EPOCH2_SOURCE.json'),
        local_cpu_receipt=str(epoch / 'cpu/LOCAL_SOURCE_CPU.json'), local_cpu_sha256=sha(epoch / 'cpu/LOCAL_SOURCE_CPU.json'),
        archive=str(archive_path), archive_sha256=sha(archive_path), archive_bytes=archive_path.stat().st_size,
        source_python_files=len(pins), additional_assets=len(manifest['additional_assets']), source_tests=evidence['tests_run'],
        changed=old_delta, epoch1_to_epoch2_delta=epoch1_delta, hard_end_unix=1789927200,
        receiving_plan_ready=False, live_handoff_authorization=False, remote_staging_performed=False,
        input_bytes_unchanged=True, native_signals=[], dispatches=[], bridge_changes=[], parent_deliveries=[])
    document(output / 'READY.json', summary)
    publish(output / 'BUILDER_PROVENANCE.md', ('# Local C2 epoch2 preparation\n\n[Builder] ' + now +
        ' Non-material continuity repair: exact epoch1 preimages reconstructed, five old-live deltas '
        '(two beyond epoch1), standalone CPU tools and source-specific synthetic tests. '
        'No remote staging, live checkpoint claim, native signals, parent delivery, bridge change or dispatch.\n').encode())
    publish(output / 'MAIN_HANDOFF.md', ('# Main: concrete C2 epoch2 bundle\n\n'
        'All source files are exact hashes; source/tools are sealed 0444/0555. '
        'Transport and staging have NOT happened. Preserve epoch1 and the running original.\n\n'
        'Proposed new node source: `' + str(remote_source) + '`. '
        'Use the full five-entry `changed` map for old-live authority; '
        '`epoch1_to_epoch2_delta` has only two entries. Do not add the tools to the pinned source.\n\n'
        'One-shot CPU invocations after Main stages and verifies the bundle:\n\n```bash\n' +
        '\n'.join(shlex.join(command) for command in commands.values()) + '\n```\n\n'
        'The default checkpoint command checks only the old, exactly pinned COMPLETE ' +
        str(template['checkpoint_tail_recovery']['complete_index']) +
        ', not a current handoff. A newer selection requires both index and hash. '
        'Tail mode reads a current COMPLETE/LEARN or refuses immediately, never signals/retries. '
        'Guard mode needs Main\'s actually prepared guard via `--guard`; no guard is fabricated here.\n\n'
        'Actual same-node Torch checkpoint/RNG validation remains to be run by Main. '
        'The local receipt is synthetic actual-source evidence, not live-handoff authority. '
        'The scanner hashes retained prefix bytes (not O(tail)); no historical body-replay fallback. '
        'Wall proof, current source authority, old bridge/parent fence and r188 admission remain required.\n').encode())
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', default=sys.executable)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.output, arguments.python), sort_keys=True, indent=2))
