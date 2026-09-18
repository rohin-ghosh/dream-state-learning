"""One disposable OLD AUTH write, not CAL/P1/C11 or a full execution contract.

Only explicit train_fit can create a model or write an adapter. Targets must
come from replayed native formation; structural banks never author targets.
"""
import copy
import hashlib
from pathlib import Path

from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_formation_plan as planner
from organism_v6 import pcfl_vertical_prepare as prepare
from organism_v6 import pcfl_vertical_train as writer


SCHEMA = "pcfl.own_write.old_auth.low200.v1"
require, canonical, digest = writer.require, writer.canonical, writer.digest
BINDING_FIELDS = {"authority_sha256", "init_seed", "dropout_seed", "base_state_sha256",
                  "environment", "tokenizer_receipt", "sources"}


def _same(actual, expected, label):
    require(canonical(actual) == canonical(expected), label)


def _seal(value):
    value = copy.deepcopy(value)
    return {**value, "sha256": digest(value)}


def _unseal(value, expected):
    writer._hash(expected)
    require(type(value) is dict and value.get("sha256") == expected, "independent seal mismatch")
    require(digest({key: item for key, item in value.items() if key != "sha256"}) == expected, "seal drift")


def build_schedule(plan, plan_sha256, *, batch_seed):
    """Pre-output deterministic 17 first blocks + 3 authentic EVENT replays.

    The existing replay balance/rotation rule uses the independently sealed
    single-life plan as its domain root, not a fictitious full-campaign hash.
    """
    planner.validate_plan(plan, plan_sha256)
    require(plan["cell"]["root"]["label"] == "disposable/0" and plan["stage"] == "OLD", "disposable OLD only")
    require(type(batch_seed) is int and 0 <= batch_seed < 2**63, "batch seed")
    first = planner.first_block_slots(plan, plan_sha256)
    require(len(first) == 17 and sum(slot["row_type"] == "EVENT" for slot in first) == 14, "17 first blocks: 14 EVENT/3 LINK")
    slots = {slot["id"]: slot for slot in first}
    eligible = sorted(slot["id"] for slot in first if slot["row_type"] == "EVENT")
    domain = [plan_sha256, "S1", "S1_four_arm", "EVENT", "replay"]
    selected, counts = prepare._select_replay(slots, eligible, [], 3, domain)
    for index, source in enumerate(selected, 17):
        slots[f"s{index:02}"] = {**copy.deepcopy(slots[source]), "id": f"s{index:02}", "source": source}
    conflicts = {name: {other for other, candidate in slots.items() if other != name and
                       (set(slot["support"]).intersection(candidate["support"]) or
                        slot["row_type"] == candidate["row_type"] == "LINK")}
                 for name, slot in slots.items()}
    order = sorted(slots, key=lambda name: (-len(conflicts[name]), digest([batch_seed, name]), name))
    groups = [[] for _ in range(5)]

    def place(index):
        if index == len(order):
            return True
        name = order[index]
        for group in groups:
            if len(group) < 4 and not conflicts[name].intersection(group):
                group.append(name)
                if place(index + 1):
                    return True
                group.pop()
                if not group:
                    break
        return False

    require(place(0), "no disjoint four-example partition; do not resample")
    corpus = {"id": "disposable/0/S1_AUTH", "root": "disposable/0", "arm": "S1_AUTH", "slots": list(slots.values())}
    epoch = [[[name, view] for name in group] for view in range(8) for group in groups]
    epochs = [copy.deepcopy(epoch) for _ in range(5)]
    writer._schedule(corpus, epochs)
    return _seal({"schema": SCHEMA + "/schedule", "plan_sha256": plan_sha256, "batch_seed": batch_seed,
                  "corpus": corpus, "epochs": epochs,
                  "replay": {"domain": domain, "eligible": eligible, "selected": selected, "support_counts": counts},
                  "recipe": {"learning_rate": 3e-5, "updates": 200, "rank": 8, "alpha": 16, "dropout": 0.05,
                             "objective": writer.OBJECTIVE, "layout": writer.LAYOUT}})


def validate_schedule(plan, plan_sha256, schedule, schedule_sha256):
    _unseal(schedule, schedule_sha256)
    _same(schedule, build_schedule(plan, plan_sha256, batch_seed=schedule["batch_seed"]), "pre-output schedule drift")
    return schedule["corpus"], schedule["epochs"]


