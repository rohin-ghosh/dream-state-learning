"""Sealed disposable OLD formation only; caller owns native actor and lifecycle.

Whole-response admissions never create or repair child targets. Local capture
joins do not certify native process identity, release, or training permission.
"""

import hashlib
import json
import math
from pathlib import Path

from gpu import astra_pcfl_native_actor as actor_api
from gpu import astra_pcfl_lf_actor as lf_api
from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_formation_plan as planner


SCHEMA = "pcfl.own_write_old_formation.v1"
POLICY = "public_session_history_whole_response_stop_only_format_public_pair_semantics_v5"
LINK_PAIR_POLICY = "requested_preselected_already_admitted_event_handles_v1"
LINK_SEMANTICS_RULE = (
    "VIA is the shared node: copy the GOT node of the first EVENT and verify it equals the AT node of the second EVENT. "
    "Do not use the AT node of the first EVENT. "
    "EVIDENCE lists the first EVENT receipt followed by the second EVENT receipt, in that order."
)
LF_COMMITMENT_RULE = (
    "End your response with exactly one LF (U+000A) after the last identifier. "
    "Emit the actual newline character, not the literal characters backslash-n (\\n). "
    "Do not add a blank line."
)
KINDS = [kind for _ in range(8) for kind in ("EXPLORE", "EVENT")] + ["LINK"] * 4
CONFIG_FIELDS = {"schema", "policy", "source_pins", "planner", "actor_config",
                 "seed", "limits", "slots", "format_scaffold", "link_pair_policy", "sha256"}


class FormationError(ValueError):
    pass


def commitment_prompt(prompt):
    return prompt + "\n" + LF_COMMITMENT_RULE


def requested_link_prompt(prompt, pair, public_event_handles):
    require(type(pair) is list and len(pair) == 2 and pair[0] != pair[1]
            and all(handle in public_event_handles for handle in pair),
            "requested pair must already be admitted public events")
    return commitment_prompt(prompt + "\nFor this controlled recording task, use the already-observed event addresses "
                             + pair[0] + " then " + pair[1] + " in that order. "
                             "Derive the shared node and evidence references only from your actual public EVENT commitments.\n"
                             + LINK_SEMANTICS_RULE)


def require(condition, message):
    if not condition:
        raise FormationError(message)


def seal(value):
    return {**detached(value), "sha256": digest(value)}


def canonical(value):
    return actor_api.canonical(value)


def digest(value):
    return actor_api.digest(value)


def detached(value):
    return json.loads(canonical(value))


