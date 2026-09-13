"""Thin PCFL v2.2 scripted runtime; native execution is deliberately unavailable.

Loaded APIs are separate from detached scientific data. No subprocess, model,
tokenizer, filesystem write, fit, or collector is hidden in this module.
"""

import copy
import math
import time
from collections import Counter

from organism_v6 import pcfl_vertical_dev as core_api
from organism_v6 import pcfl_vertical_prepare as prepare_api


DELAYED = {
    "EXACT_WITNESSED_GRAPH": (60, 64), "FULL_CHILD_TEXT": (60, 64),
    "EVENT_ATOMS_TEXT": (60, 64), "ACTIVE_LINKED_TEXT": (60, 64),
    "NATIVE_CONTEXT": (60, 64), "RAW_EPISODIC": (0, 64),
    "OLD_ONLY_TEXT": (0, 36), "NEW_ONLY_TEXT": (0, 36),
    "NONE_OFF": (0, 20), "WRONG_ROOT": (0, 20),
}
REACHOUT = {
    "EXACT_WITNESSED_GRAPH": (30, 32), "FULL_CHILD_TEXT": (30, 32),
    "ACTIVE_LINKED_TEXT": (30, 32), "NONE_OFF": (0, 18), "WRONG_ROOT": (0, 18),
}
BUDGETS = {"dev_inference": 36000, "training": 28800,
           "cal_low_readout": 3600, "cal_high_readout": 3600}
STAGE_DAG = (
    ("CONSTRUCT", ()), ("ZERO_FIT", ("CONSTRUCT",)),
    ("DISPOSABLE_FORMATION", ("ZERO_FIT",)),
    ("CAL_LOW", ("DISPOSABLE_FORMATION",)),
    ("CAL_HIGH", ("CAL_LOW_VALID_SAFE_ACQUISITION_MISS",)),
    ("DEV_OLD", ("SELECT_LOW_OR_HIGH",)),
    ("S1_FOUR_FITS_PER_ROOT", ("DEV_OLD",)),
    ("S1_READOUT", ("S1_FOUR_FITS_PER_ROOT",)),
    ("REACHOUT", ("S1_AUTH_ALL_GATES",)),
    ("NEW_R0_R1", ("REACHOUT",)),
    ("S2_THREE_FITS_PER_ROOT", ("NEW_R0_R1",)),
    ("S2_READOUT", ("S2_THREE_FITS_PER_ROOT",)),
    ("SEAL_REDUCE_ONCE", ("BOTH_ROOTS_AND_REGISTERED_CONTROLS",)),
)


class RuntimeStop(ValueError):
    def __init__(self, label, detail):
        super().__init__(f"{label}: {detail}")
        self.label = label


