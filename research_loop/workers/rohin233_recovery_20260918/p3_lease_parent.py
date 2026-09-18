"""Continue the existing P3 parent ledger through the reported lease horizon."""

import argparse
import copy
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import types

import p3_incremental


HERE = p3_incremental.HERE
END_UNIX = 1790359200
POLICY = 'R233_P3_REPORTED_LEASE_PARENT_CONTINUATION_V1'


def renewed_config(original, deadline):
    if deadline <= original['hard_end_unix'] or deadline > END_UNIX:
        raise ValueError('only_reported_lease_horizon_extension')
    result = copy.deepcopy(original)
    result['hard_end_unix'] = deadline
    return result


def authorized_wall_validator(validator, original):
    historical = copy.deepcopy(original)
    renewed = renewed_config(historical, END_UNIX)

    def validate(candidate):
        if candidate != historical and candidate != renewed:
            raise ValueError('only_exact_P3_historical_or_renewed_config')
        return validator(renewed)

    return validate


def load_on_renewed_wall():
    repair = p3_incremental.previous.previous.repair
    previous_adapt = repair.adapt

    def adapt(frozen, original):
        frozen.parent.validate = authorized_wall_validator(frozen.parent.validate, original)
        return previous_adapt(frozen, original)

    repair.adapt = adapt
    try:
        return p3_incremental.previous.load()
    finally:
        repair.adapt = previous_adapt


def bind(policy, original):
    expected = renewed_config(original, END_UNIX)
    prior_validate, prior_prompt = policy.validate, policy.prompt

    def validate(candidate):
        if candidate != expected:
            raise ValueError('deadline_only_config_delta_required')
        return prior_validate(original)

    def prompt(candidate, *arguments, **keywords):
        validate(candidate)
        return prior_prompt(original, *arguments, **keywords)

    namespace = dict(policy.tick.__globals__, validate=validate,
        prompt=lambda *arguments, **keywords: policy.prompt(*arguments, **keywords))
    policy.tick = types.FunctionType(policy.tick.__code__, namespace,
        policy.tick.__name__, policy.tick.__defaults__, policy.tick.__closure__)
    policy.validate, policy.prompt = validate, prompt
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'serve'))
    parser.add_argument('--predecessor-pid', type=int)
    parser.add_argument('--predecessor-start-ticks')
    options = parser.parse_args()
    module, policy, original, predecessor = p3_incremental.previous.load()
    config = bind(policy, original)
    manifest = dict(policy=POLICY, predecessor_manifest=predecessor,
        hard_end_unix=END_UNIX, safe_end_utc='2026-09-25T18:00:00Z',
        authority='Fable 2026-09-18 17:25Z: existing node4 lease through September26',
        scope='CPU parent only; does not renew native or wrapper deadline',
        source_sha256=p3_incremental.previous.sha(__file__),
        config_delta={'hard_end_unix': [original['hard_end_unix'], END_UNIX]},
        learner_signals=[], parent_signals=[])
    if options.action == 'validate':
        policy.validate(config)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return
    approved = json.loads((HERE / 'P3_LEASE_PARENT_MANIFEST.json').read_text())
    if manifest != approved:
        raise ValueError('exact_reviewed_parent_continuation_manifest')
    if not options.predecessor_pid or not options.predecessor_start_ticks:
        raise ValueError('exact_predecessor_required')
    process = Path('/proc') / str(options.predecessor_pid)
    descriptor = os.pidfd_open(options.predecessor_pid)
    try:
        if process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19] != options.predecessor_start_ticks:
            raise ValueError('predecessor_identity_changed')
        arguments = process.joinpath('cmdline').read_bytes().split(b'\0')
        if not any(argument.endswith(b'/p3_incremental.py') for argument in arguments):
            raise ValueError('exact_P3_CPU_predecessor')
        armed = dict(manifest, successor_pid=os.getpid(), armed_unix=time.time(),
            predecessor_pid=options.predecessor_pid,
            status='WAITING_FOR_NATURAL_CPU_PARENT_EXIT_NOT_A_LIFE_HOLD')
        (HERE / 'P3_LEASE_PARENT_ARMED.json').write_text(json.dumps(armed, indent=2) + '\n')
        while time.time() < END_UNIX:
            if select.select([descriptor], [], [], 5)[0]:
                break
        else:
            raise TimeoutError('reported_lease_horizon_reached')
    finally:
        os.close(descriptor)
    module.base.WALL = END_UNIX
    output = module.base.OWN / 'r210_parent3'
    policy.local_attempts(output / 'turns')
    original_path = output / 'CONFIG.json'
    original_read, original_sha = module.base.read, module.base.sha
    module.base.read = lambda path: config if Path(path) == original_path else original_read(path)
    module.base.sha = lambda path: p3_incremental.previous.sha(HERE / 'P3_LEASE_PARENT_MANIFEST.json') if Path(path) == original_path else original_sha(path)
    module.base.runtime = lambda: policy

    def remote(physical, request):
        if physical != 3 or request.get('op') not in ('poll', 'publish'):
            raise ValueError('existing_P3_poll_publish_only')
        endpoint_path = str(Path(p3_incremental.ENDPOINT).with_name('p3_lease_endpoint.py'))
        command = '/localhome/local-rohing/v2/venv/bin/python -B ' + endpoint_path
        result = subprocess.run(['bash', str(module.base.REPO / 'gpu/a40r_ssh.sh'), command],
            input=json.dumps(dict(request, physical=physical)), capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(result.stderr[-1200:])
        return json.loads(result.stdout)

    def record(event):
        with (HERE / 'P3_TRANSPORT.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')

    module.remote = p3_incremental.previous.recover_poll(remote, END_UNIX, record)
    record(dict(kind='P3_LEASE_PARENT_ACTIVE', observed_unix=time.time(),
        pid=os.getpid(), hard_end_unix=END_UNIX, learner_signals=[]))
    module.serve(3)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()
