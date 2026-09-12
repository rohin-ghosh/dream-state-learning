"""CPU-only export: continuous-context repetition versus separately reset copies."""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

from organism_v6 import train_adapter_v3 as trainer


COPIES = 16
ROWS = 80
MAX_LEN = 2048
EOS = "<|im_end|>"
SOURCE_SHA256 = {
    "teach": "2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c",
    "control": "e6cafbf68f361af7272a02fc23f0a90f92c34cd49b0a8e84437279bb288a8fe7",
}
COMMON_RECIPE = dict(rank=8, alpha=16, dropout=0.05, lr=3e-4, epochs=4,
                     max_len=MAX_LEN, pack=False, chat_template=False,
                     add_eos=False, overflow="truncate", shuffle_groups=True,
                     optimizer="adamw", max_steps=0)
RECIPES = {
    "short": dict(COMMON_RECIPE, batch_size=4, grad_accum=16),
    "long": dict(COMMON_RECIPE, batch_size=1, grad_accum=4),
}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_sources(teach, control):
    """Accept only the actual seed0 native training bytes, never candidate/eval rows."""
    sources = {}
    for arm, path in (("teach", teach), ("control", control)):
        payload = Path(path).read_bytes()
        require(digest(payload) == SOURCE_SHA256[arm], f"{arm}: actual source hash mismatch")
        sources[arm] = json.loads(payload)["corpus"]
    return sources


def build_views(rows):
    """Pure material transformation; no rendering, answer generation, or tokenization."""
    require(len(rows) == ROWS, "expected 80 original examples")
    require(len({row["group"] for row in rows}) == ROWS, "original groups must be unique")
    views = dict(short=[], long=[])
    for source_index, row in enumerate(rows):
        spans = row["spans"]
        require(len(spans) == 2 and spans[0][1] is False and spans[1][1] is True,
                "expected native context then response")
        require(all(len(span) == 3 and isinstance(span[0], str) and span[0]
                    for span in spans), "invalid native spans")
        require(EOS not in spans[1][0], "response already contains EOS")
        require(row.get("meta", {}).get("source_event_ids"), "missing source event binding")
        require("repetition" not in row["meta"], "already repeated source")
        unit = copy.deepcopy(spans) + [[EOS, True, spans[1][2]]]
        binding = dict(source_row_index=source_index, source_row_sha256=digest(json_bytes(row)))
        for copy_index in range(COPIES):
            short = copy.deepcopy(row)
            short["spans"] = copy.deepcopy(unit)
            short["meta"]["repetition"] = dict(binding, copies=1, copy_index=copy_index)
            views["short"].append(short)
        long = copy.deepcopy(row)
        long["spans"] = [copy.deepcopy(span) for _ in range(COPIES) for span in unit]
        long["meta"]["repetition"] = dict(binding, copies=COPIES)
        views["long"].append(long)
    return views


def encode_rows(rows, tokenizer, add_eos):
    """Reuse V3's native encoder/collator; reject rather than split or truncate."""
    encoded = []
    for index, item in enumerate(trainer.normalize_items(rows)):
        segments = trainer.encode_item_segments(item, tokenizer, MAX_LEN, False,
                                              add_eos, index, overflow="truncate")
        require(len(segments) == 1, "missing or split example")
        segment = segments[0]
        require(segment.context_dropped == segment.target_dropped == 0,
                "2048-token pilot would truncate; no export validation")
        batch = trainer.collate([[segment]], tokenizer.pad_token_id)
        require(batch["input_ids"] == [segment.ids] and batch["labels"] == [segment.labels],
                "collation changed tokens or supervised boundaries")
        require(batch["position_ids"] == [list(range(len(segment.ids)))], "position reset inside sequence")
        require(batch["segment_ids"] == [[0] * len(segment.ids)], "attention isolation inside sequence")
        encoded.append(segment)
    return encoded


def audit_order(short, long, seeds):
    """Replay V3 epoch_order and its microbatch/accumulation slicing without a model."""
    schedules = {}
    for seed in seeds:
        by_view = {}
        for view, encoded in (("short", short), ("long", long)):
            recipe = RECIPES[view]
            packs = trainer.pack_by_group(encoded, MAX_LEN, pack=False)
            updates = []
            for epoch in range(recipe["epochs"]):
                ordered = trainer.epoch_order(packs, seed, epoch, True)
                groups = [pack[0].group for pack in ordered]
                runs = [(group, len(list(run))) for group, run in itertools.groupby(groups)]
                repeats = COPIES if view == "short" else 1
                require(len(runs) == ROWS and all(count == repeats for _, count in runs),
                        "V3 order breaks contiguous original groups; trainer fix required")
                pending = []
                for batch_index, start in enumerate(range(0, len(ordered), recipe["batch_size"]), 1):
                    pending.extend(groups[start:start + recipe["batch_size"]])
                    if batch_index % recipe["grad_accum"] == 0:
                        update_groups = [group for group, _ in itertools.groupby(pending)]
                        require(len(update_groups) == 4 and
                                all(pending.count(group) == repeats for group in update_groups),
                                "V3 update does not contain four complete original groups")
                        updates.append(update_groups)
                        pending = []
                require(not pending, "partial optimizer update at epoch boundary")
            require(len(updates) == 80, "expected 80 optimizer updates over four epochs")
            by_view[view] = updates
        require(by_view["short"] == by_view["long"], "V3 short/long update group order differs")
        schedules[str(seed)] = by_view["short"]
    return schedules


