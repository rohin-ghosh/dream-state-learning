"""Fail-closed scientific thinker bridge for the recurrent organism.

This module owns the hardened :class:`ThinkerMachine` execution loop.  A
policy may propose exactly one serialized operation at a time, but it cannot
return a completed thinker result or agenda.  The machine artifact and its
model-call ledger are authoritative; the compact ``ThinkerResult`` is only a
deterministic projection used by the cyclic scheduler.

The v0.3-R compiler consumes only a public ``precheckpoint_export`` and an
exact committed semantic checkpoint.  It never receives a world object,
oracle, latent bit, final answer, answer valve, or prescribed operation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Any, Mapping, Protocol

from .goal_conditioned_thinker import (
    ThinkerContractError,
    ThinkerMachine,
    canonical_json,
    freeze_checkpoint,
    parse_operation,
)
from .model_call_ledger import (
    ABSENT_HASH,
    CallMaterials,
    DecodingConfig,
    ImmutableModelCallLedger,
    TokenAccounting,
    build_record,
    record_to_mapping,
)
from .recurrent_text_organism import (
    AgendaQueryTemplate,
    AgendaVocabulary,
    FrozenCheckpointView,
    PremiseIdentity,
    PublicLife,
    SchedulerError,
    SemanticDecision,
    ScientificGoalCompilerProtocol,
    ScientificThinkerExecution,
    SCIENTIFIC_CAUSAL_JOIN_RELATION,
    ThinkerRequest,
    compile_trusted_scientific_inputs,
    project_replayed_thinker_result,
    sha256_json,
)


CAUSAL_JOIN_RELATION = SCIENTIFIC_CAUSAL_JOIN_RELATION
OWN_QUERY_KEY = "q:causal-join:own"
DISTRACTOR_QUERY_KEY = "q:causal-join:matched-distractor"
THINKER_PROMPT_TEMPLATE = (
    "Return exactly one JSON thinker operation for the supplied typed state."
)


@dataclass(frozen=True)
class PolicyEmission:
    """One future model response plus immutable inference metadata."""

    raw_output: str
    provider: str
    model_id: str
    model_revision: str
    input_tokens: int
    output_tokens: int
    seed: int


class OperationPolicyProtocol(Protocol):
    condition_label: str
    execution_kind: str
    objective_binding: str

    def propose(
        self, public_state: Mapping[str, Any], request: ThinkerRequest,
    ) -> PolicyEmission: ...


def _exact_public_probe(public_export: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(public_export, Mapping):
        raise SchedulerError("v0.3-R public export must be an object")
    allowed_top = {"schema_version", "skin", "episodes", "operational_probe"}
    if set(public_export) != allowed_top:
        raise SchedulerError("v0.3-R public export has hidden or unknown top-level fields")
    probe = public_export.get("operational_probe")
    required = {
        "probe_id", "source_entity_id", "target_entity_id", "question",
        "matched_distractor_source_entity_id",
        "matched_distractor_target_entity_id",
    }
    if not isinstance(probe, Mapping) or set(probe) != required:
        raise SchedulerError("v0.3-R public operational probe must use the exact schema")
    result = {key: str(probe[key]) for key in sorted(required)}
    raw = canonical_json(result).casefold()
    for forbidden in (
        "answer_valve", "next_operation", "latent_bit", "final_answer",
        "ground_truth", "change", "stable", "subtract_source_contribution",
        "keep_passive_baseline",
    ):
        if forbidden in raw:
            raise SchedulerError("public operational compiler received an answer-bearing probe")
    if result["probe_id"] == "" or result["source_entity_id"] == "" \
            or result["target_entity_id"] == "":
        raise SchedulerError("public operational probe has an empty typed endpoint")
    return result


class V03RPublicAgendaCompiler:
    """Compile answer-blind own/wrong query registries after checkpoint freeze."""

    compiler_id = "v03r-public-operational-vocabulary-v1"

    def __init__(
        self, public_exports_by_life: Mapping[str, Mapping[str, Any]],
        *, visible_aliases: Mapping[str, str] | None = None,
    ):
        self._exports = {}
        for life_id, export in public_exports_by_life.items():
            copied = deepcopy(dict(export))
            self._exports[str(life_id)] = copied
            if visible_aliases is not None and str(life_id) in visible_aliases:
                alias = str(visible_aliases[str(life_id)])
                existing = self._exports.get(alias)
                if existing is not None and _exact_public_probe(existing) != \
                        _exact_public_probe(copied):
                    raise SchedulerError(
                        "one model-visible life alias maps to unequal public probes"
                    )
                if existing is None:
                    self._exports[alias] = copied
        self._probe_hashes = {
            life_id: sha256_json(_exact_public_probe(export))
            for life_id, export in self._exports.items()
        }

    def _probe(self, life_id: str) -> dict[str, str]:
        export = self._exports.get(life_id)
        if export is None:
            raise SchedulerError("public compiler has no export for this opaque life")
        return _exact_public_probe(export)

    def compile(
        self, life: PublicLife, checkpoint: FrozenCheckpointView, goal_id: str,
    ) -> AgendaVocabulary | None:
        probe = self._probe(life.logical_life_id)
        if goal_id != probe["probe_id"]:
            return None
        if checkpoint.logical_life_id != life.visible_life_id:
            raise SchedulerError("agenda compiler crossed committed life scope")
        if sha256_json([vars(item) for item in checkpoint.semantic_items]) \
                != checkpoint.semantic_state_hash:
            raise SchedulerError("agenda compiler received a changed checkpoint")
        entities = {
            item.entity_id for item in checkpoint.semantic_items
            if item.kind == "concept" and item.entity_id is not None
        }
        source = probe["source_entity_id"]
        target = probe["target_entity_id"]
        if source not in entities or target not in entities:
            raise SchedulerError("public probe endpoints are absent from committed memory")
        distractor_source = probe["matched_distractor_source_entity_id"]
        distractor_target = probe["matched_distractor_target_entity_id"]
        if distractor_source not in entities or distractor_target not in entities:
            raise SchedulerError("v0.3-R matched distractor endpoints are absent from memory")
        if (distractor_source, distractor_target) == (source, target):
            raise SchedulerError("v0.3-R matched distractor collapses to the own query")
        return AgendaVocabulary.freeze(probe["probe_id"], (
            AgendaQueryTemplate(
                OWN_QUERY_KEY, "missing_dependency", source,
                CAUSAL_JOIN_RELATION, target,
            ),
            AgendaQueryTemplate(
                DISTRACTOR_QUERY_KEY, "missing_dependency", distractor_source,
                CAUSAL_JOIN_RELATION, distractor_target,
            ),
        ))

    def compile_goal(
        self, request: ThinkerRequest, checkpoint_payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        probe = self._probe(request.life_id)
        entities = {
            item["entity_id"] for item in checkpoint_payload.get("entities", [])
        }
        source = probe["source_entity_id"]
        target = probe["target_entity_id"]
        if source not in entities or target not in entities:
            raise SchedulerError("scientific goal endpoints are outside exact snapshot")
        vocabulary = request.agenda_vocabulary
        if request.round_index == 0:
            if vocabulary is None or vocabulary.goal_id != probe["probe_id"]:
                raise SchedulerError("scientific THINK_0 lacks public compiled vocabulary")
            template = vocabulary.template(OWN_QUERY_KEY)
            if template is None or (
                template.left_id, template.relation_id, template.right_id
            ) != (source, CAUSAL_JOIN_RELATION, target):
                raise SchedulerError("scientific query is not the public causal join")
        return {
            "goal_id": f"goal:causal-join:r{request.round_index}",
            "task": "Resolve the public source-to-target causal join from committed memory.",
            "public_context": {
                "probe_id": probe["probe_id"],
                "source_entity_id": source,
                "target_entity_id": target,
                "probe_hash": self._probe_hashes[request.life_id],
            },
            "query_scope": {"templates": [{
                "query_key": OWN_QUERY_KEY,
                "subject_entity_id": source,
                "relation_id": CAUSAL_JOIN_RELATION,
                "allow_unknown_object": True,
                "allowed_object_entity_ids": [target],
            }]},
            "release_contract": {
                "mode": "DIRECTED_PATH",
                "anchor_entity_ids": [source],
                "allowed_output_entity_ids": [target],
                "min_path_edges": 1,
                "max_path_edges": 1,
            },
        }


class HardenedThinkerMachineAdapter:
    """Scheduler-owned scientific execution; policies emit operations only."""

    adapter_id = "hardened-thinker-machine-scientific-v1"
    parser_id = "typed-goal-thinker.parse-operation-v1.1"

    def __init__(
        self, goal_compiler: ScientificGoalCompilerProtocol,
        policy: OperationPolicyProtocol,
    ):
        self.goal_compiler = goal_compiler
        self.policy = policy
        self.condition_label = str(getattr(policy, "condition_label", ""))
        self.execution_kind = str(getattr(policy, "execution_kind", ""))
        self.objective_binding = str(getattr(policy, "objective_binding", ""))
        if self.execution_kind not in {"scripted_ceiling", "model_science"} \
                or self.objective_binding not in {
                    "exact_request_goal", "recurrence_probe_ceiling",
                } or not self.condition_label.strip():
            raise SchedulerError(
                "scientific operation policy must explicitly label model science "
                "or a scripted ceiling"
            )

    def run_machine(self, request: ThinkerRequest) -> ScientificThinkerExecution:
        checkpoint_payload, semantic_to_memory, goal = \
            compile_trusted_scientific_inputs(request, self.goal_compiler)
        machine = ThinkerMachine(
            freeze_checkpoint(checkpoint_payload), goal,
            max_steps=request.operation_budget,
        )
        ledger = ImmutableModelCallLedger()
        material_rows: list[dict[str, str]] = []
        prompt_template = THINKER_PROMPT_TEMPLATE
        run_id = sha256_json({
            "adapter_id": self.adapter_id, "run_scope": "cpu-scientific-gate",
        })
        ledger_life_id = sha256_json({"opaque_life": request.life_id})
        visible_scope_id = sha256_json({
            "life": request.life_id, "checkpoint": request.checkpoint_hash,
            "goal": request.goal_id,
        })
        while machine.terminal is None:
            if len(ledger.records) >= request.operation_budget:
                machine.force_defer("BUDGET_EXHAUSTED")
                break
            public_state = machine.public_state()
            input_payload = canonical_json(public_state)
            prompt = f"{prompt_template}\n{input_payload}"
            emission = self.policy.propose(public_state, request)
            if not isinstance(emission, PolicyEmission):
                raise SchedulerError("scientific policy returned a completed/non-call object")
            parsed: Mapping[str, Any] | None = None
            parse_status = "PARSED"
            try:
                parsed = parse_operation(emission.raw_output)
                parser_error = None
            except ThinkerContractError as exc:
                parse_status = "REJECTED"
                parser_error = str(exc)
            materials = CallMaterials(
                prompt=prompt.encode("utf-8"),
                prompt_template=prompt_template.encode("utf-8"),
                input_payload=input_payload.encode("utf-8"),
                raw_output=emission.raw_output.encode("utf-8"),
            )
            call_index = len(ledger.records)
            call_id = sha256_json({
                "reset": request.reset_id, "call_index": call_index,
            })
            record = build_record(
                materials=materials, call_id=call_id, run_id=run_id,
                life_id=ledger_life_id, arm=request.arm_id,
                round_index=request.round_index, stage="THINK",
                call_index=call_index,
                model_visible_scope_id=visible_scope_id,
                provider=emission.provider, model=emission.model_id,
                model_revision=emission.model_revision,
                raw_output_artifact_path=None,
                parser_id=self.parser_id, parser_version="1.1",
                parser_outcome=parse_status, parser_error=parser_error,
                token_accounting=TokenAccounting(
                    mode="EXACT_COUNTS", provenance="LOCAL_TOKENIZER",
                    tokenizer_id="whitespace", tokenizer_revision="1.0",
                    supplied_token_ids=None, generated_token_ids=None,
                    supplied_token_count=emission.input_tokens,
                    generated_token_count=emission.output_tokens,
                ),
                decoding_seed=emission.seed,
                decoding_config=DecodingConfig(
                    temperature=0.0, top_p=1.0,
                    max_output_tokens=max(1, emission.output_tokens),
                    stop_sequences=(),
                ),
                started_at="1970-01-01T00:00:00Z",
                ended_at="1970-01-01T00:00:00Z",
                reset_instance_id=request.reset_id,
                checkpoint_hash=checkpoint_payload["checkpoint_hash"],
                goal_hash=sha256_json(goal),
                vocabulary_hash=(
                    request.agenda_vocabulary.vocabulary_hash
                    if request.agenda_vocabulary is not None else ABSENT_HASH
                ),
            )
            ledger = ledger.append(record, materials)
            material_rows.append({
                "call_id": call_id, "prompt": prompt,
                "prompt_template": prompt_template,
                "input_payload": input_payload,
                "raw_output": emission.raw_output,
            })
            if parsed is None:
                machine.record_rejected_attempt(emission.raw_output, ThinkerContractError(
                    "policy output failed strict operation parser"
                ))
                machine.force_defer("POLICY_ERROR")
                break
            try:
                machine.apply(parsed)
            except ThinkerContractError as exc:
                machine.record_rejected_attempt(parsed, exc)
                machine.force_defer("POLICY_ERROR")
                break
        artifact = machine.artifact()
        result, agenda = project_replayed_thinker_result(
            artifact,
            request,
            trusted_checkpoint=checkpoint_payload,
            semantic_to_memory=semantic_to_memory,
        )
        execution = ScientificThinkerExecution(
            adapter_id=self.adapter_id,
            condition_label=self.condition_label,
            execution_kind=self.execution_kind,
            objective_binding=self.objective_binding,
            result=result,
            machine_artifact=artifact,
            agenda_artifact=agenda,
            model_call_ledger=tuple(record_to_mapping(item) for item in ledger.records),
            model_call_materials=tuple(material_rows),
            compiled_checkpoint=checkpoint_payload,
            compiled_goal=goal,
        )
        execution.validate(
            request, trusted_goal_compiler=self.goal_compiler,
        )
        return execution


class V03RGoldSemanticDreamer:
    """Deterministic public-evidence recurrence fixture, never a model claim.

    WAKE calls turn individual structured public records into one local concept.
    A feedback-selected RETURN_SLEEP call may add one direct ``causal_join`` only
    when its bounded view contains the selected source/target plus a witnessed
    route/effect pair sharing the same opaque connector.  The typed query merely
    selects that view; every derivation premise is recipient-local memory.
    """

    @staticmethod
    def _record(request: Any) -> tuple[str, Mapping[str, Any], PremiseIdentity]:
        experience = request.visible_experiences[0]
        try:
            observation = json.loads(experience.observation)
        except (TypeError, json.JSONDecodeError) as exc:
            raise SchedulerError("v0.3-R gold dreamer requires structured public records") from exc
        if not isinstance(observation, Mapping) or set(observation) != {
            "text", "public_record",
        } or not isinstance(observation["public_record"], Mapping):
            raise SchedulerError("v0.3-R public observation has the wrong exact schema")
        return (
            experience.outcome, observation["public_record"],
            PremiseIdentity("experience", experience.payload_hash),
        )

    @staticmethod
    def _concept_by_entity(request: Any, entity_id: str) -> Any | None:
        return next(
            (
                item for item in request.memory
                if item.kind == "concept" and item.entity_id == entity_id
            ),
            None,
        )

    def dream(self, request: Any) -> SemanticDecision:
        kind, record, experience_premise = self._record(request)
        if request.stage == "WAKE":
            if kind == "valve_route" and set(record) == {"valve_id", "source_id"}:
                connector = str(record["valve_id"])
                source = f"entity:source:{record['source_id']}"
                return SemanticDecision.concept(
                    canonical_key=f"record:route:{connector}:{source}",
                    display_label=f"route_record connector={connector} source={source}",
                    rule="compress one witnessed public route record",
                    premises=(experience_premise,), mark_supported=True,
                )
            if kind == "intervention_effect" and set(record) == {
                "valve_id", "target_id", "effect",
            }:
                connector = str(record["valve_id"])
                target = f"entity:target:{record['target_id']}"
                effect = str(record["effect"])
                return SemanticDecision.concept(
                    canonical_key=f"record:effect:{connector}:{target}:{effect}",
                    display_label=(
                        f"effect_record connector={connector} target={target} "
                        f"observed={effect}"
                    ),
                    rule="compress one witnessed public intervention record",
                    premises=(experience_premise,), mark_supported=True,
                )
            if kind == "source_anchor_color" and str(record.get("anchor_id")) == "animal_00":
                entity = f"entity:source:{record['source_id']}"
                return SemanticDecision.concept(
                    canonical_key=entity, display_label=entity,
                    rule="name one publicly witnessed source endpoint",
                    premises=(experience_premise,), mark_supported=True,
                )
            if kind == "target_passive_baseline" \
                    and str(record.get("anchor_id")) == "animal_00":
                entity = f"entity:target:{record['target_id']}"
                return SemanticDecision.concept(
                    canonical_key=entity, display_label=entity,
                    rule="name one publicly witnessed target endpoint",
                    premises=(experience_premise,), mark_supported=True,
                )
            return SemanticDecision.pass_()

        if request.stage != "RETURN_SLEEP" or not request.selection_queries:
            return SemanticDecision.pass_()
        query = request.selection_queries[0]
        if any(
            item.kind == "semantic_edge"
            and (item.source_entity_id, item.relation_id, item.target_entity_id)
                == (query.left_id, query.relation_id, query.right_id)
            for item in request.memory
        ):
            return SemanticDecision.pass_()
        source_item = self._concept_by_entity(request, query.left_id)
        target_item = self._concept_by_entity(request, query.right_id)
        if source_item is None or target_item is None:
            return SemanticDecision.pass_()
        route_prefix = "route_record connector="
        effect_prefix = "effect_record connector="
        route_items = [
            item for item in request.memory
            if item.kind == "concept" and item.canonical_text.startswith(route_prefix)
            and f" source={query.left_id}" in item.canonical_text
        ]
        matched_pairs = []
        for route_item in route_items:
            connector = route_item.canonical_text.split()[1].split("=", 1)[1]
            for effect_item in request.memory:
                if effect_item.kind == "concept" \
                        and effect_item.canonical_text.startswith(effect_prefix) \
                        and f"connector={connector}" in effect_item.canonical_text \
                        and f" target={query.right_id}" in effect_item.canonical_text:
                    matched_pairs.append((route_item, effect_item))
        if len(matched_pairs) != 1:
            return SemanticDecision.pass_()
        route_item, effect_item = matched_pairs[0]
        return SemanticDecision.edge(
            source_semantic_hash=source_item.semantic_hash,
            relation=CAUSAL_JOIN_RELATION,
            target_semantic_hash=target_item.semantic_hash,
            rule="join one witnessed route/effect pair within the bounded local view",
            premises=(
                PremiseIdentity("concept", source_item.semantic_hash),
                PremiseIdentity("concept", target_item.semantic_hash),
                PremiseIdentity("concept", route_item.semantic_hash),
                PremiseIdentity("concept", effect_item.semantic_hash),
            ),
            mark_supported=True,
        )


class ScriptedRecurrencePolicy:
    """Gold operation policy for the v0.3-R CPU recurrence gate only."""

    condition_label = (
        "scripted-operation-policy/hardened recurrence-probe ceiling; "
        "not a final-goal answer"
    )
    execution_kind = "scripted_ceiling"
    objective_binding = "recurrence_probe_ceiling"

    def propose(
        self, public_state: Mapping[str, Any], request: ThinkerRequest,
    ) -> PolicyEmission:
        trace = public_state["trace"] if "trace" in public_state else []
        # ``public_state`` is the live machine state, not the final artifact;
        # retrieved/confusion/hypothesis dictionaries are authoritative.
        confusions = public_state["confusions"]
        hypotheses = public_state["hypotheses"]
        retrieved_items = [
            item
            for result in public_state["retrieved"].values()
            for item in result["items"]
        ]
        if not public_state["retrieved"]:
            operation = {
                "op": "QUERY", "subgoal_id": "root",
                "query_key": OWN_QUERY_KEY, "object_entity_id": None,
            }
        elif confusions:
            confusion_ids = sorted(
                key for key, value in confusions.items() if value["status"] == "OPEN"
            )
            operation = (
                {"op": "REQUEST_DREAM", "confusion_ids": confusion_ids}
                if request.round_index == 0 else
                {"op": "DEFER", "reason_code": "INSUFFICIENT_MEMORY",
                 "confusion_ids": confusion_ids}
            )
        elif not hypotheses:
            operation = {
                "op": "HYPOTHESIZE", "subgoal_id": "root",
                "hypothesis_id": "hyp:path", "claim": "a supported causal path exists",
                "cited_semantic_ids": [retrieved_items[0]["semantic_id"]],
                "parent_hypothesis_ids": [],
            }
        elif hypotheses["hyp:path"]["prediction"] is None:
            output = public_state["goal"]["release_contract"]["allowed_output_entity_ids"][0]
            operation = {
                "op": "PREDICT", "subgoal_id": "root",
                "hypothesis_id": "hyp:path", "prediction_entity_id": output,
            }
        else:
            operation = {"op": "RELEASE", "hypothesis_id": "hyp:path"}
        raw = json.dumps(operation, sort_keys=True, separators=(",", ":"))
        return PolicyEmission(
            raw_output=raw,
            provider="local-scripted",
            model_id="scripted-gold-policy",
            model_revision="cpu-ceiling-v1",
            input_tokens=len(
                f"{THINKER_PROMPT_TEMPLATE}\n{canonical_json(public_state)}".split()
            ),
            output_tokens=len(raw.split()),
            seed=0,
        )
