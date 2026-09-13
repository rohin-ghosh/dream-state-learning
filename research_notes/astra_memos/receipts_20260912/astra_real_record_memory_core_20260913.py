"""CPU-only source-withdrawn memory compiler; not native custody or a writer."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from types import ModuleType


COMPILER = "astra_real_record_source_withdrawn_memory_20260913_v1"
CORE_PATH = "/tmp/astra_level1_real_record_core_20260913_v2.py"
CORE_SHA256 = "b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5"
SOURCE_ROOT = "/data/home/rohing/dream-state"
SCHEMA_INSTRUCTION = (
    'Output only one JSON object with keys "try", "observed", "predicted", and "relation". '
    'Use an array of three integers for "try", a Boolean for "observed", '
    'a Boolean or null for "predicted", and a string for "relation".'
)
CUE_TEMPLATES = {
    "exact": "Recall the record for this public task and execution.\nTask: {task_id}\nExecution: {public_execution_id}\n",
    "paraphrase": "Retrieve the stored record identified below.\nTask: {task_id}\nExecution: {public_execution_id}\n",
}
ENCODING_CONTRACT = {
    "context_labels": -100,
    "supervised": "exact raw_target token span plus one assistant EOS",
    "template_tail_and_padding_labels": -100,
    "truncation": "forbidden",
    "tokenization_status": "not performed; native encoder must verify exact boundaries",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_core(*, core_path=CORE_PATH, source_root=SOURCE_ROOT):
    """Read exactly pinned Python sources only; never load a tokenizer/model."""
    source = Path(core_path).read_bytes()
    require(hashlib.sha256(source).hexdigest() == CORE_SHA256, "formation core pin mismatch")
    core = ModuleType("astra_memory_pinned_formation_v2")
    exec(compile(source, str(core_path), "exec"), core.__dict__)
    return core, core.load_dependencies(source_root)


def _messages(task_id, public_execution_id, variant):
    return [{"role": "user", "content": CUE_TEMPLATES[variant].format(
        task_id=task_id, public_execution_id=public_execution_id) + SCHEMA_INSTRUCTION}]


def _project(capture, core, dependencies):
    require(type(capture) is dict and bool(capture), "a complete formation capture is required")
    capture = copy.deepcopy(capture)
    audit = core.audit_capture(capture, dependencies=dependencies)
    require(capture["schema"] == core.SCHEMA and capture["contract"] == core.contract(dependencies),
            "formation contract mismatch")
    require([episode["episode_id"] for episode in capture["episodes"]] == list(core.episode_ids()),
            "formation episode order differs")
    rows, refused, executions = [], [], {}
    for episode in capture["episodes"]:
        task_id = episode["episode_id"]
        require([turn["tick"] for turn in episode["turns"]] == [1, 2], "formation turn order differs")
        for turn in episode["turns"]:
            execution, record = turn["execution"], turn["record"]
            if record is None:
                refused.append({"task_id": task_id, "tick": turn["tick"],
                                "reason": "no_record_call", "errors": copy.deepcopy(turn["errors"])})
                continue
            require(execution is not None, "record lacks actual execution")
            response, request = record["response"], record["request"]
            public_execution_id = f"{task_id}#t{turn['tick']}"
            require(execution["eid"] == task_id and execution["tick"] == turn["tick"] and
                    execution["execution_id"] == f"{capture['state']}:{public_execution_id}",
                    "execution ID join differs")
            require(request["source_execution_sha256"] == execution["sha256"], "record execution join differs")
            raw, finish_reason = response.get("raw"), response.get("finish_reason")
            score = core.score_record(raw, finish_reason, execution, dependencies, source_errors=record["errors"])
            require(score == turn["score"], "record admission score differs")
            if score["production_eligible"] is not True or finish_reason != "stop":
                refused.append({"task_id": task_id, "tick": turn["tick"], "reason": "record_not_production_eligible",
                                "errors": copy.deepcopy(score["source_completion_errors"] + score["production_errors"])})
                continue
            require(type(raw) is str and not record["errors"], "eligible record lacks exact source-complete text")
            row_id = f"{capture['state']}:{public_execution_id}"
            require(row_id not in executions, "duplicate memory row")
            rows.append({
                "row_id": row_id,
                "input_messages": _messages(task_id, public_execution_id, "exact"),
                "paraphrase_input_messages": _messages(task_id, public_execution_id, "paraphrase"),
                "raw_target": raw,
                "target_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "encoding_contract": copy.deepcopy(ENCODING_CONTRACT),
                "source": {
                    "state": capture["state"], "task_id": task_id, "tick": turn["tick"],
                    "public_execution_id": public_execution_id, "execution_id": execution["execution_id"],
                    "execution_sha256": execution["sha256"],
                    "wake_request_id": turn["wake"]["request"]["request_id"],
                    "record_request_id": request["request_id"], "record_event_sha256": record["sha256"],
                    "capture_sha256": capture["capture_sha256"],
                },
            })
            executions[row_id] = execution
    targets = {row["target_sha256"] for row in rows}
    triples = {tuple(execution["values"]) for execution in executions.values()}
    dataset = {
        "schema": COMPILER, "status": "WRITE_AVAILABLE" if rows else "NO_WRITE",
        "reason": "admitted_records_available_not_authorization" if rows else "no_production_eligible_records",
        "state": capture["state"], "rows": rows, "refused": refused,
        "counts": {"possible_slots": 16, "admitted_rows": len(rows), "refused_slots": len(refused),
                   "distinct_raw_targets": len(targets), "distinct_triples": len(triples),
                   "episodes_with_admissions": len({row["source"]["task_id"] for row in rows})},
        "source_proof": {"formation_core_sha256": CORE_SHA256, "capture_sha256": capture["capture_sha256"],
                         "dependencies": copy.deepcopy(dependencies.manifest), "audit": audit,
                         "declared_capture_binding": copy.deepcopy(capture["binding"])},
        "qualification": {
            "compiler_choice": "new source-withdrawn context; not unchanged original record-prompt writing",
            "order": "all admitted records, original episode order then tick1/tick2; no deduplication or selection",
            "primary": "cold readback with the identical input_messages cue; acquisition/persistence",
            "transfer": "paraphrase_input_messages is a separate endpoint, never pooled with primary",
            "independence": "rows, repeated triples, repeated targets and episode turns are not independent learners",
            "native_identity_verified": False,
            "custody": "CPU replay only; future runner must bind completed native collection and original learner adapter",
            "future_controls": "same-learner matched LR0; original perception48held+12canary retention; no tests run here",
        },
    }
    require(len(rows) + len(refused) == 16, "admission count differs")
    return dataset, executions


def project_capture(capture, *, core_path=CORE_PATH, source_root=SOURCE_ROOT):
    """Project one complete audited state; valid empty admission returns NO_WRITE.

    Missing/malformed captures raise. Metadata and raw targets must never be
    rendered into model input: only input_messages is the training/primary cue.
    """
    core, dependencies = load_core(core_path=core_path, source_root=source_root)
    dataset, unused_executions = _project(capture, core, dependencies)
    return dataset


def score_readback(capture, row_id, raw, finish_reason, *, input_messages, variant="exact",
                   core_path=CORE_PATH, source_root=SOURCE_ROOT):
    """Score against the original execution, not self-reported readback facts.

    Reaudit the source and rebuild the row; caller-authored row metadata is
    not trusted. Message equality is a CPU check, not native prompt custody.
    """
    require(type(variant) is str and variant in CUE_TEMPLATES, "unknown readback variant")
    core, dependencies = load_core(core_path=core_path, source_root=source_root)
    dataset, executions = _project(capture, core, dependencies)
    row = next((row for row in dataset["rows"] if row["row_id"] == row_id), None)
    require(row is not None, "readback row is not an admitted source row")
    key = "input_messages" if variant == "exact" else "paraphrase_input_messages"
    require(input_messages == row[key], "readback cue differs from declared variant")
    score = core.score_record(raw, finish_reason, executions[row_id], dependencies)
    return {
        "compiler": COMPILER, "row_id": row_id, "variant": variant,
        "endpoint": "exact_cue_acquisition_persistence" if variant == "exact" else "paraphrase_transfer",
        "target_sha256": row["target_sha256"], "source": copy.deepcopy(row["source"]),
        "exact_target_bytes": type(raw) is str and finish_reason == "stop" and
                              raw.encode("utf-8") == row["raw_target"].encode("utf-8"),
        "score": score, "native_identity_verified": False,
    }
