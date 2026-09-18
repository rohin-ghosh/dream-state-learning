import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


DIRECTORY = Path(__file__).resolve().parent
WORKER = DIRECTORY.parent
REPOSITORY = WORKER.parents[2]
AUTHORITY_SHA = '0df24a834cdcc3b539ed12f19bb5a9c29534334a9e4480fbe514b1f6f743e0ea'


def main():
    phase = sys.argv[1]
    assert phase in ('stage', 'dispatch', 'observe')
    authority_raw = (WORKER/'sleep6_generation1/MAIN_SLEEP6_EXECUTION_AUTHORITY.json').read_bytes()
    assert hashlib.sha256(authority_raw).hexdigest() == AUTHORITY_SHA
    authority = json.loads(authority_raw)
    gos = {}
    for key,entry in authority['gos'].items():
        raw = (REPOSITORY/entry['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry['sha256']
        gos[key] = base64.b64encode(raw).decode()
    keys = sys.argv[2:]
    assert len(keys) == len(set(keys)) and all(key in gos for key in keys)
    assert (phase == 'dispatch' and 1 <= len(keys) <= 2) or (phase != 'dispatch' and not keys)
    payload = dict(phase=phase,keys=keys,gos=gos,authority=base64.b64encode(authority_raw).decode())
    program = '''
import base64, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
payload = PAYLOAD
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
source = root/'preparation/runtime_generation3/source'
control = root/'control/candidate5_sleep6_runtime3_generation1'
operation = control/'execution1'
wrapper = control/'prospective_operator1/admission_wrapper.py'
assert socket.gethostname() == '[REDACTED_HOST]'
sys.path.insert(0,str(source))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
raw = base64.b64decode(payload['authority'],validate=True)
assert hashlib.sha256(raw).hexdigest() == '0df24a834cdcc3b539ed12f19bb5a9c29534334a9e4480fbe514b1f6f743e0ea'
authority = json.loads(raw)
assert authority['decision'] == 'GO' and authority['additional_maximum_calls'] == 336
assert authority['fixed_campaign_calls'] == 672 and authority['fixed_campaign_slots'] == 12
assert authority['hard_end_unix'] == 1789646400 and authority['latest_dispatch_strictly_before_unix'] == 1789642785
assert evaluator.sha(evaluator.__file__) == '100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc'
assert evaluator.sha(wrapper) == authority['operator_sha256'] == '7990def61757f12cbb95d1e558845408dbe9b3698ab0cb633a2d60169014ea39'
assert evaluator.sha(control/'PROSPECTIVE_OPERATOR_CPU_GATE.json') == authority['operator_cpu_gate_sha256']
initial_identities = [dict(pid=pid,start_ticks=ticks,uid=2524,boot_id='8ff7b0dc-fbdf-4945-9044-3dffe94b5407')
    for pid,ticks in ((1701761,'85463090'),(1701784,'85463206'),(1701785,'85463206'),
                     (1704179,'85573721'),(1704195,'85574399'),(1704196,'85574399'),
                     (1705340,'85618948'),(1705419,'85619609'),(1705420,'85619609'))]
def write(path,value):
    evaluator.write(path,value)
def raw_write(path,value):
    with path.open('xb') as stream:
        stream.write(value)
    path.chmod(0o400)
def ledger():
    result = evaluator.ledger_status(root,evaluator.ORIGINAL_PLAN_SHA256)
    assert result['calls_charged'] <= 504 and result['call_cap'] == 672 and result['checkpoint_cap'] == 12
    return result
def completion(key):
    path = root/'ledger'/(key+'.COMPLETE.json')
    if not path.is_file():
        return None
    terminal = evaluator.read(path)
    assert terminal['status'] == 'COMPLETE'
    assert terminal['reservation_sha256'] == evaluator.sha(root/'ledger'/(key+'.RESERVED.json'))
    assert evaluator.sha(terminal['completion']['path']) == terminal['completion']['sha256']
    return dict(reference=evaluator.ref(path),observed_unix=terminal['observed_unix'])
def predecessor_release(key):
    arm,milestone = key.rsplit('_',1)
    if milestone == '1':
        terminals = {name:completion(name+'_0') for name in evaluator.ARMS}
        assert all(terminals.values()) and all(sidecar.gone(identity) for identity in initial_identities)
        return dict(initial3=terminals,initial_identities=initial_identities,all_exact_identities_gone=True)
    previous = arm+'_'+('1' if milestone == '2' else '2')
    terminal = completion(previous)
    assert terminal is not None,'prior_slot_complete_required'
    prior_dir = operation/previous
    identities = dict(wrapper=evaluator.read(prior_dir/'WRAPPER_STARTED.json')['identity'],
        timeout=evaluator.read(root/'attempts'/previous/'LAUNCH.json')['identity'],
        evaluator=evaluator.read(prior_dir/'NATIVE_IDENTITY.json')['identity'])
    assert all(sidecar.gone(identity) for identity in identities.values()),'all_exact_prior_identities_gone_required'
    disposition = evaluator.read(prior_dir/'DISPOSITION.json')
    assert 'status' in disposition['result'] and disposition['result']['status'] == 'METADATA_ONLY'
    assert not (prior_dir/'DISPATCH_ERROR.json').exists()
    return dict(previous_key=previous,terminal=terminal,identities=identities,all_exact_identities_gone=True,
        disposition=evaluator.ref(prior_dir/'DISPOSITION.json'))
if payload['phase'] == 'stage':
    assert time.time() < 1789642780
    before = ledger()
    assert before['calls_charged'] == 168 and before['completed'] == before['reserved'] == 3
    assert before['failed'] == before['unresolved'] == 0
    assert all(sidecar.gone(identity) for identity in initial_identities)
    operation.mkdir(mode=0o700,parents=True,exist_ok=False)
    raw_write(operation/'MAIN_SLEEP6_EXECUTION_AUTHORITY.json',raw)
    staged = {}
    for key,encoded in payload['gos'].items():
        entry = authority['gos'][key]
        assert evaluator.ref(entry['execution']['path']) == entry['execution']
        go_raw = base64.b64decode(encoded,validate=True)
        assert hashlib.sha256(go_raw).hexdigest() == entry['sha256']
        assert json.loads(go_raw) == dict(schema=evaluator.SCHEMA,status='MAIN_GO',execution=entry['execution'])
        path = control/(key+'.MAIN_GO.json')
        raw_write(path,go_raw)
        staged[key] = evaluator.ref(path)
    result = dict(status='SIX_EXACT_GOS_STAGED_NO_DISPATCH',gos=staged,
        authority=evaluator.ref(operation/'MAIN_SLEEP6_EXECUTION_AUTHORITY.json'),ledger=ledger(),observed_unix=time.time())
    write(operation/'STAGED.json',result)
elif payload['phase'] == 'dispatch':
    assert evaluator.sha(operation/'MAIN_SLEEP6_EXECUTION_AUTHORITY.json') == hashlib.sha256(raw).hexdigest()
    assert time.time() < 1789642780
    prepared = {}
    physicals = set()
    for key in payload['keys']:
        entry = authority['gos'][key]
        config_path = Path(entry['execution']['path'])
        assert evaluator.ref(config_path) == entry['execution']
        go = control/(key+'.MAIN_GO.json')
        assert evaluator.sha(go) == entry['sha256']
        assert not (operation/key).exists(), 'once_directory_already_exists_no_retry'
        assert not (root/'attempts'/key).exists()
        assert not any((root/'ledger'/(key+'.'+name+'.json')).exists() for name in ('RESERVED','COMPLETE','FAILED'))
        config = evaluator.read(config_path)
        assert config['physical'] not in physicals
        physicals.add(config['physical'])
        release = predecessor_release(key)
        environment = dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(source),
            R159_MAIN_GO_SHA256=entry['sha256'],HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        directory = operation/key
        directory.mkdir(mode=0o700,exist_ok=False)
        with (directory/'VALIDATION.private.log').open('x') as errors:
            checked = subprocess.run([config['python'],'-B','-m','gpu.orch_r159_matched_evaluation','validate',
                '--config',str(config_path),'--go',str(go)],cwd=source,env=environment,
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=errors,timeout=120)
        status = json.loads(checked.stdout)
        write(directory/'VALIDATION.json',dict(returncode=checked.returncode,result=status,observed_unix=time.time()))
        assert checked.returncode == 0 and status['status'] == 'PASS_NO_GPU'
        write(directory/'PREDECESSOR_RELEASE.json',release)
        prepared[key] = (config_path,go,config,directory,environment)
    before = ledger()
    assert before['calls_charged']+len(prepared)*56 <= 504
    launches = {}
    for key,(config_path,go,config,directory,environment) in prepared.items():
        assert time.time() < 1789642780
        predecessor_release(key)
        assert not (root/'ledger'/(key+'.RESERVED.json')).exists() and not (root/'attempts'/key).exists()
        write(directory/'INITIATOR.json',dict(identity=sidecar.identity(os.getpid()),observed_unix=time.time()))
        write(directory/'DISPATCH_ONCE.json',dict(key=key,execution=evaluator.ref(config_path),main_go=evaluator.ref(go),
            authority=evaluator.ref(operation/'MAIN_SLEEP6_EXECUTION_AUTHORITY.json'),retry_allowed=False,observed_unix=time.time()))
        with (directory/'dispatch.private.log').open('x') as log:
            child = subprocess.Popen([config['python'],'-B',str(wrapper),'--source',str(source),
                '--config',str(config_path),'--go',str(go),'--operator',str(directory)],cwd=directory,env=environment,
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
        launch = dict(status='DETACHED_ONCE_WRAPPER_NOT_YET_ADMITTED',identity=sidecar.identity(child.pid),
            execution=evaluator.ref(config_path),main_go=evaluator.ref(go),physical=config['physical'],observed_unix=time.time())
        write(directory/'DISPATCH_LAUNCH.json',launch)
        launches[key] = launch
    result = dict(status='ONCE_WRAPPERS_SPAWNED',launches=launches,ledger_before=before,observed_unix=time.time())
else:
    result = dict(status='METADATA_ONLY',ledger=ledger(),keys={},held_contents_read=False,observed_unix=time.time())
    for key in authority['gos']:
        directory = operation/key
        item = dict(operator_exists=directory.exists(),key=key)
        if directory.exists():
            for name in ('DISPATCH_LAUNCH','WRAPPER_STARTED','DISPOSITION','DISPATCH_ERROR'):
                path = directory/(name+'.json')
                if path.is_file():
                    item[name] = evaluator.read(path)
            if 'WRAPPER_STARTED' in item:
                item['wrapper_gone'] = sidecar.gone(item['WRAPPER_STARTED']['identity'])
            admission = directory/'ACTUAL_ADMISSION.private.json'
            if admission.is_file():
                capture = evaluator.read(admission)
                report = capture['report']
                item['admission'] = dict(reference=evaluator.ref(admission),observed_unix=capture['observed_unix'],
                    clear=report['clear'],blocking_reasons=report['blocking_reasons'],gpu=report['gpu'],scanner_euid=report['scanner_euid'])
            launch_path = root/'attempts'/key/'LAUNCH.json'
            if launch_path.is_file():
                launch = evaluator.read(launch_path)
                item['native_launch'] = launch
                item['timeout_gone'] = sidecar.gone(launch['identity'])
                identity_path = directory/'NATIVE_IDENTITY.json'
                if not identity_path.exists():
                    found = []
                    for process_directory in Path('/proc').glob('[0-9]*'):
                        try:
                            fields = (process_directory/'stat').read_text().rsplit(')',1)[1].split()
                            if int(fields[1]) != launch['identity']['pid']:
                                continue
                            arguments = (process_directory/'cmdline').read_bytes().split(b'\\0')
                            if b'gpu.orch_r159_matched_evaluation' not in arguments or b'evaluate' not in arguments:
                                continue
                            if arguments[arguments.index(b'--config')+1].decode() != launch['execution']['path']:
                                continue
                            found.append(sidecar.identity(int(process_directory.name)))
                        except (FileNotFoundError,ProcessLookupError,PermissionError,IndexError,ValueError):
                            continue
                    assert len(found) <= 1
                    if found:
                        write(identity_path,dict(identity=found[0],timeout_identity=launch['identity'],
                            execution=launch['execution'],observed_unix=time.time()))
                if identity_path.is_file():
                    native = evaluator.read(identity_path)
                    item['native_identity'] = native['identity']
                    item['native_gone'] = sidecar.gone(native['identity'])
            sealed = root/'attempts'/key/'sealed'
            if sealed.is_dir():
                names = os.listdir(sealed)
                item['output_artifact_count'] = sum(name.startswith('CALL_') and name.endswith('.RAW.private.json') for name in names)
                item['item_reservation_count'] = sum(name.startswith('CALL_') and name.endswith('.RESERVED.private.json') for name in names)
            item['completion'] = completion(key)
            failure = root/'ledger'/(key+'.FAILED.json')
            item['failed'] = failure.exists()
            if failure.exists():
                item['failure_receipt'] = evaluator.ref(failure)
        result['keys'][key] = item
    result['gpu_processes'] = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_gpu_memory',
        '--format=csv,noheader,nounits'],text=True,timeout=20).splitlines()
    result['observed_unix'] = time.time()
print(json.dumps(result,sort_keys=True))
'''.replace('PAYLOAD',repr(payload),1)
    label = phase+'_'+'_'.join(keys) if keys else phase+'_'+str(time.time_ns())
    with (DIRECTORY/(label+'.stderr')).open('xb') as errors:
        result = subprocess.run(['bash',str(REPOSITORY/'gpu/ovx_ssh.sh'),'/localhome/local-rohing/v2/venv/bin/python -B -'],
            input=program.encode(),stdout=subprocess.PIPE,stderr=errors,timeout=260,check=True)
    with (DIRECTORY/(label+'.json')).open('xb') as output:
        output.write(result.stdout)
    print(result.stdout.decode())


if __name__ == '__main__':
    main()