def validate_material(sources, material, tokenizer, seeds=(0, 1, 2)):
    """Native CPU audit, also usable with a tokenizer fixture; never loads a model."""
    require(seeds, "at least one order seed required")
    require(tokenizer.encode(EOS, add_special_tokens=False) == [tokenizer.eos_token_id],
            "inserted EOS must encode to exactly the native EOS ID")
    report = dict(arms={}, order_seeds=list(seeds), tokenizer_class=type(tokenizer).__name__)
    if hasattr(tokenizer, "get_vocab"):
        report["tokenizer_vocab_sha256"] = digest(json_bytes(tokenizer.get_vocab()))
    reference_order = None
    paired_budgets = []
    for arm in ("teach", "control"):
        require(material[arm] == build_views(sources[arm]), "material or source bindings changed")
        original = encode_rows(sources[arm], tokenizer, True)
        short = encode_rows(material[arm]["short"], tokenizer, False)
        long = encode_rows(material[arm]["long"], tokenizer, False)
        for index, source in enumerate(original):
            require(sum(label == tokenizer.eos_token_id for label in source.labels) == 1,
                    "source must have exactly one supervised EOS (context EOS remain masked)")
            copies = short[index * COPIES:(index + 1) * COPIES]
            for attribute in ("ids", "labels", "cats"):
                expected = getattr(source, attribute)
                require(all(getattr(item, attribute) == expected for item in copies),
                        "short copy differs from actual native source")
                require(getattr(long[index], attribute) == expected * COPIES,
                        "long copy boundaries or token budgets differ")
        schedules = audit_order(short, long, seeds)
        if reference_order is not None:
            require(schedules == reference_order, "teach/control group order differs")
        reference_order = schedules
        budgets = {}
        for view, encoded in (("original", original), ("short", short), ("long", long)):
            budgets[view] = dict(rows=len(encoded), input_tokens=sum(len(item.ids) for item in encoded),
                                 target_tokens=sum(item.n_target for item in encoded),
                                 max_sequence_tokens=max(len(item.ids) for item in encoded))
        for name in ("input_tokens", "target_tokens"):
            require(budgets["short"][name] == budgets["long"][name] == COPIES * budgets["original"][name],
                    "repeated token mass mismatch")
        paired_budgets.append([(len(item.ids), item.n_target) for item in original])
        report["arms"][arm] = budgets
    require(paired_budgets[0] == paired_budgets[1], "native teach/control budgets differ")
    report["optimizer_update_groups"] = reference_order
    report["status"] = "TOKENIZER_AND_V3_ORDER_VALIDATED_NO_FIT"
    return report


def export_material(teach, control, out, tokenizer=None, seeds=(0, 1, 2)):
    """Write only into a fresh directory, after validation; bind exact source/output bytes."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    sources = load_sources(teach, control)
    material = {arm: build_views(rows) for arm, rows in sources.items()}
    files = {f"{arm}_{view}.json": json_bytes(dict(corpus=rows))
             for arm, views in material.items() for view, rows in views.items()}
    audit = validate_material(sources, material, tokenizer, seeds) if tokenizer is not None else None
    manifest = dict(status="NATIVE_AUDIT_PENDING" if audit is None else audit["status"],
                    comparison="continuous-context repetition versus resets",
                    source_sha256=SOURCE_SHA256, copies=COPIES, recipes=RECIPES,
                    source_code_sha256={"exporter": digest(Path(__file__).read_bytes()),
                                        "trainer": digest(Path(trainer.__file__).read_bytes())},
                    output_sha256={name: digest(payload) for name, payload in files.items()},
                    audit=audit,
                    limitations=["2048-token pilot, not superlong validation",
                                 "microbatch/accumulation differ; dropout=0.05 remains active",
                                 "one supervised EOS per copy; native context EOS stay masked",
                                 "no child-experience, sleep, or plasticity-separation claim",
                                 "update counts assume finite loss on every microbatch",
                                 "overflow=truncate is a V3 selector, not permission: audit requires zero drops",
                                 "no fit, model output, or evaluation confirmation"])
    files["manifest.json"] = json_bytes(manifest)
    out.mkdir(parents=True, exist_ok=False)
    for name, payload in files.items():
        with (out / name).open("xb") as handle:
            handle.write(payload)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teach", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tokenizer", type=Path, help="local native snapshot; never downloads or loads weights")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    args = parser.parse_args(argv)
    tokenizer = None
    if args.tokenizer is not None:
        require(args.tokenizer.is_dir(), "tokenizer must be an existing local directory")
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True,
                                                 trust_remote_code=False)
    manifest = export_material(args.teach, args.control, args.out, tokenizer, tuple(args.seeds))
    print(json.dumps(dict(status=manifest["status"], source_sha256=manifest["source_sha256"],
                          output_sha256=manifest["output_sha256"]), sort_keys=True))


if __name__ == "__main__":
    main()
