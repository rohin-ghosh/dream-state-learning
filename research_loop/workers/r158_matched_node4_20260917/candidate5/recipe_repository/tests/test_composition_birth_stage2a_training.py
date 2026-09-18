"""Source contracts plus optional real-torch CPU mechanics, never GPU science.

Run with ``python3 -m unittest tests.test_composition_birth_stage2a_training``.
Native tests explicitly skip without an installed torch; no packages are fetched.
The tiny CPU model uses real autograd, dropout, activation checkpointing and
AdamW. It is neither Qwen nor a PEFT qualification, and its compact synthetic
token IDs are not tokenizer evidence. No optimizer-step evidence uses mocks.
"""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
import math
import subprocess
import sys
from types import SimpleNamespace
import unittest

from organism_v6 import composition_birth_stage2a_curriculum as curriculum
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_tape as tape
from organism_v6 import composition_birth_stage2a_tokenization as tokenization
from organism_v6 import composition_birth_stage2a_training as source
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


MASTER = b"SYNTHETIC-STATEFUL-TRAINING-SOURCE-ONLY"
HAS_TORCH = importlib.util.find_spec("torch") is not None


def planned_roster():
    return tuple(source.ParameterSpec(
        f"model.layers.0.{group}.{module}.lora_{side}.default.weight",
        (8, 4) if side == "A" else (4, 8), "torch.float32")
        for group, modules in (("self_attn", source.TARGET_MODULES[:4]), ("mlp", source.TARGET_MODULES[4:]))
        for module in modules for side in ("A", "B"))


def compact_row(record):
    context = (2, 3, 4) if record.arm == "CLOSED" else (2, 3)
    command = record.unit.command.split()[0]
    target = ({"READ": 4, "STEP": 5, "THINK": 6, "STOP": 7}[command], 1)
    prefix_bytes = tokenization.targets.messages_bytes(record.prefix)
    target_bytes = record.unit.target_bytes + b"<|im_end|>"
    return tokenization.TokenizedArm(
        record=record, context_ids=context, target_ids=target, input_ids=context + target + (10,),
        labels=(-100,) * len(context) + target + (-100,), attention_mask=(1,) * (len(context) + 3),
        context_roundtrip_bytes=prefix_bytes, target_roundtrip_bytes=target_bytes,
        sequence_roundtrip_bytes=prefix_bytes + target_bytes + b"\n", identifier_tokenization=(),
        eos_token_id=1, pad_token_id=0, count_basis="SYNTHETIC_FIXTURE",
        suffix_ids=(10,), suffix_roundtrip_bytes=b"\n",
    )


def padded_batch(arm, records, width):
    return tokenization.ArmBatch(
        arm, records,
        tuple(row.input_ids + (0,) * (width - len(row.input_ids)) for row in records),
        tuple(row.labels + (-100,) * (width - len(row.input_ids)) for row in records),
        tuple(row.attention_mask + (0,) * (width - len(row.input_ids)) for row in records), width,
    )


@lru_cache(maxsize=1)
def fixture():
    compiled = curriculum.compile_birth_curriculum(
        role_tokens_by_world={f"p{number:02d}": synthetic_bindings(number) for number in range(32)},
        master=MASTER)
    rows = {pair.closed.unit.unit_id: (compact_row(pair.closed), compact_row(pair.atom_local))
            for pair in compiled.paired_targets}
    batches = []
    for presentation in compiled.batches:
        closed = tuple(rows[unit][0] for unit in presentation.unit_ids)
        atom = tuple(rows[unit][1] for unit in presentation.unit_ids)
        batches.append(tokenization.PairedBatch(
            presentation, padded_batch("CLOSED", closed, 8), padded_batch("ATOM_LOCAL", atom, 6),
            tuple(row.record.unit.target_sha256 for row in closed), tuple(len(row.target_ids) for row in closed)))
    return tuple(batches)


