"""Adversarial plain tests for the CPU-only cyclic-organism v1 contract."""

from __future__ import annotations

from copy import deepcopy
import hashlib

from .cyclic_organism_contract import (
    PHASES,
    SCHEMA_VERSION,
    ContractError,
    agenda_digest,
    assert_valid_dataset,
    assert_valid_trace,
    compute_metrics,
    concept_semantic_hash,
    derivation_digest,
    edge_semantic_hash,
    experience_payload_hash,
    hypothesis_digest,
    phase_barrier_digest,
    realization_digest,
    realization_state_digest,
    semantic_state_digest,
    sha256_json,
    thinker_state_digest,
    touch_plan_digest,
    validate_dataset,
    validate_trace,
)


_TOP_KIND_ID = {
    "experiences": ("experience", "experience_id"),
    "concepts": ("concept", "concept_id"),
    "semantic_edges": ("semantic_edge", "edge_id"),
    "derivations": ("derivation", "derivation_id"),
    "epistemic_events": ("epistemic_event", "epistemic_event_id"),
    "realization_specs": ("realization_spec", "realization_id"),
    "touch_plans": ("touch_plan", "touch_plan_id"),
    "checkpoints": ("checkpoint", "checkpoint_id"),
    "thinker_states": ("thinker_state", "thinker_state_id"),
    "thinker_hypotheses": ("thinker_hypothesis", "hypothesis_id"),
    "thinker_confusions": ("thinker_confusion", "confusion_id"),
    "thinker_desires": ("thinker_desire", "desire_id"),
    "agendas": ("agenda", "agenda_id"),
}


def _scope(prefix: str = "a") -> dict[str, str]:
    return {
        "world_id": f"world-{prefix}", "skin_id": "aligned",
        "life_id": f"life-{prefix}",
    }


def _barrier_id(prefix: str, round_index: int, phase: str) -> str:
    return f"{prefix}-barrier-r{round_index}-{phase.casefold()}"


def _record_scope(scope: dict[str, str], round_index: int,
                  barrier_id: str) -> dict[str, object]:
    return {**scope, "round_index": round_index, "created_barrier_id": barrier_id}


def _rehash_barriers(trace: dict) -> None:
    refs: dict[str, list[dict[str, str]]] = {}
    for top_key, (kind, id_key) in _TOP_KIND_ID.items():
        for record in trace[top_key]:
            refs.setdefault(record["created_barrier_id"], []).append({
                "kind": kind, "id": record[id_key], "record_hash": sha256_json(record),
            })
    for items in refs.values():
        items.sort(key=lambda item: (item["kind"], item["id"]))
    previous = None
    scope = _scope_from_trace(trace)
    for index, barrier in enumerate(trace["phase_barriers"]):
        barrier["record_refs"] = refs.get(barrier["barrier_id"], [])
        barrier["previous_barrier_hash"] = previous
        barrier["barrier_hash"] = phase_barrier_digest(
            scope, barrier["barrier_index"], barrier["round_index"],
            barrier["phase"], previous, barrier["record_refs"],
        )
        previous = barrier["barrier_hash"]


def _scope_from_trace(trace: dict) -> dict[str, str]:
    return {key: trace[key] for key in ("world_id", "skin_id", "life_id")}


def _premise_identity(kind: str, record: dict) -> dict[str, str]:
    return {
        "kind": kind,
        "identity": record["payload_hash"] if kind == "experience"
        else record["semantic_hash"],
    }


