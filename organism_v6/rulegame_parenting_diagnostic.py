"""Fixed 156-response RuleGame diagnostic; formation stops for Main's audit.

CPU: prepare --out ROOT --model LOCAL_MODEL --device GPU --lease-end ISO8601
Opt-in interface repair: prepare ... --protocol interaction_v2 (exploratory only).
New exploratory control/definition: prepare ... --protocol interaction_v3.
V3 formation exports through rulegame_record_material.build_record_pair only;
the legacy synthetic material/write path is not available for this protocol.
GPU opt-in: formation --root ROOT --allow-gpu
CPU: replay --root ROOT; material --root ROOT --main-audit AUDIT.json
GPU opt-in: write --root ROOT --allow-gpu; evaluate --root ROOT --allow-gpu

Edit a copy of formation/main_audit.template.json after reading the raw calls.
Main's content decision is not a lexical semantic certificate or a C11 gate.
All roots are fresh, failed stages cannot retry, and no adapter is promoted.
This tests material/write/new-rule transfer, not adult sequential adaptation/G5.
Main separately reserves/releases formation, write and evaluation phases. The
1800s aggregate counts supervised worker windows including owned cleanup, not
CPU preparation or Main's audit. Main owns the full device/queue reservation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time

from . import nursery_dialogue, run_reasoning_neutral as supervisor, train_adapter
from .batch_loop import _seed_for
from .gym_backend import Episode
from .rulegame import RuleGame


REPO = Path(__file__).resolve().parents[1]
ARMS = ("P", "A")
CELLS = ("OFF", "P_ON", "A_ON")
CLAIM_BOUNDARY = "material/write/new-rule parent-free transfer; not adult sequential adaptation or G5"
GEN_SEED = 20260912
LIMITS = {"formation": {"wake": 40, "record": 12, "parent": 4, "restate": 4},
          "evaluation": {"wake": 20, "record": 12}}
TOKENS = {"wake": 400, "record": 100, "parent": 200, "restate": 120}
TRAIN = dict(rank=8, epochs=12, lr=1e-4, seed=2, steps=12, n_texts=2)
MAX_MODEL_LEN = 16384
RESERVED_SECONDS = 1800
WORKER_SECONDS = 600
CALL_SECONDS = 120
LOAD_SECONDS = 180
CLEANUP_GRACE = 100
CLEANUP_RESERVE = 140
PROTOCOLS = ("strict_v1", "interaction_v2", "interaction_v3")
BOOT = nursery_dialogue.CHILD_BOOT + """
For this bounded task emit at most one ACT per response. You have five responses:
up to three TRY actions, one ACT: QUIZ ? reveal, and one six-label ACT: QUIZ.
Use exactly three comma-separated integers for TRY and six T/F labels for QUIZ.
An early scored quiz or DONE ends this task. No external memory is available.
"""
CONTROL = """You are an active neutral conversational parent. Acknowledge the child's
participation, then ask it to restate that acknowledgment. Do not give strategy,
hypotheses, rules, answers, action recommendations, or evaluated corrections.
Keep the acknowledgment under 120 words. Child transcript:\n---\n"""
CONTROL_V2 = """You are an active neutral conversational parent. Acknowledge only the
child's participation, then explicitly request an acknowledgement-only restatement.
Do not ask for task reflection, quizzes, what was learned, or a task summary.
Do not give strategy, hypotheses, rules, answers, action recommendations, or
evaluated corrections. Keep the acknowledgment under 120 words.
Child transcript:\n---\n"""
CONTROL_V3 = """You are an active neutral conversational parent. Acknowledge the
child's participation. You may optionally give an accurate recap of already-visible
events in the transcript. Do not give new strategy, hypotheses, recommendations,
evaluated corrections, or invented facts. Do not supply hidden rules or future
answers. Ask the child to restate your message in its own words; do not require
acknowledgment-only content or forbid the child's own reflection.
Keep the message under 120 words. Child transcript:\n---\n"""
RECORD = """Record only the TRY just executed and its returned result. Output one JSON
object with keys "try", "observed", "predicted", and "relation". "try" is the
submitted array of three integers; "observed" is the returned Boolean.
"predicted" is your explicit T/F prediction before that ACT, as a Boolean, or
null if none was made. "relation" is "matched", "mismatched", or "unavailable"
accordingly. Do not issue an action, state a hidden rule, or add other text."""
RELATION_DEFINITION = ('Explicit mapping: no prediction (null) => unavailable; prediction equal to '
                       'observation => matched; prediction different from observation => mismatched.')
SOURCE_FILES = ("rulegame_parenting_diagnostic.py", "rulegame.py", "gym_backend.py",
                "batch_loop.py", "model_backend.py", "nursery_dialogue.py",
                "parent_prompt.txt", "run_reasoning_neutral.py", "train_adapter.py")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def record_instruction(protocol="strict_v1"):
    require(protocol in PROTOCOLS, "unknown record protocol")
    return RECORD + ("\n" + RELATION_DEFINITION if protocol == "interaction_v3" else "")


def record_prompt(execution, output, protocol="strict_v1"):
    instruction = record_instruction(protocol)
    facts = {key: execution[key] for key in ("values", "observed", "predicted")}
    return (f"Task: {execution['eid']}\nExecution: {execution['eid']}#t{execution['tick']}\nActual emitted output:\n{output}"
            f"\nActual world response:\n{execution['outcome']}\nObserved fields: {json.dumps(facts)}\n{instruction}")


def main_audit_contract(protocol):
    require(protocol == "interaction_v3", "new control contract requires interaction_v3")
    return dict(protocol=protocol,
                parent_contracts=dict(P="Process guidance without hidden rules or future answers.",
                    A="Neutral participation; optional accurate already-visible recap; no new strategy, hypotheses, "
                      "recommendations, evaluated corrections, invented facts, hidden rules or future answers."),
                child_criterion="Unrestricted own-word restatement in both arms; spontaneous child reflection is not "
                                "parent leakage and is not an acknowledgment-only acceptance criterion.",
                decision_scope="Parent-supplied content; record child observations separately, not as a purity decision.",
                material_criterion="Actual records must remain faithful; no copied lesson/restatement prose in "
                                   "exported masked context or target.",
                shared_record_definition=RELATION_DEFINITION)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def decode(text):
    def reject_constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def read(path):
    return decode(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name("." + path.name + ".tmp")
    with temporary.open("xb") as target:
        target.write(encoded(value))
        target.flush()
        os.fsync(target.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def tree_hashes(root, exclude=()):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "symlink in artifact tree")
        if path.is_file() and str(path.relative_to(root)) not in exclude:
            result[str(path.relative_to(root))] = digest(path)
    return result


def model_hashes(root):
    from .reasoning_neutral_probe import file_hashes
    return file_hashes(root)


def sources():
    return {name: digest(REPO / "organism_v6" / name) for name in SOURCE_FILES}


def task_id(rule, phase):
    suffix = f"lesson{rule}/{phase}" if phase != "readout" else phase
    return f"rule{rule}/astra-minimum-20260912/{suffix}"


def schedule():
    return {"formation": [task_id(rule, phase) for rule in range(2)
                          for phase in ("pre", "apply")],
            "evaluation": [task_id(rule, "readout") for rule in range(2, 6)]}


def fresh_directory(path, model=None):
    path = Path(path).expanduser()
    require(not path.exists() and not path.is_symlink(), "output already exists")
    path = path.resolve()
    require(path != REPO and REPO not in path.parents and path not in REPO.parents,
            "output overlaps repository")
    if model is not None:
        model = Path(model).resolve()
        require(path != model and model not in path.parents and path not in model.parents,
                "output overlaps model")
    path.mkdir()
    return path


def prepare(out, model, device, lease_end, protocol="strict_v1"):
    require(protocol in PROTOCOLS, "unknown interaction protocol")
    model = Path(model).expanduser().resolve(strict=True)
    require(model.is_dir(), "local model directory required")
    require(read(model / "config.json").get("model_type") == "qwen2", "expected pinned Qwen base")
    require(re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device), "one explicit device required")
    end = datetime.fromisoformat(lease_end.replace("Z", "+00:00"))
    require(end.tzinfo is not None and end.timestamp() > time.time(), "future timezone-aware lease end required")
    game = RuleGame()
    panels = {eid: game.quiz_triples(eid) for group in schedule().values() for eid in group}
    require(all(len(panel) == 6 for panel in panels.values()), "incomplete six-item quiz")
    plan = dict(schema=1, protocol=protocol, model=str(model), model_files=model_hashes(model), device=device,
                lease_end=end.timestamp(), reserved_seconds=RESERVED_SECONDS, source_hashes=sources(),
                schedule=schedule(), panels=panels, train=TRAIN, limits=LIMITS, token_caps=TOKENS,
                gen_seed=GEN_SEED, origin="local-byte pins, not base-origin authentication",
                semantic_audit="Main must inspect generated parent/control and restatement content")
    root = fresh_directory(out, model)
    write_json(root / "plan.json", plan)
    write_json(root / "plan.sha256.json", {"sha256": digest(root / "plan.json")})
    return plan


def verify_plan(root, check_model=True):
    root = Path(root).resolve(strict=True)
    require(digest(root / "plan.json") == read(root / "plan.sha256.json")["sha256"], "plan changed")
    plan = read(root / "plan.json")
    require(plan.get("protocol", "strict_v1") in PROTOCOLS, "unknown interaction protocol")
    require(plan["source_hashes"] == sources(), "source bytes changed")
    require(plan["schedule"] == schedule() and plan["train"] == TRAIN and plan["limits"] == LIMITS
            and plan["token_caps"] == TOKENS and plan["gen_seed"] == GEN_SEED
            and plan["reserved_seconds"] == RESERVED_SECONDS, "protocol changed")
    game = RuleGame()
    require(plan["panels"] == {eid: [list(triple) for triple in game.quiz_triples(eid)]
                               for group in schedule().values() for eid in group}, "quiz manifest changed")
    if check_model:
        require(model_hashes(plan["model"]) == plan["model_files"], "local model bytes changed")
    return plan


def parse_action(text, protocol="strict_v1"):
    require(protocol in PROTOCOLS, "unknown interaction protocol")
    if protocol in ("interaction_v2", "interaction_v3"):
        require(not re.search(r"\[\s*OUTCOME\s*\]", text, re.IGNORECASE), "imagined OUTCOME in response")
        intents = list(re.finditer(r"\b(?:ACT|TRY|QUIZ)\s*:", text, re.IGNORECASE))
        if intents:
            require(len(intents) == 1, "multiple action markers")
            require(not re.search(r"^\s*DONE\b", text, re.MULTILINE | re.IGNORECASE), "action and DONE coexist")
            marker = intents[0]
            start = text.rfind("\n", 0, marker.start()) + 1
            line = text[start:].splitlines()[0]
            if not marker.group().startswith("ACT"):
                require(marker.start() == start and line.startswith(("TRY: ", "QUIZ: ")),
                        "noncanonical alias line")
                text = text[:start] + "ACT: " + line.replace(":", "", 1) + text[start + len(line):]
        require(not re.search(r"^\s*(?:TRY|QUIZ)\b", text, re.MULTILINE | re.IGNORECASE),
                "unanchored or additional action")
    markers = list(re.finditer(r"\bACT\s*:", text, re.IGNORECASE))
    if not markers:
        if re.fullmatch(r"\s*DONE\s*:?\s*", text):
            return {"kind": "done"}
        raise ValueError("missing canonical ACT")
    require(len(markers) == 1, "multiple ACT markers")
    marker = markers[0]
    start = text.rfind("\n", 0, marker.start()) + 1
    line = text[start:].splitlines()[0]
    require(line.startswith("ACT: ") and marker.start() == start, "noncanonical ACT line")
    require(not re.search(r"^\s*DONE\b", text, re.MULTILINE), "ACT and DONE coexist")
    action = line[5:].strip()
    triple = re.fullmatch(r"TRY\s+([+-]?[0-9]+)\s*,\s*([+-]?[0-9]+)\s*,\s*([+-]?[0-9]+)", action)
    prediction_lines = re.findall(r"^PREDICT:\s*([^\n]*)", text[:start], re.MULTILINE)
    ambiguous = len(prediction_lines) > 1 or any(value.strip() not in ("T", "F") for value in prediction_lines)
    predicted = prediction_lines[0].strip() == "T" if prediction_lines and not ambiguous else None
    if triple:
        return dict(kind="try", action=action, values=[int(value) for value in triple.groups()],
                    predicted=predicted, prediction_ambiguous=ambiguous)
    if action == "QUIZ ?":
        return dict(kind="reveal", action=action)
    quiz = re.fullmatch(r"QUIZ\s+([TF](?:\s*,\s*[TF]){5})", action)
    require(quiz is not None, "ACT needs exactly three integers or six literal T/F labels")
    return dict(kind="quiz", action=action)


def judge_record(text, execution):
    failures = []
    try:
        record = decode(text)
        require(isinstance(record, dict) and set(record) == {"try", "observed", "predicted", "relation"},
                "record schema")
        require(type(record["try"]) is list and len(record["try"]) == 3
                and all(type(value) is int for value in record["try"]), "record triple types")
        require(record["try"] == execution["values"], "action mismatch")
        require(type(record["observed"]) is bool and record["observed"] == execution["observed"], "outcome mismatch")
        require(not execution["prediction_ambiguous"], "ambiguous source prediction")
        require(record["predicted"] is None or type(record["predicted"]) is bool, "prediction type")
        require(record["predicted"] is execution["predicted"], "prediction mismatch")
        relation = ("unavailable" if execution["predicted"] is None else
                    "matched" if execution["predicted"] == execution["observed"] else "mismatched")
        require(record["relation"] == relation, "relation mismatch")
    except (ValueError, TypeError, KeyError) as error:
        failures.append(str(error))
    return dict(eligible=not failures, failures=failures)


def validate_response(request, response):
    require(isinstance(response, dict) and isinstance(response.get("text"), str), "missing native text")
    for field in ("prompt_token_ids", "output_token_ids"):
        require(type(response.get(field)) is list and all(type(value) is int and value >= 0
                for value in response[field]), "missing actual native token IDs")
    require(response["prompt_token_ids"] and len(response["prompt_token_ids"]) + request["max_tokens"] <= MAX_MODEL_LEN,
            "native prompt exceeds model limit")
    require(len(response["output_token_ids"]) <= request["max_tokens"], "native output exceeds cap")
    require(isinstance(response.get("rendered_prompt"), str), "missing actual rendered prompt")


class NativeBackend:
    def __init__(self, model, adapter):
        from . import model_backend
        require(Path(model_backend.MODEL).resolve() == Path(model).resolve(), "V6_MODEL differs from pin")
        self.backend = model_backend.VLLMBackend(adapter_path=adapter, max_model_len=MAX_MODEL_LEN)

    def identity(self):
        return self.backend.generation_identity()

    def generate(self, request):
        from vllm import SamplingParams
        backend = self.backend
        rendered = backend.tok.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                   tokenize=False, add_generation_prompt=True)
        require(len(backend.tok.encode(rendered)) + request["max_tokens"] <= MAX_MODEL_LEN, "prompt exceeds model limit")
        stops = {key: request[key] for key in ("stop", "include_stop_str_in_output") if key in request}
        sampling = SamplingParams(max_tokens=request["max_tokens"], temperature=request["temperature"],
                                  seed=request["seed"], **stops)
        lora = backend._LoRARequest("life", 1, backend.adapter_path) if backend.adapter_path else None
        outputs = backend.llm.generate([rendered], sampling, lora_request=lora, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, "native generation cardinality mismatch")
        result = outputs[0].outputs[0]
        return dict(text=result.text, prompt_token_ids=list(outputs[0].prompt_token_ids),
                    output_token_ids=list(result.token_ids), rendered_prompt=rendered,
                    finish_reason=result.finish_reason, stop_reason=result.stop_reason)


def interaction_settings(protocol, role):
    require(protocol in PROTOCOLS, "unknown interaction protocol")
    if protocol == "strict_v1":
        return {}
    return dict(protocol=protocol, stop=["\n[OUTCOME]"] if role == "wake" else [],
                include_stop_str_in_output=False)


class Calls:
    def __init__(self, path, backend, stage, identity, protocol="strict_v1"):
        self.path, self.backend, self.stage, self.identity = Path(path), backend, stage, identity
        require(protocol in PROTOCOLS, "unknown interaction protocol")
        self.protocol = protocol
        self.path.mkdir()
        self.counts = Counter()
        self.count = 0

    def ask(self, role, arm, eid, tick, prompt):
        require(self.counts[role] < LIMITS[self.stage].get(role, 0), "response budget exhausted")
        require(self.backend.identity() == self.identity, "backend identity changed")
        call_id = f"{self.count:04d}"
        salt = {"wake": 0, "record": 0x5A5A, "parent": 0x1010, "restate": 0x2020}[role]
        request = dict(call_id=call_id, role=role, arm=arm, eid=eid, tick=tick, prompt=prompt,
                       seed=_seed_for(eid, tick, GEN_SEED ^ salt), max_tokens=TOKENS[role],
                       temperature=.5 if role in ("parent", "restate") else .7,
                       **interaction_settings(self.protocol, role))
        self.count += 1
        self.counts[role] += 1
        write_json(self.path / f"{call_id}.request.json", dict(request=request, started=time.monotonic(),
                   prompt_sha256=value_hash(prompt), identity=self.identity))
        response = self.backend.generate(request)
        write_json(self.path / f"{call_id}.response.json", dict(response=response, ended=time.monotonic(),
                   response_sha256=value_hash(response)))
        validate_response(request, response)
        return call_id, response["text"]


class ReplayCalls:
    def __init__(self, path, identity, protocol="strict_v1"):
        self.path, self.identity = Path(path), identity
        self.protocol = protocol
        self.count = 0
        self.counts = Counter()
        self.last_ended = 0

    def ask(self, role, arm, eid, tick, prompt):
        call_id = f"{self.count:04d}"
        request_receipt = read(self.path / f"{call_id}.request.json")
        receipt = read(self.path / f"{call_id}.response.json")
        salt = {"wake": 0, "record": 0x5A5A, "parent": 0x1010, "restate": 0x2020}[role]
        expected = dict(call_id=call_id, role=role, arm=arm, eid=eid, tick=tick, prompt=prompt,
                        seed=_seed_for(eid, tick, GEN_SEED ^ salt), max_tokens=TOKENS[role],
                        temperature=.5 if role in ("parent", "restate") else .7,
                        **interaction_settings(self.protocol, role))
        require(request_receipt["request"] == expected, "source request/seed/context mismatch: " + call_id)
        require(request_receipt["identity"] == self.identity, "source identity mismatch")
        require(request_receipt["prompt_sha256"] == value_hash(prompt), "prompt hash mismatch")
        require(receipt["response_sha256"] == value_hash(receipt["response"]), "raw response hash mismatch")
        require(receipt["ended"] >= request_receipt["started"] >= self.last_ended, "call ordering invalid")
        self.last_ended = receipt["ended"]
        validate_response(expected, receipt["response"])
        self.count += 1
        self.counts[role] += 1
        return call_id, receipt["response"]["text"]


class Events:
    def __init__(self, path=None):
        self.path, self.rows = path, []

    def append(self, row):
        self.rows.append(row)
        if self.path:
            with Path(self.path).open("ab") as target:
                target.write(encoded(row))
                target.flush()
                os.fsync(target.fileno())


def play_task(calls, events, arm, eid, notes=False, prefix=""):
    protocol = getattr(calls, "protocol", "strict_v1")
    episode = Episode(eid=eid, goal="Induce the hidden rule and answer the quiz.",
                      metric="first quiz accuracy (0..1)", intro="A fresh mystery box.")
    game = RuleGame()
    tail = [episode.intro + ("\nTemporary parent restatement:\n" + prefix if prefix else "")]
    tries, revealed, score, valid_quiz = 0, False, 0.0, False
    terminal = "wake_budget"
    for tick in range(1, 6):
        prompt = f"{BOOT}\nTask: {episode.eid}\nGoal: {episode.goal}\nResponse: {tick}/5\n" + "\n".join(tail)
        if protocol in ("interaction_v2", "interaction_v3"):
            prompt += (f"\nHarness state: remaining TRY budget: {3 - tries}. "
                       + ("Quiz already revealed; submit six T/F labels with ACT: QUIZ."
                          if revealed else "Quiz reveal still needed before scoring: ACT: QUIZ ?.")
                       + "\nEmit one action only; never supply [OUTCOME] or simulate a world reply.")
        call_id, output = calls.ask("wake", arm, eid, tick, prompt)
        tail.append(output)
        try:
            action = parse_action(output, protocol)
            if action["kind"] == "done":
                terminal = "done"
                break
            require(action["kind"] != "try" or tries < 3, "TRY budget exhausted")
            require(action["kind"] != "reveal" or not revealed, "quiz already revealed")
            require(action["kind"] != "quiz" or revealed, "quiz not revealed")
        except ValueError as error:
            terminal = "protocol_invalid"
            events.append(dict(kind="protocol_invalid", arm=arm, eid=eid, call_id=call_id, failure=str(error)))
            break
        reward, outcome = game.evaluate(episode, action["action"])
        execution = dict(action, kind="execution", action_kind=action["kind"], arm=arm, eid=eid,
                         tick=tick, call_id=call_id, execution_id=f"{arm}:{eid}#t{tick}", reward=reward, outcome=outcome)
        if protocol in ("interaction_v2", "interaction_v3"):
            execution.update(raw_response=output, canonical_action="ACT: " + action["action"])
        if action["kind"] == "try":
            observed = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome)
            require(observed is not None and [int(value) for value in observed.groups()[1:]] == action["values"],
                    "world TRY outcome mismatch")
            execution["observed"] = observed.group(1) == "True"
            tries += 1
        events.append(execution)
        tail.append("[OUTCOME] " + outcome)
        if action["kind"] == "try" and notes:
            record_id, text = calls.ask("record", arm, eid, tick, record_prompt(execution, output, protocol))
            events.append(dict(kind="record", arm=arm, eid=eid, execution_id=execution["execution_id"],
                               source_call_id=call_id, call_id=record_id, text=text, **judge_record(text, execution)))
        if action["kind"] == "reveal":
            revealed = True
        if action["kind"] == "quiz":
            score, valid_quiz, terminal = reward, True, "first_quiz"
            break
    result = dict(arm=arm, eid=eid, tries=tries, quiz_accuracy=score, valid_quiz=valid_quiz, terminal=terminal)
    events.append(dict(kind="task", **result))
    return result, "\n".join(tail)


def run_formation(calls, events):
    tasks, interactions = [], []
    protocol = getattr(calls, "protocol", "strict_v1")
    for arm in ARMS:
        for lesson in range(2):
            eid = task_id(lesson, "pre")
            pre, transcript = play_task(calls, events, arm, eid)
            parent_id = f"{calls.count:04d}"
            if arm == "P":
                def parent_model(prompt, max_tokens, temperature):
                    require(max_tokens == 200 and temperature == .5, "parent helper contract changed")
                    return calls.ask("parent", arm, eid, 0, prompt)[1]
                parent = nursery_dialogue.parent_turn(parent_model, transcript)
            else:
                control = {"strict_v1": CONTROL, "interaction_v2": CONTROL_V2, "interaction_v3": CONTROL_V3}[protocol]
                _, parent = calls.ask("parent", arm, eid, 0, control + transcript[-4000:] + "\n---")
            restate = "\nRestate that message in your own words in 2-3 sentences."
            if arm == "A" and protocol == "interaction_v2":
                restate = ("\nRestate only the acknowledgement of participation in 2-3 sentences. "
                           "No task reflection, quizzes, task summary, or what you learned.")
            restate_id, restatement = calls.ask("restate", arm, eid, 0,
                "Your parent said:\n" + parent + restate)
            interactions.append(dict(arm=arm, lesson=lesson, parent_call_id=parent_id, parent=parent,
                                     restatement_call_id=restate_id, restatement=restatement))
            post, _ = play_task(calls, events, arm, task_id(lesson, "apply"), notes=True, prefix=restatement)
            tasks.extend([pre, post])
    result = dict(status="AWAITING_MAIN_AUDIT", tasks=tasks, interactions=interactions,
                  semantic_no_answer_certification=False, claim_boundary=CLAIM_BOUNDARY,
                  calls=calls.count, roles=dict(calls.counts))
    if protocol == "interaction_v3":
        result.update(protocol=protocol, main_audit_contract=main_audit_contract(protocol))
    return result


def run_evaluation(calls, events, cell):
    require(cell in CELLS, "unknown evaluation cell")
    tasks = [play_task(calls, events, cell, eid, notes=True)[0] for eid in schedule()["evaluation"]]
    return dict(cell=cell, tasks=tasks, calls=calls.count, roles=dict(calls.counts),
                claim_boundary=CLAIM_BOUNDARY,
                mean_quiz_accuracy=sum(task["quiz_accuracy"] for task in tasks) / 4,
                faithful_records=sum(row["kind"] == "record" and row["eligible"] for row in events.rows),
                allotted_record_opportunities=12, semantic_no_answer_certification=False)


def capture_manifest(path):
    write_json(path / "manifest.json", {"files": tree_hashes(path, ("manifest.json",))})


def usage(path):
    by_role = {}
    for request_path in sorted((Path(path) / "calls").glob("*.request.json")):
        request = read(request_path)
        response = read(request_path.with_name(request_path.name.replace(".request.", ".response.")))
        role = request["request"]["role"]
        zero = dict(requests=0, native_input_tokens=0, native_output_tokens=0,
                    output_token_ceiling=0, generation_seconds=0.0)
        totals = by_role.setdefault(role, dict(zero, by_arm={}))
        arm_totals = totals["by_arm"].setdefault(request["request"]["arm"], dict(zero))
        for target in (totals, arm_totals):
            target["requests"] += 1
            target["native_input_tokens"] += len(response["response"]["prompt_token_ids"])
            target["native_output_tokens"] += len(response["response"]["output_token_ids"])
            target["output_token_ceiling"] += request["request"]["max_tokens"]
            target["generation_seconds"] += response["ended"] - request["started"]
    return by_role


def check_capture(path, identity=None, protocol=None):
    path = Path(path)
    failures = []
    try:
        require(read(path / "manifest.json")["files"] == tree_hashes(path, ("manifest.json",)), "capture file hashes changed")
        header = read(path / "identity.json")
        captured_protocol = header.get("protocol", "strict_v1")
        require(captured_protocol in PROTOCOLS, "unknown interaction protocol")
        require(protocol is None or captured_protocol == protocol, "capture protocol differs from plan")
        if identity is not None:
            require(header["backend"] == identity, "capture model/adapter identity mismatch")
        calls = ReplayCalls(path / "calls", header["backend"], captured_protocol)
        events = Events()
        result = (run_formation(calls, events) if header["stage"] == "formation" else
                  run_evaluation(calls, events, header["cell"]))
        require(result == read(path / "result.json"), "recomputed result mismatch")
        actual_events = [decode(line) for line in (path / "events.jsonl").read_text().splitlines()]
        require(actual_events == events.rows, "execution/record provenance mismatch")
        require(read(path / "usage.json") == usage(path), "native usage accounting mismatch")
        require(len(list((path / "calls").glob("*.json"))) == 2 * calls.count, "extra or missing raw calls")
        for role, count in calls.counts.items():
            require(count <= LIMITS[header["stage"]].get(role, 0), "call budget exceeded")
        return dict(ok=True, failures=[], result=result, events=events.rows)
    except (ValueError, OSError, KeyError, TypeError) as error:
        failures.append(str(error))
    return dict(ok=False, failures=failures)


def expected_identity(plan, adapter=None):
    from .model_backend import configured_generation_identity
    return configured_generation_identity(plan["model"], str(adapter) if adapter else None)


def audit_template(path):
    result = read(path / "result.json")
    template = dict(actor="Main", formation_sha256=digest(path / "manifest.json"), provenance_decision="pending",
                provenance_notes="", reviews=[dict(arm=item["arm"], lesson=item["lesson"],
                parent_call_id=item["parent_call_id"], restatement_call_id=item["restatement_call_id"],
                decision="pending", notes="") for item in result["interactions"]])
    if result.get("protocol") == "interaction_v3":
        contract = main_audit_contract("interaction_v3")
        require(result.get("main_audit_contract") == contract, "formation control contract changed")
        template["main_audit_contract"] = contract
        for review in template["reviews"]:
            review.update(parent_contract=contract["parent_contracts"][review["arm"]],
                          child_criterion=contract["child_criterion"], child_observations="")
    return template


def native_tokenizer(model):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    return tokenizer


def audit_tokens(tokenizer, corpus):
    require(len(corpus) == 2, "exactly two child rows required")
    prefixes = [train_adapter.child_record_prefix_length(text) for text in corpus]
    untruncated = tokenizer(corpus, padding=False, truncation=False)["input_ids"]
    require(all(len(row) <= 512 for row in untruncated), "child target would truncate")
    batch = tokenizer(corpus, padding=True, truncation=True, max_length=512, return_offsets_mapping=True)
    receipts = []
    for index, prefix in enumerate(prefixes):
        offsets, attention, input_ids = (batch[field][index] for field in ("offset_mapping", "attention_mask", "input_ids"))
        require([token for token, present in zip(input_ids, attention) if present] == untruncated[index], "native encoding changed")
        mask = train_adapter.child_target_mask(offsets, prefix, attention)
        labels = [token if enabled else -100 for token, enabled in zip(input_ids, mask)]
        counts = train_adapter.child_label_counts(offsets, prefix, attention, labels)
        receipts.append(dict(counts=counts, input_tokens=sum(attention), input_ids_sha256=value_hash(input_ids),
                             labels_sha256=value_hash(labels), row_sha256=value_hash(corpus[index])))
    return receipts


def audit_native_calls(tokenizer, path):
    for request_path in sorted((path / "calls").glob("*.request.json")):
        request = read(request_path)["request"]
        response = read(request_path.with_name(request_path.name.replace(".request.", ".response.")))["response"]
        rendered = tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                 tokenize=False, add_generation_prompt=True)
        require(rendered == response["rendered_prompt"], "native rendered source prompt mismatch")
        require(tokenizer.encode(rendered) == response["prompt_token_ids"], "native source input token mismatch")
        decoded = tokenizer.decode(response["output_token_ids"], skip_special_tokens=True,
                                   clean_up_tokenization_spaces=False)
        if request.get("protocol") in ("interaction_v2", "interaction_v3") and response.get("stop_reason") in request.get("stop", []):
            require(response.get("finish_reason") == "stop", "native stop finish mismatch")
            decoded = decoded.split(response["stop_reason"], 1)[0]
        require(decoded == response["text"], "native source output token mismatch")


def validate_main_audit(decision, template):
    require(decision.get("formation_sha256") == template["formation_sha256"] and decision.get("actor") == "Main",
            "Main audit not bound to this formation")
    require(isinstance(decision.get("provenance_notes"), str) and decision["provenance_notes"].strip(), "Main provenance notes required")
    if "main_audit_contract" in template:
        require(decision.get("main_audit_contract") == template["main_audit_contract"], "Main control contract mismatch")
    reviews = decision.get("reviews", [])
    require(len(reviews) == 4, "audit all four parent/control responses and restatements")
    for actual, expected in zip(reviews, template["reviews"]):
        require(all(actual.get(key) == expected[key] for key in ("arm", "lesson", "parent_call_id", "restatement_call_id")),
                "Main review identity mismatch")
        if "main_audit_contract" in template:
            require(all(actual.get(key) == expected[key] for key in ("parent_contract", "child_criterion")),
                    "Main parent/child assessment scope changed")
        require(actual.get("decision") in ("accept", "reject") and isinstance(actual.get("notes"), str)
                and actual["notes"].strip(), "Main content decision and notes required")
    require(decision.get("provenance_decision") in ("accept", "reject"), "Main provenance decision required")
    return decision["provenance_decision"] == "accept" and all(review["decision"] == "accept" for review in reviews)


def select_records(audit):
    selected, failures = {arm: [] for arm in ARMS}, []
    payloads = [item[field] for item in audit["result"]["interactions"] for field in ("parent", "restatement")] + [RECORD]
    seen = set()
    for row in audit["events"]:
        if row["kind"] != "record":
            continue
        reasons = list(row["failures"])
        if not row["eid"].endswith("/apply") or row["arm"] not in ARMS:
            reasons.append("not formation apply material")
        if row["execution_id"] in seen:
            reasons.append("duplicate execution")
        seen.add(row["execution_id"])
        body = row["text"].strip()
        if any(len(payload.strip()) >= 16 and " ".join(payload.split()) in " ".join(body.split()) for payload in payloads):
            reasons.append("delivered payload bytes in record; lexical check only")
        if reasons:
            failures.append(dict(execution_id=row["execution_id"], call_id=row["call_id"], reasons=reasons))
        elif len(selected[row["arm"]]) < 2:
            selected[row["arm"]].append(row)
    return dict(selected=selected, failures=failures,
                selection="first two distinct executions; post-treatment selection; no quiz/unique-text gate")


def render_corpora(selection):
    return {arm: [f"Situation {row['eid']}; execution {row['execution_id']}.\nMy measured action record: {row['text']}"
                  for row in selection["selected"][arm]] for arm in ARMS}


def material(root, main_audit, tokenizer=None):
    root = Path(root).resolve()
    plan = verify_plan(root)
    require(plan.get("protocol", "strict_v1") != "interaction_v3",
            "interaction_v3 requires build_record_pair; legacy synthetic material disabled")
    require(read(root / "formation" / "result.json")["status"] == "AWAITING_MAIN_AUDIT", "formation incomplete")
    path = root / "formation" / "data"
    audit = check_capture(path, expected_identity(plan), plan.get("protocol", "strict_v1"))
    destination = fresh_directory(root / "material", plan["model"])
    write_json(destination / "provenance.json", audit)
    if not audit["ok"]:
        write_json(destination / "result.json", dict(status="PROVENANCE_FAILURE", failures=audit["failures"]))
        return read(destination / "result.json")
    decision = read(main_audit)
    write_json(destination / "main_audit.json", decision)
    template = audit_template(path)
    if not validate_main_audit(decision, template):
        write_json(destination / "result.json", dict(status="MAIN_DECLINED_MATERIAL", semantic_no_answer_certification=False))
        return read(destination / "result.json")
    selection = select_records(audit)
    write_json(destination / "selection.json", selection)
    if any(len(selection["selected"][arm]) < 2 for arm in ARMS):
        write_json(destination / "result.json", dict(status="PAIRED_SHORTAGE", failures=selection["failures"], no_more_tasks=True))
        return read(destination / "result.json")
    tokenizer = tokenizer or native_tokenizer(plan["model"])
    audit_native_calls(tokenizer, path)
    corpora = render_corpora(selection)
    tokens = {arm: audit_tokens(tokenizer, corpora[arm]) for arm in ARMS}
    for arm in ARMS:
        write_json(destination / f"{arm}.json", dict(recipe="preschool_records_v1", corpus=corpora[arm]))
    write_json(destination / "tokens.json", tokens)
    write_json(destination / "result.json", dict(status="READY", formation_sha256=template["formation_sha256"],
               semantic_no_answer_certification=False, content_decision="Main-supplied audit, not machine certification"))
    capture_manifest(destination)
    return read(destination / "result.json")


def verify_material(root, plan, tokenizer=None):
    require(plan.get("protocol", "strict_v1") != "interaction_v3",
            "interaction_v3 requires actual-record V3 material; legacy synthetic write disabled")
    path = root / "material"
    require(read(path / "result.json")["status"] == "READY", "paired material not ready; no more tasks")
    require(read(path / "manifest.json")["files"] == tree_hashes(path, ("manifest.json",)), "material changed")
    require(read(path / "result.json")["formation_sha256"] == digest(root / "formation" / "data" / "manifest.json"),
            "formation binding changed")
    audit = check_capture(root / "formation" / "data", expected_identity(plan), plan.get("protocol", "strict_v1"))
    require(audit["ok"], "formation provenance failure: " + str(audit["failures"]))
    require(validate_main_audit(read(path / "main_audit.json"), audit_template(root / "formation" / "data")), "Main declined material")
    selection = select_records(audit)
    require(selection == read(path / "selection.json"), "selected executions changed")
    corpora = render_corpora(selection)
    require(all(read(path / f"{arm}.json") == dict(recipe="preschool_records_v1", corpus=corpora[arm])
                for arm in ARMS), "corpus differs from actual selected child outputs")
    tokenizer = tokenizer or native_tokenizer(plan["model"])
    audit_native_calls(tokenizer, root / "formation" / "data")
    tokens = {arm: audit_tokens(tokenizer, read(path / f"{arm}.json")["corpus"]) for arm in ARMS}
    require(tokens == read(path / "tokens.json"), "native token/mask evidence changed")
    return tokens


def remaining_seconds(root, plan):
    spent = 0.0
    for path in root.glob("**/supervision.json"):
        receipt = read(path)
        require(receipt["ok"] and receipt["reservation_release_verified"], "previous worker failed or cleanup unverified")
        spent += receipt["reserved_seconds"]
    remaining = min(RESERVED_SECONDS - spent, plan["lease_end"] - time.time() - 10)
    require(remaining > 0, "lease/reservation cap exhausted")
    return remaining


def supervise(root, plan, stage_path, command, call_path=None, popen=None, occupancy=None):
    popen = popen or subprocess.Popen
    occupancy = occupancy or supervisor.gpu_processes_absent
    require(occupancy(plan["device"]) is True, "selected device occupied or unverifiable")
    timeout = min(WORKER_SECONDS, remaining_seconds(root, plan) - CLEANUP_RESERVE)
    require(timeout > 0, "insufficient lease/reservation time for owned cleanup")
    stage_path.mkdir()
    environment = os.environ.copy()
    environment.update(V6_MODEL=plan["model"], PYTHONPATH=str(REPO), PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
        VLLM_WORKER_MULTIPROC_METHOD="spawn", CUDA_VISIBLE_DEVICES=plan["device"])
    started = time.monotonic()
    process, status, error, group_empty, gpu_empty = None, None, None, False, False
    previous_handlers = {}
    def interrupted(signum, frame):
        raise RuntimeError(f"supervisor interrupted by signal {signum}")
    try:
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGTERM, signal.SIGINT):
                previous_handlers[signum] = signal.signal(signum, interrupted)
        with (stage_path / "stdout.log").open("xb") as log:
            process = popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=str(REPO), env=environment,
                            start_new_session=True)
            write_json(stage_path / "process.json", dict(pid=process.pid, pgid=process.pid, argv=command,
                       device=plan["device"], timeout=timeout, started=started))
            while process.poll() is None:
                now = time.monotonic()
                require(now - started < timeout and time.time() < plan["lease_end"] - 10, "worker/lease timeout")
                if call_path is not None:
                    ready = call_path.parent / "backend.ready.json"
                    require(ready.exists() or now - started < LOAD_SECONDS, "backend load timeout")
                    for request_path in call_path.glob("*.request.json"):
                        response_path = request_path.with_name(request_path.name.replace(".request.", ".response."))
                        if not response_path.exists():
                            require(now - read(request_path)["started"] < CALL_SECONDS, "actual backend call timeout")
                time.sleep(.1)
            status = process.returncode
            require(status == 0, f"worker failed rc={status}")
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        try:
            if process is not None and process.poll() is None:
                process.terminate()
                grace_end = time.monotonic() + CLEANUP_GRACE
                while process.poll() is None and time.monotonic() < grace_end:
                    time.sleep(.05)
            group_empty = supervisor._cleanup_group(process) if process is not None else True
            gpu_empty = occupancy(plan["device"]) is True
        except Exception as cleanup_error:
            error = error or dict(type=type(cleanup_error).__name__, message=str(cleanup_error))
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        receipt = dict(ok=error is None and group_empty and gpu_empty, error=error, returncode=status,
                       owned_group_empty=group_empty, gpu_processes_absent=gpu_empty,
                       reservation_release_verified=group_empty and gpu_empty,
                       reserved_seconds=time.monotonic() - started, device=plan["device"],
                       scope="supervised worker window including owned cleanup; excludes CPU prep/Main audit; Main reserves each phase")
        write_json(stage_path / "supervision.json", receipt)
    require(receipt["ok"], "supervised worker failed: " + str(receipt))
    return receipt


def worker_command(root, stage, out, cell=None):
    command = [sys.executable, "-B", "-m", "organism_v6.rulegame_parenting_diagnostic", "_worker",
               "--root", str(root), "--stage", stage, "--out", str(out), "--allow-gpu"]
    if cell is not None:
        command.extend(["--cell", cell])
    return command


def formation(root, allow_gpu=False):
    require(allow_gpu, "GPU stage requires explicit --allow-gpu")
    root = Path(root).resolve()
    plan = verify_plan(root)
    stage = fresh_directory(root / "formation", plan["model"])
    path = stage / "data"
    try:
        supervise(root, plan, stage / "worker", worker_command(root, "formation", path), path / "calls")
        verify_plan(root)
        audit = check_capture(path, expected_identity(plan), plan.get("protocol", "strict_v1"))
        write_json(stage / "provenance.json", audit)
        require(audit["ok"], str(audit["failures"]))
        write_json(stage / "main_audit.template.json", audit_template(path))
        write_json(stage / "result.json", dict(status="AWAITING_MAIN_AUDIT", formation_sha256=digest(path / "manifest.json")))
    except BaseException as error:
        write_json(stage / "failure.json", dict(error=str(error)))
        raise
    return read(stage / "result.json")


def verify_fit(root, plan, arm, tokens):
    path = root / "write" / arm / "adapter"
    require((path / "DONE").is_file() and not (path / "EMPTY_CORPUS").exists(), "missing complete fit")
    metadata = read(path / "train_meta.json")
    expected = dict(TRAIN, recipe="v1_frozen_child_target_seeded", source_recipe="preschool_records_v1",
                    loss_target="child_body_only", source_corpus_sha256=digest(root / "material" / f"{arm}.json"),
                    supervised_tokens=12 * sum(row["counts"]["supervised_child_tokens"] for row in tokens[arm]),
                    tokens=12 * sum(row["input_tokens"] for row in tokens[arm]))
    require(all(metadata.get(key) == value for key, value in expected.items()), "fit recipe/token/source mismatch")
    require(type(metadata.get("final_loss")) in (int, float) and math.isfinite(metadata["final_loss"]), "nonfinite fit loss")
    config = read(path / "adapter_config.json")
    require(all(config.get(key) == value for key, value in dict(r=8, lora_alpha=16, lora_dropout=.05,
                bias="none", peft_type="LORA").items()), "adapter config mismatch")
    require(Path(config.get("base_model_name_or_path", "")).resolve() == Path(plan["model"]), "adapter base differs")
    weights = [path / name for name in ("adapter_model.safetensors", "adapter_model.bin") if (path / name).is_file()]
    require(len(weights) == 1 and weights[0].stat().st_size > 0, "missing/ambiguous adapter weights")
    return dict(adapter=str(path), files=tree_hashes(path), metadata=metadata)


def write_adapters(root, allow_gpu=False):
    require(allow_gpu, "GPU stage requires explicit --allow-gpu")
    root = Path(root).resolve()
    plan = verify_plan(root)
    tokens = verify_material(root, plan)
    stage = fresh_directory(root / "write", plan["model"])
    write_json(stage / "native_preflight.json", tokens)
    fits = {}
    try:
        for arm in ARMS:
            verify_plan(root)
            require(verify_material(root, plan) == tokens, "paired material changed before fit")
            arm_path = stage / arm
            command = [sys.executable, "-B", "-m", "organism_v6.train_adapter", "--corpus",
                       str(root / "material" / f"{arm}.json"), "--out", str(arm_path / "adapter"),
                       "--rank", "8", "--epochs", "12", "--lr", "1e-4", "--seed", "2"]
            supervise(root, plan, arm_path, command)
            verify_plan(root)
            fits[arm] = verify_fit(root, plan, arm, tokens)
        write_json(stage / "result.json", dict(status="PAIRED_FITS_COMPLETE", fits=fits, promoted=False))
    except BaseException as error:
        write_json(stage / "failure.json", dict(error=str(error), completed_fits=list(fits), evaluation_allowed=False))
        raise
    return read(stage / "result.json")


def verify_fits(root, plan):
    require(not (root / "write" / "failure.json").exists(), "paired write failed")
    result = read(root / "write" / "result.json")
    require(result["status"] == "PAIRED_FITS_COMPLETE" and set(result["fits"]) == set(ARMS), "both fits required")
    tokens = read(root / "write" / "native_preflight.json")
    require({arm: verify_fit(root, plan, arm, tokens) for arm in ARMS} == result["fits"], "fit bytes changed")
    return result["fits"]


def evaluate(root, allow_gpu=False):
    require(allow_gpu, "GPU stage requires explicit --allow-gpu")
    root = Path(root).resolve()
    plan = verify_plan(root)
    verify_material(root, plan)
    fits = verify_fits(root, plan)
    stage = fresh_directory(root / "evaluation", plan["model"])
    results = {}
    try:
        for cell in CELLS:
            verify_plan(root)
            verify_fits(root, plan)
            path = stage / cell / "data"
            supervise(root, plan, stage / cell, worker_command(root, "evaluation", path, cell), path / "calls")
            verify_plan(root)
            verify_fits(root, plan)
            adapter = fits[cell[0]]["adapter"] if cell != "OFF" else None
            audit = check_capture(path, expected_identity(plan, adapter), plan.get("protocol", "strict_v1"))
            write_json(stage / cell / "provenance.json", audit)
            require(audit["ok"], str(audit["failures"]))
            audit_native_calls(native_tokenizer(plan["model"]), path)
            results[cell] = audit["result"]
        means = {cell: result["mean_quiz_accuracy"] for cell, result in results.items()}
        write_json(stage / "result.json", dict(status="COMPLETE", cells=results,
                   claim_boundary=CLAIM_BOUNDARY,
                   P_minus_OFF=means["P_ON"] - means["OFF"], A_minus_OFF=means["A_ON"] - means["OFF"],
                   P_minus_A=means["P_ON"] - means["A_ON"], inference="post-treatment selected material; one shared OFF; exploratory only"))
    except BaseException as error:
        write_json(stage / "failure.json", dict(error=str(error), completed_cells=list(results)))
        raise
    return read(stage / "result.json")


def worker(root, stage, out, cell=None, allow_gpu=False):
    require(allow_gpu, "GPU worker requires explicit --allow-gpu")
    root = Path(root).resolve()
    plan = verify_plan(root)
    require(time.time() < plan["lease_end"] - 10, "lease expired")
    require(supervisor.selected_device() == plan["device"], "worker device differs")
    adapter = None
    if stage == "evaluation":
        require(cell in CELLS, "evaluation cell required")
        fits = verify_fits(root, plan)
        adapter = fits[cell[0]]["adapter"] if cell != "OFF" else None
    else:
        require(stage == "formation" and cell is None, "invalid worker stage")
    expected_path = root / "formation" / "data" if stage == "formation" else root / "evaluation" / cell / "data"
    require(Path(out).resolve() == expected_path, "worker output outside fixed stage")
    process_path = root / "formation" / "worker" if stage == "formation" else root / "evaluation" / cell
    deadline = time.monotonic() + 5
    while not (process_path / "process.json").exists() and time.monotonic() < deadline:
        time.sleep(.05)
    require(read(process_path / "process.json")["pid"] == os.getpid(), "worker requires owning supervisor receipt")
    path = fresh_directory(out, plan["model"])
    parent_pid = os.getppid()
    require(os.getpgrp() == os.getpid(), "worker must own a fresh supervised process group")
    def watch_parent():
        while os.getppid() == parent_pid and time.time() < plan["lease_end"] - 10:
            time.sleep(.2)
        os.killpg(os.getpgrp(), signal.SIGTERM)
    threading.Thread(target=watch_parent, daemon=True).start()
    from .model_backend import close_backend
    def interrupted(signum, frame):
        raise RuntimeError(f"worker interrupted by signal {signum}")
    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGINT)}
    backend = None
    try:
        backend = NativeBackend(plan["model"], adapter)
        identity = expected_identity(plan, adapter)
        require(backend.identity() == identity, "native loader identity differs")
        protocol = plan.get("protocol", "strict_v1")
        header = dict(stage=stage, cell=cell, backend=identity, model_files=plan["model_files"])
        if protocol != "strict_v1":
            header["protocol"] = protocol
        write_json(path / "identity.json", header)
        write_json(path / "backend.ready.json", dict(pid=os.getpid(), ready=time.monotonic()))
        calls, events = Calls(path / "calls", backend, stage, identity, protocol), Events(path / "events.jsonl")
        result = run_formation(calls, events) if stage == "formation" else run_evaluation(calls, events, cell)
        write_json(path / "result.json", result)
        write_json(path / "usage.json", usage(path))
    except BaseException as error:
        write_json(path / "failure.json", dict(error=str(error)))
        raise
    finally:
        closed, cleanup_error = False, None
        try:
            closed = close_backend(backend.backend if backend is not None else None)
        except Exception as error:
            cleanup_error = str(error)
        write_json(path / "backend.cleanup.json", dict(closed=closed, error=cleanup_error,
                   scope="this worker's backend handle and descendant engine PIDs only"))
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
        require(closed is True, "owned backend cleanup failed; retain reservation")
    require(sources() == plan["source_hashes"], "source changed during worker")
    capture_manifest(path)


def replay(root):
    root = Path(root).resolve()
    plan = verify_plan(root, check_model=False)
    captures = {}
    formation_path = root / "formation" / "data"
    if formation_path.exists():
        captures["formation"] = check_capture(formation_path, expected_identity(plan), plan.get("protocol", "strict_v1"))
    for cell in CELLS:
        path = root / "evaluation" / cell / "data"
        if path.exists():
            adapter = root / "write" / cell[0] / "adapter" if cell != "OFF" else None
            captures[cell] = check_capture(path, expected_identity(plan, adapter), plan.get("protocol", "strict_v1"))
    failures = [f"{name}: {failure}" for name, result in captures.items() for failure in result["failures"]]
    return dict(ok=bool(captures) and not failures, captures=captures, failures=failures,
                scope="CPU raw-call/world replay; no semantic no-answer certification or native model-origin authentication")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    for option in ("out", "model", "device", "lease-end"):
        prepare_parser.add_argument("--" + option, required=True)
    prepare_parser.add_argument("--protocol", choices=PROTOCOLS, default="strict_v1")
    for name in ("formation", "material", "write", "evaluate", "replay", "_worker"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        if name in ("formation", "write", "evaluate", "_worker"):
            command.add_argument("--allow-gpu", action="store_true")
        if name == "material":
            command.add_argument("--main-audit", required=True)
        if name == "_worker":
            command.add_argument("--stage", choices=["formation", "evaluation"], required=True)
            command.add_argument("--out", required=True)
            command.add_argument("--cell", choices=CELLS)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.out, args.model, args.device, args.lease_end, args.protocol)
    elif args.command == "material":
        result = material(args.root, args.main_audit)
    elif args.command == "replay":
        result = replay(args.root)
    elif args.command == "_worker":
        result = worker(args.root, args.stage, args.out, args.cell, args.allow_gpu)
    else:
        operation = {"formation": formation, "write": write_adapters, "evaluate": evaluate}[args.command]
        result = operation(args.root, args.allow_gpu)
    if result is not None:
        print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
