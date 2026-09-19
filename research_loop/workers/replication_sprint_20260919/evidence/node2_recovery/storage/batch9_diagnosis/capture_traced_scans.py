"""Read-only exception tracing around the byte-identical frozen scanner; no admission."""

import json
from pathlib import Path
import subprocess

from capture_raw_scan import BATCH_SHA, FROZEN, HERE, PROGRAM, SCANNER_SHA, STORAGE, frozen, pidfd_scan


TRACER = r'''
import errno,json,os,pathlib,select,sys,time
from datetime import datetime,timezone
namespace={'__name__':'frozen_readonly_diagnostic'}
exec(compile(original_program,'frozen_pidfd_scan.py','exec'),namespace)
events=[]
def observed_path(path):
    try:
        info=os.stat(path)
        return dict(exists=True,device=info.st_dev,inode=info.st_ino)
    except OSError as error:
        return dict(exists=None if error.errno!=errno.ENOENT else False,error_type=type(error).__name__,errno=error.errno)
def observe(frame,event,argument):
    if event!='exception' or frame.f_code.co_filename!='frozen_pidfd_scan.py' or frame.f_code.co_name!='inspect_process':
        return observe
    error=argument[1]
    if not isinstance(error,(OSError,ValueError,KeyError)) or len(events)>=40:
        return observe
    local=frame.f_locals
    pid=local.get('pid')
    descriptor=local.get('descriptor')
    entry=local.get('entry')
    row=dict(utc=datetime.now(timezone.utc).isoformat(),pid=pid,bound_start_ticks=local.get('start'),
        exception_type=type(error).__name__,errno=getattr(error,'errno',None),
        filename=str(getattr(error,'filename',None)),message=str(error)[:400],
        source_line=original_program.splitlines()[frame.f_lineno-1].strip(),
        enumerated_fd=None if entry is None else entry.name)
    try:
        row['pidfd_readable_before']=None if descriptor is None else namespace['pidfd_exited'](descriptor)
        try: row['current_start_before']=namespace['process_start'](pid)
        except OSError as failure: row['current_start_before_error']=dict(type=type(failure).__name__,errno=failure.errno)
        if entry is not None:
            row['fd_after_exception']=observed_path(f'/proc/{pid}/fd/{entry.name}')
            row['fdinfo_after_exception']=observed_path(f'/proc/{pid}/fdinfo/{entry.name}')
        try: row['current_start_after']=namespace['process_start'](pid)
        except OSError as failure: row['current_start_after_error']=dict(type=type(failure).__name__,errno=failure.errno)
        row['pidfd_readable_after']=None if descriptor is None else namespace['pidfd_exited'](descriptor)
    except (OSError,ValueError) as failure:
        row['observer_uncertainty']=dict(type=type(failure).__name__,errno=getattr(failure,'errno',None))
    events.append(row)
    return observe
paths=json.load(sys.stdin)
scans=[]
started=time.monotonic()
for ordinal in range(8):
    if time.monotonic()-started>20:
        break
    events=[]
    sys.settrace(observe)
    try:
        result=namespace['scan'](paths)
    finally:
        sys.settrace(None)
    scans.append(dict(ordinal=ordinal,original_scanner_result=result,exception_observations=events))
    if result['inaccessible_or_exited']:
        break
print(json.dumps(dict(scans=scans,scan_count=len(scans),elapsed_seconds=time.monotonic()-started,
    original_program_bytes_unchanged=True,sys_settrace_may_change_timing=True,
    historical_original_failure_not_recovered=True,admission_or_coalescence_performed=False),sort_keys=True))
'''


def main():
    frozen.frozen_artifacts()
    frozen.require(frozen.sha((FROZEN / 'pidfd_scan.py').read_bytes()) == SCANNER_SHA, 'unchanged_original_scanner')
    raw = (STORAGE / 'coalescence_remaining/BATCH_0009.json').read_bytes()
    frozen.require(frozen.sha(raw) == BATCH_SHA, 'exact_failed_batch')
    batch = json.loads(raw)
    paths = [row['path'] for group in batch['groups'] for inode in [group['canonical'], *group['replacement_inodes']]
             for row in inode['paths']]
    diagnostic = f'original_program={pidfd_scan.PROGRAM!r}\n' + TRACER
    program = f'paths={paths!r}\nscanner_program={diagnostic!r}\nbatch_sha256={BATCH_SHA!r}\nscanner_source_sha256={SCANNER_SHA!r}\n' + PROGRAM
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    result = subprocess.run(['bash', str(repo / 'gpu/ovx_ssh.sh'), frozen.encoded_command(program)],
                            capture_output=True, text=True, check=True, timeout=60)
    report = json.loads(result.stdout)
    timestamp = report['started_utc'].replace('-', '').replace(':', '').replace('+0000', 'Z').replace('.', '_')
    destination = HERE / f'TRACED_SCAN_{timestamp}.json'
    with destination.open('x') as output:
        json.dump(report, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(dict(receipt=str(destination),sha256=frozen.sha(destination.read_bytes()),
        started_utc=report['started_utc'],returncode=report['returncode'],diagnosis=report.get('raw_scan'),
        owner_available_bytes=report['owner_available_bytes'],all_target_metadata_unchanged=report['all_target_metadata_unchanged']),sort_keys=True))


if __name__ == '__main__':
    main()
