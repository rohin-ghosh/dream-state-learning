"""Explicit offline sidecar repair handoff preserving all community state."""

import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

from gpu import orch_r153_community_exchange as exchange
from gpu.orch_r153_community_service import validate_config


TRANSPORT = 'gpu/orch_r153_community_transport.py'
EXCHANGE = 'gpu/orch_r153_community_exchange.py'


def validate_transition(previous, successor):
    validate_config(previous)
    validate_config(successor)
    exchange.require(previous.get('profile') == 'ALL5_OVX3', 'node5_service_only')
    expected = json.loads(exchange.encoded(previous))
    old_host = previous['hosts']['ovx3']
    new_host = successor['hosts']['ovx3']
    exchange.require(re.fullmatch(r'/localhome/local-rohing/orch_r153_service_source_v[0-9]+_[0-9]{8}',
                                  new_host['repository']), 'independent_sidecar_source_required')
    exchange.require(old_host['repository'] != new_host['repository']
                     and old_host['source_sha256'][TRANSPORT] != new_host['source_sha256'][TRANSPORT],
                     'new_transport_release_required')
    expected['hosts']['ovx3']['repository'] = new_host['repository']
    expected['hosts']['ovx3']['source_sha256'][TRANSPORT] = new_host['source_sha256'][TRANSPORT]
    if EXCHANGE in old_host['source_sha256']:
        expected['hosts']['ovx3']['source_sha256'][EXCHANGE] = new_host['source_sha256'][EXCHANGE]
    exchange.require(expected == successor, 'transport_only_no_roots_cursors_recipe_or_gate_change')


def handoff(previous, successor, evidence):
    validate_transition(previous, successor)
    root = Path(previous['broker_root'])
    evidence = Path(evidence)
    exchange.require(evidence.is_absolute() and evidence.resolve() == evidence
                     and root not in evidence.parents, 'external_canonical_evidence')
    with ExitStack() as stack:
        directory = stack.enter_context(exchange.console._directory(root))
        root_stat = os.fstat(directory)
        exchange.require(root_stat.st_uid == os.geteuid() and root_stat.st_mode & 0o077 == 0,
                         'private_broker_root')
        for name in ('SERVICE_OWNER.lock', 'LOCK'):
            descriptor = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
            stack.callback(os.close, descriptor)
            current = os.fstat(descriptor)
            exchange.require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1
                             and current.st_uid == os.geteuid(), 'regular_owned_lock')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ('state.sqlite3', 'state.sqlite3-journal', 'state.sqlite3-wal', 'state.sqlite3-shm'):
            try:
                current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            exchange.require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1
                             and current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0,
                             'private_regular_database')
        database = sqlite3.connect(str(root / 'state.sqlite3'), isolation_level=None)
        stack.callback(database.close)
        prior = database.execute("SELECT value FROM metadata WHERE key='service_config'").fetchone()
        exchange.require(prior is not None and prior[0] == exchange.encoded(previous), 'exact_previous_configuration')
        unresolved = database.execute("SELECT count(*) FROM service_jobs WHERE status IN ('CPU_INTENT','CPU_UNKNOWN')").fetchone()[0]
        exchange.require(unresolved == 0, 'resolve_inflight_CPU_before_handoff')
        evidence.mkdir(mode=0o700)
        with sqlite3.connect(str(evidence / 'BEFORE.sqlite3')) as backup:
            database.backup(backup)
        os.chmod(evidence / 'BEFORE.sqlite3', 0o400)
        receipt = dict(schema='R153_SIDECAR_REPAIR_HANDOFF_V1', created_unix=time.time(),
                       previous=previous, successor=successor,
                       backup_sha256=hashlib.sha256((evidence / 'BEFORE.sqlite3').read_bytes()).hexdigest(),
                       cursors_preserved=True, jobs_preserved=True, artifacts_preserved=True,
                       messages_preserved=True, deliveries_preserved=True)
        with exchange.console._directory(evidence) as receipt_directory:
            exchange.immutable_file(receipt_directory, 'INTENT.json', exchange.encoded(receipt))
        database.execute('PRAGMA synchronous=FULL')
        database.execute('BEGIN IMMEDIATE')
        try:
            changed = database.execute("UPDATE metadata SET value=? WHERE key='service_config' AND value=?",
                                       (exchange.encoded(successor), exchange.encoded(previous))).rowcount
            exchange.require(changed == 1, 'previous_config_compare_and_swap')
            database.commit()
        except BaseException:
            database.rollback()
            raise
        with exchange.console._directory(evidence) as receipt_directory:
            exchange.immutable_file(receipt_directory, 'APPLIED.json', exchange.encoded(receipt))
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', required=True, type=Path)
    parser.add_argument('--successor', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    options = parser.parse_args()
    previous = exchange.decode(options.previous.read_bytes())
    successor = exchange.decode(options.successor.read_bytes())
    print(json.dumps(handoff(previous, successor, options.evidence), sort_keys=True))


if __name__ == '__main__':
    main()
