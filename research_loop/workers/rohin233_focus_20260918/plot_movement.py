"""Plot actual fixed-token probes; do not connect separate lineages as ages."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import types
import xml.etree.ElementTree as xml


HERE = Path(__file__).resolve().parent
WORKERS = HERE.parent
STYLES = {
    'source51': ('C2 sleep 51', '#2868b2', ''),
    'currentC2': ('C2 sleep 87', '#c45123', '7 4'),
    'base': ('Frozen base', '#46555c', '3 3'),
    'C0': ('C0 sleep 84', '#7d4396', '9 3'),
    'fresh_s1': ('Fresh birth sleep 1', '#228369', '2 3'),
}
specification = importlib.util.spec_from_file_location('r233_original_plot',
    WORKERS / 'rohin232_coordination_20260918/plot_age_probe.py')
original = importlib.util.module_from_spec(specification)
specification.loader.exec_module(original)
checked_curves = types.FunctionType(original.checked_curves.__code__,
    dict(original.checked_curves.__globals__, STYLES=STYLES))


def combine(primary, c0, fresh):
    for other in (c0, fresh):
        for name in ('panel_sha256', 'rule_sha256'):
            if other['judge'][name] != primary['judge'][name]:
                raise ValueError('same_judge_and_private_panel_required')
        for name in ('scenes_sha256', 'selected_contests'):
            if other['freshness'][name] != primary['freshness'][name]:
                raise ValueError('same_fresh_development_battery_required')
        if other['freshness']['eligible'] is not True:
            raise ValueError('exposure_eligibility_required')
    for name in ('scenes', 'per_scene_seed_budget', 'seeds'):
        if c0[name] != primary[name]:
            raise ValueError('same_budget_and_seeds_required')
    if (fresh['status'] != 'COMPLETE' or fresh['optimizer_updates'] != 0
        or fresh['parent_tokens'] != 0 or fresh['source_context_used'] is not False
        or fresh['whole_generation_tokens_charged_before_credit'] is not True
        or sum(fresh['actual_tokens_by_stage'].values()) != fresh['generated_tokens']):
        raise ValueError('complete_frozen_parent_free_evaluation_required')
    condition = dict(condition='fresh_s1', generated_tokens=fresh['generated_tokens'],
        probe_optimizer_updates=0, new_pixel_events=fresh['new_pixel_events'],
        accepted_new_scores=fresh['accepted_new_scores'], seed_curves={})
    for seed, curve in fresh['seed_curves'].items():
        normalized = []
        prior_tokens, prior_pixels = 0, 0
        for row in curve:
            tokens = row['cumulative_generated_tokens']
            pixels = row['cumulative_new_pixel_events']
            normalized.append(dict(cumulative_generated_tokens=tokens,
                cumulative_new_pixels=pixels, actual_response_tokens=tokens-prior_tokens,
                marginal_new_pixels=pixels-prior_pixels,
                response_receipt_sha256=row['response_receipt_sha256']))
            prior_tokens, prior_pixels = tokens, pixels
        condition['seed_curves'][seed] = normalized
    document = {name: deepcopy(primary[name]) for name in ('scenes', 'per_scene_seed_budget', 'seeds')}
    document['conditions'] = deepcopy(primary['conditions'] + c0['conditions']) + [condition]
    checked_curves(document)
    return document


def render(document):
    budget, curves = checked_curves(document)
    root = xml.Element('svg', dict(xmlns='http://www.w3.org/2000/svg', width='1300', height='590',
        viewBox='0 0 1300 590', role='img'))
    original.element(root, 'title').text = 'Exploration movement at fixed generated-token budgets'
    original.element(root, 'desc').text = ('Five frozen evaluations, separate paired seed panels. '
        'C0 and the fresh birth are separate branches, not later ages of C2. No causal learning claim.')
    group = original.element(root, 'g', font_family='sans-serif', fill='#20262b')
    original.text(group, 32, 31, 'Exploration movement, not GPU utilization', 22)
    original.text(group, 32, 56, 'Parent-free frozen probes: 3 development scenes × 2 seeds × 1024 generated tokens = 6144 per condition', 14)
    for ordinal, (name, (label, color, dash)) in enumerate(STYLES.items()):
        horizontal = 32 + ordinal * 250
        original.element(group, 'line', x1=horizontal, y1=85, x2=horizontal+25, y2=85,
            stroke=color, stroke_width=3, stroke_dasharray=dash or 'none')
        original.text(group, horizontal+33, 89, label, 14)
    maximum = max(curve[-1]['cumulative_new_pixels'] for seeds in curves.values() for curve in seeds.values())
    ceiling = max(5, ((maximum+4)//5)*5)
    for ordinal, seed in enumerate(map(str, document['seeds'])):
        left, top, width, height = 75+ordinal*640, 137, 525, 290
        horizontal = lambda tokens: left+width*tokens/budget
        vertical = lambda pixels: top+height-height*pixels/ceiling
        original.text(group, left, top-15, 'Paired seed '+seed, 16)
        for pixels in range(0, ceiling+1, 5):
            original.element(group, 'line', x1=left, y1=vertical(pixels), x2=left+width,
                y2=vertical(pixels), stroke='#dde3e6')
            original.text(group, left-10, vertical(pixels)+4, str(pixels), 12, text_anchor='end')
        for tokens in range(0, budget+1, 512):
            original.text(group, horizontal(tokens), top+height+21, str(tokens), 12, text_anchor='middle')
        for boundary in range(document['per_scene_seed_budget'], budget, document['per_scene_seed_budget']):
            original.element(group, 'line', x1=horizontal(boundary), y1=top, x2=horizontal(boundary),
                y2=top+height, stroke='#b7c3cd', stroke_dasharray='3 4')
        for name, seeds in curves.items():
            commands = [f'M {left} {top+height}']
            for row in seeds[seed]:
                commands.extend((f'H {horizontal(row["cumulative_generated_tokens"]):.3f}',
                    f'V {vertical(row["cumulative_new_pixels"]):.3f}'))
            label, color, dash = STYLES[name]
            original.element(group, 'path', d=' '.join(commands), fill='none', stroke=color,
                stroke_width=2.6, stroke_dasharray=dash or 'none')
        original.text(group, left+width/2, 477, 'Cumulative generated tokens (THINK + ACT)', 14, text_anchor='middle')
    original.text(group, 20, 283, 'Cumulative new-pixel events', 14, transform='rotate(-90 20 283)', text_anchor='middle')
    original.text(group, 32, 517, 'Credit follows the complete response cost. Novelty events are summed in independent seed archives, not globally unique ideas.', 13)
    original.text(group, 32, 541, 'C2 sleep 51 → 87 is a within-lineage comparison; C0 and the fresh birth are separate branches. No causal H2 result.', 13)
    original.text(group, 32, 565, 'Provisional rank/relevance/novelty statistics—not certified jokes. Additional ages are pending; source hashes: MOVEMENT_CURVES.json.', 13)
    return xml.tostring(root, encoding='unicode')+'\n'


def main():
    paths = [WORKERS/'rohin232_age_probe_20260918/RESULTS.json',
        WORKERS/'rohin232_age_probe_20260918/C0_RESULTS.json',
        WORKERS/'rohin233_kept_age_probe_20260918/R233_FRESH_R231_s1_STATUS.json']
    document = combine(*(json.loads(path.read_bytes()) for path in paths))
    document['source_sha256'] = {str(path.relative_to(WORKERS.parent.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths+[Path(__file__), WORKERS/'rohin232_coordination_20260918/plot_age_probe.py']}
    document['cross_lineage_causal_age_series'] = False
    document['new_pixels_are_globally_unique_ideas'] = False
    (HERE/'public/MOVEMENT_CURVES.json').write_text(json.dumps(document,indent=2,sort_keys=True)+'\n')
    (HERE/'public/MOVEMENT_CURVES.svg').write_text(render(document))


if __name__ == '__main__':
    main()
