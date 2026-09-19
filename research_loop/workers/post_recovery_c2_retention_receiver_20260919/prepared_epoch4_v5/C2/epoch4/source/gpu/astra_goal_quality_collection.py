"""Readonly quality successor: reuse original attempts, teach only four new units.

No baseline, correction-diagnostic, evaluation, encoder, optimizer or fit path.
Prepare and assembly are CPU-only. Native collection uses portable frozen37ec.
"""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import astra_goal_scale_collection as original
from organism_v6 import experienced_event_goal_quality as quality


portable = original.portable
source = original.source
require = source.require
same = original.same
PARENT_STATE = original.PARENT_STATE
SCHEMA = 'DEV_GOAL_QUALITY_NATIVE_V1'
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_goal_quality_collection_protocol.md'
PROTOCOL_SHA = 'cf742f62dc45810caeea3ec68272a9e1a8c97d3b7c6c06f148639252ba1738f1'
ORIGINAL_PROTOCOL_SHA = 'dd1d078a01d9f547219afd23790c467ca0ccb413f3148a2af9b963b63e652f24'
NATIVE_SECONDS = 3600


def helpers():
    return dict(driver=source.file_hash(__file__), quality=source.file_hash(quality.__file__), original=original.helpers())


def load_inputs(options):
    started = time.monotonic()
    protocol = Path(__file__).resolve().parents[1]/PROTOCOL_PATH
    require(source.file_hash(protocol) == PROTOCOL_SHA, 'exact_quality_protocol_required')
    require(len(options.shard_roots) == 8 and len({str(Path(path).resolve()) for path in options.shard_roots}) == 8,
            'all_eight_distinct_original_shard_roots_required')
    first = original.load_inputs(SimpleNamespace(**dict(vars(options),shard=0)))
    require(first['binding']['state'] == PARENT_STATE and first['binding']['protocol_sha256'] == ORIGINAL_PROTOCOL_SHA,
            'original_portable_scale_source_required')
    exposures, teachings, receipts = [], {}, []
    for shard, location in enumerate(options.shard_roots):
        worlds = first['registry'][shard]
        inputs = dict(first,shard=shard,worlds=worlds,binding=dict(first['binding'],shard=shard,worlds=worlds))
        root = Path(location)
        exposure, expose_sha = original.read_stage(root/'expose','expose',inputs)
        require(sum(collection['model_calls'] for collection in exposure['collections']) == 80,
                'original_eighty_exposure_calls_per_shard_required')
        exposures.append(exposure)
        receipt = dict(shard=shard,exposure_result_sha256=expose_sha,original_binding=inputs['binding'])
        if shard in quality.REUSED_SHARDS:
            teaching, teach_sha = original.read_stage(root/'teach','teach',inputs,exposure,
                dict(exposure_result_sha256=expose_sha))
            teachings[shard] = teaching['lessons']
            receipt.update(teaching_result_sha256=teach_sha,original_curriculum_ready=teaching['curriculum_ready'],
                           original_row_count=teaching['row_count'])
        receipts.append(receipt)
    plan = quality.source_plan(exposures)
    reused = quality.reused_quality(exposures,teachings)
    binding = dict(protocol_sha256=PROTOCOL_SHA,bundle_sha256=options.bundle_sha,parent_state=PARENT_STATE,
        original_receipts=receipts,source_plan_sha256=plan['plan_sha256'],reuse_sha256=reused['reuse_sha256'],helpers=helpers())
    return dict(binding=binding,manifest=first['manifest'],exposures=exposures,teachings=teachings,plan=plan,reused=reused,
                admission_seconds=time.monotonic()-started)


