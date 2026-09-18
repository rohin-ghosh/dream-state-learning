"""Main 08:37-authorized R168 parent-only rollout; C2/C3/C4 first."""

import argparse
from contextlib import contextmanager
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import tarfile
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as takeover
from gpu import orch_r167_parent_watchdog as watchdog
from gpu import orch_r168_manual_parent_turn as manual
from gpu import orch_r168_parent_rollout as transaction


OUTPUT = Path(__file__).resolve().parent
STAGE = OUTPUT.parent
ROOT = STAGE.parents[2]
CANDIDATE = STAGE
PRIOR = ROOT/'research_loop/workers/r167_parent_policy_candidates_20260917/R154_ATTENTION_V2/ROLLOUT'
INDEX_SHA = '7369963ca25e3963101f40cb5eadaa9360bbde68e0321d049f7c7e990b4cc88d'
CPU_SHA = '4d1e31e1cda3d9e5d3198dcd73054f701b29e1dfc9318cfcb95807d4f27c82e0'
PATCH_SHA = 'ee9c0af3a618695f51eea13c56ba2a139827c5abf8bc161dac51834662c11367'
DEADLINE = 1789636920


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=takeover.sha(path))


def write(path, value):
    community.write(path, value)


def check_current_source(index):
    assert takeover.sha(CANDIDATE/'INDEX.json') == INDEX_SHA
    assert takeover.sha(CANDIDATE/'CPU_GATE.json') == CPU_SHA
    gate = json.loads(takeover.read_file(index['gate_draft']['path']))
    assert takeover.sha(index['gate_draft']['path']) == index['gate_draft']['sha256']
    for side, pins in (('local_source', gate['source_pins']),
                       ('remote_source', gate['remote_source_pins']['ovx3'])):
        for name, expected in pins.items():
            assert takeover.sha(CANDIDATE/side/name) == expected
        assert pins['gpu/orch_r153_community_parents.py'] == PATCH_SHA
    return gate


