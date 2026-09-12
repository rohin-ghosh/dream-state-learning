import hashlib
import json
from pathlib import Path
import re
import zlib

BASE = Path('/tmp/astra_rawfork_terminal_20260912')
ROOT = BASE / 'astra_P0_raw_wake_fork_seed0_20260912_attempt1'
analysis = json.loads((BASE / 'analysis.json').read_text())
plan = json.loads((ROOT / 'plan.json').read_text())
oracle_path = Path('/tmp/astra_mini_sudoku_terminal_20260912/astra_mini_sudoku_useful_corrupt_20260912_attempt3/material/oracle_sources.json')
oracle = {row['episode_id']: row['q'] for row in json.loads(oracle_path.read_text())['records']}
marker = re.compile(r'^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$', re.MULTILINE)
sha = lambda text: hashlib.sha256(text.encode()).hexdigest()
checks, cells = [], {}
for arm in ('lesson', 'sham'):
    for condition in ('off', 'on'):
        directory = ROOT / f'probes/{arm}/{condition}'
        config = json.loads((directory / 'configuration.json').read_text())
        raw = [json.loads(line) for line in (directory / 'generations.jsonl').read_text().splitlines() if line.strip()]
        requests = [row for row in raw if row.get('kind') == 'generation_request']
        outputs = {row['request_index']: row['outputs'] for row in raw if row.get('kind') == 'generation_output'}
        counts = dict(episodes=0, raw_actions=0, later_actions=0, native_best_solves=0)
        for episode in analysis['pairs'][arm][condition]['episodes']:
            episode_id = episode['episode_id']
            seed = (zlib.crc32(f'{episode_id}/1'.encode()) ^ config['gen_seed']) & 0x7fffffff
            matching = [(request, index) for request in requests for index, value in enumerate(request['seeds']) if value == seed]
            assert len(matching) == 1, (arm, condition, episode_id, 'ambiguous first wake request')
            request, index = matching[0]
            prompt = request['prompts'][index]
            output = outputs[request['request_index']][index]
            goal = prompt.split('=== STATE ===\nGOAL: ', 1)[1]
            head, separator, _ = goal.partition('\nWrite each attempt on one ACT: line;')
            assert separator
            question = head.split('\n', 1)[1]
            ledger = [json.loads(line) for line in (directory / episode['ledger']).read_text().splitlines() if line.strip()]
            actions = [row for row in ledger if row.get('kind') == 'act']
            raw_actions = [match.group(2).strip() for match in marker.finditer(output) if match.group(1) == 'ACT']
            assert [row['action'] for row in actions] == raw_actions, 'raw output/ACT parser mismatch'
            assert len(actions) == episode['metrics']['n_acts']
            assert actions[1:] == episode['later_acts']
            assert (episode['first_act']['record_index'] is None) == (not actions)
            if actions:
                assert ledger[episode['first_act']['record_index']] == actions[0]
            scored = episode['first_act']['status'] == 'measured'
            assert episode['metrics']['first_act_solved'] == int(scored and episode['first_act']['native_score'] == 1)
            assert episode['metrics']['first_act_native_score_zero_filled'] == (episode['first_act']['native_score'] if scored else 0)
            for row in actions:
                receipt = row['generation']
                assert receipt['prompt_sha256'] == sha(prompt) and receipt['output_sha256'] == sha(output)
                assert receipt['seed'] == seed and receipt['max_tokens'] == request['max_tokens'] == 400
            counts['episodes'] += 1
            counts['raw_actions'] += len(actions)
            counts['later_actions'] += max(0, len(actions)-1)
            counts['native_best_solves'] += int(episode['metrics']['native_best'] == 1)
            checks.append(dict(arm=arm, condition=condition, episode_id=episode_id,
                request_index=request['request_index'], prompt_sha256=sha(prompt), output_sha256=sha(output),
                question_hash_matches_plan=sha(question) == plan['bound']['question_audit']['canary_question_sha256'][episode_id],
                birth_prefix_matches=prompt.startswith('=== YOU ===\n' + config['birth_prompt'].strip() + '\n=== STATE ===\n'),
                exact_native_prompt_matches_oracle_reference=prompt == oracle[episode_id],
                clocks=[line for line in prompt.splitlines() if line.startswith('CLOCK:')],
                actual_temperature=request['temperature'], actual_max_tokens=request['max_tokens'],
                raw_act_count=len(actions), first_act_status=episode['first_act']['status']))
        cells[f'{arm}_{condition}'] = dict(**counts, primary=analysis['pairs'][arm][condition]['summary'],
            first_act_status_counts=analysis['pairs'][arm][condition]['first_act_status_counts'],
            solved_ids=[row['episode_id'] for row in analysis['pairs'][arm][condition]['episodes'] if row['metrics']['first_act_solved']])
report = dict(cells=cells, checks=checks, prompt_checks=len(checks),
    question_mismatches=sum(not row['question_hash_matches_plan'] for row in checks),
    birth_prefix_mismatches=sum(not row['birth_prefix_matches'] for row in checks),
    exact_reference_prompt_mismatches=sum(not row['exact_native_prompt_matches_oracle_reference'] for row in checks),
    oracle_reference=str(oracle_path), oracle_reference_sha256=hashlib.sha256(oracle_path.read_bytes()).hexdigest(),
    scope='Raw trace/parser/ledger and planned question/birth bindings; no new native answer scoring or source-formation judgment')
with (BASE / 'raw_endpoint_prompt_review.json').open('x') as target:
    json.dump(report, target, indent=2, sort_keys=True)
    target.write('\n')
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}, indent=2))
