"""Fresh sealed inference and separate TRAIN-only continuation processes."""

import argparse
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import orch_r119_grid_final_lifecycle as custody


def require_released(plan, mode):
    output = Path(plan['output'])
    custody.require(custody.read(output / 'RELEASED.json')['status'] == 'RELEASED'
                    and not custody.same_process(plan['predecessor']), 'fresh_process_after_release')
    path = output / (mode.upper() + '_AUTHORIZATION.json')
    custody.require(custody.sha(path) == os.environ.get('ORCH_GRID_FINAL_PHASE_AUTHORIZATION_SHA256'),
                    'exact_phase_authorization')
    authorization = custody.read(path)
    custody.require(authorization['mode'] == mode and authorization['plan'] == custody.ref(output / 'PLAN.json')
        and authorization['release'] == custody.ref(output / 'RELEASED.json')
        and custody.same_process(authorization['timer_identity'])
        and authorization['issued_unix'] <= time.time() < authorization['deadline_unix'], 'live_phase_custody')
    admission = authorization['admission']
    custody.require(custody.sha(admission['path']) == admission['sha256'], 'immutable_phase_admission')
    report = custody.read(admission['path'])
    custody.require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons'],
                    'strict_actual_admission')
    return output


def evaluate(plan):
    prior, grid, config, checkpoint = custody.validate(plan)
    output = require_released(plan, 'evaluate')
    custody.require(custody.MORNING <= time.time() < custody.EVAL_END, 'new_morning_only')
    custody.require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'], 'exact_readout_GPU')
    custody.require(custody.no_attempt(output), 'no_duplicate_capture')
    custody.write(output / 'EVAL_CLAIM.json', dict(pid=os.getpid(), event=custody.EVENT,
        parent_absent=True, carry_access=False, observed_unix=time.time()))
    sys.path.insert(0, str(prior.OLD))
    from gpu import orch_r116_grid_shared_client as decoder_source
    native = decoder_source.native
    identity = native.bridge.AdapterIdentity.from_document(checkpoint['adapter'])
    stage = native.bridge.StageBinding('R119_FINAL_' + plan['branch'], native.bridge.ARMS[0],
        1, 'sealed_readout', identity, False, True, plan['checkpoint']['sha256'])

    def check(unused):
        custody.require(custody.MORNING <= time.time() < custody.EVAL_END - 4, 'fixed_readout_deadline')

    loaded = native.load_stage(stage, model_dir=config['model_dir'], device='cuda:0',
        gpu_uuid=config['uuid'], context=native.StageContext(), check=check,
        predecessor_processes=(tuple(checkpoint['source_process']),))
    custody.require(loaded.optimizer is None, 'sealed_eval_never_optimizer')
    engine = decoder_source.SharedDecoder(loaded)
    custody.require(custody.sha(plan['final_file']['path']) == plan['final_file']['sha256'], 'sealed_hash')
    tasks = custody.read(plan['final_file']['path'])
    custody.require(len(tasks) == 8 and [task['id'] for task in tasks] == plan['final_ids']
                    and all(task['split'] == 'FINAL' for task in tasks), 'exact_sealed_eight')
    custody.require(grid.policy.HELD_PROMPT == plan['held_prompt']
        and all(grid.policy.DECODER[key] == value for key, value in plan['decoder'].items()), 'same_decoder')
    messages = [[dict(role='system', content=plan['held_prompt']), dict(role='user', content=json.dumps(
        grid.policy.public_observation(task, grid.policy.game.initial(task)), sort_keys=True))] for task in tasks]
    check(None)
    reservations = [dict(number=ordinal, task_id=task['id'], split='FINAL', purpose=custody.EVENT,
        cap=2048, evaluation_only=True, trainingAllowed=False, reserved_unix=time.time())
        for ordinal, task in enumerate(tasks, 1)]
    custody.write(output / 'EVAL_LEDGER.json', dict(max_native_calls=8, parent_calls=0, training_calls=0,
        optimizer_steps=0, checkpoint=plan['checkpoint'], reservations=reservations))
    responses = engine.batch(messages, 2048)
    custody.require(len(responses) == 8, 'eight_returned_no_retry')
    references = []
    for row, prompt, response in zip(reservations, messages, responses):
        path = output / 'sealed_calls' / f'{row["number"]:02d}.json'
        custody.write(path, dict(row, status='COMPLETE', messages=prompt, response=response,
            checkpoint=plan['checkpoint'], finished_unix=time.time()))
        references.append(custody.ref(path))
    engine.verify_base()
    custody.write(output / 'EVAL_COMPLETE.json', dict(status='COMPLETE', calls=8,
        response_refs=references, parent_calls=0, optimizer_steps=0, training_calls=0,
        fresh_process=True, parent_absent=True, carry_access=False, finished_unix=time.time()))


