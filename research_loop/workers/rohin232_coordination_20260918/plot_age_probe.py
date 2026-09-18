"""Render the immutable primary fixed-token probe without changing its scores."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as xml


STYLES = {
    'source51': ('C2 sleep 51', '#2868b2', ''),
    'currentC2': ('C2 sleep 87', '#c45123', '7 4'),
    'base': ('Frozen base', '#46555c', '3 3'),
}


def checked_curves(document):
    budget = document['scenes'] * document['per_scene_seed_budget']
    expected = set(map(str, document['seeds']))
    result = {}
    for condition in document['conditions']:
        name = condition['condition']
        if name not in STYLES or name in result or set(condition['seed_curves']) != expected:
            raise ValueError('exact_primary_conditions_and_paired_seeds_required')
        if condition['generated_tokens'] != budget * len(expected) or condition['probe_optimizer_updates'] != 0:
            raise ValueError('complete_frozen_common_budget_required')
        total_pixels = 0
        for curve in condition['seed_curves'].values():
            prior_tokens, prior_pixels = 0, 0
            for row in curve:
                tokens, pixels = row['cumulative_generated_tokens'], row['cumulative_new_pixels']
                if tokens - prior_tokens != row['actual_response_tokens'] or not prior_tokens < tokens <= budget:
                    raise ValueError('charge_every_actual_generated_token_once')
                if pixels - prior_pixels != row['marginal_new_pixels'] or pixels < prior_pixels:
                    raise ValueError('monotone_response_bound_pixel_events')
                prior_tokens, prior_pixels = tokens, pixels
            if prior_tokens != budget:
                raise ValueError('incomplete_seed_budget')
            total_pixels += prior_pixels
        if total_pixels != condition['new_pixel_events']:
            raise ValueError('seed_events_must_match_reported_total')
        result[name] = condition['seed_curves']
    if set(result) != set(STYLES):
        raise ValueError('all_three_primary_conditions_required')
    return budget, result


def element(parent, tag, **attributes):
    return xml.SubElement(parent, tag, {name.replace('_', '-'): str(value) for name, value in attributes.items()})


def text(parent, horizontal, vertical, value, size=13, **attributes):
    node = element(parent, 'text', x=horizontal, y=vertical, font_size=size, **attributes)
    node.text = value
    return node


def render(document, source_sha):
    budget, curves = checked_curves(document)
    root = xml.Element('svg', dict(xmlns='http://www.w3.org/2000/svg', width='1120', height='570',
                                  viewBox='0 0 1120 570', role='img'))
    title = element(root, 'title')
    title.text = 'Fixed-token developmental-age probe, independent seed panels'
    description = element(root, 'desc')
    description.text = ('Step curves charge the full generated response before crediting its score. '
        'Three development cartoons per seed, 1024 generated tokens each. Provisional scoring '
        'events, not certified humor, globally distinct ideas, or a causal H2 result.')
    group = element(root, 'g', font_family='sans-serif', fill='#20262b')
    text(group, 35, 32, 'Matched generated-token probe: no improvement in this small diagnostic', 20)
    text(group, 35, 57, 'Frozen inference • no parent • three fresh development cartoons • rank ≤ 50 plus relevance and novelty', 13)
    for ordinal, (name, style) in enumerate(STYLES.items()):
        label, color, dash = style
        horizontal = 35 + ordinal * 245
        element(group, 'line', x1=horizontal, y1=82, x2=horizontal + 30, y2=82,
                stroke=color, stroke_width=3, stroke_dasharray=dash or 'none')
        text(group, horizontal + 39, 87, label, 14)
    maximum = max(curve[-1]['cumulative_new_pixels'] for seeds in curves.values() for curve in seeds.values())
    ceiling = max(5, ((maximum + 4) // 5) * 5)
    for ordinal, seed in enumerate(map(str, document['seeds'])):
        left, top, width, height = 75 + ordinal * 550, 128, 455, 290
        scale_horizontal = lambda tokens: left + width * tokens / budget
        scale_vertical = lambda pixels: top + height - height * pixels / ceiling
        text(group, left, top - 17, f'Paired seed {seed}', 16)
        for pixels in range(0, ceiling + 1, 5):
            vertical = scale_vertical(pixels)
            element(group, 'line', x1=left, y1=vertical, x2=left + width, y2=vertical, stroke='#dde3e6')
            text(group, left - 12, vertical + 4, str(pixels), 12, text_anchor='end')
        for tokens in range(0, budget + 1, 512):
            horizontal = scale_horizontal(tokens)
            element(group, 'line', x1=horizontal, y1=top + height, x2=horizontal, y2=top + height + 5, stroke='#68757e')
            text(group, horizontal, top + height + 22, str(tokens), 12, text_anchor='middle')
        for boundary in range(document['per_scene_seed_budget'], budget, document['per_scene_seed_budget']):
            horizontal = scale_horizontal(boundary)
            element(group, 'line', x1=horizontal, y1=top, x2=horizontal, y2=top + height,
                    stroke='#cad3d9', stroke_dasharray='3 4')
        for name, seeds in curves.items():
            curve = seeds[seed]
            commands = [f'M {left:.3f} {top + height:.3f}']
            for row in curve:
                commands.append(f'H {scale_horizontal(row["cumulative_generated_tokens"]):.3f}')
                commands.append(f'V {scale_vertical(row["cumulative_new_pixels"]):.3f}')
            label, color, dash = STYLES[name]
            element(group, 'path', d=' '.join(commands), fill='none', stroke=color,
                    stroke_width=2.7, stroke_dasharray=dash or 'none')
        text(group, left + width / 2, 463, 'Cumulative generated tokens (THINK + ACT)', 13, text_anchor='middle')
        endpoints = '  |  '.join(f'{STYLES[name][0]}: {seeds[seed][-1]["cumulative_new_pixels"]}'
                                for name, seeds in curves.items())
        text(group, left, 488, endpoints, 12)
    text(group, 19, 284, 'Cumulative new-pixel events', 13, transform='rotate(-90 19 284)', text_anchor='middle')
    text(group, 35, 517, 'Vertical dotted lines mark fresh-scene boundaries. Seed archives are independent; totals are not global unique-idea counts.', 12)
    text(group, 35, 538, 'Only 9/200 accepted strings spot-reviewed as literal caption attempts. No humor certification or causal learning claim.', 12)
    text(group, 35, 559, 'Source RESULTS.json SHA256: ' + source_sha, 11)
    return xml.tostring(root, encoding='unicode') + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    options = parser.parse_args()
    raw = options.source.read_bytes()
    result = render(json.loads(raw), hashlib.sha256(raw).hexdigest())
    options.output.write_text(result)


if __name__ == '__main__':
    main()
