"""Independent authored truth checks and CPU-only fake-tokenizer audits."""
from collections import Counter, defaultdict
import copy
import hashlib
import itertools
import json
import random
import re

import pytest

from organism_v6 import birth_conditional_corpus as birth


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


@pytest.fixture
def candidate():
    return birth.build_candidate()


def independent_target(row, arm):
    context = row["context"]
    if row["operation"] == "PROSPECT":
        goal = re.search(r"GOAL: (\w+)", context)[1]
        bindings = dict(part.split(" -> ") for part in re.search(r"BELIEF: ([^.]+)", context)[1].split("; "))
        action, outcome = next((action, outcome) for action, outcome in bindings.items() if (outcome == goal) == (arm == "AUTH"))
        return f"PREDICT: {action} -> {outcome}\nACT: {action}"
    if row["operation"] == "REVISE":
        actions = re.search(r"ACTIONS: ([^.]+)", context)[1].split(", ")
        prior = re.search(r"PRIOR: ACT (\w+)", context)[1]
        expected = re.search(r"EXPECTED: (\w+)", context)[1]
        observed = re.search(r"OBSERVED: (\w+)", context)[1]
        keep = (expected == observed) == (arm == "AUTH")
        action = prior if keep else next(value for value in actions if value != prior)
        return f"COMPARE: {'MATCH' if keep else 'MISMATCH'}\nPOLICY: {'KEEP' if keep else 'SWITCH'}\nNEXT: {action}"
    if row["operation"] == "ADDITION":
        operands = [int(value) for value in re.findall(r"\d+", context)]
        assert len(operands) == 2
        return f"ACT: {sum(operands)}"
    literal = re.search(r"(?:amber|marble)-\d-\d{3}", context)[0]
    return f"COPY: {literal}"


@pytest.mark.parametrize("root", (0, 1, 2))
def test_counts_sources_truth_and_balanced_groups(root):
    material = birth.build_candidate(root)
    report = birth.audit_candidate(material)
    assert report["train_counts"] == dict.fromkeys(birth.OPERATIONS, 64)
    assert report["dev_counts"] == dict(PROSPECT=32, REVISE=64, ADDITION=16, COPY=16)
    assert report["source_records"] == 304 and report["groups_per_epoch"] == 32
    events = {row["id"]: row for row in material["source_records"]}
    for arm in birth.ARMS:
        rows = material["train"][arm]
        for row in rows:
            assert row["response"] == independent_target(row, arm)
            event = events[row["source_event_ids"][0]]
            assert event["inputs"] == {key: value for key, value in row["inputs"].items() if key != "action_order"}
            assert event["origin"] == row["origin"] == birth.ORIGIN
            assert event["id"] not in row["context"]
        for offset in range(0, 256, 8):
            block = rows[offset:offset + 8]
            assert [row["order"] for row in block] == list(range(8))
            assert len({row["group"] for row in block}) == 1
            assert [row["operation"] for row in block] == ["PROSPECT", "REVISE", "PROSPECT", "REVISE", "ADDITION", "ADDITION", "COPY", "COPY"]
    for auth, deranged in zip(material["train"]["AUTH"], material["train"]["DERANGED"], strict=True):
        assert {key: value for key, value in auth.items() if key != "response"} == {key: value for key, value in deranged.items() if key != "response"}
        assert (auth["response"] == deranged["response"]) == (auth["operation"] in ("ADDITION", "COPY"))
    for offset in range(0, 256, 8):
        auth = material["train"]["AUTH"][offset:offset + 8]
        deranged = material["train"]["DERANGED"][offset:offset + 8]
        assert [row["response"] for row in deranged] == [auth[index]["response"] for index in (2, 3, 0, 1, 4, 5, 6, 7)]


@pytest.mark.parametrize("split", ("train", "dev"))
def test_full_crossing_inside_each_visible_instance_and_form(candidate, split):
    rows = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
    groups = defaultdict(list)
    for row in rows:
        if row["operation"] in birth.CONDITIONAL:
            groups[(row["operation"], row["instance_id"], row["template"])].append(row)
    for (operation, instance, _), group in groups.items():
        assert all(instance in row["context"] for row in group)
        assert len({tuple(row["inputs"]["action_order"]) for row in group}) == 1
        if operation == "REVISE":
            assert {(row["inputs"]["expected"], row["inputs"]["observed"], row["inputs"]["prior_action"]) for row in group} == set(
                itertools.product(candidate["spellings"]["outcomes"], candidate["spellings"]["outcomes"], candidate["spellings"]["actions"]))
            assert len(group) == 8
        else:
            assert {(row["factors"]["belief"], row["factors"]["goal"]) for row in group} == set(itertools.product((0, 1), repeat=2))
    for operation in birth.CONDITIONAL:
        orders = Counter(tuple(row["inputs"]["action_order"]) for row in rows if row["operation"] == operation)
        assert len(orders) == 2 and len(set(orders.values())) == 1
    for family, pairs in candidate["twins"][split].items():
        indexed = {row["id"]: row for row in rows}
        for first, second in pairs:
            before, after = indexed[first], indexed[second]
            changed = {key for key in before["inputs"] if before["inputs"][key] != after["inputs"][key]}
            assert changed == {family}
            assert before["instance_id"] == after["instance_id"] and before["template"] == after["template"]


