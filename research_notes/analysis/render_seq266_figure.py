"""Render the finite SEQ266 comparison, retaining failed gates and denominators."""

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as xml


STATES = ('BASELINE', 'NEW_TRAJECTORY_LOSS_OFF', 'FULL_TARGET')
LABELS = ('Baseline', 'Loss-off', 'Full')
COLORS = ('#74818f', '#bd7539', '#286789')
CONDITIONS = ('OWN_TEXT', 'UNAVAILABLE')
PROTOCOL = '1683ca250ef6f95cb41c7972685279a07ec3693fb9ab34e049ffb975e8eb96e9'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(reduction_path, native_root):
    result = read(reduction_path)
    assert result['schema'] == 'QUALITY_ATTEMPT2_TERMINAL_REDUCTION_V1'
    assert result['protocol_sha256'] == PROTOCOL
    assert result['engineering_target_met'] is False
    grouped = defaultdict(dict)
    for task in result['taskwise']:
        if task['split'] != 'PROBE':
            continue
        key = task['state'], task['condition'], task['master']
        assert task['task_index'] not in grouped[key]
        grouped[key][task['task_index']] = task
    rows = []
    expected_worlds = None
    for state in STATES:
        for condition in CONDITIONS:
            worlds = sorted(master for saved_state, saved_condition, master in grouped
                            if (saved_state, saved_condition) == (state, condition))
            assert len(worlds) == 16
            if expected_worlds is None:
                expected_worlds = worlds
            assert worlds == expected_worlds
            goals = pairs = covered_worlds = 0
            for master in worlds:
                tasks = grouped[state, condition, master]
                assert set(tasks) == {0, 1, 2, 3}
                goals += sum(task['correct'] for task in tasks.values())
                world_pairs = 0
                for indexes in ((0, 2), (1, 3)):
                    selected = [tasks[index] for index in indexes]
                    correct = all(task['correct'] for task in selected)
                    ports = [task['actual_first_port'] for task in selected]
                    matched = ports == [task['source_first_port'] for task in selected]
                    commits = all(len(task['routes']) == 2 and
                                  all(route['committed'] and route['kind'] == 'transition'
                                      for route in task['routes']) for task in selected)
                    world_pairs += correct and matched and len(set(ports)) == 2 and commits
                pairs += world_pairs
                covered_worlds += world_pairs > 0
            metrics = result['states'][state]['metrics']['PROBE_' + condition]
            for metric, correct, denominator in (('goals', goals, 64), ('pairs', pairs, 32),
                                                  ('worlds_with_pair', covered_worlds, 16)):
                assert metrics[metric] == correct
                rows.append(dict(state=state, condition=condition, metric=metric,
                                 correct=correct, denominator=denominator))
        retained = result['states'][state]
        for metric in (retained['old_recall']['0'], retained['old_recall']['8'], retained['audit']):
            assert metric['correct'] == metric['denominator'] == 16
    bindings = {'reduction': digest(reduction_path)}
    for arm in STATES[1:]:
        recipe_path = native_root / arm / 'train/RECIPE.json'
        recipe = read(recipe_path)
        assert recipe['seed'] == 0 and recipe['group_sizes'] == [128, 20, 62, 12, 1452]
        assert recipe['updates'] == 2928 and recipe['new_target_presentations'] == 5808
        assert result['training'][arm]['new_trajectory_presentations'] == 5808
        bindings[arm + '_recipe'] = digest(recipe_path)
    return dict(schema='SEQ266_FIGURE_TABLE_V1', source_sha256=bindings,
                executed_source=result['source_commit'], protocol_sha256=PROTOCOL,
                archive_sha256=result['archive_sha256'], rows=rows,
                training_seed=0, new_targets=1452, trajectory_presentations=4,
                updates=2928, retention='W0/W8/audit16/16_each_state',
                engineering_target_met=False,
                scope='One-seed exposed DEV, held identifiers, supplied text; no automatic promotion or H1/H2.')


