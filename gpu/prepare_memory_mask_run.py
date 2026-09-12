"""Derive an exploratory prefix-mask comparison without changing trainer inputs."""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path

from gpu import prepare_memory_seed_run as seed_run
from organism_v6 import memory_dose as memory


CORPUS_PATH = "corpora/bank0/F_r16k16/across/sleep4/corpus.json"
ORIGINAL_SHA256 = "f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d"
RECEIPT = "mask_run_receipt.json"


def derive_corpus(original, tokenizer):
    derived = copy.deepcopy(original)
    counts = dict(items=0, changed_masks=0, changed_label_items=0,
                  input_tokens_per_epoch=0, original_supervised_per_epoch=0,
                  supervised_per_epoch=0, removed_labels=0, boundary_straddles=0,
                  truncated_items=0, omitted_owner_prefix_tokens=0)
    for before, after in zip(original["corpus"], derived["corpus"]):
        seed_run.require(before["mask_context"] is False and before["chat"] is False,
                         "expected original whole-text non-chat corpus")
        if before["kind"] in ("fact", "lesson"):
            after["mask_context"] = True
            counts["changed_masks"] += 1
        old_encoded = memory.encode_item(tokenizer, before)
        new_encoded = memory.encode_item(tokenizer, after)
        seed_run.require(old_encoded["input_ids"] == new_encoded["input_ids"],
                         "mask transformation changed model inputs")
        seed_run.require(all(new == old or new == -100 for old, new in
                             zip(old_encoded["labels"], new_encoded["labels"])),
                         "mask transformation changed target tokens")
        counts["items"] += 1
        counts["input_tokens_per_epoch"] += len(new_encoded["input_ids"])
        counts["original_supervised_per_epoch"] += sum(
            label != -100 for label in old_encoded["labels"][1:])
        counts["supervised_per_epoch"] += sum(
            label != -100 for label in new_encoded["labels"][1:])
        counts["changed_label_items"] += old_encoded["labels"] != new_encoded["labels"]
        counts["boundary_straddles"] += new_encoded["n_straddle"]
        counts["truncated_items"] += new_encoded["truncated"]
        if new_encoded["n_straddle"]:
            full = after["context"] + after["target"]
            cut = len(after["context"])
            offsets = tokenizer(full, add_special_tokens=False,
                                return_offsets_mapping=True)["offset_mapping"]
            crossings = [(full[start:cut], full[cut:end]) for start, end in offsets
                         if start < cut < end]
            seed_run.require(after["kind"] == "fact" and crossings == [(" ", "Owner")],
                             "unexpected context/target boundary token")
            counts["omitted_owner_prefix_tokens"] += 1
    seed_run.require(counts["changed_masks"] > 0, "no selected memory rows")
    seed_run.require(counts["truncated_items"] == 0, "truncation requires separate diagnosis")
    counts["removed_labels"] = (counts["original_supervised_per_epoch"]
                                - counts["supervised_per_epoch"])
    seed_run.require(counts["removed_labels"] > 0, "no supervision removed")
    identities = [(memory.render_item(item), item["weight"], item["mask_context"])
                  for item in derived["corpus"]]
    derived["sha"] = memory.sha_of(identities)
    derived["items_sha"] = memory.items_sha(derived["corpus"])
    derived["stats"]["supervised_tokens"] = counts["supervised_per_epoch"]
    derived["stats"]["supervised_tokens_semantics"] = "joint tokenization, shifted causal labels, one epoch"
    derived["mask_ablation"] = dict(
        treatment="fact_and_lesson_context_mask_only", original_sha=original["sha"],
        original_items_sha=original["items_sha"], input_strings_order_weights_unchanged=True,
        original_supervised_stat=original["stats"].get("supervised_tokens"),
        clean_lineage_eligible=False)
    return derived, counts


def prepare_run(source, destination, tokenizer):
    source, inputs, manifest, banks, metadata = seed_run.inspect_source(source, "F_r16k16", [0])
    destination = seed_run.plain_path(destination)
    seed_run.require(not destination.exists() and destination.parent.is_dir(),
                     "destination must be new with existing parent")
    seed_run.require(not destination.is_relative_to(source) and not source.is_relative_to(destination),
                     "source/destination overlap")
    source_digest = hashlib.sha256(inputs[CORPUS_PATH]).hexdigest()
    seed_run.require(source_digest == ORIGINAL_SHA256, "wrong original A1 corpus")
    derived, counts = derive_corpus(json.loads(inputs[CORPUS_PATH]), tokenizer)
    seed_run.require(counts["items"] == 12924 and counts["changed_masks"] == 6720
                     and counts["changed_label_items"] == 5376
                     and counts["boundary_straddles"] == counts["omitted_owner_prefix_tokens"] == 5376
                     and counts["input_tokens_per_epoch"] == 249995
                     and counts["original_supervised_per_epoch"] == 237071
                     and counts["supervised_per_epoch"] == 140975,
                     "unexpected original corpus/tokenizer accounting")
    output_inputs = dict(inputs)
    output_inputs[CORPUS_PATH] = (json.dumps(derived, sort_keys=True, indent=2) + "\n").encode()
    receipt = dict(status="PREPARED_NOT_TRAINED", created_utc=datetime.datetime.now(
        datetime.timezone.utc).isoformat(), source=str(source), destination=str(destination),
        source_corpus_sha256=source_digest, training_seed=2, source_bank_seed=manifest["seed"],
        rank=8, epochs=3, lr=1e-4, expected_steps=9693, counts=counts,
        treatment="fact_and_lesson_context_mask_only", clean_lineage_eligible=False,
        model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY", source_corpora=metadata,
        source_inputs={name: hashlib.sha256(content).hexdigest() for name, content in inputs.items()},
        inputs={name: hashlib.sha256(content).hexdigest() for name, content in output_inputs.items()})
    for name, content in inputs.items():
        seed_run.require(seed_run.read_input(source, name) == content, "source changed: " + name)
    destination.mkdir()
    for name, content in output_inputs.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(content)
        target.chmod(0o444)
    with (destination / RECEIPT).open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--tokenizer", required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    print(json.dumps(prepare_run(args.source, args.destination, tokenizer), sort_keys=True))


if __name__ == "__main__":
    main()
