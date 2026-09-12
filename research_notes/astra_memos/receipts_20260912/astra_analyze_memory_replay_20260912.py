import collections
import datetime
import hashlib
import json
from pathlib import Path
import re
import tarfile


ARCHIVE = Path('/tmp/astra_memory_replay_seed0_terminal_20260912.tgz')
ROOT = Path('/tmp/astra_memory_replay_seed0_terminal_20260912')
PREFIX = 'astra_diagnostics/astra_memory_replay_20260912_attempt1/seed0'
OUTPUT = Path('/tmp/astra_memory_replay_seed0_analysis_20260912.json')


def read(path):
    return json.loads(path.read_text())


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def addition(text, expected):
    found = {}
    for label in ('ACT', 'PREDICT'):
        entries = []
        for position, line in enumerate(text.splitlines()):
            if re.match(r'^[ \t]*' + label + r'\b', line):
                match = re.fullmatch(r'[ \t]*' + label + r':[ \t]*([+-]?[0-9]+)[ \t]*', line)
                entries.append((position, int(match[1]) if match else None))
        found[label] = entries
    actions, predictions = found['ACT'], found['PREDICT']
    valid = len(actions) == 1 and actions[0][1] is not None
    correct = valid and actions[0][1] == expected
    habit = correct and len(predictions) == 1 and predictions[0][1] == expected and predictions[0][0] < actions[0][0]
    return dict(correct_action=bool(correct), action_valid=bool(valid), adherence=bool(habit))


def main():
    validation = read(Path(str(ARCHIVE) + '.validation.json'))
    assert checksum(ARCHIVE) == validation['sha256']
    with tarfile.open(ARCHIVE) as archive:
        members = archive.getmembers()
        assert len(members) == len(validation['files'])
        assert {member.name for member in members} == set(validation['files'])
        for member in members:
            assert member.isfile() and member.name.startswith(PREFIX + '/')
            assert '..' not in Path(member.name).parts and not Path(member.name).is_absolute()
            assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == validation['files'][member.name]
        ROOT.mkdir(exist_ok=False)
        archive.extractall(ROOT, filter='data')
    base = ROOT / PREFIX
    plan, terminal, release = (read(base / name) for name in ('plan.json', 'run/terminal.json', 'run/main_release.json'))
    assert checksum(base / 'plan.json') == '70405bfa50486feaa2b000ee8102a1cdf30265bccaf102958d7e3ea17035bbb9'
    assert release['full_release'] and release['controller_absent']
    assert release['terminal_sha256'] == checksum(base / 'run/terminal.json')
    assert terminal['status'] == 'COMPLETE' and terminal['deadline_met'] and terminal['release_verified']
    assert list(plan['arm_order']) == ['mixed', 'all_memory'] and set(terminal['arms']) == {'mixed', 'all_memory'}
    results = {}
    for arm in ('mixed', 'all_memory'):
        branch = base / 'run' / arm
        manifest = read(branch / 'adapter/train_manifest.json')
        assert manifest['steps'] == 160 and manifest['nonfinite_batches'] == 0
        assert manifest['epochs_run'] == (20 if arm == 'mixed' else 40)
        panels = {}
        for panel_name, count in (('dev', 48), ('exact', 16)):
            panel = branch / panel_name
            reduction, panel_plan = read(panel / 'reduction.json'), read(panel / 'plan.json')
            assert reduction['complete'] and len(reduction['rows']) == count
            cases = {case['id']: case for case in panel_plan['cases']}
            assert len(cases) == count and {row['case_id'] for row in reduction['rows']} == set(cases)
            reasons, answers, arithmetic = collections.Counter(), {}, []
            correct_memory = 0
            for row in reduction['rows']:
                case = cases[row['case_id']]
                assert row['expected'] == case['expected']
                received = read(panel / 'run/data/calls' / (row['call_id'] + '.response.json'))['response']
                assert received['text'] == row['raw_text']
                reasons[received['finish_reason']] += 1
                if panel_name == 'exact' or row['kind'] == 'memory_recall':
                    normalized = row['raw_text'].strip().lower().removesuffix('.')
                    correct = normalized == case['expected']
                    assert correct == row['correct']
                    correct_memory += correct
                    answers[row['case_id']] = dict(expected=case['expected'], raw=row['raw_text'], correct=correct)
                else:
                    scored = addition(row['raw_text'], case['expected'])
                    assert all(row[key] == value for key, value in scored.items())
                    arithmetic.append(dict(case_id=row['case_id'], raw=row['raw_text'], **scored))
            assert len(answers) == 16
            assert correct_memory == (reduction['counts']['correct'] if panel_name == 'exact' else reduction['counts']['memory']['correct'])
            if panel_name == 'dev':
                assert len(arithmetic) == 32
                assert sum(row['adherence'] for row in arithmetic) == reduction['counts']['addition']['adherence']
                assert sum(row['correct_action'] for row in arithmetic) == reduction['counts']['addition']['correct_action']
            panels[panel_name] = dict(counts=reduction['counts'], memory=answers, arithmetic=arithmetic,
                                     finish_reasons=dict(reasons), cost=reduction['cost'])
        results[arm] = dict(panels=panels, accounting=read(branch / 'fit-result.json')['accounting'])
    mixed = results['mixed']['panels']
    gate = mixed['dev']['counts']['memory']['correct'] >= 15 and mixed['exact']['counts']['correct'] >= 15 and \
        mixed['dev']['counts']['addition']['adherence'] >= 30 and mixed['dev']['counts']['addition']['correct_action'] >= 31
    result = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  capsule_sha256=validation['sha256'], verified_files=len(validation['files']), arms=results,
                  progression_pass=gate, next_seeds=[1, 2] if gate else [], new_fits=2, new_calls=128,
                  new_updates=320, new_off_calls=0, confirmation_calls=0,
                  full_reservation_seconds=release['full_reservation_seconds'], controller_seconds=terminal['reserved_seconds'],
                  worker_seconds=terminal['worker_reserved_seconds'], release_utc=release['release_utc'],
                  claim='Fixed-update allocation to replay versus all-memory, not equal memory dose or token compute. '
                        'Both panels query the same16facts. Root0 exploratory diagnostic; no general G3/P1/G5/H1/H2.',
                  cost_scope='Nested scopes, not additive; full reservation includes collection delay.')
    with OUTPUT.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
    print(json.dumps(dict(output=str(OUTPUT), progression_pass=gate, counts={arm: {name: panel['counts']
          for name, panel in value['panels'].items()} for arm, value in results.items()}, release_utc=release['release_utc']), indent=2))


if __name__ == '__main__':
    main()
