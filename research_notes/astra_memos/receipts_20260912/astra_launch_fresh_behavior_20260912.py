import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from organism_v6 import fresh_behavior_panel as diagnostic
from organism_v6 import run_reasoning_neutral as supervisor
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, choices=(0, 1, 2), required=True)
parser.add_argument('--device', choices=('1', '2', '3'), required=True)
parser.add_argument('--manifest-sha256', required=True)
parser.add_argument('--execute', action='store_true')
args = parser.parse_args()
root = Path.home() / 'astra_diagnostics/astra_fresh_behavior_panel_20260912_attempt2'
source = Path(diagnostic.__file__).resolve().parents[1]
logs = root / ('seed' + str(args.seed) + '_execution')
assert diagnostic.custody._digest(root / 'manifest.json') == args.manifest_sha256
inputs = diagnostic.analysis._Inputs()
panel, preflight = diagnostic._load_prepared(root, inputs)
assert diagnostic.custody._digest(diagnostic.__file__) == preflight['helper_sha256']
diagnostic.custody.verify_source_snapshot(preflight['source_snapshot'])
assert diagnostic._runtime() == preflight['runtime']
inputs.verify()
cutoff = datetime.datetime.fromisoformat('2026-09-25T21:03:00+00:00')
assert (cutoff - datetime.datetime.now(datetime.timezone.utc)).total_seconds() > 4200
cpu = Path('/tmp/astra_fresh_behavior_attempt2_native_cpu_20260912.log')
assert '\nOK\n' in cpu.read_text() and 'Ran 96 tests' in cpu.read_text()
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=args.device, V6_MODEL=diagnostic.MODEL,
                   PYTHONPATH=str(source), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                   VLLM_WORKER_MULTIPROC_METHOD='spawn')
if not args.execute:
    assert not logs.exists()
    gpu, xml = check_free(args.device)
    logs.mkdir()
    (logs / 'gpu.xml').write_text(xml)
    command = [sys.executable, '-B', str(Path(__file__).resolve()), '--seed', str(args.seed),
               '--device', args.device, '--manifest-sha256', args.manifest_sha256, '--execute']
    with (logs / 'controller.log').open('xb') as output:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', pid=process.pid, node=3,
        device=args.device, optimizer_seed=args.seed, gpu=gpu, source=str(source), root=str(root),
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
        manifest_sha256=args.manifest_sha256, launcher_sha256=diagnostic.custody._digest(__file__),
        native_cpu_sha256=diagnostic.custody._digest(cpu), conditions=4, episode_cells=64, fits=0,
        continuous_reservation=True, lease_finish_cutoff_utc=cutoff.isoformat(),
        model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', boundary=diagnostic.LIMITATIONS)
    write_new(logs / 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
else:
    started = time.monotonic()
    completed = []
    try:
        for arm in ('useful', 'corrupt'):
            diagnostic.custody.verify_source_snapshot(preflight['source_snapshot'])
            spec = root / 'specs' / f'seed{args.seed}_{arm}.json'
            spec_hash = spec.with_suffix('.json.sha256').read_text().strip()
            supervisor.read_spec(spec, spec_hash)
            command = [sys.executable, '-B', '-m', 'organism_v6.run_reasoning_neutral',
                       '--spec', str(spec), '--spec-sha256', spec_hash, '--allow-gpu']
            with (logs / (arm + '.log')).open('xb') as output:
                process = subprocess.Popen(command, cwd=source, env=environment,
                    stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                    start_new_session=True)
                write_new(logs / (arm + '.process.json'), dict(pid=process.pid,
                    command=command, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
                status = process.wait()
            assert status == 0, (arm, status)
            pair = diagnostic.analysis._pair_custody(root / 'probes' / f'seed{args.seed}_{arm}',
                                                    diagnostic.analysis._Inputs())
            assert pair['status'] == 'ARTIFACT_CUSTODY_VALIDATED'
            completed.append(arm)
        assert supervisor.gpu_processes_absent(args.device)
        write_new(logs / 'result.json', dict(status='BOTH_PAIRS_COMPLETE_PENDING_MAIN_REDUCTION',
            completed=completed, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            controller_seconds=time.monotonic() - started, fits=0,
            gpu_processes_absent=True, external_full_release_check_required=True))
    except BaseException as error:
        write_new(logs / 'failure.json', dict(status='INCOMPLETE', error=repr(error), completed=completed,
            observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            controller_seconds=time.monotonic() - started, reservation_release_verified=False))
        raise