def valid_trace(prefix: str = "a") -> dict:
    scope = _scope(prefix)
    barrier_ids = {
        (round_index, phase): _barrier_id(prefix, round_index, phase)
        for round_index in range(2) for phase in PHASES
    }

    exp0 = {
        **_record_scope(scope, 0, barrier_ids[(0, "EXPERIENCE")]),
        "experience_id": f"{prefix}-exp-route", "sequence_index": 0,
        "action": "inspect copper valve", "observation": "copper routes Candyland",
        "outcome": "route witnessed",
    }
    exp0["payload_hash"] = experience_payload_hash(
        exp0["action"], exp0["observation"], exp0["outcome"],
    )
    exp1 = {
        **_record_scope(scope, 1, barrier_ids[(1, "EXPERIENCE")]),
        "experience_id": f"{prefix}-exp-change", "sequence_index": 1,
        "action": "close copper valve",
        "observation": "Confluenceland changes while copper is closed",
        "outcome": "change witnessed",
    }
    exp1["payload_hash"] = experience_payload_hash(
        exp1["action"], exp1["observation"], exp1["outcome"],
    )

    def concept(round_index: int, step: int, suffix: str, key: str,
                label: str, derivation_id: str) -> dict:
        return {
            **_record_scope(scope, round_index, barrier_ids[(round_index, "DREAM")]),
            "concept_id": f"{prefix}-concept-{suffix}", "step_index": step,
            "canonical_key": key, "display_label": label,
            "semantic_hash": concept_semantic_hash(key),
            "derivation_id": derivation_id, "initial_status": "provisional",
        }

    c_valve = concept(0, 0, "valve", "valve:copper", "copper valve", f"{prefix}-der-valve")
    c_source = concept(0, 1, "source", "land:candy", "Candyland", f"{prefix}-der-source")
    e_route = {
        **_record_scope(scope, 0, barrier_ids[(0, "DREAM")]),
        "edge_id": f"{prefix}-edge-route", "step_index": 2,
        "source_concept_id": c_valve["concept_id"], "relation": "routes",
        "target_concept_id": c_source["concept_id"],
        "semantic_hash": edge_semantic_hash(
            c_valve["semantic_hash"], "routes", c_source["semantic_hash"],
        ),
        "derivation_id": f"{prefix}-der-route", "initial_status": "provisional",
    }
    c_target = concept(
        1, 0, "target", "land:confluence", "Confluenceland", f"{prefix}-der-target",
    )
    e_change = {
        **_record_scope(scope, 1, barrier_ids[(1, "DREAM")]),
        "edge_id": f"{prefix}-edge-change", "step_index": 1,
        "source_concept_id": c_valve["concept_id"], "relation": "changes",
        "target_concept_id": c_target["concept_id"],
        "semantic_hash": edge_semantic_hash(
            c_valve["semantic_hash"], "changes", c_target["semantic_hash"],
        ),
        "derivation_id": f"{prefix}-der-change", "initial_status": "provisional",
    }
    semantics = {
        item_id: item for item_id, item in (
            (c_valve["concept_id"], c_valve), (c_source["concept_id"], c_source),
            (e_route["edge_id"], e_route), (c_target["concept_id"], c_target),
            (e_change["edge_id"], e_change),
        )
    }
    experiences = {exp0["experience_id"]: exp0, exp1["experience_id"]: exp1}

    def derivation(round_index: int, step: int, derivation_id: str,
                   conclusion_kind: str, conclusion_id: str,
                   premises: list[tuple[str, str]], depth: int,
                   guidance: list[str] | None = None) -> dict:
        premise_refs = [{"kind": kind, "id": item_id} for kind, item_id in premises]
        identities = [
            _premise_identity(
                kind, experiences[item_id] if kind == "experience" else semantics[item_id],
            )
            for kind, item_id in premises
        ]
        return {
            **_record_scope(scope, round_index, barrier_ids[(round_index, "DREAM")]),
            "derivation_id": derivation_id, "step_index": step,
            "rule": "local associative extension", "conclusion_kind": conclusion_kind,
            "conclusion_id": conclusion_id, "premise_refs": premise_refs,
            "guidance_agenda_ids": list(guidance or []), "declared_depth": depth,
            "derivation_hash": derivation_digest(
                "local associative extension", semantics[conclusion_id]["semantic_hash"],
                identities,
            ),
        }

    derivations = [
        derivation(0, 0, c_valve["derivation_id"], "concept", c_valve["concept_id"],
                   [("experience", exp0["experience_id"])], 1),
        derivation(0, 1, c_source["derivation_id"], "concept", c_source["concept_id"],
                   [("experience", exp0["experience_id"])], 1),
        derivation(0, 2, e_route["derivation_id"], "semantic_edge", e_route["edge_id"],
                   [("experience", exp0["experience_id"]),
                    ("concept", c_valve["concept_id"]),
                    ("concept", c_source["concept_id"])], 2),
        derivation(1, 0, c_target["derivation_id"], "concept", c_target["concept_id"],
                   [("experience", exp1["experience_id"])], 1,
                   [f"{prefix}-agenda-r0"]),
        derivation(1, 1, e_change["derivation_id"], "semantic_edge", e_change["edge_id"],
                   [("experience", exp1["experience_id"]),
                    ("concept", c_valve["concept_id"]),
                    ("concept", c_target["concept_id"]),
                    ("semantic_edge", e_route["edge_id"])], 3,
                   [f"{prefix}-agenda-r0"]),
    ]

    epistemic_events = []
    for semantic in (c_valve, c_source, e_route, c_target, e_change):
        kind = "semantic_edge" if "edge_id" in semantic else "concept"
        subject_id = semantic.get("edge_id", semantic.get("concept_id"))
        stem = subject_id.replace(f"{prefix}-", "")
        common = _record_scope(
            scope, semantic["round_index"], semantic["created_barrier_id"],
        )
        epistemic_events.extend([
            {
                **common, "epistemic_event_id": f"{prefix}-event-{stem}-create",
                "step_index": semantic["step_index"], "event_kind": "CREATE",
                "subject_kind": kind, "subject_id": subject_id,
                "previous_status": None, "new_status": "provisional",
                "evidence_derivation_id": semantic["derivation_id"],
                "replacement_subject_id": None,
            },
            {
                **common, "epistemic_event_id": f"{prefix}-event-{stem}-support",
                "step_index": semantic["step_index"], "event_kind": "SUPPORT",
                "subject_kind": kind, "subject_id": subject_id,
                "previous_status": "provisional", "new_status": "supported",
                "evidence_derivation_id": semantic["derivation_id"],
                "replacement_subject_id": None,
            },
        ])

    realization_specs = []
    touch_plans = []
    ordered_semantics = (c_valve, c_source, e_route, c_target, e_change)
    for order_index, semantic in enumerate(ordered_semantics):
        round_index = semantic["round_index"]
        source_kind = "semantic_edge" if "edge_id" in semantic else "concept"
        source_id = semantic.get("edge_id", semantic.get("concept_id"))
        realization_id = f"{prefix}-real-{source_id.removeprefix(prefix + '-')}"
        cue = f"What durable item is bound to {source_id}?"
        target = semantic.get("display_label", semantic.get("relation"))
        realization = {
            **_record_scope(scope, round_index, barrier_ids[(round_index, "REALIZE")]),
            "realization_id": realization_id, "source_kind": source_kind,
            "source_id": source_id, "source_semantic_hash": semantic["semantic_hash"],
            "form": "qa", "cue_text": cue, "target_text": target,
            "realization_hash": realization_digest(
                semantic["semantic_hash"], "qa", cue, target,
            ),
        }
        plan_id = f"{prefix}-touch-{source_id.removeprefix(prefix + '-')}"
        plan = {
            **_record_scope(scope, round_index, barrier_ids[(round_index, "REALIZE")]),
            "touch_plan_id": plan_id, "realization_id": realization_id,
            "touches": 24, "weight": 1.0, "order_index": order_index,
            "plan_hash": touch_plan_digest(realization_id, 24, 1.0, order_index),
        }
        realization_specs.append(realization)
        touch_plans.append(plan)

    depth_by_id = {
        c_valve["concept_id"]: 1, c_source["concept_id"]: 1,
        e_route["edge_id"]: 2, c_target["concept_id"]: 1,
        e_change["edge_id"]: 3,
    }
    checkpoints = []
    previous_checkpoint_id = None
    for round_index in range(2):
        checkpoint_id = f"{prefix}-checkpoint-r{round_index}"
        included = sorted(
            item_id for item_id, item in semantics.items()
            if item["round_index"] <= round_index
        )
        round_realizations = sorted(
            (item for item in realization_specs if item["round_index"] <= round_index),
            key=lambda item: item["realization_id"],
        )
        round_plans = sorted(
            (item for item in touch_plans if item["round_index"] <= round_index),
            key=lambda item: item["touch_plan_id"],
        )
        semantic_payload = [
            {"id": item_id, "semantic_hash": semantics[item_id]["semantic_hash"],
             "status": "supported", "derivation_depth": depth_by_id[item_id]}
            for item_id in included
        ]
        checkpoint = {
            **_record_scope(scope, round_index, barrier_ids[(round_index, "CHECKPOINT")]),
            "checkpoint_id": checkpoint_id,
            "memory_adapter_id": f"{prefix}-memory-adapter",
            "previous_checkpoint_id": previous_checkpoint_id,
            "included_semantic_ids": included,
            "realization_ids": [item["realization_id"] for item in round_realizations],
            "touch_plan_ids": [item["touch_plan_id"] for item in round_plans],
            "semantic_state_hash": semantic_state_digest(semantic_payload),
            "realization_state_hash": realization_state_digest(
                round_realizations, round_plans,
            ),
            "adapter_artifact_hash": hashlib.sha256(
                f"adapter:{prefix}:{round_index}".encode("utf-8")
            ).hexdigest(),
        }
        checkpoints.append(checkpoint)
        previous_checkpoint_id = checkpoint_id

    state0 = {
        **_record_scope(scope, 0, barrier_ids[(0, "THINK")]),
        "thinker_state_id": f"{prefix}-think-r0", "step_index": 0,
        "checkpoint_id": checkpoints[0]["checkpoint_id"], "parent_state_id": None,
        "goal": "Predict the counterfactual after closing copper",
        "retrieved_semantic_ids": [e_route["edge_id"]],
        "workspace": ["copper routes Candyland"],
        "query_registry": [{
            "query_key": "target_effect", "subject_entity_id": c_valve["concept_id"],
            "relation_id": "changes",
        }],
    }
    state0["state_hash"] = thinker_state_digest(
        state0["checkpoint_id"], None, state0["goal"],
        state0["retrieved_semantic_ids"], state0["workspace"], state0["query_registry"],
    )
    state1 = {
        **_record_scope(scope, 1, barrier_ids[(1, "THINK")]),
        "thinker_state_id": f"{prefix}-think-r1", "step_index": 0,
        "checkpoint_id": checkpoints[1]["checkpoint_id"], "parent_state_id": None,
        "goal": state0["goal"],
        "retrieved_semantic_ids": [e_route["edge_id"], e_change["edge_id"]],
        "workspace": ["copper routes Candyland", "copper changes Confluenceland"],
        "query_registry": [],
    }
    state1["state_hash"] = thinker_state_digest(
        state1["checkpoint_id"], None, state1["goal"],
        state1["retrieved_semantic_ids"], state1["workspace"], state1["query_registry"],
    )
    hypothesis0 = {
        **_record_scope(scope, 0, barrier_ids[(0, "THINK")]),
        "hypothesis_id": f"{prefix}-hyp-r0", "step_index": 1,
        "thinker_state_id": state0["thinker_state_id"],
        "parent_hypothesis_ids": [],
        "claim": "Candyland may matter, but the target effect is unknown",
        "cited_semantic_ids": [e_route["edge_id"]],
        "release_support_semantic_ids": [], "confidence": 0.4,
        "disposition": "deferred",
    }
    hypothesis0["hypothesis_hash"] = hypothesis_digest(
        hypothesis0["thinker_state_id"], hypothesis0["claim"],
        hypothesis0["cited_semantic_ids"], hypothesis0["confidence"],
        hypothesis0["disposition"],
    )
    hypothesis1 = {
        **_record_scope(scope, 1, barrier_ids[(1, "THINK")]),
        "hypothesis_id": f"{prefix}-hyp-r1", "step_index": 1,
        "thinker_state_id": state1["thinker_state_id"],
        "parent_hypothesis_ids": [],
        "claim": "Closing copper removes Candyland's contribution from Confluenceland",
        "cited_semantic_ids": [e_route["edge_id"], e_change["edge_id"]],
        "release_support_semantic_ids": [e_route["edge_id"], e_change["edge_id"]],
        "confidence": 0.8, "disposition": "released",
    }
    hypothesis1["hypothesis_hash"] = hypothesis_digest(
        hypothesis1["thinker_state_id"], hypothesis1["claim"],
        hypothesis1["cited_semantic_ids"], hypothesis1["confidence"],
        hypothesis1["disposition"], (), hypothesis1["release_support_semantic_ids"],
    )
    confusion0 = {
        **_record_scope(scope, 0, barrier_ids[(0, "THINK")]),
        "confusion_id": f"{prefix}-conf-r0", "step_index": 2,
        "thinker_state_id": state0["thinker_state_id"],
        "query_key": "target_effect", "subject_entity_id": c_valve["concept_id"],
        "relation_id": "changes", "unknown_slot": "object",
    }
    desires = []
    agendas = []
    desire_id = f"{prefix}-desire-r0"
    desire = {
        **_record_scope(scope, 0, barrier_ids[(0, "FEEDBACK")]),
        "desire_id": desire_id, "source_confusion_id": confusion0["confusion_id"],
        "query_key": confusion0["query_key"],
        "subject_entity_id": confusion0["subject_entity_id"],
        "relation_id": confusion0["relation_id"], "unknown_slot": "object",
        "checkpoint_id": checkpoints[0]["checkpoint_id"],
        "checkpoint_semantic_state_hash": checkpoints[0]["semantic_state_hash"],
        "thinker_state_hash": state0["state_hash"],
        "priority": 1, "non_evidentiary": True,
    }
    desires.append(desire)
    for round_index, state, desire_rows in (
        (0, state0, [desire]),
        (1, state1, []),
    ):
        desire_ids = [item["desire_id"] for item in desire_rows]
        query_keys = [item["query_key"] for item in desire_rows]
        agenda = {
            **_record_scope(scope, round_index, barrier_ids[(round_index, "FEEDBACK")]),
            "agenda_id": f"{prefix}-agenda-r{round_index}",
            "checkpoint_id": checkpoints[round_index]["checkpoint_id"],
            "checkpoint_semantic_state_hash": checkpoints[round_index]["semantic_state_hash"],
            "thinker_state_hash": state["state_hash"],
            "desire_ids": desire_ids, "priority_query_keys": query_keys,
            "non_evidentiary": True,
        }
        agenda["agenda_hash"] = agenda_digest(
            agenda["checkpoint_id"], agenda["checkpoint_semantic_state_hash"],
            agenda["thinker_state_hash"], agenda["desire_ids"],
            agenda["priority_query_keys"],
        )
        agendas.append(agenda)

    barriers = []
    for index in range(2 * len(PHASES)):
        round_index, phase_offset = divmod(index, len(PHASES))
        barriers.append({
            **scope, "barrier_id": barrier_ids[(round_index, PHASES[phase_offset])],
            "barrier_index": index, "round_index": round_index,
            "phase": PHASES[phase_offset], "previous_barrier_hash": None,
            "record_refs": [], "barrier_hash": "0" * 64,
        })

    trace = {
        "schema_version": SCHEMA_VERSION, "trace_id": f"{prefix}-trace", **scope,
        "split": "dev", "round_count": 2,
        "memory_adapter_id": f"{prefix}-memory-adapter",
        "experiences": [exp0, exp1],
        "concepts": [c_valve, c_source, c_target],
        "semantic_edges": [e_route, e_change],
        "derivations": derivations,
        "epistemic_events": epistemic_events,
        "realization_specs": realization_specs,
        "touch_plans": touch_plans,
        "checkpoints": checkpoints,
        "thinker_states": [state0, state1],
        "thinker_hypotheses": [hypothesis0, hypothesis1],
        "thinker_confusions": [confusion0],
        "thinker_desires": desires,
        "agendas": agendas,
        "phase_barriers": barriers,
    }
    _rehash_barriers(trace)
    return trace