class Stage2ATrainingValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batches = fixture()

    def reject_batch(self, batch, index=0, error=None):
        batches = self.batches[:index] + (batch,) + self.batches[index + 1:]
        with self.assertRaisesRegex(ValueError, error or ".+"):
            source.validate_batches(batches, master=MASTER)

    def test_import_is_lazy_and_all_science_gates_closed(self):
        script = (
            "import sys; from organism_v6 import composition_birth_stage2a_training as module; "
            "assert 'torch' not in sys.modules; assert not any(module.SCIENCE_GATES.values())"
        )
        subprocess.run([sys.executable, "-c", script], check=True)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_exact_recipe_and_no_implicit_features(self):
        source.validate_recipe(dict(source.RECIPE))
        for key, expected in source.RECIPE.items():
            recipe = dict(source.RECIPE)
            recipe[key] = not expected if type(expected) is bool else None
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "recipe_drift"):
                source.validate_recipe(recipe)
        for recipe in ({}, {**source.RECIPE, "loss_reduction": "sum"}):
            with self.assertRaises(ValueError):
                source.validate_recipe(recipe)
        with self.assertRaises(ValueError):
            source.validate_recipe({**source.RECIPE, "batch_size": 4.0})

    def test_all_512_planned_batches_are_deterministic(self):
        observed = source.validate_batches(self.batches, master=MASTER)
        self.assertEqual(len(observed), 64)
        self.assertEqual(observed, source.validate_batches(self.batches, master=MASTER))
        for update in (1, 256, 257, 512):
            expected = int.from_bytes(sha256(MASTER + b"\0dropout\0" + update.to_bytes(4, "big")).digest()[24:32], "big")
            self.assertEqual(self.batches[update - 1].presentation.rng_start_seed, expected)
            self.assertEqual(primitives.dropout_seed(MASTER, update), expected)
        self.assertEqual(sum(len(batch.presentation.unit_ids) for batch in self.batches[:256]), 1024)

    def test_missing_duplicate_reordered_or_extra_batch_rejected(self):
        for batches in (self.batches[:-1], self.batches + self.batches[:1], list(self.batches),
                        self.batches[:1] + self.batches[:511], tuple(reversed(self.batches))):
            with self.assertRaises(ValueError):
                source.validate_batches(batches, master=MASTER)

    def test_wrong_d2_seed_cursor_or_unit_order_fails_pure_preflight(self):
        batch = self.batches[256]
        for presentation in (
            replace(batch.presentation, rng_start_seed=batch.presentation.rng_start_seed ^ 1),
            replace(batch.presentation, update_number=1),
            replace(batch.presentation, presentation_index=3),
            replace(batch.presentation, unit_ids=tuple(reversed(batch.presentation.unit_ids))),
        ):
            self.reject_batch(replace(batch, presentation=presentation), 256, "tape_or_seed")
        with self.assertRaisesRegex(ValueError, "tape_or_seed"):
            source.validate_batches(self.batches, master=b"SYNTHETIC-WRONG-MASTER")

    def test_masks_preserve_template_lf_and_right_padding(self):
        batch = self.batches[0]
        for arm in (batch.closed, batch.atom_local):
            for row, labels, attention in zip(arm.records, arm.labels, arm.attention_mask):
                self.assertEqual(labels[row.target_start:row.target_end], row.target_ids)
                self.assertTrue(all(label == -100 for label in labels[row.target_end:]))
                self.assertEqual(attention[row.target_end], 1)
                self.assertEqual(row.suffix_roundtrip_bytes, b"\n")
                self.assertEqual(attention[-1], 0)
        labels = list(batch.closed.labels[0])
        labels[batch.closed.records[0].target_end] = 10
        self.reject_batch(replace(batch, closed=replace(batch.closed, labels=(tuple(labels),) + batch.closed.labels[1:])),
                          error="padding_or_loss_mask")
        labels = list(batch.closed.labels[0])
        labels[0] = batch.closed.input_ids[0][0]
        self.reject_batch(replace(batch, closed=replace(batch.closed, labels=(tuple(labels),) + batch.closed.labels[1:])))

    def test_batch_four_target_hash_counts_and_attention_rejected(self):
        batch = self.batches[0]
        variants = (
            replace(batch, closed=replace(batch.closed, records=batch.closed.records[:3])),
            replace(batch, target_hashes=("0" * 64,) + batch.target_hashes[1:]),
            replace(batch, target_token_counts=(100,) + batch.target_token_counts[1:]),
            replace(batch, closed=replace(batch.closed, attention_mask=((True,) * 8,) + batch.closed.attention_mask[1:])),
            replace(batch, closed=replace(batch.closed, padding_length=16385)),
            replace(batch, closed=replace(batch.closed, padding_length=1)),
        )
        for variant in variants:
            self.reject_batch(variant)

    def test_target_pairing_repeated_record_and_suffix_drift(self):
        batch = self.batches[0]
        row = batch.atom_local.records[0]
        target = (9, 1)
        changed = replace(row, target_ids=target, input_ids=row.context_ids + target + row.suffix_ids,
                          labels=(-100,) * len(row.context_ids) + target + (-100,))
        self.reject_batch(replace(batch, atom_local=padded_batch("ATOM_LOCAL", (changed,) + batch.atom_local.records[1:], 6)),
                          error="paired_target")
        changed = replace(row, suffix_roundtrip_bytes=b"\r\n")
        self.reject_batch(replace(batch, atom_local=replace(batch.atom_local, records=(changed,) + batch.atom_local.records[1:])),
                          error="template_lf")
        batch = self.batches[64]
        row = replace(batch.closed.records[0], context_roundtrip_bytes=b"changed")
        self.reject_batch(replace(batch, closed=replace(batch.closed, records=(row,) + batch.closed.records[1:])),
                          64, "repeated_unit")

    def test_initial_batch_invalid_before_torch_or_model_access(self):
        with self.assertRaisesRegex(ValueError, "complete_512_update_plan"):
            source.StatefulTrainer(None, arm="CLOSED", master=MASTER, batches=self.batches[:256],
                                   trainable_roster=planned_roster(), layer_count=1, adapter_name="default",
                                   lineage_id="SYNTHETIC-ONLY", preparation_sha256="0" * 64,
                                   initial_adapter_sha256="1" * 64)

    def test_exact_all_layer_lora_name_shape_dtype_roster(self):
        roster = planned_roster()
        self.assertEqual(source.validate_trainable_roster(roster, layer_count=1, adapter_name="default"), roster)
        variants = (roster[:-1], roster + roster[:1], roster[:-1] + roster[:1],
                    (replace(roster[0], name="model.embed_tokens.weight"),) + roster[1:],
                    (replace(roster[0], name=roster[0].name.replace("layers.0", "layers.1")),) + roster[1:],
                    (replace(roster[0], name=roster[0].name.replace("default", "other")),) + roster[1:],
                    (replace(roster[0], shape=(4, 4)),) + roster[1:],
                    (replace(roster[0], dtype="torch.float16"),) + roster[1:])
        for variant in variants:
            with self.assertRaises(ValueError):
                source.validate_trainable_roster(variant, layer_count=1, adapter_name="default")
        with self.assertRaises(ValueError):
            source.validate_trainable_roster(roster, layer_count=True, adapter_name="default")

    def test_exact_checkpoint_boundaries_without_tensor_evidence(self):
        source.validate_stage_cursor(256, 1024)
        source.validate_stage_cursor(512, 2048)
        for completed, cursor in ((0, 0), (255, 1020), (257, 1028), (256, 256), (512, 1024),
                                  (256.0, 1024), (True, 4), (256, 1024.0)):
            with self.assertRaises(ValueError):
                source.validate_stage_cursor(completed, cursor)

    def test_actual_tokenization_worker_batch_interface(self):
        from tests.test_composition_birth_stage2a_tokenization import FakeTokenizer
        first = self.batches[0]
        pair = tokenization.targets.PairedTarget(first.closed.records[0].record, first.atom_local.records[0].record)
        prepared = tokenization.tokenize_paired_target(pair, tokenizer=FakeTokenizer(), count_basis="SYNTHETIC_FIXTURE")
        source._validate_row(prepared.closed, "CLOSED")
        source._validate_row(prepared.atom_local, "ATOM_LOCAL")
        self.assertEqual(prepared.closed.labels[prepared.closed.target_end:], (-100,))


