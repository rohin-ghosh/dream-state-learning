"""Append TRAIN-only per-cycle node5 exchange summaries, without live patching."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import time


ROOTS = {index: f'/localhome/local-rohing/orch_r108_code_parent_node5_{index}_20260915_attempt2' for index in (4, 5)}
END = 1789491720


def snapshot(root, index):
    if index not in ROOTS or str(root) != ROOTS[index]:
        raise ValueError('only_owned_node5_4_5')
    lane = root / 'campaign_code_parent'
    rows = []
    for cycle_path in sorted(lane.glob('CYCLE_*_COMPLETE.json')):
        cycle = int(cycle_path.name.split('_')[1])
        cells = [json.loads(path.read_text()) for path in (lane / 'cells').glob('*.json')]
        parents = [row for row in cells if row['cycle'] == cycle and row['kind'] == 'PARENT']
        triples = [json.loads(path.read_text()) for path in lane.glob(f'TRIPLE_C{cycle:03d}_*.json')]
        train_triples = [row for row in triples if row.get('episode_index') in (1, 2)]
        operations = Counter(row.get('declared_behavior_operation', 'UNCLASSIFIED') for row in parents)
        accepted = sum(row['status'] == 'COMPLETE' for row in parents)
        missing = sum(row['status'] in ('FAILED', 'MISSING') for row in parents)
        rows.append(dict(index=index, cycle=cycle, source_root=str(root),
            ready_sha256=hashlib.sha256((root / 'READY.json').read_bytes()).hexdigest(),
            cycle_receipt_sha256=hashlib.sha256(cycle_path.read_bytes()).hexdigest(),
            parent_turns_recorded=len(parents), accepted_parent_turns=accepted,
            unusable_parent_turns=missing, declared_operations=dict(operations),
            actual_train_triples=len(train_triples),
            changed_train_continuation_texts=sum(row.get('continuation_changed') is True for row in train_triples),
            semantic_behavior_change='UNREVIEWED', includes_held_outcomes=False,
            raw_in_repository=False, raw_pointer=str(root / 'parent_transcripts' / 'campaign_code_parent')))
    return dict(index=index, observed_unix=time.time(), cycles=rows,
        terminal=(lane / 'TERMINAL.json').exists())


def append_exchange(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open('a+', encoding='utf-8') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        stream.seek(0)
        existing = stream.read()
        for row in rows:
            if row['index'] not in ROOTS or row['includes_held_outcomes'] or row['raw_in_repository']:
                raise ValueError('owned_train_only_exchange')
            identifier = f'R110_CODE_NODE5_{row["index"]}_C{row["cycle"]:03d}'
            marker = '<!-- ' + identifier + ' -->'
            if marker in existing:
                continue
            payload_sha = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            operations = json.dumps(row['declared_operations'], sort_keys=True)
            entry = (f'\n{marker}\n### {datetime.now(timezone.utc).isoformat()} — node5/{row["index"]} CODE cycle {row["cycle"]}\n'
                f'- Parent did: {row["parent_turns_recorded"]} scheduled turns recorded; '
                f'{row["accepted_parent_turns"]} accepted structured plans, {row["unusable_parent_turns"]} unusable/missing. '
                f'Declared operations only (not semantic audit): {operations}.\n'
                f'- Child changed: text changed in {row["changed_train_continuation_texts"]}/{row["actual_train_triples"]} '
                'paired TRAIN continuations; semantic behavior/benefit UNREVIEWED. Missing interventions are not counted as parent triples.\n'
                f'- Pointer for other half: `{row["raw_pointer"]}`; native root `{row["source_root"]}`; '
                f'READY `{row["ready_sha256"]}`, cycle receipt `{row["cycle_receipt_sha256"]}`. Raw stays node-local.\n'
                '- Request/disagreement: compare actual mid-solution departures/returns and effort allocation, not headings or length; '
                'no success claim from changed wording. Share questions/observations, not answers or held scores.\n'
                f'- TRAIN-only metadata snapshot `{payload_sha}`. No optimizer/weight update; exchange publication is not proof any live parent consumed it.\n')
            stream.write(entry)
            existing += entry
            count += 1
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return count


def serve(repository, receipts):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('cpu_only_sidecar')
    receipts.mkdir(parents=True, exist_ok=True)
    script = ('import json,hashlib,time\nfrom pathlib import Path\nfrom collections import Counter\n'
        + 'ROOTS=' + repr(ROOTS) + '\n' + inspect.getsource(snapshot)
        + '\nprint(json.dumps([snapshot(Path(root),index) for index,root in ROOTS.items()],sort_keys=True))\n')
    sequence = 0
    while time.time() < END:
        result = subprocess.run(['bash', str(repository / 'gpu' / 'ovx3_ssh.sh'),
            "python3 -B - <<'R110_EXCHANGE'\n" + script + '\nR110_EXCHANGE'],
            capture_output=True, text=True, timeout=60)
        sequence += 1
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            rows = [row for item in payload for row in item['cycles']]
            added = append_exchange(repository / 'research_loop' / 'PARENTING_EXCHANGE.md', rows)
            receipt = dict(observed_unix=time.time(), snapshots=payload, newly_appended=added, no_model_calls=True)
            encoded = json.dumps(receipt, indent=2, sort_keys=True) + '\n'
            (receipts / 'LATEST.json').write_text(encoded)
            if added:
                (receipts / f'APPENDED_{sequence:05d}.json').write_text(encoded)
            if all(item['terminal'] for item in payload):
                break
        else:
            (receipts / f'ERROR_{sequence:05d}.json').write_text(json.dumps(dict(observed_unix=time.time(),
                returncode=result.returncode, raw_stderr_omitted=True, no_model_calls=True)) + '\n')
        time.sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    arguments = parser.parse_args()
    serve(arguments.repository, arguments.receipts)
