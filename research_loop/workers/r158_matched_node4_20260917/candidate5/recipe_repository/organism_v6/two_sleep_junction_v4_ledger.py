"""Symbolic CPU-only TSJ-v4 phase/resource caps, not an execution plan or evidence."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json


SOURCE_STATUS = "PARTIAL_SOURCE_ONLY"
V4_SHA256 = "57cdeb290573acb4edf68a1a4c1cbf12ae64eee6f0dc31730cc264cc79ae848a"
V3_SHA256 = "fafbd7818f607e0227328b13b47068f9d1493e244a297fc3c7e18bd882b61ad9"
V3_SECTION_7_SHA256 = "87227a0327b50ca25c14c336d2370cc79758b51cd783d57ff12c4fed04b57bff"
V3_SECTION_10_SHA256 = "7e68047f3f7aba25aef5d1dbb6406a0d8e38de17c8da1ebd5c14bab2ada89dc3"
PHASE_ORDER = (
    "P00", "P05_IMPORT_CONTROLLER_BASELINE", "P10", "P20", "P30", "P31",
    "P40", "P50", "P60", "P70", "P71",
)
SKILLS = ("SEEK", "PROSPECT", "CHECK", "CONTINUE")
PAIRS = (0, 2, 4, 6)
CHAINS = (0, 4, 8, 12, 16, 20, 24, 28)
S1_ARMS = ("AUTH", "O", "T", "ATOM", "REL_CUT", "IRR_CUT", "RAW")
S2_ARMS = ("AUTH", "N", "O", "ATOM", "RAW", "OLD_FILLER")
RESOURCE_CATEGORIES = (
    "actor", "native_reader", "cold_canary", "formation", "preservation",
)
OLD_ACTION = "a(g xor O xor T); 2/2"
OLD_O_ACTION = "a(g xor (1-O) xor T); 2/2"
OLD_T_ACTION = "a(g xor O xor (1-T)); 2/2"
NEW_ACTION = "a(g xor O xor T xor N); 2/2"
NEW_O_ACTION = "a(g xor (1-O) xor T xor N); 2/2"
NEW_N_ACTION = "a(g xor O xor T xor (1-N)); 2/2"


def verify_source_bytes(v4_bytes: bytes, v3_bytes: bytes) -> dict:
    """Verify caller-supplied local bytes without opening files or importing material."""
    for name, content, expected in (
        ("v4", v4_bytes, V4_SHA256), ("v3", v3_bytes, V3_SHA256),
    ):
        if not isinstance(content, bytes) or sha256(content).hexdigest() != expected:
            raise ValueError(f"source_hash_mismatch:{name}")
    return source_binding()


def source_binding() -> dict:
    return {
        "v4_sha256": V4_SHA256,
        "v3_sha256": V3_SHA256,
        "v3_commit": "ac1feacb08581adf60972adc14eabd501c13847b",
        "v3_section_7_sha256": V3_SECTION_7_SHA256,
        "v3_section_10_sha256": V3_SECTION_10_SHA256,
        "section_hash_rule": "Exact bytes from ## heading to next ## heading, exclusive.",
        "amendments": ["v4 section 3.1", "v4 section 3.2", "v4 section 3.3"],
        "supporting_formulas": ["v3 sections 3, 4, 9, 10", "v4 section 5.4"],
    }


def _budget(category: str, calls: int, tokens: int) -> dict:
    return {"category": category, "calls": calls, "generated_tokens": tokens}


def _phase(phase: str, label: str, rows: list) -> dict:
    return {"phase": phase, "label": label, "rows": rows}


def _route_rows(phase: str, specifications: tuple) -> list:
    rows = []
    ordinal = 1
    for condition, mount, service, bank, expected, role, primary in specifications:
        goals = ["g*"] if primary else [0, 1]
        goal_family = "F" if phase in ("P10", "P30") or condition == "AUTH_OLD_RETENTION" else "H"
        budgets = [_budget("actor", len(goals) * 22, len(goals) * 4096)]
        if service == "NATIVE":
            budgets.append(_budget("native_reader", len(goals) * 10, len(goals) * 10 * 160))
        rows.append({
            "kind": "route", "condition": condition, "actor_mount": mount,
            "service": service, "bank": bank, "goals": goals,
            "goal_selector": "P" if primary else "G", "goal_family": goal_family,
            "goal_count": len(goals), "ordinals": list(range(ordinal, ordinal + len(goals))),
            "ordinal_prefix": "R", "expected": expected, "role": role,
            "predicate_scope": "each_world_independently",
            "budgets": budgets,
        })
        ordinal += len(goals)
    return rows


def _pre_s1_rows() -> list:
    return _route_rows("P10", (
        ("SUPPLIED_INLINE", "BIRTH", "INLINE", "AUTH-OLD", OLD_ACTION, "gate", False),
        ("SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING", "BIRTH", "ACTIVE", "AUTH-OLD", "self-READ then " + OLD_ACTION, "gate", False),
        ("ATOM_TEXT", "BIRTH", "ACTIVE", "AUTH events/no links", "success <=1/2", "gate", False),
        ("O_TEXT", "BIRTH", "ACTIVE", "O transform", OLD_O_ACTION, "gate", False),
        ("T_TEXT", "BIRTH", "ACTIVE", "T transform", OLD_T_ACTION, "gate", False),
        ("RELEVANT_CUT_TEXT", "BIRTH", "ACTIVE", "rel cut", "fail/change", "gate", True),
        ("IRRELEVANT_CUT_TEXT", "BIRTH", "ACTIVE", "irr cut", "success/same", "gate", True),
    ))


def _post_s1_rows() -> list:
    return _route_rows("P30", (
        ("AUTH", "S1 AUTH", "NATIVE", "AUTH", OLD_ACTION, "gate", False),
        ("O", "S1 O", "NATIVE", "O", OLD_O_ACTION, "gate", False),
        ("T", "S1 T", "NATIVE", "T", OLD_T_ACTION, "gate", False),
        ("ATOM", "S1 ATOM", "NATIVE", "atom", "success <=1/2", "gate", False),
        ("BIRTH", "BIRTH", "NATIVE", "BIRTH", "success <=1/2", "gate", False),
        ("FOREIGN", "other world's S1 AUTH", "NATIVE", "foreign", "success <=1/2", "gate", False),
        ("RAW", "S1 RAW", "NATIVE", "raw", "oracle action a(g xor O xor T); report", "diagnostic", False),
        ("RESP_T", "S1 AUTH", "FORK", "T", "exact T-counterfactual; 2/2", "gate", False),
        ("REL_CUT", "S1 REL_CUT", "NATIVE", "cut", "fail/change from AUTH", "gate", True),
        ("IRR_CUT", "S1 IRR_CUT", "NATIVE", "cut", "AUTH action/success", "gate", True),
    ))


def _post_new_rows() -> list:
    return _route_rows("P50", (
        ("SUPPLIED_INLINE", "BIRTH", "INLINE", "AUTH OLD+NEW", NEW_ACTION, "gate", False),
        ("SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING", "BIRTH", "ACTIVE", "AUTH OLD+NEW", "self-READ then " + NEW_ACTION, "gate", False),
        ("ATOM_TEXT", "BIRTH", "ACTIVE", "atoms", "success <=1/2", "gate", False),
        ("O_TEXT", "BIRTH", "ACTIVE", "O", NEW_O_ACTION, "gate", False),
        ("N_TEXT", "BIRTH", "ACTIVE", "N", NEW_N_ACTION, "gate", False),
        ("OLD_FILLER_TEXT", "BIRTH", "ACTIVE", "OLD+filler", "success <=1/2", "gate", False),
        ("RESP_O_PRE", "BIRTH", "FORK", "AUTH active", NEW_O_ACTION, "gate", False),
        ("RESP_N_PRE", "BIRTH", "FORK", "AUTH active", NEW_N_ACTION, "gate", False),
    ))


def _post_s2_rows() -> list:
    return _route_rows("P70", (
        ("AUTH", "S2 AUTH", "NATIVE", "AUTH", NEW_ACTION, "gate", False),
        ("N", "S2 N", "NATIVE", "N", NEW_N_ACTION, "gate", False),
        ("O", "S2 O", "NATIVE", "O", NEW_O_ACTION, "gate", False),
        ("ATOM", "S2 ATOM", "NATIVE", "atom", "success <=1/2", "gate", False),
        ("RAW", "S2 RAW", "NATIVE", "raw", "oracle delayed action; report", "diagnostic", False),
        ("OLD_FILLER", "S2 OLD_FILLER", "NATIVE", "filler", "success <=1/2", "gate", False),
        ("FOREIGN", "other world's S2 AUTH", "NATIVE", "foreign", "success <=1/2", "gate", False),
        ("RESP_O", "S2 AUTH", "FORK", "O", "exact O-counterfactual; 2/2", "gate", False),
        ("RESP_N", "S2 AUTH", "FORK", "N", "exact N-counterfactual; 2/2", "gate", False),
        ("S1_NOWRITE", "S1 AUTH", "NATIVE", "AUTH-old", "success <=1/2; diagnostic only", "diagnostic", False),
        ("AUTH_OLD_RETENTION", "S2 AUTH", "NATIVE", "AUTH", OLD_ACTION, "gate", False),
    ))


def _formation_rows(stage: str) -> list:
    if stage == "S1":
        schedule = [
            (role, kind)
            for role in ("s0", "s1", "t0", "t1", "i0", "i1", "i2", "i3")
            for kind in ("action", "EVENT")
        ] + [(role, "LINK") for role in ("LS0", "LS1", "IL0", "IL1")]
    else:
        schedule = [
            ("primary", "PROBE"), ("primary", "EVENT"),
            ("complement", "PROBE"), ("complement", "EVENT"),
            ("NL0", "LINK"), ("NL1", "LINK"),
        ]
    caps = {"action": 64, "PROBE": 64, "EVENT": 128, "LINK": 160}
    return [{
        "kind": "formation", "condition": role, "call_kind": kind,
        "ordinal": ordinal, "ordinal_prefix": "F", "goal_count": 0,
        "actor_mount": "BIRTH" if stage == "S1" else "S1 AUTH child",
        "service": "public world/accepted rows", "expected": "exact yields",
        "role": "gate", "gate_stage": stage,
        "budgets": [_budget("formation", 1, caps[kind])],
    } for ordinal, (role, kind) in enumerate(schedule, 1)]


def _cold_rows(event_count: int) -> list:
    specifications = (
        ("EVENT_AT", event_count * 2, 160, "EVENT rows ascending; SOURCE slots 0,1; retain repeats"),
        ("LINKS_FROM", event_count * 2, 160, "EVENT IDs ascending; slots 0,1"),
        ("EVENT", event_count, 160, "EVENT IDs ascending"),
        ("INVALID", 4, 160, "EVENT_AT invalid/0, EVENT_AT invalid/1, LINKS_FROM invalid/0, EVENT invalid"),
        ("CANARY", 16, 256, "upstream canary ordinal 0..15"),
    )
    rows = []
    ordinal = 1
    for kind, count, cap, order in specifications:
        rows.append({
            "kind": kind, "ordinals": list(range(ordinal, ordinal + count)),
            "order": order, "role": "gate",
            "expected": "canaries >=15/16" if kind == "CANARY" else "exact registered row/MISS; 1.00",
            "budgets": [_budget("cold_canary", count, count * cap)],
        })
        ordinal += count
    return rows


def _fit_rows(stage: str) -> list:
    arms = S1_ARMS if stage == "S1" else S2_ARMS
    ancestors = {"AUTH": "AUTH", "N": "AUTH", "O": "O", "ATOM": "ATOM", "RAW": "RAW", "OLD_FILLER": "AUTH"}
    rows = []
    for ordinal, arm in enumerate(arms, 1):
        rows.append({
            "kind": "fit", "condition": arm, "stage": stage,
            "ordinal": ordinal, "ordinal_prefix": "F", "fits": 1,
            "actor_mount": "BIRTH ancestor" if stage == "S1" else "S1 " + ancestors[arm],
            "service": "named tape", "goal_count": 0,
            "role": "gate", "expected": "fit/cold gates", "budgets": [],
            "memory_units": 12 if stage == "S1" else 16,
            "views_per_unit": 8, "repeats_per_view": 25,
            "cold_immediately_after_fit": _cold_rows(8 if stage == "S1" else 10),
        })
    return rows


def controller_metrics(compare_birth: bool = False) -> list:
    """Declare fixed denominators/minima; never accept or evaluate learner outputs."""
    specifications = [(skill, 4, 3) for skill in SKILLS] + [
        ("typed_intervention_calls", 32, 30), ("chain_success", 8, 6),
        ("chain_useful_pre_STEP_READ", 8, 7), ("chain_typed_STEP", 8, 7),
        ("canaries", 16, 15),
    ]
    return [{
        "metric": metric, "denominator": denominator, "absolute_minimum": minimum,
        "birth_maximum_count_drop": 1 if compare_birth else None,
        "count_rule": "both pair members correct" if metric in SKILLS else "integer count",
        "role": "gate", "scope": "each_world_independently",
    } for metric, denominator, minimum in specifications]


def reservation_call_maximum(kind: str, state: str = "RESERVED") -> int:
    """Account for a symbolic slot, without recording any execution or output."""
    if kind not in ("intervention", "chain", "alias"):
        raise ValueError("unknown_reservation_kind")
    if state not in ("RESERVED", "EMPTY") or (state == "EMPTY" and kind != "chain"):
        raise ValueError("invalid_reservation_state")
    return 0 if kind == "alias" or state == "EMPTY" else 1


def _preservation_rows(stage: str) -> list:
    rows = []
    ordinal = 1
    for skill in SKILLS:
        for pair in PAIRS:
            for member in ("lower", "upper"):
                rows.append({
                    "kind": "intervention", "skill": skill, "pair": pair,
                    "member": member, "ordinals": [ordinal], "ordinal_prefix": "C",
                    "role": "gate", "budgets": [_budget("preservation", reservation_call_maximum("intervention"), 256)],
                })
                ordinal += 1
    for chain in CHAINS:
        slots = list(range(ordinal, ordinal + 29))
        rows.append({
            "kind": "chain", "chain_ordinal": chain, "ordinals": slots,
            "ordinal_prefix": "C", "role": "gate", "reservation_state": "RESERVED",
            "unused_tail_state": "EMPTY", "empty_slot_calls": 0, "empty_slot_tokens": 0,
            "token_cap_scope": "whole_chain_not_each_reserved_slot",
            "budgets": [_budget("preservation", len(slots) * reservation_call_maximum("chain"), 4096)],
        })
        ordinal += len(slots)
    cold_canaries = _cold_rows(8 if stage == "S1" else 10)[-1]["ordinals"]
    for canary, target in enumerate(cold_canaries):
        rows.append({
            "kind": "alias", "ordinals": [ordinal], "ordinal_prefix": "C",
            "role": "gate", "target": {
                "phase": "P20" if stage == "S1" else "P60", "fit": "AUTH",
                "world": "same_world", "query_ordinal": target, "canary_ordinal": canary,
            },
            "identical_raw_hashes_required": True,
            "budgets": [_budget("preservation", reservation_call_maximum("alias"), 0)],
        })
        ordinal += 1
    return rows


def canonical_phases() -> list:
    """Return a fresh per-world template, not instantiated worlds or scientific rows."""
    baseline = _phase("P05_IMPORT_CONTROLLER_BASELINE", "Imported reduced-controller BIRTH subset", [{
        "kind": "import", "actor_mount": "BIRTH", "role": "gate",
        "goal_count": 0, "budgets": [], "metrics": controller_metrics(),
        "skill_order": list(SKILLS), "pair_ordinals": list(PAIRS),
        "member_order": ["lower", "upper"], "chain_ordinals": list(CHAINS),
        "canary_ordinals": list(range(16)),
        "requires": ["content-bound upstream receipt", "exact raw output hashes", "exact call hashes"],
        "receipt_import_implemented": False,
    }])
    phases = [
        _phase("P00", "OLD formation", _formation_rows("S1")), baseline,
        _phase("P10", "PRE-S1", _pre_s1_rows()),
        _phase("P20", "S1 fits", _fit_rows("S1")),
        _phase("P30", "POST-S1", _post_s1_rows()),
        _phase("P31", "preservation", _preservation_rows("S1")),
        _phase("P40", "NEW formation", _formation_rows("S2")),
        _phase("P50", "POST-NEW", _post_new_rows()),
        _phase("P60", "S2 fits", _fit_rows("S2")),
        _phase("P70", "POST-S2", _post_s2_rows()),
        _phase("P71", "preservation", _preservation_rows("S2")),
    ]
    for phase in phases:
        if phase["phase"] in ("P31", "P71"):
            phase["metrics"] = controller_metrics(compare_birth=True)
            phase["actor_mount"] = "S1 AUTH" if phase["phase"] == "P31" else "S2 AUTH"
            phase["service"] = "upstream exact"
    return phases


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def validate_phases(phases: list) -> None:
    if not isinstance(phases, list) or any(not isinstance(phase, dict) for phase in phases):
        raise ValueError("invalid_phase_schema")
    names = [phase.get("phase") for phase in phases]
    if any(not isinstance(name, str) for name in names):
        raise ValueError("invalid_phase_name")
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        raise ValueError("duplicate_phase:" + ",".join(duplicates))
    missing = [name for name in PHASE_ORDER if name not in names]
    if missing:
        raise ValueError("omitted_phase:" + ",".join(missing))
    if tuple(names) != PHASE_ORDER:
        raise ValueError("noncanonical_phase_order_or_unknown_phase")
    try:
        matches = _json(phases) == _json(canonical_phases())
    except (TypeError, ValueError) as error:
        raise ValueError("invalid_phase_json") from error
    if not matches:
        raise ValueError("noncanonical_phase_rows")


def _row_budgets(row: dict) -> list:
    return row["budgets"] + [
        budget
        for cold in row.get("cold_immediately_after_fit", [])
        for budget in cold["budgets"]
    ]


def _resources_for_rows(rows: list) -> dict:
    categories = {category: {"calls": 0, "generated_tokens": 0} for category in RESOURCE_CATEGORIES}
    for row in rows:
        for budget in _row_budgets(row):
            category = categories[budget["category"]]
            category["calls"] += budget["calls"]
            category["generated_tokens"] += budget["generated_tokens"]
    return {
        "route_rollouts": sum(row["goal_count"] for row in rows if row["kind"] == "route"),
        "native_reader_rollouts": sum(row["goal_count"] for row in rows if row["kind"] == "route" and row["service"] == "NATIVE"),
        "fits": sum(row.get("fits", 0) for row in rows),
        "categories": categories,
        "model_calls": sum(category["calls"] for category in categories.values()),
        "generated_tokens": sum(category["generated_tokens"] for category in categories.values()),
    }


def _scale_counts(value: dict, factor: int) -> dict:
    return {
        key: _scale_counts(count, factor) if isinstance(count, dict) else count * factor
        for key, count in value.items()
    }


def _training_maxima(rows: list) -> dict:
    result = {}
    for dose, birth_presentations in (("D1", 1024), ("D2", 2048)):
        stages = {}
        for stage in ("S1", "S2"):
            fits = [row for row in rows if row["kind"] == "fit" and row["stage"] == stage]
            fit_presentations = [
                row["memory_units"] * row["views_per_unit"] * row["repeats_per_view"] + birth_presentations
                for row in fits
            ]
            stages[stage] = {
                "fits_per_world": sum(row["fits"] for row in fits),
                "presentations_per_fit": fit_presentations[0],
                "updates_per_fit": fit_presentations[0] // 4,
                "presentations_per_world": sum(fit_presentations),
                "updates_per_world": sum(presentations // 4 for presentations in fit_presentations),
            }
        presentations = sum(stage["presentations_per_world"] for stage in stages.values())
        per_world = {
            "updates": sum(stage["updates_per_world"] for stage in stages.values()),
            "presentations": presentations,
            "maximum_padded_training_tokens": presentations * 16384,
        }
        result[dose] = {"stages": stages, "per_world": per_world, "pair": _scale_counts(per_world, 2)}
    return result


def derive_resources(phases: list) -> dict:
    """Reject any noncanonical roster before deriving upper bounds from its rows."""
    validate_phases(phases)
    rows = [row for phase in phases for row in phase["rows"]]
    per_world = _resources_for_rows(rows)
    return {
        "interpretation": "declared upper bounds, not observed usage or empirical feasibility",
        "by_phase_per_world": {phase["phase"]: _resources_for_rows(phase["rows"]) for phase in phases},
        "per_world": per_world, "pair": _scale_counts(per_world, 2),
        "training": _training_maxima(rows),
        "training_formula": {
            "birth_presentations": {"D1": 1024, "D2": 2048},
            "batch_size": 4, "maximum_sequence_tokens": 16384,
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
    }


def build_ledger() -> dict:
    phases = canonical_phases()
    return {
        "source_status": SOURCE_STATUS, "source_binding": source_binding(),
        "scope": "symbolic per-world CPU phase/resource template only",
        "world_order": ["W0", "W1"], "world_count": 2,
        "gates": {name: False for name in (
            "GO_PREPARE", "GO_MATERIALIZE", "GO_TOKENIZER", "GO_MODEL",
            "GO_FORMATION", "GO_FIT", "GO_GPU", "GO_FIT_OR_GPU", "GO_CLAIM", "GO_RELEASE",
        )},
        "empirical_feasibility_claim": False,
        "predicate_policy": {
            "evaluated": False, "noncompensatory": True,
            "malformed_rejected_stopped": "zero in fixed denominator; no retry or denominator reduction",
            "controller_comparison": "each integer count >= imported BIRTH subset count minus one AND absolute minimum; no ratio rounding",
            "atom_failure": "2/2 in either world stops corresponding stage; no cross-world rescue",
            "raw_role": "diagnostic except interface/custody/feasibility gates",
        },
        "phases": phases, "resources": derive_resources(phases),
        "unimplemented_scope": [
            "scientific material, topology, goals and opaque identifiers",
            "upstream receipt import, raw hashes and controller baseline values",
            "tokenizer, model, learner outputs and predicate evaluation",
            "formation, fits, adapters, GPU execution and resource enforcement",
            "exact padded-token witness and numerical FLOP budget",
            "full TSJ generator, preparation audit and scientific claims",
        ],
    }


def validate_ledger(ledger: dict) -> None:
    if not isinstance(ledger, dict) or "phases" not in ledger:
        raise ValueError("invalid_ledger_schema")
    validate_phases(ledger["phases"])
    try:
        matches = _json(ledger) == _json(build_ledger())
    except (TypeError, ValueError) as error:
        raise ValueError("invalid_ledger_json") from error
    if not matches:
        raise ValueError("noncanonical_ledger")


def canonical_json(ledger: dict | None = None) -> str:
    """Emit an immutable canonical JSON string; no file, model, or scientific IO."""
    if ledger is None:
        ledger = build_ledger()
    else:
        validate_ledger(ledger)
    return _json(ledger)
