"""Exact COMMUNITY parent environment refresh using existing custody primitives."""

from collections import Counter
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import tomllib

from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as custody
from gpu import orch_r167_parent_watchdog as watchdog
from gpu import orch_r168_parent_rollout as transaction


STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
BRANCHES = ('C1', 'C2', 'C3', 'C4', 'C5')
MODEL = 'openai/openai/gpt-6-astra'


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=custody.sha(path))


def write(path, value):
    community.write(path, value)


def discover():
    found = {}
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            observed = custody.identity(int(process.name))
            argv = observed['argv']
            if '-m' not in argv or argv[argv.index('-m') + 1] != 'gpu.orch_r153_community_parents':
                continue
            config_path = Path(argv[argv.index('--config') + 1])
            config = json.loads(custody.read_file(config_path))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        branch = config['branch']
        assert branch in BRANCHES and branch not in found, 'duplicate_or_unscoped_parent'
        assert config['node'] == 'ovx3'
        found[branch] = dict(identity=observed, config=reference(config_path),
            repository=argv[argv.index('--repository') + 1], output=argv[argv.index('--output') + 1],
            gate=reference(argv[argv.index('--gate') + 1]), root=config['root'],
            cwd=str((process / 'cwd').resolve()))
    return found


def summary(output):
    counts = Counter()
    delivered = 0
    entries = []
    for attempt in sorted(Path(output).glob('parent_*')):
        result_path = attempt / 'RESULT.json'
        result = json.loads(custody.read_file(result_path)) if result_path.exists() else dict(status='UNFINISHED')
        counts[result['status']] += 1
        delivery = attempt / 'DELIVERED.json'
        entry = dict(attempt=attempt.name, status=result['status'], rendered=False)
        if result_path.exists():
            entry['result'] = reference(result_path)
        if delivery.exists():
            value = json.loads(custody.read_file(delivery))
            assert value['status'] == 'RENDERED' and value['result_sha256'] == custody.sha(result_path)
            assert value['publication'] == result['publication']
            assert value['rendered']['inbox_sha256'] == result['publication']['sha256']
            assert value['rendered']['text_sha256'] == hashlib.sha256(result['message'].encode()).hexdigest()
            delivered += 1
            entry.update(rendered=True, delivery=reference(delivery), rendered_metadata=value['rendered'])
        envelope_path = attempt / 'stdout.json'
        if envelope_path.exists():
            envelope = json.loads(custody.read_file(envelope_path))
            entry.update(provider_status=envelope.get('status'), model=envelope.get('model'),
                provider_complete=envelope.get('status') == 'completed' and not envelope.get('error'),
                provider_receipt=reference(envelope_path))
        entries.append(entry)
    return dict(attempt_count=len(entries), status_counts=dict(counts), rendered_count=delivered,
        pending_publications=counts['PUBLISHED'] - delivered, entries=entries)


