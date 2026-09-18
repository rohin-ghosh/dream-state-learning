"""New readonly TEACH calls, reusing verified rich-v1 exposure without fitting."""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time

from gpu import astra_rich_trajectory_collection as original


rich = original.rich
portable = original.portable
source = original.source
require = source.require
SCHEMA = 'DEV_RICH_ACTION_FIRST_NATIVE_V2'
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_rich_action_first_collection_protocol.md'
PROTOCOL_SHA = '509f85c17d4be373eb1e917ee11e5134dcb447257a376163fe6a995d533eece9'
V1_RICH_SHA = 'ed0e59ed9719908f616bfd57d5b27c68ae58ec9cf45a8765687569bed1b3fb0d'
NATIVE_SECONDS = 3600


def helpers():
    return dict(driver=source.file_hash(__file__), original=original.helpers(),
                guard=source.file_hash(Path(__file__).with_name('astra_rich_action_first_collection_guard.sh')))


def load_inputs(options):
    started = time.monotonic()
    require(source.file_hash(Path(__file__).resolve().parents[1]/PROTOCOL_PATH) == PROTOCOL_SHA,
            'exact_action_first_protocol_required')
    inputs = original.load_inputs(options)
    inputs['binding']['helpers']['rich'] = V1_RICH_SHA
    exposure, exposure_sha = original.read_stage(options.exposure, 'expose', inputs)
    require(exposure['source_ready'] and len(exposure['collections']) == 5,
            'all_five_original_sources_required')
    return dict(exposure=exposure, manifest=inputs['manifest'], old_ids=inputs['old_ids'],
                admission_seconds=time.monotonic()-started,
                binding=dict(protocol_sha256=PROTOCOL_SHA, original_binding=inputs['binding'],
                    exposure_result_sha256=exposure_sha, execution_policy='ACTION_FIRST_V2',
                    rich_protocol=deepcopy(rich.ACTION_FIRST_PROTOCOL), helpers=helpers()))


