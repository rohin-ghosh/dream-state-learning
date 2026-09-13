"""Stdlib tests by default; Main alone runs --torch-cpu --out FRESH_PATH."""
from __future__ import annotations

from collections import Counter
import copy
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import time
import traceback
import unittest

sys.dont_write_bytecode = True
MODULE_PATH = Path(__file__).with_name("astra_additive_replay_train_20260913.py")
specification = importlib.util.spec_from_file_location("additive_candidate", MODULE_PATH)
candidate = importlib.util.module_from_spec(specification)
specification.loader.exec_module(candidate)
ARCHIVE = Path("/data/home/rohing/dream-state/gpu_artifacts_local/own_replay_repair_20260913_attempt1/evidence.tar")


class FixtureTokenizer:
    eos_token_id = 1
    pad_token_id = 0

    def encode(self, text, add_special_tokens=False):
        pieces = text.split("<|im_end|>")
        result = []
        for index, piece in enumerate(pieces):
            if index:
                result.append(self.eos_token_id)
            result.extend(ord(character)+3 for character in piece)
        return result

    def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        return "".join("<|im_end|>" if token == self.eos_token_id else chr(token-3) for token in ids)


def fixture_item(trainer, tokenizer, row_id, target, index=0, kind="memory"):
    prompt = "Public Q: "
    item = dict(group=row_id, order=index, view="fixture", category="target",
                spans=[[prompt, False, "context"], [target, True, "skill_target"],
                       ["<|im_end|>", True, "assistant_end"], ["\n", False, "template_tail"]],
                meta=dict(row_id=row_id, source_row_id="fixture-source:"+row_id,
                          target_sha256=candidate.hashlib.sha256(target.encode()).hexdigest(),
                          item_kind=kind, presentation_index=index))
    segment = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")[0]
    audit = dict(row_id=row_id, source_row_id=item["meta"]["source_row_id"], item_kind=kind, presentation_index=index,
                 full_assistant_text="".join(span[0] for span in item["spans"]), input_ids=segment.ids,
                 labels=segment.labels, supervised_ids=[label for label in segment.labels if label != -100],
                 template_tail="\n", native_prompt=dict(rendered_prompt=prompt,
                                                        prompt_token_ids=tokenizer.encode(prompt)))
    return item, audit


def pure_config(trainer, **changes):
    config = trainer.TrainConfig(rank=8, alpha=16, dropout=.05, lr=3e-5, epochs=8, max_len=1024,
                                seed=0, overflow="truncate", pack=False, add_eos=False)
    return replace(config, **changes)


class PureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trainer = candidate.load_trainer()
        cls.tokenizer = FixtureTokenizer()
        cls.sources = {}
        cls.byte_pins = {}
        with tarfile.open(ARCHIVE, "r") as archive:
            for seed in range(3):
                cls.sources[seed] = []
                cls.byte_pins[seed] = {}
                for arm in ("EXTRA_MEMORY", "REPLAY"):
                    name = f"own_replay_repair_seed{seed}_20260913_attempt1/training_{arm}.json"
                    members = [member for member in archive.getmembers() if member.name == name]
                    candidate.require(len(members) == 1 and members[0].isfile(), "unique regular fixture member required")
                    raw = archive.extractfile(members[0]).read()
                    cls.byte_pins[seed][arm.lower()+"_sha256"] = candidate.hashlib.sha256(raw).hexdigest()
                    cls.sources[seed].append(json.loads(raw))

    def pair(self, seed=0):
        return candidate.prepare_pair(*self.sources[seed], seed=seed, source_pins=self.byte_pins[seed])

    def fixture(self):
        return fixture_item(self.trainer, self.tokenizer, "fixture:one", "a raw answer")

    def test_01_all_original_file_bytes_and_objects_bound(self):
        for seed in range(3):
            paired = self.pair(seed)
            candidate.validate_pair(paired)
            self.assertEqual(paired["primary"], self.sources[seed][0])
            self.assertEqual(paired["replay"], self.sources[seed][1])

    def test_02_exact_memory_schedule_and_update_counts(self):
        for seed, updates in enumerate((304, 256, 256)):
            paired = self.pair(seed)
            for arm in candidate.ARMS:
                self.assertEqual(paired["costs"][arm]["updates"], updates)
                self.assertEqual(paired["costs"][arm]["memory_forwards"], updates)
            self.assertEqual(paired["primary"]["epoch_order"], self.sources[seed][0]["epoch_order"])
            self.assertEqual(set(Counter(row for order in paired["primary"]["epoch_order"] for row in order).values()), {8})

    def test_03_pairing_bijective_and_eight_replays(self):
        for seed in range(3):
            paired = self.pair(seed)
            self.assertEqual(len({pair["memory_row_id"] for pair in paired["pairs"]}), 24)
            self.assertEqual(len({pair["replay_row_id"] for pair in paired["pairs"]}), 24)
            mapping = {pair["memory_row_id"]: pair["replay_row_id"] for pair in paired["pairs"]}
            counts = Counter(mapping[row] for order in paired["primary"]["epoch_order"] for row in order if row in mapping)
            self.assertEqual(set(counts.values()), {8})
            self.assertEqual(paired["costs"]["ADDITIVE"]["replay_forwards"], 192)
            self.assertEqual(paired["costs"]["MEMORY_ONLY"]["replay_forwards"], 0)

    def test_04_seed0_unequal_cycling_preserved(self):
        source_ids = [item["meta"]["source_row_id"] for item in self.pair()["primary"]["items"]]
        self.assertEqual(Counter(Counter(source_ids).values()), {3: 10, 2: 4})

    def test_05_costs_exact_per_kind(self):
        expected_memory = (52888, 43552, 44928)
        expected_targets = (8776, 6368, 7744)
        for seed in range(3):
            costs = self.pair(seed)["costs"]
            for arm in candidate.ARMS:
                self.assertEqual(costs[arm]["memory_total_tokens"], expected_memory[seed])
                self.assertEqual(costs[arm]["memory_supervised_tokens"], expected_targets[seed])
                self.assertEqual(costs[arm]["total_tokens"], costs[arm]["supervised_tokens"]+costs[arm]["context_tokens"])
            self.assertEqual(costs["ADDITIVE"]["replay_total_tokens"], 66184)
            self.assertEqual(costs["ADDITIVE"]["replay_supervised_tokens"], 5688)

    def test_06_teacher_held_raw_source_tampering_rejected(self):
        for key, value in (("target", "teacher replacement"), ("context", "held answer"), ("source", "foreign source")):
            sources = copy.deepcopy(self.sources[0])
            if key == "source":
                sources[1]["items"][-1]["meta"]["source_row_id"] = value
            else:
                sources[1]["items"][-1]["spans"][key == "target"][0] = value
            with self.assertRaisesRegex(ValueError, "original encoded object"):
                candidate.prepare_pair(*sources, seed=0, source_pins=self.byte_pins[0])

    def test_07_repin_cannot_bypass_original_files(self):
        sources = copy.deepcopy(self.sources[0])
        sources[0]["items"][0]["spans"][1][0] = "different"
        pins = dict(self.byte_pins[0], extra_memory_sha256=candidate.value_hash(sources[0]))
        with self.assertRaisesRegex(ValueError, "file byte pin"):
            candidate.prepare_pair(*sources, seed=0, source_pins=pins)

    def test_08_pair_order_and_cost_tampering_rejected(self):
        for field in ("pairs", "costs", "epoch_order"):
            paired = self.pair()
            if field == "pairs":
                paired["pairs"].reverse()
            elif field == "costs":
                paired["costs"]["ADDITIVE"]["updates"] += 1
            else:
                paired["primary"]["epoch_order"][0].reverse()
            paired["paired_sha256"] = candidate.value_hash(candidate._without(paired, "paired_sha256"))
            with self.assertRaises(ValueError):
                candidate.validate_pair(paired)

    def test_09_missing_replay_and_unknown_seed_rejected(self):
        sources = copy.deepcopy(self.sources[0])
        sources[1]["items"].pop()
        with self.assertRaises(ValueError):
            candidate.prepare_pair(*sources, seed=0, source_pins=self.byte_pins[0])
        with self.assertRaises(ValueError):
            candidate.prepare_pair(*self.sources[0], seed=True, source_pins=self.byte_pins[0])

    def test_10_preparation_does_not_mutate_inputs(self):
        before = candidate.value_hash(self.sources)
        paired = self.pair()
        paired["primary"]["items"][0]["spans"][1][0] = "local only"
        self.assertEqual(candidate.value_hash(self.sources), before)

    def test_11_raw_roundtrip_eos_and_masks(self):
        item, audit = self.fixture()
        segments = candidate.validate_encoding([item], [audit], self.tokenizer, self.trainer, pure_config(self.trainer))
        self.assertEqual(len(segments), 1)
        self.assertEqual(audit["supervised_ids"][-1], self.tokenizer.eos_token_id)
        self.assertEqual(audit["labels"][0], -100)
        self.assertEqual(audit["labels"][-1], -100)

    def test_12_supervised_context_and_missing_eos_rejected(self):
        item, audit = self.fixture()
        for change in ("context", "eos", "tail"):
            altered_item, altered_audit = copy.deepcopy(item), copy.deepcopy(audit)
            if change == "context":
                altered_audit["labels"][0] = altered_audit["input_ids"][0]
            elif change == "eos":
                altered_item["spans"][2][0] = ""
            else:
                altered_item["spans"][3][1] = True
            with self.assertRaises(ValueError):
                candidate.validate_encoding([altered_item], [altered_audit], self.tokenizer, self.trainer, pure_config(self.trainer))

    def test_13_target_or_context_truncation_rejected(self):
        item, audit = self.fixture()
        for length in (4, 20):
            with self.assertRaisesRegex(ValueError, "truncation"):
                candidate.validate_encoding([item], [audit], self.tokenizer, self.trainer, pure_config(self.trainer, max_len=length))

    def test_14_split_missing_and_tokenizer_drift_rejected(self):
        item, audit = self.fixture()
        with self.assertRaises(ValueError):
            candidate.validate_encoding([item], [audit], self.tokenizer, self.trainer,
                                        pure_config(self.trainer, max_len=16, overflow="split"))
        with self.assertRaises(ValueError):
            candidate.validate_encoding([item], [], self.tokenizer, self.trainer, pure_config(self.trainer))
        class Drift(FixtureTokenizer):
            def encode(self, text, add_special_tokens=False):
                return [token+1 for token in super().encode(text, add_special_tokens)]
        with self.assertRaises(ValueError):
            candidate.validate_encoding([item], [audit], Drift(), self.trainer, pure_config(self.trainer))

    def test_15_raw_target_roundtrip_failure_rejected(self):
        item, audit = self.fixture()
        class BadDecode(FixtureTokenizer):
            def decode(self, ids, **kwargs):
                return "canonicalized rather than raw"
        with self.assertRaisesRegex(ValueError, "roundtrip"):
            candidate.validate_encoding([item], [audit], BadDecode(), self.trainer, pure_config(self.trainer))

    def test_16_toy_recipe_has_no_production_bypass(self):
        config = pure_config(self.trainer)
        candidate._validate_config(config, 0, self.trainer)
        for change in (dict(device="cpu"), dict(rank=2), dict(epochs=1), dict(lr=1e-4), dict(add_eos=True), dict(pack=True)):
            with self.assertRaises(ValueError):
                candidate._validate_config(replace(config, **change), 0, self.trainer)
        with self.assertRaises(ValueError):
            candidate.run_training({}, None, None, config, "/unused", arm="MEMORY_ONLY", init_adapter="/unused", expected_parent_files={})

    def test_17_failure_writeonce_and_unowned_output(self):
        with tempfile.TemporaryDirectory(prefix="astra-additive-pure-") as directory:
            root = Path(directory)
            done = root / "DONE"
            done.write_bytes(b"other writer\n")
            candidate._owned_failure(root, ValueError("test"), False)
            self.assertEqual(done.read_bytes(), b"other writer\n")
            self.assertFalse((root / "failure.json").exists())
            candidate._owned_failure(root, ValueError("owned failure"), True)
            self.assertFalse(done.exists())
            self.assertEqual(json.loads((root / "failure.json").read_text())["status"], "FAILED")
            with self.assertRaises(FileExistsError):
                candidate._write_json(root / "failure.json", {})

    def test_18_frozen_source_pin_and_no_heavy_imports(self):
        self.assertEqual(candidate.digest(self.trainer.__file__), candidate.TRAINER_PIN)
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("peft", sys.modules)
        self.assertNotIn("transformers", sys.modules)

    def test_19_frozen_packing_sort_precedes_epoch_shuffle(self):
        for seed in range(3):
            source = self.sources[seed][0]
            segments = [self.trainer.Encoded(ids=audit["input_ids"], labels=audit["labels"], cats=[],
                        group=item["group"], order=item["order"], view=item["view"], item_index=index,
                        n_target=len(audit["supervised_ids"]))
                        for index, (item, audit) in enumerate(zip(source["items"], source["encoding"]))]
            packs = self.trainer.pack_by_group(list(reversed(segments)), 1024, False)
            orders = [[pack[0].group for pack in self.trainer.epoch_order(packs, seed, epoch, True)] for epoch in range(8)]
            self.assertEqual(orders, source["epoch_order"])


