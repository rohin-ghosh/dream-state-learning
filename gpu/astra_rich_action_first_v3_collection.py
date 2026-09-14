"""Prospective V3 header compatibility; same V2 prompt and original EXPOSE."""

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import os
from pathlib import Path
import time

from gpu import astra_rich_action_first_collection as v2

original = v2.original
rich = v2.rich
portable = v2.portable
source = v2.source
require = v2.require
SCHEMA = 'DEV_RICH_ACTION_FIRST_NATIVE_V3'
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_rich_action_first_v3_collection_protocol.md'
PROTOCOL_SHA = 'a45be0236103a759de40473a81029b1568a035220c544aa96bbc18a3cbc81aef'
NATIVE_SECONDS = v2.NATIVE_SECONDS


@dataclass(frozen=True)
class PolicyConfig:
    execution_policy: str = rich.ACTION_FIRST_V3
    protocol_sha256: str = PROTOCOL_SHA


CONFIG = PolicyConfig()


def helpers():
    return dict(driver=source.file_hash(__file__), v2=v2.helpers(),
                guard=source.file_hash(Path(__file__).with_name('astra_rich_action_first_v3_collection_guard.sh')))


def load_inputs(options):
    require(source.file_hash(Path(__file__).resolve().parents[1]/PROTOCOL_PATH) == CONFIG.protocol_sha256,
            'exact_v3_protocol_required')
    inputs = v2.load_inputs(options)
    inputs['binding'] = dict(protocol_sha256=CONFIG.protocol_sha256,
        execution_policy=CONFIG.execution_policy, rich_protocol=deepcopy(rich.ACTION_FIRST_PROTOCOL),
        v2_loader_binding=inputs['binding'], helpers=helpers())
    return inputs


def collect(inputs, shard, generate, *, config=CONFIG):
    require(config == CONFIG, 'fixed_v3_policy_required')
    require(inputs['binding']['execution_policy'] == config.execution_policy, 'bound_v3_policy_required')
    document = rich.collect_teaching(shard, inputs['exposure']['collections'][:4], generate,
        old_ids=inputs['old_ids'], protocol=rich.ACTION_FIRST_PROTOCOL, execution_policy=config.execution_policy)
    rows = rich.replay_teaching(document)
    require(document['fit_ready'] is False, 'unreviewed_candidates_never_fit_ready')
    counts = {form: len(rows[form]) for form in rich.FORMS}
    require(len(set(counts.values())) == 1 and 0 <= counts['RICH'] <= 96 and counts['RICH'] % 6 == 0,
            'paired_complete_episode_candidates_only')
    identity = lambda row: (row['episode_id'], row['call_sha256'], row['source_sha256'])
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
        execution_policy=CONFIG.execution_policy,protocol_sha256=PROTOCOL_SHA,entry_sha256=source.file_hash(__file__),
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
