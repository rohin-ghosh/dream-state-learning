"""Read-only, finite observation of the two already-published Astra nudges."""

import argparse
import fcntl
import os
from pathlib import Path
import time

from gpu import orch_r158_kernel_execution as runtime


service = runtime.service
PUBLICATION = 'astra_main_nudge_20260917t0422z'
MAX_POLLS = 180
POLL_SECONDS = 15


def document(path):
    return service.cpu.read_document(service.read(path, 1048576))


def mutable_state(path):
    for attempt in range(3):
        try:
            return document(path)
        except ValueError as error:
            if str(error) != 'file_changed_during_read' or attempt == 2:
                raise
            time.sleep(0.02)


def match_record(record, publication, text, registered):
    payload = record['document']
    reference = dict(index=record['index'], sha256=record['sha256'])
    if record['kind'] == 'INBOX' and payload['message']['id'] == publication['id']:
        message = payload['message']
        service.require(message['speaker'] == 'Astra' and message['actor'] == 'parent'
                        and message['text'] == text and message['split'] == 'TRAIN'
                        and payload['source_sha256'] == publication['sha256'], 'exact_Astra_registration')
        return dict(registration=reference)
    if record['kind'] == 'REQUEST':
        service.require(payload['split'] == 'TRAIN', 'TRAIN_only_observer')
        included = any(message.get('role') == 'user' and isinstance(message.get('content'), str)
                       and 'Astra: ' + text in message['content'] for message in payload['messages'])
        if registered and included:
            return dict(rendered_request=dict(reference, started_unix=payload['started_unix'],
                                             exact_attributed_text_in_messages=True))
    return {}


def snapshot_service(base):
    lanes = {}
    for lane in (0, 4):
        phases = {}
        for phase in sorted((base / f'lane{lane}').glob('phase_*')):
            try:
                state = mutable_state(phase / 'service/STATE.json')
            except FileNotFoundError:
                phases[phase.name] = dict(initialization_pending=True)
                continue
            results = []
            for path in phase.glob('service/*/BRIDGE_RECEIPT.json'):
                receipt = document(path)
                result_path = Path(receipt['result_path'])
                service.require(result_path.is_relative_to(phase / 'spool'), 'owned_result_path')
                raw = service.read(result_path, 1048576)
                result = service.cpu.read_document(raw)
                results.append(dict(receipt_path=str(path), result_path=str(result_path),
                                    result_sha256=service.sha(raw), status=result['status'],
                                    launch_attempted=result.get('launch_attempted'),
                                    child_generated=result.get('origin', {}).get('child_generated'),
                                    request_id=result.get('request_id'), delivery=receipt.get('delivery')))
            phases[phase.name] = dict(state=state, results=results,
                                     terminal=document(phase / 'TERMINAL.json')
                                     if (phase / 'TERMINAL.json').exists() else None)
        lanes[str(lane)] = phases
    return lanes


def existing_lock_available(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return True
    finally:
        os.close(descriptor)


def campaign_closure(base):
    if not (base / 'FINISHED.json').exists():
        return None
    finished = document(base / 'FINISHED.json')
    activation = document(base / 'ACTIVATION.json')
    intent = document(base / 'HANDOFF_INTENT.json')
    service.require(finished.get('status') == 'WORKERS_EXITED'
                    and finished.get('exit_codes') == [0, 0], 'clean_campaign_exit_required')
    identities = {}
    for pid in [intent['pid']] + activation['pids']:
        path = Path('/proc', str(pid))
        identities[str(pid)] = dict(present=path.exists())
    if any(value['present'] for value in identities.values()):
        return dict(status='TERMINAL_PRESENT_PROCESS_EXIT_PENDING', processes=identities)
    locks = runtime.predecessor()[2] + [service.executor.LOCK_PATH]
    for lane in (0, 4):
        for phase in sorted((base / f'lane{lane}').glob('phase_*')):
            state = document(phase / 'service/STATE.json')
            runtime.campaign.stopped(document(phase / 'TERMINAL.json'), state)
            locks.append(phase / 'service/SERVICE.lock')
    available = {str(path): existing_lock_available(path) for path in locks}
    return dict(status='CLEAN_TERMINAL_PROCESSES_GONE_LOCKS_AVAILABLE' if all(available.values())
                else 'TERMINAL_BUT_LOCK_UNAVAILABLE_NO_ACTION', processes=identities,
                locks_available=available, finished=finished)


def observe(base, output_name='astra_nudge_observation'):
    publication_directory = base / PUBLICATION
    intent = document(publication_directory / 'INTENT_NO_RETRY.json')
    publications = document(publication_directory / 'PUBLISHED.json')
    service.require(output_name in ('astra_nudge_observation', 'astra_nudge_observation_v2'), 'owned_observer_output')
    output = base / output_name
    output.mkdir(mode=0o700, exist_ok=False)
    cursors, configs, evidence = {}, {}, {}
    for lane, publication in publications.items():
        config = document(base / f'lane{lane}/phase_01/CONFIG.json')
        index = publication['before']['next_index']
        _, previous = service.record(config, index - 1)
        cursors[lane] = dict(next_index=index, previous_sha256=previous['sha256'])
        configs[lane] = config
        evidence[lane] = dict(inbox_publication=publication['inbox_publication'])
    try:
        for poll in range(MAX_POLLS):
            children = runtime.prior.child_identities()
            service.require(children == intent['children'], 'same_children_during_observation')
            for lane, cursor in cursors.items():
                for _ in range(16):
                    try:
                        _, record = service.record(configs[lane], cursor['next_index'])
                    except FileNotFoundError:
                        break
                    service.require(record['previous_sha256'] == cursor['previous_sha256'], 'observation_chain')
                    matched = match_record(record, publications[lane]['inbox_publication'], intent['text'],
                                           'registration' in evidence[lane])
                    for key, value in matched.items():
                        evidence[lane].setdefault(key, value)
                    cursor.update(next_index=record['index'] + 1, previous_sha256=record['sha256'])
            closure = campaign_closure(base)
            status = dict(observed_unix=time.time(), poll=poll, children=children,
                          evidence=evidence, cursors=cursors, services=snapshot_service(base),
                          campaign_closure=closure,
                          observer_only_no_publication_or_dispatch=True)
            service.store(output / 'STATUS.json', service.encoded(status), replace=True)
            if (closure and closure['status'] != 'TERMINAL_PRESENT_PROCESS_EXIT_PENDING'
                    or (base / 'FAILED_NO_RETRY.json').exists()):
                break
            if poll + 1 < MAX_POLLS:
                time.sleep(POLL_SECONDS)
        service.store(output / 'FINISHED.json', service.encoded(dict(
            observed_unix=time.time(), status='BOUNDED_OBSERVATION_ENDED', polls=poll + 1)))
    except BaseException as error:
        service.store(output / 'FAILED_NO_RETRY.json', service.encoded(dict(
            observed_unix=time.time(), error_type=type(error).__name__, error=str(error))))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output-name', default='astra_nudge_observation')
    options = parser.parse_args()
    observe(options.base, options.output_name)
