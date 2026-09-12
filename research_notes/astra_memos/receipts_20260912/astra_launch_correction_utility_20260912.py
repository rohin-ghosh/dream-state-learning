import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu.astra_mini_sudoku_diagnostic import check_free, digest, write_new
from gpu import astra_correction_utility_diagnostic as diagnostic

parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, choices=[0, 1, 2], required=True)
parser.add_argument('--devices', nargs=2, required=True)
args = parser.parse_args()
if len(set(args.devices)) != 2:
    raise ValueError('separate devices required')
root = Path.home() / 'astra_diagnostics/astra_correction_utility_20260912_attempt1'
material = root / 'preparation'
panel = Path('/tmp/astra_correction_utility_panel_20260912.json')
source = Path(diagnostic.__file__).resolve().parents[1]
report, _ = diagnostic.inspect_preparation(material, panel)
now = datetime.datetime.now(datetime.timezone.utc)
deadline = datetime.datetime(2026, 9, 12, 15, 45, tzinfo=datetime.timezone.utc)
if (deadline - now).total_seconds() < 2500:
    raise ValueError('insufficient time for prospective comparison budget')
selected = []
for arm, device in zip(('whole_raw', 'act_only'), args.devices):
    command = diagnostic.selected_command(material, report, arm, args.seed)
    logs = root / 'launch_logs' / arm / f'seed{args.seed}'
    out = root / 'recipient_logs' / arm / f'seed{args.seed}'
    if logs.exists() or out.exists():
        raise ValueError('recipient already claimed or attempted')
    gpu, xml = check_free(device)
    selected.append((arm, device, logs, out, gpu, xml))
for arm, device, logs, out, gpu, xml in selected:
    logs.mkdir(parents=True, exist_ok=False)
    write_new(logs / 'CLAIM.json', dict(arm=arm, seed=args.seed, device=device,
        main_serialized=True, adapter=report['recipient_root'] + '/' + arm + f'/seed{args.seed}'))
    current_gpu, current_xml = check_free(device)
    if current_gpu['gpu_uuid'] != gpu['gpu_uuid']:
        raise ValueError('device identity changed')
    (logs / 'prelaunch_gpu.xml').write_text(current_xml)
    argv = [sys.executable, '-B', '-m', 'gpu.astra_correction_utility_diagnostic',
        '--material', str(material), '--panel', str(panel), '--out', str(out),
        '--arm', arm, '--seed', str(args.seed), '--device', device, '--allow-gpu']
    environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1',
        PYTHONNOUSERSITE='1', CUDA_VISIBLE_DEVICES=device, V6_MODEL=report['model_path'],
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
        OMP_NUM_THREADS='1')
    with (logs / 'controller.log').open('xb') as output:
        process = subprocess.Popen(argv, cwd=source, env=environment, stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        pid=process.pid, node=3, device=device, arm=arm, seed=args.seed, gpu=current_gpu,
        source=str(source), command=argv, out=str(out), logs=str(logs), continuous_reservation=True,
        material_inventory_sha256=digest(material / 'artifact_hashes.json'),
        panel_sha256=digest(panel), launcher_sha256=digest(Path(__file__)),
        worker_caps_seconds=dict(fit=600, pair=1800, condition=750),
        cleanup_boundary='Main retains reservation and inspects recorded nested owned PIDs on timeout',
        comparison_deadline=deadline.isoformat(), official_model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
        clean_lineage=False, parenting_advantage=False)
    write_new(logs / 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
