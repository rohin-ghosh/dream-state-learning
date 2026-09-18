"""Synthetic captured bytes only; fabricated metadata never constitutes native evidence."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from gpu import astra_correction_utility_analysis as analysis


BOARD = "1 2 3 4 ; 3 4 1 2 ; 2 1 4 3 ; 4 3 2 1"


class CorrectionUtilityAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.model = "/never-open/synthetic-Qwen2.5-7B-Instruct"
        self.remote_recipients = "/never-open/recipients"
        self.model_hashes = {"config.json": "a" * 64, "model.safetensors": "b" * 64}
        self.bootstrap = "SYNTHETIC BOOTSTRAP, NOT MODEL EVIDENCE"
        self.snapshot = dict(schema="neutral-pair-source-v1", source_root="/never-open/source",
            bootstrap_path="organism_v6/bootstrap_reasoning_gym.txt", sha256={
                "organism_v6/bootstrap_reasoning_gym.txt": analysis.text_hash(self.bootstrap),
                "organism_v6/reasoning_neutral_probe.py": "c" * 64})
        self.material = self.root / "material"
        self.panel_path = self.root / "panel.json"
        self.index_path = self.root / "capture.json"
        self.panel = dict(status="NATIVE_PANEL_PREPARED_NO_INFERENCE", episode_ids=analysis.EPISODES,
            prospective_probe=analysis.BUDGET, model_path=self.model, families_sha256="d" * 64,
            source_act_sha256=analysis.TARGETS["act_only"], questions=[dict(episode_id=episode,
                question=f"SYNTHETIC puzzle {episode}", question_sha256=analysis.text_hash(f"SYNTHETIC puzzle {episode}"),
                initial_prompt=f"SYNTHETIC prompt {episode}", initial_prompt_sha256=analysis.text_hash(f"SYNTHETIC prompt {episode}"),
                learned_board_compatible=False) for episode in analysis.EPISODES])
        self.write(self.panel_path, self.panel)
        self.panel_pin = self.hash(self.panel_path)
        self.pin_patch = patch.object(analysis, "PANEL_SHA256", self.panel_pin)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        self.prepared = dict(status="READY_CPU_PREPARATION_ONLY", synthetic=False, unique_events=1,
            explicit_replays_per_arm=32, recipient_seeds=[0, 1, 2], optimizer_steps_per_recipient=96,
            token_matched=False, recipient_root=self.remote_recipients, model_path=self.model,
            expected_model_files=self.model_hashes, selection=dict(scratchpad_sha256=analysis.TARGETS["whole_raw"],
                act_sha256=analysis.TARGETS["act_only"]))
        self.write(self.material / "preparation.json", self.prepared)
        self.commands = {}
        for arm in analysis.ARMS:
            self.make_material(arm)
        self.seal_material()
        recipients = []
        for seed in analysis.SEEDS:
            for arm in analysis.ARMS:
                self.make_recipient(arm, seed)
                recipients.append(dict(arm=arm, seed=seed, logs=f"logs/{arm}/seed{seed}",
                                       adapter=f"adapters/{arm}/seed{seed}"))
        self.index = dict(schema="correction-utility-capture-v1", synthetic=True,
                          material="material", panel="panel.json", recipients=recipients)
        self.write(self.index_path, self.index)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n")

    def read(self, path):
        return json.loads(path.read_text())

    def jsonl(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))

    def hash(self, path):
        return analysis.custody._digest(path)

    def logs(self, arm="whole_raw", seed=0):
        return self.root / "logs" / arm / f"seed{seed}"

    def adapter(self, arm="whole_raw", seed=0):
        return self.root / "adapters" / arm / f"seed{seed}"

    def pair(self, arm="whole_raw", seed=0):
        return self.logs(arm, seed) / "probes/pair"

    def make_material(self, arm):
        directory = self.material / arm
        self.write(directory / "corpus.json", dict(synthetic_fixture=True, corpus=["fixture"] * 32))
        target = 20 if arm == "whole_raw" else 10
        rows = [dict(replay_index=index, raw_target_sha256=analysis.TARGETS[arm], supervised_eos_tokens=1,
            supervised_context_tokens=0, supervised_padding_tokens=0, truncation=False, splits=0,
            target_roundtrip_exact=True, input_tokens=100 + target, supervised_target_tokens=target,
            rendered_context_sha256="e" * 64) for index in range(32)]
        preflight = dict(status="PASS_ACTUAL_TOKENIZER_V3_ENCODE_AND_COLLATE", optimizer_steps=96,
            add_eos=True, truncation=False, splits=0, supervised_tokens_per_epoch=32 * target,
            input_tokens_per_epoch=32 * (100 + target), supervised_tokens_all_epochs=96 * target,
            input_tokens_all_epochs=96 * (100 + target), rows=rows)
        self.write(directory / "tokenizer_preflight.json", preflight)
        commands = []
        for seed in analysis.SEEDS:
            command = dict(seed=seed, config=dict(analysis.RECIPE, seed=seed, model=self.model),
                output=f"{self.remote_recipients}/{arm}/seed{seed}", fresh_base=True, adapter_input=None,
                corpus_sha256=self.hash(directory / "corpus.json"))
            self.commands[arm, seed] = command
            commands.append(command)
        self.write(directory / "training_commands.json", dict(commands=commands))

    def seal_material(self):
        self.write(self.material / "artifact_hashes.json", dict(files={
            path.relative_to(self.material).as_posix(): self.hash(path)
            for path in self.material.rglob("*") if path.is_file() and path.name != "artifact_hashes.json"}))

    def make_recipient(self, arm, seed):
        logs, adapter = self.logs(arm, seed), self.adapter(arm, seed)
        adapter.mkdir(parents=True)
        logs.mkdir(parents=True)
        command = self.commands[arm, seed]
        tokens = self.read(self.material / arm / "tokenizer_preflight.json")
        manifest = dict(config=command["config"], steps=96, nonfinite_batches=0, final_loss=.5, empty=False,
            base_model=self.model, corpus=dict(sha256=command["corpus_sha256"], n_items=32, n_encoded=32,
                n_skipped_no_target=0), truncation=dict(items_truncated=0, context_tokens_dropped=0,
                target_tokens_dropped=0, items_split=0), tokens=dict(target=tokens["supervised_tokens_per_epoch"],
                total=tokens["input_tokens_per_epoch"]), train_tokens_seen=tokens["input_tokens_all_epochs"],
            train_seconds=10., wall_seconds=12.)
        self.write(adapter / "train_manifest.json", manifest)
        self.write(adapter / "train_meta.json", dict(steps=96, seed=seed, rank=8, epochs=3, lr=1e-4,
                                                     tokens=tokens["input_tokens_all_epochs"]))
        self.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05,
                                                        bias="none", target_modules=analysis.PROJECTIONS))
        (adapter / "DONE").write_text("ok\n")
        hashes = {path.name: self.hash(path) for path in adapter.iterdir()}
        hashes["adapter_model.safetensors"] = "f" * 64
        spec = dict(analysis.BUDGET, episode_ids=analysis.EPISODES, order=["off", "on"], model_path=self.model,
            expected_model_hashes=self.model_hashes, expected_adapter_hashes=hashes,
            adapter_path=command["output"], families_sha256=self.panel["families_sha256"],
            panel_role="development_validation", selection_used_episode_ids=["rg/mini_sudoku/1850124"])
        self.write(logs / "probe_spec.json", spec)
        self.write(logs / "STARTED.json", dict(arm=arm, seed=seed, unique_events=1, explicit_replays=32,
            token_matched=False, started_utc="2026-09-12T13:30:00+00:00",
            material_sha256=self.hash(self.material / "artifact_hashes.json"), panel_sha256=self.panel_pin,
            script_sha256="1" * 64))
        self.write(logs / "COMPLETED.json", dict(arm=arm, seed=seed, steps=96,
            status="COMPLETED_NOT_A_LEARNING_CLAIM", clean_lineage=False, parenting_advantage=False,
            unique_events=1, manifest_sha256=self.hash(adapter / "train_manifest.json"),
            adapter_sha256=hashes, finished_utc="2026-09-12T13:32:00+00:00"))
        for name in ("fit.log", "pair.log"):
            (logs / name).write_text("SYNTHETIC completion log\n")
        for condition in ("off", "on"):
            self.make_condition(arm, seed, condition, spec)
        self.seal_pair(arm, seed)

    def make_condition(self, arm, seed, name, spec, outputs=None):
        directory = self.pair(arm, seed) / name
        identity = dict(backend="vllm", model_input=self.model,
            adapter_input=spec["adapter_path"] if name == "on" else None,
            adapter_files={key: value for key, value in spec["expected_adapter_hashes"].items()
                           if key in analysis.WEIGHTS | {"adapter_config.json"}} if name == "on" else {},
            default_max_tokens=400, default_temperature=.7)
        sources, hashes = dict(model=self.model), dict(model=self.model_hashes)
        if name == "on":
            sources["adapter"] = spec["adapter_path"]
            hashes["adapter"] = spec["expected_adapter_hashes"]
        config = dict({key: value for key, value in analysis.BUDGET.items() if key != "max_model_len"},
            evidence_label="EVALUATION_ONLY", episode_ids=analysis.EPISODES, source_identity=identity,
            sources=sources, hashes_before=hashes, birth_prompt=self.bootstrap,
            code_hashes_before={"/never-open/source/organism_v6/reasoning_neutral_probe.py": "c" * 64},
            gym_configuration=dict(synthetic_fixture=True), reasoning_gym_version="synthetic",
            protected_roots=[spec["adapter_path"]], probe_root=f"/never-open/{arm}/{seed}/probes",
            origin_verification="UNAUTHENTICATED_SYNTHETIC_FIXTURE")
        self.write(directory / "configuration.json", config)
        self.write(directory / "source_check.json", dict(evidence_label="EVALUATION_ONLY",
            hashes_after=hashes, code_hashes_after=config["code_hashes_before"]))
        events, entries = [], []

        def generation(prompts, seeds, texts, limit):
            index = len(events) // 2
            events.append(dict(evidence_label="EVALUATION_ONLY", kind="generation_request", request_index=index,
                prompts=prompts, seeds=seeds, max_tokens=limit, source_identity=identity, temperature=.7,
                prompt_scope="batch_user_text_before_chat_template"))
            events.append(dict(evidence_label="EVALUATION_ONLY", kind="generation_output", request_index=index,
                               outputs=texts))

        for index, question in enumerate(self.panel["questions"]):
            episode, prompt = question["episode_id"], question["initial_prompt"]
            output = "No ACT in this synthetic output."
            scores = []
            if name == "on" and index < (seed + 2 if arm == "whole_raw" else seed + 1):
                output, scores = "ACT: " + BOARD, [1.0]
            if outputs is not None and index in outputs:
                output, scores = outputs[index]
            wake_seed = analysis.batch_loop._seed_for(episode, 1, 0)
            generation([prompt], [wake_seed], [output], 400)
            receipt = dict(schema="child-generation-v1", identity=identity, prompt_sha256=analysis.text_hash(prompt),
                output_sha256=analysis.text_hash(output), seed=wake_seed, max_tokens=400, temperature=.7)
            markers = [match for match in analysis.batch_loop._MARK.finditer(output) if match.group(1) == "ACT"]
            self.assertEqual(len(markers), len(scores))
            actions = []
            for attempt, (marker, score) in enumerate(zip(markers, scores), 1):
                verdict = "accepted" if score == 1 else "not accepted; partial credit" if score else "not accepted"
                actions.append(dict(evidence_label="EVALUATION_ONLY", kind="act", episode_id=episode, tick=1,
                    execution_id=f"{episode}#occ1#t1a{attempt}", occurrence_id=f"{episode}#occ1", occurrence_index=1,
                    action=marker.group(2).strip(), outcome=f"attempt {attempt}: verifier score {score:.2f} ({verdict})",
                    score=score, generation=receipt))
                if not marker.group(2).strip():
                    actions[-1]["outcome"] = f"INVALID: attempt {attempt} was empty"
            thought = dict(evidence_label="EVALUATION_ONLY", kind="thought", episode_id=episode,
                           tick=1, note=output.strip()[:2000], prompt=prompt[:24000], generation=receipt)
            ledger = actions + [thought]
            if actions:
                prompts = [prompt.rstrip("\n") + "\n\n" + analysis.outcome_block(analysis.facts_from_act(action), "Scratchpad")
                           for action in actions]
                seeds = [(zlib.crc32(action["execution_id"].encode()) ^ analysis.BUDGET["seed_salt"]) & 0x7fffffff
                         for action in actions]
                texts = ["  SYNTHETIC scratchpad whitespace retained.\n" for action in actions]
                generation(prompts, seeds, texts, 100)
                for action, scratch_prompt, text, scratch_seed in zip(actions, prompts, texts, seeds):
                    scratch = {key: value for key, value in action.items() if key not in ("evidence_label", "generation")}
                    scratch.update(kind="scratchpad", text=text, n_chars=len(text), gen_seconds=.1,
                        generation=dict(prompt=scratch_prompt, prompt_sha256=analysis.text_hash(scratch_prompt),
                            output_sha256=analysis.text_hash(text), max_tokens=100, backend_identity=identity,
                            temperature=.7, base_seed=0, seed_salt=analysis.BUDGET["seed_salt"], seed=scratch_seed))
                    ledger.append(scratch)
            ledger_name = f"episode_{index:04d}.jsonl"
            self.jsonl(directory / ledger_name, ledger)
            entries.append(dict(episode_id=episode, ledger=ledger_name, n_actions=len(actions),
                n_measured_actions=sum(analysis.facts_from_act(action).measured for action in actions),
                n_scratchpads=len(actions), summary=dict(episode_id=episode, ticks=1, n_acts=len(actions),
                                                       best_score=max([0.] + scores))))
        self.jsonl(directory / "generations.jsonl", events)
        total = sum(entry["n_actions"] for entry in entries)
        self.write(directory / "results.json", dict(evidence_label="EVALUATION_ONLY", episodes=entries,
            n_actions=total, n_measured_actions=sum(entry["n_measured_actions"] for entry in entries),
            n_scratchpads=total, generation_batches=len(events) // 2,
            reserved_output_tokens=32 * 400 + total * 100))

    def seal_pair(self, arm="whole_raw", seed=0):
        root = self.pair(arm, seed)
        spec_path = self.logs(arm, seed) / "probe_spec.json"
        spec_hash, spec = self.hash(spec_path), self.read(spec_path)
        receipts, hashes = {}, {}
        for offset, name in enumerate(("off", "on")):
            directory = root / name
            self.write(directory / "manifest.json", dict(evidence_label="EVALUATION_ONLY", sha256={
                path.name: self.hash(path) for path in directory.iterdir() if path.name != "manifest.json"}))
            receipt = dict(evidence_label="EVALUATION_ONLY", condition=name, spec_sha256=spec_hash, pid=100 + offset,
                device="0", multiprocessing="spawn", results_sha256=self.hash(directory / "results.json"),
                manifest_sha256=self.hash(directory / "manifest.json"))
            self.write(root / f"{name}_WORKER_DONE.json", receipt)
            receipts[name] = receipt
            hashes[name] = self.hash(root / f"{name}_WORKER_DONE.json")
        self.write(root / "PAIR_STARTED.json", dict(evidence_label="EVALUATION_ONLY", spec_sha256=spec_hash,
            spec=spec, source_snapshot=self.snapshot, controller_pid=99, device="0"))
        self.write(root / "PAIR_DONE.json", dict(evidence_label="EVALUATION_ONLY", spec_sha256=spec_hash,
            workers=receipts, receipt_sha256=hashes, source_snapshot=self.snapshot))

    def reduce(self):
        return analysis.reduce_capture(self.index_path, self.hash(self.index_path))

    def refresh_material(self):
        self.seal_material()
        for seed in analysis.SEEDS:
            for arm in analysis.ARMS:
                path = self.logs(arm, seed) / "STARTED.json"
                started = self.read(path)
                started["material_sha256"] = self.hash(self.material / "artifact_hashes.json")
                self.write(path, started)

    def test_six_cells_gains_costs_and_shared_off(self):
        before = {str(path): self.hash(path) for path in self.root.rglob("*") if path.is_file()}
        report = self.reduce()
        self.assertTrue(report["synthetic"])
        self.assertEqual(report["evidence_label"], "SYNTHETIC_FIXTURE_NOT_EVIDENCE")
        self.assertEqual(len(report["cells"]), 6)
        self.assertTrue(report["off_baseline"]["identical_outputs_and_outcomes"])
        self.assertEqual(report["off_baseline"]["independent_learner_replications"], 0)
        for row in report["per_seed"]:
            self.assertEqual(row["whole_raw_minus_act_only_gain"]["first_act_accepted"], 1)
            self.assertEqual(row["whole_raw_minus_act_only_gain"]["first_act_accepted_rate"], 1 / 32)
        cell = report["cells"]["whole_raw/seed0"]
        self.assertEqual(cell["fit"]["target_token_passes"], 1920)
        self.assertEqual(cell["fit"]["weight_verification"], "OMITTED_WEIGHTS_NOT_REHASHED")
        self.assertEqual(cell["condition_wall_seconds"], 120)
        self.assertIsNone(cell["on"]["costs"]["measured_output_tokens"])
        self.assertEqual(cell["on"]["summary"]["strict_first_act_count"], 2)
        self.assertEqual(before, {str(path): self.hash(path) for path in self.root.rglob("*") if path.is_file()})

    def test_missing_cell_and_duplicate_seed_rejected(self):
        for entries in (self.index["recipients"][:-1], self.index["recipients"][:-1] + self.index["recipients"][:1]):
            with self.subTest(entries=len(entries)):
                self.write(self.index_path, dict(self.index, recipients=entries))
                with self.assertRaisesRegex(ValueError, "six distinct"):
                    self.reduce()

    def test_missing_completion_and_failed_attempt_rejected(self):
        completion = self.logs() / "COMPLETED.json"
        saved = completion.read_bytes()
        completion.unlink()
        with self.assertRaises(ValueError):
            self.reduce()
        completion.write_bytes(saved)
        self.write(self.logs() / "FAILED.json", dict(error="synthetic failure"))
        with self.assertRaisesRegex(ValueError, "failed recipient"):
            self.reduce()

    def test_wrong_arm_in_completion_rejected(self):
        path = self.logs() / "COMPLETED.json"
        value = self.read(path)
        value["arm"] = "act_only"
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, "completion/arm/seed"):
            self.reduce()

    def test_changed_fit_steps_and_recipe_rejected(self):
        path = self.adapter() / "train_manifest.json"
        original = self.read(path)
        for change in (dict(steps=95), dict(nonfinite_batches=1), dict(config=dict(original["config"], rank=16))):
            with self.subTest(change=change):
                self.write(path, dict(original, **change))
                with self.assertRaises(ValueError):
                    self.reduce()

    def test_panel_hash_and_capture_pin_rejected(self):
        with self.assertRaisesRegex(ValueError, "index hash"):
            analysis.reduce_capture(self.index_path, "0" * 64)
        self.write(self.panel_path, dict(self.panel, episode_ids=list(reversed(analysis.EPISODES))))
        with self.assertRaisesRegex(ValueError, "panel hash"):
            self.reduce()

    def test_changed_ledger_hash_rejected(self):
        ledger = self.pair() / "on/episode_0000.jsonl"
        ledger.write_text(ledger.read_text() + "{}\n")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.reduce()

    def test_resealed_summary_cannot_override_first_act(self):
        path = self.pair() / "on/results.json"
        results = self.read(path)
        results["episodes"][0]["summary"]["best_score"] = .1
        self.write(path, results)
        self.seal_pair()
        with self.assertRaisesRegex(ValueError, "best summary"):
            self.reduce()

    def test_multiact_uses_first_partial_not_later_success(self):
        spec = self.read(self.logs() / "probe_spec.json")
        self.make_condition("whole_raw", 0, "on", spec, {0: (f"ACT: {BOARD}\nACT: {BOARD}", [.25, 1.])})
        self.seal_pair()
        cell = self.reduce()["cells"]["whole_raw/seed0"]["on"]
        self.assertEqual(cell["episodes"][0]["first_act_accepted"], 0)
        self.assertEqual(cell["episodes"][0]["first_act_score"], .25)
        self.assertEqual(cell["episodes"][0]["native_best"], 1.)
        self.assertEqual(cell["summary"]["multiple_act_episodes"], 1)
        self.assertFalse(cell["episodes"][0]["exactly_one_strict_act"])

    def test_permissive_marker_is_not_strict_format(self):
        spec = self.read(self.logs() / "probe_spec.json")
        self.make_condition("whole_raw", 0, "on", spec, {0: (f"ACT {BOARD}", [1.])})
        self.seal_pair()
        episode = self.reduce()["cells"]["whole_raw/seed0"]["on"]["episodes"][0]
        self.assertEqual(episode["first_act_accepted"], 1)
        self.assertFalse(episode["first_act_strict_format"])
        self.assertEqual(episode["malformed_act_markers"], 1)

    def test_empty_first_act_zero_filled(self):
        spec = self.read(self.logs() / "probe_spec.json")
        self.make_condition("whole_raw", 0, "on", spec, {0: ("ACT:", [0.])})
        self.seal_pair()
        episode = self.reduce()["cells"]["whole_raw/seed0"]["on"]["episodes"][0]
        self.assertEqual(episode["first_act"]["status"], "unmeasured")
        self.assertEqual(episode["first_act_accepted"], 0)
        self.assertEqual(episode["first_act_score"], 0)

    def test_wrong_token_dose_rejected_after_material_reseal(self):
        path = self.material / "whole_raw/tokenizer_preflight.json"
        preflight = self.read(path)
        preflight["input_tokens_all_epochs"] += 1
        self.write(path, preflight)
        self.refresh_material()
        with self.assertRaisesRegex(ValueError, "token dose"):
            self.reduce()

    def test_preflight_label_leak_rejected(self):
        path = self.material / "whole_raw/tokenizer_preflight.json"
        preflight = self.read(path)
        preflight["rows"][0]["supervised_context_tokens"] = 1
        self.write(path, preflight)
        self.refresh_material()
        with self.assertRaisesRegex(ValueError, "source/mask"):
            self.reduce()

    def test_resealed_wrong_probe_settings_rejected(self):
        path = self.pair() / "on/configuration.json"
        config = self.read(path)
        config["wake_max_tokens"] = 399
        self.write(path, config)
        self.seal_pair()
        with self.assertRaisesRegex(ValueError, "probe settings"):
            self.reduce()

    def test_incomplete_generation_rejected(self):
        path = self.pair() / "on/generations.jsonl"
        events = [json.loads(line) for line in path.read_text().splitlines()]
        self.jsonl(path, events[:-1])
        self.seal_pair()
        with self.assertRaisesRegex(ValueError, "unfinished generation"):
            self.reduce()

    def test_resealed_recorded_source_mismatch_rejected(self):
        path = self.pair() / "PAIR_DONE.json"
        done = self.read(path)
        done["source_snapshot"]["sha256"]["organism_v6/reasoning_neutral_probe.py"] = "0" * 64
        self.write(path, done)
        with self.assertRaisesRegex(ValueError, "source binding"):
            self.reduce()

    def test_fresh_process_receipt_rejected_if_controller_reused(self):
        path = self.pair() / "PAIR_STARTED.json"
        started = self.read(path)
        started["controller_pid"] = 100
        self.write(path, started)
        with self.assertRaisesRegex(ValueError, "worker/controller"):
            self.reduce()

    def test_off_same_outcomes_different_text_not_collapsed(self):
        spec = self.read(self.logs("act_only", 2) / "probe_spec.json")
        self.make_condition("act_only", 2, "off", spec, {0: ("Different synthetic no-action thought.", [])})
        self.seal_pair("act_only", 2)
        baseline = self.reduce()["off_baseline"]
        self.assertFalse(baseline["identical_outputs_and_outcomes"])
        self.assertEqual(baseline["comparisons"]["act_only/seed2"], dict(outputs_equal=False, outcomes_equal=True))

    def test_off_outcome_mismatch_retains_own_baseline(self):
        spec = self.read(self.logs("act_only", 2) / "probe_spec.json")
        self.make_condition("act_only", 2, "off", spec, {0: (f"ACT: {BOARD}", [1.])})
        self.seal_pair("act_only", 2)
        report = self.reduce()
        self.assertFalse(report["off_baseline"]["identical_outputs_and_outcomes"])
        self.assertEqual(report["cells"]["act_only/seed2"]["on_minus_off"]["first_act_accepted"], 2)

    def test_raw_generation_ledger_disagreement_rejected(self):
        path = self.pair() / "on/generations.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[1]["outputs"][0] = "No action instead of recorded action."
        self.jsonl(path, rows)
        self.seal_pair()
        with self.assertRaisesRegex(ValueError, "thought/generation"):
            self.reduce()

    def test_pair_receipt_mismatch_rejected(self):
        path = self.pair() / "PAIR_DONE.json"
        done = self.read(path)
        done["receipt_sha256"]["on"] = "0" * 64
        self.write(path, done)
        with self.assertRaisesRegex(ValueError, "receipt hash"):
            self.reduce()

    def test_failed_source_check_rejected(self):
        path = self.pair() / "on/source_check.json"
        value = self.read(path)
        value["hashes_after"]["model"]["config.json"] = "0" * 64
        self.write(path, value)
        self.seal_pair()
        with self.assertRaisesRegex(ValueError, "source check"):
            self.reduce()

    def test_nonfinite_and_duplicate_json_rejected(self):
        path = self.logs() / "COMPLETED.json"
        for content in ('{"steps": NaN}', '{"steps":96,"steps":95}'):
            path.write_text(content)
            with self.assertRaises(ValueError):
                self.reduce()

    def test_unsafe_index_paths_and_symlink_rejected(self):
        for name in ("../material", "/never-open/material"):
            self.write(self.index_path, dict(self.index, material=name))
            with self.assertRaisesRegex(ValueError, "relative and contained"):
                self.reduce()
        (self.root / "linked").symlink_to(self.material, target_is_directory=True)
        self.write(self.index_path, dict(self.index, material="linked"))
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.reduce()

    def test_changed_input_detected_at_final_verification(self):
        inputs = analysis.Inputs()
        inputs.read(self.index_path)
        self.index_path.write_text(self.index_path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "changed"):
            inputs.verify()

    def test_cli_read_only_stdout_and_invalid_exit(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = analysis.main(["--capture", str(self.index_path), "--capture-sha256", self.hash(self.index_path)])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "SIX_TERMINAL_CELLS_VALIDATED")
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            result = analysis.main(["--capture", str(self.index_path), "--capture-sha256", "0" * 64])
        self.assertEqual(result, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("INVALID", error.getvalue())


if __name__ == "__main__":
    unittest.main()