def test_split_identifiers_renderings_and_anchor_payloads_are_disjoint(candidate):
    train, dev = candidate["train"]["AUTH"], candidate["dev"]
    for field in ("id", "semantic_id", "instance_id", "context"):
        assert not {row[field] for row in train} & {row[field] for row in dev}
    for operation in birth.OPERATIONS:
        assert not {row["template"] for row in train if row["operation"] == operation} & {row["template"] for row in dev if row["operation"] == operation}
    train_copy = {row["inputs"]["literal"] for row in train if row["operation"] == "COPY"}
    dev_copy = {row["inputs"]["literal"] for row in dev if row["operation"] == "COPY"}
    assert len(train_copy) == 64 and len(dev_copy) == 16 and not train_copy & dev_copy
    train_operands = {number for row in train if row["operation"] == "ADDITION" for number in row["inputs"].values()}
    dev_operands = {number for row in dev if row["operation"] == "ADDITION" for number in row["inputs"].values()}
    assert not train_operands & dev_operands
    assert candidate["confirmation_cases"] == [] and candidate["composition"]["trained_chain_rows"] == 0


@pytest.mark.parametrize("split", ("train", "dev"))
@pytest.mark.parametrize("arm", birth.ARMS)
def test_independent_omitted_expected_lookup_ceiling(candidate, split, arm):
    rows = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
    buckets = defaultdict(Counter)
    for row in rows:
        if row["operation"] != "REVISE":
            continue
        inputs = row["inputs"]
        key = (row["instance_id"], row["template"], tuple(inputs["action_order"]), inputs["observed"], inputs["prior_action"])
        buckets[key][independent_target(row, arm)] += 1
    total = sum(sum(bucket.values()) for bucket in buckets.values())
    maximum = sum(max(bucket.values()) for bucket in buckets.values())
    assert (maximum, total) == (32, 64)
    report = birth.audit_omitted_factors(rows, arm)
    assert report["REVISE"]["without_expected"] == dict(correct=32, total=64, ceiling=.5, projection_values=32, target="FULL_JOINT")
    assert all(entry["ceiling"] <= .5 for operation in report.values() for entry in operation.values())


@pytest.mark.parametrize("split", ("train", "dev"))
@pytest.mark.parametrize("arm", birth.ARMS)
def test_every_omitted_factor_independent_full_joint_lookup(candidate, split, arm):
    rows = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
    report = birth.audit_omitted_factors(rows, arm)
    for operation, names in (("PROSPECT", ("belief", "goal")), ("REVISE", ("expected", "observed", "prior_action"))):
        for omitted in names:
            buckets = defaultdict(Counter)
            for row in rows:
                if row["operation"] == operation:
                    visible = {name: row["inputs"][name] for name in names if name != omitted}
                    key = (row["instance_id"], row["template"], tuple(row["inputs"]["action_order"]), json.dumps(visible, sort_keys=True))
                    buckets[key][independent_target(row, arm)] += 1
            correct = sum(max(bucket.values()) for bucket in buckets.values())
            total = sum(sum(bucket.values()) for bucket in buckets.values())
            assert correct * 2 == total
            assert report[operation]["without_" + omitted]["correct"] == correct
            assert report[operation]["without_" + omitted]["total"] == total


def test_old_fixed_expected_shortcut_and_order_leak_are_rejected(candidate):
    rows = candidate["train"]["AUTH"]
    missing_cross = [row for row in rows if row["operation"] != "REVISE" or row["factors"]["expected"] == 0]
    with pytest.raises(ValueError, match="without_expected"):
        birth.audit_omitted_factors(missing_cross)
    rows = copy.deepcopy(rows)
    for row in rows:
        if row["operation"] == "REVISE":
            row["inputs"]["action_order"] = row["inputs"]["actions"][::(-1 if row["factors"]["expected"] else 1)]
    with pytest.raises(ValueError, match="without_expected"):
        birth.audit_omitted_factors(rows)