def render(table):
    assert table['schema'] == 'SEQ266_FIGURE_TABLE_V1'
    assert table['protocol_sha256'] == PROTOCOL and table['engineering_target_met'] is False
    assert (table['training_seed'], table['new_targets'], table['trajectory_presentations'], table['updates']) == (0, 1452, 4, 2928)
    values = {(row['state'], row['condition'], row['metric']): row for row in table['rows']}
    assert len(values) == len(table['rows']) == 18
    for row in table['rows']:
        assert type(row['correct']) is int and 0 <= row['correct'] <= row['denominator']
        assert row['denominator'] == {'pairs': 32, 'goals': 64, 'worlds_with_pair': 16}[row['metric']]
    root = xml.Element('svg', xmlns='http://www.w3.org/2000/svg', width='1200', height='640',
                       viewBox='0 0 1200 640', role='img', **{'aria-labelledby': 'title description'})
    xml.SubElement(root, 'title', id='title').text = 'SEQ266 held-identifier supplied-text comparison'
    xml.SubElement(root, 'desc', id='description').text = (
        'One seed. Full supervision reaches 30 of 32 pairs with text, versus one loss-off and two baseline. '
        'All states reach zero pairs without text. Full covers 15 of 16 worlds, failing the every-world gate.')

    def shape(kind, **attributes):
        return xml.SubElement(root, kind, {name.replace('_', '-'): str(value) for name, value in attributes.items()})

    def text(horizontal, vertical, message, size=14, color='#263442', anchor='start', weight='normal'):
        element = shape('text', x=horizontal, y=vertical, font_size=size, fill=color,
                        text_anchor=anchor, font_weight=weight, font_family='DejaVu Sans, sans-serif')
        element.text = message

    shape('rect', x=0, y=0, width=1200, height=640, fill='white')
    text(55, 43, 'SEQ266: text-supported held-identifier transfer', 25, weight='bold')
    text(55, 72, 'One training seed | Same topology family | No automatic checkpoint promotion', 14)
    shape('rect', x=838, y=53, width=307, height=34, rx=5, fill='#fff0e8')
    text(991, 76, 'Engineering conjunction: FAIL', 15, '#923619', 'middle', 'bold')
    definitions = xml.SubElement(root, 'defs')
    pattern = xml.SubElement(definitions, 'pattern', id='hatch', width='6', height='6', patternUnits='userSpaceOnUse')
    xml.SubElement(pattern, 'path', d='M-1,1 l2,-2 M0,6 l6,-6 M5,7 l2,-2', stroke='#384653', **{'stroke-width': '1'})
    shape('rect', x=55, y=102, width=19, height=16, fill='#667988')
    text(84, 115, 'OWN_TEXT: actual stored EVENT text', 13)
    shape('rect', x=395, y=102, width=19, height=16, fill='url(#hatch)', stroke='#384653')
    text(424, 115, 'UNAVAILABLE: stored text withheld', 13)
    titles = ('A  Strict opposite-goal pairs', 'B  Individual goals', 'C  Worlds with a correct pair')
    for panel, metric in enumerate(('pairs', 'goals', 'worlds_with_pair')):
        left, bottom, height = 68 + panel * 385, 466, 250
        text(left - 15, 168, titles[panel], 17, weight='bold')
        if panel == 2:
            text(left - 15, 190, 'OWN_TEXT only; every world is required', 12)
        for tick in (0, .25, .5, .75, 1):
            vertical = bottom - tick * height
            shape('line', x1=left, y1=vertical, x2=left+302, y2=vertical,
                  stroke='#dbe1e5', stroke_width=1)
            text(left-9, vertical+4, f'{tick:.0%}', 11, '#63717c', 'end')
        if panel == 2:
            shape('line', x1=left, y1=bottom-height, x2=left+302, y2=bottom-height,
                  stroke='#923619', stroke_width=1.5, stroke_dasharray='5,4')
            text(left+300, bottom-height-10, 'Required: 16/16', 12, '#923619', 'end')
        for position, state in enumerate(STATES):
            center = left + 54 + position * 100
            conditions = CONDITIONS if panel < 2 else CONDITIONS[:1]
            for condition_index, condition in enumerate(conditions):
                row = values[state, condition, metric]
                bar_height = height * row['correct'] / row['denominator']
                bar_width = 28 if panel < 2 else 56
                horizontal = center - 31 + 35*condition_index if panel < 2 else center-28
                shape('rect', x=horizontal, y=bottom-bar_height, width=bar_width, height=bar_height,
                      fill=COLORS[position] if condition == 'OWN_TEXT' else 'url(#hatch)',
                      stroke=COLORS[position], stroke_width=1)
                inside = panel == 2 and row['correct'] / row['denominator'] > .85
                text(horizontal+bar_width/2, bottom-bar_height+(19 if inside else -8),
                     f"{row['correct']}/{row['denominator']}", 12,
                     color='white' if inside else '#263442', anchor='middle',
                     weight='bold' if state == 'FULL_TARGET' else 'normal')
            text(center, bottom+26, LABELS[position], 13, anchor='middle')
    shape('rect', x=45, y=528, width=1110, height=92, rx=5, fill='#f3f6f8')
    text(59, 552, 'Four presentations/trajectory; 1,452 new terse targets; 2,928 updates/fit. Old W0/W8 and audit: 16/16 in every state.', 12)
    text(59, 576, 'All 32 pairs and 16 worlds retained. The preexisting invalid EVENT remains: no exclusions or repaired source.', 12)
    text(59, 600, 'No error bars: one training seed. Not a rich-supervision, new parametric-memory, or H1/H2 result.', 12)
    return xml.tostring(root, encoding='utf-8', xml_declaration=True)


