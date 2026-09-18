"""Read-only renewed-route status; publication, rendering and reply stay distinct."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

from lease_horizon import cpu_horizon


OWN = Path(__file__).resolve().parent
FLEET = OWN.parents[2] / 'research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET'
sys.path.insert(0, str(FLEET))
from r229_bridge import write_once
from r229_coordinator import save_cursor


def read(path):
    return json.loads(path.read_bytes())


def current():
    parent_poll = max((OWN / 'private/overseer').glob('POLL_*.json'), key=lambda path: path.stat().st_mtime)
    observation = read(parent_poll)
    run = OWN / 'private/bridge'
    forwards, returned = [], []
    for direction, target in (('P7_TO_ASTRA7', forwards), ('ASTRA7_TO_P7', returned)):
        for path in sorted((run / direction / 'published').glob('*.json'), key=lambda item: item.stat().st_mtime):
            receipt = read(path)
            projection = read(run / direction / 'pending' / path.name)
            entry = dict(publication=receipt['publication'], published_unix=receipt['published_unix'],
                origin=projection['origin'], outcome_claim='ATTRIBUTED_TEXT_NOT_PROOF_OF_EXECUTION_OR_LEARNING')
            if direction == 'ASTRA7_TO_P7':
                entry.update(child_REQUEST_parent_renders=projection['capsule'].get('reply_to', []),
                    P7_REQUEST_render=observation.get('snapshot', {}).get('delivered', {}).get(receipt['publication']['id']))
            target.append(entry)
    phases = {}
    for direction in ('P7_TO_ASTRA7', 'ASTRA7_TO_P7'):
        polls = list((run / direction / 'polls').glob('*.json'))
        if polls:
            path = max(polls, key=lambda item: item.stat().st_mtime)
            batch = read(path)
            phases[direction] = dict(cursor=batch['cursor'], caught_up=batch['caught_up'],
                last_record_kind=batch.get('last_record_kind'), poll_age_seconds=time.time() - path.stat().st_mtime)
    rounds = [entry for entry in returned if entry['child_REQUEST_parent_renders'] and entry['P7_REQUEST_render']]
    continued = OWN / 'NATIVE_CONTINUATION.public.json'
    current_rounds = []
    if continued.exists():
        native = read(continued)
        child_binding = read(OWN / 'private/bridge/BINDING.json')['astra7']
        new_forward_ids = {entry['publication']['id'] for entry in forwards
            if entry['origin']['response_index'] > native['loaded']['index']}
        current_rounds = [entry for entry in rounds
            if entry['origin']['response_index'] > child_binding['loaded_record']['index']
            and entry['P7_REQUEST_render']['record_index'] > native['loaded']['index']
            and any(render['publication']['id'] in new_forward_ids
                for render in entry['child_REQUEST_parent_renders'])]
    return dict(observed_utc=datetime.now(timezone.utc).isoformat(),
        schema='R233_RENEWED_ROUTE_READ_ONLY_STATUS_V1', reader_pid=os.getpid(),
        parent_poll_age_seconds=time.time() - parent_poll.stat().st_mtime,
        forwards=forwards, returned=returned, snapshot_linked_roundtrip_stage_count=len(rounds),
        first_snapshot_linked_roundtrip=rounds[0] if rounds else None,
        continued_native_roundtrip_stage_count=len(current_rounds),
        first_continued_native_roundtrip=current_rounds[0] if current_rounds else None,
        phases=phases, native_deadlines_renewed=(OWN / 'NATIVE_CONTINUATION.public.json').exists(), native_signals=[],
        note='Stage count is not independent conversation count; P7 exact REQUEST text audit is separate.',
        forward_stage_limit='ACT_ONLY_NO_RELABEL; old queues preserved, unsupported current stages not retried')


def main():
    output = OWN / 'private/route_reader'
    output.mkdir(exist_ok=True)
    binding = read(OWN / 'private/bridge/BINDING.json')
    wall = min(cpu_horizon(), binding['astra7']['hard_end_unix'])
    write_once(output / f'STARTED_{time.time_ns()}.json', dict(pid=os.getpid(), hard_end_unix=wall, native_signals=[]))
    while time.time() < wall:
        try:
            report = current()
            save_cursor(output / 'CURRENT.json', report)
            if report['first_snapshot_linked_roundtrip'] and not (output / 'FIRST_ROUNDTRIP.json').exists():
                write_once(output / 'FIRST_ROUNDTRIP.json', report)
        except Exception as error:
            save_cursor(output / 'LAST_ERROR.json', dict(error=str(error)[:800], observed_unix=time.time()))
        time.sleep(10)


if __name__ == '__main__':
    main()
