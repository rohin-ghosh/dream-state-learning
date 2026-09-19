"""One authorized pre-model continuation of the original FINAL allocation."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_math_feedback_uptake_r118_final_custody as prior

original, life = prior.original, prior.life
read, write, ref, require = prior.read, prior.write, prior.ref, prior.require
MODULE = 'gpu.orch_math_feedback_uptake_r119_final_premodel'
SOURCE = Path(__file__).resolve().parents[1]
OUTPUT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r119_final_premodel_20260915_attempt1')
PREVIOUS = prior.OUTPUT
SELECTED_SHA = '65899137a9833b177547f6ba3f392576436d590049ebf6454e1a3199642891b7'
LOG_SHA = '67c7fb5bc53be747dd2cb8238d9f3fdde4ef2e3c7b07fd6cf20afc9d8873e20c'
GUARDS = {
    'gpu/astra_goal_breadth_collection_guard.sh': 'b0ccefbf96e4509bbbe35560e9eba5d4871b798300faa290ad791f192ee3ee6f',
    'gpu/astra_goal_pair_collection_guard.sh': '5382d40ea594ceda241ffcc12ac91f99cf7a8afaf823db7891daff33e49d098f',
    'gpu/astra_event_two_hop_memory_guard.sh': '851b1de47cf1220be5bc8ba21bd40a2d53f1e86e8439efe3065f6b3387b255a1'}


def configure():
    prior.MODULE, prior.SOURCE, prior.OUTPUT = MODULE, SOURCE, OUTPUT


def functions():
    configure()
    result = prior.functions()
    result.update(validate=validate, release=release)
    return result


def no_model_evidence(root, branch):
    root = Path(root)
    for name in ('LEDGER.json', 'BEFORE.json', 'AFTER.json', 'MOUNTED_FINAL.json', 'COMPLETE.json'):
        require(not (root/name).exists(), 'model_or_input_evidence_forbids_recovery')
    require(not list(root.glob('CALL_*.json')), 'any_request_or_capture_forbids_recovery')
    terminal = read(root/'TERMINAL.json')
    require(terminal['charged_native'] == terminal['completed_native'] == 0
        and terminal['unattempted_native'] == 8, 'zero_model_input_denominators')
    scheduled = read(root/'SCHEDULED.json')
    require(not life.alive(scheduled['identity']), 'old_waiter_still_live')
    if branch == 'F2':
        require(terminal['status'] == 'FAILED' and original.sha(root/'NATIVE.log') == LOG_SHA,
            'exact_pre_model_packaging_failure')
        launch = read(root/'LAUNCH.json')
        require(not life.alive(launch['identity']), 'old_native_still_live')
        source = Path(read(root/'PLAN.json')['source_root'])
        require(original.sha(source/'gpu/orch_math_feedback_uptake_r118_final.py') ==
            '007415e5a2543bf0373c7928de5b070f3aef7d746803ed94f518f87fb434b9fb', 'exact_proven_preload_call_order')
        return dict(terminal=ref(root/'TERMINAL.json'), launch=ref(root/'LAUNCH.json'),
            log=ref(root/'NATIVE.log'), original_process_attempts=1)
    require(branch == 'A2' and terminal['status'] == 'NOT_RUN'
        and not (root/'LAUNCH.json').exists() and not (root/'NATIVE_CLAIM.json').exists()
        and not (root/'SELECTION_USED.json').exists(), 'A2_no_native_dispatch')
    require(original.sha(root/'ADMISSION.json') ==
        '75b5c95b5acf69e2bbe830095c6c5d9ed4cbb4c4382450374b61798147be0e52', 'exact_A2_failed_admission')
    return dict(terminal=ref(root/'TERMINAL.json'), admission=ref(root/'ADMISSION.json'), original_process_attempts=0)


def validate(root):
    configure()
    plan = prior.validate(root)
    original.window(plan, time.time())
    require(plan['premodel_previous']['path'] == str(PREVIOUS/f"lane{plan['physical']}"/'PLAN.json'),
        'only_exact_failed_FINAL_predecessor')
    old = original.bound(plan['premodel_previous'])
    proof = no_model_evidence(old['root'], plan['branch'])
    require(proof == plan['premodel_proof'], 'immutable_pre_model_failure_evidence')
    require(original.sha(plan['selection_path']) == SELECTED_SHA, 'same_exact_canonical_selection')
    for name, digest in GUARDS.items():
        require(original.sha(SOURCE/name) == digest, 'exact_restored_script_bytes')
    checked = original.bound(plan['mounted_CPU_check'])
    require(checked['verified'] is True and checked['model_loaded'] is False
        and checked['source_root'] == str(SOURCE), 'actual_full_mounted_CPU_check')
    return plan


def attempts(plan):
    original.window(plan, time.time())
    excluded = original.bound(plan['premodel_previous'])['root']
    no_model_evidence(excluded, plan['branch'])
    inspected = dict(plan, evaluation_chain=[entry for entry in plan['evaluation_chain'] if entry['root'] != excluded])
    return prior.attempts(inspected, time.time())


def claim(plan):
    require(not attempts(plan), 'any_old_model_attempt_forbids_continuation')
    path = Path(plan['continuation_claim'])
    old_claim = plan['original_claim']
    if old_claim:
        require(ref(plan['quota_claim']) == old_claim, 'preserved_original_claim_no_reset')
    else:
        require(not Path(plan['quota_claim']).exists(), 'unexpected_quota_owner')
    document = dict(quota_id=plan['quota_id'], root=plan['root'], plan=ref(Path(plan['root'])/'PLAN.json'),
        original_claim=old_claim, previous=plan['premodel_previous'], proof=plan['premodel_proof'],
        recovery_attempt=1, native_cap=8, retry_model_input=False, observed_unix=time.time())
    write(path, document)
    if old_claim is None:
        write(plan['quota_claim'], dict(quota_id=plan['quota_id'], root=plan['root'],
            plan=ref(Path(plan['root'])/'PLAN.json'), continuation=ref(path), native_cap=8, attempt=1))
    return ref(path)


def release(plan):
    released = prior.custody(plan)
    require(not attempts(plan), 'no_model_input_replay')
    if plan['original_claim']:
        require(ref(plan['quota_claim']) == plan['original_claim'], 'original_claim_unchanged')
    path = Path(plan['continuation_claim'])
    if path.exists():
        receipt = read(path)
        require(receipt['root'] == plan['root'] and receipt['plan'] == ref(Path(plan['root'])/'PLAN.json'),
            'only_one_continuation_owner')
    return dict(released, premodel_proof=plan['premodel_proof'], original_claim=plan['original_claim'])


def prepare(branch, manifest, tests, mounted_check):
    configure()
    physical = original.MEMBERS[branch][0]
    old_path = PREVIOUS/f'lane{physical}'/'PLAN.json'
    old = read(old_path)
    original.window(old, time.time())
    proof = no_model_evidence(old['root'], branch)
    root = OUTPUT/f'lane{physical}'
    require(not root.exists(), 'one_recovery_namespace')
    plan = deepcopy(old)
    plan.update(root=str(root), source_root=str(SOURCE), source_manifest=manifest, tests=tests,
        previous_evaluation_plan=ref(old_path), evaluation_chain=prior.evaluation_chain(ref(old_path)),
        premodel_previous=ref(old_path), premodel_proof=proof, mounted_CPU_check=mounted_check,
        original_claim=ref(old['quota_claim']) if Path(old['quota_claim']).exists() else None,
        continuation_claim=str(Path(old['original_root'])/'R119_FINAL_PREMODEL_CONTINUATION.json'),
        authority='Main17:06 one pre-model-only recovery, exact original8 calls and17:20 stop; no reset',
        recovery_model_input_retries=0)
    write(root/'PLAN.json', plan)
    validate(root)
    write(root/'DENOMINATORS.json', dict(planned_native=8, extra_native_quota=0, parent=0,
        optimizer_steps=0, original_process_attempts=proof['original_process_attempts'], recovery_attempt_max=1))
    return ref(root/'PLAN.json')


def schedule(root):
    root = Path(root)
    plan = validate(root)
    child = expected = None
    status = 'NOT_RUN'
    with Path(plan['quota_lock']).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not Path(plan['continuation_claim']).exists(), 'one_recovery_only')
        write(root/'SCHEDULED.json', dict(identity=life.identity(os.getpid()), plan=ref(root/'PLAN.json'), observed_unix=time.time()))
        try:
            release(plan)
            selected = functions()['selection'](plan, time.time())
            write(root/'SELECTED.json', dict(selection=selected, reference=ref(plan['selection_path'])))
            result = subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+str(SOURCE),'python3','-B','-m',MODULE,'scan','--root',str(root)],
                capture_output=True,text=True,check=True,timeout=min(90,plan['end_unix']-time.time()))
            admission = json.loads(result.stdout)
            write(root/'ADMISSION.json', admission)
            require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons'],
                'strict_fresh_FINAL_full_proc_UUID_admission')
            release(plan)
            write(root/'NATIVE_CLAIM.json', dict(continuation=claim(plan), model_input_retry=False))
            with (root/'NATIVE.log').open('x') as log:
                child = subprocess.Popen([life.previous.math.PYTHON,'-B','-m',MODULE,'native','--root',str(root)],
                    cwd=SOURCE,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                    env=dict(os.environ,CUDA_VISIBLE_DEVICES=plan['uuid'],PYTHONPATH=str(SOURCE),
                        PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                        OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
                for observation in range(100):
                    expected = life.identity(child.pid)
                    if MODULE.encode() in (Path('/proc')/str(child.pid)/'cmdline').read_bytes().split(b'\0'):
                        break
                    time.sleep(.01)
                else:
                    raise ValueError('actual_native_exec_required')
                write(root/'LAUNCH.json', dict(identity=expected, uuid=plan['uuid'], observed_unix=time.time()))
                require(child.wait(timeout=max(.01,plan['end_unix']-20-time.time())) == 0
                    and (root/'COMPLETE.json').exists(), 'fresh_FINAL_failed_no_further_recovery')
                status = 'COMPLETE'
        except BaseException as error:
            status = 'FAILED' if child is not None else 'NOT_RUN'
            write(root/(status+'.json'), dict(reason=type(error).__name__+': '+str(error),retry=False,observed_unix=time.time()))
        finally:
            if child is not None and child.poll() is None:
                life.terminate_owned(expected,force=True)
            write(root/'TERMINAL.json',dict(status=status,**original.denominators(root),
                recovery_attempts=1,original_attempts_preserved=True,observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('schedule','scan','native'))
    parser.add_argument('--root',type=Path,required=True)
    args = parser.parse_args()
    if args.phase == 'schedule':
        schedule(args.root)
    elif args.phase == 'scan':
        plan = validate(args.root)
        print(json.dumps(prior.recovery.prior.fresh_scan(Path(plan['original_root']).parent,plan['physical'])))
    else:
        plan = validate(args.root)
        require(Path(plan['continuation_claim']).exists(),'continuation_claim_before_model')
        functions()['native'](args.root)


if __name__ == '__main__':
    main()
