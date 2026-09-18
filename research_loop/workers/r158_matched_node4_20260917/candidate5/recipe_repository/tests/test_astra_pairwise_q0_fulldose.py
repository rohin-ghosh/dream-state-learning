"""CPU fixtures and real CPU autograd, never native Qwen or GPU proof."""
from __future__ import annotations

import copy
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pairwise_q0_fulldose as q0

try:
    import torch
except ImportError:
    torch = None


class TokenizerFixture:
    eos_token_id = 151645
    pad_token_id = 151645
    pieces = {6823: "ACT", 25: ":", 481: " -", 10536: "mem", 17: "2", 1580: "reg",
              21404: "gv", 77: "n", 198: "\n"}

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert not tokenize and add_generation_prompt and len(messages) == 1
        return "<user>" + messages[0]["content"] + "</user><assistant>"

    def __call__(self, text, **kwargs):
        assert kwargs.get("truncation") is False and kwargs.get("padding") is False
        end = text.find("</user><assistant>")
        boundary = end + len("</user><assistant>") if end >= 0 else 0
        prefix, suffix = text[:boundary], text[boundary:]
        ids = [1000000 + ord(character) for character in prefix]
        while suffix:
            possible = [(token, piece) for token, piece in self.pieces.items() if suffix.startswith(piece)]
            if possible:
                token, piece = max(possible, key=lambda item: len(item[1]))
                ids.append(token)
                suffix = suffix[len(piece):]
            else:
                ids.append(1000000 + ord(suffix[0]))
                suffix = suffix[1:]
        return {"input_ids": ids}

    def decode(self, ids):
        return "".join("<eos>" if token == self.eos_token_id else self.pieces[token]
                       if token in self.pieces else chr(token - 1000000) for token in ids)


POLICY = q0.NumericalPolicy(gradient_floor=1e-12, safety=4, median_convention="arithmetic_middle_two")


def raw_output(text, tokenizer):
    ids = q0.encode(tokenizer, text) + [tokenizer.eos_token_id]
    return dict(generated_ids=ids, text=text, decoded_with_terminal_eos=tokenizer.decode(ids),
                eos_terminated=True, truncated=False)


def prefix_output(margin=0, mass=.5):
    first, second = margin / 2, -margin / 2
    return dict(z0=first, z1=second, d=margin, q=1 / (1 + math.exp(-margin)), M=mass,
                log_normalizer=math.log(math.exp(first) + math.exp(second)) - math.log(mass))


def readout_fixture(prepared, tokenizer, arm, snapshot):
    rows = {row["id"]: row for row in prepared["rows"]}
    records = []
    for request in q0.request_inventory(prepared, arm, snapshot):
        row = rows[request["row_id"]]
        bit = q0.target(row, arm) if arm != "OFF" and row["panel"] in ("exact", "held") else 0
        if request["operation"] == "prefix":
            margin = (1 - 2 * bit) * 2 if arm != "OFF" and row["panel"] in ("exact", "held") else 0
            output = prefix_output(margin)
        else:
            text = row["expected"] + "\n" if row["panel"] == "copy" else "ACT: " + q0.ACTIONS[bit] + "\n"
            output = raw_output(text, tokenizer)
        records.append(dict(request, output=output))
    return records


def audit_fixture(prepared, nondegenerate=False, zero=False):
    rows = [dict(row_id=row["id"], M=math.exp(-.0001), negative_log_M=.0001)
            for row in prepared["rows"] if row["panel"] == "exact"]
    grad_p = [torch.tensor([0. if zero else 1.])]
    grad_v = [torch.tensor([0. if zero else 1.2 if nondegenerate else 1.])]
    norms = q0.gradient_comparison(grad_p, grad_v, grad_p, POLICY)
    quartets = [dict(quartet_sha256=q0.digest(item), raw_P=[q0.tensor_payload(value) for value in grad_p],
                     raw_V=[q0.tensor_payload(value) for value in grad_v], **norms) for item in prepared["quartets"]]
    return dict(initial={"allocation": prepared["allocation"], "fixture": "root-bound zero-B inventory and logits placeholder; NOT NATIVE",
                         "trainables": [dict(name="CPU_FIXTURE_PARAMETER", shape=[1], dtype="torch.float32")]},
                rows=rows, quartets=quartets, optimizer_steps=0,
                decision=q0.classify_audit(rows, quartets, POLICY))


def canary_fixture(prepared, arm, passed):
    rows = {row["id"]: row for row in prepared["rows"]}
    signs = [1 - 2 * q0.target(rows[row_id], arm) for row_id in prepared["training_order"][0]]
    delta = torch.tensor([.01 if passed else -.01], dtype=torch.float32)
    head = [torch.tensor([.5], dtype=torch.float64), torch.tensor([-.5], dtype=torch.float64)]
    before, after = [], []
    for sign in signs:
        for value, destination in ((0., before), (sign * delta.item(), after)):
            _, surface = q0.head_margin(torch.tensor([value], dtype=torch.float64), head, POLICY)
            surface["z_train32"] = [value / 2, -value / 2]
            destination.append(surface)
    raw = dict(policy_sha256=q0.digest(vars(POLICY)), signs=signs,
               parameters_before=[q0.tensor_payload(torch.zeros(1))], parameters_after=[q0.tensor_payload(delta)],
               delta=[q0.tensor_payload(delta)], signed_gradients=[[q0.tensor_payload(torch.ones(1))] for _ in range(4)],
               before=before, after=after)
    return q0.replay_canary(raw, POLICY), raw


def fit_fixture(prepared, audit, arm, passed=True, diagnostic_only=False):
    updates = 128
    canary, canary_raw = canary_fixture(prepared, arm, passed)
    return dict(arm=arm, diagnostic_only=diagnostic_only, initial=copy.deepcopy(audit["initial"]),
                updates=updates, training_forwards=updates * 4, canary=canary, canary_raw=canary_raw,
                snapshots={str(update): dict(adapter_sha256=q0.digest([arm, update]), fixture=True)
                           for update in q0.SNAPSHOTS} if updates == 128 else {},
                steps=[dict(update=index + 1, row_ids=row_ids, loss=.5,
                            rng=[dict(cpu=q0.digest([index, position]), cuda=[]) for position in range(4)])
                       for index, row_ids in enumerate(prepared["training_order"][:updates])])


def evidence_fixture(prepared, tokenizer, *, nondegenerate=False, auth=True, deranged=True):
    audit = audit_fixture(prepared, nondegenerate)
    fits = [fit_fixture(prepared, audit, "P_AUTH", auth),
            fit_fixture(prepared, audit, "P_DERANGED", deranged)]
    readouts = {"OFF/0": readout_fixture(prepared, tokenizer, "OFF", 0)}
    for fit in fits:
        for snapshot in q0.SNAPSHOTS:
            readouts[fit["arm"] + "/" + str(snapshot)] = readout_fixture(prepared, tokenizer, fit["arm"], snapshot)
    return dict(evidence_kind="CPU_FIXTURE_ONLY", prepared_sha256=q0.digest(prepared),
                audit=audit, fits=fits, readouts=readouts)