def source_pins():
    paths = [Path(__file__), Path(actor_api.__file__), Path(lf_api.__file__), Path(planner.__file__),
             Path(core.__file__), Path(planner.prepare.__file__)]
    return {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def build_config(cell, actions, link_choices, *, actor_config, seed, limits):
    """Seal caller choices/config before outputs; no defaults or selection."""
    plan = planner.build_plan(cell, actions, link_choices)
    require(cell.root.label == "disposable/0", "only disposable/0 OLD formation")
    require(len(plan["first_blocks"]) == 17, "AUTH needs exactly 17 first blocks")
    require(type(seed) is int and 0 <= seed < 2**63, "invalid formation seed")
    require(type(actor_config) is dict and set(actor_config) == actor_api.CONFIG_FIELDS,
            "closed existing actor config required")
    require(actor_config["schema"] == actor_api.SCHEMA and
            actor_config["engine"] == actor_api.ENGINE, "frozen C0 engine required")
    require(type(actor_config["max_calls"]) is int and actor_config["max_calls"] == 20,
            "dedicated actor must have exactly 20 call slots")
    pins = source_pins()
    require(all(actor_config["source_files"].get(path) == expected
                for path, expected in pins.items()), "actor must bind formation source pins")
    fields = {"output_tokens", "returned_tokens", "remaining_reads", "deadline",
              "device_seconds", "input_tokens"}
    require(type(limits) is dict and set(limits) == fields, "closed fixed limits required")
    for key, maximum in (("output_tokens", actor_config["max_output_tokens"]),
                         ("input_tokens", actor_config["max_input_tokens"])):
        require(type(limits[key]) is int and type(maximum) is int
                and 0 < limits[key] <= maximum, "invalid " + key)
    require(type(limits["remaining_reads"]) is int and limits["remaining_reads"] == 0
            and type(limits["returned_tokens"]) is int and limits["returned_tokens"] == 0,
            "formation has no READ service")
    for key, maximum in (("deadline", actor_config["deadline"]),
                         ("device_seconds", actor_config["device_seconds_cap"])):
        require(_finite(limits[key]) and _finite(maximum)
                and 0 < limits[key] <= maximum, "invalid " + key)
    slots = [{"id": f"old/formation/{index:02d}", "kind": kind}
             for index, kind in enumerate(KINDS)]
    return seal(dict(schema=SCHEMA + "/config", policy=POLICY, source_pins=pins,
                     link_pair_policy=LINK_PAIR_POLICY,
                     format_scaffold={"policy": lf_api.POLICY, "regex": lf_api.REGEX,
                                      "applies_to": ["EVENT", "LINK"], "readout": "UNCONSTRAINED"},
                     planner=plan, actor_config=actor_config, seed=seed,
                     limits=limits, slots=slots))


def validate_config(config, expected_sha256):
    require(type(config) is dict and set(config) == CONFIG_FIELDS, "config fields")
    require(config["sha256"] == expected_sha256 and
            digest({key: value for key, value in config.items() if key != "sha256"})
            == expected_sha256, "config seal drift")
    plan = config["planner"]
    planner.validate_plan(plan, plan["plan_sha256"])
    rebuilt = build_config(core.from_data(plan["cell"]), plan["actions"],
                           plan["link_choices"], actor_config=config["actor_config"],
                           seed=config["seed"], limits=config["limits"])
    require(canonical(config) == canonical(rebuilt), "config/source drift")
    return True


def _decode_json(raw):
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, "duplicate JSON key in actor receipt")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs)
    canonical(value)
    return value


def read_actor_capture(directory, index):
    """Read existing NativeActor sidecars once, retaining exact file bytes.

    Missing files remain absent so an interrupted actor can still be archived.
    Never reads a model, protected process environment, or native GPU state.
    """
    require(type(index) is int and 0 <= index < 20, "capture index")
    names = ["config.json", "identity.json"] + [f"call_{index:04d}.{suffix}.json"
             for suffix in ("request", "render", "raw", "response", "error")]
    files = {}
    for name in names:
        path = Path(directory) / name
        if path.exists():
            require(path.is_file() and path.stat().st_size <= 4 * 1024 * 1024,
                    "bounded actor sidecar required")
            payload = path.read_bytes()
            files[name] = {"utf8": payload.decode("utf-8"),
                           "sha256": hashlib.sha256(payload).hexdigest()}
    return {"schema": SCHEMA + "/capture", "index": index, "files": files}


def _capture_data(capture, index):
    require(type(capture) is dict and set(capture) == {"schema", "index", "files"}
            and capture["schema"] == SCHEMA + "/capture"
            and type(capture["index"]) is int and capture["index"] == index,
            "capture identity differs")
    required = {"config.json", "identity.json"} | {
        f"call_{index:04d}.{suffix}.json" for suffix in ("request", "render", "raw", "response")}
    require(type(capture["files"]) is dict and set(capture["files"]) == required,
            "missing/extra/error actor receipt")
    result = {}
    for name, record in capture["files"].items():
        require(type(record) is dict and set(record) == {"utf8", "sha256"}
                and type(record["utf8"]) is str
                and core.byte_hash(record["utf8"]) == record["sha256"], "actor file byte drift")
        result[name] = _decode_json(record["utf8"])
    return result