class Refresh:
    def __init__(self, branch, original, epoch):
        self.branch, self.original, self.epoch = branch, original, epoch
        self.directory = STAGE / epoch / branch
        self.directory.mkdir(parents=True, mode=0o700)
        self.new_output = self.directory / 'parent'

    def no_competitor(self, expected):
        current = discover().get(self.branch)
        assert (current['identity']['pid'] if current else None) == expected, 'competing_parent'

    def preflight(self):
        original = self.original
        observed = original['identity']
        self.config_path = Path(original['config']['path'])
        config = json.loads(custody.read_file(self.config_path))
        self.repository = Path(original['repository'])
        self.old_output = Path(original['output'])
        self.binding = dict(branch=self.branch, **observed, config=original['config'],
            source=reference(self.repository / 'gpu/orch_r153_community_parents.py'),
            output=str(self.old_output), root=config['root'])
        custody.verify_identity(self.binding, custody.identity(observed['pid']))
        custody.verify_files(self.binding)
        self.no_competitor(observed['pid'])
        gate = json.loads(custody.read_file(original['gate']['path']))
        assert custody.sha(original['gate']['path']) == original['gate']['sha256']
        self.source_pins = gate['source_pins']
        assert all(custody.sha(self.repository / name) == digest for name, digest in self.source_pins.items())
        gate = copy.deepcopy(gate)
        gate['parents'][self.branch]['output'] = str(self.new_output)
        self.gate_path = self.directory / 'PARENT_GATE.json'
        write(self.gate_path, gate)
        self.command = list(observed['argv'])
        for flag, value in (('--output', str(self.new_output)), ('--gate', str(self.gate_path)),
                ('--gate-sha256', custody.sha(self.gate_path))):
            self.command[self.command.index(flag) + 1] = value
        environment = dict(entry.split('=', 1) for entry in
            (Path('/proc') / str(observed['pid']) / 'environ').read_bytes().decode().split('\0') if entry)
        assert os.environ.get('NVIDIA_API_KEY'), 'sourced_credential_missing'
        self.credential_changed = environment.get('NVIDIA_API_KEY') != os.environ['NVIDIA_API_KEY']
        self.environment = dict(environment, NVIDIA_API_KEY=os.environ['NVIDIA_API_KEY'],
            PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(self.repository))
        script = ('import json;from pathlib import Path;from gpu import orch_r153_community_parents as c;'
            'from gpu import orch_r133_programme_parent as p;'
            f'config,gate=c.verify_gate(Path({str(self.config_path)!r}),Path({str(self.repository)!r}),'
            f'Path({str(self.new_output)!r}),Path({str(self.gate_path)!r}),{custody.sha(self.gate_path)!r});'
            f'assert p.STRONG=={MODEL!r};'
            f'print(json.dumps(p.transport_preflight(Path({str(self.repository)!r}),config)))')
        result = subprocess.run([self.command[0], '-B', '-c', script], cwd=self.repository,
            env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=55)
        assert result.returncode == 0, 'exact_source_transport_preflight_failed'
        write(self.directory / 'PREFLIGHT.json', dict(observed_unix=time.time(), original=original,
            config=reference(self.config_path), gate=reference(self.gate_path), source_pins=self.source_pins,
            provider_model=MODEL, credential_changed=self.credential_changed, credential_values_recorded=False,
            transport=json.loads(result.stdout), command=self.command, scope='COMMUNITY_PARENT_ENVIRONMENT_ONLY',
            authority='Rohin user directive September17 urgent rotated-key COMMUNITY C1-C5 refresh',
            preserve_cadence_policy_and_all_attempts=True, no_child_signals=True))

    def quiesce(self):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            custody.verify_identity(self.binding, custody.identity(self.binding['pid']))
            tasks = list((Path('/proc') / str(self.binding['pid']) / 'task').iterdir())
            assert 0 < len(tasks) <= 128
            if all(not (task / 'children').read_text().strip() for task in tasks):
                break
            time.sleep(0.1)
        else:
            raise ValueError('no_childless_gap_defer')
        self.no_competitor(self.binding['pid'])
        return watchdog.quiesce(self.binding, scope_verifier=custody.verify_identity, seconds=30)

    def settled(self):
        return custody.settled_attempts(self.old_output)

    def preserve(self, manifest):
        self.manifest = manifest
        self.new_output.mkdir(mode=0o700)
        custody.copy_attempts(self.old_output, self.new_output, manifest)
        write(self.directory / 'LEDGER_TRANSFER.json', manifest)
        write(self.directory / 'QUIESCED.json', dict(observed_unix=time.time(), binding=self.binding,
            attempts=len(manifest['attempts']), bytes=manifest['bytes'],
            reservation=manifest['reserved_response_count'], preserve_pending_and_refused=True))

    @contextmanager
    def old_lock(self):
        with community.parent_lock(self.old_output):
            yield

    def confirm_exit(self, manifest):
        self.no_competitor(None)
        assert custody.settled_attempts(self.old_output) == custody.settled_attempts(self.new_output) == manifest
        write(self.directory / 'OLD_PARENT_EXIT.json', dict(pid=self.binding['pid'],
            start_ticks=self.binding['start_ticks'], pidfd_exit_verified=True,
            old_lock_exclusively_acquired=True, observed_unix=time.time()))

    def start_successor(self):
        assert all(custody.sha(self.repository / name) == digest for name, digest in self.source_pins.items())
        with (self.directory / 'PARENT.log').open('xb') as log:
            return subprocess.Popen(self.command, cwd=self.original['cwd'], env=self.environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)

    def verify_successor(self, process):
        time.sleep(1)
        assert process.poll() is None, 'successor_exited_no_retry'
        self.successor = custody.identity(process.pid)
        assert self.successor['argv'] == self.command and self.successor['state'] not in ('T', 't', 'Z', 'X')
        self.no_competitor(process.pid)
        environment = dict(entry.split('=', 1) for entry in
            (Path('/proc') / str(process.pid) / 'environ').read_bytes().decode().split('\0') if entry)
        assert environment.get('NVIDIA_API_KEY') == os.environ['NVIDIA_API_KEY'], 'fresh_credential_not_inherited'

    def record_started(self, process):
        write(self.directory / 'STARTED.json', dict(observed_unix=time.time(), successor=self.successor,
            old_parent=self.original['identity'], config=reference(self.config_path), source_pins=self.source_pins,
            output=str(self.new_output), gate=reference(self.gate_path), command=self.command,
            credential_changed=self.credential_changed, fresh_credential_inherited=True,
            model=MODEL, reserved_response_count=self.manifest['reserved_response_count'],
            inherited_attempts=len(self.manifest['attempts']), no_replay=True, delivery_claimed=False))

    def reconcile_failed_handoff(self, successor):
        write(self.directory / 'RECONCILIATION_REQUIRED.json', dict(observed_unix=time.time(),
            old_parent=self.original['identity'], successor_pid=successor.pid if successor else None,
            no_blind_retry=True, no_child_signals=True))


