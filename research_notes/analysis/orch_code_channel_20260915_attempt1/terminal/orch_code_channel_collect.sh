#!/bin/bash
set -euo pipefail
root=/tmp/orch_code_channel_20260915_attempt1
while ! test -f "$root/TERMINAL.json"; do sleep 10; done
env CUDA_VISIBLE_DEVICES= PYTHONPATH="$root/source" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false \
    /localhome/local-rohing/v2/venv/bin/python -B "$root/orch_code_channel_verify.py" \
    --root "$root" --model-dir /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 \
    --output "$root/VERIFY.json"
python3 - "$root" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
import tarfile

root = Path(sys.argv[1])
paths = [path for path in root.glob('*') if path.is_file() and path.suffix in ('.json', '.log', '.py', '.sh')
         and path.name != 'collect.log']
for arm in ('LEGACY', 'SEPARATED', 'TERSE', 'prepare'):
    paths.extend((root / arm).glob('*.json'))
with tarfile.open(root / 'terminal.tar.gz', 'x:gz') as stream:
    for path in sorted(paths):
        stream.add(path, arcname=str(path.relative_to(root)), recursive=False)
with tarfile.open(root / 'terminal.tar.gz', 'r:gz') as stream:
    assert len(stream.getmembers()) == len(paths)
    for member in stream:
        assert hashlib.sha256(stream.extractfile(member).read()).digest() == hashlib.sha256((root / member.name).read_bytes()).digest()
with (root / 'TERMINAL_PACKAGE.json').open('x') as output:
    json.dump(dict(archive_sha256=hashlib.sha256((root / 'terminal.tar.gz').read_bytes()).hexdigest(),
                   files=len(paths), verified=True), output, indent=2)
print((root / 'TERMINAL_PACKAGE.json').read_text())
PY