def _assert_invalid(trace: dict, fragment: str) -> None:
    errors = validate_trace(trace)
    assert errors, "adversarial trace unexpectedly passed"
    assert any(fragment in error for error in errors), "\n".join(errors)
    try:
        assert_valid_trace(trace)
    except ContractError:
        pass
    else:
        raise AssertionError("assert_valid_trace accepted an invalid trace")


def _add_target_reinforcement(trace: dict, *, derivation_id: str,
                              experience_id: str, rule: str,
                              new_experience: bool) -> None:
    """Append one later derivation of the existing target concept."""
    scope = _scope_from_trace(trace)
    if new_experience:
        experience = {
            **_record_scope(scope, 1, _barrier_id(scope["life_id"].removeprefix("life-"),
                                                  1, "EXPERIENCE")),
            "experience_id": experience_id,
            "sequence_index": max(item["sequence_index"] for item in trace["experiences"]) + 1,
            "action": "inspect independent target telemetry",
            "observation": "Confluenceland independently responds to copper",
            "outcome": "independent response witnessed",
        }
        experience["payload_hash"] = experience_payload_hash(
            experience["action"], experience["observation"], experience["outcome"],
        )
        trace["experiences"].append(experience)
    else:
        experience = next(
            item for item in trace["experiences"] if item["experience_id"] == experience_id
        )
    target = next(
        item for item in trace["concepts"] if item["concept_id"].endswith("concept-target")
    )
    prefix = scope["life_id"].removeprefix("life-")
    derivation = {
        **_record_scope(scope, 1, _barrier_id(prefix, 1, "DREAM")),
        "derivation_id": derivation_id, "step_index": 2, "rule": rule,
        "conclusion_kind": "concept", "conclusion_id": target["concept_id"],
        "premise_refs": [{"kind": "experience", "id": experience_id}],
        "guidance_agenda_ids": [f"{prefix}-agenda-r0"], "declared_depth": 1,
        "derivation_hash": derivation_digest(
            rule, target["semantic_hash"],
            [{"kind": "experience", "identity": experience["payload_hash"]}],
        ),
    }
    support = {
        **_record_scope(scope, 1, _barrier_id(prefix, 1, "DREAM")),
        "epistemic_event_id": f"{derivation_id}-support", "step_index": 2,
        "event_kind": "SUPPORT", "subject_kind": "concept",
        "subject_id": target["concept_id"], "previous_status": "supported",
        "new_status": "supported", "evidence_derivation_id": derivation_id,
        "replacement_subject_id": None,
    }
    trace["derivations"].append(derivation)
    trace["epistemic_events"].append(support)
    _rehash_barriers(trace)


