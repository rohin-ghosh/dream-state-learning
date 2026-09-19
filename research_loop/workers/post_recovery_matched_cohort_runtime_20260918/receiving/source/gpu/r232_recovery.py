"""Bounded dead-pair context recovery; immutable previous runtime retained."""

from copy import deepcopy
import gc
import os
from pathlib import Path
import random
import time
from types import FunctionType, SimpleNamespace

from gpu import r205_runtime as runtime
from gpu import r232_runtime as frozen
from gpu import orch_r125_continual_native as native
from gpu import orch_r125_stream_journal as journal_module
from gpu.r231_runtime import receiving_command
from organism_v6.orch_r125_continual_stream import digest, require


POLICY = 'R232_DEAD_PAIR_CONTEXT_RECOVERY_V1'
CONTEXT = 6144
OLD_CONTEXT = 4096
ROOTS = {
    0: Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918'),
    1: Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918'),
}
DEVICES = {
    0: ('GPU-c57b2860-9ba6-74ee-876b-4fa22a10366e', '0000:4f:00.0'),
    1: ('GPU-02917283-de83-a2c7-db03-272dca482162', '0000:52:00.0'),
}


def epoch_document(checkpoint, evidence_sha256):
    previous = checkpoint['state']
    require(previous['context_limit'] == OLD_CONTEXT and previous.get('presentation') is None,
        'exact_legacy_budget_only')
    require(previous['pending'] is None and previous['sleep_frontier'] == len(previous['rows'])
        and previous['sleep_receipts'][-1]['status'] == 'COMPLETE', 'coherent_saved_sleep_only')
    current = deepcopy(checkpoint)
    current['state']['context_limit'] = CONTEXT
    current['sha256'] = digest(current['state'])
    return dict(policy=POLICY, previous_sha256=checkpoint['sha256'], state=current,
        evidence_sha256=evidence_sha256, new_runtime_epoch=True, no_gap_claim=False)


class EpochJournalMixin:
    def _advance(self, state, kind, document):
        if kind != 'R232_RECOVERY_CONTEXT':
            return super()._advance(state, kind, document)
        require(state['latest'] is not None and state['request'] is None
            and state['response'] is None and state['sleep_request'] is None, 'no_inflight_recovery')
        require(len(document['evidence_sha256']) == 64, 'bound_recovery_evidence')
        previous = state['latest']['document']
        require(document == epoch_document(previous, document['evidence_sha256']),
            'context_only_exact_state_transition')
        state['latest'] = self._checkpoint(document['state'])


class LearnerJournal(EpochJournalMixin, journal_module.StreamJournal):
    pass


class FrozenJournal(EpochJournalMixin, frozen.FrozenJournal):
    pass


