"""Native TRAIN-only continuous generation, child compaction and LoRA sleep."""

import argparse
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
from organism_v6.orch_r125_continual_stream import ContinualStream, digest, require


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
    'Your inherited model is frozen Qwen2.5-7B-Instruct. A rank-8 LoRA adapter is the only '
    'trainable part. During sleep, your actual generated tokens are used as targets, with '
    'earlier input, parent messages and runtime notices masked. Ordinary competent base '
    'examples are mixed in as anchors. Training can change your behaviour, but improvement '
    'is not guaranteed and repeating an error can reinforce it. Your general purpose is '
    'to turn available abilities into useful behaviours and learn from your experience. '
    'You will see token and context costs. When context is full, oldest visible history '
    'may be explicitly removed; raw records are preserved. Before sleep you can distill '
    'what you want to carry forward. You currently have a text stream and a human-message '
    'inbox, not a shell or independent GPU-experiment tools. Do not claim to have run '
    'an experiment or observed a result that the environment did not return.'
)
COMPACTION_INVITATION = 'You are about to sleep. Distill from your history what you want to carry forward.'


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
    require(plan['system_prompt'] == SYSTEM and plan['birth_prompt'] == BIRTH
            and plan['compaction_invitation'] == COMPACTION_INVITATION, 'exact_posted_prompts')
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1
            and plan['anchor_lambda'] == 0.25, 'declared_presentation_and_anchor_schedule')
    require(plan['seed'] == 0 and plan['segments_per_sleep'] == 2, 'initial_native_schedule')
    require(type(plan['segment_tokens']) is int and 1 <= plan['segment_tokens'] <= 1024,
            'bounded_native_segment')
    require(type(plan['context_limit']) is int and plan['segment_tokens'] < plan['context_limit'] <= 8192,
            'bounded_native_context')
    require(plan['max_sleeps'] is None or type(plan['max_sleeps']) is int and plan['max_sleeps'] > 0,
            'explicit_smoke_or_long_life')
    require(type(plan['physical']) is int and 0 <= plan['physical'] < 8
            and plan['gpu_uuid'].startswith('GPU-'), 'explicit_gpu_identity')
    require(time.time() < plan['hard_end_unix'] <= plan['lease_end_unix']-120, 'within_lease_wall')
    require(plan['decoder'] == dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05,
                                   no_repeat_ngram_size=16), 'posted_decoder')
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
    require(not set(tokenizer.all_special_ids).intersection(visible), 'no_special_token_target_injection')
    require(tokenizer.decode(visible, skip_special_tokens=False,
                clean_up_tokenization_spaces=False) == row['target'], 'native_target_roundtrip')
    require(len(prefix)+len(target) <= context_limit, 'whole_source_no_training_trim')
    return EncodedRow(prefix+target, (-100,)*len(prefix)+target, target)


def presentation_schedule(new_rows, old_rows):
    require(new_rows, 'new_rows_required')
    return [('NEW', row) for unused in range(16) for row in new_rows] + [
        ('REHEARSAL', row) for row in old_rows]