def test_valid_two_round_cyclic_trace_and_separate_metrics():
    trace = valid_trace()
    assert validate_trace(trace) == []
    assert_valid_trace(trace)
    metrics = compute_metrics(trace)
    assert metrics["structure"] == {
        "concept_count": 3, "edge_count": 2, "unique_semantic_hashes": 5,
        "component_count": 1, "max_shortest_path": 2,
    }
    assert metrics["derivation"]["max_depth"] == 3
    assert metrics["realization"]["spec_count"] == 5
    assert metrics["thinker"]["confusion_count"] == 1


def test_named_growth_metrics_have_conservative_auditable_semantics():
    metrics = compute_metrics(valid_trace())
    assert metrics["derivation_lineage_depth"] == 3
    assert metrics["supported_derivation_depth"] == 3
    assert metrics["semantic_structural_hops"] == 2
    assert metrics["independent_support_depth"] == 1
    assert metrics["thinker_compositional_depth"] == 3  # two edges + one hypothesis
    assert metrics["realization_count"] == 5


def test_thinker_compositional_depth_counts_typed_released_lineage_only():
    trace = valid_trace()
    released = trace["thinker_hypotheses"][1]
    scratch = {
        **_record_scope(_scope_from_trace(trace), 1, _barrier_id("a", 1, "THINK")),
        "hypothesis_id": "a-hyp-r1-scratch", "step_index": 1,
        "thinker_state_id": released["thinker_state_id"],
        "parent_hypothesis_ids": [],
        "claim": "Copper and Candyland may be the relevant branch",
        "cited_semantic_ids": ["a-edge-route"],
        "release_support_semantic_ids": [], "confidence": 0.6,
        "disposition": "tentative",
    }
    scratch["hypothesis_hash"] = hypothesis_digest(
        scratch["thinker_state_id"], scratch["claim"], scratch["cited_semantic_ids"],
        scratch["confidence"], scratch["disposition"], scratch["parent_hypothesis_ids"],
    )
    released["step_index"] = 2
    released["parent_hypothesis_ids"] = [scratch["hypothesis_id"]]
    released["hypothesis_hash"] = hypothesis_digest(
        released["thinker_state_id"], released["claim"], released["cited_semantic_ids"],
        released["confidence"], released["disposition"],
        released["parent_hypothesis_ids"], released["release_support_semantic_ids"],
    )
    trace["thinker_hypotheses"].append(scratch)
    _rehash_barriers(trace)
    assert_valid_trace(trace)
    metrics = compute_metrics(trace)
    assert metrics["thinker_compositional_depth"] == 4  # two edges + two hypotheses
    assert metrics["semantic_structural_hops"] == 2
    assert metrics["independent_support_depth"] == 1


