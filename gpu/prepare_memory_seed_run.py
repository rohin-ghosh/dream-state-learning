"""Prepare source-identical diagnostic inputs without copying trained outputs."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import stat


BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
LABEL = "SYNTHETIC_DIAGNOSTIC_NOT_CLEAN_LINEAGE"
CELLS = ("F_r16k16", "CF_r16_b")
RECEIPT = "seed_run_receipt.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def plain_path(value):
    path = Path(value).expanduser()
    require(".." not in path.parts, f"parent traversal refused: {path}")
    path = path.absolute()
    for component in (*reversed(path.parents), path):
        require(not component.is_symlink(), f"symlink refused: {component}")
    return path


def read_input(root, relative):
    parts = Path(relative).parts
    require(parts and not Path(relative).is_absolute() and ".." not in parts,
            f"input escapes source: {relative}")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        child = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                        dir_fd=descriptor)
        with os.fdopen(child, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode),
                    f"not a regular input: {relative}")
            return stream.read()
    finally:
        os.close(descriptor)


def short_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def event_ids(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "event_id":
                yield child
            else:
                yield from event_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from event_ids(child)


def matches(document, expected, label):
    require(isinstance(document, dict), f"{label}: expected JSON object")
    for key, value in expected.items():
        require(key in document and type(document[key]) is type(value)
                and document[key] == value, f"{label}: missing/mismatched {key}")


def inspect_source(source, cell, banks=None):
    source = plain_path(source)
    require(source.is_dir(), "source must be an existing directory")
    require(cell in CELLS, "unsupported cell")
    inputs = {}

    def load(relative):
        content = read_input(source, relative)
        inputs[relative] = content
        document = json.loads(content)
        matches(document, {"synthetic": True}, relative)
        return document

    manifest = load("manifest.json")
    matches(manifest, {"model": BASE_MODEL, "scorer": "HFScorer", "counter": "hf"},
            "manifest")
    for key in ("seed", "n_banks", "token_budget"):
        require(type(manifest.get(key)) is int and manifest[key] >= (0 if key == "seed" else 1),
                f"manifest: invalid {key}")
    lora = manifest.get("lora", {})
    require(lora.get("rank") == 8 and lora.get("epochs") == 3
            and lora.get("lr") == 0.0001, "manifest: unexpected LoRA recipe")
    selected = list(range(manifest["n_banks"])) if banks is None else list(banks)
    require(selected and len(selected) == len(set(selected))
            and all(type(bank) is int and 0 <= bank < manifest["n_banks"] for bank in selected),
            "invalid or duplicate bank selection")
    distractor = load("distractor.json")
    matches(distractor, {"counter": "hf"}, "distractor")
    require(isinstance(distractor.get("text"), str) and distractor["text"],
            "distractor: missing text")
    all_banks = {}
    for bank in range(manifest["n_banks"]):
        document = load(f"banks/bank{bank}.json")
        matches(document, {"bank": bank, "seed": manifest["seed"]}, f"bank{bank}")
        require(isinstance(document.get("events"), list) and document["events"],
                f"bank{bank}: missing events")
        all_banks[bank] = document
    corpus_metadata = {}
    for bank in selected:
        prefix = f"corpora/bank{bank}/{cell}/across/sleep4"
        corpus = load(f"{prefix}/corpus.json")
        child = cell == "CF_r16_b"
        matches(corpus, {"bank": bank, "arm": "across", "sleep": 4,
                        "writer": "occurrences", "representation": "childframes" if child else "frames",
                        "shuffled": False, "ordering": "chronological", "counter": "hf",
                        "epochs": 3, "frame_forms": 1 if child else 16, "frame_repeats": 16}, prefix)
        require(corpus.get("frame_negatives", 0) == 0, f"{prefix}: unexpected negatives")
        budget = corpus.get("token_budget")
        require(type(budget) is int and budget > 0, f"{prefix}: missing token budget")
        items = corpus.get("corpus")
        require(isinstance(items, list) and items, f"{prefix}: missing corpus items")
        matches(corpus.get("stats"), {"n_items": len(items), "token_budget": budget}, prefix)
        identities = []
        known_events = set(event_ids(all_banks[bank]))
        for item in items:
            matches(item, {"chat": False, "shuffled": False}, prefix)
            require(isinstance(item.get("context"), str) and isinstance(item.get("target"), str)
                    and type(item.get("mask_context")) is bool, f"{prefix}: malformed item")
            weight = item.get("weight")
            require(type(weight) in (int, float) and math.isfinite(weight) and weight > 0,
                    f"{prefix}: invalid item weight")
            references = item.get("event_ids")
            require(isinstance(references, list) and references
                    and all(isinstance(reference, str) for reference in references),
                    f"{prefix}: missing event references")
            if item.get("kind") in ("filler", "filler_colour"):
                require(all(reference.startswith("fill-") for reference in references),
                        f"{prefix}: unexpected filler provenance")
            else:
                require(set(references) <= known_events, f"{prefix}: unknown source event")
            identities.append((item["context"] + item["target"], weight, item["mask_context"]))
        matches(corpus, {"sha": short_hash(identities), "items_sha": short_hash(sorted(identities))}, prefix)
        if child:
            matches(corpus, {"child_variant": "b", "child_backend": "vllm"}, prefix)
            generations = load(f"{prefix}/generations.json")
            matches(generations, {"bank": bank, "arm": "across", "sleep": 4,
                                  "variant": "b", "backend": "vllm", "model": BASE_MODEL,
                                  "repeats": 16, "negatives": 0}, prefix)
            events = generations.get("events")
            require(isinstance(events, dict) and events and set(events) <= known_events,
                    f"{prefix}: invalid generation events")
            for event in events.values():
                require(isinstance(event, dict) and isinstance(event.get("lines"), list) and len(event["lines"]) == 16
                        and all(isinstance(line, str) for line in event["lines"]),
                        f"{prefix}: malformed generations")
            matches(corpus, {"generations_sha": short_hash(
                [(key, value["lines"]) for key, value in sorted(events.items())])}, prefix)
        corpus_metadata[str(bank)] = {key: corpus[key] for key in
                                     ("sha", "items_sha", "token_budget", "ordering")}
    return source, inputs, manifest, selected, corpus_metadata


def prepare_run(source, destination, training_seed, cell, banks=None, check_only=False):
    require(type(training_seed) is int and training_seed >= 0, "training seed must be nonnegative")
    source = plain_path(source)
    destination = plain_path(destination)
    require(not destination.exists(), f"destination already exists: {destination}")
    require(destination.parent.is_dir(), "destination parent must already exist")
    require(not destination.is_relative_to(source) and not source.is_relative_to(destination),
            "source/destination overlap refused")
    source, inputs, manifest, selected, metadata = inspect_source(source, cell, banks)
    receipt = {
        "schema_version": 1, "status": "validated_only" if check_only else "prepared",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_run": str(source), "destination_run": str(destination),
        "source_bank_seed": manifest["seed"], "training_seed": training_seed,
        "base_model": BASE_MODEL, "source_scorer": manifest["scorer"],
        "label": LABEL, "clean_lineage_eligible": False, "cell": cell,
        "banks": selected, "arm": "across", "sleep": 4,
        "source_lora": manifest["lora"], "corpora": metadata,
        "inputs": {relative: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
                   for relative, content in sorted(inputs.items())},
    }
    for relative, content in inputs.items():
        require(read_input(source, relative) == content, f"source changed during validation: {relative}")
    if check_only:
        return receipt
    plain_path(destination)
    destination.mkdir()
    for relative, content in inputs.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(content)
        target.chmod(0o444)
        require(read_input(destination, relative) == content, f"copy verification failed: {relative}")
    for relative, content in inputs.items():
        require(read_input(source, relative) == content, f"source changed during copy: {relative}")
    with (destination / RECEIPT).open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    (destination / RECEIPT).chmod(0o444)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--destination", required=True, help="new run directory; parent must exist")
    parser.add_argument("--training-seed", required=True, type=int)
    parser.add_argument("--cell", required=True, choices=CELLS)
    parser.add_argument("--banks", nargs="+", type=int, help="corpus banks; default all; all bank JSONs retained")
    parser.add_argument("--check-only", "--check", action="store_true", help="validate inputs without writing anything")
    args = parser.parse_args(argv)
    try:
        receipt = prepare_run(args.source, args.destination, args.training_seed, args.cell,
                              args.banks, args.check_only)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"prepare_memory_seed_run: {error}\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
