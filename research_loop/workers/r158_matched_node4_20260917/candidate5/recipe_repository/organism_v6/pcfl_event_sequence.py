"""Authenticated split-EVENT material for a separate V3 diagnostic; no execution."""

from collections import Counter
from collections.abc import Mapping
import copy
from dataclasses import asdict
import hashlib
from pathlib import Path

from gpu import astra_pcfl_event_prefix_import as prefix
from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import train_adapter_v3 as trainer


SCHEMA = "pcfl.event_sequence.material.v1"
PHASES = {
    "S_A": (None, 40),
    "SEQ_REPLAY": ("S_A", 80),
    "SEQ_NEW_ONLY": ("S_A", 80),
    "FRESH_MIX": (None, 80),
    "ALL_AVAILABLE_1": (None, 40),
    "ALL_AVAILABLE_2": ("ALL_AVAILABLE_1", 80),
}
READ_STATES = {
    "NO_WRITE": None, "S_A": "S_A", "SEQ_REPLAY": "SEQ_REPLAY",
    "SEQ_NEW_ONLY": "SEQ_NEW_ONLY", "FRESH_MIX": "FRESH_MIX",
    "ALL_AVAILABLE": "ALL_AVAILABLE_2",
}
LIMITS = (
    "Exposed-DEV one-bank sequential V3 weight writes, fresh optimizer per write; "
    "not the unchanged SEQ179 PCFL numerical recipe. Chronological A/B are both "
    "original OLD EVENTs. External format assistance and compiler-selected replay; "
    "no autonomous discovery or new factual material. W8 is a previously exposed "
    "development wrapper, not unseen facts/addresses or confirmation. NEW_ONLY "
    "matches phase2 slots/updates, not new-fact dose; FRESH_MIX matches phase2 "
    "material, not lifetime compute; NO_WRITE is not compute-matched. No parenting, "
    "general G3, H1/H2, C11, generalization, selectivity or full-assay qualification."
)
require, same, seal = prefix.require, prefix.same, prefix.seal


def source_snapshot():
    paths = [Path(module.__file__).resolve() for module in (prefix, core, trainer, prefix.native)]
    paths += [Path(__file__).resolve(), Path(__file__).with_name("pcfl_vertical_train.py").resolve()]
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def training_config(phase, model_path, *, device="cuda"):
    """Runner constructs a fresh base; init_adapter is a separate run_training arg."""
    require(phase in PHASES, "unknown fixed phase")
    require(isinstance(model_path, (str, Path)) and Path(model_path).is_absolute(), "absolute local base path")
    require(type(device) is str and bool(device), "explicit device required")
    return trainer.TrainConfig(
        model=str(model_path), device=device, rank=8, alpha=16, dropout=.05,
        lr=3e-5, seed=0, epochs=1, max_steps=PHASES[phase][1], max_len=512,
        batch_size=4, grad_accum=1, pack=False, shuffle_groups=False,
        optimizer="adamw", layers="all", svd_init=False, freeze_a=False,
        chat_template=False, add_eos=True, overflow="truncate",
        grad_checkpoint=False, dtype="bf16", log_every=0, note=SCHEMA,
    )


def _schedules():
    def expand(groups, repeats):
        return [[[index, view] for index in group]
                for repetition in range(repeats) for view in range(8) for group in groups]
    mixed = [(0, 1, 4, 5), (2, 3, 6, 7)]
    replay = expand(mixed, 5)
    available = expand([*mixed, (0, 1, 2, 3)], 5)
    return {"S_A": expand([(0, 1, 2, 3)], 5), "SEQ_REPLAY": replay,
            "SEQ_NEW_ONLY": expand([(4, 5, 6, 7)], 10),
            "FRESH_MIX": copy.deepcopy(replay),
            "ALL_AVAILABLE_1": available[:40], "ALL_AVAILABLE_2": available[40:]}


def _spec(imported):
    records = []
    require(len(imported["rows"]) == len(imported["generations"]) == 8, "eight chronological EVENTs required")
    for index, (row, generation) in enumerate(zip(imported["rows"], imported["generations"])):
        request = "READ EVENT " + row["fields"]["event"]
        query = imported["queries"][request]
        same([query["support"], query["target"], generation["raw"]],
             [[row["fields"]["event"]], row["raw"], row["raw"]], "singleton child byte lineage")
        records.append({"index": index, "bank": "A" if index < 4 else "B",
                        "call_index": prefix.EVENT_INDICES[index], "request": request,
                        "row": copy.deepcopy(row), "generation": copy.deepcopy(generation),
                        "target": query["target"], "source_sha256": query["source_sha256"]})
    phases = {}
    for name, batches in _schedules().items():
        parent, updates = PHASES[name]
        require(len(batches) == updates and all(len(batch) == len({pair[0] for pair in batch}) == 4 for batch in batches), "four distinct sources per batch")
        counts = Counter(tuple(pair) for batch in batches for pair in batch)
        phases[name] = {"parent_phase": parent, "updates": updates,
                        "presentations": 4 * updates, "batches": batches,
                        "exposures": [{"record": index, "view": view, "count": count}
                                      for (index, view), count in sorted(counts.items())]}
    roster = [{"id": f"event-sequence/W{view}/{index:02}", "request": record["request"],
               "view": view, "seed": 0, "output_tokens": 2048}
              for view in (0, 8) for index, record in enumerate(records)]
    return seal({"schema": SCHEMA, "status": "MATERIAL_SPEC_ONLY", "label": "EXPOSED_DEV_FORMAT_ASSISTED_V3_SEQUENCE",
                 "import_sha256": imported["sha256"], "sources": source_snapshot(), "limits": LIMITS,
                 "records": records, "phases": phases, "read_states": copy.deepcopy(READ_STATES),
                 "roster": roster, "roster_sha256": prefix.digest(roster),
                 "historical": {key: imported[key] for key in
                                ("original_status", "original_returncode", "original_calls", "format_scaffold")},
                 "budget": {"fits": 6, "updates": 400, "presentations": 1600,
                            "readout_states": 6, "calls_per_state": 16, "readout_calls": 96, "new_formation_calls": 0},
                 "measurement": {"primary_view": 8, "diagnostic_view": 0, "addresses_per_bank": 4,
                                 "strict_stop": True, "pass_threshold": None, "zero_pre_correct_retention": "UNDEFINED",
                                 "report": ["pre_correct", "post_correct", "kept_1_to_1", "lost_1_to_0", "gained_0_to_1"]},
                 "full_contract_released": False, "automatic_promotion": False})


