"""CPU fixtures only; no native imports, live roots or model execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


DRIVER = Path(os.environ.get("PERCEPTION_ANALYSIS_DRIVER", "/tmp/astra_perception_multi_seed_analysis_20260913.py"))
SOURCE = Path(os.environ.get("PERCEPTION_PUBLIC_SOURCE", "/data/home/rohing/dream-state"))
spec = importlib.util.spec_from_file_location("perception_analysis_fixture", DRIVER)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(analysis.canonical(value) + "\n")


def read(path):
    return analysis.decode(path.read_bytes())


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_path = SOURCE / analysis.SOURCE_NAMES[0]
        cls.binding = dict(path=str(cls.source_path), sha256=analysis.digest(cls.source_path),
                           parser_sha256=analysis.digest(cls.source_path.with_name("rulegame_parenting_diagnostic.py")))
        cls.corpus = analysis.load_corpus(cls.binding)
        variants = cls.corpus.build_variants("perception", split="dev", system_anchor="EXPLICIT CPU FIXTURE ANCHOR")
        cls.dev = {anchor: variants["supplied" if anchor == "present" else "absent"]["rows"] for anchor in analysis.ARMS}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="perception_analysis_cpu_")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.manifest = dict(schema=analysis.SCHEMA, corpus=copy.deepcopy(self.binding), runs=[])
        for seed in range(3):
            self.make_seed(seed)

    def make_seed(self, seed):
        root = self.base / f"collected_seed{seed}"
        entry = dict(learner_seed=seed, root=str(root), scores=str(self.base / f"scores_seed{seed}" / "scores.json"),
                     collected_snapshot=True)
        self.manifest["runs"].append(entry)
        original = str(self.base / f"not_read_original_seed{seed}")
        metadata = {} if seed == 0 else dict(learner_seed=seed)
        plan = dict(scope=analysis.SCOPES[seed != 0], root=original, config=dict(seed=seed, rank=8, alpha=16, dropout=.05,
                    lr=1e-4, epochs=4, batch_size=4, max_len=1024, pack=False), stages=list(analysis.STAGES),
                    source_hashes={analysis.SOURCE_NAMES[0]: self.binding["sha256"], analysis.SOURCE_NAMES[1]: self.binding["parser_sha256"]},
                    engine=dict(seed=0, enable_lora=True, max_lora_rank=32), params=dict(seed=0, max_tokens=192),
                    model="NEVER_READ_MODEL", model_files={"fixture": "model identity"}, binding=dict(revision="fixture_revision"),
                    chat_template="FIXTURE ONLY", anchor="EXPLICIT CPU FIXTURE ANCHOR", probe_sha256="b" * 64, **metadata)
        calls = {}
        for anchor in analysis.ARMS:
            calls[anchor] = [dict(call_id=f"{index:02d}", row_id=row["row_id"], messages=row["input_messages"],
                                 native=dict(rendered_prompt=analysis.canonical(row["input_messages"]), prompt_token_ids=[1, 2, 3],
                                             actual_system_text=plan["anchor"] if anchor == "present" else "fixture default",
                                             actual_system_segment="fixture")) for index, row in enumerate(self.dev[anchor])]
        write(root / "dev.json", self.dev)
        write(root / "calls.json", calls)
        write(root / "plan.json", plan)
        count = {"OFF__absent": 0, "OFF__present": 0, "fitAbsent__absent": seed + 3,
                 "fitAbsent__present": seed + 2, "fitPresent__absent": seed + 4, "fitPresent__present": seed + 6}
        for ordinal, stage in enumerate(analysis.STAGES):
            directory = root / "run" / stage
            write(directory / "started.json", dict(stage=stage, pid=100 + ordinal, time=1000 + ordinal * 100,
                                                   plan_sha256="pending", **metadata))
            write(directory / "released.json", dict(pid=100 + ordinal, time=1010 + ordinal * 100))
            if stage.startswith("fit_"):
                write(directory / "fit.json", dict(arm=stage.removeprefix("fit_"), updates=12, presentations=48,
                      adapter=original + "/run/" + stage + "/adapter", adapter_files={"fixture_weights": "a" * 64}, **metadata))
                continue
            anchor = stage.split("__")[1]
            adapter = None if stage.startswith("OFF__") else original + "/run/" + ("fit_absent" if stage.startswith("fitAbsent__") else "fit_present") + "/adapter"
            route = None if adapter is None else dict(name="perception", id=1, path=adapter)
            write(directory / "identity.json", dict(cell=stage, model=plan["model"], model_files=plan["model_files"], revision="fixture_revision",
                  engine=plan["engine"], params=plan["params"], adapter=adapter, adapter_files={} if adapter is None else {"fixture_weights": "a" * 64},
                  lora_request=route, **metadata))
            for index, (row, call) in enumerate(zip(self.dev[anchor], calls[anchor])):
                write(directory / f"{index:02d}.request.json", call)
                text = row["raw_target"] if index < count[stage] else "{}"
                write(directory / f"{index:02d}.response.json", dict(**call["native"], actual_prompt_token_ids=[1, 2, 3],
                      output_token_ids=[9, 10], text=text, decoded_output=text, finish_reason="stop", stop_reason=None,
                      started=index * 2, ended=index * 2 + 1, lora_request=route))
        self.seal(seed)

    def seal(self, seed):
        entry = self.manifest["runs"][seed]
        root = Path(entry["root"])
        plan = read(root / "plan.json")
        plan["input_hashes"] = {name: analysis.digest(root / name) for name in ("dev.json", "calls.json")}
        write(root / "plan.json", plan)
        entry["plan_sha256"] = analysis.digest(root / "plan.json")
        inventory, cells = {}, {}
        dev = read(root / "dev.json")
        metadata = {} if seed == 0 else dict(learner_seed=seed)
        for stage in analysis.STAGES:
            directory = root / "run" / stage
            started = read(directory / "started.json")
            started["plan_sha256"] = entry["plan_sha256"]
            write(directory / "started.json", started)
            if not stage.startswith("fit_"):
                files = {"identity.json"} | {f"{index:02d}{suffix}" for index in range(12) for suffix in (".request.json", ".response.json")}
                write(directory / "closed.json", dict(calls=12, files={name: analysis.digest(directory / name) for name in files}))
                rows = []
                for index, row in enumerate(dev[stage.split("__")[1]]):
                    response_path = directory / f"{index:02d}.response.json"
                    response = read(response_path)
                    rows.append(dict(row_id=row["row_id"], source_id=row["source"]["source_id"],
                                     score=self.corpus.score_response(row, response["text"]), finish_reason=response["finish_reason"],
                                     response_sha256=analysis.digest(response_path)))
                cells[stage] = dict(rows=rows, correct=sum(row["score"]["passed"] for row in rows), total=12,
                                    length_finishes=sum(row["finish_reason"] == "length" for row in rows))
            inventory[stage] = {path.name: analysis.digest(path) for path in directory.iterdir() if path.is_file()}
        write(root / "capture_complete.json", dict(plan_sha256=entry["plan_sha256"], calls=72, scored=False, stages=inventory, **metadata))
        entry["completion_sha256"] = analysis.digest(root / "capture_complete.json")
        write(Path(entry["scores"]), dict(scope=plan["scope"], plan_sha256=entry["plan_sha256"], completion_sha256=entry["completion_sha256"],
              cells=cells, calls=72, automatic_pass=False, **metadata))
        entry["scores_sha256"] = analysis.digest(entry["scores"])

    def mutate_json(self, path, change):
        value = read(path)
        change(value)
        write(path, value)

    def response_path(self, seed=0, cell="OFF__absent", index=0):
        return Path(self.manifest["runs"][seed]["root"]) / "run" / cell / f"{index:02d}.response.json"

    def change_text(self, text, seed=0, cell="OFF__absent", index=0):
        self.mutate_json(self.response_path(seed, cell, index), lambda value: value.update(text=text, decoded_output=text))
        self.seal(seed)

    def test_complete_three_seeds_primary_pairing_effects_mean_range_and_timing(self):
        result = analysis.analyze(self.manifest)
        self.assertEqual(result["learner_seeds"], [0, 1, 2])
        self.assertEqual(result["total_responses"], 216)
        self.assertEqual(result["across_seed"]["cells"]["fitAbsent__absent"]["primary_correct"],
                         dict(mean=4, minimum=3, maximum=5, n_learner_seeds=3))
        for seed, run in enumerate(result["per_seed"]):
            self.assertEqual(run["contrasts"]["gain_over_matched_OFF"]["fitAbsent__absent"]["net"], seed + 3)
            self.assertEqual(run["contrasts"]["withdrawal_absent_minus_present"]["fitPresent"]["net"], -2)
            self.assertEqual(run["contrasts"]["training_anchor_present_minus_absent"]["absent"]["net"], 1)
            self.assertEqual(run["timing"]["summed_started_receipt_to_release_seconds"], 80)
            self.assertEqual(run["timing"]["generation_seconds"], 72)
            for cell in run["cells"].values():
                self.assertEqual(cell["primary"]["total"], 12)
                self.assertEqual(cell["secondary"]["total"], 12)
                self.assertEqual(cell["prompt_tokens"], 36)
                self.assertEqual(cell["output_tokens"], 24)

    def test_paired_losses_and_off_adjustment_are_not_unpaired_count_differences(self):
        self.change_text(self.dev["absent"][11]["raw_target"], index=11)
        result = analysis.analyze(self.manifest)["per_seed"][0]["contrasts"]
        self.assertEqual(result["gain_over_matched_OFF"]["fitAbsent__absent"],
                         dict(gains=3, losses=1, both_correct=0, both_wrong=8, net=2, total=12))
        self.assertEqual(result["withdrawal_absent_minus_present"]["fitAbsent"]["off_adjusted_net"], 0)

    def test_single_fence_is_secondary_only_original_score_unchanged(self):
        self.change_text("\n```json\n" + self.dev["absent"][0]["raw_target"] + "\n```\n")
        cell = analysis.analyze(self.manifest)["per_seed"][0]["cells"]["OFF__absent"]
        self.assertEqual(cell["primary"]["correct"], 0)
        self.assertEqual(cell["primary"]["raw_format_errors"], 1)
        self.assertEqual(cell["primary"]["field_errors"], {field: 12 for field in analysis.FIELDS})
        self.assertEqual(cell["primary"]["schema_errors"], 12)
        self.assertEqual(cell["secondary"]["complete_records"], 1)
        self.assertEqual(cell["secondary"]["fences_stripped"], 1)
        self.assertEqual(cell["secondary"]["field_errors"], {field: 11 for field in analysis.FIELDS})

    def test_secondary_refuses_prose_multiple_nested_non_json_or_inline_fences(self):
        target = analysis.decode(self.dev["absent"][0]["raw_target"])
        text = analysis.canonical(target)
        for raw in ("before\n```json\n" + text + "\n```", "```json\n" + text + "\n```\nafter",
                    "```json\n{}\n```\n```json\n{}\n```", "```\n" + text + "\n```",
                    "```JSON\n" + text + "\n```", "```json " + text + "```", "```json\n```json\n{}\n```\n```"):
            with self.subTest(raw=raw):
                view = analysis.field_view(raw, target)
                self.assertFalse(view["fence_stripped"])
                self.assertTrue(view["view_format_error"])
                self.assertTrue(all(view["field_errors"].values()))

    def test_audit_six_contrast_groups_have_all_directional_rows_and_correct_signs(self):
        result = analysis.analyze(self.manifest)
        groups = result["per_seed"][0]["prespecified_contrasts"]
        self.assertEqual(len(groups), 6)
        pairs = {
            "prompt_elicitation_O1_minus_O0": ("OFF__present", "OFF__absent"),
            "ordinary_transfer_N0_minus_O0": ("fitAbsent__absent", "OFF__absent"),
            "ordinary_prompted_N1_minus_O1": ("fitAbsent__present", "OFF__present"),
            "anchor_training_withdrawn_P0_minus_N0": ("fitPresent__absent", "fitAbsent__absent"),
            "anchor_training_prompted_P1_minus_N1": ("fitPresent__present", "fitAbsent__present"),
        }
        for run in result["per_seed"]:
            for name, (left, right) in pairs.items():
                pair = run["prespecified_contrasts"][name]
                self.assertEqual((pair["x_cell"], pair["y_cell"]), (left, right))
                self.check_directions(run, pair)
            for state in analysis.STATES:
                pair = run["prespecified_contrasts"]["residual_readout_prompt_dependence"][state]
                self.assertEqual((pair["x_cell"], pair["y_cell"]), (state + "__present", state + "__absent"))
                self.check_directions(run, pair)
                compact = run["contrasts"]["readout_present_minus_absent"][state]
                self.assertEqual(compact, dict(gains=pair["x_only"], losses=pair["y_only"], both_correct=pair["both"],
                                              both_wrong=pair["neither"], net=pair["net_count"], total=12))
            self.assertEqual(run["prespecified_contrasts"]["residual_readout_prompt_dependence"]["OFF"],
                             run["prespecified_contrasts"]["prompt_elicitation_O1_minus_O0"])
            interaction = run["descriptive_training_anchor_interaction"]
            self.assertEqual(interaction["net_count"], -3)
            self.assertEqual(sum(row["contribution"] for row in interaction["per_row"]), -3)
            self.assertEqual(interaction["net_fraction"], -.25)
        self.assertEqual(result["across_seed"]["prespecified_contrasts"]["anchor_training_withdrawn_P0_minus_N0"]["net_count"]["mean"], 1)
        self.assertEqual(result["interpretation_audit_sha256"], analysis.AUDIT_SHA256)

    def check_directions(self, run, pair):
        left = {row["row_id"]: row["primary"]["passed"] for row in run["cells"][pair["x_cell"]]["rows"]}
        right = {row["row_id"]: row["primary"]["passed"] for row in run["cells"][pair["y_cell"]]["rows"]}
        flattened = [row_id for identifiers in pair["row_ids"].values() for row_id in identifiers]
        self.assertEqual(len(flattened), 12)
        self.assertEqual(set(flattened), set(left))
        for name, expected in (("x_only", (True, False)), ("y_only", (False, True)), ("both", (True, True)), ("neither", (False, False))):
            self.assertEqual(pair[name], len(pair["row_ids"][name]))
            for row_id in pair["row_ids"][name]:
                self.assertEqual((left[row_id], right[row_id]), expected)
        self.assertEqual(pair["net_count"], pair["x_only"] - pair["y_only"])
        self.assertEqual(pair["net_fraction"], pair["net_count"] / 12)

    def test_prompt_elicitation_includes_bidirectional_flips_not_just_net(self):
        self.change_text(self.dev["present"][0]["raw_target"], cell="OFF__present", index=0)
        self.change_text(self.dev["absent"][1]["raw_target"], cell="OFF__absent", index=1)
        pair = analysis.analyze(self.manifest)["per_seed"][0]["prespecified_contrasts"]["prompt_elicitation_O1_minus_O0"]
        self.assertEqual((pair["x_only"], pair["y_only"], pair["both"], pair["neither"], pair["net_count"]), (1, 1, 0, 10, 0))
        self.assertEqual(pair["row_ids"]["x_only"], [self.dev["present"][0]["row_id"]])
        self.assertEqual(pair["row_ids"]["y_only"], [self.dev["absent"][1]["row_id"]])
        self.assertEqual(analysis.analyze(self.manifest)["per_seed"][0]["contrasts"]["readout_present_minus_absent"]["OFF"],
                         dict(gains=1, losses=1, both_correct=0, both_wrong=10, net=0, total=12))

    def test_strict_and_secondary_field_errors_agree_without_a_fence(self):
        target = analysis.decode(self.dev["absent"][0]["raw_target"])
        record = dict(target, observed=not target["observed"])
        self.change_text(analysis.canonical(record))
        cell = analysis.analyze(self.manifest)["per_seed"][0]["cells"]["OFF__absent"]
        self.assertEqual(cell["primary"]["field_errors"], cell["secondary"]["field_errors"])
        self.assertEqual(cell["primary"]["field_errors"], {field: 12 if field == "observed" else 11 for field in analysis.FIELDS})

    def test_secondary_missing_malformed_nonobject_and_duplicate_keys_keep_all_fields(self):
        target = analysis.decode(self.dev["absent"][0]["raw_target"])
        for raw in ("", "not JSON", "null", "[]", "{}", '{"observed":true,"observed":false}',
                    '```json\n{"x":{"nested":1,"nested":2}}\n```', '{"observed":NaN}'):
            with self.subTest(raw=raw):
                view = analysis.field_view(raw, target)
                self.assertFalse(view["complete_record"])
                self.assertTrue(all(view["field_errors"].values()))

    def test_strict_boolean_null_triple_and_relation_types_no_coercion(self):
        target = {"try": [1, 2, 3], "observed": True, "predicted": None, "relation": "unavailable"}
        bad_values = {"try": ([True, 2, 3], [1.0, 2, 3], [1, 2], "1,2,3"), "observed": (1, "true", None),
                      "predicted": (0, "null", "false"), "relation": (None, 0, ["unavailable"])}
        for field, values in bad_values.items():
            for value in values:
                record = dict(target, **{field: value})
                view = analysis.field_view(analysis.canonical(record), target)
                self.assertTrue(view["field_errors"][field])
                self.assertEqual(sum(view["field_errors"].values()), 1)
        self.assertFalse(analysis.field_view(analysis.canonical(target), target)["field_errors"]["predicted"])
        missing = dict(target)
        del missing["predicted"]
        self.assertTrue(analysis.field_view(analysis.canonical(missing), target)["field_errors"]["predicted"])

    def test_independent_field_errors_and_extra_schema_keys(self):
        target = analysis.decode(self.dev["absent"][0]["raw_target"])
        record = dict(target, observed=not target["observed"])
        view = analysis.field_view(analysis.canonical(record), target)
        self.assertEqual(view["field_errors"], {field: field == "observed" for field in analysis.FIELDS})
        view = analysis.field_view(analysis.canonical(dict(target, extra="ignored only for field view")), target)
        self.assertTrue(view["schema_error"])
        self.assertFalse(view["complete_record"])
        self.assertFalse(any(view["field_errors"].values()))

    def test_requires_exactly_three_unique_integer_seeds_before_loading_sources(self):
        for seeds in ([0, 1], [0, 1, 1], [False, 1, 2], [0, 1, 2.0], [0, 1, 3]):
            manifest = copy.deepcopy(self.manifest)
            manifest["runs"] = [dict(manifest["runs"][0], learner_seed=seed) for seed in seeds]
            with patch.object(analysis, "load_corpus", side_effect=AssertionError("must not load")):
                with self.assertRaises(ValueError):
                    analysis.analyze(manifest)

    def test_unordered_manifest_has_deterministic_seed_order(self):
        self.manifest["runs"].reverse()
        self.assertEqual([run["learner_seed"] for run in analysis.analyze(self.manifest)["per_seed"]], [0, 1, 2])

    def test_reject_missing_response_or_cell_never_omit_seed(self):
        self.response_path(seed=2).unlink()
        with self.assertRaises(ValueError):
            analysis.analyze(self.manifest)

    def test_reject_missing_cell_even_with_new_external_scores_hash(self):
        entry = self.manifest["runs"][1]
        self.mutate_json(Path(entry["scores"]), lambda value: value["cells"].pop("OFF__absent"))
        entry["scores_sha256"] = analysis.digest(entry["scores"])
        with self.assertRaisesRegex(ValueError, "inventory"):
            analysis.analyze(self.manifest)

    def test_external_plan_completion_and_scores_pins(self):
        for key in ("plan_sha256", "completion_sha256", "scores_sha256"):
            manifest = copy.deepcopy(self.manifest)
            manifest["runs"][2][key] = "0" * 64
            with self.subTest(pin=key), self.assertRaisesRegex(ValueError, "hash mismatch"):
                analysis.analyze(manifest)

    def test_original_decision_counts_identifiers_and_bool_type_are_verified(self):
        entry = self.manifest["runs"][1]
        path = Path(entry["scores"])
        original = read(path)
        changes = (lambda value: value["cells"]["OFF__absent"]["rows"][0]["score"].update(passed=True),
                   lambda value: value["cells"]["OFF__absent"]["rows"][0]["score"].update(passed=0),
                   lambda value: value["cells"]["OFF__absent"].update(correct=1),
                   lambda value: value["cells"]["OFF__absent"]["rows"][0].update(row_id="wrong"),
                   lambda value: value["cells"]["OFF__absent"]["rows"][0].update(source_id="wrong"),
                   lambda value: value["cells"]["OFF__absent"].update(total=11))
        for change in changes:
            write(path, original)
            self.mutate_json(path, change)
            entry["scores_sha256"] = analysis.digest(path)
            with self.assertRaises(ValueError):
                analysis.analyze(self.manifest)

    def test_resealed_request_response_prompt_pairing_rejected(self):
        self.mutate_json(self.response_path(), lambda value: value.update(actual_prompt_token_ids=[4]))
        self.seal(0)
        with self.assertRaisesRegex(ValueError, "prompt token"):
            analysis.analyze(self.manifest)

    def test_resealed_request_identifier_rejected(self):
        request = self.response_path().with_name("00.request.json")
        self.mutate_json(request, lambda value: value.update(call_id="01"))
        self.seal(0)
        with self.assertRaisesRegex(ValueError, "request pairing"):
            analysis.analyze(self.manifest)

    def test_resealed_dev_target_or_source_proof_cannot_change_public_target(self):
        root = Path(self.manifest["runs"][0]["root"])
        self.mutate_json(root / "dev.json", lambda value: value["absent"][0].update(raw_target="{}"))
        self.seal(0)
        with self.assertRaisesRegex(ValueError, "fixed public DEV"):
            analysis.analyze(self.manifest)

    def test_resealed_readout_seed_or_lora_drift_rejected(self):
        path = self.response_path().with_name("identity.json")
        original = read(path)
        for change in (lambda value: value["engine"].update(seed=1), lambda value: value.update(lora_request={"id": 1})):
            write(path, original)
            self.mutate_json(path, change)
            self.seal(0)
            with self.assertRaises(ValueError):
                analysis.analyze(self.manifest)

    def test_resealed_config_seed_or_cross_seed_recipe_drift_rejected(self):
        root = Path(self.manifest["runs"][2]["root"])
        path = root / "plan.json"
        original = read(path)
        for field, value in (("seed", 1), ("seed", True), ("lr", .002)):
            write(path, original)
            self.mutate_json(path, lambda plan: plan["config"].update({field: value}))
            self.seal(2)
            with self.assertRaises(ValueError):
                analysis.analyze(self.manifest)

    def test_length_termination_counts_tokens_and_timing(self):
        self.mutate_json(self.response_path(), lambda value: value.update(finish_reason="length", output_token_ids=[4] * 192, stop_reason="fixture_limit"))
        self.seal(0)
        cell = analysis.analyze(self.manifest)["per_seed"][0]["cells"]["OFF__absent"]
        self.assertEqual(cell["termination"], dict(stop=11, length=1, stop_reasons={'"fixture_limit"': 1, "null": 11}))
        self.assertEqual(cell["output_tokens"], 214)
        self.assertEqual(cell["generation_seconds"], 12)

    def test_invalid_lengths_token_types_and_timing_rejected(self):
        path = self.response_path()
        original = read(path)
        for update in (dict(finish_reason="length"), dict(output_token_ids=[True]), dict(output_token_ids=[]),
                       dict(output_token_ids=[2] * 193), dict(ended=-1), dict(started=True)):
            write(path, original)
            self.mutate_json(path, lambda value: value.update(update))
            self.seal(0)
            with self.assertRaises(ValueError):
                analysis.analyze(self.manifest)

    def test_failures_unclosed_promoted_collections_reject_aggregate(self):
        entry = self.manifest["runs"][0]
        root = Path(entry["root"])
        write(root / "controller_failure.json", {"error": "fixture"})
        with self.assertRaisesRegex(ValueError, "failed input"):
            analysis.analyze(self.manifest)
        (root / "controller_failure.json").unlink()
        complete = read(root / "capture_complete.json")
        complete["scored"] = True
        write(root / "capture_complete.json", complete)
        entry["completion_sha256"] = analysis.digest(root / "capture_complete.json")
        self.mutate_json(Path(entry["scores"]), lambda value: value.update(completion_sha256=entry["completion_sha256"]))
        entry["scores_sha256"] = analysis.digest(entry["scores"])
        with self.assertRaisesRegex(ValueError, "incomplete or promoted"):
            analysis.analyze(self.manifest)

    def test_duplicate_json_keys_rejected_in_external_artifacts(self):
        path = Path(self.manifest["runs"][0]["scores"])
        path.write_text('{"cells": {}, "cells": {}}')
        self.manifest["runs"][0]["scores_sha256"] = analysis.digest(path)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            analysis.analyze(self.manifest)

    def test_public_corpus_and_parser_are_explicitly_hash_bound(self):
        for field in ("sha256", "parser_sha256"):
            manifest = copy.deepcopy(self.manifest)
            manifest["corpus"][field] = "0" * 64
            with self.assertRaisesRegex(ValueError, "public source pin"):
                analysis.analyze(manifest)

    def test_source_loader_ignores_environment_module_cache(self):
        with patch.dict(sys.modules, {"organism_v6.birth_skill_corpus": object(), "organism_v6": object()}):
            self.assertEqual(analysis.analyze(self.manifest)["total_responses"], 216)

    def test_relocated_roots_only_no_native_or_original_path_dereferences(self):
        self.assertFalse(any(self.base.glob("not_read_original*")))
        original_resolve = Path.resolve

        def collected_only_resolve(path, *args, **kwargs):
            self.assertNotIn("not_read_original", str(path))
            return original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", collected_only_resolve):
            self.assertEqual(analysis.analyze(self.manifest)["total_responses"], 216)
        root = Path(self.manifest["runs"][0]["root"])
        self.mutate_json(root / "plan.json", lambda value: value.update(root=str(root)))
        self.seal(0)
        with self.assertRaisesRegex(ValueError, "relocated snapshot"):
            analysis.analyze(self.manifest)

    def test_explicit_snapshot_attestation_required(self):
        self.manifest["runs"][2]["collected_snapshot"] = False
        with self.assertRaisesRegex(ValueError, "explicit collected"):
            analysis.analyze(self.manifest)

    def test_completion_response_hash_and_extra_records_are_rejected(self):
        path = self.response_path()
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            analysis.analyze(self.manifest)
        path.write_bytes(original)
        write(path.with_name("12.response.json"), read(path))
        with self.assertRaisesRegex(ValueError, "extra/missing"):
            analysis.analyze(self.manifest)

    def test_original_score_response_hash_and_failure_list_are_exact(self):
        entry = self.manifest["runs"][0]
        path = Path(entry["scores"])
        original = read(path)
        for change in (lambda row: row.update(response_sha256="0" * 64),
                       lambda row: row["score"].update(failures=["invented reason"])):
            value = copy.deepcopy(original)
            change(value["cells"]["OFF__absent"]["rows"][0])
            write(path, value)
            entry["scores_sha256"] = analysis.digest(path)
            with self.assertRaisesRegex(ValueError, "original score decision"):
                analysis.analyze(self.manifest)

    def test_missing_replication_seed_and_boolean_seed_are_rejected(self):
        entry = self.manifest["runs"][1]
        path = Path(entry["root"]) / "plan.json"
        original = read(path)
        for change in (lambda value: value.pop("learner_seed"), lambda value: value.update(learner_seed=True)):
            write(path, original)
            self.mutate_json(path, change)
            self.seal(1)
            with self.assertRaisesRegex(ValueError, "plan learner seed"):
                analysis.analyze(self.manifest)

    def test_missing_bound_stage_or_failure_inventory_rejects(self):
        entry = self.manifest["runs"][2]
        path = Path(entry["root"]) / "capture_complete.json"
        original = read(path)
        for change in (lambda value: value["stages"].pop("fit_present"),
                       lambda value: value["stages"]["fit_present"].update({"failure.json": "0" * 64})):
            value = copy.deepcopy(original)
            change(value)
            write(path, value)
            entry["completion_sha256"] = analysis.digest(path)
            self.mutate_json(Path(entry["scores"]), lambda scores: scores.update(completion_sha256=entry["completion_sha256"]))
            entry["scores_sha256"] = analysis.digest(entry["scores"])
            with self.assertRaises(ValueError):
                analysis.analyze(self.manifest)

    def test_empty_text_is_a_scored_failure_not_a_dropped_response(self):
        self.change_text("")
        cell = analysis.analyze(self.manifest)["per_seed"][0]["cells"]["OFF__absent"]
        self.assertEqual(cell["primary"]["total"], 12)
        self.assertEqual(cell["primary"]["raw_format_errors"], 1)
        self.assertEqual(cell["secondary"]["field_errors"], {field: 12 for field in analysis.FIELDS})

    def test_cli_writes_only_complete_output_and_never_overwrites(self):
        manifest = self.base / "manifest.json"
        output = self.base / "analysis.json"
        write(manifest, self.manifest)
        analysis.main(["--manifest", str(manifest), "--output", str(output)])
        before = output.read_bytes()
        with self.assertRaises(FileExistsError):
            analysis.main(["--manifest", str(manifest), "--output", str(output)])
        self.assertEqual(before, output.read_bytes())
        self.response_path(seed=2).unlink()
        rejected = self.base / "not_written.json"
        with self.assertRaises(ValueError):
            analysis.main(["--manifest", str(manifest), "--output", str(rejected)])
        self.assertFalse(rejected.exists())

    def test_import_is_standard_library_only(self):
        program = "import runpy,sys; runpy.run_path(sys.argv[1],run_name='fixture_import'); assert not ({'torch','vllm','transformers','peft'} & set(sys.modules))"
        result = subprocess.run([sys.executable, "-B", "-c", program, str(DRIVER)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
