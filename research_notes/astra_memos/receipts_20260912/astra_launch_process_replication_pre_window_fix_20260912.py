import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


DRIVER = Path('/tmp/astra_rulegame_process_replication_20260912.py')
DRIVER_SHA = '96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd'
COLLECTOR = Path('/tmp/astra_process_replication_collectors_20260912.py')
COLLECTOR_SHA = 'fe80cfbbef70b2dc09b103d1de555eb7bdd359135be2bd9f59b9acc9d9bf39f8'
SOURCE_ID = '4c3064c1c3eef068951e9c3b2ca46630754564e7'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, expected, name):
    if digest(path) != expected:
        raise ValueError('source hash mismatch: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('write', 'readout'))
    parser.add_argument('--fit-seed', type=int, choices=(0, 1), required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--write-release', type=Path)
    parser.add_argument('--write-release-sha256')
    parser.add_argument('--allow-gpu', action='store_true')
    args = parser.parse_args()
    if not args.allow_gpu:
        raise ValueError('explicit GPU opt-in required')
    source = Path.home() / 'astra_sources' / SOURCE_ID
    runner = load(DRIVER, DRIVER_SHA, 'main_process_replication')
    collector = load(COLLECTOR, COLLECTOR_SHA, 'main_process_replication_collector')
    bridge = runner.WritePhase(args.fit_seed) if args.phase == 'write' else runner.ReadoutPhase(args.fit_seed)
    root, plan, diagnostic = bridge.checked_plan(args.root, args.plan_sha256)[:3]
    if plan['source_root'] != str(source) or plan['device'] != '2':
        raise ValueError('explicit source/device differs')
    cap = 1200 if args.phase == 'write' else 1800
    if time.time() + cap + 300 >= min(plan['deadline'], plan['lease_cutoff']):
        raise ValueError('insufficient full controller and collection window')
    logs = root.parent / (root.name + '_launch')
    if (root / 'run').exists() or logs.exists():
        raise ValueError('existing run or launch; never retry implicitly')
    cpu_hashes = {}
    for name, count in (('astra_process_replication_native_cpu_20260912.log', 27),
                        ('astra_process_replication_collectors_native_cpu_20260912.log', 19)):
        path = Path('/tmp') / name
        text = path.read_text()
        if f'Ran {count} tests' not in text or not text.rstrip().endswith('OK'):
            raise ValueError('native CPU acceptance missing: ' + name)
        cpu_hashes[name] = digest(path)
    extras = {}
    if args.phase == 'readout':
        if args.write_release is None or not args.write_release_sha256:
            raise ValueError('explicit completed write release required')
        extras = dict(write_plan_sha256=plan['write_plan_sha256'], write_driver_sha256=DRIVER_SHA,
                      write_release_path=str(args.write_release), write_release_sha256=args.write_release_sha256)
    elif args.write_release is not None or args.write_release_sha256:
        raise ValueError('write cannot use prior release')
    command = [plan['python'], '-B', str(DRIVER), 'write' if args.phase == 'write' else 'evaluate',
               '--fit-seed', str(args.fit_seed), '--root', str(root),
               '--plan-sha256', args.plan_sha256, '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], PYTHONPATH=str(source),
                       ASTRA_SOURCE_ROOT=str(source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                       OMP_NUM_THREADS='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    from gpu.astra_mini_sudoku_diagnostic import check_free
    gpu, xml = check_free(plan['device'])
    started = datetime.datetime.now(datetime.timezone.utc)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', source=str(source), root=str(root), node=3,
                   device=plan['device'], gpu=gpu, started_utc=started.isoformat(), command=command,
                   phase=bridge.WRITE_PROTOCOL if args.phase == 'write' else bridge.VERSION,
                   plan_sha256=args.plan_sha256, fit_seed=args.fit_seed, driver_sha256=DRIVER_SHA,
                   launcher_sha256=digest(__file__), collector_sha256=COLLECTOR_SHA,
                   native_cpu_sha256=cpu_hashes, continuous_reservation=True, controller_seconds=cap,
                   cleanup_reserve=140, worker_cap_seconds=600, external_collection_margin_seconds=300,
                   automatic_next_phase=False, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
                   expected_custody_end_unix=started.timestamp()+cap+300, **extras)
    receipt['arms' if args.phase == 'write' else 'cells'] = ['P', 'A'] if args.phase == 'write' else ['OFF', 'P_ON', 'A_ON']
    if args.phase == 'readout':
        collector.write_release(dict(root=root, launch_root=logs, write_release=args.write_release,
            write_release_sha256=args.write_release_sha256, fit_seed=args.fit_seed), plan, receipt)
    logs.mkdir()
    with (logs / 'gpu.xml').open('x') as stream:
        stream.write(xml)
    with (logs / 'controller.log').open('xb') as stream:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    receipt.update(pid=process.pid, pgid=os.getpgid(process.pid))
    with (logs / 'launch.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(receipt, launch_sha256=digest(logs / 'launch.json')), sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
