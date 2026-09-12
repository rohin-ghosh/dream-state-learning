import collections
import hashlib
import json
from pathlib import Path

from organism_v6.mini_sudoku_behavior_material import board_from_text, validate_solution

report_path = Path('/tmp/astra_correction_utility_analysis_20260912_main.json')
report = json.loads(report_path.read_bytes())
panel = json.loads(Path('/tmp/astra_correction_utility_panel_20260912.json').read_bytes())
questions = {row['episode_id']: row['question'] for row in panel['questions']}
cells = {}
for name, cell in report['cells'].items():
    observations = []
    for episode in cell['on']['episodes']:
        valid = False
        try:
            puzzle = board_from_text(questions[episode['episode_id']], question=True)
            board = board_from_text(episode['first_action'])
            validate_solution(puzzle, board)
            valid = True
        except (ValueError, RuntimeError):
            pass
        if valid != bool(episode['first_act_accepted']):
            raise ValueError('public constraint/native acceptance mismatch: ' + name + '/' + episode['episode_id'])
        observations.append(dict(episode_id=episode['episode_id'], public_constraints_pass=valid,
            native_accepted=episode['first_act_accepted']))
    counts = collections.Counter(episode['first_action'] for episode in cell['on']['episodes'])
    cells[name] = dict(n=len(observations), accepted=sum(row['public_constraints_pass'] for row in observations),
        distinct_first_actions=len(counts), dominant_first_action_count=counts.most_common(1)[0][1],
        most_common_first_actions=counts.most_common(3), observations=observations)
print(json.dumps(dict(status='PUBLIC_CONSTRAINTS_MATCH_ALL_192_ON_FIRST_ACTIONS',
    analysis_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
    question_source='fixed panel, no reference answers', cells=cells), indent=2, sort_keys=True))
