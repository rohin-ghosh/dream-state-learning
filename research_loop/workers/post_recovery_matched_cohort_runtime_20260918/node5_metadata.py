"""Read-only target inventory; no device opens, model calls, signals or writes."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time


model = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28')
result = dict(observed_unix=time.time(), uid=os.getuid(), gid=os.getgid(),
    host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
    inventory=subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,pci.bus_id,memory.used',
        '--format=csv,noheader,nounits'], text=True),
    compute_processes=subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True), model_dir=str(model), model_dir_exists=model.is_dir(),
    protected_processes={str(pid): Path('/proc', str(pid)).exists() for pid in (2495635, 2757295)})
import torch
result['torch_version'] = torch.__version__
result['cuda_initialized'] = torch.cuda.is_initialized()
print(json.dumps(result, sort_keys=True, indent=2))
