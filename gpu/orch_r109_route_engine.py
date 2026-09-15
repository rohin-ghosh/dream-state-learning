"""Resident native generation and real inherited-optimizer LoRA sleep."""

from dataclasses import replace
from pathlib import Path
import hashlib
import time

from gpu import orch_guided_native as native
from gpu import orch_r109_route_seed as seed
from gpu import orch_reflection_repetition_stop as stop
from gpu.orch_rich_hot_node3_base107_engine import Engine as BaseEngine
from organism_v6 import orch_r109_route as policy
from organism_v6 import orch_r107_parented_replay as replay


def generate(engine, messages, *, reflection=False):
    engine.check('generation')
    policy.require(not any(parameter.requires_grad for parameter in engine.model.parameters()), 'readonly_generation')
    engine.model.eval()
    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    cap = policy.token_budget(len(tokens))
    inputs = engine.torch.tensor([tokens], dtype=engine.torch.long, device=engine.device)
    config = engine.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
        max_new_tokens=cap, repetition_penalty=1.0, eos_token_id=engine.tokenizer.eos_token_id,
        pad_token_id=engine.tokenizer.pad_token_id)
    criterion = None
    options = {}
    if reflection:
        policy.require(hashlib.sha256(Path(stop.__file__).read_bytes()).hexdigest() == policy.STOP_SHA, 'pinned_reflection_helper')
        criterion = stop.ExactParagraphRepetitionStop(engine.tokenizer, prompt_length=len(tokens), eos_token_ids=engine.tokenizer.eos_token_id)
        options['stopping_criteria'] = engine.transformers.StoppingCriteriaList([criterion])
    with engine.torch.inference_mode():
        output = engine.model.generate(input_ids=inputs, attention_mask=engine.torch.ones_like(inputs), generation_config=config, **options)
    policy.require(output[0, :len(tokens)].tolist() == tokens, 'complete_actual_prompt_prefix')
    tail = output[0, len(tokens):].tolist()
    terminal = bool(tail) and tail[-1] == engine.tokenizer.eos_token_id
    raw = engine.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    ending = criterion.finalize(output, max_new_tokens=cap) if criterion else None
    return dict(messages=messages, raw=raw, token_ids=tail, prompt_tokens=len(tokens), input_truncated=False,
        full_prompt_prefix_verified=True, prompt_token_ids_sha256=policy.digest(tokens), terminal=terminal,
        truncated=ending['truncated'] if ending else not terminal and len(tail) == cap,
        effective_generation_cap=cap, reflection_guard=ending, semantic_functional_change=None, trainingAllowed=False)


def replay_row(call, path, digest):
    response = call['response']
    row = dict(replay_mode=replay.MODE, student_prefix=response['messages'], target=response['raw'],
        source_prompt_sha256=replay.history_policy.digest(response['messages']), source_prompt_tokens=response['prompt_tokens'],
        source_generated_token_ids=response['token_ids'], append_eos=response['terminal'], continuation_only=not response['terminal'],
        target_sha256=hashlib.sha256(response['raw'].encode()).hexdigest(), source_record_sha256=digest,
        source_call_path=str(path), source_call_sha256=digest, episode_id=call['task_id'],
        objective='R109_OWN_CAUSAL_CONTINUATION_ALL_PREFIX_MASKED', observed_fact_endorsement=False)
    replay.verify_source(row, call)
    return row


def load_learned(document, lane, root, check):
    identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
    binding = native.bridge.StageBinding(root.name, native.bridge.ARMS[0], 0, 'training', identity, True, True, policy.digest(lane))
    loaded = native.load_stage(binding, model_dir=document['model_dir'], device='cuda:0', gpu_uuid=lane['uuid'],
        context=native.StageContext(private_guidance=('R109_ROUTE_PRIVATE_PARENT',)), check=check,
        predecessor_processes=(tuple(document['source_process']),))
    provenance = seed.restore(loaded, document)
    loaded.engine.model.requires_grad_(False)
    return loaded, provenance


def sleep(loaded, document, rows, old_rows, anchors, output, deadline, check, write, sha):
    from gpu import orch_r108_guided_native as trainer
    engine = loaded.engine
    native.development.enable_existing_adapter(engine)
    encoded, rejected = [], []
    for row in rows:
        try:
            encoded.append((row, replay.encode_row(row, engine.tokenizer, policy.CONTEXT)))
        except ValueError as error:
            rejected.append(dict(source=row['source_call_sha256'], reason=str(error)))
    write(output / 'REPLAY_ELIGIBILITY.json', dict(eligible=[row['source_call_sha256'] for row, value in encoded],
        rejected=rejected, no_outcome_selection=True, parent_prefix_masked=True))
    policy.require(encoded, 'no_valid_native_replay_rows')
    trainer.validate_anchor_inventory(anchors)
    old_l1 = [seed.encoded(row, engine.tokenizer) for row in seed.rehearsal_rows(document)]
    prior = []
    for row in old_rows[-64:]:
        try:
            prior.append(replay.encode_row(row, engine.tokenizer, policy.CONTEXT))
        except ValueError:
            pass
    started, step = time.time(), 0
    before = native.state_hash({name:parameter for name,parameter in engine.model.named_parameters() if native.is_lora(name)})
    presentations = {row['source_call_sha256']:0 for row,value in encoded}
    while time.time() < deadline:
        row, value = encoded[step % len(encoded)]
        batch = [('NEW:' + row['source_call_sha256'], value), ('L1_REHEARSAL', old_l1[step % len(old_l1)])]
        if prior:
            batch.append(('L2_REHEARSAL', prior[step % len(prior)]))
        batch += [('BASE_ANCHOR:' + family, values[step % len(values)]['encoded']) for family,values in sorted(anchors.items())]
        losses = trainer.train_batch(engine, loaded.optimizer, batch, check)
        presentations[row['source_call_sha256']] += 1
        step += 1
        write(output / 'updates' / f'{step:06d}.json', dict(step=step, losses=losses, finished_unix=time.time()))
    policy.require(step > 0, 'real_LoRA_updates_required')
    engine.verify_base()
    destination = output / 'adapter'
    engine.model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
    parameters = {name:parameter for name,parameter in engine.model.named_parameters() if native.is_lora(name)}
    after = native.state_hash(parameters)
    policy.require(after != before, 'actual_LoRA_state_change_required')
    identity = native.bridge.AdapterIdentity(str(destination), after, seed.BASE_SHA,
        tuple((path.name,sha(path)) for path in sorted(destination.iterdir()) if path.is_file())).verify()
    carried = seed.save_carry(loaded, document, identity, output / 'carry')
    policy.require(carried['optimizer_summary']['step'] > document['optimizer_summary']['step'], 'optimizer_step_advances')
    loaded.binding = replace(loaded.binding, adapter=identity)
    loaded.observed = identity
    loaded.r108_seed_provenance['binding_sha256'] = carried['binding_sha256']
    engine.model.requires_grad_(False)
    engine.model.eval()
    summary = dict(optimizer_updates=step, before_adapter_sha256=before, after_adapter_sha256=after,
        inherited_step=document['optimizer_summary']['step'], final_step=carried['optimizer_summary']['step'],
        presentations=presentations, every_row_presented=all(presentations.values()),
        started_unix=started, finished_unix=time.time(), resident_process=native.process_identity(), no_optimizer_reset=True)
    write(output / 'COMPLETE.json', summary)
    return carried, summary
