"""Local, source-bound community exchange; no execution, transport, or model calls."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
import uuid

from gpu import orch_r127_pilot_console as console
from gpu.orch_r125_stream_journal import _digest, require


SCHEMA = 'R153_COMMUNITY_EXCHANGE_V1'
ACTORS = ('C1', 'C2', 'C3', 'C4', 'C5')
ARTIFACT_LIMIT = 16 * 1024
TEXT_LIMIT = 4096
RECORD_LIMIT = 32 * 1024 * 1024
PAGE_SIZE = 20
DATABASE_MAX_PAGES = 131072
WORKSPACE_ENTRIES = 256
EFFECTS_PER_ACTOR = 512
ARTIFACTS_PER_ACTOR = 64
ARTIFACT_BYTES_PER_ACTOR = 1024 * 1024
SNAPSHOT_BYTES_PER_ACTOR = 512 * 1024 * 1024
ACTION_FIELDS = {
    'list_workspace': {'cursor'}, 'read_workspace': {'name'},
    'write_workspace': {'name', 'text'},
    'publish_artifact': {'name'}, 'list_artifacts': {'cursor'},
    'open_artifact': {'artifact_id'}, 'send_message': {'recipient', 'text'},
    'list_messages': {'cursor'}, 'read_message': {'message_id'},
}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def unique(pairs):
        document = {}
        for key, value in pairs:
            require(key not in document, 'duplicate_key')
            document[key] = value
        return document

    document = json.loads(raw, object_pairs_hook=unique)
    require(type(document) is dict, 'object_required')
    encoded(document)
    return document


def safe_name(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', name)
            and '..' not in name, 'safe_flat_workspace_name_required')
    require(not re.search(r'sealed|readout|credential|secret|token|password|private|final|benchmark|'
                          r'(^|[_.-])(env|key|keys|ssh|gate)([_.-]|$)', name, re.I),
            'reserved_workspace_name')
    return name


def identifier(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'invalid_identifier')
    return value


def verify_snapshot(actor, journal_id, origin, snapshot, action, action_parser=decode):
    """Verify integrity, not transport authentication; only trusted wrappers submit snapshots."""
    require(actor in ACTORS and type(snapshot) is dict and set(snapshot) == {'manifest', 'records'},
            'exact_trusted_snapshot_fields')
    require(snapshot['manifest'] == dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id),
            'pinned_snapshot_journal')
    require(type(origin) is dict and set(origin) == {'kind', 'record_index', 'record_sha256'}
            and origin['kind'] == 'TRAIN_CHILD_RESPONSE', 'exact_TRAIN_origin')
    index = origin['record_index']
    require(type(index) is int and 1 <= index < 10**18, 'response_record_index')
    identifier(origin['record_sha256'])
    records = snapshot['records']
    require(type(records) is list and len(records) == 3, 'one_committed_triple_required')
    for number, record in zip((index - 1, index, index + 1), records):
        require(type(record) is dict and len(encoded(record)) <= RECORD_LIMIT
                and record.get('schema') == 'R125_STREAM_JOURNAL_V1'
                and record.get('journal_id') == journal_id
                and type(record.get('index')) is int and record['index'] == number
                and record.get('sha256') == _digest({key: value for key, value in record.items()
                                                    if key != 'sha256'}), 'journal_record_hash')
    previous, response, committed = records
    require([record['kind'] for record in records] == ['REQUEST', 'RESPONSE', 'COMMITTED'],
            'committed_response_required')
    require(response['sha256'] == origin['record_sha256']
            and response['previous_sha256'] == previous['sha256']
            and committed['previous_sha256'] == response['sha256'], 'origin_chain_mismatch')
    source_request = {key: value for key, value in previous['document'].items() if key != 'resume_state'}
    require(source_request.get('split') == 'TRAIN'
            and response['document']['request_sha256'] == _digest(source_request)
            and committed['document']['source_sha256'] == _digest(response['document']),
            'TRAIN_request_response_commit_join')
    generation = response['document']['response']
    require(generation.get('terminal') is True and generation.get('truncated') is False
            and type(generation.get('raw')) is str, 'complete_generated_response_required')
    parsed = action_parser(generation['raw'])
    require(type(parsed) is dict and encoded(parsed) == encoded(action), 'generated_action_mismatch')
    return dict(origin, actor=actor, journal_id=journal_id,
                request_sha256=previous['sha256'], committed_sha256=committed['sha256'],
                generated_sha256=sha(generation['raw'].encode('utf-8')))


def read_regular(directory, name, limit):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                         dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'single_link_regular_file_required')
        require(before.st_size <= limit, 'file_size_limit')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
    signatures = {(entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns,
                   entry.st_ctime_ns, entry.st_nlink) for entry in (before, after, current)}
    require(len(signatures) == 1 and len(raw) == before.st_size, 'file_changed_during_read')
    return raw


def immutable_file(directory, name, raw, *, replace_hashes=()):
    try:
        existing = read_regular(directory, name, ARTIFACT_LIMIT if replace_hashes else len(raw))
    except FileNotFoundError:
        existing = None
    if existing is not None:
        if existing == raw:
            os.fsync(directory)
            return
        require(sha(existing) in replace_hashes, 'immutable_file_conflict')
    temporary = '.' + uuid.uuid4().hex + '.partial'
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=directory)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fchmod(stream.fileno(), 0o400)
        os.fsync(stream.fileno())
    os.rename(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
    os.fsync(directory)


def validate_packet(packet):
    require(type(packet) is dict and set(packet) == {'schema', 'handle', 'recipient', 'journal_id',
            'source', 'source_sha256', 'text', 'packet_sha256'}, 'exact_delivery_packet')
    require(packet['schema'] == 'R153_DELIVERY_PACKET_V1'
            and packet['recipient'] in ACTORS and type(packet['journal_id']) is str
            and re.fullmatch('[0-9a-f]{32}', packet['journal_id']), 'delivery_identity')
    identifier(packet['handle'])
    require(type(packet['source']) is dict and packet['source'].get('schema') == SCHEMA
            and packet['source_sha256'] == sha(encoded(packet['source']))
            and packet['packet_sha256'] == sha(encoded({key: value for key, value in packet.items()
                                                       if key != 'packet_sha256'})), 'delivery_packet_hash')
    require(type(packet['text']) is str and len(packet['text'].encode('utf-8')) <= 128 * 1024,
            'bounded_delivery_text')
    source = packet['source']
    if source.get('status') == 'AVAILABLE':
        require(source.get('recipient') == packet['recipient'], 'notice_recipient_mismatch')
        effect_id = identifier(source.get('message_id'))
    else:
        require(source.get('status') == 'RECORDED' and source.get('actor') == packet['recipient']
                and type(source.get('origin')) is dict
                and source['origin'].get('actor') == packet['recipient'], 'feedback_actor_mismatch')
        effect_id = identifier(source.get('effect_id'))
    require(packet['handle'] == sha(encoded([effect_id, packet['recipient']])), 'delivery_handle_binding')


def install_delivery(root, packet):
    """Trusted receiver helper; transport authentication is required before calling."""
    validate_packet(packet)
    root = Path(root).absolute()
    require(root.resolve() == root and '..' not in root.parts, 'canonical_receiver_root')
    with console._directory(root / 'stream') as directory:
        manifest = decode(read_regular(directory, 'JOURNAL.json', 4096))
    require(manifest == dict(schema='R125_STREAM_JOURNAL_V1', journal_id=packet['journal_id']),
            'receiver_journal_mismatch')
    with console._directory(root) as directory:
        try:
            os.mkdir('community_receipts', mode=0o700, dir_fd=directory)
        except FileExistsError:
            pass
        os.fsync(directory)
    source_path = root / 'community_receipts' / (packet['handle'] + '.json')
    with console._directory(source_path.parent) as directory:
        current = os.fstat(directory)
        require(current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0,
                'private_receiver_receipts')
        lock = os.open('LOCK', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
        try:
            current = os.fstat(lock)
            require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1, 'regular_receiver_lock')
            fcntl.flock(lock, fcntl.LOCK_EX)
            immutable_file(directory, source_path.name, encoded(packet['source']))
            document = dict(schema=console.SCHEMA, id=packet['handle'], text=packet['text'], split='TRAIN',
                            actor='environment', speaker='Tool',
                            source_receipt=dict(path=str(source_path), sha256=packet['source_sha256']))
            with console._open_stream_directory(root, 'inbox') as (inbox_directory, inbox_path):
                immutable_file(inbox_directory, packet['handle'] + '.json', encoded(document))
        finally:
            os.close(lock)
    return dict(schema='R153_DELIVERY_INSTALL_V1', handle=packet['handle'], actor=packet['recipient'],
                journal_id=packet['journal_id'], packet_sha256=packet['packet_sha256'],
                source_path=str(source_path), source_sha256=packet['source_sha256'],
                path=str(inbox_path / (packet['handle'] + '.json')), sha256=sha(encoded(document)),
                status='INBOX_PUBLISHED', rendered=False, executed=False)


class CommunityExchange:
    def __init__(self, root, bindings, *, action_parser=None):
        self.root = Path(root).absolute()
        require(self.root.resolve() == self.root and '..' not in self.root.parts, 'canonical_broker_root')
        self.root.mkdir(mode=0o700, exist_ok=True)
        with console._directory(self.root.parent) as directory:
            os.fsync(directory)
        require(type(bindings) is dict and set(bindings) == set(ACTORS), 'exact_five_actor_bindings')
        self.bindings = {}
        self.action_parser = decode if action_parser is None else action_parser
        require(callable(self.action_parser), 'trusted_action_parser_required')
        for actor, binding in bindings.items():
            require(type(binding) is dict and set(binding) == {'root', 'workspace', 'journal_id'},
                    'exact_binding_fields')
            life = Path(binding['root']).absolute()
            workspace = Path(binding['workspace']).absolute()
            require(life.resolve() == life and workspace.resolve() == workspace
                    and '..' not in life.parts and '..' not in workspace.parts, 'canonical_life_paths')
            require(life in workspace.parents and workspace != life / 'stream'
                    and life / 'stream' not in workspace.parents, 'private_workspace_outside_stream')
            require(self.root != life and self.root not in life.parents and life not in self.root.parents,
                    'broker_and_life_disjoint')
            require(type(binding['journal_id']) is str
                    and re.fullmatch('[0-9a-f]{32}', binding['journal_id']), 'journal_id_required')
            paths = {}
            for path in (life, workspace, life / 'stream', life / 'stream' / 'records', life / 'stream' / 'inbox'):
                with console._directory(path) as directory:
                    current = os.fstat(directory)
                    paths[str(path)] = [current.st_dev, current.st_ino]
            with console._directory(life / 'stream') as directory:
                manifest = read_regular(directory, 'JOURNAL.json', 4096)
            require(decode(manifest) == {'schema': 'R125_STREAM_JOURNAL_V1',
                                        'journal_id': binding['journal_id']}, 'pinned_journal_manifest')
            self.bindings[actor] = dict(root=str(life), workspace=str(workspace),
                journal_id=binding['journal_id'], manifest_sha256=sha(manifest), paths=paths)
        for position, actor in enumerate(ACTORS):
            life = Path(self.bindings[actor]['root'])
            for other in ACTORS[position + 1:]:
                peer = Path(self.bindings[other]['root'])
                require(life != peer and life not in peer.parents and peer not in life.parents,
                        'independent_life_roots')
                require(self.bindings[actor]['journal_id'] != self.bindings[other]['journal_id'],
                        'independent_journal_ids')
        with console._directory(self.root) as directory:
            current = os.fstat(directory)
            require(current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0,
                    'owner_private_broker_required')
            self.root_identity = (current.st_dev, current.st_ino)
            for name in ('objects', 'receipts'):
                try:
                    os.mkdir(name, mode=0o700, dir_fd=directory)
                except FileExistsError:
                    pass
            for name in ('LOCK', 'state.sqlite3'):
                descriptor = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                                     0o600, dir_fd=directory)
                os.close(descriptor)
            os.fsync(directory)
        with self._locked() as database:
            for statement in (
                'CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value BLOB NOT NULL)',
                'CREATE TABLE IF NOT EXISTS effects (id TEXT PRIMARY KEY, actor TEXT NOT NULL, '
                'fingerprint TEXT NOT NULL, receipt BLOB NOT NULL)',
                'CREATE TABLE IF NOT EXISTS artifacts (seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, '
                'actor TEXT NOT NULL, name TEXT NOT NULL, version INTEGER NOT NULL, sha256 TEXT NOT NULL, '
                'data BLOB NOT NULL, UNIQUE(actor, name, version))',
                'CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, actor TEXT NOT NULL, '
                'recipient TEXT NOT NULL, sequence INTEGER NOT NULL, text TEXT NOT NULL, '
                'open_requested INTEGER NOT NULL DEFAULT 0, UNIQUE(recipient, sequence))',
                'CREATE TABLE IF NOT EXISTS deliveries (handle TEXT PRIMARY KEY, actor TEXT NOT NULL, '
                'source BLOB NOT NULL, text TEXT NOT NULL, delivered INTEGER NOT NULL DEFAULT 0, installation BLOB)',
                'CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, actor TEXT NOT NULL, name TEXT NOT NULL, '
                'version INTEGER NOT NULL, sha256 TEXT NOT NULL, data BLOB NOT NULL, UNIQUE(actor, name, version))',
            ):
                database.execute(statement)
            configuration = encoded(dict(schema=SCHEMA, bindings=self.bindings))
            prior = database.execute("SELECT value FROM metadata WHERE key='configuration'").fetchone()
            require(prior is None or prior[0] == configuration, 'broker_bindings_changed')
            database.execute("INSERT OR IGNORE INTO metadata VALUES ('configuration', ?)", (configuration,))

    @contextmanager
    def _locked(self):
        with console._directory(self.root) as directory:
            current = os.fstat(directory)
            require((current.st_dev, current.st_ino) == self.root_identity
                    and current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0,
                    'broker_root_changed')
            lock = os.open('LOCK', os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
            try:
                current = os.fstat(lock)
                require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1, 'private_regular_lock')
                fcntl.flock(lock, fcntl.LOCK_EX)
                for name in ('state.sqlite3', 'state.sqlite3-journal'):
                    try:
                        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
                    except FileNotFoundError:
                        continue
                    require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1
                            and current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0,
                            'private_regular_database')
                database = sqlite3.connect(str(self.root / 'state.sqlite3'), isolation_level=None)
                database.row_factory = sqlite3.Row
                try:
                    database.execute('PRAGMA synchronous=FULL')
                    database.execute(f'PRAGMA max_page_count={DATABASE_MAX_PAGES}')
                    database.execute('BEGIN IMMEDIATE')
                    yield database
                    if database.in_transaction:
                        database.commit()
                except BaseException:
                    if database.in_transaction:
                        database.rollback()
                    raise
                finally:
                    database.close()
            finally:
                os.close(lock)

    def _binding(self, actor):
        require(type(actor) is str and actor in self.bindings, 'authenticated_actor_required')
        binding = self.bindings[actor]
        for path, identity in binding['paths'].items():
            with console._directory(path) as directory:
                current = os.fstat(directory)
                require([current.st_dev, current.st_ino] == identity, 'life_directory_replaced')
        with console._directory(Path(binding['root']) / 'stream') as directory:
            require(sha(read_regular(directory, 'JOURNAL.json', 4096)) == binding['manifest_sha256'],
                    'journal_manifest_changed')
        return binding

    def _origin(self, actor, origin, action):
        binding = self._binding(actor)
        require(type(origin) is dict and set(origin) == {'kind', 'record_index', 'record_sha256'}
                and origin['kind'] == 'TRAIN_CHILD_RESPONSE', 'exact_TRAIN_origin')
        index = origin['record_index']
        require(type(index) is int and 1 <= index < 10**18, 'response_record_index')
        identifier(origin['record_sha256'])
        snapshots = {}
        with console._open_stream_directory(binding['root'], 'records') as (directory, unused_path):
            records = []
            for number in (index - 1, index, index + 1):
                name = f'{number:020d}.json'
                raw = read_regular(directory, name, RECORD_LIMIT)
                snapshots[name] = raw
                record = decode(raw)
                records.append(record)
            snapshot = dict(manifest=dict(schema='R125_STREAM_JOURNAL_V1', journal_id=binding['journal_id']), records=records)
            proof = verify_snapshot(actor, binding['journal_id'], origin, snapshot, action, self.action_parser)
            for name, raw in snapshots.items():
                require(read_regular(directory, name, RECORD_LIMIT) == raw, 'origin_changed_during_validation')
        return proof

    def apply_snapshot(self, actor, snapshot, action):
        """Authenticated host adapter: validate a remote triple, retain it locally, then apply."""
        self._action(actor, action)
        binding = self._binding(actor)
        require(type(snapshot) is dict and type(snapshot.get('records')) is list
                and len(snapshot['records']) == 3, 'one_committed_triple_required')
        response = snapshot['records'][1]
        origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=response['index'], record_sha256=response['sha256'])
        verify_snapshot(actor, binding['journal_id'], origin, snapshot, action, self.action_parser)
        with self._locked():
            with console._open_stream_directory(binding['root'], 'records') as (directory, unused_path):
                inventory = {}
                with os.scandir(directory) as entries:
                    for position, entry in enumerate(entries):
                        require(position < EFFECTS_PER_ACTOR * 3, 'snapshot_record_quota')
                        current = entry.stat(follow_symlinks=False)
                        require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1,
                                'regular_snapshot_inventory')
                        inventory[entry.name] = current.st_size
                added = {f'{record["index"]:020d}.json': len(encoded(record)) for record in snapshot['records']
                         if f'{record["index"]:020d}.json' not in inventory}
                require(len(inventory) + len(added) <= EFFECTS_PER_ACTOR * 3
                        and sum(inventory.values()) + sum(added.values()) <= SNAPSHOT_BYTES_PER_ACTOR,
                        'snapshot_storage_quota')
                for record in snapshot['records']:
                    immutable_file(directory, f'{record["index"]:020d}.json', encoded(record))
        return self.apply(actor, origin, action)

    def _action(self, actor, action):
        require(type(action) is dict and type(action.get('op')) is str
                and action['op'] in ACTION_FIELDS, 'bounded_operation_required')
        require(set(action) == ACTION_FIELDS[action['op']] | {'op'}, 'exact_action_fields_no_actor_or_paths')
        if 'name' in action:
            safe_name(action['name'])
        if 'cursor' in action:
            require(type(action['cursor']) is int and 0 <= action['cursor'] <= 100000, 'bounded_cursor')
        for field in ('artifact_id', 'message_id'):
            if field in action:
                identifier(action[field])
        if action['op'] == 'send_message':
            require(type(action['recipient']) is str and action['recipient'] in ACTORS
                    and action['recipient'] != actor, 'one_named_peer_required')
        if 'text' in action:
            limit = ARTIFACT_LIMIT if action['op'] == 'write_workspace' else TEXT_LIMIT
            require(type(action['text']) is str and 0 < len(action['text'].encode('utf-8')) <= limit
                    and '\0' not in action['text'], 'bounded_text')

    def _workspace(self, actor, name, database):
        binding = self._binding(actor)
        self._workspace_current(database, actor, name)
        with console._directory(binding['workspace']) as directory:
            raw = read_regular(directory, safe_name(name), ARTIFACT_LIMIT)
        text = raw.decode('utf-8')
        require('\0' not in text, 'text_artifact_required')
        return raw, text

    def _enqueue(self, database, effect_id, actor, source, text):
        handle = sha(encoded([effect_id, actor]))
        require(len(text.encode('utf-8')) <= 128 * 1024, 'bounded_feedback')
        database.execute('INSERT INTO deliveries(handle, actor, source, text) VALUES (?, ?, ?, ?)',
                         (handle, actor, encoded(source), text))
        return handle

    def apply(self, actor, origin, action):
        self._action(actor, action)
        with self._locked() as database:
            proof = self._origin(actor, origin, action)
            effect_id = sha(encoded([SCHEMA, actor, proof['journal_id'], origin['record_index'],
                                    origin['record_sha256']]))
            fingerprint = sha(encoded(dict(proof=proof, action=action)))
            existing = database.execute('SELECT fingerprint, receipt FROM effects WHERE id=?', (effect_id,)).fetchone()
            if existing is not None:
                require(existing['fingerprint'] == fingerprint, 'committed_record_already_used')
                receipt = decode(existing['receipt'])
            else:
                count = database.execute('SELECT count(*) FROM effects WHERE actor=?', (actor,)).fetchone()[0]
                require(count < EFFECTS_PER_ACTOR, 'actor_effect_quota')
                result, text = self._operate(database, actor, effect_id, action)
                receipt = dict(schema=SCHEMA, effect_id=effect_id, actor=actor, operation=action['op'],
                               origin=proof, status='RECORDED', executed=False, training_target=False,
                               created_unix=time.time(), result=result)
                handles = [self._enqueue(database, effect_id, actor, receipt, text)]
                if action['op'] == 'send_message':
                    notice = dict(schema=SCHEMA, status='AVAILABLE', executed=False,
                                  message_id=effect_id, recipient=action['recipient'])
                    handles.append(self._enqueue(database, effect_id, action['recipient'], notice,
                        f'Peer inbox availability: {effect_id}. Use read_message to inspect explicitly.'))
                receipt['delivery_handles'] = handles
                database.execute('INSERT INTO effects VALUES (?, ?, ?, ?)',
                                 (effect_id, actor, fingerprint, encoded(receipt)))
            database.commit()
            if action['op'] in ('publish_artifact', 'open_artifact'):
                self._artifact_file(database, receipt['result']['artifact_id'])
            if action['op'] == 'write_workspace':
                self._workspace_current(database, actor, action['name'])
            return receipt

    def _operate(self, database, actor, effect_id, action):
        operation = action['op']
        if operation == 'list_workspace':
            for row in database.execute('SELECT DISTINCT name FROM notes WHERE actor=?', (actor,)).fetchall():
                self._workspace_current(database, actor, row['name'])
            with console._directory(self._binding(actor)['workspace']) as directory:
                names = []
                with os.scandir(directory) as entries:
                    for position, entry in enumerate(entries):
                        require(position < WORKSPACE_ENTRIES, 'workspace_entry_quota')
                        try:
                            safe_name(entry.name)
                        except ValueError:
                            continue
                        current = entry.stat(follow_symlinks=False)
                        if stat.S_ISREG(current.st_mode) and current.st_nlink == 1:
                            names.append(entry.name)
                names.sort()
                cursor = action['cursor']
                result = dict(names=names[cursor:cursor + PAGE_SIZE],
                              next_cursor=cursor + PAGE_SIZE if cursor + PAGE_SIZE < len(names) else None)
        elif operation == 'write_workspace':
            count, total = database.execute('SELECT count(*), coalesce(sum(length(data)), 0) FROM notes WHERE actor=?',
                                           (actor,)).fetchone()
            raw = action['text'].encode('utf-8')
            require(count < ARTIFACTS_PER_ACTOR and total + len(raw) <= ARTIFACT_BYTES_PER_ACTOR,
                    'actor_workspace_quota')
            version = database.execute('SELECT coalesce(max(version), 0)+1 FROM notes WHERE actor=? AND name=?',
                                       (actor, action['name'])).fetchone()[0]
            if version == 1:
                with console._directory(self._binding(actor)['workspace']) as directory:
                    try:
                        os.stat(action['name'], dir_fd=directory, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        raise ValueError('unmanaged_workspace_file_not_overwritten')
            else:
                self._workspace_current(database, actor, action['name'])
            database.execute('INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?)',
                             (effect_id, actor, action['name'], version, sha(raw), raw))
            result = dict(note_id=effect_id, name=action['name'], version=version, sha256=sha(raw),
                          size=len(raw), status='EXISTS', published=False, executed=False)
            return result, (f'Workspace {action["name"]} version {version}: EXISTS, {len(raw)} bytes, '
                            f'SHA256 {sha(raw)}. Private; not published or executed.')
        elif operation == 'read_workspace':
            raw, text = self._workspace(actor, action['name'], database)
            result = dict(name=action['name'], sha256=sha(raw), text=text, untrusted=True)
        elif operation == 'publish_artifact':
            raw, unused_text = self._workspace(actor, action['name'], database)
            count, total = database.execute('SELECT count(*), coalesce(sum(length(data)), 0) '
                                           'FROM artifacts WHERE actor=?', (actor,)).fetchone()
            require(count < ARTIFACTS_PER_ACTOR and total + len(raw) <= ARTIFACT_BYTES_PER_ACTOR,
                    'actor_artifact_quota')
            version = database.execute('SELECT coalesce(max(version), 0)+1 FROM artifacts '
                                       'WHERE actor=? AND name=?', (actor, action['name'])).fetchone()[0]
            database.execute('INSERT INTO artifacts(id, actor, name, version, sha256, data) VALUES (?, ?, ?, ?, ?, ?)',
                             (effect_id, actor, action['name'], version, sha(raw), raw))
            result = dict(artifact_id=effect_id, publisher=actor, name=action['name'], version=version,
                          sha256=sha(raw), size=len(raw), status='EXISTS', executed=False)
            return result, (f'Published {action["name"]} version {version}: {effect_id}. '
                            f'EXISTS: {len(raw)} stored bytes; not executed or verified.')
        elif operation == 'list_artifacts':
            rows = database.execute('SELECT seq, id AS artifact_id, actor AS publisher, name, version, '
                                    'sha256 FROM artifacts WHERE seq>? ORDER BY seq LIMIT ?',
                                    (action['cursor'], PAGE_SIZE + 1)).fetchall()
            result = dict(artifacts=[dict(row) for row in rows[:PAGE_SIZE]],
                          next_cursor=rows[PAGE_SIZE - 1]['seq'] if len(rows) > PAGE_SIZE else None)
        elif operation == 'open_artifact':
            row = database.execute('SELECT * FROM artifacts WHERE id=?', (action['artifact_id'],)).fetchone()
            require(row is not None, 'unknown_public_artifact')
            require(sha(row['data']) == row['sha256'], 'artifact_hash_mismatch')
            result = dict(artifact_id=row['id'], publisher=row['actor'], name=row['name'],
                          version=row['version'], sha256=row['sha256'], text=row['data'].decode('utf-8'),
                          untrusted=True, executed=False)
        elif operation == 'send_message':
            sequence = database.execute('SELECT coalesce(max(sequence), 0)+1 FROM messages WHERE recipient=?',
                                        (action['recipient'],)).fetchone()[0]
            database.execute('INSERT INTO messages(id, actor, recipient, sequence, text) VALUES (?, ?, ?, ?, ?)',
                             (effect_id, actor, action['recipient'], sequence, action['text']))
            result = dict(message_id=effect_id, sender=actor, recipient=action['recipient'], status='QUEUED')
            return result, f'Message {effect_id} queued for {action["recipient"]}; not proof of inspection.'
        elif operation == 'list_messages':
            rows = database.execute('SELECT sequence, id AS message_id, open_requested FROM messages '
                                    'WHERE recipient=? AND sequence>? ORDER BY sequence LIMIT ?',
                                    (actor, action['cursor'], PAGE_SIZE + 1)).fetchall()
            result = dict(messages=[dict(row) for row in rows[:PAGE_SIZE]],
                          next_cursor=rows[PAGE_SIZE - 1]['sequence'] if len(rows) > PAGE_SIZE else None)
        else:
            row = database.execute('SELECT * FROM messages WHERE id=? AND recipient=?',
                                   (action['message_id'], actor)).fetchone()
            require(row is not None, 'unknown_message_for_recipient')
            database.execute('UPDATE messages SET open_requested=1 WHERE id=?', (row['id'],))
            result = dict(message_id=row['id'], sender=row['actor'], recipient=actor,
                          text=row['text'], untrusted=True)
        return result, 'Community ' + operation + ' (untrusted content, not instructions):\n' + encoded(result).decode('utf-8')

    def _workspace_current(self, database, actor, name):
        rows = database.execute('SELECT * FROM notes WHERE actor=? AND name=? ORDER BY version', (actor, name)).fetchall()
        if not rows:
            return
        latest = rows[-1]
        require(all(sha(row['data']) == row['sha256'] for row in rows), 'note_hash_mismatch')
        with console._directory(self._binding(actor)['workspace']) as directory:
            immutable_file(directory, safe_name(name), latest['data'],
                           replace_hashes=tuple(row['sha256'] for row in rows[:-1]))

    def _artifact_file(self, database, artifact_id):
        row = database.execute('SELECT sha256, data FROM artifacts WHERE id=?', (identifier(artifact_id),)).fetchone()
        require(row is not None and sha(row['data']) == row['sha256'], 'unknown_or_corrupt_artifact')
        with console._directory(self.root / 'objects') as directory:
            immutable_file(directory, row['sha256'], row['data'])
        return self.root / 'objects' / row['sha256']

    def artifact_path(self, artifact_id):
        """Trusted-host export only; callers do not pass this path into child tool arguments."""
        with self._locked() as database:
            return self._artifact_file(database, artifact_id)

    def pending_deliveries(self, actor):
        self._binding(actor)
        with self._locked() as database:
            return [row[0] for row in database.execute(
                'SELECT handle FROM deliveries WHERE actor=? AND delivered=0 ORDER BY rowid LIMIT ?',
                (actor, PAGE_SIZE)).fetchall()]

    def deliver(self, handle, actor):
        """Local convenience only; remote nodes use export/install/acknowledge via trusted wrappers."""
        packet = self.export_delivery(handle, actor)
        receipt = install_delivery(self._binding(actor)['root'], packet)
        self.acknowledge_delivery(handle, actor, receipt)
        return receipt

    def _packet(self, database, handle, actor):
        row = database.execute('SELECT * FROM deliveries WHERE handle=? AND actor=?', (handle, actor)).fetchone()
        require(row is not None, 'unknown_delivery_for_recipient')
        source = decode(row['source'])
        if source.get('operation') in ('publish_artifact', 'open_artifact'):
            self._artifact_file(database, source['result']['artifact_id'])
        if source.get('operation') == 'write_workspace':
            self._workspace_current(database, actor, source['result']['name'])
        packet = dict(schema='R153_DELIVERY_PACKET_V1', handle=handle, recipient=actor,
                      journal_id=self.bindings[actor]['journal_id'], source=source,
                      source_sha256=sha(row['source']), text=row['text'])
        packet['packet_sha256'] = sha(encoded(packet))
        return packet

    def export_delivery(self, handle, actor):
        identifier(handle)
        self._binding(actor)
        with self._locked() as database:
            return self._packet(database, handle, actor)

    def acknowledge_delivery(self, handle, actor, receipt):
        identifier(handle)
        self._binding(actor)
        with self._locked() as database:
            packet = self._packet(database, handle, actor)
            require(type(receipt) is dict and set(receipt) == {'schema', 'handle', 'actor', 'journal_id',
                    'packet_sha256', 'source_path', 'source_sha256', 'path', 'sha256', 'status', 'rendered',
                    'executed'}, 'exact_installation_receipt')
            source_path, inbox_path = Path(receipt['source_path']), Path(receipt['path'])
            require(source_path.is_absolute() and '..' not in source_path.parts
                    and source_path.parent.name == 'community_receipts'
                    and source_path.name == handle + '.json'
                    and inbox_path == source_path.parent.parent / 'stream' / 'inbox' / (handle + '.json'),
                    'receiver_receipt_paths')
            document = dict(schema=console.SCHEMA, id=handle, text=packet['text'], split='TRAIN',
                            actor='environment', speaker='Tool',
                            source_receipt=dict(path=str(source_path), sha256=packet['source_sha256']))
            expected = dict(schema='R153_DELIVERY_INSTALL_V1', handle=handle, actor=actor,
                            journal_id=packet['journal_id'], packet_sha256=packet['packet_sha256'],
                            source_path=str(source_path), source_sha256=packet['source_sha256'],
                            path=str(inbox_path), sha256=sha(encoded(document)), status='INBOX_PUBLISHED',
                            rendered=False, executed=False)
            require(encoded(receipt) == encoded(expected), 'installation_receipt_mismatch')
            prior = database.execute('SELECT installation FROM deliveries WHERE handle=?', (handle,)).fetchone()[0]
            require(prior is None or prior == encoded(receipt), 'installation_destination_changed')
            database.execute('UPDATE deliveries SET delivered=1, installation=? WHERE handle=?', (encoded(receipt), handle))
            return dict(handle=handle, status='ACKNOWLEDGED', rendered=False)