def test_independent_evidence_reinforces_without_adding_semantic_nodes():
    trace = valid_trace()
    before = compute_metrics(trace)
    _add_target_reinforcement(
        trace, derivation_id="a-der-target-independent",
        experience_id="a-exp-target-independent",
        rule="independent target observation", new_experience=True,
    )
    assert_valid_trace(trace)
    after = compute_metrics(trace)
    assert after["structure"] == before["structure"]
    assert len(trace["concepts"]) == 3
    assert len(trace["semantic_edges"]) == 2
    assert len(trace["derivations"]) == len(valid_trace()["derivations"]) + 1
    assert after["independent_support_depth"] == 2
    assert after["derivation_lineage_depth"] == before["derivation_lineage_depth"]
    assert after["realization_count"] == before["realization_count"]


def test_repeated_same_evidence_cannot_inflate_independent_support():
    trace = valid_trace()
    _add_target_reinforcement(
        trace, derivation_id="a-der-target-reworded",
        experience_id="a-exp-change", rule="reworded same observation",
        new_experience=False,
    )
    _assert_invalid(trace, "repeated evidence identity cannot add independent support")


def test_thinker_answer_cannot_be_laundered_as_dream_evidence():
    trace = valid_trace()
    derivation = trace["derivations"][-1]
    derivation["premise_refs"].append({
        "kind": "thinker_hypothesis", "id": "a-hyp-r0",
    })
    _rehash_barriers(trace)
    _assert_invalid(trace, "non-evidentiary")


