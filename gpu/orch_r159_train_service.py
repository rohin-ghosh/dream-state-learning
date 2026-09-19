"""Bounded, future-only TRAIN sidecar. Never starts or pauses a learner."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time

from gpu import orch_r158_train_gym as gym
from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
from gpu.orch_r125_stream_journal import StreamJournal, _decode, _digest, require
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


SCHEMA = 'R159_TRAIN_SERVICE_V1'
STATE_SCHEMA = 'R159_TRAIN_SERVICE_EVENT_V1'
GYM_SHA256 = 'dd88f24f5ff12949e94cc8a78c398c699219c9823b93027dd878342a824bbc8b'
CAPS = dict(tasks=24, checks=48, checks_per_task=2, responses_per_task=6)
LIMITS = dict(wall_seconds=21600, polls=21600, record_reads=8192, record_bytes=8*1024**2,
    read_bytes=8*1024**3, output_bytes=256*1024**2, ledger_bytes=64*1024**2,
    helper_seconds=60, helper_output_bytes=128*1024, directory_entries=40000)
SOURCE_FILES = (
    'gpu/__init__.py', 'gpu/orch_r158_train_gym.py', 'gpu/orch_r125_stream_console.py',
    'gpu/orch_r125_stream_journal.py', 'gpu/orch_r127_pilot_console.py',
    'organism_v6/__init__.py', 'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py', 'organism_v6/orch_r125_plain_context.py',
    'organism_v6/reasoning_gym_gym.py', 'organism_v6/gym_backend.py',
    'organism_v6/reasoning_gym_families.json', 'organism_v6/bootstrap_reasoning_gym.txt',
)
ARMS = ('parented_learning', 'parented_frozen', 'unparented_learning')
HELPER_SCRIPT = '''
import hashlib, importlib, json, os, pathlib, resource, sys
options = json.loads(sys.argv[1])
resource.setrlimit(resource.RLIMIT_FSIZE, (options['output_limit'], options['output_limit']))
resource.setrlimit(resource.RLIMIT_CPU, (options['seconds'], options['seconds']))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
root = pathlib.Path(options['source_root'])
origins = {}
for relative, checksum in options['sources'].items():
    path = root / relative
    assert path.resolve() == path and not path.is_symlink(), 'canonical_staged_source'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum, 'staged_source_pin'
    if relative.endswith('.py'):
        module = importlib.import_module(relative[:-3].replace('/', '.').removesuffix('.__init__'))
        assert pathlib.Path(module.__file__).resolve() == path, 'staged_import_origin'
        origins[relative] = str(path)
from gpu import orch_r158_train_gym as gym
action = options['action']
if action == 'preflight':
    bindings = []
    for index in range(3):
        source, entry, binding = gym.dataset(index)
        assert isinstance(entry['question'], str) and entry['question'].strip(), 'actual_task_schema'
        assert callable(source.score_answer), 'actual_verifier_API'
        bindings.append(binding)
    assert bindings[0] == bindings[1] == bindings[2], 'single_package_binding'
    result = dict(schema='R159_STAGED_GYM_PREFLIGHT_V1', binding=bindings[0], origins=origins,
                  task_ids=[gym.task_id(index) for index in range(3)], offered=False, checked=False)
elif action == 'offer':
    result = gym.offer(pathlib.Path(options['root']), options['task_index'])
elif action == 'check':
    result = gym.check(pathlib.Path(options['root']), options['task_index'], options['response_index'])
else:
    raise ValueError('unknown_helper_action')
print(json.dumps(result, sort_keys=True, allow_nan=False))
'''


def canonical(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and '..' not in path.parts
        and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_full_path_required')
    return path


def bounded_bytes(path, limit):
    path = canonical(path)
    with gym.console._directory(path.parent) as directory:
        return StreamJournal._read_bytes(directory, path.name, limit)


def bounded_record(directory, index, limit):
    try:
        record = _decode(StreamJournal._read_bytes(directory, f'{index:020d}.json', limit))
    except FileNotFoundError:
        return None
    require(type(record) is dict and set(record) == {'schema', 'journal_id', 'index', 'kind',
        'previous_sha256', 'document', 'sha256'} and record['schema'] == 'R125_STREAM_JOURNAL_V1'
        and type(record['index']) is int and record['index'] == index
        and type(record['journal_id']) is str and re.fullmatch('[0-9a-f]{32}', record['journal_id'])
        and type(record['previous_sha256']) is str and re.fullmatch('[0-9a-f]{64}', record['previous_sha256'])
        and type(record['kind']) is str and re.fullmatch('[A-Z][A-Z0-9_]{0,63}', record['kind'])
        and type(record['document']) is dict
        and record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'}),
        'bounded_journal_record_integrity')
    return record


def reference(path):
    path = canonical(path)
    return dict(path=str(path), sha256=hashlib.sha256(bounded_bytes(path, LIMITS['record_bytes'])).hexdigest())


def bound(reference_value):
    require(type(reference_value) is dict and set(reference_value) == {'path', 'sha256'}, 'exact_reference')
    raw = bounded_bytes(reference_value['path'], LIMITS['record_bytes'])
    require(hashlib.sha256(raw).hexdigest() == reference_value['sha256'], 'reference_hash_mismatch')
    return _decode(raw)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def source_inventory(source_root):
    return {name: reference(canonical(source_root)/name)['sha256'] for name in SOURCE_FILES}


def validate_config(config, now, *, allow_expired=False):
    require(type(config) is dict and set(config) == {'schema', 'owner_id', 'root', 'plan', 'initialized',
        'lifecycle', 'birth', 'source_root', 'sources', 'service_sha256', 'python', 'dependency_paths',
        'deadline_unix', 'poll_seconds', 'caps', 'limits'}, 'fixed_config_fields')
    require(config['schema'] == SCHEMA and config['caps'] == CAPS, 'fixed_version_and_caps')
    require(type(config['owner_id']) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}', config['owner_id']), 'owner_id')
    require(type(config['limits']) is dict and set(config['limits']) == set(LIMITS)
        and all(type(value) is int and 0 < value <= LIMITS[key] for key, value in config['limits'].items()),
        'bounded_explicit_limits')
    require(finite(config['poll_seconds']) and 0.1 <= config['poll_seconds'] <= 60, 'bounded_poll_cadence')
    require(finite(config['deadline_unix']) and config['deadline_unix'] > 0
        and (allow_expired or now < config['deadline_unix'])
        and config['deadline_unix'] <= now+config['limits']['wall_seconds'],
        'fixed_future_wall')
    root = canonical(config['root'])
    gym.directory(root, 0)
    require(root.is_dir(), 'existing_born_life_only')
    require(reference(Path(__file__).resolve())['sha256'] == config['service_sha256'], 'service_source_pin')
    require(reference(Path(gym.__file__).resolve())['sha256'] == GYM_SHA256, 'exact_frozen_R158_helper')
    source = canonical(config['source_root'])
    require(config['sources'] == source_inventory(source)
        and config['sources']['gpu/orch_r158_train_gym.py'] == GYM_SHA256, 'staged_source_inventory')
    for module in (gym, sys.modules[_read_record.__module__], sys.modules[StreamJournal.__module__],
                   sys.modules[TrainHistory.__module__], sys.modules[event_message.__module__]):
        path = Path(module.__file__).resolve()
        relative = '/'.join(path.parts[-2:])
        require(reference(path)['sha256'] == config['sources'][relative], 'reader_and_staged_semantics_match')
    require(canonical(config['python']).is_file() and type(config['dependency_paths']) is list
        and all(canonical(path).is_dir() for path in config['dependency_paths']), 'explicit_local_interpreter_dependencies')
    plan, initialized, lifecycle, birth = (bound(config[key]) for key in ('plan', 'initialized', 'lifecycle', 'birth'))
    require(plan['schema'] == 'R125_NATIVE_CONTINUITY_V1' and plan['root'] == str(root)
        and plan['matched_arm'] == root.name and plan['source_root'] == str(source)
        and plan.get('authorized_wall_extension') is None and plan.get('preupdate_recovery') is None,
        'actual_fresh_matched_plan')
    cohort = bound(plan['matched_cohort'])
    require(cohort['schema'] == 'R150_MATCHED_CONTINUAL_COHORT_V1' and cohort['fresh_histories'] is True
        and cohort['initial_optimizer_steps'] == 0 and cohort['evaluations_gate_continuation'] is False
        and set(cohort['members']) == set(ARMS) and cohort['members'][root.name]['root'] == str(root)
        and cohort['common']['source_root'] == str(source), 'new_matched_cohort')
    require(finite(plan['hard_end_unix']) and finite(plan['lease_end_unix'])
        and config['deadline_unix'] <= plan['hard_end_unix'] <= plan['lease_end_unix'], 'within_life_and_lease_wall')
    initial = root.parent/'common_initial'
    require(cohort['initial_directory'] == str(initial)
        and config['initialized']['path'] == str(initial/'INITIALIZED.json')
        and config['birth']['path'] == str(root/'INITIAL_STATE_VERIFIED.json')
        and config['lifecycle']['path'] == str(root.parent/'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json'),
        'actual_activation_receipt_paths')
    require(initialized['schema'] == cohort['schema'] and initialized['cohort_sha256'] == plan['matched_cohort']['sha256']
        and initialized['generation_calls'] == 0 and initialized['optimizer_updates'] == 0
        and initialized['checkpoint_commit_sha256'] == reference(initial/'COMMIT.json')['sha256'], 'actual_INITIALIZED')
    capacity_reference = initialized['initialization_validation']
    require(capacity_reference['path'] == str(initial/'capacity_validation/RESULT.json')
        and capacity_reference['status'] == 'PASS' and capacity_reference['schema'] == 'R151_MATCHED_INITIAL_CAPACITY_V1',
        'capacity_PASS_reference')
    capacity = bound({key: capacity_reference[key] for key in ('path', 'sha256')})
    require(capacity['schema'] == capacity_reference['schema'] and capacity['status'] == 'PASS'
        and capacity['state_restored'] is True and capacity['restoration_status'] == 'VERIFIED'
        and capacity['optimizer_updates'] == 0 and capacity['generation_calls'] == 0
        and capacity['stream_data_written'] is False and capacity['synthetic_shape_only'] is True
        and capacity['scientific_evaluation'] is False
        and capacity['plan_sha256'] == initialized['source_plan_sha256'], 'actual_capacity_PASS')
    require(lifecycle['status'] == 'SERVICE_EXIT_VERIFIED' and lifecycle['cgroup_empty_verified'] is True
        and type(lifecycle['service_returncode']) is int and lifecycle['service_returncode'] == 0, 'clean_initializer_exit')
    require(birth['arm'] == root.name and birth['cohort_sha256'] == plan['matched_cohort']['sha256']
        and all(birth[key] == value for key, value in initialized['observed_initial_state'].items()), 'actual_verified_birth')
    with _open_stream_directory(root, 'records') as (directory, unused):
        require(os.stat('00000000000000000000.json', dir_fd=directory).st_size <= config['limits']['record_bytes'],
            'bounded_birth_record')
        first = bounded_record(directory, 0, config['limits']['record_bytes'])
    state = first['document']['state']
    require(first['kind'] == 'COMMITTED' and first['document']['kind'] == 'BIRTH'
        and state['sha256'] == _digest(state['state']) and state['state']['schema'] == 'R150_MATCHED_STREAM_V1'
        and state['state']['rows'] == [] and state['state']['matched']['arm'] == root.name
        and state['state']['matched']['cohort_sha256'] == plan['matched_cohort']['sha256'], 'actual_new_matched_journal_birth')
    manifest = _decode(bounded_bytes(root/'stream/JOURNAL.json', 4096))
    require(manifest == dict(schema='R125_STREAM_JOURNAL_V1', journal_id=first['journal_id']), 'journal_birth_identity')
    return dict(journal_id=first['journal_id'], cohort_sha256=plan['matched_cohort']['sha256'])


class StagedGym:
    def __init__(self, config):
        self.config = config

    def __call__(self, action, task_index=0, response_index=None):
        config = self.config
        remaining = min(config['limits']['helper_seconds'], config['deadline_unix']-time.time())
        require(remaining > 0, 'wall_before_helper')
        options = dict(action=action, task_index=task_index, response_index=response_index,
            root=config['root'], source_root=config['source_root'], sources=config['sources'],
            seconds=max(1, math.ceil(remaining)), output_limit=config['limits']['helper_output_bytes'])
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
            PYTHONPATH=os.pathsep.join([config['source_root'], *config['dependency_paths']]))
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            process = subprocess.Popen([config['python'], '-B', '-P', '-c', HELPER_SCRIPT, json.dumps(options)],
                cwd=config['source_root'], env=environment, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                start_new_session=True)
            try:
                process.wait(timeout=remaining)
            except BaseException:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
            require(process.returncode == 0, 'helper_failure_uncertain_no_retry')
            output.seek(0)
            raw = output.read(config['limits']['helper_output_bytes']+1)
            require(len(raw) <= config['limits']['helper_output_bytes'], 'helper_output_budget')
            return _decode(raw)


class Service:
    def __init__(self, config, *, fresh, api=None, clock=time.time):
        self.config, self.clock = deepcopy(config), clock
        self.api = api if api is not None else StagedGym(config)
        self.directory = canonical(config['root'])/'train_service_r159'
        self.lock = None
        self.state = None
        self.sequence, self.previous, self.ledger_bytes = 0, '0'*64, 0
        identity = validate_config(config, clock(), allow_expired=not fresh)
        self.root_identity = (Path(config['root']).stat().st_dev, Path(config['root']).stat().st_ino)
        self.monotonic_start = time.monotonic()
        try:
            require(type(fresh) is bool, 'explicit_fresh_or_resume')
            if fresh:
                require(not os.path.lexists(Path(config['root'])/'train_environment'), 'fresh_owner_no_prior_offers')
                self.directory.mkdir(mode=0o700)
            canonical(self.directory)
            self.lock = os.open(self.directory/'OWNER.lock', os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
                | (os.O_CREAT | os.O_EXCL if fresh else 0), 0o600)
            require(stat.S_ISREG(os.fstat(self.lock).st_mode), 'regular_owner_lock')
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_identity = (os.fstat(self.lock).st_dev, os.fstat(self.lock).st_ino)
            if fresh:
                head = self.head()
                with _open_stream_directory(config['root'], 'records') as (directory, unused):
                    require(os.stat(f'{head:020d}.json', dir_fd=directory).st_size <= config['limits']['record_bytes'],
                        'bounded_initial_cursor')
                    last = bounded_record(directory, head, config['limits']['record_bytes'])
                require(last['journal_id'] == identity['journal_id'], 'same_life_cursor')
                self.state = dict(config_sha256=_digest(config), identity=identity, started_unix=clock(),
                    cursor=head+1, floor=head+1, previous_record=last['sha256'], task_index=0, offers=0, check_calls=0,
                    task_checks=0, checked=0, exposures=0, accepted=False, phase='OFFER', task=None, feedback=None,
                    pending_action=None, last_commit=head, outcomes=[], polls=0, read_bytes=0, record_reads=0,
                    output_reserved=0, terminal=None, starts=1)
                self.append('OWNER_CREATED', dict(config=deepcopy(config)))
            else:
                self.restore()
                require(self.state['config_sha256'] == _digest(config) and self.state['identity'] == identity,
                    'resume_exact_config_sources_life')
                require(self.state['starts'] < 8, 'bounded_restarts')
                self.state['starts'] += 1
                self.append('OWNER_RESUMED')
            if self.state['terminal'] is None and (self.state['pending_action'] is not None
                    or (not fresh and 'generator_binding' not in self.state)):
                self.finish('UNCERTAIN_NO_RETRY')
            if self.state['terminal'] is None and fresh:
                self.invoke('preflight')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None

    def head(self):
        maximum, entries = -1, 0
        with _open_stream_directory(self.config['root'], 'records') as (directory, unused):
            with os.scandir(directory) as listing:
                for entry in listing:
                    entries += 1
                    require(entries <= self.config['limits']['directory_entries'], 'bounded_record_directory')
                    if re.fullmatch('[0-9]{20}\\.json', entry.name):
                        require(entry.is_file(follow_symlinks=False), 'regular_record_entry')
                        maximum = max(maximum, int(entry.name[:20]))
        require(maximum >= 0, 'born_journal_required')
        return maximum

    def append(self, kind, details=None):
        document = dict(schema=STATE_SCHEMA, index=self.sequence, previous_sha256=self.previous,
            kind=kind, observed_unix=self.clock(), state=deepcopy(self.state), details=details or {})
        document['sha256'] = _digest(document)
        raw = gym.encoded(document)+b'\n'
        reserve = 0 if kind == 'TERMINAL' else 65536
        require(self.ledger_bytes+len(raw)+reserve <= self.config['limits']['ledger_bytes'], 'ledger_output_budget')
        with gym.console._directory(self.directory) as directory:
            StreamJournal._publish(directory, f'{self.sequence:08d}.json', document)
        self.ledger_bytes += len(raw)
        self.previous, self.sequence = document['sha256'], self.sequence+1

    def restore(self):
        entries = []
        for path in self.directory.iterdir():
            require(len(entries) < self.config['limits']['directory_entries'], 'bounded_owner_ledger')
            entries.append(path)
        require(not any(path.name.endswith('.partial') for path in entries), 'incomplete_ledger_no_automatic_recovery')
        events = sorted(path for path in entries if re.fullmatch('[0-9]{8}\\.json', path.name))
        require(events, 'existing_owner_state_required')
        for path in events:
            raw = bounded_bytes(path, min(128*1024, self.config['limits']['ledger_bytes']-self.ledger_bytes))
            event = _decode(raw)
            require(path.name == f'{self.sequence:08d}.json' and event['schema'] == STATE_SCHEMA
                and event['index'] == self.sequence and event['previous_sha256'] == self.previous
                and event['sha256'] == _digest({key: value for key, value in event.items() if key != 'sha256'}),
                'append_only_ledger_chain')
            self.ledger_bytes += len(raw)
            self.previous, self.sequence, self.state = event['sha256'], self.sequence+1, event['state']

    def reserve(self, read_bytes=0, records=0, output_bytes=0):
        for field, addition, bound_name in (('read_bytes', read_bytes, 'read_bytes'),
                ('record_reads', records, 'record_reads'), ('output_reserved', output_bytes, 'output_bytes')):
            require(self.state[field]+addition <= self.config['limits'][bound_name], bound_name+'_budget')
            self.state[field] += addition
        self.append('BUDGET_RESERVED')

    def read(self, path, limit=None):
        path = canonical(path)
        size = path.stat().st_size
        limit = self.config['limits']['record_bytes'] if limit is None else limit
        require(size <= limit, 'bounded_evidence_file')
        self.reserve(read_bytes=size+1)
        return _decode(bounded_bytes(path, size))

    def record(self, index):
        with _open_stream_directory(self.config['root'], 'records') as (directory, unused):
            try:
                size = os.stat(f'{index:020d}.json', dir_fd=directory, follow_symlinks=False).st_size
            except FileNotFoundError:
                return None
            require(size <= self.config['limits']['record_bytes'], 'bounded_record_bytes')
            self.reserve(read_bytes=size+1, records=1)
            return bounded_record(directory, index, size)

    def publication(self, source_path, expected_text=None):
        source = self.read(source_path)
        publication = self.read(source_path.parent/'PUBLICATION.json', 16384)
        message_path = canonical(publication['path'])
        require(message_path == Path(self.config['root'])/'stream/inbox'/(publication['id']+'.json'), 'full_inbox_path')
        message = self.read(message_path, 32768)
        require(set(message) == {'schema', 'id', 'text', 'split', 'actor', 'speaker', 'source_receipt'}
            and message['schema'] == 'R127_ATTRIBUTED_INBOX_V1' and message['id'] == publication['id']
            and message['actor'] == 'environment' and message['speaker'] == 'Tool' and message['split'] == 'TRAIN'
            and reference(message_path)['sha256'] == publication['sha256']
            and message['source_receipt'] == reference(source_path)
            and message['text'] == (source['text'] if expected_text is None else expected_text), 'actual_published_source_join')
        return source, dict(publication=publication, source=reference(source_path), text=message['text'])

    def exposed(self, record, evidence):
        if record['kind'] != 'REQUEST' or record['document'].get('split') != 'TRAIN':
            return False
        request = record['document']
        resume = request['resume_state']
        require(resume['sha256'] == _digest(resume['state'])
            and request['history_sha256'] == _digest(resume['state']['history']), 'request_history_hash')
        publication = evidence['publication']
        event = dict(event_id='environment:inbox:'+publication['id'], actor='environment', split='TRAIN',
            text='Tool: '+evidence['text'], phase='feedback', episode_id='continual_stream',
            source_id=publication['path'], source_sha256=publication['sha256'], origin='TRAIN_COLLECTION')
        if event not in resume['state']['history']['events']:
            return False
        history = TrainHistory.restore(resume['state']['history'])
        rendered = history.render(lambda messages: 0, 0, presentation=resume['state'].get('presentation'))
        require(rendered.messages == request['messages'], 'actual_original_rendering')
        restored = TrainEvent.restore(event)
        message = event_message(restored) if resume['state'].get('presentation') else TrainHistory._message(restored)
        return message in request['messages']

    def invoke(self, action, response_index=None, triple=None):
        state = self.state
        require(self.clock() < self.config['deadline_unix'], 'wall_before_external_action')
        require(self.config['sources'] == source_inventory(self.config['source_root']), 'source_changed_no_action')
        self.reserve(read_bytes=3*self.config['limits']['record_bytes']+16*1024**2, output_bytes=2*1024**2)
        if action == 'offer':
            require(state['offers'] < CAPS['tasks'] and state['task_index'] == state['offers'], 'sequential_offer_cap')
            require(not os.path.lexists(gym.directory(Path(self.config['root']), state['task_index'])), 'no_existing_task_retry')
            if state['offers'] == 0:
                require(not os.path.lexists(Path(self.config['root'])/'train_environment'), 'no_manual_task_zero_adoption')
            state['offers'] += 1
        elif action == 'check':
            require(state['check_calls'] < CAPS['checks'] and state['task_checks'] < CAPS['checks_per_task'], 'checker_attempt_cap')
            require(reference(state['task']['source']['path']) == state['task']['source']
                and reference(state['task']['publication']['path'])['sha256'] == state['task']['publication']['sha256'],
                'original_task_and_publication_still_bound')
            state['check_calls'] += 1
            state['task_checks'] += 1
        state['pending_action'] = dict(action=action, task_index=state['task_index'], response_index=response_index)
        self.append('INTENT')
        try:
            result = self.api(action, state['task_index'], response_index)
            require(self.clock() < self.config['deadline_unix'], 'wall_after_helper_no_retry')
            if action == 'preflight':
                require(result['schema'] == 'R159_STAGED_GYM_PREFLIGHT_V1' and result['offered'] is False
                    and result['checked'] is False and result['binding']['package_version'] == gym.PACKAGE_VERSION
                    and result['task_ids'] == [gym.task_id(index) for index in range(3)]
                    and result['origins'] == {name: str(Path(self.config['source_root'])/name)
                        for name in SOURCE_FILES if name.endswith('.py')}, 'actual_staged_helper_preflight')
                state['generator_binding'] = result['binding']
            elif action == 'offer':
                path = gym.directory(Path(self.config['root']), state['task_index'])/'TASK.json'
                task, evidence = self.publication(path)
                require(task['schema'] == 'R158_TRAIN_GYM_TASK_V1' and task['task_id'] == gym.task_id(state['task_index'])
                    and task['task_index'] == state['task_index'] and task['split'] == 'TRAIN'
                    and task['binding'] == state['generator_binding'] and task['answer_key_published'] is False
                    and finite(task['created_unix']) and task['created_unix'] <= self.clock()
                    and result == dict(task_id=task['task_id'], publication=evidence['publication'], rendered=False),
                    'actual_offer_schema')
                state['task'], state['task_created'], state['phase'] = evidence, task['created_unix'], 'ACTIVE'
            elif result == dict(status='NO_COMPLETE_ANSWER', checked=False, response_index=response_index):
                self.append('NO_COMPLETE_ANSWER_WAIT_FUTURE')
            else:
                path = gym.directory(Path(self.config['root']), state['task_index'])/f'answer_{response_index:020d}'/'RESULT.json'
                receipt = self.read(path)
                require(set(receipt) == {'schema', 'task_id', 'split', 'answer', 'origin', 'generation_boundary',
                    'binding', 'score', 'accepted', 'finished_unix', 'answer_key_published'}, 'actual_result_fields')
                generation = triple[1]['document']['response']
                answer = gym.parse_answer(generation['raw'], terminal=generation['terminal'], truncated=generation['truncated'])
                require(receipt['schema'] == 'R158_TRAIN_GYM_RESULT_V1' and receipt['task_id'] == gym.task_id(state['task_index'])
                    and receipt['split'] == 'TRAIN' and receipt['binding'] == state['generator_binding']
                    and receipt['answer'] == answer and receipt['answer_key_published'] is False
                    and receipt['origin'] == dict(response_index=response_index, response_sha256=triple[1]['sha256'],
                        commit_sha256=triple[2]['sha256'])
                    and receipt['generation_boundary'] == dict(terminal=True, truncated=False)
                    and finite(receipt['score']) and 0 <= receipt['score'] <= 1
                    and type(receipt['accepted']) is bool and receipt['accepted'] is (receipt['score'] == 1)
                    and finite(receipt['finished_unix']) and triple[1]['document']['finished_unix'] <= receipt['finished_unix'] <= self.clock(),
                    'actual_matching_result')
                intent = self.read(path.parent/'INTENT.json')
                require(intent == dict(response_index=response_index, response_sha256=triple[1]['sha256'],
                    generated_sha256=hashlib.sha256(generation['raw'].encode()).hexdigest(), answer=answer,
                    task_sha256=state['task']['source']['sha256'], replay_allowed=False), 'actual_check_intent')
                text = ('Training puzzle check: '+('accepted' if receipt['accepted'] else 'not accepted')
                    +f"; verifier score {receipt['score']:.3f}. This is a real check of your submitted answer."
                    +' The reference answer is not shown.')
                unused, evidence = self.publication(path, text)
                require(result == dict(status='CHECKED', accepted=receipt['accepted'], result_path=str(path),
                    publication=evidence['publication']), 'actual_check_return')
                state['checked'] += 1
                state['accepted'], state['feedback'] = receipt['accepted'], evidence
                state['feedback_after'], state['feedback_time'] = triple[2]['index'], receipt['finished_unix']
            state['pending_action'] = None
            self.append('ACTION_COMPLETE', dict(action=action))
        except Exception as error:
            self.finish('UNCERTAIN_NO_RETRY', type(error).__name__+':'+str(error)[:256])

    def advance(self):
        state = self.state
        if state['accepted']:
            observation = 'ACCEPTED'
        elif state['checked'] >= 2:
            observation = 'TWO_CHECKED'
        elif state['checked'] == 0:
            observation = 'NO_SUBMISSION/ABANDONED'
        else:
            observation = 'ABANDONED_AFTER_CHECK'
        state['outcomes'].append(dict(task_index=state['task_index'], observation=observation,
            checked=state['checked'], checker_attempts=state['task_checks'], exposed_responses=state['exposures']))
        self.append('TASK_TERMINAL_OBSERVATION')
        state['task_index'] += 1
        if state['task_index'] == CAPS['tasks']:
            self.finish('COMPLETE')
            return
        state.update(task_checks=0, checked=0, exposures=0, accepted=False, task=None, feedback=None, phase='OFFER')
        self.append('NEXT_TASK_FUTURE_BOUNDARY')

    def finish(self, status, reason=None):
        if self.state['terminal'] is None:
            self.state['terminal'] = dict(status=status, reason=reason, no_retry=True, finished_unix=self.clock())
            self.append('TERMINAL')

    def tick(self):
        require(self.lock is not None, 'owner_lock_required')
        state = self.state
        if state['terminal'] is not None:
            return deepcopy(state['terminal'])
        try:
            require(self.clock() < self.config['deadline_unix']
                and time.monotonic()-self.monotonic_start < self.config['limits']['wall_seconds'], 'fixed_wall_expired')
            require(state['polls'] < self.config['limits']['polls'], 'poll_budget')
            root = canonical(self.config['root'])
            require((root.stat().st_dev, root.stat().st_ino) == self.root_identity, 'life_root_replaced')
            lock_stat = canonical(self.directory/'OWNER.lock').stat()
            require((lock_stat.st_dev, lock_stat.st_ino) == self.lock_identity, 'owner_lock_replaced')
            state['polls'] += 1
            self.append('POLL')
            if state['phase'] == 'OFFER':
                self.invoke('offer')
                return dict(status='OFFERED' if state['terminal'] is None else state['terminal']['status'])
            record = self.record(state['cursor'])
            if record is None:
                return dict(status='WAIT_FUTURE')
            require(record['journal_id'] == state['identity']['journal_id']
                and record['previous_sha256'] == state['previous_record'], 'future_journal_chain')
            state['cursor'] += 1
            state['previous_record'] = record['sha256']
            self.append('CURSOR_CONSUMED')
            if record['kind'] == 'REQUEST':
                feedback = state['feedback']
                if (feedback is not None and record['index'] > state['feedback_after']
                    and record['document'].get('started_unix', -1) >= state['feedback_time']):
                    if self.exposed(record, feedback):
                        state['feedback'] = None
                        self.append('FEEDBACK_ACTUALLY_RENDERED')
                if state['feedback'] is None and record['index'] > state['last_commit'] and (
                        state['accepted'] or state['task_checks'] >= CAPS['checks_per_task']
                        or state['exposures'] >= CAPS['responses_per_task']):
                    self.advance()
                return dict(status='REQUEST_OBSERVED')
            if record['kind'] != 'COMMITTED' or record['index']-2 < state['floor']:
                return dict(status='BACKGROUND_NOT_COUNTED')
            triple = [self.record(record['index']-2), self.record(record['index']-1), record]
            if any(item is None for item in triple) or [item['kind'] for item in triple] != ['REQUEST', 'RESPONSE', 'COMMITTED']:
                return dict(status='BACKGROUND_NOT_COUNTED')
            if not self.exposed(triple[0], state['task']):
                return dict(status='TASK_NOT_RENDERED')
            require(triple[0]['document']['started_unix'] >= state['task_created'], 'post_publication_request')
            generation = gym.verify_triple(triple, state['task']['text'])
            if state['exposures'] >= CAPS['responses_per_task']:
                return dict(status='WAIT_FEEDBACK_OR_BOUNDARY')
            state['exposures'] += 1
            state['last_commit'] = record['index']
            self.append('OWN_RESPONSE_EXPOSED', dict(response_index=triple[1]['index']))
            if state['feedback'] is not None or state['accepted'] or state['task_checks'] >= CAPS['checks_per_task']:
                return dict(status='WAIT_FEEDBACK_OR_BOUNDARY')
            if generation['terminal'] is not True or generation['truncated'] is not False:
                self.append('PARTIAL_NOT_CHECKED')
                return dict(status='PARTIAL_NOT_CHECKED')
            if gym.parse_answer(generation['raw'], terminal=True, truncated=False) is None:
                self.append('NO_COMPLETE_ANSWER_WAIT_FUTURE')
                return dict(status='NO_COMPLETE_ANSWER')
            self.invoke('check', triple[1]['index'], triple)
            return dict(status='CHECK_ATTEMPTED')
        except Exception as error:
            self.finish('STOPPED_NO_RETRY', type(error).__name__+':'+str(error)[:256])
            return deepcopy(state['terminal'])


def prepare(plan_reference, owner_id, deadline_unix, *, python=sys.executable, dependency_paths=()):
    plan = bound(plan_reference)
    root = canonical(plan['root'])
    config = dict(schema=SCHEMA, owner_id=owner_id, root=str(root), plan=plan_reference,
        initialized=reference(root.parent/'common_initial/INITIALIZED.json'),
        lifecycle=reference(root.parent/'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json'),
        birth=reference(root/'INITIAL_STATE_VERIFIED.json'), source_root=plan['source_root'],
        sources=source_inventory(plan['source_root']), service_sha256=reference(Path(__file__).resolve())['sha256'],
        python=str(Path(python).resolve()), dependency_paths=[str(canonical(path)) for path in dependency_paths],
        deadline_unix=deadline_unix, poll_seconds=1, caps=deepcopy(CAPS), limits=deepcopy(LIMITS))
    validate_config(config, time.time())
    return config


def run_service(config, *, fresh):
    def expired(unused_signal, unused_frame):
        raise TimeoutError('service_fixed_wall_expired')

    previous_handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, config['deadline_unix']-time.time()))
    watcher = None
    try:
        watcher = Service(config, fresh=fresh)
        while watcher.state['terminal'] is None:
            watcher.tick()
            if watcher.state['terminal'] is None:
                time.sleep(min(config['poll_seconds'], max(0, config['deadline_unix']-time.time())))
        return watcher.state['terminal']
    except (KeyboardInterrupt, TimeoutError) as error:
        if watcher is None:
            raise
        watcher.finish('OPERATOR_OR_WALL_STOP_NO_RETRY', type(error).__name__)
        return watcher.state['terminal']
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if watcher is not None:
            watcher.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'preflight', 'run'))
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--owner-id')
    parser.add_argument('--deadline-unix', type=float)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--dependency-path', action='append', default=[])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--fresh-owner', action='store_true')
    mode.add_argument('--resume-owner', action='store_true')
    options = parser.parse_args()
    if options.action == 'prepare':
        require(options.plan is not None and options.plan_sha256 and options.owner_id and options.deadline_unix,
            'explicit_prepare_arguments')
        config = prepare(dict(path=str(options.plan), sha256=options.plan_sha256), options.owner_id,
            options.deadline_unix, python=options.python, dependency_paths=options.dependency_path)
        gym.write(options.config, config)
        result = dict(status='PREPARED_NOT_ACTIVATED', config=reference(options.config))
    else:
        config = _decode(bounded_bytes(options.config, 65536))
        if options.action == 'preflight':
            validate_config(config, time.time())
            result = StagedGym(config)('preflight')
        else:
            require(options.fresh_owner or options.resume_owner, 'explicit_owner_mode')
            result = run_service(config, fresh=options.fresh_owner)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get('status') in ('COMPLETE', 'PREPARED_NOT_ACTIVATED') or options.action == 'preflight' else 1


if __name__ == '__main__':
    raise SystemExit(main())
