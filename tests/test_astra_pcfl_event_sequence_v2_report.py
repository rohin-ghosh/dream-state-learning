"""Synthetic in-memory reporting fixtures, NOT native evidence or science results.

The NATIVE label exercises the input contract, not an attestation of these data.
No reducer/runtime imports, actual archives, model execution, SSH or GPU access.
"""

import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_event_sequence_v2_report as api


def seal(value):
    value.pop("sha256", None)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    value["sha256"] = hashlib.sha256(encoded).hexdigest()
    return value


def file_bytes(value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    return raw, hashlib.sha256(raw).hexdigest()


def fixture_pin():
    return dict(path="/NONNATIVE_IN_MEMORY_FIXTURE/not-a-real-file.json", sha256="a" * 64)


def contrast(states, control):
    result = {}
    for view in ("W0", "W8"):
        result[view] = {}
        for bank, endpoint in (("A", "retention"), ("B", "acquisition")):
            left = states["REPLAY400"]["panels"][view][bank]
            right = states[control]["panels"][view][bank]
            delta = [int(left["strict_stop"][index]) - int(right["strict_stop"][index]) for index in range(4)]
            result[view][bank] = dict(endpoint=endpoint, ids=left["ids"], denominator=4,
                                      replay_strict_stop=left["strict_stop"], control_strict_stop=right["strict_stop"],
                                      paired_delta=delta, correct_difference=sum(delta), rate_difference=sum(delta) / 4)
    return result


def state_fixture(seed_index, state_index):
    rows, captures = [], []
    for view_index, view in enumerate((0, 8)):
        for record in range(8):
            row_id = f"event-sequence-v2/W{view}/{record:02}"
            strict = (record + seed_index + state_index + view_index) % 3 == 0
            finish = "length" if record == state_index and view == 8 else "stop"
            rows.append(dict(id=row_id, request=f"READ EVENT FIXTURE{record}", record=record, view=view,
                             bank="A" if record < 4 else "B", raw="NONNATIVE SYNTHETIC ROW", target_sha256=str(record) * 64,
                             score=dict(strict=strict), strict_stop=strict and finish == "stop", finish_reason=finish,
                             prompt_tokens=2, output_tokens=1))
            captures.append(dict(id=row_id, raw_capture=fixture_pin(), prompt_token_ids=[1, 2], output_token_ids=[3], stop_reason=None))
    panels = {}
    for view in (0, 8):
        panels[f"W{view}"] = {}
        for bank in ("A", "B"):
            selected = [row for row in rows if row["view"] == view and row["bank"] == bank]
            panels[f"W{view}"][bank] = dict(denominator=4, ids=[row["id"] for row in selected],
                                          strict_stop=[row["strict_stop"] for row in selected], correct=sum(row["strict_stop"] for row in selected))
    return dict(denominator=16, gpu_released=True, results=rows, captures=captures, panels=panels,
                strict_stop=[row["strict_stop"] for row in rows], tokens=dict(prompt=32, output=16),
                truncated=1, elapsed_seconds=dict(worker=1, outer_release_inclusive=2))


def receipt_fixture():
    states = ("NO_WRITE", "A200", "B200_NEW_DOSE", "B400_FIXED_WORK", "REPLAY400", "CLEAN_CUM600")
    seeds = []
    for seed_index in range(3):
        seed_states = {name: state_fixture(seed_index, index) for index, name in enumerate(states)}
        failed = dict(fits=seed_index, updates=200 * seed_index, presentations=800 * seed_index, readout_calls=0)
        failure = None if seed_index == 0 else dict(earlier_failure=None, failed_work=failed.copy(),
            cumulative_failed_work=failed.copy(), attempt_elapsed_seconds=seed_index * 10, elapsed_seconds=seed_index * 10)
        seed = dict(schema=api.SCHEMA + "/seed", kind="NATIVE", status="VALIDATED_NOT_PROMOTED", learner_seed=seed_index,
                    automatic_promotion=False, full_contract_released=False, limits="SYNTHETIC — not scientific evidence",
                    manifest=fixture_pin(), completed=fixture_pin(), material=fixture_pin(), acquisition_receipt=fixture_pin(),
                    runtime_allocation=fixture_pin(), spec_sha256="b" * 64,
                    bank_identity=dict(import_sha256="c" * 64, records_sha256="d" * 64, roster_sha256="e" * 64,
                                       tokenizer_receipt=dict(synthetic=True)),
                    model_identity=dict(model_path="/NONNATIVE", model_binding=fixture_pin(), base_state_receipt=fixture_pin()),
                    counts=dict(fits=4, updates=1600, presentations=6400, calls=64, initial_updates=200, total_updates=1800),
                    states=seed_states, fits={name: dict(phase=name, updates=updates, presentations=updates * 4,
                        gpu_released=True, elapsed_seconds=dict(worker=1, outer_release_inclusive=2))
                        for name, updates in zip(states[1:], (200, 200, 400, 400, 600))},
                    prior_failure=failure, prior_failed_work=failed,
                    total_physical_work=dict(fits=5 + seed_index, updates=1800 + failed["updates"],
                                             presentations=7200 + failed["presentations"], readout_calls=96),
                    elapsed_seconds=dict(initial_collections=30, prior_failure=seed_index * 10, followup=100 + seed_index,
                                         total=130 + 11 * seed_index),
                    paired_contrasts={"REPLAY400-" + control: contrast(seed_states, control) for control in states[2:4]},
                    phase_boundary_descriptive=dict(contrast="REPLAY400-CLEAN_CUM600", panels=contrast(seed_states, states[-1]),
                                                    interpretation="Descriptive phase-boundary only"))
        seeds.append(seal(seed))
    summary = {}
    for control in ("B200_NEW_DOSE", "B400_FIXED_WORK", "CLEAN_CUM600"):
        panels = {}
        for view in ("W0", "W8"):
            panels[view] = {}
            for bank in ("A", "B"):
                delta = []
                for seed in seeds:
                    delta.extend(contrast(seed["states"], control)[view][bank]["paired_delta"])
                panels[view][bank] = dict(denominator=12, unique_records=4, learners=3, seed_order=[0, 1, 2],
                                          paired_delta=delta, correct_difference=sum(delta), rate_difference=sum(delta) / 12)
        summary["REPLAY400-" + control] = dict(descriptive_only=control == "CLEAN_CUM600", panels=panels)
    receipt = dict(schema=api.SCHEMA + "/receipt", kind="NATIVE", status="VALIDATED_NOT_PROMOTED", request=fixture_pin(),
                   learner_seeds=[0, 1, 2], independent_banks=1, unique_events=8, seeds=seeds,
                   automatic_promotion=False, full_contract_released=False, limits="SYNTHETIC — not scientific evidence",
                   interpretation="NONNATIVE TEST FIXTURE ONLY", descriptive_paired_summary=summary)
    for field in ("total_physical_work", "prior_failed_work", "elapsed_seconds"):
        receipt[field] = {key: sum(seed[field][key] for seed in seeds) for key in seeds[0][field]}
    return seal(receipt)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.receipt = receipt_fixture()

    def render(self, receipt=None):
        return api.render_receipt(*file_bytes(self.receipt if receipt is None else receipt))

    def reject_mutation(self, mutate, *, reseal_seeds=True):
        receipt = copy.deepcopy(self.receipt)
        mutate(receipt)
        if reseal_seeds:
            for seed in receipt["seeds"]:
                seal(seed)
        seal(receipt)
        with self.assertRaises(ValueError):
            self.render(receipt)

    def test_complete_pure_render_is_deterministic_and_preserves_input(self):
        raw, checksum = file_bytes(self.receipt)
        before = copy.deepcopy(self.receipt)
        with patch.object(Path, "open", side_effect=AssertionError("pure renderer must not access files")):
            report = api.render_receipt(raw, checksum)
            self.assertEqual(report, api.render_receipt(raw, checksum))
        self.assertEqual(self.receipt, before)
        self.assertIn(checksum, report)
        self.assertIn(self.receipt["sha256"], report)
        self.assertIn("## W0 strict correctness", report)
        self.assertIn("## W8 strict correctness", report)
        self.assertIn("| NO_WRITE | 2/4 | 1/4 | 0/8 | 1/4 | 1/4 | 0/8 | 1/4 | 2/4 | 0/8 |", report)
        self.assertIn("| NO_WRITE | 1/4 | 1/4 | 1/8 | 1/4 | 2/4 | 1/8 | 1/4 | 1/4 | 1/8 |", report)
        self.assertIn("| Learner sum | 18 | 6000 | 24000 | 288 | 3 | 600 | 2400 | 0 |", report)
        self.assertIn("| Learner sum (not wallclock) | 90.000000 | 30.000000 | 303.000000 | 423.000000 |", report)
        for control in ("B200_NEW_DOSE", "B400_FIXED_WORK", "CLEAN_CUM600"):
            self.assertEqual(report.count("| REPLAY400-" + control + " |"), 6)
        for text in ("already-validated raw reduction", "does not itself verify native custody", "execute models",
                     "promote G3/H1/H2/parenting", "not independent banks", "NOT wallclock", "not added again"):
            self.assertIn(text, report)
        self.assertNotIn("NONNATIVE SYNTHETIC ROW", report)
        self.assertNotIn("NONNATIVE_IN_MEMORY_FIXTURE", report)

    def test_file_hash_is_required_and_distinct_from_sealed_digest(self):
        raw, checksum = file_bytes(self.receipt)
        for invalid in (None, "", "g" * 64, checksum.upper(), "0" * 64, self.receipt["sha256"]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                api.render_receipt(raw, invalid)
        with self.assertRaisesRegex(ValueError, "FILE SHA256"):
            api.render_receipt(raw + b" ", checksum)
        with self.assertRaises(ValueError):
            api.render_receipt(raw.decode(), checksum)

    def test_outer_and_seed_digest_drift(self):
        self.receipt["status"] = "CHANGED"
        with self.assertRaisesRegex(ValueError, "sealed digest"):
            self.render()
        self.receipt = receipt_fixture()
        self.reject_mutation(lambda receipt: receipt["seeds"][0].update(limits="unsealed edit"), reseal_seeds=False)

    def test_wrong_schema_kind_status_and_promotion(self):
        for field, bad in (("schema", api.SCHEMA + "/request"), ("kind", "INJECTED_CPU_TEST"), ("status", "PARTIAL"),
                           ("automatic_promotion", True), ("full_contract_released", True)):
            for nested in (False, True):
                with self.subTest(field=field, nested=nested):
                    self.reject_mutation(lambda receipt: (receipt["seeds"][0] if nested else receipt).update({field: bad}))

    def test_partial_duplicate_reordered_and_mislabeled_learners(self):
        mutations = [lambda receipt: receipt["seeds"].pop(),
                     lambda receipt: receipt["seeds"].reverse(),
                     lambda receipt: receipt["seeds"][1].update(learner_seed=0),
                     lambda receipt: receipt["seeds"][0].update(learner_seed=False),
                     lambda receipt: receipt.update(learner_seeds=[1, 2]),
                     lambda receipt: receipt.update(independent_banks=3),
                     lambda receipt: receipt.update(unique_events=24)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.reject_mutation(mutate)

    def test_missing_required_fields(self):
        for key in self.receipt:
            with self.subTest(root=key):
                receipt = copy.deepcopy(self.receipt)
                del receipt[key]
                if key != "sha256":
                    seal(receipt)
                with self.assertRaises(ValueError):
                    self.render(receipt)
        for key in ("states", "fits", "prior_failure", "prior_failed_work", "counts", "elapsed_seconds", "paired_contrasts",
                    "phase_boundary_descriptive", "bank_identity", "model_identity", "manifest", "spec_sha256"):
            with self.subTest(seed=key):
                self.reject_mutation(lambda receipt: receipt["seeds"][0].pop(key))

    def test_changed_shared_bank_model_and_event_identity(self):
        for key in ("import_sha256", "records_sha256", "roster_sha256"):
            with self.subTest(key=key):
                self.reject_mutation(lambda receipt: receipt["seeds"][1]["bank_identity"].update({key: "f" * 64}))
        self.reject_mutation(lambda receipt: receipt["seeds"][1]["model_identity"].update(model_path="/different"))
        self.reject_mutation(lambda receipt: receipt["seeds"][1]["states"]["NO_WRITE"]["results"][0].update(request="READ EVENT OTHER"))

    def test_state_counts_vectors_labels_and_truncations(self):
        mutations = [lambda state: state["results"].pop(), lambda state: state["captures"].pop(),
                     lambda state: state["strict_stop"].pop(), lambda state: state.update(denominator=15),
                     lambda state: state.update(truncated=0), lambda state: state.update(gpu_released=False),
                     lambda state: state["panels"]["W0"]["A"].update(correct=4),
                     lambda state: state["panels"]["W0"]["A"].update(denominator=12),
                     lambda state: state["panels"]["W0"]["A"]["strict_stop"].__setitem__(0, 1),
                     lambda state: state["panels"]["W0"]["A"]["ids"].reverse(),
                     lambda state: state["results"][0].update(record=1),
                     lambda state: state["results"][0].update(bank="B"),
                     lambda state: state["results"][0].update(view=8),
                     lambda state: state["results"][0].update(strict_stop=1),
                     lambda state: state["results"][0].update(finish_reason="length"),
                     lambda state: state["results"][0]["score"].update(strict=False),
                     lambda state: state["results"][0].update(prompt_tokens=3),
                     lambda state: state["captures"][0]["output_token_ids"].append(5),
                     lambda state: state["tokens"].update(output=17)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.reject_mutation(lambda receipt: mutate(receipt["seeds"][0]["states"]["NO_WRITE"]))
        self.reject_mutation(lambda receipt: receipt["seeds"][0]["states"].pop("A200"))
        self.reject_mutation(lambda receipt: receipt["seeds"][0]["states"].update(UNKNOWN={}))
        self.reject_mutation(lambda receipt: receipt["seeds"][0]["fits"]["A200"].update(phase="REPLAY400"))

    def test_paired_contrast_and_descriptive_summary_drift(self):
        for key, bad in (("endpoint", "acquisition"), ("correct_difference", 42), ("rate_difference", .123),
                         ("paired_delta", [0] * 4), ("denominator", 12), ("control_strict_stop", [True] * 4)):
            with self.subTest(key=key):
                self.reject_mutation(lambda receipt: receipt["seeds"][0]["paired_contrasts"]["REPLAY400-B200_NEW_DOSE"]["W0"]["A"].update({key: bad}))
        self.reject_mutation(lambda receipt: receipt["seeds"][0]["phase_boundary_descriptive"].update(contrast="OTHER"))
        for key, bad in (("unique_records", 12), ("learners", 1), ("seed_order", [2, 1, 0]), ("rate_difference", 9)):
            with self.subTest(summary=key):
                self.reject_mutation(lambda receipt: receipt["descriptive_paired_summary"]["REPLAY400-B200_NEW_DOSE"]["panels"]["W8"]["B"].update({key: bad}))
        self.reject_mutation(lambda receipt: receipt["descriptive_paired_summary"]["REPLAY400-CLEAN_CUM600"].update(descriptive_only=False))

    def test_cost_and_elapsed_drift_negative_boolean_and_nonfinite(self):
        for field, key in (("total_physical_work", "updates"), ("prior_failed_work", "fits"), ("elapsed_seconds", "total")):
            for nested in (False, True):
                with self.subTest(field=field, nested=nested):
                    self.reject_mutation(lambda receipt: (receipt["seeds"][0] if nested else receipt)[field].update({key: 999}))
        self.reject_mutation(lambda receipt: receipt["seeds"][1]["prior_failure"]["failed_work"].update(updates=999))
        for bad in (-1, True, "30"):
            self.reject_mutation(lambda receipt: receipt["seeds"][0]["elapsed_seconds"].update(initial_collections=bad))
        raw, _ = file_bytes(self.receipt)
        for invalid in (b"NaN", b"Infinity", b"1e999"):
            changed = raw.replace(b'"initial_collections": 90', b'"initial_collections": ' + invalid, 1)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                api.render_receipt(changed, hashlib.sha256(changed).hexdigest())

    def test_malformed_json_duplicate_keys_and_utf8(self):
        raw, _ = file_bytes(self.receipt)
        duplicate = raw.replace(b'"unique_events": 8', b'"unique_events": 8, "unique_events": 8', 1)
        for invalid in (b"{", b"[]", b"null", b"\xff", duplicate):
            with self.subTest(invalid=invalid[:20]), self.assertRaises(ValueError):
                api.render_receipt(invalid, hashlib.sha256(invalid).hexdigest())

    def test_cli_exclusive_output_and_no_writes_on_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "receipt.json", root / "report.md"
            raw, checksum = file_bytes(self.receipt)
            source.write_bytes(raw)
            args = ["--receipt", str(source), "--receipt-sha256", checksum, "--output", str(output)]
            api.main(args)
            self.assertEqual(output.read_text(), self.render())
            before = output.read_bytes()
            with patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit) as caught:
                api.main(args)
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(output.read_bytes(), before)
            with self.assertRaises(FileExistsError):
                api.write_report(source, checksum, source)
            self.assertEqual(source.read_bytes(), raw)
            rejected = root / "rejected.md"
            with self.assertRaises(ValueError):
                api.write_report(source, "0" * 64, rejected)
            self.assertFalse(rejected.exists())
            link = root / "link.md"
            link.symlink_to(output)
            with self.assertRaises(FileExistsError):
                api.write_report(source, checksum, link)
            self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
