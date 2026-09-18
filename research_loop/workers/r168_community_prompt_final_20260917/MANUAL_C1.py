"""Detached, bounded, Main-authorized one-turn parent custody; never native signals."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as takeover
from gpu import orch_r167_parent_watchdog as watchdog
from gpu import orch_r168_manual_parent_turn as manual


ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
PRIOR = ROOT/'research_loop/workers/r167_parent_policy_candidates_20260917/R154_ATTENTION_V2/ROLLOUT/C1'
OUTPUT = STAGE/'MANUAL_C1_CUSTODY_ATTEMPT2'


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=takeover.sha(path))


def write(name, value):
    community.write(OUTPUT/name, value)


class Operations:
    def preflight(self):
        self.started = json.loads(takeover.read_file(PRIOR/'STARTED.json'))
        self.identity = self.started['successor']
        self.command = self.started['command']
        assert self.identity['pid'] == 349597 and self.identity['start_ticks'] == '173953514'
        self.config_path = Path(self.started['config']['path'])
        self.parent_output = PRIOR/'parent'
        self.config, self.gate = community.verify_gate(self.config_path, ROOT, self.parent_output,
            Path(self.started['gate']['path']), self.started['gate']['sha256'])
        self.binding = dict(branch='C1', pid=self.identity['pid'], start_ticks=self.identity['start_ticks'],
            argv=self.command, config=self.started['config'], source=ref(ROOT/'gpu/orch_r153_community_parents.py'),
            output=str(self.parent_output), root=self.config['root'])
        takeover.verify_identity(self.binding, takeover.identity(self.identity['pid']))
        self.no_competitor(self.identity['pid'])
        process = Path('/proc')/str(self.identity['pid'])
        self.cwd = str((process/'cwd').resolve())
        self.environment = dict(entry.split('=', 1) for entry in (process/'environ').read_bytes().decode().split('\0') if entry)
        assert self.environment.get('NVIDIA_API_KEY')
        self.environment['PYTHONDONTWRITEBYTECODE'] = '1'
        basis_path = ROOT/'research_loop/workers/r168_targeted_replay/C1_EARLIER_TRAIN_SAMPLE.json'
        basis = json.loads(takeover.read_file(basis_path))
        rows = {row['segment']: row for row in basis['rows']}
        assert 'forest' in rows[74]['TRAIN_excerpt'].lower() and 'left' in rows[77]['TRAIN_excerpt'].lower()
        child = json.loads(takeover.read_file(PRIOR/'PREFLIGHT.json'))['child']
        pins = community.remote_source_pins(self.gate, self.config['node'])
        script = '''import hashlib,json,time
from pathlib import Path
child=CHILD;basis=BASIS;source=Path(SOURCE);pins=PINS
process=Path('/proc')/str(child['pid']);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
assert fields[19]==child['start_ticks'] and fields[0] not in ('Z','X','T','t')
for key in ('config_ref','plan_ref'):
 path=Path(child[key]['path']);assert path.stat().st_size<1048576
 assert hashlib.sha256(path.read_bytes()).hexdigest()==child[key]['sha256']
for name,expected in pins.items():
 path=source/name;assert path.stat().st_size<16777216
 assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
path=Path(basis['path']);assert path.stat().st_size==basis['bytes'] and basis['bytes']<16777216
assert hashlib.sha256(path.read_bytes()).hexdigest()==basis['sha256']
print(json.dumps(dict(child=child,basis=basis,observed_unix=time.time(),source_verified=True)))
'''.replace('CHILD', repr(child)).replace('BASIS', repr(basis['record_ref'])).replace(
            'SOURCE', repr(self.config['source_root'])).replace('PINS', repr(pins))
        remote = parent.remote(ROOT, self.config, script)
        parent.transport_preflight(ROOT, self.config)
        probe = ('from pathlib import Path;from gpu.orch_r153_community_parents import verify_gate;'
            'verify_gate(Path('+repr(str(self.config_path))+'),Path('+repr(str(ROOT))+'),Path('
            +repr(str(self.parent_output))+'),Path('+repr(self.started['gate']['path'])+'),'
            +repr(self.started['gate']['sha256'])+');print("PASS")')
        result = subprocess.run([self.command[0], '-B', '-c', probe], cwd=self.cwd, env=self.environment,
            capture_output=True, text=True, timeout=20)
        assert result.returncode == 0 and result.stdout.strip() == 'PASS'
        write('PREFLIGHT.json', dict(binding=self.binding, child_and_source=remote,
            original_start=ref(PRIOR/'STARTED.json'), sourcebasis=ref(basis_path),
            same_executable_restart_checked=True, observed_unix=time.time()))

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
            except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
                continue
        assert matches == ([expected_pid] if expected_pid else []), ('competing_parent', matches)

    def quiesce(self):
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            takeover.verify_identity(self.binding, takeover.identity(self.identity['pid']))
            tasks = list((Path('/proc')/str(self.identity['pid'])/'task').iterdir())
            assert 0 < len(tasks) <= 128
            if all(not (task/'children').read_text().strip() for task in tasks):
                break
            time.sleep(0.1)
        else:
            raise ValueError('no_childless_parent_gap_defer')
        self.no_competitor(self.identity['pid'])
        return watchdog.quiesce(self.binding, scope_verifier=takeover.verify_identity, seconds=30)

    def settled(self):
        return manual.settled_and_rendered(self.parent_output)

    def preserve(self, manifest):
        self.manifest = manifest
        write('PRESERVED_LEDGER.json', manifest)
        write('QUIESCED.json', dict(binding=self.binding, no_provider_children=True,
            all_results_settled_and_prior_publications_rendered=True, observed_unix=time.time()))

    @contextmanager
    def exclusive_lock(self):
        with community.parent_lock(self.parent_output):
            yield

    def confirm_exit(self, manifest):
        self.no_competitor(None)
        assert takeover.settled_attempts(self.parent_output) == manifest
        write('OLD_PARENT_EXIT.json', dict(pid=self.identity['pid'], start_ticks=self.identity['start_ticks'],
            pidfd_exit_verified=True, old_lock_exclusively_acquired=True, observed_unix=time.time()))

    def write_intent(self, message):
        write('MANUAL_PUBLICATION_INTENT.json', dict(author='Main', speaker='Astra',
            type='MANUAL_TRAIN_PARENTING', text=message, text_sha256=hashlib.sha256(message.encode()).hexdigest(),
            sourcebasis=ref(ROOT/'research_loop/workers/r168_targeted_replay/C1_EARLIER_TRAIN_SAMPLE.json'),
            prospective_epoch='R168_MAIN_C1_OBJECT_ATTENTION_20260917', original96='SILENT_UNCHANGED',
            provider_result=False, retries=0, created_unix=time.time()))

    def publish(self, message):
        return parent.publish(ROOT, self.config, message)

    def record_publication(self, publication):
        write('PUBLICATION.json', dict(status='PUBLISHED_NOT_YET_RENDER_VERIFIED',
            author='Main', speaker='Astra', type='MANUAL_TRAIN_PARENTING', publication=publication,
            intent=ref(OUTPUT/'MANUAL_PUBLICATION_INTENT.json'), observed_unix=time.time()))

    def restart_unchanged(self):
        self.no_competitor(None)
        assert takeover.settled_attempts(self.parent_output) == self.manifest
        log = (OUTPUT/'RESUMED_PARENT.log').open('xb')
        process = subprocess.Popen(self.command, cwd=self.cwd, env=self.environment,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        log.close()
        time.sleep(1)
        assert process.poll() is None, 'unchanged_parent_restart_failed'
        write('PARENT_RESUMED.json', dict(successor=takeover.identity(process.pid), command=self.command,
            config=self.started['config'], gate=self.started['gate'], original_output=str(self.parent_output),
            observed_unix=time.time(), preserved_ledger=ref(OUTPUT/'PRESERVED_LEDGER.json'),
            provider_environment_inherited_without_logging=True, no_policy_or_native_change=True))


def main():
    previous = STAGE/'MANUAL_C1'
    assert not (previous/'MANUAL_PUBLICATION_INTENT.json').exists()
    assert not (previous/'OLD_PARENT_EXIT.json').exists()
    assert json.loads(takeover.read_file(previous/'STOPPED_OR_FAILED.json'))['publication_may_be_unknown'] is False
    OUTPUT.mkdir(mode=0o700)
    paths = [ROOT/'gpu/orch_r168_manual_parent_turn.py', ROOT/'gpu/orch_r167_parent_watchdog.py',
        ROOT/'gpu/orch_r167_parent_takeover.py', Path(__file__),
        ROOT/'tests/test_orch_r168_manual_parent_turn.py', ROOT/'tests/test_orch_r167_parent_watchdog.py',
        ROOT/'tests/test_orch_r167_parent_takeover.py']
    pins = {str(path): takeover.sha(path) for path in paths}
    tests = [str(path) for path in paths if path.parent.name == 'tests']
    command = ['uv', 'run', '--with', 'pytest', '--with', 'pytest-subtests', 'python', '-m', 'pytest', '-q', *tests]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    (OUTPUT/'CPU_OUTPUT.txt').write_text(completed.stdout+completed.stderr)
    assert completed.returncode == 0 and all(takeover.sha(path) == expected for path, expected in pins.items())
    write('CPU_GATE.json', dict(status='PASS', execution_kind='CPU_ONLY', command=command,
        pins=pins, output=ref(OUTPUT/'CPU_OUTPUT.txt'), finished_unix=time.time()))
    with (ROOT/'research_loop/COORDINATION.md').open('a') as stream:
        stream.write('\n[Builder] 2026-09-17 '+time.strftime('%H:%M:%S',time.gmtime())+' UTC — '
            'R168 C1 Main-authored manual TRAIN parenting only: 41 focused CPU lifecycle tests PASS; '
            'gate '+str(OUTPUT/'CPU_GATE.json')+' SHA256 '+takeover.sha(OUTPUT/'CPU_GATE.json')+'. '
            'Exact Main text, one publication only after settled/rendered predecessor custody and '
            'pidfd exit/lock. Same parent config/output restart, no native/provider signals; '
            'unknown publication is never retried. Publication is not rendering.\n')
    try:
        manual.execute_once(Operations())
    except BaseException as error:
        write('STOPPED_OR_FAILED.json', dict(error_type=type(error).__name__, error=str(error)[:1000],
            publication_may_be_unknown=(OUTPUT/'MANUAL_PUBLICATION_INTENT.json').exists(),
            retry_forbidden=True, observed_unix=time.time()))
        raise


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('manual_operator_interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    main()
