"""Exact local Qwen owner entry inside the unchanged NODE4 strict-slot wrapper."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

from gpu import ny_caption_vision as vision


OWNER_ROOT = Path('/localhome/local-rohing/orch_r177_local_qwen_vision_20260917')
SLOT_ROOT = Path('/localhome/local-rohing/orch_r177_strict_slots_20260917_v1')
SLOT_POLICY_SHA256 = '6c69c690d4e2491255a3a12370b1143515a4d223456880e889fd24eafaea0c51'
SLOT_BUNDLE_SHA256 = 'd26f808fcce89c9d5674d69484bcbac614608761b1f2602d04ee6e5935b49aec'
HARD_END = 1789754400


def reference(path):
    return dict(path=str(path), sha256=vision.file_digest(path))


def bound(pin):
    vision.require(set(pin) == {'path', 'sha256'} and vision.file_digest(pin['path']) == pin['sha256'],
                   'exact_owner_reference_required')
    return vision.strict_json(Path(pin['path']).read_bytes())


def write_once(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def load_slot_policy():
    vision.require(vision.file_digest(SLOT_ROOT / 'slot_policy.py') == SLOT_POLICY_SHA256 and
                   vision.file_digest(SLOT_ROOT / 'BUNDLE.json') == SLOT_BUNDLE_SHA256,
                   'unchanged_Main_strict_slot_bundle_required')
    specification = importlib.util.spec_from_file_location('r177_bound_slot_policy', SLOT_ROOT / 'slot_policy.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    module.verify_bundle()
    return module


def current_slot(policy):
    cgroup = Path('/proc/self/cgroup').read_text().strip()
    match = re.fullmatch(r'0::/system.slice/(orch-r177-slot5-[a-f0-9]{32})\.service', cgroup)
    vision.require(match is not None, 'actual_physical5_outer_service_required')
    candidates = []
    for path in (SLOT_ROOT / 'attempts').glob('launch_5_*/CONFIG.json'):
        config = vision.strict_json(path.read_bytes())
        if config.get('unit') == match.group(1):
            candidates.append(path)
    vision.require(len(candidates) == 1, 'one_config_for_actual_kernel_cgroup_required')
    path = candidates[0]
    config = policy.validate_config(path)
    vision.require(config['physical'] == 5 and config['minor'] == vision.GPU_MINOR and
                   config['gpu_uuid'] == vision.GPU_UUID and 0 < config['seconds'] <= 3570 and
                   config['hard_end_unix'] == HARD_END, 'exact_existing_slot_and_cleanup_budget')
    policy.verify_device_containment(config)
    return path, config


def validate_metadata(document):
    fields = {'schema', 'code', 'entrypoint', 'cpu_receipt', 'packet', 'snapshot',
              'runtime', 'port', 'max_gpu_seconds'}
    vision.require(type(document) is dict and set(document) == fields and
                   document['schema'] == 'R177_LOCAL_VISION_OWNER_V1' and
                   type(document['port']) is int and 1024 <= document['port'] <= 65535 and
                   document['max_gpu_seconds'] == 3600, 'exact_owner_metadata_schema')
    vision.require(document['code'] == reference(Path(vision.__file__).resolve()) and
                   document['entrypoint'] == reference(Path(__file__).resolve()), 'actual_owner_source_pins')
    cpu = bound(document['cpu_receipt'])
    vision.require(cpu['status'] == 'PASS' and cpu['gpu_model_loaded'] is False and
                   cpu['code_sha256'] == document['code']['sha256'] and
                   cpu['owner_entry_sha256'] == document['entrypoint']['sha256'], 'receiving_owner_CPU_bound')
    packet = vision.ImagePacket(bound(document['packet']))
    vision.require(len(packet.images) == 3, 'exactly_three_released_game_images_required')
    for handle in packet.images:
        unused_spec, pixels = packet.verified_image(handle)
        pixels.close()
    manifest = bound(document['snapshot'])
    vision.require(manifest['model_id'] == vision.MODEL_ID and manifest['revision'] == vision.REVISION,
                   'pinned_local_Qwen_snapshot_required')
    runtime = Path(document['runtime'])
    vision.require(runtime.parent == OWNER_ROOT and re.fullmatch(r'runtime[1-9][0-9]*', runtime.name) and
                   not runtime.exists() and not runtime.is_symlink(), 'fresh_own_runtime_required')
    return packet


def build_admission(metadata, metadata_pin, config, config_pin, scan_binding, owner_exec, containment,
                    now, process_id):
    vision.require(metadata_pin in config['metadata_pins'] and
                   config['entrypoint'] == metadata['entrypoint']['path'], 'outer_binds_actual_owner_metadata')
    vision.require(owner_exec['pid'] == process_id and owner_exec['config'] == config_pin and
                   owner_exec['command'] == config['command'] and owner_exec['no_retry'] is True and
                   owner_exec['status'] == 'EXEC_REQUESTED_NOT_MODEL_LOAD', 'exact_outer_exec_not_replay')
    vision.require(scan_binding['config'] == config_pin and scan_binding['original_scanner_unmodified'] is True and
                   0 <= now - scan_binding['verified_unix'] < 60, 'fresh_unchanged_outer_scan_required')
    vision.require(containment['pid'] == process_id and containment['configuration'] == config_pin and
                   containment['physical'] == 5 and containment['gpu_uuid'] == vision.GPU_UUID and
                   containment['minor'] == vision.GPU_MINOR and containment['target_open_close'] is True and
                   containment['denied_foreign_minors'] == [0, 1, 2, 3, 4, 5, 7], 'exact_outer_device_proof')
    vision.require(config['physical'] == 5 and config['minor'] == vision.GPU_MINOR and
                   config['gpu_uuid'] == vision.GPU_UUID and config['hard_end_unix'] == HARD_END and
                   0 < config['seconds'] <= metadata['max_gpu_seconds'] - 30 and
                   config['created_unix'] <= now < config['end_unix'], 'unchanged_outer_wall_and_cleanup')
    return dict(schema='R177_LOCAL_VISION_ADMISSION_V1', approved=True, physical=5,
        gpu_uuid=vision.GPU_UUID, kernel_minor=vision.GPU_MINOR, host_sha256=vision.HOST_SHA256,
        code_sha256=metadata['code']['sha256'], packet_sha256=metadata['packet']['sha256'],
        snapshot_manifest_sha256=metadata['snapshot']['sha256'], not_before_unix=config['created_unix'],
        hard_end_unix=HARD_END, max_gpu_seconds=metadata['max_gpu_seconds'],
        device_checked_unix=scan_binding['verified_unix'], service_unit=config['unit'] + '.service',
        cpu_receipt=metadata['cpu_receipt'], device_receipt=scan_binding['report'], lease_receipt=config['lease'],
        outer_slot_config=config_pin)


def probe(output):
    policy = load_slot_policy()
    config_path, config = current_slot(policy)
    actual_minor = vision.kernel_device_minor(vision.GPU_UUID)
    vision.require(actual_minor == vision.GPU_MINOR, 'actual_UUID_minor_six_required')
    denied = vision.verify_device_access(actual_minor)
    policy.scoped_path(output, OWNER_ROOT)
    write_once(output, dict(schema='R177_OWNER_STRICT_CPU_PROBE_V1', status='PASS',
        code=reference(Path(vision.__file__).resolve()), entrypoint=reference(Path(__file__).resolve()),
        config=reference(config_path), physical=5, kernel_minor=actual_minor, denied_foreign_minors=denied,
        gpu_model_loaded=False, torch_imported='torch' in sys.modules, observed_unix=time.time(),
        existing_processes_modified=False))


def run(metadata_pin):
    metadata = bound(metadata_pin)
    validate_metadata(metadata)
    policy = load_slot_policy()
    config_path, config = current_slot(policy)
    attempt = Path(config['attempt'])
    config_pin = reference(config_path)
    scan_binding = bound(reference(attempt / 'ADMISSION_BINDING.json'))
    owner_exec = bound(reference(attempt / 'OWNER_EXEC.json'))
    containment = bound(owner_exec['containment'])
    vision.require(owner_exec['admission'] == reference(attempt / 'ADMISSION_BINDING.json'),
                   'outer_exec_exact_scan_binding')
    policy.require_clear(bound(scan_binding['report']), config)
    admission = build_admission(metadata, metadata_pin, config, config_pin, scan_binding,
                                owner_exec, containment, time.time(), os.getpid())
    runtime = Path(metadata['runtime'])
    runtime.mkdir(mode=0o700)
    (runtime / 'OWNER_ENTRY_ONCE').mkdir()
    admission_path = runtime / 'ADMISSION.json'
    write_once(admission_path, admission)
    write_once(runtime / 'OWNER_ENTRY.json', dict(status='CHECKED_NOT_MODEL_LOADED',
        metadata=metadata_pin, admission=reference(admission_path), outer_config=config_pin,
        code=metadata['code'], entrypoint=metadata['entrypoint'], pid=os.getpid(), observed_unix=time.time()))
    vision.serve(metadata['packet']['path'], Path(metadata['snapshot']['path']).parent, admission_path,
                 vision.file_digest(admission_path), runtime / 'receipts', metadata['port'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    service = commands.add_parser('serve')
    service.add_argument('--metadata', type=Path, required=True)
    service.add_argument('--metadata-sha256', required=True)
    cpu_probe = commands.add_parser('probe')
    cpu_probe.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'probe':
        probe(arguments.output)
    else:
        run(dict(path=str(arguments.metadata), sha256=arguments.metadata_sha256))


if __name__ == '__main__':
    main()
