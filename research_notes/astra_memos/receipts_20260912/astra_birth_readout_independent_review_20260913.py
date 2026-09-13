"""Stdlib-only independent raw recount. No frozen scorer/import, extraction or native load."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile


STEM = Path("/tmp/astra_birth_readout_independent_review_20260913")
READOUT = Path("/tmp/astra_birth_readout_seed0_20260912_attempt1_capsule.tgz")
VALIDATION = Path("/tmp/astra_birth_readout_seed0_20260912_attempt1_validation.json")
FIT = Path("/tmp/astra_birth_fit_seed0_20260912_attempt1_capsule.tgz")
FIT_VALIDATION = Path("/tmp/astra_birth_fit_seed0_20260912_attempt1_validation.json")
PINS = {
    str(READOUT): "07816cb0649255ddaec5377e0b2ab4442919ea806d2eb60243b0155f1dc96a2a",
    str(VALIDATION): "4a47152320d9b78e16427c25858b9f8d37d2bb054d6db2fcda46128dd2a3a07b",
    str(FIT): "d2460cb3be9b357ae1beecad84ae9bcfc7e76b61d296fb7b359ae9e68d8e2474",
    str(FIT_VALIDATION): "d403b48b645dcc5ebd971a6527108f21287fd722981f128c8780c58a2f1cf770",
}
CELLS = ("OFF", "AUTH", "DERANGED")
OPERATIONS = ("PROSPECT", "REVISE", "ADDITION", "COPY")
FACTORS = {"PROSPECT": ("belief", "goal"), "REVISE": ("expected", "observed", "prior_action")}
FLIPS = dict(belief=("PREDICT_ACTION", "ACT"), goal=("PREDICT_ACTION", "PREDICT_OUTCOME", "ACT"),
             expected=("COMPARE", "POLICY", "NEXT"), observed=("COMPARE", "POLICY", "NEXT"), prior_action=("NEXT",))
DISCLOSURE = ("Reviewer authored downstream /tmp/astra_born_process_readout_20260912.py, but did not author "
              "this original birth runner/corpus. Algorithmically independent recount, not a blinded reviewer: "
              "Main supplied expected counts and reviewer previously inspected scorer interfaces. No frozen "
              "scoring function is imported or invoked; stored results are compared only after all 384 recounts.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value, indent=None):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=indent) + "\n").encode()


def duplicate_free(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(data):
    def nonfinite(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(data, object_pairs_hook=duplicate_free, parse_constant=nonfinite)


def archive(path, receipt):
    files = {}
    with tarfile.open(path, "r:gz") as stream:
        for member in stream:
            require(member.isfile() and not PurePosixPath(member.name).is_absolute()
                    and ".." not in PurePosixPath(member.name).parts and member.name not in files,
                    "unsafe or duplicate archive member")
            require(member.size < 40_000_000, "unexpected oversized metadata")
            files[member.name] = stream.extractfile(member).read()
    require({name: sha(data) for name, data in files.items()} == receipt["archive_files"], "member manifest mismatch")
    return files


def member(files, name):
    return decode(files[name])


def truth(case, arm):
    values, operation = case["inputs"], case["operation"]
    if operation == "PROSPECT":
        matches = [action for action in values["actions"] if values["belief"][action] == values["goal"]]
        require(len(matches) == 1, "nonunique public goal action")
        action = matches[0]
        if arm == "DERANGED":
            action = next(other for other in values["actions"] if other != action)
        return dict(PREDICT_ACTION=action, PREDICT_OUTCOME=values["belief"][action], ACT=action)
    if operation == "REVISE":
        keep = values["expected"] == values["observed"]
        if arm == "DERANGED":
            keep = not keep
        action = values["prior_action"] if keep else next(action for action in values["actions"] if action != values["prior_action"])
        return dict(COMPARE="MATCH" if keep else "MISMATCH", POLICY="KEEP" if keep else "SWITCH", NEXT=action)
    if operation == "ADDITION":
        return {"ADDITION": values["left"] + values["right"]}
    require(operation == "COPY", "unknown public operation")
    return {"COPY": values["literal"]}


def canonical(operation, fields):
    if operation == "PROSPECT":
        return f"PREDICT: {fields['PREDICT_ACTION']} -> {fields['PREDICT_OUTCOME']}\nACT: {fields['ACT']}"
    if operation == "REVISE":
        return f"COMPARE: {fields['COMPARE']}\nPOLICY: {fields['POLICY']}\nNEXT: {fields['NEXT']}"
    return f"ACT: {fields['ADDITION']}" if operation == "ADDITION" else "COPY: " + fields["COPY"]


def parse_raw(operation, raw):
    token = r"([A-Za-z0-9_-]+)"
    patterns = dict(PREDICT=r"\bPREDICT:[ \t]*" + token + r"[ \t]*->[ \t]*" + token,
                    ACT=r"\bACT:[ \t]*" + token, COMPARE=r"\bCOMPARE:[ \t]*" + token,
                    POLICY=r"\bPOLICY:[ \t]*" + token, NEXT=r"\bNEXT:[ \t]*" + token,
                    COPY=r"\bCOPY:[ \t]*" + token)
    allowed = {"PROSPECT": ("PREDICT", "ACT"), "REVISE": ("COMPARE", "POLICY", "NEXT"),
               "ADDITION": ("ACT",), "COPY": ("COPY",)}[operation]
    counts = Counter(re.findall(r"\b(PREDICT|ACT|COMPARE|POLICY|NEXT|COPY)[ \t]*:", raw))
    fields = {}
    for label in allowed:
        pattern = r"\bACT:[ \t]*([+-]?[0-9]+)" if operation == "ADDITION" else patterns[label]
        matches = list(re.finditer(pattern, raw))
        if counts[label] != 1 or len(matches) != 1:
            continue
        if label == "PREDICT":
            fields.update(PREDICT_ACTION=matches[0][1], PREDICT_OUTCOME=matches[0][2])
        elif operation == "ADDITION":
            fields["ADDITION"] = int(matches[0][1])
        else:
            fields[label] = matches[0][1]
    strict_patterns = {
        "PROSPECT": r"PREDICT:[ \t]*" + token + r"[ \t]*->[ \t]*" + token + r"[ \t]*\nACT:[ \t]*" + token,
        "REVISE": r"COMPARE:[ \t]*(MATCH|MISMATCH)[ \t]*\nPOLICY:[ \t]*(KEEP|SWITCH)[ \t]*\nNEXT:[ \t]*" + token,
        "ADDITION": r"ACT:[ \t]*([+-]?[0-9]+)", "COPY": r"COPY:[ \t]*" + token,
    }
    strict = re.fullmatch(strict_patterns[operation], raw.strip()) is not None
    return fields, strict, any(count and label not in allowed for label, count in counts.items()), dict(counts)


def score(case, raw, assigned_arm):
    operation = case["operation"]
    fields, strict, spill, counts = parse_raw(operation, raw)
    auth, own = truth(case, "AUTH"), truth(case, assigned_arm)
    auth_fields = {key: fields.get(key) == value for key, value in auth.items()}
    own_fields = {key: fields.get(key) == value for key, value in own.items()}
    auth_joint, own_joint = all(auth_fields.values()), all(own_fields.values())
    exact_auth, exact_own = raw == canonical(operation, auth), raw == canonical(operation, own)
    compliant = strict and own_joint and not spill
    if operation in ("ADDITION", "COPY"):
        compliant = raw in (canonical(operation, own), canonical(operation, own) + "\n") and not spill
    return dict(operation=operation, fields=fields, strict_surface=strict, tag_spill=spill,
                auth_fields=auth_fields, own_map_fields=own_fields, auth_joint_semantic=auth_joint,
                own_map_joint_semantic=own_joint, auth_strict_joint=strict and auth_joint,
                own_map_strict_joint=strict and own_joint, exact_auth=exact_auth, exact_own_map=exact_own,
                instruction_compliant=compliant, auth_truth=auth, assigned_truth=own, tag_counts=counts)


def check_public(case):
    values, context, operation = case["inputs"], case["context"], case["operation"]
    if operation == "PROSPECT":
        arrows = dict(re.findall(r"([a-z]+) -> ([a-z]+)", context))
        require(arrows == values["belief"] and re.search(r"GOAL: ([a-z]+)", context)[1] == values["goal"], "public belief/goal differs")
    elif operation == "REVISE":
        for label, key in (("EXPECTED", "expected"), ("OBSERVED", "observed")):
            require(re.search(label + r": ([a-z]+)", context)[1] == values[key], "public revision factor differs")
        require(re.search(r"PRIOR: ACT ([a-z]+)", context)[1] == values["prior_action"], "public prior differs")
        order = re.search(r"ACTIONS: ([a-z]+), ([a-z]+)", context).groups()
        require(list(order) == values["action_order"], "public action order differs")
    elif operation == "ADDITION":
        numbers = [int(value) for value in re.findall(r"[+-]?[0-9]+", context)]
        require(numbers == [values["left"], values["right"]], "public arithmetic operands differ")
    else:
        require(values["literal"] in context, "public copy literal differs")


def metrics(rows):
    names = ("strict_surface", "auth_joint_semantic", "own_map_joint_semantic", "auth_strict_joint", "own_map_strict_joint",
             "exact_auth", "exact_own_map", "instruction_compliant", "tag_spill")
    result = dict(total=len(rows), **{name: sum(row[name] for row in rows) for name in names})
    for kind in ("auth_fields", "own_map_fields"):
        result[kind] = {field: sum(row[kind][field] for row in rows) for field in rows[0][kind]}
    return result


def independent_pairs(cases):
    pairs = {name: [] for name in FLIPS}
    for first, second in itertools.combinations(cases, 2):
        if first["operation"] not in FACTORS or any(first[key] != second[key] for key in ("operation", "instance_id", "template")):
            continue
        changed = [name for name in FACTORS[first["operation"]] if first["inputs"][name] != second["inputs"][name]]
        if len(changed) == 1:
            pairs[changed[0]].append([first["id"], second["id"]])
    return pairs


def twins(pairs, rows):
    indexed = {row["case_id"]: row for row in rows}
    result = {}
    for factor, edges in pairs.items():
        details = []
        for first_id, second_id in edges:
            first, second = indexed[first_id], indexed[second_id]
            changed = all(field in first["fields"] and field in second["fields"] and first["fields"][field] != second["fields"][field]
                          for field in FLIPS[factor])
            details.append(dict(case_ids=[first_id, second_id], full_required_flip=changed,
                                auth_strict_pass=changed and first["auth_strict_joint"] and second["auth_strict_joint"],
                                own_map_strict_pass=changed and first["own_map_strict_joint"] and second["own_map_strict_joint"],
                                auth_semantic_pass=changed and first["auth_joint_semantic"] and second["auth_joint_semantic"],
                                own_map_semantic_pass=changed and first["own_map_joint_semantic"] and second["own_map_joint_semantic"]))
        result[factor] = dict(total=len(details), rows=details, **{key: sum(row[key] for row in details)
                            for key in ("auth_strict_pass", "own_map_strict_pass", "auth_semantic_pass", "own_map_semantic_pass")})
    return result


def costs(files, validation):
    launch = member(files, "metadata/launch/launch.json")
    exit_receipt = member(files, "metadata/launch/exit.json")
    controller = member(files, "metadata/run/run/controller.json")
    collection = member(files, "metadata/collection/started.json")
    require(exit_receipt["returncode"] == 0 and launch["pid"] == controller["pid"]
            and exit_receipt["launch_sha256"] == sha(files["metadata/launch/launch.json"]), "launch/controller exit join differs")
    elapsed = validation["released_wall"] - launch["started_wall"]
    require(abs(elapsed - validation["launch_to_release_seconds"]) < 1e-6, "launch-to-release arithmetic differs")
    collection_elapsed = validation["released_wall"] - collection["started_wall"]
    require(abs(collection_elapsed - validation["collection_seconds"]) < 0.01, "collection clock mismatch")
    require(validation["costs_nested_not_added"] is True and elapsed <= launch["controller_seconds"] + 300,
            "registered phase window differs")
    workers = {}
    plan = member(files, "metadata/run/plan.json")
    for cell in plan["members"]:
        prefix = "metadata/run/run/" + cell
        process = member(files, prefix + "/worker/process.json")
        supervision = member(files, prefix + "/worker/supervision.json")
        require(supervision["returncode"] == 0 and supervision["ok"] is True and supervision["error"] is None
                and supervision["owned_group_empty"] and supervision["reservation_release_verified"]
                and supervision["gpu_processes_absent"] and supervision["reserved_seconds"] <= 600,
                "worker release evidence differs")
        workers[cell] = dict(pid=process["pid"], started=process["started"], reserved_seconds=supervision["reserved_seconds"])
    return dict(launch_started_wall=launch["started_wall"], released_wall=validation["released_wall"],
                controller_exit_wall=exit_receipt["ended_wall"], launcher_to_controller_exit_seconds=exit_receipt["ended_wall"] - launch["started_wall"],
                exit_to_collection_start_seconds=collection["started_wall"] - exit_receipt["ended_wall"],
                collection_seconds=validation["collection_seconds"], launch_to_release_seconds=elapsed,
                workers=workers, summed_worker_windows_seconds=sum(row["reserved_seconds"] for row in workers.values()),
                registered_phase_seconds=launch["controller_seconds"], registered_collection_seconds=300)


def recount(files, plan, candidate):
    cases = candidate["dev"]
    require(len(cases) == len({case["id"] for case in cases}) == 128, "fixed128 panel required")
    require(Counter(case["operation"] for case in cases) == Counter(PROSPECT=32, REVISE=64, ADDITION=16, COPY=16), "panel composition differs")
    pairs = independent_pairs(cases)
    require({key: len(value) for key, value in pairs.items()} == dict(belief=16, goal=16, expected=32, observed=32, prior_action=32), "factor twin counts differ")
    require(all({tuple(sorted(edge)) for edge in pairs[name]} == {tuple(sorted(edge)) for edge in candidate["twins"]["dev"][name]}
                for name in pairs), "independently reconstructed twins disagree with candidate")
    for case in cases:
        check_public(case)
    require(len(plan["requests"]) == len(plan["native_inputs"]) == 128 and plan["members"] == list(CELLS)
            and plan["generation"] == dict(max_tokens=64, seed=20260912, temperature=0.0), "registered request panel differs")
    cells = {}
    for cell in CELLS:
        prefix = "metadata/run/run/" + cell
        header = member(files, prefix + "/data/identity.json")
        spec = member(files, prefix + ".spec.json")
        fitted = plan["fit_receipts"].get(cell)
        adapter_files = {} if fitted is None else {key: value for key, value in fitted["adapter_files"].items()
                                                 if key in ("adapter_config.json", "adapter_model.safetensors")}
        expected_identity = dict(backend="vllm", model_input=plan["model"], adapter_input=None if fitted is None else fitted["adapter"],
                                 adapter_files=adapter_files, default_max_tokens=400, default_temperature=0.7,
                                 scope="configured loader inputs; base authentication requires lineage pins")
        require(header["backend"] == expected_identity and header["model_files"] == plan["model_files"]
                and header["adapter_files"] == ({} if fitted is None else fitted["adapter_files"]), "loader header mismatch")
        for key in ("model", "model_files", "source_hashes", "requests", "native_inputs", "sidecar_sha256", "module_sha256", "protocol"):
            require(spec[key] == plan[key], "worker spec-plan mismatch: " + key)
        require(spec["adapter"] == expected_identity["adapter_input"] and spec["adapter_files"] == header["adapter_files"]
                and spec["member"] == cell, "worker adapter/member mismatch")
        process = member(files, prefix + "/worker/process.json")
        supervision = member(files, prefix + "/worker/supervision.json")
        isolation = member(files, prefix + "/data/isolation.json")
        ready = member(files, prefix + "/data/backend.ready.json")
        cleanup = member(files, prefix + "/data/backend.cleanup.json")
        controller = member(files, "metadata/run/run/controller.json")
        require(isolation == dict(pid=process["pid"], pgid=process["pgid"], parent_pid=controller["pid"],
                                  spec_sha256=sha(files[prefix + ".spec.json"]), parent_calls=0, task_prefix="", online_updates=False),
                "worker isolation/spec join differs")
        require(ready["pid"] == process["pid"] and 0 <= ready["ready"] - process["started"] <= 180
                and cleanup["closed"] is True and cleanup["error"] is None, "load/close receipt differs")
        manifest = member(files, prefix + "/data/manifest.json")
        actual = {name[len(prefix + "/data/"):]: sha(data) for name, data in files.items()
                  if name.startswith(prefix + "/data/") and not name.endswith("/manifest.json")}
        require(manifest["files"] == actual, "capture manifest mismatch")
        call_prefix = prefix + "/data/calls/"
        require({name[len(call_prefix):] for name in files if name.startswith(call_prefix)} ==
                {f"{index:04d}.{kind}.json" for index in range(128) for kind in ("request", "response")}, "call pair inventory differs")
        rows, previous = [], ready["ready"]
        for index, case in enumerate(cases):
            call_id = f"{index:04d}"
            request_path, response_path = call_prefix + call_id + ".request.json", call_prefix + call_id + ".response.json"
            sent, received = member(files, request_path), member(files, response_path)
            response = received["response"]
            expected = dict(call_id=call_id, case_id=case["id"], role="readout", arm="readout", prompt=case["context"],
                            max_tokens=64, seed=20260912, temperature=0.0)
            require(sent["request"] == expected == plan["requests"][index] and sent["identity"] == expected_identity,
                    "exact call routing/prompt/loader differs")
            require(sent["prompt_sha256"] == sha(encoded(case["context"])) and received["response_sha256"] == sha(encoded(response)),
                    "raw request/response canonical hash differs")
            require(all(type(clock) in (int, float) and math.isfinite(clock) for clock in (sent["started"], received["ended"]))
                    and previous <= sent["started"] <= received["ended"] <= process["started"] + supervision["reserved_seconds"], "call clock/order/window differs")
            duration = received["ended"] - sent["started"]
            require(duration <= 120, "call limit exceeded")
            previous = received["ended"]
            for key in ("prompt_token_ids", "output_token_ids"):
                require(type(response[key]) is list and all(type(token) is int and token >= 0 for token in response[key]), "raw token IDs invalid")
            require(0 < len(response["prompt_token_ids"]) <= 16384 - 64 and len(response["output_token_ids"]) <= 64, "native length bounds differ")
            require(all(response[key] == plan["native_inputs"][index][key] for key in ("prompt_token_ids", "rendered_prompt")),
                    "stored native request rendering/tokens differ")
            require(response["rendered_prompt"].count(case["context"]) == 1, "raw public context not isolated in rendered prompt")
            raw = response["text"]
            require(type(raw) is str, "missing raw output")
            scored = score(case, raw, "DERANGED" if cell == "DERANGED" else "AUTH")
            rows.append(dict(scored, case_id=case["id"], call_id=call_id, cell=cell, raw_text=raw,
                             inputs=case["inputs"], factors=case["factors"], template=case["template"],
                             request_member=request_path, response_member=response_path,
                             request_sha256=sha(files[request_path]), response_sha256=sha(files[response_path]),
                             output_token_ids=response["output_token_ids"], prompt_token_count=len(response["prompt_token_ids"]),
                             output_token_count=len(response["output_token_ids"]), finish_reason=response["finish_reason"],
                             stop_reason=response["stop_reason"], hit_token_limit=len(response["output_token_ids"]) == 64,
                             length_finish=response["finish_reason"] == "length", eos_in_output=plan["eos_token_id"] in response["output_token_ids"],
                             call_seconds=duration))
        usage = dict(calls=len(rows), input_tokens=sum(row["prompt_token_count"] for row in rows),
                     output_tokens=sum(row["output_token_count"] for row in rows), output_token_ceiling=128 * 64,
                     call_seconds=sum(row["call_seconds"] for row in rows), token_limit_calls=sum(row["hit_token_limit"] for row in rows),
                     length_finish_calls=sum(row["length_finish"] for row in rows), eos_in_output_calls=sum(row["eos_in_output"] for row in rows),
                     model_load_seconds=ready["ready"] - process["started"], worker_seconds=supervision["reserved_seconds"])
        cells[cell] = dict(identity=expected_identity, operations={op: metrics([row for row in rows if row["operation"] == op]) for op in OPERATIONS},
                           twins=twins(pairs, rows), usage=usage, rows=rows)
    require(sum(len(cell["rows"]) for cell in cells.values()) == 384, "all384 required before comparison")
    return cells


def registered(cells, criteria):
    result = {}
    for cell in ("AUTH", "DERANGED"):
        checks = {}
        for op in ("PROSPECT", "REVISE"):
            values = cells[cell]["operations"][op]
            minimum = math.ceil(values["total"] * criteria["conditional_fraction"][0] / criteria["conditional_fraction"][1])
            checks[op] = dict(observed=values[criteria["conditional_metric"]], required=minimum, passed=values[criteria["conditional_metric"]] >= minimum)
        for factor, values in cells[cell]["twins"].items():
            minimum = math.ceil(values["total"] * criteria["twin_fraction"][0] / criteria["twin_fraction"][1])
            checks["twin_" + factor] = dict(observed=values[criteria["twin_metric"]], required=minimum, passed=values[criteria["twin_metric"]] >= minimum)
        for op in ("ADDITION", "COPY"):
            values = cells[cell]["operations"][op]
            minimum = math.ceil(values["total"] * criteria["anchor_fraction"][0] / criteria["anchor_fraction"][1])
            checks[op] = dict(observed=values[criteria["anchor_metric"]], required=minimum, passed=values[criteria["anchor_metric"]] >= minimum)
            loss = cells["OFF"]["operations"][op][criteria["anchor_metric"]] - values[criteria["anchor_metric"]]
            checks[op + "_loss_from_OFF"] = dict(observed=loss, maximum=criteria["max_anchor_loss_from_OFF"], passed=loss <= criteria["max_anchor_loss_from_OFF"])
            checks[op + "_tag_spill"] = dict(observed=values["tag_spill"], required=criteria["anchor_tag_spill"], passed=values["tag_spill"] == criteria["anchor_tag_spill"])
        result[cell] = dict(passed=all(row["passed"] for row in checks.values()), checks=checks)
    return result


def selftest():
    case = dict(operation="REVISE", inputs=dict(actions=["dax", "wug"], prior_action="dax", expected="fep", observed="fep"))
    require(truth(case, "AUTH") == dict(COMPARE="MATCH", POLICY="KEEP", NEXT="dax"), "AUTH truth fixture")
    require(truth(case, "DERANGED") == dict(COMPARE="MISMATCH", POLICY="SWITCH", NEXT="wug"), "DERANGED truth fixture")
    require(score(case, "COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax", "AUTH")["own_map_strict_joint"], "strict fixture")
    require(not score(case, "COMPARE: MATCH\nPOLICY: KEEP\nNEXT: wug", "AUTH")["own_map_joint_semantic"], "wrong next fixture")
    require(not score(case, "COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax\nNEXT: wug", "AUTH")["own_map_joint_semantic"], "ambiguous next fixture")
    addition = dict(operation="ADDITION", inputs=dict(left=31, right=48))
    require(score(addition, "ACT: 79", "AUTH")["instruction_compliant"], "addition fixture")
    require(not score(addition, "ACT: 78", "AUTH")["auth_joint_semantic"], "arithmetic error fixture")
    require(not score(addition, "ACT: 79\nPREDICT: F", "AUTH")["instruction_compliant"], "spill fixture")
    require(not score(addition, "", "AUTH")["strict_surface"], "empty fixture")


def main():
    selftest()
    for path, pin in PINS.items():
        require(sha(Path(path).read_bytes()) == pin, "input file hash mismatch: " + path)
    validation, fit_validation = decode(VALIDATION.read_bytes()), decode(FIT_VALIDATION.read_bytes())
    for receipt in (validation, fit_validation):
        require(receipt["status"] == "COLLECTED_RELEASED" and receipt["phase_complete"] is True
                and receipt["full_release"] is True and receipt["automatic_L1_pass"] is False, "completed bounded release required")
    files, fit_files = archive(READOUT, validation), archive(FIT, fit_validation)
    require(len(files) == 814 and len(fit_files) == 39, "archive inventory differs")
    plan, fit_plan = member(files, "metadata/run/plan.json"), member(fit_files, "metadata/run/plan.json")
    require(sha(files["metadata/run/plan.json"]) == validation["plan_sha256"]
            and sha(fit_files["metadata/run/plan.json"]) == plan["fit_plan_sha256"] == fit_validation["plan_sha256"], "plan pins differ")
    require(plan["fit_release_sha256"] == PINS[str(FIT_VALIDATION)] and fit_validation["archive_sha256"] == PINS[str(FIT)]
            and validation["archive_sha256"] == PINS[str(READOUT)], "readout-fit release join differs")
    candidate = member(fit_files, "metadata/run/material/candidate.json")
    require(sha(encoded(candidate)) == plan["candidate_sha256"] == fit_plan["candidate_sha256"], "candidate value hash differs")
    for key in ("model", "model_files", "source_hashes", "module_sha256", "sidecar_sha256", "primary_criteria", "primary_criteria_sha256"):
        require(plan[key] == fit_plan[key], "fit-readout fixed source/base/criteria join differs: " + key)
    linked = 0
    for path, pin in plan["input_hashes"].items():
        if path.startswith(plan["fit_root"] + "/"):
            local = "metadata/run/" + path[len(plan["fit_root"]) + 1:]
            require(local in fit_files and sha(fit_files[local]) == pin, "fit input member differs: " + local)
            linked += 1
    for arm in ("AUTH", "DERANGED"):
        require(member(fit_files, "metadata/run/run/" + arm + "/receipt.json") == plan["fit_receipts"][arm], "fit adapter receipt join differs")
        for case in candidate["train"][arm]:
            require(case["response"] == canonical(case["operation"], truth(case, arm)), "independent map disagrees with public training assignment")
    cells = recount(files, plan, candidate)
    report = dict(schema="independent-birth-raw-review-v1", generated_utc=datetime.now(timezone.utc).isoformat(),
                  reviewer_disclosure=DISCLOSURE, inputs=PINS, review_source_sha256=sha(Path(__file__).read_bytes()),
                  verified_archive_members=dict(readout=len(files), fit=len(fit_files)), verified_fit_input_links=linked,
                  source_hashes=plan["source_hashes"], base_model=plan["model"], base_model_files=plan["model_files"],
                  candidate_value_sha256=plan["candidate_sha256"], candidate_file_sha256=sha(fit_files["metadata/run/material/candidate.json"]),
                  raw_count=384, cells=cells, registered_criteria=plan["primary_criteria"], registered_conjunction=registered(cells, plan["primary_criteria"]),
                  costs=dict(readout=costs(files, validation), fit=costs(fit_files, fit_validation)),
                  claim="SOURCE_AUTHORED_BIRTH_NOT_CLEAN", origin="UNRESOLVED_LOCAL_HASHES_ONLY",
                  limitations=["one authored root, one seed, exploratory fixed dev diagnostic", "not independent holdout or clean ancestry",
                               "loader/token identity checked against pinned metadata; no independent tokenizer decode or full base/adapter weight rehash",
                               "no L1/G3/P1/G5/H1/H2/birth-impact promotion", "semantic parsing requires unique canonical uppercase tags; formatting audited separately"],
                  comparison=dict(status="PENDING_AFTER_COMPLETE_RAW_RECOUNT"))
    paired = report["costs"]["fit"]["launch_to_release_seconds"] + report["costs"]["readout"]["launch_to_release_seconds"]
    require(abs(paired - validation["paired_launch_to_release_seconds"]) < 1e-6 and paired <= 5100, "paired phase cost differs")
    report["costs"].update(paired_launch_to_release_seconds=paired, paired_cap_seconds=5100,
                          calendar_first_launch_to_final_release_seconds=validation["released_wall"] - report["costs"]["fit"]["launch_started_wall"],
                          fit_release_to_readout_launch_gap_seconds=report["costs"]["readout"]["launch_started_wall"] - fit_validation["released_wall"],
                          nested_not_additive=True)
    STEM.with_suffix(".json").write_bytes(encoded(report, indent=2))
    print(json.dumps({cell: dict(operations=cells[cell]["operations"], twins={factor: values["own_map_strict_pass"] for factor, values in cells[cell]["twins"].items()},
                                usage=cells[cell]["usage"]) for cell in CELLS}, indent=2))
    print("384 raw rows recounted; frozen score comparison not yet performed.")


if __name__ == "__main__":
    main()
