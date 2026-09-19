"""Prepare a separate, synthetic-only C2 epoch4 proposal; never activate it."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import ports


TOOLS = Path(__file__).resolve().parent
WORKER = TOOLS.parent
REPOSITORY = WORKER.parents[2]
PREVIOUS = WORKER / 'prepared_epoch3_v1/C2/epoch3'
KUHN = WORKER.parent / 'post_recovery_prefix_proof_20260919'
BANACH = WORKER.parent / 'post_recovery_pair_retention_receiver_20260919'


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


base = load('c2_epoch4_local_prepare_utilities', WORKER / 'epoch2_tools/prepare_epoch2.py')
require, publish, document, sha = base.require, base.publish, base.document, base.sha


def snapshot(root):
    return {str(path.relative_to(root)): dict(mode=path.stat().st_mode & 0o777,
        sha256=sha(path) if path.is_file() else None) for path in (root, *root.rglob('*'))}


def source_checker(content):
    result = content.replace(b'EPOCH3_SOURCE.json', b'EPOCH4_SOURCE.json').replace(b'C2_EPOCH3_', b'C2_EPOCH4_')
    result = result.replace(b"len(manifest['changed']) == 5", b"len(manifest['changed']) == 9")
    beginning = result.index(b'def verify_source(')
    ending = result.index(b'\ndef ', beginning + 4)
    result = result[:beginning] + (b'def verify_source(source, manifest):\n'
        b'    from manifest_checks import verify\n    return verify(source, manifest)\n\n') + result[ending:]
    return result


def source_cases(content, reader_hash):
    old = b"'gpu/checkpoint_tail_runtime.py': '972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e'"
    require(content.count(old) == 1, 'one_explicit_reader_expectation_in_legacy_tests')
    return content.replace(old, ("'gpu/checkpoint_tail_runtime.py': '" + reader_hash + "'").encode(), 1)


def probe_port(content):
    result = ports.replace_once(content, 'def readonly_tail(source, candidate, selection):\n',
        'def readonly_tail(source, candidate, selection, prefix_arguments=None):\n')
    result = ports.replace_once(result, '        state = scan(journal, selection)\n',
        '        state = scan(journal, selection, **(prefix_arguments or {}))\n')
    result = ports.replace_once(result, '    journal = object.__new__(ReadOnlyJournal)\n',
        '    journal = object.__new__(ReadOnlyJournal if prefix_arguments is None else StreamJournal)\n')
    result = ports.replace_once(result, 'def probe(source, candidate, plan, mode, selection=None):\n',
        'def probe(source, candidate, plan, mode, selection=None, prefix_context=None):\n')
    result = ports.replace_once(result, '        return readonly_tail(source, candidate, selection)\n',
        '        if prefix_context is None:\n'
        '            return readonly_tail(source, candidate, selection)\n'
        '        from gpu.orch_r125_continual_guard import validate\n'
        '        from gpu.c2_prefix_authority import admitted_prefix, reader_arguments\n'
        '        guard_path = prefix_context["receiver"]["guard_path"]\n'
        '        config, validated = validate(guard_path)\n'
        '        require(validated == plan and plan["source_root"] == str(source), "same_original_CPU_guard_plan")\n'
        '        with admitted_prefix(config, plan, guard_path=guard_path):\n'
        '            arguments = reader_arguments(plan, prefix_context, selection)\n'
        '            return readonly_tail(source, candidate, selection, arguments)\n')
    result = ports.replace_once(result,
        "        result = probe(request['source'], request['candidate'], request['plan'], arguments.mode, request.get('selection'))\n",
        "        result = probe(request['source'], request['candidate'], request['plan'], arguments.mode,\n"
        "            request.get('selection'), request.get('prefix_context'))\n")
    return result


def receiver_port(content):
    result = ports.replace_once(content,
        'from research_loop.workers.post_recovery_c2_retention_receiver_20260919.ports import changes_for, NATIVE, RUNTIME\n',
        'from source_delta import changes_for, NATIVE, RUNTIME, READER, PROOF, AUTHORITY, GUARD\n')
    result = ports.replace_once(result, '            python_executable, route=None):\n',
        '            python_executable, route=None, prefix_control=None):\n')
    result = ports.replace_once(result, '        self.prepared = None\n',
        '        self.prepared = None\n        self.prefix_control = prefix_control\n        self.prefix_context = None\n')
    result = ports.replace_once(result,
        "        require(set(prepared['old_source_pins']) | {RUNTIME} == set(prepared['new_source_pins'])\n"
        "            and changes == stage['changed'] and set(changes) == CHANGED_FILES | {NATIVE, RUNTIME}\n",
        "        require(set(prepared['old_source_pins']) | {RUNTIME, PROOF, AUTHORITY} == set(prepared['new_source_pins'])\n"
        "            and changes == stage['changed'] and set(changes) == CHANGED_FILES | {NATIVE, RUNTIME, READER, PROOF, AUTHORITY, GUARD}\n")
    result = ports.replace_once(result, '        self.prepared = deepcopy(prepared)\n',
        '        if self.prefix_control is not None:\n'
        '            self.prefix_control.attach_cpu_authority(cpu)\n'
        '        self.prepared = deepcopy(prepared)\n')
    result = ports.replace_once(result,
        '        request = dict(source=str(self.source), candidate=candidate, plan=plan, selection=selection)\n',
        '        request = dict(source=str(self.source), candidate=candidate, plan=plan, selection=selection)\n'
        '        timeout = 120\n'
        '        if self.prefix_control is not None:\n'
        '            require(self.prefix_control.reservation_budget is not None, "bounded_prefix_probe_only")\n'
        '            if mode == "tail":\n'
        '                require(self.prefix_context is not None, "original_admission_CPU_context_required")\n'
        '                request["prefix_context"] = self.prefix_context\n')
    result = ports.replace_once(result, '        result = subprocess.run([self.python,',
        '        if self.prefix_control is not None:\n'
        '            timeout = self.prefix_control.reservation_budget.timeout(120)\n'
        '        result = subprocess.run([self.python,')
    result = ports.replace_once(result, '            text=True, timeout=120, check=True)\n',
        '            text=True, timeout=timeout, check=True)\n')
    result = ports.replace_once(result,
        "        scanned = self._probe('tail', candidate, plan, plan['checkpoint_tail_recovery'])\n",
        '        prefix_binding = None\n'
        '        if self.prefix_control is not None:\n'
        '            prefix_binding = self.prefix_control.derive_selection(prepared, plan,\n'
        '                plan["checkpoint_tail_recovery"], write_once, self.control / "prefix_selections")\n'
        "        scanned = self._probe('tail', candidate, plan, plan['checkpoint_tail_recovery'])\n")
    begin = result.index(b'        attempt = self.control /')
    end = result.index(b'        parent = dict(', begin)
    guard_block = result[begin:end]
    late_lines = (b"        write_once(attempt / 'TAIL_CPU.json', scanned)\n",
        b"        write_once(attempt / 'PLAN_METADATA_RECEIPTS.json', receipts)\n")
    for line in late_lines:
        require(guard_block.count(line) == 1, 'exact_receiver_guard_move_seam')
        guard_block = guard_block.replace(line, b'')
    require(guard_block.count(b"        write_once(attempt / 'RECEIVING_CPU.json', read(self.cpu_receipt_path))\n") == 1,
        'one_original_receiving_CPU_copy_seam')
    guard_block = guard_block.replace(
        b"        write_once(attempt / 'RECEIVING_CPU.json', read(self.cpu_receipt_path))\n",
        b'        receiving_cpu = read(self.cpu_receipt_path)\n'
        b'        if self.prefix_control is not None:\n'
        b'            receiving_cpu = self.prefix_control.receiving_cpu(receiving_cpu, plan,\n'
        b'                prepared["new_source_pins"], plan["checkpoint_tail_recovery"])\n'
        b"        write_once(attempt / 'RECEIVING_CPU.json', receiving_cpu)\n", 1)
    result = result[:begin] + b''.join(late_lines) + result[end:]
    seam = b"        scanned = self._probe('tail', candidate, plan, plan['checkpoint_tail_recovery'])\n"
    guard_block += (b'        if self.prefix_control is not None:\n'
        b'            self.prefix_context = self.prefix_control.cpu_context(prepared, plan, attempt / "GUARD.json")\n')
    require(result.count(seam) == 1, 'guard_before_tail_exact_seam')
    result = result.replace(seam, guard_block + seam, 1)
    result = ports.replace_once(result,
        "            and scanned['prefix_work'] == 'ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY'\n",
        "            and scanned['prefix_work'] == ('ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY'\n"
        "                if self.prefix_control is None else 'EXTERNALLY_PINNED_PREHASH_PLUS_IMMUTABLE_METADATA_RECHECK')\n")
    result = ports.replace_once(result,
        '        verify_receiver_plan(self.binding, prepared, receiver, candidate)\n',
        '        if prefix_binding is not None:\n'
        '            receiver["prefix_binding"] = prefix_binding\n'
        '            receiver["artifact_pins"][prefix_binding["selection_guard"]["path"]] = prefix_binding["selection_guard"]["sha256"]\n'
        '        verify_receiver_plan(self.binding, prepared, receiver, candidate)\n')
    result = ports.replace_once(result,
        "        attempt = Path(receiver['guard_path']).parent\n",
        '        if self.prefix_control is not None:\n'
        '            require(receiver.get("prefix_binding") == self.prefix_control.selection_binding, "same_prefix_binding")\n'
        '            self.prefix_control.reader_argument(receiver["plan"], self.prepared["new_source_pins"],\n'
        '                receiver["plan"]["checkpoint_tail_recovery"])\n'
        "        attempt = Path(receiver['guard_path']).parent\n")
    return result


def prepare(output):
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(WORKER) and not output.exists(), 'new_worker_output_only')
    old_tree = snapshot(WORKER / 'prepared_epoch3_v1')
    old = base.read(PREVIOUS / 'EPOCH3_SOURCE.json')
    require(sha(PREVIOUS / 'EPOCH3_SOURCE.json') == 'b3cd913e0254c98eb5eb90d77f75e61b91c2fb591c9b9b5efcb15255fffdd5c8',
        'exact_sealed_epoch3_manifest')
    receipt_path = KUHN / 'TEST_RECEIPT_v3.json'
    receipt = base.read(receipt_path)
    input_paths = [receipt_path, BANACH / 'prefix_authority.py', BANACH / 'reserved_preflight.py',
        BANACH / 'TO_KUHN_PREFIX.md', KUHN / 'TO_BANACH_PASTEUR.md', WORKER / 'receiver.py',
        *[KUHN / name for name in ('immutable_prefix_proof.py', 'prefix_port.py', 'prefix_cli.py', 'test_prefix_proof.py')],
        *[KUHN / 'consumer_context_v4' / name for name in ('source_port.py', 'context_extension.py',
            'TO_BANACH_PASTEUR_REVIEW.md')], *sorted(TOOLS.glob('*.py'))]
    input_bytes = {str(path): path.read_bytes() for path in input_paths}
    for name, expected in receipt['artifacts'].items():
        require(ports.sha(input_bytes[str(KUHN / name)]) == expected, 'Kuhn_testing_in_progress_or_unreceipted_bytes:' + name)
    namespace = {'__name__': 'pinned_Kuhn_port'}
    exec(compile(input_bytes[str(KUHN / 'prefix_port.py')], '<Kuhn_pinned_port>', 'exec'), namespace)
    context_path = KUHN / 'consumer_context_v4/source_port.py'
    context = {'__name__': 'pinned_Kuhn_context_port', '__file__': str(context_path)}
    exec(compile(input_bytes[str(context_path)], '<Kuhn_v4_pinned_port>', 'exec'), context)
    original_reader = namespace['port']((PREVIOUS / 'source' / ports.READER).read_bytes())
    require(ports.sha(original_reader) == receipt['candidate_reader_sha256'], 'same_Kuhn_v3_reader_preimage')
    reader = context['port_reader'](original_reader)
    proof = context['port_helper'](input_bytes[str(KUHN / 'immutable_prefix_proof.py')])
    cli = context['port_cli'](input_bytes[str(KUHN / 'prefix_cli.py')])
    require(all(Path(path).read_bytes() == content for path, content in input_bytes.items()), 'stable_peer_snapshot')
    additions = ports.proposed(PREVIOUS / 'source', lambda original: reader,
        proof, input_bytes[str(TOOLS / 'authority.py')])
    epoch = output / 'C2/epoch4'
    source = epoch / 'source'
    source.mkdir(parents=True)
    for path in (PREVIOUS / 'source').rglob('*'):
        if path.is_file():
            publish(source / path.relative_to(PREVIOUS / 'source'), path.read_bytes())
    diffs = []
    for name, content in additions.items():
        path = source / name
        if path.exists():
            lines = list(difflib.unified_diff(path.read_text().splitlines(True), content.decode().splitlines(True),
                fromfile='a/' + name, tofile='b/' + name))
            patch_text = '*** Begin Patch\n*** Update File: ' + str(path) + '\n'
            patch_text += ''.join('@@\n' if line.startswith('@@ ') else line for line in lines[2:])
            diffs.extend(lines)
        else:
            patch_text = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
            patch_text += ''.join('+' + line for line in content.decode().splitlines(True))
            diffs.extend(difflib.unified_diff([], content.decode().splitlines(True), fromfile='/dev/null', tofile='b/' + name))
        patch_text += '*** End Patch\n'
        subprocess.run(['apply_patch'], input=patch_text, text=True, capture_output=True, check=True, cwd=WORKER, timeout=30)
        require(path.read_bytes() == content, 'exact_apply_patch_result')
    publish(epoch / 'EPOCH4.patch', ''.join(diffs).encode())
    pins = dict(old['new_source_pins'])
    pins.update({name: ports.sha(content) for name, content in additions.items()})
    require(len(pins) == 186 and len(base.delta(old['old_source_pins'], pins)) == 9, '186_source_files_nine_old_live_deltas')
    for name in ('gpu/r188_node5_confinement.py', 'gpu/r184_cpu_bridge.py', 'gpu/orch_r125_continual_native.py',
            'gpu/orch_r125_stream_journal.py', 'organism_v6/orch_r124_train_history.py'):
        require(pins[name] == old['new_source_pins'][name], 'unchanged_epoch3_invariant_source:' + name)
    helpers = {name: (PREVIOUS / 'tools' / name).read_bytes() for name in old['helper_pins']}
    helpers['cpu_check.py'] = source_checker(helpers['cpu_check.py'])
    helpers['source_checks.py'] = source_cases(helpers['source_checks.py'], pins[ports.READER])
    helpers['cpu_probe.py'] = probe_port(helpers['cpu_probe.py'])
    for name in ('manifest_checks.py', 'prefix_preflight.py', 'prefix_checks.py', 'test_preflight.py'):
        helpers[name] = (TOOLS / name).read_bytes()
    helpers['receiving_core.py'] = receiver_port(input_bytes[str(WORKER / 'receiver.py')])
    for name in ('prefix_port.py', 'prefix_cli.py', 'immutable_prefix_proof.py'):
        helpers[name] = input_bytes[str(KUHN / name)]
    helpers['prefix_cli.py'] = cli
    helpers['immutable_prefix_proof.py'] = proof
    helpers['prefix_cases.py'] = input_bytes[str(KUHN / 'test_prefix_proof.py')]
    plumbing = ('gpu/orch_r125_continual_native.py', ports.RUNTIME, ports.READER, ports.PROOF, ports.AUTHORITY, ports.GUARD)
    delta = {name: dict(before=old['old_source_pins'].get(name), after=pins[name]) for name in plumbing}
    helpers['source_delta.py'] = ('from pathlib import Path\nimport hashlib\n'
        'NATIVE = "gpu/orch_r125_continual_native.py"\nRUNTIME = "' + ports.RUNTIME + '"\n'
        'READER = "' + ports.READER + '"\nPROOF = "' + ports.PROOF + '"\n'
        'AUTHORITY = "' + ports.AUTHORITY + '"\nGUARD = "' + ports.GUARD + '"\n'
        'EXPECTED = ' + repr(delta) + '\n'
        'def changes_for(source):\n'
        '    for name, entry in EXPECTED.items():\n'
        '        path = Path(source) / name\n'
        '        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None\n'
        '        if actual != entry["before"]:\n            raise ValueError("exact_original_C2_preimage:" + name)\n'
        '    return {name: dict(entry) for name, entry in EXPECTED.items()}\n').encode()
    for name, content in helpers.items():
        publish(epoch / 'tools' / name, content)
    remote = Path('/localhome/local-rohing/orch_retention_20260919/C2/epoch4')
    plan = base.plan_template(base.read(PREVIOUS / 'control/PLAN.template.json'), remote / 'source')
    document(epoch / 'control/PLAN.template.json', plan)
    for name in ('ORIGINAL_GUARD_METADATA.json', 'ORIGINAL_PLAN_OBSERVATION.json'):
        publish(epoch / 'control' / name, (PREVIOUS / 'control' / name).read_bytes())
    manifest = deepcopy(old)
    manifest.update(schema='C2_EPOCH4_OFFLINE_CANDIDATE_V1', status='OFFLINE_TEST_CANDIDATE_NOT_ADMISSION_READY',
        local_source=str(source), new_source=str(remote / 'source'), epoch3_source_pins=old['new_source_pins'],
        epoch3_manifest_sha256=sha(PREVIOUS / 'EPOCH3_SOURCE.json'), new_source_pins=pins,
        changed=base.delta(old['old_source_pins'], pins), epoch3_to_epoch4_delta=base.delta(old['new_source_pins'], pins),
        epoch1_to_epoch4_delta=base.delta(old['epoch1_source_pins'], pins), source_file_count=len(pins),
        helper_pins={name: ports.sha(content) for name, content in helpers.items()},
        plan_template_sha256=sha(epoch / 'control/PLAN.template.json'),
        proof_owner_receipt_sha256=sha(receipt_path), trust_review_required=True,
        same_namespace_native_admission_proven=False, actual_30_second_budget_proven=False,
        prefix_ABI='Kuhn_consumer_context_v4_prefix_admission',
        explicit_namespace_modes=['SAME_MOUNT_NAMESPACE', 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'],
        receiver_plumbing_scope='TOOLS_OUTSIDE_RUNTIME_ORIGINAL_BOUNDARY_IMPORTS_REQUIRED',
        historical_default_checkpoint=dict(old['historical_default_checkpoint'], current_wall_compatible=False))
    document(epoch / 'EPOCH4_SOURCE.json', manifest)
    document(epoch / 'SOURCE_PINS.json', pins)
    document(epoch / 'control/SOURCE_EPOCH.template.json', dict(schema='C2_PREFIX_SOURCE_EPOCH_V1',
        epoch_id='C2_EPOCH4_REQUIRES_MAIN_EXPLICIT_STAGE_AUTHORITY', source_root=str(remote / 'source'),
        source_pins_sha256=hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        deadline_unix=1789927200))
    input_pins = {path: ports.sha(content) for path, content in input_bytes.items()}
    document(output / 'INPUTS.json', dict(input_pins=input_pins, epoch3_tree=old_tree,
        copied_peer_bytes_are_not_owner_acknowledgements=True))
    for path, content in input_bytes.items():
        publish(epoch / 'provenance' / (Path(path).parent.name + '__' + Path(path).name), content)
    scratch = output / 'scratch'
    scratch.mkdir()
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source),
        TMPDIR=str(scratch), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    results = {}
    for name in ('source_checks', 'frontier_checks', 'prefix_checks'):
        command = [sys.executable, '-B', str(epoch / 'tools' / (name + '.py')), '--source', str(source),
            '--manifest', str(epoch / 'EPOCH4_SOURCE.json')]
        result = subprocess.run(command, env=environment, cwd=source, capture_output=True, text=True, timeout=180)
        publish(epoch / 'cpu' / (name + '.stdout'), result.stdout.encode())
        publish(epoch / 'cpu' / (name + '.stderr'), result.stderr.encode())
        require(result.returncode == 0, 'source_tests_failed:' + str(epoch / 'cpu' / (name + '.stderr')))
        results[name] = json.loads(result.stdout)
        require(results[name]['passed'] is True, 'all_source_groups_pass')
        document(epoch / 'cpu' / (name + '.json'), results[name])
    command = [sys.executable, '-B', str(epoch / 'tools/test_preflight.py')]
    tested = subprocess.run(command, env=environment, cwd=source, capture_output=True, text=True, timeout=30)
    publish(epoch / 'cpu/PREFLIGHT_TESTS.log', (tested.stdout + tested.stderr).encode())
    require(tested.returncode == 0, 'focused_preflight_tests_must_pass')
    require(snapshot(WORKER / 'prepared_epoch3_v1') == old_tree, 'epoch3_tree_unchanged')
    base.seal(source)
    base.seal(epoch / 'tools')
    base.seal(epoch / 'provenance')
    archive = output / 'C2_EPOCH4_OFFLINE_CANDIDATE.tar.gz'
    with tarfile.open(archive, 'x:gz') as handle:
        handle.add(epoch, arcname='C2/epoch4')
    with tarfile.open(archive, 'r:gz') as handle:
        for member in handle.getmembers():
            require(member.isfile() or member.isdir(), 'regular_archive_member')
            require(not Path(member.name).is_absolute() and '..' not in Path(member.name).parts, 'safe_archive_member')
            if member.isfile():
                require(ports.sha(handle.extractfile(member).read()) == sha(output / member.name), 'exact_archive_bytes')
    summary = dict(schema='C2_EPOCH4_CANDIDATE_RECEIPT_V1', status='OFFLINE_CPU_TESTED_NOT_DISPATCH_READY',
        observed_utc=datetime.now(timezone.utc).isoformat(), local_source=str(source),
        manifest=str(epoch / 'EPOCH4_SOURCE.json'), manifest_sha256=sha(epoch / 'EPOCH4_SOURCE.json'),
        archive=str(archive), archive_sha256=sha(archive), source_python_files=len(pins),
        epoch3_to_epoch4_delta=manifest['epoch3_to_epoch4_delta'], changed=manifest['changed'],
        tests={name: result['tests_run'] for name, result in results.items()},
        preflight_log_sha256=sha(epoch / 'cpu/PREFLIGHT_TESTS.log'), source_tools_sealed=True,
        epoch3_unchanged=True, trust_review_required=True, same_namespace_native_admission_proven=False,
        actual_30_second_budget_proven=False, remote_actions=[], signals=[], dispatches=[], admission_granted=False,
        blockers=['actual_original_consumer_all_object_proof_not_startup_claim', 'explicit_trust_and_ABI_owner_review',
            'Main_actual_entire_reserved_path_cost_and_original_admission_evidence'])
    document(output / 'CANDIDATE.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), sort_keys=True, indent=2))
