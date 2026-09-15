"""Resume the saved node3 grid prefix without repeating charged calls."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_r111_grid_recover as prior
from gpu import orch_r111_route_admission as admission


ROOT = prior.ROOT
SOURCE = Path(__file__).resolve().parents[1]
READY_SHA = '1041b72f2c7c6067c8908aaf63a14b679a95c58d2595ce6a5db3b5ec4e33ffc9'
UUID = 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'
RECEIPTS = 'recovery_node3_v1/receipts'
TERMINAL = 'RECOVERY_NODE3_V1_TERMINAL.json'
require, read, ref, write = prior.require, prior.read, prior.ref, prior.write_new


class Replay(prior.Replay):
    def __init__(self, root, old):
        super().__init__(root, old, 'segment', 1)
        self.output = root / RECEIPTS


class DryComplete(BaseException):
    pass


class DryReplay(Replay):
    def spend(self, root, kind, detail):
        if self.cursor == len(self.cached):
            raise DryComplete('saved_prefix_complete_before_new_charge')
        return super().spend(root, kind, detail)

    def write(self, path, value):
        if path.name == 'FAILED.json':
            require(value['error_type'] == 'DryComplete', 'unexpected_dry_failure:' + value['error_type'])
            return
        require(path.exists(), 'dry_replay_new_evidence:' + str(path))
        return super().write(path, value)


def checked_old():
    from gpu import orch_r109_grid_run as old

    require(ref(ROOT / 'READY.json')['sha256'] == READY_SHA, 'exact_node3_original_ready')
    require(ref(Path(old.__file__))['sha256'] == prior.OLD_RUN_SHA, 'original_runtime_bytes')
    ready = old.validate(ROOT, 'ovx2')
    require(read(ROOT / 'segment/cycle01/train/FAILED.json')['error_type'] == 'JSONDecodeError',
            'exact_preserved_publication_failure')
    require(ready['allocation']['index'] == 5 and ready['allocation']['uuid'] == UUID,
            'only_node3_physical5')
    return old, ready


def cpu_check():
    old, ready = checked_old()
    before = ref(ROOT / 'LEDGER.jsonl')
    replay = DryReplay(ROOT, old)
    prior.install(old, replay)
    loaded = read(ROOT / 'segment/cycle01/train/LOADED.json')
    tokenizer = old.portable.source.native.load_local_tokenizer(ready['model_dir'])
    engine = SimpleNamespace(no_adapter=loaded['no_adapter'], loaded_base_sha256=loaded['base_sha256'],
        runtime=loaded['runtime'], tokenizer=tokenizer)
    engine.generate = lambda messages, **kwargs: replay.generate(None, messages, **kwargs)
    try:
        old.run(ROOT, 'ovx2', 'segment', 1, 'train', shared_engine=engine)
        raise ValueError('expected_new_call_boundary')
    except DryComplete:
        pass
    require(before == ref(ROOT / 'LEDGER.jsonl'), 'zero_charge_CPU_replay')
    import torch
    require(not torch.cuda.is_initialized(), 'CPU_only')
    return dict(passed=True, cached_records_reconstructed=replay.cursor,
        original_native_charged=replay.initial_native, original_parent_charged=replay.initial_parent,
        ledger=before, model_loaded=False, cuda_initialized=False, new_native_calls=0, new_parent_calls=0)


def native():
    old, ready = checked_old()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == UUID, 'exact_assigned_UUID')
    replay = Replay(ROOT, old)
    prior.install(old, replay)
    def check(label):
        require(time.time() < old.policy.NATIVE_END, 'original_deadline:' + label)
    tokenizer = old.portable.source.native.load_local_tokenizer(ready['model_dir'])
    engine = prior.EngineProxy(old.Engine(ready['model_dir'], tokenizer, device='cuda:0', check=check), replay)
    write(ROOT / RECEIPTS / 'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(),
        original_native_charged=replay.initial_native, original_parent_charged=replay.initial_parent,
        base_sha256=engine.loaded_base_sha256, no_adapter=engine.no_adapter))
    for cadence in old.policy.LANES['ovx2']['order']:
        for cycle in range(1, old.policy.CYCLES + 1):
            for phase in ('train', 'held'):
                if (ROOT / cadence / f'cycle{cycle:02d}' / phase / 'COMPLETE.json').exists():
                    continue
                old.run(ROOT, 'ovx2', cadence, cycle, phase, shared_engine=engine)
    engine.verify_base()


def scan():
    from gpu import orch_r109_grid_run as old

    if os.geteuid() != 0:
        argv = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(SOURCE), 'python3', '-B', '-m',
            'gpu.orch_r118_node3_5_grid_recover', 'scan']
        return json.loads(subprocess.check_output(argv, text=True, timeout=100))
    old.bind('ovx2')
    return admission.scan(5, ROOT / 'SERVICE_IDENTITY.json')


def guard():
    old, unused = checked_old()
    output = ROOT / RECEIPTS
    (output / 'GUARD_ONCE').mkdir()
    try:
        require(read(output / 'CPU_REPLAY_PASSED.json')['passed'], 'actual_CPU_prefix_replay_required')
        require(not Path('/proc', str(read(ROOT / 'RESIDENT_LOADED.json')['pid'])).exists(),
                'old_native_gone_no_signal')
        for attempt in range(90):
            report = scan()
            write(output / f'ADMISSION_{attempt:03d}.json', report)
            if report['clear']:
                require(report['scanner_euid'] == 0 and not report['blocking_reasons'] and
                        report['gpu']['uuid'] == UUID, 'fresh_privileged_exact_GPU')
                break
            time.sleep(2)
        else:
            raise ValueError('no_fresh_admission_no_waiver')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=UUID, PYTHONPATH=str(SOURCE),
            PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        seconds = int(old.policy.HARD_END - time.time() - 5)
        require(seconds > 0, 'original_hard_end')
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(seconds) + 's', old.PYTHON,
            '-B', '-m', 'gpu.orch_r118_node3_5_grid_recover', 'native']
        with (output / 'NATIVE.log').open('x') as stream:
            child = subprocess.Popen(command, cwd=SOURCE, env=environment, stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True)
        write(output / 'LAUNCH.json', dict(pid=child.pid, launched_unix=time.time(), command=command))
        require(child.wait() == 0, 'native_failure_preserved_no_retry')
        write(ROOT / TERMINAL, dict(status='COMPLETE', finished_unix=time.time()))
    except BaseException as error:
        write(ROOT / TERMINAL, dict(status='FAILED', error_type=type(error).__name__,
            error=str(error), finished_unix=time.time()))
        raise
    finally:
        write(output / 'FINAL_RELEASE.json', scan())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'scan', 'native', 'guard'))
    args = parser.parse_args()
    if args.mode in ('cpu', 'scan'):
        print(json.dumps((cpu_check if args.mode == 'cpu' else scan)(), sort_keys=True))
    else:
        (native if args.mode == 'native' else guard)()
