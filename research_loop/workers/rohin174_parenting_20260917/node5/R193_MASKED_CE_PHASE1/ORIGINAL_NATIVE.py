"""Native TRAIN-only continuous generation, optional child compaction and LoRA sleep.

New PLANs may omit seed (0) and presleep_variant (free_distillation), or select
a nonnegative 32-bit seed and one of PRESLEEP_INVITATIONS with its exact
compaction_invitation. no_distillation uses an empty invitation and no extra
generation or compaction; ordinary bounded-context eviction still applies.
reread_select is a prompt-guided selection, not a verified extractive parser.
Parent guidance uses the ordinary TRAIN inbox, never a private target channel.
New lives bind seed and prompts in stream, adapter COMMIT and optimizer/RNG
checkpoints. Legacy resumes retain their saved adapter/RNG and no new binding.
"""

import argparse
from copy import deepcopy
import gc
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import (
    ContinualStream, PRESLEEP_INVITATIONS, digest, experiment_binding, require,
    validate_experiment, verify_experiment_resume,
)


SCHEMA = 'R125_NATIVE_CONTINUITY_V1'
BASE_SHA256 = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
SYSTEM = (
    'You are a language-model agent with an ongoing history. Between incoming messages, '
    'continue your own inquiry without waiting for another request. You can consider what '
    'to investigate next, revisit an observation, or reflect on how your thinking is going. '
    'Use your own organization; do not pad or repeat a passage just to keep producing text. '
    'An end-of-generation marker is a software boundary, not a request to forget your history. '
    'Runtime notices and parent messages are inputs, not your own words.'
)
BIRTH = (
    'Take the intelligence in your inherited model and turn it into behaviours you actually '
    'do, repeat those behaviours, and learn them in your LoRA. What is worth exploring and '
    'practising is for you to discover through experience and conversation. '
    'Your inherited model is frozen Qwen2.5-7B-Instruct. Your rank-8 LoRA is a small adapter '
    'attached to it, and only that adapter changes during sleep. Sleep trains on your own '
    'words, not the words people or the environment supply. Ordinary competent examples '
    'are mixed in to help keep general abilities accessible. Repeated errors and empty '
    'rituals can also be learned; improvement is not guaranteed. '
    'At the end of a thought, consider what you want to think about next and continue. '
    'When nothing else is happening, you can think about how you are thinking. Before '
    'sleep, consider what from your experience you want to carry forward. Your context '
    'is finite: the oldest visible passages are dropped when it fills. Short notices '
    'tell you your token costs. People can speak to you as you go; you need not wait '
    'for them. For now you have this conversation, not an enabled shell or experiment '
    'tools. Distinguish your ideas and predictions from results you actually receive.'
)
COMPACTION_INVITATION = PRESLEEP_INVITATIONS['free_distillation']


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_once(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def validate_plan(plan):
    require(plan['schema'] == SCHEMA and plan['base_sha256'] == BASE_SHA256, 'frozen_native_contract')
    if plan.get('think_act_learn') is not None:
        from gpu.orch_r184_think_act_learn import validate_config
        validate_config(plan['think_act_learn'])
        require(plan['rehearsal_presentations'] == 0, 'R184_new_rows_only')
    startup = plan.get('startup_context')
    if startup is None:
        require(plan['birth_prompt'] == BIRTH, 'exact_posted_prompts')
    else:
        require(type(startup) is dict and set(startup) == {'version', 'path', 'sha256'}
            and startup['version'] == 'R127_STARTUP_V1', 'exact_R127_startup_binding')
        path = Path(startup['path'])
        require(path.is_absolute() and path.resolve().is_relative_to(Path(plan['source_root']).resolve())
            and not path.is_symlink() and sha(path) == startup['sha256'], 'pinned_startup_source')
        text = path.read_text()
        require(text == plan['birth_prompt'] and 0 < len(text.encode()) <= 16384
            and 'Machine-side configuration' not in text, 'child_facing_startup_only')
        import re
        require(re.search(r'\[[A-Z][A-Z_]+\]', text) is None, 'startup_placeholders_filled')
    require(plan['system_prompt'] == SYSTEM, 'exact_posted_prompts')
    experiment_binding(plan)
    require(plan['new_presentations'] == 16 and type(plan['rehearsal_presentations']) is int
            and plan['rehearsal_presentations'] in (0, 1)
            and plan['anchor_lambda'] == 0.25, 'declared_presentation_and_anchor_schedule')
    require(plan['segments_per_sleep'] == 2, 'initial_native_schedule')
    require(type(plan['segment_tokens']) is int and 1 <= plan['segment_tokens'] <= 1024,
            'bounded_native_segment')
    from organism_v6.orch_r125_plain_context import VERSION
    plain = plan.get('presentation_version') == VERSION
    require(plan.get('presentation_version') in (None, VERSION), 'known_presentation_version')
    require(type(plan['context_limit']) is int and (16384 <= plan['context_limit'] <= 32768 if plain
            else plan['segment_tokens'] < plan['context_limit'] <= 8192),
            'bounded_native_context')
    require(plan['max_sleeps'] is None or type(plan['max_sleeps']) is int and plan['max_sleeps'] > 0,
            'explicit_smoke_or_long_life')
    require(type(plan['physical']) is int and 0 <= plan['physical'] < 8
            and plan['gpu_uuid'].startswith('GPU-'), 'explicit_gpu_identity')
    require(time.time() < plan['hard_end_unix'] <= plan['lease_end_unix']-120, 'within_lease_wall')
    if plan.get('authorized_wall_extension') is not None:
        from gpu.orch_r125_stream_journal import validate_wall_extension
        authorization = validate_wall_extension(plan['authorized_wall_extension'])
        require(authorization['new_deadline_unix'] == plan['hard_end_unix']
            and authorization['lease_end_unix'] == plan['lease_end_unix'], 'wall_extension_plan_budget_binding')
    require(plan['decoder'] == dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05,
                                   no_repeat_ngram_size=16), 'posted_decoder')
    readout_name(plan, 0)
    for key in ('root', 'model_dir', 'anchors', 'source_root'):
        require(Path(plan[key]).is_absolute(), 'absolute_path:'+key)
    require(not Path(plan['root']).resolve().is_relative_to(Path(plan['source_root']).resolve()),
            'raw_outside_source_tree')
    return plan