def prepare():
    index = json.loads(takeover.read_file(CANDIDATE/'INDEX.json'))
    draft = check_current_source(index)
    review_path = ROOT/'research_loop/workers/R168_COMMUNITY_PROMPT_REVIEW.md'
    review = takeover.read_file(review_path).decode()
    assert 'PASS for attempt3' in review and INDEX_SHA in review
    authority = OUTPUT/'MAIN_GO.json'
    write(authority, dict(schema='R168_MAIN_PARENT_OPERATIONAL_GO_V1', authorized_by='Main',
        authority_kind='executor_authorization_under_standing_user_scope_not_human_ratification',
        issued_utc='2026-09-17T08:37:00Z', index=ref(CANDIDATE/'INDEX.json'),
        cpu=ref(CANDIDATE/'CPU_GATE.json'), patched_source_sha256=PATCH_SHA,
        review=ref(review_path), first_scope=['C2','C3','C4'],
        C1_condition='manual229eb2802b92494e82a346dd0287e666_verified_rendered',
        C5_condition='Banach_exact_sleep28_recovery_LOADED_verified',
        no_native_service_wall_recipe_changes=True, busy_or_unknown='defer_original_alive',
        operation_deadline_unix=DEADLINE))
    test_names = ['tests/test_orch_r168_parent_rollout.py', 'tests/test_orch_r167_parent_takeover.py',
        'tests/test_orch_r167_parent_watchdog.py', 'tests/test_orch_r168_manual_parent_turn.py',
        'tests/test_orch_r168_community_prompt_patch.py']
    names = test_names + ['gpu/orch_r168_parent_rollout.py', 'gpu/orch_r167_parent_takeover.py',
        'gpu/orch_r167_parent_watchdog.py', 'gpu/orch_r168_manual_parent_turn.py',
        'gpu/orch_r168_community_prompt_patch.py', str(Path(__file__))]
    pins = {name: takeover.sha(ROOT/name) for name in names}
    command = ['uv','run','--with','pytest','--with','pytest-subtests','python','-m','pytest','-q',*test_names]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
    (OUTPUT/'CPU_OUTPUT.txt').write_text(result.stdout+result.stderr)
    assert result.returncode == 0 and all(takeover.sha(ROOT/name) == expected for name, expected in pins.items())
    write(OUTPUT/'CPU_GATE.json', dict(status='PASS', execution_kind='CPU_ONLY', command=command,
        pins=pins, output=ref(OUTPUT/'CPU_OUTPUT.txt'), finished_unix=time.time()))
    archive = io.BytesIO()
    remote_pins = draft['remote_source_pins']['ovx3']
    with tarfile.open(fileobj=archive, mode='w:gz') as package:
        for name, expected in sorted(remote_pins.items()):
            path = CANDIDATE/'remote_source'/name
            assert takeover.sha(path) == expected
            package.add(path, arcname=name, recursive=False)
    raw = archive.getvalue()
    assert len(raw) <= 4*1024*1024
    archive_path = OUTPUT/'REMOTE_SOURCE.tar.gz'
    with archive_path.open('xb') as stream:
        stream.write(raw)
    remote_root = index['proposed_remote_source']
    script = '''import hashlib,io,json,os,sys,tarfile
from pathlib import Path
root=Path(REMOTE_ROOT);pins=PINS;expected=ARCHIVE_SHA
raw=sys.stdin.buffer.read(4194305);assert len(raw)<=4194304 and hashlib.sha256(raw).hexdigest()==expected
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 members=archive.getmembers();assert len(members)==len(pins) and {entry.name for entry in members}==set(pins)
 assert all(entry.isfile() and 0<=entry.size<=16777216 for entry in members)
 assert sum(entry.size for entry in members)<=33554432
 assert all(not Path(entry.name).is_absolute() and '..' not in Path(entry.name).parts for entry in members)
 contents={entry.name:archive.extractfile(entry).read() for entry in members}
 assert all(hashlib.sha256(contents[name]).hexdigest()==expected for name,expected in pins.items())
 root.parent.mkdir(mode=0o700);root.mkdir(mode=0o700)
 for entry in members:
  destination=root/entry.name;destination.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
  descriptor=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,entry.mode&0o777)
  with os.fdopen(descriptor,'wb') as stream:stream.write(contents[entry.name]);stream.flush();os.fsync(stream.fileno())
 assert {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}==set(pins)
 assert all(not (root/name).is_symlink() and hashlib.sha256((root/name).read_bytes()).hexdigest()==expected for name,expected in pins.items())
sys.path.insert(0,str(root))
from gpu import orch_r153_community_parents as module
from gpu import orch_r127_pilot_console as console
assert Path(module.__file__).resolve()==root/'gpu/orch_r153_community_parents.py'
assert Path(console.__file__).resolve()==root/'gpu/orch_r127_pilot_console.py' and callable(console.publish_parent)
print(json.dumps(dict(status='RECEIVING_VERIFIED',source_root=str(root),pins=pins,files=len(pins),
 archive_sha256=hashlib.sha256(raw).hexdigest(),python=sys.executable,uid=os.getuid(),gid=os.getgid(),
 community_module=str(Path(module.__file__).resolve()),console_module=str(Path(console.__file__).resolve()),
 provider_calls=0,native_mutations=0)))
'''.replace('REMOTE_ROOT', repr(remote_root)).replace('PINS', repr(remote_pins)).replace(
        'ARCHIVE_SHA', repr(hashlib.sha256(raw).hexdigest()))
    command = ['bash', str(ROOT/'gpu/ovx3_ssh.sh'), 'PYTHONDONTWRITEBYTECODE=1 python3 -c '+shlex.quote(script)]
    receiving = subprocess.run(command, input=raw, cwd=ROOT, capture_output=True, timeout=45)
    if receiving.returncode:
        write(OUTPUT/'RECEIVING_FAILED.json', dict(exit_code=receiving.returncode,
            stderr=receiving.stderr.decode()[-4000:], no_signals=True, retry_requires_reconciliation=True))
        raise ValueError('receiving_failed_no_parent_signals')
    receipt = json.loads(receiving.stdout)
    assert receipt['status'] == 'RECEIVING_VERIFIED' and receipt['pins'] == remote_pins
    write(OUTPUT/'RECEIVING.json', dict(receipt, observed_unix=time.time(), archive=ref(archive_path)))
    env_source = ROOT/'gpu/hosts.env'
    assert env_source.is_file() and env_source == env_source.resolve()
    env_link = CANDIDATE/'local_source/gpu/hosts.env'
    env_link.symlink_to(env_source)
    write(OUTPUT/'EXISTING_TRANSPORT_ENV_BINDING.json', dict(kind='symlink_to_unchanged_existing_runtime_configuration',
        path=str(env_link), target=str(env_source), target_sha256=takeover.sha(env_source),
        credential_copied=False, credential_modified=False, not_a_source_code_patch=True))
    gate = copy.deepcopy(draft)
    gate['status'] = 'MAIN_BOUND'
    gate['operational_go'] = ref(authority)
    gate['lifecycle_cpu_gate'] = ref(OUTPUT/'CPU_GATE.json')
    gate['actual_receiving'] = ref(OUTPUT/'RECEIVING.json')
    gate['existing_transport_configuration'] = ref(OUTPUT/'EXISTING_TRANSPORT_ENV_BINDING.json')
    write(OUTPUT/'PARENT_GATE.json', gate)
    with (ROOT/'research_loop/COORDINATION.md').open('a') as stream:
        stream.write('\n[Builder] 2026-09-17 '+time.strftime('%H:%M:%S',time.gmtime())+' UTC — R168 C2/C3/C4 parent-only rollout: '
            'own focused lifecycle/source CPU PASS '+str(OUTPUT/'CPU_GATE.json')+' SHA'+takeover.sha(OUTPUT/'CPU_GATE.json')+
            '; Main08:37 exact authority and Galileo attempt3PASS bound; actual67-file remote receiving/import verified '+
            str(OUTPUT/'RECEIVING.json')+'. New Main-bound gate '+takeover.sha(OUTPUT/'PARENT_GATE.json')+
            '. No signals yet. C1 waits manual rendering; C5 waits Banach sleep28LOADED. Existing hosts.env referenced '
            'unchanged for sanctioned wrapper, no credential copy. No native/service/wall changes.\n')


