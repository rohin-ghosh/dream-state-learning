"""Synthetic CPU-only fixtures; no captured experimental responses are opened."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ANALYZER = Path(__file__).with_name("astra_reflection_multi_seed_analysis_20260913.py")
spec = importlib.util.spec_from_file_location("reflection_analysis_test_target", ANALYZER)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
SOURCE_ROOT = Path(os.environ.get("REFLECTION_SOURCE_ROOT", "/data/home/rohing/dream-state"))
SEED0_RUNTIME = Path(os.environ.get("REFLECTION_SEED0_RUNTIME", "/tmp/astra_reflection_fit_run_20260913.py"))
REPLICA_RUNTIME = Path(os.environ.get("REFLECTION_REPLICA_RUNTIME", "/tmp/astra_reflection_fit_replication_run_20260913.py"))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(analysis.canonical(value) + "\n", encoding="utf-8")
    return analysis.digest(path)


def read(path):
    return analysis.decode(path.read_bytes())


def source_manifest():
    return dict(schema=analysis.SCHEMA, preselected_learner_seeds=[0, 1, 2], selection_before_outcomes=True,
                source=dict(root=str(SOURCE_ROOT), sha256=dict(analysis.SOURCE_PINS)),
                runtimes={"seed0": dict(path=str(SEED0_RUNTIME), sha256=analysis.RUNTIME_PINS["seed0"]),
                          "replication": dict(path=str(REPLICA_RUNTIME), sha256=analysis.RUNTIME_PINS["replication"])}, runs=[])


def seed_fields(seed):
    return {} if seed == 0 else {"learner_seed": seed}


def native(messages):
    system = messages[0]["content"]
    segment = "<|im_start|>system\n" + system + "<|im_end|>\n"
    text = segment + "<|im_start|>user\n" + messages[1]["content"] + "<|im_end|>\n<|im_start|>assistant\n"
    count = 7 if "In future records" in messages[1]["content"] else 5
    return dict(rendered_prompt=text, prompt_token_ids=list(range(10, 10 + count)),
                actual_system_text=system, actual_system_segment=segment)


def training(rows, seed):
    encoding, items = [], []
    for index, row in enumerate(rows):
        prompt = native(row["input_messages"])
        supervised = [100 + index, 200 + index, 1]
        ids = prompt["prompt_token_ids"] + supervised + [9]
        labels = [-100] * len(prompt["prompt_token_ids"]) + supervised + [-100]
        encoding.append(dict(row_id=row["row_id"], response_target=row["response_target"], native_prompt=prompt,
                             input_ids=ids, labels=labels, supervised_ids=supervised, prompt_tokens=len(prompt["prompt_token_ids"]),
                             target_tokens=2, supervised_tokens=3, input_tokens=len(ids),
                             target_utf8_bytes=len(row["response_target"].encode()), prompt_utf8_bytes=len(prompt["rendered_prompt"].encode())))
        items.append(dict(group=row["row_id"], order=index))
    order_ids = [row["row_id"] for row in rows]
    orders = [order_ids[(seed + epoch) % 12:] + order_ids[:(seed + epoch) % 12] for epoch in range(4)]
    by_id = {row["row_id"]: row for row in encoding}
    batches = []
    for epoch, order in enumerate(orders):
        for offset in range(0, 12, 4):
            selected = order[offset:offset + 4]
            batches.append(dict(epoch=epoch, row_ids=selected, input_tokens=sum(by_id[name]["input_tokens"] for name in selected),
                                padded_tokens=4 * max(by_id[name]["input_tokens"] for name in selected), supervised_tokens=12))
    fields = {"prompt_tokens": "prompt_tokens", "authored_target_tokens": "target_tokens", "target_tokens": "supervised_tokens",
              "total_tokens": "input_tokens", "target_utf8_bytes": "target_utf8_bytes", "prompt_utf8_bytes": "prompt_utf8_bytes"}
    return dict(**seed_fields(seed), items=items, encoding=encoding, epoch_order=orders, batch_exposure=batches,
                **{name: sum(row[field] for row in encoding) for name, field in fields.items()})


def tree(path):
    return {str(member.relative_to(path)): analysis.digest(member) for member in sorted(path.rglob("*")) if member.is_file()}


class SnapshotFixture:
    def __init__(self, base, corpus, runtimes, expected):
        self.manifest = source_manifest()
        self.base, self.corpus = base, corpus
        trains, dev, exports = expected
        calls = {arm: [dict(call_id=f"{index:02d}", row_id=row["row_id"], messages=row["input_messages"],
                           native=native(row["input_messages"])) for index, row in enumerate(dev[arm])] for arm in analysis.ARMS}
        for seed in range(3):
            root, logs, collection = (base / f"seed{seed}_{name}" for name in ("snapshot", "logs", "collection"))
            root.mkdir()
            logs.mkdir()
            runtime_name = "seed0" if seed == 0 else "replication"
            runtime = runtimes[runtime_name]
            config = dict(runtime["RECIPE"], seed=seed, model=f"/native/{seed}/model", target_modules=["q_proj", "v_proj"])
            binding = dict(revision="synthetic-fixture-only", model_files={"fixture-model": "0" * 64}, clean_ancestry_certified=False)
            prepared = {arm: training(trains[arm], seed) for arm in analysis.ARMS}
            inputs = {"dev.json": dev, "calls.json": calls, "exports.json": exports, "source_pins.json": analysis.SOURCE_PINS,
                      "binding_receipt.json": binding, **{f"train_{arm}.json": prepared[arm] for arm in analysis.ARMS}}
            pins = {name: dump(root / name, value) for name, value in inputs.items()}
            plan = dict(**seed_fields(seed), root=f"/native/{seed}/run", log_dir=f"/native/{seed}/logs", source=f"/native/{seed}/source",
                        model=config["model"], scope=runtime["SCOPE"], claim=runtime["CLAIM"], self_sha256=analysis.RUNTIME_PINS[runtime_name],
                        engine=runtime["ENGINE"], params=runtime["PARAMS"], config=config, source_hashes=analysis.SOURCE_PINS,
                        binding=binding, model_files=binding["model_files"], input_hashes=pins, calls=144, stages=list(analysis.STAGES),
                        truncation_allowed=False, generic_system=runtime["GENERIC_SYSTEM"], source_pins_sha256=pins["source_pins.json"],
                        binding_receipt_sha256=pins["binding_receipt.json"], chat_template="SYNTHETIC_CPU_TEMPLATE", probe_sha256="1" * 64)
            if seed:
                plan["parent_driver_sha256"] = analysis.RUNTIME_PINS["seed0"]
            plan_pin = dump(root / "plan.json", plan)
            fits = {}
            results = {}
            for position, stage in enumerate(analysis.STAGES):
                directory = root / "run" / stage
                pid = 1000 + seed * 10 + position
                dump(directory / "started.json", dict(**seed_fields(seed), pid=pid, pgid=pid, stage=stage, plan_sha256=plan_pin, time=position * 10.0))
                dump(directory / "launch.json", dict(**seed_fields(seed), pid=pid, pgid=pid, stage=stage, plan_sha256=plan_pin))
                dump(directory / "released.json", dict(**seed_fields(seed), pid=pid, pgid=pid, time=position * 10.0 + 5.0))
                (logs / stage).mkdir()
                (logs / stage / "stdout.log").write_text("SYNTHETIC CPU FIXTURE\n")
                (logs / stage / "stderr.log").write_text("")
                if stage.startswith("fit_"):
                    arm = stage.removeprefix("fit_")
                    train = prepared[arm]
                    adapter = directory / "adapter"
                    adapter.mkdir()
                    (adapter / "adapter_model.safetensors").write_bytes(b"NOT TENSORS: SYNTHETIC CUSTODY FIXTURE")
                    (adapter / "DONE").write_text("fixture")
                    dump(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, target_modules=config["target_modules"], bias="none"))
                    fit_manifest = dict(config=config, empty=False, steps=12, micro_batches=12, epochs_run=4, nonfinite_batches=0,
                                        corpus=dict(n_items=12, n_encoded=12, n_skipped_no_target=0),
                                        truncation={name: 0 for name in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")},
                                        packing=dict(mode="one_item_per_sequence", n_sequences=12), train_tokens_seen=4 * train["total_tokens"],
                                        tokens=dict(target=train["target_tokens"], context=train["total_tokens"] - train["target_tokens"], total=train["total_tokens"],
                                                    target_by_category=dict(authored_restatement=train["authored_target_tokens"], assistant_end=12),
                                                    target_by_view=dict(restatement=train["target_tokens"])), mean_loss_per_epoch=[1.0] * 4, final_loss=1.0)
                    dump(adapter / "train_manifest.json", fit_manifest)
                    fit = dict(**seed_fields(seed), arm=arm, adapter=str(Path(plan["root"]) / "run" / stage / "adapter"),
                               adapter_files=tree(adapter), updates=12, presentations=48)
                    dump(directory / "fit.json", fit)
                    fits[stage] = fit
                    continue
                state, arm = stage.split("__")
                fit = None if state == "OFF" else fits["fit_withdrawn" if state == "fitWithdrawn" else "fit_present"]
                adapter = None if fit is None else fit["adapter"]
                route = None if fit is None else dict(name="reflection", id=1, path=adapter)
                identity = dict(**seed_fields(seed), cell=stage, model=plan["model"], revision=binding["revision"], model_files=binding["model_files"],
                                adapter=adapter, adapter_files={} if fit is None else fit["adapter_files"], lora_request=route,
                                engine=plan["engine"], params=plan["params"])
                dump(directory / "identity.json", identity)
                for index, (row, call) in enumerate(zip(dev[arm], calls[arm], strict=True)):
                    text = row["response_target"]
                    dump(directory / f"{index:02d}.request.json", call)
                    dump(directory / f"{index:02d}.response.json", dict(**call["native"], text=text, decoded_output=text,
                         actual_prompt_token_ids=call["native"]["prompt_token_ids"], output_token_ids=[101, 102], finish_reason="stop",
                         stop_reason=1, started=1.0, ended=1.25, lora_request=route))
                names = {"identity.json"} | {f"{index:02d}{suffix}" for index in range(24) for suffix in (".request.json", ".response.json")}
                dump(directory / "closed.json", dict(**seed_fields(seed), calls=24, files={name: analysis.digest(directory / name) for name in names}))
                results[stage] = {}
            complete = dict(**seed_fields(seed), plan_sha256=plan_pin, calls=144, scored=False, time=80.0,
                            stages={stage: dict(artifacts=tree(root / "run" / stage), logs=tree(logs / stage)) for stage in analysis.STAGES})
            completion_pin = dump(root / "capture_complete.json", complete)
            scores = dict(**seed_fields(seed), scope=plan["scope"], claim=plan["claim"], plan_sha256=plan_pin, completion_sha256=completion_pin,
                          cells=results, calls=144, fresh_workers=8, automatic_pass=False, composite_metric=None, clean_ancestry_certified=False,
                          restatement_limitation="An exact authored fixture mismatch is NOT semantic prose failure.")
            if seed:
                scores["parent_driver_sha256"] = analysis.RUNTIME_PINS["seed0"]
            dump(collection / "scores.json", scores)
            entry = dict(learner_seed=seed, collected_snapshot=True, root=str(root), logs=str(logs), scores=str(collection / "scores.json"),
                         plan_sha256=plan_pin, completion_sha256=completion_pin)
            self.manifest["runs"].append(entry)
            self.refresh(seed)

    def root(self, seed):
        return Path(self.manifest["runs"][seed]["root"])

    def change_response(self, seed, cell, index, text, length=False):
        path = self.root(seed) / "run" / cell / f"{index:02d}.response.json"
        response = read(path)
        response.update(text=text, decoded_output=text, output_token_ids=[101] * (192 if length else 2), finish_reason="length" if length else "stop")
        dump(path, response)
        self.refresh(seed)

    def refresh(self, seed):
        entry = self.manifest["runs"][seed]
        root, logs, scores_path = self.root(seed), Path(entry["logs"]), Path(entry["scores"])
        dev = read(root / "dev.json")
        scores = read(scores_path)
        for cell in analysis.CELLS:
            directory = root / "run" / cell
            closed = read(directory / "closed.json")
            closed["files"] = {name: analysis.digest(directory / name) for name in closed["files"]}
            dump(directory / "closed.json", closed)
            panels = {}
            for panel in analysis.PANELS:
                rows = []
                for index, row in enumerate(dev[cell.split("__")[1]]):
                    if row["panel"] != panel:
                        continue
                    response_path = directory / f"{index:02d}.response.json"
                    response = read(response_path)
                    rows.append(dict(row_id=row["row_id"], source_id=row["source"]["source_id"], score=self.corpus.score_response(row, response["text"]),
                                     finish_reason=response["finish_reason"], response_sha256=analysis.digest(response_path)))
                panels[panel] = dict(rows=rows, metric=analysis.METRICS[panel], count=sum(row["score"]["passed"] for row in rows), total=12,
                                     semantic_prose_score=None, length_finishes=sum(row["finish_reason"] == "length" for row in rows))
            scores["cells"][cell] = panels
        complete = read(root / "capture_complete.json")
        complete["stages"] = {stage: dict(artifacts=tree(root / "run" / stage), logs=tree(logs / stage)) for stage in analysis.STAGES}
        entry["completion_sha256"] = dump(root / "capture_complete.json", complete)
        scores["completion_sha256"] = entry["completion_sha256"]
        entry["scores_sha256"] = dump(scores_path, scores)
        entry["collection_sha256"] = dump(scores_path.parent / "collection.json", dict(**seed_fields(seed), scores_sha256=entry["scores_sha256"],
                                               completion_sha256=entry["completion_sha256"]))


class ReflectionAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.runtimes = analysis.load_sources(source_manifest())
        cls.expected = analysis.build_expected(cls.corpus)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="reflection_analysis_fixture_")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.fixture = SnapshotFixture(self.base, self.corpus, self.runtimes, self.expected)
        self.manifest = self.fixture.manifest

    def analyze(self):
        return analysis.analyze(self.manifest)

    def mutate_json(self, path, change):
        value = read(path)
        change(value)
        return dump(path, value)

    def test_complete_three_seed_api_separates_panels_and_cost(self):
        report = self.analyze()
        self.assertEqual(report["total_responses"], 432)
        self.assertEqual(set(report["tables"]), {"restatement", "application"})
        for panel in analysis.PANELS:
            for row in report["tables"][panel]:
                self.assertEqual(row["counts"], [12, 12, 12])
                self.assertEqual(row["denominator_per_seed"], 12)
        self.assertEqual(report["tables"]["restatement"][0]["syntax_valid"], [None] * 3)
        self.assertIsNone(report["semantic_prose_score"])
        self.assertIsNone(report["composite_metric"])
        self.assertFalse(report["automatic_pass"])
        self.assertEqual(report["per_seed"][0]["timing"]["summed_stage_seconds"], 40.0)
        self.assertEqual(report["per_seed"][0]["training_exposure"]["withdrawn"]["full_fit"]["target_tokens"], 144)

    def test_nonexact_prose_preserved_without_semantic_judgment(self):
        text = "Different public summary.\n  Preserve this prose exactly. "
        self.fixture.change_response(0, "OFF__withdrawn", 0, text)
        result = self.analyze()["per_seed"][0]["cells"]["OFF__withdrawn"]
        self.assertEqual(result["restatement"]["count"], 11)
        self.assertEqual(result["application"]["count"], 12)
        self.assertEqual(result["restatement"]["rows"][0]["raw_response"], text)
        self.assertIsNone(result["restatement"]["syntax_valid_count"])
        self.assertIsNone(result["restatement"]["rows"][0]["score"]["semantic_prose_score"])

    def test_strict_application_whitespace_and_length_remain_failures(self):
        target = self.expected[1]["withdrawn"][12]["response_target"]
        self.fixture.change_response(1, "fitWithdrawn__withdrawn", 12, target + " ", length=True)
        result = self.analyze()["per_seed"][1]["cells"]["fitWithdrawn__withdrawn"]["application"]
        self.assertEqual((result["count"], result["syntax_valid_count"], result["termination"]["length"]), (11, 11, 1))

    def test_seedwise_flips_retain_correct_memberships(self):
        self.fixture.change_response(2, "OFF__withdrawn", 12, "invalid")
        self.fixture.change_response(2, "fitWithdrawn__withdrawn", 13, "invalid")
        flip = self.analyze()["per_seed"][2]["paired_flips"]["application"]["ordinary_transfer"]
        self.assertEqual(flip["counts"], dict(gains=1, losses=1, both_correct=10, both_wrong=0))
        self.assertEqual(flip["net_count"], 0)
        self.assertEqual(flip["row_ids"]["gains"], [self.expected[1]["withdrawn"][12]["row_id"]])

    def test_missing_or_duplicate_seed_rejected(self):
        self.manifest["runs"][2]["learner_seed"] = 1
        with self.assertRaisesRegex(ValueError, "exact seeds"):
            self.analyze()

    def test_boolean_seed_rejected(self):
        self.manifest["preselected_learner_seeds"] = [False, 1, 2]
        with self.assertRaisesRegex(ValueError, "preselected"):
            self.analyze()
        self.manifest["preselected_learner_seeds"] = [0, 1, 2]
        self.manifest["runs"][0]["learner_seed"] = False
        with self.assertRaisesRegex(ValueError, "exact seeds"):
            self.analyze()

    def test_explicit_postcollection_required(self):
        self.manifest["runs"][0]["collected_snapshot"] = False
        with self.assertRaisesRegex(ValueError, "completed collection"):
            self.analyze()

    def test_source_and_runtime_pins_fail_closed(self):
        self.manifest["source"]["sha256"]["organism_v6/birth_reflection_probe.py"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source pins"):
            self.analyze()
        self.manifest["source"]["sha256"] = dict(analysis.SOURCE_PINS)
        self.manifest["runtimes"]["seed0"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "runtime source"):
            self.analyze()

    def test_raw_byte_tamper_rejected(self):
        path = self.fixture.root(0) / "run/OFF__withdrawn/00.response.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.analyze()

    def test_score_tamper_with_updated_score_pin_rejected(self):
        entry = self.manifest["runs"][0]
        path = Path(entry["scores"])
        entry["scores_sha256"] = self.mutate_json(path, lambda value: value["cells"]["OFF__withdrawn"]["restatement"].update(count=0))
        entry["collection_sha256"] = self.mutate_json(path.parent / "collection.json", lambda value: value.update(scores_sha256=entry["scores_sha256"]))
        with self.assertRaisesRegex(ValueError, "stored corpus"):
            self.analyze()

    def test_collection_required_even_when_scores_exist(self):
        Path(self.manifest["runs"][0]["scores"]).with_name("collection.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing file"):
            self.analyze()

    def test_failed_collection_rejected(self):
        Path(self.manifest["runs"][0]["scores"]).with_name("collection_failure.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "failed collection"):
            self.analyze()

    def test_bad_lora_route_rejected_after_custody_refresh(self):
        self.mutate_json(self.fixture.root(1) / "run/fitPresent__present/00.response.json", lambda value: value.update(lora_request=None))
        self.fixture.refresh(1)
        with self.assertRaisesRegex(ValueError, "route mismatch"):
            self.analyze()

    def test_replica_seed_binding_rejected_after_custody_refresh(self):
        self.mutate_json(self.fixture.root(2) / "run/OFF__present/closed.json", lambda value: value.update(learner_seed=1))
        self.fixture.refresh(2)
        with self.assertRaisesRegex(ValueError, "learner seed"):
            self.analyze()

    def test_worker_identity_reuse_rejected(self):
        directory = self.fixture.root(0) / "run/OFF__withdrawn"
        for name in ("started.json", "launch.json", "released.json"):
            self.mutate_json(directory / name, lambda value: value.update(pid=1000, pgid=1000))
        self.fixture.refresh(0)
        with self.assertRaisesRegex(ValueError, "eight fresh"):
            self.analyze()

    def test_unindexed_log_rejected(self):
        (Path(self.manifest["runs"][0]["logs"]) / "fit_present/extra.log").write_text("extra")
        with self.assertRaisesRegex(ValueError, "custody file inventory"):
            self.analyze()

    def test_symlink_plan_rejected(self):
        plan = self.fixture.root(0) / "plan.json"
        other = self.base / "other_plan.json"
        plan.rename(other)
        plan.symlink_to(other)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.analyze()

    def test_actual_prompt_rejected(self):
        path = self.fixture.root(0) / "run/OFF__withdrawn/00.response.json"
        self.mutate_json(path, lambda value: value.update(actual_prompt_token_ids=[999]))
        self.fixture.refresh(0)
        with self.assertRaisesRegex(ValueError, "actual prompt"):
            self.analyze()

    def test_missing_adapter_bytes_rejected(self):
        (self.fixture.root(0) / "run/fit_withdrawn/adapter/adapter_model.safetensors").unlink()
        with self.assertRaisesRegex(ValueError, "custody file inventory"):
            self.analyze()

    def test_bad_training_batch_exposure_rejected(self):
        entry = self.manifest["runs"][0]
        root = self.fixture.root(0)
        pin = self.mutate_json(root / "train_withdrawn.json", lambda value: value["batch_exposure"][0].update(padded_tokens=0))
        plan = read(root / "plan.json")
        plan["input_hashes"]["train_withdrawn.json"] = pin
        entry["plan_sha256"] = dump(root / "plan.json", plan)
        complete = read(root / "capture_complete.json")
        complete["plan_sha256"] = entry["plan_sha256"]
        dump(root / "capture_complete.json", complete)
        scores = read(Path(entry["scores"]))
        scores["plan_sha256"] = entry["plan_sha256"]
        dump(Path(entry["scores"]), scores)
        self.fixture.refresh(0)
        with self.assertRaisesRegex(ValueError, "batch exposure"):
            self.analyze()

    def test_cross_seed_template_drift_rejected(self):
        entry = self.manifest["runs"][2]
        root = self.fixture.root(2)
        entry["plan_sha256"] = self.mutate_json(root / "plan.json", lambda value: value.update(chat_template="CHANGED"))
        self.mutate_json(root / "capture_complete.json", lambda value: value.update(plan_sha256=entry["plan_sha256"]))
        self.mutate_json(Path(entry["scores"]), lambda value: value.update(plan_sha256=entry["plan_sha256"]))
        for stage in analysis.STAGES:
            for name in ("started.json", "launch.json"):
                self.mutate_json(root / "run" / stage / name, lambda value: value.update(plan_sha256=entry["plan_sha256"]))
        self.fixture.refresh(2)
        with self.assertRaisesRegex(ValueError, "cross-seed"):
            self.analyze()

    def test_duplicate_json_and_nonfinite_rejected(self):
        for text in ('{"seed":0,"seed":1}', '{"time":NaN}'):
            with self.assertRaises(ValueError):
                analysis.decode(text)

    def test_pair_rejects_mismatched_ids(self):
        with self.assertRaisesRegex(ValueError, "paired row"):
            analysis.pair([dict(row_id="first", score=dict(passed=True))], [dict(row_id="other", score=dict(passed=False))])

    def test_cli_exclusive_output_and_outside_inputs(self):
        manifest_path = self.base / "manifest.json"
        dump(manifest_path, self.manifest)
        output = self.base / "analysis.json"
        analysis.main(["--manifest", str(manifest_path), "--output", str(output)])
        before = output.read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            analysis.main(["--manifest", str(manifest_path), "--output", str(output)])
        self.assertEqual(output.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "outside all inputs"):
            analysis.main(["--manifest", str(manifest_path), "--output", str(self.fixture.root(0) / "new.json")])

    def test_failed_analysis_never_writes_output(self):
        self.manifest["runs"][0]["completion_sha256"] = "f" * 64
        manifest_path, output = self.base / "bad.json", self.base / "unwritten.json"
        dump(manifest_path, self.manifest)
        with self.assertRaises(ValueError):
            analysis.main(["--manifest", str(manifest_path), "--output", str(output)])
        self.assertFalse(output.exists())

    def test_analyzer_does_not_import_native_or_repository_modules(self):
        original = __import__

        def guarded(name, *args, **kwargs):
            self.assertNotIn(name.split(".")[0], {"torch", "transformers", "vllm", "peft", "organism_v6"})
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded):
            self.analyze()

    def test_missing_raw_response_rejected(self):
        (self.fixture.root(0) / "run/OFF__withdrawn/00.response.json").unlink()
        with self.assertRaisesRegex(ValueError, "custody file inventory"):
            self.analyze()

    def test_weak_length_finish_rejected(self):
        path = self.fixture.root(0) / "run/OFF__withdrawn/00.response.json"
        self.mutate_json(path, lambda value: value.update(finish_reason="length"))
        self.fixture.refresh(0)
        with self.assertRaisesRegex(ValueError, "weak length"):
            self.analyze()

    def test_preselection_declared_before_outcomes(self):
        self.manifest["selection_before_outcomes"] = False
        with self.assertRaisesRegex(ValueError, "preselected"):
            self.analyze()

    def test_native_root_is_not_accepted_as_snapshot(self):
        entry = self.manifest["runs"][0]
        entry["plan_sha256"] = self.mutate_json(self.fixture.root(0) / "plan.json", lambda value: value.update(root=entry["root"]))
        with self.assertRaisesRegex(ValueError, "original/native"):
            self.analyze()

    def test_claim_composite_is_rejected(self):
        entry = self.manifest["runs"][0]
        path = Path(entry["scores"])
        entry["scores_sha256"] = self.mutate_json(path, lambda value: value.update(composite_metric=24))
        entry["collection_sha256"] = self.mutate_json(path.parent / "collection.json", lambda value: value.update(scores_sha256=entry["scores_sha256"]))
        with self.assertRaisesRegex(ValueError, "claim boundary"):
            self.analyze()

    def test_failed_stage_is_rejected_even_when_indexed(self):
        dump(self.fixture.root(0) / "run/fit_present/failure.json", dict(error="synthetic failure"))
        self.fixture.refresh(0)
        with self.assertRaisesRegex(ValueError, "failed custody"):
            self.analyze()

    def test_unsafe_custody_member_rejected(self):
        entry = self.manifest["runs"][0]
        root = self.fixture.root(0)
        complete = read(root / "capture_complete.json")
        complete["stages"]["fit_present"]["artifacts"]["../outside"] = "0" * 64
        entry["completion_sha256"] = dump(root / "capture_complete.json", complete)
        entry["scores_sha256"] = self.mutate_json(Path(entry["scores"]), lambda value: value.update(completion_sha256=entry["completion_sha256"]))
        entry["collection_sha256"] = self.mutate_json(Path(entry["scores"]).with_name("collection.json"),
                lambda value: value.update(completion_sha256=entry["completion_sha256"], scores_sha256=entry["scores_sha256"]))
        with self.assertRaisesRegex(ValueError, "custody file inventory"):
            self.analyze()
        with self.assertRaisesRegex(ValueError, "unsafe inventory"):
            analysis.member(root, "../outside")

    def test_analysis_does_not_modify_fixture_inputs(self):
        before = tree(self.base)
        self.analyze()
        self.assertEqual(tree(self.base), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
