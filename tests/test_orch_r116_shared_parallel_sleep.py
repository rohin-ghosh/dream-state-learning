"""CPU-only candidate tests; real eight-rank Gloo test skips without torch."""

from copy import deepcopy
from datetime import timedelta
import json
import os
from pathlib import Path
import random
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

try:
    import orch_r116_shared_parallel_sleep as parallel
except ImportError:
    from gpu import orch_r116_shared_parallel_sleep as parallel

try:
    import torch
except ImportError:
    torch = None


def row(offset=0):
    return SimpleNamespace(input_ids=(1, 2, 3 + offset % 3, 6),
                           labels=(-100, -100, 3 + offset % 3, 6),
                           target_ids=(3 + offset % 3, 6))


class ScheduleTests(unittest.TestCase):
    def test_1884_presentations_preserves_tail_and_exact_exposures(self):
        schedule = parallel.validate_schedule(parallel.make_schedule(114,60),114,60,42)
        self.assertEqual(len(schedule),1884)
        self.assertEqual((len(schedule)+7)//8,236)
        self.assertEqual(len(schedule)%8,4)
        self.assertEqual(sum(kind=='NEW' for kind,index,anchor in schedule),1824)
        self.assertEqual(sum(kind=='REHEARSAL' for kind,index,anchor in schedule),60)

    def test_integration_never_authorizes_active_sleep_change(self):
        contract = parallel.integration_contract()
        self.assertEqual(contract['collective_tensors'],'CPU')
        self.assertEqual(contract['rank_order'][0],'F1')
        self.assertIn('never mid-sleep',contract['activation'])
        self.assertFalse(contract['native_gpu_tested'])
        self.assertIsNone(contract['measured_speedup'])
    def test_exact_exposures_and_eightfold_fewer_steps(self):
        allocations = parallel.make_schedule(3, 8)
        result = parallel.validate_schedule(allocations, 3, 8, 42)
        self.assertEqual(len(result), 56)
        self.assertEqual(len(result) // 8, 7)
        self.assertEqual([sum(kind == 'NEW' and index == child for kind, index, anchor in result)
                          for child in range(3)], [16] * 3)
        self.assertEqual([sum(kind == 'REHEARSAL' and index == child for kind, index, anchor in result)
                          for child in range(8)], [1] * 8)
        self.assertEqual({anchor for kind, index, anchor in result}, set(range(42)))

    def test_every_tail_size_preserves_exact_exposures_without_padding(self):
        for tail in range(1, 8):
            allocations = parallel.make_schedule(3, tail)
            result = parallel.validate_schedule(allocations, 3, tail, 42)
            self.assertEqual(len(result), 48 + tail)
            self.assertEqual(sum(kind == 'NEW' for kind, index, anchor in result), 48)
            self.assertEqual(sum(kind == 'REHEARSAL' for kind, index, anchor in result), tail)

    def test_small_inventory_cannot_silently_drop_anchors(self):
        with self.assertRaisesRegex(ValueError, 'cannot_cover_42'):
            parallel.make_schedule(1, 0)

    def test_exposure_tampering(self):
        allocations = list(parallel.make_schedule(3, 8))
        allocations[-1] = dict(allocations[-1], kind='NEW', index=0)
        with self.assertRaisesRegex(ValueError, 'new16_old1'):
            parallel.validate_schedule(allocations, 3, 8, 42)

    def test_no_dropped_rows_and_all_anchors_required(self):
        allocations = list(parallel.make_schedule(3, 8))
        with self.assertRaisesRegex(ValueError, 'new16_old1'):
            parallel.validate_schedule(allocations[:-1], 3, 8, 42)
        for item in allocations:
            item['anchors'] = [0]
        with self.assertRaisesRegex(ValueError, 'all42'):
            parallel.validate_schedule(allocations, 3, 8, 42)

    def test_weights_and_multi_anchor_unsupported_explicitly(self):
        for change, message in ((dict(child_weight=1), '75_25'),
                                (dict(anchors=[0, 1]), 'exactly_one_anchor'),
                                (dict(anchors=[42]), 'anchor_index')):
            allocations = list(parallel.make_schedule(3, 8))
            allocations[0] = dict(allocations[0], **change)
            with self.assertRaisesRegex(ValueError, message):
                parallel.validate_schedule(allocations, 3, 8, 42)

    def test_masked_native_encoding_frozen_without_retokenization(self):
        original = row()
        original.input_ids = list(original.input_ids)
        frozen = parallel.freeze_encoded(original)
        original.input_ids[0] = 99
        self.assertEqual(frozen.input_ids, (1, 2, 3, 6))
        self.assertEqual(frozen.labels, (-100, -100, 3, 6))

    def test_unmasked_parent_changed_target_and_empty_target_rejected(self):
        for change, message in ((dict(labels=(1, -100, 3, 6)), 'prefix_mask'),
                                (dict(target_ids=(4, 6)), 'prefix_mask'),
                                (dict(input_ids=(1, 2, 4, 6)), 'native_suffix'),
                                (dict(target_ids=()), 'empty_or_invalid'),
                                (dict(labels=(-100, 3, 6)), 'length_mismatch')):
            candidate = row()
            candidate.__dict__.update(change)
            with self.assertRaisesRegex(ValueError, message):
                parallel.freeze_encoded(candidate)


class FakeTensor:
    def __init__(self, values):
        self.values = list(values)
        self.device = 'cpu'

    def detach(self):
        return self

    def to(self, device=None, copy=False):
        result = deepcopy(self) if copy or device != self.device else self
        result.device = device
        return result

    def contiguous(self):
        return self

    def copy_(self, other):
        self.values = list(other.values)
        return self

    def __getitem__(self, position):
        return SimpleNamespace(item=lambda: self.values[position])

    def div_(self, divisor):
        self.values = [value / divisor for value in self.values]
        return self


class ProvenanceAdapterTests(unittest.TestCase):
    def setUp(self):
        from gpu import orch_r116_shared_learner as shared
        self.shared = shared
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.common = self.root/'common'
        self.specs = {branch:dict(root=str(self.root/branch),train_ids=[branch+'_1',branch+'_2'])
                      for branch in shared.BRANCHES}
        checkpoint = {}
        for key in ('path','optimizer_path'):
            path = self.root/(key+'.json')
            shared.write(path,dict(test_only=True))
            checkpoint.update({key:str(path),key+'_sha256':shared.sha(path)})
        shared.initialize(self.common,self.specs,checkpoint,excluded_ids=['sealed'],
                          prior_metrics=dict.fromkeys(shared.METRICS,0),initial_history={})
        for branch in shared.BRANCHES:
            rows = []
            for ordinal, task in enumerate(self.specs[branch]['train_ids']):
                messages = [dict(role='user',content='parent text stays in masked source prefix')]
                response = dict(messages=messages,prompt_tokens=2,raw='child',token_ids=[3,4,6],
                                terminal=True,truncated=False)
                call = dict(task_id=task,phase='open_turn',split='TRAIN',response=response,
                            shared_generation=0,shared_checkpoint_sha256=checkpoint['path_sha256'])
                path = self.root/branch/(str(ordinal)+'.json')
                shared.write(path,call)
                rows.append(dict(replay_mode=shared.replay.MODE,student_prefix=messages,
                    source_prompt_sha256=shared.replay.history_policy.digest(messages),source_prompt_tokens=2,
                    target='child',target_sha256=shared.replay.history_policy.text_sha('child'),
                    source_generated_token_ids=[3,4,6],append_eos=True,continuation_only=False,
                    source_call_path=str(path),source_call_sha256=shared.sha(path),episode_id=task))
            shared.submit(self.common,branch,0,checkpoint['path_sha256'],self.specs[branch]['train_ids'],rows)
        self.tokenizer = SimpleNamespace(apply_chat_template=lambda *args,**kwargs:'prefix',
            encode=lambda *args,**kwargs:[1,2],decode=lambda *args,**kwargs:'child',eos_token_id=6,all_special_ids=[6])
        self.anchors = [dict(task_id='anchor'+str(index),source_call_sha256=parallel.digest(index),encoded=row(index))
                        for index in range(42)]
        self.anchor_module = SimpleNamespace(__file__=parallel.__file__,policy=SimpleNamespace(__file__=parallel.__file__),
            build_inventory=lambda *args,**kwargs:({'fixture':deepcopy(self.anchors)},dict(fixture_only=True)))
        self.source_files = {str(Path(module.__file__).resolve()):parallel.file_sha(module.__file__)
                             for module in (shared,shared.replay,parallel)}

    def prepare(self, **changes):
        arguments = dict(shared=self.shared,anchor_module=self.anchor_module,root=self.common,
            tokenizer=self.tokenizer,anchors=self.anchors,anchor_root=self.root/'anchors',
            expected_config_sha256=self.shared.sha(self.common/'CONFIG.json'),
            expected_state_sha256=self.shared.sha(self.common/'STATE.json'),source_files=self.source_files)
        arguments.update(changes)
        return parallel.prepare_native_cohort(**arguments)

    def test_real_capture_validator_and_replay_encoder_no_file_mocks(self):
        result = self.prepare()
        self.assertEqual(len(result['encoded_new']),16)
        self.assertEqual(result['encoded_new'][0].labels,(-100,-100,3,4,6))
        self.assertEqual(result['encoded_new'][0].target_ids,(3,4,6))
        self.assertEqual(len(result['schedule']),256)
        self.assertFalse(result['manifest']['activation_authorized'])

    def test_capture_tamper_fails_before_encoding(self):
        path = self.root/'F1/0.json'
        path.write_text(path.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'capture_hash'):
            self.prepare()

    def test_state_and_source_pins_are_required(self):
        with self.assertRaisesRegex(ValueError,'native_source_hash'):
            self.prepare(expected_state_sha256='f'*64)
        with self.assertRaisesRegex(ValueError,'pinned_validator'):
            self.prepare(source_files={})

    def test_native_encoder_rejection_is_retained_not_trimmed(self):
        original = self.tokenizer.encode
        calls = []
        def encode(*args,**kwargs):
            calls.append(None)
            return [1] if len(calls)==1 else original(*args,**kwargs)
        self.tokenizer.encode = encode
        result = self.prepare()
        rejected = [row for row in result['manifest']['decisions'] if row['status']=='REJECTED_ENCODING']
        self.assertEqual(len(rejected),1)
        self.assertIn('native_prompt_token_count',rejected[0]['reason'])
        self.assertEqual(len(result['encoded_new']),15)

    def test_anchor_source_or_encoding_cannot_be_substituted(self):
        anchors = deepcopy(self.anchors)
        anchors[0]['encoded'] = row(1)
        with self.assertRaisesRegex(ValueError,'anchor_encoding'):
            self.prepare(anchors=anchors)

    def test_missing_peer_or_changed_current_child_rejected(self):
        path = self.common/'generation_000000/A4.json'
        receipt = self.shared.read(path)
        receipt['checkpoint_sha256']='f'*64
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError,'current_common_child'):
            self.prepare()
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.prepare()


class CollectiveMockTests(unittest.TestCase):
    def backend(self, rank=0):
        backend = parallel.ParallelSleep.__new__(parallel.ParallelSleep)
        backend.rank, backend.root, backend.world_size = rank, 11, 8
        backend.group = object()
        backend.cursor = 0
        backend.schedule = parallel.validate_schedule(parallel.make_schedule(3, 8), 3, 8, 42)
        backend.dist = Mock()
        backend.dist.ReduceOp.SUM = 'SUM'
        backend.dist.all_gather_object.side_effect = lambda output, value, group: output.__setitem__(slice(None), [value] * 8)
        backend.engine = SimpleNamespace(device='cpu')
        return backend

    def test_preflight_peer_error_is_shared_before_work(self):
        backend = self.backend()
        def gather(output, value, group):
            output[:] = [None] * 8
            output[5] = 'ValueError: invalid mask'
        backend.dist.all_gather_object.side_effect = gather
        with self.assertRaisesRegex(RuntimeError, '5.*invalid mask'):
            backend._collective('preflight', lambda: None)
        backend.dist.reduce.assert_not_called()

    def test_constructor_translates_group_local_owner_to_global_rank(self):
        distributed = Mock()
        group = object()
        distributed.get_rank.return_value = 0
        distributed.get_world_size.return_value = 8
        distributed.get_global_rank.return_value = 11
        distributed.all_gather_object.side_effect = lambda output, value, group: output.__setitem__(slice(None), [value] * 8)
        def prepare(backend, *args):
            backend.binding, backend.schema = 'bound', ('schema',)
        with patch.object(parallel.ParallelSleep, '_prepare', prepare), patch.object(
                parallel.ParallelSleep, '_adapter_digest', return_value='adapter'):
            backend = parallel.ParallelSleep(SimpleNamespace(torch=None), None, group=group,
                encoded_new=[], encoded_old=[], encoded_anchors=[], schedule=[],
                source_manifest_sha256='a' * 64, distributed=distributed)
        self.assertEqual(backend.root, 11)
        distributed.get_global_rank.assert_called_once_with(group, 0)

    def test_local_failure_is_gathered(self):
        backend = self.backend()
        with self.assertRaisesRegex(RuntimeError, 'division by zero'):
            backend._collective('forward', lambda: 1 / 0)

    def test_sum_average_uses_global_subgroup_root_and_preserves_unused(self):
        backend = self.backend()
        first = SimpleNamespace(grad=FakeTensor([2., 4.]),device='cuda:0')
        unused = SimpleNamespace(grad=None,device='cuda:0')
        backend.lora = (('layer.lora_A.weight', first), ('layer.lora_B.weight', unused))
        backend.torch = SimpleNamespace(int32='int32', tensor=lambda values, **kwargs: FakeTensor(values),
                                        zeros_like=lambda parameter, **kwargs: FakeTensor([0., 0.]))
        def reduce(tensor, dst, op, group):
            self.assertEqual(dst, 11)
            self.assertEqual(op, 'SUM')
            self.assertIs(group, backend.group)
            self.assertEqual(tensor.device,'cpu')
            if len(backend.dist.reduce.call_args_list) == 1:
                tensor.values = [8, 0]
            elif len(backend.dist.reduce.call_args_list) == 2:
                tensor.values = [72., 144.]
        backend.dist.reduce.side_effect = reduce
        backend._reduce()
        self.assertEqual(first.grad.values, [9., 18.])
        self.assertIsNone(unused.grad)
        self.assertEqual(backend.dist.reduce.call_count, 3)

    def test_workers_never_step(self):
        backend = self.backend(rank=7)
        backend.optimizer = None
        backend._step()

    def test_partial_batch_denominator_is_active_ranks_not_eight(self):
        backend = self.backend()
        backend.schedule = parallel.validate_schedule(parallel.make_schedule(3, 3), 3, 3, 42)
        backend.cursor = 6
        parameter = SimpleNamespace(grad=FakeTensor([12., 24.]),device='cpu')
        backend.lora = (('layer.lora_A.weight', parameter),)
        backend.torch = SimpleNamespace(int32='int32', tensor=lambda values, **kwargs: FakeTensor(values))
        backend._reduce()
        self.assertEqual(parameter.grad.values, [4., 8.])
        self.assertEqual(backend._active_batch_size(), 3)

    def test_inactive_tail_worker_clears_stale_grad_without_forward(self):
        backend = self.backend(rank=7)
        backend.schedule = parallel.validate_schedule(parallel.make_schedule(3, 3), 3, 3, 42)
        backend.cursor = 6
        backend._identity_check = Mock()
        backend.engine.model = Mock()
        backend._backward()
        backend.engine.model.zero_grad.assert_called_once_with(set_to_none=True)
        backend.engine.model.assert_not_called()

    def test_broadcast_keeps_parameter_identity(self):
        from contextlib import nullcontext
        backend = self.backend()
        parameter = FakeTensor([1.,2.])
        parameter.device = 'cuda:0'
        backend.lora = (('layer.lora_A.weight', parameter),)
        backend.torch = SimpleNamespace(no_grad=nullcontext)
        backend._broadcast_parameters()
        backend.dist.broadcast.assert_called_once()
        transferred = backend.dist.broadcast.call_args.args[0]
        self.assertIsNot(transferred,parameter)
        self.assertEqual(transferred.device,'cpu')
        self.assertEqual(backend.dist.broadcast.call_args.kwargs,dict(src=11,group=backend.group))
        self.assertIs(backend.lora[0][1], parameter)

    def test_metrics_do_not_claim_serial_adamw_equivalence(self):
        backend = self.backend()
        backend.cursor = 2
        backend.schedule = parallel.validate_schedule(parallel.make_schedule(3, 8), 3, 8, 42)
        backend.rows = dict(NEW=[row()] * 3, REHEARSAL=[row()] * 8)
        backend.anchors = [row()] * 42
        backend.binding = 'a' * 64
        backend.source_manifest_sha256 = 'b' * 64
        metrics = backend.metrics()
        self.assertEqual(metrics['optimizer_steps'], 2)
        self.assertEqual(metrics['serial_equivalent_presentations'], 16)
        self.assertEqual(metrics['child_token_exposures'], 32)
        self.assertEqual(metrics['anchor_token_exposures'], 32)
        self.assertEqual(metrics['optimizer_steps_avoided_vs_serial'], 14)
        self.assertFalse(metrics['serial_adamw_equivalent'])

    def test_partial_batch_metrics_and_token_counts_are_explicit(self):
        backend = self.backend()
        backend.schedule = parallel.validate_schedule(parallel.make_schedule(3, 3), 3, 3, 42)
        backend.cursor = 7
        backend.rows = dict(NEW=[row()] * 3, REHEARSAL=[row()] * 3)
        backend.anchors = [row()] * 42
        backend.binding = 'a' * 64
        backend.source_manifest_sha256 = 'b' * 64
        metrics = backend.metrics()
        self.assertEqual(metrics['optimizer_steps'], 7)
        self.assertEqual(metrics['completed_full_batches'], 6)
        self.assertEqual(metrics['completed_partial_batch_size'], 3)
        self.assertEqual(metrics['serial_equivalent_presentations'], 51)
        self.assertEqual(metrics['child_token_exposures'], 102)
        self.assertEqual(metrics['anchor_token_exposures'], 102)
        self.assertEqual(metrics['new_row_exposures'], 48)
        self.assertEqual(metrics['rehearsal_row_exposures'], 3)
        self.assertTrue(metrics['complete'])


if torch is not None:
    class TinyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = torch.nn.Embedding(7, 4)
            self.base = torch.nn.Linear(4, 7, bias=False)
            self.layer = torch.nn.Module()
            self.layer.lora_A = torch.nn.ModuleDict({'default': torch.nn.Linear(4, 2, bias=False)})
            self.layer.lora_B = torch.nn.ModuleDict({'default': torch.nn.Linear(2, 7, bias=False)})
            self.dropout = torch.nn.Dropout(0)
            self.requires_grad_(False)
            self.eval()
            self.config = SimpleNamespace(use_cache=True)
            self.seen = []
            self.fail = False

        def forward(self, input_ids, attention_mask, labels):
            self.seen.append((input_ids.tolist()[0], labels.tolist()[0]))
            hidden = self.embedding(input_ids)
            logits = self.base(hidden) + self.layer.lora_B['default'](self.layer.lora_A['default'](self.dropout(hidden)))
            loss = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 7), labels[:, 1:].reshape(-1))
            return SimpleNamespace(loss=loss * float('nan') if self.fail else loss)


