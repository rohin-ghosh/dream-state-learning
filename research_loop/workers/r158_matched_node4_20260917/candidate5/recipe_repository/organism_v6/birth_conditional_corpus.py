"""Authored BIRTH diagnostics, not own-wake experience or clean ancestry.

Pure candidate/scorer plus optional offline tokenizer audit; no runner or fit.
Eight isolated rows per optimizer group preserve two conditional target swaps
and four identical truthful anchors. Epochs/LR are caller choices, not defaults.
REVISE crosses EXPECTED x OBSERVED x PRIOR within every visible instance/form.
No CPU audit or response score supplies a birth, cognition, Q0, L1 or H1 pass.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import itertools
import json
from pathlib import Path
import re

from . import conditional_behavior_corpus as legacy
from . import train_adapter_v3 as trainer


ARMS = legacy.ARMS
CONDITIONAL = ("PROSPECT", "REVISE")
OPERATIONS = (*CONDITIONAL, "ADDITION", "COPY")
ORIGIN = "ORACLE_AUTHORED_BIRTH_DIAGNOSTIC_NOT_OWN_WAKE_NOT_CLEAN_ANCESTRY"
GROUP_SIZE = 8
MAX_LEN = 512
SCHEMA = "birth-conditional-crossed-v1"
REVISE_TEMPLATES = (
    "CASE {instance}. ACTIONS: {actions}.\nPRIOR: ACT {prior}.\nEXPECTED: {expected}.\n"
    "OBSERVED: {observed}.\nReview before the next attempt.",
    "Instance {instance}\nACTIONS: {actions}. EXPECTED: {expected}.\nPRIOR: ACT {prior}.\n"
    "OBSERVED: {observed}.\nDecide what to do next.",
    "Trial {instance}\nPRIOR: ACT {prior}. ACTIONS: {actions}.\nEXPECTED: {expected}.\n"
    "OBSERVED: {observed}.\nReview this result before choosing the next attempt.",
    "Trial {instance}: ACTIONS: {actions}.\nOBSERVED: {observed}.\nEXPECTED: {expected}.\n"
    "PRIOR: ACT {prior}.\nChoose the next attempt after reviewing the result.",
)
ADDITION_TEMPLATES = (
    "Add {left} and {right}.\nReply only ACT: <sum>.",
    "Compute {left} + {right}. Return one line: ACT: <sum>.",
    "What is the sum of {left} and {right}? Output ACT: <sum> only.",
    "Find {left} plus {right}. Use just ACT: <sum>, with no other fields.",
)
COPY_TEMPLATES = (
    "Literal: {literal}\nReturn only COPY: <literal>, copying the literal exactly.",
    "Copy this literal exactly: {literal}\nUse only one line: COPY: <literal>.",
    "Given literal {literal}, reproduce it as COPY: <literal>. Nothing else.",
    "Repeat {literal} exactly after COPY: on one line, with no other fields.",
)
FACTOR_NAMES = dict(PROSPECT=("belief", "goal"), REVISE=("expected", "observed", "prior_action"))
FAMILY_NAMES = dict(belief="belief", goal="goal", expected="expected", observed="observed", prior_action="prior_action")
SWAP = (2, 3, 0, 1, 4, 5, 6, 7)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()).hexdigest()


def response_text(case, arm="AUTH"):
    require(arm in ARMS, "unknown arm")
    if case["operation"] in CONDITIONAL:
        return legacy.response_text(case, arm)
    if case["operation"] == "ADDITION":
        return f"ACT: {case['inputs']['left'] + case['inputs']['right']}"
    require(case["operation"] == "COPY", "unknown operation")
    return f"COPY: {case['inputs']['literal']}"


def _prospect(root, split, square, template, actions, outcomes):
    rows = legacy._square(root, split, "PROSPECT", square, template, actions, outcomes)
    for row in rows:
        for key in ("id", "semantic_id", "instance_id"):
            row[key] = "birth-" + row[key]
        row["source_event_ids"] = ["source-" + row["semantic_id"]]
        row["origin"] = ORIGIN
        row["context"] = legacy._context(row)
    return rows


def _revise(root, split, instance, template, actions, outcomes):
    name = f"birth-r{root}-{split}-revise-{instance:02d}"
    action_order = actions[::-1] if (instance // 2 + template) % 2 else list(actions)
    rows = []
    for expected, observed, prior in itertools.product((0, 1), repeat=3):
        semantic_id = f"{name}-{expected}{observed}{prior}"
        inputs = dict(actions=list(actions), outcomes=list(outcomes), action_order=action_order,
                      expected=outcomes[expected], observed=outcomes[observed], prior_action=actions[prior])
        context = REVISE_TEMPLATES[template].format(instance=name, actions=", ".join(action_order),
            prior=inputs["prior_action"], expected=inputs["expected"], observed=inputs["observed"])
        rows.append(dict(id=f"{semantic_id}-view{template}", semantic_id=semantic_id, instance_id=name,
                         operation="REVISE", split=split, template=template, context=context, inputs=inputs,
                         factors=dict(expected=expected, observed=observed, prior_action=prior),
                         source_event_ids=["source-" + semantic_id], origin=ORIGIN))
    return rows


def _anchors(root, split):
    count = 64 if split == "train" else 16
    rows = {operation: [] for operation in ("ADDITION", "COPY")}
    for index in range(count):
        template = index % 2 + (0 if split == "train" else 2)
        left, right = ((2 + index // 8, 12 + index % 8) if split == "train" else (31 + index // 4, 47 + index % 4))
        literal = f"{'amber' if split == 'train' else 'marble'}-{root}-{index:03d}"
        for operation, inputs, templates in (
            ("ADDITION", dict(left=left, right=right), ADDITION_TEMPLATES),
            ("COPY", dict(literal=literal), COPY_TEMPLATES),
        ):
            name = f"birth-r{root}-{split}-{operation.lower()}-{index:03d}"
            rows[operation].append(dict(id=name, semantic_id=name, instance_id=name, operation=operation,
                split=split, template=template, context=templates[template].format(**inputs), inputs=inputs,
                factors={}, source_event_ids=["source-" + name], origin=ORIGIN))
    return rows


def _twins(cases):
    panels = defaultdict(dict)
    for case in cases:
        if case["operation"] not in CONDITIONAL:
            continue
        names = FACTOR_NAMES[case["operation"]]
        coordinate = tuple(case["factors"][name] for name in names)
        panel = panels[(case["operation"], case["instance_id"], case["template"])]
        require(coordinate not in panel, "duplicate conditional corner")
        panel[coordinate] = case["id"]
    result = {family: [] for family in FAMILY_NAMES.values()}
    for (operation, _, _), panel in panels.items():
        names = FACTOR_NAMES[operation]
        require(set(panel) == set(itertools.product((0, 1), repeat=len(names))), "incomplete crossed instance/form")
        for axis, name in enumerate(names):
            for coordinate in sorted(panel):
                if coordinate[axis] == 0:
                    other = tuple(1 if index == axis else value for index, value in enumerate(coordinate))
                    result[FAMILY_NAMES[name]].append([panel[coordinate], panel[other]])
    return result


def _construct(root, action_labels, outcome_labels):
    actions = action_labels[root % 2:] + action_labels[:root % 2]
    offset = (root // 2) % 2
    outcomes = outcome_labels[offset:] + outcome_labels[:offset]
    prospect, revise = [], []
    for square, template in itertools.product(range(4), range(4)):
        rows = _prospect(root, "train", square, template, actions, outcomes)
        prospect.extend((rows[:2], rows[2:]))
    for instance, template in itertools.product(range(4), range(2)):
        rows = _revise(root, "train", instance, template, actions, outcomes)
        indexed = {tuple(row["factors"][name] for name in FACTOR_NAMES["REVISE"]): row for row in rows}
        for observed, prior in itertools.product((0, 1), repeat=2):
            pair = [indexed[(expected, observed, prior)] for expected in (0, 1)]
            revise.append(pair[::-1] if (instance + template + observed + prior) % 2 else pair)
    anchors = _anchors(root, "train")
    training = []
    for group, (prospect_pair, revise_pair) in enumerate(zip(prospect, revise, strict=True)):
        rows = [prospect_pair[0], revise_pair[0], prospect_pair[1], revise_pair[1],
                *anchors["ADDITION"][2 * group:2 * group + 2], *anchors["COPY"][2 * group:2 * group + 2]]
        for order, row in enumerate(rows):
            training.append(dict(row, group=f"birth-r{root}-batch-{group:03d}", order=order))
    dev = []
    for instance in range(8):
        dev.extend(_prospect(root, "dev", instance, 4 + instance % 2, actions, outcomes))
        dev.extend(_revise(root, "dev", instance, 2 + instance % 2, actions, outcomes))
    dev_anchors = _anchors(root, "dev")
    dev.extend(dev_anchors["ADDITION"] + dev_anchors["COPY"])
    sources = {}
    for row in training + dev:
        event = dict(id=row["source_event_ids"][0], semantic_id=row["semantic_id"], split=row["split"],
                     operation=row["operation"], origin=ORIGIN,
                     inputs={key: value for key, value in row["inputs"].items() if key != "action_order"},
                     rule={"PROSPECT": "select belief consequence relative to goal",
                           "REVISE": "compare EXPECTED with OBSERVED; keep PRIOR on match, switch otherwise",
                           "ADDITION": "integer addition", "COPY": "literal equality"}[row["operation"]])
        require(event["id"] not in sources or sources[event["id"]] == event, "source changes between renderings")
        sources[event["id"]] = event
    return dict(schema=SCHEMA, root=root, label_config=dict(actions=action_labels, outcomes=outcome_labels),
                spellings=dict(actions=actions, outcomes=outcomes), origin=ORIGIN, native_token_match="PENDING_NATIVE_AUDIT",
                train={arm: [dict(copy.deepcopy(row), response=response_text(row, arm)) for row in training] for arm in ARMS},
                dev=dev, source_records=list(sources.values()), twins=dict(train=_twins(training), dev=_twins(dev)),
                training_constraints=dict(initialization="FRESH_BASE_SINGLE_RANK8_ADAPTER_NO_WARMSTART",
                    rank=8, batch_size=8, grad_accum=1, pack=False, shuffle_groups=True, add_eos=True,
                    chat_template=False, max_len=MAX_LEN, learning_rate="CALLER_REQUIRED", epochs="CALLER_REQUIRED"),
                confirmation_cases=[], composition=dict(status="SEPARATE_FUTURE_LEVEL2_ASSAY", trained_chain_rows=0),
                supplies_l1_verdict=False, claim_limits="First authored BIRTH core only; not all cognition, own-wake, clean ancestry, Q0 or H1.")


def build_candidate(root=0, action_labels=("dax", "wug"), outcome_labels=("fep", "nup")):
    require(type(root) is int and root in (0, 1, 2), "root must be 0, 1 or 2")
    actions, outcomes = legacy._labels(action_labels), legacy._labels(outcome_labels)
    require(not set(actions) & set(outcomes), "action/outcome spellings must be disjoint")
    return _construct(root, actions, outcomes)


def training_recipe(*, learning_rate, seed, epochs):
    """Explicit caller choices; no rate, dose, or scientific success selection."""
    require(type(epochs) is int and epochs > 0, "positive caller-selected epochs required")
    recipe = legacy.training_recipe(learning_rate=learning_rate, seed=seed)
    recipe.update(epochs=epochs, batch_size=GROUP_SIZE)
    return recipe


def readout_cases(candidate, *, split="dev"):
    """Only context is model input; remaining fields are routing/source metadata."""
    audit_candidate(candidate)
    require(split in ("train", "dev"), "unknown readout split")
    cases = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
    return [dict(id=row["id"], context=row["context"], operation=row["operation"], family=row["operation"],
                 split=split, instance_id=row["instance_id"], template=row["template"],
                 source_event_ids=list(row["source_event_ids"]), origin=ORIGIN) for row in cases]


def _lookup(keys, targets):
    buckets = defaultdict(Counter)
    for key, target in zip(keys, targets, strict=True):
        buckets[key][target] += 1
    correct = sum(max(bucket.values()) for bucket in buckets.values())
    return dict(correct=correct, total=len(targets), ceiling=correct / len(targets), projection_values=len(buckets))


def audit_omitted_factors(cases, arm="AUTH"):
    """Best joint lookup using EVERY remaining task factor plus visible nuisances.

    Instance/form/action order ARE included. Source ID, unprinted corner ID,
    absolute index and batch slot are not input-visible factors. A separate
    batch-slot-only lookup is reported; it is not granted hidden corner data.
    Goal-only outcome prediction can be perfect; the ceiling concerns FULL JOINT.
    """
    require(arm in ARMS, "unknown arm")
    result = {}
    for operation in CONDITIONAL:
        indexed = [(index, row) for index, row in enumerate(cases) if row["operation"] == operation]
        require(indexed, "missing conditional operation")
        decisions = [tuple(legacy.expected_fields(row, arm).values()) for _, row in indexed]
        projections = {}
        for omitted in FACTOR_NAMES[operation]:
            keys = []
            for _, row in indexed:
                inputs = row["inputs"]
                values = tuple((name, json.dumps(inputs[name], sort_keys=True)) for name in FACTOR_NAMES[operation] if name != omitted)
                keys.append((row["instance_id"], row["template"], tuple(inputs["action_order"]), values))
            projections["without_" + omitted] = keys
        projections["constant"] = [0 for _ in indexed]
        projections["template_only"] = [row["template"] for _, row in indexed]
        projections["action_order_only"] = [tuple(row["inputs"]["action_order"]) for _, row in indexed]
        projections["batch_slot_only"] = [row.get("order", index % GROUP_SIZE) for index, row in indexed]
        report = {}
        for name, keys in projections.items():
            ceiling = _lookup(keys, decisions)
            require(2 * ceiling["correct"] <= ceiling["total"], f"omitted-factor/shortcut leakage: {operation}/{name} {ceiling}")
            report[name] = dict(ceiling, target="FULL_JOINT")
        result[operation] = report
    return result


def audit_candidate(candidate):
    expected = build_candidate(candidate["root"], candidate["label_config"]["actions"], candidate["label_config"]["outcomes"])
    require(candidate == expected, "candidate/source/target/group/split differs from authored specification")
    train, dev = candidate["train"]["AUTH"], candidate["dev"]
    require(len(train) == 256 and len(dev) == 128, "wrong complete-panel counts")
    for key in ("id", "semantic_id", "instance_id", "context"):
        require(not {row[key] for row in train} & {row[key] for row in dev}, "train/dev overlap")
    for operation in OPERATIONS:
        require(not {row["template"] for row in train if row["operation"] == operation} &
                    {row["template"] for row in dev if row["operation"] == operation}, "held templates overlap")
    for row in train + dev:
        require(all(source_id not in row["context"] for source_id in row["source_event_ids"]), "source ID printed")
    for offset in range(0, 256, GROUP_SIZE):
        auth, deranged = (candidate["train"][arm][offset:offset + GROUP_SIZE] for arm in ARMS)
        require(len({row["group"] for row in auth}) == 1 and [row["order"] for row in auth] == list(range(8)), "closed group broken")
        require([row["response"] for row in deranged] == [auth[index]["response"] for index in SWAP], "complete target swaps/anchors differ")
        require([row["context"] for row in auth] == [row["context"] for row in deranged], "arm inputs differ")
    action_orders = {}
    for split, rows in (("train", train), ("dev", dev)):
        action_orders[split] = {}
        for operation in CONDITIONAL:
            counts = Counter(",".join(row["inputs"]["action_order"]) for row in rows if row["operation"] == operation)
            require(len(counts) == 2 and len(set(counts.values())) == 1, "conditional action ordering unbalanced")
            action_orders[split][operation] = dict(counts)
    shortcuts = {split: {arm: audit_omitted_factors(rows, arm) for arm in ARMS} for split, rows in (("train", train), ("dev", dev))}
    return dict(status="PURE_AUDIT_PASS_NATIVE_PENDING", candidate_sha256=digest(candidate),
                train_counts=dict(Counter(row["operation"] for row in train)), dev_counts=dict(Counter(row["operation"] for row in dev)),
                groups_per_epoch=32, batch_size=8, source_records=len(candidate["source_records"]),
                twins={split: {name: len(pairs) for name, pairs in families.items()} for split, families in candidate["twins"].items()},
                shortcuts=shortcuts, action_order_counts=action_orders, supplies_l1_verdict=False)


def train_items(candidate, arm, render_context=None):
    require(arm in ARMS, "unknown arm")
    audit_candidate(candidate)
    render_context = render_context or (lambda text: text)
    return [dict(spans=[[render_context(row["context"]), False, "context"], [row["response"], True, "authored_birth_target"]],
                 group=row["group"], order=row["order"], view=row["operation"], category="authored_birth_target",
                 meta=dict(case_id=row["id"], source_event_ids=row["source_event_ids"], origin=ORIGIN, split="train"))
            for row in candidate["train"][arm]]


def audit_tokenizer(candidate, tokenizer, *, recipe=None, epochs=None, seeds=None, max_len=MAX_LEN):
    """Fixture/callback audit is never native certification or a recipe choice."""
    audit_candidate(candidate)
    if recipe is not None:
        require(recipe == training_recipe(learning_rate=recipe["lr"], seed=recipe["seed"], epochs=recipe["epochs"]),
                "recipe differs from isolated eight-row birth contract")
        require(epochs is None or epochs == recipe["epochs"], "conflicting audit epochs/recipe")
        require(seeds is None or tuple(seeds) == (recipe["seed"],), "conflicting audit seeds/recipe")
        epochs, seeds = recipe["epochs"], (recipe["seed"],)
    seeds = (0,) if seeds is None else seeds
    require(type(epochs) is int and epochs > 0 and seeds and len(set(seeds)) == len(seeds) and
            all(type(seed) is int and seed >= 0 for seed in seeds), "explicit positive audit epochs and distinct seeds required")
    require(max_len == MAX_LEN, "max_len512 contract")
    eos, pad = tokenizer.eos_token_id, tokenizer.pad_token_id
    require(type(eos) is int and type(pad) is int and eos != pad, "distinct native EOS/PAD required")
    for labels in candidate["spellings"].values():
        for prefix in ("", " "):
            lengths = [len(tokenizer.encode(prefix + value, add_special_tokens=False)) for value in labels]
            require(lengths[0] == lengths[1] and lengths[0] > 0, "native physical label lengths differ")
    render = lambda text: tokenizer.apply_chat_template([dict(role="user", content=text)], tokenize=False, add_generation_prompt=True)
    corpora = {arm: train_items(candidate, arm, render) for arm in ARMS}
    segments, records = {}, {}
    for arm in ARMS:
        segments[arm], records[arm] = [], []
        for index, item in enumerate(trainer.normalize_items(corpora[arm])):
            prefix = tokenizer.encode(item["spans"][0][0], add_special_tokens=False)
            target = tokenizer.encode(item["spans"][1][0], add_special_tokens=False)
            require(prefix and target and eos not in target and pad not in target, "target special token or empty sequence")
            ids = prefix + target + [eos]
            require(len(ids) <= max_len, "native overflow: no truncation permitted")
            encoded = trainer.encode_item_segments(item, tokenizer, max_len, False, True, index, overflow="truncate")
            require(len(encoded) == 1, "native row missing/split")
            segment = encoded[0]
            require(segment.ids == ids and segment.labels == [-100] * len(prefix) + target + [eos] and
                    segment.n_target == len(target) + 1 and segment.context_dropped == segment.target_dropped == 0,
                    "native labels/EOS/boundary mismatch")
            segments[arm].append(segment)
            records[arm].append(dict(case_id=item["meta"]["case_id"], prefix_ids=prefix, input_ids=ids,
                                     labels=segment.labels, context_tokens=len(prefix), input_tokens=len(ids),
                                     target_tokens=segment.n_target, supervised_eos_position=len(ids) - 1,
                                     operation=item["view"], group=item["group"], order=item["order"]))
    for left, right in zip(records["AUTH"], records["DERANGED"], strict=True):
        require(left["case_id"] == right["case_id"] and left["prefix_ids"] == right["prefix_ids"], "native paired prefixes differ")
    for offset in range(0, 256, GROUP_SIZE):
        for index, swapped in enumerate(SWAP):
            auth, deranged = records["AUTH"][offset + swapped], records["DERANGED"][offset + index]
            require(len(auth["prefix_ids"]) == len(deranged["prefix_ids"]), "native swap context lengths differ")
            require([value for value in auth["labels"] if value != -100] == [value for value in deranged["labels"] if value != -100],
                    "whole supervised sequence including EOS did not swap")
    schedules, group_costs = {}, {}
    for seed in seeds:
        batches, costs = [], []
        for epoch in range(epochs):
            orders = {arm: trainer.epoch_order(trainer.pack_by_group(segments[arm], max_len, False), seed, epoch, True) for arm in ARMS}
            for offset in range(0, 256, GROUP_SIZE):
                summaries, indices = {}, {}
                for arm in ARMS:
                    packs = orders[arm][offset:offset + GROUP_SIZE]
                    require(len(packs) == 8 and all(len(pack) == 1 for pack in packs) and
                            len({pack[0].group for pack in packs}) == 1 and [pack[0].order for pack in packs] == list(range(8)),
                            "actual optimizer group/swap pairing broken")
                    batch = trainer.collate(packs, pad)
                    width = max(len(pack[0].ids) for pack in packs)
                    for index, (segment,) in enumerate(packs):
                        padding = width - len(segment.ids)
                        require(batch["input_ids"][index] == segment.ids + [pad] * padding and
                                batch["labels"][index] == segment.labels + [-100] * padding and
                                batch["position_ids"][index][:len(segment.ids)] == list(range(len(segment.ids))), "padding loss/positions differ")
                    indices[arm] = [pack[0].item_index for pack in packs]
                    summaries[arm] = dict(joint_lengths=sorted((len(pack[0].ids) - pack[0].n_target, pack[0].n_target,
                                                              len(pack[0].ids), len(pack[0].ids) - 1) for pack in packs),
                        target_sequences=Counter(tuple(value for value in pack[0].labels if value != -100) for pack in packs),
                        input_tokens=Counter(value for pack in packs for value in pack[0].ids),
                        target_tokens=Counter(value for pack in packs for value in pack[0].labels if value != -100))
                require(indices["AUTH"] == indices["DERANGED"] and summaries["AUTH"] == summaries["DERANGED"], "per-batch native parity failed")
                batches.append(indices["AUTH"])
                actual = [segments["AUTH"][index] for index in indices["AUTH"]]
                input_tokens = sum(len(segment.ids) for segment in actual)
                target_tokens = sum(segment.n_target for segment in actual)
                padded_tokens = GROUP_SIZE * max(len(segment.ids) for segment in actual)
                costs.append(dict(epoch=epoch, update_index=len(costs), group=actual[0].group,
                                  row_indices=indices["AUTH"], context_tokens=input_tokens - target_tokens,
                                  input_tokens=input_tokens, target_tokens=target_tokens, eos_tokens=8,
                                  padded_input_tokens=padded_tokens, padding_tokens=padded_tokens - input_tokens))
        schedules[str(seed)] = batches
        group_costs[str(seed)] = costs
    return dict(status="CALLBACK_AUDIT_PASS_NOT_NATIVE_CERTIFICATION", candidate_sha256=digest(candidate),
                corpora=corpora, rows=records, optimizer_update_rows=schedules, group_costs=group_costs,
                audited_epochs=epochs, recipe=recipe,
                updates_per_epoch=32, updates_per_audited_seed=32 * epochs, batch_size=8,
                config_counts=dict(rows_per_arm=256, groups_per_epoch=32, epochs=epochs,
                                   optimizer_updates=32 * epochs, batch_size=8, grad_accum=1, pack=False,
                                   skipped_rows=0, truncated_rows=0, split_rows=0),
                input_tokens_per_epoch={arm: sum(row["input_tokens"] for row in records[arm]) for arm in ARMS},
                target_tokens_per_epoch={arm: sum(row["target_tokens"] for row in records[arm]) for arm in ARMS},
                source_sha256={Path(module.__file__).name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                               for module in (legacy, trainer)} | {Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                birth_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                no_truncation=True, loss_bearing_padding=False, model_origin_authenticated=False, supplies_l1_verdict=False)


def audit_native(candidate, model_path, expected_file_hashes, *, recipe=None, epochs=None, seeds=None):
    """Offline local tokenizer only; expected hashes supplied by Main, no weights loaded."""
    directory = Path(model_path).expanduser().resolve(strict=True)
    required = {"config.json", "tokenizer.json", "tokenizer_config.json"}
    required |= {name for name in ("vocab.json", "merges.txt", "special_tokens_map.json", "added_tokens.json",
                                   "chat_template.jinja", "chat_template.json") if (directory / name).exists()}
    require(not (directory / "chat_templates").exists(), "external chat templates require separate binding")
    require(isinstance(expected_file_hashes, dict) and required <= set(expected_file_hashes), "missing local tokenizer pins")
    for name, expected in expected_file_hashes.items():
        require(Path(name).name == name and hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected, "tokenizer pin mismatch")
    require(json.loads((directory / "config.json").read_text())["model_type"] == "qwen2", "Qwen2 base configuration required")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
    report = audit_tokenizer(candidate, tokenizer, recipe=recipe, epochs=epochs, seeds=seeds)
    for name, expected in expected_file_hashes.items():
        require(hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected, "tokenizer changed during audit")
    report.update(status="NATIVE_TOKEN_MATCH_VERIFIED", tokenizer_path=str(directory), tokenizer_file_hashes=expected_file_hashes)
    return report


def score_response(case, raw, *, assigned_arm="AUTH"):
    require(assigned_arm in ARMS and isinstance(raw, str), "assigned map and raw string required")
    operation = case["operation"]
    if operation in CONDITIONAL:
        scored = legacy.score_response(case, raw, assigned_arm=assigned_arm)
    else:
        require(operation in ("ADDITION", "COPY"), "unknown operation")
        if operation == "ADDITION":
            match = re.fullmatch(r"ACT: ([+-]?[0-9]+)\n?", raw)
            correct = bool(match and int(match[1]) == case["inputs"]["left"] + case["inputs"]["right"])
        else:
            match = re.fullmatch(r"COPY: ([a-z0-9-]+)\n?", raw)
            correct = bool(match and match[1] == case["inputs"]["literal"])
        scored = dict(case_id=case["id"], raw_text=raw, fields={} if not match else {operation: match[1]},
                      strict_surface=match is not None, auth_fields={operation: correct}, own_map_fields={operation: correct},
                      auth_joint_semantic=correct, own_map_joint_semantic=correct,
                      auth_strict_joint=bool(match and correct), own_map_strict_joint=bool(match and correct))
    allowed = {"PROSPECT": {"PREDICT", "ACT"}, "REVISE": {"COMPARE", "POLICY", "NEXT"},
               "ADDITION": {"ACT"}, "COPY": {"COPY"}}[operation]
    forbidden = {"PREDICT", "ACT", "COMPARE", "POLICY", "NEXT", "COPY"} - allowed
    spill = bool(re.search(r"\b(?:" + "|".join(sorted(forbidden)) + r")\s*:", raw))
    return dict(scored, operation=operation, tag_spill=spill,
                exact_auth=raw == response_text(case, "AUTH"), exact_own_map=raw == response_text(case, assigned_arm),
                instruction_compliant=(raw in (response_text(case, assigned_arm), response_text(case, assigned_arm) + "\n")
                                       and not spill) if operation not in CONDITIONAL else scored["own_map_strict_joint"] and not spill)


def _metrics(rows):
    keys = ("strict_surface", "auth_joint_semantic", "own_map_joint_semantic", "auth_strict_joint", "own_map_strict_joint",
            "exact_auth", "exact_own_map", "instruction_compliant", "tag_spill")
    return dict(total=len(rows), **{key: sum(row[key] for row in rows) for key in keys},
                auth_fields={key: sum(row["auth_fields"][key] for row in rows) for key in rows[0]["auth_fields"]},
                own_map_fields={key: sum(row["own_map_fields"][key] for row in rows) for key in rows[0]["own_map_fields"]})


def score_outputs(candidate, outputs, *, split="dev", assigned_arm="AUTH"):
    audit_candidate(candidate)
    require(split in ("train", "dev") and assigned_arm in ARMS, "unknown split/map")
    cases = candidate["train"][assigned_arm] if split == "train" else candidate["dev"]
    require(isinstance(outputs, dict) and set(outputs) == {row["id"] for row in cases}, "complete fixed-panel output IDs required")
    rows = {case["id"]: score_response(case, outputs[case["id"]], assigned_arm=assigned_arm) for case in cases}
    operations, strata = {}, {}
    for operation in OPERATIONS:
        subset = [case for case in cases if case["operation"] == operation]
        operations[operation] = _metrics([rows[case["id"]] for case in subset])
        groups = defaultdict(list)
        for case in subset:
            values = dict(template=str(case["template"]))
            if operation in CONDITIONAL:
                fields = legacy.expected_fields(case, "AUTH")
                action = fields["ACT"] if operation == "PROSPECT" else fields["NEXT"]
                values.update(action=action, action_order=",".join(case["inputs"]["action_order"]),
                              target_position=str(case["inputs"]["action_order"].index(action)))
                values.update({name: json.dumps(case["inputs"][name], sort_keys=True) for name in FACTOR_NAMES[operation]})
                if operation == "REVISE":
                    values["branch"] = fields["COMPARE"]
            for key, value in values.items():
                groups[f"{key}/{value}"].append(rows[case["id"]])
        strata[operation] = {name: _metrics(group) for name, group in groups.items()}
    flips = dict(goal=("PREDICT_ACTION", "PREDICT_OUTCOME", "ACT"), belief=("PREDICT_ACTION", "ACT"),
                 expected=("COMPARE", "POLICY", "NEXT"), observed=("COMPARE", "POLICY", "NEXT"), prior_action=("NEXT",))
    twins = {}
    for family, pairs in candidate["twins"][split].items():
        details = []
        for first_id, second_id in pairs:
            first, second = rows[first_id], rows[second_id]
            changed = all(field in first["fields"] and field in second["fields"] and
                          first["fields"][field] != second["fields"][field] for field in flips[family])
            details.append(dict(case_ids=[first_id, second_id], full_required_flip=changed,
                auth_semantic_pass=changed and first["auth_joint_semantic"] and second["auth_joint_semantic"],
                own_map_semantic_pass=changed and first["own_map_joint_semantic"] and second["own_map_joint_semantic"],
                auth_strict_pass=changed and first["auth_strict_joint"] and second["auth_strict_joint"],
                own_map_strict_pass=changed and first["own_map_strict_joint"] and second["own_map_strict_joint"]))
        twins[family] = dict(total=len(pairs), rows=details, **{name: sum(row[name] for row in details) for name in
            ("auth_semantic_pass", "own_map_semantic_pass", "auth_strict_pass", "own_map_strict_pass")})
    return dict(candidate_sha256=digest(candidate), split=split, assigned_arm=assigned_arm, rows=list(rows.values()),
                operations=operations, per_stratum=strata, twins=twins, supplies_l1_verdict=False,
                origin=ORIGIN, stratum_reference="AUTH-grounded branches/actions; public input factors", claim_limits=candidate["claim_limits"])
