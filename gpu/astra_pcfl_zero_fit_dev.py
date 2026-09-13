"""Separate, finite C0-only diagnostic; never a full v2.2 release or fit path."""
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import astra_pcfl_native_actor as native
from gpu import astra_pcfl_vertical_dev as runtime
from organism_v6 import pcfl_vertical_dev as core


SCHEMA = "PCFL_C0_ZERO_FIT_DIAGNOSTIC_V1"
ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "research_notes/astra_memos/ASTRA_PCFL_ZERO_FIT_SCOPE_2026-09-13.md"
WORLD = ROOT / "research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md"
INVENTORY = ROOT / "research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md"
canonical, digest = native.canonical, native.digest
require = native.require


def _seal(data):
    payload = copy.deepcopy(data)
    return {**payload, "sha256": digest(payload)}


def _unseal(data):
    require(type(data) is dict and "sha256" in data, "sealed object required")
    payload = {key: value for key, value in data.items() if key != "sha256"}
    require(digest(payload) == data["sha256"], "seal drift")
    return payload


def _record(data, fields):
    require(type(data) is dict and set(data) == set(fields), "closed fields differ")


def _file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_snapshot():
    return {str(Path(path).resolve()): _file_hash(path) for path in
            (__file__, core.__file__, runtime.__file__, native.__file__, SCOPE, WORLD, INVENTORY)}


def build_tasks(root_wires):
    """Only reuse expansion, not the frozen scripted/full-assay constructor."""
    require(type(root_wires) is list and len(root_wires) == 4, "four excluded roots required")
    roots = [core.from_data(wire) for wire in root_wires]
    require([root.label for root in roots] == [f"excluded/{index}" for index in range(4)], "excluded root order")
    require(core.production_binding_status()["definition_bound"] is True, "production world unresolved")
    contract = {"bindings": {"root_registry": [{"role": "excluded", "wire": wire} for wire in root_wires]}}
    expanded = runtime.prepare_scripted_plan(contract)
    tasks = expanded["tasks"]
    slots = [{"task": task["id"], "turn": turn, "id": f"{core.byte_hash(task['id'])}/actor/{turn}",
              "seed": task["seed"], "mount": "C0"}
             for task in tasks for turn in range(13 if task["projection"] == "ACTIVE_LINKED_TEXT" else 1)]
    require(len(tasks) == 800 and len(slots) == 1952, "fixed task/call-slot counts")
    return _seal({"schema": SCHEMA, "roots": root_wires, "tasks": tasks, "call_slots": slots,
                  "continuation": "pinned Runtime._task exact READ/assistant then exact service/user transcript",
                  "material_origin": "RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD",
                  "actor_tokens_per_task": 2048, "returned_tokens_per_task": 4096,
                  "reads_per_task": 12, "fits": 0, "updates": 0})


def _render(tokenizer, messages):
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    require(type(text) is str and text, "rendered text required")
    ids = native.token_ids(tokenizer.encode(text, add_special_tokens=False))
    templated = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    if isinstance(templated, dict):
        templated = templated.get("input_ids")
    require(ids and ids == native.token_ids(templated), "template/encode mismatch")
    return text, ids


def tokenizer_binding(actor_config):
    return {key: copy.deepcopy(actor_config[key]) for key in
            ("model_path", "tokenizer_files", "chat_template_sha256")}


