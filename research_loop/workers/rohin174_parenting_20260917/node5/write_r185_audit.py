"""Produce one concise NODE5 receipt table without sending or signalling."""

from datetime import datetime
import json
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from activate_parent import read, reference


HERE = Path(__file__).resolve().parent
ZONE = ZoneInfo('America/Los_Angeles')


def clock(value):
    return datetime.fromtimestamp(value, ZONE).strftime('%H:%M:%S PDT')


def main():
    audit_path = sorted(HERE.glob('R181_AUDIT_*.json'))[-1]
    audit = read(audit_path)
    first = {row['label']: row.get('first_recipe') for row in
             read(HERE / 'ALL8_CACHE_STATUS_1789684377754893693.json')['rows']}
    rows = {row['label']: row for row in audit['rows']}
    now = time.time()
    lines = ['# NODE5 R185 receipt audit — September 17, 2026 ' + clock(now), '',
        'Native/recipe/cache observation: ' + clock(audit['observed_unix']) +
        '. Parent phase files inspected at table creation. No NODE2 operations.', '',
        '| Life | Latest completed sleep / time | Current state | R181 first recipe / completed new-only | Cache / operator | R184 effort parent |',
        '| --- | --- | --- | --- | --- | --- |']
    phase_refs = []
    for label in ('C1','C2','C3','C4','C5','run1','pilot','repo_reader'):
        row = rows[label]
        complete = row['latest']['SLEEP_COMPLETE']
        completed = str(complete['details']['cycle']) + ' / ' + clock(complete['mtime_unix'])
        requested = row['latest'].get('SLEEP_REQUEST', {}).get('details', {}).get('cycle')
        state = row['head']['kind'] + str(row['head']['index'])
        if row['head']['kind'] == 'UPDATE':
            state += ' sleep' + str(requested)
        state += '; native ' + ('live' if row['native_live'] else 'not live')
        recipe = first.get(label)
        if recipe:
            details = recipe['metadata']
            recipe_text = 'APPLIED old' + str(details['selected_old_rows']) + '/new' + str(details['new_rows']) + '×16 @' + clock(recipe['mtime_unix']) + ' #' + str(recipe['index'])
        else:
            recipe = row['latest'].get('SLEEP_RECIPE')
            recipe_text = ('old' + str(recipe['details']['selected_old_rows']) + '/new' +
                str(recipe['details']['new_rows']) + '×16 @' + clock(recipe['mtime_unix']) +
                ' #' + str(recipe['index'])) if recipe else 'ARMED; old sleep completing'
        completed_recipe = row.get('completed_recipe')
        new_only_complete = completed_recipe and completed_recipe['details'].get('selected_old_rows') == 0
        recipe_text += '; completed new-only ' + (str(complete['details']['cycle']) if new_only_complete else 'none')
        cache = ('LOADED' if row['cache_active'] else 'pending') + '; ' + str(row['operator']['pid'])
        cache += ' live' if row['operator_live'] else ' not live'
        phase = 'EXCLUDED; fixed172; no extra Astra'
        if label != 'C2':
            candidates = sorted(HERE.glob('ROUTE_' + label + '_*/source/R184_EFFORT_PHASE.json'))
            phase = 'pending; no R184 PUB/REQUEST'
            if candidates:
                root = candidates[-1].parents[1]
                output = root / 'parent'
                phase_refs.append(label + ': `' + str(root.relative_to(HERE)) + '`')
                failed = output / 'FAILED_CLOSED.json'
                if failed.exists():
                    failure = read(failed)
                    phase = 'parent-only failure: ' + failure['error_type'] + ': ' + failure['error'].replace('|', '/')
                elif (output / 'ACTIVE_PARENT.json').exists():
                    active = read(output / 'ACTIVE_PARENT.json')
                    phase = 'active PID' + str(active['pid']) + '; PUB/REQUEST pending'
                elif (root / 'STARTED.json').exists():
                    phase = 'handoff pending; PUB/REQUEST pending'
                else:
                    phase = 'source staging; PUB/REQUEST pending'
                publication = output / 'R184_FIRST_PUBLICATION.json'
                rendered = output / 'R184_FIRST_RENDERED_REQUEST.json'
                if publication.exists():
                    receipt = read(publication)
                    phase = 'PUB ' + receipt['publication']['id'] + ' @' + clock(receipt['observed_unix'])
                    phase += '; REQUEST ' + json.dumps(read(rendered).get('rendered', read(rendered).get('delivery', {}))) if rendered.exists() else '; REQUEST pending'
        lines.append('| ' + ' | '.join((label,completed,state,recipe_text,cache,phase)) + ' |')
    lines += ['', 'Completed times are retained record file times; publication times are observer receipt times. Recipe start is not sleep completion. A live waiter is not a loaded successor.', '',
        'Exact native/source/cache/record references: `' + audit_path.name + '` SHA `' + reference(audit_path)['sha256'] + '`.',
        'Initial recipe references: `ALL8_CACHE_STATUS_1789684377754893693.json`.',
        'Effort phase preserves existing arms, cadence, caps, pending publications and withdrawal clocks. No baseline repeated, no peer addition, no learner signal by this parent phase.', '',
        '## Parent phase receipt roots', *phase_refs, '']
    path = HERE / ('R185_NODE5_AUDIT_' + str(time.time_ns()) + '.md')
    with path.open('x') as handle:
        handle.write('\n'.join(lines))
    print(json.dumps(reference(path)))


if __name__ == '__main__':
    main()
