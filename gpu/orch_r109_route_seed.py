"""CPU seed binding and explicit inherited-state restoration; never a launcher.

prepare(checkpoint) -> document; validate(document) -> document.
restore(loaded, document) -> provenance, after caller-owned native.load_stage.
save_carry(loaded, document, adapter, output_dir) -> next document.
rehearsal_rows(document) returns the fixed16 original corpus entries;
encoded(row, tokenizer) returns the original native EncodedRow, without padding.
Only sleep's training binding may restore; collection/readouts stay read-only.
"""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import orch_combined_l1_continual_run as continual
from gpu import orch_guided_native as native
from organism_v6 import orch_combined_l1_continual as storage


CHECKPOINT = continual.ROOT/'FULL/checkpoints/000008932'
COMMIT_SHA = 'e4122dd6f760431fabfd106a7fdd1f6c06b52fe3a16012f0ba865eb2df88bb51'
STATE_SHA = '121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
SOURCE_SHA = '4859efad8a0a26ed8de120ed42fa9ac7c74d5d75786447ac9c6a255cc2c86a55'
CORPUS_SHA = 'ee2aa551ae71d271bc6cbf2101dcfef4a708f6d031fe4f2dbbd2c161dd09ce19'
ORDER_SHA = 'b0ea22e59fe7c709f896265090d63c22cd53917f610e5a1bb9fe9adfed42df37'
SCHEMA = 'R109_ROUTE_RESIDENT_INHERITED_SEED_V1'
require = native.require
read, sha = continual.read, continual.sha


def _seal(document):
    result = dict(document)
    result.pop('binding_sha256', None)
    result['binding_sha256'] = storage.digest(result)
    return result


def _ref(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path and path.is_file(), 'canonical_source_file')
    return dict(path=str(path), sha256=sha(path))


def _verify_ref(entry):
    require(_ref(entry['path']) == entry, 'source_file_hash_drift')


def _once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def parameter_manifest(model):
    return [dict(name=name, shape=list(parameter.shape), dtype=str(parameter.dtype))
        for name, parameter in model.named_parameters() if native.is_lora(name)]


def _meta_manifest(model_dir, adapter_dir):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoConfig, AutoModelForCausalLM
    require(not torch.cuda.is_initialized(), 'CPU_prepare_no_CUDA_context')
    config = AutoConfig.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    require(config.model_type == 'qwen2', 'frozen_qwen_architecture')
    with torch.random.fork_rng(devices=[]):
        with torch.device('meta'):
            model = get_peft_model(AutoModelForCausalLM.from_config(config, trust_remote_code=False),
                LoraConfig.from_pretrained(adapter_dir, local_files_only=True))
        manifest = parameter_manifest(model)
        require(all(parameter.device.type == 'meta' for parameter in model.parameters()), 'metadata_only_model')
    require(len(manifest) == 392 and hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        == ORDER_SHA, 'original_native_optimizer_order')
    require(not torch.cuda.is_initialized(), 'CPU_prepare_initialized_CUDA')
    return manifest


def optimizer_summary(state, parameters, expected_step=None):
    import torch
    require(set(state) == {'state','param_groups'} and len(state['param_groups']) == 1, 'one_AdamW_group')
    group = state['param_groups'][0]
    identifiers = group['params']
    names = [entry['name'] for entry in parameters]
    require(bool(names) and len(names) == len(set(names)) == len(identifiers) == len(set(identifiers)),
        'optimizer_parameter_bijection')
    require(set(state['state']) == set(identifiers), 'complete_optimizer_slots')
    require(group['lr'] == 3e-5 and tuple(group['betas']) == (.9,.999) and group['eps'] == 1e-8
        and group['weight_decay'] == .01 and all(group.get(key) is False for key in
            ('amsgrad','maximize','foreach','capturable','differentiable','fused')),
        'inherited_AdamW_recipe')
    require(group.get('decoupled_weight_decay', True) is True, 'AdamW_weight_decay')
    named, steps = {}, []
    for entry, identifier in zip(parameters, identifiers):
        require(native.is_lora(entry['name']) and entry['dtype'] == 'torch.float32', 'fp32_LoRA_mapping')
        buffers = state['state'][identifier]
        require(set(buffers) == {'step','exp_avg','exp_avg_sq'}, 'exact_AdamW_buffers')
        step = buffers['step']
        require(torch.is_tensor(step) and step.numel() == 1 and bool(torch.isfinite(step).all()), 'finite_step')
        value = step.item()
        require(value >= 1 and value == int(value), 'positive_integral_step')
        steps.append(int(value))
        for key in ('exp_avg','exp_avg_sq'):
            tensor = buffers[key]
            require(torch.is_tensor(tensor) and list(tensor.shape) == entry['shape']
                and str(tensor.dtype) == entry['dtype'] and bool(torch.isfinite(tensor).all()), 'moment_shape_dtype_finite')
        require(bool((buffers['exp_avg_sq'] >= 0).all()), 'nonnegative_second_moment')
        named[entry['name']] = buffers
    require(len(set(steps)) == 1 and (expected_step is None or steps[0] == expected_step), 'optimizer_step_continuity')
    options = json.loads(json.dumps({key:value for key,value in group.items() if key not in ('params','param_names')}))
    return dict(step=steps[0], parameter_count=len(names), options=options,
        named_state_sha256=native.state_hash(dict(parameters=named, options=options)))


