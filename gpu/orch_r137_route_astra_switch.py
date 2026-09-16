"""Forward-only R121 route-parent model choice, without child restarts or retries."""

import argparse
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import signal
import tempfile
import time

from gpu import orch_r121_route_astra_fast as fast

astra = fast.prior
transport = fast.transport
require = transport.require
ROOT = '/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1'
OLD_CONFIG = '/localhome/local-rohing/orch_r127_f1_substitution_20260915_v1/F1/CONFIG.json'
OLD_SHA = 'aa2abe0e496c5334f68ccc8c21d8108c378fd1a3814341de7dd1e66a6a0295d4'
PLAN_SHA = '9a5537780508ac451125d9bc4afde85a45a021fb762498efdf05c070513b884e'
RUNTIME = Path('/data/home/rohing/courier/runtime')
LEDGER = 'parent_astra_r137'


def source_pins():
    pins = transport.source_pins()
    for module in (fast, astra, astra.existing, astra.slots):
        path = Path(module.__file__).resolve()
        pins[str(path.relative_to(transport.ROOT))] = transport.sha(path)
    pins[str(Path(__file__).resolve().relative_to(transport.ROOT))] = transport.sha(__file__)
    return pins


def sequence(name):
    match = re.fullmatch(r'([0-9]{6})_F1_C([0-9]{4})\.request\.json', name)
    require(match is not None, 'exact_F1_request_name')
    return int(match.group(1)), int(match.group(2))


def eligible(name, boundary, mtime, already_claimed=False, already_answered=False):
    number, cycle = sequence(name)
    return (number > boundary['highest_request'] and cycle >= boundary['highest_cycle']
        and mtime >= boundary['observed_unix'] and not already_claimed and not already_answered)


def consumer_ready(plan):
    require(plan.get('provider') == astra.MODEL and not plan.get('parent_model_substitution'),
        'consumer_Astra_authorization_required_before_broker')


def snapshot(store):
    script = f'''
import hashlib,json,time
from pathlib import Path
root=Path({ROOT!r}); config_path=Path({OLD_CONFIG!r})
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert digest(config_path)=={OLD_SHA!r}, 'old_config_binding'
assert digest(root/'R121_INDEPENDENT_PLAN_V2.json')=={PLAN_SHA!r}, 'live_child_plan'
plan=json.loads((root/'R121_INDEPENDENT_PLAN_V2.json').read_text())
assert not (root/'R121_INDEPENDENT_TERMINAL.json').exists(), 'child_already_terminal'
retired=json.loads((root/'parent_claude/RETIRED_R121_20260916.json').read_text())
assert retired['status']=='RETIRED' and retired['child_restart'] is False, 'retired_provider_only'
proc=Path('/proc')/str(retired['pid'])
if proc.exists():
 fields=(proc/'stat').read_text().split(')',1)[1].split()
 assert fields[19]!=retired['start_ticks'] or fields[0]=='Z', 'old_provider_still_alive'
names=sorted(path.name for path in (root/'parent_queue').glob('*.request.json'))
claims=list((root/'parent_claude').glob('*.claim'))
assert all((path/'PUBLISHED.json').exists() for path in claims), 'old_claim_inflight'
print(json.dumps(dict(config=json.loads(config_path.read_text()),requests=names,consumer_plan=dict(provider=plan.get('provider'),parent_model_substitution=plan.get('parent_model_substitution')),
 observed_unix=time.time(),old_claims=len(claims),retirement_sha256=digest(root/'parent_claude/RETIRED_R121_20260916.json'))))
'''
    return transport.loads(store.shell('python3 -c ' + shlex.quote(script)).stdout)


def new_config(old, old_claims):
    require(old['remote_root'] == ROOT and old['branch'] == 'F1' and old['family'] == 'route', 'same_child')
    require(type(old_claims) is int and 0 <= old_claims < old['max_parent_calls'], 'remaining_original_cap')
    config = dict(old)
    for key in ('predecessor_config', 'terminal_binding', 'allowed_substitute_models'):
        config.pop(key, None)
    config.update(queue_transport='ssh', provider_lock_scope='shared', parent_effort='low',
        max_output_tokens=512, max_parent_calls=old['max_parent_calls']-old_claims,
        source_files=transport.source_pins())
    return config


