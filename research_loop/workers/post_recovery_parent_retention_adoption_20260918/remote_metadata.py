"""Read-only source/process metadata; executed over the existing SSH wrapper."""

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import time


def read_bytes(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 16 * 1024 * 1024:
            raise ValueError('bounded_regular_metadata_or_source_only')
        content = handle.read()
        after = os.fstat(handle.fileno())
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('changed_during_read')
    return content


def sha(content):
    return hashlib.sha256(content).hexdigest()


def identity(pid):
    root = Path('/proc') / str(pid)
    fields = (root / 'stat').read_text().rsplit(') ', 1)[1].split()
    argv = (root / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    return dict(pid=pid, start_ticks=fields[19], process_state=fields[0],
        argv=argv, cwd=str((root / 'cwd').resolve()))


def source_structure(content):
    tree = ast.parse(content)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = sorted({ast.unparse(child.func) for child in ast.walk(node)
                if isinstance(child, ast.Call)})
            reasons = [child.args[1].value for child in ast.walk(node)
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                and child.func.id == 'require' and len(child.args) >= 2
                and isinstance(child.args[1], ast.Constant) and isinstance(child.args[1].value, str)]
            functions.append(dict(name=node.name, line=node.lineno, calls=calls, requirements=reasons))
    return functions


def collect(targets):
    result = dict(schema='RETENTION_SOURCE_OBSERVATION_V1', observed_unix=time.time(), targets={})
    for label, expected in targets.items():
        before = identity(expected['pid'])
        if any(before[key] != expected[key] for key in ('pid', 'start_ticks', 'cwd', 'argv')):
            raise ValueError('phase2_process_identity_changed')
        if before['process_state'] in ('Z', 'X'):
            raise ValueError('native_not_live')
        guard_raw = read_bytes(expected['guard_path'])
        if sha(guard_raw) != expected['guard_sha256']:
            raise ValueError('phase2_guard_changed')
        guard = json.loads(guard_raw)
        source = Path(before['cwd'])
        hashes = {}
        structures = {}
        for relative, pinned in guard['source_pins'].items():
            candidate = Path(relative)
            if candidate.is_absolute() or '..' in candidate.parts or candidate.suffix != '.py':
                raise ValueError('relative_python_source_only')
            path = source / candidate
            if path.resolve() != path:
                raise ValueError('source_symlink_refused')
            content = read_bytes(path)
            hashes[relative] = sha(content)
            if hashes[relative] != pinned:
                raise ValueError('live_source_pin_mismatch:' + relative)
            if relative in ('gpu/r205_runtime.py', 'gpu/orch_r125_stream_journal.py',
                    'gpu/orch_r184_think_act_learn.py', 'gpu/orch_r125_continual_guard.py'):
                structures[relative] = source_structure(content)
        if set(hashes) != {str(path.relative_to(source)) for path in source.rglob('*.py')}:
            raise ValueError('unguarded_python_source')
        plan_raw = read_bytes(guard['plan_path'])
        lease_raw = read_bytes(guard['lease_path'])
        if sha(plan_raw) != guard['plan_sha256'] or sha(lease_raw) != guard['lease_sha256']:
            raise ValueError('plan_or_lease_pin_changed')
        plan = json.loads(plan_raw)
        if not time.time() < guard['hard_end_unix'] == plan['hard_end_unix']:
            raise ValueError('outside_current_guard_window')
        if plan['source_root'] != str(source) or plan['root'] != expected['root']:
            raise ValueError('source_or_life_binding_changed')
        after = identity(expected['pid'])
        if any(after[key] != before[key] for key in ('pid', 'start_ticks', 'cwd', 'argv')):
            raise ValueError('process_changed_during_capture')
        if sha(read_bytes(expected['guard_path'])) != expected['guard_sha256']:
            raise ValueError('guard_changed_during_capture')
        result['targets'][label] = dict(native=after, guard_path=expected['guard_path'],
            guard_sha256=sha(guard_raw), source_pins=guard['source_pins'], disk_hashes=hashes,
            plan_sha256=sha(plan_raw), lease_sha256=sha(lease_raw), root=plan['root'],
            hard_end_unix=guard['hard_end_unix'], lease_end_unix=plan['lease_end_unix'],
            phase2_full_source_pins_match=guard['source_pins'] == expected['source_pins'],
            source_structure=structures,
            plan_metadata={key: plan.get(key) for key in (
                'context_limit', 'segment_tokens', 'learn_row_policy', 'checkpoint_tail')})
    result['finished_unix'] = time.time()
    result['attestation_limit'] = 'disk/guard/proc only; not resident heap or a boundary reservation'
    return result


if __name__ == '__main__':
    print(json.dumps(collect(TARGETS), sort_keys=True))
