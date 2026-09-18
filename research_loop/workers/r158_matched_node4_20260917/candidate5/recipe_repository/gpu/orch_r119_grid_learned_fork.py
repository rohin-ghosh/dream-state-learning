"""Explicit gen1 frozen-LoRA fork retaining the prior public GRID life context."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ERA = 'learned_fork_r119'
CHECKPOINT = Path('/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1/generation_000000/sleep/checkpoint/CHECKPOINT.json')
CHECKPOINT_SHA = '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'
OPTIMIZER_SHA = '2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5'
CONTINUATION_SHA = '9de64111bc02c2db61050e36aa244bc8c558440b7682ac8699f4590515d9439b'


def validate_checkpoint(path=CHECKPOINT):
    path = Path(path)
    require = lambda condition, reason: None if condition else fail(reason)
    require(hashlib.sha256(path.read_bytes()).hexdigest() == CHECKPOINT_SHA, 'actual_gen1_checkpoint')
    document = json.loads(path.read_text())
    require(document['complete'] is True and document['optimizer_rng_sha256'] == OPTIMIZER_SHA,
            'complete_checkpoint_original_optimizer_preserved')
    require(hashlib.sha256((path.parent / 'optimizer_rng.pt').read_bytes()).hexdigest() == OPTIMIZER_SHA,
            'original_optimizer_copied_not_reset')
    adapter = document['adapter']
    require(Path(adapter['path']) == path.parent / 'adapter', 'exact_saved_adapter_path')
    for name, digest in adapter['files']:
        require(Path(name).name == name and hashlib.sha256((Path(adapter['path']) / name).read_bytes()).hexdigest() == digest,
                'exact_saved_adapter_file')
    return document


def fail(reason):
    raise ValueError(reason)


def load_runtime():
    path = Path(__file__).with_name('orch_r119_grid_continuation.py')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == CONTINUATION_SHA
    spec = importlib.util.spec_from_file_location('r119_fork_continuation', path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    original = base.configure

    def configure(args):
        require = base.require
        require(args.physical == 7, 'only_assigned_ovx2_7')
        module, grid, root, config = original(args)
        checkpoint = validate_checkpoint()
        release = grid.read(root / 'continuation_r119_1710/SCOPED_SETTLED_RELEASE.json')
        require(release['pid'] == 2276637 and release['all_charged_current_TRAIN_and_parents_terminal']
                and release['ledger_sha256'] == '71f8496b1b818588a7356f34a10ef6b92aef7966ef9ef7a82e8d9fd6bbb5b985',
                'actual_BASE_predecessor_settled_for_fork')
        before = grid.policy.queue_request

        def queue(*values, **kwargs):
            result = before(*values, **kwargs)
            result['lane_deadline_unix'] += 480
            return result

        grid.policy.queue_request = queue
        original_load = grid.load_engine

        def load_engine(config):
            from peft import PeftModel
            from gpu import orch_guided_native as native
            engine = original_load(config)
            identity = native.bridge.AdapterIdentity.from_document(checkpoint['adapter'])
            engine.model = PeftModel.from_pretrained(engine.model, identity.path,
                is_trainable=False, local_files_only=True, autocast_adapter_dtype=False)
            engine.model.requires_grad_(False)
            engine.model.eval()
            observed = native.observe_adapter(engine, identity)
            require(observed == identity, 'actual_gen1_params_and_original_base')
            engine.no_adapter = dict(mode='LEARNED_CHILD_FROZEN_LORA_ELICITATION_ONLY',
                adapter=identity.document(), local_optimizer=None, optimizer_steps=0,
                optimizer_archive_sha256=OPTIMIZER_SHA, prior_BASE_lineage_not_relabelled=True)
            engine.verify_base = lambda: require(native.observe_adapter(engine, identity) == identity,
                                                  'frozen_gen1_params_unchanged')
            return engine

        grid.load_engine = load_engine
        original_write = grid.write

        def write(path, value, replace=False):
            if isinstance(value, dict) and value.get('status') in ('STARTED', 'COMPLETE') and 'messages' in value:
                require(value.get('split') == 'TRAIN' and not value.get('attached_readout'), 'new_fork_TRAIN_only')
                value = dict(value, adapter=checkpoint['adapter'], fork_checkpoint_sha256=CHECKPOINT_SHA,
                    fork_generation=1, local_optimizer_steps=0, continuation_role='LEARNED_CHILD_ELICITATION_ONLY')
            return original_write(path, value, replace=replace)

        grid.write = write
        return module, grid, root, config

    base.configure = configure
    base.__file__ = __file__
    base.ERA, base.TERMINAL = ERA, 'R119_LEARNED_GRID_TERMINAL.json'
    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'guard', 'native'))
    parser.add_argument('--physical', type=int, choices=(7,), required=True)
    parser.add_argument('--old-source', type=Path, required=True)
    args = parser.parse_args()
    base = load_runtime()
    result = getattr(base, args.mode)(args)
    if result is not None:
        print(json.dumps(result))


if __name__ == '__main__':
    main()
