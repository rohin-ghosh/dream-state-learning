"""Prepare immutable CPU successor receipts after actual LOAD; no activation."""

import argparse
import json
from pathlib import Path

from c2_parent_continue import FLEET, validate_config_change
from checkpoint_tail_parent_binding import CONTROL, ROOT, WALL
from deadline_resume import sha, write


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
OLD_CONFIG = FLEET / 'LIVE_CONVERSATION_PARENT14_CONFIG.json'
OLD_OUTPUT = FLEET / 'LIVE_CONVERSATION_PARENT14/run'


def proposed_config(previous, binding, binding_path, binding_sha, reserved, predecessor_sha):
    if (binding['status'] != 'LOADED' or binding['root'] != ROOT
            or binding['guard_path'] != str(CONTROL / 'GUARD.json') or binding['hard_end_unix'] != WALL):
        raise ValueError('actual_new_C2_LOADED_required_not_dispatch')
    result = dict(previous, hard_end_unix=WALL, predecessor_output=str(OLD_OUTPUT),
        predecessor_started_sha256=predecessor_sha,
        start_after_response_count=max(previous['start_after_response_count'], reserved),
        native_binding_path=binding_path, native_binding_sha256=binding_sha)
    validate_config_change(previous, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--remote-binding-path', required=True)
    parser.add_argument('--remote-operator', required=True)
    parser.add_argument('--receipt-directory', type=Path, required=True)
    parser.add_argument('--parent-output', type=Path, required=True)
    arguments = parser.parse_args()
    binding = json.loads(arguments.binding.read_bytes())
    previous = json.loads(OLD_CONFIG.read_bytes())
    reserved = max([previous['start_after_response_count']] + [json.loads(path.read_bytes())['response_count']
        for path in OLD_OUTPUT.glob('parent_*/SOURCE.json')])
    config = proposed_config(previous, binding, arguments.remote_binding_path, sha(arguments.binding),
        reserved, sha(OLD_OUTPUT / 'STARTED.json'))
    directory = arguments.receipt_directory.absolute()
    directory.mkdir(parents=True, exist_ok=False)
    config_path = directory / 'CHECKPOINT_TAIL_PARENT_CONFIG.json'
    write(config_path, config)
    files = [OWN / 'checkpoint_tail_parent_continue.py', OWN / 'checkpoint_tail_parent_prepare.py',
        OWN / 'checkpoint_tail_parent_binding.py', OWN / 'deadline_resume.py', OWN / 'receipt_window.py',
        OWN / 'c2_parent_continue.py', FLEET / 'r202_parent.py', FLEET / 'R230_PARENT_CURRICULUM.md',
        FLEET.parents[1] / 'provider_route.py', FLEET.parents[1] / 'console_baseline.py',
        REPO / 'gpu/orch_r133_programme_parent.py', REPO / 'gpu/orch_route_parent_campaign_providers.py',
        config_path, OLD_CONFIG, Path(previous['principles_path']), Path(previous['programme_path'])]
    remote_names = ['checkpoint_tail_parent_binding.py', 'deadline_resume.py', 'receipt_window.py']
    manifest = dict(status='PREPARED_NOT_ACTIVATED', config_path=str(config_path),
        predecessor_config_path=str(OLD_CONFIG), output=str(arguments.parent_output.absolute()),
        remote_operator=arguments.remote_operator, policy_addendum=str(FLEET / 'R230_PARENT_CURRICULUM.md'),
        local_source_sha256={str(path): sha(path) for path in files},
        remote_helper_sha256={str(Path(arguments.remote_operator) / name): sha(OWN / name) for name in remote_names},
        hard_end_unix=WALL, original_parent_view_preserved=True, native_signals=[], journal_writes=0,
        old_waiter_must_be_drained_by_owner=dict(pid=3590563, start_ticks='186658124'),
        old_parent_must_be_drained_by_owner=dict(pid=471781, start_ticks='183179491'))
    write(directory / 'CHECKPOINT_TAIL_PARENT_MANIFEST.json', manifest)
    print(json.dumps(dict(status=manifest['status'], manifest=str(directory / 'CHECKPOINT_TAIL_PARENT_MANIFEST.json'),
        manifest_sha256=sha(directory / 'CHECKPOINT_TAIL_PARENT_MANIFEST.json'), native_signals=[]), indent=2))


if __name__ == '__main__':
    main()
