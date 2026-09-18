"""Actual new-fork launch and peer receipts; old cap-exit roots are read-only."""

from datetime import datetime, timezone
import json

import r213_receipts as evidence
from r209_filter_resume import ROOT, read, require, sha, write
from r209_node3_audit import metadata, read_record
from r213_fork_policy import ASSIGNMENTS, FORKS, GROUPS


def main():
    observed = datetime.now(timezone.utc)
    rows = {}
    for name in ASSIGNMENTS:
        arm = ROOT / name
        if not (arm / 'r213_parent/PHASE_START.json').exists():
            rows[name] = dict(assignment=ASSIGNMENTS[name], status='DISPATCHED_NOT_YET_PARENT_PHASE',
                current_native=False, dispatch=read(arm / 'DISPATCHED.json'))
            continue
        evidence.ASSIGNMENTS = ASSIGNMENTS
        row = evidence.collect(name)
        if name in FORKS:
            lineage = read(arm / 'LINEAGE.json')
            loaded = row['loaded']
            require(loaded['optimizer_steps'] == 4908
                and loaded['adapter_sha256'] == '82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92'
                and loaded['base_sha256'] == 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992',
                'actual_loaded_C2_51_base_adapter_optimizer')
            require(lineage['named_peers'] == list(GROUPS[name]) and lineage['operator_budget_seconds'] == 21600
                and row['presentations'] == 16 and row['plasticity'] is None, 'six_hour_baseline_named_new_group')
            row['lineage'] = lineage
            row['cpu'] = read(arm / 'CPU.json')
            row['cpu_log'] = (arm / 'CPU.log').read_text()
            row['new_receiver_members'] = GROUPS[name]
            for peer in row['peer_receipts']:
                require(peer['sender'] in GROUPS[name] and peer['receiver'] == name
                    and peer['actual_THINK_render_verified'] and peer['imported_training_rows'] == 0,
                    'actual_same_group_masked_THINK_receipt')
        else:
            row['legacy_receiver_limit'] = ('NO_NATIVE_PEER_RECEIVER' if name == 'conversational'
                else 'OLD_MATH_B_PATH_NOT_NEW_FORK_ID_NO_REBINDING')
        rows[name] = row
    previous = read(ROOT / 'R213_PHASE_RECEIPTS_20260918T055839Z.json')
    ended = {}
    for name in ('peer_math', 'peer_repo', 'p32', 'lr03', 'lr3'):
        arm = ROOT / name
        paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        prior = previous['arms'][name]
        require(int(paths[-1].stem) == prior['journal_tail'][-1]['index'], 'ended_raw_head_not_advanced')
        complete = prior['latest_complete_file']
        require(sha(complete['path']) == complete['file_sha256'], 'ended_COMPLETE_unchanged')
        latest = read_record(paths[-1])
        ended[name] = dict(status='ENDED_FAILED_CAP_RUN_NOT_PAUSED_NOT_CONTINUED',
            last_index=latest['index'], last_kind=metadata(paths[-1]), head_sha256=latest['sha256'],
            last_complete=complete, outer_exit=read(arm / 'r210_enrichment/control/OUTER_EXIT.json'),
            raw_head_not_advanced=True, last_complete_unchanged=True)
    receipt = dict(observed_utc=observed.isoformat(), arms=rows, ended_preserved_runs=ended,
        current_native_count=sum(row['current_native'] for row in rows.values()),
        data_classification='OPERATIONAL_PROVENANCE_NOT_PRIVATE_EVALUATION',
        no_child_signals=True, new_forks_not_recovered_continuations=True)
    path = ROOT / ('R213_NEW_FORKS_' + observed.strftime('%Y%m%dT%H%M%SZ') + '.json')
    write(path, receipt)
    print(json.dumps(dict(receipt_path=str(path), observed_utc=receipt['observed_utc'],
        current_native_count=receipt['current_native_count'], arms={name: dict(
            physical=row['assignment'][0], current=row['current_native'],
            loaded_index=row.get('loaded', {}).get('index'), pid=row.get('loaded', {}).get('pid'),
            loaded_unix=row.get('loaded', {}).get('loaded_unix'), wall=row.get('hard_end_unix'),
            parent_requests=[item['request_index'] for item in row.get('parent_renders', [])],
            peers=[dict(index=item['index'], sender=item['sender'], THINK=item['actual_THINK_render_verified'])
                for item in row.get('peer_receipts', [])],
            CPU_tail=row.get('cpu_log', '').splitlines()[-4:]) for name, row in rows.items()})))


if __name__ == '__main__':
    main()
