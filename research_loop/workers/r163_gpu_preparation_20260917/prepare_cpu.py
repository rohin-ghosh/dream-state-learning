"""CPU-only asset/import and fresh-plan preparation; never invokes a model."""

import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r163_numerical_preparation_20260917_attempt1')
SOURCE = ROOT / 'source'
MODEL = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28')
ANCHORS = Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
LEASE = Path('/localhome/local-rohing/orch_r118_node3_7_grid_20260915_attempt1/lease_budget_r119_learned/LEASE_BUDGET.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')


def main():
    assert socket.gethostname() == '[REDACTED_HOST]'
    assert os.getuid() == os.getgid() == 2524
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert sha(SOURCE / 'STAGED_SOURCE.json') == '044746077805b5a461970acd8e9c066de71e170996a5f919cb32746754453cce'
    assert sha(SOURCE / 'gpu/orch_r125_continual_native.py') == 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'
    assert sha(LEASE) == '919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770'
    assert sha(ANCHORS / 'ANCHOR_MANIFEST.json') == '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
    assert not (ROOT / 'validation_run1').exists()
    sys.path.insert(0, str(SOURCE))
    native = importlib.import_module('gpu.orch_r125_continual_native')
    plain = importlib.import_module('organism_v6.orch_r125_plain_context')
    assert Path(native.__file__).resolve() == SOURCE / 'gpu/orch_r125_continual_native.py'
    modules = {}
    for name in ('torch', 'transformers', 'peft', 'tokenizers', 'safetensors'):
        module = importlib.import_module(name)
        modules[name] = dict(distribution=importlib.metadata.version(name),
                            imported=getattr(module, '__version__', None),
                            path=str(Path(module.__file__).resolve()),
                            entrypoint_sha256=sha(module.__file__))
    torch = sys.modules['torch']
    assert torch.cuda.is_initialized() is False
    tokenizer = sys.modules['transformers'].AutoTokenizer.from_pretrained(str(MODEL), local_files_only=True)
    config = json.loads((MODEL / 'config.json').read_bytes())
    assert config['model_type'] == 'qwen2' and config['hidden_size'] == 3584
    assert config['num_hidden_layers'] == 28 and config['vocab_size'] == 152064
    assert config['max_position_embeddings'] >= 16384
    budget = json.loads(LEASE.read_bytes())
    plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
                system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
                presentation_version=plain.VERSION, context_limit=16384,
                segment_tokens=512, segments_per_sleep=2, max_sleeps=None,
                new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
                presleep_variant='free_distillation',
                compaction_invitation='You are about to sleep. Distill from your history what you want to carry forward.',
                seed=0, physical=5, gpu_uuid='GPU-bc211959-642d-664b-3581-42a0dbe434e9',
                model_dir=str(MODEL), anchors=str(ANCHORS), source_root=str(SOURCE),
                root=str(ROOT / 'validation_run1'), hard_end_unix=1789646400,
                lease_end_unix=budget['lease_end_unix'], readout_revision=1,
                decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
                r163_validation_only=True)
    assert native.validate_plan(plan) == plan
    assert plan['hard_end_unix'] + 21600 <= budget['hard_end_unix']
    assert time.time() + 1800 < plan['hard_end_unix']
    assert not any(key in plan for key in ('initialization_source', 'preupdate_recovery', 'matched_cohort'))
    assets = {}
    for path in sorted(MODEL.iterdir()):
        if not path.is_file():
            continue
        item = dict(path=str(path), resolved_path=str(path.resolve()), bytes=path.stat().st_size,
                    symlink=path.is_symlink(), mtime_ns=path.stat().st_mtime_ns)
        if path.suffix in ('.json', '.txt', '.model', '.tiktoken'):
            item['sha256'] = sha(path)
        else:
            item['content_rehashed'] = False
            item['content_addressed_blob_name'] = path.resolve().name
        assets[path.name] = item
    manifest = json.loads((ANCHORS / 'ANCHOR_MANIFEST.json').read_bytes())
    anchor_metadata = dict(root=str(ANCHORS), manifest_path=str(ANCHORS / 'ANCHOR_MANIFEST.json'),
                           manifest_sha256=sha(ANCHORS / 'ANCHOR_MANIFEST.json'),
                           anchors_path=manifest['anchors_path'], anchors_sha256=manifest['anchors_sha256'],
                           anchor_rows_rehashed=False, held_readouts_opened=False)
    assert Path(manifest['anchors_path']).is_file()
    assert torch.cuda.is_initialized() is False
    write(ROOT / 'PLAN.json', plan)
    result = dict(status='CPU_PREPARED_DRIVER_REVIEW_PENDING_NO_GPU', observed_unix=time.time(),
                  interpreter=sys.executable, python=sys.version, imports=modules,
                  source_root=str(SOURCE), source_manifest_sha256=sha(SOURCE / 'STAGED_SOURCE.json'),
                  plan_path=str(ROOT / 'PLAN.json'), plan_sha256=sha(ROOT / 'PLAN.json'),
                  native_plan_validation='PASS', exact_native_SYSTEM_BIRTH=True,
                  fresh_seed=0, checkpoint_loaded=False, model_loaded=False, cuda_initialized=False,
                  tokenizer=dict(class_name=type(tokenizer).__name__, vocab_size=tokenizer.vocab_size,
                                 eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id),
                  model_assets=assets, anchors=anchor_metadata,
                  lease=dict(path=str(LEASE), sha256=sha(LEASE), hard_end_unix=budget['hard_end_unix'],
                             lease_end_unix=budget['lease_end_unix'], provider_booking_verified=False),
                  proposed_service_runtime_seconds=1800, probe_outer_hard_end_unix=plan['hard_end_unix'],
                  existing_hardwall_margin_seconds=budget['hard_end_unix']-plan['hard_end_unix'],
                  no_service_created=True, no_gpu_process_started=True)
    write(ROOT / 'CPU_PREPARATION.json', result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