def memory_probe(child, checkpoint, output, training):
    torch = child.torch
    saved = dict(cpu=torch.get_rng_state(), cuda=torch.cuda.get_rng_state_all(), python=random.getstate())
    adapter_before = child.adapter_hash()
    optimizer_before = runtime.optimizer_digest(child.optimizer, torch)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    target_count = child.plan['segment_tokens']
    token = child.tokenizer.encode(' arithmetic', add_special_tokens=False)[0]
    input_ids = [token] * CONTEXT
    labels = [-100] * (CONTEXT - target_count) + [token] * target_count
    sample = SimpleNamespace(input_ids=input_ids, labels=labels, target_ids=[token] * target_count)
    inputs = torch.tensor([input_ids], device='cuda:0', dtype=torch.long)
    targets = torch.tensor([labels], device='cuda:0', dtype=torch.long)
    try:
        if training:
            child.engine.model.train()
            for parameter in child.parameters.values():
                parameter.requires_grad_(True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = native.sleep_causal_loss(child.engine.model, inputs, targets, torch.ones_like(inputs),
                    implementation=native.sleep_loss_implementation(child.plan), sample=sample)
            require(bool(torch.isfinite(loss)), 'finite_receiving_memory_probe')
            loss.backward()
            del loss
        else:
            with torch.no_grad(), torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                result = child.engine.model(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                    use_cache=True, logits_to_keep=1)
            del result
        torch.cuda.synchronize()
        peak = torch.cuda.max_memory_allocated()
        reserved = torch.cuda.max_memory_reserved()
        total = torch.cuda.get_device_properties(0).total_memory
        require(total - reserved >= 256 * 1024**2, 'receiving_memory_margin_at_least_256MiB')
    finally:
        child.optimizer.zero_grad(set_to_none=True)
        child.engine.model.requires_grad_(False)
        child.engine.model.eval()
        del inputs, targets
        gc.collect()
        torch.cuda.empty_cache()
        torch.set_rng_state(saved['cpu'])
        torch.cuda.set_rng_state_all(saved['cuda'])
        random.setstate(saved['python'])
    require(child.adapter_hash() == adapter_before == checkpoint['adapter_state_sha256']
        and child.optimizer_steps == checkpoint['optimizer_steps']
        and runtime.optimizer_digest(child.optimizer, torch) == optimizer_before, 'probe_no_saved_state_change')
    require(torch.equal(torch.get_rng_state(), saved['cpu'])
        and all(torch.equal(before, after) for before, after in zip(saved['cuda'], torch.cuda.get_rng_state_all()))
        and random.getstate() == saved['python'], 'probe_RNG_restored')
    native.write_once(output, dict(policy=POLICY, passed=True, measured_unix=time.time(),
        context_limit=CONTEXT, microbatch=1, target_tokens=target_count, nonreentrant_checkpointing=True,
        training_forward_backward_only=training, inference_full_context_KV=not training,
        peak_allocated_bytes=peak, peak_reserved_bytes=reserved, total_bytes=total,
        adapter_sha256=adapter_before, optimizer_steps=child.optimizer_steps,
        optimizer_sha256=optimizer_before, saved_RNG_restored=True, optimizer_step_calls=0,
        synthetic_probe_not_child_training=True, checkpoint_sha256=checkpoint['checkpoint_sha256']))


def main():
    runtime.DEVICES = DEVICES
    runtime.TRIALS += ('R231_BASE_CURRICULUM_FROM_BIRTH',)
    runtime.MODULE = 'gpu.r232_recovery'
    old_install, old_command = runtime.install_runtime, runtime.contained_command
    verifier = runtime.verify_devices
    require(verifier.__code__.co_consts.count(2524) == 1, 'one_exact_owner_seam')
    runtime.verify_devices = FunctionType(verifier.__code__.replace(co_consts=tuple(
        1352 if value == 2524 else value for value in verifier.__code__.co_consts)), verifier.__globals__)

    def install(plan):
        physical = plan['physical']
        require(physical in ROOTS and Path(plan['root']) == ROOTS[physical] / 'raw'
            and plan['context_limit'] == CONTEXT, 'only_dead_pair_roots_and_identical_context')
        require(all(scope.get('learn_row_policy') == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
            for scope in (plan, plan['think_act_learn'])), 'no_semantic_exclusions')
        frozen.INITIAL = native.read(ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json')
        runtime.receive_peer = lambda driver: None
        runtime.compact_birth = lambda stream, journal: journal.record('R232_RECOVERY_RESUME',
            dict(policy=POLICY, state_sha256=stream.checkpoint()['sha256'], birth_recompacted=False,
                new_runtime_epoch=True, no_gap_claim=False, resumed_unix=time.time()))
        old_install(plan)
        base_child = frozen.FrozenChild if physical == 1 else native.NativeChild

        class ReceivingChild(base_child):
            def __init__(self, received_plan, checkpoint=None):
                require(checkpoint is not None, 'never_cold_start_or_initial_fallback')
                binding = native.read(Path(received_plan['source_root']).parent / 'control/PRESERVATION.json')
                require(checkpoint == binding['checkpoint'], 'latest_coherent_model_no_rollback')
                super().__init__(received_plan, checkpoint)
                memory_probe(self, checkpoint, Path(received_plan['source_root']).parent / 'control/MEMORY.json',
                    training=physical == 0)

        native.NativeChild = ReceivingChild
        if physical == 1:
            native.ContinualStream = frozen.FrozenStream
        journal_module.StreamJournal = FrozenJournal if physical == 1 else LearnerJournal

    def command(config_path, mode):
        from gpu.orch_r125_continual_guard import validate
        config, plan = validate(config_path)
        require(config['resume'] is True and Path(plan['root']) == ROOTS[plan['physical']] / 'raw',
            'dead_pair_same_identity_resume_only')
        return receiving_command(old_command(config_path, mode), mode, plan['hard_end_unix'], time.time())

    runtime.install_runtime, runtime.contained_command = install, command
    runtime.main()


if __name__ == '__main__':
    main()