def prepare(directory, repository):
    directory = Path(directory).resolve()
    require(directory.is_relative_to(RUNTIME), 'data_runtime_only')
    require(not directory.exists(), 'fresh_switch_directory')
    store = transport.Store(repository)
    current = snapshot(store)
    consumer_ready(current['consumer_plan'])
    numbers = [sequence(name) for name in current['requests']]
    require(bool(numbers), 'existing_child_queue')
    config = new_config(current['config'], current['old_claims'])
    transport.validate_config(config)
    boundary = dict(schema='R137_F1_FORWARD_ONLY_V1', root=ROOT,
        observed_unix=current['observed_unix'], highest_request=max(number for number, cycle in numbers),
        highest_cycle=max(cycle for number, cycle in numbers), old_config_sha256=OLD_SHA,
        old_claims=current['old_claims'], original_parent_cap=current['config']['max_parent_calls'],
        new_parent_cap=config['max_parent_calls'], plan_sha256=PLAN_SHA,
        retirement_sha256=current['retirement_sha256'], source_files=source_pins(),
        old_requests_sha256=transport.digest(current['requests']), child_restart=False,
        replay=False, requested_model=astra.MODEL, ledger=LEDGER)
    directory.mkdir(parents=True)
    transport.write(directory/'CONFIG.json', config)
    transport.write(directory/'BOUNDARY.json', boundary)
    print(json.dumps(boundary, sort_keys=True))


def data_evaluator():
    source = inspect.getsource(astra.evaluate)
    before = "directory.resolve().is_relative_to(Path('/tmp'))"
    require(source.count(before) == 1, 'exact_scratch_location_seam')
    source = source.replace(before, "directory.resolve().is_relative_to(Path('/data/home/rohing/courier/runtime'))")
    namespace = dict(astra.evaluate.__globals__)
    exec(compile(source, __file__+':data_scratch_only', 'exec'), namespace)
    return namespace['evaluate']


def evaluate(request, directory, deadline, **kwargs):
    result = data_evaluator()(request, directory, deadline, runner=fast.runner(), **kwargs)
    result.update(parent_provider_era='R137_PROSPECTIVE_ASTRA', parent_effort='low',
        max_output_tokens=512, provider_timeout_seconds=20, historical_turn_replayed=False)
    transport.write(Path(directory)/'MODEL_CHOICE.json', dict(requested_model=astra.MODEL,
        actual_model=result.get('actual_model'), status=result['status'], attempts_maximum=1,
        provider_era='R137_PROSPECTIVE_ASTRA', historical_turn_replayed=False))
    return result


def processor():
    source = inspect.getsource(transport.process_request)
    before = "ledger = root / 'parent_claude'"
    require(source.count(before) == 1, 'exact_separate_ledger_seam')
    source = source.replace(before, "ledger = root / 'parent_astra_r137'")
    namespace = dict(transport.process_request.__globals__, evaluate=evaluate, MODEL=astra.MODEL)
    exec(compile(source, __file__+':new_ledger', 'exec'), namespace)
    return namespace['process_request']


def gate(store, name, boundary):
    sequence(name)
    if sequence(name)[0] <= boundary['highest_request']:
        return False
    root = Path(ROOT)
    identifier = name.removesuffix('.request.json')
    old_claim = store.exists(root/'parent_claude'/(identifier+'.claim'))
    new_claim = store.exists(root/LEDGER/(identifier+'.claim'))
    answered = store.exists(root/'parent_queue'/(identifier+'.response.json'))
    mtime = float(store.shell('stat -c %Y '+shlex.quote(str(root/'parent_queue'/name))).stdout)
    return eligible(name, boundary, mtime, old_claim or new_claim, answered)


