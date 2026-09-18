"""Separate fixed EVENT-prefix LOW200 scope; unchanged numerical writer."""

import copy
import hashlib
from pathlib import Path

from gpu import astra_pcfl_event_prefix_import as prefix
from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_prepare as prepare
from organism_v6 import pcfl_vertical_train as writer


SCHEMA = "pcfl.event_only.low200.v1"
ENDPOINT = {"views": [0, 8], "queries_per_view": 14, "calls_per_arm": 28, "calls_total": 56,
            "primary_view": 8, "exact_service_required": 14, "auth_min": 13, "c0_max": 1,
            "paired_gain_min": 12, "stop_required": True, "full_bank_threshold_applied": False}
BINDING_FIELDS = {"authority_sha256", "base_state_sha256", "init_seed", "dropout_seed", "environment", "tokenizer_receipt", "sources"}
same, seal, unseal = prefix.same, prefix.seal, prefix.unseal
require = writer.require


def source_snapshot():
    return {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in
            (("event_writer", __file__), ("prefix_importer", prefix.__file__), ("core", core.__file__),
             ("preparer", prepare.__file__), ("writer", writer.__file__), ("shared", writer.shared.__file__),
             ("native_actor", prefix.native.__file__))}


def _schedule(imported):
    queries = imported["queries"]
    fields = {row["fields"]["event"]: row["fields"] for row in imported["rows"]}
    slots = {}
    for index, (request, query) in enumerate(sorted(queries.items())):
        name = f"s{index:02}"
        slots[name] = {"id": name, "source": None, "row_type": "EVENT", "phase": "OLD", "support": query["support"],
                       "bank": {handle: fields[handle] for handle in query["support"]}, "taint": "AUTHENTIC", "request": request}
    domain = [prefix.FIXED_FILES["formation/records/formation.json"], "EVENT_ONLY", "S1", "EVENT", "replay"]
    eligible = sorted(slots)
    selected, counts = prepare._select_replay(slots, eligible, [], 6, domain)
    for index, source in enumerate(selected, 14):
        name = f"s{index:02}"
        slots[name] = {**copy.deepcopy(slots[source]), "id": name, "source": source}
    conflicts = {name: {other for other, candidate in slots.items() if other != name and
                       set(slot["support"]).intersection(candidate["support"])} for name, slot in slots.items()}
    order = sorted(slots, key=lambda name: (-len(conflicts[name]), writer.digest([0, name]), name))
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
    require(place(0), "no disjoint partition; no resampling")
    corpus = {"id": "disposable/0/EVENT_ONLY_AUTH", "root": "disposable/0", "arm": "S1_AUTH", "slots": list(slots.values())}
    epoch = [[[name, view] for name in group] for view in range(8) for group in groups]
    epochs = [copy.deepcopy(epoch) for _ in range(5)]
    writer._schedule(corpus, epochs)
    return seal({"schema": SCHEMA + "/schedule", "import_sha256": imported["sha256"], "batch_seed": 0,
                 "corpus": corpus, "epochs": epochs, "replay": {"domain": domain, "eligible": eligible,
                 "selected": selected, "support_counts": counts}, "recipe": {"learning_rate": 3e-5,
                 "updates": 200, "rank": 8, "alpha": 16, "dropout": 0.05, "objective": writer.OBJECTIVE, "layout": writer.LAYOUT}})


def build_schedule(imported, import_sha256):
    prefix.validate_import(imported, import_sha256)
    return _schedule(imported)


def read_roster(imported):
    return [{"id": f"event-only/W{view}/{index:02}", "request": request, "view": view, "seed": 0, "output_tokens": 2048}
            for view in ENDPOINT["views"] for index, request in enumerate(sorted(imported["queries"]))]


def build_fit(imported, import_sha256, schedule, schedule_sha256, binding):
    writer._record(binding, BINDING_FIELDS, "EVENT-only binding")
    fit = seal({"schema": SCHEMA, "imported": imported, "import_sha256": import_sha256, "schedule": schedule,
                "schedule_sha256": schedule_sha256, "binding": {**binding, "learning_rate": 3e-5},
                "endpoint": ENDPOINT, "read_roster": read_roster(imported), "full_contract_released": False})
    validate_fit(fit)
    return fit


def validate_fit(fit):
    writer._record(fit, {"schema", "imported", "import_sha256", "schedule", "schedule_sha256", "binding",
                        "endpoint", "read_roster", "full_contract_released", "sha256"}, "EVENT-only fit")
    unseal(fit, fit["sha256"])
    same([fit["schema"], fit["full_contract_released"]], [SCHEMA, False], "separate prefix scope")
    imported = fit["imported"]
    prefix.validate_import(imported, fit["import_sha256"])
    unseal(fit["schedule"], fit["schedule_sha256"])
    same(fit["schedule"], _schedule(imported), "fixed14+6 schedule differs")
    same([fit["endpoint"], fit["read_roster"]], [ENDPOINT, read_roster(imported)], "W0/W8 endpoint changed")
    binding = fit["binding"]
    writer._record(binding, BINDING_FIELDS | {"learning_rate"}, "EVENT-only recipe binding")
    same(binding["learning_rate"], 3e-5, "LOW only")
    writer._hash(binding["authority_sha256"])
    original = prefix._json(imported["evidence"]["files"]["manifest.json"])["binding"]
    for key in ("base_state_sha256", "init_seed", "dropout_seed", "environment", "tokenizer_receipt"):
        same(binding[key], original[key], "original fresh-base/seed/tokenizer binding: " + key)
    same(binding["sources"], source_snapshot(), "loaded EVENT-only source drift")
    corpus = fit["schedule"]["corpus"]
    writer._lineage({}, corpus, imported["rows"], imported["generations"], [])
    same(imported["queries"], core.materialize_queries(imported["rows"]), "actual EVENT-only materializer")
    for slot in corpus["slots"]:
        query = imported["queries"][slot["request"]]
        same(query["support"], slot["support"], "query support binding")
        core.read_query(imported["queries"], slot["request"])
    writer._schedule(corpus, fit["schedule"]["epochs"])
    return {"schema": SCHEMA + "/validation", "fit_sha256": fit["sha256"], "rows": 8, "queries": 14,
            "slots": 20, "views": 8, "epochs": 5, "updates": 200, "presentations": 800,
            "original_status": "FORMATION_FAILED", "tokenizer_check_required_before_fit": True,
            "native_custody_verified": False, "full_contract_released": False}


def encode_fit(fit, tokenizer):
    validate_fit(fit)
    prefix.verify_tokenizer(fit["imported"], tokenizer)
    schedule = fit["schedule"]
    return writer._encode_corpus(fit["sha256"], schedule["corpus"], schedule["epochs"],
                                 fit["imported"]["queries"], core.registries()["render_registry"],
                                 fit["binding"]["environment"]["chat_template_sha256"], tokenizer)


def train_fit(fit, tokenizer, base_factory, out):
    """Single explicit LOW200 numerical call; no load unless validation passes."""
    out = Path(out)
    require(not out.exists() and not out.is_symlink(), "fresh EVENT-only fit directory required")
    validation = validate_fit(fit)
    encoded = encode_fit(fit, tokenizer)
    return writer._train_encoded(fit, encoded, base_factory, out, fit["binding"]["environment"], validation,
                                 report_name="event_only_scope_report.json")
