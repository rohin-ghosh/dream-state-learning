"""Single admitted fresh-child numerical validation, never a science learner."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read_bound(path, expected):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve()
            and not any(parent.is_symlink() for parent in (path, *path.parents)), 'canonical_pinned_file')
    raw = path.read_bytes()
    require(len(raw) <= 16*1024**2 and hashlib.sha256(raw).hexdigest() == expected, 'pinned_file_bytes')
    return json.loads(raw)


def file_sha(path):
    with Path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return digest


def verify_sources(manifest):
    require(manifest.get('schema') == 'R163_PROBE_SOURCE_PINS_V1'
            and type(manifest.get('files')) is dict and manifest['files'], 'explicit_source_closure')
    for name, expected in manifest['files'].items():
        path = Path(name)
        require(path.is_absolute() and path == path.resolve() and not path.is_symlink()
                and file_sha(path) == expected, 'exact_probe_dependency_bytes:'+name)


def verify_imports(manifest):
    origins = {}
    for name, module in tuple(sys.modules.items()):
        if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
            path = str(Path(module.__file__).resolve())
            require(path in manifest['files'] and file_sha(path) == manifest['files'][path],
                    'actual_import_in_pinned_closure:'+name)
            origins[name] = dict(path=path, sha256=manifest['files'][path])
    return origins


@dataclass(frozen=True)
class Component:
    label: str
    input_ids: tuple
    labels: tuple
    target_ids: tuple
    objective_weight: float


@dataclass(frozen=True)
class Batch:
    components: tuple

    @property
    def sha256(self):
        raw = json.dumps(asdict(self), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        return hashlib.sha256(raw).hexdigest()


def validation_batch(tokenizer, anchors, length, *, label='NEW', one_token=False):
    from gpu.orch_r161_native_executor import FAMILIES
    seed = tuple(tokenizer.encode('This is a synthetic numerical validation sequence, not a training example.',
                                  add_special_tokens=False))
    target = tuple(tokenizer.encode('A checked observation differs from an untested assertion.', add_special_tokens=False))
    require(label in ('NEW', 'REHEARSAL') and type(one_token) is bool, 'explicit_validation_case')
    if one_token:
        target = target[:1]
    require(seed and target and len(target) < length and not set(tokenizer.all_special_ids).intersection(seed+target),
            'ordinary_synthetic_validation_tokens')
    prefix_size = length-len(target)
    prefix = (seed*((prefix_size+len(seed)-1)//len(seed)))[:prefix_size]
    components = [Component(label, prefix+target, (-100,)*prefix_size+target, target, 0.75)]
    for family in FAMILIES:
        sample = max(anchors[family], key=lambda item: len(item['encoded'].input_ids))['encoded']
        require(len(sample.input_ids) <= 1024, 'full_anchor_capacity_bound')
        components.append(Component('ANCHOR:'+family, tuple(sample.input_ids), tuple(sample.labels),
            tuple(sample.target_ids), 0.0625))
    return Batch(tuple(components))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args(argv)
    plan = read_bound(args.plan, args.plan_sha256)
    manifest = read_bound(args.manifest, args.manifest_sha256)
    verify_sources(manifest)
    require(file_sha(__file__) == manifest['files'].get(str(Path(__file__).resolve())), 'driver_in_source_closure')
    require(plan.get('r163_validation_only') is True and plan.get('context_limit') == 16384,
            'isolated_16k_validation_plan')
    require(time.time() < plan['hard_end_unix'] <= time.time()+1800
            and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'bounded_admitted_probe')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1',
            'local_model_only')
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r108_guided_native import validate_anchor_inventory
    from gpu.orch_r161_native_executor import NativeExecutor
    from gpu.orch_r163_executor_probe import run_probe
    native.validate_plan(plan)
    verify_imports(manifest)
    root = Path(plan['root'])
    require(root.is_absolute() and root == root.resolve() and not root.exists(), 'new_validation_root_only')
    root.mkdir()
    native.write_once(root/'PLAN.json', plan)
    child = native.NativeChild(plan, checkpoint=None)
    verify_imports(manifest)
    initial = child.checkpoint(root/'initial')
    reference = dict(path=str(root/'initial/COMMIT.json'), sha256=file_sha(root/'initial/COMMIT.json'))
    binding = dict(fork_root=str(root), mode='learning', authority_sha256=args.plan_sha256,
        initializer_commit_sha256=reference['sha256'])
    executor = NativeExecutor(child, fork_binding=binding, execution_kind='VALIDATION_ONLY',
        initializer_reference=reference)
    require(executor.verify_checkpoint(reference) == executor.snapshot(), 'fresh_initializer_saved_state_verified')
    anchors, inventory = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
    validate_anchor_inventory(anchors)
    native.write_once(root/'ANCHOR_INVENTORY.json', inventory)
    pairs = (validation_batch(child.tokenizer, anchors, 64, one_token=True),
        validation_batch(child.tokenizer, anchors, 512),
        validation_batch(child.tokenizer, anchors, 1024, label='REHEARSAL'))
    longest = validation_batch(child.tokenizer, anchors, plan['context_limit'])
    native.write_once(root/'VALIDATION_BATCHES.json', dict(synthetic=True,
        pairs=[dict(sha256=batch.sha256, **asdict(batch)) for batch in pairs],
        longest=dict(sha256=longest.sha256, **asdict(longest))))
    receipt = run_probe(executor, pairs, longest, root/'numerical')
    verify_sources(manifest)
    origins = verify_imports(manifest)
    require(receipt['real_7b_validated'] and receipt['status'] == 'PASS', 'actual_numerical_proof_required')
    native.write_once(root/'COMPLETE.json', dict(schema='R163_NUMERICAL_VALIDATION_COMPLETE_V1',
        status='PASS', real_7b_validated=True, source_manifest_sha256=args.manifest_sha256,
        plan_sha256=args.plan_sha256, origins=origins, initial_checkpoint=reference,
        numerical_receipt=dict(path=str(root/'numerical/PROBE.json'), sha256=file_sha(root/'numerical/PROBE.json')),
        scientific_optimizer_updates=0, safe_existing_checkpoint_loader_validated=False,
        requires_separate_training_admission=True, finished_unix=time.time()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
