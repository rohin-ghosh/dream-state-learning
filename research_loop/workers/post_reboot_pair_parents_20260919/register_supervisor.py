"""Atomically register only this owner's two entries; never modify supervisor policy."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

from parent_service import HERE, read, require, save, sha


SERVICES = HERE.parent / 'post_reboot_services_20260919'


def permitted_enable(existing, desired):
    fields = ('name', 'owner', 'argv', 'cwd', 'entrypoint', 'entrypoint_sha256', 'until_unix',
              'lease_evidence', 'singleton_lock', 'local_daemon_only', 'child_native', 'restart_safe',
              'self_enforces_lease', 'foreground', 'shutdown_leaves_child_natives_running')
    return (existing.get('enabled') is False and desired.get('enabled') is True and
            existing.get('registration_status') == 'OWNER_REGISTERED_PENDING_SUPERVISOR_HORIZON' and
            all(existing.get(field) == desired.get(field) for field in fields))


def registration_entry(requested, validator):
    try:
        validator(requested)
        return dict(requested, registration_status='OWNER_REGISTERED_READY_FOR_ADOPTION'), None
    except ValueError as error:
        if str(error) != 'finite_existing_fleet_horizon_required':
            raise
        return dict(requested, enabled=False, requested_enabled=True,
                    registration_status='OWNER_REGISTERED_PENDING_SUPERVISOR_HORIZON',
                    pending='Averroes/main: reconcile supervisor cap with existing pair authority 1790791200; '
                            'do not shorten the pair horizon or replace the current healthy CPU parents.',
                    registration_handoff='research_loop/workers/post_reboot_pair_parents_20260919/TO_AVERROES.md'), str(error)


def main():
    sys.path.insert(0, str(SERVICES))
    import supervisor
    registry = SERVICES / 'services.d'
    entries = []
    for source in sorted((HERE / 'supervisor_entries').glob('pair-curriculum-*.json')):
        requested = read(source)
        require(requested['until_unix'] == 1790791200, 'exact_requested_parent_horizon')
        registered, blocker = registration_entry(requested, supervisor.validate)
        destination = registry / source.name
        if destination.exists():
            existing = read(destination)
            if existing != registered:
                require(blocker is None and permitted_enable(existing, registered),
                        'existing_registry_entry_changed_by_owner_do_not_overwrite')
                history = HERE / 'registration_history'
                history.mkdir(exist_ok=True)
                save(history / (source.stem + '_disabled_' + sha(destination) + '.json'), existing)
                save(destination, registered)
        else:
            temporary = registry / ('.' + source.name + '.' + str(time.time_ns()) + '.pending')
            with temporary.open('x') as output:
                json.dump(registered, output, indent=2, sort_keys=True)
                output.write('\n')
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, destination)
            finally:
                temporary.unlink()
        entries.append(dict(name=requested['name'], path=str(destination), sha256=sha(destination),
                            requested_manifest=str(source), requested_manifest_sha256=sha(source),
                            enabled=registered['enabled'], until_unix=requested['until_unix'],
                            registration_status=registered['registration_status'], blocker=blocker))
    receipt = dict(observed_utc=datetime.now(timezone.utc).isoformat(), addressee='Averroes / main',
                   supervisor_max_until_unix=supervisor.MAX_UNTIL, requested_until_unix=1790791200,
                   entries=entries, registry_files_registered=True,
                   adoption_confirmed=False, native_signals=0, native_restarts=0,
                   current_parents_restarted=False, supervisor_source_modified=False,
                   lease_changes=0, boot_installation_performed=False)
    save(HERE / 'SUPERVISOR_REGISTRATION_RECEIPT.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
