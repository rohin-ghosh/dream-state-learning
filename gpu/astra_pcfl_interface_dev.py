"""Supplied-memory typed-turn DEV only; no CLI, fit or lifecycle authority."""

from collections.abc import Mapping
import copy
import hashlib
import json
from pathlib import Path
import re
import time
from types import MappingProxyType

from gpu import astra_pcfl_native_actor as native
from organism_v6 import pcfl_vertical_dev as core


SCHEMA = "pcfl.supplied_memory_interface_dev.v1"
STAGES = {
    "A1_READ_DISCLOSED": {"reads": 12, "thinks": 0, "calls": 13},
    "A2_DIRECT": {"reads": 0, "thinks": 0, "calls": 1},
    "A3_THINK": {"reads": 0, "thinks": 6, "calls": 7},
    "ACTIVE_THINK": {"reads": 12, "thinks": 6, "calls": 19},
    "READ_REQUIRED_SMOKE": {"reads": 12, "thinks": 0, "calls": 13},
    "READ_REQUIRED_PANEL": {"reads": 12, "thinks": 0, "calls": 13},
    "STRUCTURED_ACTION_SMOKE": {"reads": 12, "thinks": 0, "calls": 13},
    "STRUCTURED_FIRST_READ_SMOKE": {"reads": 12, "thinks": 0, "calls": 13},
    "A3B_NEWLINE_FRAMED_SMOKE": {"reads": 0, "thinks": 6, "calls": 7},
    "A3C_STRUCTURED_FRAMED_SMOKE": {"reads": 0, "thinks": 6, "calls": 7},
}
READ_REQUIRED_STAGES = ("READ_REQUIRED_SMOKE", "READ_REQUIRED_PANEL")
STRUCTURED_STAGES = ("STRUCTURED_ACTION_SMOKE", "STRUCTURED_FIRST_READ_SMOKE")
STRUCTURED_FRAMED_STAGES = ("A3C_STRUCTURED_FRAMED_SMOKE",)
FRAMED_STAGES = ("A3B_NEWLINE_FRAMED_SMOKE",) + STRUCTURED_FRAMED_STAGES
CUSTOM_STAGES = STRUCTURED_STAGES + FRAMED_STAGES
READ_REGEX = r"READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})"
ACTION_REGEX = (
    r"(?:READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})"
    r"|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)"
)
THINK_ROUTE_REGEX = (
    r"(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*"
    r"|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)\n?"
)
SMOKE_INDICES = (0, 1, 16, 17, 32, 33, 48, 49)
READ_REQUIRED = (
    "Before any ROUTE, you must issue at least one READ. Use only the public START\n"
    "and exact identifiers returned by memory; never invent a READ address."
)
CONTINUE = "CONTINUE: follow the declared turn budgets and commit the final action when ready."
ROW_SEMANTICS = (
    "EDGE <source> <port> <destination> is a directed transition.\n"
    "EVENT <event> AT <source> DID <port> GOT <destination> EVIDENCE <receipt>\n"
    "records the same directed transition: using <port> at <source> moved to\n"
    "<destination>. LINK records that two EVENTs were consecutive; it does not\n"
    "change either EVENT transition."
)
READ_API = (
    "Local reads are enabled. The only legal READ commands are:\n"
    "READ EVENT <event_id>\nREAD EVENTS_AT <node_id>\nREAD LINKS_FROM <event_id>\n"
    "READ EVENT returns the matching EVENT. READ EVENTS_AT returns all EVENTs whose AT/source is that node. "
    "READ LINKS_FROM returns all LINKs whose first event is that event. "
    "The return is exact registered rows or MISS. Output one READ per response; at most 12 READs."
)
BASE_SYSTEM = (
    "You operate a deterministic directed route system. Identifiers are opaque and case-sensitive. "
    "Use only the public task, supplied memory and conversation. Never invent, rename or repair an identifier. "
    "Each response must be exactly one complete typed physical line, without a trailing newline, fence or prose. "
    "Commit the final action as ROUTE <start> <goal> : <comma-separated ports>. "
    "The complete ROUTE is terminal; there is no route feedback, correction or retry. "
    "At most 256 generated tokens per response and 2048 cumulatively are available.\n"
)
THINK_API = (
    "You may output THINK <one nonempty physical line of reasoning>. "
    "Use at least one THINK before ROUTE and at most six THINK responses. "
    "A THINK receives only a fixed CONTINUE message, not world information. "
    "Never combine a THINK and an action in one response."
)
require, canonical, digest = native.require, native.canonical, native.digest