def main():
    action = sys.argv[1]
    if action == 'inspect':
        current = discover()
        receipt = dict(observed_unix=time.time(), parents=current,
            ledgers={branch: summary(value['output']) for branch, value in current.items()})
        path = STAGE / ('INSPECT_' + str(time.time_ns()) + '.json')
        write(path, receipt)
        print(json.dumps(dict(receipt=reference(path), counts={branch: {
            key: value for key, value in ledger.items() if key != 'entries'}
            for branch, ledger in receipt['ledgers'].items()})), flush=True)
        return
    assert action == 'execute'
    config_path = Path.home() / '.codex/nvidia-astra.config.toml'
    provider_config = tomllib.loads(config_path.read_text())
    assert provider_config['model'] == MODEL
    assert os.environ.get('NVIDIA_API_KEY')
    current = discover()
    assert set(current) == set(BRANCHES)
    epoch = 'attempt_' + time.strftime('%H%M%S', time.gmtime())
    write(STAGE / 'AUTHORITY.json', dict(observed_unix=time.time(), directive_scope='C1-C5 parent refresh only',
        model=MODEL, provider_config=reference(config_path), credential_source='~/.codex/nvidia.env',
        credential_mtime_unix=(Path.home() / '.codex/nvidia.env').stat().st_mtime,
        no_credential_changes=True, no_child_restart=True, no_legacy_or_evaluation=True,
        no_COORDINATION_changes=True, epoch=epoch, originals=current, operator=reference(__file__)))
    for branch in BRANCHES:
        operation = Refresh(branch, current[branch], epoch)
        try:
            successor = transaction.handoff(operation)
            print(json.dumps(dict(branch=branch, status='REFRESHED_NOT_YET_DELIVERED', pid=successor.pid,
                receipt=reference(operation.directory / 'STARTED.json'))), flush=True)
        except Exception as error:
            write(operation.directory / 'DEFERRED.json', dict(observed_unix=time.time(),
                error_type=type(error).__name__, reason=str(error)[:200], no_blind_retry=True))
            print(json.dumps(dict(branch=branch, status='DEFERRED', error_type=type(error).__name__,
                reason=str(error)[:200])), flush=True)


if __name__ == '__main__':
    main()
