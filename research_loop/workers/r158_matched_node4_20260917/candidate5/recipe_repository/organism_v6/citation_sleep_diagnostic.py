"""One selected t02 citation-supervision utility comparison; not parenting.

Prepare (CPU): --source-run RUN --source-preparation PREP --model-path LOCAL
--pins PINS --out NEW. PINS: {"model_path": absolute_path, "files": hash_map}.
Run (Main only): --preparation PREP --out NEW --device GPU --allow-gpu
--lease-deadline-utc ISO_WITH_TIMEZONE. Requires pinned V6_MODEL and offline flags.
Replay (CPU): --analyze RUN --preparation PREP --out NEW.
One shared OFF, two fresh-base fits, then fresh full/syntax ON workers: 24 calls.
OFF and each fit+ON share separate 900s budgets; total work <=2700s, with a
300s outer cleanup reserve (five workers). No retries, promotion or certificates.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import time

from . import constraint_demonstration_diagnostic as demo
from . import train_adapter_v3 as trainer


base = demo.base
require, read, write, sha = demo.require, demo.read, demo.write, demo.sha
SCHEMA = "citation-sleep-v1"
ARMS = ("full", "syntax")
READS = ("off", "full", "syntax")
SOURCE_PREP_SHA = "75c528b40e2884f560214a30bc875fa51cc9ef8223d63fa654d030acae707343"
SOURCE_LOG_SHA = "9a6de4bae98d54927c4d87573083b533dc6b0be0eed444bc631e95241fdcd268"
TARGET_SHA = "019bcf5685a46a2f05be4e32ac4e9f138b71da7b1fd72f38078ed65e32d842bf"
BOARD_SHA = "0b38f1c804b5f458531d544260eb669571ba652108e03dfba669fc7400b45ffc"
PROTOCOL = dict(steps=32, optimizer_seed=1729, generation_seed=7101, temperature=0.0,
                max_tokens=128, cases=8, calls=24, stage_seconds=900, total_seconds=2700,
                cleanup_seconds_per_worker=60, outer_seconds=3000,
                order=["off", "fit_full", "fit_syntax", "full", "syntax"])
BOUNDARY = dict(unique_experiences=1, selected_posthoc=True, training_target="exact citation prefix only",
                parent_lesson_in_sleep=False, own_lesson_in_sleep=False, source_note_in_sleep=False,
                clean_ancestry=False, P1_claim=False, internalization_claim=False, holdout_claim=False,
                syntax_control="same teacher-forced values; different loss mask, not withheld content",
                supervised_token_dose_matched=False, no_update_compute_matched=False,
                whole_record_training_approved=False, automatic_promotion=False)


def digest(path):
    return base.formation._hash(Path(path))


def source_snapshot(run, preparation):
    root, prep = Path(run).resolve(strict=True), Path(preparation).resolve(strict=True)
    require(base.receipts.verify_inventory(prep) == SOURCE_PREP_SHA, "not the selected demonstration preparation")
    log = root / "process" / "generations.jsonl"
    require(digest(log) == SOURCE_LOG_SHA, "selected raw generation receipt differs")
    replay = demo.analyze_pair(root, prep)
    completed = read(root / "COMPLETED.json")
    require(all(completed.get(key) == value for key, value in replay.items()) and not replay["synthetic"],
            "native terminal replay mismatch")
    events = [json.loads(line) for line in log.read_text().splitlines()]
    request, raw, output = events[9:12]
    pairs = read(prep / "pairs.json")
    case = pairs[1]["transfer"]
    require(case["case_id"] == "t02" and case["episode_id"] == "rg/mini_sudoku/1851301"
            and sha(base.formation.policy._encoded(case["candidate"])) == case["candidate_sha256"] == BOARD_SHA,
            "selected actual t02 board differs")
    text = raw["requests"][0]["outputs"][0]["text"]
    require(text == output["text"] and sha(text.encode()) == TARGET_SHA
            and base.score_record(text, case)["whole_structured_record_clean"], "selected child citation invalid")
    return dict(source_run=str(root), source_preparation=str(prep), source_preparation_sha256=SOURCE_PREP_SHA,
                raw_log_sha256=SOURCE_LOG_SHA, request_index=3, raw_return_line=11,
                raw_text_pointer="/requests/0/outputs/0/text", original_raw_text=text,
                output_sha256=TARGET_SHA, original_request=request, original_raw_return=raw,
                bad_source_note=events[8]["text"], source_pair=pairs[1],
                panel=[pair["transfer"] for pair in pairs], source_config=read(prep / "config.json"))


def prefix_and_ranges(text):
    require(sha(text.encode()) == TARGET_SHA, "exact selected raw target required")
    boundary = text.index(',"lesson":')
    prefix = text[:boundary]
    require(prefix.isascii() and prefix.endswith("}]") and "lesson" not in prefix, "citation prefix boundary differs")
    case = re.search(r'"case_id":"([^"]+)"', prefix)
    group = re.search(r'"group":"([^"]+)"', prefix)
    cells = re.search(r'"cells":(\[\[\d,\d\],\[\d,\d\]\])', prefix)
    digit = re.search(r'"digit":(\d)', prefix)
    require(all((case, group, cells, digit)), "unexpected selected citation syntax")
    case_ranges = [list(case.span(1))]
    content_ranges = [list(group.span(1)), list(digit.span(1))]
    content_ranges.extend([[cells.start(1)+match.start(), cells.start(1)+match.end()]
                           for match in re.finditer(r"\d", cells.group(1))])
    return prefix, dict(case=case_ranges, content=content_ranges, end_byte=boundary)


def prompt_for(case):
    board = "\n".join(" ".join(map(str, row)) for row in case["candidate"])
    return f"{base.TASK}\n\ncase_id: {case['case_id']}\nCandidate:\n{board}"


def request_for(case, tokenizer):
    prompt = prompt_for(case)
    rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)], tokenize=False, add_generation_prompt=True)
    ids = tokenizer.encode(rendered, add_special_tokens=False)
    require(ids and len(ids) + 128 <= 4096, "evaluation truncation/headroom failure")
    return dict(case_id=case["case_id"], prompt=prompt, rendered_prompt=rendered,
                prompt_sha256=sha(prompt.encode()), rendered_sha256=sha(rendered.encode()),
                prompt_token_ids=ids, prompt_tokens=len(ids), seed=7101, temperature=0.0, max_tokens=128)


def token_preflight(provenance, tokenizer):
    prefix, ranges = prefix_and_ranges(provenance["original_raw_text"])
    panel = provenance["panel"]
    require([case["case_id"] for case in panel] == [f"t{index:02}" for index in range(1, 9)]
            and [case["episode_id"] for case in panel] == list(demo.TRANSFER_IDS), "fixed transfer panel/order required")
    require(sha(base.formation.policy._encoded(panel[1]["candidate"])) == BOARD_SHA, "t02 board hash differs")
    require(base.score_record(provenance["original_raw_text"], panel[1])["whole_structured_record_clean"], "t02 citation invalid")
    requests = [request_for(case, tokenizer) for case in panel]
    rendered = requests[1]["rendered_prompt"]
    tokenized = tokenizer(prefix, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = list(tokenized["input_ids"]), [list(value) for value in tokenized["offset_mapping"]]
    require(ids == tokenizer.encode(prefix, add_special_tokens=False) and len(ids) == len(offsets) and ids,
            "real tokenizer offsets required")
    partition = []
    cursor = 0
    for token_id, (start, end) in zip(ids, offsets):
        require(start == cursor and end > start and end <= len(prefix), "overlapping/gapped token offsets; no salvage")
        text = prefix[start:end]
        require(tokenizer.encode(text, add_special_tokens=False) == [token_id], "partition retokenization differs")
        overlap = lambda intervals: any(start < right and end > left for left, right in intervals)
        full = not overlap(ranges["case"])
        syntax = full and not overlap(ranges["content"])
        partition.append(dict(start_byte=start, end_byte=end, text=text, token_id=token_id, full=full, syntax=syntax))
        cursor = end
    require(cursor == len(prefix), "prefix token coverage incomplete")
    whole_ids = tokenizer.encode(rendered + prefix, add_special_tokens=False)
    require(whole_ids == requests[1]["prompt_token_ids"] + ids and len(whole_ids) <= 4096,
            "cross-prompt retokenization or truncation; reject rather than rerender")
    corpora, proof = {}, {}
    for arm in ARMS:
        spans = [[rendered, False, "context"]] + [[row["text"], row[arm], "own_citation_prefix"] for row in partition]
        corpus = dict(recipe=trainer.RECIPE, corpus=[dict(spans=spans, group="selected-t02", view=arm,
                      category="own_citation_prefix", order=0)], unique_experiences=1, explicit_presentations=32)
        item = trainer.normalize_items(corpus)[0]
        segments = trainer.encode_item_segments(item, tokenizer, 4096, chat_template=False, add_eos=False, overflow="split")
        require(len(segments) == 1, "one unsplit sequence required")
        segment = segments[0]
        expected_labels = [trainer.IGNORE]*len(requests[1]["prompt_token_ids"]) + [row["token_id"] if row[arm] else trainer.IGNORE for row in partition]
        require(segment.ids == whole_ids and segment.labels == expected_labels and segment.n_target > 0
                and segment.context_dropped == segment.target_dropped == 0, "actual trainer mask/token/truncation mismatch")
        corpora[arm] = corpus
        proof[arm] = dict(input_ids=segment.ids, labels=segment.labels, input_tokens=len(segment.ids),
                          supervised_tokens=segment.n_target, train_tokens_seen=32*len(segment.ids))
    require(proof["full"]["input_ids"] == proof["syntax"]["input_ids"] and
            proof["full"]["supervised_tokens"] > proof["syntax"]["supervised_tokens"] > 0,
            "nonempty differential citation supervision required")
    return corpora, dict(prefix=prefix, prefix_sha256=sha(prefix.encode()), ranges=ranges, partition=partition,
                         proof=proof, evaluation_requests=requests, eos_appended=False, continuation_present=False,
                         tokenizer_policy="whole-prefix offsets; any overlap with excluded value masks the entire token")


def source_pins():
    modules = (demo, base, trainer, base.model_backend, base.supervisor, base.receipts, base.formation)
    return {str(Path(module.__file__).resolve()): digest(module.__file__) for module in modules} | {str(Path(__file__).resolve()): digest(__file__)}


def prepare(out, source_run, source_preparation, model_path, expected_files, *, tokenizer=None):
    provenance = source_snapshot(source_run, source_preparation)
    model = Path(model_path).resolve(strict=True)
    synthetic = tokenizer is not None
    require(base.formation.local_files(model) == expected_files == provenance["source_config"]["expected_files"], "local base/source pins differ")
    require(provenance["source_config"]["task"] == base.TASK, "frozen common task differs")
    tokenizer = tokenizer if tokenizer is not None else base._load_tokenizer(str(model))
    corpora, check = token_preflight(provenance, tokenizer)
    root = base.receipts.fresh_output(out, [source_run, source_preparation, model, Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    config = dict(schema=SCHEMA, protocol=PROTOCOL, boundary=BOUNDARY, task=base.TASK, model_path=str(model),
                  expected_files=expected_files, sources=source_pins(), synthetic=synthetic)
    write(root / "config.json", config)
    write(root / "provenance.json", provenance)
    write(root / "panel.json", provenance["panel"])
    write(root / "preflight.json", check)
    for arm in ARMS:
        write(root / f"{arm}.corpus.json", corpora[arm])
    base.receipts.seal(root)
    return dict(status="SYNTHETIC_CPU_ONLY" if synthetic else "READY", preparation=str(root),
                preparation_sha256=base.receipts.verify_inventory(root), target_sha256=check["prefix_sha256"],
                input_token_parity=True, supervised_tokens={arm:check["proof"][arm]["supervised_tokens"] for arm in ARMS})


def load_preparation(preparation, *, native=False, tokenizer=None):
    prep = Path(preparation).resolve(strict=True)
    checksum = base.receipts.verify_inventory(prep)
    config, provenance, check = (read(prep / name) for name in ("config.json", "provenance.json", "preflight.json"))
    require(config["schema"] == SCHEMA and config["protocol"] == PROTOCOL and config["boundary"] == BOUNDARY
            and config["task"] == base.TASK, "preparation config drift")
    prefix, ranges = prefix_and_ranges(provenance["original_raw_text"])
    require(check["prefix"] == prefix and check["ranges"] == ranges and read(prep/"panel.json") == provenance["panel"], "prefix/panel drift")
    for arm in ARMS:
        corpus = read(prep / f"{arm}.corpus.json")
        spans = corpus["corpus"][0]["spans"]
        require(len(corpus["corpus"]) == 1 and spans[0] == [check["evaluation_requests"][1]["rendered_prompt"], False, "context"]
                and spans[1:] == [[row["text"], row[arm], "own_citation_prefix"] for row in check["partition"]]
                and "".join(span[0] for span in spans[1:]) == prefix, "sleep bytes or masks changed")
    if native:
        require(not config["synthetic"], "synthetic preparation cannot launch")
        require(base.formation.local_files(config["model_path"]) == config["expected_files"], "base hashes changed")
        require(all(digest(path) == expected for path, expected in config["sources"].items()), "implementation source changed")
    if tokenizer is not None:
        corpora, actual = token_preflight(provenance, tokenizer)
        require(actual == check and all(corpora[arm] == read(prep/f"{arm}.corpus.json") for arm in ARMS), "runtime tokenizer changed")
    return prep, checksum, config, provenance["panel"], check


def training_spec(prep, output, arm, config):
    require(arm in ARMS, "unknown fit")
    command = [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus", str(prep/f"{arm}.corpus.json"),
               "--out", str(output), "--model", config["model_path"], "--rank", "8", "--alpha", "16",
               "--dropout", "0.05", "--lr", "1e-4", "--optimizer", "adamw", "--batch-size", "1", "--grad-accum", "1",
               "--epochs", "32", "--max-steps", "32", "--seed", "1729", "--max-len", "4096", "--no-pack",
               "--no-shuffle-groups", "--no-eos", "--target-modules", ",".join(trainer.ALL_PROJ),
               "--layers", "all", "--overflow", "split", "--device", "cuda", "--dtype", "bf16"]
    actual = asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:])))
    require(not actual["add_eos"] and not actual["chat_template"] and actual["grad_checkpoint"], "trainer configuration mismatch")
    return dict(argv=command, config=actual, corpus_sha256=digest(prep/f"{arm}.corpus.json"), fresh_base=True)


def verify_fit(adapter, spec, proof):
    adapter = Path(adapter)
    manifest = read(adapter/"train_manifest.json")
    require((adapter/"DONE").is_file() and not (adapter/"EMPTY_CORPUS").exists()
            and manifest["config"] == spec["config"] and manifest["steps"] == manifest["micro_batches"] == 32
            and manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"]), "wrong/incomplete/nonfinite fit")
    require(manifest["base_model"] == spec["config"]["model"] and manifest["corpus"]["sha256"] == spec["corpus_sha256"]
            and manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == 1
            and manifest["corpus"]["n_skipped_no_target"] == 0, "fit corpus/base differs")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit truncation/splitting")
    require(manifest["tokens"]["total"] == proof["input_tokens"] and manifest["tokens"]["target"] == proof["supervised_tokens"]
            and manifest["train_tokens_seen"] == proof["train_tokens_seen"], "fit token dose differs")
    saved = read(adapter/"adapter_config.json")
    require(saved["r"] == 8 and saved["lora_alpha"] == 16 and saved["lora_dropout"] == .05
            and set(saved["target_modules"]) == set(trainer.ALL_PROJ), "saved LoRA differs")
    identity = base.model_backend.configured_generation_identity(spec["config"]["model"], str(adapter))
    return dict(manifest_sha256=digest(adapter/"train_manifest.json"), adapter_files=identity["adapter_files"],
                steps=32, input_tokens=manifest["train_tokens_seen"], supervised_tokens_per_presentation=proof["supervised_tokens"])


@contextmanager
def local_backend(model_path, adapter):
    require(base.model_backend.MODEL == os.environ.get("V6_MODEL") == model_path, "set pinned V6_MODEL before Python")
    require(os.environ.get("HF_HUB_OFFLINE") == os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline environment required")
    model = base.model_backend.VLLMBackend(adapter_path=adapter)
    try:
        yield model
    finally:
        require(base.model_backend.close_backend(model), "backend cleanup failed")


class Capture(base.CaptureBackend):
    def __init__(self, model, model_path, out, adapter, *, synthetic=False):
        super().__init__(model, model_path, out, "", synthetic=synthetic)
        self.identity = base.model_backend.configured_generation_identity(model_path, adapter)

    def generate_record(self, row):
        self.generation_identity()
        self._append([dict(kind="request", request_index=self.requests, source_identity=self.identity, **row)])
        if self.synthetic:
            outputs = self.model.batch([row["prompt"]], max_tokens=128, temperature=0.0, seeds=[7101])
            self._append([dict(kind="raw_return", request_index=self.requests, synthetic=True, outputs=outputs)])
            require(len(outputs) == 1 and isinstance(outputs[0], str), "synthetic output cardinality")
            text = outputs[0]
            metadata = dict(actual_prompt_tokens=None, actual_output_tokens=None, finish_reason="synthetic_fixture",
                            stop_reason=None, usage_source="SYNTHETIC_NOT_ACTUAL_USAGE")
        else:
            from vllm import SamplingParams
            params = SamplingParams(max_tokens=128, temperature=0.0, seed=7101)
            lora = self.model._LoRARequest("life", 1, self.model.adapter_path) if self.model.adapter_path else None
            requests = self.model.llm.generate([row["rendered_prompt"]], [params], lora_request=lora, use_tqdm=False)
            raw = [dict(request_id=request.request_id, prompt=request.prompt, prompt_token_ids=list(request.prompt_token_ids),
                        finished=request.finished, outputs=[dict(text=output.text, token_ids=list(output.token_ids),
                        finish_reason=output.finish_reason, stop_reason=output.stop_reason) for output in request.outputs]) for request in requests]
            self._append([dict(kind="raw_return", request_index=self.requests, synthetic=False, requests=raw)])
            require(len(raw) == 1 and len(raw[0]["outputs"]) == 1, "native cardinality mismatch")
            output = raw[0]["outputs"][0]
            text = output["text"]
            metadata = dict(actual_prompt_tokens=len(raw[0]["prompt_token_ids"]), actual_output_tokens=len(output["token_ids"]),
                            finish_reason=output["finish_reason"], stop_reason=output["stop_reason"], usage_source="NATIVE_VLLM_TOKEN_IDS")
        capture = dict(request_index=self.requests, case_id=row["case_id"], text=text, output_sha256=sha(text.encode()),
                       input_truncated=False, output_rewritten=False, **metadata)
        self._append([dict(kind="output", **capture)])
        self.requests += 1
        if not self.synthetic:
            require(raw[0]["finished"] and raw[0]["prompt"] == row["rendered_prompt"]
                    and raw[0]["prompt_token_ids"] == row["prompt_token_ids"]
                    and output["finish_reason"] == "stop" and len(output["token_ids"]) <= 128
                    and all(type(token) is int and token >= 0 for token in output["token_ids"]),
                    "native protocol failure (raw preserved); no truncation success")
        return capture


def counts(records):
    result = {}
    for label, selected in (("all8", records), ("t02", [row for row in records if row["case_id"] == "t02"]),
                            ("other7_exposed_development", [row for row in records if row["case_id"] != "t02"])):
        result[label] = dict(denominator=len(selected), **{key:sum(int(row["score"][key]) for row in selected) for key in
                            ("grounded", "format_valid", "valid_citations", "invalid_citations", "whole_structured_record_clean")})
    return result


def evaluate(preparation, out, condition, *, adapter=None, backend_factory=local_backend, allow_synthetic=False):
    require(condition in READS and ((condition == "off") == (adapter is None)), "OFF/ON adapter selection differs")
    prep, checksum, config, panel, check = load_preparation(preparation, native=not allow_synthetic)
    require(allow_synthetic or backend_factory is local_backend, "native local backend required")
    require(not config["synthetic"] or allow_synthetic, "synthetic worker forbidden")
    root = base.receipts.fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]] + ([adapter] if adapter else []))
    root.mkdir(parents=True)
    write(root/"runtime.json", dict(base.runtime(), generation_seed=7101, optimizer_seed=1729))
    try:
        with backend_factory(config["model_path"], adapter) as model:
            load_preparation(prep, tokenizer=model.tok)
            capture = Capture(model, config["model_path"], root, adapter, synthetic=config["synthetic"])
            records = []
            for case, request in zip(panel, check["evaluation_requests"]):
                output = capture.generate_record(request)
                records.append(dict(case_id=case["case_id"], capture=output, score=base.score_record(output["text"], case)))
        require(capture.requests == 8, "exactly eight reads required")
        result = dict(status="COMPLETE", condition=condition, preparation_sha256=checksum, synthetic=config["synthetic"],
                      identity=capture.identity, generation_calls=8, records=records, counts=counts(records))
        write(root/"results.json", result)
        return result
    except BaseException as error:
        write(root/"FAILED.json", dict(error=repr(error), raw_outputs="preserved when returned"))
        raise
    finally:
        base.receipts.seal(root)


def lease_check(deadline, required_seconds):
    parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "lease deadline must include timezone")
    require((parsed - datetime.now(timezone.utc)).total_seconds() > required_seconds, "insufficient lease/cleanup headroom")


def execute(preparation, out, device, lease_deadline):
    with base.time_budget(PROTOCOL["outer_seconds"]):
        return _execute(preparation, out, device, lease_deadline)


def _execute(preparation, out, device, lease_deadline):
    prep, checksum, config, _, check = load_preparation(preparation, native=True)
    require(base.supervisor.selected_device() == device and os.environ.get("V6_MODEL") == base.model_backend.MODEL == config["model_path"],
            "explicit reserved device and pinned V6_MODEL required")
    require(os.environ.get("HF_HUB_OFFLINE") == os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline environment required")
    lease_check(lease_deadline, PROTOCOL["outer_seconds"])
    root = base.receipts.fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    started = time.monotonic()
    write(root/"STARTED.json", dict(preparation=str(prep), preparation_sha256=checksum, protocol=PROTOCOL,
                                   device=device, lease_deadline_utc=lease_deadline, runtime=base.runtime()))
    used = {key:0.0 for key in READS}
    try:
        for stage in PROTOCOL["order"]:
            group = stage.removeprefix("fit_")
            remaining = min(900-used[group]-60, 2700-(time.monotonic()-started)-60)
            require(remaining > 0, "stage/total deadline exhausted; no retry")
            lease_check(lease_deadline, remaining+60)
            require(base.supervisor.selected_device() == device, "device reservation selector changed")
            output = root/stage
            require(not output.exists() and not output.is_symlink(), "worker output already exists")
            if stage.startswith("fit_"):
                spec = training_spec(prep, output, group, config)
                write(root/f"{stage}.command.json", spec)
                command = spec["argv"]
            else:
                command = [sys.executable, "-B", "-m", "organism_v6.citation_sleep_diagnostic", "--preparation", str(prep),
                           "--out", str(output), "--condition", stage, "--device", device,
                           "--lease-deadline-utc", lease_deadline, "--allow-gpu"]
                if stage != "off":
                    adapter = root/f"fit_{stage}"
                    base.receipts.verify_inventory(adapter)
                    command += ["--adapter", str(adapter)]
            before = time.monotonic()
            base.supervisor.run_worker(command, log_path=root/f"{stage}.log", timeout=remaining, device=device)
            used[group] += time.monotonic()-before
            require(used[group] < 900, "stage incl cleanup exceeds budget")
            if stage.startswith("fit_"):
                receipt = verify_fit(output, spec, check["proof"][group])
                write(output/"fit_receipt.json", receipt)
                base.receipts.seal(output)
        result = analyze(root, prep)
        require(time.monotonic()-started < 2700, "total stage budget exhausted")
        result.update(elapsed_seconds=time.monotonic()-started, stage_seconds=used)
        write(root/"COMPLETED.json", result)
        return result
    except BaseException as error:
        write(root/"FAILED.json", dict(error=repr(error), retry=False))
        raise
    finally:
        for path in root.iterdir():
            if path.is_file():
                path.chmod(0o444)
        root.chmod(0o555)


def analyze(run, preparation):
    root = Path(run).resolve(strict=True)
    prep, checksum, config, panel, check = load_preparation(preparation)
    require(not (root/"FAILED.json").exists(), "failed run cannot be complete")
    started = read(root/"STARTED.json")
    require(started["preparation_sha256"] == checksum and started["protocol"] == PROTOCOL, "run preparation/protocol differs")
    fits, readings, pids = {}, {}, []
    for arm in ARMS:
        adapter = root/f"fit_{arm}"
        base.receipts.verify_inventory(adapter)
        spec = read(root/f"fit_{arm}.command.json")
        expected = training_spec(prep, adapter, arm, config)
        require(spec["config"] == expected["config"] and spec["corpus_sha256"] == expected["corpus_sha256"], "fit command/config differs")
        fits[arm] = verify_fit(adapter, spec, check["proof"][arm])
        require(fits[arm] == read(adapter/"fit_receipt.json"), "fit receipt differs")
    for condition in READS:
        folder = root/condition
        base.receipts.verify_inventory(folder)
        result = read(folder/"results.json")
        require(not (folder/"FAILED.json").exists() and result["status"] == "COMPLETE" and result["condition"] == condition
                and result["generation_calls"] == len(result["records"]) == 8
                and result["preparation_sha256"] == checksum and result["synthetic"] == config["synthetic"], "read completion differs")
        runtime = read(folder/"runtime.json")
        pids.append(runtime["pid"])
        require(runtime["generation_seed"] == 7101, "read seed differs")
        identity = result["identity"]
        require(identity["model_input"] == config["model_path"] and identity["adapter_files"] ==
                ({} if condition == "off" else fits[condition]["adapter_files"])
                and ((identity["adapter_input"] is None) == (condition == "off")), "actual adapter/base identity differs")
        events = [json.loads(line) for line in (folder/"generations.jsonl").read_text().splitlines()]
        require([event["kind"] for event in events] == ["request", "raw_return", "output"]*8, "read call cardinality differs")
        records, prompt_tokens, output_tokens = [], 0, 0
        for index, (case, expected) in enumerate(zip(panel, check["evaluation_requests"])):
            request, raw, output = events[index*3:index*3+3]
            require(request == dict(kind="request", request_index=index, source_identity=identity, **expected)
                    and raw["request_index"] == output["request_index"] == index and raw["synthetic"] == config["synthetic"], "read request differs")
            if config["synthetic"]:
                require(raw["outputs"] == [output["text"]] and output["actual_output_tokens"] is None, "synthetic raw differs")
            else:
                require(len(raw["requests"]) == len(raw["requests"][0]["outputs"]) == 1, "native cardinality")
                native = raw["requests"][0]
                response = native["outputs"][0]
                require(native["finished"] and native["prompt"] == expected["rendered_prompt"]
                        and native["prompt_token_ids"] == expected["prompt_token_ids"]
                        and response["text"] == output["text"] and response["finish_reason"] == output["finish_reason"] == "stop"
                        and response["stop_reason"] == output["stop_reason"] and len(response["token_ids"]) == output["actual_output_tokens"] <= 128
                        and len(native["prompt_token_ids"]) == output["actual_prompt_tokens"], "native text/stop/token mismatch")
                prompt_tokens += output["actual_prompt_tokens"]
                output_tokens += output["actual_output_tokens"]
            require(output["output_sha256"] == sha(output["text"].encode()) and output["case_id"] == case["case_id"]
                    and not output["input_truncated"] and not output["output_rewritten"], "output hash/case/rewriting differs")
            record = dict(case_id=case["case_id"], capture={key:value for key,value in output.items() if key != "kind"},
                          score=base.score_record(output["text"], case))
            require(record == result["records"][index], "summary/raw differs")
            records.append(record)
        require(counts(records) == result["counts"], "read totals differ")
        readings[condition] = dict(counts=counts(records), records=records,
                                   actual_prompt_tokens=None if config["synthetic"] else prompt_tokens,
                                   actual_output_tokens=None if config["synthetic"] else output_tokens)
    require(config["synthetic"] or len(set(pids)) == 3, "three fresh read processes required")
    for stage in PROTOCOL["order"]:
        cleanup = read(root/f"{stage}.cleanup.json")
        require(cleanup["cleanup_error"] is None and cleanup["owned_group_empty"] and cleanup["gpu_processes_absent"]
                and cleanup["reservation_release_verified"] and cleanup["device"] == started["device"], "cleanup unverified")
    changes = {arm:[dict(case_id=case["case_id"], off=readings["off"]["records"][index]["score"]["grounded"],
                        on=readings[arm]["records"][index]["score"]["grounded"],
                        output_equal=readings[arm]["records"][index]["capture"]["text"] == readings["off"]["records"][index]["capture"]["text"])
                   for index,case in enumerate(panel)] for arm in ARMS}
    gain = {arm:{subset:readings[arm]["counts"][subset]["grounded"]-readings["off"]["counts"][subset]["grounded"]
                 for subset in readings["off"]["counts"]} for arm in ARMS}
    return dict(status="COMPLETE", schema=SCHEMA, boundary=BOUNDARY, calls=24, fits=fits, reads=readings,
                per_case=changes, gain_vs_shared_off=gain,
                full_minus_syntax={key:gain["full"][key]-gain["syntax"][key] for key in gain["full"]},
                optimizer_seed=1729, generation_seed=7101, synthetic=config["synthetic"],
                replay_scope="captured inventories/raw native returns; remote absolute paths and current GPU state not authenticated")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("out", "source-run", "source-preparation", "model-path", "pins", "preparation", "analyze", "adapter", "device", "lease-deadline-utc"):
        parser.add_argument("--"+name, required=name == "out")
    parser.add_argument("--condition", choices=READS)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.analyze:
        require(args.preparation and not any((args.allow_gpu, args.condition, args.adapter, args.source_run, args.source_preparation,
                                              args.model_path, args.pins, args.device, args.lease_deadline_utc)), "CPU replay only")
        result = analyze(args.analyze, args.preparation)
        root = base.receipts.fresh_output(args.out, [args.analyze, args.preparation, Path(__file__).resolve().parents[1]])
        root.mkdir(parents=True)
        write(root/"analysis.json", result)
        base.receipts.seal(root)
    elif args.preparation:
        require(args.allow_gpu and args.device and args.lease_deadline_utc and not any((args.source_run, args.source_preparation, args.model_path, args.pins)), "Main GPU opt-in, device and lease required")
        require(base.supervisor.selected_device() == args.device, "device selector mismatch")
        if args.condition:
            lease_check(args.lease_deadline_utc, 60)
            with base.time_budget(900):
                result = evaluate(args.preparation, args.out, args.condition, adapter=args.adapter)
        else:
            require(args.adapter is None, "controller starts from fresh base")
            result = execute(args.preparation, args.out, args.device, args.lease_deadline_utc)
    else:
        require(args.source_run and args.source_preparation and args.model_path and args.pins
                and not any((args.allow_gpu, args.condition, args.adapter, args.device, args.lease_deadline_utc)), "CPU preparation inputs required")
        pins = read(args.pins)
        require(pins["model_path"] == str(Path(args.model_path).resolve(strict=True)), "pins path mismatch")
        result = prepare(args.out, args.source_run, args.source_preparation, args.model_path, pins["files"])
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
