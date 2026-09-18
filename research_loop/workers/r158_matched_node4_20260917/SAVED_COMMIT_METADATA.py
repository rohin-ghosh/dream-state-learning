"""Read only the preserved attempt3 saved checkpoint; never admit or repair it."""

import hashlib
import json
import os
from pathlib import Path
import runpy
import time


base = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt3')
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
assert hashlib.sha256((base / 'operator_metadata/INITIAL_METADATA.py').read_bytes()).hexdigest() == 'dab6ef19eee039cd44320645545739aa4698a0af216d7a809ad20a3bca8647ef'
helpers = runpy.run_path(str(base / 'operator_metadata/INITIAL_METADATA.py'))
sha = helpers['sha']
read = helpers['read']
initial = base / 'common_initial'
commit_path = initial / 'COMMIT.json'
commit_sha = sha(commit_path)
assert commit_sha == 'f1fdb87d92e3e2efc401583faa02f2d6c5a8de07f5dcd20866215c8cb54a332c'
commit = read(commit_path)
assert commit['optimizer_steps'] == 0
assert not (initial / 'INITIALIZED.json').exists()
assert commit['adapter_path'] == str(initial / 'adapter')
assert commit['optimizer_rng_path'] == str(initial / 'optimizer_rng.pt')
adapter_files = {path.name: sha(path) for path in (initial / 'adapter').iterdir() if path.is_file()}
assert adapter_files == commit['adapter_files']
headers = {path.name: helpers['adapter_header'](path)
           for path in (initial / 'adapter').glob('*.safetensors')}
assert headers
optimizer_sha = sha(initial / 'optimizer_rng.pt')
assert optimizer_sha == commit['checkpoint_sha256']['optimizer'] == commit['checkpoint_sha256']['rng']
import torch

payload = torch.load(initial / 'optimizer_rng.pt', map_location='cpu', weights_only=True)
assert payload['optimizer_steps'] == 0
assert payload['optimizer']['state'] == {}
assert not torch.cuda.is_initialized()
assert sha(commit_path) == commit_sha
result = dict(
    schema='R158_PRESERVED_FAILED_INITIALIZER_METADATA_V1',
    status='SAVED_COMMIT_VERIFIED_NOT_ADMITTED', observed_unix=time.time(),
    original_commit_path=str(commit_path), commit_sha256=commit_sha,
    cohort_sha256=sha(base / 'COHORT.json'),
    capacity_result_sha256=sha(initial / 'capacity_validation/RESULT.json'),
    lifecycle_sha256=sha(base / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json'),
    metadata_reader_sha256=sha(base / 'operator_metadata/INITIAL_METADATA.py'),
    adapter_file_sha256=adapter_files, adapter_headers=headers,
    total_adapter_numel=sum(header['total_numel'] for header in headers.values()),
    optimizer_rng_sha256=optimizer_sha, saved_optimizer_steps=payload['optimizer_steps'],
    saved_AdamW_state_entries=len(payload['optimizer']['state']),
    saved_optimizer_group_count=len(payload['optimizer']['param_groups']),
    saved_parameter_name_count=len(payload['parameter_names']),
    initialized_receipt_exists=False, capacity_status='FAIL',
    capacity_restoration_status='UNVERIFIED', GPU_calls=0,
    optimizer_updates_performed=0, adapter_values_returned=False,
    RNG_values_returned=False, evaluation_contents_read=False,
    original_state_files_modified=False)
print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
