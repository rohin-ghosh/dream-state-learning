"""Rohin119 independent gen1 GRID elicitation, no shared learner or optimizer."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import orch_r119_grid_async_parent as mailbox
import orch_r119_grid_lease_budget as budget


OLD = Path('/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2')
CLOSURE_SHA = '03a2f241f2a043da9de28d9fc6d91fa7dc240b7ce6ef9fa08b2ff2bd92face9d'
CHECKPOINT = Path('/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1/generation_000000/sleep/checkpoint/CHECKPOINT.json')
CHECKPOINT_SHA = '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'
CLOCK = Path('/localhome/local-rohing/orch_r119_lease_continuation_20260915/CLOCK.json')
CLOCK_SHA = 'a1aa51349c1784ec9f78e6411912576be43b55942c5fcdf1858ca391fd81c510'
ERA = 'independent_r119_v1'
TERMINAL = 'R119_GRID_INDEPENDENT_TERMINAL.json'
CONFIG_SHAS = {'F4': 'b75690eae7e762834abd9ca824c3deacbdfe1d6d9045e2c8e13dc4fbd2a090a8',
               'A4': '9aeba909f17ac11f9dc4328c70e8597cd371cfa9d45d4b81894590b80ebb4d21'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def configure(branch):
    sys.path.insert(0, str(OLD))
    from gpu import orch_r115_grid_native as grid
    from gpu import orch_r111_route_admission as admission
    budget.require(sha(OLD / 'SOURCE_CLOSURE.json') == CLOSURE_SHA, 'immutable_working_source_closure')
    for name, digest in grid.read(OLD / 'SOURCE_CLOSURE.json')['files'].items():
        budget.require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and sha(OLD / name) == digest, 'working_source_bytes:' + name)
    budget.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == grid.HOST_SHA, 'node5_only')
    root = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915') / branch
    budget.require(sha(root / 'CONFIG.json') == CONFIG_SHAS[branch], 'historical_CONFIG_unchanged')
    config = grid.read(root / 'CONFIG.json')
    budget.require(config['physical'] == {'F4': 3, 'A4': 7}[branch], 'own_GRID_slots_only')
    for name in ('TRAIN.json', 'DEV.json', 'FINAL.json', 'LEGACY_READOUT.json'):
        budget.require(sha(root / name) == config['inputs'][name], 'original_frozen_inputs')
    budget.require(sha(CLOCK) == CLOCK_SHA and sha(CHECKPOINT) == CHECKPOINT_SHA, 'actual_clock_gen1')
    clock = grid.read(CLOCK)
    grid.END, grid.TRAIN_END = 1789596240.0, 1789596120.0
    budget.require(clock['hard_end_unix'] == grid.END and clock['train_end_unix'] == grid.TRAIN_END,
                   'same_actual_lease_clock')
    budget.require(time.time() < grid.TRAIN_END, 'within_actual_lease_margin')
    checkpoint = grid.read(CHECKPOINT)
    budget.require(sha(CHECKPOINT.parent / 'optimizer_rng.pt') == checkpoint['optimizer_rng_sha256']
        == '2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5', 'optimizer_archive_not_reset_or_used')
    for name, digest in checkpoint['adapter']['files']:
        budget.require(Path(name).name == name and sha(Path(checkpoint['adapter']['path']) / name) == digest,
                       'actual_gen1_adapter_files')
    return grid, admission, root, config, checkpoint


def cpu(branch):
    grid, admission, root, config, checkpoint = configure(branch)
    ledger = (root / 'LEDGER.jsonl').read_bytes()
    rows = [json.loads(line) for line in ledger.splitlines() if line]
    counts = budget.counts(rows)
    history = grid.read(root / 'cycles/0008/TRAIN_COMPLETE.json')
    budget.require(grid.read(root / 'CARRY.json') == history['carry'] and len(history['outcomes']) == 2,
                   'exact_two_completed_episodes_and_retained_carry')
    budget.require(max(row['cycle'] for row in rows) == 8 and counts['PARENT'] == 40,
                   'no_new_shared_actor_charges')
    for row in rows:
        if row['kind'] == 'NATIVE' and row['split'] == 'TRAIN' and not row.get('attached_readout'):
            budget.require(grid.read(root / 'calls' / f'N{row["number"]:05d}.json')['status'] == 'COMPLETE',
                           'all_prior_TRAIN_charges_complete')
        elif row['kind'] == 'PARENT':
            budget.require((root / 'parent_received' / f'P{row["number"]:04d}.json').is_file(),
                           'prior_parent_dispositions_preserved')
    folder = root / ERA
    document = budget.authorize(root=root, ledger_bytes=ledger, rows=rows, config_sha256=sha(root / 'CONFIG.json'),
        lease_end=grid.END + 21600, hard_end=grid.END, now=time.time())
    grid.write(folder / 'LEASE_BUDGET.json', document)
    policy = dict(schema='R119_GRID_INDEPENDENT_FORK_V1', branch=branch, root=str(root), status='CPU_READY',
        mode='GEN1_FROZEN_LORA_ELICITATION_ONLY', local_optimizer_steps=0, common_barriers=False,
        checkpoint=grid.ref(CHECKPOINT), optimizer_archive_sha256=checkpoint['optimizer_rng_sha256'],
        old_carry=grid.ref(root / 'CARRY.json'), old_ledger=grid.ref(root / 'LEDGER.jsonl'),
        old_CONFIG=grid.ref(root / 'CONFIG.json'), old_train_complete=grid.ref(root / 'cycles/0008/TRAIN_COMPLETE.json'),
        pending_shared_rows='PRESERVED_ARCHIVED_NOT_RESUBMITTED_NO_NEW_SHARED_SLEEP', next_cycle=9,
        counts=counts, budget=grid.ref(folder / 'LEASE_BUDGET.json'), parent_nonblocking=True,
        source_files={str(path): sha(path) for path in HERE.glob('orch_r119_grid_*.py')},
        old_FINAL_replayed=False, new_final_not_before_unix=1789538400.0,
        new_final_utc='2026-09-16T06:00:00Z', new_final_separate_quota=8,
        train_end_unix=grid.TRAIN_END, hard_end_unix=grid.END, final_timer_status='NOT_YET_ARMED',
        raw_node_only=True, observed_unix=time.time())
    grid.write(folder / 'READY.json', policy)
    print(json.dumps(grid.ref(folder / 'READY.json')))


def ready(grid, root):
    document = grid.read(root / ERA / 'READY.json')
    for name, digest in document['source_files'].items():
        budget.require(sha(name) == digest, 'new_immutable_source')
    for key in ('old_carry', 'old_ledger', 'old_CONFIG', 'old_train_complete'):
        budget.require(grid.ref(document[key]['path']) == document[key], 'startup_continuity:' + key)
    return document


def scan(branch):
    grid, admission, root, config, checkpoint = configure(branch)
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'python3', '-B', str(Path(__file__).resolve()), 'scan', '--branch', branch]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={config['physical']: config['uuid']},
        HOST_SHA=grid.HOST_SHA, require=grid.require,
        allocation=lambda physical: budget.require(physical == config['physical'], 'own_assigned_device'))
    return admission.scan(config['physical'], root / 'SERVICE_IDENTITY.json')


def native(branch):
    grid, admission, root, config, checkpoint = configure(branch)
    document = ready(grid, root)
    budget.require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'], 'exact_GPU_UUID')
    from peft import PeftModel
    from gpu import orch_guided_native as native_source
    engine = grid.load_engine(config)
    identity = native_source.bridge.AdapterIdentity.from_document(checkpoint['adapter'])
    engine.model = PeftModel.from_pretrained(engine.model, identity.path, is_trainable=False,
        local_files_only=True, autocast_adapter_dtype=True)
    engine.model.requires_grad_(False)
    engine.model.eval()
    budget.require(native_source.observe_adapter(engine, identity) == identity, 'exact_gen1_base_params')
    grid.write(root / ERA / 'LOADED.json', dict(pid=os.getpid(), adapter=identity.document(),
        optimizer_steps=0, fork=True, observed_unix=time.time(), next_cycle=9))
    caps = grid.read(root / ERA / 'LEASE_BUDGET.json')['prospective_caps']
    grid.MAX_NATIVE, grid.MAX_PARENT = caps['NATIVE'], caps['PARENT']
    original_write = grid.write

    def write(path, value, replace=False):
        if isinstance(value, dict) and 'messages' in value and 'status' in value:
            budget.require(value['split'] == 'TRAIN' and not value['attached_readout'], 'no_FINAL_in_live_fork')
            value = dict(value, adapter=identity.document(), fork_checkpoint_sha256=CHECKPOINT_SHA,
                parent_nonblocking=True, local_optimizer_steps=0)
        return original_write(path, value, replace=replace)

    grid.write = write
    life_type = mailbox.life_class(grid, ERA)
    roster = grid.read(root / 'TRAIN.json')
    memory = grid.read(root / 'CARRY.json')
    cycle = 9
    while time.time() < grid.TRAIN_END:
        life = life_type(root, engine, config, cycle)
        tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
        try:
            grid.train_cycle(life, tasks, memory)
        except grid.TrainWindowClosed:
            break
        memory = grid.read(root / 'CARRY.json')
        original_write(root / ERA / f'C{cycle:04d}.json', dict(cycle=cycle, carry=grid.ref(root / 'CARRY.json'),
            ledger=grid.ref(root / 'LEDGER.jsonl'), shared_optimizer_steps=0, observed_unix=time.time()))
        cycle += 1


def guard(branch):
    grid, admission, root, config, checkpoint = configure(branch)
    ready(grid, root)
    folder = root / ERA
    grid.write(folder / 'GUARD_ONCE.json', dict(pid=os.getpid(), observed_unix=time.time()))
    try:
        report = scan(branch)
        grid.write(folder / 'ADMISSION.json', report)
        budget.require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons'],
                       'fresh_privileged_admission')
        ready(grid, root)
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(grid.END-time.time()-5))+'s',
            grid.PYTHON, '-B', str(Path(__file__).resolve()), 'native', '--branch', branch]
        with (folder / 'NATIVE.log').open('x') as log:
            child = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'],
                PYTHONPATH=str(OLD), PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        grid.write(folder / 'LAUNCH.json', dict(pid=child.pid, command=command, observed_unix=time.time()))
        code = child.wait()
        grid.write(root / TERMINAL, dict(status='COMPLETE' if code == 0 else 'FAILED', exit_code=code,
            finished_unix=time.time(), no_retry=True))
    except BaseException as error:
        if not (root / TERMINAL).exists():
            grid.write(root / TERMINAL, dict(status='FAILED', reason=str(error), no_retry=True,
                                           finished_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'scan', 'guard', 'native'))
    parser.add_argument('--branch', choices=('F4', 'A4'), required=True)
    arguments = parser.parse_args()
    result = globals()[arguments.mode](arguments.branch)
    if result is not None:
        print(json.dumps(result))
