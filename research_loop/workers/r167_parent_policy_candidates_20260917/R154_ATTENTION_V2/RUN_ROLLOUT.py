"""Main-authorized C1..C5-only rollout; helper is CPU-gated before any signal."""

import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as takeover


STAGE = Path(__file__).resolve().parent
REPOSITORY = STAGE.parents[3]
OUTPUT = STAGE/'ROLLOUT'
EXPECTED = {
    'INDEX.json': 'ad3e80d1a29fe7187fa2b77d30fa3397a5b8d38f7b845ec9a865f3182c24f4ba',
    'CPU_GATE.json': '2687c787d90fdcec33ce2389263a9b3f3c0a201cf4be8ff443a60357c6a60289'}
DEADLINE = 1789634854


def write(path, value):
    community.write(path, value)


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=takeover.sha(path))


def native_live(config, expected):
    script = '''import hashlib,json,time
from pathlib import Path
entry=EXPECTED
process=Path('/proc')/str(entry['pid'])
fields=(process/'stat').read_text().rsplit(')',1)[1].split()
argv=(process/'cmdline').read_bytes().rstrip(b'\\0').decode().split('\\0')
assert fields[19]==entry['start_ticks'] and argv==entry['argv'] and fields[0] not in ('Z','X','T','t')
for key in ('config_ref','plan_ref'):
 path=Path(entry[key]['path']);assert path.stat().st_size<1048576
 assert hashlib.sha256(path.read_bytes()).hexdigest()==entry[key]['sha256']
print(json.dumps(dict(root=entry['root'],pid=entry['pid'],start_ticks=fields[19],state=fields[0],observed_unix=time.time(),config_ref=entry['config_ref'],plan_ref=entry['plan_ref'])))
'''.replace('EXPECTED', repr(expected))
    return parent.remote(REPOSITORY, config, script)


