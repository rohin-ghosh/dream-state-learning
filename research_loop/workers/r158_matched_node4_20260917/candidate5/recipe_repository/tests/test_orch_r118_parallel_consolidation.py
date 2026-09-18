from datetime import timedelta
import fcntl
import json
import os
import random
import subprocess
import sys
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r116_shared_learner as shared
from gpu import orch_r116_shared_parallel_sleep as parallel
from gpu import orch_r118_parallel_consolidation as candidate
from gpu import orch_r118_final_selection as selector

try:
    import torch
except ImportError:
    torch = None


class ContractTests(unittest.TestCase):
    def test_prospective_only(self):
        contract = candidate.integration_contract()
        self.assertFalse(contract['process_launch'])
        self.assertFalse(contract['native_gpu_tested'])
        self.assertIn('NOT serial-equivalent', contract['algorithm'])
        self.assertEqual(contract['rank_order'], list(shared.BRANCHES))

    def test_original_bounds_exact(self):
        self.assertEqual(time.strftime('%H:%M', time.gmtime(candidate.HARD_END)), '17:02')
        self.assertEqual(time.strftime('%H:%M', time.gmtime(candidate.TRAIN_END)), '17:00')

    def test_actual_steps_not_presentations_and_unknown_preserved(self):
        state = dict(generation=2, config_sha256='a' * 64,
            optimizer_steps=1125, child_token_exposures=None, anchor_token_exposures=20351,
            shared_optimizer_steps=0, shared_child_token_exposures=0, shared_anchor_token_exposures=0)
        metrics = dict(optimizer_steps=236, child_token_exposures=319802, anchor_token_exposures=35885)
        result = candidate.advance_state(state, {}, metrics)
        self.assertEqual(result['optimizer_steps'], 1361)
        self.assertIsNone(result['child_token_exposures'])
        self.assertEqual(result['shared_child_token_exposures'], 319802)
        self.assertEqual(result['generation'], 3)
        self.assertNotIn('parallel', result)

    def test_negative_and_bool_counters_fail(self):
        for value in (-1, True, None):
            with self.assertRaisesRegex(ValueError, 'actual_nonnegative'):
                candidate.advance_state(dict(generation=0, config_sha256='x'), {}, dict(optimizer_steps=value))

    def test_checked_file_tamper_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'original'
            path.write_text('original')
            digest = candidate.sha(path)
            self.assertEqual(candidate.checked_file(path, digest), path)
            link = Path(folder) / 'link'
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, 'immutable'):
                candidate.checked_file(link, digest)
            path.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'immutable'):
                candidate.checked_file(path, digest)

    def test_metadata_recovery_cannot_accept_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pins = {}
            for name in ('CONFIG.json','INITIALIZED.json','ADOPTION.json'):
                shared.write(root / name, {})
                pins[name] = shared.sha(root / name)
            activation = root / 'ACTIVATE.json'
            shared.write(activation, dict(schema=candidate.SCHEMA, root=str(root), pins=pins, generation=0))
            with self.assertRaises(FileNotFoundError):
                candidate.recover_complete(root, activation_path=activation, activation_sha256=shared.sha(activation))
            self.assertFalse((root / 'STATE.json').exists())

    def test_future_launch_plan_does_not_touch_serial(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'common'
            root.mkdir()
            config = dict(owner='F1',anchor_sha256=shared.ANCHOR_SHA,
                branches={branch:dict(root=str(Path(folder) / branch)) for branch in shared.BRANCHES})
            shared.write(root / 'CONFIG.json',config)
            shared.write(root / 'STATE.json',dict(generation=0))
            shared.write(root / 'ADOPTION.json',dict(immutable=True))
            shared.write(root / 'INITIALIZED.json',dict(immutable=True))
            shared.write(root / 'generation_000000/sleep/START.json',dict(serial_running=True))
            before={str(path.relative_to(root)):shared.sha(path) for path in root.rglob('*') if path.is_file()}
            output=Path(folder) / 'future/LAUNCH_PLAN.json'
            result=candidate.prepare_launch_plan(root=root,output=output,generation=1,
                pins={name:shared.sha(root / name) for name in ('CONFIG.json','ADOPTION.json','INITIALIZED.json')},
                source_files={str(Path(candidate.__file__).resolve()):shared.sha(candidate.__file__)},deadline_unix=candidate.TRAIN_END)
            self.assertEqual(result['status'],'PREPARED_NOT_ACTIVE')
            self.assertFalse((output.parent / 'ACTIVATION.json').exists())
            self.assertFalse((output.parent / 'RENDEZVOUS').exists())
            self.assertEqual(before,{str(path.relative_to(root)):shared.sha(path) for path in root.rglob('*') if path.is_file()})
            with self.assertRaisesRegex(ValueError,'future_STATE'):
                candidate.arm_launch(plan_path=output,plan_sha256=result['sha256'],participants={})
            with (root / 'COORDINATOR.lock').open('a') as serial_lock:
                fcntl.flock(serial_lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    candidate.arm_launch(plan_path=output,plan_sha256=result['sha256'],participants={})
            self.assertEqual(before,{str(path.relative_to(root)):shared.sha(path) for path in root.rglob('*')
                if path.is_file() and path.name!='COORDINATOR.lock'})

    def test_launch_supervision_rejects_stale_guard_and_no_final(self):
        identity=candidate.process_identity()
        certificate=dict(identity=identity,launch_device=dict(kind='cpu',physical=0,cuda_visible_devices=''),
            retained_supervision=dict(guard_identity=dict(identity,start_ticks=identity['start_ticks']+1)))
        with self.assertRaisesRegex(ValueError,'retained_process'):
            candidate.validate_launch_participant(certificate,'F1','CPU_TEST_ONLY')
        certificate['retained_supervision']=dict(guard_identity=identity,native_identity=identity,final_identity_bindings=[])
        with self.assertRaisesRegex(ValueError,'FINAL_identity'):
            candidate.validate_launch_participant(certificate,'F1','CPU_TEST_ONLY')


def encoded(offset=0):
    return SimpleNamespace(input_ids=(1,2,3 + offset % 3,6),
        labels=(-100,-100,3 + offset % 3,6), target_ids=(3 + offset % 3,6))


if torch is not None:
    class TinyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = torch.nn.Embedding(7,4)
            self.base = torch.nn.Linear(4,7,bias=False)
            self.layer = torch.nn.Module()
            self.layer.lora_A = torch.nn.ModuleDict({'default':torch.nn.Linear(4,2,bias=False)})
            self.layer.lora_B = torch.nn.ModuleDict({'default':torch.nn.Linear(2,7,bias=False)})
            self.requires_grad_(False)
            self.eval()
            self.config = SimpleNamespace(use_cache=True)
            self.fail = False

        def forward(self, input_ids, attention_mask, labels):
            hidden = self.embedding(input_ids)
            logits = self.base(hidden) + self.layer.lora_B['default'](self.layer.lora_A['default'](hidden))
            loss = torch.nn.functional.cross_entropy(logits[:,:-1].reshape(-1,7), labels[:,1:].reshape(-1))
            return SimpleNamespace(loss=loss * float('nan') if self.fail else loss)

        def save_pretrained(self, folder, **kwargs):
            folder = Path(folder)
            folder.mkdir()
            torch.save({name:parameter.detach() for name,parameter in self.named_parameters()
                        if parallel.is_lora(name)}, folder / 'adapter_model.pt')


def source_files():
    from organism_v6 import pcfl_vertical_train, orch_guided_bridge
    result = {str(Path(module.__file__).resolve()):shared.sha(module.__file__)
              for module in (candidate,parallel,shared,pcfl_vertical_train,orch_guided_bridge)}
    result[str(Path(__file__).resolve())] = shared.sha(__file__)
    return result


def fake_cohort(**kwargs):
    return dict(encoded_new=[encoded(index) for index in range(3)],
        encoded_old=[encoded(index) for index in range(11)],
        encoded_anchors=[encoded(index) for index in range(42)],
        schedule=parallel.make_schedule(3,11), source_manifest_sha256='a' * 64,
        manifest=dict(test_only_synthetic_encoded_inputs=True, native_validator_called_separately=True))


def create_fixture(root, engine, optimizer, identities):
    from gpu import orch_r111_route_pair_shared as original
    initial = root / 'F1' / 'initial'
    original.checkpoint(engine, optimizer, initial, 6, 6)
    specs = {}
    for branch in shared.BRANCHES:
        branch_root = root / branch
        branch_root.mkdir(exist_ok=True)
        shared.write(branch_root / 'CARRY.json', dict(native=17, parent=2, next_cycle=7))
        specs[branch] = dict(root=str(branch_root), train_ids=[branch + '_one',branch + '_two'])
    common = root / 'common'
    shared.initialize(common, specs, candidate.reference(initial), initial_history={}, excluded_ids=['sealed'],
        prior_metrics=dict(optimizer_steps=1,child_token_exposures=0,anchor_token_exposures=0))
    shared.write(common / 'ADOPTION.json', dict(prior_history_preserved=True))
    if not (common / 'INITIALIZED.json').exists():
        shared.write(common / 'INITIALIZED.json', dict(real=True))
    state = shared.read(common / 'STATE.json')
    participants = {}
    for rank, branch in enumerate(shared.BRANCHES):
        messages = [dict(role='user',content='Visible parent advice; child-only target.')]
        rows = []
        for episode in specs[branch]['train_ids']:
            call = dict(task_id=episode,phase='experience',split='TRAIN',attached_readout=False,
                shared_generation=0,shared_checkpoint_sha256=state['checkpoint']['path_sha256'],
                response=dict(messages=messages,prompt_tokens=12,raw=episode,token_ids=[3,4],terminal=True,truncated=False))
            path = root / branch / (episode + '.json')
            shared.write(path,call)
            rows.append(dict(replay_mode=shared.replay.MODE,student_prefix=messages,
                source_prompt_sha256=shared.replay.history_policy.digest(messages),source_prompt_tokens=12,
                target=episode,target_sha256=shared.replay.history_policy.text_sha(episode),source_generated_token_ids=[3,4],
                append_eos=True,continuation_only=False,source_call_path=str(path),source_call_sha256=shared.sha(path),episode_id=episode))
        submission = shared.submit(common,branch,0,state['checkpoint']['path_sha256'],specs[branch]['train_ids'],rows)
        path = root / branch / 'SAFE.json'
        shared.write(path,dict(branch=branch,root=str(root / branch),generation=0,
            checkpoint_sha256=state['checkpoint']['path_sha256'],identity=identities[rank],status='SAFE_FOR_PARALLEL',
            bounds=dict(train_end_unix=candidate.TRAIN_END,hard_end_unix=candidate.HARD_END,
                        native_used=17,native_cap=1858,parent_used=2,parent_cap=298),
            preserved_files={'CARRY.json':shared.sha(root / branch / 'CARRY.json')},submission_sha256=submission['sha256']))
        participants[branch] = dict(path=str(path),sha256=shared.sha(path))
    activation = root / 'ACTIVATE.json'
    shared.write(activation,dict(schema=candidate.SCHEMA,status='ACTIVATE_PARALLEL_AT_SAFE_BOUNDARY',
        root=str(common),generation=0,pins={name:shared.sha(common / name)
            for name in ('CONFIG.json','STATE.json','ADOPTION.json','INITIALIZED.json')},
        source_files=source_files(),participants=participants,deadline_unix=candidate.TRAIN_END,commit_reserve_seconds=30))
    return activation


def real_worker(rank, rendezvous, folder):
    torch.set_num_threads(1)
    torch.distributed.init_process_group('gloo', init_method='file://' + rendezvous,
        rank=rank,world_size=8,timeout=timedelta(seconds=120))
    group = torch.distributed.group.WORLD
    assertions = unittest.TestCase()
    collective = candidate.Collectives(torch, group)
    identities = collective.gather(candidate.process_identity())
    from gpu import orch_r111_route_pair_shared as original
    try:
        for scenario in ('success','peer_failure','deadline','metadata_crash','missing_participant','optimizer_reset','held','existing_start','carry_tamper','worker_optimizer','late_start','wrong_rank'):
            root = Path(folder) / scenario
            torch.manual_seed(414)
            model = TinyModel()
            lora = [parameter for name,parameter in model.named_parameters() if parallel.is_lora(name)]
            optimizer = torch.optim.AdamW(lora,lr=.003) if rank == 0 else None
            if optimizer is not None:
                for parameter in lora:
                    parameter.grad = torch.ones_like(parameter)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            for parameter in lora:
                torch.distributed.broadcast(parameter.data,src=0)
            base = {name:parameter.detach().clone() for name,parameter in model.named_parameters() if not parallel.is_lora(name)}
            def verify_base():
                for name,parameter in model.named_parameters():
                    if name in base:
                        assertions.assertTrue(torch.equal(base[name],parameter))
            engine = SimpleNamespace(torch=torch,model=model,device='cpu',tokenizer=None,verify_base=verify_base)
            parameter_ids = [id(parameter) for parameter in model.parameters()]
            optimizer_id = id(optimizer)
            if rank == 0:
                root.mkdir()
                create_fixture(root,engine,optimizer,identities)
                if scenario == 'missing_participant':
                    activation = read_json(root / 'ACTIVATE.json')
                    activation['participants'].pop('A4')
                    shared.write(root / 'ACTIVATE.json',activation,replace=True)
                if scenario == 'held':
                    path = root / 'F2' / 'F2_one.json'
                    call = read_json(path)
                    call['split'] = 'DEV'
                    shared.write(path,call,replace=True)
                if scenario == 'existing_start':
                    shared.write(root / 'common/generation_000000/sleep/START.json',dict(serial=True))
                if scenario == 'carry_tamper':
                    shared.write(root / 'A4/CARRY.json',dict(native=0),replace=True)
                if scenario == 'optimizer_reset':
                    optimizer.state.clear()
            if scenario == 'worker_optimizer' and rank == 4:
                optimizer = torch.optim.AdamW(lora,lr=.003)
            torch.distributed.barrier()
            activation_path = root / 'ACTIVATE.json'
            activation_sha = shared.sha(activation_path)
            common = root / 'common'
            initial_state = read_json(common / 'STATE.json')
            calls = []
            ticks = [0]
            def check(stage):
                if stage == 'shared_parallel_optimizer_update':
                    ticks[0] += 1
                    if scenario == 'peer_failure' and rank == 4 and ticks[0] == 2:
                        raise RuntimeError('synthetic_peer_failure_after_one_real_step')
            def clock():
                return candidate.TRAIN_END if scenario == 'late_start' or scenario == 'deadline' and ticks[0] >= 1 else candidate.TRAIN_END - 3600
            def save(destination,generation,metrics):
                calls.append(generation)
                original.checkpoint(engine,optimizer,destination,7,7)
                return candidate.reference(destination)
            original_write = candidate.write
            def write_with_crash(path,value,replace=False):
                if scenario == 'metadata_crash' and Path(path) == common / 'STATE.json':
                    raise OSError('simulated_STATE_publication_crash')
                return original_write(path,value,replace=replace)
            try:
                with patch.object(parallel,'prepare_native_cohort',side_effect=fake_cohort), patch.object(candidate,'write',side_effect=write_with_crash):
                    result = candidate.consolidate(root=common,activation_path=activation_path,activation_sha256=activation_sha,
                        branch=shared.BRANCHES[(rank + 1) % 8] if scenario == 'wrong_rank' else shared.BRANCHES[rank],engine=engine,optimizer=optimizer,group=group,
                        anchor_module=None,anchors=[],anchor_root=root,save_checkpoint=save if rank == 0 else None,
                        check=check,clock=clock)
                assertions.assertEqual(scenario,'success')
                assertions.assertEqual(result['metrics']['optimizer_steps'],8)
                assertions.assertEqual(result['metrics']['child_token_exposures'],118)
                assertions.assertEqual(result['metrics']['anchor_token_exposures'],118)
                assertions.assertEqual(result['state']['optimizer_steps'],9)
                assertions.assertFalse(result['metrics']['serial_adamw_equivalent'])
                assertions.assertEqual(result['metrics']['completed_partial_batch_size'],3)
            except RuntimeError:
                if scenario == 'success':
                    raise
                assertions.assertEqual(read_json(common / 'STATE.json'),initial_state)
            torch.distributed.barrier()
            assertions.assertEqual(parameter_ids,[id(parameter) for parameter in model.parameters()])
            if scenario != 'worker_optimizer' or rank != 4:
                assertions.assertEqual(optimizer_id,id(optimizer))
            verify_base()
            if scenario == 'success':
                checkpoint = read_json(common / 'STATE.json')['checkpoint']
                payload = torch.load(Path(checkpoint['path']).parent / 'PARALLEL_RNG.pt',weights_only=False)
                with torch.no_grad():
                    for parameter in lora:
                        parameter.add_(1)
                if optimizer is not None:
                    for value in optimizer.state.values():
                        value['step'].add_(1)
                restored = candidate.restore_committed(root=common,engine=engine,optimizer=optimizer,
                    group=group,branch=shared.BRANCHES[rank],checkpoint_sha256=checkpoint['path_sha256'])
                assertions.assertEqual(restored['optimizer_updates_replayed'],0)
                assertions.assertEqual(parameter_ids,[id(parameter) for parameter in model.parameters()])
                assertions.assertEqual(optimizer_id,id(optimizer))
                assertions.assertTrue(torch.equal(torch.get_rng_state(),payload['rng'][rank]['cpu']))
                import random
                import numpy
                assertions.assertEqual(candidate.state_hash(random.getstate()),candidate.state_hash(payload['rng'][rank]['python']))
                assertions.assertEqual(candidate.state_hash(numpy.random.get_state()),candidate.state_hash(payload['rng'][rank]['numpy']))
                verify_base()
            torch.distributed.barrier()
            if rank == 0:
                output = common / 'generation_000000/sleep'
                if scenario in ('success','metadata_crash'):
                    assertions.assertEqual(calls,[1])
                    if scenario == 'metadata_crash':
                        before = {path.name:shared.sha(path) for path in (output / 'checkpoint').iterdir() if path.is_file()}
                        recovered = candidate.recover_complete(common,activation_path=activation_path,activation_sha256=activation_sha)
                        assertions.assertEqual(recovered['optimizer_updates_replayed'],0)
                        assertions.assertEqual(before,{path.name:shared.sha(path) for path in (output / 'checkpoint').iterdir() if path.is_file()})
                        assertions.assertEqual(candidate.recover_complete(common,activation_path=activation_path,
                            activation_sha256=activation_sha)['status'],'ALREADY_PUBLISHED')
                    state = read_json(common / 'STATE.json')
                    checkpoint = state['checkpoint']
                    candidate.verify_parallel_checkpoint(checkpoint)
                    selector.checkpoint_valid(checkpoint,common,read_json(common / 'CONFIG.json'))
                    pins = read_json(activation_path)['pins']
                    selection = selector.select(common,config_sha256=pins['CONFIG.json'],
                        initialized_sha256=pins['INITIALIZED.json'],adoption_sha256=pins['ADOPTION.json'],
                        clock=lambda:selector.CUT + 1)
                    assertions.assertEqual(selection['shared_metrics']['optimizer_steps'],8)
                    payload = torch.load(Path(checkpoint['path']).parent / 'PARALLEL_RNG.pt',weights_only=False)
                    assertions.assertEqual(len(payload['rng']),8)
                    assertions.assertEqual({int(value['step']) for value in optimizer.state.values()},{9})
                    assertions.assertNotIn('checkpoint.pending',read_json(checkpoint['path'])['adapter']['path'])
                    if scenario == 'success':
                        assertions.assertEqual(len(read_json(output / 'ALL8_RELOAD.json')['acknowledgments']),8)
                else:
                    assertions.assertEqual(calls,[])
                    if scenario in ('peer_failure','deadline'):
                        assertions.assertTrue((output / 'FAILED.json').exists())
                        assertions.assertEqual(len(list((output / 'updates').glob('*.json'))),1)
                        with assertions.assertRaisesRegex(ValueError,'existing_sleep'):
                            candidate.validate_activation(common,activation_path,activation_sha,clock=lambda:candidate.TRAIN_END - 3600)
                    with assertions.assertRaises((ValueError,FileNotFoundError)):
                        candidate.recover_complete(common,activation_path=activation_path,activation_sha256=activation_sha)
                shared.write(root / 'RESULT.json',dict(scenario=scenario,passed=True,rank0_existing_optimizer=id(optimizer)==optimizer_id,
                    actual_optimizer_steps=sorted({int(value['step']) for value in optimizer.state.values()}),
                    native_validator=True,original_serializer=True,synthetic_encoder=True,
                    committed_all8_rng_inplace_restore=scenario=='success',cuda_initialized=torch.cuda.is_initialized()))
            torch.distributed.barrier()
        if rank == 0:
            path = os.environ.get('R118_PARALLEL_PROOF')
            if path:
                shared.write(path,dict(schema=candidate.SCHEMA,eight_real_gloo_ranks=True,
                    scenarios=[read_json(path) for path in sorted(Path(folder).glob('*/RESULT.json'))],
                    native_original_serializer=True,synthetic_encoded_rows=True,live_COMMON_untouched=True))
    finally:
        torch.distributed.destroy_process_group()


def read_json(path):
    return json.loads(Path(path).read_text())


def wait_file(path, seconds=30):
    deadline=time.monotonic()+seconds
    while not Path(path).exists():
        if time.monotonic()>=deadline:
            raise TimeoutError('CPU_fixture_coordination_timeout')
        time.sleep(.02)


def launch_worker(rank, folder, guard_identity):
    torch.set_num_threads(1)
    assertions=unittest.TestCase()
    base_root=Path(folder)
    shared.write(base_root / f'IDENTITY_{rank}.json',candidate.process_identity())
    from gpu import orch_r111_route_pair_shared as original
    for scenario in ('launch_success','group_peer_failure','missing_join','existing_group'):
        root=base_root / scenario
        if rank==0:
            root.mkdir()
        wait_file(root)
        torch.manual_seed(414)
        model=TinyModel()
        lora={name:parameter for name,parameter in model.named_parameters() if parallel.is_lora(name)}
        optimizer=torch.optim.AdamW(list(lora.values()),lr=.003) if rank==0 else None
        if optimizer is not None:
            for parameter in lora.values():
                parameter.grad=torch.ones_like(parameter)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        base={name:parameter.detach().clone() for name,parameter in model.named_parameters() if name not in lora}
        def verify_base():
            for name,parameter in model.named_parameters():
                if name in base:
                    assertions.assertTrue(torch.equal(base[name],parameter))
        engine=SimpleNamespace(torch=torch,model=model,device='cpu',tokenizer=None,verify_base=verify_base)
        parameter_ids=[id(parameter) for parameter in model.parameters()]
        optimizer_id=id(optimizer)
        if rank==0:
            identities=[]
            for member in range(8):
                wait_file(base_root / f'IDENTITY_{member}.json')
                identities.append(read_json(base_root / f'IDENTITY_{member}.json'))
            old_activation=create_fixture(root,engine,optimizer,identities)
            old=read_json(old_activation)
            participants={}
            for member,branch in enumerate(shared.BRANCHES):
                previous=read_json(old['participants'][branch]['path'])
                policy=root / branch / 'FINAL_POLICY_BINDING.json'
                shared.write(policy,dict(native_identity=identities[member],guard_identity=guard_identity,
                    hard_end_unix=candidate.HARD_END,original_lease_preserved=True,synthetic_identity_fixture=True))
                evidence=dict(path=str(policy),sha256=shared.sha(policy))
                previous.update(launch_device=dict(kind='cpu',physical=member,cuda_visible_devices=''),
                    retained_supervision=dict(native_identity=identities[member],guard_identity=guard_identity,
                        guard_binding=evidence,final_identity_bindings=[dict(identity=identities[member],evidence=evidence)],
                        owner_verified_safe_for_parallel=True))
                path=root / branch / 'SAFE_LAUNCH.json'
                shared.write(path,previous)
                participants[branch]=dict(path=str(path),sha256=shared.sha(path))
            plan=candidate.prepare_launch_plan(root=root / 'common',output=root / 'launch/LAUNCH_PLAN.json',generation=0,
                pins={name:digest for name,digest in old['pins'].items() if name!='STATE.json'},source_files=source_files(),
                deadline_unix=candidate.TRAIN_END,mode='CPU_TEST_ONLY',join_timeout_seconds=5 if scenario=='missing_join' else 30,
                collective_timeout_seconds=30,commit_reserve_seconds=30)
            activated=candidate.arm_launch(plan_path=plan['path'],plan_sha256=plan['sha256'],participants=participants)
            shared.write(root / 'ARMED_REFERENCE.json',activated)
        wait_file(root / 'ARMED_REFERENCE.json')
        activation=read_json(root / 'ARMED_REFERENCE.json')
        if rank!=0:
            saved=torch.load(root / 'F1/initial/adapter/adapter_model.pt',weights_only=False)
            with torch.no_grad():
                for name,parameter in lora.items():
                    parameter.copy_(saved[name])
        initial_state=read_json(root / 'common/STATE.json')
        def check(stage):
            if scenario=='group_peer_failure' and rank==6 and stage=='shared_parallel_optimizer_update':
                raise RuntimeError('fixture_peer_failure_after_real_Gloo_join')
        def save(destination,generation,metrics):
            original.checkpoint(engine,optimizer,destination,7,7)
            return candidate.reference(destination)
        old_interface=os.environ.get('GLOO_SOCKET_IFNAME')
        if scenario=='existing_group':
            torch.distributed.init_process_group('gloo',init_method=(root / 'OWNER_GROUP').as_uri(),
                rank=rank,world_size=8,timeout=timedelta(seconds=30))
        if scenario=='missing_join' and rank==7:
            for member in range(7):
                wait_file(root / f'DONE_{member}.json',seconds=30)
        else:
            try:
                with patch.object(parallel,'prepare_native_cohort',side_effect=fake_cohort):
                    result=candidate.launch_at_boundary(activation_path=activation['path'],activation_sha256=activation['sha256'],
                        branch=shared.BRANCHES[rank],engine=engine,optimizer=optimizer,anchor_module=None,anchor_root=root,
                        anchors=[],save_checkpoint=save if rank==0 else None,check=check)
                assertions.assertEqual(scenario,'launch_success')
                assertions.assertEqual(result['metrics']['optimizer_steps'],8)
                assertions.assertEqual(result['state']['optimizer_steps'],9)
            except (RuntimeError,ValueError):
                if scenario=='launch_success':
                    raise
                assertions.assertEqual(initial_state,read_json(root / 'common/STATE.json'))
            if scenario=='existing_group':
                assertions.assertTrue(torch.distributed.is_initialized())
                torch.distributed.barrier()
                torch.distributed.destroy_process_group()
            assertions.assertFalse(torch.distributed.is_initialized())
            assertions.assertEqual(os.environ.get('GLOO_SOCKET_IFNAME'),old_interface)
            assertions.assertEqual(parameter_ids,[id(parameter) for parameter in model.parameters()])
            assertions.assertEqual(optimizer_id,id(optimizer))
            assertions.assertFalse(torch.cuda.is_initialized())
            verify_base()
        shared.write(root / f'DONE_{rank}.json',dict(rank=rank,optimizer_present=optimizer is not None,
            parameter_identity_preserved=True,optimizer_identity_preserved=True,group_destroyed=not torch.distributed.is_initialized(),
            cuda_initialized=torch.cuda.is_initialized(),optimizer_step_values=sorted({int(value['step']) for value in optimizer.state.values()}) if optimizer else []))
        for member in range(8):
            wait_file(root / f'DONE_{member}.json')
        if rank==0:
            report=candidate.launch_status(activation['path'],activation['sha256'])
            assertions.assertEqual(len(report['joined']),0 if scenario=='existing_group' else 7 if scenario=='missing_join' else 8)
            assertions.assertEqual(len(report['returned']),8 if scenario=='launch_success' else 0)
            assertions.assertEqual(len(report['failures']),0 if scenario in ('launch_success','existing_group') else 7 if scenario=='missing_join' else 8)
            if scenario=='missing_join':
                assertions.assertFalse((root / 'launch/RENDEZVOUS').exists())
                assertions.assertFalse((root / 'common/generation_000000/sleep/START.json').exists())
            for branch in shared.BRANCHES:
                certificate=read_json(root / branch / 'SAFE_LAUNCH.json')
                candidate.validate_launch_participant(certificate,branch,'CPU_TEST_ONLY')
            shared.write(root / 'LAUNCH_PROOF.json',dict(scenario=scenario,passed=True,status=report,
                ranks=[read_json(root / f'DONE_{member}.json') for member in range(8)],
                model_processes_spawned_by_candidate=0,actors_signalled=0,
                original_final_identity_files_unchanged=True,same_existing_F1_AdamW=True,peer_optimizers=0))
        wait_file(root / 'LAUNCH_PROOF.json')
    if rank==0 and os.environ.get('R118_LAUNCH_PROOF'):
        shared.write(os.environ['R118_LAUNCH_PROOF'],dict(schema=candidate.LAUNCH_SCHEMA,
            scenarios=[read_json(path) for path in sorted(base_root.glob('*/LAUNCH_PROOF.json'))],
            real_inprocess_Gloo_startup=True,device='cpu',synthetic_model_and_identity_policy=True))


@unittest.skipUnless(torch is not None,'native CPU torch required')
class RealCollectiveTests(unittest.TestCase):
    def test_eight_rank_commit_failures_and_selector(self):
        with tempfile.TemporaryDirectory(prefix='r118_parallel_cpu_') as folder:
            torch.multiprocessing.start_processes(real_worker,args=(str(Path(folder) / 'rendezvous'),folder),
                nprocs=8,start_method='spawn',join=True)

    def test_inprocess_Gloo_launch_success_failure_and_missing_peer(self):
        self.assertEqual(os.environ.get('CUDA_VISIBLE_DEVICES'),'')
        with tempfile.TemporaryDirectory(prefix='r118_inplace_launch_cpu_') as folder:
            torch.multiprocessing.start_processes(launch_worker,args=(folder,candidate.process_identity()),
                nprocs=8,start_method='spawn',join=True)


def fresh_fixture(folder, parallel_rng=False, postcommit=False, pending=False):
    root = Path(folder)
    torch.manual_seed(414)
    model = TinyModel()
    lora = [parameter for name,parameter in model.named_parameters() if parallel.is_lora(name)]
    optimizer = torch.optim.AdamW(lora,lr=.02,betas=(.9,.95),weight_decay=.01)
    for parameter in lora:
        parameter.grad = torch.full_like(parameter,.125)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    engine = SimpleNamespace(torch=torch,model=model,device='cpu',tokenizer=None,verify_base=lambda:None)
    create_fixture(root,engine,optimizer,[candidate.process_identity()] * 8)
    common = root / 'common'
    state = read_json(common / 'STATE.json')
    checkpoint = state['checkpoint']
    if parallel_rng:
        import numpy
        folder = Path(checkpoint['path']).parent
        original = torch.load(checkpoint['optimizer_path'],weights_only=False)
        rngs = []
        for rank in range(8):
            random.seed(701 + rank)
            numpy.random.seed(801 + rank)
            torch.manual_seed(901 + rank)
            rngs.append(dict(python=random.getstate(),numpy=numpy.random.get_state(),
                             cpu=original['cpu_rng'] if rank == 0 else torch.get_rng_state(),cuda=None))
        payload = dict(rng=rngs,optimizer=original['optimizer'],lora={name:parameter.detach() for name,parameter in model.named_parameters() if parallel.is_lora(name)})
        torch.save(payload,folder / 'PARALLEL_RNG.pt')
        shared.write(folder / 'PARALLEL.json',dict(parallel_rng_sha256=shared.sha(folder / 'PARALLEL_RNG.pt'),
            ranks=[dict(branch=branch,rng_sha256=candidate.state_hash(rngs[rank])) for rank,branch in enumerate(shared.BRANCHES)],serial_adamw_equivalent=False))
        document = read_json(checkpoint['path'])
        document['parallel'] = dict(schema=candidate.SCHEMA,manifest_sha256=shared.sha(folder / 'PARALLEL.json'),payload_sha256=shared.sha(folder / 'PARALLEL_RNG.pt'))
        shared.write(checkpoint['path'],document,replace=True)
        checkpoint = candidate.reference(folder)
    source_checkpoint = state['checkpoint']
    state = candidate.advance_state(state,checkpoint,dict.fromkeys(shared.METRICS,0))
    shared.write(common / 'STATE.json',state,replace=True)
    shared.write(common / 'generation_000000/sleep/COMPLETE.json',dict(state=state,same_optimizer=True,source_checkpoint=source_checkpoint))
    predecessor = subprocess.Popen([sys.executable,'-c','pass'])
    identity = dict(candidate.process_identity(),pid=predecessor.pid)
    predecessor.wait(timeout=10)
    owners = {}
    sources = source_files()
    for rank,branch in enumerate(shared.BRANCHES):
        branch_root = root / branch
        bounds = dict(train_end_unix=candidate.TRAIN_END,hard_end_unix=candidate.HARD_END,
                      native_used=17,native_cap=1858,parent_used=2,parent_cap=298)
        shared.write(branch_root / 'DEV.json',dict(fresh=True,checkpoint_sha256=checkpoint['path_sha256'],test_fixture=True))
        shared.write(branch_root / 'RELEASE.json',dict(status='RELEASED'))
        preserved = {name:shared.sha(branch_root / name) for name in ('CARRY.json','DEV.json')}
        handoff = branch_root / 'HANDOFF.json'
        shared.write(handoff,dict(root=str(branch_root),bounds=bounds,release=dict(path=str(branch_root / 'RELEASE.json'),sha256=shared.sha(branch_root / 'RELEASE.json')),
            predecessors=[identity],preserved_files=preserved,next_cycle=7))
        owners[branch] = dict(handoff=dict(path=str(handoff),sha256=shared.sha(handoff)),inherited_bounds=bounds,
            boundary=dict(committed_checkpoint_sha256=checkpoint['path_sha256'],mounted_checkpoint_sha256=checkpoint['path_sha256'],
                fresh_dev=dict(path=str(branch_root / 'DEV.json'),sha256=preserved['DEV.json']),
                settled_cursor=dict(path=str(branch_root / 'CARRY.json'),sha256=preserved['CARRY.json'])),
            command=[sys.executable,'-m','tests.test_orch_r118_parallel_consolidation','--fresh-cpu-worker'],
            cwd=str(Path.cwd()),env=dict(CUDA_VISIBLE_DEVICES='',R118_FRESH_CPU_ROOT=str(root)),source_files=sources,
            bootstrap_path=str(branch_root / 'BOOTSTRAP.json'),device=dict(kind='cpu',physical=rank))
    if postcommit:
        for branch in ('F1','F2','A1','A2'):
            postcommit_fixture(root,owners[branch],branch,state)
    if pending:
        pending_fixture(root,owners['F3'],'F3',state,published=True)
        pending_fixture(root,owners['A4'],'A4',state,published=False)
    return dict(root=common,output=root / 'fresh/SESSION.json',owners=owners,source_files=sources,
                startup_deadline_unix=min(time.time()+90,candidate.TRAIN_END),mode='cpu')


def postcommit_fixture(root, owner, branch, state):
    branch_root = root / branch
    def ref(path):
        return dict(path=str(path),sha256=shared.sha(path))
    terminal = branch_root / 'FAILED_NATIVE.json'
    shared.write(terminal,dict(status='FAILED',error='ordering_only_reload_or_interrupted_eval',charged_calls_retained=True))
    previous = root / 'common/generation_000000'
    disposition = branch_root / 'POSTCOMMIT_EVAL.json'
    shared.write(disposition,dict(schema='R118_POSTCOMMIT_EVAL_DISPOSITION_V1',status='TERMINAL_POSTCOMMIT_EVALUATION',
        root=str(branch_root),branch=branch,generation=state['generation'],checkpoint_sha256=state['checkpoint']['path_sha256'],
        accepted_submission=ref(previous / (branch + '.json')),committed_sleep=ref(previous / 'sleep/COMPLETE.json'),
        native_terminal=ref(terminal),evaluations=dict(DEV='FAILED',OPEN='NOT_ATTEMPTED'),
        evaluation_evidence=[ref(terminal)],replay_train=False))
    cursor = branch_root / 'RECOVERED_CURSOR.json'
    shared.write(cursor,dict(schema='R118_POSTCOMMIT_RECOVERED_CURSOR_V1',root=str(branch_root),branch=branch,
        accepted_generation=0,accepted_submission_sha256=shared.sha(previous / (branch + '.json')),
        checkpoint_sha256=state['checkpoint']['path_sha256'],completed_train_cycle=6,next_cycle=7,
        native_used=17,parent_used=2,pending_train_calls=[],pending_train_submissions=[],action='NEXT_NEW_CYCLE_AFTER_CANONICAL_BOOTSTRAP'))
    envelope = read_json(owner['handoff']['path'])
    for path in (terminal,disposition,cursor):
        envelope['preserved_files'][path.name] = shared.sha(path)
    shared.write(owner['handoff']['path'],envelope,replace=True)
    owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
    owner['boundary'] = dict(committed_checkpoint_sha256=state['checkpoint']['path_sha256'],mounted_checkpoint_sha256=None,
        canonical_reload_required=True,postcommit_eval_disposition=ref(disposition),settled_cursor=ref(cursor))


def pending_fixture(root, owner, branch, state, published):
    from copy import deepcopy
    branch_root = root / branch
    def ref(path):
        return dict(path=str(path),sha256=shared.sha(path))
    prior = read_json(root / 'common/generation_000000' / (branch + '.json'))
    rows, terminals = [], []
    for row in prior['rows']:
        row = deepcopy(row)
        call = read_json(row['source_call_path'])
        call.update(shared_generation=state['generation'],shared_checkpoint_sha256=state['checkpoint']['path_sha256'])
        path = branch_root / ('PENDING_' + row['episode_id'] + '.json')
        shared.write(path,call)
        row.update(source_call_path=str(path),source_call_sha256=shared.sha(path))
        rows.append(row)
        terminals.append(dict(ref(path),status='COMPLETE'))
    row_path = branch_root / 'PENDING_ROWS.json'
    shared.write(row_path,dict(rows=rows))
    complete = branch_root / 'TWO_EPISODES_COMPLETE.json'
    shared.write(complete,dict(episode_ids=prior['episode_ids'],status='COMPLETE',synthetic_CPU_fixture=True))
    submission = shared.submit(root / 'common',branch,state['generation'],state['checkpoint']['path_sha256'],prior['episode_ids'],rows) if published else None
    pending = branch_root / 'PENDING_CONSOLIDATION.json'
    shared.write(pending,dict(schema='R118_SETTLED_PENDING_CONSOLIDATION_V1',status='SETTLED_PENDING_CONSOLIDATION',
        root=str(branch_root),branch=branch,generation=state['generation'],checkpoint_sha256=state['checkpoint']['path_sha256'],
        cycle=7,episode_ids=prior['episode_ids'],episode_completions=[dict(episode_id=episode,status='COMPLETE',evidence=ref(complete)) for episode in prior['episode_ids']],
        rows=ref(row_path),terminal_calls=terminals,submission=submission,trained=False,replay_calls=False))
    cursor = branch_root / 'PENDING_CURSOR.json'
    shared.write(cursor,dict(schema='R118_PENDING_CONSOLIDATION_CURSOR_V1',root=str(branch_root),branch=branch,
        generation=state['generation'],checkpoint_sha256=state['checkpoint']['path_sha256'],cycle=7,next_cycle=8,native_used=19,parent_used=2,
        inflight_native_calls=[],inflight_parent_calls=[],action='RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS'))
    shared.write(branch_root / 'CARRY.json',dict(native=19,parent=2,next_cycle=8),replace=True)
    envelope = read_json(owner['handoff']['path'])
    envelope['next_cycle'] = 8
    envelope['bounds']['native_used'] = 19
    owner['inherited_bounds']['native_used'] = 19
    for path in (pending,cursor,row_path,complete,branch_root / 'CARRY.json',*(Path(item['path']) for item in terminals)):
        envelope['preserved_files'][path.name] = shared.sha(path)
    shared.write(owner['handoff']['path'],envelope,replace=True)
    owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
    owner['boundary'] = dict(committed_checkpoint_sha256=state['checkpoint']['path_sha256'],mounted_checkpoint_sha256=None,
        canonical_reload_required=True,settled_pending_consolidation=ref(pending),settled_cursor=ref(cursor))


def fresh_cpu_worker():
    torch.set_num_threads(1)
    root = Path(os.environ['R118_FRESH_CPU_ROOT'])
    branch = os.environ['R118_PARALLEL_BRANCH']
    torch.manual_seed(999)
    model = TinyModel()
    state = read_json(root / 'common/STATE.json')
    checkpoint = read_json(state['checkpoint']['path'])
    adapter = torch.load(Path(checkpoint['adapter']['path']) / 'adapter_model.pt',weights_only=False)
    with torch.no_grad():
        for name,parameter in model.named_parameters():
            if name in adapter:
                parameter.copy_(adapter[name])
    base = {name:parameter.detach().clone() for name,parameter in model.named_parameters() if not parallel.is_lora(name)}
    def verify_base():
        assert all(torch.equal(base[name],parameter) for name,parameter in model.named_parameters() if name in base)
    lora = [parameter for name,parameter in model.named_parameters() if parallel.is_lora(name)]
    optimizer = torch.optim.AdamW(lora,lr=.987,betas=(.4,.5)) if branch == 'F1' else None
    optimizer_id = id(optimizer)
    engine = SimpleNamespace(torch=torch,model=model,device='cpu',tokenizer=None,verify_base=verify_base)
    session = dict(session_path=Path(os.environ['R118_PARALLEL_SESSION']),session_sha256=os.environ['R118_PARALLEL_SESSION_SHA256'])
    receipt = candidate.bootstrap_fresh_actor(root=root / 'common',branch=branch,engine=engine,optimizer=optimizer,**session)
    assert optimizer_id == id(optimizer)
    with unittest.TestCase().assertRaisesRegex(ValueError,'once_no_rng_reset'):
        candidate.bootstrap_fresh_actor(root=root / 'common',branch=branch,engine=engine,optimizer=optimizer,**session)
    if optimizer is not None:
        original = torch.load(state['checkpoint']['optimizer_path'],weights_only=False)
        assert candidate.state_hash(optimizer.state_dict()) == candidate.state_hash(original['optimizer'])
        assert optimizer.param_groups[0]['lr'] == .02
        assert receipt['torch_cpu_rng_sha256'] == candidate.state_hash(original['cpu_rng'])
    candidate.wait_fresh_collection_go(branch=branch,**session)
    if receipt['startup_action'] == 'RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS':
        original_submit = shared.submit
        with patch.object(shared,'submit',wraps=original_submit) as submit:
            resumed = candidate.resume_pending_consolidation(root=root / 'common',branch=branch,**session)
            assert resumed['new_native_calls'] == resumed['optimizer_updates'] == 0
            assert submit.call_count == int(branch == 'A4')
            with unittest.TestCase().assertRaises((ValueError,FileExistsError)):
                candidate.resume_pending_consolidation(root=root / 'common',branch=branch,**session)
            assert submit.call_count == int(branch == 'A4')
        shared.write(root / branch / 'PENDING_INPUT_READY.json',{key:value for key,value in resumed.items() if key != 'rows'})
    shared.write(root / branch / 'COLLECTION_ALLOWED.json',dict(identity=candidate.process_identity(),receipt=receipt))
    while not (root / 'TEST_EXIT.json').exists():
        if time.time() > read_json(session['session_path'])['startup_deadline_unix']:
            raise TimeoutError('test_cleanup_deadline')
        time.sleep(.1)


@unittest.skipUnless(torch is not None,'native CPU torch required')
class FreshExecTests(unittest.TestCase):
    def test_campaign_auto_arms_two_generations_and_never_retries_failed_arm(self):
        for fail in (False,True):
            with tempfile.TemporaryDirectory(prefix='r118_campaign_cpu_') as folder:
                request = fresh_fixture(folder)
                session = candidate.publish_fresh_sessions(**request)
                root = request['root']
                campaign = candidate.prepare_campaign(root=root,output=Path(folder) / 'campaign/CAMPAIGN.json',first_generation=1,
                    pins={name:shared.sha(root / name) for name in ('CONFIG.json','ADOPTION.json','INITIALIZED.json')},
                    source_files=request['source_files'],activation_directory=Path(folder) / 'inbox',safe_directory=Path(folder) / 'safe',
                    deadline_unix=candidate.TRAIN_END,mode='CPU_TEST_ONLY',commit_reserve_seconds=30)
                _, dispatch = candidate.fresh_session(session['path'],session['sha256'])
                shared.write(dispatch / 'GO.json',dict(status='ALL8_BOOTSTRAPPED_COLLECTION_GO',session_sha256=session['sha256'],
                    bootstraps=dict.fromkeys(shared.BRANCHES,{'synthetic_unit_fixture':True})))
                now = [time.time()]
                def publish_inputs(generation):
                    state = read_json(root / 'STATE.json')
                    for branch in shared.BRANCHES:
                        certificate = Path(folder) / branch / f'SAFE_{generation}.json'
                        shared.write(certificate,dict(branch=branch,generation=generation,status='SAFE_FOR_PARALLEL',
                            checkpoint_sha256=state['checkpoint']['path_sha256'],identity=candidate.process_identity()))
                        binding = dict(path=str(certificate),sha256=shared.sha(certificate))
                        candidate.publish_campaign_safe(campaign['path'],campaign['sha256'],branch,binding)
                        shared.write(root / f'generation_{generation:06d}' / (branch + '.json'),dict(native_validator_covered_in_real_collective_tests=True))
                publish_inputs(1)
                armed = []
                def arm(**kwargs):
                    plan = read_json(kwargs['plan_path'])
                    armed.append(plan['generation'])
                    if fail:
                        raise ValueError('fixture_failed_join_no_retry')
                    path = Path(kwargs['plan_path']).parent / 'ACTIVATION.json'
                    shared.write(path,dict(generation=plan['generation'],participants=kwargs['participants'],
                        launch=dict(join_deadline_unix=candidate.TRAIN_END)))
                    return dict(path=str(path),sha256=shared.sha(path))
                def advance(seconds):
                    state = read_json(root / 'STATE.json')
                    generation = state['generation']
                    advanced = candidate.advance_state(state,state['checkpoint'],dict.fromkeys(shared.METRICS,1))
                    shared.write(root / f'generation_{generation:06d}/sleep/COMPLETE.json',dict(state=advanced,same_optimizer=True))
                    shared.write(root / 'STATE.json',advanced,replace=True)
                    if generation == 1:
                        publish_inputs(2)
                    else:
                        now[0] = candidate.TRAIN_END
                arguments = dict(campaign_path=campaign['path'],campaign_sha256=campaign['sha256'],
                    session_path=session['path'],session_sha256=session['sha256'],clock=lambda:now[0],pause=advance)
                with patch.object(candidate,'arm_launch',side_effect=arm):
                    if fail:
                        with self.assertRaisesRegex(ValueError,'fixture_failed_join'):
                            candidate.watch_campaign(**arguments)
                        self.assertEqual(armed,[1])
                        self.assertFalse((Path(folder) / 'inbox/generation_000001.ref.json').exists())
                    else:
                        self.assertEqual(candidate.watch_campaign(**arguments)['status'],'DEADLINE_NO_MORE_ARMS')
                        self.assertEqual(armed,[1,2])
                        self.assertTrue((Path(folder) / 'inbox/generation_000002.ref.json').exists())
                    with self.assertRaises((FileExistsError,ValueError)):
                        candidate.watch_campaign(**arguments)

    def test_all8_real_fresh_exec_optimizer_and_rng(self):
        proofs = []
        for sidecar, recovery, pending in ((False,False,False),(True,False,False),(False,True,False),(False,True,True)):
            with tempfile.TemporaryDirectory(prefix='r118_fresh_exec_') as folder:
                request = fresh_fixture(folder,sidecar,recovery,pending)
                published = candidate.publish_fresh_sessions(**request)
                before = {str(path):shared.sha(path) for path in request['root'].rglob('*') if path.is_file() and path.name != 'COORDINATOR.lock'}
                try:
                    result = candidate.dispatch_fresh_sessions(session_path=published['path'],session_sha256=published['sha256'])
                    self.assertEqual(len(result['bootstraps']),8)
                    for branch in shared.BRANCHES:
                        wait_file(Path(folder) / branch / 'COLLECTION_ALLOWED.json')
                    receipts = [read_json(item['path']) for item in result['bootstraps'].values()]
                    self.assertEqual(sum(receipt['optimizer_count'] for receipt in receipts),1)
                    self.assertEqual(len({receipt['identity']['pid'] for receipt in receipts}),8)
                    after = {str(path):shared.sha(path) for path in request['root'].rglob('*') if path.is_file() and path.name != 'COORDINATOR.lock'}
                    if pending:
                        after.pop(str(request['root'] / 'generation_000001/A4.json'))
                        existing = read_json(Path(folder) / 'F3/PENDING_INPUT_READY.json')
                        unpublished = read_json(Path(folder) / 'A4/PENDING_INPUT_READY.json')
                        self.assertTrue(existing['existing_submission_reused'])
                        self.assertFalse(unpublished['existing_submission_reused'])
                        self.assertEqual(existing['generation'],1)
                        self.assertEqual(unpublished['cycle'],7)
                    self.assertEqual(before,after)
                    if sidecar:
                        payload = torch.load(Path(request['root']) .parent / 'F1/initial/PARALLEL_RNG.pt',weights_only=False)
                        self.assertTrue(all(receipt['rng_provenance'] == 'RESTORED_ALL8_PARALLEL_SIDECAR' and receipt['new_stream_seed'] is None for receipt in receipts))
                        for receipt in receipts:
                            self.assertEqual(receipt['rng_sha256'],candidate.state_hash(payload['rng'][receipt['rank']]))
                    else:
                        self.assertEqual(len({receipt['new_stream_seed'] for receipt in receipts}),8)
                        self.assertTrue(all('NOT_OLD_PEER_RNG' in receipt['rng_provenance'] for receipt in receipts if receipt['branch'] != 'F1'))
                    with self.assertRaises((FileExistsError,ValueError)):
                        candidate.dispatch_fresh_sessions(session_path=published['path'],session_sha256=published['sha256'])
                    if recovery:
                        self.assertEqual(sum(receipt['postcommit_eval_disposition'] is not None for receipt in receipts),4)
                        self.assertTrue(all(receipt['canonical_adapter_actually_verified'] for receipt in receipts))
                    proofs.append(dict(sidecar=sidecar,postcommit_recovery=recovery,pending_catchup=pending,
                        all8_fresh_exec=True,receipts=receipts,common_unchanged=not pending,canonical_STATE_unchanged=True,
                        pending_publications=int(pending),all8_GO_before_new_submission=True))
                finally:
                    shared.write(Path(folder) / 'TEST_EXIT.json',dict(stop=True))
                    control = Path(published['path']).parent / 'SESSION.dispatch'
                    for path in control.glob('*.EXEC.json'):
                        try:
                            os.waitpid(read_json(path)['pid'],0)
                        except ChildProcessError:
                            pass
        if os.environ.get('R118_FRESH_PROOF'):
            shared.write(os.environ['R118_FRESH_PROOF'],dict(scenarios=proofs,native_GPU_tested=False))

    def test_preflight_rejects_live_predecessor_and_missing_owner_before_spawn(self):
        with tempfile.TemporaryDirectory(prefix='r118_fresh_reject_') as folder:
            request = fresh_fixture(folder)
            owner = request['owners']['A4']
            envelope = read_json(owner['handoff']['path'])
            envelope['predecessors'] = [candidate.process_identity()]
            shared.write(owner['handoff']['path'],envelope,replace=True)
            owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
            with patch.object(candidate.subprocess,'Popen') as spawn:
                with self.assertRaisesRegex(ValueError,'predecessor_still_live'):
                    candidate.publish_fresh_sessions(**request)
                spawn.assert_not_called()
            request['owners'].pop('A4')
            with self.assertRaisesRegex(ValueError,'all8_owners'):
                candidate.publish_fresh_sessions(**request)

    def test_failed_exec_terminal_prevents_retry_and_GO(self):
        with tempfile.TemporaryDirectory(prefix='r118_fresh_failed_') as folder:
            request = fresh_fixture(folder)
            request['owners']['F1']['command'] = ['/nonexistent-r118-cpu-test-command']
            published = candidate.publish_fresh_sessions(**request)
            with self.assertRaises(FileNotFoundError):
                candidate.dispatch_fresh_sessions(session_path=published['path'],session_sha256=published['sha256'])
            control = Path(published['path']).parent / 'SESSION.dispatch'
            self.assertTrue((control / 'FAILED.json').exists())
            self.assertFalse((control / 'GO.json').exists())
            with self.assertRaises(FileExistsError):
                candidate.dispatch_fresh_sessions(session_path=published['path'],session_sha256=published['sha256'])


    def test_postcommit_disposition_rejects_partial_checkpoint_and_uncommitted_STATE(self):
        for scenario in ('partial_checkpoint','uncommitted_STATE','missing_COMPLETE','unfinished_sleep','new_submission'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory(prefix='r118_postcommit_reject_') as folder:
                request = fresh_fixture(folder,postcommit=True)
                root = request['root']
                state = read_json(root / 'STATE.json')
                if scenario == 'partial_checkpoint':
                    path = Path(state['checkpoint']['path'])
                    document = read_json(path)
                    document['complete'] = False
                    shared.write(path,document,replace=True)
                    state['checkpoint']['path_sha256'] = shared.sha(path)
                    shared.write(root / 'STATE.json',state,replace=True)
                elif scenario == 'uncommitted_STATE':
                    shared.write(root / 'STATE.json',dict(state,generation=0),replace=True)
                elif scenario == 'missing_COMPLETE':
                    (root / 'generation_000000/sleep/COMPLETE.json').unlink()
                elif scenario == 'unfinished_sleep':
                    shared.write(root / 'generation_000001/sleep/START.json',dict(partial_training=True))
                else:
                    shared.write(root / 'generation_000001/F1.json',dict(new_training_submission=True))
                with patch.object(candidate.subprocess,'Popen') as spawn:
                    with self.assertRaises((ValueError,FileNotFoundError)):
                        candidate.publish_fresh_sessions(**request)
                    spawn.assert_not_called()

    def test_postcommit_disposition_rejects_pending_TRAIN_replay_and_charge_reset(self):
        for field,value in (('pending_train_calls',['unfinished']),('pending_train_submissions',['unfinished']),
                            ('next_cycle',6),('native_used',0),('parent_used',0),('accepted_generation',1)):
            with self.subTest(field=field), tempfile.TemporaryDirectory(prefix='r118_postcommit_cursor_') as folder:
                request = fresh_fixture(folder,postcommit=True)
                owner = request['owners']['F1']
                binding = owner['boundary']['settled_cursor']
                cursor = read_json(binding['path'])
                cursor[field] = value
                shared.write(binding['path'],cursor,replace=True)
                binding['sha256'] = shared.sha(binding['path'])
                envelope = read_json(owner['handoff']['path'])
                envelope['preserved_files'][Path(binding['path']).name] = binding['sha256']
                shared.write(owner['handoff']['path'],envelope,replace=True)
                owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
                with self.assertRaises(ValueError):
                    candidate.publish_fresh_sessions(**request)

    def test_postcommit_disposition_rejects_fake_clean_eval_and_wrong_trained_submission(self):
        for scenario in ('fake_clean_eval','wrong_submission','replay_train'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory(prefix='r118_postcommit_evidence_') as folder:
                request = fresh_fixture(folder,postcommit=True)
                owner = request['owners']['F1']
                binding = owner['boundary']['postcommit_eval_disposition']
                disposition = read_json(binding['path'])
                if scenario == 'fake_clean_eval':
                    disposition['evaluations'] = dict(DEV='COMPLETE',OPEN='COMPLETE')
                elif scenario == 'wrong_submission':
                    disposition['accepted_submission'] = dict(path=str(request['root'] / 'generation_000000/F2.json'),
                        sha256=shared.sha(request['root'] / 'generation_000000/F2.json'))
                else:
                    disposition['replay_train'] = True
                shared.write(binding['path'],disposition,replace=True)
                binding['sha256'] = shared.sha(binding['path'])
                envelope = read_json(owner['handoff']['path'])
                envelope['preserved_files'][Path(binding['path']).name] = binding['sha256']
                shared.write(owner['handoff']['path'],envelope,replace=True)
                owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
                with self.assertRaises(ValueError):
                    candidate.publish_fresh_sessions(**request)


    def test_pending_handoff_rejects_mid_episode_trained_or_duplicate_submission(self):
        for scenario in ('one_episode','unfinished_episode','inflight_call','trained','old_generation','wrong_checkpoint',
                         'unpublished_existing','published_missing','replay_calls','row_not_terminal','charge_reset'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory(prefix='r118_pending_reject_') as folder:
                request = fresh_fixture(folder,pending=True)
                owner = request['owners']['F3']
                reference = owner['boundary']['settled_pending_consolidation']
                document = read_json(reference['path'])
                cursor_reference = owner['boundary']['settled_cursor']
                cursor = read_json(cursor_reference['path'])
                if scenario == 'one_episode':
                    document['episode_ids'] = document['episode_ids'][:1]
                elif scenario == 'unfinished_episode':
                    document['episode_completions'][0]['status'] = 'RUNNING'
                elif scenario == 'inflight_call':
                    cursor['inflight_native_calls'] = ['unsettled']
                elif scenario == 'trained':
                    document['trained'] = True
                elif scenario == 'old_generation':
                    document['generation'] = 0
                elif scenario == 'wrong_checkpoint':
                    document['checkpoint_sha256'] = '0' * 64
                elif scenario == 'unpublished_existing':
                    document['submission'] = None
                elif scenario == 'published_missing':
                    Path(document['submission']['path']).unlink()
                elif scenario == 'replay_calls':
                    document['replay_calls'] = True
                elif scenario == 'row_not_terminal':
                    document['terminal_calls'][0]['status'] = 'RUNNING'
                else:
                    cursor['native_used'] = 0
                shared.write(reference['path'],document,replace=True)
                reference['sha256'] = shared.sha(reference['path'])
                shared.write(cursor_reference['path'],cursor,replace=True)
                cursor_reference['sha256'] = shared.sha(cursor_reference['path'])
                envelope = read_json(owner['handoff']['path'])
                for binding in (reference,cursor_reference):
                    envelope['preserved_files'][Path(binding['path']).name] = binding['sha256']
                shared.write(owner['handoff']['path'],envelope,replace=True)
                owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
                with patch.object(candidate.subprocess,'Popen') as spawn:
                    with self.assertRaises((ValueError,FileNotFoundError)):
                        candidate.publish_fresh_sessions(**request)
                    spawn.assert_not_called()

    def test_pending_rows_exclude_old_generation_and_held_sources(self):
        for scenario in ('old_capture','held_capture','duplicate_row'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory(prefix='r118_pending_source_') as folder:
                request = fresh_fixture(folder,pending=True)
                owner = request['owners']['A4']
                binding = owner['boundary']['settled_pending_consolidation']
                document = read_json(binding['path'])
                rows = read_json(document['rows']['path'])['rows']
                envelope = read_json(owner['handoff']['path'])
                if scenario == 'old_capture':
                    old = read_json(request['root'] / 'generation_000000/A4.json')['rows'][0]
                    rows[0] = old
                    document['terminal_calls'][0] = dict(path=old['source_call_path'],sha256=old['source_call_sha256'],status='COMPLETE')
                    envelope['preserved_files'][Path(old['source_call_path']).name] = old['source_call_sha256']
                elif scenario == 'held_capture':
                    path = Path(rows[0]['source_call_path'])
                    call = read_json(path)
                    call['split'] = 'DEV'
                    shared.write(path,call,replace=True)
                    rows[0]['source_call_sha256'] = shared.sha(path)
                    document['terminal_calls'][0]['sha256'] = shared.sha(path)
                    envelope['preserved_files'][path.name] = shared.sha(path)
                else:
                    rows.append(rows[0])
                shared.write(document['rows']['path'],dict(rows=rows),replace=True)
                document['rows']['sha256'] = shared.sha(document['rows']['path'])
                shared.write(binding['path'],document,replace=True)
                binding['sha256'] = shared.sha(binding['path'])
                for item in (binding,document['rows']):
                    envelope['preserved_files'][Path(item['path']).name] = item['sha256']
                shared.write(owner['handoff']['path'],envelope,replace=True)
                owner['handoff']['sha256'] = shared.sha(owner['handoff']['path'])
                with self.assertRaises(ValueError):
                    candidate.publish_fresh_sessions(**request)


if __name__ == '__main__':
    if '--fresh-cpu-worker' in sys.argv:
        fresh_cpu_worker()
    else:
        unittest.main()
