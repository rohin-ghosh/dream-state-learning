"""CPU-only physical5 rebind of the reviewed R158 forgiving-parser executor."""

import hashlib
import json
from pathlib import Path
import shutil


HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
ORIGINAL_SHA = '034ddbdddfea960b97a3461366d9eebfc05a9ff053c9cc7ec497c565cdea66b7'
UUID = 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30'
ROOTS = {
    0: '/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1',
    4: '/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1/run1',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target(life_physical, root, executor_physical, uuid, minor):
    require(type(life_physical) is int and life_physical in ROOTS and ROOTS[life_physical] == root,
        'kernel0_and_kernel4_only_no_raw_or_control_routing')
    require(type(executor_physical) is int and executor_physical == 5 and uuid == UUID
        and type(minor) is int and minor == 6, 'physical5_UUID_kernel_minor6_only')


def rebind(source):
    require(hashlib.sha256(source.encode()).hexdigest() == ORIGINAL_SHA, 'exact_reviewed_R158_executor_bytes')
    replacements = [
        ('GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', UUID),
        ('GPU_MINOR = 1', 'GPU_MINOR = 6'),
        ('.orch_r132_kernel_gpu1.lock', '.orch_r175_kernel_physical5_minor6.lock'),
        ('/dev/nvidia1', '/dev/nvidia6'),
        ("fields[1] == '2'", "fields[1] == '5'"),
        ("info.get('Device Minor') == '1'", "info.get('Device Minor') == '6'"),
        ('== [195, 1]', '== [195, 6]'),
        ('physical_index=2', 'physical_index=5'),
    ]
    patched = source
    for before, after in replacements:
        require(before in patched and after not in patched, 'exact_device_rebind_seam')
        patched = patched.replace(before, after)
    restored = patched
    for before, after in reversed(replacements):
        restored = restored.replace(after, before)
    require(restored == source, 'only_physical_device_identity_changed')
    return patched


def rebind_test_fixture(name, source):
    replacements = {
        'tests/test_orch_r148_kernel_tool_service.py': (
            ('physical_index=2', 'physical_index=5'),
            ("nodes={'/dev/nvidia1': [195, 1]}", "nodes={'/dev/nvidia6': [195, 6]}"),
            ('device_minor=1, executor_lock=', 'device_minor=6, executor_lock='),
        ),
        'tests/test_orch_r148_kernel_service_campaign.py': (
            ("admission['device_minor'] == 1", "admission['device_minor'] == 6"),
            ("device_identity.return_value['physical_index'] == 2",
             "device_identity.return_value['physical_index'] == 5"),
        ),
    }.get(name, ())
    patched = source
    for before, after in replacements:
        count = 2 if name == 'tests/test_orch_r148_kernel_service_campaign.py' and before == "admission['device_minor'] == 1" else 1
        require(patched.count(before) == count and after not in patched,
            'exact_historical_fixture_device_binding:' + name)
        patched = patched.replace(before, after)
    restored = patched
    for before, after in reversed(replacements):
        restored = restored.replace(after, before)
    require(restored == source, 'fixture_changes_only_device_identity')
    return patched


def build(output):
    output = Path(output).resolve()
    require(output.parent == HOME and not output.exists(), 'fresh_owned_CPU_stage')
    manifest = REPO / 'research_loop/workers/r158_kernel_execution_20260917/SOURCE_MANIFEST.json'
    pins = json.loads(manifest.read_text())
    inputs = {}
    for name, digest in pins.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'reviewed_relative_path')
        candidate = REPO / name
        if sha(candidate) != digest:
            candidate = HOME / 'kernel5_cpu_stage_20260917T2203Z/source' / name
        require(candidate.is_file() and sha(candidate) == digest,
            'unchanged_reviewed_source_closure:' + name)
        inputs[name] = candidate
    output.mkdir()
    source = output / 'source'
    for name in pins:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inputs[name], path)
    for package in ('gpu', 'organism_v6', 'tests'):
        path = source / package / '__init__.py'
        if not path.exists():
            path.write_text('')
    executor = source / 'gpu/orch_r132_kernel_executor.py'
    executor.write_text(rebind(executor.read_text()))
    fixture_changes = {}
    for name in pins:
        if name.startswith('tests/') and name.endswith('.py'):
            path = source / name
            original = path.read_text()
            patched = rebind_test_fixture(name, original)
            if patched != original:
                path.write_text(patched)
                fixture_changes[name] = dict(original_sha256=pins[name], target_sha256=sha(path))
    receipt = dict(status='CPU_STAGED_NOT_GPU_ADMITTED', reviewed_manifest_sha256=sha(manifest),
        old_executor_sha256=ORIGINAL_SHA, new_executor_sha256=sha(executor), physical=5, kernel_minor=6,
        gpu_uuid=UUID, allowed_child_roots=ROOTS, forgiving_parser_policy='R153_FIRST_CODE_BLOCK_ASCII_PUNCTUATION_V1',
        unchanged_validation_and_sandbox_except_target_identity=True, source=str(source),
        source_pins={str(path.relative_to(source)): sha(path) for path in source.rglob('*') if path.is_file()},
        fresh_admission_required=True, exclusive_reservation_verified=False, real_tool_calls=0,
        synthetic_fixture_device_rebindings=fixture_changes,
        reviewed_input_paths={name: str(path) for name, path in inputs.items()},
        real_child_results=0, must_not_replay_prior_offline_gap=True, native_restart_required=False,
        future_start_frontier='BIND_FRESH_COMMITTED_HEAD_AT_ACTUAL_SERVICE_START_NOT_THIS_STAGE')
    (output / 'STAGED.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    import sys
    print(json.dumps(build(sys.argv[1]), sort_keys=True))
