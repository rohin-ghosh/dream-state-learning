import hashlib
import json
from pathlib import Path
import sys

root, supplement, out = map(Path, sys.argv[1:])
primary = json.loads((root / 'report.json').read_text())
specificity = json.loads(supplement.read_text())
assert primary['no_update']['exact_scores_equal']
assert primary['cost']['new_fit_steps'] == 12765
states = ['A1_before', 'AN', 'A2']
rows = {}
for state in states:
    old = primary['native_old_summaries'][state]['per_dose']['16']
    new = specificity['states'][state]['means']
    rows[state] = dict(old_n=old['n'], old_fact_gain=old['d_p'],
                       old_frame_gain=old['frame_d_p'], new_n=32,
                       new_frame_gain=new['frame']['probability_gain']['mean'],
                       new_bicycle_gain=new['bicycle']['probability_gain']['mean'],
                       new_paired_gain=new['frame_minus_bicycle']['probability_gain']['mean'],
                       new_bicycle_abstain=new['bicycle']['ON']['p_abstain']['mean'],
                       new_bicycle_mass=new['bicycle']['ON']['raw_colour_mass']['mean'])
cost = primary['cost']
summary = dict(source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in [root / 'report.json', supplement]}, rows=rows,
               reserved_gpu_seconds=cost['run']['reserved_gpu_seconds'],
               fit_loop_seconds=sum(fit['wall_seconds'] for fit in cost['fits'].values()),
               fit_input_passes=sum(fit['tokens'] for fit in cost['fits'].values()),
               fit_supervised_passes=sum(fit['supervised_tokens'] for fit in cost['fits'].values()),
               read_scoring_seconds=sum(read['measured_work']['scoring_seconds'] for read in cost['reads'].values()),
               read_padded_input_positions=sum(read['measured_work']['padded_input_tokens'] for read in cost['reads'].values()),
               candidate_sequences=sum(read['measured_work']['candidate_sequences'] for read in cost['reads'].values()),
               forward_calls=sum(read['measured_work']['forward_calls'] for read in cost['reads'].values()),
               generation_calls=0, no_update=primary['no_update'],
               interpretation='One training seed; fresh-base reconstruction, not OLD-parameter retention; raw colour mass and abstention remain unqualified')
with out.with_suffix('.json').open('x') as target:
    json.dump(summary, target, indent=2, sort_keys=True, allow_nan=False)
headers = ['state', *rows[states[0]]]
with out.with_suffix('.csv').open('x') as target:
    target.write(','.join(headers) + '\n')
    for state, values in rows.items():
        target.write(','.join([state, *[str(values[key]) for key in headers[1:]]]) + '\n')
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="390" viewBox="0 0 960 390">',
       '<rect width="960" height="390" fill="white"/>',
       '<g font-family="sans-serif" fill="#202020">',
       '<text x="32" y="28" font-size="19">Cumulative replay: assay dependence and NEW-cue spill</text>',
       '<text x="32" y="51" font-size="12">Mean ON minus OFF target probability, conditional on four colours; no learner-level error bars</text>']
panels = [('OLD owners (n=16)', 'old_fact_gain', 'old_frame_gain', 'Fact', 'Frame'),
          ('NEW owners (n=32)', 'new_frame_gain', 'new_bicycle_gain', 'Frame', 'Bicycle control')]
colours = ['#356ca5', '#bd5738']
for panel_index, (title, first, second, first_label, second_label) in enumerate(panels):
    left = 50 + 470 * panel_index
    svg.append(f'<text x="{left}" y="80" font-size="15">{title}</text>')
    for value in [0.0, .2, .4, .6, .8]:
        height = 290 - value * 220
        svg.append(f'<line x1="{left}" y1="{height}" x2="{left+380}" y2="{height}" stroke="#ddd"/>')
        svg.append(f'<text x="{left-28}" y="{height+4}" font-size="11">{value:.1f}</text>')
    for state_index, state in enumerate(states):
        center = left + 62 + state_index * 120
        for metric_index, metric in enumerate([first, second]):
            value = rows[state][metric]
            top, height = min(290, 290-value*220), abs(value)*220
            position = center - 35 + metric_index * 34
            svg.append(f'<rect x="{position}" y="{top}" width="28" height="{height}" fill="{colours[metric_index]}"/>')
            svg.append(f'<text x="{position+14}" y="{top-5}" text-anchor="middle" font-size="10">{value:.3f}</text>')
        label = {'A1_before': 'OLD only', 'AN': 'NEW only', 'A2': 'OLD + NEW'}[state]
        svg.append(f'<text x="{center}" y="315" text-anchor="middle" font-size="12">{label}</text>')
    for index, label in enumerate([first_label, second_label]):
        position = left + index * 150
        svg.append(f'<rect x="{position}" y="335" width="12" height="12" fill="{colours[index]}"/>')
        svg.append(f'<text x="{position+18}" y="346" font-size="12">{label}</text>')
svg.extend(['<text x="32" y="376" font-size="12">Fresh-base fits, one training seed; not warm-start retention, selective memory, or parenting.</text>', '</g></svg>'])
with out.with_suffix('.svg').open('x') as target:
    target.write('\n'.join(svg) + '\n')
print(json.dumps({key: value for key, value in summary.items() if key != 'source_sha256'}, sort_keys=True))