def encode_own(row, tokenizer, context_limit):
    from gpu.astra_pchain2_native import EncodedRow
    require(row['split'] == 'TRAIN' and row['actor'] == 'child'
            and row['prefix_loss'] is False and row['target_loss'] is True, 'child_targets_only')
    prefix = tuple(tokenizer.apply_chat_template(row['prefix'], tokenize=True,
                   add_generation_prompt=True, return_dict=False))
    target = tuple(row['token_ids'])
    require(target and all(type(token) is int and token >= 0 for token in target), 'actual_native_target_ids')
    require(not row['terminal'] or target[-1] == tokenizer.eos_token_id, 'actual_terminal_eos')
    visible = target[:-1] if row['terminal'] else target
    permitted = set()
    pad = getattr(tokenizer, 'pad_token_id', None)
    if pad is not None and tokenizer.decode([pad], skip_special_tokens=False,
            clean_up_tokenization_spaces=False) == '<|endoftext|>':
        permitted.add(pad)
    require(not (set(tokenizer.all_special_ids)-permitted).intersection(visible),
            'no_special_token_target_injection')
    require(tokenizer.decode(visible, skip_special_tokens=False,
                clean_up_tokenization_spaces=False) == row['target'], 'native_target_roundtrip')
    require(len(prefix)+len(target) <= context_limit, 'whole_source_no_training_trim')
    return EncodedRow(prefix+target, (-100,)*len(prefix)+target, target)


def presentation_schedule(new_rows, old_rows):
    require(new_rows, 'new_rows_required')
    return [('NEW', row) for unused in range(16) for row in new_rows] + [
        ('REHEARSAL', row) for row in old_rows]


def select_rehearsal_rows(plan, old_rows):
    presentations = plan.get('rehearsal_presentations', 1)
    require(type(presentations) is int and presentations in (0, 1), 'explicit_rehearsal_schedule')
    return old_rows if presentations else []


def readout_name(plan, cycle):
    revision = plan.get('readout_revision', 1)
    require(type(revision) is int and revision >= 1, 'positive_readout_revision')
    return f'sleep_{cycle:06d}' + (f'_r{revision}' if revision > 1 else '')