def source_snapshot():
    from gpu import astra_pcfl_own_write_dev as formation
    from gpu import astra_pcfl_native_actor as native
    from gpu import astra_pcfl_zero_fit_dev as zero
    return {name: hashlib.sha256(Path(module.__file__ if name != "own_writer" else __file__).read_bytes()).hexdigest()
            for name, module in (("own_writer", writer), ("writer", writer), ("shared", writer.shared),
                                 ("core", core), ("preparer", prepare), ("planner", planner),
                                 ("formation", formation), ("native_actor", native), ("tokenizer_render", zero))}


def _native_binding(config, report, receipts, binding):
    from gpu import astra_pcfl_own_write_dev as formation
    from gpu import astra_pcfl_native_actor as native
    writer._record(receipts, ("config", "identity", "load", "close"), "native lifecycle")
    settings, identity = receipts["config"], receipts["identity"]
    _same(settings, config["actor_config"], "formation actor config")
    _same([identity["kind"], identity["config_sha256"]], ["NATIVE", digest(settings)], "native identity required")
    witness = identity["identity"]
    _same([witness[key] for key in ("repository", "revision", "mount", "lora_request", "clean_lineage_certified")],
          [native.MODEL_NAME, native.REVISION, "C0", None, False], "frozen C0 witness")
    require(len(witness["model_files"]) == 14 and not any("adapter" in name.lower() for name in witness["model_files"]), "14 frozen base files")
    for checksum in witness["model_files"].values():
        writer._hash(checksum)
    environment = binding["environment"]
    require(type(environment) is dict, "factory environment required")
    _same([environment[key] for key in ("base", "model_revision", "model_files", "tokenizer_revision", "chat_template_sha256")],
          [prepare.RECIPE["base"], native.REVISION, witness["model_files"], native.REVISION, settings["chat_template_sha256"]], "factory base/tokenizer identity")
    token_receipt = binding["tokenizer_receipt"]
    writer._record(token_receipt, ("kind", "revision", "files", "chat_template_sha256", "measurements"), "scoped tokenizer receipt")
    _same([token_receipt[key] for key in ("kind", "revision", "files", "chat_template_sha256")],
          ["offline_measurement", native.REVISION, settings["tokenizer_files"], settings["chat_template_sha256"]], "actual offline tokenizer receipt")
    require(set(token_receipt["files"]) == native.TOKENIZER_FILES and type(token_receipt["measurements"]) is list and token_receipt["measurements"], "complete tokenizer pins/measurements")
    for measurement in token_receipt["measurements"]:
        writer._record(measurement, ("text", "token_ids"), "tokenizer measurement")
        require(type(measurement["text"]) is str and native.token_ids(measurement["token_ids"]), "nonempty tokenizer surface")
    close, load = receipts["close"], receipts["load"]
    _same([close[key] for key in ("kind", "failed", "error_type", "budget_exceeded", "calls_consumed", "token_count_calls")],
          ["NATIVE", False, None, False, 20, 0], "complete native formation lifecycle")
    _same([load[key] for key in ("kind", "mount", "lora_request")], ["NATIVE", "C0", None], "native load route")
    for value in (load["operation_started"], load["model_load_started"], load["ready_at"], close["elapsed_actor_seconds"]):
        native.number(value)
    require(load["operation_started"] <= load["model_load_started"] <= load["ready_at"] and
            report["device_seconds"] <= close["elapsed_actor_seconds"] <= settings["device_seconds_cap"], "native lifecycle clock")
    for index, slot in enumerate(report["slots"]):
        files = formation._capture_data(slot["attempt"]["capture"], index)
        _same(files["config.json"], settings, "capture/config join")
        _same(files["identity.json"], identity, "capture/identity join")
        raw = files[f"call_{index:04}.raw.json"]
        require(raw["generation_started"] >= load["ready_at"], "generation precedes model load")


def build_fit(config, config_sha256, report, report_sha256, schedule, schedule_sha256, binding, native_receipts):
    """Bind complete native formation, never create target text or choose a dose.

    All three independently retained seals are mandatory. This code cannot
    prove when the caller retained them or authorize a lease/model invocation.
    """
    writer._record(binding, BINDING_FIELDS, "own-write binding")
    fit = _seal({"schema": SCHEMA, "config": config, "config_sha256": config_sha256,
                 "report": report, "report_sha256": report_sha256, "schedule": schedule,
                 "schedule_sha256": schedule_sha256, "native_receipts": native_receipts,
                 "binding": {**binding, "learning_rate": 3e-5}})
    validate_fit(fit)
    return fit


