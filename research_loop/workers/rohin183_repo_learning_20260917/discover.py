"""Bounded receiving identity and installed dependency metadata, no model load."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


def inspect():
    lease_path = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
    raw = lease_path.read_bytes()
    lease = json.loads(raw)
    model = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28')
    anchors = Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
    devices = []
    for info in sorted(Path('/proc/driver/nvidia/gpus').glob('*/information')):
        text = info.read_text()
        fields = dict(line.split(':', 1) for line in text.splitlines() if ':' in line)
        devices.append(dict(uuid=fields['GPU UUID'].strip(), minor=int(fields['Device Minor']),
            kernel_path=str(info), sha256=hashlib.sha256(text.encode()).hexdigest()))
    python = '/localhome/local-rohing/v2/venv/bin/python'
    modules = subprocess.check_output([python, '-B', '-c',
        "import importlib.util,json; print(json.dumps({name:importlib.util.find_spec(name) is not None for name in ('torch','transformers','peft','pytest')}))"],
        text=True, timeout=20, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
    capacity = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,memory.total', '--format=csv,noheader,nounits'], text=True, timeout=20)
    return dict(schema='R183_RECEIVING_DISCOVERY_V1', observed_unix=time.time(), uid=os.getuid(), gid=os.getgid(),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(), python=python, modules=json.loads(modules),
        lease=dict(path=str(lease_path),sha256=hashlib.sha256(raw).hexdigest(),
            hard_end_unix=lease['hard_deadline_unix'],lease_end_unix=lease['lease_end_unix']),
        lease_gpu_uuid=lease['uuid_by_index'][2] if isinstance(lease['uuid_by_index'],list) else lease['uuid_by_index']['2'], devices=devices, capacity=capacity.strip().splitlines(),
        model_dir=str(model), model_exists=model.is_dir(), model_files=sorted(path.name for path in model.iterdir()) if model.is_dir() else [],
        anchors=str(anchors), anchors_exists=anchors.is_dir(),
        anchor_names=sorted(path.name for path in anchors.iterdir()) if anchors.is_dir() else [],
        disk_free=shutil.disk_usage('/localhome/local-rohing').free,
        systemd=Path('/usr/bin/systemd-run').is_file(), stopped_receipt_exists=Path('/localhome/local-rohing/orch_r183_corpus_stop_20260917/STOP_RECEIPT.json').is_file(),
        GPU_model_calls=0, learner_writes=0)


if __name__ == '__main__':
    print(json.dumps(inspect(),sort_keys=True))