def seal(value):
    return {**copy.deepcopy(value), "sha256": digest(value)}


def _unseal(value):
    require(type(value) is dict and "sha256" in value, "sealed object required")
    body = {key: item for key, item in value.items() if key != "sha256"}
    require(digest(body) == value["sha256"], "seal drift")
    return body


def source_pins():
    return {str(Path(module).resolve()): hashlib.sha256(Path(module).read_bytes()).hexdigest()
            for module in (__file__, native.__file__, core.__file__)}


def build_roster(root_wires, stage):
    """Use caller-supplied preserved wires, never allocate or reselect roots."""
    require(stage in STAGES, "unknown interface stage")
    require(type(root_wires) is list and len(root_wires) == 4, "four preserved root wires required")
    roots = [core.from_data(wire) for wire in root_wires]
    require([root.label for root in roots] == [f"excluded/{index}" for index in range(4)], "excluded root order")
    require([core.to_data(root) for root in roots] == root_wires, "root wire roundtrip differs")
    limits = STAGES[stage]
    system = BASE_SYSTEM + ROW_SEMANTICS + "\n"
    system += READ_API if limits["reads"] else "Local reads are disabled; do not emit READ."
    system += "\n" + (THINK_API if limits["thinks"] else "THINK is unavailable; do not emit THINK.")
    if stage in READ_REQUIRED_STAGES + STRUCTURED_STAGES:
        system += "\n" + READ_REQUIRED
    projection = "ACTIVE_LINKED_TEXT" if limits["reads"] else "EXACT_WITNESSED_GRAPH"
    tasks = []
    for root in roots:
        for cell in core.expand_cube(root):
            rows = core.ideal_rows(cell)
            queries = core.materialize_queries(rows) if limits["reads"] else {}
            for goal in (0, 1):
                block = f"{root.label}/{cell.old}/{cell.relevant}/{cell.distractor}/{goal}"
                identifier = f"interface/{stage}/{block}"
                public = core.render_task(cell, goal, projection, rows=rows, fixture_only=True)
                tasks.append({"id": identifier, "case_id": block, "cell": core.to_data(cell), "goal": goal,
                              "projection": projection, "seed": core.seed("runtime-test/" + block),
                              "messages": [{"role": "system", "content": system},
                                           {"role": "user", "content": public["user"]}],
                              "queries": copy.deepcopy(queries), "source_rows": copy.deepcopy(rows),
                              "slot_ids": [f"{core.byte_hash(identifier)}/actor/{turn}" for turn in range(limits["calls"])]})
    require(len(tasks) == 64 and len({task["case_id"] for task in tasks}) == 64, "case denominator")
    if stage == "READ_REQUIRED_SMOKE" or stage in CUSTOM_STAGES:
        tasks = [tasks[index] for index in SMOKE_INDICES]
    roster = {"schema": SCHEMA + "/roster", "stage": stage, "roots": copy.deepcopy(root_wires),
                 "roots_sha256": digest(root_wires), "sources": source_pins(), "tasks": tasks,
                 "limits": {**limits, "turn_tokens": 256, "actor_tokens": 2048, "returned_tokens": 4096,
                            "input_tokens": 14336, "possible_calls": len(tasks) * limits["calls"]},
                 "continue": CONTINUE, "material_origin": "RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD",
                 "fits": 0, "updates": 0, "full_assay_qualified": False}
    if stage in STRUCTURED_STAGES:
        first_regex = READ_REGEX if stage == "STRUCTURED_FIRST_READ_SMOKE" else ACTION_REGEX
        roster["sampling_policy"] = {
            "name": f"pcfl.supplied_memory.{stage.lower()}.v1", "externally_scaffolded": True,
            "external_first_read": stage == "STRUCTURED_FIRST_READ_SMOKE",
            "first_slot_regex": first_regex, "first_slot_regex_sha256": core.byte_hash(first_regex),
            "later_slot_regex": ACTION_REGEX, "later_slot_regex_sha256": core.byte_hash(ACTION_REGEX),
            "autonomy_claim": False, "learning_claim": False,
        }
    if stage in FRAMED_STAGES:
        roster["sampling_policy"] = {
            "name": f"pcfl.supplied_memory.{stage.lower()}.v1", "externally_framed": True,
            "stop": ["\n"], "include_stop_str_in_output": False,
            "decode_contract": "EXACT_FIRST_LF_PREFIX_FULL_TOKEN_DECODE_RETAINED",
            "autonomy_claim": False, "learning_claim": False,
        }
    if stage in STRUCTURED_FRAMED_STAGES:
        roster["sampling_policy"].update(
            structured_outputs={"regex": THINK_ROUTE_REGEX}, regex_sha256=core.byte_hash(THINK_ROUTE_REGEX),
            externally_scaffolded=True, external_first_think=False)
    return seal(roster)