def tiny_native_model():
    import torch
    from torch.utils.checkpoint import checkpoint

    class TinyLoRA(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.base = torch.nn.Linear(4, 4, bias=False, dtype=torch.bfloat16)
            self.base.weight.requires_grad_(False)
            self.lora_A = torch.nn.ModuleDict({"default": torch.nn.Linear(4, 8, bias=False)})
            self.lora_B = torch.nn.ModuleDict({"default": torch.nn.Linear(8, 4, bias=False)})
            torch.nn.init.zeros_(self.lora_B["default"].weight)
            self.lora_dropout = torch.nn.ModuleDict({"default": torch.nn.Dropout(0.05)})
            self.r, self.lora_alpha, self.scaling = {"default": 8}, {"default": 16}, {"default": 2}
            self.disable_adapters = self.merged = False

        def forward(self, hidden):
            adapter = self.lora_B["default"](self.lora_A["default"](self.lora_dropout["default"](hidden)))
            return hidden + 0.1 * self.base(hidden) + self.scaling["default"] * adapter

    class TinyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = torch.nn.Module()
            layer = torch.nn.Module()
            self.model.layers = torch.nn.ModuleList([layer])
            for group, names in (("self_attn", source.TARGET_MODULES[:4]), ("mlp", source.TARGET_MODULES[4:])):
                modules = torch.nn.Module()
                setattr(layer, group, modules)
                for name in names:
                    setattr(modules, name, TinyLoRA())
            self.embedding = torch.nn.Embedding(16, 4, dtype=torch.bfloat16)
            self.embedding.weight.requires_grad_(False)
            self.config = SimpleNamespace(num_hidden_layers=1, use_cache=False, max_position_embeddings=16384)
            self.peft_config = {"default": SimpleNamespace(
                r=8, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                init_lora_weights=True, target_modules=source.TARGET_MODULES)}
            self.active_adapters, self.is_gradient_checkpointing = ["default"], True
            self.forward_calls, self.nonfinite = 0, False

        def get_input_embeddings(self):
            return self.embedding

        def forward(self, input_ids, labels, attention_mask, use_cache):
            self.forward_calls += 1
            if use_cache or input_ids.shape[0] != 4:
                raise AssertionError("The native fixture requires one un-packed batch of four")
            hidden = self.embedding(input_ids) * attention_mask.unsqueeze(-1)

            def transform(values):
                for group in (self.model.layers[0].self_attn, self.model.layers[0].mlp):
                    for module in group.children():
                        values = module(values)
                return values

            hidden = checkpoint(transform, hidden, use_reentrant=False)
            logits = torch.nn.functional.linear(hidden, self.embedding.weight)
            loss = torch.nn.functional.cross_entropy(logits[:, :-1].float().reshape(-1, 16),
                                                     labels[:, 1:].reshape(-1), ignore_index=-100)
            return SimpleNamespace(loss=loss * float("nan") if self.nonfinite else loss)

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(1729)
        return TinyModel()


@unittest.skipUnless(HAS_TORCH, "native torch absent on VM; no optimizer steps tested")
class Stage2ATrainingNativeCPUTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        cls.torch = torch
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.batches = fixture()
        cls.roster = planned_roster()
        cls.initial_digest = source.adapter_sha256(tiny_native_model(), cls.roster)
        cls.d1_trainer = cls.trainer()
        cls.d1_trainer.train_stage("D1")
        cls.d1_checkpoint = cls.d1_trainer.checkpoint()

    @classmethod
    def tearDownClass(cls):
        cls.torch.set_num_threads(cls.threads)

    @classmethod
    def trainer(cls, *, model=None, checkpoint=None, arm="CLOSED", **overrides):
        kwargs = dict(arm=arm, master=MASTER, batches=cls.batches, trainable_roster=cls.roster,
                      layer_count=1, adapter_name="default", lineage_id="SYNTHETIC-CPU-" + arm,
                      preparation_sha256="a" * 64, initial_adapter_sha256=cls.initial_digest,
                      checkpoint=checkpoint)
        kwargs.update(overrides)
        return source.StatefulTrainer(tiny_native_model() if model is None else model, **kwargs)

    @staticmethod
    def rehash(checkpoint):
        checkpoint["sha256"] = source._digest(source._tree_hash(
            {key: value for key, value in checkpoint.items() if key != "sha256"}))

    def test_256_to_512_continuity_exact_adapter_optimizer_and_rng(self):
        uninterrupted = self.trainer(checkpoint=self.d1_checkpoint)
        self.assertEqual(uninterrupted.completed_updates, 256)
        self.assertEqual(uninterrupted.cursor, 1024)
        self.assertEqual(source._rng_hashes(source._rng_state()), source._rng_hashes(self.d1_checkpoint["rng"]))
        self.assertEqual(source._tree_hash(uninterrupted.optimizer.state_dict()), source._tree_hash(self.d1_checkpoint["optimizer"]))
        uninterrupted.train_stage("D2")
        expected = uninterrupted.checkpoint()
        self.d1_trainer.train_stage("D2")
        actual = self.d1_trainer.checkpoint()
        self.assertEqual(source._tree_hash(actual), source._tree_hash(expected))
        self.assertEqual(actual["completed_updates"], 512)
        self.assertEqual(actual["cursor"], 2048)
        self.assertEqual(self.d1_trainer.model.forward_calls, 512)
        self.assertEqual(uninterrupted.model.forward_calls, 256)
        self.assertEqual(actual["receipts"][256]["update_number"], 257)
        self.assertTrue(all(math.isfinite(row["loss"]) for row in actual["receipts"]))
        self.assertTrue(all(state["step"].item() == 512 for state in actual["optimizer"]["state"].values()))
        with self.assertRaisesRegex(ValueError, "invalid_stage_transition"):
            uninterrupted.train_stage("D2")

    def test_paired_rng_start_equal_not_masks_or_moments(self):
        atom = self.trainer(arm="ATOM_LOCAL")
        atom.train_stage("D1")
        closed_receipts = self.d1_checkpoint["receipts"]
        for closed, local in zip(closed_receipts, atom.receipts):
            self.assertEqual(closed["pre_forward_rng"], local["pre_forward_rng"])
            self.assertEqual(closed["rng_start_seed"], local["rng_start_seed"])
            self.assertEqual(closed["target_token_counts"], local["target_token_counts"])
            self.assertFalse(local["masks_identical_claim"])
        self.assertNotEqual(source._tree_hash(atom.optimizer.state_dict()), source._tree_hash(self.d1_checkpoint["optimizer"]))

    def test_bad_resume_fails_before_forward_and_model_mutation(self):
        for fault in ("cursor", "arm", "preparation", "missing_optimizer", "missing_moment", "step", "second_moment",
                      "adapter_nan", "rng", "rng_size", "loss_history", "recipe", "state_dtype", "target_receipt"):
            with self.subTest(fault=fault):
                checkpoint = source._tree_copy(self.d1_checkpoint)
                if fault == "cursor":
                    checkpoint["cursor"] = 256
                elif fault == "arm":
                    checkpoint["binding"]["arm"] = "ATOM_LOCAL"
                elif fault == "preparation":
                    checkpoint["binding"]["preparation_sha256"] = "b" * 64
                elif fault == "missing_optimizer":
                    del checkpoint["optimizer"]
                elif fault == "missing_moment":
                    del checkpoint["optimizer"]["state"][0]
                elif fault == "step":
                    checkpoint["optimizer"]["state"][0]["step"].fill_(255)
                elif fault == "second_moment":
                    checkpoint["optimizer"]["state"][0]["exp_avg_sq"].fill_(-1)
                elif fault == "adapter_nan":
                    checkpoint["adapter"][self.roster[0].name].fill_(float("nan"))
                elif fault == "rng":
                    checkpoint["rng"]["cpu"] = checkpoint["rng"]["cpu"].float()
                elif fault == "rng_size":
                    checkpoint["rng"]["cpu"] = checkpoint["rng"]["cpu"][:1]
                elif fault == "loss_history":
                    checkpoint["receipts"].pop()
                elif fault == "recipe":
                    checkpoint["optimizer"]["param_groups"][0]["lr"] = 1e-3
                elif fault == "state_dtype":
                    checkpoint["optimizer"]["state"][0]["exp_avg"] = checkpoint["optimizer"]["state"][0]["exp_avg"].double()
                elif fault == "target_receipt":
                    checkpoint["receipts"][0]["target_hashes"] = ("0" * 64,) * 4
                self.rehash(checkpoint)
                model = tiny_native_model()
                before = source.adapter_sha256(model, self.roster)
                rng_before = source._rng_hashes(source._rng_state())
                with self.assertRaises(ValueError):
                    self.trainer(model=model, checkpoint=checkpoint)
                self.assertEqual(model.forward_calls, 0)
                self.assertEqual(source.adapter_sha256(model, self.roster), before)
                self.assertEqual(source._rng_hashes(source._rng_state()), rng_before)

    def test_resume_digest_detects_unrehashable_external_changes(self):
        checkpoint = source._tree_copy(self.d1_checkpoint)
        checkpoint["adapter"][self.roster[0].name].add_(1)
        with self.assertRaisesRegex(ValueError, "checkpoint_digest_mismatch"):
            self.trainer(checkpoint=checkpoint)

    def test_nonfinite_loss_performs_no_native_step_and_poisons_lineage(self):
        model = tiny_native_model()
        trainer = self.trainer(model=model)
        before = source.adapter_sha256(model, self.roster)
        model.nonfinite = True
        with self.assertRaisesRegex(ValueError, "finite_scalar_training_loss"):
            trainer.train_stage("D1")
        self.assertEqual(model.forward_calls, 1)
        self.assertEqual(trainer.completed_updates, 0)
        self.assertEqual(trainer.optimizer.state_dict()["state"], {})
        self.assertEqual(source.adapter_sha256(model, self.roster), before)
        with self.assertRaisesRegex(ValueError, "failed_lineage_cannot_retry"):
            trainer.train_stage("D1")
        with self.assertRaises(ValueError):
            trainer.checkpoint()

    def test_nonfinite_native_gradient_fails_before_optimizer_step(self):
        trainer = self.trainer()
        before = source.adapter_sha256(trainer.model, self.roster)
        handle = trainer.named[0][1].register_hook(lambda gradient: self.torch.full_like(gradient, float("inf")))
        try:
            with self.assertRaisesRegex(ValueError, "nonfinite_lora_gradient"):
                trainer.train_stage("D1")
        finally:
            handle.remove()
        self.assertEqual(trainer.model.forward_calls, 1)
        self.assertEqual(trainer.optimizer.state_dict()["state"], {})
        self.assertEqual(trainer.completed_updates, 0)
        self.assertEqual(source.adapter_sha256(trainer.model, self.roster), before)

    def test_prepared_model_config_and_initialization_rejections(self):
        for fault in ("trainable_base", "dropout", "checkpointing", "rank", "initial_hash"):
            model = tiny_native_model()
            kwargs = {}
            if fault == "trainable_base":
                model.embedding.weight.requires_grad_(True)
            elif fault == "dropout":
                model.model.layers[0].self_attn.q_proj.lora_dropout["default"].p = 0
            elif fault == "checkpointing":
                model.is_gradient_checkpointing = False
            elif fault == "rank":
                model.peft_config["default"].r = 16
            else:
                kwargs["initial_adapter_sha256"] = "0" * 64
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                self.trainer(model=model, **kwargs)
            self.assertEqual(model.forward_calls, 0)

    def test_live_optimizer_drift_fails_before_d2(self):
        for fault in ("lr", "reorder", "fresh_optimizer"):
            trainer = self.trainer(checkpoint=self.d1_checkpoint)
            if fault == "lr":
                trainer.optimizer.param_groups[0]["lr"] = 1e-3
            elif fault == "reorder":
                trainer.optimizer.param_groups[0]["params"].reverse()
            else:
                trainer.optimizer = self.torch.optim.AdamW([parameter for _, parameter in trainer.named], **source.OPTIMIZER_RECIPE)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                trainer.train_stage("D2")
            self.assertEqual(trainer.model.forward_calls, 0)
            self.assertEqual(trainer.completed_updates, 256)

    def test_checkpoint_owns_copies_and_retains_training_rng_not_ambient_rng(self):
        trainer = self.trainer(checkpoint=self.d1_checkpoint)
        self.torch.rand(11)
        saved = trainer.checkpoint()
        self.assertEqual(source._rng_hashes(saved["rng"]), source._rng_hashes(self.d1_checkpoint["rng"]))
        saved["adapter"][self.roster[0].name].add_(1)
        saved["optimizer"]["state"][0]["exp_avg"].add_(1)
        self.assertEqual(source._tree_hash(trainer.checkpoint()), source._tree_hash(self.d1_checkpoint))


if __name__ == "__main__":
    unittest.main()