def test_agenda_can_guide_but_cannot_support_a_derivation():
    trace = valid_trace()
    derivation = trace["derivations"][-1]
    derivation["premise_refs"] = [{"kind": "agenda", "id": "a-agenda-r0"}]
    _rehash_barriers(trace)
    _assert_invalid(trace, "non-evidentiary")


def test_realization_cannot_be_cited_as_evidence():
    trace = valid_trace()
    derivation = trace["derivations"][-1]
    derivation["premise_refs"].append({
        "kind": "realization_spec", "id": trace["realization_specs"][0]["realization_id"],
    })
    _rehash_barriers(trace)
    _assert_invalid(trace, "non-evidentiary")


def test_unknown_answer_key_field_is_rejected_instead_of_laundered():
    trace = valid_trace()
    trace["realization_specs"][0]["hidden_answer"] = "yellow-green"
    _rehash_barriers(trace)
    _assert_invalid(trace, "forbidden or unknown field hidden_answer")


def test_future_semantic_citation_is_rejected():
    trace = valid_trace()
    first_edge_derivation = trace["derivations"][2]
    first_edge_derivation["premise_refs"].append({
        "kind": "semantic_edge", "id": "a-edge-change",
    })
    _rehash_barriers(trace)
    _assert_invalid(trace, "future or same-step semantic citation")


def test_cross_life_citation_is_rejected():
    trace = valid_trace()
    trace["derivations"][-1]["premise_refs"][0] = {
        "kind": "experience", "id": "foreign-life-experience",
    }
    _rehash_barriers(trace)
    _assert_invalid(trace, "missing or cross-life premise")


