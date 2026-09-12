import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

archive = Path('/tmp/astra_interleaved_memory_root0_terminal_20260912.tgz')
validation_path = Path('/tmp/astra_interleaved_memory_validation_20260912.json')
validation = json.loads(validation_path.read_text())
assert hashlib.sha256(archive.read_bytes()).hexdigest() == validation['sha256'] == '9aa7fb67b3f68afa3d4520e1f4b7cfcc41322367ef1cf6ee83396a7c60cdbf64'
payloads = {}
with tarfile.open(archive, 'r:gz') as bundle:
    for member in bundle.getmembers():
        path = PurePosixPath(member.name)
        assert member.isfile() and not path.is_absolute() and '..' not in path.parts
        assert member.name not in payloads and path.parts[0] == 'fits_root0_attempt1'
        payload = bundle.extractfile(member).read()
        assert hashlib.sha256(payload).hexdigest() == validation['files'][member.name]
        payloads[member.name] = payload
assert set(payloads) == set(validation['files']) and len(payloads) == 548

def read(relative):
    return json.loads(payloads['fits_root0_attempt1/' + relative])

terminal = read('run/terminal.json')
release = read('run/main_release.json')
plan = read('plan.json')
assert terminal['status'] == 'COMPLETE' and terminal['deadline_met'] and terminal['release_verified']
assert release['full_release'] and not release['observation']['late_observation']
assert terminal['plan_sha256'] == validation['plan_sha256'] == '4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388'
counts = {}
for arm in ('SINGLE_VIEW', 'FOUR_VIEW'):
    counts[arm] = {panel: read(f'run/{arm}/{panel}/reduction.json')['counts']
                   for panel in ('dev', 'exact', 'lexical')}
four = counts['FOUR_VIEW']
checks = dict(dev_memory=four['dev']['memory']['correct'] >= 15,
              exact_memory=four['exact']['correct'] >= 15,
              habit=four['dev']['addition']['correct_action'] >= 30,
              act=four['dev']['addition']['adherence'] >= 31,
              lexical_families=all(four['lexical']['by_family'][str(family)]['correct'] >= 15 for family in range(3)))
watch = json.loads(Path('/tmp/astra_interleaved_watch_terminal_20260912.json').read_text())
assert watch['success'] and watch['signals_attempted'] == []
result = dict(analysis='Main custody and sealed-reducer integration, not independent raw recount',
              capsule_sha256=validation['sha256'], files=len(payloads), seed=plan['seed'],
              counts=counts, four_gate_checks=checks, recorded_gate_pass=all(checks.values()),
              raw_review_pending=True, automatic_progression=False,
              total_calls=plan['total_calls'], confirmation_calls=plan['confirmation_calls'],
              accounting=plan['accounting'], memory_target_mass_fraction=plan['memory_target_mass_fraction'],
              controller_seconds=terminal['reserved_seconds'], worker_seconds=terminal['worker_reserved_seconds'],
              full_release=release, watchdog=watch,
              limits='One root0 authored-material positive diagnostic. Same16facts acrosslexical48, no FOUR advantage, no isolated temporal effect, operational sleep, parenting, G3, freeze or H1/H2 qualification.')
print(json.dumps(result, sort_keys=True, indent=2))