def _verify_capture(config, index, request, response, capture, previous_end):
    files = _capture_data(capture, index)
    prefix = f"call_{index:04d}."
    requested, rendered, raw, returned = [files[prefix + suffix + ".json"]
                                         for suffix in ("request", "render", "raw", "response")]
    settings, identity = files["config.json"], files["identity.json"]
    require(settings == config["actor_config"] and
            identity["config_sha256"] == digest(settings), "actor config binding differs")
    native = identity["identity"]
    require(native["repository"] == actor_api.MODEL_NAME and native["revision"] == actor_api.REVISION
            and native["model_binding_sha256"] == settings["model_binding"]["sha256"]
            and native["source_files"] == settings["source_files"]
            and native["environment"] == settings["environment"]
            and native["gpu_uuid_expected"] == settings["gpu_uuid"]
            and native["mount"] == "C0" and native["lora_request"] is None,
            "native model/source/route identity differs")
    require(type(native["model_files"]) is dict and native["model_files"]
            and all(native["model_files"].get(name) == expected
                    for name, expected in settings["tokenizer_files"].items()),
            "native tokenizer file binding differs")
    require(identity["kind"] in ("NATIVE", "INJECTED_CPU_TEST")
            and raw["kind"] == identity["kind"], "capture kind differs")
    request_hash = digest(request)
    require(requested["request"] == request and requested["limits"] == config["limits"]
            and requested["request_sha256"] == raw["request_sha256"] == request_hash,
            "public request/limits hash differs")
    require(raw["mount"] == rendered["mount"] == "C0"
            and raw["lora_request"] is None and rendered["lora_request"] is None,
            "formation adapter contamination")
    require(rendered["sampling"] == lf_api.sampling_for(request, config["limits"]),
            "sampling differs")
    output = raw["raw"]
    require(type(output) is dict and set(output) == {"text", "output_token_ids",
            "prompt_token_ids", "finish_reason", "stop_reason"}, "raw output fields")
    for key in ("prompt_token_ids", "output_token_ids"):
        require(type(output[key]) is list and all(type(token) is int and token >= 0
                                                 for token in output[key]), "typed token IDs required")
    require(output["prompt_token_ids"] == rendered["prompt_token_ids"]
            and 0 < len(output["prompt_token_ids"]) <= config["limits"]["input_tokens"]
            and len(output["output_token_ids"]) <= config["limits"]["output_tokens"],
            "native prompt/output token join differs")
    require(type(output["text"]) is str and (output["output_token_ids"] or not output["text"])
            and type(rendered["rendered_prompt"]) is str and rendered["rendered_prompt"],
            "raw/render text missing")
    require(output["finish_reason"] in ("stop", "length") and
            (output["stop_reason"] is None or type(output["stop_reason"]) in (int, str)),
            "finish receipt differs")
    require(type(response) is dict and set(response) == {"request_sha256", "text",
            "prompt_tokens", "output_tokens", "device_seconds"}
            and returned["response"] == response and response["request_sha256"] == request_hash
            and response["text"] == output["text"] == returned["decoded"]
            and returned["raw_utf8_sha256"] == core.byte_hash(output["text"])
            and returned["raw_hex"] == output["text"].encode("utf-8").hex(),
            "returned/raw response byte join differs")
    for key, tokens in (("prompt_tokens", "prompt_token_ids"), ("output_tokens", "output_token_ids")):
        require(type(response[key]) is int and response[key] == len(output[tokens]), "response token count differs")
    times = [raw[name] for name in ("operation_started", "generation_started", "generation_ended")]
    require(all(_finite(value) for value in times) and previous_end <= times[0] <= times[1] <= times[2]
            and requested["started"] == times[0] and times[2] <= config["limits"]["deadline"]
            and _finite(response["device_seconds"])
            and times[2] - times[0] <= response["device_seconds"] <= config["limits"]["device_seconds"]
            and times[0] + response["device_seconds"] <= config["limits"]["deadline"],
            "capture chronology/budget differs")
    return output, identity["kind"], times[0] + response["device_seconds"]


