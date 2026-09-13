"""Pure PCFL v2.2 preparation bridge, not a launch or scientific gate.

Main supplies pre-output registries; no tokenizer, solver, world generator, or
runtime is invoked here. Core-owned semantic registries are pinned, not claimed
to have been independently certified. See validation_report.missing_interfaces.
"""

import hashlib
import itertools
import json
import math
import re
from collections import Counter


SCHEMA = "pcfl.execution_contract.v2.2"
CANONICALIZATION = "utf8-json-sort-keys-compact-no-nan-v1"
SOURCE_PINS = {
    "2026-09-13_pcfl_vertical_dev_v2_synthesis.md": "222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456",
    "2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md": "683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca",
    "2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md": "5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd",
    "2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md": "f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679",
    "2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md": "599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b",
    "2026-09-13_pcfl_v22_execution_readiness_audit.md": "deb3b51abde362a0d35f41295b565c9b5ef02d7d77757644ae5834294e539c13",
}
CLOSURE_PIN = {"2026-09-13_pcfl_v22_minimum_execution_closure_contract.md": "f9b9891761c47e6d8047e7a9161a827d00fae464df91940c523b40f85af535d0"}
PRODUCTION_BINDINGS = {
    "distractor": {
        "status": "UNRESOLVED",
        "source_note_sha256": "bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf",
        "missing": ["frontier_topology", "D0_D1_public_result_bytes", "receipt_schema", "terminal_public_response"],
    },
    "probe_result_bytes": "UNRESOLVED",
}
WRAPPERS = [
    "Retrieve the exact stored memory for this request.\n{REQUEST}\nReply with only the stored memory block.",
    "Personal memory query:\n{REQUEST}\nReturn only the exact stored block.",
    "{REQUEST}\nRead personal memory and output only its exact stored block.",
    "Use personal memory for the request below. Output the stored block only.\n{REQUEST}",
    "Lookup request: {REQUEST}\nRespond only with the exact memory block.",
    "Return the exact personal-memory block matching:\n{REQUEST}\nNo explanation.",
    "Read this local memory address and emit only the stored block.\nAddress request: {REQUEST}",
    "For this personal memory lookup, give only the exact stored block.\n{REQUEST}",
    "Provide the exact stored personal-memory block at this address.\n{REQUEST}\nOutput only the block.",
]
PARSER_POLICY = {
    "strict": "registered_block_byte_identity",
    "semantic": "exact_ordered_rows_or_single_bare_or_text_fence",
    "optional_final_lf": True,
    "extra_prose_or_rows": False,
    "refusals": ["MISS", "MISS\n"],
    "usable_false_row": "any_parsable_wrong_or_absent_row_even_with_prose_or_refusal",
}
RECIPE = {
    "slots": 20, "views": 8, "examples_per_epoch": 160,
    "batch_size": 4, "epochs": 5, "updates": 200, "accumulation": 1,
    "rank": 8, "alpha": 16, "dropout": 0.05, "dtype": "bf16",
    "base": "Qwen2.5-7B-Instruct", "base_frozen": True,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "optimizer": {"name": "AdamW", "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.01},
    "gradient_clip": 1.0, "max_sequence": 512,
    "initialization": "clean_C0", "fresh_optimizer": True,
    "checkpoint": "final_200", "loss": "response_only_including_eos",
    "formation": "exact_presealed_chronological_banks_no_remap_or_ideal_substitution",
    "padding": {"position": "post_eos", "attention_mask": 0, "label": -100},
    "learning_rates": {"CAL_LOW": 3e-5, "CAL_HIGH": 3e-4},
    "prohibited": ["loss_active_padding", "token_equalization", "trained_MISS", "warm_start",
                   "checkpoint_choice", "retry", "replacement_root", "output_derived_decision",
                   "arm_local_shuffle", "target_truncation", "packing"],
}
ARMS = {
    "S1_AUTH": (17, 3, 0), "S1_ATOMS": (14, 6, 0),
    "S1_EVENT_TWIN": (17, 3, 0), "S1_LINK_PERMUTE": (17, 3, 0),
    "S2_FULL_R0": (19, 1, 0), "S2_FULL_R1": (19, 1, 0),
    "S2_OLD_REPLAY": (17, 2, 1),
}
PROJECTIONS = {
    "EXACT_WITNESSED_GRAPH", "FULL_CHILD_TEXT", "EVENT_ATOMS_TEXT", "ACTIVE_LINKED_TEXT",
    "NATIVE_CONTEXT", "RAW_EPISODIC", "OLD_ONLY_TEXT", "NEW_ONLY_TEXT", "NONE_OFF", "WRONG_ROOT",
}
BINDING_FIELDS = {
    "source_pins", "implementation_pins", "environment", "root_registry", "slot_registry",
    "counterpart_registry", "replay_registry", "batch_registry", "core_registry",
    "diagnostic_registry", "intervention_registry", "locality_registry",
    "work_registry", "profile_registry",
}
ROOT_FIELDS = ("id", "role", "seed", "old_bit", "canonical_r", "primary_reachout", "wire", "topology", "cube")
SLOT_FIELDS = ("id", "source", "row_type", "phase", "support", "bank", "taint", "request")
INTEGRITY = ("custody", "masks", "schedule", "finite_200_updates", "zero_truncation", "complete_readout", "checkpoint")
SAFETY = ("locality_refusal", "zero_false_rows", "generic_canary", "pcfl_retention")
ACQUISITION = ("event_semantic", "event_strict", "link_semantic", "link_strict")
CORE_TOTALS = {"single_actor": 1106, "service_task": 576, "direct_read": 324, "formation": 76, "canary": 280}


class ExecutionContractError(ValueError):
    """An execution binding is malformed, ambiguous, or inconsistent."""


def _require(condition, message):
    if not condition:
        raise ExecutionContractError(message)


def _record(value, fields, name):
    _require(type(value) is dict and set(value) == set(fields), f"{name}: missing/unknown fields")


def _integer(value, name, minimum=0):
    _require(type(value) is int and value >= minimum, f"{name}: expected integer >= {minimum}")


def _identifier(value):
    _require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_./:-]+", value) is not None, "invalid structural identifier")


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "expected SHA-256")


def _unique(values, name):
    _require(type(values) is list and len(values) == len(set(values)), f"{name}: duplicate/non-list")