@pytest.mark.parametrize("change", ("target", "source", "context", "group", "split", "twin"))
def test_candidate_tampering_rejected(candidate, change):
    altered = copy.deepcopy(candidate)
    if change == "source":
        altered["source_records"][0]["origin"] = "clean"
    elif change == "twin":
        altered["twins"]["dev"]["expected"].pop()
    else:
        field = {"target": "response", "context": "context", "group": "group", "split": "split"}[change]
        altered["train"]["AUTH"][0][field] = "tampered"
    with pytest.raises(ValueError, match="specification"):
        birth.audit_candidate(altered)


def test_explicit_recipe_and_input_only_readout(candidate):
    with pytest.raises(TypeError):
        birth.training_recipe()
    recipe = birth.training_recipe(learning_rate=1e-4, seed=0, epochs=3)
    assert recipe["batch_size"] == 8 and recipe["grad_accum"] == 1 and recipe["pack"] is False and recipe["epochs"] == 3
    assert "init_adapter" not in recipe
    requests = birth.readout_cases(candidate)
    assert len(requests) == 128 and len(birth.readout_cases(candidate, split="train")) == 256
    assert all(not {"response", "expected", "inputs", "factors", "target"} & set(row) for row in requests)
    assert [row["context"] for row in requests] == [row["context"] for row in candidate["dev"]]
    items = birth.train_items(candidate, "AUTH")
    assert all(item["spans"][0][1] is False and item["spans"][1][1] is True for item in items)
    assert len(birth.trainer.normalize_items(items)) == 256


@pytest.mark.parametrize("split", ("train", "dev"))
@pytest.mark.parametrize("arm", birth.ARMS)
def test_symmetric_semantic_scoring_and_all_twins(candidate, split, arm):
    cases = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
    outputs = {row["id"]: independent_target(row, arm) for row in cases}
    result = birth.score_outputs(candidate, outputs, split=split, assigned_arm=arm)
    for operation, metrics in result["operations"].items():
        assert metrics["exact_own_map"] == metrics["own_map_joint_semantic"] == metrics["instruction_compliant"] == metrics["total"]
        assert metrics["tag_spill"] == 0
        if operation in birth.CONDITIONAL and arm == "DERANGED":
            assert metrics["auth_joint_semantic"] == 0
    assert all(row["own_map_strict_pass"] == row["total"] for row in result["twins"].values())
    assert result["supplies_l1_verdict"] is False and "PASS" not in result


def test_anchor_exact_instruction_spill_and_missing_outputs(candidate):
    addition = next(row for row in candidate["dev"] if row["operation"] == "ADDITION")
    target = independent_target(addition, "AUTH")
    assert birth.score_response(addition, target)["instruction_compliant"]
    bad = birth.score_response(addition, "PREDICT: 78\n" + target)
    assert bad["tag_spill"] and not bad["instruction_compliant"] and not bad["auth_joint_semantic"]
    leading_zero = target.replace("ACT: ", "ACT: 0")
    assert birth.score_response(addition, leading_zero)["auth_joint_semantic"]
    assert not birth.score_response(addition, leading_zero)["instruction_compliant"]
    copied = next(row for row in candidate["dev"] if row["operation"] == "COPY")
    text = independent_target(copied, "AUTH")
    assert birth.score_response(copied, text + "\n")["instruction_compliant"]
    assert not birth.score_response(copied, text + " extra")["instruction_compliant"]
    assert birth.score_response(copied, text + "\nACT: 1")["tag_spill"]
    outputs = {row["id"]: independent_target(row, "AUTH") for row in candidate["dev"]}
    outputs.pop(next(iter(outputs)))
    with pytest.raises(ValueError, match="complete"):
        birth.score_outputs(candidate, outputs)


def test_constant_valid_revise_syntax_is_not_conditional_success(candidate):
    outputs = {row["id"]: independent_target(row, "AUTH") for row in candidate["dev"]}
    for row in candidate["dev"]:
        if row["operation"] == "REVISE":
            outputs[row["id"]] = "COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax"
    result = birth.score_outputs(candidate, outputs)
    assert result["operations"]["REVISE"]["strict_surface"] == 64
    assert result["operations"]["REVISE"]["auth_joint_semantic"] == 16
    for family in ("expected", "observed", "prior_action"):
        assert result["twins"][family]["auth_strict_pass"] == 0