def serve(directory, repository, prompt_root, principles):
    directory = Path(directory).resolve()
    require(directory.is_relative_to(RUNTIME) and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'data_CPU_controller')
    config = transport.loads((directory/'CONFIG.json').read_text())
    boundary = transport.loads((directory/'BOUNDARY.json').read_text())
    publication = transport.loads((directory/'PUBLICATION.json').read_text())
    require(publication['boundary_sha256'] == transport.sha(directory/'BOUNDARY.json')
        and publication['config_sha256'] == transport.sha(directory/'CONFIG.json')
        and publication['builder_published'] is True, 'published_exact_switch')
    require(source_pins() == boundary['source_files'], 'immutable_broker_source')
    require(boundary['root'] == ROOT and boundary['ledger'] == LEDGER
        and boundary['old_config_sha256'] == OLD_SHA and boundary['plan_sha256'] == PLAN_SHA,
        'exact_branch_boundary')
    require(boundary['new_parent_cap'] == config['max_parent_calls']
        and boundary['old_claims']+config['max_parent_calls'] == boundary['original_parent_cap'], 'no_budget_reset')
    transport.validate_config(config)
    require(transport.sha(principles) == config['principles_sha256'], 'same_principles')
    launch = dict(authorized=True, authorization='BUILDER_PUBLISHED_PAIRED_ASTRA',
        config_sha256=transport.digest(config), source_reference=publication,
        not_before_unix=boundary['observed_unix'])
    astra.authorize(config, launch, time.time())
    store = transport.Store(repository)
    consumer_ready(snapshot(store)['consumer_plan'])
    ledger = Path(ROOT)/LEDGER
    store.shell('mkdir -p '+shlex.quote(str(ledger)))
    lock = ledger/'RUNNER.lock'
    require(store.shell('mkdir '+shlex.quote(str(lock)), check=False).returncode == 0, 'single_prospective_broker')
    store.copy(directory/'BOUNDARY.json', 'NODE:'+str(ledger/'BOUNDARY.json'))
    require(store.hash(ledger/'BOUNDARY.json') == transport.sha(directory/'BOUNDARY.json'), 'native_boundary_join')
    def stop(signum, frame):
        raise KeyboardInterrupt('broker_only_stop')
    signal.signal(signal.SIGTERM, stop)
    process = processor()
    transport.write(directory/'START.json', dict(pid=os.getpid(), started_unix=time.time(),
        boundary_sha256=transport.sha(directory/'BOUNDARY.json'), first_eligible_request=boundary['highest_request']+1,
        provider=astra.MODEL, child_restart=False))
    try:
        while time.time() < config['deadline_unix']:
            if store.exists(Path(ROOT)/'R121_INDEPENDENT_TERMINAL.json'):
                break
            require(store.hash(Path(ROOT)/'R121_INDEPENDENT_PLAN_V2.json') == PLAN_SHA, 'child_plan_unchanged')
            names = store.shell('find '+shlex.quote(str(Path(ROOT)/'parent_queue'))+
                ' -maxdepth 1 -type f -name "*.request.json" -printf "%f\\n"').stdout.splitlines()
            for name in sorted(names):
                if not gate(store, name, boundary):
                    continue
                with tempfile.TemporaryDirectory(prefix='packet_', dir=directory) as temporary:
                    status = process(store, config, launch, name, Path(temporary), prompt_root, principles)
                print(json.dumps(dict(request=name, status=status, requested_model=astra.MODEL,
                    observed_unix=time.time(), provider_era='R137_PROSPECTIVE_ASTRA')), flush=True)
            time.sleep(.5)
    finally:
        store.shell('rmdir '+shlex.quote(str(lock)), check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'serve'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, default=transport.MUTABLE_PROMPT_ROOT)
    parser.add_argument('--principles', type=Path, default=transport.ROOT/'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
    arguments = parser.parse_args()
    if arguments.phase == 'prepare':
        prepare(arguments.directory, arguments.repository)
    else:
        serve(arguments.directory, arguments.repository, arguments.prompt_root, arguments.principles)


if __name__ == '__main__':
    main()
