"""Render independent-seed token curves without merging scoring epochs."""

import html
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
COLORS = dict(base='#334155', learner24='#2563eb', frozen24='#d97706',
    c2sleep51='#15803d', c2sleep117='#dc2626')


def render(document):
    epochs = {row['judge_epoch_sha256'] for row in document['rows'] if row.get('judge_epoch_sha256')}
    if len(epochs) > 1:
        raise ValueError('one_adopted_epoch_per_comparison')
    lines = ['# Adopted-judge age block', '', 'Observed: ' + document['observed_utc'], '',
        'Parent-free, all parameters frozen, three DEVELOPMENT scenes, two independent seeds.',
        'Fixed budget:3072 actual generated tokens per seed;6144 per source.',
        document.get('source_description', 'Source age24 is not current age.'), '',
        '| Source | Seed | State | Actual tokens | Distinct scored strings | Accepted | New pixels | ACTs without scored strings | Source optimizer steps |',
        '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in document['rows']:
        if not row.get('per_seed'):
            lines.append(f'| {row["arm"]} | — | {row["state"]} | unknown | unknown | unknown | unknown | unknown | unknown |')
        for seed, counts in sorted(row.get('per_seed', {}).items()):
            steps = row.get('source_optimizer_steps')
            source_steps = str(steps) if steps is not None else 'not applicable' if row['arm'] == 'base' else 'unknown'
            lines.append(f'| {row["arm"]} | {seed} | {row["state"]} | {counts["generated_tokens"]} | '
                f'{counts["distinct_scored"]} | {counts["distinct_accepted"]} | {counts["new_pixels"]} | '
                f'{counts["acts_without_scored_strings"]} | {source_steps} |')
    lines.extend(['', 'Judge epoch: `' + next(iter(epochs), 'LOAD not observed') + '`.', '',
        'Scored/accepted strings and operational embedding pixels are not certified jokes or globally unique ideas.',
        'Seeds remain separate; partial rows are not compared as equal-budget completed results.',
        'ACTs without scored strings are not necessarily format errors; optimizer steps are not training FLOPs.',
        'No parent/life receives these results or private reference captions. No source learning occurred in a probe.',
        'The1146+ every-sleep enrollment backlog is not claimed evaluated by this three-source block.',
        'The first operator-protocol failure and its repair are preserved in FAILURE_REPAIR.md.', '',
        'Current chain audit: learner level0, frozen sibling level1 in their independently pinned later windows;',
        'no level2/3 chain shown there. See ../post_recovery_pair_evidence_20260918/REPORT.md.',
        'P3 post-recovery movement:0 substantive captions/1536 ACT tokens in the inspected three ACTs;',
        'feedback rendered, no successful next-ACT correction. See ../post_recovery_p3_movement_20260918/STATUS_LATEST.md.'])
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="790" viewBox="0 0 920 790">',
        '<rect width="920" height="790" fill="white"/>',
        '<g font-family="sans-serif" fill="#0f172a">',
        '<text x="60" y="28" font-size="19">Parent-free adopted-judge exploration — separate seeds</text>',
        '<text x="60" y="51" font-size="12">' + html.escape(document['observed_utc']) + '</text>']
    for metric, label, baseline in (('distinct_accepted', 'Distinct accepted strings', 330),
            ('new_pixels', 'New embedding pixels', 660)):
        maximum = max([10] + [point[metric] for row in document['rows']
            for counts in row.get('per_seed', {}).values() for point in counts['curve']])
        ceiling = ((maximum + 4) // 5) * 5
        svg.append(f'<text x="60" y="{baseline-250}" font-size="14">{label}</text>')
        for value in range(0, ceiling + 1, 5):
            vertical = baseline - value * 230 / ceiling
            svg += [f'<line x1="60" x2="730" y1="{vertical}" y2="{vertical}" stroke="#e2e8f0"/>',
                f'<text x="25" y="{vertical+4}" font-size="12">{value}</text>']
        for value in (0, 1024, 2048, 3072):
            horizontal = 60 + value * 670 / 3072
            svg.append(f'<text x="{horizontal-12}" y="{baseline+25}" font-size="12">{value}</text>')
        for row in document['rows']:
            for seed, counts in sorted(row.get('per_seed', {}).items()):
                color = COLORS[row['arm']]
                points = [(0, 0)] + [(point['generated_tokens'], point[metric]) for point in counts['curve']]
                coordinates = ' '.join(f'{60+tokens*670/3072:.1f},{baseline-total*230/ceiling:.1f}'
                    for tokens, total in points)
                dash = '' if seed == '23201' else 'stroke-dasharray="6 4"'
                svg.append(f'<polyline data-metric="{metric}" points="{coordinates}" fill="none" '
                    f'stroke="{color}" stroke-width="2" {dash}/>')
    legend = 90
    for row in document['rows']:
        for seed, counts in sorted(row.get('per_seed', {}).items()):
            color = COLORS[row['arm']]
            svg.append(f'<text x="748" y="{legend}" font-size="12" fill="{color}">{row["arm"]} / {seed}</text>')
            legend += 22
    svg += ['<text x="220" y="715" font-size="13">Actual generated tokens per independent seed</text>',
        '<text x="60" y="740" font-size="12">Acceptance ≠ validated humor. Pixels ≠ globally unique ideas. Partial curves are unfinished.</text>',
        '<text x="60" y="765" font-size="12">No causal learning or every-sleep coverage claim.</text>', '</g></svg>']
    return '\n'.join(lines) + '\n', '\n'.join(svg) + '\n'


if __name__ == '__main__':
    markdown, svg = render(json.loads((HERE / 'AGE_BLOCK_CURRENT.json').read_bytes()))
    (HERE / 'STATUS.md').write_text(markdown)
    (HERE / 'TOKEN_CURVES.svg').write_text(svg)