def run_torch_cpu(out_dir, trainer_path):
    candidate.require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "Main must explicitly set CUDA_VISIBLE_DEVICES=''")
    output = Path(out_dir).absolute()
    candidate.require(not any(path.is_symlink() for path in (output, *output.parents)), "fixture output cannot be symlinked")
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema="astra_additive_replay_tiny_cpu_receipt_v1", status="RUNNING", fixture_only=True,
                   native_scientific_evidence=False, trainer_sha256=candidate.digest(MODULE_PATH),
                   tests_sha256=candidate.digest(__file__), frozen_trainer_sha256=candidate.TRAINER_PIN,
                   protocol_sha256=candidate.PROTOCOL_PIN, output=str(output), checks={})
    started = time.monotonic()
    try:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        import torch
        import torch.nn.functional as functional
        from transformers import Qwen2Config, Qwen2ForCausalLM
        trainer = candidate.load_trainer(trainer_path)
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        receipt["versions"] = trainer._versions()
        tokenizer = FixtureTokenizer()
        config = trainer.TrainConfig(rank=2, alpha=4, dropout=.05, lr=3e-5, epochs=2, max_len=128,
                                     pack=False, batch_size=1, device="cpu", dtype="fp32", model=str(output/"tiny-base-config"),
                                     grad_checkpoint=False, log_every=0, add_eos=False, overflow="truncate", seed=7)
        model_config = Qwen2Config(vocab_size=256, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                  num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=256,
                                  tie_word_embeddings=False)
        model_config._attn_implementation = "eager"
        model_config._name_or_path = config.model
        model_config.save_pretrained(config.model)

        def base():
            torch.manual_seed(137)
            model = Qwen2ForCausalLM(copy.deepcopy(model_config)).float().cpu()
            model.name_or_path = config.model
            return model

        memory = [fixture_item(trainer, tokenizer, "tiny:original", "yes", 0),
                  fixture_item(trainer, tokenizer, "tiny:extra", "no", 1, "extra_memory")]
        observation = [fixture_item(trainer, tokenizer, "tiny:observation", "a longer raw answer", 2, "observation_replay")]
        items, audits = [row[0] for row in memory], [row[1] for row in memory]
        replay_items, replay_audits = [row[0] for row in observation], [row[1] for row in observation]
        primary = candidate.validate_encoding(items, audits, tokenizer, trainer, config)
        replay = candidate.validate_encoding(replay_items, replay_audits, tokenizer, trainer, config)
        packs = trainer.pack_by_group(primary, config.max_len, False)
        orders = [[pack[0].group for pack in trainer.epoch_order(packs, config.seed, epoch, True)]
                  for epoch in range(config.epochs)]
        pairs = [dict(memory_row_id="tiny:extra", replay_row_id="tiny:observation")]
        candidate._write_json(output / "fixture.json", dict(config=vars(config), items=items, encoding=audits,
                              replay_items=replay_items, replay_encoding=replay_audits, orders=orders, pairs=pairs))
        parent = output / "parent"
        trainer.run_training(items, tokenizer, base(), replace(config, epochs=1), str(parent), log=lambda text: None)
        parent_files = trainer._warm_inventory(parent)
        candidate._write_json(output / "parent_inventory.json", parent_files)
        legacy = trainer.run_training(items, tokenizer, base(), config, str(output / "legacy"),
                                      log=lambda text: None, init_adapter=str(parent))

        def execute(name, arm, supplied_base=None):
            model = base() if supplied_base is None else supplied_base
            before = [(parameter, parameter.detach().clone()) for parameter in model.parameters()]
            manifest = candidate._run_encoded(primary, replay, orders, pairs, tokenizer, model, config, output/name,
                          arm=arm, init_adapter=parent, expected_parent_files=parent_files, trainer=trainer,
                          binding=dict(schema="astra_additive_replay_tiny_fixture_v1", fixture_only=True,
                                       arm=arm, objective=candidate.OBJECTIVES[arm],
                                       costs=candidate._costs(audits, replay_audits, config.epochs, arm)), log=lambda text: None)
            candidate.require(all(torch.equal(parameter.detach(), old) and not parameter.requires_grad for parameter, old in before),
                              "fixture base changed or trainable")
            return manifest

        baseline = execute("baseline", "MEMORY_ONLY")
        additive = execute("additive", "ADDITIVE")

        def saved_state(path):
            if (path / "adapter_model.safetensors").is_file():
                from safetensors.torch import load_file
                return load_file(str(path / "adapter_model.safetensors"), device="cpu")
            return torch.load(str(path / "adapter_model.bin"), map_location="cpu", weights_only=True)

        old_state, new_state = saved_state(output/"legacy"), saved_state(output/"baseline")
        candidate.require(set(old_state) == set(new_state), "baseline tensor keys differ")
        differences = {name: (old_state[name]-new_state[name]).abs().max().item() for name in old_state}
        candidate.require(max(differences.values()) == 0, "MEMORY_ONLY differs from legacy final tensors")
        candidate.require(legacy["mean_loss_per_epoch"] == baseline["mean_loss_per_epoch"] and
                          legacy["final_loss"] == baseline["final_loss"], "baseline loss parity differs")
        candidate._write_json(output / "baseline_parity.json", dict(max_absolute_tensor_differences=differences,
                              losses_equal=True, exact_tensor_equality=True))
        receipt["checks"]["legacy_memory_only_parity"] = True
        for manifest in (baseline, additive):
            warm = manifest["warm_start"]
            candidate.require(warm["source_state"] == legacy["warm_start"]["source_state"] and
                              warm["initialized_state"] == legacy["warm_start"]["initialized_state"] and
                              warm["optimizer_defaults"] == legacy["warm_start"]["optimizer_defaults"] and
                              warm["optimizer_initial_state_entries"] == 0 and not warm["optimizer_state_restored"] and
                              not warm["optimizer_state_saved"] and warm["adapter_count"] == 1 and warm["base_frozen"],
                              "initialization/optimizer/base contract differs")
            candidate.require(manifest["steps"] == 4 and manifest["memory_forwards"] == 4, "tiny memory update count differs")
        candidate.require(baseline["replay_forwards"] == 0 and additive["replay_forwards"] == 2, "tiny replay count differs")
        candidate.require([row["memory_row_id"] for row in baseline["executed_order"]] ==
                          [row["memory_row_id"] for row in additive["executed_order"]], "memory order differs")
        receipt["checks"]["fresh_optimizer_base_frozen_parent_load_and_exposures"] = True

        warm = trainer._warm_parent(parent, output/"gradient-unsaved", config)
        model, _ = trainer._warm_initialize(base(), config, warm)
        model.eval()
        memory_tensors = trainer.to_tensors(trainer.collate([[primary[1]]], tokenizer.pad_token_id), torch.device("cpu"), torch.float32, "2d")
        replay_tensors = trainer.to_tensors(trainer.collate([[replay[0]]], tokenizer.pad_token_id), torch.device("cpu"), torch.float32, "2d")
        params = [parameter for parameter in model.parameters() if parameter.requires_grad]

        def grads():
            return torch.cat([parameter.grad.detach().flatten().clone() for parameter in params])

        def independent(tensors):
            model.zero_grad(set_to_none=True)
            result = model(**tensors)
            labels = tensors["labels"][:, 1:].reshape(-1)
            logits = result.logits[:, :-1, :].float().reshape(-1, result.logits.shape[-1])
            explicit = functional.cross_entropy(logits, labels, ignore_index=-100, reduction="mean")
            candidate.require(torch.allclose(result.loss, explicit, atol=1e-7, rtol=1e-7), "legacy loss is not separate masked mean CE")
            explicit.backward()
            return explicit.item(), grads(), int((labels != -100).sum())

        memory_loss, memory_gradient, memory_labels = independent(memory_tensors)
        replay_loss, replay_gradient, replay_labels = independent(replay_tensors)
        candidate.require(memory_labels != replay_labels, "unequal target lengths required")
        model.zero_grad(set_to_none=True)
        composed = candidate.backward_components(model, memory_tensors, replay_tensors)
        actual = grads()
        expected_sum = memory_gradient+replay_gradient
        average = expected_sum/2
        pooled = (memory_gradient*memory_labels+replay_gradient*replay_labels)/(memory_labels+replay_labels)
        candidate.require(torch.allclose(actual, expected_sum, atol=1e-7, rtol=1e-6), "paired gradient is not sum")
        candidate.require(not torch.allclose(actual, average, atol=1e-7, rtol=1e-6) and
                          not torch.allclose(actual, pooled, atol=1e-7, rtol=1e-6), "sum indistinguishable from wrong normalization")
        candidate.require(abs(composed["total"]-memory_loss-replay_loss) < 1e-6, "loss sum differs")
        torch.save(dict(memory=memory_gradient, replay=replay_gradient, actual=actual, expected_sum=expected_sum,
                        wrong_average=average, wrong_pooled=pooled), output/"gradient_vectors.pt")
        candidate._write_json(output/"gradient_algebra.json", dict(memory_labels=memory_labels, replay_labels=replay_labels,
                              memory_loss=memory_loss, replay_loss=replay_loss, composed=composed,
                              sum_max_error=(actual-expected_sum).abs().max().item(),
                              wrong_average_max_difference=(actual-average).abs().max().item(),
                              wrong_pooled_max_difference=(actual-pooled).abs().max().item(),
                              context_labels_masked=True, algebra_dropout_mode="eval; parity training uses dropout0.05"))
        receipt["checks"]["unequal_length_separate_masked_mean_ce_gradient_sum"] = True

        for failure_kind in ("loss", "gradient"):
            broken = base()
            if failure_kind == "loss":
                with torch.no_grad():
                    broken.lm_head.weight.fill_(float("nan"))
            else:
                def poison_gradient(module, args, result):
                    if result.requires_grad:
                        result.register_hook(lambda gradient: gradient*float("nan"))
                broken.lm_head.register_forward_hook(poison_gradient)
            try:
                execute("failure-"+failure_kind, "ADDITIVE", broken)
                raise AssertionError("nonfinite fixture unexpectedly completed")
            except ValueError as error:
                candidate.require("nonfinite" in str(error), "unexpected failure instead of finite guard")
            candidate.require(not (output/("failure-"+failure_kind)/"DONE").exists() and
                              (output/("failure-"+failure_kind)/"failure.json").is_file(), "failure custody missing")
        receipt["checks"]["nonfinite_loss_and_gradient_reject_no_done"] = True
        baseline_files = trainer._warm_inventory(output/"baseline")
        try:
            execute("baseline", "MEMORY_ONLY")
            raise AssertionError("existing output accepted")
        except ValueError as error:
            candidate.require("fresh" in str(error), "unexpected output failure")
        candidate.require(trainer._warm_inventory(output/"baseline") == baseline_files and
                          trainer._warm_inventory(parent) == parent_files, "existing output/parent changed")
        receipt["checks"]["existing_output_writeonce_and_parent_immutable"] = True
        receipt["status"] = "PASS"
    except BaseException as error:
        receipt.update(status="FAIL", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt["elapsed_seconds"] = time.monotonic()-started
        receipt["retained_files"] = {str(path.relative_to(output)): candidate.digest(path)
                                     for path in sorted(output.rglob("*")) if path.is_file()}
        candidate._write_json(output/"receipt.json", receipt)
        print(json.dumps(dict(status=receipt["status"], receipt=str(output/"receipt.json"),
                              sha256=candidate.digest(output/"receipt.json")), sort_keys=True))


if __name__ == "__main__":
    if "--torch-cpu" in sys.argv:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--torch-cpu", action="store_true", required=True)
        parser.add_argument("--out", required=True)
        parser.add_argument("--frozen-trainer", default=candidate.TRAINER_PATH)
        arguments = parser.parse_args()
        run_torch_cpu(arguments.out, arguments.frozen_trainer)
    else:
        unittest.main(verbosity=2)
