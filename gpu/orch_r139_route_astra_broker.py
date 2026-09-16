"""R137 future-only Astra transport bound to the actual R139 resumed consumer."""

import argparse
import inspect
import json
from pathlib import Path
import shlex

from gpu import orch_r137_route_astra_switch as prior


HANDOFF = '/localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt2'
ORIGINAL_SNAPSHOT = prior.snapshot
ORIGINAL_PINS = prior.source_pins


def validate_consumer(report):
    prior.require(report['provider'] == prior.astra.MODEL and report['substitution'] is None,
        'truthful_Astra_consumer_required')
    prior.require(report['mode'] == 'R139_SAME_LOGICAL_LIFE_ASTRA_SEGMENT' and
        report['actual_checkpoint'] == report['expected_checkpoint'], 'exact_resumed_child_required')
    prior.require(report['next_cycle'] == report['expected_cycle'] and report['source_verified']
        and report['actor_command_verified'] and report['logical_life_reset'] is False,
        'live_saved_state_consumer_required')


def snapshot(store):
    previous = ORIGINAL_SNAPSHOT(store)
    script = f'''
import hashlib,json
from pathlib import Path
stage=Path({HANDOFF!r}); root=Path({prior.ROOT!r})
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
ready=json.loads((stage/'READY.json').read_text())
release=json.loads((stage/'RELEASED.json').read_text())
assert digest(release['boundary']['path'])==release['boundary']['sha256']
boundary=json.loads(Path(release['boundary']['path']).read_text())
plan=json.loads((stage/'RESUME_PLAN.json').read_text())
actor=json.loads((root/'R139_INDEPENDENT_ACTOR_READY.json').read_text())
checkpoint=json.loads(Path(boundary['checkpoint']['path']).read_text())
assert digest(boundary['checkpoint']['path'])==boundary['checkpoint']['sha256']
proc=Path('/proc')/str(actor['pid'])
argv=(proc/'cmdline').read_bytes().split(b'\\0')
fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
assert str(actor['process'][2])==fields[19] and fields[0]!='Z'
print(json.dumps(dict(provider=plan['provider'],substitution=plan.get('parent_model_substitution'),
 mode=actor['mode'],actual_checkpoint=actor['adapter'],expected_checkpoint=checkpoint['adapter'],
 next_cycle=actor['next_cycle'],expected_cycle=boundary['next_cycle'],logical_life_reset=plan['logical_life_reset'],
 source_verified=digest(stage/'handoff.py')==ready['source_sha256'],
 actor_command_verified=str(stage/'handoff.py').encode() in argv and b'resume' in argv and str(stage).encode() in argv)))
'''
    report = json.loads(store.shell('python3 -c ' + shlex.quote(script)).stdout)
    validate_consumer(report)
    previous['consumer_plan'] = dict(provider=report['provider'], parent_model_substitution=None)
    return previous


def source_pins():
    result = ORIGINAL_PINS()
    path = Path(__file__).resolve()
    result[str(path.relative_to(prior.transport.ROOT))] = prior.transport.sha(path)
    return result


def gate(store, name, boundary):
    prior.sequence(name)
    if prior.sequence(name)[0] <= boundary['highest_request']:
        return False
    root = Path(prior.ROOT)
    identifier = name.removesuffix('.request.json')
    claimed = store.exists(root/'parent_claude'/(identifier+'.claim')) or store.exists(root/prior.LEDGER/(identifier+'.claim'))
    answered = store.exists(root/'parent_queue'/(identifier+'.response.json'))
    path = root/'parent_queue'/name
    script = 'from pathlib import Path; print(Path('+repr(str(path))+').stat().st_mtime_ns/1000000000)'
    mtime = float(store.shell('python3 -c ' + shlex.quote(script)).stdout)
    return prior.eligible(name, boundary, mtime, claimed, answered)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'serve'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, default=prior.transport.MUTABLE_PROMPT_ROOT)
    parser.add_argument('--principles', type=Path,
        default=prior.transport.ROOT/'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
    arguments = parser.parse_args()
    prior.snapshot = snapshot
    prior.source_pins = source_pins
    prior.gate = gate
    if arguments.phase == 'prepare':
        prior.prepare(arguments.directory, arguments.repository)
    else:
        source = inspect.getsource(prior.serve)
        prior.require(source.count('child_restart=False') == 1, 'exact_logical_identity_receipt_site')
        source = source.replace('child_restart=False', 'logical_life_reset=False, consumer_process_handoff=True')
        namespace = dict(prior.serve.__globals__)
        exec(compile(source, __file__+':explicit_process_handoff_receipt', 'exec'), namespace)
        namespace['serve'](arguments.directory, arguments.repository, arguments.prompt_root, arguments.principles)


if __name__ == '__main__':
    main()
