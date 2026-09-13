"""Bounded PCFL writer; consumes sealed schedules, never constructs a world.

Import/validation need no Torch. train_fit is an optional explicit caller-owned
entry point, not a launcher. Native custody, calibration and release remain
external gates. Four unpadded forwards share one pooled loss/backward/update.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re

from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_prepare as prepare
from organism_v6 import train_adapter_v3 as shared


SCHEMA = "pcfl.writer.v2.2.unpadded.v1"
OBJECTIVE = "pooled_response_token_mean"
LAYOUT = "four_unpadded_forwards_one_backward"
BINDING_FIELDS = {
    "contract_sha256", "authority_sha256", "custody_sha256", "objective",
    "layout", "learning_rate", "phase", "selection_receipt_sha256",
    "init_seed", "dropout_seed", "base_state_sha256", "writer_sha256",
    "shared_trainer_sha256",
}


class WriterError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise WriterError(message)


def byte_hash(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def canonical(value):
    return prepare.canonical(value)


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _hash(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "invalid SHA256")


def _record(value, fields, label):
    require(type(value) is dict and set(value) == set(fields), f"closed {label} fields")


def _binding(contract, binding):
    _record(binding, BINDING_FIELDS, "fit binding")
    for name in BINDING_FIELDS:
        if name.endswith("sha256"):
            _hash(binding[name])
    require(binding["contract_sha256"] == digest(contract), "contract hash drift")
    require(binding["objective"] == OBJECTIVE and binding["layout"] == LAYOUT,
            "explicit pooled objective/unpadded layout binding required")
    rate = binding["learning_rate"]
    require(type(rate) is float and math.isfinite(rate) and rate in (3e-5, 3e-4), "learning rate")
    require(binding["phase"] in ("CAL_LOW", "CAL_HIGH", "DEV"), "fit phase")
    if binding["phase"] != "DEV":
        require(rate == {"CAL_LOW": 3e-5, "CAL_HIGH": 3e-4}[binding["phase"]], "CAL rate mismatch")
        seeds = contract["bindings"]["environment"]["cal_seeds"]
        require(binding["init_seed"] == seeds["cal/init"] and
                binding["dropout_seed"] == seeds["cal/dropout"], "shared CAL RNG drift")
    for key in ("init_seed", "dropout_seed"):
        require(type(binding[key]) is int and 0 <= binding[key] < 2**63, "seed must be an integer")


def _authentic(row, generations, used):
    core.validate_row(row)
    require(row["taint"] == "CHILD_SUBMISSION", "non-child ancestor/ceiling forbidden")
    provenance = row["provenance"]
    generation_hash = provenance.get("generation_sha256")
    require(generation_hash in generations, "missing original child generation")
    generation = generations[generation_hash]
    start, end = provenance.get("byte_start"), provenance.get("byte_end")
    payload = generation["raw"].encode("utf-8")
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(payload), "child byte bounds")
    require(payload[start:end] == row["raw"].encode("utf-8"), "target not exact child span")
    require(byte_hash(row["raw"]) == row["sha256"], "child span hash")
    used.add(generation_hash)


def _lineage(contract, corpus, rows, generations, controls):
    require(type(generations) is list and type(controls) is list, "generation/control lists required")
    indexed, used = {}, set()
    for generation in generations:
        _record(generation, ("raw", "sha256", "origin", "capture_sha256"), "generation")
        require(type(generation["raw"]) is str and generation["origin"] == "CHILD_NATIVE", "child origin required")
        _hash(generation["capture_sha256"])
        require(byte_hash(generation["raw"]) == generation["sha256"], "generation hash drift")
        require(generation["sha256"] not in indexed, "duplicate generation")
        indexed[generation["sha256"]] = generation
    derived, names = {}, set()
    for control in controls:
        _record(control, ("name", "ancestors"), "control")
        name = control["name"]
        require(name in ("EVENT_TWIN", "LINK_PERMUTE") and name not in names, "unregistered/duplicate transformation")
        require(corpus["arm"] == "S1_" + name, "control/arm mismatch")
        require(type(control["ancestors"]) is list and control["ancestors"], "control ancestors required")
        names.add(name)
        for ancestor in control["ancestors"]:
            require(ancestor["root"] == corpus["root"], "foreign control ancestor")
            _authentic(ancestor, indexed, used)
        root_wire = next(root["wire"] for root in contract["bindings"]["root_registry"] if root["id"] == corpus["root"])
        transform = {"EVENT_TWIN": core.make_event_twin, "LINK_PERMUTE": core.make_link_permute}[name]
        for row in transform(control["ancestors"], core.from_data(root_wire)):
            derived[digest(row)] = row
    control_count = 0
    for row in rows:
        if row["taint"] == "CHILD_SUBMISSION":
            _authentic(row, indexed, used)
        else:
            require(row["taint"] == "CONTROL" and digest(row) in derived, "unverified control/ceiling target")
            control_count += 1
    require(bool(controls) == bool(control_count), "unused control declaration")
    require(set(indexed) == used, "unused generation payload")


def _schedule(corpus, schedule):
    slots = {slot["id"]: slot for slot in corpus["slots"]}
    require(len(slots) == len(corpus["slots"]) == 20, "twenty unique slots required")
    require(type(schedule) is list and len(schedule) == 5, "five epochs required")
    expected = Counter((slot_id, view) for slot_id in slots for view in range(8))
    for epoch in schedule:
        require(type(epoch) is list and len(epoch) == 40, "forty batches per epoch")
        seen = []
        for batch in epoch:
            require(type(batch) is list and len(batch) == 4, "four examples per update")
            occupied, slot_seen, links, new = set(), set(), 0, 0
            for pair in batch:
                require(type(pair) is list and len(pair) == 2, "batch item pair")
                slot_id, view = pair
                require(type(slot_id) is str and slot_id in slots and type(view) is int and 0 <= view < 8, "slot/view; W8 never trains")
                slot = slots[slot_id]
                require(slot_id not in slot_seen and not occupied.intersection(slot["support"]), "batch underlying-span collision")
                occupied.update(slot["support"])
                slot_seen.add(slot_id)
                links += slot["row_type"] == "LINK"
                new += slot["phase"] == "NEW"
                seen.append((slot_id, view))
            require(links <= 1 and new <= 1, "LINK/NEW batch collision")
        require(Counter(seen) == expected, "epoch coverage changed")


def build_fit(contract, corpus_id, queries, rows, generations, controls, binding):
    """Bind supplied bytes; never certify native custody or calibration success."""
    data = json.loads(canonical(dict(contract=contract, corpus_id=corpus_id,
                                    queries=queries, rows=rows, generations=generations,
                                    controls=controls, binding=binding)))
    data["schema"] = SCHEMA
    _validate(data)
    return {**data, "sha256": digest(data)}


def _validate(data):
    _record(data, ("schema", "contract", "corpus_id", "queries", "rows", "generations", "controls", "binding"), "fit")
    require(data["schema"] == SCHEMA, "writer schema")
    contract, binding = data["contract"], data["binding"]
    prepare.validate_execution_contract(contract)
    _binding(contract, binding)
    corpora = [entry for entry in contract["bindings"]["slot_registry"] if entry["id"] == data["corpus_id"]]
    require(len(corpora) == 1, "unknown/duplicate corpus")
    corpus = corpora[0]
    prepare.validate_formation_binding(contract, data["corpus_id"], data["queries"], data["rows"])
    for request in data["queries"]:
        core.read_query(data["queries"], request)
    _lineage(contract, corpus, data["rows"], data["generations"], data["controls"])
    schedules = [entry["epochs"] for entry in contract["bindings"]["batch_registry"] if entry["corpus"] == corpus["id"]]
    require(len(schedules) == 1, "missing/duplicate concrete schedule")
    _schedule(corpus, schedules[0])
    role = next(root["role"] for root in contract["bindings"]["root_registry"] if root["id"] == corpus["root"])
    require(role == ("dev" if binding["phase"] == "DEV" else "disposable"), "CAL/DEV root mismatch")
    return corpus, schedules[0]


def validate_fit(fit):
    require(type(fit) is dict and "sha256" in fit, "sealed fit required")
    data = {key: value for key, value in fit.items() if key != "sha256"}
    require(digest(data) == fit["sha256"], "fit seal drift")
    corpus, schedule = _validate(data)
    return {"fit_sha256": fit["sha256"], "corpus": corpus["id"], "updates": 200,
            "presentations": 800, "slots": 20, "views": 8, "epochs": len(schedule),
            "native_custody_verified": False, "release_authorized": False}


def encode_fit(fit, tokenizer):
    """Use shared span encoder without truncation, packing or physical padding."""
    validate_fit(fit)
    corpus, schedule = _validate({key: value for key, value in fit.items() if key != "sha256"})
    registry = fit["contract"]["bindings"]["core_registry"]["render_registry"]
    return _encode_corpus(fit["sha256"], corpus, schedule, fit["queries"], registry,
                          fit["contract"]["bindings"]["environment"]["chat_template_sha256"], tokenizer)


def _encode_corpus(fit_sha256, corpus, schedule, queries, registry,
                   chat_template_sha256, tokenizer):
    require(type(tokenizer.eos_token_id) is int and tokenizer.eos_token_id >= 0, "EOS token required")
    require(type(tokenizer.chat_template) is str and byte_hash(tokenizer.chat_template) ==
            chat_template_sha256, "chat template pin")
    items = []
    for slot in corpus["slots"]:
        query = queries[slot["request"]]
        for view in range(8):
            messages = [{"role": "system", "content": registry["systems"]["memory"]},
                        {"role": "user", "content": registry["wrappers"][f"W{view}"].format(REQUEST=slot["request"])}]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            require(type(prompt) is str and bool(prompt), "rendered prompt required")
            source = {"spans": [[prompt, False, "context"], [query["target"], True, slot["row_type"]]],
                      "group": slot["id"], "order": view, "view": f"W{view}"}
            encoded = shared.encode_item(source, tokenizer, 512, chat_template=False,
                                         add_eos=True, item_index=len(items))
            require(encoded is not None and not encoded.context_dropped and not encoded.target_dropped,
                    "zero context/target truncation required")
            prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
            target_ids = tokenizer.encode(query["target"], add_special_tokens=False)
            require(prompt_ids and target_ids and tokenizer.eos_token_id not in target_ids, "empty or premature-EOS target")
            require(encoded.ids == prompt_ids + target_ids + [tokenizer.eos_token_id] and
                    encoded.labels == [-100] * len(prompt_ids) + target_ids + [tokenizer.eos_token_id], "response/EOS mask drift")
            require(all(type(token) is int and token >= 0 for token in encoded.ids), "invalid token IDs")
            items.append({"slot": slot["id"], "view": view, "prompt_sha256": byte_hash(prompt),
                          "target_sha256": query["target_sha256"], "source_sha256": query["source_sha256"],
                          "encoded": asdict(encoded)})
    payload = {"fit_sha256": fit_sha256, "items": items, "epochs": schedule,
               "layout": LAYOUT, "padding": "none", "objective": OBJECTIVE,
               "target_tokens_per_epoch": sum(item["encoded"]["n_target"] for item in items)}
    return {**payload, "sha256": digest(payload)}


def verify_sources(fit):
    """Rehash the actually imported modules and controlling local source files."""
    validate_fit(fit)
    paths = {"writer": Path(__file__), "shared": Path(shared.__file__),
             "core": Path(core.__file__), "preparer": Path(prepare.__file__)}
    pins = {"writer": fit["binding"]["writer_sha256"], "shared": fit["binding"]["shared_trainer_sha256"],
            "core": fit["contract"]["bindings"]["implementation_pins"]["core"],
            "preparer": fit["contract"]["bindings"]["implementation_pins"]["preparer"]}
    for role, path in paths.items():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == pins[role], f"imported {role} pin drift")
    root = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
    for name, expected in fit["contract"]["bindings"]["source_pins"].items():
        require(Path(name).name == name, "source pin path")
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, "protocol source drift")
    return pins


def verify_tokenizer_files(fit, tokenizer):
    receipt = fit["contract"]["tokenizer_receipt"]
    require(receipt["kind"] == "offline_measurement", "synthetic tokenizer evidence cannot fit")
    root = Path(tokenizer.name_or_path)
    require(root.is_absolute() and root.is_dir(), "local qualified tokenizer directory required")
    files = receipt["files"]
    require(type(files) is dict and bool(files), "tokenizer file pins required")
    for name, expected in files.items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, "tokenizer pins must be relative paths")
        _hash(expected)
        require(hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected, "tokenizer file drift")
    for measurement in receipt["measurements"]:
        require(tokenizer.encode(measurement["text"], add_special_tokens=False) == measurement["token_ids"],
                "actual tokenizer differs from qualified measurement")


def _state_hash(value):
    import torch
    hashed = hashlib.sha256()

    def add(item):
        if torch.is_tensor(item):
            tensor = item.detach().cpu().contiguous()
            hashed.update(canonical([str(tensor.dtype), list(tensor.shape)]))
            hashed.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(item, dict):
            for key in sorted(item, key=lambda entry: (type(entry).__name__, str(entry))):
                hashed.update(canonical([type(key).__name__, key]))
                add(item[key])
        elif isinstance(item, (tuple, list)):
            hashed.update(canonical(["sequence", len(item)]))
            for entry in item:
                add(entry)
        else:
            hashed.update(canonical(item))

    add(value)
    return hashed.hexdigest()


def _rng_hash():
    import torch
    return {"cpu": _state_hash(torch.get_rng_state()),
            "cuda": [_state_hash(state) for state in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else []}


def _batch_objective(model, examples, device):
    import torch
    numerator = None
    denominator = 0
    for example in examples:
        ids = torch.tensor([example["ids"]], dtype=torch.long, device=device)
        labels = torch.tensor([example["labels"]], dtype=torch.long, device=device)
        logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
        terms = torch.nn.functional.cross_entropy(logits[:, :-1, :].float().reshape(-1, logits.shape[-1]),
                                                   labels[:, 1:].reshape(-1), ignore_index=-100, reduction="sum")
        numerator = terms if numerator is None else numerator + terms
        denominator += sum(label != -100 for label in example["labels"][1:])
    require(denominator > 0, "empty batch objective")
    return numerator / denominator, denominator


def _require_execution_contract(contract, *, profile_receipts=None):
    report = prepare.validate_execution_contract(contract, profile_receipts=profile_receipts)
    require(type(report) is dict and all(report.get(key) is True for key in
            ("execution_contract_valid", "static_contract_complete", "ready_for_model_calls"))
            and report.get("missing_interfaces") == [],
            "native fitting blocked: unresolved execution contract")
    return report


def train_fit(fit, tokenizer, base_factory, out, *, profile_receipts=None):
    """Optional explicit fit; factory returns fresh (base_model, environment_dict).

    Caller must independently qualify custody/LR/release. This function checks
    actual initial base tensors, imported source bytes, masks and update work.
    It offers no native loader, inference, collection, retries or selection.
    """
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    release = _require_execution_contract(fit["contract"], profile_receipts=profile_receipts)
    verify_sources(fit)
    verify_tokenizer_files(fit, tokenizer)
    encoded = encode_fit(fit, tokenizer)
    return _train_encoded(fit, encoded, base_factory, out,
                          fit["contract"]["bindings"]["environment"], release)


def _train_encoded(fit, encoded, base_factory, out, expected_environment, release,
                   *, report_name="execution_contract_report.json"):
    out.mkdir(parents=False, exist_ok=False)
    updates = 0
    try:
        (out / "fit.json").write_bytes(canonical(fit) + b"\n")
        (out / "encoding.json").write_bytes(canonical(encoded) + b"\n")
        (out / report_name).write_bytes(canonical(release) + b"\n")
        import torch
        from peft import get_peft_model

        model, environment = base_factory()
        require(canonical(environment) == canonical(expected_environment), "base factory identity mismatch")
        require(not getattr(model, "peft_config", None) and not any("lora_" in name for name, _ in model.named_parameters()), "warm/adapted base forbidden")
        require(_state_hash(model.state_dict()) == fit["binding"]["base_state_sha256"], "actual C0 tensor identity mismatch")
        require(all(parameter.dtype == torch.bfloat16 for parameter in model.parameters() if parameter.is_floating_point()), "bf16 base required")
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        torch.manual_seed(fit["binding"]["init_seed"])
        cfg = shared.TrainConfig(rank=8, alpha=16, dropout=0.05, lr=fit["binding"]["learning_rate"],
                                 epochs=5, max_len=512, batch_size=4, grad_accum=1,
                                 pack=False, shuffle_groups=False, optimizer="adamw", layers="all",
                                 svd_init=False, freeze_a=False, chat_template=False, add_eos=True,
                                 grad_checkpoint=False, dtype="bf16", max_steps=200)
        model = get_peft_model(model, shared.lora_config(cfg, model.config.num_hidden_layers))
        trainable = {name: parameter for name, parameter in model.named_parameters() if parameter.requires_grad}
        require(trainable and all("lora_" in name for name in trainable), "only fresh LoRA may train")
        optimizer = torch.optim.AdamW(list(trainable.values()), lr=cfg.lr, betas=(0.9, 0.999),
                                     eps=1e-8, weight_decay=0.01)
        require(not optimizer.state, "optimizer must be fresh")
        initial = {"lora": _state_hash(trainable), "optimizer": _state_hash(optimizer.state_dict())}
        (out / "initial.json").write_bytes(canonical(initial) + b"\n")
        torch.manual_seed(fit["binding"]["dropout_seed"])
        model.train()
        device = next(iter(model.parameters())).device
        lookup = {(item["slot"], item["view"]): item for item in encoded["items"]}
        with (out / "updates.jsonl").open("x", encoding="utf-8") as stream:
            for epoch_index, epoch in enumerate(encoded["epochs"]):
                for batch_index, batch in enumerate(epoch):
                    optimizer.zero_grad(set_to_none=True)
                    before = _rng_hash()
                    examples = [lookup[tuple(pair)]["encoded"] for pair in batch]
                    loss, target_count = _batch_objective(model, examples, device)
                    require(torch.isfinite(loss).item(), "nonfinite loss; abort, never skip")
                    loss.backward()
                    gradients = [parameter for parameter in trainable.values() if parameter.grad is not None]
                    require(gradients, "missing LoRA gradients")
                    pre = torch.nn.utils.clip_grad_norm_(list(trainable.values()), 1.0, error_if_nonfinite=True)
                    post = torch.linalg.vector_norm(torch.stack([parameter.grad.detach().float().norm() for parameter in gradients])).item()
                    require(math.isfinite(post) and post <= 1.00001, "clipping failed")
                    optimizer.step()
                    updates += 1
                    require(all(torch.isfinite(parameter).all().item() for parameter in trainable.values()), "nonfinite updated LoRA")
                    receipt = {"update": updates, "epoch": epoch_index, "batch": batch_index, "items": batch,
                               "source_sha256": [lookup[tuple(pair)]["source_sha256"] for pair in batch],
                               "loss": loss.item(), "supervised_tokens": target_count,
                               "pre_clip_norm": pre.item(), "post_clip_norm": post,
                               "rng_before": before, "rng_after": _rng_hash()}
                    stream.write(canonical(receipt).decode("utf-8") + "\n")
                    stream.flush()
        require(updates == 200, "final checkpoint requires all 200 updates")
        final = {"lora": _state_hash(trainable), "optimizer": _state_hash(optimizer.state_dict())}
        model.save_pretrained(out / "adapter", safe_serialization=True)
        files = {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(out.rglob("*")) if path.is_file()}
        receipt = {"status": "COMPLETE", "fit_sha256": fit["sha256"], "encoding_sha256": encoded["sha256"],
                   "updates": updates, "presentations": 800, "training_forwards": 800,
                   "initial": initial, "final": final, "files": files,
                   "objective": OBJECTIVE, "layout": LAYOUT, "native_custody_verified": False}
        (out / "completed.json").write_bytes(canonical(receipt) + b"\n")
        return receipt
    except BaseException as error:
        (out / "failed.json").write_bytes(canonical({"status": "FAILED", "updates": updates,
                                                     "error": type(error).__name__, "message": str(error)}) + b"\n")
        raise