def no_competitor(config, expected_pid):
    matches = []
    processes = list(Path('/proc').iterdir())
    takeover.require(len(processes) <= 20000, 'process_census_limit')
    for process in processes:
        if not process.name.isdigit():
            continue
        try:
            raw = (process/'cmdline').read_bytes()
            if b'gpu.orch_r153_community_parents\0' not in raw:
                continue
            argv = raw.rstrip(b'\0').decode().split('\0')
            if '-m' not in argv or argv[argv.index('-m')+1] != 'gpu.orch_r153_community_parents':
                continue
            candidate = json.loads(takeover.read_file(argv[argv.index('--config')+1]))
            if candidate['root'] == config['root']:
                matches.append(int(process.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    takeover.require(matches == [expected_pid], 'one_existing_parent_leader_only')


def main():
    for name, expected in EXPECTED.items():
        takeover.require(takeover.sha(STAGE/name) == expected, 'Main_exact_stage_GO')
    takeover.require(takeover.sha(REPOSITORY/'gpu/orch_r166_parent_policy.py') ==
        '2874e7eb436459c207f48c218a267e86e3877d270aba830e3e465c1db382deee', 'Main_exact_policy_GO')
    OUTPUT.mkdir(mode=0o700)
    write(OUTPUT/'MAIN_GO.json', dict(schema='R167_SCOPED_PARENT_ROLLOUT_GO_V1', confirmed_by='Main',
        branches=['C1', 'C3', 'C2', 'C4', 'C5'], stage_pins=EXPECTED,
        policy_sha256='2874e7eb436459c207f48c218a267e86e3877d270aba830e3e465c1db382deee',
        observed_unix=time.time(), monitor_deadline_unix=DEADLINE,
        permitted_signals='verified parent pidfd SIGSTOP; busy/uncertain SIGCONT; clean SIGTERM then SIGCONT',
        prohibited='native/provider signals, SIGKILL, expiry changes, hot edits, uncertain replay',
        authorization='Main scoped GO in current conversation; operational gate creation authorized'))
    tests=['tests/test_orch_r167_parent_takeover.py', 'tests/test_orch_r166_parent_policy.py',
        'tests/test_orch_r166_parent_snapshot.py', 'tests/test_orch_r153_community_parents.py']
    paths=[REPOSITORY/'gpu/orch_r167_parent_takeover.py', Path(__file__), *[REPOSITORY/name for name in tests]]
    pins={str(path): takeover.sha(path) for path in paths}
    test=subprocess.run([sys.executable, '-m', 'pytest', '-q', *tests], cwd=REPOSITORY,
        capture_output=True, text=True, timeout=60)
    with (OUTPUT/'CPU_TEST_OUTPUT.txt').open('x') as stream:
        stream.write(test.stdout+test.stderr)
    passed=test.returncode==0 and all(takeover.sha(path)==expected for path,expected in pins.items())
    write(OUTPUT/'CPU_GATE.json', dict(status='PASS' if passed else 'FAIL', execution_kind='CPU_ONLY',
        exit_code=test.returncode, pins=pins, output=ref(OUTPUT/'CPU_TEST_OUTPUT.txt'), finished_unix=time.time()))
    takeover.require(passed, 'lifecycle_CPU_gate_before_signals')
    metadata=json.loads((REPOSITORY/'research_loop/workers/r166_parenting_update_20260917/LOCAL_PARENT_METADATA.json').read_bytes())
    native_metadata=json.loads((REPOSITORY/'research_loop/workers/r166_parenting_update_20260917/REMOTE_CHILD_METADATA.json').read_bytes())
    parents={entry['config']['branch']:entry for entry in metadata['parents'] if entry['config']['branch'] in community.LEARNERS}
    natives={entry['root']:entry for entry in native_metadata['nodes']['ovx3']['matches']
             if 'native' in entry['argv'] and 'orch_r153_community_' in entry['root']}
    old_gate_path=Path(parents['C1']['argv'][parents['C1']['argv'].index('--gate')+1])
    old_gate=json.loads(takeover.read_file(old_gate_path))
    gate=copy.deepcopy(old_gate)
    gate['operational_go']=ref(OUTPUT/'MAIN_GO.json')
    gate['lifecycle_cpu_gate']=ref(OUTPUT/'CPU_GATE.json')
    configs={}
    for branch, observed in parents.items():
        config_path=STAGE/(branch+'_'+str(observed['pid']))/'CONFIG.json'
        config=json.loads(takeover.read_file(config_path))
        configs[branch]=(config_path,config)
        gate['parents'][branch].update(config_sha256=takeover.sha(config_path), output=str((OUTPUT/branch/'parent').resolve()))
    gate_path=OUTPUT/'PARENT_GATE.json'
    write(gate_path,gate)
    gate_hash=takeover.sha(gate_path)
    results=[]
    for branch in ('C1','C3','C2','C4','C5'):
        takeover.require(time.time()<DEADLINE,'bounded_operation_deadline')
        observed=parents[branch]
        config_path,config=configs[branch]
        directory=OUTPUT/branch
        directory.mkdir(mode=0o700)
        new_output=directory/'parent'
        config_check,unused=community.verify_gate(config_path,REPOSITORY,new_output,gate_path,gate_hash)
        expected_remote=community.remote_source_pins(gate,config['node'])
        script=('import json;from pathlib import Path;from gpu.orch_r133_programme_parent import sha;'
            'root=Path('+repr(config['source_root'])+');pins='+repr(expected_remote)+';'
            'assert all(sha(root/name)==value for name,value in pins.items());print(json.dumps({"verified":True}))')
        takeover.require(parent.remote(REPOSITORY,config,script)=={'verified':True},'same_remote_transport_closure')
        transport=parent.transport_preflight(REPOSITORY,config)
        child=native_live(config,natives[config['root']])
        write(directory/'PREFLIGHT.json',dict(child=child,transport=transport,gate=ref(gate_path),config=ref(config_path),observed_unix=time.time()))
        environment=dict(item.split('=',1) for item in (Path('/proc')/str(observed['pid'])/'environ').read_bytes().decode().split('\0') if item)
        takeover.require(bool(environment.get('NVIDIA_API_KEY')),'same_existing_parent_provider_environment')
        environment['PYTHONDONTWRITEBYTECODE']='1'
        command=list(observed['argv'])
        for flag,value in (('--config',str(config_path)),('--output',str(new_output)),('--gate',str(gate_path)),('--gate-sha256',gate_hash)):
            command[command.index(flag)+1]=value
        binding=dict(branch=branch,pid=observed['pid'],start_ticks=observed['start_ticks'],argv=observed['argv'],
            config=observed['config_ref'],source=observed['source_ref'],output=observed['output'],root=config['root'])
        startup_probe=('from pathlib import Path;from gpu.orch_r153_community_parents import verify_gate;'
            'verify_gate(Path('+repr(str(config_path))+'),Path('+repr(str(REPOSITORY))+'),Path('
            +repr(str(new_output))+'),Path('+repr(str(gate_path))+'),'+repr(gate_hash)+');print("PREFLIGHT_OK")')
        executable_probe=subprocess.run([command[0],'-B','-c',startup_probe],cwd=observed['cwd'],env=environment,
            stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=30)
        takeover.require(executable_probe.returncode==0 and executable_probe.stdout.strip()=='PREFLIGHT_OK',
            'exact_successor_interpreter_preflight')
        write(directory/'EXECUTABLE_PREFLIGHT.json',dict(status='PASS',executable=command[0],observed_unix=time.time()))
        launched=False
        for attempt in range(20):
            no_competitor(config,observed['pid'])
            handle=None
            try:
                with takeover.quiesce(binding) as handle:
                    manifest=takeover.settled_attempts(observed['output'])
                    new_output.mkdir(mode=0o700)
                    takeover.copy_attempts(observed['output'],new_output,manifest)
                    write(directory/'LEDGER_TRANSFER.json',manifest)
                    write(directory/'QUIESCED.json',dict(binding=binding,observed_unix=time.time(),attempt=attempt,
                        all_task_children_empty=True,all_attempt_results_settled=True,transfer=ref(directory/'LEDGER_TRANSFER.json')))
                    handle.terminate()
                lock=os.open(Path(observed['output'])/'PARENT.lock',os.O_RDWR|os.O_NOFOLLOW)
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                write(directory/'OLD_PARENT_EXIT.json',dict(pid=observed['pid'],start_ticks=observed['start_ticks'],
                    pidfd_exit_verified=True,old_lock_exclusively_acquired=True,observed_unix=time.time()))
                log=(directory/'PARENT.log').open('xb')
                process=subprocess.Popen(command,cwd=observed['cwd'],env=environment,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                log.close()
                time.sleep(2)
                if process.poll() is not None:
                    takeover.require(takeover.settled_attempts(new_output)==manifest,'failed_successor_new_attempts_do_not_replay')
                    os.close(lock)
                    fallback_log=(directory/'RESTORED_ORIGINAL.log').open('xb')
                    fallback=subprocess.Popen(observed['argv'],cwd=observed['cwd'],env=environment,stdin=subprocess.DEVNULL,
                        stdout=fallback_log,stderr=subprocess.STDOUT,start_new_session=True)
                    fallback_log.close()
                    write(directory/'RESTORED_ORIGINAL.json',dict(pid=fallback.pid,reason='successor_failed_before_new_attempt',observed_unix=time.time()))
                    raise RuntimeError('successor_failed_original_restored')
                successor=takeover.identity(process.pid)
                write(directory/'STARTED.json',dict(successor=successor,command=command,gate=ref(gate_path),
                    config=ref(config_path),provider_environment_inherited_without_logging=True,observed_unix=time.time()))
                os.close(lock)
                no_competitor(config,process.pid)
                launched=True
                results.append(dict(branch=branch,status='STARTED_NOT_DELIVERY',pid=process.pid,receipt=ref(directory/'STARTED.json')))
                break
            except ValueError as error:
                state='HANDOFF_ERROR_REQUIRES_RECONCILIATION' if handle is not None and handle.terminated else 'RESUMED_DEFERRED'
                write(directory/f'DEFERRED_{attempt:03d}.json',dict(status=state,error=str(error),observed_unix=time.time()))
                if new_output.exists():
                    raise
                time.sleep(1)
        if not launched:
            results.append(dict(branch=branch,status='OLD_PARENT_REMAINS_DEFERRED'))
        write(directory/'RESULT.json',results[-1])
        print(json.dumps(results[-1]),flush=True)
    write(OUTPUT/'ROLLOUT_RESULT.json',dict(results=results,finished_unix=time.time(),no_native_signals=True))


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('rollout_interrupted_resume_quiesced_parent')
    signal.signal(signal.SIGTERM,interrupted)
    main()