def test_cross_life_memory_adapter_reuse_is_rejected():
    first = valid_trace("a")
    second = valid_trace("b")
    second["memory_adapter_id"] = first["memory_adapter_id"]
    for checkpoint in second["checkpoints"]:
        checkpoint["memory_adapter_id"] = first["memory_adapter_id"]
    _rehash_barriers(second)
    dataset = {"schema_version": SCHEMA_VERSION, "dataset_id": "ds", "traces": [first, second]}
    errors = validate_dataset(dataset)
    assert any("memory adapter reused across lives" in error for error in errors)


def test_dataset_accepts_isolated_lives():
    dataset = {
        "schema_version": SCHEMA_VERSION, "dataset_id": "ds",
        "traces": [valid_trace("a"), valid_trace("b")],
    }
    assert validate_dataset(dataset) == []
    assert_valid_dataset(dataset)


def test_paraphrase_cannot_masquerade_as_a_new_semantic_node():
    trace = valid_trace()
    duplicate = deepcopy(trace["concepts"][0])
    duplicate["concept_id"] = "a-concept-valve-paraphrase"
    duplicate["display_label"] = "the copper-colored control valve"
    duplicate["derivation_id"] = "a-der-valve-paraphrase"
    trace["concepts"].append(duplicate)
    _rehash_barriers(trace)
    _assert_invalid(trace, "duplicate semantic hashes")


def test_declared_derivation_depth_cannot_be_inflated():
    trace = valid_trace()
    trace["derivations"][-1]["declared_depth"] = 99
    _rehash_barriers(trace)
    _assert_invalid(trace, "derived value is 3")


def test_hub_walks_do_not_inflate_structural_depth():
    # The valid fixture is a two-leaf star around the valve concept.  There are
    # arbitrarily many cyclic walks through that hub, but the graph metric is
    # the finite shortest-path diameter, not a walk count or prose claim.
    metrics = compute_metrics(valid_trace())
    assert metrics["structure"]["edge_count"] == 2
    assert metrics["structure"]["max_shortest_path"] == 2
    assert metrics["derivation"]["max_depth"] == 3


def test_claimed_structural_depth_field_is_rejected():
    trace = valid_trace()
    trace["semantic_edges"][0]["structural_depth"] = 400
    _rehash_barriers(trace)
    _assert_invalid(trace, "forbidden or unknown field structural_depth")


def test_realization_cannot_masquerade_as_a_semantic_node():
    trace = valid_trace()
    realization = trace["realization_specs"][0]
    realization["creates_semantic_id"] = "fabricated-node"
    realization["declared_depth"] = 100
    _rehash_barriers(trace)
    _assert_invalid(trace, "forbidden or unknown field creates_semantic_id")


def test_realization_variation_changes_write_metrics_not_graph_or_depth():
    before = valid_trace()
    after = deepcopy(before)
    realization = after["realization_specs"][0]
    realization["form"] = "paraphrase"
    realization["cue_text"] = "Recall the same item in another surface form."
    realization["target_text"] = "The copper control is the same valve."
    realization["realization_hash"] = realization_digest(
        realization["source_semantic_hash"], realization["form"],
        realization["cue_text"], realization["target_text"],
    )
    for checkpoint in after["checkpoints"]:
        round_index = checkpoint["round_index"]
        realizations = sorted(
            (item for item in after["realization_specs"] if item["round_index"] <= round_index),
            key=lambda item: item["realization_id"],
        )
        plans = sorted(
            (item for item in after["touch_plans"] if item["round_index"] <= round_index),
            key=lambda item: item["touch_plan_id"],
        )
        checkpoint["realization_state_hash"] = realization_state_digest(realizations, plans)
    _rehash_barriers(after)
    assert_valid_trace(after)
    before_metrics = compute_metrics(before)
    after_metrics = compute_metrics(after)
    assert after_metrics["structure"] == before_metrics["structure"]
    assert after_metrics["derivation"] == before_metrics["derivation"]
    assert after_metrics["independent_support_depth"] == before_metrics[
        "independent_support_depth"
    ]
    assert after_metrics["thinker_compositional_depth"] == before_metrics[
        "thinker_compositional_depth"
    ]
    assert after_metrics["realization"]["forms"] != before_metrics["realization"]["forms"]


def test_phase_order_mutation_is_rejected_even_with_rehashed_chain():
    trace = valid_trace()
    barrier = trace["phase_barriers"][2]
    barrier["phase"] = "DREAM"
    _rehash_barriers(trace)
    _assert_invalid(trace, "immutable order requires REALIZE")


def test_record_cannot_move_across_phase_barrier():
    trace = valid_trace()
    trace["realization_specs"][0]["created_barrier_id"] = _barrier_id("a", 0, "DREAM")
    _rehash_barriers(trace)
    _assert_invalid(trace, "record committed in wrong phase")