def validate_fit(fit):
    from gpu import astra_pcfl_own_write_dev as formation
    writer._record(fit, ("schema", "config", "config_sha256", "report", "report_sha256", "schedule",
                         "schedule_sha256", "native_receipts", "binding", "sha256"), "own-write fit")
    _unseal(fit, fit["sha256"])
    require(fit["schema"] == SCHEMA, "separate diagnostic schema required")
    binding, config, report = fit["binding"], fit["config"], fit["report"]
    writer._record(binding, BINDING_FIELDS | {"learning_rate"}, "bound own-write recipe")
    _same(binding["learning_rate"], 3e-5, "one LOW recipe only")
    for name in ("authority_sha256", "base_state_sha256"):
        writer._hash(binding[name])
    for name in ("init_seed", "dropout_seed"):
        require(type(binding[name]) is int and 0 <= binding[name] < 2**63, "integer RNG seed")
    _same(binding["sources"], source_snapshot(), "loaded writer/source drift")
    _unseal(report, fit["report_sha256"])
    formation.replay_validate(config, fit["config_sha256"], report)
    _same([report[key] for key in ("status", "failure", "capture_kinds", "fits", "updates", "full_contract_released")],
          ["COMPLETE", None, ["NATIVE"], 0, 0, False], "complete native-only formation required")
    plan = config["planner"]
    corpus, epochs = validate_schedule(plan, plan["plan_sha256"], fit["schedule"], fit["schedule_sha256"])
    payload = report["writer_payload"]
    _same(payload["first_block_slots"], plan["first_blocks"], "formation first blocks")
    _same(payload["controls"], [], "AUTH only, no control/ideal targets")
    require(len(payload["rows"]) == len(payload["generations"]) == 12, "eight EVENT/four LINK generations")
    writer._lineage({}, corpus, payload["rows"], payload["generations"], [])
    _same(payload["queries"], core.materialize_queries(payload["rows"]), "exact admitted query compiler")
    for slot in corpus["slots"]:
        query = payload["queries"][slot["request"]]
        _same(query["support"], slot["support"], "scheduled source support")
        core.read_query(payload["queries"], slot["request"])
    writer._schedule(corpus, epochs)
    _native_binding(config, report, fit["native_receipts"], binding)
    return {"schema": SCHEMA + "/validation", "fit_sha256": fit["sha256"], "formation_report_sha256": fit["report_sha256"],
            "schedule_sha256": fit["schedule_sha256"], "slots": 20, "views": 8, "epochs": 5, "updates": 200,
            "presentations": 800, "native_capture_joins_verified": True, "native_custody_verified": False,
            "full_contract_released": False, "cal_qualified": False, "parenting": False}


def encode_fit(fit, tokenizer):
    """Reuse the extracted existing response+EOS encoder; no synthetic gate."""
    from gpu import astra_pcfl_own_write_dev as formation
    from gpu import astra_pcfl_zero_fit_dev as zero
    validate_fit(fit)
    require(callable(getattr(writer, "_encode_corpus", None)), "Main-owned _encode_corpus extraction not available")
    for index, slot in enumerate(fit["report"]["slots"]):
        files = formation._capture_data(slot["attempt"]["capture"], index)
        prefix = f"call_{index:04}."
        text, ids = zero._render(tokenizer, files[prefix + "request.json"]["request"]["messages"])
        render, raw = files[prefix + "render.json"], files[prefix + "raw.json"]["raw"]
        _same([text, ids], [render["rendered_prompt"], render["prompt_token_ids"]], "actual formation tokenizer render")
        _same(tokenizer.decode(raw["output_token_ids"], skip_special_tokens=True), raw["text"], "actual native output decode")
    schedule = fit["schedule"]
    return writer._encode_corpus(fit["sha256"], schedule["corpus"], schedule["epochs"],
                                 fit["report"]["writer_payload"]["queries"], core.registries()["render_registry"],
                                 fit["binding"]["environment"]["chat_template_sha256"], tokenizer)


def train_fit(fit, tokenizer, base_factory, out):
    """Explicit single LOW write; caller owns allocation, clocks and cold READs."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    validation = validate_fit(fit)
    require(callable(getattr(writer, "_train_encoded", None)), "Main-owned _train_encoded extraction not available")
    writer.verify_tokenizer_files({"contract": {"tokenizer_receipt": fit["binding"]["tokenizer_receipt"]}}, tokenizer)
    encoded = encode_fit(fit, tokenizer)
    return writer._train_encoded(fit, encoded, base_factory, out, fit["binding"]["environment"], validation,
                                 report_name="own_write_scope_report.json")
