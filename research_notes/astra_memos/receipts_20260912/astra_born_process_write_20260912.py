"""Bound born AUTH -> two own-wake warm-start requests; no native runner.

Main owns supervision, loading, fits, collection and release. The only CLI
operation verifies birth custody on CPU in its original source interpreter.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
from types import ModuleType, SimpleNamespace


sys.dont_write_bytecode = True
SELF = Path(__file__).resolve()
BIRTH = Path('/tmp/astra_birth_conditional_run_20260913.py')
BIRTH_SHA = '072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa'
WRITER = Path('/tmp/astra_rulegame_process_write_20260912.py')
WRITER_SHA = 'a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9'
SCHEMA = 'born_process_write_bindings_v1_20260912'
ARMS = ('P', 'A')
BOUNDARY = dict(origin='SOURCE_AUTHORED_BIRTH_NOT_CLEAN', model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
    H1=False, H2=False, generalG3=False, P1=False, freeze=False, clean_lineage=False,
    target_tokens_matched=False, input_tokens_matched=False, readout=False, automatic_chaining=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_helper(path, pin, name):
    require(digest(path) == pin, 'frozen helper changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(digest(path) == pin, 'helper changed during import')
    return module


def apis(source_root):
    old = load_helper(WRITER, WRITER_SHA, 'born_process_low_level')
    diagnostic, exporter, trainer = old.modules(source_root)
    born = importlib.import_module('organism_v6.born_rulegame_formation')
    require(Path(born.__file__).resolve().parent.parent == Path(source_root).resolve(), 'born snapshot mismatch')
    return old, diagnostic, exporter, trainer, born


def verify_birth(custody):
    """CPU only; call in an isolated interpreter (birth source may be older)."""
    require(set(custody) == {'fit_root', 'fit_plan_sha256', 'fit_release', 'fit_release_sha256'}, 'birth custody fields mismatch')
    driver = load_helper(BIRTH, BIRTH_SHA, 'born_process_frozen_birth')
    root, plan, api = driver.verify_plan(custody['fit_root'], custody['fit_plan_sha256'])
    require(plan['phase'] == 'fit', 'birth fit, not readout, required')
    release = driver.accepted_release(custody['fit_release'], custody['fit_release_sha256'], plan, custody['fit_plan_sha256'])
    require(release['phase_complete'] is True and release['full_release'] is True, 'birth incomplete or unreleased')
    require(driver.audit_terminal(root, plan, api, custody['fit_plan_sha256'])['phase_complete'] is True, 'birth terminal incomplete')
    fit = driver.verify_fit(root, plan, api, 'AUTH')
    require(driver.read(root / 'run/AUTH/receipt.json') == driver.verify_member(root, plan, api, 'AUTH'), 'birth AUTH receipt mismatch')
    backend = importlib.import_module('organism_v6.model_backend')
    identity = backend.configured_generation_identity(plan['model'], fit['adapter'])
    pin = dict(schema='completed_birth_adapter_pin_v1', status='COMPLETE', birth_arm='AUTH',
        birth_plan_sha256=custody['fit_plan_sha256'], completion_receipt_sha256=driver.digest(root / 'run/result.json'),
        child_identity=identity, model_files=plan['model_files'], origin=BOUNDARY['origin'], model_origin=BOUNDARY['model_origin'])
    return dict(birth_pin=pin, custody=copy.deepcopy(custody), parent_files=fit['adapter_files'], parent_steps=fit['steps'],
        terminal_sha256=driver.digest(root / 'run/result.json'), auth_receipt_sha256=driver.digest(root / 'run/AUTH/receipt.json'), birth_driver_sha256=BIRTH_SHA,
        full_release=True, phase_complete=True)


def checked_birth(custody):
    """No GPU/native imports; separation prevents old/new organism module mixing."""
    command = [sys.executable, '-B', str(SELF), 'custody', '--json', json.dumps(custody, allow_nan=False)]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES=''))
    return json.loads(result.stdout)


def source_pins(source_root):
    old, diagnostic, exporter, trainer, born = apis(source_root)
    pins = old.implementation(source_root, diagnostic)
    pins.update({str(SELF): digest(SELF), str(BIRTH): BIRTH_SHA,
        str(Path(born.__file__).resolve()): digest(born.__file__)})
    return pins


def projection_documents(capture, diagnostic):
    binding = capture['binding']
    documents = {'identity.json': dict(stage='formation', protocol='interaction_v3',
        schema=binding['schema'], backend=binding['role_identities']['wake'], model_files=binding['birth']['model_files'],
        role_identities=binding['role_identities'], binding_sha256=capture['binding_sha256'])}
    for row in capture['calls']:
        prefix = 'calls/' + row['request']['call_id']
        documents[prefix + '.request.json'] = {key: row[key] for key in
            ('request', 'identity', 'identity_sha256', 'prompt_sha256', 'started')}
        response = row['envelope']['response']
        documents[prefix + '.response.json'] = dict(response=response, ended=row['ended'],
            response_sha256=diagnostic.value_hash(response), envelope=row['envelope'], envelope_sha256=row['envelope_sha256'])
    return documents


def project_capture(source_root, capture_file, capture_sha256, binding_sha256, out):
    """Lossless format projection, not a legacy/OFF capture. No tokenizer needed."""
    old, diagnostic, exporter, trainer, born = apis(source_root)
    source, output = old.local_path(capture_file), old.local_path(out, fresh=True)
    require(digest(source) == capture_sha256, 'original born capture pin mismatch')
    capture = diagnostic.read(source)
    born.replay_formation(capture, capture['binding'], expected_binding_sha256=binding_sha256, cutoff=capture['cutoff'])
    require(capture['binding']['birth']['birth_arm'] == 'AUTH', 'AUTH capture only')
    for protected in (source, Path(capture['binding']['birth']['child_identity']['adapter_input']),
                      Path(capture['binding']['birth']['child_identity']['model_input'])):
        require(not old.overlaps(output, protected), 'projection overlaps protected input')
    require(not (output.parents[1] / 'plan.json').exists(), 'projection would inherit an unrelated legacy plan')
    output.mkdir()
    (output / 'calls').mkdir()
    with (output / 'native_capture.json').open('xb') as target:
        target.write(source.read_bytes())
    require(digest(output / 'native_capture.json') == capture_sha256 == digest(source), 'capture changed during projection')
    for name, value in projection_documents(capture, diagnostic).items():
        old.write_json(output / name, value)
    old.write_json(output / 'manifest.json', dict(files=diagnostic.tree_hashes(output)))
    bound_exporter(source_root, output, capture_sha256, binding_sha256)
    return dict(capture_root=str(output), capture_sha256=capture_sha256, binding_sha256=binding_sha256)


def bound_exporter(source_root, capture_root, capture_sha256, binding_sha256):
    """Unchanged exporter code; isolated diagnostic facade replaces ONLY replay.

    Legacy single-identity replay is never relaxed globally or fed a fake OFF
    identity. Born replay verifies original envelopes and every role/world join.
    """
    old, diagnostic, exporter, trainer, born = apis(source_root)
    root = old.local_path(capture_root)

    def replay(path, identity=None, protocol=None):
        require(Path(path).resolve() == root and identity is None and protocol == 'interaction_v3', 'wrong born replay scope')
        require(digest(root / 'native_capture.json') == capture_sha256, 'native capture changed')
        capture = diagnostic.read(root / 'native_capture.json')
        checked = born.replay_formation(capture, capture['binding'], expected_binding_sha256=binding_sha256, cutoff=capture['cutoff'])
        require(capture['binding']['birth']['birth_arm'] == 'AUTH', 'AUTH capture only')
        documents = projection_documents(capture, diagnostic)
        inventory = diagnostic.tree_hashes(root, ('manifest.json',))
        require(set(inventory) == set(documents) | {'native_capture.json'}, 'extra/missing projected evidence')
        require(diagnostic.read(root / 'manifest.json') == dict(files=inventory), 'projection manifest mismatch')
        require(all(diagnostic.read(root / name) == value for name, value in documents.items()), 'projection differs from original born envelope')
        return dict(ok=True, failures=[], result=checked['result'], events=checked['events'])

    replay(root, protocol='interaction_v3')
    adapted = ModuleType('organism_v6._born_bound_process_exporter')
    adapted.__file__, adapted.__package__ = exporter.__file__, 'organism_v6'
    exec(compile(Path(exporter.__file__).read_bytes(), exporter.__file__, 'exec'), adapted.__dict__)
    adapted.diagnostic = SimpleNamespace(**dict(vars(diagnostic), check_capture=replay))
    return adapted


def prepare(source_root, projection, custody, review, fixed_candidate, tokenizer, out):
    """Main supplies its native tokenizer and existing four-row review. No loads."""
    old, diagnostic, exporter, trainer, born = apis(source_root)
    output = old.local_path(out, fresh=True)
    proof = checked_birth(custody)
    root = old.local_path(projection['capture_root'])
    capture = diagnostic.read(root / 'native_capture.json')
    require(proof['birth_pin'] == capture['binding']['birth'], 'birth custody/formation binding mismatch')
    for protected in (root, Path(proof['birth_pin']['child_identity']['model_input']),
                      Path(proof['birth_pin']['child_identity']['adapter_input']), Path(custody['fit_root']), Path(custody['fit_release']).parent):
        require(not old.overlaps(output, protected), 'write output overlaps immutable input')
    bound = bound_exporter(source_root, root, projection['capture_sha256'], projection['binding_sha256'])
    pins = source_pins(source_root)
    pair = bound.build_process_pair(root, review, tokenizer, fixed_candidate=fixed_candidate, max_len=4096, protocol=old.PROTOCOL)
    tokens = {arm: old.full_tokens(pair['corpora'][arm], tokenizer, trainer) for arm in ARMS}
    config = old.fit_config(trainer, proof['birth_pin']['child_identity']['model_input'])
    config.note = SCHEMA + '_SOURCE_AUTHORED_BIRTH_NOT_CLEAN_NO_CLAIMS'
    parent = proof['birth_pin']['child_identity']['adapter_input']
    for arm in ARMS:
        warm = trainer._warm_parent(parent, str(output / 'fits' / arm / 'adapter'), config)
        require(warm['parent_files'] == proof['parent_files'], 'complete birth adapter inventory mismatch')
    output.mkdir()
    bound.export_pair(root, output / 'material', review, tokenizer, fixed_candidate=fixed_candidate, max_len=4096, protocol=old.PROTOCOL)
    require(all(diagnostic.read(output / 'material/corpora' / (arm + '.json')) == pair['corpora'][arm] for arm in ARMS), 'export differs from audited pair')
    plan = dict(schema=SCHEMA, status='PREPARED_BINDINGS_NOT_LAUNCHED', root=str(output), source_root=str(Path(source_root).resolve()),
        boundary=BOUNDARY, birth=proof, projection=copy.deepcopy(projection), config=asdict(config), init_adapter=parent,
        arms=list(ARMS), tokens=tokens, material_files=diagnostic.tree_hashes(output / 'material'),
        projection_files=diagnostic.tree_hashes(root), sources=pins, recipe=trainer.RECIPE,
        supervision='MAIN_EXISTING_SUPERVISOR_REQUIRED', release='MAIN_COLLECTION_REQUIRED_NOT_RELEASED')
    require(source_pins(source_root) == pins and checked_birth(custody) == proof, 'inputs changed during preparation')
    old.write_json(output / 'plan.json', plan)
    return dict(root=str(output), plan_sha256=digest(output / 'plan.json'))


def checked_plan(root, plan_sha256):
    require(digest(Path(root) / 'plan.json') == plan_sha256, 'writer plan pin mismatch')
    plan = json.loads((Path(root) / 'plan.json').read_text())
    old, diagnostic, exporter, trainer, born = apis(plan['source_root'])
    root = old.local_path(root)
    require(plan['root'] == str(root) and plan['schema'] == SCHEMA and plan['boundary'] == BOUNDARY
        and plan['arms'] == list(ARMS), 'writer scope mismatch')
    require(source_pins(plan['source_root']) == plan['sources'], 'writer dependencies changed')
    require(checked_birth(plan['birth']['custody']) == plan['birth'], 'birth custody changed')
    require(diagnostic.tree_hashes(root / 'material') == plan['material_files'], 'material changed')
    projection = plan['projection']
    require(diagnostic.tree_hashes(projection['capture_root']) == plan['projection_files'], 'born source changed')
    bound_exporter(plan['source_root'], **projection)
    capture = diagnostic.read(Path(projection['capture_root']) / 'native_capture.json')
    require(capture['binding']['birth'] == plan['birth']['birth_pin'], 'formation/birth mismatch')
    config = old.fit_config(trainer, plan['birth']['birth_pin']['child_identity']['model_input'])
    config.note = SCHEMA + '_SOURCE_AUTHORED_BIRTH_NOT_CLEAN_NO_CLAIMS'
    require(plan['config'] == asdict(config) and plan['init_adapter'] == plan['birth']['birth_pin']['child_identity']['adapter_input'],
        'fixed recipe or immutable AUTH parent changed')
    return root, plan, old, diagnostic, trainer


def worker_binding(root, plan_sha256, arm, tokenizer):
    """Arguments for ONE Main-supervised run_training; never calls it or loads a base."""
    root, plan, old, diagnostic, trainer = checked_plan(root, plan_sha256)
    require(arm in ARMS, 'only P/A writes')
    corpus_path = root / 'material/corpora' / (arm + '.json')
    corpus = diagnostic.read(corpus_path)
    tokens = old.full_tokens(corpus, tokenizer, trainer)
    require(tokens == plan['tokens'][arm], 'actual native tokenizer or masks differ')
    bound = bound_exporter(plan['source_root'], **plan['projection'])
    pair = bound.build_process_pair(plan['projection']['capture_root'], diagnostic.read(root / 'material/audit/main_review.json'),
        tokenizer, fixed_candidate=diagnostic.read(root / 'material/audit/candidate.json'), max_len=4096, protocol=old.PROTOCOL)
    require(pair['corpora'][arm] == corpus, 'worker source/exporter join mismatch')
    config = trainer.TrainConfig(**plan['config'])
    out = root / 'fits' / arm / 'adapter'
    warm = trainer._warm_parent(plan['init_adapter'], str(out), config)
    require(warm['parent_files'] == plan['birth']['parent_files'], 'parent inventory changed')
    return dict(items=trainer.normalize_items(corpus), cfg=config, out_dir=str(out),
        corpus_sha=digest(corpus_path), corpus_name=arm + '.json', init_adapter=plan['init_adapter'])


def forward_observer(root, plan_sha256, arm):
    """Main attaches this pre-hook to its fresh base with with_kwargs=True."""
    root, plan, old, diagnostic, trainer = checked_plan(root, plan_sha256)
    require(arm in ARMS, 'only P/A forward traces')
    destination = root / 'fits' / arm / 'forwards'
    old.local_path(destination, fresh=True)
    destination.mkdir()
    count = 0

    def observe(model, args, kwargs):
        nonlocal count
        require(not args and all(kwargs.get(key) is None for key in ('inputs_embeds', 'position_ids', 'past_key_values')),
            'unexpected positional/embedded/cached forward inputs')
        batch = {key: kwargs[key].detach().cpu().tolist() for key in ('input_ids', 'labels', 'attention_mask')}
        receipt = old.forward_receipt(batch, plan['tokens'][arm], count)
        old.write_json(destination / f'{count + 1:04d}.json', receipt)
        count += 1

    return observe


def initial_state_receipt(parent, warm, shapes, old):
    """Check source bytes and recorded initialized bytes, including dtype casts."""
    weights = Path(parent) / 'adapter_model.safetensors'
    tensors = old.saved_weights(weights, shapes)
    formats = {'F32': ('torch.float32', 4), 'F16': ('torch.float16', 2), 'BF16': ('torch.bfloat16', 2)}
    require(set(warm['dtype_conversions']) <= set(warm['source_state']), 'unknown dtype conversion tensor')
    with weights.open('rb') as stream:
        header_size = struct.unpack('<Q', stream.read(8))[0]
        for name, source in warm['source_state'].items():
            metadata = tensors[name[name.index('layers.'):]]
            source_dtype, width = formats[metadata['dtype']]
            initialized = warm['initialized_state'][name]
            target_dtype = initialized['dtype']
            require(source['dtype'] == source_dtype and target_dtype in {item[0] for item in formats.values()}, 'state dtype mismatch')
            start, end = metadata['data_offsets']
            stream.seek(8 + header_size + start)
            source_hash, initial_hash = hashlib.sha256(), hashlib.sha256()
            remaining = end - start
            while remaining:
                block = stream.read(min(1024 * 1024, remaining))
                require(block and len(block) % width == 0, 'short parent tensor')
                source_hash.update(block)
                if source_dtype == target_dtype:
                    initial_hash.update(block)
                else:
                    converted = bytearray()
                    for offset in range(0, len(block), width):
                        scalar = block[offset:offset + width]
                        value = struct.unpack('<f', b'\0\0' + scalar)[0] if source_dtype == 'torch.bfloat16' else struct.unpack('<f' if width == 4 else '<e', scalar)[0]
                        require(math.isfinite(value), 'nonfinite source tensor')
                        if target_dtype == 'torch.bfloat16':
                            bits = int.from_bytes(struct.pack('<f', value), 'little')
                            converted.extend(((bits + 0x7fff + ((bits >> 16) & 1)) >> 16).to_bytes(2, 'little'))
                        else:
                            converted.extend(struct.pack('<f' if target_dtype == 'torch.float32' else '<e', value))
                    initial_hash.update(converted)
                remaining -= len(block)
            require(source['sha256'] == source_hash.hexdigest() and initialized['sha256'] == initial_hash.hexdigest(), 'parent-to-initialized tensor bytes mismatch')


def validate_fit(root, plan_sha256, arm):
    """CPU receipts only; completion is NOT a release or scientific verdict."""
    root, plan, old, diagnostic, trainer = checked_plan(root, plan_sha256)
    require(arm in ARMS, 'only P/A receipts')
    adapter = old.local_path(root / 'fits' / arm / 'adapter')
    files = trainer._warm_inventory(adapter)
    required = {'DONE', 'adapter_config.json', 'adapter_model.safetensors', 'train_manifest.json', 'train_meta.json'}
    require(required <= set(files) <= required | {'README.md'}, 'incomplete/unexpected adapter receipt files')
    manifest = diagnostic.read(adapter / 'train_manifest.json')
    require(manifest['recipe'] == plan['recipe'] and manifest['config'] == plan['config']
        and manifest['base_model'] == plan['config']['model'] and manifest['empty'] is False, 'fit recipe/base mismatch')
    require(manifest['steps'] == manifest['micro_batches'] == manifest['epochs_run'] == 12
        and manifest['nonfinite_batches'] == 0 and math.isfinite(manifest['final_loss'])
        and len(manifest['mean_loss_per_epoch']) == 12 and all(math.isfinite(value) for value in manifest['mean_loss_per_epoch']), 'fit incomplete/nonfinite/dose mismatch')
    require(manifest['corpus'] == dict(file=arm + '.json', sha256=plan['material_files']['corpora/' + arm + '.json'],
        n_items=2, n_encoded=2, n_skipped_no_target=0), 'fit corpus mismatch')
    tokens = plan['tokens'][arm]
    require(manifest['tokens'] == tokens['tokens'] and manifest['train_tokens_seen'] == tokens['train_tokens_seen'], 'fit token count mismatch')
    forwards = root / 'fits' / arm / 'forwards'
    require(set(diagnostic.tree_hashes(forwards)) == {f'{index + 1:04d}.json' for index in range(12)}, 'missing/extra observed forward receipts')
    for index in range(12):
        observed = diagnostic.read(forwards / f'{index + 1:04d}.json')
        batch = old.expected_forward_batch(tokens, observed['row_order'])
        require(observed == old.forward_receipt(batch, tokens, index), 'observed forward masks/exposure mismatch')
    require(manifest['truncation'] == dict(overflow='split', items_truncated=0, context_tokens_dropped=0,
        target_tokens_dropped=0, items_split=0, segments_from_splits=0, max_segment_tokens=tokens['max_segment_tokens'])
        and manifest['packing']['mode'] == 'one_item_per_sequence' and manifest['packing']['n_sequences'] == 2
        and manifest['packing']['n_groups'] == 2 and manifest['packing']['isolation_check']['ran'] is False,
        'truncation/splitting/packing forbidden')
    warm = manifest['warm_start']
    require(warm['mode'] == 'WEIGHT_WARM_START_FRESH_OPTIMIZER' and warm['optimizer_initialization'] == 'fresh_per_write'
        and warm['optimizer_state_restored'] is False and warm['optimizer_state_saved'] is False
        and warm['initialized_loaded_state_check'] is True and warm['base_frozen'] is True and warm['adapter_count'] == 1
        and warm['phase_seed'] == 2 and warm['phase_steps'] == 12 and warm['parent_unchanged'] is True
        and warm['parent_path'] == plan['init_adapter'] and warm['parent_files'] == warm['parent_files_after'] == plan['birth']['parent_files']
        and warm['parent_cumulative_steps'] == plan['birth']['parent_steps']
        and warm['cumulative_steps'] == plan['birth']['parent_steps'] + 12
        and warm['trainer_sha256'] == digest(trainer.__file__), 'warm-start continuity/fresh optimizer mismatch')
    require(trainer._warm_inventory(plan['init_adapter']) == plan['birth']['parent_files'], 'immutable birth changed')
    parent_manifest = diagnostic.read(Path(plan['init_adapter']) / 'train_manifest.json')
    layers = parent_manifest['lora']['n_layers']
    expected = {f'layers.{layer}.{group}.{projection}.lora_{part}.weight'
        for layer in range(layers) for group, projections in
        (('self_attn', ('q_proj', 'k_proj', 'v_proj', 'o_proj')), ('mlp', ('gate_proj', 'up_proj', 'down_proj')))
        for projection in projections for part in ('A', 'B')}
    initialized, source = warm['initialized_state'], warm['source_state']
    require(set(initialized) == set(source) and len(initialized) == 14 * layers and layers > 0, 'incomplete initialized/source tensor coverage')
    normalized = {}
    for name, state in initialized.items():
        require('layers.' in name, 'unexpected initialized tensor')
        key = name[name.index('layers.'):]
        require(key in expected and key not in normalized and state['shape'] == source[name]['shape']
            and len(state['shape']) == 2 and state['shape'][0 if '.lora_A.' in key else 1] == 8, 'initialized tensor shape/coverage mismatch')
        require(state == source[name] if name not in warm['dtype_conversions'] else
            warm['dtype_conversions'][name] == dict(source=source[name]['dtype'], initialized=state['dtype']), 'source-to-initial state continuity mismatch')
        normalized[key] = state
    require(set(normalized) == set(expected), 'missing initialized projection')
    require(len(warm['trainable_names']) == len(set(warm['trainable_names'])) == len(expected)
        and {name[name.index('layers.'):].replace('.default.', '.') for name in warm['trainable_names']} == set(expected), 'trainable tensor coverage mismatch')
    require(manifest['lora'] == dict(rank=8, alpha=16, dropout=.05, scaling=2.0, target_modules=list(trainer.ALL_PROJ),
        layers='all', n_layers=layers, freeze_a=False, trainable_params=sum(math.prod(row['shape']) for row in normalized.values())), 'LoRA receipt coverage mismatch')
    initial_state_receipt(plan['init_adapter'], warm, normalized, old)
    saved = diagnostic.read(adapter / 'adapter_config.json')
    require(saved['r'] == 8 and saved['lora_alpha'] == 16 and saved['lora_dropout'] == .05 and saved['bias'] == 'none'
        and saved['peft_type'] == 'LORA' and set(saved['target_modules']) == set(trainer.ALL_PROJ)
        and saved['base_model_name_or_path'] == plan['config']['model'] and not any(saved.get(key) for key in
        ('modules_to_save', 'rank_pattern', 'alpha_pattern', 'layers_to_transform', 'use_dora', 'use_rslora', 'fan_in_fan_out')), 'saved adapter configuration mismatch')
    old.saved_weights(adapter / 'adapter_model.safetensors', normalized)
    common = load_helper(BIRTH, BIRTH_SHA, 'born_process_finite_checker').common
    common.finite_weights(adapter / 'adapter_model.safetensors', files['adapter_model.safetensors'])
    require(diagnostic.read(adapter / 'train_meta.json') == dict(recipe=trainer.RECIPE, n_texts=2, steps=12,
        tokens=manifest['train_tokens_seen'], rank=8, epochs=12, lr=1e-4, seed=2, final_loss=manifest['final_loss']), 'train metadata mismatch')
    require(trainer._warm_inventory(adapter) == files, 'fit changed during audit')
    return dict(arm=arm, adapter=str(adapter), adapter_files=files, parent_path=plan['init_adapter'],
        parent_files=plan['birth']['parent_files'], plan_sha256=plan_sha256, steps=12, tokens=tokens['tokens'],
        status='COMPLETE_ADAPTER_NOT_RELEASED', boundary=BOUNDARY)


def pair_receipt(root, plan_sha256):
    """Main must bind this complete pair to its existing collector's full release."""
    fits = {arm: validate_fit(root, plan_sha256, arm) for arm in ARMS}
    require(fits['P']['adapter'] != fits['A']['adapter'] and fits['P']['parent_files'] == fits['A']['parent_files'], 'independent sibling writes required')
    return dict(schema=SCHEMA, plan_sha256=plan_sha256, fits=fits, boundary=BOUNDARY,
        status='PAIR_COMPLETE_NOT_RELEASED', release_required=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['custody'])
    parser.add_argument('--json', required=True, help='exact four-field birth custody object')
    args = parser.parse_args(argv)
    print(json.dumps(verify_birth(json.loads(args.json)), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
