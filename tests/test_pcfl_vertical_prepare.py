"""Synthetic CPU-only bridge tests; fixtures are NOT PCFL scientific evidence."""

import copy
import hashlib
import itertools
import json
from pathlib import Path
import unittest

from organism_v6 import pcfl_vertical_prepare as prepare
from organism_v6 import pcfl_vertical_dev as core


def _synthetic_replays(bindings):
    for corpus in bindings["slot_registry"]:
        slots = {slot["id"]: slot for slot in corpus["slots"]}
        for slot in slots.values():
            if slot["source"] is not None:
                slot.update({key: copy.deepcopy(value) for key, value in slots[slot["source"]].items() if key not in ("id", "source")})
    corpora, skeleton_hash = prepare._structural(bindings)
    bindings["replay_registry"] = []
    for corpus in corpora.values():
        slots = {slot["id"]: slot for slot in corpus["slots"]}
        arm = corpus["arm"]
        if arm.startswith("S1"):
            quotas = [("EVENT", "replay", ["s17", "s18", "s19"])]
            if arm == "S1_ATOMS":
                quotas.append(("EVENT", "atoms_extra", ["s14", "s15", "s16"]))
        else:
            quotas = [("EVENT", "replay", ["s19"])]
            if arm == "S2_OLD_REPLAY":
                quotas.extend([("EVENT", "old_event_extra", ["s17"]), ("LINK", "old_link_extra", ["s18"])])
        common = []
        for row_type, suffix, replay_ids in quotas:
            eligible = prepare._eligible_replay(bindings, corpora, corpus, row_type, suffix)
            prior = common if suffix in ("atoms_extra", "old_event_extra") else []
            domain = [skeleton_hash, arm[:2], "S1_four_arm" if arm.startswith("S1") else "S2_three_arm", row_type, suffix]
            selected, counts = prepare._select_replay(slots, eligible, prior, len(replay_ids), domain)
            if suffix == "replay":
                common = selected
            for replay_id, source_id in zip(replay_ids, selected):
                slots[replay_id].update({key: copy.deepcopy(value) for key, value in slots[source_id].items() if key not in ("id", "source")})
                slots[replay_id]["source"] = source_id
            bindings["replay_registry"].append({"corpus": corpus["id"], "row_type": row_type, "suffix": suffix,
                                               "eligible": eligible, "prior": prior, "selected": selected,
                                               "slots": replay_ids, "domain_hash": prepare.digest(domain), "support_counts": counts})
    return skeleton_hash


def _synthetic_batches(bindings):
    ids = [f"s{index:02}" for index in range(20)]
    conflicts = {slot_id: set() for slot_id in ids}
    for corpus in bindings["slot_registry"]:
        for left, right in itertools.combinations(corpus["slots"], 2):
            if (set(left["support"]) & set(right["support"]) or left["row_type"] == right["row_type"] == "LINK"
                    or left["phase"] == right["phase"] == "NEW"):
                conflicts[left["id"]].add(right["id"])
                conflicts[right["id"]].add(left["id"])
    ordered = sorted(ids, key=lambda slot_id: (-len(conflicts[slot_id]), slot_id))
    groups = [[] for _ in range(5)]
    def place(index):
        if index == len(ordered):
            return True
        slot_id = ordered[index]
        for group in groups:
            if len(group) < 4 and not conflicts[slot_id].intersection(group):
                group.append(slot_id)
                if place(index + 1):
                    return True
                group.pop()
                if not group:
                    break
        return False
    if not place(0):
        raise AssertionError("synthetic five-group schedule is infeasible")
    epoch = [[[slot_id, view] for slot_id in sorted(group)] for view in range(8) for group in groups]
    bindings["batch_registry"] = [{"corpus": corpus["id"], "epochs": [copy.deepcopy(epoch) for _ in range(5)]} for corpus in bindings["slot_registry"]]