def resume(plan):
    prior, grid, config, checkpoint = custody.validate(plan)
    output = require_released(plan, 'resume')
    custody.require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'], 'exact_TRAIN_GPU')
    boundary = custody.read(output / 'BOUNDARY.json')
    for key in ('carry', 'ledger', 'train_complete'):
        reference = boundary[key]
        custody.require(custody.sha(reference['path']) == reference['sha256'], 'unchanged_TRAIN_' + key)
    from peft import PeftModel
    from gpu import orch_guided_native as native
    engine = grid.load_engine(config)
    identity = native.bridge.AdapterIdentity.from_document(checkpoint['adapter'])
    engine.model = PeftModel.from_pretrained(engine.model, identity.path, is_trainable=False,
        local_files_only=True, autocast_adapter_dtype=True)
    engine.model.requires_grad_(False)
    engine.model.eval()
    custody.require(native.observe_adapter(engine, identity) == identity, 'same_frozen_gen1')
    caps = custody.read(plan['budget']['path'])['prospective_caps']
    grid.MAX_NATIVE, grid.MAX_PARENT = caps['NATIVE'], caps['PARENT']
    writer = grid.write

    def train_only(path, value, replace=False):
        if isinstance(value, dict) and 'messages' in value and 'status' in value:
            custody.require(value['split'] == 'TRAIN' and not value['attached_readout'], 'never_held_to_TRAIN')
            value = dict(value, adapter=identity.document(), fork_checkpoint_sha256=plan['checkpoint']['sha256'],
                         parent_nonblocking=True, local_optimizer_steps=0)
        return writer(path, value, replace=replace)

    grid.write = train_only
    root = Path(plan['root'])
    memory = grid.read(root / 'CARRY.json')
    roster = grid.read(root / 'TRAIN.json')
    cycle = boundary['next_cycle']
    life_type = prior.mailbox.life_class(grid, plan['mailbox_era'])
    custody.write(output / 'RESUMED.json', dict(identity=custody.process(os.getpid()),
        next_cycle=cycle, counts=boundary['counts'], checkpoint=plan['checkpoint'],
        mailbox_era=plan['mailbox_era'], optimizer_used=False, counter_reset=False,
        ledger_replayed=False, parent_claims_replayed=False, observed_unix=time.time()))
    while time.time() < custody.TRAIN_END:
        life = life_type(root, engine, config, cycle)
        tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
        try:
            grid.train_cycle(life, tasks, memory)
        except grid.TrainWindowClosed:
            break
        memory = grid.read(root / 'CARRY.json')
        custody.write(output / 'cycles' / f'C{cycle:04d}.json', dict(cycle=cycle,
            carry=grid.ref(root / 'CARRY.json'), ledger=grid.ref(root / 'LEDGER.jsonl'), observed_unix=time.time()))
        cycle += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('evaluate', 'resume'))
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    custody.require(custody.sha(args.plan) == args.plan_sha256, 'exact_plan')
    globals()[args.mode](custody.read(args.plan))


if __name__ == '__main__':
    main()