def validate_roster(roster, expected_sha256):
    _unseal(roster)
    require(roster["sha256"] == expected_sha256, "roster hash differs")
    require(canonical(roster) == canonical(build_roster(roster["roots"], roster["stage"])), "roster/source reconstruction differs")


def sampling_for(stage, request, limits):
    require(stage in STAGES, "unknown sampling stage")
    sampling = {**native.SAMPLING, "seed": request["seed"], "max_tokens": limits["output_tokens"]}
    if stage in STRUCTURED_STAGES:
        require(re.fullmatch(r"[0-9a-f]{64}/actor/(?:[0-9]|1[0-2])", request["id"]) is not None,
                "structured slot syntax")
        first = stage == "STRUCTURED_FIRST_READ_SMOKE" and request["id"].endswith("/actor/0")
        sampling["structured_outputs"] = {"regex": READ_REGEX if first else ACTION_REGEX}
    if stage in FRAMED_STAGES:
        sampling.update(stop=["\n"], include_stop_str_in_output=False)
    if stage in STRUCTURED_FRAMED_STAGES:
        sampling["structured_outputs"] = {"regex": THINK_ROUTE_REGEX}
    return sampling


def _validate_frame(decoded, raw, sampling):
    require(sampling.get("stop") == ["\n"] and sampling.get("include_stop_str_in_output") is False
            and "structured_outputs" not in sampling, "LF framing sampling differs")
    if raw["finish_reason"] == "stop" and raw["stop_reason"] == "\n":
        offset = decoded.find("\n")
        require(offset >= 0 and raw["text"] == decoded[:offset], "LF frame prefix differs")
    else:
        require(decoded == raw["text"], "output text/token decode differs")
        require(raw["finish_reason"] == "length" or
                (raw["finish_reason"] == "stop" and raw["stop_reason"] is None and "\n" not in decoded),
                "LF frame termination differs")


def _validate_structured_frame(decoded, raw, sampling):
    require(sampling.get("structured_outputs") == {"regex": THINK_ROUTE_REGEX}, "structured frame grammar differs")
    _validate_frame(decoded, raw, {key: value for key, value in sampling.items() if key != "structured_outputs"})