def read_unit(directory, inputs, unit):
    directory = Path(directory)
    result = source.read(directory/'RESULT.json')
    require(not (directory/'FAILED.json').exists() and result['schema'] == SCHEMA and result['phase'] == 'collect'
        and result['status'] == 'COMPLETE' and result['unit'] == unit and result['fits'] == result['updates'] == 0
        and result['trainingAllowed'] is False and result['parent_present'] is True
        and result['loaded_adapter_state_sha256'] == result['adapter_state_after'] == PARENT_STATE
        and result['frozen_base_unchanged'] is True and result['max_native_calls'] == quality.UNIT_CAPS[unit],
        'complete_readonly_quality_attempts_required')
    same(result['binding'],inputs['binding'],'quality_unit_source_binding_drift')
    same(source.read(directory/'STATES.json'),dict(before=PARENT_STATE,after=PARENT_STATE),'quality_state_drift')
    require(set(result['output_files']) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'quality_output_inventory_drift')
    portable.transfer.verify_files(directory,result['output_files'])
    document = quality.replay_unit(inputs['exposures'],source.read(directory/'DATA.json'))
    require(document['unit'] == unit and result['model_calls'] == document['model_calls'], 'quality_native_count_drift')
    captures = [capture for world in document['documents'] for capture in world['evidence']['captures']]
    require({path.name for path in directory.glob('CALL_*.json')} == {f'CALL_{index:03d}.json' for index in range(len(captures))},
            'quality_native_inventory_drift')
    for index,capture in enumerate(captures):
        expected = dict(call_index=index,unit=unit,role='coached_actor',**{key:deepcopy(capture[key]) for key in (
            'master','task_index','episode_call_index','messages','response','error')})
        require(capture['call_index'] == index,'quality_native_call_order_drift')
        same(source.read(directory/f'CALL_{index:03d}.json'),expected,'quality_native_capture_drift')
    require(result['row_count'] == len(document['rows']) and result['admitted_pairs'] == document['admitted_pairs']
            and result['rejected_pairs'] == document['rejected_pairs'] and result['native_error_calls'] == document['native_error_calls'],
            'quality_summary_drift')
    same(result['role_calls'],dict(coached_actor=len(captures)) if captures else {},'quality_role_count_drift')
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle','bundle-sha','model-dir','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--shard-roots',nargs=8,required=True)
    parser.add_argument('--phase',choices=('prepare','collect','assemble'),required=True)
    parser.add_argument('--unit',type=int,choices=quality.UNITS)
    parser.add_argument('--unit-roots',nargs=4)
    parser.add_argument('--gpu-uuid')
    options = parser.parse_args(argv)
    require((options.phase == 'collect') == (options.unit is not None),'quality_collect_unit_required')
    require((options.phase == 'assemble') == bool(options.unit_roots),'four_unit_roots_only_for_assembly')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1','offline_required')
    require(options.phase != 'collect' or bool(options.gpu_uuid) and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid,
            'exact_visible_gpu_required')
    output = Path(options.output).resolve()
    for location in options.shard_roots + (options.unit_roots or []) + [options.bundle,options.model_dir]:
        reference = Path(location).resolve()
        require(output != reference and reference not in output.parents,'original_artifact_overlap_forbidden')
    output.mkdir(parents=True,exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA,phase=options.phase,unit=options.unit,arguments=vars(options),started_unix=started,
        fits=0,updates=0,trainingAllowed=False,parent_present=options.phase == 'collect',model_calls=0,
        max_native_calls=quality.UNIT_CAPS[options.unit] if options.phase == 'collect' else 0,
        protocol_sha256=PROTOCOL_SHA,entry_sha256=source.file_hash(__file__),claim=quality.CLAIM)
    source.write(output/'REQUEST.json',result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + NATIVE_SECONDS,'quality_stage_deadline:'+label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'],admission_seconds=inputs['admission_seconds'])
        source.write(output/'INPUTS.json',inputs['binding'])
        source.write(output/'SOURCE_PLAN.json',inputs['plan'])
        if options.phase == 'prepare':
            source.write(output/'REUSED_QUALITY.json',inputs['reused'])
            result.update(status='PREPARED_NO_MODEL',reused_candidate_rows=len(inputs['reused']['rows']),
                eligible_train_worlds=61,new_worlds=29,max_new_calls=696,max_dataset_rows=1452,finished_unix=time.time())
        elif options.phase == 'assemble':
            units = [read_unit(directory,inputs,unit) for directory,unit in zip(options.unit_roots,quality.UNITS)]
            capsule = quality.assemble(inputs['exposures'],inputs['teachings'],units)
            source.write(output/'CAPSULE.json',dict(capsule=capsule,native_binding=inputs['binding'],
                unit_results=[dict(unit=unit,result_sha256=source.file_hash(Path(directory)/'RESULT.json'))
                              for unit,directory in zip(quality.UNITS,options.unit_roots)]))
            result.update(status='COMPLETE_NO_MODEL',row_count=capsule['row_count'],reused_calls=768,
                new_calls=capsule['new_calls'],finished_unix=time.time())
        else:
            arguments = portable.read_bundle(options.bundle,expected_manifest_sha256=options.bundle_sha,
                model_dir=options.model_dir,device='cuda:0',gpu_uuid=options.gpu_uuid)
            engine = source.Engine(arguments,source.native.load_local_tokenizer(arguments.model_dir),check=check)
            from organism_v6.pcfl_vertical_train import _state_hash

            parameters = {name:parameter for name,parameter in engine.model.named_parameters() if '.lora_A.' in name or '.lora_B.' in name}
            require(bool(parameters) and _state_hash(parameters) == PARENT_STATE,'mounted_37ec_required')
            require(not any(parameter.requires_grad for unused,parameter in engine.model.named_parameters()),'readonly_actor_required')
            result.update(runtime=engine.runtime,loaded_adapter_state_sha256=PARENT_STATE)

            def generate(messages, **metadata):
                nonlocal cap_hit
                check('call')
                if len(captures) >= result['max_native_calls']:
                    cap_hit = True
                    raise ValueError('quality_native_call_cap')
                capture = dict(call_index=len(captures),unit=options.unit,role='coached_actor',messages=deepcopy(messages),
                               response=None,error=None,**metadata)
                captures.append(capture)
                try:
                    capture['response'] = deepcopy(engine.generate(deepcopy(messages),max_new_tokens=160))
                    return deepcopy(capture['response'])
                except Exception as error:
                    capture['error'] = dict(type=type(error).__name__,message=str(error))
                    raise
                finally:
                    source.write(output/f"CALL_{capture['call_index']:03d}.json",capture)

            document = quality.collect_unit(inputs['exposures'],options.unit,generate)
            source.write(output/'DATA.json',document)
            require(not cap_hit and len(captures) == document['model_calls'],'quality_native_capture_count_required')
            check('complete')
            engine.verify_base()
            final_state = _state_hash(parameters)
            require(final_state == PARENT_STATE,'quality_readonly_state_drift')
            portable.verify_base_files(options.bundle,options.model_dir,expected_manifest_sha256=options.bundle_sha)
            same(helpers(),inputs['binding']['helpers'],'quality_runtime_source_drift')
            source.write(output/'STATES.json',dict(before=PARENT_STATE,after=final_state))
            result.update(status='COMPLETE',adapter_state_after=final_state,frozen_base_unchanged=True,
                model_calls=len(captures),role_calls=dict(Counter(capture['role'] for capture in captures)),
                row_count=len(document['rows']),admitted_pairs=document['admitted_pairs'],rejected_pairs=document['rejected_pairs'],
                native_error_calls=document['native_error_calls'],attempted_tasks=document['attempted_tasks'],
                data_status='ATTEMPTS_COMPLETE_QUALITY_FILTERED_NOT_ALL_CASES_SUCCESSFUL',finished_unix=time.time(),
                gpu_assigned_wall_seconds=time.time()-started,
                generated_tokens=sum(len(capture['response'].get('token_ids',[])) for capture in captures if isinstance(capture['response'],dict)))
        result['output_files'] = {path.name:source.file_hash(path) for path in output.glob('*.json')}
        source.write(output/'RESULT.json',result)
        return result
    except BaseException as error:
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash(parameters)
                engine.verify_base()
                portable.verify_base_files(options.bundle,options.model_dir,expected_manifest_sha256=options.bundle_sha)
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
            source.write(output/'STATES.json',dict(before=result.get('loaded_adapter_state_sha256'),after=result.get('adapter_state_after')))
        result.update(status='FAILED',error=repr(error),model_calls=len(captures),cap_hit=cap_hit,finished_unix=time.time())
        source.write(output/'FAILED.json',result)
        raise


if __name__ == '__main__':
    main()
