"""Offline analysis of Main-supplied pinned native collections; never native replay."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path


ROSTER = Path('/tmp/astra_l2_lr_prepared_20260913_attempt1.json')
ROSTER_SHA256 = '2cf367e16116d205eb1e938d05d786d99309d4ae4df4d7afed66863d9d1f865b'
SCHEMA = 'astra_l2_public_record_runtime_v1'
STAGES = ('baseline', 'wake1', 'fit1', 'report1_PROMOTE', 'report1_SHADOW',
          'wake2_PROMOTE', 'wake2_SHADOW', 'fit2_PROMOTE', 'fit2_SHADOW',
          'report2_PROMOTE', 'report2_SHADOW')
REPORTS = tuple(stage for stage in STAGES if stage == 'baseline' or stage.startswith('report'))
NAMES = tuple(f'seed{seed}_{level}' for seed in range(3) for level in ('low', 'high'))
CLAIM = ('Excluded exploratory DEV full-loop LR contrast, not fixed-material quality; '
         'no clean ancestry, mechanism freeze, P1, parenting, H1/H2 or scientific-pass claim. '
         'Three independent learner seeds on one inspected world; original seed0 is a bridge, not a fourth seed.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, label, low=0, high=None):
    require(type(value) is int and value >= low and (high is None or value <= high), label)
    return value


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, label)
    return value


def pin(value):
    require(type(value) is str and len(value) == 64 and all(char in '0123456789abcdef' for char in value), 'invalid SHA256')
    return value


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def finite_tree(value):
    if type(value) is float:
        require(math.isfinite(value), 'nonfinite number')
    elif isinstance(value, dict):
        for child in value.values():
            finite_tree(child)
    elif isinstance(value, list):
        for child in value:
            finite_tree(child)


def read_pinned(path, checksum):
    data = Path(path).read_bytes()
    require(hashlib.sha256(data).hexdigest() == pin(checksum), 'file pin differs')
    value = json.loads(data, object_pairs_hook=unique,
                       parse_constant=lambda constant: require(False, 'nonfinite JSON'))
    finite_tree(value)
    return value


def roster(path=ROSTER):
    data = read_pinned(path, ROSTER_SHA256)
    rows = data['prepared']
    require(type(rows) is list and len(rows) == 6, 'six roster entries required')
    require({row['name'] for row in rows} == set(NAMES), 'exact six roster names required')
    for field in ('root', 'plan_sha256', 'gpu_index', 'gpu_uuid'):
        require(len({row[field] for row in rows}) == 6, 'duplicate roster ' + field)
    result = {row['name']: row for row in rows}
    for seed in range(3):
        for level, rate in (('low', 3e-5), ('high', 1e-4)):
            row = result[f'seed{seed}_{level}']
            require(integer(row['learner_seed'], 'roster seed', 0, 2) == seed and
                    type(row['learning_rate']) is float and row['learning_rate'] == rate and
                    row['schema'] == SCHEMA, 'roster identity differs')
            pin(row['plan_sha256'])
    return result


def validate_report(report, row):
    require(report['schema'] == SCHEMA and report['plan_sha256'] == row['plan_sha256'], 'collection plan/schema differs')
    if 'root' in report:
        require(report['root'] == row['root'], 'collection root differs')
    pin(report['seal_sha256'])
    integer(report['bytes'], 'collection bytes')
    integer(report['file_count'], 'collection file count')
    require(report['scientific_pass'] is None, 'scientific pass is not an analysis claim')
    status = report['status']
    require(status in ('COMPLETE', 'FORMATION_SHORTAGE', 'NONREPORTABLE_RUNTIME_ABORT'), 'unknown status')
    aborted = status == 'NONREPORTABLE_RUNTIME_ABORT'
    if not aborted or 'seeds' in report:
        seeds = report['seeds']
        expected = dict(vocabulary=2026091301, truth=2026091302, learner=row['learner_seed'])
        require(set(seeds) == set(expected) and all(type(seeds[key]) is int and seeds[key] == value
                                                  for key, value in expected.items()), 'collection seed differs')
    if not aborted or 'learning_rate' in report:
        require(type(report['learning_rate']) is float and report['learning_rate'] == row['learning_rate'], 'collection LR differs')
    require(report['two_cycle_complete'] is (status == 'COMPLETE'), 'completion flag differs')
    completed = report['completed']
    require(type(completed) is list and len(set(completed)) == len(completed) and
            all(stage in STAGES for stage in completed), 'completed stages differ')
    if aborted:
        require(report['scientific_replay'] is False and report['failed_raw_stages_not_scored'] is True, 'abort replay flags differ')
        require(all(report.get(key) is None for key in ('reports', 'endpoint', 'work', 'formation', 'exposure', 'contrasts')),
                'aborted raw stages must not be scored')
        return None
    require(report['scientific_replay'] is True, 'verified collection replay required')
    require(completed == list(STAGES[:len(completed)]) and
            report['incomplete'] == list(STAGES[len(completed):]), 'stage prefix/incomplete differs')
    require((len(completed) == len(STAGES)) == (status == 'COMPLETE'), 'status/stages differ')
    panels, exposure, formation = report['reports'], report['exposure'], report['formation']
    require(set(panels) == set(REPORTS) and set(exposure) == set(completed) and
            set(formation) == {stage for stage in completed if stage.startswith('fit')}, 'stage inventory differs')
    work = dict(calls=0, fits=0, updates=0)
    for stage in completed:
        cost = exposure[stage]
        if stage.startswith('fit'):
            formed = formation[stage]
            opportunities = 8 if stage == 'fit1' else 16
            admitted = integer(formed['admitted'], 'admitted', 0, opportunities)
            rejected = integer(formed['rejected'], 'rejected', 0, opportunities)
            require(admitted + rejected == opportunities, 'admission denominator differs')
            fits = integer(cost['fits'], 'fits', 0, 1)
            updates = integer(cost['updates'], 'updates')
            require(fits == int(admitted > 0) and updates == 20 * math.ceil(admitted / 8) and
                    integer(cost['presentations'], 'presentations') == 20 * admitted, 'fit exposure differs')
            require(formed['status'] == ('FIT_COMPLETE' if fits else 'FORMATION_SHORTAGE') and
                    formed['shared_physical_fit'] is (stage == 'fit1'), 'formation status/shared fit differs')
            pin(formed['corpus_sha256'])
            pin(formed['initialized_from_sha256'])
            if fits:
                pin(formed['candidate_sha256'])
                target = integer(cost['target_tokens_per_epoch'], 'target tokens', 1)
                total = integer(cost['total_tokens_per_epoch'], 'total tokens', target)
                require(integer(cost['train_tokens_seen'], 'train tokens') == 20 * total, 'train token denominator differs')
            else:
                require(formed['candidate_sha256'] is None, 'shortage candidate differs')
            work['fits'] += fits
            work['updates'] += updates
        else:
            calls = integer(cost['calls'], 'calls', 8 if stage.startswith('wake') else 16, 16)
            work['calls'] += calls
            integer(cost['prompt_tokens'], 'prompt tokens')
            integer(cost['output_tokens'], 'output tokens')
            integer(cost['length_outputs'], 'length outputs', 0, calls)
            number(cost['generation_seconds'], 'generation seconds')
    require(set(report['work']) == set(work), 'work fields differ')
    for field, cap in (('calls', 128), ('fits', 3), ('updates', 100)):
        require(integer(report['work'][field], field, 0, cap) == work[field], 'work count disagreement')
    for stage, panel in panels.items():
        if stage not in completed:
            require(panel is None, 'uncompleted panel scored')
            continue
        for field in ('total', 'old_total', 'new_total', 'legal', 'malformed', 'old_correct', 'new_correct', 'length_outputs'):
            integer(panel[field], 'panel ' + field, 0, 16)
        require(panel['total'] == 16 and panel['old_total'] == panel['new_total'] == 8 and
                panel['old_correct'] <= 8 and panel['new_correct'] <= 8 and
                panel['old_correct'] + panel['new_correct'] <= panel['legal'] and
                panel['legal'] + panel['malformed'] == 16 and
                panel['length_outputs'] == exposure[stage]['length_outputs'], 'panel count disagreement')
    require(set(report['contrasts']) == {'1', '2'}, 'contrast inventory differs')
    for cycle in ('1', '2'):
        promote, shadow = (panels[f'report{cycle}_{policy}'] for policy in ('PROMOTE', 'SHADOW'))
        contrast = report['contrasts'][cycle]
        if promote is None or shadow is None:
            require(contrast is None, 'incomplete contrast scored')
        else:
            require(set(contrast) == {'old_correct', 'new_correct', 'legal'} and
                    all(type(contrast[key]) is int and contrast[key] == promote[key] - shadow[key]
                        for key in contrast), 'contrast count disagreement')
    if status != 'COMPLETE':
        require(report['endpoint'] is None and completed and completed[-1].startswith('fit') and
                formation[completed[-1]]['status'] == 'FORMATION_SHORTAGE', 'shortage endpoint/status differs')
        return None
    endpoint = report['endpoint']
    require(endpoint['endpoint_evaluable'] is True and endpoint['scientific_pass'] is None and
            endpoint['native_verified'] is False, 'endpoint flags differ from collection API')
    require(set(endpoint['cells']) == {'PROMOTE', 'SHADOW'}, 'endpoint policies differ')
    correct = {}
    for policy, cell in endpoint['cells'].items():
        panel = panels['report2_' + policy]
        for field in ('total', 'observed_correct', 'legal', 'missing', 'old_correct', 'new_correct', 'accepted', 'rejected'):
            integer(cell[field], 'endpoint ' + field, 0, 16)
        correct[policy] = panel['old_correct'] + panel['new_correct']
        require(cell['endpoint_evaluable'] is True and cell['total'] == 16 and cell['missing'] == 0 and
                cell['observed_correct'] == correct[policy] and number(cell['accuracy'], 'accuracy') == correct[policy] / 16 and
                all(cell[key] == panel[key] for key in ('legal', 'old_correct', 'new_correct')) and
                cell['accepted'] == formation['fit2_' + policy]['admitted'] and
                cell['rejected'] == formation['fit2_' + policy]['rejected'], 'endpoint count disagreement')
    paired = endpoint['paired']
    for key in ('both', 'neither', 'promote_only', 'shadow_only', 'total'):
        integer(paired[key], 'paired ' + key, 0, 16)
    require(paired['total'] == 16 and sum(paired[key] for key in ('both', 'neither', 'promote_only', 'shadow_only')) == 16 and
            paired['both'] + paired['promote_only'] == correct['PROMOTE'] and
            paired['both'] + paired['shadow_only'] == correct['SHADOW'] and
            type(paired['net']) is int and paired['net'] == correct['PROMOTE'] - correct['SHADOW'], 'paired count disagreement')
    return dict(numerator=paired['net'], denominator=16, value=paired['net'] / 16)


def describe(values):
    available = [value for value in values if value is not None]
    return dict(planned_learners=3, observed_learners=len(available),
                mean=sum(available) / 3 if len(available) == 3 else None,
                range=[min(available), max(available)] if len(available) == 3 else None)


def cost_totals(report):
    if report['status'] == 'NONREPORTABLE_RUNTIME_ABORT':
        return None
    exposure = report['exposure']
    generation = [value for stage, value in exposure.items() if not stage.startswith('fit')]
    fitted = [value for stage, value in exposure.items() if stage.startswith('fit')]
    return dict(work=report['work'], physical_fit_accounting='Shared fit1 counted once; cumulative later fits counted separately.',
                generation_seconds=sum(value['generation_seconds'] for value in generation),
                prompt_tokens=sum(value['prompt_tokens'] for value in generation),
                output_tokens=sum(value['output_tokens'] for value in generation),
                length_outputs=sum(value['length_outputs'] for value in generation),
                presentations=sum(value['presentations'] for value in fitted),
                train_tokens_seen=sum(value.get('train_tokens_seen', 0) for value in fitted),
                supervised_tokens_seen=sum(20 * value.get('target_tokens_per_epoch', 0) for value in fitted),
                elapsed_scope='Summed generation only, not wall-clock/controller/fit time.')


def analyze(collections, roster_path=ROSTER):
    rows = roster(roster_path)
    require(len(collections) == 6 and {entry[0] for entry in collections} == set(NAMES), 'exact six unique collection keys required')
    require(len({str(Path(entry[1]).resolve()) for entry in collections}) == 6 and
            len({entry[2] for entry in collections}) == 6, 'duplicate collection path/pin')
    runs = {}
    for name, path, checksum in collections:
        report = read_pinned(path, checksum)
        primary = validate_report(report, rows[name])
        runs[name] = dict(identity=rows[name], collection=dict(path=str(path), sha256=checksum),
                          status=report['status'], final_promote_minus_shadow=primary, native_collection=report,
                          measured_cost_totals=cost_totals(report),
                          root_binding='Root resolved by unique pinned roster plan_sha256; collector does not emit root.',
                          seed_lr_binding='roster/plan only; absent in runtime abort' if 'seeds' not in report else 'collection and roster agree',
                          admission_denominators={stage: dict(admitted=value['admitted'], rejected=value['rejected'],
                                                             opportunities=8 if stage == 'fit1' else 16)
                                                  for stage, value in report.get('formation', {}).items()},
                          unavailable=dict(fit_losses=None, fit_elapsed_seconds=None, controller_elapsed_seconds=None,
                                           first_report_paired_intersections=None,
                                           reason='Not emitted by native collect API; no raw/model/corpus reads performed.'))
    pairs = []
    for seed in range(3):
        low, high = (runs[f'seed{seed}_{level}']['final_promote_minus_shadow'] for level in ('low', 'high'))
        pairs.append(dict(seed=seed, low=low, high=high,
                          high_minus_low=None if low is None or high is None else
                          dict(numerator=high['numerator'] - low['numerator'], denominator=16,
                               value=high['value'] - low['value'])))
    summaries = {field: describe([pair[field]['value'] if pair[field] is not None else None for pair in pairs])
                 for field in ('low', 'high', 'high_minus_low')}
    return dict(schema='astra_l2_lr_analysis_v1', claim=CLAIM,
                analysis_scope='Analysis over Main-supplied verified native collections, not raw-byte/native replay or independent native certification.',
                roster=dict(path=str(roster_path), sha256=ROSTER_SHA256), runs=runs, paired_learners=pairs,
                descriptive=summaries, all_six_complete=all(run['status'] == 'COMPLETE' for run in runs.values()),
                failures={name: run['status'] for name, run in runs.items() if run['status'] != 'COMPLETE'},
                original_seed0_bridge_included_as_replicate=False, scientific_pass=None)


def write_once(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roster', default=str(ROSTER))
    parser.add_argument('--collection', nargs=3, action='append', required=True, metavar=('NAME', 'PATH', 'SHA256'))
    parser.add_argument('--output', required=True)
    options = parser.parse_args(argv)
    write_once(options.output, analyze(options.collection, options.roster))


if __name__ == '__main__':
    main()