def fresh_readout(child, plan_path, checkpoint, cycle):
    name = readout_name(child.plan, cycle)
    output = Path(child.plan['root'])/'readouts'/name
    output.parent.mkdir(parents=True, exist_ok=True)
    status_path = output.parent/f'{name}_DISPATCH.json'
    require(not output.exists() and not status_path.exists(), 'readout_no_implicit_replay')
    checkpoint_path = Path(checkpoint['adapter_path']).parent/'COMMIT.json'
    command = [sys.executable, '-B', '-m', 'gpu.orch_r125_continual_readout',
        '--plan', str(plan_path), '--checkpoint', str(checkpoint_path), '--output', str(output)]
    write_once(status_path, dict(cycle=cycle, command_sha256=digest(command),
        checkpoint_sha256=sha(checkpoint_path), resident_pid=os.getpid(),
        started_unix=time.time(), history_shared=False, parent_present=False))
    state = child.offload_for_readout()
    process = None
    try:
        with (output.parent/f'{name}.log').open('x') as log:
            process = subprocess.Popen(command, cwd=child.plan['source_root'],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
            status = process.wait(timeout=max(1, child.plan['hard_end_unix']-time.time()-15))
        require(status == 0 and (output/'COMPLETE.json').is_file(), 'fresh_readout_incomplete')
    except Exception as error:
        write_once(output.parent/f'{name}_FAILED.json',
            dict(error_type=type(error).__name__, error=str(error), failed_unix=time.time(),
                 retry_allowed=False, continued_training_not_evidence_of_readout_success=True))
    finally:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        child.restore_after_readout(state)


class NativeChild:
    def __init__(self, plan, checkpoint=None):
        from gpu import astra_experienced_event_microloop as source
        from gpu import orch_guided_native as native
        self.plan, self.native = plan, native
        self.experiment = deepcopy(checkpoint.get('experiment')) if checkpoint else experiment_binding(plan)
        if checkpoint:
            verify_experiment_resume(plan, self.experiment)
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_bound_GPU_environment')
        tokenizer = source.native.load_local_tokenizer(plan['model_dir'])
        if checkpoint:
            self.verify_checkpoint(checkpoint)
        options = SimpleNamespace(model_dir=plan['model_dir'], device='cuda:0' if checkpoint else 'cpu',
            phase='readout', expected_base_sha256=BASE_SHA256,
            adapter_dir=checkpoint['adapter_path'] if checkpoint else None)
        self.engine = source.Engine(options, tokenizer, check=self.check)
        self.torch, self.tokenizer = self.engine.torch, tokenizer
        if not checkpoint:
            self.initialize_adapter()
        require(plan['context_limit'] <= self.engine.model.config.max_position_embeddings,
                'context_within_local_model_positions')
        self.parameters = {name: parameter for name, parameter in self.engine.model.named_parameters()
                           if native.is_lora(name)}
        require(self.parameters and all(parameter.dtype == self.torch.float32
                for parameter in self.parameters.values()), 'FP32_LoRA_parameters')
        if checkpoint:
            self.engine.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            self.engine.model.enable_input_require_grads()
        self.optimizer = self.torch.optim.AdamW(list(self.parameters.values()), lr=3e-5,
            betas=(0.9,0.999), eps=1e-8, weight_decay=0.01, foreach=False, fused=False)
        self.optimizer_steps = 0
        if checkpoint:
            payload = self.torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
            require(payload.get('experiment') == self.experiment, 'optimizer_experiment_binding')
            require(payload['parameter_names'] == list(self.parameters), 'exact_optimizer_parameter_order')
            self.optimizer.load_state_dict(payload['optimizer'])
            self.optimizer_steps = payload['optimizer_steps']
            self.torch.set_rng_state(payload['cpu_rng'])
            self.torch.cuda.set_rng_state_all(payload['cuda_rng'])
            random.setstate(payload['python_rng'])
            require(self.adapter_hash() == checkpoint['adapter_state_sha256'], 'restored_adapter_state')
        else:
            self.seed_rng()
        self.engine.model.requires_grad_(False)
        self.engine.model.eval()

    def seed_rng(self):
        seed = self.experiment['seed']
        random.seed(seed)
        self.torch.manual_seed(seed)
        self.torch.cuda.manual_seed_all(seed)

    def initialize_adapter(self):
        from gpu.astra_pchain2_native import TARGET_MODULES
        import peft
        self.seed_rng()
        config = peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
            target_modules=list(TARGET_MODULES), bias='none', task_type='CAUSAL_LM',
            init_lora_weights=True, use_rslora=False, use_dora=False)
        model = peft.get_peft_model(self.engine.model, config, autocast_adapter_dtype=True)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        model.config.use_cache = False
        self.engine.hook.remove()
        self.engine.model = model.to('cuda:0')
        self.engine.device = 'cuda:0'
        self.engine.hook = model.register_forward_pre_hook(lambda module, inputs: self.check('forward'))

    def check(self, label):
        require(time.time() < self.plan['hard_end_unix'], 'native_wall:'+label)

    def adapter_hash(self):
        return self.native.state_hash(self.parameters)

    def offload_for_readout(self):
        self.torch.cuda.synchronize()
        state = dict(cpu_rng=self.torch.get_rng_state(),
            cuda_rng=self.torch.cuda.get_rng_state_all(), python_rng=random.getstate(),
            adapter_sha256=self.adapter_hash(), optimizer_steps=self.optimizer_steps,
            optimizer_devices={})
        self.optimizer.zero_grad(set_to_none=True)
        for parameter, values in self.optimizer.state.items():
            for key, value in values.items():
                if self.torch.is_tensor(value):
                    state['optimizer_devices'][(parameter, key)] = value.device
                    values[key] = value.to('cpu')
        self.engine.model.to('cpu')
        gc.collect()
        self.torch.cuda.empty_cache()
        return state

    def restore_after_readout(self, state):
        self.engine.model.to('cuda:0')
        for (parameter, key), device in state['optimizer_devices'].items():
            self.optimizer.state[parameter][key] = self.optimizer.state[parameter][key].to(device)
        self.engine.model.requires_grad_(False)
        self.engine.model.eval()
        self.torch.set_rng_state(state['cpu_rng'])
        self.torch.cuda.set_rng_state_all(state['cuda_rng'])
        random.setstate(state['python_rng'])
        require(self.adapter_hash() == state['adapter_sha256']
            and self.optimizer_steps == state['optimizer_steps'], 'readout_cannot_change_resident_learning')

    @staticmethod
    def verify_checkpoint(document):
        require(document['base_sha256'] == BASE_SHA256, 'checkpoint_base')
        if 'experiment' in document:
            validate_experiment(document['experiment'])
        require(sha(document['optimizer_rng_path']) == document['checkpoint_sha256']['optimizer']
                == document['checkpoint_sha256']['rng'], 'optimizer_RNG_file_binding')
        files = {path.name:sha(path) for path in sorted(Path(document['adapter_path']).iterdir()) if path.is_file()}
        require(files == document['adapter_files'] and digest(files) == document['checkpoint_sha256']['adapter'],
                'adapter_file_binding')

    def checkpoint(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=False)
        self.engine.verify_base()
        adapter_path = directory/'adapter'
        self.engine.model.save_pretrained(adapter_path, safe_serialization=True, save_embedding_layers=False)
        payload = dict(optimizer=self.optimizer.state_dict(), parameter_names=list(self.parameters),
            optimizer_steps=self.optimizer_steps, cpu_rng=self.torch.get_rng_state(),
            cuda_rng=self.torch.cuda.get_rng_state_all(), python_rng=random.getstate())
        if self.experiment is not None:
            payload['experiment'] = deepcopy(self.experiment)
        optimizer_path = directory/'optimizer_rng.pt'
        with optimizer_path.open('xb') as stream:
            self.torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        files = {path.name:sha(path) for path in sorted(adapter_path.iterdir()) if path.is_file()}
        checkpoint = dict(schema=SCHEMA, base_sha256=BASE_SHA256, adapter_path=str(adapter_path),
            adapter_files=files, adapter_state_sha256=self.adapter_hash(), optimizer_rng_path=str(optimizer_path),
            checkpoint_sha256=dict(adapter=digest(files), optimizer=sha(optimizer_path), rng=sha(optimizer_path)),
            optimizer_steps=self.optimizer_steps, created_unix=time.time())
        if self.experiment is not None:
            checkpoint['experiment'] = deepcopy(self.experiment)
        write_once(directory/'COMMIT.json', checkpoint)
        self.verify_checkpoint(checkpoint)
        return checkpoint

    def count_tokens(self, messages):
        return len(self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False))

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.check('generate')
        require(deadline_unix == self.plan['hard_end_unix'], 'generation_wall_binding')
        require(not any(parameter.requires_grad for parameter in self.engine.model.parameters()), 'readonly_generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        require(len(tokens)+max_new_tokens <= self.plan['context_limit'], 'no_generation_prefix_crop')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device='cuda:0')
        config = self.engine.transformers.GenerationConfig(do_sample=True, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id, **self.plan['decoder'])
        self.engine.model.eval()
        with self.torch.inference_mode():
            generated = self.engine.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                                                   generation_config=config)
        require(generated[0,:len(tokens)].tolist() == tokens, 'actual_prompt_prefix_unchanged')
        target = generated[0,len(tokens):].tolist()
        terminal = bool(target) and target[-1] == self.tokenizer.eos_token_id
        raw = self.tokenizer.decode(target[:-1] if terminal else target, skip_special_tokens=False,
                                    clean_up_tokenization_spaces=False)
        return dict(raw=raw, token_ids=target, terminal=terminal,
            truncated=not terminal and len(target)==max_new_tokens, prompt_tokens=len(tokens),
            prompt_token_ids_sha256=digest(tokens), adapter_state_sha256=self.adapter_hash(),
            base_sha256=BASE_SHA256, decoder=self.plan['decoder'])

    def sleep(self, new_rows, old_rows, anchors, record):
        available_old_rows = len(old_rows)
        old_rows = select_rehearsal_rows(self.plan, old_rows)
        record('SLEEP_RECIPE', dict(policy='R181_NEW_ONLY_V1' if not self.plan.get('rehearsal_presentations', 1)
            else 'LEGACY_FULL_REHEARSAL', new_presentations=16, new_rows=len(new_rows),
            available_old_rows=available_old_rows, selected_old_rows=len(old_rows), anchor_lambda=0.25))
        from gpu.orch_r108_guided_native import validate_anchor_inventory
        validate_anchor_inventory(anchors)
        require(len(anchors) == 4, 'four_broad_anchor_families')
        before = self.adapter_hash()
        steps_before = self.optimizer_steps
        exclusions = []
        if self.plan.get('presentation_version'):
            from organism_v6.orch_r125_plain_context import eligible_rows
            presentation = dict(version=self.plan['presentation_version'],
                system_prompt=self.plan['system_prompt'], birth_prompt=self.plan['birth_prompt'])
            new_rows, rejected_new = eligible_rows(new_rows, presentation)
            old_rows, rejected_old = eligible_rows(old_rows, presentation)
            exclusions = [dict(row, cohort='NEW') for row in rejected_new] + [
                dict(row, cohort='REHEARSAL') for row in rejected_old]
        from gpu.orch_r144_sleep_targets import POLICY, encode_sleep_targets
        new_rows, old_rows, encoded, rejected_targets = encode_sleep_targets(
            new_rows, old_rows, self.tokenizer, self.plan['context_limit'], encode_own)
        exclusions.extend(rejected_targets)
        record('TARGET_ELIGIBILITY', dict(version=self.plan.get('presentation_version'),
            runtime_policy=POLICY, excluded=exclusions,
            new_row_sha256=[row['source_sha256'] for row in new_rows],
            rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False))
        schedule = (presentation_schedule(new_rows, old_rows) if new_rows else
                    [('REHEARSAL', row) for row in old_rows])
        if not schedule:
            self.engine.verify_base()
            return dict(optimizer_steps=0, total_optimizer_steps=self.optimizer_steps,
                before_adapter_sha256=before, after_adapter_sha256=before,
                no_update_reason='no_eligible_child_rows', child_token_exposures=0,
                anchor_token_exposures=0, presentations={}, excluded_rows=exclusions,
                anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION')
        child_exposures, anchor_exposures = 0, 0
        presentations = {}
        for parameter in self.parameters.values():
            parameter.requires_grad_(True)
        try:
            for index, (kind, row) in enumerate(schedule):
                self.check('optimizer_update')
                require(not any(parameter.requires_grad for name,parameter in self.engine.model.named_parameters()
                    if not self.native.is_lora(name)), 'base_parameters_frozen')
                own = encoded[row['source_sha256']]
                batch = [(kind,own,0.75)]
                for family, records in sorted(anchors.items()):
                    batch.append(('ANCHOR:'+family, records[index%len(records)]['encoded'],0.0625))
                self.engine.model.train()
                self.optimizer.zero_grad(set_to_none=True)
                losses = []
                for label, sample, weight in batch:
                    self.check('microbatch')
                    inputs = self.torch.tensor([sample.input_ids], dtype=self.torch.long, device='cuda:0')
                    labels = self.torch.tensor([sample.labels], dtype=self.torch.long, device='cuda:0')
                    with self.torch.autocast(device_type='cuda', dtype=self.torch.bfloat16):
                        loss = self.engine.model(input_ids=inputs, labels=labels,
                            attention_mask=self.torch.ones_like(inputs), use_cache=False).loss
                    require(bool(self.torch.isfinite(loss)), 'finite_training_loss')
                    (loss*weight).backward()
                    count = sum(token != -100 for token in sample.labels)
                    if label.startswith('ANCHOR:'):
                        anchor_exposures += count
                    else:
                        child_exposures += count
                    losses.append(dict(kind=label, mean_loss=loss.item(), objective_weight=weight, target_tokens=count))
                require(all(parameter.grad is not None and bool(self.torch.isfinite(parameter.grad).all())
                        for parameter in self.parameters.values()), 'finite_adapter_gradients')
                self.optimizer.step()
                self.optimizer_steps += 1
                presentations[row['source_sha256']] = presentations.get(row['source_sha256'],0)+1
                record('UPDATE', dict(optimizer_step=self.optimizer_steps, losses=losses,
                    source_sha256=row['source_sha256'], finished_unix=time.time()))
        finally:
            self.engine.model.requires_grad_(False)
            self.engine.model.eval()
        self.engine.verify_base()
        after = self.adapter_hash()
        require(after != before, 'actual_LoRA_change_required')
        return dict(optimizer_steps=self.optimizer_steps-steps_before, total_optimizer_steps=self.optimizer_steps,
            before_adapter_sha256=before, after_adapter_sha256=after, frozen_base_verified=True,
            child_token_exposures=child_exposures, anchor_token_exposures=anchor_exposures,
            presentations=presentations, excluded_rows=exclusions,
            anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION')


def prepare_sleep(child, stream, journal, cycle):
    require(stream.pending is None and stream.sleep_due, 'presleep_requires_completed_experience')
    variant = child.plan.get('presleep_variant', 'free_distillation')
    if variant == 'no_distillation':
        return
    invitation_text = child.plan['compaction_invitation']
    invitation = TrainEvent(event_id=f'presleep:{cycle}', actor='environment', split='TRAIN',
        phase='presleep', episode_id='continual_stream', source_id='R124_RUNTIME_INVITATION',
        source_sha256=digest([cycle, invitation_text]), origin='TRAIN_COLLECTION', text=invitation_text)
    stream.step(child.generate, child.count_tokens, journal.record, incoming=[invitation]+journal.read_inbox())
    raw_summary = stream.history.events[-2]
    require(raw_summary.actor == 'child', 'actual_child_compaction_response')
    if raw_summary.text.strip():
        summary = replace(raw_summary, event_id=f'compaction:{cycle}', phase='compaction')
        stream.history.compact(summary, through=stream.history.frontier(len(stream.history.events)-1))
        journal.record('COMPACTION', dict(kind='CHILD_COMPACTION', state=stream.checkpoint()))
    else:
        journal.record('COMPACTION_SKIPPED', dict(cycle=cycle,
            source_sha256=raw_summary.source_sha256, reason='empty_child_summary_no_invented_replacement'))


def respond_to_presleep_inbox(child, stream, journal, cycle):
    require(stream.pending is None and stream.sleep_due, 'presleep_inbox_at_completed_response')
    known_ids = {event.event_id for event in stream.history.events}
    incoming = [event for event in journal.read_inbox() if event.event_id not in known_ids]
    if not any(event.actor == 'parent' for event in incoming):
        return False
    journal.record('PRESLEEP_INBOX_RESPONSE', dict(cycle=cycle,
        event_ids=[event.event_id for event in incoming], maximum_extra_segments=1,
        all_external_text_masked=True, additional_own_row_presentations=16))
    stream.step(child.generate, child.count_tokens, journal.record, incoming=incoming)
    return True


def finish_sleep(child, stream, journal, anchors, root, cycle):
    checkpoint_path = root/'checkpoints'/f'sleep_{cycle:06d}'
    require(not checkpoint_path.exists(), 'never_repeat_checkpointed_sleep')
    new_rows = stream.pending_rows()
    if stream.pending is not None:
        require(stream.pending == 'sleep:'+digest([row['source_sha256'] for row in new_rows]),
                'only_verified_pending_sleep_may_complete')
    receipt = child.sleep(new_rows, stream.rows[:stream.sleep_frontier], anchors, journal.record)
    checkpoint = child.checkpoint(checkpoint_path)
    require(checkpoint.get('experiment') == stream.experiment, 'stream_model_experiment_binding')
    receipt.update(status='COMPLETE', new_row_sha256=[row['source_sha256'] for row in new_rows],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], checkpoint=checkpoint, cycle=cycle)
    stream.pending = None
    stream.commit_sleep(receipt, journal.record)
    return checkpoint


def prepare_wall_extension(plan, stream, *, resume, plan_sha256):
    """Prepare a deadline-only audit record; never mutate the supplied live state."""
    from gpu.orch_r125_stream_journal import validate_wall_extension
    require(resume is True, 'wall_extension_resume_only')
    validate_plan(plan)
    authorization = validate_wall_extension(plan.get('authorized_wall_extension'))
    require(plan.get('preupdate_recovery') is None and stream.pending is None
        and stream.sleep_frontier == len(stream.rows) and stream.sleep_receipts
        and stream.sleep_receipts[-1].get('status') == 'COMPLETE', 'wall_extension_saved_sleep_boundary')
    prior = stream.checkpoint()
    require(prior['sha256'] == authorization['previous_stream_sha256']
        and stream.deadline_unix == authorization['previous_deadline_unix'], 'wall_extension_exact_prior_binding')
    expected_presentation = (dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
        birth_prompt=plan['birth_prompt']) if plan.get('presentation_version') else None)
    prompts = stream.presentation or stream.history.checkpoint()
    require(stream.segment_tokens == plan['segment_tokens']
        and stream.segments_per_sleep == plan['segments_per_sleep'] and stream.context_limit == plan['context_limit']
        and stream.presentation == expected_presentation
        and prompts['system_prompt'] == plan['system_prompt'] and prompts['birth_prompt'] == plan['birth_prompt'],
        'wall_extension_training_configuration_frozen')
    candidate = deepcopy(prior)
    candidate['state']['deadline_unix'] = authorization['new_deadline_unix']
    candidate['sha256'] = digest(candidate['state'])
    return dict(schema='R131_WALL_EXTENDED_V1', authorization=deepcopy(authorization),
                plan_sha256=plan_sha256, state=candidate)