def collect(inputs, shard, generate):
    document = rich.collect_teaching(shard, inputs['exposure']['collections'][:4], generate,
        old_ids=inputs['old_ids'], protocol=rich.ACTION_FIRST_PROTOCOL, execution_policy='ACTION_FIRST_V2')
    rows = rich.replay_teaching(document)
    require(document['fit_ready'] is False, 'unreviewed_candidates_never_fit_ready')
    counts = {form:len(rows[form]) for form in rich.FORMS}
    require(len(set(counts.values())) == 1 and 0 <= counts['RICH'] <= 96 and counts['RICH'] % 6 == 0,
            'paired_complete_episode_candidates_only')
    identity = lambda row: (row['episode_id'],row['call_sha256'],row['source_sha256'])
    require(all([identity(row) for row in rows[form]] == [identity(row) for row in rows['TERSE']]
                for form in rich.FORMS), 'same_candidate_source_in_every_view')
    return document, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle','bundle-sha','model-dir','exposure','output'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--shard', type=int, choices=range(4), required=True)
    parser.add_argument('--phase', choices=('prepare','teach'), required=True)
    parser.add_argument('--gpu-uuid')
    options = parser.parse_args(argv)
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase != 'teach' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output).resolve()
    for location in (options.bundle,options.model_dir,options.exposure):
        reference = Path(location).resolve()
        require(output != reference and reference not in output.parents, 'source_overlap_forbidden')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA,phase=options.phase,shard=options.shard,arguments=vars(options),
        started_unix=started,model_calls=0,max_native_calls=96 if options.phase == 'teach' else 0,
        fits=0,updates=0,trainingAllowed=False,fit_ready=False,parent_present=options.phase == 'teach',
        protocol_sha256=PROTOCOL_SHA,entry_sha256=source.file_hash(__file__),
        claim='ACTION_EXECUTION_AND_UNREVIEWED_RICH_CANDIDATES_NOT_TRANSFER_OR_RATIONALE_TRUTH')
    source.write(output/'REQUEST.json',result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + NATIVE_SECONDS, 'action_first_deadline:'+label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'],admission_seconds=inputs['admission_seconds'])
        source.write(output/'INPUTS.json',inputs['binding'])
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL',finished_unix=time.time())
        else:
            arguments = portable.read_bundle(options.bundle,expected_manifest_sha256=options.bundle_sha,
                model_dir=options.model_dir,device='cuda:0',gpu_uuid=options.gpu_uuid)
            engine = source.Engine(arguments,source.native.load_local_tokenizer(arguments.model_dir),check=check)
            from organism_v6.pcfl_vertical_train import _state_hash

            parameters = {name:parameter for name,parameter in engine.model.named_parameters()
                          if '.lora_A.' in name or '.lora_B.' in name}
            require(bool(parameters) and _state_hash(parameters) == original.PARENT_STATE, 'mounted_37ec_required')
            require(not any(parameter.requires_grad for unused,parameter in engine.model.named_parameters()),
                    'readonly_actor_required')
            result.update(runtime=engine.runtime,loaded_adapter_state_sha256=original.PARENT_STATE)

            def generate(messages):
                nonlocal cap_hit
                check('call')
                if len(captures) >= 96:
                    cap_hit = True
                    raise ValueError('action_first_call_cap')
                capture = dict(call_index=len(captures),shard=options.shard,role='rich_actor',messages=deepcopy(messages),
                               response=None,error=None,max_new_tokens=512)
                captures.append(capture)
                try:
                    capture['response'] = deepcopy(engine.generate(deepcopy(messages),max_new_tokens=512))
                    return deepcopy(capture['response'])
                except Exception as error:
                    capture['error'] = dict(type=type(error).__name__,message=str(error))
                    raise
                finally:
                    source.write(output/f"CALL_{capture['call_index']:03d}.json",capture)

            document, counts = collect(inputs,options.shard,generate)
            source.write(output/'LESSONS.json',document)
            require(not cap_hit and len(captures) == document['model_calls'], 'actual_call_count_required')
            require(len(document['captures']) == len(captures), 'actual_capture_count_required')
            for native, captured in zip(captures,document['captures']):
                original.same({key:native[key] for key in ('messages','response','error')},
                              {key:captured[key] for key in ('messages','response','error')}, 'actual_capture_join')
            check('complete')
            engine.verify_base()
            final_state = _state_hash(parameters)
            require(final_state == original.PARENT_STATE, 'readonly_state_drift')
            portable.verify_base_files(options.bundle,options.model_dir,expected_manifest_sha256=options.bundle_sha)
            original.same(helpers(),inputs['binding']['helpers'],'runtime_source_drift')
            source.write(output/'STATES.json',dict(before=original.PARENT_STATE,after=final_state))
            source.write(output/'NATIVE_METRICS.json',original.native_metrics(captures))
            result.update(status='COMPLETE',adapter_state_after=final_state,frozen_base_unchanged=True,
                model_calls=len(captures),row_counts=counts,complete_episodes=document['complete_episode_count'],
                planned_episodes=16,attempted_episodes=document['attempted_task_count'],
                native_error_calls=sum(capture['error'] is not None for capture in captures),
                execution_rejections=dict(Counter(capture['validation_error']['message']
                    for capture in document['captures'] if capture['validation_error'])),
                data_status='EXECUTION_COMPLETE_CANDIDATES_UNREVIEWED',finished_unix=time.time())
        result['output_files'] = {path.name:source.file_hash(path) for path in output.glob('*.json')}
        source.write(output/'RESULT.json',result)
        return result
    except BaseException as error:
        result.update(status='FAILED',error=repr(error),model_calls=len(captures),finished_unix=time.time())
        source.write(output/'FAILED.json',result)
        raise


if __name__ == '__main__':
    main()
