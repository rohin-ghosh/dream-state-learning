"""Read-only, source-bound inventory for retention source adoption."""

import hashlib
import json
import os
from pathlib import Path
import time


FILES = ('gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(pid):
    root = Path('/proc') / str(pid)
    fields = (root / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0], uid=root.stat().st_uid,
        argv=(root / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'),
        cwd=str((root / 'cwd').resolve()), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def collect(targets):
    results = []
    for target in targets:
        result = dict(life=target['life'], node=target['node'], observed_unix=time.time())
        try:
            native = identity(target['pid'])
            if (target.get('start_ticks') is not None and native['start_ticks'] != str(target['start_ticks'])):
                raise ValueError('changed_native_incarnation')
            if native['state'] in ('Z', 'X') or native['uid'] != os.getuid():
                raise ValueError('exact_owned_live_native_required')
            result['native'] = native
            if '--config' not in native['argv'] or 'native' not in native['argv']:
                result['status'] = 'NOT_R125_THINK_ACT_NATIVE_REQUIRES_SEPARATE_SCOPE'
                results.append(result)
                continue
            guard_path = Path(native['argv'][native['argv'].index('--config') + 1])
            guard = json.loads(guard_path.read_bytes())
            plan_path = Path(guard['plan_path'])
            if sha(plan_path) != guard['plan_sha256']:
                raise ValueError('guard_plan_hash_mismatch')
            plan = json.loads(plan_path.read_bytes())
            source = Path(plan['source_root'])
            if native['cwd'] != str(source):
                raise ValueError('native_source_root_mismatch')
            observed = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
            if observed != guard['source_pins']:
                raise ValueError('whole_source_guard_mismatch')
            journal = Path(guard.get('copy_raw', plan['root'])) / 'stream'
            if identity(target['pid']) != native:
                latest = identity(target['pid'])
                if any(latest[key] != native[key] for key in native if key != 'state'):
                    raise ValueError('native_changed_during_source_capture')
            result.update(status='EXACT_GUARDED_SOURCE_VERIFIED', guard_path=str(guard_path),
                guard_sha256=sha(guard_path), source_pins=observed, plan=plan,
                guard_metadata={key: value for key, value in guard.items() if key != 'source_pins'},
                journal_id=json.loads((journal / 'JOURNAL.json').read_bytes())['journal_id'],
                journal_root=str(journal), files={name: dict(sha256=observed[name], text=(source / name).read_text())
                    for name in FILES}, source_files=len(observed), native_signals=[])
        except (ValueError, OSError, KeyError) as error:
            result.update(status='UNRESOLVED_NO_ACTION', error_type=type(error).__name__, error=str(error)[:300])
        results.append(result)
    return dict(observed_unix=time.time(), results=results, read_only=True, native_signals=[])
