"""Bounded current-incarnation NODE2 read; no model calls or learner controls."""

import json
import os
from pathlib import Path
import time

import enrich


def collect():
    output = dict(observed_unix=time.time(), host=os.uname().nodename, arms={})
    for arm in enrich.ARMS:
        bound, root = enrich.identity(arm)
        rows = enrich.recent(root, 1200)
        loaded = next(enrich.verified(path) for path, meta in reversed(rows) if meta['kind'] == 'LOADED')
        if loaded['document']['pid'] != bound['native']['pid']:
            raise ValueError('actual_current_LOADED_required')
        rows = [(path, meta) for path, meta in rows if meta['index'] >= loaded['index']]
        entry = dict(native=bound['native'], current_control=bound['current_control'], loaded=loaded,
                     head=rows[-1][1], parents=enrich.verify(arm)['publications'], records={})
        for kind in ('RESPONSE', 'REQUEST', 'R184_ACT', 'COMPACTION', 'TARGET_ELIGIBILITY',
                     'R195_PROSE_TARGET_REVIEW', 'SLEEP_COMPLETE', 'R184_LEARN_COMPLETE'):
            path = next((path for path, meta in reversed(rows) if meta['kind'] == kind), None)
            if path is None:
                continue
            record = enrich.verified(path)
            if kind in ('REQUEST', 'SLEEP_COMPLETE', 'R184_LEARN_COMPLETE'):
                document = record['document']
                record = dict(index=record['index'], sha256=record['sha256'], document={
                    key: document.get(key) for key in ('started_unix', 'finished_unix', 'segment',
                                                      'prompt_tokens', 'render_receipt', 'cycle')})
            entry['records'][kind] = record
        act = entry['records'].get('R184_ACT')
        if act is not None:
            segment = act['document']['segment']
            request = next((enrich.verified(path) for path, meta in reversed(rows)
                            if meta['kind'] == 'REQUEST' and enrich.read(path)['document']['segment'] == segment), None)
            if request is not None:
                response_path = root / 'raw/stream/records' / '{:020d}.json'.format(request['index'] + 1)
                response = enrich.verified(response_path)
                if response['kind'] != 'RESPONSE' or response['previous_sha256'] != request['sha256']:
                    raise ValueError('actual_ACT_response_chain')
                entry['actual_act_response'] = response
        plan = enrich.read(Path(bound['current_control']) / 'PLAN.json')
        entry['filter_policy'] = plan.get('think_act_learn', {}).get('prose_target_filter')
        entry['current_filter_source_sha256'] = enrich.file_sha(
            Path(bound['source_root']) / 'organism_v6/orch_r203_prose_target_filter.py')
        entry['pause_files_present'] = [str(path) for path in (
            root / 'PAUSED.json', root / 'raw/PAUSED.json', Path(bound['current_control']) / 'PAUSED.json') if path.exists()]
        staging = root / 'r210_filter_saved_boundary_20260918_v3'
        entry['filter_receipts'] = {name: enrich.read(staging / name) for name in (
            'HANDOFF_FAILED.json', 'DISPATCHED.json', 'RETIRED_EXACT.json') if (staging / name).exists()}
        output['arms'][arm] = entry
    return output


if __name__ == '__main__':
    print(json.dumps(collect()))
