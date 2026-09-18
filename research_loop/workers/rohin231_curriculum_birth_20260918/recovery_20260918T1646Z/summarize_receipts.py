"""Publish only bounded runtime hashes/counts and parent delivery bindings."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def summarize_parent(private, start):
    publications = []
    for result_path in sorted(private.glob('*/RESULT.json')):
        result = read(result_path)
        if result.get('completed_unix', 0) < start:
            continue
        publication_path = result_path.parent / 'PUBLICATION.json'
        item = dict(provider_completed_unix=result['completed_unix'],
            result_sha256=sha(result_path), model=result.get('model'), raw_parent_text_exported=False)
        if publication_path.exists():
            receipt = read(publication_path)
            publication = receipt['publication']
            item['publication'] = {key: publication[key] for key in ('id', 'sha256')}
            marker = private / ('RENDER_' + publication['id'] + '.json')
            if marker.exists():
                render = read(marker)
                item['render'] = {key: render[key] for key in ('request_index', 'request_sha256', 'started_unix')}
            else:
                item['render'] = None
        publications.append(item)
    latest_path = private / 'LATEST.json'
    latest = read(latest_path) if latest_path.exists() else None
    return dict(latest=latest, new_provider_responses=publications,
        historical_reused_publications_not_counted_as_new=True, no_child_answer_claim=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('observation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    observation = read(arguments.observation)
    receipt = dict(schema='R233_PAIR_CURRENT_PUBLIC_RECEIPT_V1',
        summarized_utc=datetime.now(timezone.utc).isoformat(),
        observations=observation, observation_file_sha256=sha(arguments.observation),
        allocation=read(HERE / 'ALLOCATION_DATE_CORRECTION.json'),
        parents={
            'learner': summarize_parent(HERE.parent / 'private/parent', 1789750785),
            'frozen': summarize_parent(HERE.parent / 'r232_pair/private/frozen_parent', 1789751768)},
        deadline_control=dict(learner_native_owner='Main',
            main_actual_guard=dict(pid=418521, start_ticks='9776388', armed_unix=1789752179.512767,
                term_at_unix=1789754380, kill_grace_seconds=5,
                source_sha256='19a8180170ae65c7503be2c4c09b11d91c9d9ff6ac2da1ea8fb3edffde2dfbaa',
                canceled_unix=1789752608.8327272, guard_exit_confirmed=True,
                independently_read_utc='2026-09-18T17:31:19Z', native_signals=[], no_pause=True),
            former_complete_watcher=dict(pid=415506, canceled_unix=1789752064.8141506,
                before_first_action=True, native_signals=0),
            parent_only_guard=dict(pid=2887549, target_pid=2779281,
                canceled_unix=1789752499.986508, native_signals=0),
            parent_renewals={arm: read(HERE / 'private' / ('RENEW_PARENT_' + arm + '.json'))
                for arm in ('frozen', 'learner')},
            native_horizon_updated=False,
            remaining_native_horizons_utc={'learner': '2026-09-18T23:30:00Z', 'frozen': '2026-09-18T18:00:00Z'}),
        every_sleep_external_queue_reenrollment='AWAITING_LEIBNIZ_RECEIPT',
        raw_console_exported=False, credentials_exported=False,
        checkpoint_rng_not_resident_unsaved_sampling_rng=True)
    arguments.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