def test_barrier_manifest_omission_is_rejected():
    trace = valid_trace()
    trace["phase_barriers"][1]["record_refs"].pop()
    # Do not repair the manifest: this is the exact artifact omission attack.
    _assert_invalid(trace, "not an exact manifest")


def test_semantic_hash_tampering_is_rejected():
    trace = valid_trace()
    trace["semantic_edges"][0]["semantic_hash"] = "0" * 64
    _rehash_barriers(trace)
    _assert_invalid(trace, "canonical identity mismatch")


def test_support_event_cannot_launder_an_unrelated_derivation():
    trace = valid_trace()
    change_support = next(
        item for item in trace["epistemic_events"]
        if item["subject_id"] == "a-edge-change" and item["event_kind"] == "SUPPORT"
    )
    change_support["evidence_derivation_id"] = "a-der-route"
    _rehash_barriers(trace)
    _assert_invalid(trace, "evidence derivation does not bind subject")


def test_checkpoint_cannot_include_unrealized_future_semantics():
    trace = valid_trace()
    trace["checkpoints"][0]["included_semantic_ids"].append("a-edge-change")
    trace["checkpoints"][0]["included_semantic_ids"].sort()
    _rehash_barriers(trace)
    _assert_invalid(trace, "semantic manifest is not exact live state")


def test_thinker_cannot_retrieve_outside_its_checkpoint():
    trace = valid_trace()
    state = trace["thinker_states"][0]
    state["retrieved_semantic_ids"].append("a-edge-change")
    state["state_hash"] = thinker_state_digest(
        state["checkpoint_id"], state["parent_state_id"], state["goal"],
        state["retrieved_semantic_ids"], state["workspace"], state["query_registry"],
    )
    _rehash_barriers(trace)
    _assert_invalid(trace, "retrieves outside checkpoint")


def test_thinker_hypothesis_must_cite_retrieved_memory():
    trace = valid_trace()
    hypothesis = trace["thinker_hypotheses"][0]
    hypothesis["cited_semantic_ids"] = ["a-concept-valve"]
    hypothesis["hypothesis_hash"] = hypothesis_digest(
        hypothesis["thinker_state_id"], hypothesis["claim"],
        hypothesis["cited_semantic_ids"], hypothesis["confidence"],
        hypothesis["disposition"],
    )
    _rehash_barriers(trace)
    _assert_invalid(trace, "cites memory not retrieved")


def test_non_evidentiary_flags_cannot_be_mutated():
    trace = valid_trace()
    trace["thinker_desires"][0]["non_evidentiary"] = False
    trace["agendas"][0]["non_evidentiary"] = False
    _rehash_barriers(trace)
    _assert_invalid(trace, "must remain non-evidentiary")


def test_desire_cannot_substitute_free_text_or_a_different_typed_query():
    trace = valid_trace()
    desire = trace["thinker_desires"][0]
    desire["query_key"] = "answer_is_red"
    trace["agendas"][0]["priority_query_keys"] = ["answer_is_red"]
    agenda = trace["agendas"][0]
    agenda["agenda_hash"] = agenda_digest(
        agenda["checkpoint_id"], agenda["checkpoint_semantic_state_hash"],
        agenda["thinker_state_hash"], agenda["desire_ids"],
        agenda["priority_query_keys"],
    )
    _rehash_barriers(trace)
    _assert_invalid(trace, "not a mechanical confusion projection")


def test_agenda_priority_keys_are_derived_exactly_from_desires():
    trace = valid_trace()
    agenda = trace["agendas"][0]
    agenda["priority_query_keys"] = ["answer_is_red"]
    agenda["agenda_hash"] = agenda_digest(
        agenda["checkpoint_id"], agenda["checkpoint_semantic_state_hash"],
        agenda["thinker_state_hash"], agenda["desire_ids"],
        agenda["priority_query_keys"],
    )
    _rehash_barriers(trace)
    _assert_invalid(trace, "priority keys are not mechanical")


def test_feedback_must_bind_exact_round_checkpoint_and_thinker_state():
    trace = valid_trace()
    agenda = trace["agendas"][0]
    agenda["checkpoint_id"] = trace["checkpoints"][1]["checkpoint_id"]
    agenda["checkpoint_semantic_state_hash"] = trace["checkpoints"][1]["semantic_state_hash"]
    agenda["agenda_hash"] = agenda_digest(
        agenda["checkpoint_id"], agenda["checkpoint_semantic_state_hash"],
        agenda["thinker_state_hash"], agenda["desire_ids"],
        agenda["priority_query_keys"],
    )
    _rehash_barriers(trace)
    _assert_invalid(trace, "stale checkpoint/state binding")


def test_feedback_guidance_must_come_from_an_earlier_round():
    trace = valid_trace()
    trace["derivations"][0]["guidance_agenda_ids"] = ["a-agenda-r0"]
    _rehash_barriers(trace)
    _assert_invalid(trace, "guidance must precede dream")
