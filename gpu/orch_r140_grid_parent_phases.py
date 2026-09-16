"""Exact three-phase TRAIN routing over the frozen prospective F4 Astra broker."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace


HEAD = Path('/data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1/gpu/orch_r139_grid_head_fields.py')
HEAD_SHA = '2401d5708abec95e655bc572cb55122b507f076617eea868526f0312ca0a9262'
PHASES = ('experience', 'open_turn', 'presleep_metacognition')
FLOOR = 324


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_ref():
    return dict(path=str(Path(__file__).resolve()), sha256=sha(__file__))


def dependencies():
    require(sha(HEAD) == HEAD_SHA, 'frozen_head_wrapper')
    spec = importlib.util.spec_from_file_location('r140_frozen_head', HEAD)
    head = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(head)
    return head, *head.dependencies()


def phase_predicate(handoff):
    def prospective(request, boundary, *, now, disposed=False):
        if not isinstance(request, dict) or not re.fullmatch(r'P[0-9]{4,}', request.get('id', '')):
            return False
        payload = request.get('payload', {})
        return (not disposed and int(request['id'][1:]) > max(FLOOR, boundary['after_parent'])
            and payload.get('cycle', -1) >= boundary['next_cycle']
            and payload.get('phase') in PHASES and payload.get('life_id') == 'F4_FABLE'
            and payload.get('game') == 'grid' and payload.get('task_provenance', {}).get('split') == 'TRAIN'
            and type(request.get('lane_deadline_unix')) in (int, float)
            and now < min(request['lane_deadline_unix'] - 30, handoff.TRAIN_END))
    return prospective


def authorize(head, scratch, handoff, plan, publication, plan_sha, mode, now, floor):
    head.authorize(scratch, handoff, plan, publication, plan_sha, mode, now, floor)
    require(floor == FLOOR and publication.get('phase_wrapper') == source_ref()
            and publication.get('allowed_TRAIN_phases') == list(PHASES)
            and publication.get('P0324_preserved_no_retry') is True
            and publication.get('prompt_text_unchanged') is True, 'Main_exact_phase_routing_publication')
    previous = publication['previous_publication']
    archived = scratch.runtime_path(Path(previous['path']))
    require(sha(archived) == previous['sha256'], 'immutable_pre_revocation_publication')


def broker_builder(head, scratch, handoff, http):
    view = SimpleNamespace(**dict(vars(handoff),
        broker_functions=scratch.bind(handoff.broker_functions, prospective=phase_predicate(handoff))))
    def guarded_authorize(current_scratch, current_handoff, plan, publication, plan_sha, mode, now, floor):
        return authorize(head, current_scratch, current_handoff, plan, publication, plan_sha, mode, now, floor)
    factory = scratch.bind(head.broker_builder, authorize=guarded_authorize)
    return factory(scratch, view, http, FLOOR)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('check', 'broker'))
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--publication', type=Path)
    args = parser.parse_args()
    require(sha(__file__) == args.expected_self_sha256 and sys.dont_write_bytecode, 'immutable_no_bytecode_command')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    if args.mode == 'check':
        head, scratch, handoff, http = dependencies()
        broker_builder(head, scratch, handoff, http)
        print(json.dumps(dict(source=source_ref(), head_wrapper=dict(path=str(HEAD), sha256=HEAD_SHA),
            phases=list(PHASES), after_parent=FLOOR, provider_calls=0, prompt_changes=0)))
        return
    require(args.plan is not None and args.publication is not None, 'explicit_Main_publication')
    head, scratch, handoff, http = dependencies()
    require(args.plan_sha256 == scratch.PLAN_SHA and sha(args.plan) == scratch.PLAN_SHA, 'exact_frozen_plan')
    scratch.runtime_path(args.plan)
    scratch.runtime_path(args.publication)
    plan, publication = handoff.read(args.plan.resolve()), handoff.read(args.publication.resolve())
    authorize(head, scratch, handoff, plan, publication, scratch.PLAN_SHA, 'broker', time.time(), FLOOR)
    scratch.private_scratch()
    broker = scratch.bind(handoff.broker, broker_functions=broker_builder(head, scratch, handoff, http))
    broker(plan, publication, scratch.PLAN_SHA, args.publication.resolve())


if __name__ == '__main__':
    main()