def require(condition, label, detail):
    if not condition:
        raise RuntimeStop(label, detail)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def prepare_scripted_plan(contract):
    """Expand fixed CPU-test slots before outputs; NOT a native work manifest.

    Native prompts/token caps/load/continuation rows must instead be expanded
    and bound by Main's completed execution contract. This plan never waives it.
    """
    roots = [core_api.from_data(entry["wire"]) for entry in contract["bindings"]["root_registry"]
             if entry["role"] == "excluded"]
    roots.sort(key=lambda root: root.label)
    require([root.label for root in roots] == [f"excluded/{index}" for index in range(4)],
            "VS_ASSAY_INVALID", "four excluded roots required")
    tasks = []
    for root_index, root in enumerate(roots):
        donor = roots[(root_index + 1) % 4]
        for cell in core_api.expand_cube(root):
            rows = core_api.ideal_rows(cell)
            wrong = core_api.ideal_rows(core_api.WorldCell(donor, cell.old, cell.relevant, cell.distractor))
            for goal in (0, 1):
                block = f"{root.label}/{cell.old}/{cell.relevant}/{cell.distractor}/{goal}"
                for projection in DELAYED:
                    tasks.append({"id": f"delayed/{block}/{projection}", "panel": "delayed",
                                  "cell": core_api.to_data(cell), "goal": goal, "projection": projection,
                                  "seed": core_api.seed("runtime-test/" + block),
                                  "public": core_api.render_task(cell, goal, projection, rows=rows, wrong_rows=wrong, fixture_only=True),
                                  "queries": core_api.materialize_queries(rows) if projection == "ACTIVE_LINKED_TEXT" else {}})
        for old in (0, 1):
            cell = core_api.WorldCell(root, old, 0, 0)
            rows = core_api.ideal_rows(cell)
            wrong = core_api.ideal_rows(core_api.WorldCell(donor, old, 0, 0))
            for goal in (0, 1):
                for view in ("RA", "RB"):
                    block = f"{root.label}/{old}/{goal}/{view}"
                    for projection in REACHOUT:
                        memory = ""
                        if projection == "EXACT_WITNESSED_GRAPH":
                            memory = "".join("EDGE " + edge.source + " " + edge.port + " " + edge.destination + "\n" for edge in cell.edges[:8])
                        elif projection in ("FULL_CHILD_TEXT", "WRONG_ROOT"):
                            memory = "".join(row["raw"] for row in (wrong if projection == "WRONG_ROOT" else rows)[:12])
                        public = {"system": core_api.REACHOUT_SYSTEM,
                                  "user": ("MEMORY\n" + memory + "\n" if memory else "") + core_api.render_reachout(cell, goal, view, fixture_only=True),
                                  "service_enabled": projection == "ACTIVE_LINKED_TEXT"}
                        if projection == "ACTIVE_LINKED_TEXT":
                            public["system"] += " On earlier turns you may issue one exact READ request; at most 12 READs."
                        tasks.append({"id": f"reachout/{block}/{projection}", "panel": "reachout",
                                      "cell": core_api.to_data(cell), "goal": goal, "projection": projection,
                                      "seed": core_api.seed("runtime-test/" + block), "public": public,
                                      "queries": core_api.materialize_queries(rows[:12]) if projection == "ACTIVE_LINKED_TEXT" else {}})
        plan = {"kind": "SCRIPTED_TEST_ONLY", "contract_sha256": prepare_api.digest(contract),
            "tasks": tasks, "task_actor_cap": 2048, "task_returned_cap": 4096,
            "task_read_cap": 12, "roots": [core_api.to_data(root) for root in roots]}
    require(len(tasks) == 800 and len({task["id"] for task in tasks}) == 800,
            "VS_ASSAY_INVALID", "zero-fit denominator differs")
    return plan