def run(plan_path, *, resume=False):
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r125_stream_journal import StreamJournal
    plan = validate_plan(read(plan_path))
    require(resume or plan.get('authorized_wall_extension') is None, 'wall_extension_resume_only')
    root = Path(plan['root'])
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == sha(plan_path), 'admitted_plan_environment')
    if not resume:
        root.mkdir(parents=True, exist_ok=True)
    old_handler = signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError('native_wall')))
    signal.setitimer(signal.ITIMER_REAL, plan['hard_end_unix']-time.time())
    try:
        with StreamJournal(root/'stream', create=not resume) as journal:
            recovering = False
            if resume:
                state = journal.latest_checkpoint()
                stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
                verify_experiment_resume(plan, stream.experiment)
                wall_extension = (prepare_wall_extension(plan, stream, resume=resume, plan_sha256=sha(plan_path))
                    if plan.get('authorized_wall_extension') is not None else None)
                recovering = (isinstance(stream.pending, str) and stream.pending.startswith('sleep:')
                    and isinstance(plan.get('preupdate_recovery'), dict))
                require(stream.pending is None or recovering, 'unresolved_generation_or_sleep_requires_reconciliation')
                require(recovering or stream.sleep_frontier == len(stream.rows), 'resume_requires_saved_RNG_sleep_boundary')
                require(wall_extension is not None or stream.deadline_unix == plan['hard_end_unix'], 'same_resume_wall')
                matching = [read(path) for path in (root/'checkpoints').glob('*/COMMIT.json')
                    if digest(read(path)['checkpoint_sha256']) == stream.model_state_sha256]
                require(len(matching) == 1, 'one_exact_model_checkpoint_for_stream')
                require(matching[0].get('experiment') == stream.experiment, 'stream_model_experiment_binding')
                verify_experiment_resume(plan, matching[0].get('experiment'))
                child = NativeChild(plan, matching[0])
                if wall_extension is not None:
                    journal.record('WALL_EXTENDED', wall_extension)
                    stream.deadline_unix = wall_extension['authorization']['new_deadline_unix']
                if recovering:
                    from gpu.orch_r125_preupdate_recovery import recover_rng
                    recover_rng(child, stream, journal, plan['preupdate_recovery'])
                if plan.get('presentation_version'):
                    require(not recovering, 'presentation_not_during_recovery')
                    presentation = dict(version=plan['presentation_version'],
                        system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
                    if stream.presentation != presentation or stream.context_limit != plan['context_limit']:
                        stream.set_presentation(presentation, plan['context_limit'])
                        journal.record('PRESENTATION', dict(state=stream.checkpoint(),
                            plan_sha256=sha(plan_path), raw_modified=False,
                            previous_context_limit=state['document']['state']['context_limit']))
                else:
                    require(stream.presentation is None and stream.context_limit == plan['context_limit'],
                            'resume_presentation_plan_binding')
            else:
                child = NativeChild(plan)
                checkpoint = child.checkpoint(root/'checkpoints'/'initial')
                history = TrainHistory(system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
                initial_budget = dict(context_limit=plan['context_limit'],
                    segment_tokens=plan['segment_tokens'], total_generated_tokens=0,
                    segments_per_sleep=plan['segments_per_sleep'])
                history.append(TrainEvent(event_id='runtime:birth_budget', actor='environment',
                    split='TRAIN', phase='feedback', episode_id='continual_stream',
                    source_id='R125_RUNTIME_BUDGET', source_sha256=digest(initial_budget),
                    origin='TRAIN_COLLECTION', text='[budget] '+json.dumps(initial_budget, sort_keys=True)))
                stream = ContinualStream(history, context_limit=plan['context_limit'], segment_tokens=plan['segment_tokens'],
                    segments_per_sleep=2, deadline_unix=plan['hard_end_unix'],
                    model_state_sha256=digest(checkpoint['checkpoint_sha256']), allow_eviction=True,
                    experiment=experiment_binding(plan))
                if plan.get('presentation_version'):
                    stream.set_presentation(dict(version=plan['presentation_version'],
                        system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt']), plan['context_limit'])
                journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
            anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
            journal.record('LOADED', dict(pid=os.getpid(), runtime=child.engine.runtime,
                base_sha256=BASE_SHA256, adapter_sha256=child.adapter_hash(), optimizer_steps=child.optimizer_steps,
                anchors=anchor_receipt, resume=resume, loaded_unix=time.time()))
            completed_sleeps = len(stream.sleep_receipts)
            if recovering:
                completed_sleeps += 1
                checkpoint = finish_sleep(child, stream, journal, anchors, root, completed_sleeps)
            if plan.get('think_act_learn') is not None:
                from gpu.orch_r184_think_act_learn import run_loop
                return run_loop(child, stream, journal, anchors, plan, root, plan_path, completed_sleeps)
            for readout_cycle in range(completed_sleeps+1):
                readout_dispatch = root/'readouts'/f'{readout_name(plan, readout_cycle)}_DISPATCH.json'
                if not readout_dispatch.exists():
                    directory = 'initial' if readout_cycle == 0 else f'sleep_{readout_cycle:06d}'
                    fresh_readout(child, plan_path, read(root/'checkpoints'/directory/'COMMIT.json'), readout_cycle)
            while time.time() < plan['hard_end_unix']:
                stream.step(child.generate, child.count_tokens, journal.record, incoming=journal.read_inbox())
                if not stream.sleep_due:
                    continue
                cycle = completed_sleeps+1
                prepare_sleep(child, stream, journal, cycle)
                respond_to_presleep_inbox(child, stream, journal, cycle)
                new_rows = stream.pending_rows()
                pending = stream.checkpoint()
                pending['state']['pending'] = 'sleep:'+digest([row['source_sha256'] for row in new_rows])
                pending['sha256'] = digest(pending['state'])
                journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
                checkpoint = finish_sleep(child, stream, journal, anchors, root, cycle)
                completed_sleeps = cycle
                fresh_readout(child, plan_path, checkpoint, cycle)
                if plan['max_sleeps'] is not None and completed_sleeps >= plan['max_sleeps']:
                    stream.step(child.generate, child.count_tokens, journal.record, incoming=journal.read_inbox())
                    journal.record('TERMINAL', dict(status='ENGINEERING_SMOKE_COMPLETE',
                        sleeps=completed_sleeps, optimizer_steps=child.optimizer_steps,
                        continued_after_sleep=True, retained_learning_claim=False, finished_unix=time.time()))
                    return
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    run(args.plan, resume=args.resume)
