"""Scratch-only binding around the frozen F4 Astra broker; check never dispatches."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import time
from types import FunctionType, SimpleNamespace


HANDOFF = Path('/tmp/orch_r139_F4_vm_v1/gpu/orch_r139_grid_astra_handoff.py')
HANDOFF_SHA = 'adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778'
PLAN_SHA = '21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546'
RUNTIME = Path('/data/home/rohing/courier/runtime')
SCRATCH = RUNTIME / 'orch_r139_F4_broker_scratch_v1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_ref():
    return dict(path=str(Path(__file__).resolve()), sha256=sha(__file__))


def bind(function, **namespace):
    bound = FunctionType(function.__code__, dict(function.__globals__, **namespace),
                         function.__name__, function.__defaults__, function.__closure__)
    bound.__kwdefaults__ = function.__kwdefaults__
    return bound


def literal(function, before, after):
    require(sum(value == before for value in function.__code__.co_consts) == 1, 'exact_single_literal_site')
    code = function.__code__.replace(co_consts=tuple(after if value == before else value
                                                     for value in function.__code__.co_consts))
    result = FunctionType(code, function.__globals__, function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def runtime_path(path):
    path = Path(path)
    base = RUNTIME.resolve(strict=True)
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(RUNTIME), 'courier_runtime_only')
    relative = path.relative_to(RUNTIME)
    current = RUNTIME
    for component in relative.parts:
        current = current / component
        require(not current.is_symlink(), 'no_scratch_symlink')
    require(path.resolve().is_relative_to(base), 'no_runtime_escape')
    return path.resolve()


def private_scratch():
    path = runtime_path(SCRATCH)
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700, 'private_owned_scratch')
    return path


def load_runtime():
    require(sha(HANDOFF) == HANDOFF_SHA, 'frozen_handoff_source')
    spec = importlib.util.spec_from_file_location('r139_scratch_frozen_handoff', HANDOFF)
    handoff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handoff)
    return handoff, handoff.load_broker_runtime()


def authorize(handoff, plan, publication, plan_sha, mode, now):
    handoff.authorize(plan, publication, plan_sha, mode, now)
    require(publication.get('scratch_wrapper') == source_ref()
            and publication.get('raw_scratch_root') == str(SCRATCH)
            and publication.get('shared_HTTP_slots_unchanged') is True, 'Main_published_scratch_binding')


def broker_builder(handoff, scratch):
    def guarded_authorize(plan, publication, plan_sha, mode, now):
        return authorize(handoff, plan, publication, plan_sha, mode, now)
    original_builder = bind(handoff.broker_functions, authorize=guarded_authorize)

    def build(http, boundary, plan, publication, plan_sha):
        view = SimpleNamespace(**vars(http))
        view.evaluate = literal(http.evaluate, '/tmp', str(scratch))
        serving = original_builder(view, boundary, plan, publication, plan_sha)
        serving = literal(serving, '/tmp', str(scratch))
        return literal(serving, '/', str(scratch))
    return build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('check', 'broker'))
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--publication', type=Path)
    args = parser.parse_args()
    require(sha(__file__) == args.expected_self_sha256 and sys.dont_write_bytecode, 'immutable_no_bytecode_command')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_broker_only')
    scratch = runtime_path(SCRATCH)
    if args.mode == 'check':
        handoff, http = load_runtime()
        serving = broker_builder(handoff, scratch)(http, dict(after_parent=319, next_cycle=106),
            dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        require(callable(serving), 'pinned_adapter_compiles')
        print(json.dumps(dict(status='CPU_COMPILED_NO_DISPATCH', wrapper=source_ref(),
            raw_scratch_root=str(SCRATCH), changed_literal_sites=3, shared_HTTP_slots_unchanged=True,
            provider_calls=0, queue_reads=0, claims_created=0, scratch_created=False), sort_keys=True))
        return
    require(args.plan is not None and args.publication is not None
            and args.plan_sha256 == PLAN_SHA and sha(args.plan) == PLAN_SHA, 'exact_frozen_plan_and_publication')
    runtime_path(args.plan)
    runtime_path(args.publication)
    handoff, http = load_runtime()
    plan, publication = handoff.read(args.plan.resolve()), handoff.read(args.publication.resolve())
    authorize(handoff, plan, publication, PLAN_SHA, 'broker', time.time())
    scratch = private_scratch()
    broker = bind(handoff.broker, broker_functions=broker_builder(handoff, scratch))
    broker(plan, publication, PLAN_SHA, args.publication.resolve())


if __name__ == '__main__':
    main()