class InterfaceActor(native.NativeActor):
    def __init__(self, config, *, stage, roster, **native_kwargs):
        require(stage in CUSTOM_STAGES and roster["stage"] == stage, "structured actor stage binding")
        validate_roster(roster, roster["sha256"])
        require(all(config["source_files"].get(path) == checksum for path, checksum in roster["sources"].items()),
                "structured actor source pins")
        self._stage = stage
        self._slot_seeds = MappingProxyType({slot: task["seed"] for task in roster["tasks"] for slot in task["slot_ids"]})
        self._first_slots = frozenset(task["slot_ids"][0] for task in roster["tasks"])
        super().__init__(config, **native_kwargs)

    def _sampling(self, request, limits):
        require(request["id"] in self._slot_seeds and request["seed"] == self._slot_seeds[request["id"]],
                "structured slot/seed binding")
        require((request["id"] in self._first_slots) == (len(request["messages"]) == 2), "structured slot/turn binding")
        return sampling_for(self._stage, request, limits)

    def _validate_decoded(self, decoded, raw, sampling):
        if self._stage in STRUCTURED_FRAMED_STAGES:
            _validate_structured_frame(decoded, raw, sampling)
        elif self._stage in FRAMED_STAGES:
            _validate_frame(decoded, raw, sampling)
        else:
            super()._validate_decoded(decoded, raw, sampling)


def _render(tokenizer, messages):
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    if isinstance(ids, Mapping):
        ids = ids.get("input_ids")
    ids = native.token_ids(ids)
    require(type(text) is str and ids and ids == native.token_ids(tokenizer.encode(text, add_special_tokens=False)),
            "template/encode mismatch")
    return text, ids


