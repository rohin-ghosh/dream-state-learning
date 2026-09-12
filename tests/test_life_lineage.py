"""Tiny synthetic byte fixtures only; no real model authentication or GPU use."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from organism_v6 import life_lineage as lineage
from organism_v6 import lineage_guard as guard
from organism_v6 import train_adapter
from organism_v6 import preschool_reasoning as reasoning
from test_nursery_selection_receipt import synthetic_selection
from organism_v6.nursery_selection_receipt import SelectionReceiptError


def encode(value):
    return json.dumps(value, sort_keys=True).encode() + b"\n"


def sha(content):
    return hashlib.sha256(content).hexdigest()


def event(number=1, text=None):
    action = {"kind": "act", "execution_id": f"execution-{number}",
              "episode_id": f"nursery-{number}", "tick": number, "action": "turn-left",
              "outcome": "distance 2 -> 1", "status": "success"}
    record = {**action, "kind": "note_after", "text": text or
              f"I turned left at step {number} and observed distance decrease from 2 to 1."}
    return [action, record]


def reasoning_event(number=1, score=0.5, text=None):
    episode = f"rg/countdown/{1000000 + number}"
    occurrence = f"{episode}#occ{number}"
    reservation = {"kind": "episode_occurrence", "episode_id": episode,
                   "occurrence_id": occurrence, "occurrence_index": number,
                   "slot_kind": "note_after"}
    verdict = "accepted" if score == 1 else "not accepted; partial credit" if score > 0 else "not accepted"
    action = {"kind": "act", "episode_id": episode, "tick": 1, "action": "4 3 2 1",
              "execution_id": f"{occurrence}#t1a1", "occurrence_id": occurrence,
              "occurrence_index": number, "score": score, "prediction": "accepted",
              "outcome": f"attempt 1: verifier score {score:.2f} ({verdict})",
              "surprise": 0.5, "time_cost": 1.0, "generation": {"fixture": True}}
    record = {key: action[key] for key in ("episode_id", "tick", "action", "execution_id",
                                         "occurrence_id", "occurrence_index", "score", "outcome")}
    record.update(reasoning._measurement(reasoning.facts_from_act(action)))
    record.update(kind="note_after", speaker="child", label="NOTE_AFTER",
                  policy_version=reasoning.POLICY_VERSION,
                  text=text if text is not None else f"I submitted 4 3 2 1 and observed score {score:.2f}.")
    return [reservation, action, record]


class LifeLineageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="life_lineage_", dir="/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.life = self.root / "life"
        self.life.mkdir()
        self.model = self.root / "model"
        self.model.mkdir()
        self.base_bytes = {
            "config.json": encode({"model_type": "qwen2", "architectures": ["Qwen2ForCausalLM"]}),
            "model.safetensors": b"tiny fixture weights, NOT authenticated Qwen weights",
            "tokenizer.json": encode({"fixture": "tokenizer"}),
            "tokenizer_config.json": encode({"tokenizer_class": "Qwen2TokenizerFast"}),
        }
        for name, content in self.base_bytes.items():
            (self.model / name).write_bytes(content)
        self.pins = {name: sha(content) for name, content in self.base_bytes.items()}
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.adapter = self.runtime / "adapter"
        self.adapter.mkdir()
        self.write_adapter()

    def write_adapter(self, **overrides):
        (self.adapter / "adapter_model.safetensors").write_bytes(b"tiny fixture LoRA bytes")
        (self.adapter / "DONE").write_bytes(b"ok\n")
        config = {"peft_type": "LORA", "base_model_name_or_path": guard.BASE_MODEL, **overrides}
        (self.adapter / "adapter_config.json").write_bytes(encode(config))

    def birth_args(self, **overrides):
        return {"model_dir": self.model, "expected_model_id": guard.BASE_MODEL,
                "expected_model_files": dict(self.pins),
                "loaded_adapter_path": None, "exposure_status": "UNEXPOSED",
                "other_influences": [], **overrides}

    def birth(self, **overrides):
        return lineage.prepare_birth(self.life, **self.birth_args(**overrides))

    def verify(self, birth, **overrides):
        return lineage.verify_birth(self.life, expected_manifest_sha256=birth.ancestry.manifest.sha256,
                                     **self.birth_args(**overrides))

    def inputs(self, previous, rows=None):
        rows = event() if rows is None else rows
        lines = [encode(row) for row in rows]
        admitted = [index for index, row in enumerate(rows) if row.get("kind") == "note_after"]
        items, admissions = [], []
        for index in admitted:
            row = rows[index]
            source = next(position for position, other in enumerate(rows)
                          if other.get("kind") == "act"
                          and other.get("execution_id") == row["execution_id"])
            if row["episode_id"].startswith("rg/"):
                items.append(reasoning.RECORD_ITEM.format(eid=row["episode_id"], text=row["text"]))
            else:
                items.append(f"Program {row['episode_id']}.\nMy measured action record: {row['text'].strip()}")
            admissions.append({"record_line": index, "record_sha256": sha(lines[index]),
                               "source_line": source, "source_sha256": sha(lines[source])})
        corpus = {"recipe": lineage.RECIPE, "corpus": items, "principles": [],
                  "n_new": len(items), "n_dropped_legacy": 0}
        ledger = b"".join(lines)
        gate = {"schema_version": 1, "recipe": lineage.RECIPE, "decision": "ADMIT",
                "exposure_status": "UNEXPOSED", "ledger_sha256": sha(ledger),
                "corpus_sha256": sha(encode(corpus)), "admissions": admissions,
                "previous_manifest_sha256": previous.ancestry.manifest.sha256}
        ledger_path, corpus_path, gate_path = [self.runtime / name for name in
                                              ("ledger.jsonl", "corpus.json", "gate.json")]
        ledger_path.write_bytes(ledger)
        corpus_path.write_bytes(encode(corpus))
        gate_path.write_bytes(encode(gate))
        metadata = {"recipe": "v1_frozen_child_target", "source_recipe": lineage.RECIPE,
                    "loss_target": "child_body_only", "source_corpus_sha256": sha(encode(corpus)),
                    "n_texts": len(admissions), "epochs": 1, "steps": 1,
                    "tokens": 30 * len(admissions), "supervised_tokens": 18 * len(admissions),
                    "masked_nonpadding_tokens": 12 * len(admissions)}
        (self.adapter / "train_meta.json").write_bytes(encode(metadata))
        trainer = {
            "schema_version": 1, "corpus_recipe": lineage.RECIPE,
            "supervision": "child_only_v1", "status": "COMPLETED",
            "previous_manifest_sha256": previous.ancestry.manifest.sha256,
            "corpus_sha256": sha(encode(corpus)), "gate_receipt_sha256": sha(encode(gate)),
            "train_metadata_sha256": sha(encode(metadata)),
            "adapter_files": {name: sha((self.adapter / name).read_bytes())
                              for name in ("adapter_config.json", "adapter_model.safetensors")
                              if (self.adapter / name).exists()},
            "rows": [{"record_sha256": admission["record_sha256"],
                      "source_sha256": admission["source_sha256"],
                      "masked_prefix_tokens": 12, "supervised_prefix_tokens": 0,
                      "supervised_child_tokens": 18, "supervised_padding_tokens": 0}
                     for admission in admissions],
        }
        trainer_path = self.runtime / "trainer.json"
        trainer_path.write_bytes(encode(trainer))
        try:
            selected = synthetic_selection(self.adapter, previous.model_dir, previous.ancestry.manifest.sha256)
        except (SelectionReceiptError, lineage.LifeLineageError, OSError):
            selected = {"selection_path": None, "selection_sha256": None}
        return {"previous_manifest": previous.ancestry.manifest.path,
                "selection_path": selected["selection_path"], "expected_selection_sha256": selected["selection_sha256"],
                "previous_sha256": previous.ancestry.manifest.sha256,
                "ledger_path": ledger_path, "corpus_path": corpus_path,
                "gate_receipt_path": gate_path, "expected_gate_sha256": sha(encode(gate)),
                "trainer_receipt_path": trainer_path, "expected_trainer_sha256": sha(encode(trainer)),
                "adapter_dir": self.adapter, "exposure_status": "UNEXPOSED", "other_influences": []}

    def update_trainer(self, arguments, change):
        path = arguments["trainer_receipt_path"]
        value = json.loads(path.read_bytes())
        change(value)
        content = encode(value)
        path.write_bytes(content)
        arguments["expected_trainer_sha256"] = sha(content)

    def update_train_metadata(self, arguments, change):
        path = self.adapter / "train_meta.json"
        value = json.loads(path.read_bytes())
        change(value)
        content = encode(value)
        path.write_bytes(content)
        self.update_trainer(arguments, lambda receipt: receipt.update(train_metadata_sha256=sha(content)))

    def update_gate(self, arguments, change):
        path = arguments["gate_receipt_path"]
        value = json.loads(path.read_bytes())
        change(value)
        content = encode(value)
        path.write_bytes(content)
        arguments["expected_gate_sha256"] = sha(content)

    def update_corpus(self, arguments, change):
        path = arguments["corpus_path"]
        value = json.loads(path.read_bytes())
        change(value)
        content = encode(value)
        path.write_bytes(content)
        self.update_gate(arguments, lambda gate: gate.update(corpus_sha256=sha(content)))

    def reject_sleep(self, arguments, checkpoint="sleep_0001", pattern="."):
        with self.assertRaisesRegex(lineage.LifeLineageError, pattern):
            lineage.record_sleep(self.life, checkpoint, **arguments)

    def test_prepare_and_verify_actual_pinned_birth(self):
        birth = self.birth()
        self.assertTrue(birth.ancestry.eligible)
        self.assertIsNone(birth.adapter_dir)
        self.assertIsNone(birth.ledger_snapshot)
        self.assertEqual(len(birth.ancestry.files), len(self.pins))
        self.assertEqual(self.verify(birth), birth)
        self.assertEqual(self.verify(birth, model_dir=birth.model_dir), birth)
        for binding in birth.ancestry.files:
            path = Path(birth.ancestry.root) / binding.path
            self.assertFalse(path.is_symlink())
            self.assertEqual(path.stat().st_mode & 0o222, 0)
            self.assertEqual(sha(path.read_bytes()), self.pins[path.name])

    def test_external_pins_required_for_config_weights_and_tokenizer(self):
        for name in self.pins:
            with self.subTest(name=name):
                pins = dict(self.pins)
                pins[name] = "0" * 64
                with self.assertRaisesRegex(lineage.LifeLineageError, "pin mismatch"):
                    self.birth(expected_model_files=pins)
                self.assertFalse((self.life / "lineage").exists())
        for pins in (None, {}, {"config.json": self.pins["config.json"]}):
            with self.assertRaises(lineage.LifeLineageError):
                self.birth(expected_model_files=pins)

    def test_explicit_external_model_identity_is_mandatory(self):
        for identity in (None, "", "UNKNOWN", "Qwen2.5-7B-Instruct", "other/model"):
            with self.subTest(identity=identity), self.assertRaisesRegex(lineage.LifeLineageError, "model ID"):
                self.birth(expected_model_id=identity)
        args = self.birth_args()
        del args["expected_model_id"]
        with self.assertRaises(lineage.LifeLineageError):
            lineage.prepare_birth(self.life, **args)
        birth = self.birth()
        with self.assertRaisesRegex(lineage.LifeLineageError, "model ID"):
            self.verify(birth, expected_model_id="other/model")

    def test_invalid_actual_base_and_missing_runtime_files(self):
        path = self.model / "config.json"
        content = encode({"model_type": "other"})
        path.write_bytes(content)
        pins = {**self.pins, "config.json": sha(content)}
        with self.assertRaisesRegex(lineage.LifeLineageError, "model config"):
            self.birth(expected_model_files=pins)
        path.write_bytes(self.base_bytes[path.name])
        (self.model / "tokenizer.json").unlink()
        with self.assertRaises(lineage.LifeLineageError):
            self.birth()

    def test_unknown_model_input_is_not_ignored(self):
        (self.model / "adapter_config.json").write_bytes(b"{}")
        with self.assertRaises(lineage.LifeLineageError):
            self.birth()
        pins = {**self.pins, "adapter_config.json": sha(b"{}")}
        with self.assertRaisesRegex(lineage.LifeLineageError, "unsupported model file"):
            self.birth(expected_model_files=pins)

    def test_complete_pinned_shard_index(self):
        (self.model / "model.safetensors").unlink()
        del self.pins["model.safetensors"]
        for number in (1, 2):
            name = f"model-{number:05d}-of-00002.safetensors"
            content = f"fixture shard {number}".encode()
            (self.model / name).write_bytes(content)
            self.pins[name] = sha(content)
        index_name = "model.safetensors.index.json"
        content = encode({"weight_map": {"layer1": "model-00001-of-00002.safetensors",
                                         "layer2": "model-00002-of-00002.safetensors"}})
        (self.model / index_name).write_bytes(content)
        self.pins[index_name] = sha(content)
        self.assertTrue(self.birth().ancestry.eligible)

    def test_hf_leaf_symlinks_are_resolved_pinned_and_copied(self):
        blobs = self.root / "blobs"
        blobs.mkdir()
        for name, content in self.base_bytes.items():
            actual = blobs / sha(content)
            actual.write_bytes(content)
            (self.model / name).unlink()
            (self.model / name).symlink_to(actual)
        birth = self.birth()
        snapshot = Path(birth.model_dir) / "model.safetensors"
        original = snapshot.read_bytes()
        (self.model / "model.safetensors").resolve().write_bytes(b"later corrupted blob")
        self.assertEqual(snapshot.read_bytes(), original)
        self.assertFalse(snapshot.is_symlink())
        with self.assertRaisesRegex(lineage.LifeLineageError, "pin mismatch"):
            self.verify(birth)
        self.assertTrue(guard.validate_manifest(birth.ancestry.manifest.path,
                                                root=birth.ancestry.root).eligible)

    def test_directory_symlinks_are_not_hf_leaf_exception(self):
        link = self.root / "model-link"
        link.symlink_to(self.model, target_is_directory=True)
        with self.assertRaises(lineage.LifeLineageError):
            self.birth(model_dir=link)
        life_link = self.root / "life-link"
        life_link.symlink_to(self.life, target_is_directory=True)
        with self.assertRaises(lineage.LifeLineageError):
            lineage.prepare_birth(life_link, **self.birth_args())

    def test_loaded_adapter_unknown_influences_and_status_fail_closed(self):
        for adapter in ("", False, self.adapter):
            with self.subTest(adapter=adapter), self.assertRaises(lineage.LifeLineageError):
                self.birth(loaded_adapter_path=adapter)
        for influences in (None, {}, ["unknown lesson"]):
            with self.subTest(influences=influences), self.assertRaises(lineage.LifeLineageError):
                self.birth(other_influences=influences)
        for status in (None, "UNKNOWN", "QUARANTINE_TASK_EXPOSED"):
            with self.subTest(status=status), self.assertRaises(lineage.LifeLineageError):
                self.birth(exposure_status=status)

    def test_birth_refuses_preexisting_sleep_or_unknown_files(self):
        for name in ("sleep_0001", "unknown.txt"):
            path = self.life / name
            path.write_bytes(b"unknown adapter/influence")
            with self.assertRaisesRegex(lineage.LifeLineageError, "not empty"):
                self.birth()
            path.unlink()
        (self.life / "sleep_0001").mkdir()
        with self.assertRaises(lineage.LifeLineageError):
            self.birth()

    def test_birth_verification_rejects_runtime_changes_and_unknown_influences(self):
        birth = self.birth()
        with self.assertRaises(lineage.LifeLineageError):
            self.verify(birth, loaded_adapter_path=self.adapter)
        (self.life / "new-influence.json").write_bytes(b"{}")
        with self.assertRaisesRegex(lineage.LifeLineageError, "unknown influences"):
            self.verify(birth)

    def test_birth_is_exclusive_and_existing_snapshots_unchanged(self):
        birth = self.birth()
        manifest = Path(birth.ancestry.root) / birth.ancestry.manifest.path
        content = manifest.read_bytes()
        with self.assertRaises(lineage.LifeLineageError):
            self.birth()
        self.assertEqual(manifest.read_bytes(), content)

    def test_sleep_links_gate_corpus_source_rows_and_adapter_bytes(self):
        birth = self.birth()
        args = self.inputs(birth)
        sleep = lineage.record_sleep(self.life, "sleep_0001", **args)
        self.assertTrue(sleep.ancestry.eligible)
        self.assertEqual(len(sleep.ancestry.manifests), 2)
        root = Path(sleep.ancestry.root)
        manifest = json.loads((root / sleep.ancestry.manifest.path).read_bytes())
        self.assertEqual(manifest["parents"], [{"path": birth.ancestry.manifest.path,
                                               "sha256": birth.ancestry.manifest.sha256}])
        self.assertEqual(len(manifest["sources"]), 4)
        self.assertEqual(len(manifest["artifacts"]), 8)
        self.assertEqual(len(manifest["trained_corpus"]), 1)
        self.assertEqual(Path(sleep.ledger_snapshot).read_bytes(), args["ledger_path"].read_bytes())
        self.assertEqual((Path(sleep.adapter_dir).parent / "corpus.json").read_bytes(),
                         args["corpus_path"].read_bytes())
        self.assertEqual((Path(sleep.adapter_dir).parent / "trainer_receipt.json").read_bytes(),
                         args["trainer_receipt_path"].read_bytes())
        self.assertEqual((Path(sleep.adapter_dir) / "train_meta.json").read_bytes(),
                         (self.adapter / "train_meta.json").read_bytes())
        self.assertEqual((Path(sleep.adapter_dir) / "DONE").read_bytes(), b"ok\n")
        for name in ("adapter_config.json", "adapter_model.safetensors"):
            self.assertEqual((Path(sleep.adapter_dir) / name).read_bytes(), (self.adapter / name).read_bytes())
        self.assertIn("not factual entailment", sleep.ancestry.scope)

    def test_actual_trainer_receipt_writer_interoperates_with_lifecycle(self):
        self.trainer_writer_fixture(event() + event(2))

    def test_actual_trainer_writer_binds_situation_without_renaming(self):
        self.trainer_writer_fixture(reasoning_event() + reasoning_event(2, score=1.0))

    def trainer_writer_fixture(self, rows):
        """Exercise real helper functions on synthetic character-token fixtures, not training."""
        args = self.inputs(self.birth(), rows)
        corpus_bytes = args["corpus_path"].read_bytes()
        corpus = json.loads(corpus_bytes)["corpus"]
        gate = train_adapter.load_gate_binding(
            args["gate_receipt_path"], args["expected_gate_sha256"],
            args["previous_sha256"], corpus_bytes,
        )
        row_counts = []
        nonpadding_tokens = 0
        for text in corpus:
            boundary = train_adapter.child_record_prefix_length(text)
            offsets = [(index, index + 1) for index in range(len(text))] + [(0, 0)]
            attention = [1] * len(text) + [0]
            mask = train_adapter.child_target_mask(offsets, boundary, attention)
            labels = [index + 1 if selected else -100 for index, selected in enumerate(mask)]
            counts = train_adapter.child_label_counts(offsets, boundary, attention, labels)
            self.assertEqual(counts["masked_prefix_tokens"], boundary - 1)
            self.assertEqual(counts["supervised_child_tokens"], len(text) - boundary)
            row_counts.append(counts)
            nonpadding_tokens += sum(attention)
        epochs = 3
        for _ in range(epochs - 1):
            for text, expected in zip(corpus, row_counts):
                boundary = train_adapter.child_record_prefix_length(text)
                offsets = [(index, index + 1) for index in range(len(text))] + [(0, 0)]
                attention = [1] * len(text) + [0]
                mask = train_adapter.child_target_mask(offsets, boundary, attention)
                labels = [index + 1 if selected else -100 for index, selected in enumerate(mask)]
                self.assertEqual(train_adapter.child_label_counts(offsets, boundary, attention, labels), expected)
        supervised = sum(row["supervised_child_tokens"] for row in row_counts) * epochs
        metadata_path = self.adapter / "train_meta.json"
        metadata = json.loads(metadata_path.read_bytes())
        metadata.update(epochs=epochs, steps=epochs, tokens=nonpadding_tokens * epochs,
                        supervised_tokens=supervised,
                        masked_nonpadding_tokens=nonpadding_tokens * epochs - supervised)
        metadata_path.write_bytes(encode(metadata))
        receipt_path = self.runtime / "actual-writer-receipt.json"
        emitted = train_adapter.write_training_receipt(
            receipt_path, self.adapter, gate, args["expected_gate_sha256"], row_counts,
        )
        self.assertEqual(emitted["train_metadata_sha256"], sha(metadata_path.read_bytes()))
        self.assertEqual([row["supervised_child_tokens"] for row in emitted["rows"]],
                         [row["supervised_child_tokens"] for row in row_counts])
        args.update(trainer_receipt_path=receipt_path, expected_trainer_sha256=sha(receipt_path.read_bytes()))
        (self.adapter / "DONE").rename(self.adapter / "CANDIDATE")
        accepted_dir = self.runtime / "runner-accepted-adapter"
        self.adapter.rename(accepted_dir)
        args["adapter_dir"] = accepted_dir
        self.reject_sleep(args, pattern="requires final DONE")
        (accepted_dir / "CANDIDATE").rename(accepted_dir / "DONE")
        selected = synthetic_selection(accepted_dir, self.life / "lineage/birth/model", args["previous_sha256"])
        args.update(selection_path=selected["selection_path"], expected_selection_sha256=selected["selection_sha256"])
        checkpoint = lineage.record_sleep(self.life, "sleep_0001", **args)
        self.assertTrue(checkpoint.ancestry.eligible)
        snapshot = Path(checkpoint.adapter_dir).parent
        self.assertEqual((snapshot / "trainer_receipt.json").read_bytes(), receipt_path.read_bytes())
        self.assertEqual((snapshot / "corpus.json").read_bytes(), corpus_bytes)
        self.assertEqual((snapshot / "adapter/train_meta.json").read_bytes(),
                         (accepted_dir / "train_meta.json").read_bytes())
        (accepted_dir / "adapter_model.safetensors").write_bytes(b"different later fixture adapter")
        self.reject_sleep(args, "sleep_0002", "trainer receipt adapter binding mismatch")
        self.assertTrue(guard.validate_manifest(checkpoint.ancestry.manifest.path,
                                               root=checkpoint.ancestry.root).eligible)

    def test_sleep_snapshots_remain_valid_after_ledger_growth(self):
        birth = self.birth()
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(birth))
        original = Path(first.ledger_snapshot).read_bytes()
        second_args = self.inputs(first, rows=event() + event(2))
        second = lineage.record_sleep(self.life, "sleep_0002", **second_args)
        self.assertEqual(len(second.ancestry.manifests), 3)
        self.assertEqual(Path(first.ledger_snapshot).read_bytes(), original)
        self.assertNotEqual(Path(second.ledger_snapshot).read_bytes(), original)
        self.assertTrue(guard.validate_manifest(first.ancestry.manifest.path,
                                               root=first.ancestry.root).eligible)
        second_args["ledger_path"].write_bytes(b"unrelated later change")
        self.assertTrue(guard.validate_manifest(second.ancestry.manifest.path,
                                               root=second.ancestry.root).eligible)

    def test_changed_or_shrunken_ledger_prefix_is_rejected(self):
        birth = self.birth()
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(birth, rows=event() + event(2)))
        for rows in (event(), event(text="changed prior child text") + event(2)):
            args = self.inputs(first, rows=rows)
            self.reject_sleep(args, "sleep_0002", "append-only")
        self.assertFalse((self.life / "lineage/sleep_0002").exists())

    def test_summary_receipt_is_not_row_linked_evidence(self):
        args = self.inputs(self.birth())
        content = encode({"enforced": True, "training_skipped": False, "n_admitted_total": 1})
        args["gate_receipt_path"].write_bytes(content)
        args["expected_gate_sha256"] = sha(content)
        self.reject_sleep(args, pattern="missing or unknown fields")

    def test_gate_pins_and_all_input_hashes_required(self):
        birth = self.birth()
        args = self.inputs(birth)
        args["expected_gate_sha256"] = "0" * 64
        self.reject_sleep(args, pattern="external gate pin")
        for field in ("previous_manifest_sha256", "ledger_sha256", "corpus_sha256"):
            args = self.inputs(birth)
            self.update_gate(args, lambda gate: gate.update({field: "0" * 64}))
            self.reject_sleep(args, pattern="gate input hash")

    def test_gate_recipe_decision_and_complete_admissions(self):
        birth = self.birth()
        for field, value in (("recipe", "legacy_v1"), ("decision", "SHADOW"),
                             ("admissions", []), ("schema_version", True),
                             ("exposure_status", "UNKNOWN")):
            with self.subTest(field=field):
                args = self.inputs(birth)
                self.update_gate(args, lambda gate: gate.update({field: value}))
                self.reject_sleep(args)

    def test_gate_links_exact_physical_record_and_source_rows(self):
        birth = self.birth()
        for field, value in (("record_sha256", "0" * 64), ("source_sha256", "0" * 64),
                             ("record_line", False), ("source_line", -1), ("record_line", 0)):
            with self.subTest(field=field):
                args = self.inputs(birth)
                self.update_gate(args, lambda gate: gate["admissions"][0].update({field: value}))
                self.reject_sleep(args)

    def test_pre_outcome_note_cannot_join_a_later_act(self):
        birth = self.birth()
        action, record = event()
        self.reject_sleep(self.inputs(birth, [record, action]), pattern="invalid gate row linkage")

    def test_trainer_receipt_and_external_pin_are_mandatory(self):
        birth = self.birth()
        for field in ("trainer_receipt_path", "expected_trainer_sha256"):
            args = self.inputs(birth)
            del args[field]
            self.reject_sleep(args)
        args = self.inputs(birth)
        args["trainer_receipt_path"].unlink()
        self.reject_sleep(args)
        args = self.inputs(birth)
        args["expected_trainer_sha256"] = "0" * 64
        self.reject_sleep(args, pattern="external trainer pin mismatch")
        self.assertFalse((self.life / "lineage/sleep_0001").exists())

    def test_child_only_boolean_or_legacy_summary_is_not_mask_evidence(self):
        args = self.inputs(self.birth())
        content = encode({"recipe": "v1_frozen", "child_only": True, "steps": 1})
        args["trainer_receipt_path"].write_bytes(content)
        args["expected_trainer_sha256"] = sha(content)
        self.reject_sleep(args, pattern="missing or unknown fields")

    def test_trainer_must_bind_lineage_corpus_gate_and_actual_adapter(self):
        birth = self.birth()
        for field in ("previous_manifest_sha256", "corpus_sha256", "gate_receipt_sha256", "train_metadata_sha256"):
            args = self.inputs(birth)
            self.update_trainer(args, lambda receipt: receipt.update({field: "0" * 64}))
            self.reject_sleep(args, pattern="trainer receipt input binding")
        for name in ("adapter_config.json", "adapter_model.safetensors"):
            args = self.inputs(birth)
            self.update_trainer(args, lambda receipt: receipt["adapter_files"].update({name: "0" * 64}))
            self.reject_sleep(args, pattern="trainer receipt adapter binding")
        args = self.inputs(birth)
        (self.adapter / "adapter_model.safetensors").write_bytes(b"different actual trained adapter")
        self.reject_sleep(args, pattern="trainer receipt adapter binding")

    def test_trainer_masks_exclude_prefix_padding_and_empty_child_loss(self):
        birth = self.birth()
        for field, value in (("supervised_prefix_tokens", 1), ("supervised_padding_tokens", 1),
                             ("supervised_prefix_tokens", False), ("masked_prefix_tokens", 0),
                             ("supervised_child_tokens", 0), ("supervised_child_tokens", True)):
            with self.subTest(field=field, value=value):
                args = self.inputs(birth)
                self.update_trainer(args, lambda receipt: receipt["rows"][0].update({field: value}))
                self.reject_sleep(args, pattern="mask evidence")

    def test_trainer_rows_are_complete_and_match_admitted_sources(self):
        birth = self.birth()
        args = self.inputs(birth)
        self.update_trainer(args, lambda receipt: receipt.update(rows=[]))
        self.reject_sleep(args, pattern="cover every admitted row")
        for field in ("record_sha256", "source_sha256"):
            args = self.inputs(birth)
            self.update_trainer(args, lambda receipt: receipt["rows"][0].update({field: "0" * 64}))
            self.reject_sleep(args, pattern="admitted row/source mismatch")
        args = self.inputs(birth, event() + event(2))
        self.update_trainer(args, lambda receipt: receipt["rows"].reverse())
        self.reject_sleep(args, pattern="admitted row/source mismatch")

    def test_incomplete_or_wrong_supervision_recipe_is_rejected(self):
        birth = self.birth()
        for field, value in (("corpus_recipe", "other"), ("supervision", "full_string_loss"),
                             ("status", "PENDING"), ("schema_version", True)):
            args = self.inputs(birth)
            self.update_trainer(args, lambda receipt: receipt.update({field: value}))
            self.reject_sleep(args, pattern="unsupported/incomplete")

    def test_actual_native_metadata_is_required_and_not_a_standalone_receipt(self):
        birth = self.birth()
        args = self.inputs(birth)
        (self.adapter / "train_meta.json").unlink()
        self.reject_sleep(args)
        args = self.inputs(birth)
        content = (self.adapter / "train_meta.json").read_bytes()
        args["trainer_receipt_path"].write_bytes(content)
        args["expected_trainer_sha256"] = sha(content)
        self.reject_sleep(args, pattern="missing or unknown fields")

    def test_full_string_or_unbound_actual_training_cannot_be_relabelled(self):
        birth = self.birth()
        for field, value in (("recipe", "v1_frozen"), ("loss_target", "full_string"),
                             ("source_recipe", "legacy"), ("source_corpus_sha256", "0" * 64)):
            with self.subTest(field=field):
                args = self.inputs(birth)
                self.update_train_metadata(args, lambda metadata: metadata.update({field: value}))
                self.reject_sleep(args, pattern="actual trainer metadata")

    def test_actual_mask_totals_must_agree_with_per_row_training_receipt(self):
        birth = self.birth()
        for field, value in (("n_texts", 2), ("supervised_tokens", 0), ("steps", False), ("epochs", 2)):
            with self.subTest(field=field):
                args = self.inputs(birth)
                self.update_train_metadata(args, lambda metadata: metadata.update({field: value}))
                self.reject_sleep(args)
        args = self.inputs(birth)
        self.update_trainer(args, lambda receipt: receipt["rows"][0].update(supervised_child_tokens=19))
        self.reject_sleep(args, pattern="disagree with actual training totals")

    def test_actual_training_metadata_snapshot_survives_later_input_changes(self):
        args = self.inputs(self.birth())
        sleep = lineage.record_sleep(self.life, "sleep_0001", **args)
        snapshot = Path(sleep.adapter_dir) / "train_meta.json"
        original = snapshot.read_bytes()
        (self.adapter / "train_meta.json").write_bytes(b"later metadata")
        self.assertEqual(snapshot.read_bytes(), original)
        self.assertTrue(guard.validate_manifest(sleep.ancestry.manifest.path,
                                               root=sleep.ancestry.root).eligible)

    def test_new_receipt_cannot_launder_missing_prior_training_evidence(self):
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(self.birth()))
        path = Path(first.ancestry.root) / first.ancestry.manifest.path
        manifest = json.loads(path.read_bytes())
        manifest["artifacts"] = [item for item in manifest["artifacts"]
                                 if not item["path"].endswith("/train_meta.json")]
        content = encode(manifest)
        path.chmod(0o600)
        path.write_bytes(content)
        changed = replace(first, ancestry=replace(first.ancestry,
                          manifest=guard.FileBinding(first.ancestry.manifest.path, sha(content))))
        self.reject_sleep(self.inputs(changed, event() + event(2)), "sleep_0002",
                          "prior sleep lacks bound training evidence")

    def test_missing_selection_is_never_a_legacy_bypass(self):
        args = self.inputs(self.birth())
        for field in ("selection_path", "expected_selection_sha256"):
            missing = dict(args)
            del missing[field]
            with self.subTest(field=field):
                self.reject_sleep(missing, pattern="selection custody is required")
        self.assertFalse((self.life / "lineage/sleep_0001").exists())

    def test_selection_input_tampering_rejected_before_snapshot(self):
        birth = self.birth()
        for name in ("trace.json", "receipt.json", "selected.json"):
            args = self.inputs(birth)
            path = Path(args["selection_path"]).parent / name
            path.chmod(0o600)
            path.write_bytes(path.read_bytes() + b" ")
            with self.subTest(name=name):
                self.reject_sleep(args)
        self.assertFalse((self.life / "lineage/sleep_0001").exists())

    def rebind_fixture_manifest(self, checkpoint, manifest):
        path = Path(checkpoint.ancestry.root) / checkpoint.ancestry.manifest.path
        content = encode(manifest)
        path.chmod(0o600)
        path.write_bytes(content)
        return replace(checkpoint, ancestry=replace(checkpoint.ancestry,
                       manifest=guard.FileBinding(checkpoint.ancestry.manifest.path, sha(content))))

    def test_replay_requires_historical_selection_not_new_receipt(self):
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(self.birth()))
        path = Path(first.ancestry.root) / first.ancestry.manifest.path
        original = json.loads(path.read_bytes())
        for filename in ("receipt.json", "selected.json"):
            manifest = deepcopy(original)
            manifest["artifacts"] = [item for item in manifest["artifacts"]
                                      if item["path"] != "sleep_0001/canary_selection/" + filename]
            changed = self.rebind_fixture_manifest(first, manifest)
            with self.subTest(missing=filename):
                self.reject_sleep(self.inputs(changed, event() + event(2)), "sleep_0002",
                                  "prior sleep lacks bound canary selection evidence")

    def test_replay_rejects_mixed_training_and_selection_references(self):
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(self.birth()))
        path = Path(first.ancestry.root) / first.ancestry.manifest.path
        original = json.loads(path.read_bytes())
        trace = next(source for source in original["sources"] if source["path"].endswith("/trace.json"))
        for target in ("corpus", "done"):
            manifest = deepcopy(original)
            if target == "corpus":
                manifest["trained_corpus"][0]["source_sha256"].append(trace["sha256"])
                pattern = "canary source mixed into training corpus"
            else:
                artifact = next(item for item in manifest["artifacts"] if item["path"].endswith("/DONE"))
                artifact["source_sha256"] = manifest["trained_corpus"][0]["source_sha256"]
                pattern = "canary selection artifact has incorrect sources"
            changed = self.rebind_fixture_manifest(first, manifest)
            with self.subTest(target=target):
                self.reject_sleep(self.inputs(changed, event() + event(2)), "sleep_0002", pattern)

    def test_replay_recomputes_false_verdict_even_with_rebound_manifest(self):
        from organism_v6 import nursery_selection_receipt as selection

        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(self.birth()))
        root = Path(first.ancestry.root)
        path = root / first.ancestry.manifest.path
        manifest = json.loads(path.read_bytes())
        receipt_path = root / "sleep_0001/canary_selection/receipt.json"
        receipt = json.loads(receipt_path.read_bytes())
        receipt.update(rate=0.0)
        receipt_path.chmod(0o600)
        receipt_path.write_bytes(selection._encoded(receipt))
        selected_path = receipt_path.parent / "selected.json"
        selected = json.loads(selected_path.read_bytes())
        selected["receipt_sha256"] = sha(receipt_path.read_bytes())
        selected_path.chmod(0o600)
        selected_path.write_bytes(selection._encoded(selected))
        for item in manifest["artifacts"]:
            if item["path"].endswith("/canary_selection/receipt.json"):
                item["sha256"] = sha(receipt_path.read_bytes())
            if item["path"].endswith("/canary_selection/selected.json"):
                item["sha256"] = sha(selected_path.read_bytes())
        changed = self.rebind_fixture_manifest(first, manifest)
        self.reject_sleep(self.inputs(changed, event() + event(2)), "sleep_0002", "false canary verdict")

    def test_new_receipt_cannot_launder_prior_prefix_supervision(self):
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(self.birth()))
        root = Path(first.ancestry.root)
        trainer_path = root / "sleep_0001/trainer_receipt.json"
        trainer = json.loads(trainer_path.read_bytes())
        trainer["rows"][0]["supervised_prefix_tokens"] = 1
        content = encode(trainer)
        trainer_path.chmod(0o600)
        trainer_path.write_bytes(content)
        path = root / first.ancestry.manifest.path
        manifest = json.loads(path.read_bytes())
        for artifact in manifest["artifacts"]:
            if artifact["path"] == "sleep_0001/trainer_receipt.json":
                artifact["sha256"] = sha(content)
        content = encode(manifest)
        path.chmod(0o600)
        path.write_bytes(content)
        changed = replace(first, ancestry=replace(first.ancestry,
                          manifest=guard.FileBinding(first.ancestry.manifest.path, sha(content))))
        self.reject_sleep(self.inputs(changed, event() + event(2)), "sleep_0002",
                          "supervises prefix/padding")

    def test_corpus_cannot_be_parent_row_or_parent_copy(self):
        birth = self.birth()
        text = "I observed the ball moving closer after turning left."
        rows = [{"kind": "parent_turn", "text": text}] + event(text=text)
        args = self.inputs(birth, rows)
        self.reject_sleep(args, pattern="parent text")
        args = self.inputs(birth, rows=[{"kind": "parent_turn", "text": text}] + event())
        self.update_gate(args, lambda gate: gate["admissions"][0].update(
            record_line=0, record_sha256=sha(encode({"kind": "parent_turn", "text": text}))
        ))
        self.reject_sleep(args)

    def test_parent_evidence_is_snapshotted_without_becoming_corpus(self):
        birth = self.birth()
        rows = [{"kind": "parent_turn", "text": "Observe the outcome before making a claim."}] + event()
        sleep = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(birth, rows))
        self.assertIn(b"Observe the outcome", Path(sleep.ledger_snapshot).read_bytes())
        corpus = Path(sleep.adapter_dir).parent / "corpus.json"
        self.assertNotIn(b"Observe the outcome", corpus.read_bytes())
        root = Path(sleep.ancestry.root)
        manifest = json.loads((root / sleep.ancestry.manifest.path).read_bytes())
        parents = [source for source in manifest["sources"] if source["role"] == "parent_turn"]
        self.assertEqual(len(parents), 1)
        self.assertEqual((root / parents[0]["path"]).read_bytes(), encode(rows[0]))

    def test_reasoning_measured_zero_partial_full_statusless_acts(self):
        birth = self.birth()
        for number, score in enumerate((0.0, 0.5, 1.0), 1):
            with self.subTest(score=score):
                rows = reasoning_event(number, score=score, text="  I observed this outcome.\n")
                self.assertNotIn("status", rows[1])
                args = self.inputs(birth, rows)
                original = args["ledger_path"].read_bytes()
                sleep = lineage.record_sleep(self.life, f"sleep_{number:04d}", **args)
                self.assertEqual(Path(sleep.ledger_snapshot).read_bytes(), original)
                self.assertEqual(args["ledger_path"].read_bytes(), original)
                snapshot = Path(sleep.adapter_dir).parent
                self.assertEqual((snapshot / "row_00000000.jsonl").read_bytes(), encode(rows[0]))
                self.assertEqual((snapshot / "corpus.json").read_bytes(), args["corpus_path"].read_bytes())

    def test_reasoning_requires_exact_situation_wrapper_and_raw_body(self):
        birth = self.birth()
        for transform in (lambda text: text.replace("Situation ", "Program ", 1),
                          lambda text: text.replace(":   I", ": I").rstrip()):
            args = self.inputs(birth, reasoning_event(text="  I observed score 0.50.\n"))
            self.update_corpus(args, lambda corpus: corpus.update(corpus=[transform(corpus["corpus"][0])]))
            self.reject_sleep(args, pattern="exact admitted child-record recipe")
        args = self.inputs(birth)
        self.update_corpus(args, lambda corpus: corpus.update(
            corpus=[corpus["corpus"][0].replace("Program ", "Situation ", 1)]))
        self.reject_sleep(args, pattern="exact admitted child-record recipe")

    def test_reasoning_reservation_must_be_unique_earlier_and_exact(self):
        birth = self.birth()
        rows = reasoning_event()
        cases = [rows[1:], [rows[1], rows[0], rows[2]], [rows[0], *rows]]
        for field, value in (("occurrence_index", True), ("occurrence_index", 0),
                             ("occurrence_id", "wrong"), ("slot_kind", "scratchpad")):
            modified = deepcopy(rows)
            modified[0][field] = value
            cases.append(modified)
        for case in cases:
            with self.subTest(rows=case):
                self.reject_sleep(self.inputs(birth, case), pattern="occurrence")

    def test_reasoning_join_requires_exact_score_occurrence_and_measurement(self):
        birth = self.birth()
        for field, value in (("score", 1.0), ("occurrence_index", True),
                             ("occurrence_id", "wrong"), ("attempt", True),
                             ("reported_score", "0.5"), ("verifier_score", 0),
                             ("verdict", "accepted"), ("measured", 1),
                             ("status", "unmeasured"), ("policy_version", "unknown"),
                             ("speaker", "parent")):
            with self.subTest(field=field):
                rows = reasoning_event()
                rows[2][field] = value
                self.reject_sleep(self.inputs(birth, rows))

    def test_reasoning_rejects_forged_feedback_execution_or_episode(self):
        birth = self.birth()
        for field, value in (("score", True), ("score", 1.0), ("execution_id", "fabricated"),
                             ("episode_id", "rg/malformed"), ("tick", 0)):
            rows = reasoning_event()
            rows[1][field] = rows[2][field] = value
            self.reject_sleep(self.inputs(birth, rows))
        rows = reasoning_event()
        rows[1]["status"] = "unmeasured"
        self.reject_sleep(self.inputs(birth, rows), pattern="status mismatch")

    def test_reasoning_pre_outcome_record_and_missing_measurement_rejected(self):
        birth = self.birth()
        rows = reasoning_event()
        self.reject_sleep(self.inputs(birth, [rows[0], rows[2], rows[1]]), pattern="row linkage")
        for field in ("score", "measured", "status", "speaker", "policy_version"):
            modified = deepcopy(rows)
            del modified[2][field]
            self.reject_sleep(self.inputs(birth, modified))

    def test_reasoning_parent_turn_inventory_and_ledger_growth(self):
        parent = {"kind": "parent_turn", "speaker": "teacher", "teacher_authored": True,
                  "factual_evidence": False, "text": "Observe the outcome before making a claim.",
                  "lesson_receipt_sha256": sha(b"synthetic lesson receipt"),
                  "policy_version": reasoning.POLICY_VERSION}
        rows = [parent, *reasoning_event()]
        first = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(self.birth(), rows))
        original = Path(first.ledger_snapshot).read_bytes()
        second = lineage.record_sleep(self.life, "sleep_0002",
                                      **self.inputs(first, rows + reasoning_event(2)))
        self.assertEqual(Path(first.ledger_snapshot).read_bytes(), original)
        self.assertTrue(Path(second.ledger_snapshot).read_bytes().startswith(original))
        self.assertNotIn(parent["text"], (Path(second.adapter_dir).parent / "corpus.json").read_text())

    def reasoning_note_rows(self):
        families = json.loads(reasoning.FAMILIES_FILE.read_text())
        provenance = dict(gym="reasoning_gym", clone_id=3,
                          exposure_domain="reasoning_gym:" + ",".join(families["train_families"]))
        rows = reasoning_event()
        rows.append(dict(kind="note", episode_id=rows[0]["episode_id"], tick=1,
                         note="I will reconsider my next answer."))
        return [dict(row, **provenance) for row in rows]

    def test_reasoning_note_is_snapshotted_but_never_an_admission(self):
        rows = self.reasoning_note_rows()
        args = self.inputs(self.birth(), rows)
        before = args["ledger_path"].read_bytes()
        sleep = lineage.record_sleep(self.life, "sleep_0001", **args)
        self.assertTrue(sleep.ancestry.eligible)
        self.assertEqual(Path(sleep.ledger_snapshot).read_bytes(), before)
        self.assertEqual(args["ledger_path"].read_bytes(), before)
        corpus = json.loads((Path(sleep.adapter_dir).parent / "corpus.json").read_bytes())
        self.assertEqual(len(corpus["corpus"]), 1)
        self.assertNotIn(rows[-1]["note"], corpus["corpus"][0])
        self.assertNotIn("generation", rows[-1])

    def test_reasoning_note_shape_provenance_and_contamination_rejected(self):
        birth = self.birth()
        original = self.reasoning_note_rows()
        changes = ({"note": ""}, {"note": 3}, {"tick": True}, {"tick": 1.0}, {"tick": 0},
                   {"speaker": "teacher"}, {"episode_id": None},
                   {"episode_id": "rg/countdown/1000999"},
                   {"episode_id": "rg/countdown/1900001"},
                   {"episode_id": "rg/n_queens/2000001"},
                   {"gym": "other_gym"}, {"exposure_domain": "reasoning_gym:countdown"},
                   {"clone_id": 4}, {"clone_id": 3.0}, {"clone_id": True},
                   {"exposure_status": "UNKNOWN"},
                   {"exposure_status": "QUARANTINE_TASK_EXPOSED"},
                   {"note": "LLVM"}, {"note": "DEV_UNVERIFIED_PROVENANCE"},
                   {"note": "Remember rg/n_queens/2000001"},
                   {"kind": "scratchpad"}, {"kind": "episode_end"},
                   {"generation": {}}, {"teacher_authored": True})
        for change in changes:
            with self.subTest(change=change):
                self.reject_sleep(self.inputs(birth, original[:-1] + [dict(original[-1], **change)]))
        for field in ("note", "episode_id", "tick", "gym", "exposure_domain", "clone_id"):
            note = dict(original[-1])
            del note[field]
            with self.subTest(missing=field):
                self.reject_sleep(self.inputs(birth, original[:-1] + [note]))
        self.reject_sleep(self.inputs(birth, [original[-1], *original[:-1]]),
                          pattern="preceding episode reservation")
        unstamped = [{key: value for key, value in row.items()
                      if key not in ("gym", "exposure_domain", "clone_id")} for row in original]
        self.reject_sleep(self.inputs(birth, unstamped), pattern="NOTE requires ledger provenance")

    def test_rebound_gate_cannot_use_note_as_source_or_write_record(self):
        birth = self.birth()
        for role in ("source", "record"):
            rows = self.reasoning_note_rows()
            rows.insert(2, rows.pop())
            args = self.inputs(birth, rows)
            self.update_gate(args, lambda gate: gate["admissions"][0].update(
                {role + "_line": 2, role + "_sha256": sha(encode(rows[2]))}))
            with self.subTest(role=role):
                self.reject_sleep(args, pattern="corpus must link child records to environment outcomes")

    def test_note_does_not_relax_source_identity_or_raw_ledger_hash(self):
        birth = self.birth()
        rows = self.reasoning_note_rows()
        rows[2]["action"] = "substituted action"
        self.reject_sleep(self.inputs(birth, rows), pattern="record/source mismatch: action")
        rows = self.reasoning_note_rows()
        args = self.inputs(birth, rows)
        rows[-1]["note"] = "Altered after gate binding."
        args["ledger_path"].write_bytes(b"".join(encode(row) for row in rows))
        self.reject_sleep(args, pattern="gate input hash mismatch")

    def test_unknown_episode_end_and_bare_notes_remain_fail_closed(self):
        birth = self.birth()
        for kind in ("episode_end", "scratchpad"):
            self.reject_sleep(self.inputs(birth, [*reasoning_event(), {"kind": kind}]),
                              pattern="unsupported/unknown ledger influence")
        self.reject_sleep(self.inputs(birth, [*reasoning_event(), {"kind": "note"}]),
                          pattern="NOTE requires ledger provenance")

    def test_mismatched_and_ambiguous_execution_links_rejected(self):
        birth = self.birth()
        for field in ("episode_id", "tick", "action", "outcome", "status"):
            rows = event()
            rows[1][field] = 900 if field == "tick" else "forged"
            args = self.inputs(birth, rows)
            self.reject_sleep(args, pattern="mismatch")
        for rows in ([*event(), event()[0]], [*event(), event()[1]]):
            args = self.inputs(birth, rows)
            self.reject_sleep(args)

    def test_corpus_text_recipe_and_principles_cannot_be_substituted(self):
        birth = self.birth()
        for change in (lambda corpus: corpus.update(corpus=["parent lesson supplied as training text"]),
                       lambda corpus: corpus.update(recipe="bootstrap_v3"),
                       lambda corpus: corpus.update(principles=["invented principle"]),
                       lambda corpus: corpus.update(extra_influence="unknown")):
            args = self.inputs(birth)
            self.update_corpus(args, change)
            self.reject_sleep(args)

    def test_unknown_ledger_influences_exposure_or_extra_streams_rejected(self):
        birth = self.birth()
        for extra in ({"kind": "retrieved_unknown_text"},
                      {"kind": "thought", "exposure_status": "UNKNOWN"},
                      {"kind": "thought", "origin": "CompilerGym"}):
            args = self.inputs(birth, rows=event() + [extra])
            self.reject_sleep(args)
        args = self.inputs(birth)
        args["other_influences"] = ["lesson outside the ledger"]
        self.reject_sleep(args, pattern="additional influences")

    def test_adapter_requires_real_lora_weights_and_fixed_base_config(self):
        birth = self.birth()
        for overrides in ({"peft_type": "FULL"}, {"base_model_name_or_path": "other/base"}):
            self.write_adapter(**overrides)
            self.reject_sleep(self.inputs(birth), pattern="not LoRA")
        self.write_adapter()
        (self.adapter / "adapter_model.safetensors").unlink()
        self.reject_sleep(self.inputs(birth), pattern="weights/config")

    def test_adapter_may_name_the_actual_pinned_local_birth_model(self):
        birth = self.birth()
        self.write_adapter(base_model_name_or_path=birth.model_dir)
        sleep = lineage.record_sleep(self.life, "sleep_0001", **self.inputs(birth))
        self.assertTrue(sleep.ancestry.eligible)

    def test_record_sleep_waits_for_runner_final_done_transition(self):
        args = self.inputs(self.birth())
        (self.adapter / "DONE").rename(self.adapter / "CANDIDATE")
        self.reject_sleep(args, pattern="requires final DONE")
        self.assertFalse((self.life / "lineage/sleep_0001").exists())
        (self.adapter / "CANDIDATE").rename(self.adapter / "DONE")
        sleep = lineage.record_sleep(self.life, "sleep_0001", **args)
        self.assertTrue(sleep.ancestry.eligible)
        receipt = json.loads(args["trainer_receipt_path"].read_bytes())
        self.assertEqual(set(receipt["adapter_files"]),
                         {"adapter_config.json", "adapter_model.safetensors"})

    def test_missing_rejected_and_conflicting_adapter_verdicts_fail_closed(self):
        birth = self.birth()
        for markers in ((), ("REJECTED_CANARY",), ("DONE", "CANDIDATE"),
                        ("DONE", "REJECTED_SCORE")):
            with self.subTest(markers=markers):
                for name in ("DONE", "CANDIDATE", "REJECTED_CANARY", "REJECTED_SCORE"):
                    (self.adapter / name).unlink(missing_ok=True)
                for name in markers:
                    (self.adapter / name).write_bytes(b"ok\n")
                self.reject_sleep(self.inputs(birth), pattern="requires final DONE")

    def test_empty_or_changed_done_marker_is_not_recorded(self):
        birth = self.birth()
        (self.adapter / "DONE").write_bytes(b"")
        self.reject_sleep(self.inputs(birth), pattern="nonempty regular input")
        (self.adapter / "DONE").write_bytes(b"ok\n")
        args = self.inputs(birth)
        with mock.patch.object(lineage, "_accepted_marker", side_effect=[b"ok\n", b"ok\n", b"changed\n"]):
            self.reject_sleep(args, pattern="acceptance changed")
        self.assertFalse((self.life / "lineage/sleep_0001/manifest.json").exists())

    def test_parent_speaker_cannot_be_relabelled_as_child_record(self):
        birth = self.birth()
        rows = event()
        rows[1]["speaker"] = "parent"
        self.reject_sleep(self.inputs(birth, rows), pattern="not child-authored")

    def test_sleep_inputs_do_not_get_base_symlink_exception(self):
        birth = self.birth()
        for field in ("ledger_path", "corpus_path", "gate_receipt_path", "trainer_receipt_path", "adapter_dir"):
            args = self.inputs(birth)
            link = self.runtime / f"link-{field}"
            link.symlink_to(args[field], target_is_directory=field == "adapter_dir")
            args[field] = link
            self.reject_sleep(args)
        for name in ("adapter_config.json", "adapter_model.safetensors", "train_meta.json", "DONE"):
            target = self.adapter / name
            content = target.read_bytes()
            backing = self.runtime / f"backing-{name}"
            backing.write_bytes(content)
            target.unlink()
            target.symlink_to(backing)
            self.reject_sleep(self.inputs(birth))
            target.unlink()
            target.write_bytes(content)

    def test_sleep_never_overwrites_a_checkpoint(self):
        birth = self.birth()
        args = self.inputs(birth)
        sleep = lineage.record_sleep(self.life, "sleep_0001", **args)
        snapshot = Path(sleep.ledger_snapshot)
        original = snapshot.read_bytes()
        self.reject_sleep(args)
        self.assertEqual(snapshot.read_bytes(), original)

    def test_tampered_parent_or_birth_snapshot_rejected(self):
        birth = self.birth()
        target = Path(birth.model_dir) / "model.safetensors"
        target.chmod(0o600)
        target.write_bytes(b"tampered frozen snapshot")
        self.reject_sleep(self.inputs(birth), pattern="SHA256 mismatch")

    def test_invalid_paths_and_text_bound_rejected(self):
        birth = self.birth()
        args = self.inputs(birth)
        for checkpoint in ("../sleep_0001", "sleep_0001/other", "birth"):
            self.reject_sleep(args, checkpoint)
        args["previous_manifest"] = "../birth/manifest.json"
        self.reject_sleep(args)
        args = self.inputs(birth)
        with mock.patch.object(lineage, "MAX_TEXT_BYTES", 4):
            self.reject_sleep(args, pattern="supported bound")


if __name__ == "__main__":
    unittest.main()