def synthetic_bindings():
    """Artificial structural examples only, never real world/token/profile data."""
    roots = []
    for role, count in (("excluded", 4), ("disposable", 1), ("dev", 2)):
        for index in range(count):
            root_id = f"{role}/{index}"
            wire = core.to_data(core.build_root(root_id))
            roots.append({"id": root_id, "role": role, "seed": core.seed("root/" + root_id),
                          "old_bit": index % 2, "canonical_r": index % 2,
                          "primary_reachout": "RB" if index % 2 else "RA",
                          "wire": wire,
                          "topology": [[wire["inventory"]["node"]["S_L"], wire["inventory"]["port"]["a0"], wire["inventory"]["node"]["S_L"]]],
                          "cube": [list(bits) for bits in itertools.product((0, 1), repeat=3)]})
    corpora = []
    for root in roots:
        if root["role"] == "excluded":
            continue
        for arm in (["S1_AUTH"] if root["role"] == "disposable" else prepare.ARMS):
            slots = []
            for index in range(20):
                replay = (index >= 14 if arm == "S1_ATOMS" else index >= 17 if arm.startswith("S1") or arm == "S2_OLD_REPLAY" else index == 19)
                link = index in (14, 15, 16) and arm != "S1_ATOMS" or index == 18 and arm.startswith("S2")
                phase = "NEW" if arm.startswith("S2_FULL") and index in (15, 17, 18) else "OLD"
                source_index = 14 if link else 0
                row_type = "LINK" if link else "EVENT"
                control = arm == "S1_EVENT_TWIN" or arm == "S1_LINK_PERMUTE" and link
                address_index = source_index if replay else index
                support = f"{root['id']}/span{address_index:02}"
                fields = {"link": support, "first": "synthetic/event0", "second": "synthetic/event1", "via": "synthetic/node", "receipt_first": "synthetic/receipt0", "receipt_second": "synthetic/receipt1"} if link else {
                    "event": support, "source": "synthetic/source", "port": "synthetic/port", "destination": "synthetic/destination", "receipt": "synthetic/receipt"}
                slots.append({"id": f"s{index:02}", "source": f"s{source_index:02}" if replay else None,
                              "row_type": row_type, "phase": phase, "support": [support], "bank": {support: fields},
                              "taint": "CONTROL" if control else "AUTHENTIC",
                              "request": f"READ {'LINKS_FROM' if link else 'EVENT'} {root['id']}/address{address_index:02}"})
            corpora.append({"id": f"{root['id']}/{arm}", "root": root["id"], "arm": arm, "slots": slots})
    counterparts = []
    for root in roots:
        if root["role"] != "dev":
            continue
        for left, rights in (("S1_AUTH", ("S1_ATOMS", "S1_EVENT_TWIN", "S1_LINK_PERMUTE")), ("S2_FULL_R0", ("S2_FULL_R1", "S2_OLD_REPLAY"))):
            for right in rights:
                replaced = {14, 15, 16} if right == "S1_ATOMS" else {15, 17, 18} if right == "S2_OLD_REPLAY" else set()
                counterparts.append({"left": f"{root['id']}/{left}", "right": f"{root['id']}/{right}",
                                     "pairs": [[f"s{index:02}", f"s{index:02}"] for index in range(20) if index not in replaced],
                                     "replaced": [[f"s{index:02}", f"s{index:02}"] for index in sorted(replaced)]})
    bindings = {
        "source_pins": copy.deepcopy(prepare.SOURCE_PINS),
        "core_registry": core.registries(),
        "implementation_pins": {"preparer": "a" * 64, "validator": "a" * 64, "core": "c" * 64},
        "environment": {"base": prepare.RECIPE["base"], "model_revision": "SYNTHETIC", "model_files": {"synthetic": "b" * 64},
                        "tokenizer_revision": "SYNTHETIC", "chat_template_sha256": "d" * 64,
                        "environment_sha256": "e" * 64, "product": "A40", "gpu_uuids": ["GPU-SYNTHETIC"],
                        "cal_seeds": {"cal/init": 1, "cal/dropout": 2, "cal/readout": 3, "cal/batch": 4}},
        "root_registry": roots, "slot_registry": corpora, "counterpart_registry": counterparts,
        "replay_registry": [], "batch_registry": [], "intervention_registry": [], "locality_registry": [],
        "work_registry": [], "profile_registry": [],
    }
    target = "SYNTHETIC WRONG-BLOCK TEST ONLY\n"
    payload = {"role": "SCORER_ONLY_NEVER_PROMPT", "universe_sha256": "b" * 64,
               "addresses": {"synthetic_request": [{"target": target, "sha256": hashlib.sha256(target.encode()).hexdigest()}]}}
    bindings["diagnostic_registry"] = {"producer_sha256": "c" * 64, "payload": payload, "payload_sha256": prepare.digest(payload)}
    for corpus in corpora:
        other_root = "dev/1" if corpus["root"] != "dev/1" else "dev/0"
        bindings["locality_registry"].append({"corpus": corpus["id"], "other_corpus": f"{other_root}/S1_AUTH", "seed": 4,
                                             "unseen": [{"request": f"READ EVENT absent/{index}", "view": index} for index in range(8)],
                                             "wrong_root": [{"request": f"READ EVENT {other_root}/address{index:02}", "view": index} for index in range(8)]})
    for kind, arm, slot_id in (("S1_LINK", "S1_AUTH", "s14"), ("REACHOUT_OLD", "S1_AUTH", "s00"), ("S2_OLD", "S2_FULL_R0", "s00"), ("S2_NEW", "S2_FULL_R0", "s17")):
        bindings["intervention_registry"].append({"id": kind, "corpus": f"dev/0/{arm}", "kind": kind, "slots": [slot_id],
                                                 "support": [f"dev/0/span{int(slot_id[1:]):02}"], "replacement": "MISS", "endpoint": "service",
                                                 "view": 0, "seed": 5, "unaffected_mate": "s01", "task_ids": [f"task/{index}" for index in range(8)],
                                                 "denominator": 16, "minimum_drop": 6})
    for index in range(4):
        bindings["profile_registry"].append({"id": f"profile/{index}", "path": f"PREPARE/profile{index}.json", "shape": [1, 512],
                                            "cap_device_seconds": 60, "gpu_uuid": "GPU-SYNTHETIC", "accounting": "summed_device_seconds"})
    def add_work(purpose, state="C0", corpus=None, kind="generation", branch="BOTH", budget="dev_inference"):
        work = {"id": f"work/{len(bindings['work_registry'])}", "kind": kind, "purpose": purpose,
                "root": corpus["root"] if corpus else "excluded/0", "state": state,
                "corpus": corpus["id"] if corpus else None, "endpoint": "native", "prompt_sha256": "f" * 64,
                "mount": "C0", "seed": 0, "input_cap": 512, "output_cap": 128, "returned_cap": 0,
                "ancestry": "C0", "denominator": purpose, "gpu_uuid": "GPU-SYNTHETIC", "branch": branch,
                "device_seconds_cap": 1, "budget": budget, "profile": "profile/0", "reuses": None}
        bindings["work_registry"].append(work)
    for purpose, count in prepare.CORE_TOTALS.items():
        for _ in range(count):
            add_work(purpose, kind="task" if purpose == "service_task" else "generation")
    for corpus in corpora:
        states = ("CAL_LOW", "CAL_HIGH") if corpus["root"] == "disposable/0" else (corpus["id"],)
        for state in states:
            branch = "HIGH_USED" if state == "CAL_HIGH" else "BOTH"
            add_work("fit", state, corpus, "fit", branch, "training")
            for _ in range(64):
                budget = "cal_high_readout" if state == "CAL_HIGH" else "cal_low_readout" if state == "CAL_LOW" else "dev_inference"
                add_work("pcfl_retention", state, corpus, branch=branch, budget=budget)
    _synthetic_replays(bindings)
    _synthetic_batches(bindings)
    return bindings


