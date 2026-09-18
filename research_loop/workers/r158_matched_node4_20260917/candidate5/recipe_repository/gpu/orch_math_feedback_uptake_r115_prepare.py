"""Freeze node-only R115 F2 inputs and compact CPU/provenance receipts."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from gpu import orch_math_feedback_uptake_r115_native as native
from gpu import orch_r110_claude_broker as broker
from organism_v6 import orch_math_feedback_uptake_r115 as policy


def prepare(root, source):
    policy.require(root == policy.ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node_only_cpu_prepare')
    native.bind()
    broker_pins = broker.source_pins()
    predecessor = root.parent / policy.previous.AREA.name
    root.mkdir(exist_ok=False)
    (root/'sealed').mkdir(mode=0o700)
    inputs = {}
    for name in ('TRAIN.json', 'DEV8.json', 'sealed/FINAL8.json'):
        raw = (predecessor/name).read_bytes()
        (root/name).write_bytes(raw)
        inputs[name] = hashlib.sha256(raw).hexdigest()
    os.chmod(root/'sealed/FINAL8.json', 0o600)
    common = policy.contract(source)
    native.write(root/'COMMON_CONTRACT.json', common)
    tests = native.read(source/'R115_CPU_TESTS.json')
    policy.require(tests['passed'] and tests['section95_runtime_tests'] >= 8, 'three_runtime_gates_passed')
    training, dev, final = native.read(root/'TRAIN.json'), native.read(root/'DEV8.json'), native.read(root/'sealed/FINAL8.json')
    policy.require(policy.digest(dev) == '49feeb421c0ff2fd97c358b7d9770d9372f5c62cdfb6348118c836714d3bdbc1', 'frozen_dev')
    policy.require(policy.digest(final) == 'b3642ffe0e6e501ca805e323d28cdf1f159296872b78f798f65180417dc044ee', 'frozen_final')
    source_files = {str(path.relative_to(source)):policy.sha(path)
        for folder in ('gpu','organism_v6') for path in sorted((source/folder).glob('*.py'))}
    for relative in ('research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md',
            'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md', 'F2_INITIAL_FIELDS.json'):
        source_files[relative] = policy.sha(source/relative)
    native.write(root/'GO.json', dict(authorization='WATCHER_RELAYED_ROHIN_DONE',
        source_reference='R115 direct user: actual USER GO received audit complete', no_silence_inference=True))
    for index in (1,5):
        lane = root/f'lane{index}'
        lane.mkdir()
        (lane/'parent_queue').mkdir()
        (lane/'sealed').mkdir(mode=0o700)
        fields = native.read(source/'F2_INITIAL_FIELDS.json')['fields']
        config = dict(schema=broker.SCHEMA,branch='F2',family='math',remote_root=str(lane),life_id=f'R115_F2_{index}',
            deadline_unix=native.NATIVE,max_parent_calls=policy.PARENT_CAP,max_budget_usd=1.0,max_output_tokens=8192,
            train_tasks={task['id']:task['question_sha256'] for group in training for task in group},
            excluded_task_ids=[task['id'] for task in dev],cohort_sha256=policy.sha(root/'TRAIN.json'),
            principles_sha256=broker.PRINCIPLES_V2_SHA256,source_files=broker_pins,fallback_parent_fields=fields)
        broker.validate_config(config)
        native.write(lane/'BROKER_CONFIG.json', config)
        native.write(lane/'BROKER_GO.json', dict(schema='ORCH_R111_FABLE_LAUNCH_V1',authorized=True,
            authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='R115 direct user GO and F2 launch assignment',
            config_sha256=broker.digest(config),not_before_unix=0))
        native.write(lane/'CONFIG.json',dict(index=index,uuid=policy.DEVICES[index],actual_required_parent_model=policy.MODELS[index],
            common_contract_sha256=policy.digest(common), weight_updates=0, sleep=False, actual_lambda=None))
    files = native.reuse.driver.seam.portable.verify_base_files(native.BUNDLE,native.MODEL,
        expected_manifest_sha256=native.reuse.node_limits.BUNDLE_SHA)
    ready = dict(status='CPU_NATIVE_READY_PENDING_PUBLICATION_RELEASE_ADMISSION',common_contract_sha256=policy.digest(common),
        source_files=source_files,data_files=inputs,base_files=files,tests=tests,
        raw_node_only=True,judge_prompt_sha256=policy.JUDGE_SHA,weight_updates=0,actual_lambda=None)
    native.write(root/'READY.json',ready)
    roster = dict(dev_ids=[task['id'] for task in dev],final_ids=[task['id'] for task in final],
        dev_set_sha256=policy.digest(dev),final_set_sha256=policy.digest(final))
    native.write(root/'sealed/READOUT_ROSTER.json',roster)
    os.chmod(root/'sealed/READOUT_ROSTER.json',0o600)
    print(json.dumps(dict(status=ready['status'],root=str(root),source=str(source),ready_sha256=policy.sha(root/'READY.json'),
        common_contract_sha256=policy.digest(common),source_inventory_sha256=policy.digest(source_files),
        source_count=len(source_files),dev_ids=roster['dev_ids'],dev_set_sha256=roster['dev_set_sha256'],
        final_set_sha256=roster['final_set_sha256'],sealed_roster_path=str(root/'sealed/READOUT_ROSTER.json'),
        sealed_roster_sha256=policy.sha(root/'sealed/READOUT_ROSTER.json'),judge_prompt_sha256=policy.JUDGE_SHA,
        fields=fields,fixed_parent_template_sha256=common['fixed_parent_template_sha256'],
        native_calls=0,parent_calls=0,weight_updates=0,lambda_actual=None),indent=2,sort_keys=True))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--root',type=Path,default=policy.ROOT)
    args=parser.parse_args()
    prepare(args.root,args.source)
