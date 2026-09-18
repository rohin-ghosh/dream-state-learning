"""Synthetic captured-root tests; no model, package, historical path or GPU access."""
import itertools
import json
from pathlib import Path
import unittest
import zlib

from organism_v6 import mini_sudoku_behavior_run_audit as audit
from organism_v6 import neutral_pair_custody as custody
import test_mini_sudoku_behavior_analysis as analysis_tests


class RunAuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = analysis_tests.BehaviorAnalysisTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root / "captured"
        (self.root / "probes").mkdir(parents=True)
        self.fixture.useful.rename(self.root / "probes/useful")
        self.fixture.corrupt.rename(self.root / "probes/corrupt")
        self.material = self.root / "material"
        self.material.mkdir()
        choices = list(itertools.permutations((1, 2, 3, 4)))
        boards = [board for board in itertools.product(choices, repeat=4)
                  if all(len({board[row][column] for row in range(4)}) == 4 for column in range(4))
                  and all(len({board[row][column] for row in range(top, top+2) for column in range(left, left+2)}) == 4
                          for top in (0, 2) for left in (0, 2))][:48]
        records = []
        for episode_id, board in zip(audit.TRAIN_IDS + audit.reducer.EPISODE_IDS, boards):
            puzzle = list(map(list, board))
            answer = "\n".join(" ".join(map(str, row)) for row in board)
            entry = dict(question="Puzzle:\n" + answer, answer=answer,
                         metadata=dict(puzzle=puzzle, solution=puzzle, num_empty=0))
            prompt = "Native fixture\n" + entry["question"] + "\nCLOCK: chunk 1/1 | alive 0s\n"
            record = dict(episode_id=episode_id, puzzle=puzzle, solution=puzzle, entry=entry,
                          q=prompt, rendered_q="CHAT:" + prompt, a="ACT: " + answer.replace("\n", " ; "))
            record.update(board_sha256=audit._sha(audit._encoded(puzzle)), entry_sha256=audit._sha(audit._encoded(entry)),
                          q_sha256=audit._sha(prompt.encode()), rendered_q_sha256=audit._sha(record["rendered_q"].encode()))
            records.append(record)
        self.records = records
        self.write(self.material / "oracle_sources.json", dict(records=records))
        self.write(self.material / "ids.json", dict(train=list(audit.TRAIN_IDS), canary=list(audit.reducer.EPISODE_IDS)))
        self.pins = dict(model_path="/remote/model", files={"config.json": "a" * 64}, origin="UNRESOLVED")
        self.write(self.material / "local_pins.json", self.pins)
        self.write(self.material / "source_hashes.json", {"/absent/historical/source.py": "e" * 64})
        tokens = [dict(target_tokens=38, input_tokens=800) for _ in range(32)]
        self.write(self.material / "validation.json", dict(useful_tokens=tokens, corrupt_tokens=tokens))
        commands = {}
        for arm in ("useful", "corrupt"):
            corpus = []
            for index, record in enumerate(records[:32]):
                donor = records[index if arm == "useful" else (index+1) % 32]
                corpus.append(dict(episode_id=record["episode_id"], q=record["q"], rendered_q=record["rendered_q"],
                                   a=donor["a"], spans=[[record["rendered_q"], False, "native_context"],
                                                       [donor["a"], True, "external_oracle_action"]]))
            self.write(self.material / f"{arm}.json", dict(corpus=corpus))
            commands[arm] = dict(argv=["/missing/venv/python", "-m", "organism_v6.train_adapter_v3", "--out",
                f"/remote/run/training/{arm}_seed0", "--corpus", f"/remote/run/material/{arm}.json",
                "--model", "/remote/model", "--rank", "8", "--lr", "0.0001", "--epochs", "3", "--seed", "0",
                "--batch-size", "1", "--grad-accum", "1", "--max-len", "4096", "--no-pack"], expected_steps=96)
        self.write(self.material / "trainer_commands.json", dict(commands=commands))
        self.seal_material()
        for arm in ("useful", "corrupt"):
            self.make_fit_and_probe(arm)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audit._encoded(value))

    def read(self, path):
        return json.loads(path.read_text())

    def seal_material(self):
        self.write(self.material / "manifest.json", dict(status="PREPARED", files={
            path.name: custody._digest(path) for path in self.material.iterdir() if path.name != "manifest.json"}))

    def make_fit_and_probe(self, arm, training_seed=0):
        directory = self.root / "training" / f"{arm}_seed{training_seed}"
        config = dict(rank=8, alpha=0, lr=0.0001, epochs=3, seed=training_seed, batch_size=1, grad_accum=1,
                      max_len=4096, pack=False, chat_template=False, model="/remote/model")
        manifest = dict(corpus=dict(sha256=custody._digest(self.material / f"{arm}.json"),
                                   file=f"{arm}.json", n_items=32),
                        config=config, base_model="/remote/model", steps=96, nonfinite_batches=0, final_loss=0.5,
                        train_tokens_seen=76800, tokens=dict(target=1216), truncation={
                            field: 0 for field in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")})
        self.write(directory / "train_manifest.json", manifest)
        self.write(directory / "train_meta.json", dict(rank=8, lr=0.0001, epochs=3, seed=training_seed, steps=96,
                                                       n_texts=32, tokens=76800, final_loss=0.5))
        self.write(directory / "adapter_config.json", dict(r=8, lora_alpha=16, base_model_name_or_path="/remote/model"))
        (directory / "DONE").write_text("ok\n")
        inventory = {path.name: custody._digest(path) for path in directory.iterdir()}
        inventory["adapter_model.safetensors"] = "b" * 64
        spec = dict(adapter_path=f"/remote/run/training/{arm}_seed{training_seed}", model_path="/remote/model",
                    expected_model_hashes=self.pins["files"], expected_adapter_hashes=inventory,
                    episode_ids=list(audit.reducer.EPISODE_IDS))
        pair = self.root / "probes" / arm
        for condition in ("off", "on"):
            cell = pair / condition
            probe = self.read(cell / "configuration.json")
            probe["source_identity"]["model_input"] = probe["sources"]["model"] = "/remote/model"
            if condition == "on":
                probe["source_identity"]["adapter_input"] = probe["sources"]["adapter"] = spec["adapter_path"]
                probe["source_identity"]["adapter_files"] = {name: inventory[name] for name in
                                                           ("adapter_config.json", "adapter_model.safetensors")}
                probe["hashes_before"]["adapter"] = inventory
            self.write(cell / "configuration.json", probe)
            self.write(cell / "source_check.json", dict(evidence_label="EVALUATION_ONLY",
                       hashes_after=probe["hashes_before"], code_hashes_after=probe["code_hashes_before"]))
            spec.update({field: probe[field] for field in audit.BUDGET_FIELDS})
            requests = [dict(kind="generation_request", request_index=index, prompts=[record["q"]],
                        seeds=[(zlib.crc32(f'{record["episode_id"]}/1'.encode()) ^ spec["gen_seed"]) & 0x7fffffff],
                        max_tokens=400, temperature=0.7, source_identity=probe["source_identity"])
                        for index, record in enumerate(self.records[32:])]
            (cell / "generations.jsonl").write_text("".join(json.dumps(row)+"\n" for row in requests))
        spec_path = self.root / "logs" / arm / "probe_spec.json"
        self.write(spec_path, spec)
        self.seal_probe(arm)

    def seal_probe(self, arm):
        pair = self.root / "probes" / arm
        spec_path = self.root / "logs" / arm / "probe_spec.json"
        spec = self.read(spec_path)
        self.fixture.seal(pair)
        done = self.read(pair / "PAIR_DONE.json")
        done["spec_sha256"] = custody._digest(spec_path)
        for condition in ("off", "on"):
            receipt_path = pair / f"{condition}_WORKER_DONE.json"
            receipt = self.read(receipt_path)
            receipt["spec_sha256"] = done["spec_sha256"]
            self.write(receipt_path, receipt)
            done["workers"][condition] = receipt
            done["receipt_sha256"][condition] = custody._digest(receipt_path)
        self.write(pair / "PAIR_DONE.json", done)
        self.write(pair / "PAIR_STARTED.json", dict(spec=spec, spec_sha256=done["spec_sha256"], source_snapshot=done["source_snapshot"]))

    def test_full_offline_binding_and_missing_weights_labeled(self):
        report = audit.audit_run(self.root)
        self.assertEqual(report["training_seed"], 0)
        self.assertEqual(report["independent_material"]["unique_reference_completions"], 48)
        self.assertEqual(report["prompt_mismatch_count"], 0)
        self.assertEqual(len(report["prompt_checks"]), 64)
        self.assertEqual(report["arms"]["useful"]["weight_verification"], "REMOTE_WEIGHT_HASH_NOT_REHASHED_LOCALLY")
        self.assertEqual(report["arms"]["useful"]["original_labels"]["PAIR_DONE"]["evidence_label"], "EVALUATION_ONLY")

    def prepare_replication(self, training_seed):
        path = self.material / "validation.json"
        validation = self.read(path)
        validation["training_seed"] = training_seed
        self.write(path, validation)
        path = self.material / "trainer_commands.json"
        commands = self.read(path)
        for arm in ("useful", "corrupt"):
            argv = commands["commands"][arm]["argv"]
            argv[argv.index("--out") + 1] = f"/remote/run/training/{arm}_seed{training_seed}"
            argv[argv.index("--seed") + 1] = str(training_seed)
        self.write(path, commands)
        self.seal_material()
        for arm in ("useful", "corrupt"):
            self.make_fit_and_probe(arm, training_seed)

    def test_replication_seeds_one_and_two(self):
        generation_seed = self.read(self.root / "logs/useful/probe_spec.json")["gen_seed"]
        for training_seed in (1, 2):
            with self.subTest(training_seed=training_seed):
                self.prepare_replication(training_seed)
                report = audit.audit_run(self.root)
                self.assertEqual(report["training_seed"], training_seed)
                self.assertEqual(report["shared_budgets"]["gen_seed"], generation_seed)
                for arm in ("useful", "corrupt"):
                    self.assertEqual(report["arms"][arm]["train_meta"]["seed"], training_seed)

    def test_material_seed_requires_matching_paths(self):
        path = self.material / "validation.json"
        validation = self.read(path)
        validation["training_seed"] = 1
        self.write(path, validation)
        self.seal_material()
        with self.assertRaisesRegex(ValueError, "wrong arm adapter destination"):
            audit.audit_run(self.root)

    def test_each_arm_metadata_seed_must_match_material(self):
        self.prepare_replication(1)
        for arm in ("useful", "corrupt"):
            with self.subTest(arm=arm):
                path = self.root / f"training/{arm}_seed1/train_meta.json"
                meta = self.read(path)
                self.write(path, dict(meta, seed=0))
                with self.assertRaisesRegex(ValueError, "fit/material training seed mismatch"):
                    audit.audit_run(self.root)
                self.write(path, meta)

    def test_matching_command_and_fit_cannot_override_material_seed(self):
        self.prepare_replication(1)
        path = self.root / "training/useful_seed1/train_manifest.json"
        manifest = self.read(path)
        manifest["config"]["seed"] = 2
        self.write(path, manifest)
        path = self.root / "training/useful_seed1/train_meta.json"
        meta = self.read(path)
        self.write(path, dict(meta, seed=2))
        path = self.material / "trainer_commands.json"
        commands = self.read(path)
        argv = commands["commands"]["useful"]["argv"]
        argv[argv.index("--seed") + 1] = "2"
        self.write(path, commands)
        self.seal_material()
        with self.assertRaisesRegex(ValueError, "fit/material training seed mismatch"):
            audit.audit_run(self.root)

    def test_invalid_material_training_seed_rejected(self):
        path = self.material / "validation.json"
        for training_seed in (True, "1", -1, 1.0):
            with self.subTest(training_seed=training_seed):
                validation = self.read(path)
                validation["training_seed"] = training_seed
                self.write(path, validation)
                self.seal_material()
                with self.assertRaisesRegex(ValueError, "invalid material training_seed"):
                    audit.audit_run(self.root)

    def test_swapped_corpus_rejected(self):
        path = self.material / "useful.json"
        path.write_bytes((self.material / "corrupt.json").read_bytes())
        self.seal_material()
        with self.assertRaisesRegex(ValueError, "useful corpus/source"):
            audit.audit_run(self.root)

    def test_swapped_fit_rejected(self):
        path = self.root / "training/useful_seed0/train_manifest.json"
        path.write_bytes((self.root / "training/corrupt_seed0/train_manifest.json").read_bytes())
        with self.assertRaisesRegex(ValueError, "fit corpus/arm"):
            audit.audit_run(self.root)

    def test_wrong_corpus_basename_with_matching_hash_rejected(self):
        path = self.root / "training/useful_seed0/train_manifest.json"
        manifest = self.read(path)
        manifest["corpus"]["file"] = "corrupt.json"
        self.write(path, manifest)
        with self.assertRaisesRegex(ValueError, "fit corpus/arm"):
            audit.audit_run(self.root)

    def test_missing_nonweight_rejected(self):
        (self.root / "training/useful_seed0/train_meta.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            audit.audit_run(self.root)

    def test_spec_adapter_arm_swap_rejected(self):
        path = self.root / "logs/useful/probe_spec.json"
        spec = self.read(path)
        spec["adapter_path"] = "/remote/run/training/corrupt_seed0"
        self.write(path, spec)
        with self.assertRaisesRegex(ValueError, "spec arm/model"):
            audit.audit_run(self.root)

    def test_actual_backend_swap_rejected(self):
        path = self.root / "probes/useful/on/generations.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["source_identity"]["adapter_input"] = "/remote/run/training/corrupt_seed0"
        path.write_text("".join(json.dumps(row)+"\n" for row in rows))
        with self.assertRaisesRegex(ValueError, "actual generation backend/arm"):
            audit.audit_run(self.root)

    def test_nonunique_board_rejected(self):
        path = self.material / "oracle_sources.json"
        payload = self.read(path)
        payload["records"][0]["puzzle"] = [[0]*4 for _ in range(4)]
        self.write(path, payload)
        self.seal_material()
        with self.assertRaisesRegex(ValueError, "not exactly one"):
            audit.audit_run(self.root)

    def test_adapter_manifest_inventory_hash_required(self):
        path = self.root / "logs/useful/probe_spec.json"
        spec = self.read(path)
        spec["expected_adapter_hashes"]["train_manifest.json"] = "0"*64
        self.write(path, spec)
        with self.assertRaisesRegex(ValueError, "expected adapter file mismatch"):
            audit.audit_run(self.root)

    def test_new_output_no_overwrite(self):
        output = self.fixture.root / "audit.json"
        args = ["--run-root", str(self.root), "--output-new", str(output)]
        audit.main(args)
        self.assertTrue(output.is_file())
        with self.assertRaisesRegex(ValueError, "output-new"):
            audit.main(args)

    def test_exact_prompt_mismatch_reported_without_threshold(self):
        path = self.root / "probes/useful/on/generations.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["prompts"][0] = rows[0]["prompts"][0].replace("alive 0s", "alive 1s")
        path.write_text("".join(json.dumps(row)+"\n" for row in rows))
        self.seal_probe("useful")
        report = audit.audit_run(self.root)
        self.assertEqual(report["prompt_mismatch_count"], 1)
        mismatch = next(row for row in report["prompt_checks"] if not row["exact_match"])
        self.assertEqual(mismatch["episode_id"], audit.reducer.EPISODE_IDS[0])
        self.assertNotEqual(mismatch["actual_sha256"], mismatch["source_q_sha256"])
        self.assertNotEqual(mismatch["actual_clock"], mismatch["source_clock"])
        self.assertEqual(report["status"], "OFFLINE_BINDINGS_VALIDATED")

    def test_unequal_temperature_rejected(self):
        path = self.root / "probes/useful/on/configuration.json"
        config = self.read(path)
        config["source_identity"]["default_temperature"] = 0.8
        self.write(path, config)
        with self.assertRaisesRegex(ValueError, "unequal token budgets/temperature"):
            audit.audit_run(self.root)

    def test_wrong_present_weights_rejected(self):
        (self.root / "training/useful_seed0/adapter_model.safetensors").write_bytes(b"wrong weights")
        with self.assertRaisesRegex(ValueError, "expected adapter file mismatch"):
            audit.audit_run(self.root)

    def test_missing_backend_weight_identity_rejected(self):
        path = self.root / "probes/useful/on/configuration.json"
        config = self.read(path)
        config["source_identity"]["adapter_files"] = {}
        self.write(path, config)
        with self.assertRaisesRegex(ValueError, "reported adapter hashes mismatch"):
            audit.audit_run(self.root)


if __name__ == "__main__":
    unittest.main()
