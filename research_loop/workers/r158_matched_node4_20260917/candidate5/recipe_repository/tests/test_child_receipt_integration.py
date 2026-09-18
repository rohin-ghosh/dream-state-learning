"""CPU integration fixtures, never training evidence or authenticated model bytes.

The trainer helpers and lifecycle verifier are real. main() probes replace all
ML imports with deliberately non-learning, in-memory tensor/model doubles.
Regression coverage includes CPU preflight and both supported record wrappers.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

from organism_v6 import life_lineage as lineage
from organism_v6 import lineage_guard as guard
from organism_v6 import train_adapter as trainer
from test_nursery_selection_receipt import synthetic_selection


def encode(value):
    return json.dumps(value, sort_keys=True).encode() + b"\n"


def sha(content):
    return hashlib.sha256(content).hexdigest()


class FixtureTensor:
    """Only the list operations used by this trainer; no numerical backend."""

    device = "cpu"

    def __init__(self, values):
        self.values = deepcopy(values)

    def tolist(self):
        return deepcopy(self.values)

    def clone(self):
        return FixtureTensor(self.values)

    def cpu(self):
        return self

    def to(self, device):
        if device != "cuda":
            raise AssertionError(f"unexpected trainer device: {device}")
        return self.clone()

    def __iter__(self):
        return (FixtureTensor(row) for row in self.values)

    def __getitem__(self, index):
        if isinstance(index, tuple):
            rows, columns = index
            return FixtureTensor([row[columns] for row in self.values[rows]])
        return FixtureTensor(self.values[index])

    def __setitem__(self, mask, value):
        for row, selected in zip(self.values, mask.values):
            for column, enabled in enumerate(selected):
                if enabled:
                    row[column] = value

    def __eq__(self, value):
        return FixtureTensor([[item == value for item in row] for row in self.values])

    def __ne__(self, value):
        return FixtureTensor([[item != value for item in row] for row in self.values])

    def __invert__(self):
        return FixtureTensor([[not item for item in row] for row in self.values])

    def sum(self):
        return sum(sum(row) for row in self.values)


class FixtureBatch(dict):
    def __getattr__(self, name):
        return self[name]

    def to(self, device):
        if device != "cuda":
            raise AssertionError(f"unexpected trainer device: {device}")
        return self


class ChildReceiptIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="child_receipt_cpu_", dir="/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.life = self.root / "life"
        self.life.mkdir()
        model = self.root / "model"
        model.mkdir()
        model_bytes = {
            "config.json": encode({"model_type": "qwen2", "architectures": ["Qwen2ForCausalLM"]}),
            "tokenizer.json": encode({"fixture_only": True}),
            "tokenizer_config.json": encode({"tokenizer_class": "Qwen2TokenizerFast"}),
            "model.safetensors": b"CPU fixture, NOT authenticated model weights",
        }
        for name, content in model_bytes.items():
            (model / name).write_bytes(content)
        self.birth = lineage.prepare_birth(
            self.life, model_dir=model, expected_model_id=guard.BASE_MODEL,
            expected_model_files={name: sha(content) for name, content in model_bytes.items()},
            loaded_adapter_path=None, exposure_status="UNEXPOSED", other_influences=[])
        self.previous_sha = self.birth.ancestry.manifest.sha256
        self.adapter = self.root / "adapter"
        self.receipt_path = self.root / "trainer.json"
        self.events = []
        self.consumed_labels = []
        self.consumed_input_ids = []
        self.epochs = 2
        self.prepare_corpus()

    def prepare_corpus(self, record_count=2, wrapper="Program"):
        if wrapper == "Situation":
            from organism_v6 import preschool_reasoning as reasoning

        lines, items, admissions = [], [], []
        for number in range(record_count):
            action = dict(kind="act", execution_id=f"fixture-{number}",
                          episode_id=f"nursery-{number}", tick=number, action="turn-left",
                          outcome="distance 2 -> 1", status="success")
            record = dict(action, kind="note_after",
                          text=f"I turned left at step {number} and distance decreased from 2 to 1.")
            if wrapper == "Situation":
                episode = f"rg/countdown/{1000001 + number}"
                occurrence = dict(episode_id=episode, occurrence_index=number + 1,
                                  occurrence_id=f"{episode}#occ{number + 1}")
                lines.append(encode(dict(occurrence, kind="episode_occurrence", slot_kind="note_after")))
                action = dict(occurrence, kind="act", execution_id=f"{occurrence['occurrence_id']}#t1a1",
                              tick=1, action=f"north{number}", score=0.5,
                              outcome="attempt 1: verifier score 0.50 (not accepted; partial credit)")
                record = dict(action, kind="note_after", speaker="child",
                              policy_version=reasoning.POLICY_VERSION,
                              text=f'  I submitted "north{number}"; the score was 0.50.  ',
                              **reasoning._measurement(reasoning.facts_from_act(action)))
            source_line = len(lines)
            lines.extend([encode(action), encode(record)])
            admissions.append(dict(source_line=source_line, record_line=source_line + 1,
                                   source_sha256=sha(lines[-2]), record_sha256=sha(lines[-1])))
            items.append(reasoning.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"])
                         if wrapper == "Situation" else
                         f"{wrapper} {record['episode_id']}.\nMy measured action record: {record['text']}")
        self.corpus = dict(recipe=lineage.RECIPE, corpus=items, principles=[],
                           n_new=len(items), n_dropped_legacy=0)
        self.corpus_path = self.root / "corpus.json"
        self.corpus_path.write_bytes(encode(self.corpus))
        self.ledger_path = self.root / "ledger.jsonl"
        self.ledger_path.write_bytes(b"".join(lines))
        self.gate = dict(schema_version=1, recipe=lineage.RECIPE, decision="ADMIT",
                         exposure_status="UNEXPOSED", previous_manifest_sha256=self.previous_sha,
                         ledger_sha256=sha(self.ledger_path.read_bytes()),
                         corpus_sha256=sha(self.corpus_path.read_bytes()), admissions=admissions)
        self.gate_path = self.root / "gate.json"
        self.save_gate()

    def save_gate(self):
        self.gate_path.write_bytes(encode(self.gate))
        self.gate_sha = sha(self.gate_path.read_bytes())

    def bound_gate(self):
        return trainer.load_gate_binding(self.gate_path, self.gate_sha, self.previous_sha,
                                         self.corpus_path.read_bytes())

    def token_row(self, text):
        prefix = trainer.child_record_prefix_length(text)
        return ([(0, 0), (0, prefix - 1), (prefix - 1, prefix + 1),
                 (prefix + 1, prefix + 2), (prefix + 2, len(text)), (0, 0)],
                [1, 1, 1, 1, 1, 0], [10, 11, 12, 13, 14, 0])

    def actual_counts(self):
        counts = []
        for text in self.corpus["corpus"]:
            offsets, attention, tokens = self.token_row(text)
            prefix = trainer.child_record_prefix_length(text)
            mask = trainer.child_target_mask(offsets, prefix, attention)
            labels = [token if selected else -100 for token, selected in zip(tokens, mask)]
            counts.append(trainer.child_label_counts(offsets, prefix, attention, labels))
        return counts

    def save_adapter(self, output):
        output = Path(output)
        output.mkdir()
        (output / "adapter_model.safetensors").write_bytes(b"CPU fixture, NOT trained adapter weights")
        (output / "adapter_config.json").write_bytes(encode(dict(
            peft_type="LORA", base_model_name_or_path=self.birth.model_dir)))
        self.events.append("save_adapter")

    def make_receipt(self):
        gate = self.bound_gate()
        counts = self.actual_counts()
        self.save_adapter(self.adapter)
        supervised = sum(row["supervised_child_tokens"] for row in counts) * self.epochs
        total = sum(sum(self.token_row(text)[1]) for text in self.corpus["corpus"]) * self.epochs
        metadata = dict(recipe="v1_frozen_child_target", source_recipe=lineage.RECIPE,
                        loss_target="child_body_only", source_corpus_sha256=gate["corpus_sha256"],
                        n_texts=len(counts), epochs=self.epochs, steps=self.epochs,
                        tokens=total, supervised_tokens=supervised,
                        masked_nonpadding_tokens=total - supervised)
        (self.adapter / "train_meta.json").write_bytes(encode(metadata))
        receipt = trainer.write_training_receipt(self.receipt_path, self.adapter, gate,
                                                  self.gate_sha, counts)
        return receipt

    def accept_fixture(self):
        (self.adapter / "DONE").write_bytes(b"synthetic runner acceptance, NOT training evidence\n")
        self.selected = synthetic_selection(self.adapter, self.birth.model_dir, self.previous_sha)

    def verify(self):
        return lineage.record_sleep(
            self.life, "sleep_0001", previous_manifest="birth/manifest.json",
            previous_sha256=self.previous_sha, ledger_path=self.ledger_path,
            corpus_path=self.corpus_path, gate_receipt_path=self.gate_path,
            expected_gate_sha256=self.gate_sha, trainer_receipt_path=self.receipt_path,
            expected_trainer_sha256=sha(self.receipt_path.read_bytes()), adapter_dir=self.adapter,
            exposure_status="UNEXPOSED", other_influences=[],
            selection_path=getattr(self, "selected", {}).get("selection_path"),
            expected_selection_sha256=getattr(self, "selected", {}).get("selection_sha256"))

    def reject(self, pattern):
        with self.assertRaisesRegex(lineage.LifeLineageError, pattern):
            self.verify()
        self.assertFalse((self.life / "lineage/sleep_0001").exists())

    def mutate_receipt(self, change):
        value = json.loads(self.receipt_path.read_bytes())
        change(value)
        self.receipt_path.write_bytes(encode(value))

    def arguments(self):
        return ["train_adapter", "--corpus", str(self.corpus_path), "--out", str(self.adapter),
                "--epochs", str(self.epochs), "--gate-receipt", str(self.gate_path),
                "--expected-gate-sha256", self.gate_sha,
                "--previous-manifest-sha256", self.previous_sha,
                "--trainer-receipt", str(self.receipt_path)]

    def run_simulated_main(self, *, row_transform=None, receipt_error=None, finite=True,
                           bound=True, seed=None):
        child_only = self.corpus.get("recipe") == lineage.RECIPE

        def tokenize(texts, **options):
            self.assertEqual(options, dict(return_tensors="pt", padding=True,
                                           truncation=True, max_length=512,
                                           **({"return_offsets_mapping": True} if child_only else {})))
            self.events.append("tokenize")
            rows = ([self.token_row(text) for text in texts] if child_only else
                    [([(0, 0), (0, len(text)), (0, 0)], [1, 1, 0], [20, 21, 0]) for text in texts])
            if row_transform is not None:
                rows = [row_transform(*row) for row in rows]
            batch = FixtureBatch(attention_mask=FixtureTensor([row[1] for row in rows]),
                                 input_ids=FixtureTensor([row[2] for row in rows]))
            if child_only:
                batch["offset_mapping"] = FixtureTensor([row[0] for row in rows])
            return batch

        def load_model(*arguments, **options):
            self.assertEqual(options["device_map"], "cuda")
            self.events.append("cuda_loader_requested_stub_only")
            return model

        loss = mock.MagicMock()
        loss.__float__.return_value = 0.25
        loss.backward.side_effect = lambda: self.events.append("backward_stub_only")

        def forward(**batch):
            self.events.append("forward_stub_only")
            self.consumed_labels.extend(batch["labels"].tolist())
            self.consumed_input_ids.extend(batch["input_ids"].tolist())
            return SimpleNamespace(loss=loss)

        model = mock.Mock(side_effect=forward)
        model.parameters.return_value = []
        model.save_pretrained.side_effect = self.save_adapter
        tokenizer = mock.Mock(side_effect=tokenize)
        tokenizer.pad_token = "<pad>"
        torch = ModuleType("torch")
        torch.bfloat16 = "fixture-bfloat16"
        torch.manual_seed = mock.Mock()
        torch.are_deterministic_algorithms_enabled = lambda: False
        torch.optim = SimpleNamespace(AdamW=mock.Mock(return_value=mock.Mock()))
        torch.tensor = lambda values, device: FixtureTensor(values)
        torch.isfinite = lambda value: finite
        transformers = ModuleType("transformers")
        transformers.AutoTokenizer = SimpleNamespace(from_pretrained=lambda *args: tokenizer)
        transformers.AutoModelForCausalLM = SimpleNamespace(from_pretrained=load_model)
        peft = ModuleType("peft")
        peft.LoraConfig = lambda **options: options
        peft.get_peft_model = lambda base, config: base
        real_writer = trainer.write_training_receipt

        def write_receipt(*arguments):
            self.events.append("receipt_writer")
            self.assertFalse((self.adapter / "DONE").exists())
            self.assertTrue((self.adapter / "train_meta.json").is_file())
            if receipt_error is not None:
                raise receipt_error
            return real_writer(*arguments)

        arguments = self.arguments() if bound else self.arguments()[:7]
        if seed is not None:
            arguments += ["--seed", str(seed)]
        with mock.patch.dict(sys.modules, {"torch": torch, "transformers": transformers, "peft": peft}), \
                mock.patch.object(sys, "argv", arguments), \
                mock.patch.object(trainer, "write_training_receipt", side_effect=write_receipt), \
                mock.patch("builtins.print"):
            trainer.main()

    def test_real_helpers_round_trip_into_lifecycle_snapshot(self):
        receipt = self.make_receipt()
        self.accept_fixture()
        checkpoint = self.verify()
        self.assertTrue(checkpoint.ancestry.eligible)
        self.assertEqual(receipt["rows"][0]["supervised_child_tokens"], 2)
        self.assertEqual(receipt["rows"][0]["masked_prefix_tokens"], 2)
        snapshot = Path(checkpoint.adapter_dir)
        self.assertEqual((snapshot / "train_meta.json").read_bytes(),
                         (self.adapter / "train_meta.json").read_bytes())
        self.assertEqual((snapshot.parent / "trainer_receipt.json").read_bytes(),
                         self.receipt_path.read_bytes())
        self.assertNotIn("DONE", receipt["adapter_files"])

    def test_actual_main_labels_and_metadata_round_trip_with_cpu_doubles(self):
        self.run_simulated_main()
        self.assertEqual(self.events[:2], ["tokenize", "cuda_loader_requested_stub_only"])
        self.assertEqual(self.events.count("tokenize"), 1)
        self.assertEqual(self.consumed_labels, [[-100, -100, -100, 13, 14, -100]] * 4)
        self.assertEqual(self.consumed_input_ids, [[10, 11, 12, 13, 14, 0]] * 4)
        metadata = json.loads((self.adapter / "train_meta.json").read_bytes())
        self.assertEqual((metadata["epochs"], metadata["steps"], metadata["tokens"],
                          metadata["supervised_tokens"], metadata["masked_nonpadding_tokens"]),
                         (2, 2, 20, 8, 12))
        self.assertLess(self.events.index("save_adapter"), self.events.index("receipt_writer"))
        self.assertTrue((self.adapter / "DONE").is_file())
        (self.adapter / "DONE").rename(self.adapter / "CANDIDATE")
        self.reject("final DONE")
        (self.adapter / "CANDIDATE").rename(self.adapter / "DONE")
        self.accept_fixture()
        self.assertTrue(self.verify().ancestry.eligible)

    def test_wrong_source_hash_with_rebound_gate_rejected_by_lifecycle(self):
        self.gate["admissions"][0]["source_sha256"] = "f" * 64
        self.save_gate()
        self.make_receipt()
        self.accept_fixture()
        self.reject("gate row SHA256 mismatch")

    def test_receipt_source_record_hashes_and_row_order_rejected(self):
        self.make_receipt()
        self.accept_fixture()
        original = self.receipt_path.read_bytes()
        for field in ("source_sha256", "record_sha256"):
            with self.subTest(field=field):
                self.receipt_path.write_bytes(original)
                self.mutate_receipt(lambda receipt: receipt["rows"][0].update({field: "f" * 64}))
                self.reject("row/source mismatch")
        self.receipt_path.write_bytes(original)
        self.mutate_receipt(lambda receipt: receipt["rows"].reverse())
        self.reject("row/source mismatch")

    def test_shift_padding_and_boundary_invalid_actual_labels_fail_before_receipt(self):
        text = self.corpus["corpus"][0]
        offsets, attention, tokens = self.token_row(text)
        prefix = trainer.child_record_prefix_length(text)
        invalid = {
            "prefix": [-100, 11, -100, 13, 14, -100],
            "crossing": [-100, -100, 12, 13, 14, -100],
            "padding": [-100, -100, -100, 13, 14, 0],
            "empty": [-100] * len(tokens),
        }
        for name, labels in invalid.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                trainer.child_label_counts(offsets, prefix, attention, labels)
        with self.assertRaisesRegex(ValueError, "causal-shift"):
            trainer.child_label_counts([(prefix, prefix + 1), (0, prefix), (0, 0)],
                                       prefix, [1, 1, 0], [13, -100, -100])
        self.assertFalse(self.receipt_path.exists())

    def test_receipt_count_corruption_rejected_even_with_reselected_receipt_pin(self):
        self.make_receipt()
        self.accept_fixture()
        original = self.receipt_path.read_bytes()
        for field, value in (("supervised_prefix_tokens", 1), ("supervised_padding_tokens", 1),
                             ("masked_prefix_tokens", 0), ("supervised_child_tokens", 3),
                             ("supervised_child_tokens", True), ("masked_prefix_tokens", 100),
                             ("supervised_padding_tokens", False)):
            with self.subTest(field=field, value=value):
                self.receipt_path.write_bytes(original)
                self.mutate_receipt(lambda receipt: receipt["rows"][0].update({field: value}))
                self.reject("mask|padding|totals")

    def test_native_metadata_corruption_rejected_with_and_without_rebinding(self):
        self.make_receipt()
        self.accept_fixture()
        path = self.adapter / "train_meta.json"
        original_metadata = json.loads(path.read_bytes())
        original_receipt = self.receipt_path.read_bytes()
        for field, value in (("loss_target", "all_tokens"), ("source_recipe", "other"),
                             ("source_corpus_sha256", "f" * 64), ("recipe", "v1_frozen"),
                             ("n_texts", 3), ("epochs", 0), ("epochs", 3), ("steps", False),
                             ("tokens", 21), ("supervised_tokens", 9),
                             ("masked_nonpadding_tokens", 1)):
            for rebind in (False, True):
                with self.subTest(field=field, value=value, rebind=rebind):
                    self.receipt_path.write_bytes(original_receipt)
                    content = encode(dict(original_metadata, **{field: value}))
                    path.write_bytes(content)
                    if rebind:
                        self.mutate_receipt(lambda receipt: receipt.update(train_metadata_sha256=sha(content)))
                    self.reject("binding|metadata|totals")

    def test_saved_adapter_byte_corruption_rejected(self):
        self.make_receipt()
        self.accept_fixture()
        path = self.adapter / "adapter_model.safetensors"
        path.write_bytes(path.read_bytes() + b"tampered")
        self.reject("adapter binding mismatch")

    def test_writer_rejects_counts_disagreeing_with_native_metadata_without_publication(self):
        self.make_receipt()
        original = self.receipt_path.read_bytes()
        bad_path = self.root / "bad_trainer.json"
        counts = self.actual_counts()
        counts[0]["supervised_child_tokens"] += 1
        with self.assertRaisesRegex(ValueError, "actual label counts"):
            trainer.write_training_receipt(bad_path, self.adapter, self.bound_gate(),
                                           self.gate_sha, counts)
        self.assertFalse(bad_path.exists())
        self.assertEqual(self.receipt_path.read_bytes(), original)

    def test_missing_candidate_and_rejected_markers_never_publish_lineage(self):
        self.make_receipt()
        self.reject("final DONE")
        for name in ("CANDIDATE", "REJECTED_CANARY", "REJECTED_PROBE"):
            with self.subTest(marker=name):
                marker = self.adapter / name
                marker.write_bytes(b"fixture marker\n")
                (self.adapter / "DONE").write_bytes(b"synthetic ambiguous acceptance\n")
                self.reject("final DONE")
                marker.unlink()
        self.accept_fixture()
        self.assertTrue(self.verify().ancestry.eligible)

    def test_gate_pin_error_precedes_all_ml_imports(self):
        self.gate_path.write_bytes(self.gate_path.read_bytes() + b" ")
        with mock.patch.dict(sys.modules, {"torch": None, "transformers": None, "peft": None}), \
                mock.patch.object(sys, "argv", self.arguments()), \
                self.assertRaisesRegex(ValueError, "gate receipt hash mismatch"):
            trainer.main()
        self.assertFalse(self.adapter.exists())

    def test_cli_binding_errors_precede_all_ml_imports(self):
        cases = [self.arguments()[:-2], self.arguments() + ["--epochs", "0"],
                 self.arguments() + ["--trainer-receipt", str(self.adapter / "receipt.json")],
                 self.arguments() + ["--trainer-receipt", str(self.adapter)]]
        for arguments in cases:
            with self.subTest(arguments=arguments), \
                    mock.patch.dict(sys.modules, {"torch": None, "transformers": None, "peft": None}), \
                    mock.patch.object(sys, "argv", arguments), \
                    mock.patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                trainer.main()
            self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.adapter.exists())

    def test_receipt_failure_preserves_saved_bytes_but_never_writes_done(self):
        with self.assertRaisesRegex(OSError, "fixture receipt failure"):
            self.run_simulated_main(receipt_error=OSError("fixture receipt failure"))
        self.assertTrue((self.adapter / "adapter_model.safetensors").is_file())
        self.assertTrue((self.adapter / "train_meta.json").is_file())
        self.assertFalse((self.adapter / "DONE").exists())
        self.assertFalse(self.receipt_path.exists())

    def test_nonfinite_stub_loss_never_emits_receipt_or_done(self):
        with self.assertRaisesRegex(RuntimeError, "nonfinite child-target loss"):
            self.run_simulated_main(finite=False)
        self.assertNotIn("backward_stub_only", self.events)
        self.assertFalse(self.adapter.exists())
        self.assertFalse(self.receipt_path.exists())

    def test_truncated_child_must_reject_before_cuda_loader_is_requested(self):
        def truncate(offsets, attention, tokens):
            return offsets[:3], attention[:3], tokens[:3]

        with self.assertRaisesRegex(ValueError, "no child target tokens"):
            self.run_simulated_main(row_transform=truncate)
        self.assertNotIn("forward_stub_only", self.events)
        self.assertFalse(self.receipt_path.exists())
        self.assertNotIn("cuda_loader_requested_stub_only", self.events)

    def test_missing_receipt_parent_must_reject_before_cuda_loader_is_requested(self):
        self.receipt_path = self.root / "missing_directory/trainer.json"
        with self.assertRaises(FileNotFoundError):
            self.run_simulated_main()
        self.assertFalse((self.adapter / "DONE").exists())
        self.assertNotIn("cuda_loader_requested_stub_only", self.events)
        self.assertFalse(self.adapter.exists())

    def test_both_exact_wrappers_mask_prefix_crossing_and_padding(self):
        for wrapper in ("Program", "Situation"):
            with self.subTest(wrapper=wrapper):
                text = f"{wrapper} nursery-0.\nMy measured action record: I turned left and distance fell."
                prefix = trainer.child_record_prefix_length(text)
                self.assertEqual(text[prefix:], "I turned left and distance fell.")
                offsets, attention, tokens = self.token_row(text)
                mask = trainer.child_target_mask(offsets, prefix, attention)
                self.assertEqual(mask, [False, False, False, True, True, False])
                labels = [token if selected else -100 for token, selected in zip(tokens, mask)]
                self.assertEqual(trainer.child_label_counts(offsets, prefix, attention, labels),
                                 dict(masked_prefix_tokens=2, supervised_prefix_tokens=0,
                                      supervised_child_tokens=2, supervised_padding_tokens=0))

    def test_other_wrappers_and_ambiguous_reasoning_boundaries_still_reject(self):
        for text in ("Episode e.\nMy measured action record: child",
                     "situation e.\nMy measured action record: child",
                     "Situations e.\nMy measured action record: child",
                     "Situatione.\nMy measured action record: child",
                     " Situation e.\nMy measured action record: child",
                     "Situation e.\nMy measured action record: ",
                     "Situation e.\nMy measured action record: A\nMy measured action record: B"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                trainer.child_record_prefix_length(text)

    def test_reasoning_wrapper_main_keeps_child_only_recipe_and_seed(self):
        self.prepare_corpus(wrapper="Situation")
        corpus_bytes = self.corpus_path.read_bytes()
        self.run_simulated_main(seed=23)
        self.assertEqual(self.corpus_path.read_bytes(), corpus_bytes)
        self.assertTrue(self.corpus["corpus"][0].endswith("  "))
        self.assertEqual(self.consumed_labels, [[-100, -100, -100, 13, 14, -100]] * 4)
        metadata = json.loads((self.adapter / "train_meta.json").read_bytes())
        self.assertEqual(metadata["recipe"], "v1_frozen_child_target_seeded")
        self.assertEqual(metadata["source_recipe"], "preschool_records_v1")
        self.assertEqual(metadata["loss_target"], "child_body_only")
        self.assertEqual(metadata["seed"], 23)
        self.assertEqual(metadata["supervised_tokens"], 8)
        receipt = json.loads(self.receipt_path.read_bytes())
        self.assertEqual(receipt["corpus_recipe"], "preschool_records_v1")
        self.assertEqual(receipt["supervision"], "child_only_v1")

    def test_reasoning_wrapper_receipt_round_trips_through_lifecycle(self):
        self.prepare_corpus(wrapper="Situation")
        self.run_simulated_main()
        self.accept_fixture()
        self.assertTrue(self.verify().ancestry.eligible)

    def test_all_batches_preflight_once_and_preserve_distinct_row_counts(self):
        self.prepare_corpus(record_count=6)
        prepared_labels, prepared_inputs = [], []

        def vary(offsets, attention, tokens):
            number = len(prepared_labels)
            tokens[3] += number * 10
            tokens[4] += number * 10
            if number % 2:
                offsets[4], attention[4], tokens[4] = (0, 0), 0, 0
            prepared_labels.append([-100, -100, -100, tokens[3],
                                    tokens[4] if attention[4] else -100, -100])
            prepared_inputs.append(list(tokens))
            return offsets, attention, tokens

        with mock.patch.object(trainer, "child_label_counts", wraps=trainer.child_label_counts) as count_labels:
            self.run_simulated_main(row_transform=vary)
        self.assertEqual(count_labels.call_count, 6 * (1 + self.epochs))
        self.assertEqual([call.args[3] for call in count_labels.call_args_list],
                         prepared_labels * (1 + self.epochs))
        self.assertEqual(self.events[:3], ["tokenize", "tokenize", "cuda_loader_requested_stub_only"])
        self.assertEqual(self.events.count("tokenize"), 2)
        self.assertEqual(self.consumed_labels, prepared_labels * self.epochs)
        self.assertEqual(self.consumed_input_ids, prepared_inputs * self.epochs)
        receipt = json.loads(self.receipt_path.read_bytes())
        self.assertEqual([row["supervised_child_tokens"] for row in receipt["rows"]], [2, 1] * 3)
        metadata = json.loads((self.adapter / "train_meta.json").read_bytes())
        self.assertEqual((metadata["steps"], metadata["tokens"], metadata["supervised_tokens"]),
                         (4, 54, 18))
        self.accept_fixture()
        self.assertTrue(self.verify().ancestry.eligible)

    def test_invalid_last_batch_prevents_loading_and_all_simulated_training(self):
        self.prepare_corpus(record_count=6)
        prepared_rows = []

        def invalidate_last(offsets, attention, tokens):
            prepared_rows.append(tokens)
            if len(prepared_rows) == 6:
                offsets[3:] = [(0, 0)] * 3
                attention[3:] = [0] * 3
            return offsets, attention, tokens

        with self.assertRaisesRegex(ValueError, "no child target tokens"):
            self.run_simulated_main(row_transform=invalidate_last)
        self.assertEqual(self.events, ["tokenize", "tokenize"])
        self.assertFalse(self.adapter.exists())
        self.assertFalse(self.receipt_path.exists())

    def test_missing_shifted_prefix_evidence_rejects_before_cuda_loader(self):
        def no_shifted_prefix(offsets, attention, tokens):
            return [offsets[0], *offsets[3:]], [attention[0], *attention[3:]], [tokens[0], *tokens[3:]]

        with self.assertRaisesRegex(ValueError, "causal-shift child/prefix evidence"):
            self.run_simulated_main(row_transform=no_shifted_prefix)
        self.assertEqual(self.events, ["tokenize"])
        self.assertFalse(self.adapter.exists())

    def test_first_position_only_target_rejects_before_cuda_loader(self):
        def only_first_target(offsets, attention, tokens):
            return [offsets[3], offsets[1], (0, 0)], [1, 1, 0], [13, 11, 0]

        with self.assertRaisesRegex(ValueError, "causal-shift child/prefix evidence"):
            self.run_simulated_main(row_transform=only_first_target)
        self.assertEqual(self.events, ["tokenize"])
        self.assertFalse(self.adapter.exists())

    def test_actual_transferred_mask_must_agree_with_cpu_preflight(self):
        original_transfer = FixtureTensor.to

        def corrupt_transfer(tensor, device):
            transferred = original_transfer(tensor, device)
            if transferred.values[0][:3] == [-100, -100, -100]:
                transferred.values[0][3] = -100
            return transferred

        with mock.patch.object(FixtureTensor, "to", corrupt_transfer), \
                self.assertRaisesRegex(ValueError, "actual label evidence disagrees with CPU preflight"):
            self.run_simulated_main()
        self.assertNotIn("forward_stub_only", self.events)
        self.assertFalse(self.adapter.exists())
        self.assertFalse(self.receipt_path.exists())

    def test_unbound_legacy_keeps_in_loop_tokenization_and_bare_text_labels(self):
        self.corpus = dict(corpus=["legacy bare text", "another legacy item"])
        self.corpus_path.write_bytes(encode(self.corpus))
        self.run_simulated_main(bound=False)
        self.assertEqual(self.events[0], "cuda_loader_requested_stub_only")
        self.assertEqual(self.events.count("tokenize"), self.epochs)
        self.assertEqual(self.consumed_labels, [[20, 21, -100]] * 4)
        metadata = json.loads((self.adapter / "train_meta.json").read_bytes())
        self.assertEqual(metadata["recipe"], "v1_frozen")
        self.assertEqual((metadata["epochs"], metadata["steps"], metadata["tokens"]), (2, 2, 8))
        self.assertNotIn("source_recipe", metadata)
        self.assertNotIn("loss_target", metadata)
        self.assertNotIn("supervised_tokens", metadata)
        self.assertFalse(self.receipt_path.exists())
        self.assertTrue((self.adapter / "DONE").is_file())

    def test_output_parent_errors_reject_before_any_ml_import(self):
        blocked = self.root / "file_instead_of_directory"
        blocked.write_bytes(b"preserve this existing file")
        for argument in ("--out", "--trainer-receipt"):
            for parent, expected_error in ((blocked, NotADirectoryError),
                                           (self.root / "missing_parent", FileNotFoundError)):
                with self.subTest(argument=argument, parent=parent), \
                        mock.patch.dict(sys.modules, {"torch": None, "transformers": None, "peft": None}), \
                        mock.patch.object(sys, "argv", self.arguments() + [argument, str(parent / "output")]), \
                        self.assertRaises(expected_error):
                    trainer.main()
        self.assertEqual(blocked.read_bytes(), b"preserve this existing file")
        self.assertFalse(self.adapter.exists())
        self.assertFalse(self.receipt_path.exists())

    def test_unwritable_parent_rejects_before_any_ml_import(self):
        with mock.patch.dict(sys.modules, {"torch": None, "transformers": None, "peft": None}), \
                mock.patch.object(sys, "argv", self.arguments()), \
                mock.patch.object(trainer.os, "access", return_value=False), \
                self.assertRaisesRegex(PermissionError, "not writable/searchable"):
            trainer.main()
        self.assertFalse(self.adapter.exists())

    def test_existing_output_and_dangling_symlink_are_never_overwritten(self):
        existing_file = self.root / "existing_file"
        existing_file.write_bytes(b"preserve existing output")
        existing_directory = self.root / "existing_directory"
        existing_directory.mkdir()
        dangling = self.root / "dangling_output"
        dangling.symlink_to(self.root / "does_not_exist")
        for argument in ("--out", "--trainer-receipt"):
            for path in (existing_file, existing_directory, dangling):
                with self.subTest(argument=argument, path=path), \
                        mock.patch.dict(sys.modules, {"torch": None, "transformers": None, "peft": None}), \
                        mock.patch.object(sys, "argv", self.arguments() + [argument, str(path)]), \
                        mock.patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                    trainer.main()
                self.assertEqual(error.exception.code, 2)
        self.assertEqual(existing_file.read_bytes(), b"preserve existing output")
        self.assertTrue(existing_directory.is_dir())
        self.assertTrue(dangling.is_symlink())


if __name__ == "__main__":
    unittest.main()
