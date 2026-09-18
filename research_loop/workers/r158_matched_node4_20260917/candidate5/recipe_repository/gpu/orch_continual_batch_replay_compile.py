"""Compile registered checkpoint TRAIN replay on native disk, never fit or review."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from organism_v6 import orch_continual_batch as policy
from organism_v6 import orch_continual_batch_replay_compile as compiler


def execute(request_path, request_sha256, output):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_compile')
    policy.require(not Path(__file__).resolve().is_relative_to(Path('/data/home/rohing/dream-state-orch')) and
                   not any((parent / '.git').exists() for parent in Path(__file__).resolve().parents),
                   'immutable_outside_worktree_runtime_required')
    payload = request_path.read_bytes()
    policy.require(hashlib.sha256(payload).hexdigest() == request_sha256, 'request_hash_mismatch')
    request = json.loads(payload)
    root = Path(request['native_evidence_root']).resolve()
    policy.require(root.is_relative_to('/localhome/local-rohing') and root != Path('/localhome/local-rohing'),
                   'registered_node_local_evidence_only')
    policy.require(output.resolve().is_relative_to(root) and output.name.startswith('orch_continual_batch_') and
                   not output.exists(), 'fresh_native_only_compile_destination')
    model = Path(request['model_dir']).resolve()
    policy.require(model.is_relative_to('/localhome/local-rohing'), 'node_local_tokenizer_only')
    for name, digest in request['tokenizer_files'].items():
        path = (model / name).resolve()
        policy.require(path.is_relative_to(model) and hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                       'frozen_tokenizer_file_hash_mismatch')
    policy.require({'tokenizer.json', 'tokenizer_config.json'} <= set(request['tokenizer_files']),
                   'exact_tokenizer_and_template_required')
    from gpu import astra_portable_actor_bundle as portable
    tokenizer = portable.source.native.load_local_tokenizer(str(model))
    result = compiler.compile_bound_batch(request, tokenizer)
    output.mkdir()
    for name, value in (('ROWS.json', result['rows']), ('SKIPPED.json', result['skipped'])):
        with (output / name).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
    rows_sha256 = hashlib.sha256((output / 'ROWS.json').read_bytes()).hexdigest()
    handoff = compiler.handoff(result['compiled'], result['registration'], str(output / 'ROWS.json'), rows_sha256)
    handoff.update(input_bindings=request, request_sha256=request_sha256, batch_decision=result['batch_decision'],
                   skipped_rows=len(result['skipped']), compiler_scope=result['compiler_scope'])
    with (output / 'COMPILE_HANDOFF.json').open('x') as stream:
        json.dump(handoff, stream, indent=2, sort_keys=True, allow_nan=False)
    return dict(native_handoff_path=str(output / 'COMPILE_HANDOFF.json'),
                native_handoff_sha256=hashlib.sha256((output / 'COMPILE_HANDOFF.json').read_bytes()).hexdigest(),
                compiled_rows=len(result['rows']), skipped_rows=len(result['skipped']), fit_executed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    print(json.dumps(execute(options.request, options.request_sha256, options.output)))
