"""Sourced stage-A conditional-control material, CPU audits and strict scoring.

AUTH and DERANGED are oracle/authored diagnostics, not child experience or a
clean lineage. No model, runner, optimizer, write, rate selection or L1 verdict
is implemented. Every training sequence is isolated. Four-row optimizer groups
interleave one PROSPECT goal pair and one REVISE outcome pair; group shuffling
must preserve these pairs. A caller must select the learning rate independently.

PROSPECT has 16 training semantic instances (four complete goal/belief squares),
each with four renderings. These are not 16 distinct Boolean rules: the binary
world necessarily repeats logical structure. REVISE has 16 outcome pairs (eight
prior-action/match squares), each with two renderings. Development uses eight
new complete squares per operation, with held identifiers and template families.

Restricted-policy ceilings are best lookup accuracy on the full joint decision,
at most .5, not component equality to .5. Constant joint decisions score .25;
goal-only PROSPECT outcome prediction is perfect by construction. Unique case-ID/
absolute-row lookup can memorize labels; the audited position restriction is
batch slot, not that lookup. Twin-pass ceilings need not be .5.
Belief twins hold the predicted outcome fixed; prior-action twins hold COMPARE
and POLICY fixed. Their required flips must not be fabricated.

audit_tokenizer is explicitly fixture/untrusted-callback evidence. Only
audit_native loads a pinned local tokenizer, offline, before using the same
audit. Neither establishes model-weight origin or authorizes fitting.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

from . import train_adapter_v3 as trainer


ARMS = ("AUTH", "DERANGED")
OPERATIONS = ("PROSPECT", "REVISE")
ORIGIN = "ORACLE_AUTHORED_DIAGNOSTIC_NOT_CHILD_EXPERIENCE_NOT_CLEAN_LINEAGE"
MAX_LEN = 512
SHORTCUT_PROJECTIONS = ("constant", "first_listed_action", "goal_only", "observed_only",
                        "prior_action_name", "template", "batch_slot")
PROSPECT_TEMPLATES = (
    "CASE {instance}. BELIEF: {card}. GOAL: {goal}.\nMake one attempt.",
    "Instance {instance}\nGOAL: {goal}.\nBELIEF: {card}.\nChoose one attempt.",
    "CASE {instance}\nBELIEF: {card}.\nGOAL: {goal}.\nUse the card for one attempt.",
    "Instance {instance}. GOAL: {goal}. BELIEF: {card}.\nDecide on one attempt.",
    "Trial {instance}\nBELIEF: {card}. GOAL: {goal}.\nWhich attempt will you make?",
    "Trial {instance}: GOAL: {goal}.\nBELIEF: {card}.\nMake your choice.",
)
REVISE_TEMPLATES = (
    "CASE {instance}. ACTIONS: {actions}.\nPRIOR: PREDICT {prior} -> {expected}; ACT {prior}.\n"
    "OBSERVED: {observed}.\nReview before the next attempt.",
    "Instance {instance}\nACTIONS: {actions}. PRIOR: PREDICT {prior} -> {expected}; ACT {prior}.\n"
    "OBSERVED: {observed}.\nDecide what to do next.",
    "Trial {instance}. ACTIONS: {actions}.\nPRIOR: PREDICT {prior} -> {expected}; ACT {prior}.\n"
    "OBSERVED: {observed}.\nChoose the next attempt after reviewing this result.",
    "Trial {instance}\nACTIONS: {actions}.\nPRIOR: PREDICT {prior} -> {expected}; ACT {prior}.\n"
    "OBSERVED: {observed}.\nReview the result and decide the next attempt.",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def _labels(values):
    require(isinstance(values, (list, tuple)) and len(values) == 2, "two spellings required")
    require(all(isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9]{1,15}", value)
                for value in values), "spellings must be opaque lowercase words")
    require(len(set(values)) == 2, "duplicate spellings")
    reserved = {"act", "predict", "compare", "policy", "next", "match", "mismatch", "keep", "switch"}
    require(not set(values) & reserved, "protocol words cannot be physical labels")
    return list(values)


def training_recipe(*, learning_rate, seed=0):
    """Caller-selected LR only; returns v3 options for a fresh single rank8 fit."""
    require(type(learning_rate) in (int, float) and math.isfinite(learning_rate) and
            learning_rate > 0, "a positive finite caller-selected learning rate is required")
    require(type(seed) is int and seed in (0, 1, 2), "optimizer seed must be 0, 1 or 2")
    return dict(rank=8, alpha=16, dropout=0.05, lr=learning_rate, epochs=4, seed=seed,
                batch_size=4, grad_accum=1, max_len=MAX_LEN, pack=False, chat_template=False,
                add_eos=True, overflow="truncate", shuffle_groups=True, optimizer="adamw",
                target_modules=list(trainer.ALL_PROJ), layers="all", freeze_a=False,
                svd_init=False, max_steps=0)


def composition_interface():
    """Declaration only: composition is a separate future zero-training assay."""
    return dict(status="UNTRAINED_FUTURE_ASSAY", trained_chain_rows=0, cases=[],
                turns=["card_and_goal -> PROSPECT", "public_outcome -> REVISE",
                       "fresh_object_under_updated_belief -> PROSPECT"],
                required_future_checks=["whole_chain_counterfactual_twins", "no_phase_spill",
                                        "unrelated_interface", "teacher_forced_interaction"],
                supplies_l1_verdict=False)


def threshold_count(total, fraction, *, mode="at_least"):
    """Exact rational threshold arithmetic; no floating-point rounding or gate."""
    require(type(total) is int and total >= 0, "nonnegative integer denominator required")
    require(isinstance(fraction, (str, Fraction)) or type(fraction) is int,
            "use an exact fraction/string, not a binary float")
    value = Fraction(fraction)
    require(0 <= value <= 1 and mode in ("at_least", "at_most"), "invalid threshold")
    numerator = total * value.numerator
    return ((numerator + value.denominator - 1) // value.denominator if mode == "at_least"
            else numerator // value.denominator)


def threshold_requirements():
    """Named denominators only; missing interface/interaction assays prevent an L1 verdict."""
    return dict(surface=dict(predicate="strict_surface", denominator=32, minimum=30),
                strict_validity=dict(predicate="strict_surface", denominator=32,
                                     minimum=threshold_count(32, "0.95")),
                training_own_map=dict(predicate="own_map_strict_joint", denominator=128,
                                      minimum=threshold_count(128, "0.90")),
                semantics=dict(predicate="auth_joint_semantic", denominator=32, minimum=28),
                each_twin_family=dict(predicate="strict_joint_pair", denominator=16, minimum=14),
                no_phase_spill=dict(denominator=16, maximum=threshold_count(16, "0.05", mode="at_most")),
                note="30/32 is not .95; identical surface/strict predicates imply an effective 31/32 requirement.",
                supplies_l1_verdict=False)


def expected_fields(case, arm="AUTH"):
    """Derive fields from the public source inputs, independently of target text."""
    require(arm in ARMS, "unknown assigned map")
    inputs = case["inputs"]
    if case["operation"] == "PROSPECT":
        outcome = inputs["goal"]
        if arm == "DERANGED":
            outcome = next(value for value in inputs["outcomes"] if value != outcome)
        action = next(action for action, value in inputs["belief"].items() if value == outcome)
        return dict(PREDICT_ACTION=action, PREDICT_OUTCOME=outcome, ACT=action)
    require(case["operation"] == "REVISE", "unknown operation")
    match = inputs["expected"] == inputs["observed"]
    if arm == "DERANGED":
        match = not match
    action = inputs["prior_action"] if match else next(
        value for value in inputs["actions"] if value != inputs["prior_action"])
    return dict(COMPARE="MATCH" if match else "MISMATCH", POLICY="KEEP" if match else "SWITCH", NEXT=action)


def response_text(case, arm="AUTH"):
    fields = expected_fields(case, arm)
    if case["operation"] == "PROSPECT":
        return f"PREDICT: {fields['PREDICT_ACTION']} -> {fields['PREDICT_OUTCOME']}\nACT: {fields['ACT']}"
    return f"COMPARE: {fields['COMPARE']}\nPOLICY: {fields['POLICY']}\nNEXT: {fields['NEXT']}"


def _context(case):
    inputs = case["inputs"]
    if case["operation"] == "PROSPECT":
        card = "; ".join(f"{action} -> {inputs['belief'][action]}" for action in inputs["action_order"])
        return PROSPECT_TEMPLATES[case["template"]].format(
            instance=case["instance_id"], card=card, goal=inputs["goal"])
    return REVISE_TEMPLATES[case["template"]].format(
        instance=case["instance_id"], actions=", ".join(inputs["action_order"]),
        prior=inputs["prior_action"], expected=inputs["expected"], observed=inputs["observed"])


def _square(root, split, operation, square, template, actions, outcomes):
    instance = f"r{root}-{split}-{operation.lower()}-{square:02d}"
    local_actions = actions[square % 2:] + actions[:square % 2]
    local_outcomes = outcomes[(square // 2) % 2:] + outcomes[:(square // 2) % 2]
    card_order = ((square // 4) + template) % 2
    order = local_actions[card_order:] + local_actions[:card_order]
    cases = []
    for first, second in itertools.product((0, 1), repeat=2):
        source_id = f"source-{instance}-{first}{second}"
        if operation == "PROSPECT":
            inputs = dict(actions=actions, outcomes=outcomes, action_order=order,
                          belief={local_actions[index]: local_outcomes[index ^ first] for index in (0, 1)},
                          goal=local_outcomes[second])
            factors = dict(belief=first, goal=second)
        else:
            expected = local_outcomes[0]
            observed = expected if second == 0 else local_outcomes[1]
            inputs = dict(actions=actions, outcomes=outcomes, action_order=order,
                          prior_action=local_actions[first], expected=expected, observed=observed)
            factors = dict(prior_action=first, mismatch=second)
        case = dict(id=f"{instance}-{first}{second}-view{template}",
                    semantic_id=f"{instance}-{first}{second}", instance_id=instance,
                    split=split, operation=operation, template=template, factors=factors,
                    source_event_ids=[source_id], origin=ORIGIN, inputs=copy.deepcopy(inputs))
        case["context"] = _context(case)
        cases.append(case)
    return cases


def _twins(cases):
    squares = defaultdict(dict)
    for case in cases:
        factors = case["factors"]
        coordinate = (factors["belief"], factors["goal"]) if case["operation"] == "PROSPECT" else (
            factors["prior_action"], factors["mismatch"])
        square = squares[(case["operation"], case["instance_id"], case["template"])]
        require(coordinate not in square, "duplicate square corner")
        square[coordinate] = case["id"]
    pairs = dict(goal=[], belief=[], outcome=[], prior_action=[])
    for (operation, _, _), square in squares.items():
        require(set(square) == set(itertools.product((0, 1), repeat=2)), "incomplete counterfactual square")
        first_family, second_family = ("goal", "belief") if operation == "PROSPECT" else ("outcome", "prior_action")
        for bit in (0, 1):
            pairs[first_family].append([square[(bit, 0)], square[(bit, 1)]])
            pairs[second_family].append([square[(0, bit)], square[(1, bit)]])
    return pairs


def _construct(root, action_labels, outcome_labels):
    actions = action_labels[root % 2:] + action_labels[:root % 2]
    outcomes = outcome_labels[(root // 2) % 2:] + outcome_labels[:(root // 2) % 2]
    prospect_pairs, revise_pairs, dev = [], [], []
    for square, template in itertools.product(range(4), range(4)):
        cases = _square(root, "train", "PROSPECT", square, template, actions, outcomes)
        prospect_pairs.extend([cases[:2], cases[2:]])
    for square, template in itertools.product(range(8), range(2)):
        cases = _square(root, "train", "REVISE", square, template, actions, outcomes)
        for pair in (cases[:2], cases[2:]):
            revise_pairs.append(pair[::-1] if (square // 2) % 2 else pair)
    training = []
    for batch, (prospect, revise) in enumerate(zip(prospect_pairs, revise_pairs)):
        for case in (prospect[0], revise[0], prospect[1], revise[1]):
            case["group"] = f"r{root}-batch-{batch:03d}"
            case["order"] = len(training) % 4
            training.append(case)
    for operation in OPERATIONS:
        for square in range(8):
            template = (4 if operation == "PROSPECT" else 2) + square % 2
            cases = _square(root, "dev", operation, square, template, actions, outcomes)
            if operation == "REVISE" and (square // 2) % 2:
                cases = [cases[1], cases[0], cases[3], cases[2]]
            dev.extend(cases)
    sources = {}
    for case in training + dev:
        source_inputs = {key: value for key, value in case["inputs"].items() if key != "action_order"}
        event = dict(id=case["source_event_ids"][0], origin=ORIGIN, split=case["split"],
                     instance_id=case["instance_id"], operation=case["operation"], inputs=source_inputs,
                     rule="select consequence relative to goal" if case["operation"] == "PROSPECT" else
                          "compare public expected/observed; keep on match, switch otherwise")
        require(event["id"] not in sources or sources[event["id"]] == event, "source changes across views")
        sources[event["id"]] = event
    arms = {}
    for arm in ARMS:
        arms[arm] = [dict(copy.deepcopy(case), response=response_text(case, arm)) for case in training]
    return dict(schema=1, status="CANDIDATE_CPU_ONLY", native_token_match="NATIVE_TOKEN_MATCH_PENDING",
                root=root, label_config=dict(actions=action_labels, outcomes=outcome_labels),
                spellings=dict(actions=actions, outcomes=outcomes), origin=ORIGIN,
                initialization="FRESH_SINGLE_RANK8_ADAPTER_NO_WARMSTART",
                learning_rate="REQUIRED_CALLER_SELECTION_NO_DEFAULT", train=arms, dev=dev,
                source_records=list(sources.values()), twins=dict(train=_twins(training), dev=_twins(dev)),
                composition=composition_interface(), confirmation_cases=[],
                claim_limits="Authored controllability only; no model-origin, child-experience, L1 or H1 pass.")


def build_candidate(root=0, action_labels=("dax", "wug"), outcome_labels=("mip", "zot")):
    """Pure deterministic candidate; no tokenizer parity or launch authorization."""
    require(type(root) is int and root in (0, 1, 2), "material root must be 0, 1 or 2")
    actions, outcomes = _labels(action_labels), _labels(outcome_labels)
    require(not set(actions) & set(outcomes), "action and outcome spellings must be disjoint")
    return _construct(root, actions, outcomes)


def _projection(case, index, name):
    inputs = case["inputs"]
    if name == "constant":
        return "constant"
    if name == "first_listed_action":
        first = inputs["action_order"][0]
        return (first, inputs["belief"][first]) if case["operation"] == "PROSPECT" else first
    if name == "goal_only":
        return inputs.get("goal")
    if name == "observed_only":
        return inputs.get("observed")
    if name == "prior_action_name":
        return inputs.get("prior_action")
    if name == "template":
        return case["template"]
    require(name == "batch_slot", "projection is not on the frozen allowlist")
    return index % 4


def _lookup_ceiling(keys, targets):
    buckets = defaultdict(Counter)
    for key, target in zip(keys, targets):
        buckets[key][target] += 1
    maximum = sum(max(counts.values()) for counts in buckets.values())
    return dict(correct=maximum, total=len(targets), ceiling=maximum / len(targets),
                projection_values=len(buckets), possible_lookup_policies=len(set(targets)) ** len(buckets))


def audit_restricted_baselines(cases, arm="AUTH"):
    """Exact finite lookup enumeration C(h)=sum_z max_y count(z,y)/N on joint decisions.

    The frozen projections never access target length, branch labels, expected
    answers, pair coordinates or unique IDs. Batch slot means index modulo four
    in the registered interleave (train) or square layout (dev). First-listed
    PROSPECT projection includes that action's public binding, but not GOAL.
    """
    require(arm in ARMS, "unknown assigned map")
    report = {}
    for operation in OPERATIONS:
        indexed = [(index, case) for index, case in enumerate(cases) if case["operation"] == operation]
        subset = [case for _, case in indexed]
        require(subset, f"missing {operation} cases")
        decisions = [expected_fields(case, arm) for case in subset]
        joint = [tuple(fields.values()) for fields in decisions]
        entries = {}
        for name in SHORTCUT_PROJECTIONS:
            keys = [_projection(case, index, name) for index, case in indexed]
            if all(key is None for key in keys):
                entries[name] = dict(applicable=False, reason="input feature absent for this operation")
                continue
            require(all(key is not None for key in keys), "inconsistent feature visibility")
            result = _lookup_ceiling(keys, joint)
            require(result["correct"] * 2 <= result["total"], f"restricted joint leakage/correlation: {operation}/{name}")
            entries[name] = dict(result, applicable=True, target="FULL_JOINT", component_ceilings={
                field: _lookup_ceiling(keys, [fields[field] for fields in decisions])["ceiling"]
                for field in decisions[0]})
        report[operation] = entries
    return dict(operations=report, exceptions={
        "absolute_row_or_unique_case_id": "Unrestricted lookup can memorize targets (ceiling 1); not batch-slot policy.",
        "goal_only_outcome": "Outcome alone equals GOAL (AUTH) or its complement (DERANGED); ceiling 1 is allowed.",
        "belief_twin_outcome": "Goal fixed: predicted outcome must not flip; selected action must flip.",
        "prior_action_twin_compare_policy": "Match status fixed: only NEXT must flip.",
        "absent_features": "PROSPECT has no observed token; REVISE has no goal. No ceiling is asserted for absent features.",
        "complete_twin_score": "A full-twin ceiling need not be .5; constant decisions pass zero differing-decision pairs."})


def audit_candidate(candidate):
    """Reject changed sources, target maps, split leakage, schedules or marginals."""
    config = candidate["label_config"]
    expected = build_candidate(candidate["root"], config["actions"], config["outcomes"])
    require(candidate == expected, "source/rendering/map/schedule binding changed")
    auth, deranged = (candidate["train"][arm] for arm in ARMS)
    require(len(auth) == len(deranged) == 128 and len(candidate["dev"]) == 64, "incorrect panel size")
    require([case["operation"] for case in auth] == list(OPERATIONS) * 64, "interleave changed")
    train_ids = {case["instance_id"] for case in auth}
    require(not train_ids & {case["instance_id"] for case in candidate["dev"]}, "split instance leakage")
    require(not {case["context"] for case in auth} & {case["context"] for case in candidate["dev"]},
            "split rendering leakage")
    for offset in range(0, 128, 4):
        before, after = auth[offset:offset + 4], deranged[offset:offset + 4]
        require([case["context"] for case in before] == [case["context"] for case in after], "paired prompt mismatch")
        require(Counter(case["response"] for case in before) == Counter(case["response"] for case in after),
                "per-batch target multiset mismatch")
    for split, cases in (("train", auth), ("dev", candidate["dev"])):
        lookup = {case["id"]: case for case in cases}
        require(len(lookup) == len(cases), "duplicate case IDs")
        for family, pairs in candidate["twins"][split].items():
            for left_id, right_id in pairs:
                left, right = lookup[left_id], lookup[right_id]
                require(left["instance_id"] == right["instance_id"] and left["template"] == right["template"],
                        "twin nuisance/visible identifier mismatch")
                changed = {key for key in left["inputs"] if left["inputs"][key] != right["inputs"][key]}
                allowed = dict(goal={"goal"}, belief={"belief"}, outcome={"observed"},
                               prior_action={"prior_action"})[family]
                require(changed == allowed, "twin changes non-intervention inputs")
                replaced = copy.deepcopy(left)
                for key in allowed:
                    replaced["inputs"][key] = right["inputs"][key]
                require(_context(replaced) == right["context"], "non-intervention twin prompt bytes changed")
    baselines = {split: {arm: audit_restricted_baselines(cases, arm) for arm in ARMS}
                 for split, cases in (("train", auth), ("dev", candidate["dev"]))}
    return dict(status="PURE_AUDIT_PASS_NATIVE_PENDING", candidate_sha256=digest(candidate),
                train_rows_per_arm=128, dev_rows=64, train_instances=dict(PROSPECT=16, REVISE=32),
                dev_twins={key: len(value) for key, value in candidate["twins"]["dev"].items()},
                baselines=baselines, native_token_match="NATIVE_TOKEN_MATCH_PENDING")


def train_items(candidate, arm, render_context=None):
    """v3 TrainItem schema. Without a native renderer these are provisional only."""
    require(arm in ARMS, "unknown arm")
    audit_candidate(candidate)
    render_context = render_context or (lambda value: value)
    return [dict(spans=[[render_context(case["context"]), False, "context"],
                        [case["response"], True, "authored_conditional_target"]],
                 group=case["group"], order=case["order"], view=case["operation"],
                 category="authored_conditional_target", meta=dict(case_id=case["id"],
                 semantic_id=case["semantic_id"], source_event_ids=case["source_event_ids"],
                 origin=ORIGIN, split="train")) for case in candidate["train"][arm]]


def audit_tokenizer(candidate, tokenizer, *, max_len=MAX_LEN):
    """Exercise actual v3 encoding, EOS, padding and all 3x4 epoch schedules.

    A supplied callback can be a fixture; this entry point NEVER labels it a
    verified native tokenizer. audit_native provides the authenticated local
    loading route. Per-row target lengths may differ; paired per-batch length,
    EOS-position and token multisets must be identical without padding targets.
    """
    audit_candidate(candidate)
    require(type(max_len) is int and max_len == MAX_LEN, "stage-A max_len must remain 512")
    eos, pad = tokenizer.eos_token_id, tokenizer.pad_token_id
    require(type(eos) is int and type(pad) is int and eos != pad, "distinct EOS/PAD IDs required")
    for labels in candidate["spellings"].values():
        for prefix in ("", " "):
            lengths = [len(tokenizer.encode(prefix + label, add_special_tokens=False)) for label in labels]
            require(lengths[0] == lengths[1] and lengths[0] > 0, "native physical label lengths differ")
    render = lambda text: tokenizer.apply_chat_template([dict(role="user", content=text)],
                                                       tokenize=False, add_generation_prompt=True)
    corpora = {arm: train_items(candidate, arm, render) for arm in ARMS}
    segments, records = {}, {}
    for arm in ARMS:
        segments[arm], records[arm] = [], []
        for index, item in enumerate(trainer.normalize_items(corpora[arm])):
            prefix = tokenizer.encode(item["spans"][0][0], add_special_tokens=False)
            target = tokenizer.encode(item["spans"][1][0], add_special_tokens=False)
            require(prefix and target and eos not in target and pad not in target, "invalid target special tokens")
            expected_ids = prefix + target + [eos]
            require(len(expected_ids) <= max_len, "native sequence exceeds max_len; no truncation permitted")
            result = trainer.encode_item_segments(item, tokenizer, max_len, False, True, index, overflow="truncate")
            require(len(result) == 1, "missing/split native row")
            segment = result[0]
            require(segment.context_dropped == segment.target_dropped == 0 and
                    segment.ids == expected_ids and segment.labels == [-100] * len(prefix) + target + [eos] and
                    segment.n_target == len(target) + 1,
                    "native target/context/EOS boundary mismatch")
            segments[arm].append(segment)
            records[arm].append(dict(case_id=item["meta"]["case_id"], prefix_ids=prefix,
                                     input_ids=segment.ids, labels=segment.labels,
                                     input_tokens=len(segment.ids), target_tokens=segment.n_target,
                                     supervised_eos_position=len(segment.ids) - 1))
    for before, after in zip(records["AUTH"], records["DERANGED"]):
        require(before["case_id"] == after["case_id"] and before["prefix_ids"] == after["prefix_ids"],
                "actual paired native prefixes differ")
    for offset in range(0, 128, 4):
        for first, second in ((0, 2), (1, 3)):
            left, right = records["AUTH"][offset + first], records["AUTH"][offset + second]
            require(len(left["prefix_ids"]) == len(right["prefix_ids"]), "swap-pair native context lengths differ")
            for before, after in ((first, second), (second, first)):
                auth_labels = [label for label in records["AUTH"][offset + before]["labels"] if label != -100]
                other_labels = [label for label in records["DERANGED"][offset + after]["labels"] if label != -100]
                require(auth_labels == other_labels, "complete supervised sequence swap including EOS failed")
    schedules = {}
    for seed in (0, 1, 2):
        schedule = []
        for epoch in range(4):
            orders = {arm: trainer.epoch_order(trainer.pack_by_group(segments[arm], max_len, False),
                                              seed, epoch, True) for arm in ARMS}
            for offset in range(0, 128, 4):
                summaries, case_orders = {}, {}
                for arm in ARMS:
                    packs = orders[arm][offset:offset + 4]
                    require(len(packs) == 4 and all(len(pack) == 1 for pack in packs) and
                            len({pack[0].group for pack in packs}) == 1, "paired optimizer group broken")
                    batch = trainer.collate(packs, pad)
                    width = max(len(pack[0].ids) for pack in packs)
                    for position, pack in enumerate(packs):
                        segment = pack[0]
                        padding = width - len(segment.ids)
                        require(batch["input_ids"][position] == segment.ids + [pad] * padding and
                                batch["labels"][position] == segment.labels + [-100] * padding and
                                batch["position_ids"][position][:len(segment.ids)] == list(range(len(segment.ids))),
                                "padding loss or altered sequence/positions")
                    case_orders[arm] = [pack[0].item_index for pack in packs]
                    summaries[arm] = dict(input_lengths=sorted(len(pack[0].ids) for pack in packs),
                        target_lengths=sorted(pack[0].n_target for pack in packs),
                        eos_positions=sorted(len(pack[0].ids) - 1 for pack in packs),
                        joint_lengths=sorted((len(pack[0].ids) - pack[0].n_target, pack[0].n_target,
                                              len(pack[0].ids), len(pack[0].ids) - 1) for pack in packs),
                        target_sequences=Counter(tuple(label for label in pack[0].labels if label != -100)
                                                 for pack in packs),
                        target_multiset=Counter(label for pack in packs for label in pack[0].labels if label != -100),
                        input_multiset=Counter(token for pack in packs for token in pack[0].ids))
                require(case_orders["AUTH"] == case_orders["DERANGED"], "native arm order mismatch")
                require(summaries["AUTH"] == summaries["DERANGED"], "per-batch native length/EOS/token parity failed")
                schedule.append(case_orders["AUTH"])
        require(len(schedule) == 128, "expected 128 optimizer updates per four-epoch arm")
        schedules[str(seed)] = schedule
    return dict(status="CALLBACK_TOKEN_AUDIT_PASS_NOT_NATIVE_CERTIFICATION", candidate_sha256=digest(candidate),
                tokenizer_class=f"{type(tokenizer).__module__}.{type(tokenizer).__name__}",
                corpora=corpora, rows=records, optimizer_update_rows=schedules,
                input_tokens_per_epoch={arm: sum(row["input_tokens"] for row in records[arm]) for arm in ARMS},
                target_tokens_per_epoch={arm: sum(row["target_tokens"] for row in records[arm]) for arm in ARMS},
                source_sha256={"conditional_behavior_corpus.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               "train_adapter_v3.py": hashlib.sha256(Path(trainer.__file__).read_bytes()).hexdigest()},
                no_truncation=True, loss_bearing_padding=False, origin_authenticated=False)


def audit_native(candidate, model_path, expected_file_hashes):
    """Load only a pinned local tokenizer; no downloads, model construction or writes."""
    directory = Path(model_path).expanduser().resolve(strict=True)
    require(directory.is_dir(), "local tokenizer directory required")
    required = {"config.json", "tokenizer.json", "tokenizer_config.json"}
    optional = {"vocab.json", "merges.txt", "special_tokens_map.json", "added_tokens.json",
                "chat_template.jinja", "chat_template.json"}
    required |= {name for name in optional if (directory / name).exists()}
    require(not (directory / "chat_templates").exists(), "external chat-template directory requires a separately bound audit")
    require(isinstance(expected_file_hashes, dict) and required <= set(expected_file_hashes),
            "config/tokenizer/tokenizer_config hashes required")
    for name, expected in expected_file_hashes.items():
        require(isinstance(name, str) and Path(name).name == name, "flat local tokenizer filenames required")
        path = directory / name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                f"local tokenizer pin mismatch: {name}")
    require(json.loads((directory / "config.json").read_text()).get("model_type") == "qwen2", "expected Qwen2 base config")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
    report = audit_tokenizer(candidate, tokenizer)
    for name, expected in expected_file_hashes.items():
        require(hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected, "tokenizer files changed during audit")
    report.update(status="NATIVE_TOKEN_MATCH_VERIFIED", tokenizer_path=str(directory),
                  tokenizer_file_hashes=dict(expected_file_hashes), model_weight_origin="NOT_AUTHENTICATED")
    return report


def _semantic_fields(case, raw):
    """Recognize exact field vocabulary with benign whitespace/order diagnostics.

    Raw text is never rewritten. Prose, aliases, unknown labels, missing or
    duplicate fields fail; whitespace/reordered unique fields can be semantically
    right while strict procedural surface is false.
    """
    actions = "|".join(re.escape(value) for value in case["inputs"]["actions"])
    outcomes = "|".join(re.escape(value) for value in case["inputs"]["outcomes"])
    space = r"[ \t\r]*"
    if case["operation"] == "PROSPECT":
        patterns = [rf"{space}PREDICT:{space}(?P<PREDICT_ACTION>{actions}){space}->{space}(?P<PREDICT_OUTCOME>{outcomes}){space}",
                    rf"{space}ACT:{space}(?P<ACT>{actions}){space}"]
    else:
        patterns = [rf"{space}COMPARE:{space}(?P<COMPARE>MATCH|MISMATCH){space}",
                    rf"{space}POLICY:{space}(?P<POLICY>KEEP|SWITCH){space}",
                    rf"{space}NEXT:{space}(?P<NEXT>{actions}){space}"]
    fields, ambiguous = {}, set()
    for line in raw.split("\n"):
        if re.fullmatch(space, line):
            continue
        matches = [match for pattern in patterns if (match := re.fullmatch(pattern, line))]
        if len(matches) != 1:
            return {}
        incoming = matches[0].groupdict()
        ambiguous.update(set(fields) & set(incoming))
        fields.update(incoming)
        for key in ambiguous:
            fields.pop(key, None)
    return fields


def score_response(case, raw, *, assigned_arm="AUTH"):
    """Keep raw bytes and strict syntax separate from unambiguous joint semantics."""
    require(isinstance(raw, str), "raw response must be text")
    require(assigned_arm in ARMS, "unknown assigned map")
    actions = "|".join(re.escape(value) for value in case["inputs"]["actions"])
    outcomes = "|".join(re.escape(value) for value in case["inputs"]["outcomes"])
    if case["operation"] == "PROSPECT":
        pattern = rf"PREDICT: (?P<PREDICT_ACTION>{actions}) -> (?P<PREDICT_OUTCOME>{outcomes})\nACT: (?P<ACT>{actions})"
    else:
        require(case["operation"] == "REVISE", "unknown operation")
        pattern = rf"COMPARE: (?P<COMPARE>MATCH|MISMATCH)\nPOLICY: (?P<POLICY>KEEP|SWITCH)\nNEXT: (?P<NEXT>{actions})"
    match = re.fullmatch(pattern, raw)
    fields = _semantic_fields(case, raw)
    authentic = {key: fields.get(key) == value for key, value in expected_fields(case, "AUTH").items()}
    own = {key: fields.get(key) == value for key, value in expected_fields(case, assigned_arm).items()}
    return dict(case_id=case["id"], raw_text=raw, strict_surface=match is not None, fields=fields,
                auth_fields=authentic, own_map_fields=own, auth_joint_semantic=all(authentic.values()),
                own_map_joint_semantic=all(own.values()),
                auth_strict_joint=match is not None and all(authentic.values()),
                own_map_strict_joint=match is not None and all(own.values()))


def _counts(rows):
    return dict(total=len(rows), strict_surface=sum(row["strict_surface"] for row in rows),
                auth_joint_semantic=sum(row["auth_joint_semantic"] for row in rows),
                own_map_joint_semantic=sum(row["own_map_joint_semantic"] for row in rows),
                auth_strict_joint=sum(row["auth_strict_joint"] for row in rows),
                own_map_strict_joint=sum(row["own_map_strict_joint"] for row in rows),
                auth_fields={key: sum(row["auth_fields"][key] for row in rows) for key in rows[0]["auth_fields"]},
                own_map_fields={key: sum(row["own_map_fields"][key] for row in rows) for key in rows[0]["own_map_fields"]})


def score_outputs(candidate, outputs, *, split="dev", assigned_arm="AUTH"):
    """Complete fixed-panel metrics, strata and joint twin success; no L1 gate."""
    audit_candidate(candidate)
    require(split in ("train", "dev"), "only registered train/dev panels exist")
    require(assigned_arm in ARMS, "unknown assigned map")
    cases = candidate["train"][assigned_arm] if split == "train" else candidate["dev"]
    require(isinstance(outputs, dict) and set(outputs) == {case["id"] for case in cases},
            "missing/extra output IDs are not scientific zeros")
    rows = {case["id"]: score_response(case, outputs[case["id"]], assigned_arm=assigned_arm) for case in cases}
    operations, strata = {}, {}
    for operation in OPERATIONS:
        subset = [case for case in cases if case["operation"] == operation]
        operations[operation] = _counts([rows[case["id"]] for case in subset])
        groups = defaultdict(list)
        for case in subset:
            fields, inputs = expected_fields(case), case["inputs"]
            action = fields["ACT"] if operation == "PROSPECT" else fields["NEXT"]
            values = dict(action=action, outcome=inputs["goal"] if operation == "PROSPECT" else inputs["observed"],
                          template=str(case["template"]), card_order=",".join(inputs["action_order"]),
                          target_position=str(inputs["action_order"].index(action)))
            if operation == "REVISE":
                values["branch"] = fields["COMPARE"]
                values["prior_action"] = inputs["prior_action"]
            else:
                values["belief"] = str(case["factors"]["belief"])
            for key, value in values.items():
                groups[f"{key}/{value}"].append(rows[case["id"]])
        strata[operation] = {key: _counts(value) for key, value in groups.items()}
    twins = {}
    flip_fields = dict(goal=("PREDICT_ACTION", "PREDICT_OUTCOME", "ACT"),
                       belief=("PREDICT_ACTION", "ACT"), outcome=("COMPARE", "POLICY", "NEXT"),
                       prior_action=("NEXT",))
    for family, pairs in candidate["twins"][split].items():
        scored = []
        for first_id, second_id in pairs:
            first, second = rows[first_id], rows[second_id]
            flips = bool(first["fields"] and second["fields"]) and all(
                field in first["fields"] and field in second["fields"] and
                first["fields"][field] != second["fields"][field] for field in flip_fields[family])
            auth_pass = flips and first["auth_joint_semantic"] and second["auth_joint_semantic"]
            own_pass = flips and first["own_map_joint_semantic"] and second["own_map_joint_semantic"]
            strict = first["strict_surface"] and second["strict_surface"]
            scored.append(dict(case_ids=[first_id, second_id], full_required_flip=flips,
                               auth_semantic_pass=auth_pass, own_map_semantic_pass=own_pass,
                               auth_strict_pass=auth_pass and strict, own_map_strict_pass=own_pass and strict))
        twins[family] = dict(total=len(pairs), auth_semantic_passes=sum(row["auth_semantic_pass"] for row in scored),
                            own_map_semantic_passes=sum(row["own_map_semantic_pass"] for row in scored),
                            auth_strict_passes=sum(row["auth_strict_pass"] for row in scored),
                            own_map_strict_passes=sum(row["own_map_strict_pass"] for row in scored), rows=scored)
    return dict(candidate_sha256=digest(candidate), split=split, assigned_arm=assigned_arm,
                rows=list(rows.values()), operations=operations, per_stratum=strata, twins=twins,
                stratum_reference="AUTH-grounded action/branch; public goal/observed outcome and nuisance settings",
                supplies_l1_verdict=False, composition="SEPARATE_UNTRAINED_FUTURE_ASSAY")


def teacher_forcing_interface(candidate, *, split="dev"):
    """Future full-continuation contrasts; never condition ACT/POLICY on gold fields."""
    audit_candidate(candidate)
    require(split in ("train", "dev"), "unregistered split")
    cases = candidate["dev"] if split == "dev" else candidate["train"]["AUTH"]
    return dict(status="UNEXECUTED_INTERFACE_ONLY", common_prefix_rule="INPUT_ONLY_PLUS_EMPTY_ASSISTANT_STUB",
                primary_families=dict(PROSPECT="belief", REVISE="outcome"),
                log_odds_threshold_nats=1, supplies_l1_verdict=False,
                cases=[dict(case_id=case["id"], input_context=case["context"], common_assistant_stub="",
                            complete_candidates={arm: response_text(case, arm) for arm in ARMS}) for case in cases])
