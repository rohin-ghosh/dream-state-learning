"""CPU-only, explicit-GO continuation of an immutable R159 TRAIN owner."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

SCHEMA = 'R162_TRAIN_CONTINUATION_V1'
OWNER_SCHEMA = 'R162_PREDECESSOR_IDENTITY_V1'
EVENT_SCHEMA = 'R162_TRAIN_EPOCH_EVENT_V1'
R159_SHA256 = 'dd8ed5a733b5631347605b2b4415cf5eb3531c8ebe93860e5522314afd4a8b1b'


def load_predecessor():
    configured = os.environ.get('R162_R159_SCRIPT')
    if configured is None:
        from gpu import orch_r159_train_service
        return orch_r159_train_service
    path = Path(configured)
    if not path.is_absolute() or path.resolve() != path or any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('canonical_original_R159_script_required')
    with path.open('rb') as stream:
        raw = stream.read(1024*1024+1)
    if len(raw) > 1024*1024 or hashlib.sha256(raw).hexdigest() != R159_SHA256:
        raise ValueError('original_R159_script_hash')
    spec = importlib.util.spec_from_file_location('_r162_pinned_predecessor', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


old = load_predecessor()
require = old.require
COUNTERS = dict(offers='tasks', check_calls='checks', polls='polls', read_bytes='read_bytes',
    record_reads='record_reads', output_reserved='output_bytes')


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def process_identity(pid):
    require(type(pid) is int and pid > 1, 'explicit_predecessor_pid')
    directory = Path('/proc')/str(pid)
    first = (directory/'stat').read_text()
    ticks = int(first[first.rindex(')')+2:].split()[19])
    argv = (directory/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    executable = old.reference((directory/'exe').resolve())
    last = (directory/'stat').read_text()
    require(int(last[last.rindex(')')+2:].split()[19]) == ticks, 'process_identity_changed')
    return dict(pid=pid, start_ticks=ticks, boot_id=boot_id(), argv=argv, executable=executable)


def validate_owner(owner, config_ref, config):
    require(set(owner) == {'schema', 'process', 'script', 'config', 'captured_unix'}
        and owner['schema'] == OWNER_SCHEMA and owner['config'] == config_ref, 'exact_owner_identity')
    process = owner['process']
    require(set(process) == {'pid', 'start_ticks', 'boot_id', 'argv', 'executable'}
        and type(process['pid']) is int and process['pid'] > 1
        and type(process['start_ticks']) is int and process['start_ticks'] > 0
        and process['boot_id'] == boot_id(), 'pid_ticks_boot_identity')
    argv = process['argv']
    require(type(argv) is list and all(type(item) is str for item in argv)
        and argv.count(owner['script']['path']) == 1 and argv.count('--config') == 1,
        'exact_owner_command')
    script_index = argv.index(owner['script']['path'])
    require(script_index >= 1 and all(flag in ('-B', '-u', '-P') for flag in argv[1:script_index])
        and len(argv[script_index+1:]) == 4 and argv[script_index+1:script_index+2] == ['run']
        and argv[argv.index('--config')+1:argv.index('--config')+2] == [config_ref['path']]
        and ('--fresh-owner' in argv) != ('--resume-owner' in argv), 'original_run_config_command')
    require(old.reference(owner['script']['path']) == owner['script']
        and owner['script']['sha256'] == config['service_sha256'] == R159_SHA256,
        'original_script_pin')
    require(process['executable'] == old.reference(config['python']), 'original_runtime_pin')
    require(old.finite(owner['captured_unix']) and owner['captured_unix'] <= time.time(), 'identity_capture_time')


def identify(config_ref, script, pid, start_ticks):
    config = old.bound(config_ref)
    owner = dict(schema=OWNER_SCHEMA, process=process_identity(pid), script=old.reference(script),
        config=config_ref, captured_unix=time.time())
    require(owner['process']['start_ticks'] == start_ticks, 'expected_start_ticks')
    validate_owner(owner, config_ref, config)
    return owner


def require_dead(owner):
    require(owner['process']['boot_id'] == boot_id()
        and not os.path.lexists(f"/proc/{owner['process']['pid']}"), 'old_pid_still_present_no_handoff')


def acquire(path, *, create=False):
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    descriptor = os.open(path, flags | (os.O_CREAT | os.O_EXCL if create else 0), 0o600)
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'regular_owner_lock')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def inode(path):
    status = old.canonical(path).stat()
    return [status.st_dev, status.st_ino]


def limits(state, config, now):
    require(state['terminal'] is None and state['pending_action'] is None, 'settled_nonterminal_predecessor')
    require(old.finite(state['started_unix']) and state['started_unix'] <= now
        < min(config['deadline_unix'], state['started_unix']+config['limits']['wall_seconds']),
        'original_cumulative_wall')
    for field, name in COUNTERS.items():
        maximum = config['caps'][name] if name in config['caps'] else config['limits'][name]
        require(type(state[field]) is int and 0 <= state[field] <= maximum, 'cumulative_'+field)
    require(state['polls'] < config['limits']['polls'], 'poll_budget_exhausted')
    require(type(state['task_index']) is int and 0 <= state['task_index'] < 24
        and state['offers'] == state['task_index']+1 and state['phase'] == 'ACTIVE'
        and state['task'] is not None and 'generator_binding' in state, 'existing_active_task_only')
    require(type(state['task_checks']) is int and 0 <= state['task_checks'] <= 2
        and type(state['checked']) is int and 0 <= state['checked'] <= state['task_checks']
        and type(state['exposures']) is int and 0 <= state['exposures'] <= 6
        and type(state['accepted']) is bool and type(state['starts']) is int and 1 <= state['starts'] < 8,
        'original_task_counters')
    require(all(type(state[field]) is int for field in ('floor', 'cursor', 'last_commit'))
        and 0 <= state['floor'] <= state['cursor'] and 0 <= state['last_commit'] < state['cursor'],
        'original_consumed_frontiers')


def audit(config):
    directory = old.canonical(config['root'])/'train_service_r159'
    entries = []
    for entry in directory.iterdir():
        require(len(entries) < config['limits']['directory_entries'], 'bounded_predecessor_directory')
        require(entry.name == 'OWNER.lock' or re.fullmatch('[0-9]{8}\\.json', entry.name),
            'unknown_or_partial_predecessor_file')
        entries.append(entry)
    paths = sorted(path for path in entries if path.name != 'OWNER.lock')
    require(paths, 'predecessor_ledger_required')
    previous, total, pending, state = '0'*64, 0, None, None
    counts = dict(preflight=0, offer=0, check=0)
    inventory = []
    for ordinal, path in enumerate(paths):
        raw = old.bounded_bytes(path, min(128*1024, config['limits']['ledger_bytes']-total))
        event = old._decode(raw)
        require(path.name == f'{ordinal:08d}.json' and event['schema'] == old.STATE_SCHEMA
            and event['index'] == ordinal and event['previous_sha256'] == previous
            and event['sha256'] == old._digest({key: value for key, value in event.items() if key != 'sha256'}),
            'predecessor_chain_integrity')
        current = event['state']
        require(current['config_sha256'] == old._digest(config) and current['terminal'] is None,
            'predecessor_exact_config_no_terminal')
        if state is not None:
            require(all(type(current[field]) is int and current[field] >= state[field]
                for field in (*COUNTERS, 'cursor', 'last_commit', 'starts')),
                'predecessor_counter_regression')
        if event['kind'] == 'INTENT':
            require(pending is None and current['pending_action'] is not None, 'nonoverlapping_intents')
            pending = current['pending_action']
            require(set(pending) == {'action', 'task_index', 'response_index'}
                and pending['action'] in counts, 'known_predecessor_intent')
            counts[pending['action']] += 1
        elif event['kind'] == 'ACTION_COMPLETE':
            require(pending is not None and event['details']['action'] == pending['action']
                and current['pending_action'] is None, 'paired_action_complete')
            pending = None
        require(current['pending_action'] == pending, 'pending_intent_cannot_disappear')
        total += len(raw)
        inventory.append(dict(name=path.name, sha256=hashlib.sha256(raw).hexdigest()))
        previous, state = event['sha256'], current
    require(pending is None and counts == dict(preflight=1, offer=state['offers'], check=state['check_calls']),
        'all_predecessor_intents_paired')
    return dict(tip=previous, entries=len(paths), ledger_bytes=total,
        inventory_sha256=old._digest(inventory), state_sha256=old._digest(state)), deepcopy(state)


def runtime():
    require(old.reference(Path(old.__file__).resolve())['sha256'] == R159_SHA256, 'imported_R159_pin')
    return dict(continuation=old.reference(Path(__file__).resolve()),
        predecessor=old.reference(Path(old.__file__).resolve()),
        interpreter=old.reference(Path(sys.executable).resolve()))


def prepare(config_ref, identity_ref):
    config, owner = old.bound(config_ref), old.bound(identity_ref)
    validate_owner(owner, config_ref, config)
    require_dead(owner)
    identity = old.validate_config(config, time.time())
    root = old.canonical(config['root'])
    require(not os.path.lexists(root/'train_service_r162'), 'epoch_already_exists_no_retry')
    descriptor = acquire(root/'train_service_r159/OWNER.lock')
    try:
        predecessor, state = audit(config)
        require(state['identity'] == identity, 'predecessor_life_identity')
        limits(state, config, time.time())
        require(state['read_bytes']+2*predecessor['ledger_bytes'] <= config['limits']['read_bytes'],
            'predecessor_audit_read_budget')
        require_dead(owner)
        return dict(schema=SCHEMA, config=config_ref, owner_identity=identity_ref, predecessor=predecessor,
            runtime=runtime(), root_identity=inode(root), old_lock_identity=inode(root/'train_service_r159/OWNER.lock'),
            prepared_unix=time.time(), preparation_read_bytes=predecessor['ledger_bytes'])
    finally:
        os.close(descriptor)


def context_loss(record, evidence):
    if record['kind'] != 'REQUEST' or record['document'].get('split') != 'TRAIN':
        return None
    require(record['sha256'] == old._digest({key: value for key, value in record.items() if key != 'sha256'}),
        'loss_request_record_hash')
    request = record['document']
    resume = request['resume_state']
    require(resume['sha256'] == old._digest(resume['state'])
        and request['history_sha256'] == old._digest(resume['state']['history']), 'loss_request_history_hash')
    history = old.TrainHistory.restore(resume['state']['history'])
    require(history.render(lambda messages: 0, 0, presentation=resume['state'].get('presentation')).messages
        == request['messages'], 'loss_exact_original_rendering')
    publication = evidence['publication']
    event = dict(event_id='environment:inbox:'+publication['id'], actor='environment', split='TRAIN',
        text='Tool: '+evidence['text'], phase='feedback', episode_id='continual_stream',
        source_id=publication['path'], source_sha256=publication['sha256'], origin='TRAIN_COLLECTION')
    events = resume['state']['history']['events']
    if event not in events:
        return None
    position = events.index(event)
    if position >= history.visible_frontier.event_count or old.Service.exposed(None, record, evidence):
        return None
    crossing = next((operation for operation in history.operations if operation['kind'] == 'compaction'
        and operation['before']['event_count'] <= position < operation['through']['event_count']), None)
    if crossing is None:
        return None
    return dict(request_index=record['index'], request_sha256=record['sha256'],
        history_sha256=request['history_sha256'], rendered_messages_sha256=old._digest(request['messages']),
        event_position=position, event_sha256=old._digest(event), compaction=crossing,
        visible_frontier=history.visible_frontier.event_count, original_evidence=deepcopy(evidence))


class Continuation(old.Service):
    def __init__(self, authority_ref, *, main_go, api=None, clock=time.time):
        require(main_go is True, 'explicit_Main_GO_required')
        self.lock, self.old_lock = None, None
        self.boundary = None
        self.clock = clock
        authority = old.bound(authority_ref)
        require(set(authority) == {'schema', 'config', 'owner_identity', 'predecessor', 'runtime',
            'root_identity', 'old_lock_identity', 'prepared_unix', 'preparation_read_bytes'}
            and authority['schema'] == SCHEMA and authority['runtime'] == runtime(), 'exact_epoch_authority_runtime')
        self.authority = authority
        self.config = old.bound(authority['config'])
        self.owner = old.bound(authority['owner_identity'])
        validate_owner(self.owner, authority['config'], self.config)
        require_dead(self.owner)
        identity = old.validate_config(self.config, clock())
        root = old.canonical(self.config['root'])
        self.directory = root/'train_service_r162'
        self.root_identity = tuple(inode(root))
        require(list(self.root_identity) == authority['root_identity'], 'original_root_inode')
        try:
            self.old_lock = acquire(root/'train_service_r159/OWNER.lock')
            require(inode(root/'train_service_r159/OWNER.lock') == authority['old_lock_identity'], 'original_lock_inode')
            predecessor, self.state = audit(self.config)
            require(predecessor == authority['predecessor'] and self.state['identity'] == identity,
                'exact_predecessor_final_state_prefix')
            limits(self.state, self.config, clock())
            require(authority['preparation_read_bytes'] == predecessor['ledger_bytes'], 'preparation_budget_binding')
            charge = authority['preparation_read_bytes']+predecessor['ledger_bytes']
            require(self.state['read_bytes']+charge <= self.config['limits']['read_bytes'], 'cumulative_audit_read_budget')
            require(predecessor['ledger_bytes']+262144 <= self.config['limits']['ledger_bytes'], 'epoch_ledger_reserve')
            require_dead(self.owner)
            self.activation_floor = self.head()+1
            self.epoch_started = clock()
            self.monotonic_start = time.monotonic()-(self.epoch_started-self.state['started_unix'])
            self.api = api if api is not None else old.StagedGym(self.config)
            self.directory.mkdir(mode=0o700)
            self.lock = acquire(self.directory/'OWNER.lock', create=True)
            self.lock_identity = tuple(inode(self.directory/'OWNER.lock'))
            self.sequence, self.previous, self.ledger_bytes = 0, predecessor['tip'], predecessor['ledger_bytes']
            self.append('EPOCH_AUTHORITY', dict(authority=authority_ref, runtime=authority['runtime'],
                predecessor=predecessor, activation_floor=self.activation_floor, epoch_started=self.epoch_started))
            self.state['starts'] += 1
            self.reserve(read_bytes=charge)
        except BaseException:
            self.close()
            raise

    def close(self):
        super().close()
        if self.old_lock is not None:
            os.close(self.old_lock)
            self.old_lock = None

    def append(self, kind, details=None):
        event = dict(schema=EVENT_SCHEMA, index=self.sequence, previous_sha256=self.previous,
            kind=kind, observed_unix=self.clock(), state=deepcopy(self.state), details=details or {})
        event['sha256'] = old._digest(event)
        raw = old.gym.encoded(event)+b'\n'
        require(self.ledger_bytes+len(raw)+(0 if kind == 'TERMINAL' else 65536)
            <= self.config['limits']['ledger_bytes'], 'cumulative_ledger_budget')
        with old.gym.console._directory(self.directory) as directory:
            old.StreamJournal._publish(directory, f'{self.sequence:08d}.json', event)
        self.ledger_bytes += len(raw)
        self.sequence, self.previous = self.sequence+1, event['sha256']

    def record(self, index):
        record = super().record(index)
        if index == self.state['cursor'] and record is not None and record['kind'] == 'REQUEST':
            self.boundary = record
        return record

    def future(self, record):
        return (record is not None and record['kind'] == 'REQUEST' and record['document'].get('split') == 'TRAIN'
            and record['index'] >= self.activation_floor
            and old.finite(record['document'].get('started_unix'))
            and record['document']['started_unix'] >= self.epoch_started)

    def exposed(self, record, evidence):
        return self.future(record) and super().exposed(record, evidence)

    def advance(self):
        if self.future(self.boundary):
            super().advance()

    def invoke(self, action, response_index=None, triple=None):
        require(self.authority['runtime'] == runtime()
            and old.reference(self.authority['config']['path']) == self.authority['config'],
            'epoch_runtime_config_changed_no_action')
        require(self.clock() < self.state['started_unix']+self.config['limits']['wall_seconds'],
            'original_wall_before_action')
        super().invoke(action, response_index, triple)

    def retire(self, losses):
        state = self.state
        state['outcomes'].append(dict(task_index=state['task_index'], observation='CONTEXT_LOST_NOT_COMPLETED',
            checked=state['checked'], checker_attempts=state['task_checks'], exposed_responses=state['exposures'],
            actual_checker_accepted=state['accepted'], feedback_unrendered=state['feedback'] is not None,
            reasons=sorted(losses)))
        self.append('CONTEXT_LOSS_RETIREMENT', dict(losses=losses, task=state['task'], pending_feedback=state['feedback']))
        state['task_index'] += 1
        if state['task_index'] == old.CAPS['tasks']:
            self.finish('COMPLETE')
            return
        state.update(task_checks=0, checked=0, exposures=0, accepted=False, task=None, feedback=None, phase='OFFER')
        self.append('NEXT_TASK_FUTURE_BOUNDARY')

    def tick(self):
        self.boundary = None
        require(self.old_lock is not None, 'both_owner_locks_required')
        require(inode(Path(self.config['root'])/'train_service_r159/OWNER.lock')
            == self.authority['old_lock_identity'], 'predecessor_lock_replaced')
        result = super().tick()
        if self.state['terminal'] is not None or self.state['phase'] != 'ACTIVE' or not self.future(self.boundary):
            return result
        try:
            losses = {}
            for label in ('task', 'feedback'):
                evidence = self.state[label]
                if evidence is None:
                    continue
                after = self.state['task_created'] if label == 'task' else self.state['feedback_time']
                if self.boundary['document']['started_unix'] < after:
                    continue
                loss = context_loss(self.boundary, evidence)
                if loss is not None:
                    unused, published = self.publication(Path(evidence['source']['path']), evidence['text'])
                    require(published == evidence, 'loss_original_publication_still_bound')
                    losses[label.upper()+'_CONTEXT_LOST'] = loss
            if losses and (self.state['feedback'] is None or 'FEEDBACK_CONTEXT_LOST' in losses):
                self.retire(losses)
                return dict(status='CONTEXT_LOSS_RETIRED')
            return result
        except Exception as error:
            self.finish('STOPPED_NO_RETRY', type(error).__name__+':'+str(error)[:256])
            return deepcopy(self.state['terminal'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('identify', 'prepare', 'run'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--config-sha256')
    parser.add_argument('--script', type=Path)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--start-ticks', type=int)
    parser.add_argument('--owner-identity', type=Path)
    parser.add_argument('--owner-identity-sha256')
    parser.add_argument('--authority', type=Path)
    parser.add_argument('--authority-sha256')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--main-go', action='store_true')
    options = parser.parse_args()
    if options.action == 'run':
        require(options.authority is not None and options.authority_sha256, 'exact_authority_required')
        watcher = Continuation(dict(path=str(options.authority), sha256=options.authority_sha256),
            main_go=options.main_go)
        try:
            while watcher.state['terminal'] is None:
                watcher.tick()
                if watcher.state['terminal'] is None:
                    time.sleep(min(watcher.config['poll_seconds'], max(0, watcher.config['deadline_unix']-time.time())))
            print(json.dumps(watcher.state['terminal'], sort_keys=True))
        finally:
            watcher.close()
        return 0 if watcher.state['terminal']['status'] == 'COMPLETE' else 1
    require(options.config is not None and options.config_sha256 and options.output is not None,
        'explicit_config_and_new_output')
    config_ref = dict(path=str(options.config), sha256=options.config_sha256)
    if options.action == 'identify':
        require(options.script is not None and options.pid and options.start_ticks, 'explicit_owner_identity_arguments')
        document = identify(config_ref, options.script, options.pid, options.start_ticks)
    else:
        require(options.owner_identity is not None and options.owner_identity_sha256, 'bound_identity_required')
        document = prepare(config_ref, dict(path=str(options.owner_identity), sha256=options.owner_identity_sha256))
    old.gym.write(options.output, document)
    print(json.dumps(dict(status='RECORDED_NOT_ACTIVATED', output=old.reference(options.output)), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
