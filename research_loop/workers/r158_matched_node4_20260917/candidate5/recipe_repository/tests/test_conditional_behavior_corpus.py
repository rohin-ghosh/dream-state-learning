"""Independent truth tables and fixture-only CPU audits; no installed tokenizer."""
from collections import Counter, defaultdict
import copy
import itertools
import random
import re
from unittest.mock import patch

import pytest

from organism_v6 import conditional_behavior_corpus as corpus


class Tokenizer:
    eos_token_id = 900000
    pad_token_id = 900001

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]["role"] == "user"
        return "USER:\n" + messages[0]["content"] + "\nASSISTANT:\n"

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return [ord(character) + 100 for character in text]


class UnequalLabels(Tokenizer):
    def encode(self, text, *, add_special_tokens):
        result = super().encode(text, add_special_tokens=add_special_tokens)
        return result + [123456] if text in ("wug", " wug") else result


class ContextSensitiveMismatch(Tokenizer):
    def encode(self, text, *, add_special_tokens):
        result = super().encode(text, add_special_tokens=add_special_tokens)
        return result + [123456] if text.startswith("USER:") and "OBSERVED: zot." in text else result


class OverlongTokenizer(Tokenizer):
    def encode(self, text, *, add_special_tokens):
        return super().encode(text, add_special_tokens=add_special_tokens) * 10


@pytest.fixture
def candidate():
    return corpus.build_candidate()


def independent_target(case, arm):
    """Parse the visible task, not the implementation's stored factors/targets."""
    text = case["context"]
    if case["operation"] == "PROSPECT":
        card = re.search(r"BELIEF: ([^.]+)\.", text).group(1)
        goal = re.search(r"GOAL: ([a-z0-9]+)\.", text).group(1)
        entries = [entry.split(" -> ") for entry in card.split("; ")]
        selected = next((action, outcome) for action, outcome in entries
                        if (outcome == goal) == (arm == "AUTH"))
        action, outcome = selected
        return f"PREDICT: {action} -> {outcome}\nACT: {action}"
    actions = re.search(r"ACTIONS: ([^.]+)\.", text).group(1).split(", ")
    prior, predicted, acted = re.search(r"PRIOR: PREDICT (\w+) -> (\w+); ACT (\w+)\.", text).groups()
    assert prior == acted and prior in actions and len(actions) == 2
    observed = re.search(r"OBSERVED: (\w+)\.", text).group(1)
    keep = predicted == observed
    if arm == "DERANGED":
        keep = not keep
    chosen = prior if keep else next(action for action in actions if action != prior)
    return f"COMPARE: {'MATCH' if keep else 'MISMATCH'}\nPOLICY: {'KEEP' if keep else 'SWITCH'}\nNEXT: {chosen}"


@pytest.mark.parametrize("root", (0, 1, 2))
def test_counts_views_origins_and_independent_target_derivation(root):
    material = corpus.build_candidate(root)
    audit = corpus.audit_candidate(material)
    assert audit["dev_twins"] == dict.fromkeys(("goal", "belief", "outcome", "prior_action"), 16)
    sources = {source["id"]: source for source in material["source_records"]}
    assert len(sources) == 112
    for arm in corpus.ARMS:
        rows = material["train"][arm]
        assert len(rows) == 128
        assert [row["operation"] for row in rows] == ["PROSPECT", "REVISE"] * 64
        counts = {operation: Counter(row["semantic_id"] for row in rows if row["operation"] == operation)
                  for operation in corpus.OPERATIONS}
        assert len(counts["PROSPECT"]) == 16 and set(counts["PROSPECT"].values()) == {4}
        assert len(counts["REVISE"]) == 32 and set(counts["REVISE"].values()) == {2}
        for row in rows:
            assert row["response"] == independent_target(row, arm)
            assert row["origin"] == corpus.ORIGIN
            source = sources[row["source_event_ids"][0]]
            assert source["inputs"] == {key: value for key, value in row["inputs"].items() if key != "action_order"}
    assert Counter(row["operation"] for row in material["dev"]) == {"PROSPECT": 32, "REVISE": 32}
    assert material["confirmation_cases"] == [] and material["composition"]["trained_chain_rows"] == 0