def measure_tokenizer(plan, tokenizer, binding, *, synthetic=False):
    """Caller-run measurements of used zero-fit surfaces, never model loading.

    This checks the supplied inventory, not its allocator search history. No
    unused EVENT_TWIN/LINK_PERMUTE/training schedule is required or certified.
    """
    _unseal(plan)
    _record(binding, ("model_path", "tokenizer_files", "chat_template_sha256"))
    require(type(synthetic) is bool, "synthetic flag must be Boolean")
    require(type(tokenizer.chat_template) is str and core.byte_hash(tokenizer.chat_template) == binding["chat_template_sha256"], "chat template pin drift")
    if not synthetic:
        require(Path(tokenizer.name_or_path).resolve() == Path(binding["model_path"]).resolve(), "actual tokenizer path")
        require(set(binding["tokenizer_files"]) == native.TOKENIZER_FILES, "tokenizer file inventory")
        for name, expected in binding["tokenizer_files"].items():
            require(_file_hash(Path(binding["model_path"]) / name) == expected, "tokenizer file drift")
    measurements, groups = [], defaultdict(list)

    def record(identifier, text, group, ids=None):
        observed = native.token_ids(tokenizer.encode(text, add_special_tokens=False)) if ids is None else ids
        require(observed, "empty token measurement")
        measurements.append({"id": identifier, "text": text, "text_sha256": core.byte_hash(text), "token_ids": observed})
        groups[group].append(identifier)

    opaque = []
    private = []
    for wire in plan["roots"]:
        private.append(wire["label"])
        for namespace, members in wire["inventory"].items():
            for slot, value in members.items():
                record(f"opaque/{wire['label']}/{namespace}/{slot}", value, "opaque")
                opaque.append(value)
                if namespace == "goal":
                    private.append(value)
    require(len(opaque) == len(set(opaque)), "opaque collision")
    for task in plan["tasks"]:
        messages = [{"role": "system", "content": task["public"]["system"]},
                    {"role": "user", "content": task["public"]["user"]}]
        text, ids = _render(tokenizer, messages)
        require(not any(value in text for value in private), "private root/goal ID exposed")
        render_id = task["id"].split("/")[-2] if task["panel"] == "reachout" else "TASK"
        require(render_id in ("RA", "RB") if task["panel"] == "reachout" else render_id == "TASK", "unregistered initial render")
        record("initial/" + task["id"], text, f"initial/{task['panel']}/{task['projection']}/{render_id}", ids)
        for index, (request, query) in enumerate(task["queries"].items()):
            core.read_query(task["queries"], request)
            record(f"query/{task['id']}/{index}", request, "query/" + request.split()[1])
            block = query["target"]
            require(not any(value in block for value in private), "private service bytes")
            record(f"block/{task['id']}/{index}", block, f"block/{block.split()[0]}/{len(block.splitlines())}")
    record("service/MISS", "MISS", "service/MISS")
    result = _seal({"schema": SCHEMA + "/tokens", "kind": "SYNTHETIC" if synthetic else "ACTUAL_OFFLINE",
                    "plan_sha256": plan["sha256"], "binding": binding, "measurements": measurements,
                    "groups": dict(groups), "scope": "used IDs/initial requests/READs/blocks only; not allocator or full-fit qualification"})
    _check_measurements(result)
    return result


def _check_measurements(receipt):
    _unseal(receipt)
    indexed = {entry["id"]: entry for entry in receipt["measurements"]}
    require(len(indexed) == len(receipt["measurements"]), "duplicate measurement ID")
    for entry in indexed.values():
        _record(entry, ("id", "text", "text_sha256", "token_ids"))
        require(core.byte_hash(entry["text"]) == entry["text_sha256"], "measured text drift")
        require(native.token_ids(entry["token_ids"]), "empty token IDs")
    used = []
    for group, members in receipt["groups"].items():
        require(type(members) is list and members and all(member in indexed for member in members), "missing substitution measurement")
        lengths = {len(indexed[member]["token_ids"]) for member in members}
        require(len(lengths) == 1, "unequal used substitution token lengths: " + group)
        used.extend(members)
    require(sorted(used) == sorted(indexed), "substitution coverage")
    opaque = receipt["groups"].get("opaque", [])
    require(opaque and 4 <= len(indexed[opaque[0]]["token_ids"]) <= 12, "opaque common L must be 4..12")
    require(len({tuple(indexed[member]["token_ids"]) for member in opaque}) == len(opaque), "opaque token collision")


