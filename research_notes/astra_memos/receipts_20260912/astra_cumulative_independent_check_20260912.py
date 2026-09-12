import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

root = Path('/tmp/astra_cumulative_terminal_20260912/astra_cumulative_20260912_attempt1')
repo = Path('/data/home/rohing/dream-state')
supplement_path = Path('/tmp/astra_cumulative_specificity_terminal_20260912.json')
summary_path = Path('/tmp/astra_cumulative_summary_20260912.json')
load = lambda path: json.loads(path.read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
primary = load(root / 'report.json')
supplement = load(supplement_path)
summary = load(summary_path)
manifest = load(root / 'manifest.json')
finished = load(root / 'RUN_FINISHED.json')
terminal = load(root / 'MAIN_TERMINAL_AUDIT.json')
bank = load(root / 'bank.json')
cues = load(root / 'cues.json')
states = ['A1_before', 'AN', 'A2', 'A1_after']
evaluations = {state: load(root / 'stages' / state / 'eval.json') for state in states}
initial_hashes = {str(path): sha(path) for path in root.rglob('*') if path.is_file()}

def equal(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            equal(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            equal(left, right)
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)

def difference(left, right):
    if isinstance(left, dict):
        return {key: difference(left[key], right[key]) for key in left}
    return left - right

def metrics(row):
    result = {}
    for side in ['ON', 'OFF']:
        raw = row[side]['p_raw']
        mass = math.fsum(raw.values())
        conditional = raw[row['a']] / mass
        equal(row[side]['mass'], mass)
        equal(row[side]['p_norm'][row['a']], conditional)
        result[side] = dict(conditional_target_probability=conditional,
                            log_conditional_target_probability=math.log(conditional),
                            raw_target_probability=raw[row['a']], raw_colour_mass=mass,
                            p_abstain=row[side]['p_abstain'])
    delta = difference(result['ON'], result['OFF'])
    result.update(probability_gain=delta['conditional_target_probability'],
                  loggain=delta['log_conditional_target_probability'],
                  raw_mass_gain=delta['raw_colour_mass'], abstain_gain=delta['p_abstain'])
    return result

def aggregate(values):
    if isinstance(values[0], dict):
        return {key: aggregate([value[key] for value in values]) for key in values[0]}
    return dict(mean=math.fsum(values) / len(values), n=len(values))

for relative, digest in manifest['files'].items():
    assert sha(root / relative) == digest
for relative, digest in supplement['captured_file_sha256'].items():
    assert sha(root / relative) == digest
for relative, digest in manifest['sources'].items():
    assert sha(repo / relative) == digest
for path, digest in summary['source_sha256'].items():
    assert sha(Path(path)) == digest
assert sha(root / 'report.json') == terminal['report_sha256'] == terminal['replay_sha256']
assert sha(root / 'manifest.json') == primary['manifest_sha256'] == terminal['manifest_sha256']
assert primary['cost']['run'] == finished
assert finished['completed'] and finished['failure'] is None
assert len({record['pid'] for record in finished['records']}) == 6
for record in finished['records']:
    stage = record['stage']
    done_path = root / 'stages' / stage / 'DONE.json'
    assert sha(done_path) == record['done_sha256']
    done = load(done_path)
    assert sha(root / f'{stage}.job.json') == done['job_sha256']
    cleanup = load(root / f'{stage}.cleanup.json')
    assert cleanup['pid'] == record['pid'] == done['pid']
    assert all(cleanup[key] for key in ['reservation_release_verified', 'owned_group_empty', 'gpu_processes_absent'])
    if stage in states:
        assert sha(root / 'stages' / stage / 'eval.json') == done['eval_sha256']

old_owners = {owner['id'] for owner in bank['owners'] if owner['dose'] == 16}
new_owners = {cue['owner'] for cue in cues if cue['kind'] == 'new_frame'}
assert len(old_owners) == 16 and len(new_owners) == 32 and not old_owners & new_owners
recomputed = {}
for state, evaluation in evaluations.items():
    assert len(evaluation['cues']) == 1377
    assert [row['cue_id'] for row in evaluation['cues']] == [cue['cue_id'] for cue in cues]
    rows = {row['cue_id']: row for row in evaluation['cues']}
    gains = {}
    for kind in ['fact', 'frame']:
        owner_values = []
        for owner in sorted(old_owners):
            selected = [row for row in rows.values() if row['kind'] == kind and row['owner'] == owner]
            assert len(selected) == (3 if kind == 'fact' else 1)
            values = [row['ON']['p_raw'][row['a']] / math.fsum(row['ON']['p_raw'].values())
                      - row['OFF']['p_raw'][row['a']] / math.fsum(row['OFF']['p_raw'].values()) for row in selected]
            owner_values.append(statistics.mean(values))
        gains['old_' + kind + '_gain'] = statistics.mean(owner_values)
        equal(gains['old_' + kind + '_gain'], primary['native_old_summaries'][state]['per_dose']['16']['d_p' if kind == 'fact' else 'frame_d_p'])
    pairs = []
    for owner in sorted(new_owners):
        frame = metrics(rows[f'new_frame|{owner}'])
        bicycle = metrics(rows[f'new_bicycle|{owner}'])
        pairs.append(dict(owner=owner, target_colour=rows[f'new_frame|{owner}']['a'],
                          frame_cue_id=f'new_frame|{owner}', bicycle_cue_id=f'new_bicycle|{owner}',
                          frame=frame, bicycle=bicycle, frame_minus_bicycle=difference(frame, bicycle)))
    equal(pairs, supplement['states'][state]['pairs'])
    means = {key: aggregate([pair[key] for pair in pairs]) for key in ['frame', 'bicycle', 'frame_minus_bicycle']}
    equal(means, supplement['states'][state]['means'])
    assert supplement['states'][state]['n_pairs'] == 32
    gains.update(old_n=16, new_n=32, new_frame_gain=means['frame']['probability_gain']['mean'],
                 new_bicycle_gain=means['bicycle']['probability_gain']['mean'],
                 new_paired_gain=means['frame_minus_bicycle']['probability_gain']['mean'],
                 new_bicycle_abstain=means['bicycle']['ON']['p_abstain']['mean'],
                 new_bicycle_mass=means['bicycle']['ON']['raw_colour_mass']['mean'])
    recomputed[state] = gains
    if state in summary['rows']:
        equal(gains, summary['rows'][state])
assert evaluations['A1_before']['cues'] == evaluations['A1_after']['cues']
for side in ['ON', 'OFF']:
    drift = max(abs(before[side]['p_raw'][colour] - after[side]['p_raw'][colour])
                for before, after in zip(evaluations['A1_before']['cues'], evaluations['A1_after']['cues'])
                for colour in before[side]['p_raw'])
    assert drift == primary['no_update']['max_raw_probability_drift'][side] == 0

corpora = {name: load(root / f'{name}.json')['corpus'] for name in ['OLD', 'AN', 'A2']}
assert [len(corpora[name]) for name in ['OLD', 'AN', 'A2']] == [12924, 2048, 14972]
assert corpora['A2'] == corpora['OLD'] + corpora['AN']
audits = {name: load(root / f'{name}.audit.json') for name in corpora}
for key in ['row_sha256', 'encoding_sha256']:
    assert audits['A2'][key] == audits['OLD'][key] + audits['AN'][key]
for name in ['AN', 'A2']:
    fit = primary['cost']['fits']['fit_' + name]
    assert fit['steps'] == 3 * math.ceil(len(corpora[name]) / 4)
    assert fit['tokens'] == 3 * audits[name]['stats']['input_tokens']
    assert fit['supervised_tokens'] == 3 * audits[name]['stats']['shifted_supervised_tokens']
colour_sequences = 2 * sum(sum(len(variants) for variants in cue['candidates'].values()) for cue in cues)
abstention_sequences = 2 * sum(len(cue.get('abstain', [])) for cue in cues)
assert colour_sequences == 20752 and abstention_sequences == 448
for evaluation in evaluations.values():
    assert evaluation['measured_work']['candidate_sequences'] == colour_sequences + abstention_sequences == 21200
    assert evaluation['work']['candidate_sequences'] == colour_sequences
    assert evaluation['work']['abstention_sequences'] == abstention_sequences
for key, source_key in [('fit_loop_seconds', 'wall_seconds'), ('fit_input_passes', 'tokens'), ('fit_supervised_passes', 'supervised_tokens')]:
    equal(summary[key], sum(fit[source_key] for fit in primary['cost']['fits'].values()))
for key, source_key in [('read_scoring_seconds', 'scoring_seconds'), ('read_padded_input_positions', 'padded_input_tokens'), ('candidate_sequences', 'candidate_sequences'), ('forward_calls', 'forward_calls')]:
    equal(summary[key], sum(evaluation['measured_work'][source_key] for evaluation in evaluations.values()))
assert primary['cost']['new_fit_steps'] == 12765
equal(summary['reserved_gpu_seconds'], finished['reserved_gpu_seconds'])

with summary_path.with_suffix('.csv').open() as stream:
    csv_rows = list(csv.DictReader(stream))
for row in csv_rows:
    state = row.pop('state')
    equal({key: float(value) for key, value in row.items()}, summary['rows'][state])
svg = ET.parse(summary_path.with_suffix('.svg')).getroot()
namespace = {'svg': 'http://www.w3.org/2000/svg'}
bars = [element for element in svg.findall('.//svg:rect', namespace) if element.get('width') == '28']
texts = svg.findall('.//svg:text', namespace)
assert len(bars) == 12
bar_index = 0
for panel_index, keys in enumerate([['old_fact_gain', 'old_frame_gain'], ['new_frame_gain', 'new_bicycle_gain']]):
    for state_index, state in enumerate(states[:3]):
        for metric_index, key in enumerate(keys):
            value = summary['rows'][state][key]
            bar = bars[bar_index]
            bar_index += 1
            equal(float(bar.get('height')), abs(value) * 220)
            equal(float(bar.get('y')), min(290, 290 - value * 220))
            equal(float(bar.get('x')), 50 + 470 * panel_index + 62 + 120 * state_index - 35 + 34 * metric_index)
            labels = [element for element in texts if element.get('x') == str(int(float(bar.get('x'))) + 14)]
            assert len(labels) == 1 and labels[0].text == f'{value:.3f}'
scratch = Path(tempfile.mkdtemp(prefix='astra_cumulative_independent_replay_20260912_'))
subprocess.run([sys.executable, '-B', '/tmp/astra_summarize_cumulative_20260912.py', str(root), str(supplement_path), str(scratch / 'summary')], check=True, stdout=subprocess.DEVNULL)
for suffix in ['.json', '.csv', '.svg']:
    assert (scratch / ('summary' + suffix)).read_bytes() == summary_path.with_suffix(suffix).read_bytes()
with tarfile.open('/tmp/astra_cumulative_terminal_20260912.tgz') as archive:
    members = archive.getmembers()
    assert not any(member.name.endswith('.safetensors') or '/adapter/' in member.name for member in members)
    for member in members:
        if member.isfile():
            disk_path = root.parent / member.name
            assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == sha(disk_path)
assert initial_hashes == {str(path): sha(path) for path in root.rglob('*') if path.is_file()}
evidence_paths = [repo / 'research_notes/astra_memos/ASTRA_CUMULATIVE_TERMINAL_2026-09-12.md', root / 'report.json', root / 'MAIN_TERMINAL_AUDIT.json', root / 'RUN_FINISHED.json', root / 'manifest.json', supplement_path,
                  summary_path, summary_path.with_suffix('.csv'), summary_path.with_suffix('.svg'), Path('/tmp/astra_summarize_cumulative_20260912.py'), Path('/tmp/astra_capture_cumulative_20260912.py'), Path('/tmp/astra_capture_cumulative_repaired_20260912.py'), Path('/tmp/astra_cumulative_terminal_20260912.tgz'), Path(__file__)]
evidence_paths.extend(root / 'stages' / state / 'eval.json' for state in states)
result = dict(status='PASS', independent_rows=recomputed,
              native_fact_ratio=recomputed['A2']['old_fact_gain']/recomputed['A1_before']['old_fact_gain'],
              old_frame_ratio=recomputed['A2']['old_frame_gain']/recomputed['A1_before']['old_frame_gain'],
              candidate_sequences_total=4*(colour_sequences+abstention_sequences),
              abstention_sequences_total=4*abstention_sequences,
              other_reserved_seconds=summary['reserved_gpu_seconds']-summary['fit_loop_seconds']-summary['read_scoring_seconds'],
              checks='raw-score recomputation, all NEW pairs/means/counts, receipt and file hashes, raw no-update equality, OLD corpus prefix and recorded encodings, fit cost arithmetic, candidate accounting, CSV, SVG geometry and signed labels, byte-identical summary regeneration, capsule membership/content, unchanged captured inputs',
              summary_replay_directory=str(scratch), sha256={str(path):sha(path) for path in evidence_paths})
output = Path('/tmp/astra_cumulative_independent_check_20260912.json')
with output.open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
print(json.dumps(result, indent=2, sort_keys=True))