@unittest.skipIf(torch is None, "real CPU Torch unavailable; no mock substitution")
class NumericalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_explicit_p_v_identity_target_reversal_and_outside_gradient(self):
        logits = torch.tensor([.2, -.3, .8], dtype=torch.float32, requires_grad=True)
        for bit in (0, 1):
            pairwise, vocabulary, negative_log_mass = q0.losses(logits, [0, 1], bit)
            self.assertAlmostEqual((vocabulary - pairwise).item(), negative_log_mass.item(), places=6)
            pair_grad = torch.autograd.grad(pairwise, logits, retain_graph=True)[0]
            vocab_grad = torch.autograd.grad(vocabulary, logits)[0]
            self.assertEqual(pair_grad[2].item(), 0)
            self.assertGreater(vocab_grad[2].item(), 0)
        self.assertAlmostEqual(q0.losses(logits, [0, 1], 0)[0].item(),
                               q0.losses(-logits, [0, 1], 1)[0].item(), places=6)

    def test_bf16_training_surface_is_explicit_fp32(self):
        values = q0.losses(torch.tensor([1., -1., 0.], dtype=torch.bfloat16), [0, 1], 0)
        self.assertTrue(all(value.dtype == torch.float32 for value in values))

    def test_missing_nonfinite_and_wrong_inventory_gradients_abort(self):
        parameter = torch.zeros(2, dtype=torch.float32)
        for gradient in (None, torch.tensor([math.nan, 0]), torch.zeros(3)):
            with self.assertRaises(q0.IntegrityError):
                q0.gradient_comparison([gradient], [parameter], [parameter], POLICY)

    def test_zero_and_nearzero_norm_explicit_no_epsilon_cosine(self):
        parameter = torch.zeros(1, dtype=torch.float32)
        for value in (0., 1e-13):
            result = q0.gradient_comparison([torch.tensor([value])], [torch.ones(1)], [parameter], POLICY)
            self.assertTrue(result["zero_P"])
            self.assertIsNone(result["cosine"])
            self.assertGreater(result["norm_V"], 0)

    def test_fp64_cast_before_multiply(self):
        first = torch.tensor([1e20, 1e20], dtype=torch.float32)
        second = torch.tensor([1e20, -1e20], dtype=torch.float32)
        result = q0.fp64_dot([first], [second], POLICY.safety)
        self.assertEqual(result["dot"], 0)
        self.assertTrue(math.isfinite(result["abs_sum"]))
        self.assertFalse(result["passed"])

    def test_fp64_bound_and_equality_predicate(self):
        result = q0.fp64_dot([torch.ones(2)], [torch.ones(2)], POLICY.safety)
        self.assertEqual(result["bound"], POLICY.safety * q0.gamma(1) * 2)
        self.assertTrue(result["passed"])
        gradients = [[torch.ones(1)] for _ in range(4)]
        before = [dict(d_canary64=0., bound=0., head_sha256=["fixed"])] * 4
        after = [dict(d_canary64=1., bound=0., head_sha256=["fixed"])] * 4
        equal = q0.canary_result(gradients, [torch.zeros(1)], before, after, [1] * 4, POLICY)
        adjacent = q0.canary_result(gradients, [torch.nextafter(torch.zeros(1), torch.ones(1))],
                                    before, after, [1] * 4, POLICY)
        self.assertFalse(equal["passed"])
        self.assertTrue(adjacent["passed"])
        bound_before = [dict(d_canary64=0., bound=1 - POLICY.safety * 2. ** -53, head_sha256=["fixed"])] * 4
        equal = q0.canary_result(gradients, [torch.ones(1)], bound_before, after, [1] * 4, POLICY)
        adjacent_after = [dict(d_canary64=math.nextafter(1., math.inf), bound=0., head_sha256=["fixed"])] * 4
        adjacent = q0.canary_result(gradients, [torch.ones(1)], bound_before, adjacent_after, [1] * 4, POLICY)
        self.assertEqual(equal["observed"][0]["signed_change"], equal["observed"][0]["bound"])
        self.assertFalse(equal["passed"])
        self.assertTrue(adjacent["passed"])

    def test_post_float32_conversion_overflow_and_safe_median(self):
        with self.assertRaises(q0.IntegrityError):
            q0.losses(torch.tensor([1e308, 0.], dtype=torch.float64), [0, 1], 0)
        self.assertEqual(q0.median([1e308, 1e308], POLICY), 1e308)
        self.assertEqual(q0.median([-1e308, 1e308], POLICY), 0.)

    def test_directional_dot_rejects_arbitrary_float64_product_domain(self):
        gradients = [[torch.ones(1, dtype=torch.float64)]] * 4
        with self.assertRaisesRegex(q0.IntegrityError, "FP32"):
            q0.canary_result(gradients, [torch.ones(1)], [{}] * 4, [{}] * 4, [1] * 4, POLICY)

    def test_binary_tensor_artifacts_and_readonly_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            tensor = torch.tensor([1., -2., 3.])
            with q0.tensor_store(folder, writable=True):
                payload = q0.tensor_payload(tensor)
            self.assertIn("tensor_file", payload)
            with q0.tensor_store(folder):
                self.assertTrue(torch.equal(q0.payload_tensor(payload), tensor))
                self.assertEqual(q0.tensor_payload(tensor), payload)
            Path(folder, payload["tensor_file"]).write_bytes(b"broken")
            with q0.tensor_store(folder), self.assertRaises(q0.IntegrityError):
                q0.payload_tensor(payload)

    def test_held_even_median_is_explicit_fixture_parameter(self):
        self.assertEqual(q0.median([-2., -1., 1., 8.], POLICY), 0)
        self.assertGreater(q0.median([-2., -1., 1.000001, 8.], POLICY), 0)

    def test_diagnostic_state_mutations_are_detected(self):
        for mutation in ("rng", "parameter", "buffer", "grad", "mode", "optimizer"):
            torch.manual_seed(1)
            model = torch.nn.Linear(2, 1)
            model.register_buffer("marker", torch.zeros(1))
            optimizer = q0.adamw(model)
            with self.subTest(mutation=mutation), self.assertRaises(q0.IntegrityError):
                with q0.neutral_diagnostic(model, optimizer):
                    if mutation == "rng":
                        torch.rand(1)
                    elif mutation == "parameter":
                        with torch.no_grad():
                            model.weight.add_(1)
                    elif mutation == "buffer":
                        model.marker.add_(1)
                    elif mutation == "grad":
                        model.weight.grad = torch.ones_like(model.weight)
                    elif mutation == "mode":
                        model.train()
                    else:
                        optimizer.param_groups[0]["lr"] = .1

    def test_optimizer_reorder_field_and_initial_state_rejected(self):
        model = torch.nn.Linear(2, 1)
        optimizer = q0.adamw(model)
        q0.audit_optimizer(model, optimizer)
        optimizer.param_groups[0]["params"].reverse()
        with self.assertRaisesRegex(q0.IntegrityError, "order"):
            q0.audit_optimizer(model, optimizer)
        optimizer = q0.adamw(model)
        optimizer.param_groups[0]["lr"] = .01
        with self.assertRaisesRegex(q0.IntegrityError, "field"):
            q0.audit_optimizer(model, optimizer)

    def test_all_four_canary_cheap_policies_and_true_xor(self):
        signs = [1, -1, -1, 1]
        for name, features in (("constant", [1, 1, 1, 1]), ("mode", [1, -1, 1, -1]),
                               ("tool", [1, 1, -1, -1]), ("xor", signs)):
            gradients = [[torch.tensor([float(sign * feature)])] for sign, feature in zip(signs, features)]
            before = [dict(d_canary64=0., bound=0., head_sha256=["fixed"])] * 4
            after = [dict(d_canary64=feature * .01, bound=1e-16, head_sha256=["fixed"]) for feature in features]
            result = q0.canary_result(gradients, [torch.tensor([.01])], before, after, signs, POLICY)
            self.assertEqual(result["passed"], name == "xor")
            self.assertEqual(len(result["gram"]), 4)

    def toy(self, policy_name):
        class Toy(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.weight = torch.nn.Parameter(torch.zeros(1))
                self.head = torch.nn.Module()
                self.head.register_parameter("weight", torch.nn.Parameter(torch.tensor([[.5], [-.5]]), requires_grad=False))
                self.dropout = torch.nn.Dropout(.05)

            def get_output_embeddings(self):
                return self.head

            def forward(self, input_ids, use_cache=False, output_hidden_states=False):
                self.assert_cpu(input_ids)
                orientation, mode = input_ids[0].tolist()
                feature = {"constant": 1, "mode": 1 - 2 * mode, "tool": 1 - 2 * orientation,
                           "xor": (1 - 2 * orientation) * (1 - 2 * mode)}[policy_name]
                hidden = (self.dropout(torch.ones(1)) * self.weight * feature).reshape(1, 1, 1)
                return SimpleNamespace(logits=hidden @ self.head.weight.T, hidden_states=(hidden,))

            @staticmethod
            def assert_cpu(input_ids):
                assert input_ids.device.type == "cpu" and input_ids.shape == (1, 2)

        torch.manual_seed(1)
        model = Toy()
        return model, q0.adamw(model)

    def toy_prepared(self):
        prepared = q0.build_prepared(TokenizerFixture())
        for row in prepared["rows"]:
            if row["panel"] == "exact":
                row["input_ids"] = [q0.ORIENTATION[row["slot"]], row["mode"]]
                row["branch_ids"] = [0, 1]
        return prepared

    def test_real_cpu_autograd_adamw_128_uninterrupted_quartets(self):
        prepared = self.toy_prepared()
        model, optimizer = self.toy("xor")
        audit = q0.objective_audit(model, optimizer, prepared, POLICY, q0.Budget(0, 4000, clock=lambda: 0))
        self.assertEqual(audit["optimizer_steps"], 0)
        model, optimizer = self.toy("xor")
        events, snapshot_updates = [], []

        def save_snapshot(update, current):
            snapshot_updates.append(update)
            return {"tensor_sha256": q0.digest(q0.ordered_inventory(q0.trainables(current)))}

        result = q0.train_fit(model, optimizer, prepared, "P_AUTH", audit["initial"], POLICY,
                              q0.Budget(0, 4000, clock=lambda: 0),
                              lambda name, payload: events.append((name, payload)), save_snapshot)
        self.assertTrue(result["canary"]["passed"])
        self.assertEqual(result["updates"], 128)
        self.assertEqual(result["training_forwards"], 512)
        self.assertEqual(snapshot_updates, [32, 64, 128])
        self.assertEqual(sum(name == "step" for name, _ in events), 128)
        self.assertEqual(optimizer.state[model.weight]["step"].item(), 128)
        self.assertEqual(result["canary"]["surface"], "d_canary64")



    def test_real_cpu_snapshot_rng_mutation_aborts(self):
        prepared = self.toy_prepared()
        model, optimizer = self.toy("xor")
        audit = q0.objective_audit(model, optimizer, prepared, POLICY, q0.Budget(0, 4000, clock=lambda: 0))
        model, optimizer = self.toy("xor")

        def bad_save(*args):
            torch.rand(1)
            return dict(fixture=True)

        with self.assertRaisesRegex(q0.IntegrityError, "snapshot mutated"):
            q0.train_fit(model, optimizer, prepared, "P_AUTH", audit["initial"], POLICY,
                         q0.Budget(0, 4000, clock=lambda: 0), lambda *args: None, bad_save)



@unittest.skipIf(torch is None, "real CPU Torch unavailable; no mock substitution")
class ReducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = TokenizerFixture()
        cls.prepared = q0.build_prepared(cls.tokenizer)
        cls.evidence = evidence_fixture(cls.prepared, cls.tokenizer)

    def reduce(self, evidence):
        return q0.reduce_evidence(self.prepared, evidence, self.tokenizer, POLICY)

    def test_full_two_map_pass_and_exact_work_counts(self):
        result = self.reduce(self.evidence)
        self.assertEqual(result["label"], "Q0_V2_FULL_DOSE_ENDPOINT_PASS", result)
        self.assertEqual(result["updates"], 256)
        self.assertEqual(result["training_forwards"], 1024)
        self.assertEqual(result["prefix_readouts"], 1632)
        self.assertEqual(result["generations"], 888)
        self.assertFalse(result["scientific_claim"])




    def test_missing_duplicate_and_cross_state_records_abort(self):
        for mutation in ("missing", "duplicate", "cross_state", "attempt"):
            changed = copy.deepcopy(self.evidence)
            rows = changed["readouts"]["P_AUTH/128"]
            if mutation == "missing":
                rows.pop()
            elif mutation == "duplicate":
                rows[-1] = rows[0]
            elif mutation == "cross_state":
                rows[0]["state"] = "V_AUTH"
            else:
                rows[0]["attempts"] = 2
            self.assertEqual(self.reduce(changed)["label"], "NONREPORTABLE_RUNTIME_ABORT")

    def test_rng_snapshot_update_initialization_drift_abort(self):
        for mutation in ("rng", "snapshots", "updates", "initial"):
            changed = copy.deepcopy(self.evidence)
            fit = changed["fits"][1]
            if mutation == "rng":
                fit["steps"][0]["rng"][0]["cpu"] = "different"
            elif mutation == "snapshots":
                del fit["snapshots"]["64"]
            elif mutation == "updates":
                fit["updates"] = 127
            else:
                fit["initial"] = {"different": True}
            self.assertEqual(self.reduce(changed)["label"], "NONREPORTABLE_RUNTIME_ABORT")

    def test_integrity_precedence_over_science(self):
        changed = copy.deepcopy(self.evidence)
        changed["integrity_abort"] = "NONREPORTABLE_RUNTIME_ABORT"
        self.assertEqual(self.reduce(changed)["label"], "NONREPORTABLE_RUNTIME_ABORT")

    def test_native_receipts_cannot_promote_cpu_fixtures(self):
        changed = copy.deepcopy(self.evidence)
        changed["evidence_kind"] = "REAL_GPU_EXECUTION"
        self.assertEqual(self.reduce(changed)["label"], "NONREPORTABLE_RUNTIME_ABORT")

    def test_raw_canary_or_audit_summary_tampering_aborts(self):
        for mutation in ("canary", "delta", "gradient", "audit"):
            changed = copy.deepcopy(self.evidence)
            if mutation == "canary":
                changed["fits"][0]["canary"]["projections"][0]["dot"] *= 2
            elif mutation == "delta":
                changed["fits"][0]["canary_raw"]["delta"][0]["values"][0] *= -1
            elif mutation == "gradient":
                changed["fits"][0]["canary_raw"]["signed_gradients"][0][0]["values"][0] *= 2
            else:
                changed["audit"]["quartets"][0]["norm_P"] *= 2
            self.assertEqual(self.reduce(changed)["label"], "NONREPORTABLE_RUNTIME_ABORT")

    def test_boole_common_offset_producer_validator_round_trip(self):
        request = q0.request_inventory(self.prepared, "OFF", 0)[0]
        row = next(row for row in self.prepared["rows"] if row["id"] == request["row_id"])
        for offset in (0., 1000., -1000.):
            for outside in (-100., -20., 0.):
                output = q0.prefix_record(torch.tensor([offset, offset, offset + outside]), [0, 1])
                q0.validate_record(dict(request, output=output), request, row, self.tokenizer)
                self.assertEqual(q0.canonical_prefix(output), output)
                self.assertLessEqual(output["M"], 1.)

    def test_boole_accepted_ulp_drift_cannot_flip_mean_or_tail_gates(self):
        for baseline_q in (.45, .40):
            off_records = readout_fixture(self.prepared, self.tokenizer, "OFF", 0)
            on_records = readout_fixture(self.prepared, self.tokenizer, "P_AUTH", 128)
            by_id = {row["id"]: row for row in self.prepared["rows"]}
            for records, q_value in ((off_records, baseline_q), (on_records, .5)):
                for record in records:
                    if by_id[record["row_id"]]["panel"] == "missing" and record["operation"] == "prefix":
                        difference = math.log(q_value / (1 - q_value))
                        record["output"] = q0.canonical_prefix(prefix_output(difference, .5))
            off = q0.indexed_readout(self.prepared, off_records, "OFF", 0, self.tokenizer)
            on = q0.indexed_readout(self.prepared, on_records, "P_AUTH", 128, self.tokenizer)
            initial = q0.locality_gates(self.prepared["rows"], on, off, "missing")
            for record in on_records:
                if by_id[record["row_id"]]["panel"] == "missing" and record["operation"] == "prefix":
                    record["output"]["q"] = math.nextafter(record["output"]["q"], math.inf)
                    record["output"]["M"] = math.nextafter(record["output"]["M"], math.inf)
            canonical_on = q0.indexed_readout(self.prepared, on_records, "P_AUTH", 128, self.tokenizer)
            self.assertEqual(on, canonical_on)
            self.assertEqual(initial, q0.locality_gates(self.prepared["rows"], canonical_on, off, "missing"))

    def test_locality_itemwise_noncancellation_and_discrete_boundaries(self):
        rows = self.prepared["rows"]
        for family, size in q0.LOCALITY_COUNTS.items():
            selected = [row for row in rows if row["panel"] == family]
            off = {row["id"]: dict(q=.5, M=.5, identity="MEM2REG") for row in selected}
            on = copy.deepcopy(off)
            cap = 3 if size == 64 else 0
            for row in selected[:cap]:
                on[row["id"]]["identity"] = "GVN"
            self.assertTrue(q0.locality_gates(rows, on, off, family)["passed"])
            on[selected[cap]["id"]]["identity"] = "GVN"
            self.assertFalse(q0.locality_gates(rows, on, off, family)["passed"])
            for index, row in enumerate(selected):
                on[row["id"]] = dict(q=.56 if index % 2 else .44, M=.5, identity="MEM2REG")
            self.assertFalse(q0.locality_gates(rows, on, off, family)["passed"])

    def test_locality_probability_inclusive_and_next_float(self):
        rows = [row for row in self.prepared["rows"] if row["panel"] == "missing"]
        off = {row["id"]: dict(q=0., M=0., identity="INVALID") for row in rows}
        on = {row["id"]: dict(q=.05, M=.05, identity="INVALID") for row in rows}
        self.assertTrue(q0.locality_gates(self.prepared["rows"], on, off, "missing")["passed"])
        for row in rows:
            on[row["id"]]["q"] = math.nextafter(.05, math.inf)
        self.assertFalse(q0.locality_gates(self.prepared["rows"], on, off, "missing")["passed"])

    def gate_fixture(self, panel):
        rows = [row for row in self.prepared["rows"] if row["panel"] == panel]
        off = {row["id"]: dict(d=0.) for row in rows}
        on = {row["id"]: dict(d=2. * (1 - 2 * q0.target(row, "P_AUTH")),
                               identity=("MEM2REG", "GVN")[q0.target(row, "P_AUTH")]) for row in rows}
        return rows, on, off

    def test_exact_and_held_integer_acquisition_boundaries(self):
        for panel, correct_floor, recall_floor, validity_floor in (("exact", 116, 56, 122), ("held", 52, 24, 61)):
            rows, on, off = self.gate_fixture(panel)
            wrong = []
            for bit in (0, 1):
                selected = [row for row in rows if q0.target(row, "P_AUTH") == bit]
                by_key = {}
                for row in selected:
                    by_key.setdefault((row["slot"], row["mode"]), row)
                failures = (len(rows) - correct_floor) // 2
                for row in list(by_key.values())[:failures]:
                    on[row["id"]]["identity"] = ("GVN", "MEM2REG")[bit]
                    wrong.append(row)
            gate = q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)
            self.assertEqual(gate["correct"], correct_floor)
            self.assertTrue(gate["passed"], gate)
            remaining = next(row for row in rows if row not in wrong)
            changed = copy.deepcopy(on)
            changed[remaining["id"]]["identity"] = "INVALID"
            self.assertFalse(q0.acquisition_gates(self.prepared["rows"], changed, off, "P_AUTH", panel, POLICY)["core"])
            for row in wrong[:len(rows) - validity_floor]:
                on[row["id"]]["identity"] = "INVALID"
            gate = q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)
            self.assertEqual(gate["valid"], validity_floor)
            self.assertTrue(gate["interface"])
            on[wrong[len(rows) - validity_floor]["id"]]["identity"] = "INVALID"
            self.assertFalse(q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)["interface"])

    def test_class_recall_denominators_and_adjacent_failure(self):
        for panel, floor in (("exact", 56), ("held", 24)):
            rows, on, off = self.gate_fixture(panel)
            selected = [row for row in rows if q0.target(row, "P_AUTH") == 0]
            for row in selected[:len(selected) - floor]:
                on[row["id"]]["identity"] = "GVN"
            gate = q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)
            self.assertEqual(gate["recalls"][0], floor)
            self.assertTrue(gate["core"])
            on[selected[len(selected) - floor]["id"]]["identity"] = "GVN"
            gate = q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)
            self.assertEqual(gate["recalls"][0], floor - 1)
            self.assertFalse(gate["core"])

    def test_key_coverage_and_strict_positive_gain_boundaries(self):
        for panel, good_keys in (("exact", 14), ("held", 12)):
            rows, on, off = self.gate_fixture(panel)
            keys = sorted({(row["slot"], row["mode"]) for row in rows})
            for key in keys[good_keys:]:
                selected = [row for row in rows if (row["slot"], row["mode"]) == key]
                for row in selected[:2]:
                    if panel == "exact":
                        on[row["id"]]["identity"] = "INVALID"
                    else:
                        on[row["id"]]["d"] *= -1
            gate = q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)
            self.assertEqual(gate["key_coverage"], good_keys)
            self.assertTrue(gate["key_gate"])
            selected = [row for row in rows if (row["slot"], row["mode"]) == keys[good_keys - 1]]
            for row in selected[:2]:
                if panel == "exact":
                    on[row["id"]]["identity"] = "INVALID"
                else:
                    on[row["id"]]["d"] *= -1
            self.assertFalse(q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", panel, POLICY)["key_gate"])
        rows, on, off = self.gate_fixture("exact")
        for row in rows:
            if q0.target(row, "P_AUTH") == 0:
                on[row["id"]]["d"] = 0.
        self.assertFalse(q0.acquisition_gates(self.prepared["rows"], on, off, "P_AUTH", "exact", POLICY)["gain_gate"])

    def test_complement_and_wrong_root_discrete_thresholds(self):
        fits = [dict(updates=128, canary=dict(passed=True))] * 2
        cells = {arm: dict(exact=dict(passed=True), held=dict(passed=True), passed=True)
                 for arm in ("P_AUTH", "P_DERANGED")}
        self.assertEqual(q0.primary_label(fits, cells, dict(exact=112, held=48), 3), "Q0_V2_FULL_DOSE_ENDPOINT_PASS")
        for exact, held, opposite in ((111, 48, 3), (112, 47, 3), (112, 48, 4)):
            self.assertEqual(q0.primary_label(fits, cells, dict(exact=exact, held=held), opposite),
                             "Q0_V2_FULL_DOSE_ENDPOINT_FAIL")

    def test_locality_tail_probability_boundary(self):
        rows = [row for row in self.prepared["rows"] if row["panel"] == "missing"]
        off = {row["id"]: dict(q=0., M=0., identity="INVALID") for row in rows}
        on = copy.deepcopy(off)
        on[rows[0]["id"]]["q"] = .10
        self.assertTrue(q0.locality_gates(self.prepared["rows"], on, off, "missing")["passed"])
        on[rows[0]["id"]]["q"] = math.nextafter(.10, math.inf)
        self.assertFalse(q0.locality_gates(self.prepared["rows"], on, off, "missing")["passed"])

    def test_closed_identity_enum_and_other_string_identity(self):
        self.assertEqual(q0.strict_identity("ACT: -mem2reg\n", False, True), "MEM2REG")
        self.assertEqual(q0.strict_identity("ACT: -gvn", False, True), "GVN")
        self.assertEqual(q0.strict_identity("ACT: -inline\n", False, True), "OTHER_SINGLE(-inline)")
        self.assertEqual(q0.strict_identity("ACT: -gvn\nACT: -mem2reg\n", False, True), "MULTIPLE")
        self.assertEqual(q0.strict_identity(" ACT: -gvn\n\n", False, True), "GVN")
        for text, truncated, ended in (("ACT: -gvn extra", False, True), ("ACT: -gvn", True, False),
                                       ("ACT: -gvn", False, False)):
            self.assertEqual(q0.strict_identity(text, truncated, ended), "INVALID")

    def test_sealed_replay_and_mutation_extra_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            result = q0.seal_fixture(folder, self.prepared, self.evidence, self.tokenizer, POLICY)
            replay = q0.replay(folder, self.tokenizer)
            self.assertEqual(replay["report"], result)
            self.assertFalse(replay["scientific_claim"])
            with self.assertRaises(q0.IntegrityError):
                q0.seal_fixture(folder, self.prepared, self.evidence, self.tokenizer, POLICY)
            Path(folder, "unsealed.json").write_text("{}")
            with self.assertRaisesRegex(q0.IntegrityError, "inventory"):
                q0.replay(folder, self.tokenizer)



@unittest.skipIf(torch is None, "real CPU Torch unavailable; no mock substitution")
class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = TokenizerFixture()
        cls.prepared = q0.build_prepared(cls.tokenizer)
        cls.evidence = evidence_fixture(cls.prepared, cls.tokenizer)

    def lifecycle(self):
        return q0.Lifecycle(self.prepared, self.tokenizer, POLICY, q0.Budget(0, 4000, clock=lambda: 0))

    def payload(self, ticket):
        if ticket["kind"] == "audit":
            return self.evidence["audit"]
        if ticket["kind"] == "fit":
            return next(fit for fit in self.evidence["fits"] if fit["arm"] == ticket["arm"])
        return self.evidence["readouts"][ticket["arm"] + "/" + str(ticket["snapshot"])]

    def receipt(self, ticket):
        index = ticket["sequence"]
        receipt = dict(ticket_sha256=ticket["ticket_sha256"], attempts=1, evidence_kind="CPU_FIXTURE_ONLY",
                       pid=1000 + index, process_start=index, load_id="fixture-load-" + str(index),
                       start=index, finish=index + 1, status="FINISHED", cleanup="COMPLETE")
        if ticket["kind"] == "eval" and ticket["arm"] != "OFF":
            fit = next(fit for fit in self.evidence["fits"] if fit["arm"] == ticket["arm"])
            receipt["adapter"] = fit["snapshots"][str(ticket["snapshot"]) ]
        return receipt

    def test_ten_serial_fresh_stage_tickets_without_launching(self):
        lifecycle = self.lifecycle()
        order = []
        while (ticket := lifecycle.issue()) is not None:
            order.append((ticket["kind"], ticket["arm"], ticket["snapshot"]))
            lifecycle.accept(ticket, self.payload(ticket), self.receipt(ticket))
        self.assertEqual(len(order), 10)
        self.assertEqual(order[:3], [("audit", None, None), ("eval", "OFF", 0), ("fit", "P_AUTH", None)])
        self.assertEqual(lifecycle.report()["label"], "Q0_V2_FULL_DOSE_ENDPOINT_PASS")

    def test_no_concurrent_ticket_or_retry_after_worker_failure(self):
        lifecycle = self.lifecycle()
        ticket = lifecycle.issue()
        with self.assertRaises(q0.IntegrityError):
            lifecycle.issue()
        receipt = self.receipt(ticket)
        receipt["status"] = "FAILED"
        with self.assertRaises(q0.IntegrityError):
            lifecycle.accept(ticket, self.payload(ticket), receipt)
        with self.assertRaises(q0.IntegrityError):
            lifecycle.issue()
        self.assertEqual(lifecycle.report()["label"], "NONREPORTABLE_PRECHECK_ABORT")

    def test_reused_load_or_bad_cleanup_rejected(self):
        for mutation in ("load", "cleanup"):
            lifecycle = self.lifecycle()
            ticket = lifecycle.issue()
            lifecycle.accept(ticket, self.payload(ticket), self.receipt(ticket))
            ticket = lifecycle.issue()
            receipt = self.receipt(ticket)
            if mutation == "load":
                receipt["load_id"] = "fixture-load-0"
            else:
                receipt["cleanup"] = "FAILED"
            with self.assertRaises(q0.IntegrityError):
                lifecycle.accept(ticket, self.payload(ticket), receipt)



@unittest.skipIf(torch is None, "real CPU Torch unavailable; no mock substitution")
class NativeProtocolMockTests(unittest.TestCase):
    """Disk/controller plumbing with fabricated CPU workers; NOT NATIVE PROOF."""

    @classmethod
    def setUpClass(cls):
        cls.tokenizer = TokenizerFixture()
        cls.prepared = q0.build_prepared(cls.tokenizer)

    def test_gpu_entrypoints_fail_before_import_or_process_action(self):
        with patch.object(q0, "historical_helpers", side_effect=AssertionError("must not import worker helpers")):
            with self.assertRaises(q0.IntegrityError):
                q0.native_execute("/not-a-root")
            with self.assertRaises(q0.IntegrityError):
                q0.native_worker("/not-a-root", "00_audit")

    def test_production_numerical_policy_cannot_be_tuned_through_template(self):
        config = q0.native_config_template()
        config["numerical_policy"]["safety"] = 8
        self.assertEqual(q0.PRODUCTION_POLICY.safety, 4)
        with self.assertRaises(q0.IntegrityError):
            q0.require_native_ready(config)


    def test_test_support_is_separate_hash_pinned_and_path_bounded(self):
        filename = "tests/test_semantic_writer_diagnostic.py"
        support = dict(provenance="historical fixture support", scope="ARCHIVED_REGRESSION_SUPPORT_ONLY_NOT_Q0_INPUT",
                       files={filename: q0.file_hash(q0.repository() / filename)})
        self.assertEqual(q0.validate_test_support(support), support)
        for files in ({filename: "0" * 64}, {"../outside": "0" * 64}, {}):
            with self.subTest(files=files), self.assertRaises(q0.IntegrityError):
                q0.validate_test_support(dict(support, files=files))

    def run_mock_controller(self, *, fail_at=None, cleanup_ok=True, release_raises=False,
                            corrupt_counters=False, late_write=None, verify_delay=0, fail_verify=False):
        evidence = evidence_fixture(self.prepared, self.tokenizer, auth=False, deranged=False)
        actual_diagnostic, _, _ = q0.historical_helpers()
        commands = []
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = dict(gpu_uuid="GPU-" + "1" * 36, lease_cutoff_unix=q0.time.time() + 15000, allocation=q0.allocation_spec("R0"))
            manifest = dict(version=q0.VERSION, ready=True, source_pins={}, config=config)
            q0.write_once(root, "manifest.json", manifest)
            q0.write_once(root, "prepared.json", self.prepared)
            q0.write_once(root, "PREPARED.json", {"fixture_only": True})
            diagnostic = SimpleNamespace(w0=SimpleNamespace(checked_path=lambda path: Path(path),
                assert_output_fds_outside_run=Mock(), gpu_identity=Mock(return_value={"fixture": True}),
                assert_gpu_idle=Mock(), tree_hash=actual_diagnostic.w0.tree_hash),
                carrier=SimpleNamespace(process_identity=lambda pid: dict(pid=pid, start_ticks=1)))

            def binary(value):
                if isinstance(value, dict):
                    if set(value) == {"shape", "dtype", "values", "sha256"}:
                        return q0.tensor_payload(q0.payload_tensor(value))
                    return {key: binary(item) for key, item in value.items()}
                if isinstance(value, list):
                    return [binary(item) for item in value]
                return value

            def worker(command, *, log_path, timeout, device):
                commands.append(command)
                stage = command[command.index("--stage") + 1]
                job_path = root / "jobs" / (stage + ".json")
                job = json.loads(job_path.read_bytes())
                ticket = job["ticket"]
                self.assertGreater(timeout, 0)
                self.assertLessEqual(timeout, 10800 - q0.CLEANUP_RESERVE)
                self.assertEqual(device, config["gpu_uuid"])
                pid = 10000 + ticket["sequence"]
                log_path.write_bytes(b"CPU MOCK WORKER; NOT NATIVE PROOF\n")
                cleanup = dict(pid=pid, device=device, owned_group_empty=cleanup_ok, gpu_processes_absent=cleanup_ok,
                               reservation_release_verified=cleanup_ok)
                q0.write_once(log_path.parent, stage + ".cleanup.json", cleanup)
                if fail_at == ticket["sequence"]:
                    raise RuntimeError("injected mock worker failure")
                directory = root / "stages" / stage
                (directory / "events").mkdir()
                kind, arm, snapshot = ticket["kind"], ticket["arm"], ticket["snapshot"]
                if kind == "audit":
                    payload = copy.deepcopy(evidence["audit"])
                elif kind == "fit":
                    payload = copy.deepcopy(next(fit for fit in evidence["fits"] if fit["arm"] == arm))
                    for update in q0.SNAPSHOTS:
                        path = directory / "snapshots" / str(update)
                        path.mkdir(parents=True)
                        (path / "mock_adapter.bin").write_bytes(b"CPU MOCK; NOT AN ADAPTER")
                        payload["snapshots"][str(update)] = dict(path=path.relative_to(root).as_posix(),
                                                                 adapter_sha256=actual_diagnostic.w0.tree_hash(path),
                                                                 lora_sha256=q0.digest([arm, update]))
                else:
                    payload = copy.deepcopy(evidence["readouts"][arm + "/" + str(snapshot)])
                with q0.tensor_store(root, writable=True):
                    payload = binary(payload)
                    if kind == "audit":
                        branches = self.prepared["branch_ids"]
                        logits = torch.full((max(branches) + 1,), -100., dtype=torch.float32)
                        logits[branches] = 0.
                        logits[0] = math.log(2 * math.expm1(.0001))
                        prefix_record = q0.prefix_record(logits, branches)
                        raw_logits = q0.tensor_payload(logits)
                        pair_normalizer = math.log(2.)
                        for row in payload["rows"]:
                            row.update(M=prefix_record["M"], negative_log_M=prefix_record["log_normalizer"] - pair_normalizer,
                                       logits_sha256=q0.tensor_hash(logits), emitted_dtype="torch.float32",
                                       raw_z_train32=raw_logits, prefix=prefix_record)
                        payload["raw_logits_recorded"] = True
                        payload["decision"] = q0.classify_audit(payload["rows"], payload["quartets"], POLICY)
                events = []

                def event(name, value):
                    path = f"{len(events):04d}_{name}.json"
                    q0.write_once(directory / "events", path, value)
                    events.append(dict(path=path, sha256=q0.file_hash(directory / "events" / path)))

                if kind == "fit":
                    event("initial", payload["initial"])
                    event("canary_after", dict(result=payload["canary"], delta=payload["canary_raw"]["delta"]))
                    for step in payload["steps"]:
                        event("step", step)
                    prefix = 128 + 4 * payload["updates"] + 16
                    calls = prefix
                elif kind == "eval":
                    for record in payload:
                        event("readout", record)
                    prefix = sum(record["operation"] == "prefix" for record in payload)
                    calls = prefix + sum(len(record["output"]["generated_ids"]) for record in payload if record["operation"] == "generate")
                else:
                    prefix, calls = 128, 128
                load = dict(allocation=self.prepared["allocation"], recipe=self.prepared["recipe"], identity=dict(pid=pid, start_ticks=pid), load_id=str(pid),
                            ticket_sha256=ticket["ticket_sha256"], job_sha256=q0.file_hash(job_path), adapter=job.get("adapter"))
                if corrupt_counters and kind == "audit":
                    calls += 1
                q0.write_once(directory, "DONE.json", dict(result=payload, events=events, load=load, finished=q0.time.time(),
                    counters=dict(natural_prefix_forwards=prefix, model_forward_calls=calls)))
                return pid

            def release(device):
                if release_raises:
                    raise RuntimeError("fixture release query unavailable")
                return cleanup_ok

            offset = [0.]
            real_time, real_monotonic, original_write = q0.time.time, q0.time.monotonic, q0.write_once

            def verify(path):
                offset[0] += verify_delay
                if fail_verify:
                    raise q0.IntegrityError("fixture input verification rejected")
                return manifest, self.prepared, self.tokenizer

            def write(path, name, value):
                original_write(path, name, value)
                if name == late_write:
                    offset[0] += 10801

            supervisor = SimpleNamespace(run_worker=worker, gpu_processes_absent=release)
            with patch.object(q0, "historical_helpers", return_value=(diagnostic, supervisor, {})), \
                    patch.object(q0, "native_verify", side_effect=verify), \
                    patch.object(q0.time, "time", side_effect=lambda: real_time() + offset[0]), \
                    patch.object(q0.time, "monotonic", side_effect=lambda: real_monotonic() + offset[0]), \
                    patch.object(q0, "write_once", side_effect=write), \
                    patch.dict(q0.os.environ, CUDA_VISIBLE_DEVICES=config["gpu_uuid"], CUBLAS_WORKSPACE_CONFIG=":4096:8"):
                result = q0.native_execute(root, allow_gpu=True)
                before = q0.inventory(root)
                self.assertEqual(q0.native_replay(root), result)
                self.assertEqual(q0.inventory(root), before)
                with self.assertRaises(q0.IntegrityError):
                    q0.native_execute(root, allow_gpu=True)
                self.assertTrue((root / "SEAL.json").is_file())
                self.assertFalse(json.loads((root / "reduction.json").read_bytes())["scientific_claim"])
                self.assertEqual(json.loads((root / "SEAL.json").read_bytes())["classification"],
                                 "PENDING_DURABLE_FINALIZATION")
                self.assertEqual(len(list((root / "stages").iterdir())), len(commands))
                if corrupt_counters:
                    raw = json.loads((root / "stages/00_audit/DONE.json").read_bytes())
                    self.assertEqual(raw["counters"]["model_forward_calls"], 129)
                    self.assertIn("exact native forward/token work accounting", (root / "FAILED.json").read_text())
                if release_raises:
                    self.assertFalse(result["report"]["resource"]["gpu_release_verified"])
                    self.assertIn("fixture release query unavailable", (root / "FAILED.json").read_text())
                if late_write:
                    self.assertTrue((root / "FINALIZATION_ABORT.json").is_file())
                return result, commands

    def test_mock_native_controller_exact_replay_is_not_native_proof(self):
        result, commands = self.run_mock_controller()
        self.assertEqual(result["report"]["label"], "Q0_V2_FULL_DOSE_ENDPOINT_PASS")
        self.assertEqual(len(commands), 10)
        self.assertEqual(result["report"]["attempted_fits"], 2)
        self.assertIn("BOTH_MAP_FIRST_STEP_MISS", result["report"]["qualifiers"])
        self.assertEqual(result["report"]["counters"]["natural_prefix_forwards"], 3072)
        self.assertEqual(result["report"]["counters"]["model_forward_calls"], 3072 + result["report"]["generated_tokens"])
        self.assertTrue(all(command[3] == "gpu.astra_pairwise_q0_fulldose" for command in commands))
        self.assertEqual(result["report"]["resource"]["seconds_cap"], 10800)
        self.assertEqual(result["report"]["resource"]["collection_reserve_seconds"], 180)

    def test_mock_worker_failure_preserves_partial_and_never_retries(self):
        result, commands = self.run_mock_controller(fail_at=2)
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_RUNTIME_ABORT")
        self.assertEqual(len(commands), 3)
        self.assertFalse(result["report"]["scientific_claim"])

    def test_mock_cleanup_failure_never_becomes_scientific_null(self):
        result, commands = self.run_mock_controller(cleanup_ok=False)
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_PRECHECK_ABORT")
        self.assertEqual(len(commands), 1)

    def test_mock_final_raw_counter_rejection_replays_abort_without_validating_rejected_stage(self):
        result, commands = self.run_mock_controller(corrupt_counters=True)
        self.assertEqual(len(commands), 10)
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_RUNTIME_ABORT")
        self.assertFalse(result["report"]["scientific_claim"])
        self.assertEqual(result["report"]["counters"], {})

    def test_mock_final_release_query_exception_preserves_replayable_abort(self):
        result, commands = self.run_mock_controller(release_raises=True)
        self.assertEqual(len(commands), 10)
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_RUNTIME_ABORT")
        self.assertFalse(result["report"]["scientific_claim"])

    def test_mock_terminal_writes_crossing_cap_never_publish_scientific_report(self):
        for filename in ("RESOURCE.json", "reduction.json", "SEAL.json", "FINALIZED.json"):
            with self.subTest(filename=filename):
                result, commands = self.run_mock_controller(late_write=filename)
                self.assertEqual(len(commands), 10)
                self.assertEqual(result["report"]["label"], "NONREPORTABLE_RUNTIME_ABORT")
                self.assertFalse(result["report"]["scientific_claim"])
                self.assertGreaterEqual(result["report"]["late_publication"]["elapsed_seconds"], 10800)

    def test_mock_slow_execute_verification_spends_original_budget_before_any_worker(self):
        result, commands = self.run_mock_controller(verify_delay=10801)
        self.assertEqual(commands, [])
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_PRECHECK_ABORT")
        self.assertGreaterEqual(result["report"]["resource"]["elapsed_seconds"], 10800)

    def test_mock_failed_execute_verification_replays_abort_without_loading_tokenizer(self):
        result, commands = self.run_mock_controller(fail_verify=True)
        self.assertEqual(commands, [])
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_PRECHECK_ABORT")



@unittest.skipIf(torch is None, "real CPU Torch unavailable")
class ForwardCounterPlumbingTests(unittest.TestCase):
    """Torch hook/context mechanics only; patched path is NOT Qwen/PEFT proof."""

    def test_counter_removal_and_backward_does_not_double_count(self):
        decoder = torch.nn.Linear(2, 2)
        with patch.object(q0, "qwen_forward_decoder", return_value=decoder):
            with q0.native_forward_counter(None) as counts:
                output = decoder(torch.ones(1, 2))
                output.sum().backward()
                self.assertEqual(dict(counts), dict(natural_prefix_forwards=0, model_forward_calls=1))
            decoder(torch.ones(1, 2))
        self.assertEqual(counts["model_forward_calls"], 1)
        self.assertEqual(len(decoder._forward_pre_hooks), 0)
        self.assertIsNone(q0._FORWARD_COUNTS.get())

    def test_exception_removes_hook_and_restores_counter_context(self):
        decoder = torch.nn.Linear(2, 2)
        with patch.object(q0, "qwen_forward_decoder", return_value=decoder):
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with q0.native_forward_counter(None):
                    raise RuntimeError("fixture failure")
        self.assertEqual(len(decoder._forward_pre_hooks), 0)
        self.assertIsNone(q0._FORWARD_COUNTS.get())

    def test_nested_counter_rejected_without_damaging_outer_counter(self):
        decoder = torch.nn.Linear(2, 2)
        with patch.object(q0, "qwen_forward_decoder", return_value=decoder):
            with q0.native_forward_counter(None) as counts:
                with self.assertRaisesRegex(q0.IntegrityError, "one isolated forward counter"):
                    with q0.native_forward_counter(None):
                        self.fail("nested instrumentation accepted")
                decoder(torch.ones(1, 2))
                self.assertIs(q0._FORWARD_COUNTS.get(), counts)
        self.assertEqual(counts["model_forward_calls"], 1)
        self.assertIsNone(q0._FORWARD_COUNTS.get())



class AllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = TokenizerFixture()
        cls.material = q0.read_original_capsule()
        cls.prepared = {replica: q0.build_prepared(cls.tokenizer, replica=replica) for replica in q0.ALLOCATIONS}

    def test_three_exact_prospective_allocations_and_no_global_seed_mutation(self):
        for index, (replica, prepared) in enumerate(self.prepared.items()):
            self.assertEqual(prepared["allocation"], dict(replica=replica, identifier_seed=501 + index, learner_seed=1 + index))
            self.assertEqual(prepared["recipe"], dict(q0.RECIPE, seed=1 + index))
            self.assertEqual(Counter(row["panel"] for row in prepared["rows"]), q0.PANEL_COUNTS)
            q0.validate_prepared(prepared, self.tokenizer)
        self.assertEqual(q0.RECIPE["seed"], 1)
        self.assertEqual(len({item["campaign_sha256"] for item in self.prepared.values()}), 1)

    def test_public_renaming_is_only_prompt_change_and_source_rows_are_joined(self):
        original = q0.source_rows(self.material)
        used = set()
        for prepared in self.prepared.values():
            replacements = prepared["substitutions"]
            self.assertFalse(used & set(replacements.values()))
            used.update(replacements.values())
            for source, actual in zip(original, prepared["rows"]):
                restored = actual["prompt"]
                for old, new in replacements.items():
                    restored = restored.replace(new, old)
                self.assertEqual(restored, source["prompt"])
                self.assertEqual(actual["source_row_sha256"], q0.digest(source))
                if source["panel"] == "copy":
                    self.assertEqual(actual["prompt"], source["prompt"])
                self.assertFalse(set(actual) & {"target", "hidden_map", "learner_seed", "replica"})
        self.assertEqual(len(used), 96)

    def test_allocation_order_and_quartet_balance_are_target_independent(self):
        for prepared in self.prepared.values():
            rows = {row["id"]: row for row in prepared["rows"]}
            self.assertEqual(len(prepared["quartets"]), 32)
            self.assertEqual(len(prepared["training_order"]), 128)
            counts = Counter()
            for quartet in prepared["training_order"]:
                counts.update(quartet)
                for arm in q0.ARMS:
                    self.assertEqual(Counter(q0.target(rows[row_id], arm) for row_id in quartet), {0: 2, 1: 2})
            self.assertEqual(set(counts.values()), {4})
            self.assertEqual({rows[row_id]["panel"] for row_id in counts}, {"exact"})
            changed = copy.deepcopy(prepared["rows"])
            for row in changed:
                row["target"] = "not a scheduling input"
            self.assertEqual(q0.schedule(changed), prepared["quartets"])

    def test_no_v1_preparation_or_seed_prompt_campaign_drift(self):
        from gpu import astra_pairwise_q0 as legacy
        with self.assertRaises(q0.IntegrityError):
            q0.validate_prepared(legacy.build_prepared(self.tokenizer), self.tokenizer)
        for key in ("seed", "prompt", "campaign", "scope"):
            changed = copy.deepcopy(self.prepared["R1"])
            if key == "seed":
                changed["allocation"]["learner_seed"] = 1
            elif key == "prompt":
                changed["rows"][0]["prompt"] += " call0001"
            elif key == "scope":
                changed["evidence_scope"] = "CLEAN"
            else:
                changed["campaign_sha256"] = "0" * 64
            with self.subTest(key=key), self.assertRaises(q0.IntegrityError):
                q0.validate_prepared(changed, self.tokenizer)
        for name, expected in q0.LEGACY_PINS.items():
            self.assertEqual(q0.file_hash(q0.repository() / name), expected)

    def test_config_and_cli_reject_unregistered_allocation_or_version(self):
        with self.assertRaises(q0.IntegrityError):
            q0.native_config_template("R3")
        with self.assertRaises(q0.IntegrityError):
            q0.main(["execute", "--expected-version", "v1", "--allow-gpu"])
        for replica in q0.ALLOCATIONS:
            config = q0.native_config_template(replica)
            config["allocation"]["learner_seed"] += 1
            with self.assertRaisesRegex(q0.IntegrityError, "allocation"):
                q0.validate_native_config(config)


@unittest.skipIf(torch is None, "real CPU Torch unavailable")
class FullDoseTests(unittest.TestCase):
    toy = NumericalTests.toy
    toy_prepared = NumericalTests.toy_prepared

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.tokenizer = TokenizerFixture()
        cls.prepared = q0.build_prepared(cls.tokenizer)

    def test_finite_bad_canaries_reach_128_and_keep_raw_misses(self):
        prepared = self.toy_prepared()
        for name in ("constant", "mode", "tool"):
            model, optimizer = self.toy(name)
            audit = q0.objective_audit(model, optimizer, prepared, POLICY, q0.Budget(0, 20000, clock=lambda: 0))
            model, optimizer = self.toy(name)
            snapshots = []
            result = q0.train_fit(model, optimizer, prepared, "P_AUTH", audit["initial"], POLICY,
                                  q0.Budget(0, 20000, clock=lambda: 0), lambda *args: None,
                                  lambda update, current: snapshots.append(update) or {"fixture": update})
            self.assertFalse(result["canary"]["passed"], name)
            self.assertEqual(q0.replay_canary(result["canary_raw"], POLICY), result["canary"])
            self.assertEqual((result["updates"], result["training_forwards"]), (128, 512))
            self.assertEqual(snapshots, [32, 64, 128])
            self.assertEqual(optimizer.state[model.weight]["step"].item(), 128)

    def test_diagnostic_and_snapshot_callbacks_do_not_change_training(self):
        prepared = self.toy_prepared()
        model, optimizer = self.toy("mode")
        audit = q0.objective_audit(model, optimizer, prepared, POLICY, q0.Budget(0, 20000, clock=lambda: 0))
        actual, actual_optimizer = self.toy("mode")
        q0.train_fit(actual, actual_optimizer, prepared, "P_AUTH", audit["initial"], POLICY,
                     q0.Budget(0, 20000, clock=lambda: 0), lambda *args: None,
                     lambda update, current: {"update": update})
        expected, expected_optimizer = self.toy("mode")
        rows = {row["id"]: row for row in prepared["rows"]}
        for quartet in prepared["training_order"]:
            expected_optimizer.zero_grad(set_to_none=True)
            losses = [q0.losses(q0.natural_forward(expected, rows[row_id]).logits[0, -1], [0, 1],
                                q0.target(rows[row_id], "P_AUTH"))[0] for row_id in quartet]
            torch.stack(losses).mean().backward()
            expected_optimizer.step()
        actual_receipt = q0.state_receipt(actual, actual_optimizer, full_frozen=True)
        expected_receipt = q0.state_receipt(expected, expected_optimizer, full_frozen=True)
        for receipt in (actual_receipt, expected_receipt):
            receipt["frozen_versions"] = [entry[:-1] for entry in receipt["frozen_versions"]]
        self.assertEqual(actual_receipt, expected_receipt)

    def test_worker_configuration_uses_all_three_actual_rng_seeds(self):
        states = []
        for replica in q0.ALLOCATIONS:
            prepared = q0.build_prepared(self.tokenizer, replica=replica)
            config = q0.native_config_template(replica)
            def configure(settings, seed):
                torch.manual_seed(seed)
                return torch
            configure_mock = Mock(side_effect=configure)
            diagnostic = SimpleNamespace(w0=SimpleNamespace(configure_torch=configure_mock))
            q0.configure_worker_torch(diagnostic, config, prepared)
            initial = torch.rand(8)
            q0.configure_worker_torch(diagnostic, config, prepared)
            self.assertTrue(torch.equal(torch.rand(8), initial))
            configure_mock.assert_called_with(config, prepared["allocation"]["learner_seed"])
            states.append(initial)
            config["allocation"]["learner_seed"] += 1
            with self.assertRaises(q0.IntegrityError):
                q0.configure_worker_torch(diagnostic, config, prepared)
        self.assertFalse(torch.equal(states[0], states[1]))
        self.assertFalse(torch.equal(states[1], states[2]))

    def test_endpoint_qualification_is_not_canary_qualification(self):
        for auth, deranged in ((False, False), (False, True), (True, False), (True, True)):
            evidence = evidence_fixture(self.prepared, self.tokenizer, nondegenerate=True, auth=auth, deranged=deranged)
            result = q0.reduce_evidence(self.prepared, evidence, self.tokenizer, POLICY)
            self.assertEqual(result["label"], "Q0_V2_FULL_DOSE_ENDPOINT_PASS", result)
            self.assertEqual(result["first_step_canaries"]["P_AUTH"]["passed"], auth)
            self.assertEqual(result["first_step_canaries"]["P_DERANGED"]["passed"], deranged)
            self.assertEqual((result["updates"], result["training_forwards"], result["generations"], result["prefix_readouts"]),
                             (256, 1024, 888, 1632))
            self.assertEqual(q0.next_fit(evidence["audit"]["decision"], evidence["fits"][:1], {}),
                             dict(arm="P_DERANGED", diagnostic_only=False))
            self.assertIsNone(q0.next_fit(evidence["audit"]["decision"], evidence["fits"], {}))

    def test_incomplete_or_foreign_arm_cannot_be_full_dose(self):
        evidence = evidence_fixture(self.prepared, self.tokenizer, auth=False)
        for mutation in ("one_step", "extra_fit", "diagnostic", "allocation", "missing"):
            changed = copy.deepcopy(evidence)
            if mutation == "one_step":
                changed["fits"][0].update(updates=1, training_forwards=4, steps=changed["fits"][0]["steps"][:1], snapshots={})
            elif mutation == "extra_fit":
                changed["fits"].append(copy.deepcopy(changed["fits"][0]))
            elif mutation == "diagnostic":
                changed["fits"][1]["diagnostic_only"] = True
            elif mutation == "allocation":
                changed["prepared_sha256"] = "0" * 64
            else:
                del changed["readouts"]["P_DERANGED/128"]
            self.assertEqual(q0.reduce_evidence(self.prepared, changed, self.tokenizer, POLICY)["label"],
                             "NONREPORTABLE_RUNTIME_ABORT", mutation)

    def test_two_attempt_cap_and_10800_deadline(self):
        clock = [0.]
        budget = q0.Budget(0, 20000, clock=lambda: clock[0])
        self.assertEqual(budget.deadline, 10800)
        budget.attempt()
        budget.attempt()
        with self.assertRaises(q0.IntegrityError):
            budget.attempt()
        clock[0] = 10800
        with self.assertRaises(q0.IntegrityError):
            budget.check()
        self.assertEqual(q0.Budget(0, 5000, clock=lambda: 0).deadline, 5000)

    def test_pre_fit_zero_and_copy_exclusions_are_not_full_dose_outcomes(self):
        audit = audit_fixture(self.prepared, zero=True)
        evidence = dict(evidence_kind="CPU_FIXTURE_ONLY", prepared_sha256=q0.digest(self.prepared),
                        audit=audit, fits=[], readouts={})
        result = q0.reduce_evidence(self.prepared, evidence, self.tokenizer, POLICY)
        self.assertEqual(result["label"], "ZERO_XOR_TANGENT_AT_INIT")
        evidence = evidence_fixture(self.prepared, self.tokenizer)
        copy_ids = {row["id"] for row in self.prepared["rows"] if row["panel"] == "copy"}
        record = next(item for item in evidence["readouts"]["OFF/0"] if item["row_id"] in copy_ids)
        record["output"] = raw_output("bad", self.tokenizer)
        self.assertEqual(q0.reduce_evidence(self.prepared, evidence, self.tokenizer, POLICY)["label"],
                         "NONREPORTABLE_RUNTIME_ABORT")


class PublicBindingTests(unittest.TestCase):
    def receipt(self):
        receipt = json.loads((q0.repository() / q0.OFFICIAL_REFERENCE).read_bytes())
        receipt.update(node=q0.hashlib.sha256(b"fixture-node").hexdigest(), model="/fixture/model",
                       tokenizer="/fixture/model", environment={"fixture": "CPU_ONLY"})
        return receipt

    def parse(self, receipt):
        content = q0.canonical(receipt)
        return q0.public_binding_bytes(content, q0.hashlib.sha256(content).hexdigest())

    def test_new_node_receipt_keeps_literal_official_files(self):
        first = self.parse(self.receipt())
        receipt = self.receipt()
        receipt.update(node=q0.hashlib.sha256(b"another-node").hexdigest(), model="/alternate/model", tokenizer="/alternate/model")
        second = self.parse(receipt)
        self.assertNotEqual(first["receipt_sha256"], second["receipt_sha256"])
        self.assertEqual(first["files"], second["files"])
        self.assertFalse(second["clean_lineage_certified"])
        self.assertFalse(second["historical_receipts_changed"])

    def test_altered_files_origin_claims_and_old_receipt_rejected(self):
        for mutation in ("files", "clean", "historical", "revision", "node", "relative"):
            receipt = self.receipt()
            if mutation == "files":
                receipt["files"]["config.json"]["sha256"] = "0" * 64
            elif mutation == "clean":
                receipt["clean_lineage_certified"] = True
            elif mutation == "historical":
                receipt["historical_receipts_changed"] = True
            elif mutation == "revision":
                receipt["revision"] = "0" * 40
            elif mutation == "node":
                del receipt["node"]
            else:
                receipt["tokenizer"] = "relative"
            with self.subTest(mutation=mutation), self.assertRaises(q0.IntegrityError):
                self.parse(receipt)
        content = (q0.repository() / q0.OFFICIAL_REFERENCE).read_bytes()
        with self.assertRaises(q0.IntegrityError):
            q0.public_binding_bytes(content, q0.hashlib.sha256(content).hexdigest())
        with self.assertRaises(q0.IntegrityError):
            q0.public_binding_bytes(q0.canonical(self.receipt()), "0" * 64)

    def test_local_file_bytes_node_paths_and_environment_are_rechecked(self):
        diagnostic, _, _ = q0.historical_helpers()
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder, "model")
            model.mkdir()
            receipt = self.receipt()
            for name, metadata in receipt["files"].items():
                content = (q0.canonical(dict(model_type="qwen2", num_hidden_layers=28, hidden_size=3584))
                           if name == "config.json" else name.encode())
                (model / name).write_bytes(content)
                metadata.update(sha256=q0.hashlib.sha256(content).hexdigest(), size=len(content))
            receipt.update(model=str(model), tokenizer=str(model))
            config = q0.native_config_template()
            config.update(model_path=str(model), tokenizer_path=str(model), node=receipt["node"], environment=receipt["environment"],
                          gpu_uuid="GPU-11111111-1111-1111-1111-111111111111", driver_version="580.1",
                          lease_end_unix=100000, lease_cutoff_unix=70000, approved_intake="Main_DEV_v2",
                          builder_preflight_reference="CPU fixture", public_binding_path=str(Path(folder, "receipt.json")))
            Path(config["public_binding_path"]).write_bytes(q0.canonical(receipt))
            config["public_binding_sha256"] = q0.file_hash(config["public_binding_path"])
            with patch.object(q0, "OFFICIAL_FILES_SHA256", q0.digest(receipt["files"])), \
                    patch.object(q0.platform, "node", return_value="fixture-node"), \
                    patch.object(diagnostic.w0, "environment_identity", return_value=receipt["environment"]):
                binding = q0.public_binding(config["public_binding_path"], config["public_binding_sha256"])
                q0.native_input_pins(config, binding)
                for key, value in (("node", "0" * 64), ("tokenizer_path", folder), ("environment", {"other": True})):
                    changed = dict(config, **{key: value})
                    with self.subTest(key=key), self.assertRaises(q0.IntegrityError):
                        q0.native_input_pins(changed, binding)
                (model / "vocab.json").write_bytes(b"changed bytes")
                with self.assertRaises(q0.IntegrityError):
                    q0.native_input_pins(config, binding)

    @unittest.skipIf(torch is None, "real CPU Torch unavailable")
    def test_native_prepare_preserves_shape_and_binds_replica_and_support(self):
        diagnostic, _, _ = q0.historical_helpers()
        config = q0.native_config_template("R2")
        config.update(environment={"fixture": "CPU_ONLY"}, node="1" * 64,
                      gpu_uuid="GPU-11111111-1111-1111-1111-111111111111", driver_version="580.1",
                      lease_end_unix=100000, lease_cutoff_unix=70000, approved_intake="Main_DEV_v2",
                      builder_preflight_reference="CPU fixture")
        support_name = "tests/test_semantic_writer_diagnostic.py"
        support = dict(provenance="explicit fixture support", scope="ARCHIVED_REGRESSION_SUPPORT_ONLY_NOT_Q0_INPUT",
                       files={support_name: q0.file_hash(q0.repository() / support_name)})
        receipt = dict(suites=list(q0.CPU_SUITES), successful=True, failures=0, errors=0, skipped=0,
                       source_pins=q0.native_source_pins(), environment=config["environment"], platform="linux",
                       evidence_kind="CPU_REGRESSION_ONLY", test_support=support, test_support_sha256=q0.digest(support),
                       test_import_roots=[".", "tests"])
        with tempfile.TemporaryDirectory() as folder:
            receipt_path = Path(folder, "cpu.json")
            receipt_path.write_bytes(q0.canonical(receipt))
            root = Path(folder, "prepared")
            with patch.object(q0, "native_input_pins", return_value={"fixture": True}), \
                    patch.object(diagnostic.w0, "load_local_tokenizer", return_value=TokenizerFixture()):
                manifest = q0.native_prepare(root, config, receipt_path)
                self.assertEqual(manifest["recipe"]["seed"], 3)
                self.assertEqual(manifest["allocation"], q0.allocation_spec("R2"))
                self.assertEqual(manifest["test_receipt"]["test_support"], support)
                self.assertFalse(manifest["ready"])
                q0.native_verify(root)
                with self.assertRaises(q0.IntegrityError):
                    q0.native_prepare(root, config, receipt_path)
                manifest["config"]["allocation"] = q0.allocation_spec("R1")
                (root / "manifest.json").write_bytes(q0.canonical(manifest))
                (root / "PREPARED.json").write_bytes(q0.canonical(dict(manifest_sha256=q0.file_hash(root / "manifest.json"),
                    prepared_sha256=q0.file_hash(root / "prepared.json"))))
                with self.assertRaises(q0.IntegrityError):
                    q0.native_verify(root)


if __name__ == "__main__":
    unittest.main()