def export_pdf_png(image):
    """Draw this renderer's rect/line/text subset with installed Pillow/ReportLab."""
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.colors import toColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    paths = {False: '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             True: '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'}
    names = {False: 'Seq266Regular', True: 'Seq266Bold'}
    for bold, path in paths.items():
        pdfmetrics.registerFont(TTFont(names[bold], path))
    raster = Image.new('RGB', (1200, 640), 'white')
    drawing = ImageDraw.Draw(raster)
    output = io.BytesIO()
    document = canvas.Canvas(output, pagesize=(1200, 640), invariant=1)
    document.setTitle('SEQ266 finite held-identifier transfer; engineering conjunction fails')

    def line(start_x, start_y, end_x, end_y, color, width=1):
        drawing.line((start_x, start_y, end_x, end_y), fill=color, width=max(1, round(width)))
        document.setStrokeColor(toColor(color))
        document.setLineWidth(width)
        document.line(start_x, 640-start_y, end_x, 640-end_y)

    for element in xml.fromstring(image):
        kind = element.tag.rsplit('}', 1)[-1]
        attrs = element.attrib
        if kind in ('title', 'desc', 'defs'):
            continue
        if kind == 'rect':
            left, top, width, height = (float(attrs[name]) for name in ('x', 'y', 'width', 'height'))
            fill = attrs.get('fill', 'white')
            hatch = fill == 'url(#hatch)'
            fill = 'white' if hatch else fill
            stroke = attrs.get('stroke')
            drawing.rectangle((left, top, left+width, top+height), fill=fill, outline=stroke)
            document.setFillColor(toColor(fill))
            if stroke:
                document.setStrokeColor(toColor(stroke))
            document.rect(left, 640-top-height, width, height, fill=1, stroke=int(stroke is not None))
            if hatch:
                for offset in range(-int(height)-6, int(width)+1, 6):
                    start, end = max(0, -offset), min(height, width-offset)
                    if start < end:
                        line(left+offset+start, top+height-start,
                             left+offset+end, top+height-end, '#384653')
        elif kind == 'line':
            start_x, start_y, end_x, end_y = (float(attrs[name]) for name in ('x1', 'y1', 'x2', 'y2'))
            dash = attrs.get('stroke-dasharray')
            if dash:
                assert start_y == end_y
                step, gap = map(float, dash.split(','))
                while start_x < end_x:
                    line(start_x, start_y, min(start_x+step, end_x), end_y,
                         attrs['stroke'], float(attrs['stroke-width']))
                    start_x += step+gap
            else:
                line(start_x, start_y, end_x, end_y, attrs['stroke'], float(attrs['stroke-width']))
        elif kind == 'text':
            horizontal, vertical, size = (float(attrs[name]) for name in ('x', 'y', 'font-size'))
            bold = attrs['font-weight'] == 'bold'
            anchor = attrs['text-anchor']
            font = ImageFont.truetype(paths[bold], round(size))
            drawing.text((horizontal, vertical), element.text, fill=attrs['fill'], font=font,
                         anchor={'start':'ls', 'middle':'ms', 'end':'rs'}[anchor])
            document.setFont(names[bold], size)
            document.setFillColor(toColor(attrs['fill']))
            method = {'start': document.drawString, 'middle': document.drawCentredString,
                      'end': document.drawRightString}[anchor]
            method(horizontal, 640-vertical, element.text)
        else:
            raise ValueError('unsupported_figure_primitive:' + kind)
    document.showPage()
    document.save()
    png = io.BytesIO()
    raster.save(png, format='PNG')
    return png.getvalue(), output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--reduction', type=Path)
    inputs.add_argument('--table', type=Path)
    parser.add_argument('--native-root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.reduction and not arguments.native_root:
        parser.error('--native-root is required with --reduction')
    table = extract(arguments.reduction, arguments.native_root) if arguments.reduction else read(arguments.table)
    image = render(table)
    png, pdf = export_pdf_png(image)
    arguments.output.mkdir(parents=True, exist_ok=False)
    (arguments.output/'source_table.json').write_text(json.dumps(table, indent=2, sort_keys=True)+'\n')
    with (arguments.output/'source_table.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=('state','condition','metric','correct','denominator'))
        writer.writeheader()
        writer.writerows(table['rows'])
    for extension, data in (('svg', image), ('png', png), ('pdf', pdf)):
        (arguments.output/('seq266_transfer.'+extension)).write_bytes(data)
    print(json.dumps({'output': str(arguments.output), 'counts_checked': len(table['rows']),
                      'files': {path.name:digest(path) for path in sorted(arguments.output.iterdir())}},indent=2))


if __name__ == '__main__':
    main()