def _construct(roots):
    status = core.production_binding_status()
    require(status["definition_bound"] is True and status["source_sha256"] == _file_hash(WORLD), "bound-world source absent/drifted")
    audit = core.audit_construct([core.from_data(wire) for wire in roots])
    require(audit["route_construct_passed"] is True and audit["worlds"] == 32 and audit["delayed_tasks"] == 64
            and len(audit["route_cut_decisions"]) == 192 and len(audit["atoms_link_decisions"]) == 48
            and len(audit["entropy_quartets"]) == 16, "bound CPU world audit failed")
    return audit


def build_manifest(plan, measurements, actor_config, *, wall_seconds, device_seconds, output_dir, test_only=False):
    """Return a separate executable diagnostic manifest, not a v2.2 contract."""
    for value in (wall_seconds, device_seconds):
        require(runtime.finite(value) and 0 < value <= 36000, "finite scoped budget required")
    manifest = _seal({"schema": SCHEMA, "plan": plan, "measurements": measurements,
                      "actor": actor_config, "sources": source_snapshot(), "construct": _construct(plan["roots"]),
                      "wall_seconds": wall_seconds, "device_seconds": device_seconds,
                      "output_dir": str(output_dir), "test_only": test_only,
                      "panels": {"delayed": {key: list(value) for key, value in runtime.DELAYED.items()},
                                 "reachout": {key: list(value) for key, value in runtime.REACHOUT.items()}},
                      "full_v22_release": False, "fits": 0, "updates": 0})
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest, tokenizer=None):
    payload = _unseal(manifest)
    _record(payload, ("schema", "plan", "measurements", "actor", "sources", "construct", "wall_seconds",
                      "device_seconds", "output_dir", "test_only", "panels", "full_v22_release", "fits", "updates"))
    require(payload["schema"] == SCHEMA and type(payload["test_only"]) is bool, "scope/test mode")
    require(payload["full_v22_release"] is False and type(payload["fits"]) is int and payload["fits"] == 0
            and type(payload["updates"]) is int and payload["updates"] == 0, "C0-only zero-write scope")
    require(payload["sources"] == source_snapshot(), "loaded source/scope pins differ")
    plan = manifest["plan"]
    require(build_tasks(plan["roots"]) == plan, "task/control/seed/continuation drift")
    require(_construct(plan["roots"]) == manifest["construct"], "construct certificate drift")
    require(manifest["panels"] == {"delayed": {key: list(value) for key, value in runtime.DELAYED.items()},
                                    "reachout": {key: list(value) for key, value in runtime.REACHOUT.items()}}, "threshold drift")
    for key in ("wall_seconds", "device_seconds"):
        require(runtime.finite(manifest[key]) and 0 < manifest[key] <= 36000, "finite scoped budget required")
    actor = manifest["actor"]
    native.NativeActor(actor)
    require(actor["max_calls"] == 1952 and actor["max_output_tokens"] == 2048, "complete conditional call budget")
    require(actor["device_seconds_cap"] == manifest["device_seconds"], "actor/driver cap drift")
    require(all(actor["source_files"].get(path) == expected for path, expected in manifest["sources"].items()), "native actor must verify all diagnostic source pins")
    out = Path(manifest["output_dir"])
    require(out.is_absolute() and Path(actor["output_dir"]) == out / "actor", "fresh actor output must be inside diagnostic output")
    require(out != Path(actor["model_path"]) and out not in Path(actor["model_path"]).parents
            and Path(actor["model_path"]) not in out.parents, "model/output overlap")
    measured = manifest["measurements"]
    _check_measurements(measured)
    require(measured["plan_sha256"] == plan["sha256"] and measured["binding"] == tokenizer_binding(actor), "tokenizer/plan binding drift")
    require(measured["kind"] == ("SYNTHETIC" if manifest["test_only"] else "ACTUAL_OFFLINE"), "synthetic measurements cannot release native calls")
    first = [entry for entry in measured["measurements"] if entry["id"].startswith("initial/")]
    require({entry["id"] for entry in first} == {"initial/" + task["id"] for task in plan["tasks"]}, "all 800 initial requests need measurements")
    require(all(len(entry["token_ids"]) <= actor["max_input_tokens"] and
                len(entry["token_ids"]) + 2048 <= actor["engine"]["max_model_len"] for entry in first), "initial context/output cap")
    if tokenizer is not None:
        replay = measure_tokenizer(plan, tokenizer, tokenizer_binding(actor), synthetic=manifest["test_only"])
        require(replay == measured, "actual tokenizer transcript differs")
    return {"zero_fit_manifest_valid": True, "full_v22_release": False,
            "native_tokenizer_replayed": tokenizer is not None and not manifest["test_only"],
            "native_start_checks_pending": True, "tasks": 800, "max_actor_calls": 1952, "fits": 0}


