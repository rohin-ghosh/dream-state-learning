"""CPU fixtures and real CPU autograd, never native Qwen or GPU proof."""
from __future__ import annotations

import copy
from collections import Counter
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pairwise_q0 as q0

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
    return dict(initial={"fixture": "same seed1 zero-B inventory and logits placeholder; NOT NATIVE",
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
    updates = 1 if not passed or diagnostic_only else 128
    canary, canary_raw = canary_fixture(prepared, arm, passed)
    return dict(arm=arm, diagnostic_only=diagnostic_only, initial=copy.deepcopy(audit["initial"]),
                updates=updates, training_forwards=updates * 4, canary=canary, canary_raw=canary_raw,
                snapshots={str(update): dict(adapter_sha256=q0.digest([arm, update]), fixture=True)
                           for update in q0.SNAPSHOTS} if updates == 128 else {},
                steps=[dict(update=index + 1, row_ids=row_ids, loss=.5,
                            rng=[dict(cpu=q0.digest([index, position]), cuda=[]) for position in range(4)])
                       for index, row_ids in enumerate(prepared["training_order"][:updates])])


def evidence_fixture(prepared, tokenizer, *, nondegenerate=False, auth=True, deranged=True, optional=True):
    audit = audit_fixture(prepared, nondegenerate)
    fits = [fit_fixture(prepared, audit, "P_AUTH", auth),
            fit_fixture(prepared, audit, "P_DERANGED", deranged, diagnostic_only=not auth)]
    if not auth or not deranged:
        fits.append(fit_fixture(prepared, audit, "P_UNARY_TOOL", optional))
    elif nondegenerate:
        fits.append(fit_fixture(prepared, audit, "V_AUTH", optional))
    readouts = {"OFF/0": readout_fixture(prepared, tokenizer, "OFF", 0)}
    for fit in fits:
        if fit["updates"] == 128:
            for snapshot in q0.SNAPSHOTS:
                readouts[fit["arm"] + "/" + str(snapshot)] = readout_fixture(prepared, tokenizer, fit["arm"], snapshot)
    return dict(evidence_kind="CPU_FIXTURE_ONLY", prepared_sha256=q0.digest(prepared),
                audit=audit, fits=fits, readouts=readouts)


class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = TokenizerFixture()
        cls.prepared = q0.build_prepared(cls.tokenizer)

    def test_original_capsule_and_four_unchanged_helpers(self):
        self.assertEqual(q0.verify_helpers(), q0.HELPER_PINS)
        self.assertEqual(tuple(q0.read_original_capsule()["roots"][1]["orientation"]), q0.ORIENTATION)

    def test_complete_frozen_topology(self):
        self.assertEqual(Counter(row["panel"] for row in self.prepared["rows"]), q0.PANEL_COUNTS)
        self.assertEqual(len(self.prepared["quartets"]), 32)
        self.assertEqual(len(self.prepared["training_order"]), 128)
        self.assertIsNone(self.prepared["confirmation_allocation"])

    def test_all_map_balance_and_complement(self):
        rows = [row for row in self.prepared["rows"] if row["panel"] == "exact"]
        for arm in q0.ARMS:
            self.assertEqual(Counter(q0.target(row, arm) for row in rows), {0: 64, 1: 64})
        for row in rows:
            self.assertEqual(q0.target(row, "P_AUTH"), 1 - q0.target(row, "P_DERANGED"))
            self.assertEqual(q0.target(row, "P_UNARY_TOOL"), q0.ORIENTATION[row["slot"]])

    def test_schedule_target_independent_and_sweeps_identical(self):
        changed = copy.deepcopy(self.prepared["rows"])
        for row in changed:
            row["target"] = "deliberately ignored; not a scheduling coordinate"
        self.assertEqual(q0.schedule(changed), self.prepared["quartets"])
        for sweep in range(4):
            self.assertEqual(self.prepared["training_order"][32 * sweep:32 * (sweep + 1)],
                             self.prepared["training_order"][:32])
        self.assertEqual(set(Counter(item for quartet in self.prepared["training_order"] for item in quartet).values()), {4})

    def test_schedule_golden_fixture(self):
        self.assertEqual(self.prepared["schedule_sha256"], "338e543b243e852b13ad93cb5d495711d08cd6898fa0e12ae4a483fc120354ff")

    def test_natural_assistant_span_all_288_prefixes(self):
        for row in self.prepared["rows"]:
            if row["panel"] == "copy":
                continue
            self.assertEqual(self.tokenizer.decode(row["input_ids"][row["assistant_boundary"]:]), "ACT: -")
            self.assertEqual(row["branch_ids"], [10536, 21404])
            self.assertEqual(row["candidates"][0][:row["decision_position"]], row["input_ids"])
            self.assertEqual(row["candidates"][1][:row["decision_position"]], row["input_ids"])
            self.assertIn("-mem2reg or ACT: -gvn", self.tokenizer.decode(row["prompt_input_ids"]))

    def test_candidate_order_reversal_same_common_prefix(self):
        for row in self.prepared["rows"]:
            if row["panel"] != "copy":
                reverse = list(reversed(row["candidates"]))
                count = next(index for index, pair in enumerate(zip(*reverse)) if pair[0] != pair[1])
                self.assertEqual(reverse[0][:count], row["input_ids"])

    def test_no_later_material_or_target_tensor_accepted(self):
        material = q0.read_original_capsule()
        material["roots"][1]["train"]["W+"][0]["context"] += "changed"
        with self.assertRaisesRegex(q0.IntegrityError, "only original"):
            q0.build_prepared(self.tokenizer, material)
        mutated = copy.deepcopy(self.prepared)
        mutated["rows"][0]["labels"] = [10536]
        with self.assertRaisesRegex(q0.IntegrityError, "reconstructed"):
            q0.validate_prepared(mutated, self.tokenizer)

    def test_input_suffix_and_panel_collision_mutations_fail(self):
        for mutation in ("suffix", "collision", "order"):
            changed = copy.deepcopy(self.prepared)
            if mutation == "suffix":
                changed["rows"][0]["input_ids"].append(10536)
            elif mutation == "collision":
                changed["rows"][1]["decision_prefix_hash"] = changed["rows"][0]["decision_prefix_hash"]
            else:
                changed["training_order"][0].reverse()
            with self.assertRaises(q0.IntegrityError):
                q0.validate_prepared(changed, self.tokenizer)

    def test_maximal_prefix_token_merge_rejected(self):
        class BadTokenizer(TokenizerFixture):
            def __call__(self, text, **kwargs):
                result = super().__call__(text, **kwargs)
                if text.endswith("ACT: -"):
                    result["input_ids"].append(198)
                return result
        with self.assertRaises(q0.IntegrityError):
            q0.build_prepared(BadTokenizer())

    def test_request_counts_and_no_intermediate_generation(self):
        for snapshot in (32, 64):
            requests = q0.request_inventory(self.prepared, "P_AUTH", snapshot)
            self.assertEqual(len(requests), 192)
            self.assertEqual({item["operation"] for item in requests}, {"prefix"})
        requests = q0.request_inventory(self.prepared, "OFF", 0)
        self.assertEqual(Counter(item["operation"] for item in requests), {"prefix": 288, "generate": 296})

    def test_native_promotion_requires_preparation_and_frozen_policy(self):
        with self.assertRaises(q0.IntegrityError):
            q0.require_native_ready()
        self.assertFalse(q0.contract_manifest()["native_launch_ready"])
        self.assertEqual(vars(q0.PRODUCTION_POLICY), vars(POLICY))

    def test_optional_main_model_only_receipt(self):
        path = Path("/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json")
        if not path.exists():
            self.skipTest("Main's permitted external model-only receipt is not installed")
        binding = q0.public_binding(path)
        self.assertFalse(binding["clean_lineage_certified"])
        self.assertEqual(len(binding["files"]), 14)
        prepared = q0.build_prepared(self.tokenizer, public_binding_path=path)
        q0.validate_prepared(prepared, self.tokenizer)


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

    def test_real_cpu_cheap_policy_canaries_stop_at_one_update(self):
        prepared = self.toy_prepared()
        for policy_name in ("constant", "mode", "tool"):
            model, optimizer = self.toy(policy_name)
            audit = q0.objective_audit(model, optimizer, prepared, POLICY, q0.Budget(0, 4000, clock=lambda: 0))
            model, optimizer = self.toy(policy_name)
            with self.subTest(policy=policy_name):
                result = q0.train_fit(model, optimizer, prepared, "P_AUTH", audit["initial"], POLICY,
                                      q0.Budget(0, 4000, clock=lambda: 0), lambda *args: None,
                                      lambda *args: self.fail("early stop cannot snapshot"))
                self.assertFalse(result["canary"]["passed"])
                self.assertEqual(result["updates"], 1)

    def test_real_cpu_unary_localizer_passes_tool_not_xor(self):
        prepared = self.toy_prepared()
        model, optimizer = self.toy("tool")
        audit = q0.objective_audit(model, optimizer, prepared, POLICY, q0.Budget(0, 4000, clock=lambda: 0))
        model, optimizer = self.toy("tool")
        result = q0.train_fit(model, optimizer, prepared, "P_UNARY_TOOL", audit["initial"], POLICY,
                              q0.Budget(0, 4000, clock=lambda: 0), lambda *args: None,
                              lambda update, current: dict(fixture_snapshot=update))
        self.assertTrue(result["canary"]["passed"])
        self.assertEqual(result["updates"], 128)

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
class AuditAndBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = q0.build_prepared(TokenizerFixture())

    def test_degeneracy_all_strict_boundaries(self):
        audit = audit_fixture(self.prepared)
        self.assertIn("DEGENERATE", audit["decision"]["contrast"])
        for field, boundary in (("negative_log_M", .001), ("R", .05), ("cosine", .999)):
            changed = copy.deepcopy(audit)
            container = changed["rows"] if field == "negative_log_M" else changed["quartets"]
            container[0][field] = boundary
            if field == "negative_log_M":
                container[0]["M"] = math.exp(-boundary)
            decision = q0.classify_audit(changed["rows"], changed["quartets"], POLICY)
            self.assertIn("NONDEGENERATE", decision["contrast"])
            container[0][field] = math.nextafter(boundary, math.inf if field == "cosine" else -math.inf)
            if field == "negative_log_M":
                container[0]["M"] = math.exp(-container[0][field])
            decision = q0.classify_audit(changed["rows"], changed["quartets"], POLICY)
            self.assertNotIn("NONDEGENERATE", decision["contrast"])

    def test_zero_tangent_is_scientific_not_integrity_branch(self):
        audit = audit_fixture(self.prepared, zero=True)
        self.assertEqual(audit["decision"]["tangent"], "ZERO_XOR_TANGENT_AT_INIT")
        self.assertTrue(audit["decision"]["all_both_zero"])
        self.assertIsNone(q0.next_fit(audit["decision"], [], {}))

    def test_2700_seconds_and_earlier_lease_cutoff(self):
        now = [0.]
        budget = q0.Budget(0, 9000, clock=lambda: now[0])
        self.assertEqual(budget.deadline, 2700)
        now[0] = 2699.999
        budget.check()
        now[0] = 2700
        with self.assertRaisesRegex(q0.IntegrityError, "deadline"):
            budget.check()
        now[0] = 0
        self.assertEqual(q0.Budget(0, 1200, clock=lambda: now[0]).deadline, 1200)

    def test_three_attempts_includes_failed_fits(self):
        budget = q0.Budget(0, 9000, clock=lambda: 0)
        for _ in range(3):
            budget.attempt()
        with self.assertRaisesRegex(q0.IntegrityError, "three-attempt"):
            budget.attempt()

    def test_release_table_all_canary_paths(self):
        audit = audit_fixture(self.prepared)
        for auth_pass in (False, True):
            for deranged_pass in (False, True):
                auth = fit_fixture(self.prepared, audit, "P_AUTH", auth_pass)
                released = q0.next_fit(audit["decision"], [auth], {})
                self.assertEqual(released, dict(arm="P_DERANGED", diagnostic_only=not auth_pass))
                deranged = fit_fixture(self.prepared, audit, "P_DERANGED", deranged_pass, not auth_pass)
                cells = {arm: dict(exact=dict(passed=True)) for arm in ("P_AUTH", "P_DERANGED")}
                released = q0.next_fit(audit["decision"], [auth, deranged], cells)
                self.assertEqual(released, None if auth_pass and deranged_pass else dict(arm="P_UNARY_TOOL", diagnostic_only=False))

    def test_no_fourth_fit_or_duplicate_attempt(self):
        audit = audit_fixture(self.prepared)
        fit = fit_fixture(self.prepared, audit, "P_AUTH")
        with self.assertRaises(q0.IntegrityError):
            q0.next_fit(audit["decision"], [fit, fit], {})


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
        self.assertEqual(result["label"], "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS", result)
        self.assertEqual(result["updates"], 256)
        self.assertEqual(result["training_forwards"], 1024)
        self.assertEqual(result["prefix_readouts"], 1632)
        self.assertEqual(result["generations"], 888)
        self.assertFalse(result["scientific_claim"])

    def test_early_auth_deranged_and_unary_qualifiers(self):
        for auth, deranged in ((False, False), (False, True), (True, False)):
            evidence = evidence_fixture(self.prepared, self.tokenizer, auth=auth, deranged=deranged, optional=False)
            result = self.reduce(evidence)
            self.assertEqual(result["label"], "EARLY_XOR_QUARTET_STOP_" + ("AUTH" if not auth else "DERANGED"), result)
            self.assertIn("EARLY_UNARY_TOOL_STOP", result["qualifiers"])

    def test_optional_v_early_failure_never_vetoes_primary(self):
        evidence = evidence_fixture(self.prepared, self.tokenizer, nondegenerate=True, optional=False)
        result = self.reduce(evidence)
        self.assertEqual(result["label"], "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS", result)
        self.assertIn("EARLY_V_AUTH_QUARTET_STOP", result["qualifiers"])
        self.assertIn("OBJECTIVE_CONTRAST_AMBIGUOUS", result["qualifiers"])

    def test_optional_v_both_objectives_pass(self):
        result = self.reduce(evidence_fixture(self.prepared, self.tokenizer, nondegenerate=True))
        self.assertEqual(result["updates"], 384)
        self.assertEqual(result["prefix_readouts"], 2304)
        self.assertEqual(result["generations"], 1184)
        self.assertIn("COMMON_PREFIX_BOTH_OBJECTIVES_PASS_AUTH_INSTANCE", result["qualifiers"])

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
        fits = [dict(canary=dict(passed=True))] * 2
        cells = {arm: dict(exact=dict(passed=True), held=dict(passed=True), passed=True)
                 for arm in ("P_AUTH", "P_DERANGED")}
        self.assertEqual(q0.primary_label(fits, cells, dict(exact=112, held=48), 3), "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS")
        for exact, held, opposite in ((111, 48, 3), (112, 47, 3), (112, 48, 4)):
            self.assertEqual(q0.primary_label(fits, cells, dict(exact=exact, held=held), opposite),
                             "CONDITIONAL_BINDING_WITH_SPILL_OR_INTERFACE_FAILURE")

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
        self.assertEqual(lifecycle.report()["label"], "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS")

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

    def test_native_prepare_is_cpu_only_and_archives_only_pinned_sources(self):
        config = q0.native_config_template()
        config.update(model_path="/tmp/q0_mock_model_only", tokenizer_path="/tmp/q0_mock_model_only",
                      node="0" * 64, gpu_uuid="GPU-" + "1" * 36, driver_version="555.42",
                      approved_intake="closed Q0 fixture intake", builder_preflight_reference="CPU fixture only",
                      lease_end_unix=q0.time.time() + 50000, lease_cutoff_unix=q0.time.time() + 28000)
        diagnostic, _, _ = q0.historical_helpers()
        with tempfile.TemporaryDirectory() as folder:
            support = dict(provenance="CPU mock manifest only; not native acceptance",
                           scope="ARCHIVED_REGRESSION_SUPPORT_ONLY_NOT_Q0_INPUT",
                           files={"tests/test_semantic_writer_diagnostic.py":
                                  q0.file_hash(q0.repository() / "tests/test_semantic_writer_diagnostic.py")})
            receipt = dict(suites=list(q0.CPU_SUITES), successful=True, failures=0, errors=0, skipped=0,
                           source_pins=q0.native_source_pins(), environment=config["environment"],
                           platform="linux", evidence_kind="CPU_REGRESSION_ONLY", test_support=support,
                           test_support_sha256=q0.digest(support), test_import_roots=[".", "tests"])
            q0.write_once(folder, "tests.json", receipt)
            with patch.object(q0, "native_input_pins", return_value={"fixture": True}), \
                    patch.object(diagnostic.w0, "load_local_tokenizer", return_value=self.tokenizer):
                root = Path(folder, "run")
                manifest = q0.native_prepare(root, config, Path(folder, "tests.json"))
                self.assertFalse(manifest["ready"])
                self.assertIsNone(manifest["confirmation_allocation"])
                for name, expected in manifest["source_pins"].items():
                    self.assertEqual(q0.file_hash(root / "source" / name), expected)
                q0.native_verify(root)
                with self.assertRaises(q0.IntegrityError):
                    q0.native_prepare(root, config, Path(folder, "tests.json"))

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
        evidence = evidence_fixture(self.prepared, self.tokenizer)
        actual_diagnostic, _, _ = q0.historical_helpers()
        commands = []
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = dict(gpu_uuid="GPU-" + "1" * 36, lease_cutoff_unix=q0.time.time() + 4000)
            manifest = dict(ready=True, source_pins={}, config=config)
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
                self.assertLessEqual(timeout, 2700 - q0.CLEANUP_RESERVE)
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
                load = dict(identity=dict(pid=pid, start_ticks=pid), load_id=str(pid),
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
                    offset[0] += 2701

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
        self.assertEqual(result["report"]["label"], "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS")
        self.assertEqual(len(commands), 10)
        self.assertEqual(result["report"]["attempted_fits"], 2)

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
                self.assertGreaterEqual(result["report"]["late_publication"]["elapsed_seconds"], 2700)

    def test_mock_slow_execute_verification_spends_original_budget_before_any_worker(self):
        result, commands = self.run_mock_controller(verify_delay=2701)
        self.assertEqual(commands, [])
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_PRECHECK_ABORT")
        self.assertGreaterEqual(result["report"]["resource"]["elapsed_seconds"], 2700)

    def test_mock_failed_execute_verification_replays_abort_without_loading_tokenizer(self):
        result, commands = self.run_mock_controller(fail_verify=True)
        self.assertEqual(commands, [])
        self.assertEqual(result["report"]["label"], "NONREPORTABLE_PRECHECK_ABORT")


if __name__ == "__main__":
    unittest.main()
