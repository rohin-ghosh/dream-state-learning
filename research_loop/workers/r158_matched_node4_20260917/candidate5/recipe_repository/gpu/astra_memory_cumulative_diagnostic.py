"""Fixed native-memory cumulative replay, not warm-start G3 or clean lineage.

prepare is CPU/local-tokenizer only. run requires one explicitly reserved GPU,
an absolute lease cutoff, and --allow-gpu. Six fresh supervised processes run
sequentially within 90 aggregate reserved minutes, including cleanup. Failed
roots cannot resume/retry. reduce only replays saved artifacts into a new file.

Main supplies independently verified pins.json:
{"model": {"relative/file": "sha256", ...},
 "a1": {"relative/file": "sha256", ...}, "distractor_sha256": "..."}.
Both inventories must cover all files in the respective local directories.
The A1 directory must be resolved, with actual weights and native train_meta.
No adapter aliases, additional fits, generation, or threshold rescue exist.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

from organism_v6 import memory_dose as md
from organism_v6 import run_reasoning_neutral as supervisor


OLD_SHA = "f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d"
BANK_SHA = "87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31"
A1_WEIGHTS_SHA = "c5bc4b2d7599d7f30732bb3adb98a1415206ecca41e0f96ce6d1db89015d6516"
NATIVE_RECIPE = "memory_dose_v1 (mirrors train_adapter.py v1)"
OLD_ROWS, NEW_ROWS, UNION_ROWS = 12924, 2048, 14972
OLD_CUES, NEW_CUES = 1313, 64
CAP_SECONDS, CLEANUP_SECONDS = 5400, 45
STAGES = ("A1_before", "fit_AN", "fit_A2", "AN", "A2", "A1_after")
READS = ("A1_before", "AN", "A2", "A1_after")
RECIPE = dict(rank=8, epochs=3, lr=1e-4, seed=2, bsz=4, max_len=512,
              alpha=16, dropout=0.05, targets=list(md.LORA_TARGETS))
STARTING_STATE = "fresh_base_cumulative_replay_not_warm_start"
SOURCES = ("gpu/astra_memory_cumulative_diagnostic.py", "organism_v6/memory_dose.py",
           "organism_v6/run_reasoning_neutral.py")
REPO = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, payload):
    supervisor._write(Path(path), payload)


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def tree_hashes(root):
    root = Path(root).resolve(strict=True)
    require(root.is_dir(), "local directory required")
    paths = sorted(root.rglob("*"))
    require(not any(path.is_symlink() and path.is_dir() for path in paths), "directory symlink")
    require(all(path.is_file() or path.is_dir() for path in paths), "unsupported file")
    result = {str(path.relative_to(root)): file_sha(path) for path in paths if path.is_file()}
    require(bool(result), "empty artifact tree")
    return result


def source_hashes():
    return {name: file_sha(REPO / name) for name in SOURCES}


def new_events(bank):
    require(bank["seed"] == 1 and bank["bank"] == 0, "fixed bank0 seed1 required")
    events = [event for event in md.ledger_items(bank, "across", 5) if event["session"] == 5]
    require(len(events) == 128 and all(event["kind"] == "interference" for event in events),
            "exact session5 interference source required")
    require(len({event["event_id"] for event in events}) == 128, "duplicate source events")
    owners = Counter(event["owner"] for event in events)
    require(len(owners) == 32 and set(owners.values()) == {4}, "32 owners, four events each required")
    colours = {owner: {event["colour"] for event in events if event["owner"] == owner} for owner in owners}
    require(all(len(values) == 1 for values in colours.values()), "inconsistent source colours")
    require(Counter(next(iter(values)) for values in colours.values()) == {colour: 8 for colour in md.COLOURS},
            "NEW owner colours must be balanced")
    require(not set(owners) & {owner["id"] for owner in bank["owners"]}, "OLD/NEW owners overlap")
    return events


def build_rows(bank, old):
    require(len(old["corpus"]) == OLD_ROWS, "OLD row count")
    require(old["ordering"] == "chronological" and old["representation"] == "frames"
            and old["writer"] == "occurrences" and old["shuffled"] is False, "OLD native recipe")
    require(all(row["weight"] == 1 and not row["chat"] and not row["mask_context"]
                for row in old["corpus"]), "OLD mask/weight changed")
    rows = [md._piece(event, "frames", frame_forms=16, frame_repeats=16,
                      frame_copy=copy, seed=1, bank=0)
            for event in new_events(bank) for copy in range(16)]
    require(len(rows) == NEW_ROWS, "NEW row count")
    return rows, old["corpus"] + rows


def corpus_snapshot(rows, tokenizer):
    encodings, row_hashes = [], []
    for row in rows:
        encoded = md.encode_item(tokenizer, row, max_len=512)
        require(not encoded["truncated"] and encoded["n_straddle"] == 0, "token truncation/straddle")
        require(encoded["labels"] == encoded["input_ids"] and len(encoded["input_ids"]) > 1,
                "native full-token supervision lost")
        encodings.append(encoded)
        row_hashes.append(value_sha(row))
    stats = dict(n_items=len(rows), input_tokens=sum(len(enc["input_ids"]) for enc in encodings),
                 shifted_supervised_tokens=sum(len(enc["labels"]) - 1 for enc in encodings),
                 by_kind=dict(Counter(row["kind"] for row in rows)),
                 session_blocks=dict(Counter(str(row["session"]) for row in rows)),
                 colour_marginals={colour: sum(row["colour"] == colour for row in rows) for colour in md.COLOURS},
                 steps=3 * math.ceil(len(rows) / 4), boundary_straddles=0, truncated_items=0)
    corpus = dict(corpus=rows, bank=0, arm="across", sleep=5, writer="occurrences",
                  representation="frames", shuffled=False, ordering="chronological", epochs=3,
                  frame_forms=16, frame_repeats=16, frame_negatives=0, counter="hf",
                  token_budget=None, no_repadding=True, synthetic=True,
                  synthetic_note=md.SYNTHETIC_NOTE, stats=stats,
                  sha=md.sha_of([(md.render_item(row), row["weight"], row["mask_context"]) for row in rows]),
                  items_sha=md.items_sha(rows))
    audit = dict(row_sha256=row_hashes, encoding_sha256=[value_sha(enc) for enc in encodings], stats=stats)
    return corpus, audit


def build_cues(bank, distractor, tokenizer):
    cues = md.build_cues(bank, distractor, adjacent_subset=4, tokenizer=tokenizer)
    require(len(cues) == OLD_CUES, "native OLD cue count changed")
    owners = {}
    for event in new_events(bank):
        owners.setdefault(event["owner"], event["colour"])
    candidates = md.colour_candidates(True)
    for owner, colour in owners.items():
        for kind, prefix in (("new_frame", md.FRAME_PREFIX), ("new_bicycle", md.FRAME_BICYCLE_PREFIX)):
            prompt = prefix.format(owner=owner)
            require(not any(value.lower() in prompt.lower() for value in md.COLOURS), "NEW answer exposure")
            cues.append(dict(cue_id=f"{kind}|{owner}", kind=kind, prompt=prompt,
                             candidates=candidates, a=colour, owner=owner, dose=4, form=kind,
                             context="none", abstain=list(md.ABSTAIN_CANDIDATES),
                             cand_tokens=md._cand_tokens(candidates, tokenizer, prompt)))
    require(len(cues) == OLD_CUES + NEW_CUES and len({cue["cue_id"] for cue in cues}) == len(cues),
            "cue coverage/identity")
    return cues


def candidate_work(cues):
    colour = sum(sum(len(variants) for variants in cue["candidates"].values()) for cue in cues)
    abstain = sum(len(cue.get("abstain", [])) for cue in cues)
    return dict(cues=len(cues), passes=2, candidate_sequences=2 * colour,
                abstention_sequences=2 * abstain,
                scored_prompt_rows=2 * (len(cues) + sum(bool(cue.get("abstain")) for cue in cues)))


def verify_a1(path, old):
    path = Path(path)
    require(not (path / "adapter_ref.json").exists(), "resolve A1 alias before preparation")
    require((path / "adapter_model.safetensors").is_file(),
            "actual A1 weights required")
    require(file_sha(path / "adapter_model.safetensors") == A1_WEIGHTS_SHA, "original A1 weight pin mismatch")
    require((path / "DONE").is_file(), "A1 native DONE missing")
    config, meta = read(path / "adapter_config.json"), read(path / "train_meta.json")
    require(config["r"] == 8 and config["lora_alpha"] == 16 and config["lora_dropout"] == .05
            and config["bias"] == "none" and set(config["target_modules"]) == set(md.LORA_TARGETS),
            "A1 adapter recipe mismatch")
    for key, value in RECIPE.items():
        require(meta[key] == value, f"A1 {key} mismatch")
    require(meta["recipe"] == NATIVE_RECIPE and meta["corpus_sha"] == old["sha"] and meta["items_sha"] == old["items_sha"]
            and meta["steps"] == 9693 and meta["n_items"] == OLD_ROWS
            and meta["tokens"] == 749985 and meta["supervised_tokens"] == 711213
            and not meta["boundary_straddles"] and not meta["truncated_items"], "A1 original provenance mismatch")
    return meta


def load_tokenizer(model):
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(model), local_files_only=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    return tokenizer


def original_paths(original_root):
    root = Path(original_root).resolve(strict=True)
    return dict(old=root / "corpora/bank0/F_r16k16/across/sleep4/corpus.json",
                bank=root / "banks/bank0.json", distractor=root / "distractor.json",
                a1=root / "adapters/bank0/F_r16k16/across/sleep4/r8")


def prepare(out, *, original_root, model, pins):
    out = Path(out).resolve()
    inputs = {name: Path(path).resolve(strict=True) for name, path in
              dict(**original_paths(original_root), model=model, pins=pins).items()}
    require(all(out != path and out not in path.parents and path not in out.parents for path in inputs.values()),
            "output/input overlap")
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    write(out / "PREPARE_STARTED.json", dict(sources=source_hashes(), inputs={key: str(path) for key, path in inputs.items()}))
    expected = read(inputs["pins"])
    require(set(expected) == {"model", "a1", "distractor_sha256"}, "pins fields")
    require(file_sha(inputs["old"]) == OLD_SHA and file_sha(inputs["bank"]) == BANK_SHA, "fixed source hash mismatch")
    require(file_sha(inputs["distractor"]) == expected["distractor_sha256"], "distractor hash mismatch")
    require(tree_hashes(inputs["model"]) == expected["model"], "model hash mismatch")
    require(tree_hashes(inputs["a1"]) == expected["a1"], "A1 hash mismatch")
    config = read(inputs["model"] / "config.json")
    require(config.get("model_type") == "qwen2" and config.get("hidden_size") == 3584
            and config.get("num_hidden_layers") == 28, "frozen Qwen2.5-7B base required")
    original, source_bank = read(inputs["old"]), read(inputs["bank"])
    a1_meta = verify_a1(inputs["a1"], original)
    tokenizer = load_tokenizer(inputs["model"])
    new, union = build_rows(source_bank, original)
    old_snapshot, old_audit = corpus_snapshot(original["corpus"], tokenizer)
    require(old_audit["stats"]["input_tokens"] * 3 == 749985
            and old_audit["stats"]["shifted_supervised_tokens"] * 3 == 711213, "OLD tokenizer totals changed")
    require(old_snapshot["sha"] == original["sha"] and old_snapshot["items_sha"] == original["items_sha"],
            "OLD native identity changed")
    for name, key in (("OLD.json", "old"), ("bank.json", "bank"), ("distractor.json", "distractor")):
        with (out / name).open("xb") as target:
            target.write(inputs[key].read_bytes())
    write(out / "OLD.audit.json", old_audit)
    for name, rows in (("AN", new), ("A2", union)):
        corpus, audit = corpus_snapshot(rows, tokenizer)
        if name == "A2":
            require(audit["row_sha256"][:OLD_ROWS] == old_audit["row_sha256"]
                    and audit["encoding_sha256"][:OLD_ROWS] == old_audit["encoding_sha256"], "OLD prefix changed")
        write(out / f"{name}.json", corpus)
        write(out / f"{name}.audit.json", audit)
    cues = build_cues(source_bank, read(inputs["distractor"])["text"], tokenizer)
    abstain = md.abstain_token_check(tokenizer, owner=source_bank["owners"][0]["id"])
    require(abstain["ok"], "native abstention token check failed")
    require(md.render_chat("probe", tokenizer=tokenizer) == md.render_chat("probe"), "native chat template mismatch")
    write(out / "cues.json", cues)
    manifest = dict(version=1, starting_state=STARTING_STATE, recipe=RECIPE,
                    root=str(out), model=str(inputs["model"]), a1=str(inputs["a1"]), pins=expected,
                    sources=source_hashes(), stages=list(STAGES), cap_seconds=CAP_SECONDS,
                    files=tree_hashes(out), a1_meta=a1_meta, cue_work_per_read=candidate_work(cues),
                    abstain_check=abstain, prepare_cpu_seconds=time.monotonic() - started,
                    input_paths={key: str(path) for key, path in inputs.items()},
                    lineage={"A1": "Fit(base, OLD), inherited 9693 steps",
                             "AN": "Fit(base, NEW), 1536 steps", "A2": "Fit(base, OLD+NEW), 11229 steps"},
                    claims="descriptive cumulative replay only; no clean/H1/H2/G3 closure/mechanism freeze")
    write(out / "manifest.json", manifest)
    return dict(root=str(out), manifest_sha256=file_sha(out / "manifest.json"))


def verify_prepared(root, manifest_sha256, *, weights=True):
    root = Path(root).resolve(strict=True)
    require(file_sha(root / "manifest.json") == manifest_sha256, "manifest digest mismatch")
    manifest = read(root / "manifest.json")
    require(manifest["root"] == str(root) and manifest["sources"] == source_hashes(), "root/source drift")
    require(manifest["recipe"] == RECIPE and manifest["starting_state"] == STARTING_STATE
            and manifest["stages"] == list(STAGES) and manifest["cap_seconds"] == CAP_SECONDS, "protocol mismatch")
    for name, digest in manifest["files"].items():
        require(file_sha(root / name) == digest, f"prepared file drift: {name}")
    if weights:
        for name in ("model", "a1"):
            require(tree_hashes(manifest[name]) == manifest["pins"][name], f"{name} artifact drift")
    return manifest


def artifact(root, manifest, stage):
    if stage.startswith("A1_"):
        return Path(manifest["a1"]), manifest["pins"]["a1"]
    fit = read(root / "stages" / f"fit_{stage}" / "DONE.json")
    return root / "stages" / f"fit_{stage}" / "adapter", fit["adapter_hashes"]


def validate_fit(meta, corpus):
    for key, value in RECIPE.items():
        require(meta[key] == value, f"fit {key} mismatch")
    stats = corpus["stats"]
    require(meta["recipe"] == NATIVE_RECIPE and meta["n_items"] == stats["n_items"]
            and meta["steps"] == meta["total_steps"] == stats["steps"]
            and meta["tokens"] == stats["input_tokens"] * 3
            and meta["supervised_tokens"] == stats["shifted_supervised_tokens"] * 3
            and meta["corpus_sha"] == corpus["sha"] and meta["items_sha"] == corpus["items_sha"]
            and not meta["boundary_straddles"] and not meta["truncated_items"]
            and not meta["measure_only"] and math.isfinite(meta["final_loss"]), "native fit incomplete/mismatched")


def evaluate(scorer, cues, stage, adapter_meta):
    measured = dict(candidate_calls=0, prompt_rows=0, candidate_sequences=0,
                    forward_calls=0, forward_rows=0, padded_input_tokens=0)
    candidate_method = scorer.candidate_logprobs
    forward_method = getattr(scorer, "_forward_last", None)

    def counted_candidates(prompts, candidates):
        measured["candidate_calls"] += 1
        measured["prompt_rows"] += len(prompts)
        measured["candidate_sequences"] += sum(len(values) for values in candidates)
        return candidate_method(prompts, candidates)

    def counted_forward(rows, keep):
        measured["forward_calls"] += 1
        measured["forward_rows"] += len(rows)
        measured["padded_input_tokens"] += len(rows) * max(map(len, rows))
        return forward_method(rows, keep)

    scorer.candidate_logprobs = counted_candidates
    if forward_method is not None:
        scorer._forward_last = counted_forward
    tick = time.monotonic()
    try:
        result = md.score_cues(scorer, cues, lambdas=[1.0])
    finally:
        scorer.candidate_logprobs = candidate_method
        if forward_method is not None:
            scorer._forward_last = forward_method
    measured["scoring_seconds"] = time.monotonic() - tick
    measured["forward_count_available"] = forward_method is not None
    require(len(result["off"]) == len(result["on"][1.0]) == len(cues), "incomplete native scoring")
    rows = [dict(**{key: value for key, value in cue.items() if key not in ("prompt", "candidates")},
                 OFF=off, ON=on) for cue, off, on in zip(cues, result["off"], result["on"][1.0])]
    return dict(tag=stage, bank=0, lam=1.0, cues=rows, n_cues=len(rows), adapter_meta=adapter_meta,
                scorer_calls=getattr(scorer, "calls", None), work=candidate_work(cues), measured_work=measured,
                boundary_straddles=getattr(scorer, "boundary_straddles", None),
                template_check=md.render_chat("probe", tokenizer=scorer.tok) == md.render_chat("probe"),
                abstain_check=md.abstain_token_check(scorer.tok))


def worker(root, manifest_sha256, stage, *, allow_gpu=False):
    require(allow_gpu, "explicit --allow-gpu required")
    require(stage in STAGES, "unknown stage")
    started = time.monotonic()
    root = Path(root).resolve(strict=True)
    job = read(root / f"{stage}.job.json")
    reservation = read(root / "RUN_STARTED.json")
    require(job["manifest_sha256"] == manifest_sha256 and job["stage"] == stage, "job binding")
    require(reservation["manifest_sha256"] == manifest_sha256 and job["device"] == reservation["device"]
            and job["deadline_unix"] <= reservation["deadline_unix"] - CLEANUP_SECONDS
            and reservation["deadline_unix"] <= reservation["started_unix"] + CAP_SECONDS
            and reservation["deadline_unix"] <= reservation["lease_cutoff_unix"], "job reservation bound")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == job["device"] and time.time() < job["deadline_unix"],
            "worker device/deadline mismatch")
    directory = root / "stages" / stage
    directory.mkdir(parents=True, exist_ok=False)
    for predecessor in STAGES[:STAGES.index(stage)]:
        require((root / "stages" / predecessor / "DONE.json").is_file(), "missing predecessor")
    manifest = verify_prepared(root, manifest_sha256)
    require(time.time() < job["deadline_unix"], "deadline before load")
    common = dict(stage=stage, pid=os.getpid(), manifest_sha256=manifest_sha256,
                  job_sha256=file_sha(root / f"{stage}.job.json"), starting_state=STARTING_STATE,
                  device=job["device"])
    if stage.startswith("fit_"):
        corpus = read(root / f"{stage[4:]}.json")
        md.set_write_root(str(directory))
        adapter = directory / "adapter"
        require(not adapter.exists(), "fresh adapter destination required")
        meta = md.train_hf(corpus, str(adapter), rank=8, epochs=3, lr=1e-4, seed=2,
                           bsz=4, max_len=512, model_name=manifest["model"])
        validate_fit(meta, corpus)
        require(meta["model"] == manifest["model"], "fit base mismatch")
        result = dict(**common, train_meta=meta, adapter_hashes=tree_hashes(adapter))
    else:
        adapter, hashes = artifact(root, manifest, stage)
        require(tree_hashes(adapter) == hashes, "read adapter drift")
        require(md.MODEL_NAME == manifest["model"], "V6_MODEL must be set before worker import")
        scorer = md.load_scorer("hf", str(adapter), batch_size=16, seed=0)
        cues = read(root / "cues.json")
        require(build_cues(read(root / "bank.json"), read(root / "distractor.json")["text"], scorer.tok) == cues,
                "deployed tokenizer cue drift")
        evaluation = evaluate(scorer, cues, stage, read(adapter / "train_meta.json"))
        write(directory / "eval.json", evaluation)
        require(tree_hashes(adapter) == hashes, "read mutated adapter")
        result = dict(**common, adapter_hashes=hashes, eval_sha256=file_sha(directory / "eval.json"))
    require(time.time() < job["deadline_unix"], "worker exceeded deadline")
    write(directory / "DONE.json", dict(**result, worker_seconds=time.monotonic() - started))


def run(root, manifest_sha256, *, lease_cutoff_unix, allow_gpu=False):
    require(allow_gpu, "explicit --allow-gpu required")
    require(math.isfinite(lease_cutoff_unix), "finite lease cutoff required")
    device = supervisor.selected_device()
    root = Path(root).resolve(strict=True)
    started, started_unix = time.monotonic(), time.time()
    deadline = min(started_unix + CAP_SECONDS, lease_cutoff_unix)
    require(deadline - started_unix > CLEANUP_SECONDS, "insufficient remaining reservation")
    write(root / "RUN_STARTED.json", dict(manifest_sha256=manifest_sha256, device=device,
          started_unix=started_unix, deadline_unix=deadline, lease_cutoff_unix=lease_cutoff_unix,
          cap_seconds=CAP_SECONDS, workers="sequential, one GPU", starting_state=STARTING_STATE))
    records, failure = [], None
    previous_model = os.environ.get("V6_MODEL")
    try:
        manifest = verify_prepared(root, manifest_sha256)
        os.environ["V6_MODEL"] = manifest["model"]
        require(supervisor.gpu_processes_absent(device), "reserved GPU not empty")
        for stage in STAGES:
            remaining = min(deadline - time.time(), CAP_SECONDS - (time.monotonic() - started)) - CLEANUP_SECONDS
            require(remaining > 0, "aggregate reservation exhausted")
            require(not (root / "stages" / stage).exists(), "existing stage cannot retry")
            write(root / f"{stage}.job.json", dict(stage=stage, manifest_sha256=manifest_sha256,
                  device=device, deadline_unix=min(deadline - CLEANUP_SECONDS, time.time() + remaining),
                  timeout_seconds=remaining))
            command = [sys.executable, "-B", "-m", "gpu.astra_memory_cumulative_diagnostic", "worker",
                       "--root", str(root), "--manifest-sha256", manifest_sha256, "--stage", stage, "--allow-gpu"]
            tick = time.monotonic()
            record = dict(stage=stage, timeout_seconds=remaining, command=command)
            records.append(record)
            try:
                record["pid"] = supervisor.run_worker(command, log_path=root / f"{stage}.log",
                                                       timeout=remaining, device=device)
                done = read(root / "stages" / stage / "DONE.json")
                require(done["pid"] == record["pid"] and done["stage"] == stage
                        and done["manifest_sha256"] == manifest_sha256, "worker receipt binding")
                record["done_sha256"] = file_sha(root / "stages" / stage / "DONE.json")
            finally:
                record["supervised_seconds"] = time.monotonic() - tick
        require(time.time() <= deadline and time.monotonic() - started <= CAP_SECONDS, "aggregate cap exceeded")
        verify_prepared(root, manifest_sha256)
        require(time.time() <= deadline and time.monotonic() - started <= CAP_SECONDS, "verification exceeded cap")
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        if previous_model is None:
            os.environ.pop("V6_MODEL", None)
        else:
            os.environ["V6_MODEL"] = previous_model
        write(root / "RUN_FINISHED.json", dict(manifest_sha256=manifest_sha256, records=records,
              failure=failure, completed=failure is None, reserved_gpu_seconds=time.monotonic() - started,
              inherited_fit_seconds=1327.3, inherited_steps=9693,
              deadline_unix=deadline, finished_unix=time.time()))
    return read(root / "RUN_FINISHED.json")


def contrast(first, second, ids):
    left = {row["cue_id"]: row for row in first["cues"]}
    right = {row["cue_id"]: row for row in second["cues"]}
    rows = []
    for cue_id in ids:
        before, after = md.cue_metrics(left[cue_id]), md.cue_metrics(right[cue_id])
        rows.append(dict(cue_id=cue_id, before=before, after=after,
                         delta_on=after["ON"]["p_norm"] - before["ON"]["p_norm"],
                         delta_off=after["OFF"]["p_norm"] - before["OFF"]["p_norm"],
                         delta_effect=after["d_p_norm"] - before["d_p_norm"]))
    baseline = sum(row["before"]["d_p_norm"] for row in rows) / len(rows)
    later = sum(row["after"]["d_p_norm"] for row in rows) / len(rows)
    return dict(per_owner=rows, before_effect=baseline, after_effect=later,
                delta_effect=later - baseline, retention_ratio=later / baseline if baseline > 0 else None)


def reduce(root, manifest_sha256, report):
    root = Path(root).resolve(strict=True)
    manifest = verify_prepared(root, manifest_sha256)
    finished = read(root / "RUN_FINISHED.json")
    started = read(root / "RUN_STARTED.json")
    require(finished["completed"] and finished["failure"] is None
            and finished["manifest_sha256"] == manifest_sha256, "run incomplete")
    require(finished["reserved_gpu_seconds"] <= CAP_SECONDS
            and finished["finished_unix"] <= finished["deadline_unix"]
            and finished["deadline_unix"] == started["deadline_unix"], "reservation cap exceeded")
    require([record["stage"] for record in finished["records"]] == list(STAGES), "fixed stage sequence")
    require(len({record["pid"] for record in finished["records"]}) == len(STAGES), "fresh worker identities required")
    evaluations, fits = {}, {}
    for record in finished["records"]:
        stage = record["stage"]
        directory = root / "stages" / stage
        require(file_sha(directory / "DONE.json") == record["done_sha256"], "worker receipt drift")
        done = read(directory / "DONE.json")
        require(done["pid"] == record["pid"] and done["manifest_sha256"] == manifest_sha256
                and done["job_sha256"] == file_sha(root / f"{stage}.job.json"), "receipt/job mismatch")
        cleanup = read(root / f"{stage}.cleanup.json")
        require(cleanup["reservation_release_verified"] and cleanup["owned_group_empty"]
                and cleanup["gpu_processes_absent"] and cleanup["pid"] == record["pid"], "cleanup unverified")
        if stage.startswith("fit_"):
            validate_fit(done["train_meta"], read(root / f"{stage[4:]}.json"))
            require(tree_hashes(directory / "adapter") == done["adapter_hashes"], "fitted adapter drift")
            fits[stage] = done["train_meta"]
        else:
            adapter, hashes = artifact(root, manifest, stage)
            require(done["adapter_hashes"] == hashes and tree_hashes(adapter) == hashes, "read identity mismatch")
            require(file_sha(directory / "eval.json") == done["eval_sha256"], "evaluation drift")
            evaluations[stage] = read(directory / "eval.json")
    cues, bank = read(root / "cues.json"), read(root / "bank.json")
    for evaluation in evaluations.values():
        require([row["cue_id"] for row in evaluation["cues"]] == [cue["cue_id"] for cue in cues], "eval cue coverage")
        require(evaluation["work"] == candidate_work(cues), "candidate work mismatch")
    old_ids = [f"frame|{owner['id']}" for owner in bank["owners"] if owner["dose"] == 16]
    new_ids = [cue["cue_id"] for cue in cues if cue["kind"] == "new_frame"]
    require(len(old_ids) == 16 and len(new_ids) == 32, "descriptive cohort mismatch")
    summaries = {name: md.summarize_eval(dict(evaluation, cues=evaluation["cues"][:OLD_CUES]), bank)
                 for name, evaluation in evaluations.items()}
    gates = {name: md.evaluate_gates(summary, seed=0) for name, summary in summaries.items()}
    before, after = summaries["A1_before"]["per_dose"][16]["d_p"], summaries["A2"]["per_dose"][16]["d_p"]
    native_fraction = after / before if before is not None and after is not None and before > md.GATES["min_gain"] else None
    gates["A2_with_native_fact_retention"] = md.evaluate_gates(summaries["A2"], retention=native_fraction, seed=0)
    pairs = {"OLD_A1_to_A2": ("A1_before", "A2", old_ids), "OLD_AN_to_A2": ("AN", "A2", old_ids),
             "NEW_A1_to_AN": ("A1_before", "AN", new_ids), "NEW_A1_to_A2": ("A1_before", "A2", new_ids),
             "NEW_AN_to_A2": ("AN", "A2", new_ids)}
    descriptions = {name: contrast(evaluations[left], evaluations[right], ids)
                    for name, (left, right, ids) in pairs.items()}
    reload_drift = {side: max(abs(left[side]["p_raw"][answer] - right[side]["p_raw"][answer])
                    for left, right in zip(evaluations["A1_before"]["cues"], evaluations["A1_after"]["cues"])
                    for answer in left[side]["p_raw"]) for side in ("OFF", "ON")}
    payload = dict(manifest_sha256=manifest_sha256, starting_state=STARTING_STATE,
                   lineage=manifest["lineage"], pins=manifest["pins"], sources=manifest["sources"],
                   native_old_summaries=summaries, native_old_gates=gates,
                   native_fact_retention_fraction=native_fraction, descriptive=descriptions,
                   no_update=dict(max_raw_probability_drift=reload_drift,
                                  exact_scores_equal=evaluations["A1_before"]["cues"] == evaluations["A1_after"]["cues"]),
                   raw_evaluations={name: str(root / "stages" / name / "eval.json") for name in READS},
                   cost=dict(run=finished, fits=fits, new_fit_steps=sum(meta["steps"] for meta in fits.values()),
                             reads={name: {key: evaluation[key] for key in ("work", "measured_work", "scorer_calls", "boundary_straddles")}
                                    for name, evaluation in evaluations.items()}),
                   limitations=["No automatic promotion or new pass threshold; native failures remain failures.",
                                "NEW null control or reload drift leaves repeated-learning evidence inconclusive.",
                                "AN omission is not forgetting of an inherited tensor state.",
                                "No warm-start, optimizer resume, behavior retention, clean lineage, H1/H2, G3 closure or mechanism freeze.",
                                "Candidate-normalized probabilities are not generated accuracy; costs are not matched."])
    write(Path(report), payload)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare")
    for name in ("out", "original-root", "model", "pins"):
        preparation.add_argument(f"--{name}", required=True)
    for name in ("run", "worker", "reduce"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--manifest-sha256", required=True)
        if name != "reduce":
            command.add_argument("--allow-gpu", action="store_true")
        if name == "run":
            command.add_argument("--lease-cutoff-unix", type=float, required=True)
        elif name == "worker":
            command.add_argument("--stage", choices=STAGES, required=True)
        else:
            command.add_argument("--report", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    result = globals()[command](**args)
    if command != "reduce":
        print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
