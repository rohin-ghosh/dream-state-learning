"""Bind Main's exact V2 amendment; obtain the original guard result without bypass."""

import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
COMMIT = 'b310383e78beade433b0ba39985cf773fcca8931'
DOCUMENT = 'research_loop/workers/replication_sprint_20260919/operations/BUILDER_ENTRIES.txt'
REMOTE = '''
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,os,subprocess,sys
from pathlib import Path
control=Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T142337Z')
def require(condition,reason):
    if not condition: raise ValueError(reason)
def pin(path): return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def write(name,value):
    path=control/name
    with path.open('x') as output:
        json.dump(value,output,sort_keys=True,indent=2);output.flush();os.fsync(output.fileno())
    descriptor=os.open(control,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)
    return pin(path)
require(os.uname().nodename=='ipp2-ovx-p6-09' and os.getuid()==2524,'original_node_owner')
compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,process_name','--format=csv,noheader'],check=True,capture_output=True,text=True)
require(not compute.stdout.strip(),'compute_present_no_healthy_native_signal')
candidate=json.loads((control/'GUARD_CANDIDATE_V2.json').read_bytes())
allocation=json.loads((control/'ALLOCATION_CANDIDATE_V2.json').read_bytes())
require(publication['git_commit']=='b310383e78beade433b0ba39985cf773fcca8931','exact_V2_publication')
require(candidate['pending_sleep_recovery']['sha256'] in publication['entry'] and candidate['plan_sha256'] in publication['entry'] and allocation['cpu_receipt_sha256'] in publication['entry'],'published_exact_V2_bindings')
publication_pin=write('BUILDER1438_PUBLICATION.json',publication)
allocation.update(builder_entry_logged=True,builder_publication=publication_pin)
allocation_pin=write('ALLOCATION_BUILDER1438.json',allocation)
guard_document=dict(candidate,allocation_path=allocation_pin['path'],allocation_sha256=allocation_pin['sha256'])
guard_pin=write('GUARD_BUILDER1438.json',guard_document)
plan=json.loads((control/'PLAN.json').read_bytes())
sys.path.insert(0,plan['source_root'])
from gpu import orch_r125_continual_guard as guard
try:
    guard.validate(Path(guard_pin['path']))
except Exception as error:
    result=dict(utc=datetime.now(timezone.utc).isoformat(),status='EXACT_V2_GUARD_VALIDATION_FAILED_NO_BYPASS',error_type=type(error).__name__,error=str(error),guard=guard_pin,allocation=allocation_pin,publication=publication_pin,native_launch_performed=False,privileged_scanner_run=False,confinement_probe_run=False,original_failures_preserved=True,automatic_retry=False)
    write('BUILDER1438_GUARD_FAILED.json',result)
else:
    raise ValueError('unexpected_guard_success_stop_for_review_no_automatic_launch')
require(result['error']=='pinned_startup_source','new_failure_requires_review')
old_source=Path(json.loads((control/'ORIGINAL_PLAN.json').read_bytes())['source_root'])
old_startup=Path(plan['startup_context']['path'])
new_startup=Path(plan['source_root'])/old_startup.relative_to(old_source)
require(pin(old_startup)['sha256']==pin(new_startup)['sha256']==plan['startup_context']['sha256'],'exact_identical_startup_file_copy')
proposed=deepcopy(plan)
proposed['startup_context']['path']=str(new_startup)
from gpu import orch_r125_continual_native as native
require(native.validate_plan(proposed)==proposed,'original_plan_validator_accepts_exact_path_rebase')
saved=json.loads((control/'PENDING_SLEEP_CANDIDATE.json').read_bytes())['candidate']['durable_checkpoint']
native.verify_experiment_resume(proposed,saved['experiment'])
check=dict(utc=datetime.now(timezone.utc).isoformat(),status='IN_MEMORY_SINGLE_STARTUP_PATH_REBASE_PASSES_ORIGINAL_NATIVE_PLAN_AND_EXPERIMENT_VALIDATION',original=plan['startup_context'],proposed=proposed['startup_context'],birth_text_unchanged=True,source_sha256_unchanged=True,only_PLAN_delta=['startup_context.path'],no_PLAN_written=True,no_runtime_source_changed=True,no_guard_bypass=True,native_or_GPU_launch_performed=False)
write('STARTUP_PATH_REBASE_DRAFT_CPU.json',check)
print(json.dumps(dict(guard_result=result,proposed_repair_cpu=check),sort_keys=True))
'''


def main():
    raw = subprocess.run(['git', 'show', COMMIT + ':' + DOCUMENT], cwd=REPO,
        check=True, capture_output=True).stdout
    entries = [entry for entry in raw.decode().splitlines() if entry.startswith('[Builder] 2026-09-19T14:38Z')]
    if len(entries) != 1:
        raise ValueError('exact_V2_published_entry_required')
    publication = dict(git_commit=COMMIT, repo_path=DOCUMENT, entry=entries[0],
        entry_sha256=hashlib.sha256(entries[0].encode()).hexdigest(),
        document_sha256=hashlib.sha256(raw).hexdigest())
    program = 'publication=' + repr(publication) + '\n' + REMOTE
    with (HERE / 'MATH_B_BUILDER1438_GUARD_RESULT.json').open('x') as output, \
            (HERE / 'MATH_B_BUILDER1438_GUARD_RESULT.stderr').open('x') as errors:
        result = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'),
            'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -'],
            input=program, text=True, stdout=output, stderr=errors, cwd=REPO, timeout=40)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
