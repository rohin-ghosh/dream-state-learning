"""Prospective v2 EVENT material only; no model loading, training, or execution.

export_material(imported, import_sha256, tokenizer, learner_seed=...) reuses
v1's authenticated import and tokenizer checks. Optional v1_material must
equal a freshly rebuilt v1 export; it is not a backwards-source escape hatch.
The caller supplies the original bound local tokenizer. Synthetic tokenizers
are test fixtures, never native preparation evidence. Native preparation must
rerun this export with that tokenizer under the final source snapshot.

Runner inputs are phase.items, training_config(...), and initialization(...).
Initialization is a requirement, not a checkpoint validator: a future runner
must bind completed v2 A200 from this exact spec/seed, check its full tensor
inventory, and enforce acquisition before descendants. S_A40 is ineligible.
No execution, acquisition decision, or old-readout reuse is authorized here.
"""

from collections import Counter
import copy
from dataclasses import asdict, replace
import hashlib
from pathlib import Path

from organism_v6 import pcfl_event_sequence as v1


SCHEMA = "pcfl.event_sequence.material.v2"
PHASES = {
    "A200": (None, 200),
    "B200_NEW_DOSE": ("A200", 200),
    "B400_FIXED_WORK": ("A200", 400),
    "REPLAY400": ("A200", 400),
    "CLEAN_CUM600": (None, 600),
}
READ_STATES = {"NO_WRITE": None, **{phase: phase for phase in PHASES}}
LIMITS = (
    "PREPARATORY_ONLY, EXPOSED_DEV_FORMAT_ASSISTED_V3_SEQUENCE_V2. One authenticated "
    "DEV bank: eight EVENTs, chronological A4/B4, repeated W0-W7 views; seeds "
    "0/1/2 are learners on the same bank, not independent facts. Original SEQ171 "
    "full formation failed. External format assistance, no autonomous discovery. "
    "Terminal S_A40 remains failed and cannot initialize v2. W8 is exposed DEV, "
    "not confirmation. Not SEQ179's numerical recipe or per-fact dose. Fresh "
    "optimizer per write; warm replay differs from clean cumulative by the "
    "checkpoint/reload and optimizer/dropout reset. B200 matches B presentations, "
    "not replay compute; B400 matches phase2 updates/presentations, not B dose or "
    "target tokens. NO_WRITE is C0, not compute-matched. No pure causal replay "
    "claim, significance, parenting, general G3/H1/H2/C11, generalization, "
    "selectivity, or full-assay qualification. No automatic execution/promotion."
)
require, same, seal = v1.require, v1.same, v1.seal
prefix, core, trainer = v1.prefix, v1.core, v1.trainer


def source_snapshot():
    return {**v1.source_snapshot(), str(Path(__file__).resolve()):
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _seed(learner_seed):
    require(type(learner_seed) is int and learner_seed in (0, 1, 2), "explicit learner_seed 0/1/2 required")


def training_config(phase, model_path, *, learner_seed, device="cuda"):
    """Construct unchanged V3 recipe fields with only v2 dose, seed and note."""
    _seed(learner_seed)
    require(phase in PHASES, "only v2 phases; S_A40 is not compatible")
    return replace(v1.training_config("S_A", model_path, device=device),
                   max_steps=PHASES[phase][1], seed=learner_seed, note=SCHEMA)


def _schedules():
    def expand(banks, repeats):
        return [[[index, view] for index in bank]
                for repetition in range(repeats) for view in range(8) for bank in banks]
    bank_a, bank_b = range(4), range(4, 8)
    acquisition = expand([bank_a], 25)
    replay = expand([bank_a, bank_b], 25)
    return {"A200": acquisition, "B200_NEW_DOSE": expand([bank_b], 25),
            "B400_FIXED_WORK": expand([bank_b], 50), "REPLAY400": replay,
            "CLEAN_CUM600": copy.deepcopy(acquisition + replay)}


def _spec(original, learner_seed):
    _seed(learner_seed)
    sources = {**original["sources"], **{
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(v1.__file__).resolve(), Path(__file__).resolve())}}
    phases = {}
    for name, batches in _schedules().items():
        parent, updates = PHASES[name]
        require(len(batches) == updates and all(len(batch) == 4 for batch in batches), "batch4 exact updates")
        counts = Counter(tuple(pair) for batch in batches for pair in batch)
        phases[name] = {"parent_phase": parent, "updates": updates, "presentations": 4 * updates,
                        "batch_group_start": 200 if parent else 0, "batches": batches,
                        "exposures": [{"record": index, "view": view, "count": count}
                                      for (index, view), count in sorted(counts.items())]}
    roster = [{**row, "id": row["id"].replace("event-sequence/", "event-sequence-v2/")}
              for row in original["roster"]]
    return seal({"schema": SCHEMA, "status": "MATERIAL_SPEC_ONLY", "label": "EXPOSED_DEV_FORMAT_ASSISTED_V3_SEQUENCE_V2",
        "learner_seed": learner_seed, "import_sha256": original["import_sha256"], "v1_spec_sha256": original["sha256"],
        "sources": sources, "limits": LIMITS, "records": copy.deepcopy(original["records"]),
        "historical": copy.deepcopy(original["historical"]), "phases": phases, "read_states": READ_STATES,
        "roster": roster, "roster_sha256": v1.prefix.digest(roster),
        "budget": {"fits": 5, "updates": 1800, "presentations": 7200, "readout_states": 6,
                   "calls_per_state": 16, "readout_calls": 96, "new_formation_calls": 0, "basis": "per learner_seed"},
        "measurement": {**original["measurement"], "acquisition_gate_W8": {"NO_WRITE": {"A": 0, "B": 0}, "A200": {"A": 4, "B": 0}},
                        "on_gate_failure": "A200_ACQUISITION_FAILED; withhold descendants, no dose rescue",
                        "after_gate": "all four remaining fits; B200 outcome is not a progression gate"},
        "full_contract_released": False, "automatic_promotion": False})


