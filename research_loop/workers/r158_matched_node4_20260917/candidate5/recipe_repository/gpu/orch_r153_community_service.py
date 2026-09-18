"""VM-side five-life exchange and asynchronous CPU service; explicit config/run only."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import time

from gpu import orch_r153_community_exchange as exchange
from gpu import orch_r153_community_transport as transport_module


SCHEMA = 'R153_COMMUNITY_SERVICE_V1'
MAX_JOBS_PER_ACTOR = 2048
CONFIG_FIELDS = {'schema', 'repository', 'broker_root', 'mirror_root', 'hosts', 'agents',
                 'poll_seconds', 'max_records', 'max_bytes', 'max_polls', 'deadline_unix',
                 'max_cpu_calls_per_actor', 'kernel_policy'}
AGENT_FIELDS = {'host', 'root', 'journal_id', 'start_index', 'start_after_sha256'}


def parse_action(raw):
    exchange.require(type(raw) is str and len(raw.encode('utf-8')) <= transport_module.blocks.MAX_BYTES,
                     'bounded_action_generation')
    text = raw.strip()
    fenced = re.fullmatch(r'```json[ \t]*\r?\n(.*?)\r?\n```', text, re.DOTALL)
    if fenced is not None:
        text = fenced.group(1)
    return exchange.decode(text)


def classify(raw):
    text = raw.strip()
    if text.startswith('{') or text.startswith('```json'):
        try:
            action = parse_action(raw)
        except (ValueError, TypeError, UnicodeError):
            return 'REJECTED', {'reason': 'Malformed exchange JSON; use one whole JSON object or one whole json fence.'}
        return 'EXCHANGE', action
    route, report = transport_module.code_route(raw)
    if route in ('CPU', 'KERNEL'):
        return route, report
    if report['attempted']:
        return 'REJECTED', {'reason': report['reason']}
    return 'IGNORED', None


def validate_config(config):
    exchange.require(type(config) is dict and set(config) in (CONFIG_FIELDS, CONFIG_FIELDS | {'profile'})
                     and config['schema'] == SCHEMA,
                     'exact_service_config')
    profile = config.get('profile', 'THREE_A40R_TWO_OVX2')
    exchange.require(profile in transport_module.HOST_PROFILES
                     and frozenset(config['hosts']) == transport_module.HOST_PROFILES[profile], 'exact_service_host_profile')
    exchange.require(config['kernel_policy'] in ('DISABLED_SEPARATE_OWNER_REQUIRED', 'R148_FILTERED_A40R'),
                     'no_unfiltered_parallel_kernel_or_R140_CPU_owner')
    paths = [Path(config[key]) for key in ('repository', 'broker_root', 'mirror_root')]
    exchange.require(all(path.is_absolute() and '..' not in path.parts and path.resolve() == path for path in paths),
                     'canonical_service_paths')
    for position, path in enumerate(paths):
        for other in paths[position + 1:]:
            exchange.require(path != other and path not in other.parents and other not in path.parents,
                             'disjoint_repository_broker_mirrors')
    transport_module.PinnedTransport(config['repository'], config['hosts'])
    exchange.require(type(config['agents']) is dict and set(config['agents']) == set(exchange.ACTORS),
                     'exact_five_service_agents')
    host_counts, roots, journals = {host: 0 for host in config['hosts']}, set(), set()
    for actor, agent in config['agents'].items():
        exchange.require(type(agent) is dict and set(agent) == AGENT_FIELDS
                         and agent['host'] in host_counts, 'exact_agent_config')
        root = Path(agent['root'])
        exchange.require(root.is_absolute() and '..' not in root.parts
                         and any('r153' in part.lower() for part in root.parts), 'new_remote_R153_root')
        exchange.require(type(agent['journal_id']) is str and re.fullmatch('[0-9a-f]{32}', agent['journal_id']),
                         'pinned_actor_journal_id')
        exchange.require(type(agent['start_index']) is int and 0 <= agent['start_index'] < 10**18,
                         'bounded_initial_cursor')
        exchange.identifier(agent['start_after_sha256'])
        exchange.require(agent['start_index'] > 0 or agent['start_after_sha256'] == '0' * 64, 'initial_cursor_anchor')
        exchange.require((agent['host'], str(root)) not in roots and agent['journal_id'] not in journals,
                         'independent_remote_roots_and_journals')
        roots.add((agent['host'], str(root)))
        journals.add(agent['journal_id'])
        host_counts[agent['host']] += 1
    expected_counts = {'ovx3': 5} if profile == 'ALL5_OVX3' else {'a40r': 3, 'ovx2': 2}
    exchange.require(host_counts == expected_counts, 'exact_profile_learner_counts')
    exchange.require(profile != 'ALL5_OVX3' or config['kernel_policy'] == 'DISABLED_SEPARATE_OWNER_REQUIRED',
                     'ovx3_kernel_not_admitted_by_a40r_policy')
    for field, minimum, maximum in (('max_records', 1, transport_module.MAX_SCAN_RECORDS),
            ('max_bytes', 4096, transport_module.MAX_WIRE_BYTES // 2), ('max_polls', 1, 100000),
            ('max_cpu_calls_per_actor', 1, 512)):
        exchange.require(type(config[field]) is int and minimum <= config[field] <= maximum, 'bounded_' + field)
    exchange.require(type(config['poll_seconds']) in (int, float) and 0.05 <= config['poll_seconds'] <= 60,
                     'bounded_poll_seconds')
    exchange.require(type(config['deadline_unix']) in (int, float) and math.isfinite(config['deadline_unix'])
                     and config['deadline_unix'] > 0, 'finite_service_deadline')
    return config


def build_config(repository, broker_root, mirror_root, agents, host_repositories, gate_sha256, deadline_unix,
                 *, kernel_policy='DISABLED_SEPARATE_OWNER_REQUIRED', max_cpu_calls_per_actor=64,
                 profile='THREE_A40R_TWO_OVX2', gate_roots=None):
    repository = Path(repository).absolute()
    exchange.require(profile in transport_module.HOST_PROFILES, 'known_service_profile')
    selected_hosts = transport_module.HOST_PROFILES[profile]
    exchange.require(set(host_repositories) == selected_hosts and set(gate_sha256) == selected_hosts,
                     'profile_host_configuration')
    exchange.require(gate_roots is None and profile != 'ALL5_OVX3'
                     or type(gate_roots) is dict and set(gate_roots) == selected_hosts, 'explicit_profile_gate_roots')
    sources = transport_module.source_pins(repository)
    hosts = {host: dict(repository=host_repositories[host], source_sha256=sources,
                       wrapper_sha256=exchange.sha((repository / transport_module.WRAPPERS[host]).read_bytes()),
                       gate_sha256=gate_sha256[host]) for host in selected_hosts}
    if gate_roots is not None:
        for host in hosts:
            hosts[host]['gate_root'] = transport_module.validate_gate_root(gate_roots[host])
    config = dict(schema=SCHEMA, repository=str(repository), broker_root=str(broker_root),
        mirror_root=str(mirror_root), hosts=hosts, agents=agents, poll_seconds=2, max_records=12,
        max_bytes=16 * 1024 * 1024, max_polls=100000, deadline_unix=deadline_unix,
        max_cpu_calls_per_actor=max_cpu_calls_per_actor, kernel_policy=kernel_policy)
    if profile != 'THREE_A40R_TWO_OVX2':
        config['profile'] = profile
    return validate_config(config)


class CommunityService:
    def __init__(self, config, *, transport=None, executor=None):
        self.config = json.loads(exchange.encoded(validate_config(config)))
        self.transport = transport_module.PinnedTransport(config['repository'], config['hosts']) if transport is None else transport
        self.executor = executor
        self.owns_executor = executor is None
        self.futures = {}
        mirror_root = Path(config['mirror_root'])
        mirror_root.mkdir(mode=0o700, exist_ok=True)
        with exchange.console._directory(mirror_root) as directory:
            current = os.fstat(directory)
            exchange.require(current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0, 'private_mirror_parent')
        bindings = {}
        for actor, agent in config['agents'].items():
            root = mirror_root / actor
            for path in (root, root / 'stream', root / 'stream' / 'records', root / 'stream' / 'inbox', root / 'workspace'):
                path.mkdir(mode=0o700, exist_ok=True)
                with exchange.console._directory(path.parent) as directory:
                    os.fsync(directory)
            with exchange.console._directory(root / 'stream') as directory:
                exchange.immutable_file(directory, 'JOURNAL.json', exchange.encoded(
                    dict(schema='R125_STREAM_JOURNAL_V1', journal_id=agent['journal_id'])))
            bindings[actor] = dict(root=str(root), workspace=str(root / 'workspace'), journal_id=agent['journal_id'])
        self.broker = exchange.CommunityExchange(config['broker_root'], bindings, action_parser=parse_action)
        with self.broker._locked() as database:
            for statement in (
                'CREATE TABLE IF NOT EXISTS service_cursors (actor TEXT PRIMARY KEY, next_index INTEGER NOT NULL, '
                'head TEXT NOT NULL, error TEXT)',
                'CREATE TABLE IF NOT EXISTS service_jobs (id TEXT PRIMARY KEY, actor TEXT NOT NULL, '
                'snapshot BLOB NOT NULL, status TEXT NOT NULL, outcome BLOB, cpu_link BLOB)',
                'CREATE TABLE IF NOT EXISTS service_feedback (handle TEXT PRIMARY KEY, actor TEXT NOT NULL, '
                'packet BLOB NOT NULL, installation BLOB)',
            ):
                database.execute(statement)
            configuration = exchange.encoded(config)
            prior = database.execute("SELECT value FROM metadata WHERE key='service_config'").fetchone()
            exchange.require(prior is None or prior[0] == configuration, 'service_config_changed')
            database.execute("INSERT OR IGNORE INTO metadata VALUES ('service_config', ?)", (configuration,))
            for actor, agent in config['agents'].items():
                database.execute('INSERT OR IGNORE INTO service_cursors(actor, next_index, head) VALUES (?, ?, ?)',
                                 (actor, agent['start_index'], agent['start_after_sha256']))

    def _error(self, actor, error):
        reason = str(error)[:240] if isinstance(error, ValueError) else type(error).__name__
        with self.broker._locked() as database:
            database.execute('UPDATE service_cursors SET error=? WHERE actor=?', (reason, actor))

    def _ingest(self, actor):
        with self.broker._locked() as database:
            cursor = database.execute('SELECT next_index, head FROM service_cursors WHERE actor=?', (actor,)).fetchone()
        batch = self.transport.pull(self.config['agents'][actor], cursor['next_index'], cursor['head'],
                                    max_records=self.config['max_records'], max_bytes=self.config['max_bytes'])
        expected = {'schema', 'manifest', 'start_cursor', 'start_head_sha256', 'next_cursor',
                    'head_sha256', 'scanned_records', 'scanned_bytes', 'snapshots'}
        agent = self.config['agents'][actor]
        exchange.require(type(batch) is dict and set(batch) == expected and batch['schema'] == 'R153_COMMITTED_PULL_V1'
            and batch['manifest'] == dict(schema='R125_STREAM_JOURNAL_V1', journal_id=agent['journal_id'])
            and batch['start_cursor'] == cursor['next_index'] and batch['start_head_sha256'] == cursor['head'],
            'bound_remote_batch_cursor')
        exchange.require(type(batch['scanned_records']) is int and 0 <= batch['scanned_records'] <= self.config['max_records']
            and batch['next_cursor'] == cursor['next_index'] + batch['scanned_records']
            and type(batch['scanned_bytes']) is int and 0 <= batch['scanned_bytes'] <= self.config['max_bytes']
            and type(batch['snapshots']) is list and len(batch['snapshots']) <= batch['scanned_records'], 'bounded_remote_batch')
        exchange.identifier(batch['head_sha256'])
        if batch['scanned_records'] == 0:
            exchange.require(batch['head_sha256'] == cursor['head'], 'empty_batch_no_head_change')
        jobs = []
        for snapshot in batch['snapshots']:
            response = snapshot['records'][1]
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=response['index'], record_sha256=response['sha256'])
            exchange.verify_snapshot(actor, agent['journal_id'], origin, snapshot, {}, lambda text: {})
            exchange.require(cursor['next_index'] <= response['index'] + 1 < batch['next_cursor'], 'commit_inside_scanned_window')
            job_id = exchange.sha(exchange.encoded([actor, agent['journal_id'], response['index'], response['sha256']]))
            jobs.append((job_id, snapshot))
        with self.broker._locked() as database:
            current = database.execute('SELECT next_index, head FROM service_cursors WHERE actor=?', (actor,)).fetchone()
            exchange.require(tuple(current) == tuple(cursor), 'single_service_cursor_owner')
            count = database.execute('SELECT count(*) FROM service_jobs WHERE actor=?', (actor,)).fetchone()[0]
            exchange.require(count + len(jobs) <= MAX_JOBS_PER_ACTOR, 'service_job_quota')
            for job_id, snapshot in jobs:
                raw = exchange.encoded(snapshot)
                existing = database.execute('SELECT snapshot FROM service_jobs WHERE id=?', (job_id,)).fetchone()
                exchange.require(existing is None or existing[0] == raw, 'conflicting_committed_snapshot')
                database.execute('INSERT OR IGNORE INTO service_jobs(id, actor, snapshot, status) VALUES (?, ?, ?, ?)',
                                 (job_id, actor, raw, 'PENDING'))
            database.execute('UPDATE service_cursors SET next_index=?, head=?, error=NULL WHERE actor=?',
                             (batch['next_cursor'], batch['head_sha256'], actor))

    def _finish(self, job_id, status, outcome):
        with self.broker._locked() as database:
            database.execute('UPDATE service_jobs SET status=?, outcome=? WHERE id=?',
                             (status, exchange.encoded(outcome), job_id))

    def _feedback(self, job, origin, reason):
        actor = job['actor']
        effect_id = exchange.sha(exchange.encoded(['service-feedback', job['id']]))
        handle = exchange.sha(exchange.encoded([effect_id, actor]))
        source = dict(schema=exchange.SCHEMA, effect_id=effect_id, status='RECORDED', actor=actor,
                      origin=dict(origin, actor=actor), operation='SERVICE_NOTICE', executed=False,
                      training_target=False, result=dict(reason=reason))
        packet = dict(schema='R153_DELIVERY_PACKET_V1', handle=handle, recipient=actor,
                      journal_id=self.config['agents'][actor]['journal_id'], source=source,
                      source_sha256=exchange.sha(exchange.encoded(source)), text='Community service: ' + reason)
        packet['packet_sha256'] = exchange.sha(exchange.encoded(packet))
        with self.broker._locked() as database:
            existing = database.execute('SELECT packet FROM service_feedback WHERE handle=?', (handle,)).fetchone()
            exchange.require(existing is None or existing[0] == exchange.encoded(packet), 'stable_service_feedback')
            database.execute('INSERT OR IGNORE INTO service_feedback(handle, actor, packet) VALUES (?, ?, ?)',
                             (handle, actor, exchange.encoded(packet)))

    def _artifact_link(self, actor, report):
        with self.broker._locked() as database:
            receipts = database.execute('SELECT receipt FROM effects WHERE actor=? ORDER BY rowid DESC', (actor,)).fetchall()
        for row in receipts:
            receipt = exchange.decode(row[0])
            if receipt['operation'] != 'open_artifact':
                continue
            artifact = receipt['result']
            normalized, changes = transport_module.blocks.normalize_punctuation(artifact['text'])
            if transport_module.blocks.sha(normalized) != report['source_sha256']:
                continue
            return dict(artifact_id=artifact['artifact_id'], artifact_sha256=artifact['sha256'],
                        read_effect_id=receipt['effect_id'], read_origin=receipt['origin'],
                        execution_raw_source_sha256=report['raw_source_sha256'],
                        execution_source_sha256=report['source_sha256'], artifact_normalization_changes=changes,
                        match='EXACT_RAW' if artifact['sha256'] == report['raw_source_sha256'] else 'NORMALIZED_PUNCTUATION')
        return None

    def _submit_cpu(self, job, origin, report, *, start):
        actor = job['actor']
        if actor in self.futures:
            return
        exchange.require(not start or time.time() + 120 < self.config['deadline_unix'], 'CPU_deadline_reserve')
        with self.broker._locked() as database:
            link = exchange.decode(job['cpu_link']) if job['cpu_link'] else None
        if job['status'] == 'PENDING':
            link = self._artifact_link(actor, report)
            with self.broker._locked() as database:
                count = database.execute("SELECT count(*) FROM service_jobs WHERE actor=? AND status LIKE 'CPU_%'", (actor,)).fetchone()[0]
                exchange.require(count < self.config['max_cpu_calls_per_actor'], 'CPU_call_budget')
                database.execute("UPDATE service_jobs SET status='CPU_INTENT', cpu_link=? WHERE id=?",
                                 (exchange.encoded(link) if link else None, job['id']))
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix='r153-cpu')
        future = self.executor.submit(self.transport.cpu, self.config['agents'][actor], origin,
                                      start=start, artifact_link=link)
        self.futures[actor] = (job['id'], future)

    def _cpu_results(self):
        for actor, (job_id, future) in list(self.futures.items()):
            if not future.done():
                continue
            del self.futures[actor]
            try:
                result = future.result()
                with self.broker._locked() as database:
                    job = database.execute('SELECT snapshot, cpu_link FROM service_jobs WHERE id=?', (job_id,)).fetchone()
                snapshot = exchange.decode(job['snapshot'])
                previous, response, committed = snapshot['records']
                origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=response['index'], record_sha256=response['sha256'])
                route, report = transport_module.code_route(response['document']['response']['raw'])
                request = transport_module.make_request(report['source'], origin)
                proof = dict(kind='TRAIN_CHILD_RESPONSE', child_generated=True,
                             journal_id=self.config['agents'][actor]['journal_id'], record_sha256=response['sha256'],
                             request_record_sha256=previous['sha256'], commit_record_sha256=committed['sha256'],
                             code_transformation=transport_module.blocks.metadata(report))
                exchange.require(result.get('schema') == 'R153_CPU_DELIVERY_V1'
                    and result.get('journal_id') == self.config['agents'][actor]['journal_id']
                    and result.get('request_id') == request['request_id']
                    and result.get('source_sha256') == request['source_sha256']
                    and result.get('origin') == proof
                    and result.get('artifact_link') == (exchange.decode(job['cpu_link']) if job['cpu_link'] else None),
                    'bound_CPU_transport_result')
                status = 'CPU_DONE' if result['status'] == 'PUBLISHED' else 'CPU_UNKNOWN'
                self._finish(job_id, status, result)
            except Exception as error:
                self._finish(job_id, 'CPU_UNKNOWN', dict(error_type=type(error).__name__, executed=None))
                self._error(actor, error)

    def _process(self, actor):
        with self.broker._locked() as database:
            jobs = database.execute("SELECT * FROM service_jobs WHERE actor=? AND status IN ('PENDING','CPU_INTENT','CPU_UNKNOWN') "
                                    'ORDER BY rowid LIMIT ?', (actor, exchange.PAGE_SIZE)).fetchall()
        cpu_blocked = actor in self.futures
        for job in jobs:
            snapshot = exchange.decode(job['snapshot'])
            response = snapshot['records'][1]
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=response['index'], record_sha256=response['sha256'])
            route, payload = classify(response['document']['response']['raw'])
            if route == 'CPU':
                if cpu_blocked:
                    continue
                start = job['status'] == 'PENDING'
                if job['status'] == 'CPU_UNKNOWN' and job['outcome']:
                    start = exchange.decode(job['outcome']).get('status') == 'NOT_STARTED'
                try:
                    self._submit_cpu(job, origin, payload, start=start)
                    cpu_blocked = True
                except ValueError as error:
                    self._feedback(job, origin, str(error))
                    self._finish(job['id'], 'REJECTED', dict(reason=str(error)))
                continue
            if route == 'EXCHANGE':
                try:
                    result = self.broker.apply_snapshot(actor, snapshot, payload)
                    self._finish(job['id'], 'EXCHANGE_DONE', result)
                except (ValueError, OSError) as error:
                    reason = str(error) if isinstance(error, ValueError) else type(error).__name__
                    self._feedback(job, origin, 'Exchange rejected: ' + reason)
                    self._finish(job['id'], 'REJECTED', dict(reason=reason))
            elif route == 'KERNEL':
                external = self.config['kernel_policy'] == 'R148_FILTERED_A40R' and self.config['agents'][actor]['host'] == 'a40r'
                reason = ('Kernel block routed to the separate R148 owner; wait for its execution receipt. This CPU service did not execute it.'
                          if external else 'This block is kernel-routed; the kernel service is not connected here. No code ran.')
                self._feedback(job, origin, reason)
                self._finish(job['id'], 'ROUTED_KERNEL' if external else 'KERNEL_UNCONNECTED',
                             dict(transport_module.blocks.metadata(payload),
                                  route='routed_kernel' if external else 'not_connected', executed_by_CPU=False))
            elif route == 'REJECTED':
                self._feedback(job, origin, payload['reason'])
                self._finish(job['id'], 'REJECTED', payload)
            else:
                self._finish(job['id'], 'IGNORED', dict(reason='No chosen exchange action or executable first block.'))

    def _deliver(self, actor):
        for handle in self.broker.pending_deliveries(actor):
            packet = self.broker.export_delivery(handle, actor)
            receipt = self.transport.push(self.config['agents'][actor], packet)
            self.broker.acknowledge_delivery(handle, actor, receipt)
        with self.broker._locked() as database:
            feedback = database.execute('SELECT handle, packet FROM service_feedback WHERE actor=? AND installation IS NULL '
                                        'ORDER BY rowid LIMIT ?', (actor, exchange.PAGE_SIZE)).fetchall()
        for row in feedback:
            packet = exchange.decode(row['packet'])
            receipt = self.transport.push(self.config['agents'][actor], packet)
            expected = transport_module.delivery_document(self.config['agents'][actor]['root'], packet)
            exchange.require(receipt.get('handle') == row['handle'] and receipt.get('actor') == actor
                             and receipt.get('status') == 'INBOX_PUBLISHED'
                             and receipt.get('packet_sha256') == packet['packet_sha256']
                             and receipt.get('sha256') == exchange.sha(exchange.encoded(expected)), 'service_feedback_installation')
            with self.broker._locked() as database:
                database.execute('UPDATE service_feedback SET installation=? WHERE handle=?',
                                 (exchange.encoded(receipt), row['handle']))

    def tick(self):
        exchange.require(time.time() < self.config['deadline_unix'], 'service_deadline_reached')
        self._cpu_results()
        for actor in exchange.ACTORS:
            for operation in (self._ingest, self._process, self._deliver):
                try:
                    operation(actor)
                except Exception as error:
                    self._error(actor, error)
        self._cpu_results()
        return self.status()

    def status(self):
        with self.broker._locked() as database:
            cursors = [dict(row) for row in database.execute('SELECT * FROM service_cursors ORDER BY actor')]
            jobs = [dict(row) for row in database.execute('SELECT actor, status, count(*) AS count FROM service_jobs GROUP BY actor,status')]
            pending = database.execute('SELECT count(*) FROM deliveries WHERE delivered=0').fetchone()[0]
            pending += database.execute('SELECT count(*) FROM service_feedback WHERE installation IS NULL').fetchone()[0]
        return dict(schema=SCHEMA, cursors=cursors, jobs=jobs, pending_deliveries=pending,
                    cpu_inflight=sorted(self.futures), kernel_connected=False,
                    profile=self.config.get('profile', 'THREE_A40R_TWO_OVX2'),
                    external_kernel_configured=self.config['kernel_policy'] == 'R148_FILTERED_A40R')

    def run(self, *, once=False):
        with exchange.console._directory(self.broker.root) as directory:
            descriptor = os.open('SERVICE_OWNER.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                                 0o600, dir_fd=directory)
            try:
                current = os.fstat(descriptor)
                exchange.require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1, 'regular_service_owner_lock')
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                for unused in range(1 if once else self.config['max_polls']):
                    if time.time() >= self.config['deadline_unix']:
                        break
                    self.tick()
                    if once:
                        break
                    time.sleep(self.config['poll_seconds'])
                return self.status()
            finally:
                os.close(descriptor)

    def close(self):
        if self.executor is not None and self.owns_executor:
            self.executor.shutdown(wait=False, cancel_futures=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check-config', action='store_true')
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--once', action='store_true')
    options = parser.parse_args(argv)
    config = validate_config(exchange.decode(transport_module.cpu.read_regular(options.config, 2 * 1024 * 1024)))
    if options.check_config:
        print(json.dumps(dict(schema=SCHEMA, status='CONFIG_VALID_ONLY', remote_checked=False)))
        return 0
    service = CommunityService(config)
    try:
        print(json.dumps(service.run(once=options.once), sort_keys=True))
    finally:
        service.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
