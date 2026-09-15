from datetime import timedelta
import json
import os
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


@unittest.skipUnless(torch is not None,'native CPU torch required')
class RealCollectiveTests(unittest.TestCase):
    def test_eight_rank_commit_failures_and_selector(self):
        with tempfile.TemporaryDirectory(prefix='r118_parallel_cpu_') as folder:
            torch.multiprocessing.start_processes(real_worker,args=(str(Path(folder) / 'rendezvous'),folder),
                nprocs=8,start_method='spawn',join=True)


if __name__ == '__main__':
    unittest.main()