def build_spec(imported, import_sha256, *, learner_seed):
    """Authenticate original source; retain facts/history but replace all schedules."""
    return _spec(v1.build_spec(imported, import_sha256), learner_seed)


def validate_spec(spec, imported, import_sha256):
    v1.prefix.unseal(spec, spec["sha256"])
    same(spec, build_spec(imported, import_sha256, learner_seed=spec["learner_seed"]), "fixed v2 spec differs")
    return {"spec_sha256": spec["sha256"], "status": "SPEC_VALIDATED_NOT_EXECUTED"}


def initialization(spec, phase):
    """Prospective runner contract, not acceptance of a checkpoint or outcome."""
    v1.prefix.unseal(spec, spec["sha256"])
    require(spec["schema"] == SCHEMA and phase in PHASES, "only v2 initialization")
    _seed(spec["learner_seed"])
    same(spec["phases"][phase]["parent_phase"], PHASES[phase][0], "fixed v2 parent")
    parent = PHASES[phase][0]
    return {"kind": "FRESH_C0" if parent is None else "COMPLETED_V2_A200",
            "parent_phase": parent, "parent_spec_sha256": spec["sha256"] if parent else None,
            "learner_seed": spec["learner_seed"], "fresh_optimizer": True,
            "requires_acquisition_gate": phase != "A200", "sa40_parent_allowed": False}


def export_material(imported, import_sha256, tokenizer, *, learner_seed, v1_material=None):
    """Return sealed normalized items and exact encoding/token audits, not a fit.

    An optional archived v1 export is fully compared to a current authenticated
    rebuild. Omit it when re-exporting under new source pins; never mutate it.
    """
    _seed(learner_seed)
    original = v1.export_material(imported, import_sha256, tokenizer)
    if v1_material is not None:
        same(v1_material, original, "authenticated current v1 material differs")
    spec = _spec(original["spec"], learner_seed)
    surfaces = {}
    for phase in original["phases"].values():
        for item in phase["items"]:
            key = (item["meta"]["record"], int(item["view"][1:]))
            surfaces.setdefault(key, item)
    require(len(surfaces) == 64, "all eight EVENTs and W0-W7 surfaces required")
    exports = {}
    for name, phase in spec["phases"].items():
        items, encoded_items = [], []
        for batch_index, batch in enumerate(phase["batches"]):
            for order, (index, view) in enumerate(batch):
                item = copy.deepcopy(surfaces[index, view])
                item.update(group=f"batch/{phase['batch_group_start'] + batch_index:04}", order=order)
                item = v1.trainer.normalize_items([item])[0]
                same(item["spans"][1][0], spec["records"][index]["target"], "exact authentic LF target")
                encoded = v1.trainer.encode_item(item, tokenizer, 512, chat_template=False, add_eos=True, item_index=len(items))
                require(encoded is not None and not encoded.context_dropped and not encoded.target_dropped, "zero truncation/skips required")
                context_ids = tokenizer.encode(item["spans"][0][0], add_special_tokens=False)
                target_ids = tokenizer.encode(item["spans"][1][0], add_special_tokens=False)
                same(encoded.ids, context_ids + target_ids + [tokenizer.eos_token_id], "exact token boundaries")
                same(encoded.labels, [-100] * len(context_ids) + target_ids + [tokenizer.eos_token_id], "masked context; active target/EOS")
                items.append(item)
                encoded_items.append(encoded)
        ordered = v1.trainer.epoch_order(v1.trainer.pack_by_group(encoded_items, 512, pack=False), learner_seed, 0, shuffle_groups=False)
        same([entry[0].item_index for entry in ordered], list(range(len(items))), "chronological V3 order")
        exports[name] = seal({"phase": name, "parent_phase": phase["parent_phase"], "initialization": initialization(spec, name),
            "updates": phase["updates"], "presentations": len(items), "items": items, "items_sha256": v1.prefix.digest(items),
            "encoding_sha256": v1.prefix.digest([asdict(item) for item in encoded_items]),
            "supervised_tokens": sum(item.n_target for item in encoded_items), "input_tokens": sum(len(item.ids) for item in encoded_items),
            "supervised_tokens_by_bank": {bank: sum(encoded.n_target for item, encoded in zip(items, encoded_items) if item["meta"]["bank"] == bank)
                                          for bank in ("A", "B")}, "context_dropped": 0, "target_dropped": 0, "skipped_targets": 0})
    same(exports["CLEAN_CUM600"]["items"], exports["A200"]["items"] + exports["REPLAY400"]["items"], "exact cumulative item concatenation")
    return seal({"schema": SCHEMA + "/export", "status": "TOKENIZED_MATERIAL_NOT_EXECUTED", "spec": spec,
                 "v1_export_sha256": original["sha256"], "tokenizer_receipt": original["tokenizer_receipt"], "phases": exports,
                 "full_contract_released": False, "automatic_promotion": False})
