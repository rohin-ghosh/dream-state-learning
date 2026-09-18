"""Bounded public projection; raw child text and operational paths stay private."""

import argparse
import json
from pathlib import Path

from classroom import load_helpers, MEMBERS, utc
from retirement import PROTECTED, census, identity, is_native, public_identity, record, save, sha


def process(pid):
    try:
        current = identity(pid)
        return dict(**public_identity(current), alive=current['state'] not in ('Z', 'X'))
    except (FileNotFoundError, ProcessLookupError):
        return dict(pid=pid, alive=False)


def project(root, config, operator):
    helper, bound = load_helpers(root, config)
    rows = []
    current = census(root)
    live = operator / 'live'
    heartbeat = json.loads((live / 'HEARTBEAT.json').read_bytes())
    attachment_path = live / 'attachments' / (str(heartbeat['pid']) + '.json')
    if not attachment_path.exists():
        attachment_path = live / 'STARTED.json'
    attachment = json.loads(attachment_path.read_bytes())
    if attachment['pid'] != heartbeat['pid']:
        raise ValueError('current CPU heartbeat must bind its actual startup receipt')
    for name, gpu in PROTECTED.items():
        native = [item for item in current if item['lives'] == [name] and is_native(item)]
        binding = bound.get(name)
        if binding is None:
            active = json.loads((root / name / 'ACTIVE_RUNTIME.json').read_bytes())
            control = Path(active['control'])
            loaded = next(record(path) for path, kind in reversed(list(helper.records(root, name))) if kind == 'LOADED')
            plan = json.loads((control / 'PLAN.json').read_bytes())
            binding = dict(loaded=dict(index=loaded['index'], sha256=loaded['sha256']),
                native_pid=loaded['document']['pid'], control=str(control), deadline=plan['hard_end_unix'])
        plan = json.loads((Path(binding['control']) / 'PLAN.json').read_bytes())
        loaded_record = record(root / name / 'raw/stream/records' / f"{binding['loaded']['index']:020d}.json")
        recent = list(helper.records(root, name))
        latest_response = next(record(path) for path, kind in reversed(recent) if kind == 'RESPONSE')
        latest_sleep = next(record(path) for path, kind in reversed(recent) if kind == 'SLEEP_COMPLETE')
        publications = []
        for directory in sorted((live / name).glob('turn_*')):
            if not (directory / 'PUBLISHED.json').exists():
                continue
            prepared = json.loads((directory / 'PREPARED.json').read_bytes())
            published = json.loads((directory / 'PUBLISHED.json').read_bytes())
            if published['prepared_sha256'] != sha(directory / 'PREPARED.json') or sha(Path(published['path'])) != published['sha256']:
                raise ValueError('parent publication must still match exact source')
            publications.append(dict(id=published['id'], sha256=published['sha256'], stage=prepared['stage'],
                published_utc=published['published_utc'], delivery=helper.actual_delivery(root, name, published, prepared['floor'])))
        astra_count = sum(json.loads(path.read_bytes()).get('speaker') == 'Astra'
            for path in (root / name / 'raw/stream/inbox').glob('*.json'))
        rows.append(dict(life=name, gpu=gpu, native=public_identity(native[0]) if len(native) == 1 else None,
            native_alive=len(native) == 1, LOADED=binding['loaded'],
            LOADED_observed_unix=loaded_record['document'].get('loaded_unix', loaded_record['document'].get('created_unix')),
            latest_RESPONSE=dict(index=latest_response['index'], sha256=latest_response['sha256']),
            latest_COMPLETE=dict(index=latest_sleep['index'], sha256=latest_sleep['sha256'],
                checkpoint_sha256=latest_sleep['document']['checkpoint_sha256'],
                optimizer_steps=latest_sleep['document']['optimizer_steps']),
            all_astra_inbox_count=astra_count, R233_parent_publications=publications,
            policy=dict(plan_key=plan.get('learn_row_policy'), think_key=plan['think_act_learn'].get('learn_row_policy'),
                selectors={key: value for key, value in plan['think_act_learn'].items()
                    if 'filter' in key or 'review' in key}, no_policy_adoption_performed=True),
            deadline_unix=binding['deadline']))
    debate_output = root / 'r231_math_parent_live_v2'
    results = sorted(debate_output.glob('phase_*/exchange_*/RESULT.json'))
    summaries = []
    for path in results:
        result = json.loads(path.read_bytes())
        edges = result.get('peer_renders', [])
        for edge in edges:
            for field in ('receipt', 'request'):
                actual = record(root / edge['receiver'] / 'raw/stream/records' / f"{edge[field]['index']:020d}.json")
                if actual['sha256'] != edge[field]['sha256']:
                    raise ValueError('peer rendered source hash changed')
            if edge['actual_stage'] != 'THINK' or not edge['all_history_tokens_masked'] or not edge['source_bound']:
                raise ValueError('real masked THINK peer delivery required')
        summaries.append(dict(relative=str(path.relative_to(root)), sha256=sha(path),
            status=result['resolution']['status'], edges=edges,
            child_replies={name: dict(response=reply['response'], act=reply['act']) for name, reply in result['replies'].items()},
            checked_conclusion_training_not_established=True))
    historical = []
    old_paths = list((root / 'r225_siege_retirement_20260918').glob('*/IDENTITY.json'))
    old_paths.append(root / 'r224_challenger_retirement_20260918/IDENTITY.json')
    for path in old_paths:
        if path.exists():
            item = json.loads(path.read_bytes())
            historical.append(dict(life=path.parent.name if path.parent.name.startswith('r213_') else 'r213_siege_challenger_fork',
                pid=item['native_pid'], start_ticks=item['start_ticks'], identity_receipt_sha256=sha(path),
                source_relative=str(path.relative_to(root))))
    return dict(observed_utc=utc(), node='node3', lives=rows,
        parent_controller=process(heartbeat['pid']), parent_heartbeat_utc=heartbeat['observed_utc'],
        parent_loaded_source_sha256=attachment['code_sha256'],
        parent_startup_receipt_sha256=sha(attachment_path),
        shared_curriculum_round=heartbeat['shared_round'],
        CPU_handoff=json.loads((operator / 'ATTACHED.json').read_bytes()),
        previous_CPU_exit=json.loads((operator / 'CPU_WRITER_RETIRED.json').read_bytes()),
        CPU_handoff_history=[dict(relative=str(directory.relative_to(root)),
            attached=json.loads((directory / 'ATTACHED.json').read_bytes()),
            previous_exit=json.loads((directory / 'CPU_WRITER_RETIRED.json').read_bytes()))
            for directory in sorted(root.glob('r233_classroom_handoff_v*')) if (directory / 'ATTACHED.json').exists()],
        existing_debate=process(1800405), existing_tool_feedback=process(1790808),
        debate_heartbeat=json.loads((debate_output / 'HEARTBEAT.json').read_bytes()),
        latest_completed_debate=summaries[-1] if summaries else None,
        latest_proven_six_edge_exchange=next((summary for summary in reversed(summaries) if len(summary['edges']) == 6), None),
        historical_siege_start_ticks=historical, node4_admitted=False,
        native_signals=0, native_restarts=0, learning_policy_changes=0,
        no_new_native_launch=True, no_new_tool_feedback_claim=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--operator', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    value = project(options.root, json.loads(options.config.read_bytes()), options.operator)
    save(options.output, value)
    print(json.dumps(dict(observed_utc=value['observed_utc'], native_alive=sum(row['native_alive'] for row in value['lives']),
        parent_publications=sum(len(row['R233_parent_publications']) for row in value['lives']),
        actual_R233_renders=sum(bool(item['delivery']['REQUEST']) for row in value['lives'] for item in row['R233_parent_publications']),
        receipt_sha256=sha(options.output))))
