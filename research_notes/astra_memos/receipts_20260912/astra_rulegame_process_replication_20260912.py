"""Explicit FIT-seed0/1 process-V2 replication; independent Main-operated phases.

No coordinator, automatic phase launch, scientific pass gate or new material.
Historical driver files are imported by exact hash and never monkeypatched.
Local phase methods are static adaptations of their seed/protocol-bound paths.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import stat
import sys
import time

sys.dont_write_bytecode = True
SELF = Path(__file__).resolve()
WRITE_SOURCE = Path('/tmp/astra_rulegame_process_write_20260912.py')
WRITE_SHA = 'a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9'
READOUT_SOURCE = Path('/tmp/astra_rulegame_process_readout_20260912.py')
READOUT_SHA = '46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46'
WRITE_VERSION = 'rulegame_process_fit_seed_write_v1_20260912'
READOUT_VERSION = 'rulegame_process_fit_seed_readout_v1_20260912'
FIT_SEEDS = (0, 1)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bytes_read(path, limit=32*1024*1024):
    path = Path(os.path.abspath(Path(path).expanduser()))
    require(not any(part.is_symlink() for part in (path, *path.parents)), 'symlink source rejected')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
                'special/hardlinked/oversized metadata rejected')
        data = stream.read(limit+1)
        after = os.fstat(stream.fileno())
        require(len(data) == before.st_size and all(getattr(before, key) == getattr(after, key)
            == getattr(path.stat(), key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
            'metadata changed while reading')
    return data


def load_support(path, checksum, name):
    data = bytes_read(path, 2*1024*1024)
    require(hashlib.sha256(data).hexdigest() == checksum, 'frozen helper changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


base_write = load_support(WRITE_SOURCE, WRITE_SHA, 'replication_frozen_writer')
base_readout = load_support(READOUT_SOURCE, READOUT_SHA, 'replication_frozen_readout')


def seed_check(seed):
    require(type(seed) is int and seed in FIT_SEEDS, 'only additional FIT seeds0/1 accepted')
    return seed


def contract(seed):
    seed_check(seed)
    return dict(version='process_fit_seed_replication_v1', fit_seed=seed, planned_fit_seeds=list(FIT_SEEDS),
        generation_seed=20260912, purpose='quiz/persistent-output repeatability; not conditional prediction/internalization',
        scientific_criterion='Main-side existing registration; runner descriptive only', automatic_promotion=False,
        record_harm='report separately; no tolerance or rescue gate', automatic_next_phase=False,
        write_controller_seconds=1200, write_collection_seconds=300,
        readout_controller_seconds=1800, readout_collection_seconds=300,
        aggregate_reservation_ceiling_seconds=3600, combined_controller=False,
        accounting='Separate released stages; CPU gaps after release are elapsed wall, not GPU reservation. Collections require separate tooling.')


class WritePhase:
    SELF = SELF
    WRITE_PROTOCOL = WRITE_VERSION
    PROTOCOL = base_write.PROTOCOL
    API = base_write.API
    CLAIMS = base_write.CLAIMS
    CONDITIONING = base_write.CONDITIONING
    ORIGIN = base_write.ORIGIN
    local_path = staticmethod(base_write.local_path)
    overlaps = staticmethod(base_write.overlaps)
    verify_inputs = staticmethod(base_write.verify_inputs)
    check_pair = staticmethod(base_write.check_pair)
    full_tokens = staticmethod(base_write.full_tokens)
    load_native = staticmethod(base_write.load_native)
    worker_ownership = staticmethod(base_write.worker_ownership)

    def __init__(self, fit_seed):
        self.fit_seed = seed_check(fit_seed)

    def fit_config(self, trainer, model):
        return replace(base_write.fit_config(trainer, model), seed=self.fit_seed)

    def implementation(self, source_root, diagnostic):
        pins = base_write.implementation(source_root, diagnostic)
        require(base_write.digest(WRITE_SOURCE) == WRITE_SHA and base_write.digest(READOUT_SOURCE) == READOUT_SHA,
                'historical driver changed')
        pins.update({str(SELF): base_write.digest(SELF), str(READOUT_SOURCE): READOUT_SHA,
                     str(base_readout.FROZEN_READOUT): base_readout.FROZEN_SHA256})
        require(all(base_write.digest(path) == value for path, value in pins.items()), 'source dependency changed')
        return pins

    def bind_reference(self, plan):
        require(plan.get('fit_seed') == self.fit_seed and type(plan.get('fit_seed')) is int
                and plan.get('replication') == contract(self.fit_seed), 'FIT seed/replication contract changed')
        reference = plan['reference_write']
        root, original, diagnostic, _, _ = base_write.checked_plan(reference['root'], reference['plan_sha256'])
        require(original['config']['seed'] == 2 and original['init_adapter'] is None,
                'reference must be original fresh-base seed2 process-V2 write')
        require(not (root/'run/failure.json').exists() and base_write.digest(root/'run/result.json') == reference['result_sha256'],
                'reference completion changed')
        for key in ('formation_root', 'formation_plan_sha256', 'formation_manifest_sha256', 'formation_files',
                    'formation_completion_sha256', 'model', 'model_files', 'original_identity', 'main_review_path',
                    'main_review_sha256', 'fixed_candidate_path', 'fixed_candidate_sha256', 'candidate_sha256',
                    'process_api', 'exporter_source_hashes', 'material_files', 'material_manifest_sha256',
                    'tokens', 'source_root', 'python'):
            require(plan[key] == original[key], 'reference material/lineage changed: '+key)
        require(plan['config'] == dict(original['config'], seed=self.fit_seed), 'only FIT seed may change recipe')
        return root, original, diagnostic

    def prepare(self, reference_root, reference_plan_sha256, out, device, deadline, lease_end):
        root, original, diagnostic, exporter, trainer = base_write.checked_plan(reference_root, reference_plan_sha256)
        require(original['config']['seed'] == 2, 'only original seed2 reference accepted')
        output = base_write.local_path(out, fresh=True)
        require(output.parent == root.parent and not base_write.overlaps(output, root), 'fresh sibling reference/output required')
        for protected in (original['formation_root'], original['source_root'], original['model'],
                          original['main_review_path'], original['fixed_candidate_path']):
            require(not base_write.overlaps(output, Path(protected)), 'output overlaps protected input')
        require(device == original['device'], 'retain original explicit device; no implicit reassignment')
        end, lease = base_write.timestamp(deadline), base_write.timestamp(lease_end)
        require(time.time()+1200 < end <= lease-21600, 'need inherited1200s write window and six-hour lease margin')
        reference_plan = dict(write_root=str(root), write_plan_sha256=reference_plan_sha256,
            write_driver=str(WRITE_SOURCE), write_driver_sha256=WRITE_SHA,
            model=original['model'], model_files=original['model_files'], source_root=original['source_root'],
            source_pins=original['implementation'], device=original['device'], python=original['python'])
        reference_lineage = base_readout.accepted_writes(reference_plan, native=True)
        plan = dict(original, protocol=self.WRITE_PROTOCOL, out=str(output), fit_seed=self.fit_seed,
            replication=contract(self.fit_seed), reference_write=dict(root=str(root), plan_sha256=reference_plan_sha256,
                result_sha256=reference_lineage['result_sha256']),
            config=asdict(self.fit_config(trainer, original['model'])), sidecar=str(SELF),
            implementation=self.implementation(original['source_root'], diagnostic),
            deadline=end, supplied_lease_end=lease, lease_cutoff=lease-21600)
        self.bind_reference(plan)
        output.mkdir(mode=0o700)
        try:
            material = output/'material'
            material.mkdir(mode=0o700)
            entries = dict(original['material_files'], **{'manifest.json': original['material_manifest_sha256']})
            require(len(entries) <= 256, 'bounded material entries required')
            total = 0
            for name, pin in sorted(entries.items()):
                relative = Path(name)
                require(not relative.is_absolute() and '..' not in relative.parts and relative.suffix == '.json', 'unsafe material path/type')
                data = bytes_read(root/'material'/relative)
                total += len(data)
                require(total <= 64*1024*1024 and hashlib.sha256(data).hexdigest() == pin, 'raw material bytes/pin changed')
                destination = material/relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'wb') as stream:
                    stream.write(data)
            require(base_readout.accepted_writes(reference_plan) == reference_lineage, 'reference pair changed during prepare')
            require(time.time()+1200 < end, 'preparation exhausted write window')
            base_write.write_json(output/'plan.json', plan)
            pin = base_write.digest(output/'plan.json')
            self.checked_plan(output, pin)
            base_write.write_json(output/'plan.sha256.json', dict(sha256=pin))
            return dict(status='PREPARED_SEED_WRITE', root=str(output), plan_sha256=pin, fit_seed=self.fit_seed,
                        readout='SEPARATE_PREPARE_AND_MAIN_LAUNCH_REQUIRED', automatic_promotion=False)
        except BaseException as error:
            base_write.write_json(output/'prepare_failure.json', dict(error=type(error).__name__+': '+str(error), retry=False))
            raise

    def checked_plan(self, root, expected_hash):
        root = base_write.local_path(root)
        require(not (root / 'prepare_failure.json').exists(), 'failed preparation cannot launch; preserve root')
        base_write.require(base_write.digest(root / 'plan.json') == expected_hash, 'plan hash mismatch')
        raw = json.loads((root / 'plan.json').read_text())
        diagnostic, exporter, trainer = base_write.modules(raw['source_root'])
        plan = diagnostic.read(root / 'plan.json')
        self.bind_reference(plan)
        base_write.require(plan.get('schema') == 2 and plan.get('protocol') == self.WRITE_PROTOCOL and (plan.get('material_protocol') == base_write.PROTOCOL) and (plan.get('process_api') == base_write.API) and (plan.get('conditioning') == base_write.CONDITIONING) and (plan.get('model_origin') == base_write.ORIGIN) and (plan.get('claims') == base_write.CLAIMS), 'process-v2 plan/API/claim boundary mismatch')
        base_write.require(plan['out'] == str(root) and plan['sidecar'] == str(self.SELF) and (plan['arms'] == list(base_write.ARMS)), 'plan root/sidecar/order mismatch')
        base_write.require(plan['python'] == os.path.abspath(sys.executable), 'concrete native interpreter differs; never resolve virtualenv symlink')
        base_write.require(plan['config'] == asdict(self.fit_config(trainer, plan['model'])) and plan['init_adapter'] is None, 'fixed fit recipe changed')
        base_write.require((plan['controller_seconds'], plan['worker_seconds'], plan['cleanup_seconds'], plan['lease_margin_seconds']) == (1200, 600, 140, 21600) and plan['deadline'] <= plan['lease_cutoff'] == plan['supplied_lease_end'] - base_write.LEASE_MARGIN, 'controller/worker/lease bounds changed')
        base_write.require(self.implementation(plan['source_root'], diagnostic) == plan['implementation'], 'implementation binding changed')
        base_write.require(exporter.source_hashes() == plan['exporter_source_hashes'], 'process exporter sources changed')
        base_write.require(diagnostic.WORKER_SECONDS == base_write.WORKER_SECONDS and diagnostic.CLEANUP_RESERVE == base_write.CLEANUP_SECONDS, 'reused supervisor bounds differ')
        material = root / 'material'
        base_write.require(base_write.digest(material / 'manifest.json') == plan['material_manifest_sha256'] and diagnostic.read(material / 'manifest.json')['files'] == plan['material_files'] and (diagnostic.tree_hashes(material, ('manifest.json',)) == plan['material_files']), 'sealed material changed')
        exported = diagnostic.read(material / 'export_manifest.json')
        base_write.require(exported['protocol'] == base_write.PROTOCOL and exported['candidate_sha256'] == plan['candidate_sha256'] and (exported['source_hashes'] == plan['exporter_source_hashes']) and (exported['corpus_files'] == {arm: 'corpora/' + arm + '.json' for arm in base_write.ARMS}) and all((plan['material_files'].get(name) == value for name, value in exported['files'].items())), 'process export binding changed')
        self.verify_inputs(plan, diagnostic)
        return (root, plan, diagnostic, exporter, trainer)

    def validate_fit(self, root, arm, plan, diagnostic, trainer):
        fit = root / 'fits' / arm
        adapter = fit / 'adapter'
        base_write.require((adapter / 'DONE').is_file() and (not (adapter / 'EMPTY_CORPUS').exists()), 'adapter incomplete')
        manifest = diagnostic.read(adapter / 'train_manifest.json')
        expected = plan['tokens'][arm]
        base_write.require(manifest['recipe'] == trainer.RECIPE and manifest['config'] == plan['config'] and (manifest['base_model'] == plan['model']) and ('warm_start' not in manifest), 'fit recipe/base/warm-start mismatch')
        base_write.require(manifest['empty'] is False and manifest['steps'] == manifest['micro_batches'] == manifest['epochs_run'] == base_write.STEPS and (manifest['nonfinite_batches'] == 0) and math.isfinite(manifest['final_loss']) and (len(manifest['mean_loss_per_epoch']) == base_write.STEPS) and all((math.isfinite(value) for value in manifest['mean_loss_per_epoch'])), 'fit incomplete, nonfinite or wrong update count')
        base_write.require(manifest['corpus'] == dict(file=arm + '.json', sha256=plan['material_files']['corpora/' + arm + '.json'], n_items=2, n_encoded=2, n_skipped_no_target=0), 'fit corpus mismatch')
        base_write.require(manifest['tokens'] == expected['tokens'] and manifest['train_tokens_seen'] == expected['train_tokens_seen'], 'fit token counts mismatch')
        base_write.require(diagnostic.read(adapter / 'train_meta.json') == dict(recipe=trainer.RECIPE, n_texts=2, steps=12, tokens=expected['train_tokens_seen'], rank=8, epochs=12, lr=0.0001, seed=self.fit_seed, final_loss=manifest['final_loss']), 'trainer summary counts/config mismatch')
        base_write.require(manifest['truncation'] == dict(overflow='split', items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0, segments_from_splits=0, max_segment_tokens=expected['max_segment_tokens']), 'fit dropped/split tokens')
        base_write.require(manifest['packing']['mode'] == 'one_item_per_sequence' and manifest['packing']['n_sequences'] == 2 and (manifest['packing']['n_groups'] == 2) and (not manifest['packing']['isolation_check']['ran']), 'unexpected packing')
        before, after = (diagnostic.read(fit / name) for name in ('pre_update_trainability.json', 'post_update_trainability.json'))
        base_write.require(before == after and before['base_frozen'] and (before['init_adapter'] is None) and (before['adapter_count'] == 1), 'trainability changed')
        layers = diagnostic.read(Path(plan['model']) / 'config.json')['num_hidden_layers']
        base_write.require(manifest['lora'] == dict(rank=8, alpha=16, dropout=0.05, scaling=2.0, target_modules=list(trainer.ALL_PROJ), layers='all', n_layers=layers, freeze_a=False, trainable_params=before['trainable_params']), 'LoRA count/config mismatch')
        saved = diagnostic.read(adapter / 'adapter_config.json')
        base_write.require(saved['r'] == 8 and saved['lora_alpha'] == 16 and (saved['lora_dropout'] == 0.05) and (saved['bias'] == 'none') and (saved['peft_type'] == 'LORA') and (set(saved['target_modules']) == set(trainer.ALL_PROJ)) and (not saved.get('modules_to_save')) and (not saved.get('layers_to_transform')) and (base_write.local_path(saved['base_model_name_or_path']) == Path(plan['model'])), 'saved adapter config/base mismatch')
        base_write.require(not (adapter / 'adapter_model.bin').exists(), 'unexpected alternate weight file')
        tensors = base_write.saved_weights(adapter / 'adapter_model.safetensors', before['adapters'])
        files = diagnostic.tree_hashes(adapter)
        base_write.require(not any((name.startswith(('model', 'pytorch_model', 'optimizer')) for name in files)), 'unexpected base/optimizer checkpoint')
        actual_tokens = diagnostic.read(fit / 'full_tokens.json')
        base_write.require(base_write.digest(fit / 'full_tokens.json') == plan['material_files']['provenance/' + arm + '.tokens.json'], 'worker token receipt differs from preparation')
        base_write.require(actual_tokens['tokens'] == expected['tokens'], 'worker token receipt mismatch')
        forward_files = {f'{index + 1:04d}.json' for index in range(base_write.STEPS)}
        base_write.require(set(diagnostic.tree_hashes(fit / 'forwards')) == forward_files, 'missing/extra actual forward exposure receipts')
        for index in range(base_write.STEPS):
            observed = diagnostic.read(fit / 'forwards' / f'{index + 1:04d}.json')
            batch = base_write.expected_forward_batch(actual_tokens, observed['row_order'])
            base_write.require(observed == base_write.forward_receipt(batch, actual_tokens, index), 'actual forward exposure changed')
        return dict(arm=arm, adapter=str(adapter), files=files, manifest_sha256=files['train_manifest.json'], saved_tensors=tensors, trainable_params=before['trainable_params'], steps=base_write.STEPS, tokens=manifest['tokens'], train_tokens_seen=manifest['train_tokens_seen'], readout='OUT_OF_SCOPE', observed_forward_batches=base_write.STEPS, exposure=actual_tokens['exposure'])

    def worker(self, root, arm, plan_sha256, launch_token, allow_gpu=False):
        base_write.require(allow_gpu, '--allow-gpu required before worker/model work')
        base_write.require(arm in base_write.ARMS, 'unknown arm')
        root, plan, diagnostic, _, trainer = self.checked_plan(root, plan_sha256)
        launch = diagnostic.read(root / 'run' / (arm + '.launch.json'))
        base_write.require(launch['token'] == launch_token and launch['plan_sha256'] == plan_sha256 and (time.time() < launch['hard_end'] - base_write.CLEANUP_SECONDS), 'worker not bound to active controller window')
        base_write.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['device'], 'worker device differs from reservation')
        with self.worker_ownership(root, arm, plan, launch, diagnostic):
            return self.fit_worker(root, arm, plan_sha256, plan, diagnostic, trainer)

    def fit_worker(self, root, arm, plan_sha256, plan, diagnostic, trainer):
        fit = root / 'fits' / arm
        fit.mkdir()
        base_write.write_json(fit / 'attempt.json', dict(arm=arm, plan_sha256=plan_sha256, init_adapter=None, pid=os.getpid()))
        base_write.require(diagnostic.model_hashes(plan['model']) == plan['model_files'], 'base changed before load')
        tokenizer, base = self.load_native(plan['model'])
        base_write.require(not hasattr(base, 'peft_config') and (not any(('lora_' in name for name, _ in base.named_parameters()))), 'base already adapted')
        base_write.require(base_write.local_path(base.name_or_path) == Path(plan['model']), 'loaded base identity mismatch')
        corpus_path = root / 'material' / 'corpora' / (arm + '.json')
        corpus = diagnostic.read(corpus_path)
        tokens = self.full_tokens(corpus, tokenizer, trainer)
        base_write.require(hashlib.sha256(base_write.encoded(tokens)).hexdigest() == plan['material_files']['provenance/' + arm + '.tokens.json'], 'native worker tokenization changed')
        base_write.write_json(fit / 'full_tokens.json', tokens)
        (fit / 'forwards').mkdir()
        recorded, forwards = ([], [])

        def before_forward(model, args, kwargs):
            base_write.require(not args and all((kwargs.get(key) is None for key in ('inputs_embeds', 'position_ids', 'past_key_values'))), 'unexpected positional/embedded/cached forward inputs')
            batch = {key: kwargs[key].detach().cpu().tolist() for key in ('input_ids', 'labels', 'attention_mask')}
            receipt = base_write.forward_receipt(batch, tokens, len(forwards))
            base_write.write_json(fit / 'forwards' / f'{len(forwards) + 1:04d}.json', receipt)
            forwards.append(receipt)
            if not recorded:
                receipt = base_write.trainability(base, base.config.num_hidden_layers)
                base_write.write_json(fit / 'pre_update_trainability.json', receipt)
                recorded.append(receipt)
        hook = base.register_forward_pre_hook(before_forward, with_kwargs=True)
        try:
            base_write.require(not (fit / 'adapter').exists() and (not (fit / 'adapter').is_symlink()), 'adapter output must be fresh')
            trainer.run_training(trainer.normalize_items(corpus), tokenizer, base, self.fit_config(trainer, plan['model']), str(fit / 'adapter'), corpus_sha=base_write.digest(corpus_path), corpus_name=corpus_path.name, init_adapter=None)
            base_write.require(recorded, 'no pre-update trainability evidence')
            base_write.require(len(forwards) == base_write.STEPS, 'exactly twelve observed paired forward batches required')
            base_write.write_json(fit / 'post_update_trainability.json', base_write.trainability(base, base.config.num_hidden_layers))
            base_write.require(diagnostic.model_hashes(plan['model']) == plan['model_files'], 'base files changed during fit')
            receipt = self.validate_fit(root, arm, plan, diagnostic, trainer)
            base_write.write_json(fit / 'receipt.json', receipt)
            base_write.write_json(fit / 'manifest.json', dict(files=diagnostic.tree_hashes(fit)))
            return receipt
        finally:
            hook.remove()

    def write_pair(self, root, plan_sha256, allow_gpu=False):
        base_write.require(allow_gpu, '--allow-gpu required before controller/GPU work')
        started, wall = (time.monotonic(), time.time())
        with base_write.controller_watchdog(wall + base_write.CONTROLLER_SECONDS):
            root, plan, diagnostic, _, trainer = self.checked_plan(root, plan_sha256)
        hard_end = min(wall + base_write.CONTROLLER_SECONDS, plan['deadline'], plan['lease_cutoff'])
        run = root / 'run'
        run.mkdir()
        completed = {}
        base_write.write_json(run / 'controller.json', dict(plan_sha256=plan_sha256, started_wall=wall, hard_end=hard_end, worker_seconds=base_write.WORKER_SECONDS, cleanup_reserve=base_write.CLEANUP_SECONDS, pid=os.getpid(), continuous_reservation='MAIN_LAUNCHER_RESPONSIBILITY_NOT_A_LOCK'))
        try:
            with base_write.controller_watchdog(hard_end):
                self.verify_inputs(plan, diagnostic)
                (root / 'fits').mkdir()
                for arm in base_write.ARMS:
                    self.checked_plan(root, plan_sha256)
                    self.verify_inputs(plan, diagnostic)
                    base_write.require(time.time() < hard_end - base_write.CLEANUP_SECONDS, 'insufficient time for next fresh fit')
                    for previous in completed.values():
                        base_write.require(diagnostic.tree_hashes(previous['adapter']) == previous['files'], 'prior independent adapter changed')
                    token = secrets.token_hex(16)
                    command = [plan['python'], '-B', str(self.SELF), '_write-worker', '--root', str(root), '--arm', arm, '--plan-sha256', plan_sha256, '--launch-token', token, '--allow-gpu']
                    base_write.write_json(run / (arm + '.launch.json'), dict(token=token, plan_sha256=plan_sha256, hard_end=hard_end, controller_pid=os.getpid(), command=command))
                    supervision_plan = dict(model=plan['model'], device=plan['device'], lease_end=hard_end)
                    with base_write.supervisor_cleanup_window(hard_end):
                        supervision = diagnostic.supervise(root, supervision_plan, run / arm, command)
                    base_write.require(time.time() < hard_end - base_write.CLEANUP_SECONDS, 'controller work window exhausted after cleanup')
                    base_write.require(supervision['ok'] and supervision['reservation_release_verified'], 'worker cleanup unverified')
                    fit = root / 'fits' / arm
                    base_write.require(diagnostic.read(fit / 'manifest.json')['files'] == diagnostic.tree_hashes(fit, ('manifest.json',)), 'sealed fit changed')
                    receipt = self.validate_fit(root, arm, plan, diagnostic, trainer)
                    base_write.require(diagnostic.read(root / 'fits' / arm / 'receipt.json') == receipt, 'worker receipt changed')
                    completed[arm] = dict(receipt, fit_manifest_sha256=base_write.digest(fit / 'manifest.json'), supervision_sha256=base_write.digest(run / arm / 'supervision.json'))
                base_write.require(all((diagnostic.tree_hashes(prior['adapter']) == prior['files'] and base_write.digest(root / 'fits' / arm / 'manifest.json') == prior['fit_manifest_sha256'] and (diagnostic.read(root / 'fits' / arm / 'manifest.json')['files'] == diagnostic.tree_hashes(root / 'fits' / arm, ('manifest.json',))) for arm, prior in completed.items())), 'saved independent adapter changed during paired write')
                self.verify_inputs(plan, diagnostic)
                self.checked_plan(root, plan_sha256)
            base_write.require(time.monotonic() - started <= base_write.CONTROLLER_SECONDS and time.time() <= hard_end, 'inclusive controller cap exceeded')
            result = dict(status='PAIRED_ADAPTERS_SAVED_READOUT_PENDING', arms=completed, readout='OUT_OF_SCOPE', controller_seconds=time.monotonic() - started, protocol=self.WRITE_PROTOCOL, conditioning=base_write.CONDITIONING, claims=base_write.CLAIMS, model_origin=base_write.ORIGIN, exposure={arm: plan['tokens'][arm]['exposure'] for arm in base_write.ARMS}, semantic_no_answer_certification=False, model_authentication_certified=False, fit_seed=self.fit_seed, automatic_promotion=False)
            base_write.write_json(run / 'result.json', result)
            return result
        except BaseException as error:
            base_write.write_json(run / 'failure.json', dict(status='PARTIAL_FAILED' if completed else 'FAILED', completed=completed, error=type(error).__name__ + ': ' + str(error), controller_seconds=time.monotonic() - started, retry=False, readout='NOT_RUN'))
            raise

class ReadoutPhase:
    SELF = SELF
    VERSION = READOUT_VERSION
    WRITE_PROTOCOL = WRITE_VERSION
    CELLS = base_readout.CELLS
    ORIGIN = base_readout.ORIGIN
    CONDITIONING = base_readout.CONDITIONING
    CLAIMS = base_readout.CLAIMS
    worker_spec = staticmethod(base_readout.worker_spec)
    work_window = staticmethod(base_readout.work_window)
    supervised_window = staticmethod(base_readout.supervised_window)
    owning_process = staticmethod(base_readout.owning_process)
    close_native = staticmethod(base_readout.close_native)

    def __init__(self, fit_seed):
        self.fit_seed = seed_check(fit_seed)

    def load_driver(self, path, expected_hash):
        require(base_write.local_path(path) == SELF and base_write.digest(SELF) == expected_hash,
                'readout must bind exact replication writer; no historical/foreign write')
        return WritePhase(self.fit_seed)

    def protocol(self, diagnostic):
        result = base_readout.protocol(diagnostic)
        require(result['gen_seed'] == 20260912, 'generation seed unchanged')
        result.update(name=self.VERSION, write_protocol=self.WRITE_PROTOCOL,
                      replication_fit_seed=self.fit_seed, automatic_promotion=False,
                      replication_purpose=contract(self.fit_seed)['purpose'])
        return result

    def process_metrics(self, data, audit, diagnostic):
        result = base_readout.process_metrics(data, audit, diagnostic)
        executions = [row for row in audit['events'] if row['kind']=='execution' and row['action_kind']=='try']
        predicted = [row for row in executions if type(row['predicted']) is bool and not row['prediction_ambiguous']]
        result['persistent_output_diagnostics'] = dict(
            valid_prediction_true=sum(row['predicted'] is True for row in predicted),
            valid_prediction_false=sum(row['predicted'] is False for row in predicted),
            valid_prediction_denominator=len(predicted),
            all_false_correct_on_valid_predicted_probes=sum(row['observed'] is False for row in predicted),
            all_false_correct_on_all_executed_probes=sum(row['observed'] is False for row in executions),
            executed_probe_denominator=len(executions),
            global_unique_triples=len({tuple(row['values']) for row in executions}),
            sum_task_local_unique_triples=result['totals']['distinct_probe_triples'],
            limitation='All-F baseline uses the same observed probes; no conditional learning/internalization or information gain inferred. Record fidelity counts remain separate.')
        return result

    def prepare(self, write_root, write_plan_sha256, write_driver, write_driver_sha256, out, deadline, lease_end):
        driver = self.load_driver(write_driver, write_driver_sha256)
        origin, written, diagnostic, _, _ = driver.checked_plan(write_root, write_plan_sha256)
        driver.verify_inputs(written, diagnostic)
        base_readout.require(base_readout.read(Path(written['formation_root']) / 'plan.json')['protocol'] == 'interaction_v3', 'v3 lineage required')
        output = driver.local_path(out, fresh=True)
        base_readout.require(output.parent == origin.parent and output != origin, 'fresh sibling readout root required')
        for protected in (written['model'], written['source_root'], written['formation_root'], written['main_review_path'], written['fixed_candidate_path'], write_driver, self.SELF):
            base_readout.require(not driver.overlaps(output, Path(protected).resolve()), 'readout overlaps protected input')
        end, lease = (base_readout.timestamp(deadline), base_readout.timestamp(lease_end))
        base_readout.require(time.time() + base_readout.CONTROLLER_SECONDS < end <= lease - base_readout.LEASE_MARGIN, 'need 1800s and six-hour lease margin')
        python = base_readout.absolute_python(sys.executable)
        base_readout.require(python == base_readout.absolute_python(written['python']), 'invoke prepare with exact write-plan venv interpreter; do not resolve symlink')
        plan = dict(schema=2, version=self.VERSION, out=str(output), write_root=str(origin), write_plan_sha256=write_plan_sha256, write_driver=str(Path(write_driver).resolve()), write_driver_sha256=base_readout.digest(write_driver), source_root=written['source_root'], source_pins=written['implementation'], model=written['model'], model_files=written['model_files'], device=written['device'], python=python, protocol=self.protocol(diagnostic), deadline=end, supplied_lease_end=lease, lease_cutoff=lease - base_readout.LEASE_MARGIN, self_path=str(self.SELF), self_sha256=base_readout.digest(self.SELF), write_status='COMPLETED_PROCESS_PAIR_NATIVE_VERIFIED', write_protocol=self.WRITE_PROTOCOL, material_protocol=base_readout.MATERIAL_PROTOCOL, conditioning=base_readout.CONDITIONING, model_origin=base_readout.ORIGIN, claims=base_readout.CLAIMS, lease_basis='Main-supplied real expiry; not control-plane verification')
        plan.update(fit_seed=self.fit_seed, replication=contract(self.fit_seed))
        plan['lineage'] = self.accepted_writes(plan, native=True)
        base_readout.require(time.time() + base_readout.CONTROLLER_SECONDS < end, 'native preparation exhausted controller window')
        base_readout.require(self.accepted_writes(plan) == plan['lineage'], 'process pair changed during preparation')
        output.mkdir()
        base_readout.write_json(output / 'plan.json', plan)
        frozen = base_readout.digest(output / 'plan.json')
        base_readout.write_json(output / 'plan.sha256.json', dict(sha256=frozen))
        return dict(status='PROCESS_READOUT_FROZEN_NATIVE_PAIR_VERIFIED', root=str(output), plan_sha256=frozen, model_origin=base_readout.ORIGIN, conditioning=base_readout.CONDITIONING, readout='NOT_RUN')

    def checked_plan(self, root, plan_sha256):
        root = Path(root).expanduser().resolve(strict=True)
        base_readout.require(base_readout.digest(root / 'plan.json') == plan_sha256, 'readout plan changed')
        plan = base_readout.read(root / 'plan.json')
        require(plan.get('fit_seed') == self.fit_seed and type(plan.get('fit_seed')) is int and (plan.get('replication') == contract(self.fit_seed)), 'readout FIT seed contract changed')
        base_readout.require(plan['schema'] == 2 and plan['version'] == self.VERSION and (plan['write_protocol'] == self.WRITE_PROTOCOL) and (plan['material_protocol'] == base_readout.MATERIAL_PROTOCOL) and (plan['conditioning'] == base_readout.CONDITIONING) and (plan['model_origin'] == base_readout.ORIGIN) and (plan['claims'] == base_readout.CLAIMS), 'process readout protocol/objective/origin differs')
        base_readout.require(plan['out'] == str(root) and plan['self_path'] == str(self.SELF) and (plan['self_sha256'] == base_readout.digest(self.SELF)), 'readout implementation/root changed')
        base_readout.require(base_readout.digest(plan['write_driver']) == plan['write_driver_sha256'], 'write driver changed')
        base_readout.require(all((base_readout.digest(path) == expected for path, expected in plan['source_pins'].items())), 'source bytes changed')
        diagnostic = base_readout.diagnostic_module(plan['source_root'])
        base_readout.require(plan['protocol'] == self.protocol(diagnostic), 'prospective readout protocol changed')
        base_readout.require(plan['deadline'] <= plan['lease_cutoff'] == plan['supplied_lease_end'] - base_readout.LEASE_MARGIN, 'lease bounds changed')
        base_readout.require(base_readout.absolute_python(sys.executable) == plan['python'], 'controller interpreter differs from native venv')
        base_readout.require(self.accepted_writes(plan) == plan['lineage'], 'completed process-write lineage changed')
        return (root, plan, diagnostic)

    def material_custody(self, driver, root, written, diagnostic, exporter, trainer, native=False):
        base_readout.require(written['protocol'] == self.WRITE_PROTOCOL and written['material_protocol'] == base_readout.MATERIAL_PROTOCOL and (written['conditioning'] == base_readout.CONDITIONING) and (written['model_origin'] == base_readout.ORIGIN) and (written['claims'] == base_readout.CLAIMS) and (written['init_adapter'] is None), 'wrong process material or nonfresh initial adapter')
        material = root / 'material'
        candidate = base_readout.read(material / 'audit/candidate.json')
        review = base_readout.read(material / 'audit/main_review.json')
        base_readout.require(candidate == base_readout.read(written['fixed_candidate_path']) and review == base_readout.read(written['main_review_path']), 'sealed candidate/Main review changed')
        base_readout.require(candidate == exporter.inspect_capture(Path(written['formation_root']) / 'formation/data', protocol=base_readout.MATERIAL_PROTOCOL), 'fixed process source selection/context differs')
        exporter._review(candidate, review, protocol=base_readout.MATERIAL_PROTOCOL)
        token_audit = base_readout.read(material / 'audit/token_receipts.json')
        export = base_readout.read(material / 'export_manifest.json')
        corpora = {arm: base_readout.read(material / 'corpora' / (arm + '.json')) for arm in ('P', 'A')}
        tokens = {arm: base_readout.read(material / 'provenance' / (arm + '.tokens.json')) for arm in ('P', 'A')}
        pair = dict(protocol=base_readout.MATERIAL_PROTOCOL, status=export['status'], corpora=corpora, audit=dict(token_audit, candidate=candidate, main_review=review))
        driver.check_pair(pair, candidate, review, tokens, diagnostic)
        base_readout.require(token_audit['native_identity_authenticated'] is False and token_audit['semantic_certification'] is False, 'material semantic/origin certification forbidden')
        tokenizer = diagnostic.native_tokenizer(written['model']) if native else None
        if native:
            diagnostic.audit_native_calls(tokenizer, Path(written['formation_root']) / 'formation/data')
        for arm in ('P', 'A'):
            base_readout.require({key: value for key, value in tokens[arm].items() if key not in ('rows', 'batch')} == written['tokens'][arm], 'prepared process token/exposure summary differs')
            for item, receipt, source in zip(corpora[arm]['corpus'], token_audit['receipts'][arm], [row for row in candidate['candidates'] if row['arm'] == arm], strict=True):
                context = receipt['transformed_training']['rendered_context']
                base_readout.require(item['spans'] == [[context, False, 'parent_removed_wake_context'], [source['target'], True, 'complete_own_raw_wake']] and item['view'] == base_readout.MATERIAL_PROTOCOL and (item['meta']['protocol'] == base_readout.MATERIAL_PROTOCOL), 'only masked transformed context and full own wake target allowed; no record/P0/extra context')
                if native:
                    base_readout.require(tokenizer.apply_chat_template([dict(role='user', content=source['context'])], tokenize=False, add_generation_prompt=True) == context, 'native parent-removed context differs; no parent/restatement insertion')
            if native:
                base_readout.require(driver.full_tokens(corpora[arm], tokenizer, trainer) == tokens[arm], 'process native raw-target/mask/EOS/token receipt mismatch')
        return dict(material_manifest_sha256=written['material_manifest_sha256'], candidate_sha256=written['candidate_sha256'], main_review_sha256=written['main_review_sha256'], process_api=written['process_api'], exporter_source_hashes=written['exporter_source_hashes'], tokens=written['tokens'])

    def accepted_writes(self, plan, native=False):
        driver = self.load_driver(plan['write_driver'], plan['write_driver_sha256'])
        root, written, diagnostic, exporter, trainer = driver.checked_plan(plan['write_root'], plan['write_plan_sha256'])
        driver.verify_inputs(written, diagnostic)
        base_readout.require(written['model'] == plan['model'] and written['model_files'] == plan['model_files'] and (written['source_root'] == plan['source_root']) and (written['implementation'] == plan['source_pins']) and (written['device'] == plan['device']) and (base_readout.absolute_python(written['python']) == plan['python']), 'write lineage differs')
        base_readout.require(not (root / 'run' / 'failure.json').exists(), 'failed/partial writes cannot be evaluated')
        result_path = root / 'run' / 'result.json'
        result = base_readout.read(result_path)
        require(type(result.get('fit_seed')) is int and result['fit_seed'] == self.fit_seed
                and result.get('automatic_promotion') is False, 'write result seed/promotion changed')
        base_readout.require(result['status'] == 'PAIRED_ADAPTERS_SAVED_READOUT_PENDING' and set(result['arms']) == {'P', 'A'}, 'both successful writes required')
        base_readout.require(result['protocol'] == self.WRITE_PROTOCOL and result['conditioning'] == base_readout.CONDITIONING and (result['model_origin'] == base_readout.ORIGIN) and (result['claims'] == base_readout.CLAIMS) and (result['model_authentication_certified'] is False) and (result['semantic_no_answer_certification'] is False), 'completed writer objective/origin/claims differ')
        custody = self.material_custody(driver, root, written, diagnostic, exporter, trainer, native)
        fits, training = ({}, {})
        for arm in ('P', 'A'):
            fit = root / 'fits' / arm
            base_readout.require(base_readout.read(fit / 'manifest.json')['files'] == diagnostic.tree_hashes(fit, ('manifest.json',)), 'fit seal changed')
            receipt = driver.validate_fit(root, arm, written, diagnostic, trainer)
            base_readout.require(base_readout.read(fit / 'receipt.json') == receipt, 'fit receipt changed')
            supervision_path = root / 'run' / arm / 'supervision.json'
            supervision = base_readout.read(supervision_path)
            base_readout.require(supervision['ok'] and supervision['reservation_release_verified'], 'write cleanup unverified')
            sealed = dict(receipt, fit_manifest_sha256=base_readout.digest(fit / 'manifest.json'), supervision_sha256=base_readout.digest(supervision_path))
            base_readout.require(result['arms'][arm] == sealed, 'completed pair receipt differs')
            fits[arm] = sealed
            manifest = base_readout.read(fit / 'adapter/train_manifest.json')
            base_readout.require(result['exposure'][arm] == written['tokens'][arm]['exposure'], 'paired exposure summary differs')
            training[arm] = dict(final_loss=manifest['final_loss'], mean_loss_per_epoch=manifest['mean_loss_per_epoch'], tokens=manifest['tokens'], train_tokens_seen=manifest['train_tokens_seen'], exposure=written['tokens'][arm]['exposure'], steps=manifest['steps'])
        return dict(write_plan_sha256=plan['write_plan_sha256'], result_sha256=base_readout.digest(result_path), fits=fits, material=custody, training_metadata=training, model_origin=base_readout.ORIGIN, conditioning=base_readout.CONDITIONING)

    def verify_worker_bytes(self, spec, diagnostic):
        base_readout.require(all((base_readout.digest(path) == expected for path, expected in spec['source_pins'].items())) and base_readout.digest(self.SELF) == spec['self_sha256'], 'worker source changed')
        base_readout.require(diagnostic.model_hashes(spec['model']) == spec['model_files'], 'worker base changed')
        if spec['adapter']:
            base_readout.require(diagnostic.tree_hashes(spec['adapter']) == spec['adapter_files'], 'worker adapter changed')

    def worker(self, spec, spec_sha256, allow_gpu=False):
        base_readout.require(allow_gpu, '--allow-gpu required before worker work')
        spec_path = Path(spec).resolve(strict=True)
        base_readout.require(base_readout.digest(spec_path) == spec_sha256, 'worker spec changed')
        spec = base_readout.read(spec_path)
        base_readout.require(set(spec) == base_readout.SPEC_KEYS and spec['cell'] in base_readout.CELLS, 'worker spec extra context/invalid fields')
        base_readout.require(spec['adapter'] is None and spec['adapter_files'] == {} if spec['cell'] == 'OFF' else bool(spec['adapter'] and spec['adapter_files']), 'OFF/ON adapter mismatch')
        diagnostic = base_readout.diagnostic_module(spec['source_root'])
        base_readout.require(spec['protocol'] == self.protocol(diagnostic), 'worker protocol changed')
        base_readout.require(base_readout.absolute_python(sys.executable) == spec['python'] and os.environ.get('CUDA_VISIBLE_DEVICES') == spec['device'], 'worker interpreter/device mismatch')
        base_readout.require(time.time() < spec['hard_end'] - base_readout.CLEANUP_SECONDS, 'worker window exhausted')
        stage = spec_path.parent / spec['cell']
        data = stage / 'data'
        base_readout.require(spec_path.name == spec['cell'] + '.spec.json' and str(data) == spec['data'] and (not data.exists()), 'fixed fresh worker output required')
        with self.owning_process(stage, spec['hard_end']):
            self.verify_worker_bytes(spec, diagnostic)
            data.mkdir()
            base_readout.write_json(data / 'isolation.json', dict(pid=os.getpid(), pgid=os.getpgrp(), parent_pid=os.getppid(), spec_sha256=spec_sha256, parent_calls=0, task_prefix='', record_training=False, scope='fresh process and exact replayed prompts; not OS-level filesystem isolation'))
            backend = None
            try:
                backend = diagnostic.NativeBackend(spec['model'], spec['adapter'])
                identity = diagnostic.expected_identity(spec, spec['adapter'])
                base_readout.require(backend.identity() == identity, 'native backend identity differs')
                base_readout.write_json(data / 'identity.json', dict(stage='evaluation', cell=spec['cell'], backend=identity, model_files=spec['model_files'], protocol='interaction_v3'))
                base_readout.write_json(data / 'backend.ready.json', dict(pid=os.getpid(), ready=time.monotonic()))
                calls = diagnostic.Calls(data / 'calls', backend, 'evaluation', identity, 'interaction_v3')
                events = diagnostic.Events(data / 'events.jsonl')
                result = diagnostic.run_evaluation(calls, events, spec['cell'])
                base_readout.write_json(data / 'result.json', result)
                base_readout.write_json(data / 'usage.json', diagnostic.usage(data))
                diagnostic.audit_native_calls(backend.backend.tok, data)
                base_readout.write_json(data / 'native_audit.json', dict(ok=True, calls=calls.count, scope='actual rendered prompts/input IDs/decoded output IDs'))
            except BaseException as error:
                base_readout.write_json(data / 'failure.json', dict(error=type(error).__name__ + ': ' + str(error)))
                raise
            finally:
                closed, failure = (False, None)
                try:
                    closed = self.close_native(backend)
                except Exception as error:
                    failure = str(error)
                base_readout.write_json(data / 'backend.cleanup.json', dict(closed=closed, error=failure))
                base_readout.require(closed is True, 'backend cleanup unverified')
            self.verify_worker_bytes(spec, diagnostic)
            base_readout.require(base_readout.digest(spec_path) == spec_sha256, 'worker spec changed during evaluation')
            diagnostic.capture_manifest(data)
            return dict(status='CAPTURED', cell=spec['cell'])

    def audit_cell(self, root, plan, lineage, cell, diagnostic):
        data = root / 'run' / cell / 'data'
        adapter = lineage['fits'][cell[0]]['adapter'] if cell != 'OFF' else None
        header = base_readout.read(data / 'identity.json')
        base_readout.require(header['stage'] == 'evaluation' and header['cell'] == cell and (header['model_files'] == plan['model_files']), 'wrong cell/stage/base capture')
        audit = diagnostic.check_capture(data, diagnostic.expected_identity(plan, adapter), 'interaction_v3')
        base_readout.require(audit['ok'], 'readout replay failed: ' + str(audit['failures']))
        base_readout.require(base_readout.read(data / 'native_audit.json')['ok'] and base_readout.read(data / 'backend.cleanup.json')['closed'], 'native audit/cleanup missing')
        base_readout.require(not (data / 'failure.json').exists(), 'failed capture')
        diagnostic.audit_native_calls(diagnostic.native_tokenizer(plan['model']), data)
        audit['process_metrics'] = self.process_metrics(data, audit, diagnostic)
        return audit

    def evaluate(self, root, plan_sha256, allow_gpu=False):
        base_readout.require(allow_gpu, '--allow-gpu required before controller work')
        started_wall, started = (time.time(), time.monotonic())
        with self.work_window(started_wall + base_readout.CONTROLLER_SECONDS):
            root, plan, diagnostic = self.checked_plan(root, plan_sha256)
        hard_end = min(started_wall + base_readout.CONTROLLER_SECONDS, plan['deadline'], plan['lease_cutoff'])
        run = root / 'run'
        run.mkdir()
        completed = {}
        try:
            with self.work_window(hard_end):
                lineage = self.accepted_writes(plan, native=True)
                base_readout.require(lineage == plan['lineage'], 'prepared process pair changed before readout')
                base_readout.write_json(run / 'lineage.json', lineage)
                base_readout.write_json(run / 'controller.json', dict(plan_sha256=plan_sha256, started_wall=started_wall, hard_end=hard_end, cleanup_reserve=base_readout.CLEANUP_SECONDS, pid=os.getpid()))
                for cell in base_readout.CELLS:
                    self.checked_plan(root, plan_sha256)
                    base_readout.require(self.accepted_writes(plan) == lineage, 'paired write lineage changed')
                    base_readout.require(time.time() < hard_end - base_readout.CLEANUP_SECONDS, 'insufficient next-cell work window')
                    spec_path = run / (cell + '.spec.json')
                    base_readout.write_json(spec_path, self.worker_spec(root, plan, lineage, cell, hard_end))
                    spec_hash = base_readout.digest(spec_path)
                    command = [plan['python'], '-B', str(self.SELF), '_readout-worker', '--spec', str(spec_path), '--spec-sha256', spec_hash, '--allow-gpu']
                    with self.supervised_window(hard_end):
                        supervision = diagnostic.supervise(root, dict(model=plan['model'], device=plan['device'], lease_end=hard_end), run / cell, command, run / cell / 'data' / 'calls')
                    base_readout.require(supervision['ok'] and supervision['reservation_release_verified'], 'readout cleanup unverified')
                    base_readout.require(time.time() < hard_end - base_readout.CLEANUP_SECONDS, 'controller work window exhausted after cleanup')
                    base_readout.require(base_readout.digest(spec_path) == spec_hash, 'supervised worker spec changed')
                    audit = self.audit_cell(root, plan, lineage, cell, diagnostic)
                    base_readout.write_json(run / cell / 'provenance.json', audit)
                    completed[cell] = dict(result=audit['result'], capture_sha256=base_readout.digest(run / cell / 'data' / 'manifest.json'), spec_sha256=spec_hash, supervision_sha256=base_readout.digest(run / cell / 'supervision.json'), process_metrics=audit['process_metrics'])
                self.checked_plan(root, plan_sha256)
                base_readout.require(self.accepted_writes(plan) == lineage, 'paired write lineage changed during readout')
                for cell, receipt in completed.items():
                    base_readout.require(base_readout.digest(run / cell / 'data' / 'manifest.json') == receipt['capture_sha256'] and base_readout.digest(run / (cell + '.spec.json')) == receipt['spec_sha256'] and (base_readout.digest(run / cell / 'supervision.json') == receipt['supervision_sha256']), 'earlier cell changed')
                    base_readout.require(self.audit_cell(root, plan, lineage, cell, diagnostic)['process_metrics'] == receipt['process_metrics'], 'earlier process metrics changed')
            base_readout.require(time.monotonic() - started <= base_readout.CONTROLLER_SECONDS and time.time() <= hard_end, 'inclusive controller cap exceeded')
            means = {cell: receipt['result']['mean_quiz_accuracy'] for cell, receipt in completed.items()}
            result = dict(status='COMPLETE_EXPLORATORY_READOUT', cells=completed, P_minus_OFF=means['P_ON'] - means['OFF'], A_minus_OFF=means['A_ON'] - means['OFF'], P_minus_A=means['P_ON'] - means['A_ON'], inference=plan['protocol']['inference'], claim_boundary=diagnostic.CLAIM_BOUNDARY, version=self.VERSION, training_objective=plan['protocol']['training_objective'], conditioning=base_readout.CONDITIONING, model_origin=base_readout.ORIGIN, claims=base_readout.CLAIMS, training_metadata=lineage['training_metadata'], protocol=plan['protocol'], controller_seconds=time.monotonic() - started, adaptation_test=False, semantic_nonleakage_certified=False, model_authentication_certified=False, fit_seed=self.fit_seed, automatic_promotion=False)
            base_readout.write_json(run / 'result.json', result)
            return result
        except BaseException as error:
            base_readout.write_json(run / 'failure.json', dict(error=type(error).__name__ + ': ' + str(error), completed_cells=list(completed), retry=False, aggregate=None, controller_seconds=time.monotonic() - started))
            raise

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare-write')
    for name in ('reference-write-root', 'reference-write-plan-sha256', 'out', 'device', 'deadline', 'lease-end'):
        prepare.add_argument('--'+name, required=True)
    prepare.add_argument('--fit-seed', type=int, choices=FIT_SEEDS, required=True)
    readout = commands.add_parser('prepare-readout')
    for name in ('write-root', 'write-plan-sha256', 'write-driver-sha256', 'out', 'deadline', 'lease-end'):
        readout.add_argument('--'+name, required=True)
    readout.add_argument('--fit-seed', type=int, choices=FIT_SEEDS, required=True)
    for name in ('write', 'evaluate'):
        stage = commands.add_parser(name)
        stage.add_argument('--root', required=True)
        stage.add_argument('--plan-sha256', required=True)
        stage.add_argument('--fit-seed', type=int, choices=FIT_SEEDS, required=True)
        stage.add_argument('--allow-gpu', action='store_true')
    worker = commands.add_parser('_write-worker')
    for name in ('root', 'plan-sha256', 'arm', 'launch-token'):
        worker.add_argument('--'+name, required=True)
    worker.add_argument('--allow-gpu', action='store_true')
    worker = commands.add_parser('_readout-worker')
    worker.add_argument('--spec', required=True)
    worker.add_argument('--spec-sha256', required=True)
    worker.add_argument('--allow-gpu', action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'prepare-write':
        result = WritePhase(args.fit_seed).prepare(args.reference_write_root, args.reference_write_plan_sha256,
                    args.out, args.device, args.deadline, args.lease_end)
    elif args.command == 'prepare-readout':
        result = ReadoutPhase(args.fit_seed).prepare(args.write_root, args.write_plan_sha256, SELF,
                    args.write_driver_sha256, args.out, args.deadline, args.lease_end)
    elif args.command == 'write':
        result = WritePhase(args.fit_seed).write_pair(args.root, args.plan_sha256, args.allow_gpu)
    elif args.command == 'evaluate':
        result = ReadoutPhase(args.fit_seed).evaluate(args.root, args.plan_sha256, args.allow_gpu)
    elif args.command == '_write-worker':
        require(base_write.digest(Path(args.root)/'plan.json') == args.plan_sha256, 'worker plan changed')
        seed = base_readout.read(Path(args.root)/'plan.json')['fit_seed']
        result = WritePhase(seed).worker(args.root, args.arm, args.plan_sha256, args.launch_token, args.allow_gpu)
    else:
        require(base_write.digest(args.spec) == args.spec_sha256, 'worker spec changed')
        seed = base_readout.read(args.spec)['protocol']['replication_fit_seed']
        result = ReadoutPhase(seed).worker(args.spec, args.spec_sha256, args.allow_gpu)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