def real_worker(rank, rendezvous):
    torch.set_num_threads(1)
    torch.distributed.init_process_group('gloo', init_method='file://' + rendezvous,
                                        rank=rank, world_size=8, timeout=timedelta(seconds=60))
    assertions = unittest.TestCase()
    try:
        torch.manual_seed(414)
        model = TinyModel()
        named = tuple(model.named_parameters())
        lora = [parameter for name, parameter in named if parallel.is_lora(name)]
        optimizer = torch.optim.AdamW(lora, lr=.02, betas=(.9, .95), weight_decay=.01) if rank == 0 else None
        if rank == 0:
            for parameter in lora:
                parameter.grad = torch.full_like(parameter, .125)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        for parameter in lora:
            torch.distributed.broadcast(parameter, src=0)
        base = {name: parameter.detach().clone() for name, parameter in named if not parallel.is_lora(name)}
        def verify_base():
            for name, parameter in model.named_parameters():
                if name in base:
                    assertions.assertTrue(torch.equal(parameter, base[name]))
                    assertions.assertFalse(parameter.requires_grad)
        engine = SimpleNamespace(model=model, device='cpu', torch=torch, verify_base=verify_base)
        arguments = dict(group=None, encoded_new=[row(index) for index in range(3)],
                         encoded_old=[row(index) for index in range(11)],
                         encoded_anchors=[row(index) for index in range(42)],
                         schedule=parallel.make_schedule(3, 11), source_manifest_sha256='a' * 64)
        backend = parallel.ParallelSleep(engine, optimizer, **arguments)
        identities = [id(parameter) for name, parameter in named]
        optimizer_identity = id(optimizer)
        if rank == 0:
            reference = deepcopy(model)
            reference_lora = [parameter for name, parameter in reference.named_parameters() if parallel.is_lora(name)]
            reference_optimizer = torch.optim.AdamW(reference_lora, lr=.02, betas=(.9, .95), weight_decay=.01)
            reference_optimizer.load_state_dict(deepcopy(optimizer.state_dict()))
            for parameter in reference_lora:
                parameter.requires_grad_(True)
            reference.train()
            for kind, index, anchor in backend.schedule[:8]:
                for item, weight in ((backend.rows[kind][index], .75), (backend.anchors[anchor], .25)):
                    inputs = torch.tensor([item.input_ids])
                    labels = torch.tensor([item.labels])
                    (reference(inputs, torch.ones_like(inputs), labels).loss * weight / 8).backward()
            reference_optimizer.step()
        calls = []
        first = backend.run(max_steps=1, check=lambda: calls.append('lease'))
        assertions.assertEqual(calls, ['lease'])
        assertions.assertEqual(first['optimizer_steps'], 1)
        assertions.assertEqual(first['child_token_exposures'], 16)
        kind, index, anchor = backend.schedule[rank]
        assertions.assertEqual(model.seen[0], (list(backend.rows[kind][index].input_ids), list(backend.rows[kind][index].labels)))
        if rank == 0:
            for parameter, expected in zip(lora, reference_lora):
                torch.testing.assert_close(parameter, expected, rtol=1e-6, atol=1e-7)
            assertions.assertEqual([int(optimizer.state[parameter]['step']) for parameter in lora], [2] * len(lora))
        assertions.assertFalse(model.training)
        assertions.assertTrue(model.config.use_cache)
        assertions.assertTrue(all(not parameter.requires_grad for name, parameter in named))
        random.seed(901 + rank)
        torch.manual_seed(901 + rank)
        import numpy
        numpy.random.seed(901 + rank)
        model.dropout.p = .2
        checkpoint = backend.checkpoint()
        if rank == 0:
            assertions.assertEqual(len(checkpoint['rng']), 8)
            assertions.assertEqual(len({tuple(state['cpu'].tolist()) for state in checkpoint['rng']}), 8)
            assertions.assertEqual(len({repr(state['python']) for state in checkpoint['rng']}), 8)
            checkpoint_path = Path(rendezvous).parent/'cpu_checkpoint.pt'
            torch.save(checkpoint,checkpoint_path)
            checkpoint = torch.load(checkpoint_path,map_location='cpu',weights_only=False)
        else:
            assertions.assertIsNone(checkpoint)
        backend.run(max_steps=2)
        expected_lora = [parameter.detach().clone() for parameter in lora]
        expected_random = (random.random(), torch.rand(3), numpy.random.rand())
        backend.restore(checkpoint)
        assertions.assertEqual(backend.cursor, 1)
        backend.run(max_steps=2)
        for actual, expected in zip(lora, expected_lora):
            assertions.assertTrue(torch.equal(actual, expected))
        assertions.assertEqual(random.random(), expected_random[0])
        assertions.assertTrue(torch.equal(torch.rand(3), expected_random[1]))
        assertions.assertEqual(numpy.random.rand(), expected_random[2])
        assertions.assertEqual(id(optimizer), optimizer_identity)
        if rank == 0:
            assertions.assertEqual([int(optimizer.state[parameter]['step']) for parameter in lora], [4] * len(lora))
        bad_checkpoint = dict(checkpoint, binding='wrong') if rank == 0 else None
        with assertions.assertRaisesRegex(RuntimeError, 'binding_mismatch'):
            backend.restore(bad_checkpoint)
        with assertions.assertRaisesRegex(RuntimeError, 'workers_none'):
            parallel.ParallelSleep(engine, object() if rank == 1 else optimizer, **arguments)
        changed = dict(arguments, encoded_new=[row(1), row(1), row(2)]) if rank == 6 else arguments
        with assertions.assertRaisesRegex(ValueError, 'replicas_cohort'):
            parallel.ParallelSleep(engine, optimizer, **changed)
        model.base.weight.requires_grad_(rank == 4)
        with assertions.assertRaisesRegex(RuntimeError, 'base_must_be_frozen'):
            parallel.ParallelSleep(engine, optimizer, **arguments)
        model.base.weight.requires_grad_(False)
        if rank == 0:
            previous = optimizer.param_groups[0]['params'][0]
            optimizer.param_groups[0]['params'][0] = model.base.weight
        with assertions.assertRaisesRegex(RuntimeError, 'exact_existing_lora_objects'):
            backend.run(max_steps=1)
        if rank == 0:
            optimizer.param_groups[0]['params'][0] = previous
        model.fail = rank == 5
        with assertions.assertRaisesRegex(RuntimeError, 'nonfinite_weighted_loss'):
            backend.run(max_steps=1)
        with assertions.assertRaisesRegex(RuntimeError, 'restore_required'):
            backend.run(max_steps=1)
        with assertions.assertRaisesRegex(RuntimeError, 'restore_required'):
            backend.checkpoint()
        model.fail = False
        backend.restore(checkpoint)
        model.dropout.p = 0
        backend.run(max_steps=6)
        if rank == 0:
            reference = deepcopy(model)
            reference_lora = [parameter for name, parameter in reference.named_parameters() if parallel.is_lora(name)]
            reference_optimizer = torch.optim.AdamW(reference_lora, lr=.02, betas=(.9, .95), weight_decay=.01)
            reference_optimizer.load_state_dict(deepcopy(optimizer.state_dict()))
            for parameter in reference_lora:
                parameter.requires_grad_(True)
            reference.train()
            for kind, index, anchor in backend.schedule[56:]:
                for item, weight in ((backend.rows[kind][index], .75), (backend.anchors[anchor], .25)):
                    inputs = torch.tensor([item.input_ids])
                    labels = torch.tensor([item.labels])
                    (reference(inputs, torch.ones_like(inputs), labels).loss * weight / 3).backward()
            reference_optimizer.step()
        previous_forwards = len(model.seen)
        final = backend.run(max_steps=100)
        assertions.assertEqual(len(model.seen) - previous_forwards, 2 if rank < 3 else 0)
        assertions.assertEqual(final['optimizer_steps'], 8)
        assertions.assertEqual(final['completed_full_batches'], 7)
        assertions.assertEqual(final['completed_partial_batch_size'], 3)
        assertions.assertEqual(final['new_row_exposures'], 48)
        assertions.assertEqual(final['rehearsal_row_exposures'], 11)
        assertions.assertEqual(final['child_token_exposures'], 118)
        assertions.assertEqual(final['anchor_token_exposures'], 118)
        assertions.assertTrue(final['complete'])
        assertions.assertFalse(final['serial_adamw_equivalent'])
        if rank == 0:
            assertions.assertEqual([int(optimizer.state[parameter]['step']) for parameter in lora], [9] * len(lora))
            for parameter, expected in zip(lora, reference_lora):
                torch.testing.assert_close(parameter, expected, rtol=1e-6, atol=1e-7)
        else:
            assertions.assertIsNone(backend.optimizer)
        assertions.assertEqual([id(parameter) for name, parameter in model.named_parameters()], identities)
        for parameter in lora:
            replicas = [torch.empty_like(parameter) for replica in range(8)]
            torch.distributed.all_gather(replicas, parameter)
            assertions.assertTrue(all(torch.equal(parameter, replica) for replica in replicas))
        verify_base()
        proof_directory = os.environ.get('R116_PARALLEL_PROOF_DIR')
        if proof_directory:
            reports = [None]*8
            report = dict(rank=rank,pid=os.getpid(),optimizer_present=backend.optimizer is not None,
                parameter_identity_preserved=[id(parameter) for name,parameter in model.named_parameters()]==identities,
                cuda_initialized=torch.cuda.is_initialized(),cursor=backend.cursor,
                rng_restored_exactly=True,base_unchanged=True,
                optimizer_step_values=[int(optimizer.state[parameter]['step']) for parameter in lora] if rank==0 else [])
            torch.distributed.all_gather_object(reports,report)
            if rank==0:
                path = Path(proof_directory)/('EIGHT_RANK_'+str(time.time_ns())+'.json')
                with path.open('x') as stream:
                    json.dump(dict(backend='gloo',world_size=8,device='cpu',ranks=reports,
                        initial_existing_optimizer_step=1,final_optimizer_step=9,checkpoint_disk_roundtrip=True,
                        all_rank_python_numpy_torch_rng_exact_recovery=True,
                        matches_single_process_average_gradient_reference=True,
                        partial_tail_denominator=3,partial_inactive_no_forward=True,
                        peer_failure_collectively_rejected=True,metrics=final),stream,indent=2)
    finally:
        torch.distributed.destroy_process_group()