def _decode(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    value = json.loads(text, object_pairs_hook=unique)
    canonical(value)
    return value


def read_capture(directory, index):
    """Read original sidecar bytes, including partial failure evidence."""
    names = ["config.json", "identity.json"] + [f"call_{index:04d}.{suffix}.json"
             for suffix in ("request", "render", "raw", "response", "error")]
    files = {}
    for name in names:
        path = Path(directory) / name
        if path.exists():
            require(path.is_file() and path.stat().st_size <= 8 * 1024 * 1024, "oversize capture")
            text = path.read_bytes().decode("utf-8")
            files[name] = {"utf8": text, "sha256": core.byte_hash(text)}
    return {"index": index, "files": files}


def _verify(attempt, index, request, limits, settings, tokenizer, previous_end, stage):
    require(set(attempt) == {"request", "limits", "response", "capture", "error"}
            and attempt["request"] == request and attempt["limits"] == limits, "attempt binding")
    require(attempt["error"] is None, "backend/capture failure: " + str(attempt["error"]))
    capture = attempt["capture"]
    require(type(capture) is dict and set(capture) == {"index", "files"}
            and type(capture["index"]) is int and capture["index"] == index, "capture index")
    prefix = f"call_{index:04d}."
    required = {"config.json", "identity.json"} | {prefix + suffix + ".json" for suffix in ("request", "render", "raw", "response")}
    require(set(capture["files"]) == required, "missing/extra/error capture")
    files = {}
    for name, record in capture["files"].items():
        require(set(record) == {"utf8", "sha256"} and core.byte_hash(record["utf8"]) == record["sha256"], "capture byte drift")
        files[name] = _decode(record["utf8"])
    identity = files["identity.json"]
    binding = identity["identity"]
    require(files["config.json"] == settings and identity["config_sha256"] == digest(settings), "actor config binding")
    require(identity["kind"] in ("NATIVE", "INJECTED_CPU_TEST") and binding["mount"] == "C0"
            and binding["lora_request"] is None and binding["repository"] == native.MODEL_NAME
            and binding["revision"] == native.REVISION and binding["source_files"] == settings["source_files"]
            and binding["environment"] == settings["environment"] and binding["gpu_uuid_expected"] == settings["gpu_uuid"]
            and binding["model_binding_sha256"] == settings["model_binding"]["sha256"]
            and all(binding["model_files"].get(name) == checksum for name, checksum in settings["tokenizer_files"].items()),
            "model/source/route binding")
    asked, rendered, raw, returned = (files[prefix + suffix + ".json"] for suffix in ("request", "render", "raw", "response"))
    require(asked["request"] == request and asked["limits"] == limits
            and asked["request_sha256"] == raw["request_sha256"] == digest(request), "request join")
    text, ids = _render(tokenizer, request["messages"])
    require(rendered["rendered_prompt"] == text and rendered["prompt_token_ids"] == ids
            and rendered["sampling"] == sampling_for(stage, request, limits)
            and rendered["mount"] == raw["mount"] == "C0" and rendered["lora_request"] is raw["lora_request"] is None,
            "render/default sampling join")
    output, response = raw["raw"], attempt["response"]
    require(raw["kind"] == identity["kind"] and set(output) == {"text", "output_token_ids", "prompt_token_ids", "finish_reason", "stop_reason"}, "raw fields/kind")
    output_ids = native.token_ids(output["output_token_ids"])
    require(native.token_ids(output["prompt_token_ids"]) == ids and type(output["text"]) is str
            and len(output_ids) <= limits["output_tokens"] and (output_ids or not output["text"]), "raw token decode/cap")
    require(output["finish_reason"] in ("stop", "length")
            and (output["stop_reason"] is None or type(output["stop_reason"]) in (int, str)), "finish receipt")
    decoded = tokenizer.decode(output_ids, skip_special_tokens=True)
    if stage in STRUCTURED_FRAMED_STAGES:
        _validate_structured_frame(decoded, output, rendered["sampling"])
    elif stage in FRAMED_STAGES:
        _validate_frame(decoded, output, rendered["sampling"])
    else:
        require(decoded == output["text"], "raw token decode/cap")
    require(type(response) is dict and set(response) == {"request_sha256", "text", "prompt_tokens", "output_tokens", "device_seconds"}
            and response == returned["response"] and response["request_sha256"] == digest(request)
            and response["text"] == output["text"] and returned["decoded"] == decoded
            and returned["raw_hex"] == output["text"].encode("utf-8").hex()
            and returned["raw_utf8_sha256"] == core.byte_hash(output["text"]), "response byte join")
    require(type(response["prompt_tokens"]) is int and response["prompt_tokens"] == len(ids)
            and type(response["output_tokens"]) is int and response["output_tokens"] == len(output_ids), "response token counts")
    times = [raw[key] for key in ("operation_started", "generation_started", "generation_ended")]
    for value in [*times, response["device_seconds"]]:
        native.number(value)
    require(previous_end <= times[0] <= times[1] <= times[2] <= limits["deadline"]
            and asked["started"] == times[0] and times[2] - times[0] <= response["device_seconds"] <= limits["device_seconds"]
            and times[0] + response["device_seconds"] <= limits["deadline"], "capture chronology/cap")
    return output, digest(identity), times[0] + response["device_seconds"]


def _result(task):
    return {"id": task["id"], "status": "UNCALLED", "reason": None, "raw": "", "raw_sha256": core.byte_hash(""),
            "success": False, "score": None, "thinks": 0, "reads": 0, "served_reads": 0,
            "actor_tokens": 0, "returned_tokens": 0, "invalid_read": False, "services": [],
            "slots": [{"id": name, "status": "UNCALLED", "attempt_index": None} for name in task["slot_ids"]]}


def summarize(results, stage, complete):
    successes = sum(row["success"] for row in results)
    thought_tasks = sum(row["thinks"] > 0 for row in results)
    served_tasks = sum(row["served_reads"] > 0 for row in results)
    invalid = sum(row["invalid_read"] for row in results)
    terminal = [row for row in results if row["status"] == "SCORED"
                and row["reason"] == "ROUTE" and row["score"] and row["score"]["strict"]]
    read_handshakes = sum(row["served_reads"] > 0 and not row["invalid_read"] for row in terminal)
    thought_interfaces = sum(row["thinks"] > 0 for row in terminal)
    thought_routes = sum(row["thinks"] > 0 and row["success"] for row in terminal)
    active_routes = sum(row["thinks"] > 0 and row["served_reads"] > 0
                        and not row["invalid_read"] and row["success"] for row in terminal)
    gate = successes >= 60
    if stage == "A1_READ_DISCLOSED":
        gate = read_handshakes >= 60 and invalid == 0
    if stage in READ_REQUIRED_STAGES + STRUCTURED_STAGES:
        denominator, threshold = (64, 60) if stage == "READ_REQUIRED_PANEL" else (8, 7)
        gate = len(results) == denominator and read_handshakes >= threshold and invalid == 0
    if STAGES[stage]["thinks"]:
        gate = thought_routes >= 60
    if stage == "ACTIVE_THINK":
        gate = active_routes >= 60 and invalid == 0
    if stage in FRAMED_STAGES:
        gate = len(results) == 8 and thought_interfaces >= 7
    summary = {"denominator": len(results) if stage in READ_REQUIRED_STAGES + CUSTOM_STAGES else 64,
            "route_successes": successes, "thought_tasks": thought_tasks,
            "served_read_tasks": served_tasks, "invalid_read_tasks": invalid,
            "read_handshake_tasks": read_handshakes, "thought_interface_tasks": thought_interfaces,
            "thought_route_tasks": thought_routes, "active_thought_route_tasks": active_routes,
            "stage_gate_passed": bool(complete and gate), "full_assay_qualified": False}
    if stage in STRUCTURED_STAGES:
        summary.update(externally_scaffolded=True, external_first_read=stage == "STRUCTURED_FIRST_READ_SMOKE",
                       autonomy_claim=False, learning_claim=False)
    if stage in FRAMED_STAGES:
        summary.update(externally_framed=True, autonomy_claim=False, learning_claim=False)
    if stage in STRUCTURED_FRAMED_STAGES:
        summary.update(externally_scaffolded=True, external_first_think=False)
    return summary


def _execute(roster, settings, tokenizer, deadline, acquire, clock):
    started = clock()
    results, attempts = [_result(task) for task in roster["tasks"]], []
    previous_end, identity_hash, error = started, None, None
    caps = roster["limits"]
    try:
        for task, result in zip(roster["tasks"], results):
            result["status"] = "RUNNING"
            messages = copy.deepcopy(task["messages"])
            for slot in result["slots"]:
                if result["actor_tokens"] >= caps["actor_tokens"]:
                    result["reason"] = "ACTOR_TOKEN_CAP"
                    break
                now = clock()
                require(started <= now < deadline and now - started < settings["device_seconds_cap"], "stage deadline exhausted")
                rendered, ids = _render(tokenizer, messages)
                output_cap = min(caps["turn_tokens"], caps["actor_tokens"] - result["actor_tokens"])
                if len(ids) > min(caps["input_tokens"], settings["max_input_tokens"]) or len(ids) + output_cap > native.ENGINE["max_model_len"]:
                    result["reason"] = "INPUT_TOKEN_CAP"
                    break
                request = {"id": slot["id"], "messages": copy.deepcopy(messages), "seed": task["seed"], "mount": "C0"}
                limits = {"input_tokens": len(ids), "output_tokens": output_cap,
                          "remaining_reads": caps["reads"] - result["reads"],
                          "returned_tokens": caps["returned_tokens"] - result["returned_tokens"],
                          "deadline": deadline, "device_seconds": min(deadline - now, settings["device_seconds_cap"] - (now - started))}
                index = len(attempts)
                slot.update(status="ATTEMPTED", attempt_index=index)
                attempt = acquire(index, request, limits)
                attempts.append(copy.deepcopy(attempt))
                output, observed_identity, previous_end = _verify(attempt, index, request, limits, settings, tokenizer,
                                                                 max(previous_end, now), roster["stage"])
                require(identity_hash is None or identity_hash == observed_identity, "actor identity changed")
                identity_hash = observed_identity
                require(previous_end <= clock() <= deadline, "stage chronology/deadline after generation")
                raw = output["text"]
                slot["status"] = "RETURNED"
                result.update(raw=raw, raw_sha256=core.byte_hash(raw))
                result["actor_tokens"] += attempt["response"]["output_tokens"]
                if output["finish_reason"] != "stop":
                    result["reason"] = "LENGTH"
                    break
                if re.fullmatch(r"THINK [^\r\n]+", raw) and any(not char.isspace() for char in raw[6:]):
                    if result["thinks"] >= caps["thinks"]:
                        result["reason"] = "THINK_DISABLED_OR_CAP"
                        break
                    result["thinks"] += 1
                    messages.extend(({"role": "assistant", "content": raw}, {"role": "user", "content": CONTINUE}))
                    continue
                if raw.startswith("READ"):
                    try:
                        core.parse_read(raw)
                    except ValueError:
                        result.update(invalid_read=True, reason="INVALID_READ")
                        break
                    if result["reads"] >= caps["reads"]:
                        result.update(invalid_read=True, reason="READ_DISABLED_OR_CAP")
                        break
                    lookup = core.read_query(task["queries"], raw)
                    result["reads"] += 1
                    token_ids = native.token_ids(tokenizer.encode(lookup["raw"], add_special_tokens=False))
                    served = result["returned_tokens"] + len(token_ids) <= caps["returned_tokens"]
                    result["services"].append({**lookup, "token_ids": token_ids, "delivered": served})
                    if not served:
                        result["reason"] = "RETURNED_TOKEN_CAP"
                        break
                    result["returned_tokens"] += len(token_ids)
                    result["served_reads"] += int(bool(lookup["source_sha256"]))
                    messages.extend(({"role": "assistant", "content": raw}, {"role": "user", "content": lookup["raw"]}))
                    continue
                result["score"] = core.score_route(core.from_data(task["cell"]), task["goal"], raw)
                if not result["score"]["strict"]:
                    result["reason"] = "INVALID_TURN"
                elif caps["thinks"] and not result["thinks"]:
                    result["reason"] = "THINK_REQUIRED"
                else:
                    result["reason"] = "ROUTE"
                    result["success"] = result["score"]["graph_success"]
                break
            result["status"] = "SCORED"
            result["reason"] = result["reason"] or "TURN_CAP"
    except Exception as failure:
        error = {"type": type(failure).__name__, "message": str(failure)}
        for result in results:
            if result["status"] == "RUNNING":
                result.update(status="ABORTED", reason="STAGE_ERROR")
    ended = clock()
    if ended > deadline and error is None:
        error = {"type": "ActorError", "message": "stage deadline at end"}
    complete = error is None and all(result["status"] == "SCORED" for result in results)
    return {"schema": SCHEMA + "/report", "roster_sha256": roster["sha256"], "actor_config": settings,
            "deadline": deadline, "started": started, "ended": ended, "status": "COMPLETE" if complete else "FAILED",
            "error": error, "results": results, "attempts": attempts, "summary": summarize(results, roster["stage"], complete),
            "calls": len(attempts), "possible_calls": caps["possible_calls"], "fits": 0, "updates": 0,
            "material_origin": roster["material_origin"], "native_custody_verified": False,
            "outer_release_required": True, "full_assay_qualified": False,
            **({"sampling_policy": copy.deepcopy(roster["sampling_policy"])} if roster["stage"] in CUSTOM_STAGES else {})}


def _inputs(roster, expected_sha256, settings, tokenizer, deadline):
    validate_roster(roster, expected_sha256)
    native.number(deadline, positive=True)
    require(deadline <= settings["deadline"] and settings["max_calls"] >= roster["limits"]["possible_calls"]
            and settings["max_output_tokens"] >= 256 and settings["engine"] == native.ENGINE, "actor limits/binding")
    require(all(settings["source_files"].get(path) == checksum for path, checksum in roster["sources"].items()), "required source pins missing")
    require(Path(tokenizer.name_or_path).resolve() == Path(settings["model_path"]).resolve()
            and core.byte_hash(tokenizer.chat_template) == settings["chat_template_sha256"]
            and native.token_ids(tokenizer.encode(settings["tokenizer_probe"]["text"], add_special_tokens=False)) == settings["tokenizer_probe"]["token_ids"],
            "tokenizer binding")


def run_stage(roster, expected_sha256, actor, tokenizer, out, *, actor_config, deadline,
              receipt_reader=read_capture, clock=time.monotonic):
    """Caller owns fresh actor, preparation, close and release. No implicit start."""
    roster, settings = copy.deepcopy(roster), copy.deepcopy(actor_config)
    _inputs(roster, expected_sha256, settings, tokenizer, deadline)
    require(not Path(settings["output_dir"]).exists(), "actor must be fresh/unstarted")
    directory = Path(out)
    require(directory.resolve() != Path(settings["output_dir"]).resolve(), "distinct stage/actor directories required")
    directory.mkdir(parents=False, exist_ok=False)
    def write(name, value):
        with (directory / name).open("xb") as stream:
            stream.write(canonical(value) + b"\n")
    write("roster.json", roster)
    write("binding.json", {"actor_config": settings, "deadline": deadline})
    observations = []
    def observed_clock():
        value = clock()
        native.number(value)
        require(not observations or observations[-1] <= value, "clock regression")
        observations.append(value)
        return value
    def acquire(index, request, limits):
        attempt = {"request": copy.deepcopy(request), "limits": copy.deepcopy(limits), "response": None, "capture": None, "error": None}
        write(f"attempt_{index:04d}_request.json", {"request": request, "limits": limits})
        try:
            attempt["response"] = actor.generate(copy.deepcopy(request), copy.deepcopy(limits))
        except Exception as failure:
            attempt["error"] = {"type": type(failure).__name__, "message": str(failure)}
        try:
            attempt["capture"] = receipt_reader(settings["output_dir"], index)
        except Exception as failure:
            attempt["error"] = {"type": type(failure).__name__, "message": str(failure), "prior": attempt["error"]}
        write(f"attempt_{index:04d}.json", attempt)
        return attempt
    report = _execute(roster, settings, tokenizer, deadline, acquire, observed_clock)
    report = seal({**report, "clock_observations": observations})
    write("report.json", report)
    return report


def replay_validate(roster, expected_sha256, report, tokenizer):
    """Replay exact archived attempts and public service joins; no model calls."""
    _unseal(report)
    _inputs(roster, expected_sha256, report["actor_config"], tokenizer, report["deadline"])
    observations = iter(report["clock_observations"])
    consumed = []
    def clock():
        value = next(observations)
        native.number(value)
        require(not consumed or consumed[-1] <= value, "clock regression")
        consumed.append(value)
        return value
    used = []
    def acquire(index, request, limits):
        used.append(index)
        return copy.deepcopy(report["attempts"][index])
    rebuilt = _execute(roster, report["actor_config"], tokenizer, report["deadline"], acquire, clock)
    require(len(used) == len(report["attempts"]) and list(observations) == [], "extra replay attempts/clocks")
    require(canonical(report) == canonical(seal({**rebuilt, "clock_observations": consumed})), "replay differs")
    return {"local_replay_valid": True, "report_sha256": report["sha256"], "native_custody_verified": False,
            "full_assay_qualified": False}