def canonical(value):
    """Canonical JSON bytes; accept only JSON wire types, never implicit coercion."""
    def check(item):
        if type(item) is dict:
            _require(all(type(key) is str for key in item), "JSON keys must be strings")
            for nested in item.values():
                check(nested)
        elif type(item) is list:
            for nested in item:
                check(nested)
        else:
            _require(item is None or type(item) in (str, int, float, bool), "non-JSON wire type")
            _require(type(item) is not float or math.isfinite(item), "nonfinite JSON number")
    check(value)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (UnicodeError, ValueError) as error:
        raise ExecutionContractError("invalid JSON encoding") from error


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_contract(payload, expected_sha256):
    """Read exact canonical bytes and sidecar hash without any filesystem I/O."""
    _hash(expected_sha256)
    _require(type(payload) is bytes, "contract payload must be bytes")
    _require(hashlib.sha256(payload).hexdigest() == expected_sha256, "sidecar mismatch")
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    try:
        result = json.loads(payload, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as error:
        raise ExecutionContractError("invalid contract JSON") from error
    _require(canonical(result) == payload, "noncanonical payload")
    validate_execution_contract(result)
    return result


def calibration_transition(state, gates):
    """Diagnostics are deliberately not inputs to the conservative CAL table."""
    _require(state in ("CAL_LOW", "CAL_HIGH"), "unknown CAL state")
    _record(gates, INTEGRITY + SAFETY + ACQUISITION, "CAL gates")
    _require(all(type(value) is bool for value in gates.values()), "CAL gates must be Boolean")
    if not all(gates[key] for key in INTEGRITY):
        return "VS_ASSAY_INVALID"
    if not all(gates[key] for key in SAFETY):
        return "VS_WRITER_QUALIFICATION_FAIL"
    if all(gates[key] for key in ACQUISITION):
        return "SELECT_LOW" if state == "CAL_LOW" else "SELECT_HIGH"
    return "RUN_CAL_HIGH" if state == "CAL_LOW" else "VS_WRITER_QUALIFICATION_FAIL"


def _calibration_table():
    return [
        {"valid": valid, "safe": safe, "acquired": acquired,
         "low": "VS_ASSAY_INVALID" if not valid else "VS_WRITER_QUALIFICATION_FAIL" if not safe else "SELECT_LOW" if acquired else "RUN_CAL_HIGH",
         "high": "VS_ASSAY_INVALID" if not valid else "SELECT_HIGH" if safe and acquired else "VS_WRITER_QUALIFICATION_FAIL"}
        for valid, safe, acquired in itertools.product((False, True), repeat=3)
    ]


def root_skeleton_digest(bindings):
    """Hash pre-output structure before selecting replay; not a validity verdict.

    Replay placeholders have non-null source; their source/request/support/bank
    values are excluded. First-block banks and all structural IDs are frozen.
    The full builder subsequently requires resolved, valid replay assignments.
    """
    for root in bindings["root_registry"]:
        _record(root, ROOT_FIELDS, "root")
    skeleton_slots = []
    for corpus in bindings["slot_registry"]:
        _record(corpus, ("id", "root", "arm", "slots"), "corpus")
        for slot in corpus["slots"]:
            _record(slot, SLOT_FIELDS, "slot")
            first = slot["source"] is None
            skeleton_slots.append({"corpus": corpus["id"], "root": corpus["root"], "arm": corpus["arm"], "id": slot["id"], "row_type": slot["row_type"], "phase": slot["phase"], "taint": slot["taint"],
                                   "first": first, "support": slot["support"] if first else [],
                                   "bank": slot["bank"] if first else {}, "request": slot["request"] if first else None})
    return digest({"schema": SCHEMA, "source_pins_digest": digest(bindings["source_pins"]), "roots": bindings["root_registry"],
                   "root_schema": bindings["core_registry"]["root_schema"], "world_registry": bindings["core_registry"]["world_registry"],
                   "slots": skeleton_slots, "counterparts": bindings["counterpart_registry"],
                   "cuts": bindings["intervention_registry"], "addresses": bindings["locality_registry"]})


def _structural(bindings):
    roots = bindings["root_registry"]
    _require(type(roots) is list and len(roots) == 7, "need four excluded, one disposable, two DEV roots")
    root_ids, inventories = set(), set()
    for root in roots:
        _record(root, ROOT_FIELDS, "root")
        _identifier(root["id"])
        _require(root["id"] not in root_ids, "duplicate root")
        root_ids.add(root["id"])
        _integer(root["seed"], "root seed")
        expected_seed = int.from_bytes(hashlib.sha256(b"PCFL-V2.1-PREP\0" + ("root/" + root["id"]).encode("ascii")).digest()[:8], "big") & ((1 << 63) - 1)
        _require(root["seed"] == expected_seed, "root seed domain")
        for key in ("old_bit", "canonical_r"):
            _require(type(root[key]) is int and root[key] in (0, 1), "root bit must be 0/1 integer")
        _require(root["primary_reachout"] in ("RA", "RB"), "reachout render")
        _require(root["cube"] == [list(bits) for bits in itertools.product((0, 1), repeat=3)], "complete ordered O/R/D cube required")
        _require(all(type(bit) is int for cell in root["cube"] for bit in cell), "Boolean cube bit")
        wire = root["wire"]
        _record(wire, ("schema", "kind", "label", "inventory"), "core root wire")
        _require(wire["schema"] == "pcfl_vertical_cpu_v1" and wire["kind"] == "root" and wire["label"] == root["id"], "root wire binding")
        namespaces = bindings["core_registry"]["root_schema"]["slots"]
        _record(wire["inventory"], namespaces, "core inventory namespaces")
        inventory = []
        for namespace, structural_ids in namespaces.items():
            _record(wire["inventory"][namespace], structural_ids, "core inventory slots")
            inventory.extend(wire["inventory"][namespace].values())
        _unique(inventory, "opaque inventory")
        _require(bool(inventory) and not inventories.intersection(inventory), "root-disjoint inventory required")
        inventories.update(inventory)
        for opaque in inventory:
            _identifier(opaque)
        _require(type(root["topology"]) is list and bool(root["topology"]), "missing structural topology")
        for edge in root["topology"]:
            _require(type(edge) is list and len(edge) == 3, "topology must contain source/port/destination triples")
            _require(all(value in inventory for value in edge), "topology outside root inventory")
    _require(Counter(root["role"] for root in roots) == {"excluded": 4, "disposable": 1, "dev": 2}, "root roles")
    dev_roots = [root for root in roots if root["role"] == "dev"]
    _require([(root["old_bit"], root["canonical_r"], root["primary_reachout"]) for root in dev_roots] == [(0, 0, "RA"), (1, 1, "RB")], "DEV O/R/primary bindings")
    corpora = {}
    for corpus in bindings["slot_registry"]:
        _record(corpus, ("id", "root", "arm", "slots"), "corpus")
        _identifier(corpus["id"])
        _require(corpus["id"] not in corpora and corpus["root"] in root_ids and corpus["arm"] in ARMS, "corpus identity")
        _require(type(corpus["slots"]) is list and len(corpus["slots"]) == 20, "twenty slots required")
        slots = {}
        for slot in corpus["slots"]:
            _record(slot, SLOT_FIELDS, "slot")
            _identifier(slot["id"])
            _require(slot["id"] not in slots, "duplicate slot")
            _require(slot["row_type"] in ("EVENT", "LINK") and slot["phase"] in ("OLD", "NEW"), "slot type/phase")
            _require(slot["taint"] in ("AUTHENTIC", "CONTROL"), "slot taint")
            _unique(slot["support"], "support")
            _require(bool(slot["support"]), "empty support")
            for support in slot["support"]:
                _identifier(support)
            _record(slot["bank"], slot["support"], "presealed chronological bank")
            field_names = ("event", "source", "port", "destination", "receipt") if slot["row_type"] == "EVENT" else ("link", "first", "second", "via", "receipt_first", "receipt_second")
            for support, fields in slot["bank"].items():
                _record(fields, field_names, "bank row fields")
                _require(fields["event" if slot["row_type"] == "EVENT" else "link"] == support, "bank chronological handle")
                for value in fields.values():
                    _identifier(value)
            _require(type(slot["request"]) is str and re.fullmatch(r"READ (?:EVENT|EVENTS_AT|LINKS_FROM) [A-Za-z0-9_./:-]+", slot["request"]), "request grammar; PAD/MISS forbidden")
            slots[slot["id"]] = slot
        first = [slot for slot in slots.values() if slot["source"] is None]
        replays = [slot for slot in slots.values() if slot["source"] is not None]
        expected_first, events, links = ARMS[corpus["arm"]]
        _require(len(first) == expected_first and Counter(slot["row_type"] for slot in replays) == +Counter(EVENT=events, LINK=links), "v2.2 roster")
        for slot in replays:
            _identifier(slot["source"])
            _require(slot["source"] in slots and slots[slot["source"]]["source"] is None, "replay must name a first block")
            source = slots[slot["source"]]
            _require(all(slot[key] == source[key] for key in ("row_type", "phase", "support", "bank", "taint", "request")), "replay changes source")
            _require(slot["phase"] == "OLD", "replay must be OLD")
        expected_links = 0 if corpus["arm"] == "S1_ATOMS" else 3 if corpus["arm"].startswith("S1") else 4
        _require(sum(slot["row_type"] == "LINK" for slot in slots.values()) == expected_links, "LINK-bearing slot count")
        new_count = sum(slot["phase"] == "NEW" for slot in slots.values())
        _require(1 <= new_count <= 5 if corpus["arm"].startswith("S2_FULL") else new_count == 0, "NEW-bearing slot quota")
        _require(len({slot["request"] for slot in first}) == len(first), "duplicate first request")
        for slot in slots.values():
            control = corpus["arm"] == "S1_EVENT_TWIN" or (corpus["arm"] == "S1_LINK_PERMUTE" and slot["row_type"] == "LINK")
            _require(slot["taint"] == ("CONTROL" if control else "AUTHENTIC"), "lineage taint")
        corpora[corpus["id"]] = corpus
    expected = Counter((root["id"], arm) for root in roots if root["role"] == "dev" for arm in ARMS)
    expected.update((root["id"], "S1_AUTH") for root in roots if root["role"] == "disposable")
    _require(Counter((corpus["root"], corpus["arm"]) for corpus in corpora.values()) == expected, "need fourteen DEV corpora and one shared CAL corpus")
    return corpora, root_skeleton_digest(bindings)


def _select_replay(slots, eligible, prior, quota, domain):
    _require(eligible == sorted(eligible) and bool(eligible), "eligible slots must be sorted structural IDs")
    _unique(eligible, "eligible")
    _unique(prior, "prior replay sources")
    _require(set(prior) <= set(eligible), "prior sources outside eligible")
    rotation = int(digest(domain), 16) % len(eligible)
    rotated = eligible[rotation:] + eligible[:rotation]
    candidates = [source for source in rotated if source not in prior]
    _require(0 < quota <= len(candidates), "replay distinct-source quota")
    supports = sorted({support for source in eligible for support in slots[source]["support"]})
    base = Counter(support for slot in slots.values() if slot["source"] is None for support in slot["support"])
    base.update(support for source in prior for support in slots[source]["support"])
    def objective(selected):
        counts = base.copy()
        counts.update(support for source in selected for support in slots[source]["support"])
        values = [counts[support] for support in supports]
        return (max(values) - min(values), len(values) * sum(value * value for value in values) - sum(values) ** 2,
                tuple(rotated.index(source) for source in selected))
    selected = min(itertools.combinations(candidates, quota), key=objective)
    counts = base.copy()
    counts.update(support for source in selected for support in slots[source]["support"])
    return list(selected), {support: counts[support] for support in supports}


def _eligible_replay(bindings, corpora, corpus, row_type, suffix):
    eligible = lambda member: {slot["id"] for slot in member["slots"] if slot["source"] is None and slot["phase"] == "OLD" and slot["row_type"] == row_type}
    local = eligible(corpus)
    if suffix != "replay":
        return sorted(local)
    family = [member for member in corpora.values() if member["root"] == corpus["root"] and member["arm"][:2] == corpus["arm"][:2]]
    if len(family) == 1:
        return sorted(local)
    anchor = next(member for member in family if member["arm"] == ("S1_AUTH" if corpus["arm"].startswith("S1") else "S2_FULL_R0"))
    common = eligible(anchor)
    maps = {}
    for member in family:
        if member["id"] == anchor["id"]:
            continue
        mapping = next((entry for entry in bindings["counterpart_registry"] if entry["left"] == anchor["id"] and entry["right"] == member["id"]), None)
        _require(mapping is not None, "missing replay family counterpart")
        maps[member["id"]] = dict(mapping["pairs"])
        common &= {source for source, target in maps[member["id"]].items() if target in eligible(member)}
    return sorted(common if corpus["id"] == anchor["id"] else [maps[corpus["id"]][source] for source in common])


def _replays_and_batches(bindings, corpora, skeleton_hash):
    covered, selections = set(), {}
    for replay in bindings["replay_registry"]:
        _record(replay, ("corpus", "row_type", "suffix", "eligible", "prior", "selected", "slots", "domain_hash", "support_counts"), "replay selection")
        _require(replay["corpus"] in corpora, "unknown replay corpus")
        corpus = corpora[replay["corpus"]]
        slots = {slot["id"]: slot for slot in corpus["slots"]}
        stage = corpus["arm"][:2]
        _require(replay["row_type"] in ("EVENT", "LINK"), "replay row type")
        _require(replay["suffix"] in ("replay", "atoms_extra", "old_event_extra", "old_link_extra"), "unbound replay suffix")
        selection_key = (corpus["id"], replay["suffix"])
        _require(selection_key not in selections, "duplicate replay quota")
        selections[selection_key] = replay
        eligible = _eligible_replay(bindings, corpora, corpus, replay["row_type"], replay["suffix"])
        _require(replay["eligible"] == eligible, "incomplete eligible replay universe")
        domain = [skeleton_hash, stage, "S1_four_arm" if stage == "S1" else "S2_three_arm", replay["row_type"], replay["suffix"]]
        _require(replay["domain_hash"] == digest(domain), "replay domain drift")
        selected, counts = _select_replay(slots, eligible, replay["prior"], len(replay["slots"]), domain)
        _require(replay["selected"] == selected and replay["support_counts"] == counts, "replay rotation/balance selection")
        for replay_id, source_id in zip(replay["slots"], selected):
            _require(replay_id in slots and slots[replay_id]["source"] == source_id, "replay source mismatch")
            key = (corpus["id"], replay_id)
            _require(key not in covered, "duplicate replay selection")
            covered.add(key)
    _require(covered == {(corpus["id"], slot["id"]) for corpus in corpora.values() for slot in corpus["slots"] if slot["source"] is not None}, "missing replay selections")
    for corpus in corpora.values():
        arm, corpus_id = corpus["arm"], corpus["id"]
        expected = {"replay": ("EVENT", 3 if arm.startswith("S1") else 1)}
        if arm == "S1_ATOMS":
            expected["atoms_extra"] = ("EVENT", 3)
        if arm == "S2_OLD_REPLAY":
            expected.update(old_event_extra=("EVENT", 1), old_link_extra=("LINK", 1))
        _require({suffix for owner, suffix in selections if owner == corpus_id} == set(expected), "replay quota suffixes")
        for suffix, (row_type, quota) in expected.items():
            selection = selections[(corpus_id, suffix)]
            prior = selections[(corpus_id, "replay")]["selected"] if suffix in ("atoms_extra", "old_event_extra") else []
            _require(selection["row_type"] == row_type and len(selection["slots"]) == quota and selection["prior"] == prior, "replay quota/prior appearances")
    positions = {}
    for schedule in bindings["batch_registry"]:
        _record(schedule, ("corpus", "epochs"), "batch schedule")
        corpus_id = schedule["corpus"]
        _require(corpus_id in corpora and corpus_id not in positions, "unknown/duplicate schedule")
        corpus = corpora[corpus_id]
        slots = {slot["id"]: slot for slot in corpus["slots"]}
        _require(type(schedule["epochs"]) is list and len(schedule["epochs"]) == 5, "five epochs required")
        positions[corpus_id] = []
        for epoch in schedule["epochs"]:
            _require(type(epoch) is list and len(epoch) == 40, "forty batches per epoch")
            observed, placed = [], {}
            for batch_index, batch in enumerate(epoch):
                _require(type(batch) is list and len(batch) == 4, "batch size four")
                support_seen, slot_seen = set(), set()
                link_count = new_count = 0
                for item_index, item in enumerate(batch):
                    _require(type(item) is list and len(item) == 2, "batch item [slot_id, view_id]")
                    slot_id, view = item
                    _require(slot_id in slots and type(view) is int and 0 <= view < 8, "unknown slot or trained W8")
                    slot = slots[slot_id]
                    _require(slot_id not in slot_seen and not support_seen.intersection(slot["support"]), "batch support collision (including grouped reads/replay)")
                    slot_seen.add(slot_id)
                    support_seen.update(slot["support"])
                    link_count += slot["row_type"] == "LINK"
                    new_count += slot["phase"] == "NEW"
                    observed.append((slot_id, view))
                    placed[(slot_id, view)] = (batch_index, item_index)
                _require(link_count <= 1 and new_count <= 1, "LINK/NEW batch collision")
            _require(Counter(observed) == Counter((slot_id, view) for slot_id in slots for view in range(8)), "160 unique slot/view items required")
            positions[corpus_id].append(placed)
    _require(set(positions) == set(corpora), "missing schedules")
    pairs_seen = set()
    for mapping in bindings["counterpart_registry"]:
        _record(mapping, ("left", "right", "pairs", "replaced"), "counterpart map")
        left, right = mapping["left"], mapping["right"]
        _require(left in corpora and right in corpora and left != right and (left, right) not in pairs_seen, "counterpart corpus")
        pairs_seen.add((left, right))
        _require(corpora[left]["root"] == corpora[right]["root"] and corpora[left]["arm"][:2] == corpora[right]["arm"][:2], "counterpart family")
        left_slots = {slot["id"] for slot in corpora[left]["slots"]}
        right_slots = {slot["id"] for slot in corpora[right]["slots"]}
        for roster in (mapping["pairs"], mapping["replaced"]):
            _require(type(roster) is list and all(type(pair) is list and len(pair) == 2 for pair in roster), "counterpart pairs")
        all_pairs = mapping["pairs"] + mapping["replaced"]
        _require(Counter(pair[0] for pair in all_pairs) == Counter(left_slots) and Counter(pair[1] for pair in all_pairs) == Counter(right_slots), "total/injective counterpart map required")
        for left_slot, right_slot in mapping["pairs"]:
            for epoch_index in range(5):
                for view in range(8):
                    _require(positions[left][epoch_index][(left_slot, view)] == positions[right][epoch_index][(right_slot, view)], "unchanged counterpart batch position")
        mapped = dict(mapping["pairs"])
        left_common, right_common = selections[(left, "replay")], selections[(right, "replay")]
        _require([mapped.get(source) for source in left_common["selected"]] == right_common["selected"] and [mapped.get(slot) for slot in left_common["slots"]] == right_common["slots"], "common replay counterparts")
    expected_pairs = set()
    for root in bindings["root_registry"]:
        if root["role"] == "dev":
            by_arm = {corpus["arm"]: corpus["id"] for corpus in corpora.values() if corpus["root"] == root["id"]}
            expected_pairs.update((by_arm["S1_AUTH"], by_arm[arm]) for arm in ("S1_ATOMS", "S1_EVENT_TWIN", "S1_LINK_PERMUTE"))
            expected_pairs.update((by_arm["S2_FULL_R0"], by_arm[arm]) for arm in ("S2_FULL_R1", "S2_OLD_REPLAY"))
    _require(pairs_seen == expected_pairs, "complete S1/S2 counterpart families required")


def _core_registries(bindings, corpora):
    core = bindings["core_registry"]
    _record(core, ("schema", "source_pins", "root_schema", "world_registry", "render_registry", "parser_registry", "intervention_registry"), "core registries()")
    _require(core["schema"] == "pcfl_vertical_cpu_v1" and core["source_pins"] == {**SOURCE_PINS, **CLOSURE_PIN}, "core registry/source version")
    _record(core["root_schema"], ("labels", "slots", "prefixes", "seed_prefix", "tokenizer_qualified", "dev_realized_old", "dev_canonical_relevant", "dev_primary_reachout"), "core root schema")
    _require([root["id"] for root in bindings["root_registry"]] == core["root_schema"]["labels"], "core root label order")
    _require(core["root_schema"]["tokenizer_qualified"] is False, "core candidates cannot claim tokenizer qualification")
    _record(core["world_registry"], ("old_sources", "visible_port_order", "probe_endpoints", "probe_result", "distractor", "receipt", "probe_receipt_slots", "fresh_handles", "ideal_edge_handles_not_live_chronology"), "core world registry")
    _require(core["world_registry"]["ideal_edge_handles_not_live_chronology"] is True, "chronology/ideal distinction required")
    render = core["render_registry"]
    _record(render, ("projections", "wrappers", "systems", "prompts", "retention", "substitution_classes", "no_memory_join"), "core render registry")
    _record(render["projections"], PROJECTIONS, "ten core projections")
    _require(render["wrappers"] == {f"W{index}": wrapper for index, wrapper in enumerate(WRAPPERS)}, "core wrapper literal drift")
    _require(render["retention"]["items"] == 64 and render["retention"]["projection"] == "NATIVE_CONTEXT", "core retention panel")
    parser = core["parser_registry"]
    _record(parser, ("fullmatch_patterns", "strict_memory", "semantic", "refusals", "false_row", "event_template", "link_template"), "core parser registry")
    _record(parser["fullmatch_patterns"], ("EVENT", "LINK", "READ", "ROUTE", "EXPLORE", "PROBE"), "core grammars")
    _require(parser["refusals"] == PARSER_POLICY["refusals"] and parser["semantic"] == {
        "bare": "canonical rows with optional final LF", "fence_open": ["```\n", "```text\n"],
        "fence_close": ["```", "```\n"], "row_body": "exact canonical terminal-LF block",
        "no_prose_extra_missing_duplicate_reordered_rows": True}, "core semantic/refusal literal drift")
    _require(parser["false_row"] == "any parsable EVENT/LINK span not in expected rows even alongside prose/refusal", "core false-row rule")
    registry = bindings["diagnostic_registry"]
    _record(registry, ("producer_sha256", "payload", "payload_sha256"), "diagnostic_registry")
    _require(registry["producer_sha256"] == bindings["implementation_pins"]["core"], "core producer drift")
    _require(registry["payload_sha256"] == digest(registry["payload"]), "diagnostic registry byte drift")
    diagnostic = registry["payload"]
    _record(diagnostic, ("role", "universe_sha256", "addresses"), "core diagnostic_registry()")
    _require(diagnostic["role"] == "SCORER_ONLY_NEVER_PROMPT", "wrong-block visibility")
    _hash(diagnostic["universe_sha256"])
    _require(type(diagnostic["addresses"]) is dict and bool(diagnostic["addresses"]), "diagnostic addresses")
    for candidates in diagnostic["addresses"].values():
        _require(type(candidates) is list and bool(candidates), "empty wrong-block universe")
        for candidate in candidates:
            _record(candidate, ("target", "sha256"), "wrong block")
            _require(type(candidate["target"]) is str and hashlib.sha256(candidate["target"].encode("utf-8")).hexdigest() == candidate["sha256"], "wrong block bytes")
    requests = {corpus["id"]: {slot["request"] for slot in corpus["slots"]} for corpus in corpora.values()}
    locality_seen = set()
    for roster in bindings["locality_registry"]:
        _record(roster, ("corpus", "other_corpus", "unseen", "wrong_root", "seed"), "locality")
        corpus_id, other = roster["corpus"], roster["other_corpus"]
        _require(corpus_id in corpora and corpus_id not in locality_seen and other in corpora, "locality corpus")
        locality_seen.add(corpus_id)
        _require(corpora[corpus_id]["root"] != corpora[other]["root"], "wrong-root counterpart must differ")
        _integer(roster["seed"], "locality seed")
        for kind in ("unseen", "wrong_root"):
            rows = roster[kind]
            _require(type(rows) is list and len(rows) == 8, "eight locality addresses")
            _require(len({row["request"] for row in rows}) == 8, "duplicate locality address")
            for view, row in enumerate(rows):
                _record(row, ("request", "view"), "locality address")
                _require(type(row["view"]) is int and row["view"] == view, "locality W0-W7")
                _require(type(row["request"]) is str and row["request"].startswith("READ "), "locality request")
                _require(row["request"] not in requests[corpus_id], "locality supported/replay overlap")
                _require(row["request"] in requests[other] if kind == "wrong_root" else all(row["request"] not in supported for supported in requests.values()), "locality unseen/wrong-root validity")
    _require(locality_seen == set(corpora), "locality roster coverage")
    cut_ids = set()
    for cut in bindings["intervention_registry"]:
        _record(cut, ("id", "corpus", "kind", "slots", "support", "replacement", "endpoint", "view", "seed", "unaffected_mate", "task_ids", "denominator", "minimum_drop"), "cut")
        _identifier(cut["id"])
        _require(cut["id"] not in cut_ids and cut["corpus"] in corpora, "cut identity")
        cut_ids.add(cut["id"])
        _require(cut["kind"] in ("S1_LINK", "REACHOUT_OLD", "S2_OLD", "S2_NEW"), "cut kind")
        _require(cut["replacement"] == "MISS" and cut["endpoint"] == "service", "cut replacement/endpoint")
        _integer(cut["view"], "cut view")
        _require(cut["view"] < 8, "cut wrapper")
        _integer(cut["seed"], "cut seed")
        slots = {slot["id"]: slot for slot in corpora[cut["corpus"]]["slots"]}
        _unique(cut["slots"], "cut slots")
        _require(bool(cut["slots"]) and set(cut["slots"]) <= set(slots), "cut slots unknown")
        support = {span for slot_id in cut["slots"] for span in slots[slot_id]["support"]}
        _require(set(cut["support"]) == support, "cut support mismatch")
        _require(cut["unaffected_mate"] in slots and not support.intersection(slots[cut["unaffected_mate"]]["support"]), "cut touches control mate")
        _unique(cut["task_ids"], "cut tasks")
        for task_id in cut["task_ids"]:
            _identifier(task_id)
        _integer(cut["denominator"], "cut denominator", 1)
        _integer(cut["minimum_drop"], "cut drop", 1)
        _require(cut["minimum_drop"] <= len(cut["task_ids"]) <= cut["denominator"], "unattainable cut drop")
    _require({cut["kind"] for cut in bindings["intervention_registry"]} == {"S1_LINK", "REACHOUT_OLD", "S2_OLD", "S2_NEW"}, "cut-kind coverage")


def _tokenizer(receipt, decisions_hash, environment):
    _record(receipt, ("kind", "decisions_hash", "revision", "files", "chat_template_sha256", "measurements"), "tokenizer receipt")
    _require(receipt["kind"] in ("offline_measurement", "synthetic_test"), "token evidence kind")
    _require(receipt["decisions_hash"] == decisions_hash and receipt["revision"] == environment["tokenizer_revision"] and receipt["chat_template_sha256"] == environment["chat_template_sha256"], "tokenizer binding drift")
    _require(type(receipt["files"]) is dict and bool(receipt["files"]), "tokenizer file pins")
    for value in receipt["files"].values():
        _hash(value)
    _require(type(receipt["measurements"]) is list and bool(receipt["measurements"]), "real token measurements required")
    seen = set()
    for measurement in receipt["measurements"]:
        _record(measurement, ("id", "text", "token_ids", "offsets", "attention_mask", "labels", "eos_index", "opaque_spans", "categories"), "token measurement")
        _identifier(measurement["id"])
        _require(measurement["id"] not in seen and type(measurement["text"]) is str, "measurement identity/text")
        seen.add(measurement["id"])
        length = len(measurement["token_ids"])
        _require(0 < length <= 512 and all(type(measurement[key]) is list and len(measurement[key]) == length for key in ("offsets", "attention_mask", "labels", "categories")), "token measurement shape")
        eos = measurement["eos_index"]
        _integer(eos, "EOS position")
        _require(eos < length and measurement["labels"][eos] == measurement["token_ids"][eos], "supervised EOS required")
        byte_length = len(measurement["text"].encode("utf-8"))
        for span in measurement["opaque_spans"]:
            _require(type(span) is list and len(span) == 2 and all(type(value) is int for value in span) and 0 <= span[0] < span[1] <= byte_length, "opaque byte span")
        for index, token in enumerate(measurement["token_ids"]):
            _integer(token, "token id")
            mask, label = measurement["attention_mask"][index], measurement["labels"][index]
            _require(type(mask) is int and type(label) is int, "mask/label types")
            _require((mask == 0 and label == -100) if index > eos else (mask == 1 and label in (-100, token)), "post-EOS masked padding only")
            offset = measurement["offsets"][index]
            _require(type(offset) is list and len(offset) == 2 and all(type(value) is int for value in offset) and 0 <= offset[0] <= offset[1] <= byte_length, "byte token offset")
            category = "masked" if label == -100 else "content" if index != eos and any(offset[0] < end and start < offset[1] for start, end in measurement["opaque_spans"]) else "grammar"
            _require(measurement["categories"][index] == category, "unclassified/misclassified supervised token")


def _work(bindings, corpora):
    totals = {branch: Counter() for branch in ("LOW_ONLY", "HIGH_USED")}
    fits = {branch: {} for branch in totals}
    seen, fit_rows = set(), {}
    for row in bindings["work_registry"]:
        _record(row, ("id", "kind", "purpose", "root", "state", "corpus", "endpoint", "prompt_sha256", "mount", "seed", "input_cap", "output_cap", "returned_cap", "ancestry", "denominator", "gpu_uuid", "branch", "device_seconds_cap", "budget", "profile", "reuses"), "work row")
        _identifier(row["id"])
        for key in ("purpose", "root", "state", "endpoint", "mount", "denominator", "profile"):
            _identifier(row[key])
        _require(row["id"] not in seen, "duplicate work row")
        seen.add(row["id"])
        _require(row["kind"] in ("task", "generation", "lookup", "forward", "fit", "cold_load"), "work kind")
        _require(row["purpose"] and row["denominator"], "orphan work denominator/purpose")
        _hash(row["prompt_sha256"])
        _require(row["branch"] in ("BOTH", "HIGH_USED"), "work branch")
        _require(row["budget"] in ("training", "dev_inference", "cal_low_readout", "cal_high_readout"), "work accounting budget")
        _require(row["gpu_uuid"] in bindings["environment"]["gpu_uuids"], "work GPU UUID")
        for key in ("seed", "input_cap", "output_cap", "returned_cap", "device_seconds_cap"):
            _integer(row[key], key)
        _require(row["ancestry"] in ("C0", "AUTHENTIC", "CONTROL", "EXCLUDED"), "work ancestry")
        if row["kind"] == "fit":
            _require(row["corpus"] in corpora and row["root"] == corpora[row["corpus"]]["root"], "fit corpus/root")
            _require(row["mount"] == "C0" and row["budget"] == "training" and 0 < row["device_seconds_cap"] <= 1800, "clean C0 and 30-minute fit cap")
            fit_rows[row["state"]] = row
        for branch in totals:
            if row["branch"] == "BOTH" or branch == "HIGH_USED":
                totals[branch][row["purpose"]] += 1
                totals[branch]["seconds/" + row["budget"]] += row["device_seconds_cap"]
                if row["kind"] == "fit":
                    _require(row["state"] not in fits[branch], "duplicate fit state")
                    fits[branch][row["state"]] = row["corpus"]
    for row in bindings["work_registry"]:
        _require(row["reuses"] is None or row["reuses"] in seen and row["reuses"] != row["id"], "unbound reuse")
    for branch, count in (("LOW_ONLY", 15), ("HIGH_USED", 16)):
        _require(len(fits[branch]) == count, "15/16 fits required, not obsolete fourteen")
        _require(all(totals[branch][purpose] == count_value for purpose, count_value in CORE_TOTALS.items()), "v2.1 work totals")
        _require(totals[branch]["pcfl_retention"] == count * 64, "960/1024 added retention calls required")
        retention = [row for row in bindings["work_registry"] if row["purpose"] == "pcfl_retention" and (row["branch"] == "BOTH" or branch == "HIGH_USED")]
        _require(all(row["kind"] == "generation" for row in retention) and Counter(row["state"] for row in retention) == Counter({state: 64 for state in fits[branch]}), "64 retention generations per fit state")
        _require("CAL_LOW" in fits[branch] and ("CAL_HIGH" in fits[branch]) == (branch == "HIGH_USED"), "CAL work branches")
        _require(set(fits[branch].values()) == set(corpora), "fit/corpus coverage")
        for budget, cap in (("training", count * 1800), ("dev_inference", 36000), ("cal_low_readout", 3600), ("cal_high_readout", 3600 if branch == "HIGH_USED" else 0)):
            _require(totals[branch]["seconds/" + budget] <= cap, "aggregate device-time cap")
    _require(fits["HIGH_USED"]["CAL_HIGH"] == fits["HIGH_USED"]["CAL_LOW"], "HIGH must reuse CAL corpus/schedule")
    _require(all(fit_rows["CAL_LOW"][key] == fit_rows["CAL_HIGH"][key] for key in ("corpus", "seed", "mount", "ancestry", "profile", "input_cap", "output_cap", "returned_cap")), "CAL_LOW/HIGH shared initialization bindings")
    return {branch: {"fits": len(fits[branch]), "updates": len(fits[branch]) * 200, "retention_calls": totals[branch]["pcfl_retention"], "device_seconds_cap": sum(value for key, value in totals[branch].items() if key.startswith("seconds/"))} for branch in totals}


def _profiles(bindings, contract_hash, receipts):
    profiles = bindings["profile_registry"]
    _require(type(profiles) is list and len(profiles) == 4, "four predeclared profiles required")
    by_id, paths = {}, set()
    for profile in profiles:
        _record(profile, ("id", "path", "shape", "cap_device_seconds", "gpu_uuid", "accounting"), "profile")
        _identifier(profile["id"])
        _require(profile["id"] not in by_id and type(profile["path"]) is str and profile["path"] not in paths and ".." not in profile["path"].split("/"), "profile id/path")
        _require(type(profile["shape"]) is list and bool(profile["shape"]), "profile shape")
        for dimension in profile["shape"]:
            _integer(dimension, "profile dimension", 1)
        _integer(profile["cap_device_seconds"], "profile cap", 1)
        _require(profile["accounting"] == "summed_device_seconds" and profile["gpu_uuid"] in bindings["environment"]["gpu_uuids"], "profile accounting/device")
        by_id[profile["id"]] = profile
        paths.add(profile["path"])
    for row in bindings["work_registry"]:
        _require(row["profile"] in by_id, "work references unknown profile")
    supplied = set()
    _require(receipts is None or type(receipts) is list, "profile receipts must be a list")
    synthetic = False
    for receipt in receipts or []:
        _record(receipt, ("id", "kind", "contract_sha256", "path", "shape", "gpu_uuid", "product", "device_seconds", "accounting", "evidence_sha256"), "profile receipt")
        _require(receipt["id"] in by_id and receipt["id"] not in supplied, "unknown/duplicate profile receipt")
        supplied.add(receipt["id"])
        profile = by_id[receipt["id"]]
        _require(receipt["contract_sha256"] == contract_hash, "profile contract drift")
        _require(all(receipt[key] == profile[key] for key in ("path", "shape", "gpu_uuid", "accounting")) and receipt["product"] == "A40", "profile device/shape/accounting mismatch")
        _require(type(receipt["device_seconds"]) in (int, float) and math.isfinite(receipt["device_seconds"]) and 0 <= receipt["device_seconds"] <= profile["cap_device_seconds"], "profile over cap/nonfinite")
        _require(receipt["kind"] in ("measurement", "synthetic_test"), "profile kind")
        _hash(receipt["evidence_sha256"])
        synthetic |= receipt["kind"] == "synthetic_test"
    return sorted(set(by_id) - supplied), synthetic


def build_execution_contract(bindings, tokenizer_receipt):
    """Seal caller-selected bindings; missing real evidence is never invented."""
    _record(bindings, BINDING_FIELDS, "bindings")
    detached = json.loads(canonical(bindings))
    try:
        _, skeleton_hash = _structural(detached)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ExecutionContractError("malformed structural bindings") from error
    contract = {"schema": SCHEMA, "canonicalization": CANONICALIZATION,
                "bindings": detached, "decisions_sha256": digest(detached),
                "root_skeleton_hash": skeleton_hash, "recipe": json.loads(canonical(RECIPE)),
                "production_bindings": json.loads(canonical(PRODUCTION_BINDINGS)),
                "prospective_literals": {"wrappers": WRAPPERS[:], "parser_policy": json.loads(canonical(PARSER_POLICY))},
                "calibration": _calibration_table(), "tokenizer_receipt": json.loads(canonical(tokenizer_receipt))}
    validate_execution_contract(contract)
    return contract


def validate_formation_binding(contract, corpus_id, queries, rows):
    """Bind observed core records to presealed banks; never repair chronology.

    Rows and queries are the actual core admission/materialize_queries outputs.
    This verifies their structural/byte binding, not external native custody.
    """
    validate_execution_contract(contract)
    try:
        corpus = next((entry for entry in contract["bindings"]["slot_registry"] if entry["id"] == corpus_id), None)
        _require(corpus is not None, "unknown corpus")
        _require(type(rows) is list and type(queries) is dict, "core row/query records required")
        by_support = {}
        parser = contract["bindings"]["core_registry"]["parser_registry"]
        for row in rows:
            _record(row, ("kind", "raw", "sha256", "root", "fields", "taint", "provenance"), "core row")
            _require(row["root"] == corpus["root"] and row["kind"] in ("EVENT", "LINK"), "row root/type")
            _require(row["taint"] in ("CHILD_SUBMISSION", "CONTROL"), "ideal/ceiling rows forbidden in fitted banks")
            support = row["fields"]["event" if row["kind"] == "EVENT" else "link"]
            _require(support not in by_support, "duplicate chronological handle")
            template = parser["event_template" if row["kind"] == "EVENT" else "link_template"]
            _require(row["raw"] == template.format(**row["fields"]), "row bytes/fields mismatch")
            _require(hashlib.sha256(row["raw"].encode("utf-8")).hexdigest() == row["sha256"], "row span hash mismatch")
            by_support[support] = row
        first = [slot for slot in corpus["slots"] if slot["source"] is None]
        _require(set(queries) == {slot["request"] for slot in first}, "missing/extra required query bank; no posthoc remap")
        _require(set(by_support) == {support for slot in first for support in slot["support"]}, "missing/extra required row bank")
        for slot in first:
            query = queries[slot["request"]]
            _record(query, ("request", "target", "target_sha256", "support", "source_sha256", "taint"), "core query")
            _require(query["request"] == slot["request"] and query["support"] == slot["support"], "chronological support/order mismatch")
            members = [by_support[support] for support in slot["support"]]
            for row in members:
                _require(row["fields"] == slot["bank"][row["fields"]["event" if row["kind"] == "EVENT" else "link"]], "chronological fields mismatch; ideal edge remapping forbidden")
                _require(row["kind"] == slot["row_type"] and row["taint"] == ("CHILD_SUBMISSION" if slot["taint"] == "AUTHENTIC" else "CONTROL"), "row lineage/type mismatch")
            _require(query["target"] == "".join(row["raw"] for row in members), "target not exact admitted bytes")
            _require(query["source_sha256"] == [row["sha256"] for row in members] and query["taint"] == sorted({row["taint"] for row in members}), "query source custody")
            _require(query["target_sha256"] == hashlib.sha256(query["target"].encode("utf-8")).hexdigest(), "target hash mismatch")
        return {"formation_binding_valid": True, "contract_sha256": digest(contract), "corpus": corpus_id,
                "native_custody_verified": False,
                "slots": {slot["id"]: {"target_sha256": queries[slot["request"]]["target_sha256"],
                                         "source_sha256": queries[slot["request"]]["source_sha256"][:]} for slot in corpus["slots"]}}
    except (ExecutionContractError, KeyError, TypeError, IndexError, AttributeError, ValueError) as error:
        raise ExecutionContractError(f"VS_FORMATION_BANK_MISMATCH: {error}") from error


def validate_execution_contract(contract, profile_receipts=None):
    """Validate this bridge's invariants, reporting unresolved closure interfaces.

    A self-reported source hash or synthetic measurement is not proof of an
    executed core oracle, a tokenizer run, a joint solver, or a native binding.
    This sidecar intentionally cannot release model calls.
    """
    try:
        return _validate(contract, profile_receipts)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ExecutionContractError("malformed typed registry") from error


def _validate(contract, profile_receipts):
    canonical(contract)
    _record(contract, ("schema", "canonicalization", "bindings", "decisions_sha256", "root_skeleton_hash", "recipe", "production_bindings", "prospective_literals", "calibration", "tokenizer_receipt"), "contract")
    _require(contract["schema"] == SCHEMA and contract["canonicalization"] == CANONICALIZATION, "contract version")
    _require(canonical(contract["recipe"]) == canonical(RECIPE) and canonical(contract["calibration"]) == canonical(_calibration_table()), "v2.2 constants/calibration drift")
    _require(canonical(contract["prospective_literals"]) == canonical({"wrappers": WRAPPERS, "parser_policy": PARSER_POLICY}), "prospective W8/parser literal drift")
    _require(contract["production_bindings"] == PRODUCTION_BINDINGS, "unresolved production D/probe bindings cannot be invented or promoted")
    bindings = contract["bindings"]
    _record(bindings, BINDING_FIELDS, "bindings")
    _require(bindings["source_pins"] in (SOURCE_PINS, {**SOURCE_PINS, **CLOSURE_PIN}), "source-pin drift")
    _require(contract["decisions_sha256"] == digest(bindings), "sealed decisions drift")
    _record(bindings["implementation_pins"], ("preparer", "validator", "core"), "implementation pins")
    for value in bindings["implementation_pins"].values():
        _hash(value)
    environment = bindings["environment"]
    _record(environment, ("base", "model_revision", "model_files", "tokenizer_revision", "chat_template_sha256", "environment_sha256", "product", "gpu_uuids", "cal_seeds"), "environment")
    _require(environment["base"] == RECIPE["base"] and environment["product"] == "A40", "frozen base/A40 only")
    _require(all(type(environment[key]) is str and environment[key] for key in ("model_revision", "tokenizer_revision")), "model/tokenizer revisions")
    _hash(environment["chat_template_sha256"])
    _hash(environment["environment_sha256"])
    _require(type(environment["model_files"]) is dict and bool(environment["model_files"]), "model file pins")
    for value in environment["model_files"].values():
        _hash(value)
    _unique(environment["gpu_uuids"], "GPU UUIDs")
    _require(bool(environment["gpu_uuids"]) and all(type(value) is str and value.startswith("GPU-") for value in environment["gpu_uuids"]), "GPU UUIDs")
    _record(environment["cal_seeds"], ("cal/init", "cal/dropout", "cal/readout", "cal/batch"), "shared CAL seed domains")
    for value in environment["cal_seeds"].values():
        _integer(value, "CAL seed")
    corpora, skeleton_hash = _structural(bindings)
    _require(skeleton_hash == contract["root_skeleton_hash"], "root skeleton drift")
    _replays_and_batches(bindings, corpora, skeleton_hash)
    _core_registries(bindings, corpora)
    _tokenizer(contract["tokenizer_receipt"], contract["decisions_sha256"], environment)
    branches = _work(bindings, corpora)
    missing_profiles, synthetic_profiles = _profiles(bindings, digest(contract), profile_receipts)
    missing = ["production_D_frontier_outcome_receipt_and_terminal_bytes_binding",
               "production_R_and_D_public_probe_result_bytes_binding",
               "core_render_parser_diagnostic_and_cut_oracle_certification",
               "joint_backtracker_first_solution_and_replay_counterpart_proof",
               "complete_tokenizer_inventory_and_response_mask_coverage",
               "expanded_diagnostic_service_load_and_denominator_coverage",
               "native_contract_hash_enforcement_and_actual_source_pin_verification"]
    missing.extend("profile_receipt:" + profile for profile in missing_profiles)
    if contract["tokenizer_receipt"]["kind"] == "synthetic_test" or synthetic_profiles:
        missing.append("synthetic_evidence_is_not_execution_evidence")
    return {"execution_contract_valid": False, "static_contract_complete": False,
            "ready_for_model_calls": False, "bridge_invariants_valid": True,
            "contract_sha256": digest(contract), "root_skeleton_hash": skeleton_hash,
            "branches": branches, "missing_interfaces": missing}