def test_literal_boolean_truth_tables_not_generator_scoring():
    for belief, goal in itertools.product((0, 1), repeat=2):
        case = dict(operation="PROSPECT", inputs=dict(actions=["dax", "wug"], outcomes=["mip", "zot"],
                    belief={"dax": ["mip", "zot"][belief], "wug": ["mip", "zot"][1 - belief]},
                    goal=["mip", "zot"][goal]))
        for arm, complement in (("AUTH", 0), ("DERANGED", 1)):
            expected_action = ["dax", "wug"][belief ^ goal ^ complement]
            assert corpus.expected_fields(case, arm) == dict(PREDICT_ACTION=expected_action,
                       PREDICT_OUTCOME=["mip", "zot"][goal ^ complement], ACT=expected_action)
    for prior, predicted, observed in itertools.product((0, 1), repeat=3):
        case = dict(operation="REVISE", inputs=dict(actions=["dax", "wug"], prior_action=["dax", "wug"][prior],
                    expected=["mip", "zot"][predicted], observed=["mip", "zot"][observed]))
        for arm, complement in (("AUTH", 0), ("DERANGED", 1)):
            mismatch = predicted ^ observed ^ complement
            assert corpus.expected_fields(case, arm) == dict(COMPARE=["MATCH", "MISMATCH"][mismatch],
                       POLICY=["KEEP", "SWITCH"][mismatch], NEXT=["dax", "wug"][prior ^ mismatch])


@pytest.mark.parametrize("split,expected_pairs", (("train", 32), ("dev", 16)))
def test_full_squares_edges_and_only_intervention_bytes(candidate, split, expected_pairs):
    rows = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
    by_id = {row["id"]: row for row in rows}
    for family, pairs in candidate["twins"][split].items():
        assert len(pairs) == expected_pairs
        used = Counter(identifier for pair in pairs for identifier in pair)
        assert set(used.values()) == {1}
        for first_id, second_id in pairs:
            first, second = by_id[first_id], by_id[second_id]
            assert first["instance_id"] == second["instance_id"]
            assert first["template"] == second["template"]
            assert first["inputs"]["action_order"] == second["inputs"]["action_order"]
            if family == "goal":
                assert re.sub(r"GOAL: \w+", "GOAL: _", first["context"]) == re.sub(r"GOAL: \w+", "GOAL: _", second["context"])
            elif family == "belief":
                assert first["inputs"]["goal"] == second["inputs"]["goal"]
                assert re.sub(r"BELIEF: [^.]+", "BELIEF: _", first["context"]) == re.sub(r"BELIEF: [^.]+", "BELIEF: _", second["context"])
                assert list(first["inputs"]["belief"]) == list(second["inputs"]["belief"])
                assert set(first["inputs"]["belief"].items()).isdisjoint(second["inputs"]["belief"].items())
            elif family == "outcome":
                assert re.sub(r"OBSERVED: \w+", "OBSERVED: _", first["context"]) == re.sub(r"OBSERVED: \w+", "OBSERVED: _", second["context"])
            else:
                neutralize = lambda text: re.sub(r"(PREDICT |ACT )\w+", r"\1_", text)
                assert neutralize(first["context"]) == neutralize(second["context"])
                assert first["inputs"]["expected"] == second["inputs"]["expected"]
                assert first["inputs"]["observed"] == second["inputs"]["observed"]
    for row in rows:
        assert row["id"] not in row["context"]
        if row["operation"] == "REVISE":
            assert all(action in re.search(r"ACTIONS: ([^.]+)", row["context"]).group(1)
                       for action in row["inputs"]["actions"])


