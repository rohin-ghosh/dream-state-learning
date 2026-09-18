"""CPU-only preparation of the explicitly authorized dead-pair epoch."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from gpu import orch_r125_continual_native as native
from gpu import r232_recovery as recovery
from gpu import r232_runtime as frozen
from organism_v6.orch_r125_continual_stream import ContinualStream, digest, require


OLD_PIDS = {0: (62947, '7193467'), 1: (71878, '7257633')}
BLOCKS = {
    0: (169, '32a03be3bea59237ac0993c7b720530e1459c9402192abeaf03ee43b58a44322', 3637),
    1: (71, 'fc9ae9a99e66a21bec2eb034228f0d7a2384d7148a68001e14fae94406bb02db', 3600),
}


def inventory(root):
    return {str(path.relative_to(root)): native.sha(path) for path in sorted(root.rglob('*'))
        if path.is_file() and not path.is_symlink()}


def main():
    physical = int(sys.argv[1])
    require(physical in (0, 1), 'only_assigned_pair_devices')
    root = recovery.ROOTS[physical]
    epoch = root / 'recovery_6144'
    control = epoch / 'control'
    source = epoch / 'source'
    control.mkdir()
    pid, ticks = OLD_PIDS[physical]
    require(not Path('/proc', str(pid)).exists(), 'old_native_must_be_dead_not_reused')
    old_plan = native.read(root / 'control/PLAN.json')
    old_guard = native.read(root / 'control/GUARD.json')
    exit_receipt = native.read(root / 'control/EXIT.json')
    require(exit_receipt['exit_code'] == 1, 'actual_failed_exit_preserved')
    require(time.time() < old_plan['hard_end_unix'] - 300, 'existing_finite_wall_not_extended')
    birth_sha = native.sha(root / 'BIRTH_PROMPT.txt')
    require(birth_sha == '7362d19a950779633067c81bacd0f0942e4243bbd62cf029463b61c264d66191',
        'original_six_paragraph_birth_unchanged')
    block_index, block_sha, token_count = BLOCKS[physical]
    block = native.read(root / 'raw/stream/records' / f'{block_index:020d}.json')
    require(block['sha256'] == block_sha and block['document']['before_tokens'] == token_count
        and block['kind'] == 'R203_CONTEXT_BUDGET_BLOCKED', 'observed_failure_exact_binding')
    gpu = subprocess.check_output(['nvidia-smi', '-i', str(physical),
        '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip()
    require(gpu.split(',')[0].strip() == recovery.DEVICES[physical][0]
        and int(gpu.split(',')[1]) == 0, 'assigned_GPU_idle_before_preparation')
    frozen.INITIAL = native.read(recovery.ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json')
    journal_class = recovery.FrozenJournal if physical == 1 else recovery.LearnerJournal
    with journal_class(root / 'raw/stream') as journal:
        coherent = journal.latest_checkpoint()['document']
        require(coherent['state']['pending'] is None and coherent['state']['sleep_frontier']
            == len(coherent['state']['rows']) == 6, 'exact_saved_six_rows_no_inflight_drop')
        models = [native.read(path) for path in (root / 'raw/checkpoints').glob('*/COMMIT.json')
            if digest(native.read(path)['checkpoint_sha256']) == coherent['state']['model_state_sha256']]
        require(len(models) == 1 and models[0]['optimizer_steps'] == (96 if physical == 0 else 0),
            'latest_completed_model_never_initial_rollback')
        checkpoint = models[0]
        native.NativeChild.verify_checkpoint(checkpoint)
        raw_before = inventory(root / 'raw')
        if not (epoch / 'preserved_raw').exists():
            shutil.copytree(root / 'raw', epoch / 'preserved_raw', copy_function=shutil.copy2)
        require(inventory(epoch / 'preserved_raw') == raw_before, 'whole_raw_state_exact_private_preservation')
        native.write_once(control / 'PRESERVATION.json', dict(policy=recovery.POLICY,
            preserved_unix=time.time(), old_pid=pid, old_start_ticks=ticks, actual_pid_absent=True,
            old_exit=exit_receipt, block_index=block_index, block_sha256=block_sha,
            block_state_sha256=block['document']['state']['sha256'], actual_protected_tokens=token_count,
            old_plan_sha256=native.sha(root / 'control/PLAN.json'), old_guard_sha256=native.sha(root / 'control/GUARD.json'),
            checkpoint=checkpoint, coherent_state=coherent, raw_inventory=raw_before,
            birth_sha256=birth_sha, no_signals_sent=True, no_gap_claim=False))
        plan = deepcopy(old_plan)
        plan['context_limit'] = recovery.CONTEXT
        plan['source_root'] = str(source)
        plan['startup_context']['path'] = str(source / Path(old_plan['startup_context']['path']).relative_to(old_plan['source_root']))
        require(native.sha(plan['startup_context']['path']) == native.sha(old_plan['startup_context']['path']),
            'relocated_startup_pin_identical_bytes')
        native.validate_plan(plan)
        normalized = deepcopy(plan)
        normalized['context_limit'] = old_plan['context_limit']
        normalized['source_root'] = old_plan['source_root']
        normalized['startup_context']['path'] = old_plan['startup_context']['path']
        require(normalized == old_plan, 'only_context_and_versioned_source_change')
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(plan['model_dir'], local_files_only=True)
        def count(messages):
            return len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
        prospective = recovery.epoch_document(coherent, native.sha(control / 'PRESERVATION.json'))
        source_checks = []
        for label, candidate in [('coherent', prospective['state']), ('blocked', block['document']['state'])]:
            stream = ContinualStream.restore(candidate, expected_sha256=candidate['sha256'])
            stream.context_limit = recovery.CONTEXT
            before = stream.checkpoint()
            records = []
            rendered = stream.compact_for_prompt(count, lambda kind, document: records.append(kind),
                threshold=recovery.CONTEXT * 3 // 4, protected_from=block['document']['protected_from'])
            require(stream.checkpoint()['state']['history']['working_state'] == before['state']['history']['working_state']
                and stream.rows == before['state']['rows'], 'all_working_state_and_raw_targets_preserved')
            require(rendered.token_count < 4608, 'actual_protected_case_fits_identical_budget')
            source_checks.append(dict(source=label, before_sha256=before['sha256'],
                after_sha256=stream.checkpoint()['sha256'], prompt_tokens=rendered.token_count,
                compaction_records=records, protected_text_dropped=False))
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(source) + ':' + str(epoch))
        with (control / 'CPU.log').open('x') as output:
            tested = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_recovery', 'test_frozen'],
                cwd=epoch, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=60)
        require(tested.returncode == 0, 'focused_recovery_and_frozen_tests_pass')
        builder = native.read(epoch / 'BUILDER_LOG_RECEIPT.json')
        require(builder['logged'] is True, 'dated_builder_log_required')
        pins = {str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}
        native.write_once(control / 'PLAN.json', plan)
        native.write_once(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins,
            log_sha256=native.sha(control / 'CPU.log'), actual_protected_state_checks=source_checks,
            builder_log=builder, no_GPU_model_calls=True,
            receiving_memory_probe_required_before_LOADED=True))
        native.write_once(control / 'ALLOCATION.json', dict(physical=physical, gpu_uuid=plan['gpu_uuid'],
            declared_unix=time.time(), builder_entry_logged=True, cpu_tests_passed=True,
            plan_sha256=native.sha(control / 'PLAN.json'), cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
            cpu_receipt_sha256=native.sha(control / 'RECEIVING_CPU.json')))
        guard = deepcopy(old_guard)
        guard.update(attempt_dir=str(control), resume=True, plan_path=str(control / 'PLAN.json'),
            plan_sha256=native.sha(control / 'PLAN.json'), source_pins=pins,
            allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=native.sha(control / 'ALLOCATION.json'))
        native.write_once(control / 'GUARD.json', guard)
        from gpu.orch_r125_continual_guard import validate
        validate(control / 'GUARD.json')
        require(not Path('/proc', str(pid)).exists(), 'old_native_still_absent')
        transition = journal.record('R232_RECOVERY_CONTEXT', prospective)
        require(journal.latest_checkpoint()['document'] == prospective['state'], 'exact_epoch_committed')
        native.write_once(control / 'EPOCH.json', dict(transition=transition,
            previous_state_sha256=coherent['sha256'], new_state_sha256=prospective['state']['sha256'],
            same_model_sha256=coherent['state']['model_state_sha256'], context_limit=recovery.CONTEXT,
            hard_end_unix=plan['hard_end_unix'], prior_failures_preserved=True, new_runtime_epoch=True))
    with journal_class(root / 'raw/stream') as verified:
        require(verified.latest_checkpoint()['document'] == prospective['state'], 'durable_epoch_replay')
    print(json.dumps(dict(status='CPU_READY_NOT_LOADED', physical=physical,
        context_limit=recovery.CONTEXT, actual_state_checks=source_checks,
        optimizer_steps=checkpoint['optimizer_steps'], epoch_sha256=native.sha(control / 'EPOCH.json'))))


if __name__ == '__main__':
    main()