def _panels(results):
    panels = {}
    for panel, registry, denominator in (("delayed", runtime.DELAYED, 64), ("reachout", runtime.REACHOUT, 32)):
        for projection, (minimum, maximum) in registry.items():
            rows = [row for row in results if row["panel"] == panel and row["projection"] == projection]
            require(len(rows) == denominator, "fixed denominator changed")
            count = sum(row["success"] for row in rows)
            missing = sum(row["execution"] != "SCORED" for row in rows)
            false_rows = sum(row["usable_false_row"] for row in rows)
            panels[f"{panel}/{projection}"] = {"correct": count, "denominator": denominator,
                                                "minimum": minimum, "maximum": maximum, "missing": missing,
                                                "usable_false_rows": false_rows,
                                                "passed": missing == 0 and minimum <= count <= maximum and false_rows == 0}
    return panels


class Diagnostic(runtime.Runtime):
    """Reuse only frozen _task/scoring; no original full-assay release bypass."""

    def __init__(self, manifest, tokenizer, *, backend_factory=None, clock=time.monotonic):
        self.started = clock()
        self.manifest = copy.deepcopy(manifest)
        self.clock = clock
        self.validation = validate_manifest(self.manifest, tokenizer)
        require((backend_factory is not None) == manifest["test_only"], "test mode requires injected backend; native mode forbids injection")
        self.tokenizer = tokenizer
        self.factory = native.NativeActor if backend_factory is None else backend_factory
        self.plan = self.manifest["plan"]
        self.deadline = min(self.manifest["actor"]["deadline"], self.started + self.manifest["wall_seconds"],
                            self.started + self.manifest["device_seconds"])
        require(self.clock() < self.deadline, "deadline expired before claim/start")
        self.consumed = False
        self.call_log, self.results = [], []
        self.actor = None
        self.backend = SimpleNamespace(count_tokens=self._count_returned)
        self.first = {entry["id"]: entry for entry in self.manifest["measurements"]["measurements"]}
        self.slots = {(entry["task"], entry["turn"]): entry for entry in self.plan["call_slots"]}
        self.task_hashes = {task["id"]: digest(task) for task in self.plan["tasks"]}

    def _write(self, name, value):
        with (self.out / name).open("xb") as stream:
            stream.write(canonical(value) + b"\n")

    def _check(self):
        require(self.clock() < self.deadline, "diagnostic wall/device envelope exhausted")

    def _task(self, task):
        require(digest(task) == self.task_hashes[task["id"]], "task bytes changed")
        result = super()._task(task)
        require(digest(task) == self.task_hashes[task["id"]], "task bytes changed during execution")
        return result

    def _count_returned(self, text):
        self._check()
        observed = self.actor.count_tokens(text)
        expected = len(native.token_ids(self.tokenizer.encode(text, add_special_tokens=False)))
        require(type(observed) is int and observed == expected, "native service token count drift")
        return observed

    def _generate(self, task, messages, turn, actor_tokens, returned_tokens):
        self._check()
        require(digest(task) == self.task_hashes[task["id"]], "task bytes changed")
        slot = self.slots[(task["id"], turn)]
        request = {"id": slot["id"], "messages": copy.deepcopy(messages), "seed": slot["seed"], "mount": "C0"}
        text, ids = _render(self.tokenizer, messages)
        if turn == 0:
            require(ids == self.first["initial/" + task["id"]]["token_ids"] and
                    core.byte_hash(text) == self.first["initial/" + task["id"]]["text_sha256"], "first request drift")
        limits = {"input_tokens": len(ids), "output_tokens": 2048 - actor_tokens,
                  "returned_tokens": 4096 - returned_tokens, "remaining_reads": 12 - turn,
                  "deadline": self.deadline, "device_seconds": self.deadline - self.clock()}
        require(limits["output_tokens"] > 0 and len(ids) <= self.manifest["actor"]["max_input_tokens"]
                and len(ids) + limits["output_tokens"] <= native.ENGINE["max_model_len"], "actual continuation input/output envelope")
        call = {"request": request, "request_sha256": digest(request), "render_sha256": core.byte_hash(text),
                "input_token_ids": ids, "limits": limits, "response": None}
        self.call_log.append(call)
        index = len(self.call_log) - 1
        self._write(f"call_{index:04}_request.json", call)
        try:
            response = self.actor.generate(copy.deepcopy(request), copy.deepcopy(limits))
            call["response"] = copy.deepcopy(response)
            self._write(f"call_{index:04}_response.json", response)
            _record(response, ("request_sha256", "text", "prompt_tokens", "output_tokens", "device_seconds"))
            require(response["request_sha256"] == digest(request) and type(response["text"]) is str, "native response/request mismatch")
            require(type(response["prompt_tokens"]) is int and response["prompt_tokens"] == len(ids), "native prompt token count mismatch")
            require(type(response["output_tokens"]) is int and 0 <= response["output_tokens"] <= limits["output_tokens"]
                    and (response["output_tokens"] > 0 or not response["text"]), "actor output token cap")
            require(runtime.finite(response["device_seconds"]) and response["device_seconds"] <= limits["device_seconds"], "call time budget")
            self._check()
            return response
        except Exception as error:
            call["error"] = str(error)
            raise

    def run(self):
        require(not self.consumed, "one attempt only; no rerun")
        self.consumed = True
        self.out = Path(self.manifest["output_dir"])
        require(self.out.parent.is_dir() and self.out.parent.resolve() == self.out.parent, "fresh output parent must exist without aliases")
        self.out.mkdir(parents=False, exist_ok=False)
        error, release = None, None
        try:
            _unseal(self.manifest)
            self._write("manifest.json", self.manifest)
            self._check()
            self.actor = self.factory(copy.deepcopy(self.manifest["actor"]))
            require(not self.manifest["test_only"] or getattr(self.actor, "scripted", False) is True,
                    "test manifest cannot start a native actor")
            self.actor.start()
            self._check()
            for task in self.plan["tasks"]:
                item = {**self._task(task), "execution": "SCORED"}
                self.results.append(item)
                self._write(f"task_{len(self.results) - 1:03}.json", item)
        except Exception as failure:
            error = {"type": type(failure).__name__, "message": str(failure)}
        finally:
            if self.actor is not None:
                try:
                    release = self.actor.close()
                except Exception as failure:
                    error = {"type": type(failure).__name__, "message": "close: " + str(failure), "prior": error}
        elapsed = self.clock() - self.started
        try:
            _unseal(self.manifest)
        except ValueError as failure:
            error = {"type": "MANIFEST_DRIFT", "message": str(failure), "prior": error}
        if elapsed > min(self.manifest["wall_seconds"], self.manifest["device_seconds"]) or self.clock() > self.deadline:
            error = {"type": "BUDGET_EXCEEDED", "message": "cold-load-through-close envelope exceeded", "prior": error}
        if (type(release) is not dict or release.get("error_type") is not None or release.get("budget_exceeded") is True or release.get("failed") is True
                or release.get("calls_consumed") != len(self.call_log)
                or release.get("kind") != ("SYNTHETIC" if self.manifest["test_only"] else "NATIVE")):
            error = {"type": "SHUTDOWN_UNVERIFIED", "message": "backend shutdown missing/failed", "prior": error}
        complete = len(self.results) == 800 and error is None
        for task in self.plan["tasks"][len(self.results):]:
            self.results.append({"id": task["id"], "root": task["cell"]["root"]["label"],
                                 "panel": task["panel"], "projection": task["projection"], "success": False,
                                 "usable_false_row": False, "execution": "NOT_SCORED"})
        panels = _panels(self.results)
        report = _seal({"schema": SCHEMA + "/report", "manifest_sha256": self.manifest["sha256"],
                        "actor_config_sha256": digest(self.manifest["actor"]),
                        "source_files_sha256": digest(self.manifest["sources"]),
                        "tokenizer_measurements_sha256": self.manifest["measurements"]["sha256"],
                        "test_only": self.manifest["test_only"], "status": "COMPLETE_AWAITING_OUTER_RELEASE" if complete else "FAILED",
                        "diagnostic_usable": False, "full_v22_release": False, "fits": 0, "updates": 0,
                        "tasks": 800, "scored_tasks": sum(row["execution"] == "SCORED" for row in self.results),
                        "actor_attempts": len(self.call_log), "actor_responses": sum(call["response"] is not None for call in self.call_log),
                        "results": self.results, "panels": panels, "thresholds_passed": all(panel["passed"] for panel in panels.values()),
                        "error": error, "backend_close": release, "wall_seconds_through_close": elapsed,
                        "time_basis": "single-device reserved elapsed wall including validation/cold load/close, not active GPU time",
                        "started_monotonic": self.started, "gpu_uuid": self.manifest["actor"]["gpu_uuid"],
                        "wall_cap": self.manifest["wall_seconds"], "device_cap": self.manifest["device_seconds"],
                        "scope": "excluded-root interface ceilings/failures only; no memory/parenting/H1/H2/G3/full-construct claim"})
        self._write("report.json", report)
        return report


