"""Read-only caption boundary inspection using the preserved diagnostic library."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


LIBRARY_SHA = 'be9564a48d35676538925e80ad0bc7c4511d2a5ef920c0fecdb6c1f492862a21'
GUARD_SHA = 'f17b2c06389e3ef2d1f9e6fac439c096aead14c788421ddc191039418b891ec2'
BASE = '/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork'
REMOTE = r'''
import hashlib,json,os,time
from pathlib import Path
namespace = {'__name__': 'readonly_diagnostic_library'}
exec(compile(LIBRARY, '<readonly_diagnostic_library>', 'exec'), namespace)
namespace['GUARDS'] = {'Caption': GUARD_SHA}
namespace['SOURCES'] += ('gpu/r226_caption_runtime.py', 'gpu/r227_caption_runtime.py',
    'gpu/ny_caption_life.py', 'gpu/orch_r125_preupdate_recovery.py')
life = namespace['inspect_life']('Caption', BASE)
control = Path(BASE) / 'control_r233_recovery'
guard, guard_sha = namespace['load'](control / 'GUARD.json')
plan, plan_sha = namespace['load'](Path(guard['plan_path']))
records = Path(guard['copy_raw']) / 'stream/records'
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
selected = {life['head']['index'], life['latest_complete_header']['index']}
if life['latest_learn_header']:
    selected.add(life['latest_learn_header']['index'])
requests = [item for item in life['tail_headers'] if item['kind'] == 'SLEEP_REQUEST']
if requests:
    selected.add(requests[-1]['index'])
verified = []
complete_state = None
for index in sorted(selected):
    record, raw_sha = namespace['load'](records / f'{index:020d}.json', 128 * 1024 * 1024)
    if digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']:
        raise ValueError('selected_canonical_record_hash_mismatch')
    document = record['document']
    item = dict(index=index, kind=record['kind'], sha256=record['sha256'],
        raw_file_sha256=raw_sha, canonical_record_hash_verified=True)
    if record['kind'] == 'UPDATE':
        item['optimizer_step'] = document['optimizer_step']
    saved = document.get('resume_state', document.get('state'))
    if isinstance(saved, dict) and isinstance(saved.get('state'), dict):
        state = saved['state']
        if digest(state) != saved['sha256']:
            raise ValueError('saved_state_digest_mismatch')
        item.update(state_sha256=saved['sha256'], saved_state_digest_verified=True,
            cycle=document.get('cycle'), pending=state['pending'], rows=len(state['rows']),
            sleep_frontier=state['sleep_frontier'], deadline_unix=state['deadline_unix'],
            model_state_sha256=state['model_state_sha256'], history_sha256=digest(state['history']),
            working_state_sha256=digest(state['history'].get('working_state')))
        if record['kind'] == 'SLEEP_COMPLETE':
            complete_state = state
            checkpoint = document['checkpoint']
            relative = Path(checkpoint['adapter_path']).parent.relative_to(plan['root'])
            commit_path = Path(guard['copy_raw']) / relative / 'COMMIT.json'
            commit, commit_sha = namespace['load'](commit_path, 1024 * 1024)
            if commit != checkpoint or document['checkpoint_sha256'] != commit['checkpoint_sha256']:
                raise ValueError('COMPLETE_and_COMMIT_mismatch')
            item.update(commit_document_exact_match=True, commit_path=str(commit_path),
                commit_file_sha256=commit_sha, optimizer_steps=commit['optimizer_steps'],
                checkpoint_sha256=commit['checkpoint_sha256'])
        elif complete_state is not None:
            item['older_rows_exactly_preserved'] = state['rows'][:len(complete_state['rows'])] == complete_state['rows']
            item['pending_row_hashes'] = [digest(row) for row in state['rows'][state['sleep_frontier']:]]
            item['pending_source_hashes'] = [row['source_sha256'] for row in state['rows'][state['sleep_frontier']:]]
    verified.append(item)
matches = []
for entry in Path('/proc').iterdir():
    if not entry.name.isdigit():
        continue
    try:
        if entry.stat().st_uid != os.getuid():
            continue
        command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
        cwd = os.readlink(entry / 'cwd')
        if str(control / 'GUARD.json') in command or cwd == plan['source_root']:
            matches.append(dict(pid=int(entry.name), cwd=cwd, argv_prefix=command[:512]))
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
life['current_exact_guard_or_source_process_matches'] = matches
life['verified_selected_records'] = verified
for name in ('RECOVERY.json', 'CACHE_RESTORED.json', 'ARCHIVE_REPLAY.json', 'TAIL_ARTIFACTS_PRESERVED.json'):
    value, digest_value = namespace['load'](control / name, 65536)
    life.setdefault('prior_recovery_receipts', {})[name] = dict(sha256=digest_value, value=value)
print(json.dumps(dict(observed_unix=time.time(), node='node2',
    boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    scope='selected_boundary_and_metadata_only_not_native_resume', node_writes=False,
    native_signals=[], full_journal_verified=False, checkpoint_binaries_hashed=False,
    research_source_executed=False, life=life), sort_keys=True))
'''


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--receipt':
        raise SystemExit('use --receipt NEW_LOCAL_PATH')
    library = Path(__file__).with_name('read_only_inspect.py').read_bytes()
    if hashlib.sha256(library).hexdigest() != LIBRARY_SHA:
        raise ValueError('exact_preserved_diagnostic_library_required')
    source = library.decode()
    if source.count("'control_r233_lease_continuation'") != 1:
        raise ValueError('one_diagnostic_control_directory_seam')
    source = source.replace("'control_r233_lease_continuation'", "'control_r233_recovery'")
    payload = ('LIBRARY=' + repr(source) + '\nGUARD_SHA=' + repr(GUARD_SHA)
        + '\nBASE=' + repr(BASE) + '\n' + REMOTE).encode()
    completed = subprocess.run(['bash', 'gpu/ovx_ssh.sh', 'python3 -B -'], input=payload,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    receipt = dict(returncode=completed.returncode, stderr=completed.stderr.decode(errors='replace'),
        inspector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        diagnostic_library_sha256=LIBRARY_SHA, remote_payload_sha256=hashlib.sha256(payload).hexdigest(),
        report=json.loads(completed.stdout) if completed.returncode == 0 else None)
    with Path(sys.argv[2]).open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(dict(path=sys.argv[2], returncode=completed.returncode)))