def audit_formation(contract, bundle):
    """Replay exact subsequent child spans against the real CPU world/admitter.

    This proves byte/support chronology only. It cannot authenticate a remote
    generation. Native custody is not inferred from an accepted core row.
    """
    require(set(bundle) == {"contract_sha256", "root", "corpus", "generations"},
            "VS_ASSAY_INVALID", "formation bundle schema")
    require(bundle["contract_sha256"] == prepare_api.digest(contract) and bundle["root"] == "disposable/0",
            "VS_ASSAY_INVALID", "formation contract/root differs")
    entries = [entry for entry in contract["bindings"]["root_registry"] if entry["id"] == bundle["root"]]
    require(len(entries) == 1, "VS_ASSAY_INVALID", "disposable root absent")
    entry = entries[0]
    root = core_api.from_data(entry["wire"])
    cell = core_api.WorldCell(root, entry["old_bit"], entry["canonical_r"], 0)
    session = core_api.WorldSession(cell, "OLD")
    generations = bundle["generations"]
    require(len(generations) == 20, "VS_CHILD_OLD_FORMATION_FAIL", "fixed 8 actions + 8 EVENT + 4 LINK opportunities")
    expected_kinds = [kind for _ in range(8) for kind in ("EXPLORE", "EVENT")] + ["LINK"] * 4
    admissions, events, seen, span_bindings = [], {}, set(), []
    latest = None
    last_ended = 0
    for index, (generation, expected) in enumerate(zip(generations, expected_kinds)):
        require(set(generation) == {"id", "kind", "raw", "sha256", "span", "started", "ended", "prompt_sha256"},
                "VS_ASSAY_INVALID", "child generation schema")
        raw = generation["raw"]
        require(type(raw) is str and generation["kind"] == expected and generation["id"] not in seen,
                "VS_ASSAY_INVALID", "duplicate/reordered generation")
        seen.add(generation["id"])
        require(core_api.byte_hash(raw) == generation["sha256"], "VS_ASSAY_INVALID", "generation hash differs")
        require(finite(generation["started"]) and finite(generation["ended"])
                and generation["started"] >= last_ended and generation["ended"] >= generation["started"],
                "VS_ASSAY_INVALID", "source chronology differs")
        last_ended = generation["ended"]
        span = generation["span"]
        require(type(span) is list and len(span) == 2 and all(type(value) is int for value in span)
                and 0 <= span[0] < span[1] <= len(raw.encode("utf-8")), "VS_ASSAY_INVALID", "child span bounds")
        try:
            text = raw.encode("utf-8")[span[0]:span[1]].decode("utf-8")
        except UnicodeError as error:
            raise RuntimeStop("VS_ASSAY_INVALID", "split UTF-8 source span") from error
        if expected == "EXPLORE":
            prompt = session.explore_prompt()
        elif expected == "EVENT":
            require(latest is not None and latest["ok"], "VS_CHILD_OLD_FORMATION_FAIL", "failed own action")
            prompt = session.event_prompt(latest["receipt"])
        else:
            prompt = session.link_prompt()
        require(generation["prompt_sha256"] == core_api.byte_hash(prompt), "VS_ASSAY_INVALID", "public prompt receipt mismatch")
        if expected == "EXPLORE":
            require(text == raw, "VS_ASSAY_INVALID", "action cannot be extracted/repaired")
            latest = session.explore(raw)
            require(latest["ok"], "VS_CHILD_OLD_FORMATION_FAIL", "invalid child action; no replacement")
        elif expected == "EVENT":
            admission = core_api.admit_event(text, latest["receipt"], session, root.lookup("event", f"e{index // 2}"))
            admissions.append(admission)
            if admission["accepted"]:
                events[admission["row"]["fields"]["event"]] = admission["row"]
        else:
            try:
                fields = core_api.parse_link_line(text)
                members = [events[fields[key]] for key in ("first", "second")]
                receipts = [next(receipt for receipt in session.receipts if receipt["receipt"] == member["fields"]["receipt"]) for member in members]
            except (ValueError, KeyError, StopIteration):
                members, receipts = [], []
            admissions.append(core_api.admit_link(text, receipts, session, root.lookup("link", f"l{index - 16}"), members))
        if expected != "EXPLORE":
            span_bindings.append({"generation_id": generation["id"], "generation_sha256": generation["sha256"],
                                  "byte_start": span[0], "byte_end": span[1], "span_sha256": core_api.byte_hash(text),
                                  "accepted": admissions[-1]["accepted"]})
    corpora = [corpus for corpus in contract["bindings"]["slot_registry"] if corpus["id"] == bundle["corpus"]]
    require(len(corpora) == 1 and corpora[0]["root"] == "disposable/0", "VS_ASSAY_INVALID", "CAL corpus/root mismatch")
    required_bank = {}
    for slot in corpora[0]["slots"]:
        require(slot["taint"] == "AUTHENTIC", "VS_ASSAY_INVALID", "CAL must use authentic child bank")
        for identity, fields in slot["bank"].items():
            require(identity not in required_bank or required_bank[identity] == fields,
                    "VS_ASSAY_INVALID", "conflicting frozen bank")
            required_bank[identity] = fields
    report = core_api.formation_report(admissions, required_bank=required_bank)
    require(report["formation_complete"], "VS_CHILD_OLD_FORMATION_FAIL", str(report))
    rows = [admission["row"] for admission in admissions]
    queries = core_api.materialize_queries(rows)
    bank = prepare_api.validate_formation_binding(contract, bundle["corpus"], queries, rows)
    require(bank["formation_binding_valid"] is True, "VS_ASSAY_INVALID", "formation bank not validated")
    return {"report": report, "rows": rows, "queries": queries, "bank": bank,
            "generations": copy.deepcopy(generations), "native_custody_verified": False,
            "span_bindings": span_bindings, "generation_receipts_replayed": 20,
            "writer_native_capture_payloads_supplied": False,
            "source_bundle_sha256": prepare_api.digest(bundle)}