def finalize_release(report, receipt):
    """Attach Main's outer release attestation; never perform GPU/process queries."""
    _unseal(report)
    require(report["schema"] == SCHEMA + "/report" and report["tasks"] == 800
            and report["fits"] == 0 and report["updates"] == 0 and report["full_v22_release"] is False,
            "release report scope differs")
    _record(receipt, ("report_sha256", "gpu_uuid", "owned_group_released", "gpu_vacant",
                      "elapsed_seconds_from_start", "evidence_path", "evidence_sha256"))
    require(receipt["report_sha256"] == report["sha256"] and receipt["gpu_uuid"] == report["gpu_uuid"], "outer release binding")
    require(receipt["owned_group_released"] is True and receipt["gpu_vacant"] is True, "outer release not verified")
    require(runtime.finite(receipt["elapsed_seconds_from_start"]) and report["wall_seconds_through_close"] <=
            receipt["elapsed_seconds_from_start"] <= min(report["wall_cap"], report["device_cap"]), "release-inclusive budget")
    require(Path(receipt["evidence_path"]).is_absolute(), "absolute release evidence path required")
    require(_file_hash(receipt["evidence_path"]) == receipt["evidence_sha256"], "outer release evidence hash")
    attestation = {key: value for key, value in receipt.items() if key not in ("evidence_path", "evidence_sha256")}
    require(canonical(json.loads(Path(receipt["evidence_path"]).read_bytes())) == canonical(attestation), "outer release attestation fields differ")
    return _seal({"schema": SCHEMA + "/final", "report": report, "outer_release": receipt,
                  "diagnostic_usable": report["status"] == "COMPLETE_AWAITING_OUTER_RELEASE" and not report["test_only"],
                  "cpu_test_complete": report["status"] == "COMPLETE_AWAITING_OUTER_RELEASE" and report["test_only"],
                  "full_v22_release": False})