def test_literal_swap_batches_and_split_disjointness(candidate):
    auth, deranged = (candidate["train"][arm] for arm in corpus.ARMS)
    for offset in range(0, 128, 4):
        before, after = auth[offset:offset + 4], deranged[offset:offset + 4]
        assert len({row["group"] for row in before + after}) == 1
        assert [row["order"] for row in before] == [0, 1, 2, 3]
        assert [row["context"] for row in before] == [row["context"] for row in after]
        assert [row["response"] for row in after] == [before[index]["response"] for index in (2, 3, 0, 1)]
    for key in ("instance_id", "id", "context"):
        assert not {row[key] for row in auth} & {row[key] for row in candidate["dev"]}
    for operation in corpus.OPERATIONS:
        assert not {row["template"] for row in auth if row["operation"] == operation} & {
            row["template"] for row in candidate["dev"] if row["operation"] == operation}


@pytest.mark.parametrize("root", (0, 1, 2))
def test_joint_shortcut_ceilings_and_inapplicable_components(root):
    material = corpus.build_candidate(root)
    for split in ("train", "dev"):
        cases = material["train"]["AUTH"] if split == "train" else material["dev"]
        for arm in corpus.ARMS:
            report = corpus.audit_restricted_baselines(cases, arm)["operations"]
            for operation, entries in report.items():
                assert tuple(entries) == corpus.SHORTCUT_PROJECTIONS
                assert entries["constant"]["ceiling"] == 0.25
                for result in entries.values():
                    if result["applicable"]:
                        assert result["target"] == "FULL_JOINT" and result["ceiling"] <= 0.5
            assert report["PROSPECT"]["goal_only"]["ceiling"] == 0.5
            assert report["PROSPECT"]["goal_only"]["component_ceilings"]["PREDICT_OUTCOME"] == 1
            assert report["PROSPECT"]["first_listed_action"]["ceiling"] == 0.5
            assert report["REVISE"]["prior_action_name"]["ceiling"] == 0.5
            assert report["REVISE"]["observed_only"]["ceiling"] == 0.25
            assert not report["REVISE"]["goal_only"]["applicable"]


def test_lookup_formula_matches_exhaustive_policies(candidate):
    cases = [row for row in candidate["dev"] if row["operation"] == "PROSPECT"]
    goals = [row["inputs"]["goal"] for row in cases]
    targets = [independent_target(row, "AUTH") for row in cases]
    best = max(sum(dict(zip(sorted(set(goals)), choices))[goal] == target for goal, target in zip(goals, targets))
               for choices in itertools.product(sorted(set(targets)), repeat=2))
    report = corpus.audit_restricted_baselines(candidate["dev"])["operations"]["PROSPECT"]["goal_only"]
    assert best == report["correct"] == 16


def test_correlation_is_rejected_not_silently_certified(candidate):
    rows = copy.deepcopy(candidate["dev"])
    for row in rows:
        row["template"] = independent_target(row, "AUTH")
    with pytest.raises(ValueError, match="restricted joint leakage/correlation"):
        corpus.audit_restricted_baselines(rows)
    with pytest.raises(ValueError, match="allowlist"):
        corpus._projection(rows[0], 0, "gold_target")