@unittest.skipIf(torch is None, 'torch unavailable; run CPU Gloo on native venv')
class RealCollectiveTests(unittest.TestCase):
    def test_eight_rank_single_optimizer_continuity_and_all_rng_recovery(self):
        self.assertEqual(os.environ.get('CUDA_VISIBLE_DEVICES'), '', 'run explicitly CPU-only: CUDA_VISIBLE_DEVICES=')
        self.assertFalse(torch.cuda.is_initialized())
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory(prefix='r116_cpu_gloo_') as folder:
            torch.multiprocessing.start_processes(real_worker, args=(str(Path(folder) / 'rendezvous'),),
                                                  nprocs=8, start_method='spawn', join=True)
        self.assertFalse(torch.cuda.is_initialized())


@unittest.skipUnless(os.environ.get('R116_NATIVE_COMMON'),'explicit native read-only fixture not selected')
class NativeCohortTests(unittest.TestCase):
    def test_actual_submissions_replay_encoding_and_all42_anchors(self):
        self.assertEqual(os.environ.get('CUDA_VISIBLE_DEVICES'),'')
        from gpu import orch_r116_shared_learner as shared
        from gpu import orch_r107_base_anchors_inventory as anchor_module
        from gpu import orch_guided_native as native
        common = Path(os.environ['R116_NATIVE_COMMON'])
        plan = shared.read(Path(os.environ['R116_NATIVE_OWNER_PLAN']))
        state_sha = shared.sha(common/'STATE.json')
        config_sha = shared.sha(common/'CONFIG.json')
        tokenizer = native.source.native.load_local_tokenizer(plan['model_dir'])
        inventory = anchor_module.load_inventory(Path(plan['anchor_root']),tokenizer)
        anchors = [row for family in sorted(inventory) for row in inventory[family]]
        sources = dict(plan['source_files'])
        sources[str(Path(parallel.__file__).resolve())] = parallel.file_sha(parallel.__file__)
        prepared = parallel.prepare_native_cohort(shared=shared,anchor_module=anchor_module,root=common,
            tokenizer=tokenizer,anchors=anchors,anchor_root=plan['anchor_root'],
            expected_config_sha256=config_sha,expected_state_sha256=state_sha,source_files=sources)
        self.assertEqual(len(prepared['encoded_anchors']),42)
        self.assertEqual(shared.sha(common/'CONFIG.json'),config_sha)
        self.assertEqual(shared.sha(common/'STATE.json'),state_sha)
        self.assertFalse(torch.cuda.is_initialized())
        output = Path(os.environ['R116_PARALLEL_PROOF_DIR'])/('NATIVE_COHORT_'+str(time.time_ns())+'.json')
        with output.open('x') as stream:
            json.dump(dict(source_manifest_sha256=prepared['source_manifest_sha256'],manifest=prepared['manifest'],
                encoded_new=len(prepared['encoded_new']),encoded_old=len(prepared['encoded_old']),
                serial_presentations=len(prepared['schedule']),parallel_optimizer_steps=(len(prepared['schedule'])+7)//8,
                child_token_exposures=sum(len(prepared['encoded_new' if row['kind']=='NEW' else 'encoded_old'][row['index']].target_ids)
                    for row in prepared['schedule']),anchor_token_exposures=sum(len(prepared['encoded_anchors'][row['anchors'][0]].target_ids)
                    for row in prepared['schedule']),cuda_initialized=False,no_source_mutation=True,
                current_serial_not_interrupted=True,activation_authorized=False),stream,indent=2)


if __name__ == '__main__':
    unittest.main()