def fresh_readout(child, plan_path, checkpoint, cycle):
    output = Path(child.plan['root'])/'readouts'/f'sleep_{cycle:06d}'
    output.parent.mkdir(parents=True, exist_ok=True)
    status_path = output.parent/f'sleep_{cycle:06d}_DISPATCH.json'
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
        with (output.parent/f'sleep_{cycle:06d}.log').open('x') as log:
            process = subprocess.Popen(command, cwd=child.plan['source_root'],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
            status = process.wait(timeout=max(1, child.plan['hard_end_unix']-time.time()-15))
        require(status == 0 and (output/'COMPLETE.json').is_file(), 'fresh_readout_incomplete')
    except Exception as error:
        write_once(output.parent/f'sleep_{cycle:06d}_FAILED.json',
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
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_bound_GPU_environment')
        tokenizer = source.native.load_local_tokenizer(plan['model_dir'])
        if checkpoint:
            self.verify_checkpoint(checkpoint)
        options = SimpleNamespace(model_dir=plan['model_dir'], device='cuda:0',
            phase='readout' if checkpoint else 'train', expected_base_sha256=BASE_SHA256,
            adapter_dir=checkpoint['adapter_path'] if checkpoint else None)
        self.engine = source.Engine(options, tokenizer, check=self.check)
        self.torch, self.tokenizer = self.engine.torch, tokenizer
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
            require(payload['parameter_names'] == list(self.parameters), 'exact_optimizer_parameter_order')
            self.optimizer.load_state_dict(payload['optimizer'])
            self.optimizer_steps = payload['optimizer_steps']
            self.torch.set_rng_state(payload['cpu_rng'])
            self.torch.cuda.set_rng_state_all(payload['cuda_rng'])
            random.setstate(payload['python_rng'])
            require(self.adapter_hash() == checkpoint['adapter_state_sha256'], 'restored_adapter_state')
        else:
            random.seed(plan['seed'])
            self.torch.manual_seed(plan['seed'])
            self.torch.cuda.manual_seed_all(plan['seed'])
        self.engine.model.requires_grad_(False)
        self.engine.model.eval()

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
        from gpu.orch_r108_guided_native import validate_anchor_inventory
        validate_anchor_inventory(anchors)
        require(len(anchors) == 4, 'four_broad_anchor_families')
        before = self.adapter_hash()
        steps_before = self.optimizer_steps
        schedule = presentation_schedule(new_rows, old_rows)
        encoded = {row['source_sha256']:encode_own(row, self.tokenizer, self.plan['context_limit'])
                   for row in new_rows+old_rows}
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
            presentations=presentations, anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION')


def run(plan_path, *, resume=False):
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r125_stream_journal import StreamJournal
    plan = validate_plan(read(plan_path))
    root = Path(plan['root'])
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == sha(plan_path), 'admitted_plan_environment')
    old_handler = signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError('native_wall')))
    signal.setitimer(signal.ITIMER_REAL, plan['hard_end_unix']-time.time())
    try:
        with StreamJournal(root/'stream', create=not resume) as journal:
            if resume:
                state = journal.latest_checkpoint()
                stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
                require(stream.pending is None, 'unresolved_generation_or_sleep_requires_reconciliation')
                require(stream.sleep_frontier == len(stream.rows), 'resume_requires_saved_RNG_sleep_boundary')
                require(stream.deadline_unix == plan['hard_end_unix'], 'same_resume_wall')
                matching = [read(path) for path in (root/'checkpoints').glob('*/COMMIT.json')
                    if digest(read(path)['checkpoint_sha256']) == stream.model_state_sha256]
                require(len(matching) == 1, 'one_exact_model_checkpoint_for_stream')
                child = NativeChild(plan, matching[0])
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
                    model_state_sha256=digest(checkpoint['checkpoint_sha256']), allow_eviction=True)
                journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
            anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
            journal.record('LOADED', dict(pid=os.getpid(), runtime=child.engine.runtime,
                base_sha256=BASE_SHA256, adapter_sha256=child.adapter_hash(), optimizer_steps=child.optimizer_steps,
                anchors=anchor_receipt, resume=resume, loaded_unix=time.time()))
            completed_sleeps = len(stream.sleep_receipts)
            readout_dispatch = root/'readouts'/f'sleep_{completed_sleeps:06d}_DISPATCH.json'
            if not readout_dispatch.exists():
                fresh_readout(child, plan_path, matching[0] if resume else checkpoint, completed_sleeps)
            while time.time() < plan['hard_end_unix']:
                stream.step(child.generate, child.count_tokens, journal.record, incoming=journal.read_inbox())
                if not stream.sleep_due:
                    continue
                cycle = completed_sleeps+1
                invitation = TrainEvent(event_id=f'presleep:{cycle}', actor='environment', split='TRAIN',
                    phase='presleep', episode_id='continual_stream', source_id='R124_RUNTIME_INVITATION',
                    source_sha256=digest([cycle,COMPACTION_INVITATION]), origin='TRAIN_COLLECTION', text=COMPACTION_INVITATION)
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
                new_rows = stream.pending_rows()
                old_rows = stream.rows[:stream.sleep_frontier]
                pending = stream.checkpoint()
                pending['state']['pending'] = 'sleep:'+digest([row['source_sha256'] for row in new_rows])
                pending['sha256'] = digest(pending['state'])
                journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
                receipt = child.sleep(new_rows, old_rows, anchors, journal.record)
                checkpoint = child.checkpoint(root/'checkpoints'/f'sleep_{cycle:06d}')
                receipt.update(status='COMPLETE', new_row_sha256=[row['source_sha256'] for row in new_rows],
                    checkpoint_sha256=checkpoint['checkpoint_sha256'], checkpoint=checkpoint, cycle=cycle)
                stream.commit_sleep(receipt, journal.record)
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
