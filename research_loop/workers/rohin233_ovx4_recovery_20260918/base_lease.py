"""Lease-bound frozen base with complete transcript and genuine pending score."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import inspect
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from research_loop.workers.rohin221_continuous_caption_20260918.adapters import BaseBackend, SocketScorer
from research_loop.workers.rohin221_continuous_caption_20260918.controller import Controller, Plan, file_ref, write
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import generation_origin
from research_loop.workers.rohin221_continuous_caption_20260918.run_base_cohort import BASE_ROOT, prepare_assets
from research_loop.workers.rohin233_ovx4_recovery_20260918.base_epoch import migrate, retained_summary, read, run_scorer
from research_loop.workers.rohin233_kept_age_probe_20260918.parent_bridge import envelope


class ParentedScorer(SocketScorer):
    def submit(self, request):
        response = super().submit(request)
        origin = generation_origin(request['source'], request['think_source'])
        generation = read(request['source']['generation']['path'])
        config = dict(condition=self.binding['condition'], rule_sha256=self.binding['rule_sha256'])
        result, parent = envelope(dict(origin=origin, metrics=request['metrics']), response, generation['request'], config)
        write(self.parent_root / (request['request_id']+'.json'), dict(unix=time.time(), **parent,
            actual_raw_score_receipt_sha256=response['receipt_sha256'], rendering='pending_actual_generation'))
        return result


def wait(path,deadline):
    while not path.exists():
        assert time.time()<deadline
        time.sleep(.1)
    return read(path)


def player(root,config):
    original=Path(config['original_root'])
    unused,rule,unused_manifest,scenes=prepare_assets(original)
    backend=BaseBackend(BASE_ROOT)
    identity=backend.state_receipt()
    write(root/'MODEL_WARM.json',dict(unix=time.time(),pid=os.getpid(),physical=config['player_physical'],
        deadline_unix=config['deadline_unix'],session_owner=False,optimizer_created=False))
    boundary=wait(root/'BOUNDARY_READY.json',config['deadline_unix'])
    previous=read(root/'PRESERVED_CONTROLLER.private.json')
    prior_scorer=read(root/'PRESERVED_SCORER.private.json')
    plan=Plan(**dict(previous['binding']['plan'],opportunities=1000000))
    binding=deepcopy(previous['binding']);binding['plan']=asdict(plan)
    binding['controller']=file_ref(inspect.getsourcefile(Controller));binding['parser']=file_ref(inspect.getsourcefile(extract_batches))
    state,scorer=migrate(previous,prior_scorer,identity,binding,os.environ['CUDA_VISIBLE_DEVICES'],config['epoch'])
    write(root/'TRANSITION.private.json',dict(opportunity=previous['opportunity'],previous_binding=previous['binding'],
        previous_backend=previous['backend_state'],predecessor_think_origin=generation_origin(previous['think_source']) if previous['stage']=='ACT' else None))
    write(root/'MIGRATED_SCORER.private.json',scorer)
    write(root/'BINDING.json',dict(controller=binding,backend=identity))
    wait(root/'scorer/LISTENING.json',config['deadline_unix'])
    assert read(original/'player/private/state.json')['pending']['request']['request_id']==boundary['ACT_request_id']
    write(original/'player/private/state.json',state)
    service=ParentedScorer(root/'scorer/base.sock',dict(rule_sha256=plan.rule_sha256,top_k=50,reference_count=64,
        relevance=True,novelty=True,condition=plan.condition),output=original/'scorer')
    service.parent_root=root/'parent'
    with Controller(original/'player',plan,backend,service,scenes,extract_batches) as controller:
        write(root/'LOADED.json',dict(unix=time.time(),pid=os.getpid(),physical=config['player_physical'],
            deadline_unix=config['deadline_unix'],runtime_epoch=config['epoch'],preserved=retained_summary(state,scorer),
            boundary=boundary,history_reset=False,learning=False,optimizer_created=False))
        while time.time()<config['deadline_unix'] and controller.state['completed_opportunities']<plan.opportunities:
            before=len(controller.state['events'])
            controller.step()
            if len(controller.state['events'])>before:
                write(root/'LATEST_ATTEMPT.json',controller.state['events'][-1])
        write(root/'FINISHED.json',dict(unix=time.time(),deadline_unix=config['deadline_unix']))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    args=parser.parse_args();config=read(args.config);root=Path(config['root'])
    from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import validate
    from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import verify_files
    validate(config)
    verify_files(Path(config['source_root']),read(root/'SOURCE_MANIFEST.json'))
    if config['mode']=='player':
        player(root,config)
    else:
        wait(root/'BOUNDARY_READY.json',config['deadline_unix'])
        config['input_files']={'PRESERVED_SCORER.private.json':file_ref(root/'PRESERVED_SCORER.private.json')['sha256']}
        run_scorer(root,config)
