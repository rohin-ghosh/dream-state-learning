"""Dependency-free receiving regression against the actual saved source states."""

from copy import deepcopy
import json
from pathlib import Path
import sys

from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import allocation_guard, restore_contract, verify_files
from research_loop.workers.rohin233_ovx4_recovery_20260918.base_epoch import migrate, retained_summary


class SnapshotGame:
    def restore(self, state):
        self.state = deepcopy(state)

    def snapshot(self):
        return deepcopy(self.state)


def main(root):
    config_path = root / ('EPOCH.json' if root.name == 'base' else 'CONFIG.private.json')
    config = json.loads(config_path.read_bytes())
    allocation_guard(config, config.get('physical', config.get('player_physical')))
    verify_files(root / 'source', json.loads((root / 'SOURCE_MANIFEST.json').read_bytes()))
    for physical in (0, 1):
        try:
            allocation_guard(config, physical)
        except ValueError:
            pass
        else:
            raise AssertionError('pair_device_not_denied')
    try:
        allocation_guard(config, 2, now=config['deadline_unix']+1)
    except ValueError:
        pass
    else:
        raise AssertionError('expired_deadline_not_denied')
    if root.name == 'base':
        previous = json.loads((root / 'PRESERVED_CONTROLLER.private.json').read_bytes())
        scorer = json.loads((root / 'PRESERVED_SCORER.private.json').read_bytes())
        backend, binding = deepcopy(previous['backend_state']), deepcopy(previous['binding'])
        for reference in backend['source'].values():
            relative = reference['path'].split('/source/', 1)[1]
            reference['path'] = str(root / 'source' / relative)
        for name in ('controller', 'parser'):
            relative = binding[name]['path'].split('/source/', 1)[1]
            binding[name]['path'] = str(root / 'source' / relative)
        resumed, restored = migrate(previous, scorer, backend, binding,
            backend['identity']['visible_device'], config['epoch'])
        assert retained_summary(previous, scorer) == retained_summary(resumed, restored)
        assert len(previous['events']) == len(scorer['seen']) == 207
        sessions = 1
    else:
        from research_loop.workers.rohin233_ovx4_recovery_20260918.shared_restore import RestoredHub
        from gpu import ny_caption_data as data
        registry = data.bound(config['registry'])
        first = data.bound(next(iter(config['sessions'].values())))
        hub = RestoredHub(Path(config['service_root']), registry, lambda identifier: SnapshotGame(),
            first['scene_ids'], {}, config)
        assert len(hub.sessions) == len(registry['rows'])
        for name, session in hub.sessions.items():
            restore_contract(data.bound(config['sessions'][name]), session.snapshot())
        sessions = len(hub.sessions)
    print(json.dumps(dict(status='RECEIVING_CPU_PASS',actual_restored_sessions=sessions,
        pair_devices_denied=True,expired_deadline_denied=True,source_manifest_verified=True,
        actual_saved_state_continuity=True,GPU_work=False)))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