class Runtime:
    """One-shot CPU/scripted initial path with a fail-closed native entry.

    Backend: scripted=True; generate(public_request, limits), count_tokens(text),
    close(). close returns owned_group_released and gpu_vacant Boolean fields.
    No private task/scoring data is passed to the backend. Its token/device
    receipts are synthetic in this mode, never actual measurement evidence.
    """

    def __init__(self, contract, backend, *, scripted=False, clock=time.monotonic,
                 deadline=None, profile_receipts=None):
        self.contract_data = copy.deepcopy(contract)
        self.contract_hash = prepare_api.digest(self.contract_data)
        self.validation = prepare_api.validate_execution_contract(self.contract_data, profile_receipts)
        require(scripted is True and getattr(backend, "scripted", False) is True,
                "NATIVE_BINDING_UNIMPLEMENTED", "production D, full prepare/native/profile/owned-process release remain unresolved")
        require(self.validation["bridge_invariants_valid"] is True, "VS_ASSAY_INVALID", "invalid preparation bridge")
        require(self.contract_data["bindings"]["core_registry"] == core_api.registries(),
                "VS_ASSAY_INVALID", "loaded core differs from sealed registry")
        self.backend = backend
        self.clock = clock
        self.started = clock()
        self.deadline = self.started + 36000 if deadline is None else deadline
        require(finite(self.started) and finite(self.deadline) and self.deadline > self.started,
                "VS_RESOURCE_CAP", "invalid deadline")
        self.plan = prepare_scripted_plan(self.contract_data)
        self.plan_hash = prepare_api.digest(self.plan)
        self.consumed = False
        self.seconds = Counter()
        self.call_log = []
        self.results = []
        self.release = None

    def _unchanged(self):
        require(prepare_api.digest(self.contract_data) == self.contract_hash
                and prepare_api.digest(self.plan) == self.plan_hash,
                "VS_ASSAY_INVALID", "sealed input drift")

    def _generate(self, task, messages, turn, actor_tokens, returned_tokens):
        now = self.clock()
        require(now < self.deadline and self.seconds["dev_inference"] < 36000,
                "VS_RESOURCE_CAP", "inference clock exhausted")
        request = {"id": f"{core_api.byte_hash(task['id'])}/actor/{turn}", "messages": copy.deepcopy(messages),
                   "seed": task["seed"], "mount": "C0"}
        request_hash = prepare_api.digest(request)
        limits = {"output_tokens": 2048 - actor_tokens, "returned_tokens": 4096 - returned_tokens,
                  "remaining_reads": 12 - turn, "deadline": self.deadline,
                  "device_seconds": min(36000 - self.seconds["dev_inference"], self.deadline - now)}
        require(limits["output_tokens"] > 0, "VS_RESOURCE_CAP", "task actor tokens exhausted")
        call = {"request": request, "request_sha256": request_hash, "response": None}
        self.call_log.append(call)
        try:
            response = self.backend.generate(copy.deepcopy(request), copy.deepcopy(limits))
        except Exception as error:
            call["error"] = str(error)
            raise RuntimeStop("GENERATION_FAILED", "no retry; failed-call device cost unknown") from error
        call["response"] = copy.deepcopy(response)
        require(type(response) is dict and set(response) == {"request_sha256", "text", "prompt_tokens", "output_tokens", "device_seconds"},
                "VS_ASSAY_INVALID", "generation receipt schema")
        require(response["request_sha256"] == request_hash and type(response["text"]) is str,
                "VS_ASSAY_INVALID", "raw generation/request binding")
        for key in ("prompt_tokens", "output_tokens"):
            require(type(response[key]) is int and response[key] >= 0, "VS_ASSAY_INVALID", "invalid token receipt")
        require(finite(response["device_seconds"]), "VS_ASSAY_INVALID", "invalid device time")
        self.seconds["dev_inference"] += response["device_seconds"]
        require(response["output_tokens"] <= limits["output_tokens"]
                and (response["output_tokens"] > 0 or not response["text"]), "VS_RESOURCE_CAP", "output token cap/receipt")
        require(response["device_seconds"] <= limits["device_seconds"] and self.clock() <= self.deadline,
                "VS_RESOURCE_CAP", "device/wall deadline exceeded")
        return response

    def _task(self, task):
        messages = [{"role": "system", "content": task["public"]["system"]},
                    {"role": "user", "content": task["public"]["user"]}]
        actor_tokens = returned_tokens = 0
        reads = []
        raw = ""
        invalid_read = False
        for turn in range(13):
            response = self._generate(task, messages, turn, actor_tokens, returned_tokens)
            raw = response["text"]
            actor_tokens += response["output_tokens"]
            if not raw.startswith("READ "):
                break
            if task["projection"] != "ACTIVE_LINKED_TEXT" or turn == 12:
                invalid_read = True
                break
            try:
                lookup = core_api.read_query(task["queries"], raw)
            except ValueError:
                invalid_read = True
                break
            count = self.backend.count_tokens(lookup["raw"])
            require(type(count) is int and count >= 0, "VS_ASSAY_INVALID", "returned token count")
            if returned_tokens + count > 4096:
                invalid_read = True
                break
            returned_tokens += count
            reads.append(lookup)
            messages.extend(({"role": "assistant", "content": raw}, {"role": "user", "content": lookup["raw"]}))
        cell = core_api.from_data(task["cell"])
        false_row = task["projection"] == "WRONG_ROOT" and core_api.score_memory_response(raw, None)["usable_false_row"]
        if task["panel"] == "delayed":
            score = core_api.score_route(cell, task["goal"], raw)
            success = score["graph_success"] and not invalid_read
        else:
            try:
                success = core_api.parse_probe(raw) == cell.root.lookup("probe", "relevant") and not invalid_read
            except ValueError:
                success = False
            score = {"relevant_probe": success}
        return {"id": task["id"], "root": cell.root.label, "panel": task["panel"],
                "projection": task["projection"], "raw": raw, "raw_sha256": core_api.byte_hash(raw),
                "success": success, "score": score, "reads": reads, "invalid_read": invalid_read,
                "usable_false_row": false_row,
                "actor_tokens": actor_tokens, "returned_tokens": returned_tokens}

    def run_initial(self, formation=None):
        require(not self.consumed, "ALREADY_CONSUMED", "no recollection or retry")
        self.consumed = True
        stages = {name: "NOT_IMPLEMENTED" for name, _ in STAGE_DAG}
        stages.update(CONSTRUCT="PENDING", ZERO_FIT="PENDING", DISPOSABLE_FORMATION="PENDING")
        report = {"kind": "SCRIPTED_TEST_ONLY", "contract_sha256": self.contract_hash,
                  "plan_sha256": self.plan_hash, "scientific_pass": False, "native_ready": False,
                  "fits_executed": 0, "updates_executed": 0, "stages": stages,
                  "dag": STAGE_DAG, "budget_caps": BUDGETS.copy(),
                  "branch_caps": {"LOW_ONLY": {"fits": 15, "updates": 3000, "seconds": 68400},
                                  "HIGH_USED": {"fits": 16, "updates": 3200, "seconds": 72000}},
                  "cuts": copy.deepcopy(self.contract_data["bindings"]["intervention_registry"]),
                  "work_registry_sha256": prepare_api.digest(self.contract_data["bindings"].get("work_registry", [])),
                  "frozen_work_rows": len(self.contract_data["bindings"].get("work_registry", [])),
                  "work_expansion_bound": False,
                  "remaining": ["production D endpoints/outcomes/transition binding; current core is not production authority",
                                "complete construct/shortcut certificate", "native sealed request/load/continuation expansion",
                                "actual profile/tokenizer/process identity and lease enforcement",
                                "disposable generation dispatch and native capture authentication",
                                "CAL fit/readout dispatch", "all subsequent DEV stages"],
                  "preparation": self.validation, "denominators": {"delayed": 640, "reachout": 160}}
        try:
            self._unchanged()
            audit = core_api.audit_construct([core_api.from_data(root) for root in self.plan["roots"]])
            report["construct"] = audit
            require(audit["route_construct_passed"] and audit["worlds"] == 32 and audit["delayed_tasks"] == 64
                    and len(audit["route_cut_decisions"]) == 192 and len(audit["atoms_link_decisions"]) == 48,
                    "VS_ASSAY_INVALID", "CPU construct counts/oracles")
            stages["CONSTRUCT"] = "SCRIPTED_ROUTE_AUDIT_ONLY"
            for task in self.plan["tasks"]:
                self.results.append(self._task(task))
            self._unchanged()
            panels = {}
            for panel, registry, denominator in (("delayed", DELAYED, 64), ("reachout", REACHOUT, 32)):
                for projection, (minimum, maximum) in registry.items():
                    items = [item for item in self.results if item["panel"] == panel and item["projection"] == projection]
                    count = sum(item["success"] for item in items)
                    false_rows = sum(item["usable_false_row"] for item in items)
                    require(len(items) == denominator and len({item["root"] for item in items}) == 4,
                            "VS_ASSAY_INVALID", "panel denominator/root coverage")
                    panels[f"{panel}/{projection}"] = {"correct": count, "denominator": denominator,
                                                       "minimum": minimum, "maximum": maximum,
                                                       "usable_false_rows": false_rows,
                                                       "passed": minimum <= count <= maximum and false_rows == 0}
            report["panels"] = panels
            require(all(panel["passed"] for panel in panels.values()), "VS_ASSAY_INVALID_MODEL_CEILING", "mandatory ceiling/control failed")
            stages["ZERO_FIT"] = "SCRIPTED_THRESHOLDS_PASSED_NOT_NATIVE_CERTIFICATE"
            if formation is None:
                report["status"] = "AWAITING_DISPOSABLE_EXACT_CHILD_SPANS"
            else:
                report["formation"] = audit_formation(self.contract_data, copy.deepcopy(formation))
                stages["DISPOSABLE_FORMATION"] = "CPU_BYTE_AND_BANK_REPLAY_ONLY"
                report["status"] = "CAL_LOW_BINDING_REQUIRED"
                report["cal_low_handoff"] = {"corpus": formation["corpus"], "learning_rate": 3e-5,
                                              "initialization": "clean_C0", "updates": 200,
                                              "fit_seconds_cap": 1800, "readout_seconds_cap": 3600,
                                              "source_bundle_sha256": prepare_api.digest(formation),
                                              "writer_api": "organism_v6.pcfl_vertical_train.build_fit",
                                              "gaps": ["native generation custody", "writer binding and encoded masks",
                                                       "CAL readout full work expansion and dispatch"]}
        except (RuntimeStop, ValueError, KeyError, TypeError) as error:
            report["status"] = error.label if isinstance(error, RuntimeStop) else "VS_ASSAY_INVALID"
            report["error"] = str(error)
            failed = next((name for name in ("CONSTRUCT", "ZERO_FIT", "DISPOSABLE_FORMATION") if stages[name] == "PENDING"), None)
            if failed is not None:
                stages[failed] = "FAILED_OR_INCOMPLETE"
            for name in ("CONSTRUCT", "ZERO_FIT", "DISPOSABLE_FORMATION"):
                if stages[name] == "PENDING":
                    stages[name] = "BLOCKED_BY_UPSTREAM"
        finally:
            try:
                self.release = self.backend.close()
                require(type(self.release) is dict and self.release.get("owned_group_released") is True
                        and self.release.get("gpu_vacant") is True, "RELEASE_UNVERIFIED", "owned process release missing")
            except Exception as error:
                report["prior_status"] = report.get("status")
                report["status"] = "RELEASE_UNVERIFIED"
                report["release_error"] = str(error)
            report.update(results=copy.deepcopy(self.results), calls=copy.deepcopy(self.call_log),
                          generation_attempts=len(self.call_log),
                          calls_executed=sum(call["response"] is not None for call in self.call_log),
                          device_cost_incomplete=any(call["response"] is None for call in self.call_log),
                          device_seconds=dict(self.seconds),
                          release=copy.deepcopy(self.release), wall_seconds=self.clock() - self.started,
                          missing_tasks=len(self.plan["tasks"]) - len(self.results))
        return report