def remap_optimizer(state, source_parameters, destination_parameters, destination_ids):
    source = {entry['name']:entry for entry in source_parameters}
    destination = {entry['name']:entry for entry in destination_parameters}
    require(len(source) == len(source_parameters) and len(destination) == len(destination_parameters)
        and source == destination, 'named_parameter_shape_dtype_drift')
    require(len(destination_ids) == len(destination_parameters) == len(set(destination_ids)), 'destination_slots')
    before = optimizer_summary(state, source_parameters)
    identifiers = dict(zip([entry['name'] for entry in source_parameters], state['param_groups'][0]['params']))
    group = dict(state['param_groups'][0], params=list(destination_ids))
    group.pop('param_names', None)
    remapped = dict(param_groups=[group], state={identifier:state['state'][identifiers[entry['name']]]
        for identifier, entry in zip(destination_ids, destination_parameters)})
    require(optimizer_summary(remapped, destination_parameters) == before, 'remapping_changed_moments')
    return remapped


def rehearsal_indexes(rows=3635):
    require(rows == 3635, 'fixed_V13_rehearsal')
    return [position*(rows-1)//15 for position in range(16)]


def _load_optimizer(document):
    import torch
    _verify_ref(dict(path=document['optimizer_path'], sha256=document['optimizer_sha256']))
    return torch.load(document['optimizer_path'], map_location='cpu', weights_only=True)


def prepare(checkpoint=CHECKPOINT, *, output=None):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_prepare')
    checkpoint = Path(checkpoint)
    require(sha(checkpoint/'COMMIT.json') == COMMIT_SHA, 'actual_FULL8932_only')
    committed = storage.verify_checkpoint(checkpoint)
    meta = committed['metadata']
    require(meta['update'] == 8932 and meta['source_sha256'] == SOURCE_SHA, 'seed_update_source')
    identity = native.bridge.AdapterIdentity.from_document(meta['adapter'])
    require(identity.state_sha256 == STATE_SHA and identity.base_sha256 == BASE_SHA, 'actual_seed_and_base')
    root = checkpoint.parents[2]
    prepared = read(root/'PREPARE.json')
    require(sha(root/'source.tar') == SOURCE_SHA, 'frozen_trainer_archive')
    require(continual.verify_archive(root/'source.tar', root/'source') == prepared['source_files'], 'frozen_runtime_files')
    continual.common.portable.verify_base_files(prepared['bundle'], prepared['model_dir'],
        expected_manifest_sha256=continual.BUNDLE_SHA)
    corpus_path = root/'CORPORA/000013.json'
    require(meta['corpus_version'] == 13 and meta['corpus_sha256'] == sha(corpus_path) == CORPUS_SHA, 'actual_V13')
    corpus = read(corpus_path)
    require(len(corpus['rows']) == 3635, 'full_training_corpus')
    parameters = _meta_manifest(prepared['model_dir'], identity.path)
    from safetensors import safe_open
    with safe_open(Path(identity.path)/'adapter_model.safetensors', framework='pt', device='cpu') as archive:
        keys = {entry['name'].replace('.default.weight','.weight'):entry for entry in parameters}
        require(set(keys) == set(archive.keys()), 'adapter_tensor_names')
        require(all(list(archive.get_slice(name).get_shape()) == entry['shape'] for name,entry in keys.items()),
            'adapter_tensor_shapes')
    document = dict(schema=SCHEMA, generation=0, adapter=identity.document(), base_sha256=BASE_SHA,
        model_dir=prepared['model_dir'], bundle=prepared['bundle'], source_process=meta['process'],
        origin_checkpoint=_ref(checkpoint/'COMMIT.json'), origin_state_sha256=STATE_SHA,
        native_source=_ref(root/'source.tar'), source_prepare=_ref(root/'PREPARE.json'),
        optimizer_path=str(checkpoint/'optimizer.pt'), optimizer_sha256=sha(checkpoint/'optimizer.pt'),
        rng_path=str(checkpoint/'rank0.pt'), rng_sha256=sha(checkpoint/'rank0.pt'),
        optimizer_parameters=parameters, original_parameter_order_sha256=ORDER_SHA,
        corpus_path=str(corpus_path), corpus_sha256=CORPUS_SHA, corpus_version=13, corpus_rows=3635,
        rehearsal_indices=rehearsal_indexes(), rehearsal_row_sha256=[storage.digest(corpus['rows'][index])
            for index in rehearsal_indexes()], inherited_l1_update=8932,
        rank_policy='Single L2 life continues exact saved rank0 RNG; old3-rank numerical equivalence not claimed.',
        supported_row_encodings=['terse_route','rich_route','math','math_content_v2'],
        legacy_source_root=str(root), no_held_or_parent_inputs=True, no_L2_into_ongoing_L1=True,
        helper_sha256=sha(__file__), prepared_unix=time.time())
    document['optimizer_summary'] = optimizer_summary(_load_optimizer(document), parameters, 8932)
    document = _seal(document)
    validate(document)
    if output is not None:
        _once(output, document)
    return document


def validate(document):
    require(document['schema'] == SCHEMA and _seal(document) == document, 'seed_document_binding')
    require(document['helper_sha256'] == sha(__file__), 'seed_helper_source_drift')
    require(document['origin_checkpoint']['sha256'] == COMMIT_SHA and document['origin_state_sha256'] == STATE_SHA
        and document['base_sha256'] == BASE_SHA and document['inherited_l1_update'] == 8932, 'seed_lineage_drift')
    for key in ('origin_checkpoint','native_source','source_prepare'):
        _verify_ref(document[key])
    identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
    require(identity.base_sha256 == BASE_SHA and document['native_source']['sha256'] == SOURCE_SHA, 'frozen_base_source')
    require(document['original_parameter_order_sha256'] == ORDER_SHA, 'original_order_binding')
    if document['generation'] == 0:
        origin = read(document['origin_checkpoint']['path'])
        require(document['adapter'] == origin['metadata']['adapter'] and identity.state_sha256 == STATE_SHA, 'initial_adapter_drift')
        require(document['source_process'] == origin['metadata']['process'], 'original_process_binding')
        require(hashlib.sha256(json.dumps(document['optimizer_parameters'], sort_keys=True).encode()).hexdigest()
            == ORDER_SHA, 'original_parameter_order_drift')
        directory = Path(document['origin_checkpoint']['path']).parent
        require(document['optimizer_path'] == str(directory/'optimizer.pt')
            and document['optimizer_sha256'] == origin['files']['optimizer.pt']
            and document['rng_path'] == str(directory/'rank0.pt')
            and document['rng_sha256'] == origin['files']['rank0.pt'], 'initial_optimizer_rng_binding')
    else:
        require(type(document['generation']) is int and 1 <= document['generation'] <= 256, 'bounded_saved_chain')
        _verify_ref(document['parent_document'])
        parent = read(document['parent_document']['path'])
        require(_seal(parent) == parent and parent['binding_sha256'] == document['parent_binding_sha256']
            and parent['generation']+1 == document['generation'] and parent['origin_checkpoint'] == document['origin_checkpoint'],
            'saved_parent_continuity')
        require(document['optimizer_summary']['step'] >= parent['optimizer_summary']['step'], 'optimizer_counter_regression')
        require({entry['name']:entry for entry in document['optimizer_parameters']} ==
            {entry['name']:entry for entry in parent['optimizer_parameters']}, 'carry_parameter_mapping_drift')
    require(document['corpus_sha256'] == CORPUS_SHA and document['corpus_version'] == 13
        and document['corpus_rows'] == 3635 and document['rehearsal_indices'] == rehearsal_indexes(), 'rehearsal_binding')
    _verify_ref(dict(path=document['corpus_path'], sha256=CORPUS_SHA))
    _verify_ref(dict(path=document['rng_path'], sha256=document['rng_sha256']))
    summary = optimizer_summary(_load_optimizer(document), document['optimizer_parameters'])
    require(summary == document['optimizer_summary'] and summary['step'] >= 8932, 'saved_optimizer_drift_or_reset')
    require(document['generation'] != 0 or summary['step'] == 8932, 'initial_step')
    continual.common.portable.verify_base_files(document['bundle'], document['model_dir'],
        expected_manifest_sha256=continual.BUNDLE_SHA)
    return document


def restore(loaded, document):
    validate(document)
    require(loaded.binding.phase == 'training', 'restore_only_sleep_training_binding')
    identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
    require(loaded.observed == identity and native.observe_adapter(loaded.engine, identity) == identity, 'mounted_seed_identity')
    require(loaded.optimizer is None, 'do_not_overwrite_live_optimizer')
    selected = native.development.enable_existing_adapter(loaded.engine)
    parameters = parameter_manifest(loaded.engine.model)
    require(list(selected) == [entry['name'] for entry in parameters], 'live_trainability_order')
    require(native.state_hash(selected) == identity.state_sha256, 'enabling_adapter_changed_state')
    require(not any(parameter.requires_grad for name,parameter in loaded.engine.model.named_parameters()
        if not native.is_lora(name)), 'base_trainability_drift')
    torch = loaded.engine.torch
    optimizer = torch.optim.AdamW(list(selected.values()), lr=3e-5,
        betas=(.9,.999), eps=1e-8, weight_decay=.01, amsgrad=False, foreach=False, fused=False)
    destination = optimizer.state_dict()['param_groups'][0]['params']
    state = remap_optimizer(_load_optimizer(document), document['optimizer_parameters'], parameters, destination)
    optimizer.load_state_dict(state)
    summary = optimizer_summary(optimizer.state_dict(), parameters, document['optimizer_summary']['step'])
    require(summary == document['optimizer_summary'], 'loaded_optimizer_not_exact')
    _verify_ref(dict(path=document['rng_path'], sha256=document['rng_sha256']))
    rng = torch.load(document['rng_path'], map_location='cpu', weights_only=False)
    require(set(rng) == {'python','numpy','torch','cuda'}, 'complete_saved_RNG')
    continual.restore_rng(torch, rng)
    loaded.optimizer = optimizer
    loaded.engine.model.train()
    provenance = dict(schema='R108_OPTIMIZER_RESTORED_V1', binding_sha256=document['binding_sha256'],
        optimizer_path=document['optimizer_path'], optimizer_sha256=document['optimizer_sha256'],
        named_state_sha256=summary['named_state_sha256'], step=summary['step'], parameter_count=len(parameters),
        mapping='Source native IDs -> bound parameter names -> live optimizer IDs; all moments and options checked.',
        rng_path=document['rng_path'], rng_sha256=document['rng_sha256'], rank0_rng_restored=True,
        optimizer_reset=False, manual_seed_called=False, generation=document['generation'])
    loaded.r108_seed_provenance = provenance
    return provenance


def save_carry(loaded, document, adapter, output_dir):
    validate(document)
    require(loaded.binding.phase == 'training', 'carry_only_sleep_training_binding')
    require(loaded.optimizer is not None and loaded.r108_seed_provenance['binding_sha256'] == document['binding_sha256'],
        'current_loaded_seed_required')
    identity = native.bridge.AdapterIdentity.from_document(adapter.document() if hasattr(adapter,'document') else adapter)
    require(identity.base_sha256 == BASE_SHA and native.observe_adapter(loaded.engine, identity) == identity, 'saved_mounted_child')
    parameters = parameter_manifest(loaded.engine.model)
    selected = [parameter for name, parameter in loaded.engine.model.named_parameters() if native.is_lora(name)]
    require(len(loaded.optimizer.param_groups) == 1
        and [id(parameter) for parameter in loaded.optimizer.param_groups[0]['params']]
        == [id(parameter) for parameter in selected], 'carry_live_optimizer_order')
    state = loaded.optimizer.state_dict()
    summary = optimizer_summary(state, parameters)
    require(summary['step'] >= document['optimizer_summary']['step'], 'carry_reset_forbidden')
    directory = Path(output_dir)
    require(directory.is_absolute(), 'absolute_carry_directory')
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('optimizer.pt','rng.pt','PARENT_SEED.json','CARRY.json'):
        require(not (directory/name).exists(), 'carry_never_overwrites')
    loaded.engine.verify_base()
    torch = loaded.engine.torch
    with (directory/'optimizer.pt').open('xb') as stream:
        torch.save(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    with (directory/'rng.pt').open('xb') as stream:
        torch.save(continual.rng_state(torch), stream)
        stream.flush()
        os.fsync(stream.fileno())
    _once(directory/'PARENT_SEED.json', document)
    result = dict(document, generation=document['generation']+1, adapter=identity.document(),
        source_process=list(loaded.process), optimizer_path=str(directory/'optimizer.pt'),
        optimizer_sha256=sha(directory/'optimizer.pt'), rng_path=str(directory/'rng.pt'),
        rng_sha256=sha(directory/'rng.pt'), optimizer_parameters=parameters, optimizer_summary=summary,
        parent_document=_ref(directory/'PARENT_SEED.json'), parent_binding_sha256=document['binding_sha256'],
        saved_unix=time.time())
    result = _seal(result)
    validate(result)
    _once(directory/'CARRY.json', result)
    return result


def rehearsal_rows(document):
    require(document['corpus_sha256'] == CORPUS_SHA and document['rehearsal_indices'] == rehearsal_indexes(), 'rehearsal_scope')
    _verify_ref(dict(path=document['corpus_path'], sha256=CORPUS_SHA))
    rows = read(document['corpus_path'])['rows']
    selected = [rows[index] for index in document['rehearsal_indices']]
    require([storage.digest(row) for row in selected] == document['rehearsal_row_sha256'], 'exact_training_rows')
    return deepcopy(selected)


def encoded(row, tokenizer):
    kind, material = row['encoding'], row['row']
    if kind == 'terse_route':
        route = continual.combined.route
        from gpu.orch_combined_l1_continual_content import encode_rows
        prefix = material['prefix']
        require([message['role'] for message in prefix] == ['system','user']
            + ['assistant','user']*material['episode_call_index'], 'alternating_goal_pair_student_prefix_required')
        require(tokenizer.eos_token == route.quality.lesson.TARGET_EOT and type(tokenizer.eos_token_id) is int
            and route.source.native._encode(tokenizer, tokenizer.eos_token) == (tokenizer.eos_token_id,),
            'exact_goal_pair_eot_required')
        result = encode_rows([dict(student_prefix=prefix, target=material['assistant'])], tokenizer)[0]
        messages = prefix + [dict(role='assistant',content=material['assistant'])]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        prefix_ids = route.source.native._encode(tokenizer, context)
        supervised = tuple(label for label in result.labels if label != -100)
        require(len(supervised) <= 160, 'untruncated_bounded_goal_pair_sequence_required')
        require(route.source.native._decode(tokenizer, prefix_ids) == context
            and route.source.native._decode(tokenizer, supervised) == material['assistant'] + tokenizer.eos_token
            and route.source.native._decode(tokenizer, route.source.native._encode(tokenizer, '\n')) == '\n',
            'goal_pair_token_roundtrip_failed')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
            return_dict=False, truncation=False, padding=False)) == result.input_ids, 'goal_pair_template_token_ids_mismatch')
        return result
    if kind == 'rich_route':
        student = material['student']
        require(student['messages'][-1] == dict(role='assistant', content=student['target']), 'rich_route_target_binding')
        material = dict(student_prefix=student['messages'][:-1], target=student['target'])
    if kind in ('math','rich_route'):
        return continual.encoding.encode_rows([material], tokenizer)[0]
    require(kind == 'math_content_v2' and row['eligibility']['eligible'] is True, 'admitted_content_only')
    from gpu.orch_combined_l1_continual_content import encode_rows
    result = encode_rows([material], tokenizer)[0]
    if row['eligibility']['policy'] == 'ROHIN98_BATCH_SAMPLED_AUTHOR_REVIEW_V2':
        supplied = material['training_encoding']
        require(list(result.input_ids) == supplied['input_ids'] and list(result.labels) == supplied['labels']
            and len(result.input_ids) == supplied['sequence_length'] <= supplied['context_limit'] == 2048,
            'exact_historical_native_encoding')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, default=CHECKPOINT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.checkpoint, output=args.output)
    print(json.dumps(dict(output=str(args.output), binding_sha256=result['binding_sha256'],
        optimizer=result['optimizer_summary'], rehearsal_indices=result['rehearsal_indices'], native_calls=0)))
