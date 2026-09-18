"""CPU-only source/provenance preparation for one native cold-start learner."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from birth_spec import POLICY, STAGE0_OBJECT, TRIAL, extract_birth


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
CONTROL = ROOT / 'control'
DEVICE = 'GPU-c57b2860-9ba6-74ee-876b-4fa22a10366e'
ANCHORS = Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, indent=2, sort_keys=True)
        output.write('\n')


def main():
    os.umask(0o077)
    assert ROOT == Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918')
    assert not CONTROL.exists() or not any(CONTROL.iterdir())
    assert not (ROOT / 'raw').exists() or not any((ROOT / 'raw').iterdir())
    inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
                                         '--format=csv,noheader,nounits'], text=True)
    assert '0, ' + DEVICE + ', 0' in inventory.splitlines()
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                    '--format=csv,noheader,nounits'], text=True)
    assert DEVICE not in apps
    package = json.loads((ROOT / 'SOURCE_PACKAGE.json').read_bytes())
    assert all(sha(ROOT / name) == expected for name, expected in package['files'].items())
    birth = extract_birth((ROOT / 'BIRTH_SPEC_SOURCE.md').read_bytes())
    assert birth == (ROOT / 'BIRTH_PROMPT.txt').read_text() == (SOURCE / 'context/BIRTH_R231.txt').read_text()
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.astra_pchain2_native import load_local_tokenizer
    from gpu.orch_r184_think_act_learn import validate_config
    template = json.loads((ROOT / 'STANDARD_PLAN_TEMPLATE.json').read_bytes())
    hard_end = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc).timestamp()
    reservation_end = datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc).timestamp()
    assert time.time() + 300 < hard_end < reservation_end - 120
    CONTROL.mkdir(mode=0o700, exist_ok=True)
    (ROOT / 'raw').mkdir(mode=0o700, exist_ok=True)
    executor = dict(schema='R205_NO_EXECUTOR_V1', executed=False,
          reason='Stage0 is shown arithmetic/prose, not code execution; no executor is connected.')
    if (ROOT / 'NO_EXECUTOR.json').exists():
        assert json.loads((ROOT / 'NO_EXECUTOR.json').read_bytes()) == executor
    else:
        write(ROOT / 'NO_EXECUTOR.json', executor)
    config = dict(schema='R184_THINK_ACT_LEARN_V1', trial_id=TRIAL,
        reflection_policy='explicit', think_segments=1,
        cpu_gate_root=str(ROOT), cpu_gate_sha256=sha(ROOT / 'NO_EXECUTOR.json'),
        continuity_policy='R193_CONTINUITY_V1', judgment_policy='R198_JUDGMENT_FIRST_V1',
        stage_boundary_policy='R203_STAGE_BOUNDARIES_V1',
        think_continuation_policy='R204_EXPLICIT_THINK_CONTINUATION_V1',
        console_reply_policy='R205_CONSOLE_REPLY_ACT_V1',
        pinned_messages_policy='R206_VERBATIM_ROHIN_MESSAGES_V1', learn_row_policy=POLICY,
        environment_facts='You are a newly BASE-born R231 learner with a new private adapter, '
            'no inherited C2 adapter, optimizer or conversation. Stage0 is small checked arithmetic. '
            'Your actual Astra parent is scheduled each cycle; only delivered messages count. '
            'There is no code executor, peer or game connected. Write your real calculation and check '
            'in English, not code that would print it. No semantic exclusion is applied to authentic '
            'child rows. This environment context is masked, not a child target. Initial object: ' + STAGE0_OBJECT)
    plan = dict(schema=template['schema'], base_sha256=template['base_sha256'],
        model_dir=template['model_dir'], anchors=str(ANCHORS), source_root=str(SOURCE), root=str(ROOT / 'raw'),
        system_prompt=template['system_prompt'], birth_prompt=birth,
        startup_context=dict(version='R127_STARTUP_V1', path=str(SOURCE / 'context/BIRTH_R231.txt'),
                             sha256=sha(SOURCE / 'context/BIRTH_R231.txt')),
        decoder=template['decoder'], seed=231180, physical=0, gpu_uuid=DEVICE,
        context_limit=4096, segment_tokens=512, segments_per_sleep=2, max_sleeps=None,
        new_presentations=16, rehearsal_presentations=0, anchor_lambda=0.25,
        compaction_invitation=template['compaction_invitation'],
        sleep_loss_impl='MASKED_CAUSAL_CE_V1', readout_revision=1,
        hard_end_unix=hard_end, lease_end_unix=reservation_end, learn_row_policy=POLICY,
        think_act_learn=config)
    native.validate_plan(plan)
    validate_config(config)
    assert Path(plan['model_dir']).is_dir()
    tokenizer = load_local_tokenizer(plan['model_dir'])
    anchors, receipt = build_inventory(ANCHORS, tokenizer, plan['context_limit'])
    assert set(anchors) == {'code', 'math', 'simulated_tools', 'concise_answer'}
    write(CONTROL / 'ANCHOR_CPU.json', receipt)
    write(CONTROL / 'PLAN.json', plan)
    write(ROOT / 'LEASE.json', dict(schema='R231_CONSERVATIVE_OPERATOR_WINDOW_V1',
        hard_end_unix=hard_end, lease_end_unix=reservation_end, physical_lease_changed=False,
        provider_exact_expiry_claimed=False, physical_lease_date_reported='2026-10-01',
        authorization='Main explicit active ovx4 GPU0 allocation, 2026-09-18 09:55UTC',
        note='lease_end_unix is a conservative operator horizon, not a claimed exact provider expiry.'))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                       PYTHONPATH=os.pathsep.join((str(ROOT), str(SOURCE))))
    with (CONTROL / 'CPU.log').open('x') as output:
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_birth_spec'],
                                 cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=60)
    assert result.returncode == 0
    import torch
    assert not torch.cuda.is_initialized()
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    builder = json.loads((ROOT / 'BUILDER_LOG_RECEIPT.json').read_bytes())
    assert builder['logged'] is True
    write(CONTROL / 'RECEIVING_CPU.json', dict(passed=True, tests=7, source_pins=pins,
        log_sha256=sha(CONTROL / 'CPU.log'), birth_sha256=sha(ROOT / 'BIRTH_PROMPT.txt'),
        synthetic_compaction_and_restore_pin_test=True, no_GPU_model_calls=True,
        anchor_inventory=receipt, builder_log=builder,
        cold_start=True, resume=False, initial_optimizer_expected=0, inherited_history=False,
        memory_configuration=dict(context_limit=4096, segment_tokens=512, microbatch=1,
            gradient_checkpointing=True, use_reentrant=False, rank=8, learning_rate=3e-5,
            new_presentations=16, anchor_lambda=0.25, empirical_GPU_memory_fit='not_yet_loaded')))
    write(CONTROL / 'ALLOCATION.json', dict(physical=0, gpu_uuid=DEVICE, declared_unix=time.time(),
        builder_entry_logged=True, cpu_tests_passed=True, plan_sha256=sha(CONTROL / 'PLAN.json'),
        cpu_receipt_path=str(CONTROL / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(CONTROL / 'RECEIVING_CPU.json')))
    guard = dict(schema='R125_CONTINUAL_GUARD_V1', host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        attempt_dir=str(CONTROL), copy_raw=str(ROOT / 'raw'), resume=False,
        plan_path=str(CONTROL / 'PLAN.json'), plan_sha256=sha(CONTROL / 'PLAN.json'),
        lease_path=str(ROOT / 'LEASE.json'), lease_sha256=sha(ROOT / 'LEASE.json'),
        hard_end_unix=hard_end, next_reserved_unix=reservation_end, source_pins=pins,
        allocation_path=str(CONTROL / 'ALLOCATION.json'), allocation_sha256=sha(CONTROL / 'ALLOCATION.json'))
    write(CONTROL / 'GUARD.json', guard)
    from gpu.orch_r125_continual_guard import validate
    validate(CONTROL / 'GUARD.json')
    print(json.dumps(dict(status='CPU_READY_COLD_BIRTH_NOT_LOADED', source_files=len(pins),
        plan_sha256=sha(CONTROL / 'PLAN.json'), CPU_sha256=sha(CONTROL / 'RECEIVING_CPU.json'),
        birth_sha256=sha(ROOT / 'BIRTH_PROMPT.txt'), physical=0, gpu_uuid=DEVICE,
        hard_end_utc=datetime.fromtimestamp(hard_end, timezone.utc).isoformat())))


if __name__ == '__main__':
    main()