@pytest.mark.parametrize("root", (0, 1, 2))
def test_actual_v3_native_fixture_groups_costs_and_eos(root):
    candidate = birth.build_candidate(root)
    recipe = birth.training_recipe(learning_rate=1e-4, seed=root, epochs=2)
    audit = birth.audit_tokenizer(candidate, Tokenizer(), recipe=recipe)
    assert audit["status"] == "CALLBACK_AUDIT_PASS_NOT_NATIVE_CERTIFICATION"
    assert audit["recipe"] == recipe and audit["config_counts"]["optimizer_updates"] == 64
    assert audit["input_tokens_per_epoch"]["AUTH"] == audit["input_tokens_per_epoch"]["DERANGED"]
    assert audit["target_tokens_per_epoch"]["AUTH"] == audit["target_tokens_per_epoch"]["DERANGED"]
    costs = audit["group_costs"][str(root)]
    assert len(costs) == len(audit["optimizer_update_rows"][str(root)]) == 64
    assert sum(row["input_tokens"] for row in costs) == 2 * audit["input_tokens_per_epoch"]["AUTH"]
    assert sum(row["target_tokens"] for row in costs) == 2 * audit["target_tokens_per_epoch"]["AUTH"]
    assert all(row["padded_input_tokens"] == row["input_tokens"] + row["padding_tokens"] and row["eos_tokens"] == 8 for row in costs)
    for arm in birth.ARMS:
        for row in audit["rows"][arm]:
            assert row["input_ids"][-1] == row["labels"][-1] == Tokenizer.eos_token_id
            assert row["context_tokens"] + row["target_tokens"] == row["input_tokens"]
            assert row["labels"][:row["context_tokens"]] == [-100] * row["context_tokens"]
    assert "birth_conditional_corpus.py" in audit["source_sha256"]


@pytest.mark.parametrize("failure", ("label", "overflow", "context", "shuffle", "padding"))
def test_native_fixture_rejects_nonmatching_or_broken_material(candidate, monkeypatch, failure):
    class BrokenTokenizer(Tokenizer):
        def encode(self, text, *, add_special_tokens):
            result = super().encode(text, add_special_tokens=add_special_tokens)
            if failure == "label" and text == " fep":
                result.append(100)
            if failure == "overflow":
                result *= 10
            if failure == "context" and text.startswith("USER:") and "EXPECTED: fep." in text:
                result.append(101)
            return result
    if failure == "shuffle":
        original = birth.trainer.epoch_order
        def broken(*args, **kwargs):
            packs = original(*args, **kwargs)
            packs[0], packs[8] = packs[8], packs[0]
            return packs
        monkeypatch.setattr(birth.trainer, "epoch_order", broken)
    if failure == "padding":
        original = birth.trainer.collate
        def broken(*args, **kwargs):
            batch = original(*args, **kwargs)
            batch["labels"][0][0] = 1
            return batch
        monkeypatch.setattr(birth.trainer, "collate", broken)
    with pytest.raises(ValueError):
        birth.audit_tokenizer(candidate, BrokenTokenizer(), epochs=1)


def test_native_file_pins_fail_before_import(candidate, tmp_path):
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json"):
        (tmp_path / name).write_text(json.dumps(dict(model_type="qwen2")))
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir()}
    hashes["tokenizer.json"] = "0" * 64
    with pytest.raises(ValueError, match="pin mismatch"):
        birth.audit_native(candidate, tmp_path, hashes, recipe=birth.training_recipe(learning_rate=1e-4, seed=0, epochs=1))


def test_native_entry_point_with_mock_local_loader(candidate, tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    from unittest.mock import Mock
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json"):
        (tmp_path / name).write_text(json.dumps(dict(model_type="qwen2")))
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir()}
    loader = Mock(return_value=Tokenizer())
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=loader)))
    report = birth.audit_native(candidate, tmp_path, hashes, recipe=birth.training_recipe(learning_rate=1e-4, seed=0, epochs=1))
    loader.assert_called_once_with(str(tmp_path), local_files_only=True, trust_remote_code=False)
    assert report["tokenizer_file_hashes"] == hashes and report["model_origin_authenticated"] is False
    assert report["config_counts"]["optimizer_updates"] == 32


def test_audit_rejects_conflicting_recipe_and_dose(candidate):
    recipe = birth.training_recipe(learning_rate=1e-4, seed=0, epochs=2)
    with pytest.raises(ValueError, match="conflicting audit epochs"):
        birth.audit_tokenizer(candidate, Tokenizer(), recipe=recipe, epochs=1)
    with pytest.raises(ValueError, match="conflicting audit seeds"):
        birth.audit_tokenizer(candidate, Tokenizer(), recipe=recipe, seeds=(1,))
    recipe["batch_size"] = 4
    with pytest.raises(ValueError, match="eight-row"):
        birth.audit_tokenizer(candidate, Tokenizer(), recipe=recipe)


def test_no_random_state_changes_and_no_hidden_recipe(candidate):
    state = random.getstate()
    assert birth.build_candidate() == candidate
    assert random.getstate() == state
    assert candidate["training_constraints"]["epochs"] == "CALLER_REQUIRED"
    assert candidate["training_constraints"]["learning_rate"] == "CALLER_REQUIRED"
    with pytest.raises(ValueError, match="explicit positive"):
        birth.audit_tokenizer(candidate, Tokenizer())