@pytest.mark.parametrize("tampering", ("target", "context", "source", "split", "order", "group", "twin", "extra", "root"))
def test_binding_tampering_is_rejected(candidate, tampering):
    changed = copy.deepcopy(candidate)
    if tampering == "target":
        changed["train"]["DERANGED"][0]["response"] = changed["train"]["AUTH"][0]["response"]
    elif tampering == "context":
        changed["train"]["AUTH"][0]["context"] += " Answer is dax."
    elif tampering == "source":
        changed["source_records"][0]["origin"] = "child experience"
    elif tampering == "split":
        changed["dev"][0]["instance_id"] = changed["train"]["AUTH"][0]["instance_id"]
    elif tampering == "order":
        changed["train"]["AUTH"][0]["order"] = 3
    elif tampering == "group":
        changed["train"]["AUTH"][0]["group"] = changed["train"]["AUTH"][0]["id"]
    elif tampering == "twin":
        changed["twins"]["dev"]["goal"][0][0] = changed["twins"]["dev"]["goal"][0][1]
    elif tampering == "extra":
        changed["train"]["AUTH"].append(changed["train"]["AUTH"][0])
    else:
        changed["root"] = 1
    with pytest.raises(ValueError):
        corpus.audit_candidate(changed)


def test_deterministic_root_permutations_no_rng_or_input_mutation(candidate):
    state = random.getstate()
    before = copy.deepcopy(candidate)
    assert corpus.build_candidate() == candidate
    assert len({tuple(corpus.build_candidate(root)["spellings"]["actions"] +
                      corpus.build_candidate(root)["spellings"]["outcomes"]) for root in (0, 1, 2)}) == 3
    custom = corpus.build_candidate(2, ("vek", "lum"), ("saf", "nib"))
    assert custom["spellings"] == dict(actions=["vek", "lum"], outcomes=["nib", "saf"])
    corpus.audit_candidate(candidate)
    assert candidate == before and random.getstate() == state
    for actions, outcomes in [(("dax", "dax"), ("mip", "zot")), (("act", "wug"), ("mip", "zot")),
                              (("dax", "wug"), ("dax", "zot"))]:
        with pytest.raises(ValueError):
            corpus.build_candidate(action_labels=actions, outcome_labels=outcomes)