def _form(config, acquire):
    plan = config["planner"]
    cell = core.from_data(plan["cell"])
    session = core.WorldSession(cell, "OLD")
    history = [{"role": "system", "content": core.FORMATION_SYSTEM}]
    slots = [{**slot, "status": "UNCALLED", "attempt": None, "admission": None,
              "world_result": None, "error": None} for slot in config["slots"]]
    events, receipts, admissions, generations = {}, {}, [], []
    actions, event_raw, link_raw, capture_kinds = [], [], [], []
    previous_end, elapsed = 0, 0
    identity_sha256 = None
    latest = None
    failure = None
    for index, slot in enumerate(slots):
        try:
            kind = slot["kind"]
            if kind == "EXPLORE":
                prompt = session.explore_prompt()
            elif kind == "EVENT":
                prompt = commitment_prompt(latest["public"] + session.event_prompt(latest["receipt"]))
            else:
                prompt = requested_link_prompt(session.link_prompt(), plan["link_choices"][index - 16], events)
            history.append({"role": "user", "content": prompt})
            request = {"id": slot["id"], "messages": detached(history),
                       "seed": config["seed"], "mount": "C0"}
            slot["status"] = "ATTEMPTED"
            attempt = acquire(index, request, detached(config["limits"]))
            slot["attempt"] = detached(attempt)
            require(type(attempt) is dict and set(attempt) == {"request", "limits", "response", "capture", "backend_error"}
                    and attempt["request"] == request and attempt["limits"] == config["limits"],
                    "attempt request differs")
            require(attempt["backend_error"] is None,
                    "actor/capture failure: " + canonical(attempt["backend_error"]).decode("utf-8"))
            output, capture_kind, previous_end = _verify_capture(
                config, index, request, attempt["response"], attempt["capture"], previous_end)
            current_identity = attempt["capture"]["files"]["identity.json"]["sha256"]
            require(identity_sha256 is None or identity_sha256 == current_identity,
                    "actor identity changed during formation")
            identity_sha256 = current_identity
            capture_kinds.append(capture_kind)
            elapsed += attempt["response"]["device_seconds"]
            require(elapsed <= config["actor_config"]["device_seconds_cap"], "aggregate actor budget exceeded")
            require(output["finish_reason"] == "stop", "non-stop output cannot execute/admit")
            raw = output["text"]
            history.append({"role": "assistant", "content": raw})
            if kind == "EXPLORE":
                latest = session.explore(raw)
                slot["world_result"] = latest
                require(latest["ok"], "invalid child action")
                require(raw == plan["actions"][index // 2], "child action differs from pre-output choice")
                actions.append(raw)
            elif kind == "EVENT":
                handle = plan["opportunities"][index // 2]["event_handle"]
                admission = core.admit_event(raw, latest["receipt"], session, handle)
                slot["admission"] = admission
                admissions.append(admission)
                require(admission["accepted"], "child EVENT rejected: " + str(admission.get("error")))
                events[handle], receipts[handle] = admission["row"], latest["receipt"]
                event_raw.append(raw)
            else:
                fields = core.parse_link_line(raw)
                pair = [fields["first"], fields["second"]]
                require(pair == plan["link_choices"][index - 16], "child LINK differs from pre-output choice")
                admission = core.admit_link(raw, [receipts[handle] for handle in pair], session,
                                           plan["links"][index - 16]["link_handle"],
                                           [events[handle] for handle in pair])
                slot["admission"] = admission
                admissions.append(admission)
                require(admission["accepted"], "child LINK rejected: " + str(admission.get("error")))
                link_raw.append(raw)
            if kind != "EXPLORE":
                generations.append({"raw": raw, "sha256": core.byte_hash(raw),
                                    "origin": "CHILD_NATIVE" if capture_kind == "NATIVE" else "CHILD_INJECTED_CPU_TEST",
                                    "capture_sha256": digest(attempt["capture"])})
            slot["status"] = "ACCEPTED"
        except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
            slot["status"] = "FAILED"
            slot["error"] = {"type": type(error).__name__, "message": str(error)}
            failure = {"slot": slot["id"], **slot["error"]}
            break
    binding, payload = None, None
    if failure is None:
        try:
            require(len(set(capture_kinds)) == 1, "mixed native/injected captures")
            binding = planner.bind_child(plan, plan["plan_sha256"], actions, event_raw, link_raw)
            payload = {"rows": binding["rows"], "queries": binding["queries"],
                       "generations": generations, "controls": [],
                       "first_block_slots": planner.first_block_slots(plan, plan["plan_sha256"])}
        except (ValueError, TypeError, KeyError, IndexError) as error:
            failure = {"slot": None, "type": type(error).__name__, "message": str(error)}
    return seal({"schema": SCHEMA + "/report", "config_sha256": config["sha256"],
                 "format_scaffold": detached(config["format_scaffold"]),
                 "link_pair_policy": config["link_pair_policy"],
                 "status": "COMPLETE" if failure is None else "FORMATION_FAILED",
                 "slots": slots, "failure": failure, "world_receipts": core.detached(session.receipts),
                 "admissions": admissions, "formation_binding": binding, "writer_payload": payload,
                 "counts": {"possible_calls": 20, "possible_events": 8, "possible_links": 4,
                            "attempted_calls": sum(slot["attempt"] is not None for slot in slots),
                            "accepted_events": len(event_raw), "accepted_links": len(link_raw)},
                 "capture_kinds": sorted(set(capture_kinds)), "device_seconds": elapsed,
                 "native_custody_verified": False, "full_contract_released": False,
                 "fits": 0, "updates": 0})


def _write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def run_formation(config, expected_sha256, actor, out, *, receipt_reader=None):
    """One-shot formation; actor.generate and existing sidecars are injected.

    An existing out or actor output directory rejects a second attempt. Caller
    owns close/release even after failure; nothing here starts a process.
    """
    config = detached(config)
    validate_config(config, expected_sha256)
    out = Path(out).absolute()
    actor_root = Path(config["actor_config"]["output_dir"]).absolute()
    require(not out.exists() and not out.is_symlink(), "formation archive already exists")
    require(not actor_root.exists() and not actor_root.is_symlink(), "dedicated actor already used")
    protected = [actor_root, Path(config["actor_config"]["model_path"]).absolute()]
    require(all(out != path and out not in path.parents and path not in out.parents for path in protected),
            "formation archive overlaps actor/model")
    out.mkdir(parents=False, exist_ok=False)
    _write(out / "config.json", config)
    reader = receipt_reader or (lambda index: read_actor_capture(actor_root, index))

    def acquire(index, request, limits):
        _write(out / f"call_{index:02d}.request.json", {"request": request, "limits": limits})
        response, capture, error = None, None, None
        try:
            response = actor.generate(detached(request), detached(limits))
        except Exception as caught:
            error = {"type": type(caught).__name__, "message": str(caught)}
        try:
            capture = reader(index)
        except Exception as caught:
            error = {"actor_error": error, "capture_error": {"type": type(caught).__name__, "message": str(caught)}}
        attempt = {"request": request, "limits": limits, "response": response,
                   "capture": capture, "backend_error": error}
        _write(out / f"call_{index:02d}.attempt.json", attempt)
        return attempt

    report = _form(config, acquire)
    try:
        validate_config(config, expected_sha256)
    except Exception as error:
        _write(out / "formation_failure.json", {"type": type(error).__name__, "message": str(error),
                                                "config_sha256": expected_sha256})
        raise
    _write(out / "formation.json", report)
    return report


def replay_validate(config, expected_sha256, report):
    """CPU-only replay; successful receipt joins are not native attestation."""
    validate_config(config, expected_sha256)
    require(type(report) is dict and "sha256" in report and
            digest({key: value for key, value in report.items() if key != "sha256"}) == report["sha256"],
            "report seal drift")
    require(type(report.get("slots")) is list and len(report["slots"]) == 20, "fixed slot denominator")

    def acquire(index, request, limits):
        return detached(report["slots"][index]["attempt"])

    rebuilt = _form(config, acquire)
    require(canonical(report) == canonical(rebuilt), "formation replay differs")
    return {"report_sha256": report["sha256"], "config_sha256": expected_sha256,
            "status": report["status"], "local_replay_valid": True,
            "native_custody_verified": False, "full_contract_released": False}
