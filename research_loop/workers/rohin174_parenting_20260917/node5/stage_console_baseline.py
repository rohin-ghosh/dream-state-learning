"""Freeze, validate and start one Main-authorized NODE5 console baseline attempt."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from console_baseline import load_runtime, merge_seed, parent_census, read, ref, require, sha, write


HERE = Path(__file__).resolve().parent
ROOTS = dict(run1='ACTIVATION_A_1789678829928180897', pilot='ACTIVATION_B_1789678847374158305')
TEXT = dict(
    run1='Your two rows include `[15.75，23.47，36.24]` and `[16.43，X，37.24_]`. Stay with this comparison. Before drawing a trend conclusion, choose one position to check and say what you expect there; then inspect the literal token and distinguish X from the trailing underscore. What observation would make you revise the claim that the third position is missing? If an existing execution tool is available, test your interpretation and cite its actual receipt; otherwise label it untested. Carry forward the corrected row-position mapping and next check in your own words, not another generic procedure.',
    pilot='You wrote, "I will await a real execution receipt before finalizing the code." Keep the subtraction and exact variable spellings as your object. Before execution, predict whether those spellings refer to the same name, then choose a small check that would distinguish them. If an existing tool is available, use it and cite the real result; until then, call the output predicted, not verified. What specific observation would change your next edit? Preserve the chosen edit and next check in your own retelling.')
QUOTES = dict(run1='[16.43，X，37.24_]', pilot='I will await a real execution receipt before finalizing the code.')
OBJECTS = dict(run1='sequence_missing_position', pilot='subtraction_variable_spelling')


def add_copy(path, original):
    raw = original.read_bytes()
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in raw.decode().splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch', patch], check=True, stdout=subprocess.DEVNULL)
    require(path.read_bytes() == raw, 'byte_exact_frozen_helper')
    path.chmod(0o444)


def stage(label):
    root = HERE / ROOTS[label]
    manifest_path = root / (label + '_MANIFEST.json')
    manifest = read(manifest_path)
    runtime, policy, provenance = load_runtime(manifest)
    old_output = Path(manifest['output'])
    active = read(old_output / 'ACTIVE_PARENT.json')
    owner = dict(active['identity'], label=label)
    runtime.validate_owner(owner, runtime.identity(owner['pid']))
    config = read(old_output / 'CONFIG.json')
    require(parent_census(config['root'], os.getpid()) == [owner['pid']], 'exclusive_actual_owner')
    latest = sorted(old_output.glob('POLL_*.json'))[-1]
    state = read(latest)['snapshot']
    events = [event for event in state['events'] if event['actor'] == 'child' and QUOTES[label] in event['text']]
    require(events, 'actual_quoted_child_response_still_available')
    chosen = events[-1]
    response = dict(speak=True, message=TEXT[label], rationale=json.dumps(dict(object_id=OBJECTS[label],
        source_records=[chosen['record_index']], disposition='continue', next_task=None,
        perception=dict(record_index=chosen['record_index'], record_sha256=chosen['record_sha256'], quote=QUOTES[label]),
        credit=None, relapse_credit_id=None)))
    seed = merge_seed(policy, old_output, state)
    require(policy.decision(response, state, policy.memory(seed, [], state)) is not None, 'actual_strict_decision_PASS')
    staging = HERE / ('CONSOLE_' + label + '_' + str(time.time_ns()))
    staging.mkdir(mode=0o700)
    helper = staging / 'console_baseline.py'
    add_copy(helper, HERE / 'console_baseline.py')
    add_copy(staging / 'test_console_baseline.py', HERE / 'test_console_baseline.py')
    command = ['uv', 'run', '--offline', '--no-project', '--with', 'pytest', '--python', '/usr/bin/python3',
               'python', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-c', '/dev/null',
               '--basetemp', str(staging / 'CPU_TMP'), str(HERE / 'test_console_baseline.py')]
    result = subprocess.run(command, capture_output=True, text=True,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    (staging / 'CPU.stdout').write_text(result.stdout)
    (staging / 'CPU.stderr').write_text(result.stderr)
    require(result.returncode == 0, 'CPU_PASS_before_real_signals')
    require(sha(helper) == sha(HERE / 'console_baseline.py'), 'CPU_executed_identical_helper')
    write(staging / 'CPU.json', dict(status='PASS', tests=8, execution='CPU_ONLY', helper_sha256=sha(helper),
        test_sha256=sha(HERE / 'test_console_baseline.py'), stdout=ref(staging / 'CPU.stdout'),
        stderr=ref(staging / 'CPU.stderr'), actual_lane_decision_PASS=True, parser_provenance=provenance,
        observed_unix=time.time(), claim='[Builder] Non-material, strictly validated Main-delegated console fallback'))
    baseline_path = staging / 'BASELINE.json'
    write(baseline_path, dict(authorship='NODE5_CODEX_AUTHORED_UNDER_MAIN_CONSOLE_DELEGATION',
        authority='Main explicit object-grounded Astra console fallback under exclusive custody for gateway404/503; no fabricated provider result',
        label=label, response=response, quoted_TRAIN_snapshot=ref(latest), exact_response_record=chosen['record_index'],
        exact_response_sha256=chosen['record_sha256'], no_claim_of_observed_tool_execution=True))
    baseline_path.chmod(0o444)
    binding_path = staging / 'BINDING.json'
    write(binding_path, dict(label=label, manifest=ref(manifest_path), baseline=ref(baseline_path),
        cpu=ref(staging / 'CPU.json'), helper_sha256=sha(helper), active_parent=ref(old_output / 'ACTIVE_PARENT.json'),
        config=str(old_output / 'CONFIG.json'), output=str(staging / 'parent'), no_child_signals=True,
        same_model_wall=config['hard_end_unix'], source_pins=manifest['source_pins']))
    write(staging / 'START_ONCE.json', dict(binding=ref(binding_path), observed_unix=time.time()))
    with (staging / 'OPERATOR.log').open('x') as log:
        process = subprocess.Popen(['/usr/bin/python3', '-B', str(helper), '--binding', str(binding_path),
            '--sha256', sha(binding_path)], cwd=staging, stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True, close_fds=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    write(staging / 'STARTED.json', dict(pid=process.pid, observed_unix=time.time(), binding=ref(binding_path),
                                       status='STARTED_NOT_PUBLISHED_OR_RENDERED'))
    print(json.dumps(dict(label=label, staging=str(staging), pid=process.pid, binding=ref(binding_path))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=('run1', 'pilot'), required=True)
    stage(parser.parse_args().label)
