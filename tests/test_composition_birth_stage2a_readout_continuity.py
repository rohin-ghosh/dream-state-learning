"""Tiny CPU writer/readout boundary tests, not HF/Qwen learning qualification.

Generation is an explicit synthetic callback over a real torch training model.
The test checks state continuity, not generated quality or native HF decoding.
"""

import importlib.util
import os
from types import MethodType, SimpleNamespace
import unittest

from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_training as training
from tests import test_composition_birth_stage2a_actor as actor_fixtures
from tests import test_composition_birth_stage2a_training as training_fixtures


@unittest.skipUnless(importlib.util.find_spec("torch") is not None,
                     "existing torch required; never install or load real models")
class ReadoutTrainingContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("CUDA_VISIBLE_DEVICES") not in ("", "-1"):
            raise unittest.SkipTest("explicit CUDA-hidden CPU process required")
        if any(os.environ.get(name) != "1" for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS")):
            raise unittest.SkipTest("prospective single-thread CPU process required")
        import torch
        cls.torch = torch
        if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
            raise AssertionError("bind torch intra/inter-op threads before running this fixture")
        cls.batches = training_fixtures.fixture()
        cls.roster = training_fixtures.planned_roster()
        cls.initial_digest = training.adapter_sha256(training_fixtures.tiny_native_model(), cls.roster)
        trainer = cls.trainer()
        trainer.train_stage("D1")
        cls.d1 = trainer.checkpoint()
        trainer.train_stage("D2")
        cls.control_d2 = trainer.checkpoint()

    @classmethod
    def trainer(cls, checkpoint=None):
        return training.StatefulTrainer(
            training_fixtures.tiny_native_model(), arm="ATOM_LOCAL",
            master=training_fixtures.MASTER, batches=cls.batches,
            trainable_roster=cls.roster, layer_count=1, adapter_name="default",
            lineage_id="SYNTHETIC-READOUT-CONTINUITY", preparation_sha256="a" * 64,
            initial_adapter_sha256=cls.initial_digest, checkpoint=checkpoint,
        )

    def bridge(self, model, *, failure=False):
        torch = self.torch
        model.generation_config = SimpleNamespace(original="synthetic-caller-config")

        def generate(current, *, input_ids, attention_mask, generation_config):
            if any(module.training for module in current.modules()):
                raise AssertionError("synthetic generation must run in eval mode")
            torch.rand(13)
            current.generation_config = SimpleNamespace(transient="synthetic-backend-mutation")
            continuation = torch.tensor([[ord(character) + 10 for character in "STOP"] + [1]],
                                        dtype=torch.long)
            output = torch.cat((input_ids, continuation), dim=1)
            if failure:
                error = RuntimeError("synthetic-generation-failure-after-output")
                error.partial_output = output
                raise error
            return output

        model.generate = MethodType(generate, model)
        return actor_api.ReadoutActor(
            tokenizer=actor_fixtures.SyntheticTokenizer(), model=model, torch=torch,
            device="cpu", count_basis="SYNTHETIC_FIXTURE",
            generation_config_factory=lambda **values: SimpleNamespace(**values),
        )

    def request(self, actor, seed):
        prefix = (held.Message("system", "Synthetic readout only."),
                  held.Message("user", "Return STOP."))
        return rollout.DecodeRequest(prefix, 256, seed, actor.count_context(prefix))

    def boundary(self, trainer):
        return (
            training._tree_hash(trainer._snapshot()),
            tuple((name, parameter.requires_grad,
                   None if parameter.grad is None else training.tensor_sha256(parameter.grad))
                  for name, parameter in trainer.model.named_parameters()),
            tuple(module.training for module in trainer.model.modules()),
        )

    def test_readouts_preserve_training_boundary_and_d2(self):
        trainer = self.trainer(checkpoint=self.d1)
        for _, parameter in trainer.named:
            parameter.grad = self.torch.ones_like(parameter)
        trainer.model.train()
        trainer.model.model.layers[0].self_attn.q_proj.eval()
        actor = self.bridge(trainer.model)
        config = trainer.model.generation_config
        before = self.boundary(trainer)
        for seed in (0, 2**63, 2**64 - 1):
            self.assertEqual(actor(self.request(actor, seed)),
                             rollout.Generation("STOP", 5, 5, False, "stop"))
            self.assertEqual(self.boundary(trainer), before)
            self.assertIs(trainer.model.generation_config, config)
        self.assertEqual(len(actor.calls), 3)
        trainer.train_stage("D2")
        self.assertEqual(training._tree_hash(trainer.checkpoint()),
                         training._tree_hash(self.control_d2))

    def test_failed_readout_preserves_state_without_authorizing_continuation(self):
        trainer = self.trainer(checkpoint=self.d1)
        actor = self.bridge(trainer.model, failure=True)
        config = trainer.model.generation_config
        before = self.boundary(trainer)
        with self.assertRaisesRegex(RuntimeError, "synthetic-generation-failure") as caught:
            actor(self.request(actor, 2**64 - 1))
        self.assertEqual(self.boundary(trainer), before)
        self.assertIs(trainer.model.generation_config, config)
        self.assertIs(actor.calls[0]["error"], caught.exception)
        self.assertIsInstance(caught.exception.partial_output, self.torch.Tensor)
        self.assertIsNone(actor.calls[0]["native_output"])
        with self.assertRaisesRegex(ValueError, "actor_failed_no_retry"):
            actor(self.request(actor, 0))
        self.assertEqual(self.boundary(trainer), before)
        self.assertEqual(training._tree_hash(trainer.checkpoint()), training._tree_hash(self.d1))


if __name__ == "__main__":
    unittest.main()
