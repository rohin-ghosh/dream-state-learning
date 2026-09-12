"""Fixed-prefix frozen-OFF forward-KL diagnostic; not OEL/SDFT reproduction.

prepare is CPU-only. cache and train require explicit --execute and Main's
resource decision. Whole-text CE remains coefficient 1; G9/G11 are untouched.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import random
import re
import string
import time

from organism_v6 import memory_dose as native


SOURCE_SHA = "ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3"
CORPUS = "corpora/bank0/F_r16k16/across/sleep4/corpus.json"
INPUT_HASHES = {
    CORPUS: "f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d",
    "manifest.json": "b2d82e650c51f9c453f7978a56840eade533f253e732b6c897c43b690ccaf35f",
    "distractor.json": "4ad56576f6d0a9ae211207ab06daef767ccca6a3968c7d9542505406137a9fdc",
    "banks/bank0.json": "87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31",
    "banks/bank1.json": "b63d649fa16a2b921c694e88a379fa01b174d5c101111c0ddaaf26e9c098e362",
    "banks/bank2.json": "a4ca0376a7cba887d2f571083ec5f4b0aa36b8fa366c1060fb01579a803a76e4",
}
N_ANCHORS = 48
N_STEPS = 9693
ID_PATTERN = re.compile(r"(?<![A-Za-z0-9])([A-Z][0-9][A-Z][0-9])(?![A-Za-z0-9])")
NAMESPACE = "anchor-20260912|"
RECIPE = "A1 whole-text CE + fixed-prefix OFF forward KL v1"
BOUNDARY = dict(synthetic=True, clean_lineage_eligible=False, exploratory=True,
                objective_scope="G9 acquisition/locality diagnostic; G11 unchanged and measured",
                reproduction="NOT OEL/SDFT; no trajectories, demonstrations, EMA or full finetuning",
                readiness="NOT_ASSERTED; low anchor KL or improved locality is not readiness",
                g11_note="Frozen OFF abstention is low; preserving it does not teach G11 abstention.",
                locality_note="Full-vocabulary KL need not preserve conditional colour probabilities.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load(path):
    def reject(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(Path(path).read_text(), parse_constant=reject)


def write_new(path, value):
    text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with Path(path).open("x") as stream:
        stream.write(text)


def coefficient(value):
    value = float(value)
    require(math.isfinite(value) and 0 <= value <= 1, "coefficient must be finite in [0,1]; no default is selected")
    return value


def check_native():
    require(digest(native.__file__) == SOURCE_SHA, "native memory_dose source changed")


def read_source(root):
    check_native()
    root = Path(root)
    contents = {}
    for name, expected in INPUT_HASHES.items():
        require(digest(root / name) == expected, "original input hash mismatch: " + name)
        contents[name] = load(root / name)
    corpus = contents[CORPUS]
    require(len(corpus["corpus"]) == 12924, "original item count")
    require(all(item["mask_context"] is False and item["chat"] is False and item["weight"] == 1
                for item in corpus["corpus"]), "original whole-text CE corpus required")
    return contents


def rank_id(owner):
    return hashlib.sha256((NAMESPACE + owner).encode()).hexdigest()


def neighbours(owner):
    for position, alphabet in enumerate((string.ascii_uppercase, string.digits,
                                         string.ascii_uppercase, string.digits)):
        for character in alphabet:
            if character != owner[position]:
                yield owner[:position] + character + owner[position + 1:]


def make_anchors(contents):
    """Native cue construction is used only for an identity/prompt denylist."""
    reserved, prompts, cue_owners = set(), set(), set()
    for content in contents.values():
        reserved.update(ID_PATTERN.findall(json.dumps(content)))
    banks = [contents[f"banks/bank{index}.json"] for index in range(3)]
    for bank in banks:
        for cue in native.build_cues(bank, contents["distractor.json"]["text"], adjacent_subset=4):
            prompts.add(cue["prompt"])
            for field in ("owner", "cue_id_used"):
                if cue.get(field):
                    cue_owners.add(cue[field])
    reserved.update(cue_owners)
    require(all(ID_PATTERN.fullmatch(owner) for owner in reserved), "unexpected reserved owner syntax")
    parents = sorted((owner["id"] for owner in banks[0]["owners"] if owner["dose"] > 0), key=rank_id)[:16]
    require(len(parents) == 16, "insufficient exposed training parents")
    used, near = set(reserved), []
    for parent in parents:
        choices = sorted(set(neighbours(parent)) - used, key=rank_id)
        require(bool(choices), "no disjoint near ID")
        near.append(choices[0])
        used.add(choices[0])
    forbidden_far = used | {candidate for owner in reserved for candidate in neighbours(owner)}
    candidates = ("".join(parts) for parts in itertools.product(
        string.ascii_uppercase, string.digits, string.ascii_uppercase, string.digits))
    far = sorted((owner for owner in candidates if owner not in forbidden_far), key=rank_id)[:32]
    require(len(far) == 32, "insufficient disjoint far IDs")
    groups = (("near_car", near, native.FRAME_PREFIX), ("far_car", far[:16], native.FRAME_PREFIX),
              ("far_bicycle", far[16:], native.FRAME_BICYCLE_PREFIX))
    rows = [dict(family=family, owner=owners[index], prefix=template.format(owner=owners[index]))
            for index in range(16) for family, owners, template in groups]
    require(len({row["owner"] for row in rows}) == N_ANCHORS, "duplicate anchors")
    require(all(row["owner"] not in reserved and row["prefix"] not in prompts
                and not row["prefix"].endswith(" ") for row in rows), "anchor/evaluation overlap")
    return dict(**BOUNDARY, schema="memory-preservation-anchors-v1", namespace=NAMESPACE,
                source_inputs=INPUT_HASHES, native_source_sha256=SOURCE_SHA,
                denylist_count=len(reserved), denylist_sha256=object_hash(sorted(reserved)),
                native_cue_owner_count=len(cue_owners), native_cue_owner_sha256=object_hash(sorted(cue_owners)),
                split="fresh IDs; full source and all three banks' native cue ownerrefs excluded; no eval score files read",
                schedule="rows[zero_based_optimizer_step % 48]; three interleaved families",
                rows=rows, rows_sha256=object_hash(rows))


def validate_anchors(path, contents):
    anchors = load(path)
    require(anchors == make_anchors(contents), "anchor content/split/provenance mismatch")
    return anchors


def model_inventory(root):
    root = Path(root).resolve(strict=True)
    names = {path.name for path in root.iterdir() if path.is_file()
             and (path.suffix in (".json", ".safetensors", ".bin", ".model", ".txt"))}
    require({"config.json", "tokenizer.json", "tokenizer_config.json"} <= names, "local model/tokenizer files missing")
    require(not any(name.startswith("adapter_") for name in names), "adapter files forbidden in frozen base")
    config = load(root / "config.json")
    require(config.get("model_type") == "qwen2" and config.get("num_hidden_layers") == 28
            and config.get("hidden_size") == 3584 and not config.get("auto_map"),
            "expected local Qwen2.5-7B configuration; not origin authentication")
    require(any(name.endswith((".safetensors", ".bin")) for name in names), "local base weights missing")
    return {name: digest(root / name) for name in sorted(names)}


def assert_lora_only(model):
    trainable = []
    for name, parameter in model.named_parameters():
        is_lora = ".lora_A." in name or ".lora_B." in name
        require(parameter.requires_grad == is_lora, "base frozen / LoRA-only mismatch: " + name)
        if parameter.requires_grad:
            trainable.append(name)
    require(trainable and any(".lora_A." in name for name in trainable)
            and any(".lora_B." in name for name in trainable), "trainable LoRA A/B required")
    return trainable


@contextmanager
def preservation_mode(model):
    import torch
    modes = [(module, module.training) for module in model.modules()]
    devices = sorted({parameter.device.index for parameter in model.parameters() if parameter.device.type == "cuda"})
    with torch.random.fork_rng(devices=devices):
        try:
            model.eval()
            with torch.enable_grad():
                yield
        finally:
            for module, training in modes:
                module.training = training


def full_forward_kl(student_logits, off_logits):
    import torch
    require(not off_logits.requires_grad, "teacher must be detached")
    require(student_logits.shape == off_logits.shape and student_logits.ndim == 1, "full-vocabulary KL shape")
    require(bool(torch.isfinite(off_logits).all()) and bool(torch.isfinite(student_logits).all()), "nonfinite logits")
    log_teacher = torch.log_softmax(off_logits.float(), dim=-1)
    log_student = torch.log_softmax(student_logits.float(), dim=-1)
    return (log_teacher.exp() * (log_teacher - log_student)).sum()


def batch_tensors(chunk, pad, device):
    import torch
    length = max(len(ids) for ids, _, _ in chunk)
    return (
        torch.tensor([ids + [pad] * (length - len(ids)) for ids, _, _ in chunk], device=device),
        torch.tensor([labels + [-100] * (length - len(labels)) for _, labels, _ in chunk], device=device),
        torch.tensor([[1] * len(ids) + [0] * (length - len(ids)) for ids, _, _ in chunk], device=device),
        torch.tensor([weight for _, _, weight in chunk], device=device, dtype=torch.float32))


def memory_loss(model, batch):
    import torch
    inputs, labels, attention, weights = batch
    logits = model(input_ids=inputs, attention_mask=attention, use_cache=False).logits
    shifted_logits, shifted_labels = logits[:, :-1, :].float(), labels[:, 1:]
    nll = torch.nn.functional.cross_entropy(
        shifted_logits.reshape(-1, shifted_logits.size(-1)), shifted_labels.reshape(-1),
        reduction="none", ignore_index=-100).view(shifted_labels.shape)
    valid = (shifted_labels != -100).float()
    loss, denominator = native.weighted_token_nll_torch(nll, valid, weights)
    require(denominator.item() > 0 and bool(torch.isfinite(loss)), "nonfinite/empty CE; no skipped updates allowed")
    return loss, int(attention.sum()), int(valid.sum())


def optimizer_step(model, optimizer, batch, strength, anchor_ids=None, off_logits=None):
    import torch
    strength = coefficient(strength)
    require(model.training, "memory CE must use training mode")
    started = time.perf_counter()
    loss, tokens, supervised = memory_loss(model, batch)
    loss.backward()
    ce = float(loss.detach())
    del loss
    kl_value = None
    if strength > 0:
        require(anchor_ids is not None and off_logits is not None, "positive coefficient needs cached anchor")
        with preservation_mode(model):
            logits = model(input_ids=anchor_ids[None], attention_mask=torch.ones_like(anchor_ids)[None],
                           use_cache=False).logits[0, -1, :]
            kl = full_forward_kl(logits, off_logits)
            require(bool(torch.isfinite(kl)), "nonfinite KL")
            (strength * kl).backward()
            kl_value = float(kl.detach())
        del logits, kl
    optimizer.step()
    optimizer.zero_grad()
    seconds = time.perf_counter() - started
    require(math.isfinite(seconds), "nonfinite step time")
    return dict(ce=ce, kl=kl_value, objective=ce + strength * (kl_value or 0.0),
                tokens=tokens, supervised_tokens=supervised, seconds=seconds)


def anchor_tokens(tokenizer, anchors):
    rows = [tokenizer(row["prefix"], add_special_tokens=False).input_ids for row in anchors["rows"]]
    require(len(rows) == N_ANCHORS and all(1 <= len(row) <= native.TRAIN_MAX_LEN for row in rows),
            "anchor token count; never truncate")
    return rows


def last_logits(model, rows, pad, device):
    import torch
    length = max(map(len, rows))
    inputs = torch.tensor([row + [pad] * (length - len(row)) for row in rows], device=device)
    attention = torch.tensor([[1] * len(row) + [0] * (length - len(row)) for row in rows], device=device)
    logits = model(input_ids=inputs, attention_mask=attention, use_cache=False).logits
    positions = torch.tensor([len(row) - 1 for row in rows], device=device)
    return logits[torch.arange(len(rows), device=device), positions, :].float().detach()


def verify_cache(cache_dir, anchors_path, rows, inventory, vocab_size):
    import torch
    cache_dir = Path(cache_dir)
    metadata = load(cache_dir / "cache.json")
    require(metadata["anchors_sha256"] == digest(anchors_path) and metadata["input_ids"] == rows,
            "cache anchor/tokenization mismatch")
    require(metadata["model_files"] == inventory and metadata["native_source_sha256"] == SOURCE_SHA,
            "cache source/base mismatch")
    require(metadata["dtype"] == "torch.float32" and metadata["temperature"] == 1.0
            and metadata["adapter"] is None and metadata["position"] == "last input token", "cache recipe")
    require(digest(cache_dir / "off_logits.pt") == metadata["logits_sha256"], "cache hash mismatch")
    logits = torch.load(cache_dir / "off_logits.pt", map_location="cpu", weights_only=True)
    require(isinstance(logits, torch.Tensor) and logits.dtype == torch.float32
            and tuple(logits.shape) == (N_ANCHORS, vocab_size) and not logits.requires_grad
            and bool(torch.isfinite(logits).all()), "cache shape/dtype/finite/detachment")
    require(torch.allclose(logits.log_softmax(-1).exp().sum(-1), torch.ones(N_ANCHORS), atol=1e-6),
            "cache normalized distribution")
    return logits, metadata


def new_directory(path, protected):
    path = Path(path).absolute()
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), "output symlink")
    require(not path.exists() and path.parent.is_dir(), "output must be new with existing parent")
    require(all(not path.is_relative_to(Path(root).resolve()) and not Path(root).resolve().is_relative_to(path)
                for root in protected), "output overlaps input")
    path.mkdir()
    return path


def cache_off(source_root, anchors_path, model_path, output):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    contents = read_source(source_root)
    anchors = validate_anchors(anchors_path, contents)
    anchors_hash, implementation_hash = digest(anchors_path), digest(__file__)
    inventory = model_inventory(model_path)
    out = new_directory(output, [source_root, model_path, anchors_path])
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    rows = anchor_tokens(tokenizer, anchors)
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16,
                                               device_map="cuda", local_files_only=True)
    model.requires_grad_(False)
    model.eval()
    require(not any(parameter.requires_grad for parameter in model.parameters()), "OFF base not frozen")
    with torch.no_grad():
        logits = torch.cat([last_logits(model, rows[start:start + 4], tokenizer.pad_token_id, "cuda").cpu()
                            for start in range(0, N_ANCHORS, 4)])
    require(bool(torch.isfinite(logits).all()), "nonfinite OFF cache")
    require(model_inventory(model_path) == inventory, "base files changed during cache")
    read_source(source_root)
    require(digest(anchors_path) == anchors_hash and digest(__file__) == implementation_hash, "cache inputs/source changed")
    with (out / "off_logits.pt").open("xb") as stream:
        torch.save(logits, stream)
    elapsed = time.perf_counter() - started
    require(math.isfinite(elapsed), "nonfinite cache time")
    metadata = dict(**BOUNDARY, anchors_sha256=digest(anchors_path), input_ids=rows,
                    model_path=str(Path(model_path).resolve()), model_files=inventory,
                    model_authentication="local file hashes only; not official or historical weight authentication",
                    native_source_sha256=SOURCE_SHA, implementation_sha256=digest(__file__),
                    logits_sha256=digest(out / "off_logits.pt"), shape=list(logits.shape),
                    dtype=str(logits.dtype), model_dtype=str(next(model.parameters()).dtype),
                    torch_version=torch.__version__, temperature=1.0, adapter=None,
                    position="last input token", seconds=elapsed)
    write_new(out / "cache.json", metadata)
    return metadata


def tensor_hash(tensors):
    import torch
    buffer = io.BytesIO()
    torch.save({name: tensor.detach().cpu() for name, tensor in tensors}, buffer)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def encode_corpus(tokenizer, corpus):
    encoded = [native.encode_item(tokenizer, item, max_len=native.TRAIN_MAX_LEN) for item in corpus["corpus"]]
    require(sum(item["n_straddle"] for item in encoded) == 0 and not any(item["truncated"] for item in encoded),
            "original CE token boundaries/truncation changed")
    require(sum(len(item["input_ids"]) for item in encoded) == 249995
            and sum(sum(label != -100 for label in item["labels"][1:]) for item in encoded) == 237071,
            "original CE token accounting mismatch")
    return [(item["input_ids"], item["labels"], item["weight"]) for item in encoded]


def train(source_root, anchors_path, cache_dir, model_path, output, strength):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    strength = coefficient(strength)
    require(strength == 0 or cache_dir is not None, "positive coefficient requires --cache")
    require(strength != 0 or cache_dir is None, "lambda0 skips cache/preservation; omit --cache")
    contents = read_source(source_root)
    corpus = contents[CORPUS]
    anchors = validate_anchors(anchors_path, contents)
    anchors_hash, implementation_hash = digest(anchors_path), digest(__file__)
    inventory = model_inventory(model_path)
    out = new_directory(output, [source_root, model_path, anchors_path, *([cache_dir] if cache_dir else [])])
    write_new(out / "setup.json", dict(**BOUNDARY, recipe=RECIPE, coefficient=strength,
              source_inputs=INPUT_HASHES, native_source_sha256=SOURCE_SHA,
              implementation_sha256=digest(__file__), anchors_sha256=digest(anchors_path),
              model_files=inventory, model_path=str(Path(model_path).resolve()),
              seed=2, rank=8, lr=1e-4, epochs=3, batch_size=4, expected_steps=N_STEPS,
              preservation_forward="eval mode, gradients enabled, RNG restored; CE backward then KL backward then one AdamW step"))
    random.seed(2)
    torch.manual_seed(2)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    chunks = encode_corpus(tokenizer, corpus)
    base = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16,
                                              device_map="cuda", local_files_only=True)
    configuration = LoraConfig(r=native.LORA_RANK, lora_alpha=native.LORA_ALPHA_MULT * native.LORA_RANK,
                               lora_dropout=native.LORA_DROPOUT, bias="none", target_modules=list(native.LORA_TARGETS))
    model = get_peft_model(base, configuration)
    trainable = assert_lora_only(model)
    model.train()
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=native.TRAIN_LR)
    initial_hash = tensor_hash((name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad)
    cache, cache_meta, token_rows = None, None, None
    if strength > 0:
        token_rows = anchor_tokens(tokenizer, anchors)
        cache, cache_meta = verify_cache(cache_dir, anchors_path, token_rows, inventory, model.config.vocab_size)
        cache = cache.to("cuda")
        token_rows = [torch.tensor(row, device="cuda") for row in token_rows]
    started = time.perf_counter()
    steps, tokens, supervised, kl_sum, ce_sum, anchor_token_count = 0, 0, 0, 0.0, 0.0, 0
    visits = [0] * N_ANCHORS
    with (out / "losses.jsonl").open("x") as stream:
        for epoch in range(native.TRAIN_EPOCHS):
            for offset in range(0, len(chunks), native.TRAIN_BSZ):
                anchor_index = steps % N_ANCHORS if strength > 0 else None
                batch = batch_tensors(chunks[offset:offset + native.TRAIN_BSZ], tokenizer.pad_token_id, "cuda")
                record = optimizer_step(model, optimizer, batch, strength,
                                        token_rows[anchor_index] if strength > 0 else None,
                                        cache[anchor_index] if strength > 0 else None)
                steps += 1
                tokens += record["tokens"]
                supervised += record["supervised_tokens"]
                ce_sum += record["ce"]
                kl_sum += record["kl"] or 0.0
                if strength > 0:
                    visits[anchor_index] += 1
                    anchor_token_count += len(token_rows[anchor_index])
                stream.write(json.dumps(dict(step=steps, epoch=epoch, item_offset=offset,
                                             anchor_index=anchor_index, **record), allow_nan=False) + "\n")
                if steps % 100 == 0:
                    stream.flush()
                    elapsed = time.perf_counter() - started
                    print(json.dumps(dict(step=steps, ce=record["ce"], kl=record["kl"],
                                          projected_fit_minutes=elapsed / steps * N_STEPS / 60)), flush=True)
    require((steps, tokens, supervised) == (N_STEPS, 749985, 711213), "incomplete native CE dose")
    assert_lora_only(model)
    require(model_inventory(model_path) == inventory, "base files changed during training")
    read_source(source_root)
    validate_anchors(anchors_path, contents)
    require(digest(anchors_path) == anchors_hash and digest(__file__) == implementation_hash, "fit anchors/source changed")
    elapsed = time.perf_counter() - started
    require(math.isfinite(elapsed), "nonfinite fit time")
    model.save_pretrained(str(out))
    metadata = dict(**BOUNDARY, recipe=RECIPE, native_ce_recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
        coefficient=strength, ce_coefficient=1.0, n_items=len(chunks), steps=steps, total_steps=N_STEPS,
        tokens=tokens, supervised_tokens=supervised, rank=8, alpha=16, dropout=native.LORA_DROPOUT,
        targets=native.LORA_TARGETS, epochs=3, lr=1e-4, bsz=4, max_len=512, seed=2,
        corpus_sha=corpus["sha"], items_sha=corpus["items_sha"], ordering=corpus["ordering"],
        writer=corpus["writer"], representation=corpus["representation"], shuffled=corpus["shuffled"],
        model="Qwen/Qwen2.5-7B-Instruct", model_path=str(Path(model_path).resolve()),
        model_authentication="local file hashes only; not official or historical weight authentication",
        tokenization="joint context+target (encode_item)", boundary_straddles=0, truncated_items=0,
        measure_only=False, throughput=dict(grad_checkpoint=False, sec_per_step=elapsed / steps),
        final_loss=record["ce"], final_kl=record["kl"], final_objective=record["objective"],
        mean_ce=ce_sum / steps, mean_kl=kl_sum / steps if strength > 0 else None,
        anchor_visits=visits, anchor_forward_count=sum(visits), anchor_input_tokens=anchor_token_count,
        anchor_distribution_positions=sum(visits), cache_used=strength > 0, cache_metadata=cache_meta,
        model_dtype=str(next(model.parameters()).dtype), trainable_dtypes=sorted({str(parameter.dtype) for parameter in model.parameters() if parameter.requires_grad}),
        kl_dtype="torch.float32" if strength > 0 else None, torch_version=torch.__version__,
        trainable_names=trainable, initial_lora_sha256=initial_hash,
        memory_order_sha256=object_hash(chunks), wall_seconds=elapsed,
        source_inputs=INPUT_HASHES, native_source_sha256=SOURCE_SHA, implementation_sha256=digest(__file__),
        anchors_sha256=digest(anchors_path), losses_sha256=digest(out / "losses.jsonl"))
    write_new(out / "train_meta.json", metadata)
    with (out / "DONE").open("x") as stream:
        stream.write("ok\n")
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--source-root", required=True)
    prepare_parser.add_argument("--output-new", required=True)
    for name in ("cache", "train"):
        command = subparsers.add_parser(name)
        command.add_argument("--source-root", required=True)
        command.add_argument("--anchors", required=True)
        command.add_argument("--model", required=True, help="pinned local original Qwen2.5-7B snapshot")
        command.add_argument("--out-new", required=True)
        command.add_argument("--execute", action="store_true")
        if name == "train":
            command.add_argument("--cache")
            command.add_argument("--coefficient", type=coefficient, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        output = Path(args.output_new).resolve()
        require(not output.is_relative_to(Path(args.source_root).resolve()), "anchor output must be outside source")
        result = make_anchors(read_source(args.source_root))
        write_new(args.output_new, result)
    else:
        if not args.execute:
            parser.error("--execute required; Main owns design, cost review and resources")
        if args.command == "cache":
            result = cache_off(args.source_root, args.anchors, args.model, args.out_new)
        else:
            result = train(args.source_root, args.anchors, args.cache, args.model, args.out_new, args.coefficient)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