def synthetic_tokenizer(bindings):
    return {"kind": "synthetic_test", "decisions_hash": prepare.digest(bindings), "revision": "SYNTHETIC",
            "files": {"synthetic": "d" * 64}, "chat_template_sha256": "d" * 64,
            "measurements": [{"id": "synthetic/0", "text": "prompt row", "token_ids": [1, 2, 3, 0],
                              "offsets": [[0, 7], [7, 10], [10, 10], [0, 0]], "attention_mask": [1, 1, 1, 0],
                              "labels": [-100, 2, 3, -100], "eos_index": 2, "opaque_spans": [[8, 10]],
                              "categories": ["masked", "content", "grammar", "masked"]}]}


def reseal(contract):
    contract["decisions_sha256"] = prepare.digest(contract["bindings"])
    contract["tokenizer_receipt"]["decisions_hash"] = contract["decisions_sha256"]


class ExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = synthetic_bindings()
        cls.contract = prepare.build_execution_contract(cls.bindings, synthetic_tokenizer(cls.bindings))

    def assert_rejected(self, mutate, pattern=None, reseal_decisions=True):
        contract = copy.deepcopy(self.contract)
        mutate(contract)
        if reseal_decisions:
            reseal(contract)
        with self.assertRaisesRegex(prepare.ExecutionContractError, pattern or ".*"):
            prepare.validate_execution_contract(contract)

    def test_synthetic_roundtrip_is_not_execution_closure(self):
        report = prepare.validate_execution_contract(self.contract)
        self.assertTrue(report["bridge_invariants_valid"])
        self.assertFalse(report["execution_contract_valid"])
        self.assertIn("synthetic_evidence_is_not_execution_evidence", report["missing_interfaces"])
        for branch, fits, updates, retention in (("LOW_ONLY", 15, 3000, 960), ("HIGH_USED", 16, 3200, 1024)):
            actual = report["branches"][branch]
            self.assertEqual((actual["fits"], actual["updates"], actual["retention_calls"]), (fits, updates, retention))
        self.assertEqual(prepare.load_contract(prepare.canonical(self.contract), prepare.digest(self.contract)), self.contract)

    def test_no_argument_mutation_or_aliases(self):
        before = prepare.canonical(self.bindings)
        receipt = synthetic_tokenizer(self.bindings)
        contract = prepare.build_execution_contract(self.bindings, receipt)
        prepare.validate_execution_contract(contract)
        self.assertEqual(before, prepare.canonical(self.bindings))
        contract["bindings"]["environment"]["cal_seeds"]["cal/init"] = 9
        contract["tokenizer_receipt"]["measurements"][0]["token_ids"][0] = 9
        self.assertEqual(self.bindings["environment"]["cal_seeds"]["cal/init"], 1)
        self.assertEqual(receipt["measurements"][0]["token_ids"][0], 1)

    def test_six_authority_source_files_match(self):
        directory = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        for name, expected in prepare.SOURCE_PINS.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)

    def test_canonical_wire_and_duplicate_fields(self):
        self.assertEqual(prepare.canonical({"é": [1, True, None], "a": 2}), b'{"a":2,"\xc3\xa9":[1,true,null]}')
        for value in ({1: "coercion"}, (1, 2), {"nan": float("nan")}, {"bytes": b"raw"}):
            with self.subTest(value=value), self.assertRaises(prepare.ExecutionContractError):
                prepare.canonical(value)
        for payload in (b'{"schema":1,"schema":2}', b' {"x":1}', b'{"x":NaN}'):
            with self.subTest(payload=payload), self.assertRaises(prepare.ExecutionContractError):
                prepare.load_contract(payload, hashlib.sha256(payload).hexdigest())
        with self.assertRaisesRegex(prepare.ExecutionContractError, "sidecar"):
            prepare.load_contract(prepare.canonical(self.contract), "0" * 64)

    def test_closed_schema_source_and_decision_drift(self):
        self.assert_rejected(lambda contract: contract.update(unknown=True), "unknown")
        self.assert_rejected(lambda contract: contract["bindings"].pop("work_registry"), "unknown")
        self.assert_rejected(lambda contract: contract["bindings"]["source_pins"].update({next(iter(prepare.SOURCE_PINS)): "0" * 64}), "source-pin")
        self.assert_rejected(lambda contract: contract["bindings"]["environment"]["cal_seeds"].update({"cal/init": 8}), "decisions drift", False)

    def test_obsolete_fields_and_false_integer_rejected(self):
        for name in ("PAD_S1_00", "PAD_S2_00", "loss_active_pad", "equal_target_tokens", "equal_token_reserve", "fourteen_fit_campaign"):
            with self.subTest(name=name):
                self.assert_rejected(lambda contract: contract["recipe"].update({name: True}), "constants")
        self.assert_rejected(lambda contract: contract["recipe"].update(batch_size=True), "constants")
        self.assert_rejected(lambda contract: contract["bindings"]["root_registry"][0].update(seed=True), "integer")
        self.assert_rejected(lambda contract: contract["bindings"]["slot_registry"][0]["slots"][0].update(request="PAD_S1_00"), "grammar")

    def test_root_skeleton_excludes_outputs_and_replay_bytes(self):
        self.assert_rejected(lambda contract: contract["bindings"]["root_registry"][0].update(child_output="EVENT fabricated"), "unknown")
        self.assert_rejected(lambda contract: contract["bindings"]["root_registry"][0]["cube"].pop(), "cube")
        self.assert_rejected(lambda contract: contract["bindings"]["root_registry"][0]["wire"]["inventory"]["node"].update(S_L="EVENT generated row"), "identifier")
        bindings = copy.deepcopy(self.bindings)
        before = prepare._structural(bindings)[1]
        bindings["core_registry"]["render_registry"]["generated_test_perturbation"] = "not a real generation"
        self.assertEqual(prepare._structural(bindings)[1], before)

    def test_exact_roster_and_replay_custody(self):
        self.assert_rejected(lambda contract: contract["bindings"]["slot_registry"][0]["slots"].pop(), "twenty")
        self.assert_rejected(lambda contract: contract["bindings"]["slot_registry"][0]["slots"][-1].update(request="READ EVENT invented"), "changes source")
        self.assert_rejected(lambda contract: contract["bindings"]["replay_registry"][0].update(domain_hash="0" * 64), "domain")
        self.assert_rejected(lambda contract: contract["bindings"]["replay_registry"][0]["eligible"].pop(), "eligible")
        self.assert_rejected(lambda contract: contract["bindings"]["replay_registry"][0]["selected"].reverse(), "balance")

    def test_replay_balance_independent_bruteforce(self):
        slots = {name: {"source": None, "support": support} for name, support in (("a", ["e0"]), ("b", ["e0", "e1"]), ("c", ["e2"]), ("d", ["e3"]))}
        domain = ["0" * 64, "S1", "S1_four_arm", "EVENT", "replay"]
        actual, counts = prepare._select_replay(slots, ["a", "b", "c", "d"], [], 2, domain)
        self.assertEqual(actual, ["c", "d"])
        self.assertEqual(counts, {"e0": 2, "e1": 1, "e2": 2, "e3": 2})
        with self.assertRaisesRegex(prepare.ExecutionContractError, "distinct-source"):
            prepare._select_replay(slots, ["a", "b", "c", "d"], ["a", "b", "c"], 2, domain)

    def test_five_forty_four_and_w8_never_trains(self):
        self.assert_rejected(lambda contract: contract["bindings"]["batch_registry"][0]["epochs"].pop(), "five")
        self.assert_rejected(lambda contract: contract["bindings"]["batch_registry"][0]["epochs"][0].pop(), "forty")
        self.assert_rejected(lambda contract: contract["bindings"]["batch_registry"][0]["epochs"][0][0].pop(), "four")
        self.assert_rejected(lambda contract: contract["bindings"]["batch_registry"][0]["epochs"][0][0][0].__setitem__(1, 8), "trained W8")
        self.assert_rejected(lambda contract: contract["bindings"]["batch_registry"][0]["epochs"][0].__setitem__(1, copy.deepcopy(contract["bindings"]["batch_registry"][0]["epochs"][0][0])), "160")

    def test_replay_support_collision_even_with_different_slot_ids(self):
        def mutate(contract):
            corpus = contract["bindings"]["slot_registry"][0]
            replay = corpus["slots"][-1]
            epoch = contract["bindings"]["batch_registry"][0]["epochs"][0]
            source_position = next((batch, item) for batch in epoch for item in batch if item == [replay["source"], 0])
            source_position[0][(source_position[0].index(source_position[1]) + 1) % 4] = [replay["id"], 0]
        self.assert_rejected(mutate, "support collision")

    def test_grouped_read_support_overlap_is_not_block_hash_equality(self):
        contract = copy.deepcopy(self.contract)
        corpus = contract["bindings"]["slot_registry"][0]
        first = [slot for slot in corpus["slots"] if slot["source"] is None and slot["row_type"] == "EVENT"]
        single, grouped = first[:2]
        grouped["request"] = "READ EVENTS_AT synthetic/source"
        grouped["support"] = single["support"] + grouped["support"]
        grouped["bank"].update(single["bank"])
        contract["root_skeleton_hash"] = _synthetic_replays(contract["bindings"])
        reseal(contract)
        epoch = contract["bindings"]["batch_registry"][0]["epochs"][0]
        epoch[0] = [[single["id"], 0], [grouped["id"], 0], [first[2]["id"], 0], [first[3]["id"], 0]]
        reseal(contract)
        with self.assertRaisesRegex(prepare.ExecutionContractError, "support collision"):
            prepare.validate_execution_contract(contract)

    def test_counterpart_totality_and_indexed_positions(self):
        contract = copy.deepcopy(self.contract)
        mapping = contract["bindings"]["counterpart_registry"][0]
        mapping["pairs"].pop()
        with self.assertRaisesRegex(prepare.ExecutionContractError, "total/injective"):
            prepare._replays_and_batches(contract["bindings"], prepare._structural(self.bindings)[0], contract["root_skeleton_hash"])
        def mutate(contract):
            schedule = next(row for row in contract["bindings"]["batch_registry"] if row["corpus"] == "dev/0/S1_EVENT_TWIN")
            schedule["epochs"][0][0], schedule["epochs"][0][1] = schedule["epochs"][0][1], schedule["epochs"][0][0]
        self.assert_rejected(mutate, "counterpart batch position")

    def test_cal_truth_table_all_boolean_inputs(self):
        keys = prepare.INTEGRITY + prepare.SAFETY + prepare.ACQUISITION
        for values in itertools.product((False, True), repeat=len(keys)):
            gates = dict(zip(keys, values))
            valid = all(gates[key] for key in prepare.INTEGRITY)
            safe = all(gates[key] for key in prepare.SAFETY)
            acquired = all(gates[key] for key in prepare.ACQUISITION)
            low = prepare.calibration_transition("CAL_LOW", gates)
            high = prepare.calibration_transition("CAL_HIGH", gates)
            self.assertEqual(low == "RUN_CAL_HIGH", valid and safe and not acquired)
            self.assertEqual(low == "SELECT_LOW", valid and safe and acquired)
            self.assertEqual(high == "SELECT_HIGH", valid and safe and acquired)
            self.assertEqual(low == "VS_ASSAY_INVALID", not valid)
            self.assertNotEqual(high, "RUN_CAL_HIGH")
        gates = dict.fromkeys(keys, True)
        gates["native_route"] = False
        with self.assertRaises(prepare.ExecutionContractError):
            prepare.calibration_transition("CAL_LOW", gates)

    def test_new_literals_are_exact_and_detached(self):
        self.assertEqual(self.contract["prospective_literals"]["wrappers"][8], "Provide the exact stored personal-memory block at this address.\n{REQUEST}\nOutput only the block.")
        self.assert_rejected(lambda contract: contract["prospective_literals"]["wrappers"].__setitem__(8, prepare.WRAPPERS[8] + "\n"), "literal")
        self.assert_rejected(lambda contract: contract["prospective_literals"]["parser_policy"]["refusals"].append("I cannot recall"), "literal")
        self.assert_rejected(lambda contract: contract["bindings"]["diagnostic_registry"]["payload"].update(separator="changed"), "byte drift")

    def test_masked_pad_legal_content_overlap_and_eos_grammar(self):
        contract = copy.deepcopy(self.contract)
        contract["tokenizer_receipt"]["measurements"][0]["token_ids"][-1] = 99
        self.assertTrue(prepare.validate_execution_contract(contract)["bridge_invariants_valid"])
        self.assert_rejected(lambda contract: contract["tokenizer_receipt"]["measurements"][0]["labels"].__setitem__(3, 0), "masked padding")
        self.assert_rejected(lambda contract: contract["tokenizer_receipt"]["measurements"][0]["categories"].__setitem__(1, "grammar"), "misclassified")
        self.assert_rejected(lambda contract: contract["tokenizer_receipt"]["measurements"][0]["categories"].__setitem__(2, "content"), "misclassified")
        self.assert_rejected(lambda contract: contract["tokenizer_receipt"].update(revision="changed"), "tokenizer binding")

    def test_locality_cut_and_work_fail_closed(self):
        contract = copy.deepcopy(self.contract)
        contract["bindings"]["locality_registry"][0]["unseen"][0]["request"] = contract["bindings"]["slot_registry"][0]["slots"][0]["request"]
        with self.assertRaisesRegex(prepare.ExecutionContractError, "overlap"):
            prepare._core_registries(contract["bindings"], prepare._structural(self.bindings)[0])
        contract = copy.deepcopy(self.contract)
        contract["bindings"]["intervention_registry"][0]["minimum_drop"] = 9
        with self.assertRaisesRegex(prepare.ExecutionContractError, "unattainable"):
            prepare._core_registries(contract["bindings"], prepare._structural(self.bindings)[0])
        self.assert_rejected(lambda contract: contract["bindings"]["work_registry"].pop(), "retention")
        self.assert_rejected(lambda contract: contract["bindings"]["work_registry"][0].update(retry_budget=1), "unknown")
        self.assert_rejected(lambda contract: contract["bindings"]["work_registry"][0].update(device_seconds_cap=36001), "device-time")
        self.assert_rejected(lambda contract: contract["bindings"]["environment"].update(product="A100"), "A40")

    def test_profiles_bind_contract_without_filling_decisions(self):
        before = prepare.canonical(self.contract)
        receipts = [{"id": profile["id"], "kind": "synthetic_test", "contract_sha256": prepare.digest(self.contract),
                     "path": profile["path"], "shape": profile["shape"], "gpu_uuid": profile["gpu_uuid"],
                     "product": "A40", "device_seconds": 2.5, "accounting": "summed_device_seconds", "evidence_sha256": "a" * 64}
                    for profile in self.bindings["profile_registry"]]
        report = prepare.validate_execution_contract(self.contract, receipts)
        self.assertFalse(report["execution_contract_valid"])
        self.assertFalse(any(item.startswith("profile_receipt:") for item in report["missing_interfaces"]))
        self.assertEqual(before, prepare.canonical(self.contract))
        for key, value in (("contract_sha256", "0" * 64), ("product", "A100"), ("gpu_uuid", "GPU-wrong"), ("device_seconds", 61), ("accounting", "parallel_wall_seconds")):
            changed = copy.deepcopy(receipts)
            changed[0][key] = value
            with self.subTest(key=key), self.assertRaises(prepare.ExecutionContractError):
                prepare.validate_execution_contract(self.contract, changed)

    def test_current_core_registry_is_consumed_without_world_reimplementation(self):
        self.assertEqual(self.contract["bindings"]["core_registry"], core.registries())
        self.assertEqual(set(core.registries()["render_registry"]["projections"]), prepare.PROJECTIONS)
        bindings = copy.deepcopy(self.bindings)
        bindings["source_pins"] = core.registries()["source_pins"]
        _synthetic_replays(bindings)
        _synthetic_batches(bindings)
        contract = prepare.build_execution_contract(bindings, synthetic_tokenizer(bindings))
        self.assertFalse(prepare.validate_execution_contract(contract)["execution_contract_valid"])
        for row in bindings["root_registry"]:
            self.assertEqual(core.to_data(core.from_data(row["wire"])), row["wire"])

    def test_core_semantic_and_false_row_policy_integration(self):
        root = core.build_root("excluded/0")
        rows = core.ideal_rows(core.expand_cube(root)[0])
        expected, wrong = rows[0]["raw"], rows[1]["raw"]
        for raw in (expected, expected[:-1], "```\n" + expected + "```", "```text\n" + expected + "```\n"):
            with self.subTest(raw=raw):
                result = core.score_memory_response(raw, expected)
                self.assertTrue(result["semantic"])
                self.assertEqual(result["strict"], raw == expected)
        for raw in ("prose\n" + expected, expected + expected, wrong + expected, expected + "extra", "```python\n" + expected + "```", "MISS"):
            with self.subTest(raw=raw):
                self.assertFalse(core.score_memory_response(raw, expected)["semantic"])
        for raw in ("MISS\n" + wrong, "prose " + wrong, wrong + " prose"):
            with self.subTest(raw=raw):
                self.assertTrue(core.score_memory_response(raw, expected)["usable_false_row"])
                self.assertTrue(core.score_memory_response(raw, None)["usable_false_row"])

    def _synthetic_formation_records(self):
        corpus = self.contract["bindings"]["slot_registry"][0]
        by_support, queries = {}, {}
        templates = self.contract["bindings"]["core_registry"]["parser_registry"]
        for slot in corpus["slots"]:
            if slot["source"] is not None:
                continue
            for support, fields in slot["bank"].items():
                template = templates["event_template" if slot["row_type"] == "EVENT" else "link_template"]
                raw = template.format(**fields)
                by_support[support] = {"kind": slot["row_type"], "raw": raw, "sha256": hashlib.sha256(raw.encode()).hexdigest(),
                                       "root": corpus["root"], "fields": copy.deepcopy(fields), "taint": "CHILD_SUBMISSION",
                                       "provenance": {"synthetic_test_only": True, "native_generation_verified": False}}
            members = [by_support[support] for support in slot["support"]]
            target = "".join(row["raw"] for row in members)
            queries[slot["request"]] = {"request": slot["request"], "target": target, "target_sha256": hashlib.sha256(target.encode()).hexdigest(),
                                        "support": slot["support"][:], "source_sha256": [row["sha256"] for row in members], "taint": ["CHILD_SUBMISSION"]}
        return corpus["id"], queries, list(by_support.values())

    def test_formation_binding_is_read_only_and_never_certifies_native_custody(self):
        corpus_id, queries, rows = self._synthetic_formation_records()
        before = prepare.canonical([self.contract, queries, rows])
        receipt = prepare.validate_formation_binding(self.contract, corpus_id, queries, rows)
        self.assertTrue(receipt["formation_binding_valid"])
        self.assertFalse(receipt["native_custody_verified"])
        self.assertEqual(len(receipt["slots"]), 20)
        self.assertEqual(before, prepare.canonical([self.contract, queries, rows]))

    def test_free_choice_chronology_cannot_be_remapped_or_replaced_with_ideal(self):
        corpus_id, queries, rows = self._synthetic_formation_records()
        first = rows[0]
        first["fields"]["port"] = "synthetic/other_port"
        first["raw"] = core.EVENT_WIRE.format(**first["fields"])
        first["sha256"] = hashlib.sha256(first["raw"].encode()).hexdigest()
        with self.assertRaisesRegex(prepare.ExecutionContractError, "VS_FORMATION_BANK_MISMATCH.*chronological fields"):
            prepare.validate_formation_binding(self.contract, corpus_id, queries, rows)
        corpus_id, queries, rows = self._synthetic_formation_records()
        rows[0]["taint"] = "CEILING_FIXTURE"
        with self.assertRaisesRegex(prepare.ExecutionContractError, "VS_FORMATION_BANK_MISMATCH.*ceiling"):
            prepare.validate_formation_binding(self.contract, corpus_id, queries, rows)
        rows.pop()
        with self.assertRaises(prepare.ExecutionContractError):
            prepare.validate_formation_binding(self.contract, corpus_id, queries, rows)

    def test_missing_inputs_and_cal_seed_drift_fail_typed(self):
        with self.assertRaises(prepare.ExecutionContractError):
            prepare.build_execution_contract({}, None)
        bindings = copy.deepcopy(self.bindings)
        bindings["slot_registry"][0]["slots"][0].pop("id")
        with self.assertRaises(prepare.ExecutionContractError):
            prepare.build_execution_contract(bindings, synthetic_tokenizer(bindings))
        def mutate(contract):
            high = next(row for row in contract["bindings"]["work_registry"] if row["kind"] == "fit" and row["state"] == "CAL_HIGH")
            high["seed"] = 100
        self.assert_rejected(mutate, "shared initialization")

    def test_replay_hash_can_precede_source_assignment(self):
        bindings = copy.deepcopy(self.bindings)
        before = prepare.root_skeleton_digest(bindings)
        for corpus in bindings["slot_registry"]:
            for slot in corpus["slots"]:
                if slot["source"] is not None:
                    slot.update(source="UNRESOLVED_REPLAY", request=None, support=[], bank={})
        self.assertEqual(prepare.root_skeleton_digest(bindings), before)
        with self.assertRaises(prepare.ExecutionContractError):
            prepare.build_execution_contract(bindings, synthetic_tokenizer(bindings))

    def test_common_replay_excludes_new_bearing_group_in_another_arm(self):
        bindings = copy.deepcopy(self.bindings)
        corpora = {corpus["id"]: corpus for corpus in bindings["slot_registry"]}
        corpora["dev/0/S2_FULL_R1"]["slots"][0]["phase"] = "NEW"
        anchor = corpora["dev/0/S2_FULL_R0"]
        old = corpora["dev/0/S2_OLD_REPLAY"]
        self.assertNotIn("s00", prepare._eligible_replay(bindings, corpora, anchor, "EVENT", "replay"))
        self.assertNotIn("s00", prepare._eligible_replay(bindings, corpora, old, "EVENT", "replay"))
        self.assertIn("s00", prepare._eligible_replay(bindings, corpora, old, "EVENT", "old_event_extra"))

    def test_production_D_is_explicitly_unresolved_not_provisional_core_authority(self):
        report = prepare.validate_execution_contract(self.contract)
        self.assertFalse(report["static_contract_complete"])
        self.assertFalse(report["ready_for_model_calls"])
        self.assertFalse(report["execution_contract_valid"])
        self.assertEqual(self.contract["production_bindings"]["distractor"]["status"], "UNRESOLVED")
        self.assertIn("production_D_frontier_outcome_receipt_and_terminal_bytes_binding", report["missing_interfaces"])
        self.assert_rejected(lambda contract: contract["production_bindings"]["distractor"].update(status="BOUND"), "cannot be invented")
        note = Path(__file__).resolve().parents[1] / "research_notes" / "analysis" / "2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md"
        self.assertEqual(hashlib.sha256(note.read_bytes()).hexdigest(), prepare.PRODUCTION_BINDINGS["distractor"]["source_note_sha256"])


if __name__ == "__main__":
    unittest.main()
