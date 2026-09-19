"""Register only P3 with Averroes's existing local supervisor; no starts."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import runner


SERVICES = runner.HERE.parent / 'post_reboot_services_20260919'


def entry():
    restart = runner.HERE / 'restart.py'
    manifest = runner.HERE / 'P3_RETRY_PARENT_MANIFEST.json'
    return dict(name='p3-parent', enabled=True, kind='parent',
        owner='P3 recovery owner; Main; supervisor coordination to Averroes',
        approval_scope='User 2026-09-19: finish P3 fresh xhigh publication/REQUEST-to-ACT receipt and supervisor registration with Averroes; no native changes',
        local_daemon_only=True, child_native=False, restart_safe=True,
        self_enforces_lease=True, foreground=True, shutdown_leaves_child_natives_running=True,
        argv=['/usr/bin/python3', '-B', str(restart)], cwd=str(runner.HERE.parents[2]),
        entrypoint=str(restart), entrypoint_sha256=runner.sha(restart), until_unix=1790359200,
        lease_evidence=dict(path=str(manifest), sha256=runner.sha(manifest), json_pointer='/hard_end_unix'),
        singleton_lock=str(runner.LEDGER / 'PARENT_OPERATOR.lock'),
        existing_live_argv=['/usr/bin/python3', '-B', str(runner.HERE / 'runner.py')],
        current_adoption='Existing parent protected by original singleton lock; no argv replacement or signals',
        restart_behavior='Fresh native/guard/source/ledger preflight then same-PID exec into existing pinned runner; incomplete attempts fail closed',
        handoff=str(runner.HERE / 'TO_MAIN_AND_AVERROES.md'))


def publish_registry(document, target):
    source = runner.HERE / 'SUPERVISOR_ENTRY.json'
    if target.exists():
        if json.loads(target.read_text()) != document:
            raise ValueError('conflicting_existing_P3_registration_no_overwrite')
        return False
    runner.save(source, document)
    os.link(source, target)
    return True


def main():
    os.umask(0o077)
    sys.path.insert(0, str(SERVICES))
    spec = importlib.util.spec_from_file_location('p3_registration_supervisor', SERVICES / 'supervisor.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    document = entry()
    module.validate(document)
    state = json.loads((runner.HERE / 'PROCESS.json').read_text())
    actual = runner.process(state['process']['pid'])
    if not actual or actual['state'] in {'Z', 'X'} or any(actual[field] != state['process'][field]
            for field in ('boot_id', 'pid', 'start_ticks', 'command_sha256')):
        raise ValueError('live_parent_required_for_no_launch_registration')
    if not module.lock_busy(runner.LEDGER / 'PARENT_OPERATOR.lock'):
        raise ValueError('original_parent_lock_must_already_be_owned')
    target = SERVICES / 'services.d/p3-parent.json'
    created = publish_registry(document, target)
    runner.save(runner.HERE / 'SUPERVISOR_REGISTRATION.json', dict(
        observed_utc=runner.utc(time.time()), target=str(target), manifest_sha256=runner.sha(target),
        installed=created, registry_validated=True, parent=actual, direct_starts=0,
        native_signals=0, boot_enabled=False, installation_status='BLOCKED_UNINSTALLED',
        supervisor_heartbeat_pending=True))
    print(json.dumps(dict(status='P3_REGISTERED_NO_PROCESS_ACTION', created=created,
        manifest_sha256=runner.sha(target), parent_pid=actual['pid'])))


if __name__ == '__main__':
    main()