class Operations:
    def __init__(self, branch):
        self.branch = branch
        self.directory = OUTPUT/branch
        self.directory.mkdir(mode=0o700)
        index = json.loads(takeover.read_file(CANDIDATE/'INDEX.json'))
        self.new_output = Path(index['candidates'][branch]['output'])

    def no_competitor(self, expected_pid):
        matches = []
        for process in Path('/proc').iterdir():
            if not process.name.isdigit():
                continue
            try:
                raw = (process/'cmdline').read_bytes()
                if b'parent' not in raw or b'--config\0' not in raw:
                    continue
                argv = raw.rstrip(b'\0').decode().split('\0')
                candidate = json.loads(takeover.read_file(argv[argv.index('--config')+1]))
                if candidate.get('root') == self.config['root']:
                    matches.append(int(process.name))
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
        assert matches == ([expected_pid] if expected_pid else []), ('competing_parent', matches)

    def preflight(self):
        assert time.time() < DEADLINE and self.branch in ('C2','C3','C4')
        self.index = json.loads(takeover.read_file(CANDIDATE/'INDEX.json'))
        check_current_source(self.index)
        candidate = self.index['candidates'][self.branch]
        assert takeover.sha(candidate['predecessor_start']['path']) == candidate['predecessor_start']['sha256']
        self.started = json.loads(takeover.read_file(candidate['predecessor_start']['path']))
        self.original = self.started['successor']
        self.config_path = CANDIDATE/self.branch/'CONFIG.json'
        assert takeover.sha(self.config_path) == candidate['config']['sha256']
        self.config = json.loads(takeover.read_file(self.config_path))
        self.old_config = json.loads(takeover.read_file(self.started['config']['path']))
        assert {key for key in self.config if self.config[key] != self.old_config[key]} == {'cadence_responses','source_root'}
        assert time.time() < self.config['hard_end_unix'] == candidate['original_wall']
        self.old_output = Path(candidate['predecessor_output'])
        self.binding = dict(branch=self.branch, pid=self.original['pid'], start_ticks=self.original['start_ticks'],
            argv=self.started['command'], config=self.started['config'], source=ref(ROOT/'gpu/orch_r153_community_parents.py'),
            output=str(self.old_output), root=self.config['root'])
        takeover.verify_identity(self.binding, takeover.identity(self.original['pid']))
        takeover.verify_files(self.binding)
        self.no_competitor(self.original['pid'])
        process = Path('/proc')/str(self.original['pid'])
        self.old_cwd = str((process/'cwd').resolve())
        self.old_environment = dict(entry.split('=',1) for entry in (process/'environ').read_bytes().decode().split('\0') if entry)
        assert self.old_environment.get('NVIDIA_API_KEY')
        self.environment = dict(self.old_environment, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(CANDIDATE/'local_source'))
        self.command = list(self.started['command'])
        self.gate_path = OUTPUT/'PARENT_GATE.json'
        self.gate_sha = takeover.sha(self.gate_path)
        for flag, value in (('--config',str(self.config_path)),('--repository',str(CANDIDATE/'local_source')),
                ('--output',str(self.new_output)),('--gate',str(self.gate_path)),('--gate-sha256',self.gate_sha)):
            self.command[self.command.index(flag)+1] = value
        child = json.loads(takeover.read_file(PRIOR/self.branch/'PREFLIGHT.json'))['child']
        script = '''import hashlib,json,time
from pathlib import Path
child=CHILD;process=Path('/proc')/str(child['pid']);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
assert fields[19]==child['start_ticks'] and fields[0] not in ('Z','X','T','t')
for key in ('config_ref','plan_ref'):
 path=Path(child[key]['path']);assert path.stat().st_size<1048576
 assert hashlib.sha256(path.read_bytes()).hexdigest()==child[key]['sha256']
print(json.dumps(dict(child=child,observed_unix=time.time(),state=fields[0])))
'''.replace('CHILD', repr(child))
        remote_child = parent.remote(ROOT, self.old_config, script)
        probe = ('from pathlib import Path;import json;from gpu import orch_r153_community_parents as module;'
            'from gpu import orch_r133_programme_parent as parent;'
            'config,gate=module.verify_gate(Path('+repr(str(self.config_path))+'),Path('+repr(str(CANDIDATE/'local_source'))
            +'),Path('+repr(str(self.new_output))+'),Path('+repr(str(self.gate_path))+'),'+repr(self.gate_sha)+');'
            'print(json.dumps(parent.transport_preflight(Path('+repr(str(CANDIDATE/'local_source'))+'),config)))')
        result = subprocess.run([self.command[0],'-B','-c',probe], cwd=CANDIDATE/'local_source',env=self.environment,
            capture_output=True,text=True,timeout=50)
        assert result.returncode == 0, ('successor_preflight',result.stderr[-2000:])
        write(self.directory/'OPERATIONAL_GO.json', dict(main_go=ref(OUTPUT/'MAIN_GO.json'),
            branch=self.branch, binding=self.binding, candidate_config=ref(self.config_path),
            actual_gate=ref(self.gate_path), received=ref(OUTPUT/'RECEIVING.json'), child=remote_child,
            executable_transport=json.loads(result.stdout), observed_unix=time.time(),
            all_preflight_before_signals=True, no_native_signals=True))

    def quiesce(self):
        deadline = min(time.monotonic()+30, time.monotonic()+max(0,DEADLINE-time.time()))
        while time.monotonic() < deadline:
            takeover.verify_identity(self.binding,takeover.identity(self.original['pid']))
            tasks = list((Path('/proc')/str(self.original['pid'])/'task').iterdir())
            assert 0 < len(tasks) <= 128
            if all(not (task/'children').read_text().strip() for task in tasks):
                break
            time.sleep(0.1)
        else:
            raise ValueError('no_childless_gap_defer')
        self.no_competitor(self.original['pid'])
        return watchdog.quiesce(self.binding, scope_verifier=takeover.verify_identity, seconds=30)

    def settled(self):
        return manual.settled_and_rendered(self.old_output)

    def preserve(self, manifest):
        self.manifest = manifest
        self.new_output.mkdir(mode=0o700)
        takeover.copy_attempts(self.old_output,self.new_output,manifest)
        write(self.directory/'LEDGER_TRANSFER.json',manifest)
        write(self.directory/'QUIESCED.json',dict(binding=self.binding,all_results_settled=True,
            old_publications_rendered=True,all_owned_task_children_empty=True,observed_unix=time.time(),
            transfer=ref(self.directory/'LEDGER_TRANSFER.json')))

    @contextmanager
    def old_lock(self):
        with community.parent_lock(self.old_output):
            yield

    def confirm_exit(self, manifest):
        self.no_competitor(None)
        assert takeover.settled_attempts(self.old_output) == manifest
        assert takeover.settled_attempts(self.new_output) == manifest
        write(self.directory/'OLD_PARENT_EXIT.json',dict(pid=self.original['pid'],start_ticks=self.original['start_ticks'],
            pidfd_exit_verified=True,old_lock_exclusively_acquired=True,observed_unix=time.time()))

    def start_successor(self):
        log = (self.directory/'PARENT.log').open('xb')
        process = subprocess.Popen(self.command,cwd=CANDIDATE/'local_source',env=self.environment,
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        log.close()
        return process

    def verify_successor(self, process):
        time.sleep(1)
        assert process.poll() is None, 'successor_exited_before_receipt'
        observed = takeover.identity(process.pid)
        assert observed['argv'] == self.command and observed['state'] not in ('T','t','Z','X')
        self.no_competitor(process.pid)

    def record_started(self, process):
        write(self.directory/'STARTED.json',dict(successor=takeover.identity(process.pid),command=self.command,
            config=ref(self.config_path),gate=ref(self.gate_path),observed_unix=time.time(),
            output=str(self.new_output),ledger=ref(self.directory/'LEDGER_TRANSFER.json'),
            source_root=str(CANDIDATE/'local_source'),provider_environment_inherited_without_logging=True,
            status='STARTED_NOT_DELIVERY',no_native_changes=True))

    def reconcile_failed_handoff(self, process):
        if process is not None and process.poll() is None:
            write(self.directory/'LIVE_SUCCESSOR_REQUIRES_OBSERVATION.json',dict(pid=process.pid,
                identity=takeover.identity(process.pid),no_duplicate_restart=True,observed_unix=time.time()))
            return
        self.no_competitor(None)
        assert takeover.settled_attempts(self.new_output) == self.manifest, 'new_attempt_uncertainty_no_old_replay'
        log = (self.directory/'ORIGINAL_RESTORED.log').open('xb')
        process = subprocess.Popen(self.started['command'],cwd=self.old_cwd,env=self.old_environment,
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        log.close()
        time.sleep(1)
        assert process.poll() is None
        write(self.directory/'ORIGINAL_RESTORED.json',dict(successor=takeover.identity(process.pid),
            original_command=self.started['command'],preserved_ledger=ref(self.directory/'LEDGER_TRANSFER.json'),
            no_new_attempts=True,observed_unix=time.time()))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','execute'])
    args=parser.parse_args()
    if args.action=='prepare':
        prepare()
        return
    assert takeover.sha(CANDIDATE/'INDEX.json')==INDEX_SHA
    assert time.time()<DEADLINE
    cpu=json.loads(takeover.read_file(OUTPUT/'CPU_GATE.json'))
    assert cpu['status']=='PASS' and all(takeover.sha(ROOT/name)==expected for name,expected in cpu['pins'].items())
    for branch in ('C2','C3','C4'):
        try:
            transaction.handoff(Operations(branch))
            print(json.dumps(dict(branch=branch,status='STARTED_NOT_DELIVERED',receipt=ref(OUTPUT/branch/'STARTED.json'))),flush=True)
        except Exception as error:
            write(OUTPUT/branch/'DEFERRED_OR_FAILED.json',dict(error_type=type(error).__name__,error=str(error)[:2000],
                observed_unix=time.time(),no_blind_retry=True))
            print(json.dumps(dict(branch=branch,status='DEFERRED_OR_FAILED',error=str(error)[:300])),flush=True)
    write(OUTPUT/'C1_DEFERRED.json',dict(reason='manual229eb_not_yet_verified_rendered',no_signals=True,observed_unix=time.time()))
    write(OUTPUT/'C5_DEFERRED.json',dict(reason='Banach_exact_sleep28_recovery_LOADED_required',no_signals=True,observed_unix=time.time()))


if __name__=='__main__':
    def interrupted(signum, frame):
        raise InterruptedError('bounded_rollout_operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    main()
