"""Context-distilled own raw-wake process write -> fresh OFF/P_ON/A_ON readout.

CPU prepare verifies the completed process-v2 pair and native material custody.
evaluate/_worker require Main's --allow-gpu. No new targets, fits or promotion.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import re
import signal
import sys
import threading
import time


SELF = Path(__file__).resolve()
CELLS = ("OFF", "P_ON", "A_ON")
CONTROLLER_SECONDS = 1800
CLEANUP_SECONDS = 140
LEASE_MARGIN = 21600
FROZEN_READOUT = Path('/tmp/astra_rulegame_record_readout_20260912.py')
FROZEN_SHA256 = '120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde'
VERSION = 'context_distilled_process_parent_free_readout_v1'
WRITE_PROTOCOL = 'rulegame_process_write_v2_20260912'
MATERIAL_PROTOCOL = 'rulegame_grounded_process_pair_v2'
CONDITIONING = 'CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT'
ORIGIN = 'UNRESOLVED_LOCAL_HASHES_ONLY'
CLAIMS = dict(context_distillation=True, model_origin=ORIGIN, clean_lineage=False,
              G3=False, P1=False, G5=False, H1=False, H2=False, semantic_certification=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read(path):
    def reject(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object, parse_constant=reject)


def write_json(path, value):
    with Path(path).open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def absolute_python(value):
    path = os.path.abspath(value)
    require(Path(path).is_file() and os.access(path, os.X_OK), "executable interpreter required")
    return path


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timezone-aware time required")
    return parsed.timestamp()


def load_driver(path, expected_hash):
    path = Path(path).expanduser().resolve(strict=True)
    require(re.fullmatch('[0-9a-f]{64}', expected_hash) and digest(path) == expected_hash,
            'explicit process writer hash differs before import')
    name = "astra_write_" + digest(path)
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    module = sys.modules[name]
    require(getattr(module, 'WRITE_PROTOCOL', None) == WRITE_PROTOCOL and module.PROTOCOL == MATERIAL_PROTOCOL
            and module.CONDITIONING == CONDITIONING and module.ORIGIN == ORIGIN and module.CLAIMS == CLAIMS,
            'only explicit process-write-v2 driver allowed; no record/P0/v1')
    return module


def diagnostic_module(source_root):
    root = Path(source_root).resolve(strict=True)
    sys.path.insert(0, str(root)) if str(root) not in sys.path else None
    module = importlib.import_module("organism_v6.rulegame_parenting_diagnostic")
    require(Path(module.__file__).resolve().parents[1] == root, "imported source-root differs")
    return module


def protocol(diagnostic):
    require(digest(FROZEN_READOUT) == FROZEN_SHA256, 'frozen reference readout changed')
    require(diagnostic.CELLS == CELLS and diagnostic.WORKER_SECONDS == 600
            and diagnostic.CLEANUP_RESERVE == CLEANUP_SECONDS and diagnostic.RESERVED_SECONDS == CONTROLLER_SECONDS,
            "frozen supervisor/cell semantics differ")
    tasks = diagnostic.schedule()["evaluation"]
    require(tasks == [f"rule{rule}/astra-minimum-20260912/readout" for rule in range(2, 6)], "evaluation schedule changed")
    return dict(name=VERSION, interaction_protocol="interaction_v3",
        cells=list(CELLS), tasks=tasks, quiz_items_per_task=6, wake_responses_per_task=5,
        limits=diagnostic.LIMITS["evaluation"], tokens={role: diagnostic.TOKENS[role] for role in ("wake", "record")},
        gen_seed=diagnostic.GEN_SEED, temperature=.7, max_model_len=diagnostic.MAX_MODEL_LEN,
        parent_calls=0, restatement_calls=0, task_prefix="", record_calls=True,
        record_feedback_into_wake=False, record_training=False, task_history="fresh per task; current task only",
        score="unchanged first quiz accuracy; invalid/absent quiz stays zero; fixed denominator four",
        contrasts=["P_minus_OFF", "A_minus_OFF", "P_minus_A"], shared_off=True,
        inference="post-treatment selected material; one shared OFF; exploratory only",
        exclusions="formation rules 0/1 excluded; no confirmation data or new confirmation selection",
        max_calls=96, max_generated_tokens=27600, controller_seconds=CONTROLLER_SECONDS,
        worker_seconds=600, cleanup_seconds=CLEANUP_SECONDS, call_seconds=diagnostic.CALL_SECONDS,
        load_seconds=diagnostic.LOAD_SECONDS, lease_margin_seconds=LEASE_MARGIN,
        claim_boundary=diagnostic.CLAIM_BOUNDARY, training_objective='complete own raw wake plus EOS; not raw RECORD',
        write_protocol=WRITE_PROTOCOL, material_protocol=MATERIAL_PROTOCOL, conditioning=CONDITIONING,
        model_origin=ORIGIN, claims=CLAIMS, quiz_items_total=24, invalid_quiz_items_score_zero=True,
        descriptive_metrics='raw PREDICT emission separate from valid executed predictions; TRY counts/distinct triples; actual/allotted record faithfulness',
        prediction_prompt='unchanged CHILD_BOOT explicitly asks PREDICT before TRY; emission/adherence, not an unprompted-spontaneity assay',
        metric_limits='probe diversity is not information gain; competence assay, not online adaptation or parenting proof',
        training_exposure='natural unequal token lengths retained; no target matching or padding objective',
        reference_readout_sha256=FROZEN_SHA256)


def prepare(write_root, write_plan_sha256, write_driver, write_driver_sha256, out, deadline, lease_end):
    driver = load_driver(write_driver, write_driver_sha256)
    origin, written, diagnostic, _, _ = driver.checked_plan(write_root, write_plan_sha256)
    driver.verify_inputs(written, diagnostic)
    require(read(Path(written["formation_root"]) / "plan.json")["protocol"] == "interaction_v3", "v3 lineage required")
    output = driver.local_path(out, fresh=True)
    require(output.parent == origin.parent and output != origin, "fresh sibling readout root required")
    for protected in (written["model"], written["source_root"], written["formation_root"], written["main_review_path"],
                      written['fixed_candidate_path'], write_driver, SELF):
        require(not driver.overlaps(output, Path(protected).resolve()), "readout overlaps protected input")
    end, lease = timestamp(deadline), timestamp(lease_end)
    require(time.time() + CONTROLLER_SECONDS < end <= lease - LEASE_MARGIN, "need 1800s and six-hour lease margin")
    python = absolute_python(sys.executable)
    require(python == absolute_python(written["python"]), "invoke prepare with exact write-plan venv interpreter; do not resolve symlink")
    plan = dict(schema=2, version=VERSION, out=str(output), write_root=str(origin), write_plan_sha256=write_plan_sha256,
        write_driver=str(Path(write_driver).resolve()), write_driver_sha256=digest(write_driver),
        source_root=written["source_root"], source_pins=written["implementation"],
        model=written["model"], model_files=written["model_files"], device=written["device"], python=python,
        protocol=protocol(diagnostic), deadline=end, supplied_lease_end=lease, lease_cutoff=lease-LEASE_MARGIN,
        self_path=str(SELF), self_sha256=digest(SELF), write_status="COMPLETED_PROCESS_PAIR_NATIVE_VERIFIED",
        write_protocol=WRITE_PROTOCOL, material_protocol=MATERIAL_PROTOCOL, conditioning=CONDITIONING,
        model_origin=ORIGIN, claims=CLAIMS,
        lease_basis="Main-supplied real expiry; not control-plane verification")
    plan['lineage'] = accepted_writes(plan, native=True)
    require(time.time()+CONTROLLER_SECONDS < end, 'native preparation exhausted controller window')
    require(accepted_writes(plan) == plan['lineage'], 'process pair changed during preparation')
    output.mkdir()
    write_json(output / "plan.json", plan)
    frozen = digest(output / "plan.json")
    write_json(output / "plan.sha256.json", dict(sha256=frozen))
    return dict(status="PROCESS_READOUT_FROZEN_NATIVE_PAIR_VERIFIED", root=str(output), plan_sha256=frozen,
                model_origin=ORIGIN, conditioning=CONDITIONING, readout='NOT_RUN')


def checked_plan(root, plan_sha256):
    root = Path(root).expanduser().resolve(strict=True)
    require(digest(root / "plan.json") == plan_sha256, "readout plan changed")
    plan = read(root / "plan.json")
    require(plan['schema'] == 2 and plan['version'] == VERSION and plan['write_protocol'] == WRITE_PROTOCOL
            and plan['material_protocol'] == MATERIAL_PROTOCOL and plan['conditioning'] == CONDITIONING
            and plan['model_origin'] == ORIGIN and plan['claims'] == CLAIMS,
            'process readout protocol/objective/origin differs')
    require(plan["out"] == str(root) and plan["self_path"] == str(SELF) and plan["self_sha256"] == digest(SELF), "readout implementation/root changed")
    require(digest(plan["write_driver"]) == plan["write_driver_sha256"], "write driver changed")
    require(all(digest(path) == expected for path, expected in plan["source_pins"].items()), "source bytes changed")
    diagnostic = diagnostic_module(plan["source_root"])
    require(plan["protocol"] == protocol(diagnostic), "prospective readout protocol changed")
    require(plan["deadline"] <= plan["lease_cutoff"] == plan["supplied_lease_end"]-LEASE_MARGIN, "lease bounds changed")
    require(absolute_python(sys.executable) == plan["python"], "controller interpreter differs from native venv")
    require(accepted_writes(plan) == plan['lineage'], 'completed process-write lineage changed')
    return root, plan, diagnostic


def material_custody(driver, root, written, diagnostic, exporter, trainer, native=False):
    require(written['protocol'] == WRITE_PROTOCOL and written['material_protocol'] == MATERIAL_PROTOCOL
            and written['conditioning'] == CONDITIONING and written['model_origin'] == ORIGIN
            and written['claims'] == CLAIMS and written['init_adapter'] is None,
            'wrong process material or nonfresh initial adapter')
    material = root / 'material'
    candidate = read(material / 'audit/candidate.json')
    review = read(material / 'audit/main_review.json')
    require(candidate == read(written['fixed_candidate_path']) and review == read(written['main_review_path']),
            'sealed candidate/Main review changed')
    require(candidate == exporter.inspect_capture(Path(written['formation_root']) / 'formation/data', protocol=MATERIAL_PROTOCOL),
            'fixed process source selection/context differs')
    exporter._review(candidate, review, protocol=MATERIAL_PROTOCOL)
    token_audit = read(material / 'audit/token_receipts.json')
    export = read(material / 'export_manifest.json')
    corpora = {arm: read(material / 'corpora' / (arm+'.json')) for arm in ('P', 'A')}
    tokens = {arm: read(material / 'provenance' / (arm+'.tokens.json')) for arm in ('P', 'A')}
    pair = dict(protocol=MATERIAL_PROTOCOL, status=export['status'], corpora=corpora,
                audit=dict(token_audit, candidate=candidate, main_review=review))
    driver.check_pair(pair, candidate, review, tokens, diagnostic)
    require(token_audit['native_identity_authenticated'] is False and token_audit['semantic_certification'] is False,
            'material semantic/origin certification forbidden')
    tokenizer = diagnostic.native_tokenizer(written['model']) if native else None
    if native:
        diagnostic.audit_native_calls(tokenizer, Path(written['formation_root']) / 'formation/data')
    for arm in ('P', 'A'):
        require({key: value for key, value in tokens[arm].items() if key not in ('rows', 'batch')} == written['tokens'][arm],
                'prepared process token/exposure summary differs')
        for item, receipt, source in zip(corpora[arm]['corpus'], token_audit['receipts'][arm],
                                         [row for row in candidate['candidates'] if row['arm'] == arm], strict=True):
            context = receipt['transformed_training']['rendered_context']
            require(item['spans'] == [[context, False, 'parent_removed_wake_context'],
                                     [source['target'], True, 'complete_own_raw_wake']]
                    and item['view'] == MATERIAL_PROTOCOL and item['meta']['protocol'] == MATERIAL_PROTOCOL,
                    'only masked transformed context and full own wake target allowed; no record/P0/extra context')
            if native:
                require(tokenizer.apply_chat_template([dict(role='user', content=source['context'])],
                        tokenize=False, add_generation_prompt=True) == context,
                        'native parent-removed context differs; no parent/restatement insertion')
        if native:
            require(driver.full_tokens(corpora[arm], tokenizer, trainer) == tokens[arm],
                    'process native raw-target/mask/EOS/token receipt mismatch')
    return dict(material_manifest_sha256=written['material_manifest_sha256'], candidate_sha256=written['candidate_sha256'],
                main_review_sha256=written['main_review_sha256'], process_api=written['process_api'],
                exporter_source_hashes=written['exporter_source_hashes'], tokens=written['tokens'])


def accepted_writes(plan, native=False):
    driver = load_driver(plan["write_driver"], plan['write_driver_sha256'])
    root, written, diagnostic, exporter, trainer = driver.checked_plan(plan["write_root"], plan["write_plan_sha256"])
    driver.verify_inputs(written, diagnostic)
    require(written["model"] == plan["model"] and written["model_files"] == plan["model_files"]
            and written["source_root"] == plan["source_root"] and written["implementation"] == plan["source_pins"]
            and written["device"] == plan["device"] and absolute_python(written["python"]) == plan["python"], "write lineage differs")
    require(not (root / "run" / "failure.json").exists(), "failed/partial writes cannot be evaluated")
    result_path = root / "run" / "result.json"
    result = read(result_path)
    require(result["status"] == "PAIRED_ADAPTERS_SAVED_READOUT_PENDING" and set(result["arms"]) == {"P", "A"}, "both successful writes required")
    require(result['protocol'] == WRITE_PROTOCOL and result['conditioning'] == CONDITIONING
            and result['model_origin'] == ORIGIN and result['claims'] == CLAIMS
            and result['model_authentication_certified'] is False and result['semantic_no_answer_certification'] is False,
            'completed writer objective/origin/claims differ')
    custody = material_custody(driver, root, written, diagnostic, exporter, trainer, native)
    fits, training = {}, {}
    for arm in ("P", "A"):
        fit = root / "fits" / arm
        require(read(fit / "manifest.json")["files"] == diagnostic.tree_hashes(fit, ("manifest.json",)), "fit seal changed")
        receipt = driver.validate_fit(root, arm, written, diagnostic, trainer)
        require(read(fit / "receipt.json") == receipt, "fit receipt changed")
        supervision_path = root / "run" / arm / "supervision.json"
        supervision = read(supervision_path)
        require(supervision["ok"] and supervision["reservation_release_verified"], "write cleanup unverified")
        sealed = dict(receipt, fit_manifest_sha256=digest(fit / "manifest.json"), supervision_sha256=digest(supervision_path))
        require(result["arms"][arm] == sealed, "completed pair receipt differs")
        fits[arm] = sealed
        manifest = read(fit / 'adapter/train_manifest.json')
        require(result['exposure'][arm] == written['tokens'][arm]['exposure'], 'paired exposure summary differs')
        training[arm] = dict(final_loss=manifest['final_loss'], mean_loss_per_epoch=manifest['mean_loss_per_epoch'],
                            tokens=manifest['tokens'], train_tokens_seen=manifest['train_tokens_seen'],
                            exposure=written['tokens'][arm]['exposure'], steps=manifest['steps'])
    return dict(write_plan_sha256=plan["write_plan_sha256"], result_sha256=digest(result_path), fits=fits,
                material=custody, training_metadata=training, model_origin=ORIGIN, conditioning=CONDITIONING)


SPEC_KEYS = {"schema", "cell", "data", "model", "model_files", "adapter", "adapter_files", "device", "python",
             "source_root", "source_pins", "self_sha256", "protocol", "hard_end", "nonce"}


def worker_spec(root, plan, lineage, cell, hard_end):
    fit = lineage["fits"][cell[0]] if cell != "OFF" else None
    return dict(schema=1, cell=cell, data=str(root / "run" / cell / "data"),
        model=plan["model"], model_files=plan["model_files"], adapter=fit["adapter"] if fit else None,
        adapter_files=fit["files"] if fit else {}, device=plan["device"], python=plan["python"],
        source_root=plan["source_root"], source_pins=plan["source_pins"], self_sha256=plan["self_sha256"],
        protocol=plan["protocol"], hard_end=hard_end, nonce=secrets.token_hex(16))


@contextmanager
def work_window(hard_end):
    require(threading.current_thread() is threading.main_thread() and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), "exclusive main-thread timer required")
    remaining = hard_end-time.time()-CLEANUP_SECONDS
    require(remaining > 0, "controller cleanup reserve exhausted")
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError("readout controller work window exhausted")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@contextmanager
def supervised_window(hard_end):
    signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        yield
    finally:
        remaining = hard_end-time.time()-CLEANUP_SECONDS
        if remaining > 0:
            signal.setitimer(signal.ITIMER_REAL, remaining)


@contextmanager
def owning_process(stage, hard_end):
    until = time.monotonic()+5
    while not (stage / "process.json").exists() and time.monotonic() < until:
        time.sleep(.05)
    receipt = read(stage / "process.json")
    require(receipt["pid"] == receipt["pgid"] == os.getpid() == os.getpgrp() == os.getsid(0), "fresh owning supervisor process required")
    parent = os.getppid()
    stop = threading.Event()
    def watch():
        while not stop.wait(.2):
            if os.getppid() != parent or time.time() >= hard_end-10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return
    def interrupted(signum, frame):
        raise RuntimeError(f"readout worker interrupted: {signum}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    threading.Thread(target=watch, daemon=True).start()
    try:
        yield
    finally:
        stop.set()
        for number, handler in handlers.items():
            signal.signal(number, handler)


def close_native(backend):
    from organism_v6.model_backend import close_backend
    return close_backend(backend.backend if backend is not None else None)


def verify_worker_bytes(spec, diagnostic):
    require(all(digest(path) == expected for path, expected in spec["source_pins"].items())
            and digest(SELF) == spec["self_sha256"], "worker source changed")
    require(diagnostic.model_hashes(spec["model"]) == spec["model_files"], "worker base changed")
    if spec["adapter"]:
        require(diagnostic.tree_hashes(spec["adapter"]) == spec["adapter_files"], "worker adapter changed")


def worker(spec, spec_sha256, allow_gpu=False):
    require(allow_gpu, "--allow-gpu required before worker work")
    spec_path = Path(spec).resolve(strict=True)
    require(digest(spec_path) == spec_sha256, "worker spec changed")
    spec = read(spec_path)
    require(set(spec) == SPEC_KEYS and spec["cell"] in CELLS, "worker spec extra context/invalid fields")
    require((spec["adapter"] is None and spec["adapter_files"] == {}) if spec["cell"] == "OFF"
            else bool(spec["adapter"] and spec["adapter_files"]), "OFF/ON adapter mismatch")
    diagnostic = diagnostic_module(spec["source_root"])
    require(spec["protocol"] == protocol(diagnostic), "worker protocol changed")
    require(absolute_python(sys.executable) == spec["python"] and os.environ.get("CUDA_VISIBLE_DEVICES") == spec["device"], "worker interpreter/device mismatch")
    require(time.time() < spec["hard_end"]-CLEANUP_SECONDS, "worker window exhausted")
    stage = spec_path.parent / spec["cell"]
    data = stage / "data"
    require(spec_path.name == spec["cell"] + ".spec.json" and str(data) == spec["data"] and not data.exists(), "fixed fresh worker output required")
    with owning_process(stage, spec["hard_end"]):
        verify_worker_bytes(spec, diagnostic)
        data.mkdir()
        write_json(data / "isolation.json", dict(pid=os.getpid(), pgid=os.getpgrp(), parent_pid=os.getppid(),
            spec_sha256=spec_sha256, parent_calls=0, task_prefix="", record_training=False,
            scope="fresh process and exact replayed prompts; not OS-level filesystem isolation"))
        backend = None
        try:
            backend = diagnostic.NativeBackend(spec["model"], spec["adapter"])
            identity = diagnostic.expected_identity(spec, spec["adapter"])
            require(backend.identity() == identity, "native backend identity differs")
            write_json(data / "identity.json", dict(stage="evaluation", cell=spec["cell"], backend=identity,
                model_files=spec["model_files"], protocol="interaction_v3"))
            write_json(data / "backend.ready.json", dict(pid=os.getpid(), ready=time.monotonic()))
            calls = diagnostic.Calls(data / "calls", backend, "evaluation", identity, "interaction_v3")
            events = diagnostic.Events(data / "events.jsonl")
            result = diagnostic.run_evaluation(calls, events, spec["cell"])
            write_json(data / "result.json", result)
            write_json(data / "usage.json", diagnostic.usage(data))
            diagnostic.audit_native_calls(backend.backend.tok, data)
            write_json(data / "native_audit.json", dict(ok=True, calls=calls.count, scope="actual rendered prompts/input IDs/decoded output IDs"))
        except BaseException as error:
            write_json(data / "failure.json", dict(error=type(error).__name__ + ": " + str(error)))
            raise
        finally:
            closed, failure = False, None
            try:
                closed = close_native(backend)
            except Exception as error:
                failure = str(error)
            write_json(data / "backend.cleanup.json", dict(closed=closed, error=failure))
            require(closed is True, "backend cleanup unverified")
        verify_worker_bytes(spec, diagnostic)
        require(digest(spec_path) == spec_sha256, "worker spec changed during evaluation")
        diagnostic.capture_manifest(data)
        return dict(status="CAPTURED", cell=spec["cell"])


def audit_cell(root, plan, lineage, cell, diagnostic):
    data = root / "run" / cell / "data"
    adapter = lineage["fits"][cell[0]]["adapter"] if cell != "OFF" else None
    header = read(data / "identity.json")
    require(header["stage"] == "evaluation" and header["cell"] == cell and header["model_files"] == plan["model_files"], "wrong cell/stage/base capture")
    audit = diagnostic.check_capture(data, diagnostic.expected_identity(plan, adapter), "interaction_v3")
    require(audit["ok"], "readout replay failed: " + str(audit["failures"]))
    require(read(data / "native_audit.json")["ok"] and read(data / "backend.cleanup.json")["closed"], "native audit/cleanup missing")
    require(not (data / "failure.json").exists(), "failed capture")
    diagnostic.audit_native_calls(diagnostic.native_tokenizer(plan['model']), data)
    audit['process_metrics'] = process_metrics(data, audit, diagnostic)
    return audit


def process_metrics(data, audit, diagnostic):
    result, events = audit['result'], audit['events']
    tasks = diagnostic.schedule()['evaluation']
    require([row['eid'] for row in result['tasks']] == tasks and len(tasks) == 4, 'fixed four-task denominator differs')
    requests = []
    for path in sorted((data / 'calls').glob('*.request.json')):
        sent = read(path)['request']
        response = read(path.with_name(path.name.replace('.request.', '.response.')))['response']
        require(sent['role'] in ('wake', 'record') and sent['eid'] in tasks, 'parent/restatement/foreign task call forbidden')
        requests.append((sent, response['text']))
    require(len(requests) == result['calls'] <= 32, 'per-cell call ceiling differs')
    rows = []
    for task in result['tasks']:
        eid = task['eid']
        executions = [row for row in events if row['kind'] == 'execution' and row['eid'] == eid and row['action_kind'] == 'try']
        records = [row for row in events if row['kind'] == 'record' and row['eid'] == eid]
        predicted = [row for row in executions if type(row['predicted']) is bool and not row['prediction_ambiguous']]
        correct = sum(row['predicted'] == row['observed'] for row in predicted)
        wake = [text for sent, text in requests if sent['eid'] == eid and sent['role'] == 'wake']
        emissions = [len(re.findall(r'^PREDICT:\s*[^\n]*', text, re.MULTILINE)) for text in wake]
        distinct = len({tuple(row['values']) for row in executions})
        invalid = sum(row['kind'] == 'protocol_invalid' and row['eid'] == eid for row in events)
        require(type(task['valid_quiz']) is bool and math.isfinite(task['quiz_accuracy'])
                and 0 <= task['quiz_accuracy'] <= 1 and (task['valid_quiz'] or task['quiz_accuracy'] == 0),
                'invalid quiz must retain zero')
        items_correct = round(task['quiz_accuracy']*6)
        require(abs(items_correct-task['quiz_accuracy']*6) < 1e-6 and len(executions) == task['tries'] <= 3,
                'quiz numerator or TRY budget differs')
        rows.append(dict(eid=eid, quiz_items=6, quiz_items_correct=items_correct, valid_quiz=task['valid_quiz'],
                         invalid_or_absent_quiz=not task['valid_quiz'], wake_responses=len(wake),
                         predict_emitting_responses=sum(count > 0 for count in emissions), predict_lines=sum(emissions),
                         protocol_invalid_actions=invalid, executed_probes=len(executions), distinct_probe_triples=distinct,
                         repeated_probe_triples=len(executions)-distinct, allotted_probe_opportunities=3,
                         valid_predicted_probes=len(predicted), correct_predicted_probes=correct,
                         probes_without_unambiguous_prediction=len(executions)-len(predicted),
                         prediction_accuracy=correct/len(predicted) if predicted else None,
                         actual_records=len(records), faithful_records=sum(row['eligible'] for row in records),
                         invalid_records=sum(not row['eligible'] for row in records), allotted_record_opportunities=3))
    keys = ('quiz_items', 'quiz_items_correct', 'wake_responses', 'predict_emitting_responses', 'predict_lines',
            'protocol_invalid_actions', 'executed_probes', 'distinct_probe_triples', 'repeated_probe_triples',
            'allotted_probe_opportunities', 'valid_predicted_probes', 'correct_predicted_probes',
            'probes_without_unambiguous_prediction', 'actual_records', 'faithful_records', 'invalid_records', 'allotted_record_opportunities')
    totals = {key: sum(row[key] for row in rows) for key in keys}
    require(totals['quiz_items'] == 24 and totals['allotted_record_opportunities'] == 12
            and totals['faithful_records'] == result['faithful_records']
            and abs(totals['quiz_items_correct']/24-result['mean_quiz_accuracy']) < 1e-6
            and totals['actual_records'] == result['roles'].get('record', 0)
            and totals['wake_responses'] == result['roles'].get('wake', 0), 'metric/raw/result denominator differs')
    return dict(tasks=rows, totals=totals, quiz_accuracy_fixed24=totals['quiz_items_correct']/24,
                invalid_or_absent_quiz_tasks=sum(row['invalid_or_absent_quiz'] for row in rows),
                prediction_accuracy=totals['correct_predicted_probes']/totals['valid_predicted_probes'] if totals['valid_predicted_probes'] else None,
                prediction_fraction_executed_probes=totals['valid_predicted_probes']/totals['executed_probes'] if totals['executed_probes'] else None,
                prediction_fraction_allotted12=totals['valid_predicted_probes']/12,
                faithful_record_fraction_actual=totals['faithful_records']/totals['actual_records'] if totals['actual_records'] else None,
                faithful_record_fraction_allotted12=totals['faithful_records']/12,
                limitation='Boot explicitly requests PREDICT: emission/adherence is not unprompted spontaneity or necessarily a valid executed prediction; probe diversity is not information gain. No online updates.')


def evaluate(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, "--allow-gpu required before controller work")
    started_wall, started = time.time(), time.monotonic()
    with work_window(started_wall+CONTROLLER_SECONDS):
        root, plan, diagnostic = checked_plan(root, plan_sha256)
    hard_end = min(started_wall+CONTROLLER_SECONDS, plan["deadline"], plan["lease_cutoff"])
    run = root / "run"
    run.mkdir()
    completed = {}
    try:
        with work_window(hard_end):
            lineage = accepted_writes(plan, native=True)
            require(lineage == plan['lineage'], 'prepared process pair changed before readout')
            write_json(run / "lineage.json", lineage)
            write_json(run / "controller.json", dict(plan_sha256=plan_sha256, started_wall=started_wall,
                hard_end=hard_end, cleanup_reserve=CLEANUP_SECONDS, pid=os.getpid()))
            for cell in CELLS:
                checked_plan(root, plan_sha256)
                require(accepted_writes(plan) == lineage, "paired write lineage changed")
                require(time.time() < hard_end-CLEANUP_SECONDS, "insufficient next-cell work window")
                spec_path = run / (cell + ".spec.json")
                write_json(spec_path, worker_spec(root, plan, lineage, cell, hard_end))
                spec_hash = digest(spec_path)
                command = [plan["python"], "-B", str(SELF), "_worker", "--spec", str(spec_path),
                           "--spec-sha256", spec_hash, "--allow-gpu"]
                with supervised_window(hard_end):
                    supervision = diagnostic.supervise(root, dict(model=plan["model"], device=plan["device"], lease_end=hard_end),
                        run / cell, command, run / cell / "data" / "calls")
                require(supervision["ok"] and supervision["reservation_release_verified"], "readout cleanup unverified")
                require(time.time() < hard_end-CLEANUP_SECONDS, "controller work window exhausted after cleanup")
                require(digest(spec_path) == spec_hash, "supervised worker spec changed")
                audit = audit_cell(root, plan, lineage, cell, diagnostic)
                write_json(run / cell / "provenance.json", audit)
                completed[cell] = dict(result=audit["result"], capture_sha256=digest(run / cell / "data" / "manifest.json"),
                    spec_sha256=spec_hash, supervision_sha256=digest(run / cell / "supervision.json"),
                    process_metrics=audit['process_metrics'])
            checked_plan(root, plan_sha256)
            require(accepted_writes(plan) == lineage, "paired write lineage changed during readout")
            for cell, receipt in completed.items():
                require(digest(run / cell / "data" / "manifest.json") == receipt["capture_sha256"]
                        and digest(run / (cell + ".spec.json")) == receipt["spec_sha256"]
                        and digest(run / cell / "supervision.json") == receipt["supervision_sha256"], "earlier cell changed")
                require(audit_cell(root, plan, lineage, cell, diagnostic)['process_metrics'] == receipt['process_metrics'],
                        'earlier process metrics changed')
        require(time.monotonic()-started <= CONTROLLER_SECONDS and time.time() <= hard_end, "inclusive controller cap exceeded")
        means = {cell: receipt["result"]["mean_quiz_accuracy"] for cell, receipt in completed.items()}
        result = dict(status="COMPLETE_EXPLORATORY_READOUT", cells=completed,
            P_minus_OFF=means["P_ON"]-means["OFF"], A_minus_OFF=means["A_ON"]-means["OFF"], P_minus_A=means["P_ON"]-means["A_ON"],
            inference=plan["protocol"]["inference"], claim_boundary=diagnostic.CLAIM_BOUNDARY,
            version=VERSION, training_objective=plan['protocol']['training_objective'], conditioning=CONDITIONING,
            model_origin=ORIGIN, claims=CLAIMS, training_metadata=lineage['training_metadata'],
            protocol=plan['protocol'],
            controller_seconds=time.monotonic()-started, adaptation_test=False,
            semantic_nonleakage_certified=False, model_authentication_certified=False)
        write_json(run / "result.json", result)
        return result
    except BaseException as error:
        write_json(run / "failure.json", dict(error=type(error).__name__ + ": " + str(error),
            completed_cells=list(completed), retry=False, aggregate=None, controller_seconds=time.monotonic()-started))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for name in ("write-root", "write-plan-sha256", "write-driver", "write-driver-sha256", "out", "deadline", "lease-end"):
        prep.add_argument("--"+name, required=True)
    evaluation = sub.add_parser("evaluate")
    for name in ("root", "plan-sha256"):
        evaluation.add_argument("--"+name, required=True)
    evaluation.add_argument("--allow-gpu", action="store_true")
    child = sub.add_parser("_worker")
    for name in ("spec", "spec-sha256"):
        child.add_argument("--"+name, required=True)
    child.add_argument("--allow-gpu", action="store_true")
    args = vars(parser.parse_args(argv))
    action = args.pop("action")
    result = {"prepare": prepare, "evaluate": evaluate, "_worker": worker}[action](**args)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
