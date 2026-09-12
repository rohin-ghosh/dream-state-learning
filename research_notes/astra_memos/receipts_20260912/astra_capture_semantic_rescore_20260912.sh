#!/usr/bin/env bash
set -euo pipefail
test ! -e /tmp/astra_semantic_rescore_terminal_20260912.tgz
bash gpu/ovx2_ssh.sh 'env PYTHONPATH="$HOME/astra_sources/02a772f8376f431274699d121f691e80e5e6ea0e" CUDA_VISIBLE_DEVICES="" "$HOME/v2/venv/bin/python" -B -' <<'PY'
import datetime,json
from pathlib import Path
from gpu import astra_semantic_rescore as rescore
from gpu.astra_mini_sudoku_diagnostic import check_free,write_new
root=Path.home()/'astra_diagnostics/astra_semantic_rescore_20260912_attempt1'
assert (root/'COMPLETED.json').is_file() and not (root/'FAILED.json').exists()
assert not Path('/proc/110916').exists()
out,supplement,original,manifest,requests=rescore.verify_supplement(root)
tokenizer=rescore.diagnostic.w0.load_local_tokenizer(manifest['config'])
report=rescore.diagnostic.reduce_records(rescore.read(original/'material.json'),requests,rescore.merge_records(original,out,requests),tokenizer)
assert report==rescore.read(root/'supplementary_report.json')
for path in root.glob('*.cleanup.json'):
    cleanup=rescore.read(path)
    assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
assert len(list(root.glob('*.cleanup.json')))==5
gpu,xml=check_free('0')
write_new(root/'MAIN_TERMINAL_AUDIT.json',dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_reduction_equal=True,controller_absent=True,gpu=gpu,xml=xml,released=True))
print(json.dumps(dict(status='NATIVE_RESCORE_REPLAY_AND_RELEASE_PASS',label=report['label'],gates=report['gates'])))
PY
bash gpu/ovx2_ssh.sh 'bash -se' <<'REMOTE'
set -euo pipefail
test ! -e /tmp/astra_semantic_rescore_terminal_20260912.tgz
tar -czf /tmp/astra_semantic_rescore_terminal_20260912.tgz -C "$HOME/astra_diagnostics" astra_semantic_rescore_20260912_attempt1 astra_semantic_rescore_20260912_attempt1_launch
sha256sum /tmp/astra_semantic_rescore_terminal_20260912.tgz
REMOTE
bash gpu/ovx2_scp.sh NODE:/tmp/astra_semantic_rescore_terminal_20260912.tgz NODE:/tmp/astra_rescore_native_cpu_20260912.log /tmp/
sha256sum /tmp/astra_semantic_rescore_terminal_20260912.tgz
mkdir /tmp/astra_semantic_rescore_terminal_20260912
tar -xzf /tmp/astra_semantic_rescore_terminal_20260912.tgz -C /tmp/astra_semantic_rescore_terminal_20260912
