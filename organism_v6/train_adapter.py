"""Sleep training: cumulative LoRA from CLEAN BASE on the compiled corpus.
V1 RECIPE — FROZEN: this is the trainer the v6.1 long-run lives launched
with; it must not change while they run (see train_adapter_v21 for the
nursery recipe). Bare-text LM loss, lr 1e-4, 3 epochs.

  python -m organism_v6.train_adapter --corpus <corpus.json> --out <dir> \
      [--rank 16] [--epochs 3] [--lr 1e-4]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import random
import re
from pathlib import Path


def seed_training(seed, torch_module):
    if seed is not None:
        random.seed(seed)
        torch_module.manual_seed(seed)


def child_record_prefix_length(text):
    separator = "\nMy measured action record: "
    if not isinstance(text, str) or not text.startswith("Program "):
        raise ValueError("invalid child-record wrapper")
    if text.count(separator) != 1:
        raise ValueError("missing or ambiguous child-record boundary")
    boundary = text.index(separator) + len(separator)
    if not text[boundary:].strip():
        raise ValueError("empty child record")
    return boundary


def child_target_mask(offsets, prefix_length, attention_mask):
    if len(offsets) != len(attention_mask):
        raise ValueError("token offsets and attention mask disagree")
    mask = [bool(attention) and start >= prefix_length and end > start
            for (start, end), attention in zip(offsets, attention_mask)]
    if not any(mask):
        raise ValueError("no child target tokens survive tokenization")
    return mask


def child_label_counts(offsets, prefix_length, attention_mask, labels):
    if not (len(offsets) == len(attention_mask) == len(labels)):
        raise ValueError("label evidence lengths disagree")
    counts = dict(masked_prefix_tokens=0, supervised_prefix_tokens=0,
                  supervised_child_tokens=0, supervised_padding_tokens=0)
    for (start, end), attention, label in zip(offsets[1:], attention_mask[1:], labels[1:]):
        supervised = label != -100
        if not attention:
            counts["supervised_padding_tokens"] += int(supervised)
        elif start >= prefix_length and end > start:
            counts["supervised_child_tokens"] += int(supervised)
        else:
            counts["supervised_prefix_tokens"] += int(supervised)
            counts["masked_prefix_tokens"] += int(not supervised)
    if counts["supervised_prefix_tokens"] or counts["supervised_padding_tokens"]:
        raise ValueError("non-child tokens receive supervision")
    if not counts["supervised_child_tokens"] or not counts["masked_prefix_tokens"]:
        raise ValueError("missing causal-shift child/prefix evidence")
    return counts


def load_gate_binding(gate_path, expected_sha256, previous_sha256, corpus_bytes):
    for digest in (expected_sha256, previous_sha256):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid externally selected gate/lineage pin")
    gate_bytes = Path(gate_path).read_bytes()
    if hashlib.sha256(gate_bytes).hexdigest() != expected_sha256:
        raise ValueError("gate receipt hash mismatch")
    gate = json.loads(gate_bytes)
    corpus = json.loads(corpus_bytes)
    if (gate.get("schema_version") != 1 or gate.get("decision") != "ADMIT"
            or gate.get("recipe") != "preschool_records_v1"
            or corpus.get("recipe") != "preschool_records_v1"
            or gate.get("exposure_status") != "UNEXPOSED"
            or gate.get("previous_manifest_sha256") != previous_sha256
            or gate.get("corpus_sha256") != hashlib.sha256(corpus_bytes).hexdigest()):
        raise ValueError("gate receipt does not admit these training inputs")
    admissions = gate.get("admissions")
    if not isinstance(admissions, list) or len(admissions) != len(corpus["corpus"]) or not admissions:
        raise ValueError("gate admission count disagrees with corpus")
    for row in admissions:
        if not isinstance(row, dict) or any(
                not isinstance(row.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", row[key])
                for key in ("record_sha256", "source_sha256")):
            raise ValueError("invalid gate admission source hashes")
    return gate


def write_training_receipt(path, adapter_dir, gate, gate_sha256, row_counts):
    adapter = Path(adapter_dir)
    weight_names = [name for name in ("adapter_model.safetensors", "adapter_model.bin")
                    if (adapter / name).is_file()]
    if len(weight_names) != 1 or len(row_counts) != len(gate["admissions"]):
        raise ValueError("incomplete trained adapter or row evidence")
    rows = []
    for admission, counts in zip(gate["admissions"], row_counts):
        if counts is None:
            raise ValueError("missing actual label evidence")
        rows.append(dict(record_sha256=admission["record_sha256"],
                         source_sha256=admission["source_sha256"], **counts))
    metadata_bytes = (adapter / "train_meta.json").read_bytes()
    metadata = json.loads(metadata_bytes)
    if sum(row["supervised_child_tokens"] for row in rows) * metadata["epochs"] != metadata["supervised_tokens"]:
        raise ValueError("actual label counts disagree with completed training")
    receipt = dict(schema_version=1, corpus_recipe="preschool_records_v1",
                   supervision="child_only_v1", status="COMPLETED",
                   previous_manifest_sha256=gate["previous_manifest_sha256"],
                   corpus_sha256=gate["corpus_sha256"], gate_receipt_sha256=gate_sha256,
                   train_metadata_sha256=hashlib.sha256(metadata_bytes).hexdigest(),
                   adapter_files={name: hashlib.sha256((adapter / name).read_bytes()).hexdigest()
                                  for name in ["adapter_config.json", *weight_names]}, rows=rows)
    with open(path, "x") as target:
        json.dump(receipt, target, sort_keys=True, indent=2)
        target.write("\n")
    return receipt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--gate-receipt")
    ap.add_argument("--expected-gate-sha256")
    ap.add_argument("--previous-manifest-sha256")
    ap.add_argument("--trainer-receipt")
    args = ap.parse_args()

    binding_options = (args.gate_receipt, args.expected_gate_sha256,
                       args.previous_manifest_sha256, args.trainer_receipt)
    if any(binding_options) and not all(binding_options):
        ap.error("bound training requires all four gate/lineage/receipt arguments")
    with open(args.corpus, "rb") as source:
        corpus_bytes = source.read()
    bound_gate = None
    if all(binding_options):
        if Path(args.out).exists() or Path(args.trainer_receipt).exists():
            ap.error("bound training refuses preexisting output artifacts")
        if Path(args.out).resolve() in Path(args.trainer_receipt).resolve().parents:
            ap.error("trainer receipt must remain outside the adapter directory")
        if args.epochs < 1:
            ap.error("bound training requires positive epochs")
        bound_gate = load_gate_binding(args.gate_receipt, args.expected_gate_sha256,
                                       args.previous_manifest_sha256, corpus_bytes)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model

    seed_training(args.seed, torch)

    model_name = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    corpus_document = json.loads(corpus_bytes)
    child_only = corpus_document.get("recipe") == "preschool_records_v1"
    corpus = corpus_document["corpus"]
    corpus = [c if isinstance(c, str) else c.get("a", "") for c in corpus]
    prefixes = [child_record_prefix_length(text) for text in corpus] if child_only else None
    if not corpus:
        os.makedirs(args.out, exist_ok=True)
        open(os.path.join(args.out, "EMPTY_CORPUS"), "w").write("no data\n")
        print("EMPTY_CORPUS — no adapter trained")
        return

    tok = AutoTokenizer.from_pretrained(model_name)
    tok.pad_token = tok.pad_token or tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank,
                     lora_dropout=0.05, bias="none",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                     "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(base, cfg)
    model.train()
    opt = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad), lr=args.lr)

    bsz, total_tokens, steps, supervised_tokens = 4, 0, 0, 0
    row_counts = [None] * len(corpus)
    for _ in range(args.epochs):
        for i in range(0, len(corpus), bsz):
            encoded = tok(corpus[i:i + bsz], return_tensors="pt", padding=True,
                          truncation=True, max_length=512,
                          **({"return_offsets_mapping": True} if child_only else {}))
            offsets = encoded.pop("offset_mapping", None)
            batch = encoded.to("cuda")
            labels = batch.input_ids.clone()
            labels[batch.attention_mask == 0] = -100
            if child_only:
                target_masks = [child_target_mask(row_offsets.tolist(), prefix, attention.tolist())
                                for row_offsets, prefix, attention in
                                zip(offsets, prefixes[i:i + bsz], batch.attention_mask.cpu())]
                labels[~torch.tensor(target_masks, device=labels.device)] = -100
                for offset, row_offsets in enumerate(offsets):
                    counts = child_label_counts(row_offsets.tolist(), prefixes[i + offset],
                                                batch.attention_mask[offset].tolist(),
                                                labels[offset].tolist())
                    previous_counts = row_counts[i + offset]
                    if previous_counts is not None and counts != previous_counts:
                        raise ValueError("label evidence changed across epochs")
                    row_counts[i + offset] = counts
            loss = model(**batch, labels=labels).loss
            if child_only and not bool(torch.isfinite(loss)):
                raise RuntimeError("nonfinite child-target loss")
            loss.backward()
            opt.step()
            opt.zero_grad()
            steps += 1
            total_tokens += int(batch.attention_mask.sum())
            supervised_tokens += int((labels[:, 1:] != -100).sum()) if child_only else int((labels != -100).sum())
    model.save_pretrained(args.out)
    with open(os.path.join(args.out, "train_meta.json"), "w") as f:
        metadata = dict(recipe="v1_frozen", n_texts=len(corpus), steps=steps,
                        tokens=total_tokens, rank=args.rank,
                        epochs=args.epochs, lr=args.lr,
                        final_loss=float(loss))
        if args.seed is not None:
            metadata.update(recipe="v1_frozen_seeded", seed=args.seed,
                            deterministic_algorithms=
                            torch.are_deterministic_algorithms_enabled())
        if child_only:
            metadata.update(recipe="v1_frozen_child_target_seeded" if args.seed is not None
                            else "v1_frozen_child_target",
                            source_recipe="preschool_records_v1", loss_target="child_body_only",
                            source_corpus_sha256=hashlib.sha256(corpus_bytes).hexdigest(),
                            supervised_tokens=supervised_tokens,
                            masked_nonpadding_tokens=total_tokens - supervised_tokens)
        json.dump(metadata, f, indent=1)
    if bound_gate is not None:
        write_training_receipt(args.trainer_receipt, args.out, bound_gate,
                               args.expected_gate_sha256, row_counts)
    open(os.path.join(args.out, "DONE"), "w").write("ok\n")
    print(f"TRAIN_DONE recipe=v1 texts={len(corpus)} steps={steps} "
          f"tokens={total_tokens} loss={float(loss):.4f}")


if __name__ == "__main__":
    main()
