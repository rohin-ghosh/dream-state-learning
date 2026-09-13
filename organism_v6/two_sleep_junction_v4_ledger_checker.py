"""Independent, CPU-only checker for the PARTIAL_SOURCE_ONLY symbolic ledger.

The roster is read from the pinned v3 section-7 table, amended by v4 section
3. Arithmetic uses the source laws, not another program's generated ledger.
Only local contract text and caller-supplied JSON are read. No scientific
material, upstream receipts, real identifiers, execution, or readiness is
validated. Generated-token and padded-training-token quantities are symbolic
maxima, not measured tokens, FLOPs, or feasibility evidence.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


CHECK_STATUS = "PARTIAL_LEDGER_CHECK_ONLY"
CONTRACT_HASHES = {
    "v3": "fafbd7818f607e0227328b13b47068f9d1493e244a297fc3c7e18bd882b61ad9",
    "v4": "57cdeb290573acb4edf68a1a4c1cbf12ae64eee6f0dc31730cc264cc79ae848a",
}
SCIENCE_GATES = (
    "GO_PREPARE", "GO_MATERIALIZE", "GO_TOKENIZER", "GO_MODEL",
    "GO_FORMATION", "GO_FIT", "GO_GPU", "GO_FIT_OR_GPU", "GO_CLAIM",
    "GO_RELEASE",
)
UNCHECKED = (
    "Full TSJ generator, topology, slot manifests, transforms, ATOM filler bytes, and real IDs.",
    "Upstream receipt/provenance, contamination, raw hashes, and imported BIRTH counts.",
    "Scientific predicates, outcomes, world-local successes, and controller preservation.",
    "Executed calls or EMPTY tails, alias hash identity, resource enforcement, and retries.",
    "Tokenizer/model execution, exact tokens, numerical FLOPs, and actual feasibility.",
    "Materialization, formation, fits, adapters, GPU use, scientific claims, or GO readiness.",
)
_CATEGORIES = ("actor", "native_reader", "cold_canary", "formation", "preservation")
_SKILLS = ("SEEK", "PROSPECT", "CHECK", "CONTINUE")


class LedgerCheckError(ValueError):
    """A symbolic input or its local source contract failed closed."""


def _require(condition: bool, path: str, reason: str) -> None:
    if not condition:
        raise LedgerCheckError(f"{path}: {reason}")


def _exact(actual: object, expected: object, path: str) -> None:
    _require(type(actual) is type(expected), path, "wrong JSON type")
    if type(expected) is dict:
        _require(actual.keys() == expected.keys(), path, "missing or unknown fields")
        for key in expected:
            _exact(actual[key], expected[key], f"{path}.{key}")
    elif type(expected) is list:
        _require(len(actual) == len(expected), path, "wrong length")
        for index, value in enumerate(expected):
            _exact(actual[index], value, f"{path}[{index}]")
    else:
        _require(actual == expected, path, "source-contract mismatch")


def _fields(actual: object, expected: dict, dynamic: tuple, path: str) -> None:
    _require(type(actual) is dict, path, "expected object")
    _require(set(actual) == set(expected).union(dynamic), path, "missing or unknown fields")
    for key, value in expected.items():
        _exact(actual[key], value, f"{path}.{key}")


def _array(value: object, length: int, path: str) -> None:
    _require(type(value) is list and len(value) == length, path, "wrong ordered roster length")


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, "JSON", f"duplicate key {key!r}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise LedgerCheckError(f"JSON: nonfinite constant {value}")


def _json_tree(value: object, ancestors: set, depth: int = 0) -> None:
    _require(depth <= 64, "JSON", "nesting limit exceeded")
    if type(value) in (dict, list):
        _require(id(value) not in ancestors, "JSON", "cyclic object")
        ancestors.add(id(value))
        if type(value) is dict:
            _require(all(type(key) is str for key in value), "JSON", "nonstring key")
            children = value.values()
        else:
            children = value
        for child in children:
            _json_tree(child, ancestors, depth + 1)
        ancestors.remove(id(value))
    else:
        _require(type(value) in (str, int, bool, type(None)), "JSON", "noninteger or non-JSON value")


def _decode(value: object) -> dict:
    if type(value) is str:
        try:
            value = json.loads(value, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        except (ValueError, RecursionError) as error:
            raise LedgerCheckError(f"JSON: {error}") from error
    _require(type(value) is dict, "JSON", "expected object or JSON object string")
    _json_tree(value, set())
    return value


def _contracts() -> tuple[dict, dict]:
    directory = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
    documents = {}
    for version, digest in CONTRACT_HASHES.items():
        path = directory / f"2026-09-13_two_sleep_own_experience_junction_source_contract_{version}.md"
        try:
            content = path.read_bytes()
        except OSError as error:
            raise LedgerCheckError(f"contract unavailable: {path.name}") from error
        _require(sha256(content).hexdigest() == digest, version, "contract hash mismatch")
        documents[version] = content.decode("utf-8")
    sections = {}
    for number in (7, 10):
        match = re.search(rf"^## {number}\. .*?(?=^## )", documents["v3"], re.M | re.S)
        _require(match is not None, "v3", f"missing section {number}")
        sections[number] = match.group()
    return documents, sections


def _source_roster(section: str) -> list:
    phases = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().replace("`", "") for cell in line[1:-1].split("|")]
        if len(cells) != 8 or cells[0] in ("phase", "---"):
            continue
        if cells[0]:
            phase, label = cells[0].split(" ", 1)
            phases.append({"phase": phase, "label": label, "table_rows": []})
        phases[-1]["table_rows"].append(cells)
    _require(len(phases) == 10, "v3.7", "unexpected source phase table")
    phases.insert(1, {
        "phase": "P05_IMPORT_CONTROLLER_BASELINE",
        "label": "Imported reduced-controller BIRTH subset", "table_rows": [],
    })
    return phases


def _metrics(value: object, compare_birth: bool, path: str) -> None:
    names = (*_SKILLS, "typed_intervention_calls", "chain_success",
             "chain_useful_pre_STEP_READ", "chain_typed_STEP", "canaries")
    denominators = (4, 4, 4, 4, 32, 8, 8, 8, 16)
    minima = (3, 3, 3, 3, 30, 6, 7, 7, 15)
    _array(value, len(names), path)
    for index, metric in enumerate(names):
        _exact(value[index], {
            "metric": metric, "denominator": denominators[index],
            "absolute_minimum": minima[index],
            "birth_maximum_count_drop": 1 if compare_birth else None,
            "count_rule": "both pair members correct" if index < 4 else "integer count",
            "role": "gate", "scope": "each_world_independently",
        }, f"{path}[{index}]")


def _empty_totals() -> dict:
    return {
        "route_rollouts": 0, "native_reader_rollouts": 0, "fits": 0,
        "categories": {category: {"calls": 0, "generated_tokens": 0} for category in _CATEGORIES},
        "model_calls": 0, "generated_tokens": 0,
    }


def _charge(budgets: object, charges: dict, totals: dict, path: str) -> None:
    _array(budgets, len(charges), path)
    for budget, (category, (calls, tokens)) in zip(budgets, charges.items()):
        _exact(budget, {"category": category, "calls": calls, "generated_tokens": tokens}, path)
        totals["categories"][category]["calls"] += calls
        totals["categories"][category]["generated_tokens"] += tokens
        totals["model_calls"] += calls
        totals["generated_tokens"] += tokens


def _routes(rows: list, source: dict, totals: dict) -> None:
    phase = source["phase"]
    _array(rows, len(source["table_rows"]), phase)
    for index, cells in enumerate(source["table_rows"]):
        _, ordinal_text, condition, mount, service_bank, goals_text, predicate, role = cells
        condition = re.sub(r" \(2\)$", "", condition)
        bounds = [int(number) for number in re.findall(r"\d+", ordinal_text)]
        first, last = bounds[0], bounds[-1]
        primary = goals_text == "P"
        count = 1 if primary else 2
        _require(last - first + 1 == count, phase, "invalid source route ordinals")
        service, bank = service_bank.split(" ", 1)
        if predicate.startswith("<=1/2"):
            predicate = "success " + predicate
        if condition == "ATOM_TEXT":
            role = "gate"
        row = rows[index]
        _fields(row, {
            "kind": "route", "condition": condition, "actor_mount": mount,
            "service": service, "bank": bank, "goals": ["g*"] if primary else [0, 1],
            "goal_selector": "P" if primary else "G",
            "goal_family": "F" if phase in ("P10", "P30") or condition == "AUTH_OLD_RETENTION" else "H",
            "goal_count": count, "ordinals": list(range(first, last + 1)),
            "ordinal_prefix": "R", "expected": predicate, "role": role,
            "predicate_scope": "each_world_independently",
        }, ("budgets",), f"{phase}[{index}]")
        charges = {"actor": (22 * count, 4096 * count)}
        totals["route_rollouts"] += count
        if service == "NATIVE":
            totals["native_reader_rollouts"] += count
            charges["native_reader"] = (10 * count, 160 * 10 * count)
        _charge(row["budgets"], charges, totals, f"{phase}[{index}].budgets")


def _formation(rows: list, stage: int, totals: dict) -> None:
    _array(rows, 20 if stage == 1 else 6, "formation")
    for index, row in enumerate(rows):
        if stage == 1:
            if index < 16:
                condition = ("s0", "s1", "t0", "t1", "i0", "i1", "i2", "i3")[index // 2]
                kind = "EVENT" if index % 2 else "action"
            else:
                condition, kind = ("LS0", "LS1", "IL0", "IL1")[index - 16], "LINK"
        elif index < 4:
            condition = "primary" if index < 2 else "complement"
            kind = "EVENT" if index % 2 else "PROBE"
        else:
            condition, kind = f"NL{index - 4}", "LINK"
        _fields(row, {
            "kind": "formation", "condition": condition, "call_kind": kind,
            "ordinal": index + 1, "ordinal_prefix": "F", "goal_count": 0,
            "actor_mount": "BIRTH" if stage == 1 else "S1 AUTH child",
            "service": "public world/accepted rows", "expected": "exact yields",
            "role": "gate", "gate_stage": f"S{stage}",
        }, ("budgets",), f"formation[{index}]")
        cap = 160 if kind == "LINK" else 128 if kind == "EVENT" else 64
        _charge(row["budgets"], {"formation": (1, cap)}, totals, f"formation[{index}].budgets")


def _cold(rows: list, events: int, totals: dict, path: str) -> None:
    counts = (2 * events, 2 * events, events, 4, 16)
    kinds = ("EVENT_AT", "LINKS_FROM", "EVENT", "INVALID", "CANARY")
    orders = (
        "EVENT rows ascending; SOURCE slots 0,1; retain repeats",
        "EVENT IDs ascending; slots 0,1", "EVENT IDs ascending",
        "EVENT_AT invalid/0, EVENT_AT invalid/1, LINKS_FROM invalid/0, EVENT invalid",
        "upstream canary ordinal 0..15",
    )
    _array(rows, 5, path)
    for index, row in enumerate(rows):
        first = 1 + sum(counts[:index])
        canary = index == 4
        _fields(row, {
            "kind": kinds[index], "ordinals": list(range(first, first + counts[index])),
            "order": orders[index], "role": "gate",
            "expected": "canaries >=15/16" if canary else "exact registered row/MISS; 1.00",
        }, ("budgets",), f"{path}[{index}]")
        _charge(row["budgets"], {"cold_canary": (counts[index], counts[index] * (256 if canary else 160))}, totals, path)


def _fits(rows: list, source: dict, stage: int, totals: dict) -> None:
    arms = source["table_rows"][0][2].split(",")
    _array(rows, len(arms), source["phase"])
    for index, arm in enumerate(arms):
        ancestor = arm if arm in ("O", "ATOM", "RAW") else "AUTH"
        row = rows[index]
        _fields(row, {
            "kind": "fit", "condition": arm, "stage": f"S{stage}",
            "ordinal": index + 1, "ordinal_prefix": "F", "fits": 1,
            "actor_mount": "BIRTH ancestor" if stage == 1 else f"S1 {ancestor}",
            "service": "named tape", "goal_count": 0, "role": "gate",
            "expected": "fit/cold gates", "budgets": [],
            "memory_units": 8 + stage * 4, "views_per_unit": 8, "repeats_per_view": 25,
        }, ("cold_immediately_after_fit",), f"{source['phase']}[{index}]")
        _cold(row["cold_immediately_after_fit"], 6 + stage * 2, totals, f"{source['phase']}[{index}].cold")
        totals["fits"] += 1


def _baseline(rows: list) -> None:
    _array(rows, 1, "P05")
    _fields(rows[0], {
        "kind": "import", "actor_mount": "BIRTH", "role": "gate",
        "goal_count": 0, "budgets": [], "skill_order": list(_SKILLS),
        "pair_ordinals": list(range(0, 8, 2)), "member_order": ["lower", "upper"],
        "chain_ordinals": list(range(0, 32, 4)), "canary_ordinals": list(range(16)),
        "requires": ["content-bound upstream receipt", "exact raw output hashes", "exact call hashes"],
        "receipt_import_implemented": False,
    }, ("metrics",), "P05.import")
    _metrics(rows[0]["metrics"], False, "P05.metrics")


def _preservation(rows: list, stage: int, totals: dict) -> None:
    _array(rows, 32 + 8 + 16, "preservation")
    for index, row in enumerate(rows):
        expected = {"ordinal_prefix": "C", "role": "gate"}
        if index < 32:
            expected.update(
                kind="intervention", skill=_SKILLS[index // 8], pair=(index % 8 // 2) * 2,
                member="upper" if index % 2 else "lower", ordinals=[index + 1],
            )
            charges = (1, 256)
        elif index < 40:
            chain = index - 32
            first = 33 + chain * 29
            expected.update(
                kind="chain", chain_ordinal=chain * 4, ordinals=list(range(first, first + 29)),
                reservation_state="RESERVED", unused_tail_state="EMPTY",
                empty_slot_calls=0, empty_slot_tokens=0,
                token_cap_scope="whole_chain_not_each_reserved_slot",
            )
            charges = (29, 4096)
        else:
            canary = index - 40
            expected.update(
                kind="alias", ordinals=[265 + canary], identical_raw_hashes_required=True,
                target={
                    "phase": "P20" if stage == 1 else "P60", "fit": "AUTH", "world": "same_world",
                    "query_ordinal": 5 * (6 + stage * 2) + 5 + canary, "canary_ordinal": canary,
                },
            )
            charges = (0, 0)
        _fields(row, expected, ("budgets",), f"preservation[{index}]")
        _charge(row["budgets"], {"preservation": charges}, totals, f"preservation[{index}].budgets")


def _envelope(ledger: dict, sections: dict) -> None:
    _fields(ledger, {
        "source_status": "PARTIAL_SOURCE_ONLY",
        "source_binding": {
            "v4_sha256": CONTRACT_HASHES["v4"], "v3_sha256": CONTRACT_HASHES["v3"],
            "v3_commit": "ac1feacb08581adf60972adc14eabd501c13847b",
            "v3_section_7_sha256": sha256(sections[7].encode()).hexdigest(),
            "v3_section_10_sha256": sha256(sections[10].encode()).hexdigest(),
            "section_hash_rule": "Exact bytes from ## heading to next ## heading, exclusive.",
            "amendments": ["v4 section 3.1", "v4 section 3.2", "v4 section 3.3"],
            "supporting_formulas": ["v3 sections 3, 4, 9, 10", "v4 section 5.4"],
        },
        "scope": "symbolic per-world CPU phase/resource template only",
        "world_order": ["W0", "W1"], "world_count": 2,
        "gates": dict.fromkeys(SCIENCE_GATES, False), "empirical_feasibility_claim": False,
        "predicate_policy": {
            "evaluated": False, "noncompensatory": True,
            "malformed_rejected_stopped": "zero in fixed denominator; no retry or denominator reduction",
            "controller_comparison": "each integer count >= imported BIRTH subset count minus one AND absolute minimum; no ratio rounding",
            "atom_failure": "2/2 in either world stops corresponding stage; no cross-world rescue",
            "raw_role": "diagnostic except interface/custody/feasibility gates",
        },
        "unimplemented_scope": [
            "scientific material, topology, goals and opaque identifiers",
            "upstream receipt import, raw hashes and controller baseline values",
            "tokenizer, model, learner outputs and predicate evaluation",
            "formation, fits, adapters, GPU execution and resource enforcement",
            "exact padded-token witness and numerical FLOP budget",
            "full TSJ generator, preparation audit and scientific claims",
        ],
    }, ("phases", "resources"), "ledger")


def _sum_totals(per_phase: dict) -> dict:
    total = _empty_totals()
    for phase in per_phase.values():
        for key in ("route_rollouts", "native_reader_rollouts", "fits", "model_calls", "generated_tokens"):
            total[key] += phase[key]
        for category in _CATEGORIES:
            for key in ("calls", "generated_tokens"):
                total["categories"][category][key] += phase["categories"][category][key]
    return total


def _pair(total: dict) -> dict:
    return {key: _pair(value) if type(value) is dict else value * 2 for key, value in total.items()}


def _training(training: object, per_phase: dict, section: str) -> None:
    _fields(training, {}, ("D1", "D2"), "training")
    for dose, replay in (("D1", 1024), ("D2", 2048)):
        stages = {}
        for stage, phase, units in (("S1", "P20", 12), ("S2", "P60", 16)):
            fits = per_phase[phase]["fits"]
            presentations = replay + units * 8 * 25
            stages[stage] = {
                "fits_per_world": fits, "presentations_per_fit": presentations,
                "updates_per_fit": presentations // 4,
                "presentations_per_world": presentations * fits,
                "updates_per_world": presentations * fits // 4,
            }
        presentations = sum(stage["presentations_per_world"] for stage in stages.values())
        per_world = {"updates": presentations // 4, "presentations": presentations,
                     "maximum_padded_training_tokens": presentations * 16384}
        pair = _pair(per_world)
        table = re.search(rf"^\|{dose}\|([\d,]+) / ([\d,]+)\|([\d,]+)\|([\d,]+)\|$", section, re.M)
        _require(table is not None, dose, "missing source training maxima")
        _exact([stages["S1"]["updates_per_fit"], stages["S2"]["updates_per_fit"],
                pair["updates"], pair["presentations"]],
               [int(value.replace(",", "")) for value in table.groups()], dose)
        _exact(training[dose], {"stages": stages, "per_world": per_world, "pair": pair}, f"training.{dose}")


def _resources(resources: object, per_phase: dict, documents: dict, sections: dict) -> dict:
    world = _sum_totals(per_phase)
    pair = _pair(world)
    for label, actual in (("model calls/world", world["model_calls"]),
                          ("model calls/pair", pair["model_calls"]),
                          ("generated tokens/world", world["generated_tokens"]),
                          ("generated tokens/pair", pair["generated_tokens"])):
        match = re.search(rf"^{re.escape(label)}\s+([\d,]+)$", documents["v4"], re.M)
        _require(match is not None, "v4.3.3", f"missing {label}")
        _exact(actual, int(match.group(1).replace(",", "")), label)
    _fields(resources, {
        "interpretation": "declared upper bounds, not observed usage or empirical feasibility",
        "by_phase_per_world": per_phase, "per_world": world, "pair": pair,
        "training_formula": {
            "birth_presentations": {"D1": 1024, "D2": 2048}, "batch_size": 4,
            "maximum_sequence_tokens": 16384,
            "flop_stop": "8 * imported_parameter_count * exact_padded_training_tokens",
            "exact_padded_training_tokens": None, "imported_parameter_count": None,
            "flop_stop_value": None,
            "flop_interpretation": "conservative stopping budget and arm-matching proxy, not profiler FLOPs",
            "parameter_count_requirement": "upstream-receipt integer; two independent index readers agree; unique named base tensors plus largest rank-8 adapter set; exclude aliases, optimizer states, gradients, tokenizer and KV cache",
        },
        "hard_stops": {"gpu_hours": 248, "cpu_preparation_hours": 8, "scientific_elapsed_hours": 72},
        "retry_policy": {
            "scientific_retries": 0, "replacement_worlds_or_seeds": 0,
            "pre_side_effect_infrastructure_restarts_whole_version": 1,
            "restart_requires": "verified pre-model-call/pre-side-effect, identical bytes, logged; later or uncertain failure stops",
            "partial_work_counts": True,
        },
    }, ("training",), "resources")
    _training(resources["training"], per_phase, sections[10])
    return world


def check_ledger(value: dict | str) -> dict:
    """Validate a symbolic object/string; raise LedgerCheckError on any mismatch.

    The input is not modified. Duplicate keys are detected in raw JSON strings;
    duplicates already discarded by an upstream JSON parser cannot be recovered
    from a Python dict. RESERVED chains retain their whole-chain upper bound;
    EMPTY is a zero-cost tail policy, not an executed usage record in this schema.
    """
    ledger = _decode(value)
    documents, sections = _contracts()
    _envelope(ledger, sections)
    roster = _source_roster(sections[7])
    _array(ledger["phases"], len(roster), "phases")
    per_phase = {}
    for phase, source in zip(ledger["phases"], roster):
        name = source["phase"]
        preservation = name in ("P31", "P71")
        expected = {"phase": name, "label": source["label"]}
        if preservation:
            expected.update(actor_mount="S1 AUTH" if name == "P31" else "S2 AUTH", service="upstream exact")
        _fields(phase, expected, ("rows", "metrics") if preservation else ("rows",), name)
        total = _empty_totals()
        rows = phase["rows"]
        if name == "P05_IMPORT_CONTROLLER_BASELINE":
            _baseline(rows)
        elif name in ("P00", "P40"):
            _formation(rows, 1 if name == "P00" else 2, total)
        elif name in ("P20", "P60"):
            _fits(rows, source, 1 if name == "P20" else 2, total)
        elif preservation:
            _metrics(phase["metrics"], True, f"{name}.metrics")
            _preservation(rows, 1 if name == "P31" else 2, total)
        else:
            _routes(rows, source, total)
        per_phase[name] = total
    world = _resources(ledger["resources"], per_phase, documents, sections)
    return {
        "status": CHECK_STATUS, "gates": dict.fromkeys(SCIENCE_GATES, False),
        "empirical_feasibility_claim": False, "predicates_evaluated": False,
        "by_phase_per_world": per_phase, "per_world": world, "pair": _pair(world),
        "unimplemented_coverage": list(UNCHECKED),
    }


def validate_ledger(value: dict | str) -> dict:
    """Alias for the independent checker, never for the primary validator."""
    return check_ledger(value)
