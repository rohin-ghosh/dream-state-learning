"""Read-only CPU saved-LoRA numerics; one immutable receipt outside the run root."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import signal
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path('/localhome/local-rohing/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2')
SOURCE = Path('/localhome/local-rohing/astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158')
DRIVER = Path('/tmp/astra_rulegame_record_write_v2_20260912.py')
PLAN_SHA = '48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4'
DRIVER_SHA = '183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c'
HELPER_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
DEFAULT_RECEIPT = Path('/tmp/astra_rulegame_record_weight_audit_20260912.json')
PID, ARMS = 233174, ('P', 'A')


def load(path, pin, name):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != pin:
        raise ValueError('dependency changed: ' + str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
    sys.modules[name] = module
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


common = load(Path('/tmp/astra_collect_memory_only_20260912.py'), HELPER_SHA, 'record_weight_common')
require, read, digest = common.require, common.read, common.digest


def tensor_stats(path):
    groups = {name: dict(entries=0, finite_entries=0, finite_nonzero_count=0, sum_squares=0., maxabs=0.)
              for name in ('total', 'LoRA_A', 'LoRA_B')}
    bad_tensors, tensor_count = [], 0
    with path.open('rb') as stream:
        header_size = struct.unpack('<Q', stream.read(8))[0]
        require(0 < header_size <= 16 * 1024 * 1024, 'invalid safetensors header')
        header = json.loads(stream.read(header_size), object_pairs_hook=common.unique_object)
        intervals = []
        for name, tensor in header.items():
            if name == '__metadata__':
                continue
            require(name.endswith(('.lora_A.weight', '.lora_B.weight')), 'non-LoRA tensor')
            part = 'LoRA_A' if name.endswith('.lora_A.weight') else 'LoRA_B'
            dtype = tensor['dtype']
            require(dtype in ('F32', 'F16', 'BF16'), 'unsupported numerical dtype')
            size = 4 if dtype == 'F32' else 2
            begin, end = tensor['data_offsets']
            require(type(begin) is int and type(end) is int and begin >= 0 and end > begin and
                all(type(value) is int and value > 0 for value in tensor['shape']) and
                end - begin == math.prod(tensor['shape']) * size, 'shape/offset/size mismatch')
            intervals.append((begin, end))
            tensor_count += 1
            stream.seek(8 + header_size + begin)
            remaining, nonfinite = end - begin, 0
            while remaining:
                payload = stream.read(min(1024 * 1024, remaining))
                require(payload and len(payload) % size == 0, 'truncated tensor payload')
                remaining -= len(payload)
                count, nonzero, maximum, square_terms = 0, 0, 0., []
                for (value,) in struct.iter_unpack({'F32': '<f', 'F16': '<e', 'BF16': '<H'}[dtype], payload):
                    if dtype == 'BF16':
                        value = struct.unpack('<f', struct.pack('<I', value << 16))[0]
                    if math.isfinite(value):
                        count += 1
                        nonzero += value != 0
                        maximum = max(maximum, abs(value))
                        square_terms.append(value * value)
                entries = len(payload) // size
                nonfinite += entries - count
                squares = math.fsum(square_terms)
                for group in (groups['total'], groups[part]):
                    group['entries'] += entries
                    group['finite_entries'] += count
                    group['finite_nonzero_count'] += nonzero
                    group['sum_squares'] += squares
                    group['maxabs'] = max(group['maxabs'], maximum)
            if nonfinite:
                bad_tensors.append(dict(name=name, nonfinite_entries=nonfinite))
        position = 0
        for begin, end in sorted(intervals):
            require(begin == position, 'tensor offset gap/overlap')
            position = end
        require(path.stat().st_size == 8 + header_size + position, 'weight file length differs')
    require(all(groups[name]['entries'] > 0 for name in ('LoRA_A', 'LoRA_B')), 'missing A/B tensors')
    for group in groups.values():
        group['nonfinite_entries'] = group['entries'] - group['finite_entries']
        squares = group.pop('sum_squares')
        group['l2'] = math.sqrt(squares) if group['nonfinite_entries'] == 0 else None
        group['nonzero_count'] = group['finite_nonzero_count'] if group['nonfinite_entries'] == 0 else None
        if group['nonfinite_entries']:
            group['maxabs'] = None
    return dict(status='FINITE' if not bad_tensors else 'NONFINITE_TENSORS', all_finite=not bad_tensors,
        tensor_count=tensor_count, groups=groups, nonfinite_tensors=bad_tensors,
        nonzero_B_from_declared_zero_init=groups['LoRA_B']['nonzero_count'] > 0 if groups['LoRA_B']['nonzero_count'] is not None else None)


def audit_arm(arm, result, bridge):
    fit = ROOT / 'fits' / arm
    manifest_sha = digest(fit / 'manifest.json')
    require(manifest_sha == result['arms'][arm]['fit_manifest_sha256'], 'fit manifest/result seal differs')
    manifest = read(fit / 'manifest.json')['files']
    before = common.capture_files(fit)
    require(before == manifest, 'fit/adapter hashes differ before numerical audit')
    try:
        receipt = read(fit / 'receipt.json')
        completed = result['arms'][arm]
        require(completed == dict(receipt, fit_manifest_sha256=manifest_sha,
            supervision_sha256=digest(ROOT / 'run' / arm / 'supervision.json')) and receipt['steps'] == 12 and
            receipt['adapter'] == str(fit / 'adapter'), 'completed write receipt differs')
        weights = fit / 'adapter/adapter_model.safetensors'
        weight_sha = before['adapter/adapter_model.safetensors']
        require(receipt['files']['adapter_model.safetensors'] == weight_sha, 'adapter weight hash binding differs')
        trainability = read(fit / 'pre_update_trainability.json')
        require(trainability['init_adapter'] is None and trainability['base_frozen'] is True and trainability['adapter_count'] == 1,
                'not declared fresh single-adapter initialization')
        bridge.saved_weights(weights, trainability['adapters'])
        numerical = tensor_stats(weights)
    finally:
        after = common.capture_files(fit)
        require(after == before and digest(fit / 'manifest.json') == manifest_sha, 'fit/adapter changed during numerical audit')
    return dict(numerical, fit_manifest_sha256=manifest_sha, files_before=before, files_after=after,
        weight_sha256_before=weight_sha, weight_sha256_after=after['adapter/adapter_model.safetensors'])


class AuditExpired(BaseException):
    pass


def expired(number, frame):
    raise AuditExpired('300-second CPU numerical audit limit; no retry or retuning')


def run(receipt_path=DEFAULT_RECEIPT):
    receipt_path = common.unaliased(receipt_path)
    require(not receipt_path.exists() and receipt_path.parent.is_dir(), 'fresh external receipt required; no overwrite')
    require(all(protected != receipt_path and protected not in receipt_path.parents for protected in (ROOT, SOURCE)),
            'receipt must be outside run and source roots')
    require(not Path(f'/proc/{PID}').exists(), 'wait for controller absence')
    started = time.monotonic()
    report = dict(status='ERROR', root=str(ROOT), plan_sha256=PLAN_SHA, arms={}, readout_success=None,
        scope='CPU saved tensor magnitudes only; no torch, model, GPU, fitting, readout, or semantic judgment.',
        interpretation='No pre-init A snapshot: A norms are NOT update deltas. Nonzero B corroborates change from declared fresh zero-B initialization, not utility. Zero B is reported without retuning a threshold.')
    handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        require(digest(ROOT / 'plan.json') == PLAN_SHA, 'plan changed')
        plan = read(ROOT / 'plan.json')
        require(plan['source_root'] == str(SOURCE) and plan['out'] == str(ROOT) and plan['init_adapter'] is None and
            plan['arms'] == list(ARMS), 'wrong prepared root/source/initialization')
        bridge = load(DRIVER, DRIVER_SHA, 'record_weight_driver')
        result_sha = digest(ROOT / 'run/result.json')
        result = read(ROOT / 'run/result.json')
        require(result['status'] == 'PAIRED_ADAPTERS_SAVED_READOUT_PENDING' and set(result['arms']) == set(ARMS) and
            not (ROOT / 'run/failure.json').exists(), 'requires completed paired write, not a readout')
        for arm in ARMS:
            try:
                report['arms'][arm] = audit_arm(arm, result, bridge)
            except Exception as error:
                report['arms'][arm] = dict(status='ERROR', error=f'{type(error).__name__}: {error}')
        require(digest(ROOT / 'plan.json') == PLAN_SHA and digest(ROOT / 'run/result.json') == result_sha, 'terminal/plan changed')
        report.update(status='FINITE_PAIRED_ADAPTERS' if all(row['status'] == 'FINITE' for row in report['arms'].values())
            else 'NONFINITE_OR_INVALID_ADAPTERS', result_sha256=result_sha)
    except (Exception, AuditExpired) as error:
        report.update(status='ERROR', error=f'{type(error).__name__}: {error}')
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, handler)
    report.update(audit_seconds=time.monotonic() - started, audit_completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        audit_script_sha256=digest(__file__), driver_sha256=DRIVER_SHA)
    common.write_json(receipt_path, report)
    return dict(status=report['status'], receipt=str(receipt_path), sha256=digest(receipt_path), audit_seconds=report['audit_seconds'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, default=DEFAULT_RECEIPT)
    result = run(parser.parse_args().receipt)
    print(json.dumps(result, sort_keys=True), flush=True)
    raise SystemExit(0 if result['status'] == 'FINITE_PAIRED_ADAPTERS' else 2)