def test_explicit_rate_fresh_recipe_and_v3_schema(candidate):
    with pytest.raises(TypeError):
        corpus.training_recipe()
    for invalid in (None, 0, -1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            corpus.training_recipe(learning_rate=invalid)
    recipe = corpus.training_recipe(learning_rate=1e-4, seed=0)
    config = corpus.trainer.TrainConfig(**recipe)
    assert config.rank == 8 and config.epochs == 4 and config.batch_size == 4 and config.grad_accum == 1
    assert not config.pack and not config.chat_template and config.add_eos
    assert "warmstart" not in recipe and "init_adapter" not in recipe
    assert candidate["initialization"] == "FRESH_SINGLE_RANK8_ADAPTER_NO_WARMSTART"
    for arm in corpus.ARMS:
        items = corpus.train_items(candidate, arm)
        assert corpus.trainer.normalize_items(dict(corpus=items)) == items
        assert all(item["spans"][0][1] is False and item["spans"][1][1] is True for item in items)


@pytest.mark.parametrize("root", (0, 1, 2))
def test_tokenizer_fixture_actual_v3_closed_sequences_and_epoch_batches(root):
    candidate = corpus.build_candidate(root)
    before = copy.deepcopy(candidate)
    report = corpus.audit_tokenizer(candidate, Tokenizer())
    assert report["status"] == "CALLBACK_TOKEN_AUDIT_PASS_NOT_NATIVE_CERTIFICATION"
    assert not report["origin_authenticated"] and candidate["native_token_match"] == "NATIVE_TOKEN_MATCH_PENDING"
    assert report["no_truncation"] and not report["loss_bearing_padding"]
    for seed, updates in report["optimizer_update_rows"].items():
        assert len(updates) == 128
        for batch in updates:
            assert len({index // 4 for index in batch}) == 1 and [index % 4 for index in batch] == [0, 1, 2, 3]
            sequences = {arm: Counter(tuple(label for label in report["rows"][arm][index]["labels"] if label != -100)
                                      for index in batch) for arm in corpus.ARMS}
            assert sequences["AUTH"] == sequences["DERANGED"]
    assert report["optimizer_update_rows"]["0"] != report["optimizer_update_rows"]["1"]
    for arm in corpus.ARMS:
        for row in report["rows"][arm]:
            prefix = len(row["prefix_ids"])
            assert row["labels"][:prefix] == [-100] * prefix
            assert row["labels"][-1] == Tokenizer.eos_token_id
            assert row["labels"].count(Tokenizer.eos_token_id) == 1
            assert row["supervised_eos_position"] == row["input_tokens"] - 1
    assert report["input_tokens_per_epoch"]["AUTH"] == report["input_tokens_per_epoch"]["DERANGED"]
    assert report["target_tokens_per_epoch"]["AUTH"] == report["target_tokens_per_epoch"]["DERANGED"]
    assert candidate == before


@pytest.mark.parametrize("tokenizer,reason", ((UnequalLabels(), "label lengths"),
                                            (ContextSensitiveMismatch(), "context lengths"),
                                            (OverlongTokenizer(), "exceeds max_len")))
def test_native_mismatch_refuses_export(candidate, tokenizer, reason):
    with pytest.raises(ValueError, match=reason):
        corpus.audit_tokenizer(candidate, tokenizer)


def test_broken_epoch_shuffle_and_loss_padding_are_rejected(candidate):
    original = corpus.trainer.epoch_order
    def shuffle_rows(packs, seed, epoch, shuffle_groups):
        result = original(packs, seed, epoch, shuffle_groups)
        result[0], result[4] = result[4], result[0]
        return result
    with patch.object(corpus.trainer, "epoch_order", shuffle_rows):
        with pytest.raises(ValueError, match="optimizer group broken"):
            corpus.audit_tokenizer(candidate, Tokenizer())
    collate = corpus.trainer.collate
    def unmask(batch, pad):
        result = collate(batch, pad)
        result["labels"][0][0] = 123
        return result
    with patch.object(corpus.trainer, "collate", unmask):
        with pytest.raises(ValueError, match="padding loss"):
            corpus.audit_tokenizer(candidate, Tokenizer())


def test_native_loader_requires_pins_before_import(candidate, tmp_path):
    with pytest.raises(ValueError, match="hashes required"):
        corpus.audit_native(candidate, tmp_path, {})


@pytest.mark.parametrize("arm", corpus.ARMS)
@pytest.mark.parametrize("split,total", (("train", 64), ("dev", 32)))
def test_symmetric_own_map_scoring_and_full_twin_success(candidate, arm, split, total):
    cases = candidate["train"][arm] if split == "train" else candidate["dev"]
    outputs = {case["id"]: independent_target(case, arm) for case in cases}
    result = corpus.score_outputs(candidate, outputs, split=split, assigned_arm=arm)
    for counts in result["operations"].values():
        assert counts["total"] == counts["strict_surface"] == counts["own_map_strict_joint"] == total
        assert counts["auth_joint_semantic"] == (total if arm == "AUTH" else 0)
    for family in result["twins"].values():
        assert family["own_map_semantic_passes"] == family["own_map_strict_passes"] == total // 2
        assert family["auth_strict_passes"] == (total // 2 if arm == "AUTH" else 0)
    for operation in result["per_stratum"].values():
        for counts in operation.values():
            assert counts["own_map_strict_joint"] == counts["total"]
    assert result["supplies_l1_verdict"] is False


@pytest.mark.parametrize("operation", corpus.OPERATIONS)
def test_semantic_correctness_does_not_hide_surface_failure(candidate, operation):
    case = next(row for row in candidate["dev"] if row["operation"] == operation)
    target = independent_target(case, "AUTH")
    for raw in (" " + target, target + "\n", "\n".join(target.split("\n")[::-1]), target.replace("\n", "\r\n")):
        score = corpus.score_response(case, raw)
        assert score["raw_text"] == raw and not score["strict_surface"]
        assert score["auth_joint_semantic"] and not score["auth_strict_joint"]
    for raw in (target + "\n" + target.split("\n")[-1], target + "\nThat is my answer.",
                target.lower(), target.split("\n")[0], target.replace("dax", "unknown")):
        if raw == target:
            continue
        score = corpus.score_response(case, raw)
        assert score["raw_text"] == raw and not score["auth_joint_semantic"] and not score["strict_surface"]


def test_joint_components_strict_and_twins_are_noncompensatory(candidate):
    outputs = {case["id"]: independent_target(case, "AUTH") for case in candidate["dev"]}
    first = candidate["dev"][0]
    outputs[first["id"]] += "\n"
    result = corpus.score_outputs(candidate, outputs)
    assert result["operations"]["PROSPECT"]["auth_joint_semantic"] == 32
    assert result["operations"]["PROSPECT"]["auth_strict_joint"] == 31
    assert result["twins"]["goal"]["auth_semantic_passes"] == 16
    assert result["twins"]["goal"]["auth_strict_passes"] == 15
    assert result["twins"]["belief"]["auth_strict_passes"] == 15
    assert result["twins"]["outcome"]["auth_strict_passes"] == 16
    with pytest.raises(ValueError, match="missing/extra"):
        corpus.score_outputs(candidate, dict(list(outputs.items())[1:]))
    with pytest.raises(ValueError, match="missing/extra"):
        corpus.score_outputs(candidate, dict(outputs, invented="ACT: dax"))


def test_missing_or_duplicate_component_fails_without_discarding_other_fields(candidate):
    case = candidate["dev"][0]
    prediction, action = independent_target(case, "AUTH").split("\n")
    for raw in (prediction, prediction + "\n" + action + "\n" + action):
        result = corpus.score_response(case, raw)
        assert result["auth_fields"] == dict(PREDICT_ACTION=True, PREDICT_OUTCOME=True, ACT=False)
        assert not result["auth_joint_semantic"] and not result["strict_surface"]
        outputs = {row["id"]: independent_target(row, "AUTH") for row in candidate["dev"]}
        outputs[case["id"]] = raw
        scored = corpus.score_outputs(candidate, outputs)
        assert scored["operations"]["PROSPECT"]["auth_fields"]["ACT"] == 31
        assert scored["twins"]["goal"]["auth_semantic_passes"] == 15


def test_constant_joint_outputs_cannot_pass_flips(candidate):
    examples = {operation: independent_target(next(row for row in candidate["dev"] if row["operation"] == operation), "AUTH")
                for operation in corpus.OPERATIONS}
    outputs = {case["id"]: examples[case["operation"]] for case in candidate["dev"]}
    result = corpus.score_outputs(candidate, outputs)
    assert all(counts["strict_surface"] == 32 and counts["auth_joint_semantic"] == 8
               for counts in result["operations"].values())
    assert all(counts["auth_semantic_passes"] == counts["auth_strict_passes"] == 0 for counts in result["twins"].values())


def test_exact_thresholds_and_untrained_common_prefix_interface(candidate):
    requirements = corpus.threshold_requirements()
    assert requirements["surface"]["minimum"] == 30
    assert requirements["strict_validity"]["minimum"] == 31
    assert requirements["training_own_map"]["minimum"] == 116
    assert requirements["no_phase_spill"]["maximum"] == 0
    assert corpus.threshold_count(7, "3/4") == 6
    with pytest.raises(ValueError, match="binary float"):
        corpus.threshold_count(32, 0.95)
    interface = corpus.teacher_forcing_interface(candidate)
    assert interface["primary_families"] == dict(PROSPECT="belief", REVISE="outcome")
    for request, case in zip(interface["cases"], candidate["dev"]):
        assert request["input_context"] == case["context"] and request["common_assistant_stub"] == ""
        assert request["complete_candidates"] == {arm: independent_target(case, arm) for arm in corpus.ARMS}
    assert candidate["composition"]["cases"] == [] and not interface["supplies_l1_verdict"]
