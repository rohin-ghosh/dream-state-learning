"""Read-only actual-token curves; never export generated text or private panels."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

from batch import ARMS, ROOT, complete_source
from epoch import DEADLINE, sha


def count_events(cells):
    totals = {}
    for contest, seed, events in cells:
        state = totals.setdefault(str(seed), dict(generated_tokens=0, act_attempts=0,
            distinct_scored=0, distinct_accepted=0, new_pixels=0, acts_without_scored_strings=0, curve=[]))
        seen = set(state.pop('_seen', []))
        for event in events:
            state['generated_tokens'] += event['actual_generated_tokens']
            is_act = event['origin']['stage'] == 'ACT'
            state['act_attempts'] += int(is_act)
            results = event['score']['results']
            state['acts_without_scored_strings'] += int(is_act and not results)
            for row in results:
                key = (contest, row['caption_sha256'])
                if key in seen or row['result'].get('cached', False):
                    continue
                seen.add(key)
                state['distinct_scored'] += int(row['result'].get('rank') is not None)
                state['distinct_accepted'] += int(row['result'].get('accepted') is True)
                state['new_pixels'] += int(row['result'].get('status') == 'new_pixel')
            state['curve'].append(dict(generated_tokens=state['generated_tokens'], new_pixels=state['new_pixels'],
                distinct_scored=state['distinct_scored'], distinct_accepted=state['distinct_accepted']))
        state['_seen'] = list(seen)
    for state in totals.values():
        state.pop('_seen', None)
    return totals


def process(pid, config):
    try:
        stat = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        argv = Path('/proc', str(pid), 'cmdline').read_bytes().split(b'\0')
        return dict(pid=pid, start_ticks=stat[19], alive=stat[0] not in ('Z', 'X'),
            correct_config=str(config).encode() in argv)
    except FileNotFoundError:
        return dict(pid=pid, alive=False, correct_config=False)


def collect():
    if time.time() >= DEADLINE:
        raise ValueError('receiving_lease_expired_no_access')
    rows = []
    for arm in ARMS:
        root = ROOT / arm
        config = json.loads((root / 'CONFIG.json').read_bytes())
        output = root / 'players' / config['identity']['condition']
        row = dict(arm=arm, source_age=config['identity'].get('absolute_sleep'),
            config_sha256=sha(root / 'CONFIG.json'), source_manifest_sha256=config['source_manifest_sha256'])
        loaded_path = output / 'LOADED.json'
        if not loaded_path.exists():
            row.update(state='LOAD_NOT_OBSERVED', evaluated=False)
            rows.append(row)
            continue
        loaded = json.loads(loaded_path.read_bytes())
        row.update(loaded_unix=loaded['unix'], loaded_sha256=sha(loaded_path),
            process=process(loaded['pid'], root / 'CONFIG.json'),
            judge_epoch_sha256=loaded['judge_epoch_sha256'], identity=loaded['identity'],
            source_optimizer_steps=(loaded.get('source_age') or {}).get('optimizer_steps'),
            parent_tokens=loaded['parent_tokens'], source_parent_text_loaded=loaded['source_parent_text_loaded'])
        cells = []
        complete_cells = 0
        for contest in json.loads((root / 'GAME_MANIFEST.json').read_bytes())['contests']:
            for seed in config['seeds']:
                cell = output / f"{contest['contest_id']}_{seed}"
                result = cell / 'RESULT.json'
                if result.exists():
                    events = json.loads(result.read_bytes())['events']
                    complete_cells += 1
                else:
                    events = [json.loads(path.read_bytes())['event'] for path in sorted(cell.glob('[0-9]*.json'))]
                cells.append((contest['contest_id'], seed, events))
        row.update(per_seed=count_events(cells), complete_cells=complete_cells, evaluated=False,
            state='LOADED_EVALUATION_INCOMPLETE')
        row['actual_generated_tokens'] = sum(item['generated_tokens'] for item in row['per_seed'].values())
        complete_path = output / 'COMPLETE.json'
        if complete_path.exists():
            complete = json.loads(complete_path.read_bytes())
            complete_source(complete, loaded)
            row.update(evaluated=True, state='COMPLETE_FIXED_6144_TOKENS', complete_sha256=sha(complete_path),
                completed_unix=complete['unix'], unchanged_identity=complete['unchanged_identity'])
        rows.append(row)
    return dict(observed_utc=datetime.now(timezone.utc).isoformat(), rows=rows,
        batch=json.loads((ROOT / 'BATCH_STATUS.json').read_bytes()),
        actual_generated_token_axis=True, independent_seed_counts_not_global_unique_ideas=True,
        acceptance_not_humor_validation=True, all_backlog_evaluated=False, source_lives_modified=False)


if __name__ == '__main__':
    print(json.dumps(collect(), sort_keys=True, indent=2))
