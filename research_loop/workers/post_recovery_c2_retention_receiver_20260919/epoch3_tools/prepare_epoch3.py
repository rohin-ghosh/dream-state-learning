"""Create a new immutable local epoch3; never stage remotely or activate C2."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time

import manifest_checks as checks


TOOLS = Path(__file__).resolve().parent
WORKER = TOOLS.parent
REPOSITORY = WORKER.parents[2]
EPOCH2_ROOT = WORKER / 'prepared_epoch2_v2'
EPOCH2 = EPOCH2_ROOT / 'C2/epoch2'
PORT = WORKER.parent / 'post_recovery_pair_receiving_checks_20260919/frontier_port.py'
TESTS = ('test_orch_r124_train_history.py', 'test_orch_r125_continual_stream.py',
    'test_orch_r125_stream_journal.py')


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


base = load('c2_epoch3_preparation_utilities', WORKER / 'epoch2_tools/prepare_epoch2.py')
require, sha, publish, document = base.require, base.sha, base.publish, base.document


def snapshot(root):
    result = {}
    for path in sorted([root, *root.rglob('*')]):
        require(not path.is_symlink(), 'no_links_in_immutable_input')
        result[str(path.relative_to(root))] = dict(mode=path.stat().st_mode & 0o777,
            sha256=sha(path) if path.is_file() else None)
    return result


def validate_output(output):
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(WORKER)
        and not output.exists(), 'new_unused_worker_local_output_only')
    return output


def exact_port(original, port_bytes):
    require(hashlib.sha256(original).hexdigest() == checks.BEFORE, 'exact_epoch2_history_preimage')
    require(hashlib.sha256(port_bytes).hexdigest() == checks.PORT, 'exact_Main_four_seam_port')
    namespace = {'__name__': 'pinned_c2_frontier_port'}
    exec(compile(port_bytes, '<pinned_Main_frontier_port>', 'exec'), namespace)
    proposed = namespace['port'](original)
    require(hashlib.sha256(proposed).hexdigest() == checks.AFTER, 'exact_epoch3_history_postimage')
    reversed_bytes = proposed
    for before, after in reversed(namespace['EDITS']):
        require(reversed_bytes.count(after.encode()) == 1, 'one_exact_reverse_seam')
        reversed_bytes = reversed_bytes.replace(after.encode(), before.encode(), 1)
    require(reversed_bytes == original, 'four_seam_inverse_recovers_epoch2_exactly')
    return proposed


def portable_checker(content):
    text = content.decode()
    seam = 'def verify_source(source, manifest):\n'
    require(text.count(seam) == 1, 'one_portable_checker_seam')
    text = text.replace(seam, seam + "    validator = load('c2_epoch3_manifest_validator', Path(__file__).with_name('manifest_checks.py'))\n"
        + '    validator.verify(source, manifest)\n', 1)
    text = text.replace('EPOCH2_SOURCE.json', 'EPOCH3_SOURCE.json').replace('C2_EPOCH2_', 'C2_EPOCH3_')
    text = text.replace('entire_exact_C2_epoch2_python_closure', 'entire_exact_C2_epoch3_python_closure')
    text = text.replace('five_old_live_deltas_two_epoch1_deltas_same_wall',
        'five_live_deltas_preserved_historical_epoch1_epoch2_map_same_wall')
    compile(text, '<epoch3_portable_checker>', 'exec')
    return text.encode()


def run_check(epoch, name, command, environment, timeout=180):
    started = time.monotonic()
    result = subprocess.run(command, cwd=epoch / 'source', env=environment,
        capture_output=True, text=True, timeout=timeout)
    publish(epoch / 'cpu' / (name + '.stdout'), result.stdout.encode())
    publish(epoch / 'cpu' / (name + '.stderr'), result.stderr.encode())
    require(result.returncode == 0, 'CPU_check_failed:' + str(epoch / 'cpu' / (name + '.stderr')))
    evidence = json.loads(result.stdout)
    require(evidence['passed'] is True, 'CPU_check_must_pass')
    document(epoch / 'cpu' / (name + '.json'), dict(schema='C2_EPOCH3_LOCAL_CPU_V1',
        command=command, elapsed_seconds=time.monotonic() - started, evidence=evidence,
        source_manifest_sha256=sha(epoch / 'EPOCH3_SOURCE.json'),
        synthetic_only=True, live_handoff_authorization=False))
    return evidence


def prepare(output, python=sys.executable):
    output = validate_output(output)
    before = snapshot(EPOCH2_ROOT)
    require(sha(EPOCH2 / 'EPOCH2_SOURCE.json') == checks.EPOCH2, 'exact_sealed_epoch2_manifest')
    old = base.read(EPOCH2 / 'EPOCH2_SOURCE.json')
    old_checker = load('c2_epoch2_source_verifier', EPOCH2 / 'tools/cpu_check.py')
    old_checker.verify_source(EPOCH2 / 'source', old)
    for name, expected in old['helper_pins'].items():
        require(sha(EPOCH2 / 'tools' / name) == expected, 'exact_epoch2_helper:' + name)
    original = (EPOCH2 / 'source' / checks.HISTORY).read_bytes()
    port_bytes = PORT.read_bytes()
    proposed = exact_port(original, port_bytes)
    snapshots = {name: (REPOSITORY / 'tests' / name).read_bytes() for name in TESTS}
    epoch = output / 'C2/epoch3'
    source = epoch / 'source'
    source.mkdir(parents=True)
    for path in (EPOCH2 / 'source').rglob('*'):
        if path.is_file():
            publish(source / path.relative_to(EPOCH2 / 'source'), path.read_bytes())
    patch_lines = list(difflib.unified_diff(original.decode().splitlines(True),
        proposed.decode().splitlines(True), fromfile='a/' + checks.HISTORY, tofile='b/' + checks.HISTORY))
    publish(epoch / 'FRONTIER.patch', ''.join(patch_lines).encode())
    patch_text = '*** Begin Patch\n*** Update File: ' + str(source / checks.HISTORY) + '\n'
    patch_text += ''.join('@@\n' if line.startswith('@@ ') else line for line in patch_lines[2:])
    patch_text += '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch_text, text=True, capture_output=True, check=True,
        cwd=WORKER, timeout=30)
    require((source / checks.HISTORY).read_bytes() == proposed, 'apply_patch_matches_exact_port_output')
    helpers = {name: (EPOCH2 / 'tools' / name).read_bytes() for name in old['helper_pins']}
    helpers['cpu_check.py'] = portable_checker(helpers['cpu_check.py'])
    helpers.update({name: (TOOLS / name).read_bytes() for name in ('manifest_checks.py', 'frontier_checks.py')})
    helpers.update({'frontier_port.py': port_bytes, 'epoch2_history.py': original})
    helpers.update({'snapshots/' + name: content for name, content in snapshots.items()})
    for name, content in helpers.items():
        publish(epoch / 'tools' / name, content)
    remote = Path('/localhome/local-rohing/orch_retention_20260919/C2/epoch3')
    previous_plan = base.read(EPOCH2 / 'control/PLAN.template.json')
    plan = base.plan_template(previous_plan, remote / 'source')
    document(epoch / 'control/PLAN.template.json', plan)
    for name in ('ORIGINAL_GUARD_METADATA.json', 'ORIGINAL_PLAN_OBSERVATION.json'):
        publish(epoch / 'control' / name, (EPOCH2 / 'control' / name).read_bytes())
    pins = dict(old['new_source_pins'], **{checks.HISTORY: checks.AFTER})
    manifest = deepcopy(old)
    manifest.update(schema='C2_EPOCH3_EXACT_LOCAL_SOURCE_V1', local_source=str(source),
        new_source=str(remote / 'source'), epoch2_source=old['new_source'],
        epoch2_manifest_sha256=checks.EPOCH2, epoch2_source_pins=old['new_source_pins'],
        new_source_pins=pins, changed=base.delta(old['old_source_pins'], pins),
        epoch2_to_epoch3_delta=base.delta(old['new_source_pins'], pins),
        epoch1_to_epoch3_delta=base.delta(old['epoch1_source_pins'], pins),
        frontier_port_origin=str(PORT), frontier_port_sha256=checks.PORT,
        frontier_patch_sha256=sha(epoch / 'FRONTIER.patch'), four_seam_inverse_verified=True,
        frontier_test_snapshot_pins={'snapshots/' + name: base.checksum(content) for name, content in snapshots.items()},
        source_file_origins={name: dict(origin=str(EPOCH2 / 'source' / name), input_sha256=value,
            output_sha256=pins[name], transformation='Main_four_seam_port' if name == checks.HISTORY else 'byte_copy')
            for name, value in old['new_source_pins'].items()},
        helper_pins={name: base.checksum(content) for name, content in helpers.items()},
        plan_template_sha256=sha(epoch / 'control/PLAN.template.json'))
    checks.verify(source, manifest)
    document(epoch / 'EPOCH3_SOURCE.json', manifest)
    document(epoch / 'SOURCE_PINS.json', pins)
    publish(epoch / 'control/EPOCH2_MANIFEST.preimage.json', (EPOCH2 / 'EPOCH2_SOURCE.json').read_bytes())
    blocks = base.read(EPOCH2 / 'control/REQUIRED_LIVE_EVIDENCE.json')
    blocks['blockers'][0] = 'Main_transport_to_new_immutable_epoch3_and_full_pin_verification'
    blocks['blockers'].append('actual_C2_checkpoint_history_byte_equivalence_and_latency_not_pair_inference')
    document(epoch / 'control/REQUIRED_LIVE_EVIDENCE.json', blocks)
    node_python = '/localhome/local-rohing/v2/venv/bin/python'
    prefix = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', node_python, '-B']
    commands = {mode: prefix + [str(remote / 'tools/cpu_check.py'), mode, '--bundle', str(remote)]
        for mode in ('source', 'checkpoint', 'tail')}
    for name in ('source_checks', 'frontier_checks'):
        commands[name] = prefix + [str(remote / 'tools' / (name + '.py')), '--source', str(remote / 'source'),
            '--manifest', str(remote / 'EPOCH3_SOURCE.json')]
    document(epoch / 'CPU_INVOCATIONS.json', dict(commands=commands, invoked_on_node=False,
        guard_requires_Main_actual_path=True, checkpoint_default=manifest['historical_default_checkpoint'],
        newer_checkpoint_requires=['--complete-index', '--complete-sha256'], one_shot_no_retry_or_signals=True,
        CPU_results_are_not_dispatch_authority=True, timeout_seconds_recommended=180))
    scratch = output / 'scratch'
    scratch.mkdir()
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), TMPDIR=str(scratch), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    results = {}
    for name, filename in (('LOCAL_SOURCE_CPU', 'source_checks.py'), ('FRONTIER_CPU', 'frontier_checks.py')):
        command = [str(python), '-B', str(epoch / 'tools' / filename), '--source', str(source),
            '--manifest', str(epoch / 'EPOCH3_SOURCE.json')]
        results[name] = run_check(epoch, name, command, environment)
    run_check(epoch, 'SOURCE_VERIFY', [str(python), '-B', str(epoch / 'tools/cpu_check.py'),
        'source', '--bundle', str(epoch)], environment)
    require(snapshot(EPOCH2_ROOT) == before, 'entire_epoch2_tree_bytes_and_modes_unchanged')
    checks.verify(source, manifest)
    document(output / 'INPUTS.json', dict(epoch2_tree=before, epoch2_unchanged=True,
        port_sha256=checks.PORT, test_snapshot_pins=manifest['frontier_test_snapshot_pins'],
        preparer_pins={path.name: sha(path) for path in TOOLS.glob('*.py')}))
    base.seal(source)
    base.seal(epoch / 'tools')
    now = datetime.now(timezone.utc).isoformat()
    document(epoch / 'LOCAL_PREPARATION.json', dict(observed_utc=now, source_sealed=True,
        source_python_files=len(pins), tests={name: result['tests_run'] for name, result in results.items()},
        epoch2_unchanged=True, non_material_performance_repair=True, admission_granted=False,
        actual_C2_checkpoint_validated=False, C2_latency_validated=False, dispatchable=False))
    archive_path = output / 'C2_EPOCH3_BUNDLE.tar.gz'
    with tarfile.open(archive_path, 'x:gz') as archive:
        archive.add(epoch, arcname='C2/epoch3', recursive=True)
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = set()
        for member in archive.getmembers():
            require(member.isdir() or member.isfile(), 'regular_portable_bundle_members_only')
            require(not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                and member.name not in members, 'safe_unique_archive_members')
            members.add(member.name)
            if member.isfile():
                require(base.checksum(archive.extractfile(member).read()) == sha(output / member.name),
                    'exact_archive_member_bytes')
    require(snapshot(EPOCH2_ROOT) == before, 'epoch2_still_unchanged_after_packaging')
    summary = dict(schema='C2_EPOCH3_LOCAL_READY_V1', status='LOCAL_IMMUTABLE_CPU_TESTED_NOT_DISPATCHABLE',
        observed_utc=now, manifest=str(epoch / 'EPOCH3_SOURCE.json'), manifest_sha256=sha(epoch / 'EPOCH3_SOURCE.json'),
        local_source=str(source), proposed_node_source=str(remote / 'source'), archive=str(archive_path),
        archive_sha256=sha(archive_path), archive_bytes=archive_path.stat().st_size,
        source_python_files=len(pins), epoch2_to_epoch3_delta=manifest['epoch2_to_epoch3_delta'],
        tests={name: result['tests_run'] for name, result in results.items()},
        receipts={name: dict(path=str(epoch / 'cpu' / (name + '.json')),
            sha256=sha(epoch / 'cpu' / (name + '.json'))) for name in (*results, 'SOURCE_VERIFY')},
        epoch2_unchanged=True, four_seam_inverse_verified=True, receiving_plan_ready=False,
        C2_real_checkpoint_validated=False, C2_latency_validated=False, remote_staging_performed=False,
        live_handoff_authorization=False, admission_granted=False, native_signals=[], dispatches=[],
        bridge_changes=[], parent_deliveries=[], hard_end_unix=1789927200, blockers=blocks['blockers'])
    document(output / 'READY.json', summary)
    publish(output / 'MAIN_HANDOFF.md', ('# C2 epoch3: local concrete closure, NOT dispatchable\n\n'
        '[Builder] ' + now + ' Non-material byte-equivalent frontier cache; exactly one change beyond epoch2.\n\n'
        'Epoch2, live/native, old r188, journal, checkpoint-tail reader and bridge are unchanged. '
        'Only Main may stage this bundle to the new proposed path. Five old-live changed filenames; '
        'three epoch1-to-epoch3 deltas; one epoch2-to-epoch3 delta. Historical epoch1-to-epoch2 map retained.\n\n'
        '## Source-specific CPU commands (not executed on node)\n\n```bash\n' +
        '\n'.join(shlex.join(command) for command in commands.values()) + '\n```\n\n'
        'The checkpoint default is historical COMPLETE11502, not current handoff authority. '
        'A new checkpoint requires both its authentic index and SHA256. Current-tail mode is one-shot '
        'and refuses absent a current COMPLETE+LEARN pair. Main owns scanner and anchor work.\n\n'
        '## Concrete blockers\n\n' + '\n'.join('- ' + item for item in blocks['blockers']) + '\n\n'
        'Pair checkpoint timings are not C2 checkpoint/latency evidence. Original WALL_EXTENDED record '
        'and intent are still needed; plan authorization alone is insufficient. Hard end1789927200 unchanged. '
        'No current candidate/guard, native/parent fence, node-side checkpoint proof or admission is fabricated.\n\n'
        '## Mandatory original route\n\n'
        '`/localhome/local-rohing/v2/venv/bin/python -B -m gpu.r188_node5_confinement dispatch '
        '--config <Main actual receiving GUARD>` remains the only eventual route (NOT invoked). '
        'It requires exact-source RECEIVING_CPU.json, once-only outer claim, confinement probe, fresh '
        'privileged admission, uid/gid2524, NoNewPrivileges, no capabilities and only GPU1/control devices. '
        'No direct guard dispatch, service changes, restarts or parent adoption are authorized by this bundle.\n').encode())
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output, args.python), sort_keys=True, indent=2))
