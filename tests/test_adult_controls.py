"""CPU-only adult control tests; model/adapter bytes are unauthenticated fixtures.

Run: PYTHONDONTWRITEBYTECODE=1 python3 tests/test_adult_controls.py
"""
from dataclasses import FrozenInstanceError
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organism_v6 import adult_controls as adult
from organism_v6 import life_lineage as lineage
from organism_v6 import lineage_guard as guard


def encoded(value):
    return json.dumps(value, sort_keys=True).encode() + b"\n"


def digest(content):
    return hashlib.sha256(content).hexdigest()


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(content if isinstance(content, bytes) else encoded(content))


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in Path(directory).rglob("*") if path.is_file()}


class AdultControlsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="adult_controls_", dir="/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        model = self.root / "base"
        model.mkdir()
        files = {
            "config.json": encoded({"model_type": "qwen2"}),
            "model.safetensors": b"test bytes, NOT authenticated Qwen weights",
            "tokenizer.json": encoded({"fixture": True}),
            "tokenizer_config.json": encoded({"tokenizer_class": "Qwen2TokenizerFast"}),
        }
        for name, content in files.items():
            write(model / name, content)
        self.child = self.root / "child"
        self.child.mkdir()
        birth = lineage.prepare_birth(
            self.child, model_dir=model, expected_model_id=guard.BASE_MODEL,
            expected_model_files={name: digest(content) for name, content in files.items()},
            loaded_adapter_path=None, exposure_status="UNEXPOSED", other_influences=[])
        runtime = self.root / "runtime"
        self.adapter_config = {"peft_type": "LORA", "base_model_name_or_path": guard.BASE_MODEL, "r": 8}
        write(runtime / "adapter" / "adapter_config.json", self.adapter_config)
        write(runtime / "adapter" / "adapter_model.safetensors", b"child adapter fixture")
        self.parent_text = "PARENT_ONLY_SENTINEL: Notice the source of an observation."
        self.child_text = "I moved east and observed the distance decrease from two to one."
        action = dict(kind="act", episode_id="lesson/train/1", execution_id="exec-1",
                      tick=1, action="move east", outcome="distance now one", status="success")
        rows = [{"kind": "parent_turn", "text": self.parent_text}, action,
                {**action, "kind": "note_after", "speaker": "child", "text": self.child_text}]
        lines = [encoded(row) for row in rows]
        ledger_bytes = b"".join(lines)
        self.child_item = f"Program {action['episode_id']}.\nMy measured action record: {self.child_text}"
        corpus_bytes = encoded(dict(recipe=lineage.RECIPE, corpus=[self.child_item],
                                    principles=[], n_new=1, n_dropped_legacy=0))
        gate_bytes = encoded(dict(
            schema_version=1, recipe=lineage.RECIPE, decision="ADMIT", exposure_status="UNEXPOSED",
            previous_manifest_sha256=birth.ancestry.manifest.sha256,
            ledger_sha256=digest(ledger_bytes), corpus_sha256=digest(corpus_bytes),
            admissions=[dict(record_line=2, record_sha256=digest(lines[2]),
                             source_line=1, source_sha256=digest(lines[1]))]))
        for name, content in (("ledger.jsonl", ledger_bytes), ("corpus.json", corpus_bytes),
                              ("gate.json", gate_bytes)):
            write(runtime / name, content)
        metadata_bytes = encoded(dict(
            recipe="v1_frozen_child_target", source_recipe=lineage.RECIPE,
            loss_target="child_body_only", source_corpus_sha256=digest(corpus_bytes),
            n_texts=1, epochs=3, steps=3, tokens=84,
            supervised_tokens=48, masked_nonpadding_tokens=36))
        write(runtime / "adapter/train_meta.json", metadata_bytes)
        trainer_bytes = encoded(dict(
            schema_version=1, corpus_recipe=lineage.RECIPE, supervision="child_only_v1",
            status="COMPLETED", previous_manifest_sha256=birth.ancestry.manifest.sha256,
            corpus_sha256=digest(corpus_bytes), gate_receipt_sha256=digest(gate_bytes),
            train_metadata_sha256=digest(metadata_bytes),
            adapter_files={name: digest((runtime / "adapter" / name).read_bytes())
                           for name in ("adapter_config.json", "adapter_model.safetensors")},
            rows=[dict(record_sha256=digest(lines[2]), source_sha256=digest(lines[1]),
                       masked_prefix_tokens=12, supervised_prefix_tokens=0,
                       supervised_child_tokens=16, supervised_padding_tokens=0)]))
        write(runtime / "trainer.json", trainer_bytes)
        write(runtime / "adapter/DONE", b"accepted childhood fixture\n")
        self.child_checkpoint = lineage.record_sleep(
            self.child, "sleep_0032", previous_manifest=birth.ancestry.manifest.path,
            previous_sha256=birth.ancestry.manifest.sha256, ledger_path=runtime / "ledger.jsonl",
            corpus_path=runtime / "corpus.json", gate_receipt_path=runtime / "gate.json",
            expected_gate_sha256=digest(gate_bytes), adapter_dir=runtime / "adapter",
            trainer_receipt_path=runtime / "trainer.json", expected_trainer_sha256=digest(trainer_bytes),
            exposure_status="UNEXPOSED", other_influences=[])
        self.life = self.root / "adult"
        self.bundle = self.child / "lineage"
        self.initial_adapter = Path(self.child_checkpoint.adapter_dir)
        self.initial_corpus = self.bundle / "sleep_0032" / "corpus.json"
        self.manifest_path = self.bundle / self.child_checkpoint.ancestry.manifest.path
        self.pin = self.child_checkpoint.ancestry.manifest.sha256
        self.config = dict(arm="B", gym="compiler", seed=9, train_seed=23, rank=8)

    def arguments(self, **overrides):
        return dict(mode="running", startup_config=dict(self.config), lineage_root=self.bundle,
                    manifest_path=self.child_checkpoint.ancestry.manifest.path,
                    expected_manifest_sha256=self.pin, initial_adapter_dir=self.initial_adapter,
                    initial_corpus_path=self.initial_corpus, **overrides)

    def prepare(self, mode="running", life=None, **overrides):
        arguments = self.arguments()
        arguments.update(mode=mode, **overrides)
        return adult.prepare_adult(life or self.life, **arguments)

    def candidate(self, control, checkpoint, text="adult observation"):
        sleep = Path(control.life_dir) / f"sleep_{checkpoint:04d}"
        adapter = sleep / "adapter"
        write(adapter / "adapter_config.json", self.adapter_config)
        write(adapter / "adapter_model.safetensors", f"adult candidate {checkpoint}".encode())
        write(adapter / "train_meta.json", {"seed": 23, "rank": 8})
        write(adapter / "CANDIDATE", b"trained\n")
        write(sleep / "corpus.json", {"corpus": [self.child_item, text]})
        return {"candidate_dir": adapter, "corpus_path": sleep / "corpus.json"}

    def decide(self, control, checkpoint, accepted=True, **arguments):
        key = adult.candidate_key(control, checkpoint, **arguments)
        return adult.record_decision(control, checkpoint, evaluated_key=key,
                                     accepted=accepted, reason="OK" if accepted else "SCORE", **arguments)

    def poison_pinned_corpus(self, items):
        corpus = json.loads(self.initial_corpus.read_bytes())
        corpus["corpus"] = items
        write(self.initial_corpus, corpus)
        gate_path = self.initial_corpus.parent / "gate_receipt.json"
        gate = json.loads(gate_path.read_bytes())
        gate["corpus_sha256"] = digest(self.initial_corpus.read_bytes())
        write(gate_path, gate)
        manifest = json.loads(self.manifest_path.read_bytes())
        manifest["trained_corpus"][0]["sha256"] = gate["corpus_sha256"]
        for artifact in manifest["artifacts"]:
            if artifact["path"].endswith("/gate_receipt.json"):
                artifact["sha256"] = digest(gate_path.read_bytes())
        write(self.manifest_path, manifest)
        self.pin = digest(self.manifest_path.read_bytes())
        guard.validate_manifest(self.child_checkpoint.ancestry.manifest.path,
                                root=self.bundle, expected_sha256=self.pin)

    def test_fresh_inputs_are_bound_and_no_nonweight_context_is_inherited(self):
        before = snapshot(self.child)
        control = self.prepare()
        self.assertEqual(adult.select_adapter(control), str(self.initial_adapter))
        self.assertEqual(adult.initial_prior(control), (self.child_item,))
        self.assertEqual(snapshot(self.child), before)
        self.assertEqual(set(snapshot(self.life)), {"adult_control/startup.json"})
        self.assertFalse((self.life / "sleep_0000").exists())
        self.assertFalse((self.life / "ledger.jsonl").exists())
        self.assertNotIn(self.parent_text, str(adult.initial_prior(control)))
        startup = json.loads(control.startup_json)
        self.assertEqual(startup["nonweight_policy"], adult.NONWEIGHT_POLICY)
        self.assertEqual(startup["manifest_sha256"], self.pin)
        with self.assertRaises(FrozenInstanceError):
            control.mode = "shadow"

    def test_inert_parser_defaults_work_but_explicit_teacher_flags_do_not(self):
        defaults = dict(adult._INACTIVE, parent_model="unused-default-model", **self.config)
        adult.validate_options(defaults, ["--rank", "8", "--train-seed=23"])
        for flags in (["--parent-mode", "brief"], ["--parent-model=unused-default-model"],
                      ["--artifact-lesson=none"], ["--clone-count=1"], ["--artifact", "none"]):
            with self.subTest(flags=flags), self.assertRaises(adult.AdultControlError):
                adult.validate_options(defaults, flags)
        for name, value in (("parent_url", "http://parent"), ("parent_mode", "agentic"),
                            ("artifact_lesson", "sham"), ("clone_group", "/tmp/group"),
                            ("clone_count", 2), ("parent_enabled", False),
                            ("lesson_prompt", "teach"), ("api_key", "secret"), ("arm", "A")):
            with self.subTest(name=name), self.assertRaises(adult.AdultControlError):
                adult.validate_options({**self.config, name: value})

    def test_actual_runner_parser_defaults_and_explicit_train_seed(self):
        from organism_v6 import run_life_v2 as runner

        tree = ast.parse(Path(runner.__file__).read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "main")
        statements = []
        for statement in main.body:
            statements.append(statement)
            if isinstance(statement, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "args"
                    for target in statement.targets):
                break
        else:
            self.fail("runner parser assignment not found")
        parser_only = compile(ast.Module(body=statements, type_ignores=[]), runner.__file__, "exec")
        for mode in ("running", "shadow"):
            for seed in (None, 23):
                life = self.root / f"{mode}_{seed}"
                flags = ["--life-dir", str(life), "--arm", "B", "--rank", "8"]
                if seed is not None:
                    flags.extend(["--train-seed", str(seed)])
                namespace = dict(vars(runner))
                with patch.object(sys, "argv", [runner.__file__, *flags]):
                    exec(parser_only, namespace)
                config = vars(namespace["args"])
                with self.subTest(mode=mode, seed=seed):
                    control = self.prepare(mode=mode, life=life, startup_config=config,
                                           explicit_flags=flags)
                    self.assertEqual(config["train_seed"], seed)
                    self.assertEqual(adult.select_adapter(control), str(self.initial_adapter))
                    self.assertEqual(self.prepare(mode=mode, life=life, startup_config=config,
                                                  explicit_flags=flags, resume=True), control)

    def test_actual_runner_staging_is_compatible_in_both_modes(self):
        from organism_v6 import run_life_v2 as runner

        before = snapshot(self.child)
        for mode in ("running", "shadow"):
            control = self.prepare(mode=mode, life=self.root / mode)
            arguments = self.candidate(control, 32)
            raw = arguments["candidate_dir"]
            stage = raw.with_name("adapter.train")
            raw.rename(stage)
            (stage / "CANDIDATE").rename(stage / "DONE")
            runner.promote_trained_adapter(str(stage), str(raw))
            runner.validate_adapter_states(control.life_dir)
            with self.subTest(mode=mode):
                decision = self.decide(control, 32, **arguments)
                self.assertIsNone(runner.existing_adapter_verdict(str(raw)))
                self.assertEqual(adult.get_decision(control, 32), decision)
                self.assertTrue((raw / "CANDIDATE").exists())
                self.assertFalse((raw / "DONE").exists())
                self.assertEqual(adult.select_adapter(control), decision.promoted_adapter
                                 if mode == "running" else str(self.initial_adapter))
                runner.validate_adapter_states(control.life_dir)
        self.assertEqual(snapshot(self.child), before)

    def test_actual_compiler_accepts_initial_prior_without_reading_briefs(self):
        from organism_v6 import sleep_compile

        for mode in ("running", "shadow"):
            control = self.prepare(mode=mode, life=self.root / mode)
            sleep = Path(control.life_dir) / "sleep_0032"
            with patch.object(sleep_compile, "select", return_value={}), \
                    patch.object(sleep_compile, "transform", return_value=dict(
                        exemplars=["adult-generated exemplar"], principles=[], brief="NOT_WAKE_CONTEXT")):
                result = sleep_compile.compile_sleep(None, [], str(sleep), list(adult.initial_prior(control)))
            with self.subTest(mode=mode):
                self.assertIn(self.child_item, result["corpus"])
                self.assertEqual(adult.wake_context(control, "Task instructions."), "Task instructions.")
                self.assertNotIn("recipe", json.loads((sleep / "corpus.json").read_bytes()))

    def test_candidates_cannot_drop_or_rewrite_initial_corpus(self):
        for mode in ("running", "shadow"):
            control = self.prepare(mode=mode, life=self.root / mode)
            arguments = self.candidate(control, 32)
            for items in (["adult observation only"], [self.child_item + " changed", "adult observation"]):
                write(arguments["corpus_path"], {"corpus": items})
                with self.subTest(mode=mode, items=items), self.assertRaisesRegex(
                        adult.AdultControlError, "retain the pinned initial child corpus"):
                    adult.candidate_key(control, 32, **arguments)

    def test_unknown_modes_and_missing_external_pins_reject(self):
        for mode in ("other", None):
            with self.subTest(mode=mode), self.assertRaises(adult.AdultControlError):
                self.prepare(mode=mode)
        for pin in (None, "", "0" * 64):
            with self.subTest(pin=pin), self.assertRaises(adult.AdultControlError):
                self.prepare(expected_manifest_sha256=pin)
        self.assertFalse(self.life.exists())

    def test_startup_types_and_runtime_directory_agree(self):
        for name, value in (("seed", True), ("train_seed", 23.0), ("rank", -1)):
            with self.subTest(name=name), self.assertRaises(adult.AdultControlError):
                self.prepare(startup_config={**self.config, name: value})
        with self.assertRaisesRegex(adult.AdultControlError, "directory differs"):
            self.prepare(startup_config={**self.config, "life_dir": str(self.root / "other")})
        with self.assertRaises(adult.AdultControlError):
            self.prepare(resume="false")
        with self.assertRaises(adult.AdultControlError):
            self.prepare(explicit_flags="--parent-mode=brief")

    def test_pinned_local_base_and_fixed_model_id_are_compatible(self):
        path = self.initial_adapter / "adapter_config.json"
        model_dir = str(self.bundle / "birth" / "model")
        write(path, {**self.adapter_config, "base_model_name_or_path": model_dir})
        trainer_path = self.initial_corpus.parent / "trainer_receipt.json"
        trainer = json.loads(trainer_path.read_bytes())
        trainer["adapter_files"]["adapter_config.json"] = digest(path.read_bytes())
        write(trainer_path, trainer)
        manifest = json.loads(self.manifest_path.read_bytes())
        for artifact in manifest["artifacts"]:
            if artifact["path"].endswith("/adapter_config.json"):
                artifact["sha256"] = digest(path.read_bytes())
            elif artifact["path"].endswith("/trainer_receipt.json"):
                artifact["sha256"] = digest(trainer_path.read_bytes())
        write(self.manifest_path, manifest)
        self.pin = digest(self.manifest_path.read_bytes())
        control = self.prepare()
        self.assertEqual(control.model_dir, model_dir)
        arguments = self.candidate(control, 8)
        self.decide(control, 8, **arguments)
        self.assertNotEqual(adult.select_adapter(control), control.initial_adapter)

    def test_actual_config_weights_and_corpus_must_match_pinned_artifacts(self):
        for filename in ("adapter_model.safetensors", "adapter_config.json"):
            path = self.initial_adapter / filename
            original = path.read_bytes()
            changed = b"different weights" if filename.endswith("safetensors") else encoded({
                **self.adapter_config, "r": 16})
            write(path, changed)
            with self.subTest(filename=filename), self.assertRaises(adult.AdultControlError):
                self.prepare()
            write(path, original)
        copied = self.root / "unbound_corpus.json"
        write(copied, {"corpus": ["unbound"]})
        with self.assertRaisesRegex(adult.AdultControlError, "corpus pin"):
            self.prepare(initial_corpus_path=copied)

    def test_structurally_pinned_parent_or_fabricated_corpus_is_not_child_prior(self):
        for items in ([self.parent_text], ["invented unsourced text"], [{"speaker": "parent"}]):
            self.poison_pinned_corpus(items)
            with self.subTest(items=items), self.assertRaises(adult.AdultControlError):
                self.prepare()
        self.assertFalse(self.life.exists())

    def test_wrong_child_record_speaker_rejected_even_with_consistent_hashes(self):
        ledger_path = self.initial_corpus.parent / "ledger.jsonl"
        lines = ledger_path.read_bytes().splitlines(keepends=True)
        row = json.loads(lines[2])
        row["speaker"] = "parent"
        old_line_hash = digest(lines[2])
        old_ledger_hash = digest(b"".join(lines))
        lines[2] = encoded(row)
        write(ledger_path, b"".join(lines))
        row_path = self.initial_corpus.parent / "row_00000002.jsonl"
        write(row_path, lines[2])
        gate_path = self.initial_corpus.parent / "gate_receipt.json"
        gate = json.loads(gate_path.read_bytes())
        gate["ledger_sha256"] = digest(b"".join(lines))
        gate["admissions"][0]["record_sha256"] = digest(lines[2])
        write(gate_path, gate)
        replaced = {old_ledger_hash: gate["ledger_sha256"], old_line_hash: digest(lines[2])}
        manifest = json.loads(self.manifest_path.read_bytes())
        for source in manifest["sources"]:
            source["sha256"] = replaced.get(source["sha256"], source["sha256"])
        for record in manifest["artifacts"] + manifest["trained_corpus"]:
            record["source_sha256"] = [replaced.get(value, value) for value in record["source_sha256"]]
            if record["path"].endswith("/gate_receipt.json"):
                record["sha256"] = digest(gate_path.read_bytes())
        write(self.manifest_path, manifest)
        self.pin = digest(self.manifest_path.read_bytes())
        guard.validate_manifest(self.child_checkpoint.ancestry.manifest.path, root=self.bundle,
                                expected_sha256=self.pin)
        with self.assertRaisesRegex(adult.AdultControlError, "child-authored"):
            self.prepare()

    def test_initial_trainer_evidence_must_be_bound_and_child_only(self):
        path = self.initial_corpus.parent / "trainer_receipt.json"
        original = json.loads(path.read_bytes())
        for field, value in (("supervised_prefix_tokens", 1), ("supervised_padding_tokens", 1),
                             ("supervised_child_tokens", 0)):
            trainer = json.loads(encoded(original))
            trainer["rows"][0][field] = value
            write(path, trainer)
            manifest = json.loads(self.manifest_path.read_bytes())
            for artifact in manifest["artifacts"]:
                if artifact["path"].endswith("/trainer_receipt.json"):
                    artifact["sha256"] = digest(path.read_bytes())
            write(self.manifest_path, manifest)
            self.pin = digest(self.manifest_path.read_bytes())
            with self.subTest(field=field), self.assertRaisesRegex(adult.AdultControlError, "trainer receipt"):
                self.prepare()
        manifest["artifacts"] = [artifact for artifact in manifest["artifacts"]
                                 if not artifact["path"].endswith("/trainer_receipt.json")]
        write(self.manifest_path, manifest)
        self.pin = digest(self.manifest_path.read_bytes())
        with self.assertRaisesRegex(adult.AdultControlError, "trainer snapshots"):
            self.prepare()

    def test_initial_native_metadata_cannot_be_relabelled_or_unbound(self):
        path = self.initial_adapter / "train_meta.json"
        original_metadata = json.loads(path.read_bytes())
        trainer_path = self.initial_corpus.parent / "trainer_receipt.json"
        original_trainer = json.loads(trainer_path.read_bytes())
        original_manifest = json.loads(self.manifest_path.read_bytes())
        for field, value in (("loss_target", "all_tokens"), ("source_corpus_sha256", "0" * 64),
                             ("supervised_tokens", 49)):
            write(path, {**original_metadata, field: value})
            write(trainer_path, {**original_trainer, "train_metadata_sha256": digest(path.read_bytes())})
            manifest = json.loads(encoded(original_manifest))
            for artifact in manifest["artifacts"]:
                if artifact["path"].endswith("/train_meta.json"):
                    artifact["sha256"] = digest(path.read_bytes())
                elif artifact["path"].endswith("/trainer_receipt.json"):
                    artifact["sha256"] = digest(trainer_path.read_bytes())
            write(self.manifest_path, manifest)
            self.pin = digest(self.manifest_path.read_bytes())
            guard.validate_manifest(self.child_checkpoint.ancestry.manifest.path,
                                    root=self.bundle, expected_sha256=self.pin)
            with self.subTest(field=field), self.assertRaises(adult.AdultControlError):
                self.prepare()
        manifest["artifacts"] = [artifact for artifact in manifest["artifacts"]
                                 if not artifact["path"].endswith("/train_meta.json")]
        write(self.manifest_path, manifest)
        self.pin = digest(self.manifest_path.read_bytes())
        with self.assertRaisesRegex(adult.AdultControlError, "trainer snapshots"):
            self.prepare()

    def test_clean_entry_cannot_hide_invalid_training_in_an_ancestor(self):
        runtime = self.root / "runtime"
        gate = json.loads((runtime / "gate.json").read_bytes())
        gate["previous_manifest_sha256"] = self.pin
        write(runtime / "gate.json", gate)
        trainer = json.loads((runtime / "trainer.json").read_bytes())
        trainer.update(previous_manifest_sha256=self.pin,
                       gate_receipt_sha256=digest((runtime / "gate.json").read_bytes()))
        write(runtime / "trainer.json", trainer)
        later = lineage.record_sleep(
            self.child, "sleep_0064", previous_manifest=self.child_checkpoint.ancestry.manifest.path,
            previous_sha256=self.pin, ledger_path=runtime / "ledger.jsonl",
            corpus_path=runtime / "corpus.json", gate_receipt_path=runtime / "gate.json",
            expected_gate_sha256=digest((runtime / "gate.json").read_bytes()),
            trainer_receipt_path=runtime / "trainer.json",
            expected_trainer_sha256=digest((runtime / "trainer.json").read_bytes()),
            adapter_dir=runtime / "adapter", exposure_status="UNEXPOSED", other_influences=[])
        ancestor_receipt = self.initial_corpus.parent / "trainer_receipt.json"
        poisoned = json.loads(ancestor_receipt.read_bytes())
        poisoned["rows"][0]["supervised_prefix_tokens"] = 1
        write(ancestor_receipt, poisoned)
        ancestor = json.loads(self.manifest_path.read_bytes())
        for artifact in ancestor["artifacts"]:
            if artifact["path"].endswith("/trainer_receipt.json"):
                artifact["sha256"] = digest(ancestor_receipt.read_bytes())
        write(self.manifest_path, ancestor)
        ancestor_pin = digest(self.manifest_path.read_bytes())
        later_directory = self.bundle / "sleep_0064"
        gate["previous_manifest_sha256"] = ancestor_pin
        write(later_directory / "gate_receipt.json", gate)
        trainer.update(previous_manifest_sha256=ancestor_pin,
                       gate_receipt_sha256=digest((later_directory / "gate_receipt.json").read_bytes()))
        write(later_directory / "trainer_receipt.json", trainer)
        later_manifest = json.loads((later_directory / "manifest.json").read_bytes())
        later_manifest["parents"][0]["sha256"] = ancestor_pin
        for artifact in later_manifest["artifacts"]:
            artifact["sha256"] = digest((self.bundle / artifact["path"]).read_bytes())
        write(later_directory / "manifest.json", later_manifest)
        later_pin = digest((later_directory / "manifest.json").read_bytes())
        guard.validate_manifest(later.ancestry.manifest.path, root=self.bundle, expected_sha256=later_pin)
        with self.assertRaisesRegex(adult.AdultControlError, "trainer receipt supervises"):
            self.prepare(manifest_path=later.ancestry.manifest.path,
                         expected_manifest_sha256=later_pin, initial_adapter_dir=later.adapter_dir,
                         initial_corpus_path=later_directory / "corpus.json")
        self.assertFalse(self.life.exists())

    def test_no_populated_birth_or_implicit_resume(self):
        self.life.mkdir()
        write(self.life / "ledger.jsonl", b"old childhood note\n")
        before = snapshot(self.life)
        with self.assertRaisesRegex(adult.AdultControlError, "empty"):
            self.prepare()
        self.assertEqual(snapshot(self.life), before)
        other = self.root / "fresh_adult"
        self.prepare(life=other)
        before = snapshot(other)
        with self.assertRaisesRegex(adult.AdultControlError, "empty"):
            self.prepare(life=other)
        self.assertEqual(snapshot(other), before)

    def test_exact_resume_and_startup_freeze(self):
        options = dict(self.config)
        control = self.prepare(startup_config=options)
        options["seed"] = 100
        self.assertEqual(json.loads(control.startup_json)["config"]["seed"], 9)
        write(self.life / "ledger.jsonl", b"adult-authored ledger\n")
        self.assertEqual(self.prepare(resume=True), control)
        before = snapshot(self.life)
        for change in ({"seed": 100}, {"train_seed": 24}, {"rank": 16}, {"gym": "other"}):
            with self.subTest(change=change), self.assertRaises(adult.AdultControlError):
                self.prepare(resume=True, startup_config={**self.config, **change})
        with self.assertRaises(adult.AdultControlError):
            self.prepare(mode="shadow", resume=True)
        self.assertEqual(snapshot(self.life), before)

    def test_startup_tampering_and_partial_startup_fail_closed(self):
        control = self.prepare()
        startup = self.life / "adult_control" / "startup.json"
        write(startup, {"mode": "shadow"})
        with self.assertRaises(adult.AdultControlError):
            adult.select_adapter(control)
        with self.assertRaises(adult.AdultControlError):
            self.prepare(resume=True)
        partial = self.root / "partial"
        (partial / "adult_control" / "decisions").mkdir(parents=True)
        with self.assertRaises(adult.AdultControlError):
            self.prepare(life=partial, resume=True)
        self.assertFalse((partial / "adult_control" / "startup.json").exists())

    def test_file_backed_startup_configuration_is_frozen_by_bytes(self):
        panel = self.root / "gate_panel.json"
        write(panel, {"panel": ["heldout/example"]})
        options = {**self.config, "gate_panel": str(panel)}
        control = self.prepare(startup_config=options)
        self.assertEqual(self.prepare(resume=True, startup_config=options), control)
        write(panel, {"panel": ["different/example"]})
        with self.assertRaisesRegex(adult.AdultControlError, "input/evidence cache"):
            adult.select_adapter(control)
        with self.assertRaisesRegex(adult.AdultControlError, "startup config/cache"):
            self.prepare(resume=True, startup_config=options)

    def test_changed_cached_initial_inputs_and_extra_runtime_weights_reject(self):
        control = self.prepare()
        write(self.initial_adapter / "adapter_model.bin", b"unbound competing weights")
        with self.assertRaises(adult.AdultControlError):
            adult.select_adapter(control)
        (self.initial_adapter / "adapter_model.bin").unlink()
        write(self.initial_corpus, {"corpus": ["changed"]})
        with self.assertRaises(adult.AdultControlError):
            adult.initial_prior(control)
        with self.assertRaises(adult.AdultControlError):
            adult.select_adapter(control)

    def test_pinned_base_runtime_changes_are_not_silently_loaded(self):
        control = self.prepare()
        extra = Path(control.model_dir) / "pytorch_model.bin"
        write(extra, b"unbound base weights")
        with self.assertRaisesRegex(adult.AdultControlError, "base runtime inventory"):
            adult.select_adapter(control)
        extra.unlink()
        write(Path(control.model_dir) / "model.safetensors", b"changed base weights")
        with self.assertRaisesRegex(adult.AdultControlError, "input/evidence cache"):
            adult.select_adapter(control)

    def test_symlink_inputs_and_outputs_reject(self):
        alias = self.root / "corpus_alias.json"
        alias.symlink_to(self.initial_corpus)
        with self.assertRaises(adult.AdultControlError):
            self.prepare(initial_corpus_path=alias)
        directory_alias = self.root / "adapter_alias"
        directory_alias.symlink_to(self.initial_adapter, target_is_directory=True)
        with self.assertRaises(adult.AdultControlError):
            self.prepare(initial_adapter_dir=directory_alias)
        target = self.root / "output_target"
        target.mkdir()
        self.life.symlink_to(target, target_is_directory=True)
        with self.assertRaises(adult.AdultControlError):
            self.prepare()
        self.assertEqual(list(target.iterdir()), [])

    def test_running_selects_latest_numeric_promotion_and_preserves_initial(self):
        before = snapshot(self.child)
        control = self.prepare()
        first_args = self.candidate(control, 8)
        first = self.decide(control, 8, **first_args)
        self.assertIsNotNone(first.promoted_adapter)
        self.assertEqual(adult.select_adapter(control), first.promoted_adapter)
        self.assertTrue((Path(first.promoted_adapter) / "DONE").exists())
        self.assertFalse((first_args["candidate_dir"] / "DONE").exists())
        self.assertTrue((first_args["candidate_dir"] / "CANDIDATE").exists())
        rejected = self.decide(control, 16, False, **self.candidate(control, 16))
        self.assertIsNone(rejected.promoted_adapter)
        self.assertEqual(adult.select_adapter(control), first.promoted_adapter)
        last = self.decide(control, 10000, **self.candidate(control, 10000))
        self.assertEqual(adult.select_adapter(control), last.promoted_adapter)
        self.assertEqual(snapshot(self.child), before)
        self.assertEqual(self.prepare(resume=True), control)

    def test_shadow_records_accept_and_reject_but_never_promotes_or_selects_candidate(self):
        control = self.prepare(mode="shadow")
        for checkpoint, accepted in ((8, True), (16, False)):
            arguments = self.candidate(control, checkpoint)
            decision = self.decide(control, checkpoint, accepted, **arguments)
            self.assertEqual(decision.accepted, accepted)
            self.assertIsNone(decision.promoted_adapter)
            self.assertEqual(adult.select_adapter(control), str(self.initial_adapter))
            self.assertEqual(adult.get_decision(control, checkpoint), decision)
        self.assertFalse(list(self.life.rglob("DONE")))
        self.assertEqual(adult.initial_prior(control), (self.child_item,))
        self.assertEqual(self.prepare(mode="shadow", resume=True), control)

    def test_rejected_running_candidate_leaves_initial_mounted(self):
        control = self.prepare()
        self.decide(control, 8, False, **self.candidate(control, 8))
        self.assertEqual(adult.select_adapter(control), str(self.initial_adapter))
        self.assertFalse(list(self.life.rglob("DONE")))

    def test_same_decision_is_read_only_idempotent_and_conflicts_reject(self):
        control = self.prepare()
        arguments = self.candidate(control, 8)
        decision = self.decide(control, 8, **arguments)
        before = snapshot(self.life)
        self.assertEqual(self.decide(control, 8, **arguments), decision)
        with self.assertRaisesRegex(adult.AdultControlError, "conflicting"):
            self.decide(control, 8, False, **arguments)
        self.assertEqual(snapshot(self.life), before)
        self.assertIsNone(adult.get_decision(control, 16))

    def test_stale_gate_keys_bind_weights_config_corpus_and_training_metadata(self):
        control = self.prepare(mode="shadow")
        for checkpoint, name in ((8, "adapter_model.safetensors"), (16, "adapter_config.json"),
                                 (24, "train_meta.json"), (32, "corpus.json")):
            arguments = self.candidate(control, checkpoint)
            key = adult.candidate_key(control, checkpoint, **arguments)
            path = arguments["corpus_path"] if name == "corpus.json" else arguments["candidate_dir"] / name
            if name == "adapter_model.safetensors":
                write(path, b"new unexamined weights")
            else:
                value = json.loads(path.read_bytes())
                value["changed"] = True
                write(path, value)
            with self.subTest(name=name), self.assertRaisesRegex(adult.AdultControlError, "stale gate cache"):
                adult.record_decision(control, checkpoint, evaluated_key=key,
                                      accepted=True, reason="OK", **arguments)
        self.assertEqual(list((self.life / "adult_control" / "decisions").iterdir()), [])

    def test_gate_key_includes_prior_decisions_and_control_mode(self):
        control = self.prepare()
        second = self.candidate(control, 16)
        stale = adult.candidate_key(control, 16, **second)
        self.decide(control, 8, **self.candidate(control, 8))
        with self.assertRaisesRegex(adult.AdultControlError, "stale gate cache"):
            adult.record_decision(control, 16, evaluated_key=stale, accepted=True, reason="OK", **second)
        other = self.prepare(mode="shadow", life=self.root / "shadow")
        candidate = self.candidate(other, 8)
        with self.assertRaisesRegex(adult.AdultControlError, "stale gate cache"):
            adult.record_decision(other, 8, evaluated_key=adult.get_decision(control, 8).candidate_key,
                                  accepted=True, reason="OK", **candidate)

    def test_wrong_checkpoint_and_out_of_order_decisions_reject(self):
        control = self.prepare()
        arguments = self.candidate(control, 16)
        for checkpoint in (0, -1, True, "16", 8):
            with self.subTest(checkpoint=checkpoint), self.assertRaises(adult.AdultControlError):
                adult.candidate_key(control, checkpoint, **arguments)
        self.decide(control, 16, **arguments)
        with self.assertRaisesRegex(adult.AdultControlError, "out-of-order"):
            self.decide(control, 8, **self.candidate(control, 8))

    def test_candidate_seed_rank_and_base_match_frozen_startup(self):
        control = self.prepare()
        arguments = self.candidate(control, 8)
        for field, value in (("r", 16), ("base_model_name_or_path", "other/base"), ("peft_type", "OTHER")):
            write(arguments["candidate_dir"] / "adapter_config.json", {**self.adapter_config, field: value})
            with self.subTest(field=field), self.assertRaises(adult.AdultControlError):
                adult.candidate_key(control, 8, **arguments)
        write(arguments["candidate_dir"] / "adapter_config.json", self.adapter_config)
        for value in ({}, {"seed": 24}, {"seed": True}):
            write(arguments["candidate_dir"] / "train_meta.json", value)
            with self.subTest(value=value), self.assertRaisesRegex(adult.AdultControlError, "seed"):
                adult.candidate_key(control, 8, **arguments)

    def test_unexpected_decision_types_or_reasons_fail_closed(self):
        control = self.prepare(mode="shadow")
        arguments = self.candidate(control, 8)
        key = adult.candidate_key(control, 8, **arguments)
        for accepted, reason in ((1, "OK"), (True, "SCORE"), (False, "OK"),
                                 (True, {"candidate": 0.123}), (False, "SCORE 0.123")):
            with self.subTest(accepted=accepted, reason=reason), self.assertRaises(adult.AdultControlError):
                adult.record_decision(control, 8, evaluated_key=key,
                                      accepted=accepted, reason=reason, **arguments)
        self.assertEqual(list((self.life / "adult_control" / "decisions").iterdir()), [])

    def test_rogue_done_and_sleep_zero_are_never_selected(self):
        control = self.prepare(mode="shadow")
        arguments = self.candidate(control, 8)
        write(arguments["candidate_dir"] / "DONE", b"rogue\n")
        with self.assertRaisesRegex(adult.AdultControlError, "cannot be DONE"):
            adult.select_adapter(control)
        (arguments["candidate_dir"] / "DONE").unlink()
        (self.life / "sleep_0000").mkdir()
        with self.assertRaisesRegex(adult.AdultControlError, "sleep_0000"):
            adult.select_adapter(control)

    def test_completed_candidate_or_promotion_tampering_is_not_a_cache_hit(self):
        control = self.prepare()
        arguments = self.candidate(control, 8)
        decision = self.decide(control, 8, **arguments)
        promoted = Path(decision.promoted_adapter) / "adapter_model.safetensors"
        original = promoted.read_bytes()
        write(promoted, b"tampered promotion")
        with self.assertRaisesRegex(adult.AdultControlError, "promoted adapter changed"):
            adult.select_adapter(control)
        write(promoted, original)
        write(arguments["candidate_dir"] / "adapter_model.safetensors", b"tampered source candidate")
        with self.assertRaisesRegex(adult.AdultControlError, "stale candidate"):
            adult.get_decision(control, 8)

    def test_shadow_promotion_tampering_and_extra_output_reject(self):
        control = self.prepare(mode="shadow")
        self.decide(control, 8, **self.candidate(control, 8))
        destination = self.life / "adult_control" / "decisions" / "sleep_0008"
        path = destination / "decision.json"
        record = json.loads(path.read_bytes())
        write(path, {**record, "promoted": True})
        with self.assertRaisesRegex(adult.AdultControlError, "cannot promote"):
            adult.select_adapter(control)
        write(path, record)
        write(destination / "DONE", b"rogue\n")
        with self.assertRaises(adult.AdultControlError):
            adult.select_adapter(control)

    def test_partial_promotion_is_preserved_and_never_resumed_as_success(self):
        control = self.prepare()
        arguments = self.candidate(control, 8)
        key = adult.candidate_key(control, 8, **arguments)
        with patch.object(lineage, "_copy", side_effect=OSError("interrupted copy")):
            with self.assertRaisesRegex(adult.AdultControlError, "interrupted"):
                adult.record_decision(control, 8, evaluated_key=key, accepted=True, reason="OK", **arguments)
        destination = self.life / "adult_control" / "decisions" / "sleep_0008"
        self.assertTrue(destination.is_dir())
        self.assertFalse((destination / "decision.json").exists())
        with self.assertRaises(adult.AdultControlError):
            adult.select_adapter(control)
        with self.assertRaises(adult.AdultControlError):
            self.prepare(resume=True)
        with self.assertRaises(adult.AdultControlError):
            self.decide(control, 8, **arguments)
        self.assertTrue(destination.is_dir())

    def test_parent_and_waking_briefs_are_never_opened_for_adult_context(self):
        control = self.prepare()
        write(self.life / "sleep_0008" / "parent_brief.txt", b"PARENT_CONTEXT_LEAK")
        write(self.life / "sleep_0008" / "waking_brief.txt", b"WAKING_CONTEXT_LEAK")
        with patch("builtins.open", side_effect=AssertionError("context must not read files")), \
                patch.object(lineage, "_read", side_effect=AssertionError("context must not read files")):
            self.assertEqual(adult.wake_context(control, "Adult task instructions."), "Adult task instructions.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