def build_spec(imported, import_sha256):
    """Validate original immutable import, then return outcome-independent schedules."""
    prefix.validate_import(imported, import_sha256)
    return _spec(imported)


def validate_spec(spec, imported, import_sha256):
    prefix.unseal(spec, spec["sha256"])
    same(spec, build_spec(imported, import_sha256), "fixed sequence spec differs")
    return {"spec_sha256": spec["sha256"], "status": "SPEC_VALIDATED_NOT_EXECUTED", "full_contract_released": False}


def export_material(imported, import_sha256, tokenizer):
    """Return normalized V3 corpora and encoding audits; never load or train a model."""
    spec = build_spec(imported, import_sha256)
    token_receipt = prefix.verify_tokenizer(imported, tokenizer)
    require(type(tokenizer.eos_token_id) is int and tokenizer.eos_token_id >= 0, "EOS token required")
    surfaces = {}
    for record in spec["records"]:
        for view in range(8):
            messages = [{"role": "system", "content": core.MEMORY_SYSTEM},
                        {"role": "user", "content": core.WRAPPERS[view].replace("{REQUEST}", record["request"])}]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            require(type(prompt) is str and bool(prompt), "nonempty rendered context")
            prompt_ids = prefix.native.token_ids(tokenizer.encode(prompt, add_special_tokens=False))
            templated = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            if isinstance(templated, Mapping):
                templated = templated.get("input_ids")
            same(prefix.native.token_ids(templated), prompt_ids, "template/encode mismatch")
            target_ids = prefix.native.token_ids(tokenizer.encode(record["target"], add_special_tokens=False))
            require(prompt_ids and target_ids, "nonempty context/target tokens")
            same(tokenizer.decode(target_ids, skip_special_tokens=False), record["target"], "exact target token roundtrip")
            require(len(prompt_ids) + len(target_ids) + 1 <= 512, "zero truncation required")
            surfaces[record["index"], view] = (prompt, prompt_ids, target_ids)
    exports = {}
    for name, phase in spec["phases"].items():
        items, encoded_items = [], []
        for batch_index, batch in enumerate(phase["batches"]):
            for order, (index, view) in enumerate(batch):
                record = spec["records"][index]
                prompt, prompt_ids, target_ids = surfaces[index, view]
                item = trainer.normalize_items([{
                    "spans": [[prompt, False, "context"], [record["target"], True, "EVENT"]],
                    "group": f"batch/{batch_index:04}", "order": order, "view": f"W{view}", "category": "EVENT",
                    "meta": {"record": index, "bank": record["bank"], "call_index": record["call_index"],
                             "request": record["request"], "generation_sha256": record["generation"]["sha256"],
                             "capture_sha256": record["generation"]["capture_sha256"], "source_sha256": record["source_sha256"]},
                }])[0]
                encoded = trainer.encode_item(item, tokenizer, 512, chat_template=False, add_eos=True, item_index=len(items))
                require(encoded is not None and not encoded.context_dropped and not encoded.target_dropped, "zero truncation required")
                same(encoded.ids, prompt_ids + target_ids + [tokenizer.eos_token_id], "full token boundary")
                same(encoded.labels, [-100] * len(prompt_ids) + target_ids + [tokenizer.eos_token_id], "context mask and target/EOS")
                items.append(item)
                encoded_items.append(encoded)
        ordered = trainer.epoch_order(trainer.pack_by_group(encoded_items, 512, pack=False), 0, 0, shuffle_groups=False)
        same([entry[0].item_index for entry in ordered], list(range(len(items))), "V3 batch order differs")
        exports[name] = seal({"phase": name, "parent_phase": phase["parent_phase"],
                              "updates": phase["updates"], "items": items, "items_sha256": prefix.digest(items),
                              "encoding_sha256": prefix.digest([asdict(item) for item in encoded_items]),
                              "presentations": len(items), "supervised_tokens": sum(item.n_target for item in encoded_items),
                              "input_tokens": sum(len(item.ids) for item in encoded_items),
                              "context_dropped": 0, "target_dropped": 0})
    return seal({"schema": SCHEMA + "/export", "status": "TOKENIZED_MATERIAL_NOT_EXECUTED",
                 "spec": spec, "tokenizer_receipt": token_receipt, "phases": exports,
                 "full_contract_released": False, "automatic_promotion": False})
