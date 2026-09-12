"""Canary custody only; an observer for run_life_v2.format_canary, not an evaluator.

Main must check_setup() with the evaluator's actual setup values, supply the
real active drivers/prompts to batch(), call finish_round()
after their consume() calls, and write() before renaming CANDIDATE. The existing
regex, zip denominator, early exits and generation defaults are preserved.
No episode scores are computed, synthesized or used here. Prompt strings are
the actual batch user inputs, not claimed post-chat-template model token inputs.
Configured backend identity is checked against disk, not authenticated GPU state.

Publish outside the adapter: sdir/canary_selection/{trace,receipt,selected}.json. The trace
is a separate selection source, never training-ledger evidence. Receipt publication
is exclusive and read-only; selected.json is the durable selection intent written
last. Interrupted directories cannot be overwritten.
The returned receipt SHA256 must be durably selected before final DONE and supplied
to verify_selection, including during lineage replay. Self-consistent caller data
or a newly computed hash is not an independent historical trust anchor.
"""
from __future__ import annotations

from functools import wraps
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re

from . import life_lineage as custody
from .model_backend import configured_generation_identity


PATTERN = r"^ACT:\s*\S"
SCHEMA = "nursery-canary-selection-v1"
TRACE_SCHEMA = "nursery-canary-trace-v1"


class SelectionReceiptError(ValueError):
    """Missing, changed, ambiguous or contradictory selection evidence."""


def _require(condition, message):
    if not condition:
        raise SelectionReceiptError(message)


def _api(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except SelectionReceiptError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
            raise SelectionReceiptError(str(error)) from error
    return checked


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"


def _sha(content):
    return hashlib.sha256(content).hexdigest()


def _copy(value):
    return json.loads(_encoded(value))


def _same(left, right):
    return _encoded(left) == _encoded(right)


def _fields(value, fields):
    _require(isinstance(value, dict) and set(value) == set(fields), "missing or unknown evidence fields")


def _hash(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "invalid SHA256")
    return value


def _load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "duplicate evidence key")
            result[key] = value
        return result

    content = custody._read(path)
    value = json.loads(content, object_pairs_hook=unique)
    _require(_encoded(value) == content, "noncanonical evidence bytes")
    return content, value


@_api
def evaluation_config(gym, threshold=0.5):
    """Capture actual current canary configuration; never run or score an episode."""
    from . import run_life_v2
    from .batch_loop import driver_class_for

    driver = driver_class_for(gym)
    config = dict(gym=gym.name, episode_ids=list(gym.canary_set()), birth_prompt=gym.birth_prompt(),
                  threshold=threshold, rounds=3, budget_ticks=3, seed_base=4242,
                  pattern=PATTERN, flags="MULTILINE", denominator="zip(active, outputs)",
                  prompt_scope="batch_user_text_before_chat_template",
                  max_tokens=400, temperature=0.7,
                  driver=f"{driver.__module__}.{driver.__qualname__}",
                  evaluator_sha256=_sha(inspect.getsource(run_life_v2.format_canary).encode()),
                  driver_module_sha256=custody._hash_file(Path(inspect.getfile(driver))),
                  gym_module_sha256=custody._hash_file(Path(inspect.getfile(type(gym)))))
    _validate_config(config)
    return config


def _validate_config(config):
    _fields(config, ("gym", "episode_ids", "birth_prompt", "threshold", "rounds", "budget_ticks",
                     "seed_base", "pattern", "flags", "denominator", "prompt_scope", "max_tokens",
                     "temperature", "driver", "evaluator_sha256", "driver_module_sha256",
                     "gym_module_sha256"))
    fixed = dict(rounds=3, budget_ticks=3, seed_base=4242, pattern=PATTERN, flags="MULTILINE",
                 denominator="zip(active, outputs)", prompt_scope="batch_user_text_before_chat_template",
                 max_tokens=400, temperature=0.7)
    _require(all(_same(config[key], value) for key, value in fixed.items()), "changed canary semantics")
    _require(type(config["threshold"]) in (int, float) and math.isfinite(config["threshold"]),
             "invalid canary threshold")
    _require(isinstance(config["episode_ids"], list)
             and all(isinstance(value, str) and value for value in config["episode_ids"]),
             "invalid canary episode IDs")
    for field in ("gym", "birth_prompt", "driver"):
        _require(isinstance(config[field], str), "invalid canary configuration text")
    _require(config["driver"] in ("organism_v6.batch_loop.EpisodeDriver",
                                   "organism_v6.batch_loop.NoEndTokenDriver"), "unsupported canary driver")
    for field in ("evaluator_sha256", "driver_module_sha256", "gym_module_sha256"):
        _hash(config[field])


def _adapter_files(adapter_dir):
    names = custody._names(adapter_dir)
    weights = names & {"adapter_model.safetensors", "adapter_model.bin"}
    _require(len(weights) == 1 and "adapter_config.json" in names, "ambiguous/missing adapter inputs")
    _require(names <= weights | {"adapter_config.json", "README.md", "train_meta.json",
                                 "CANDIDATE", "DONE", "REJECTED_CANARY"}, "unknown adapter input")
    return {name: custody._hash_file(adapter_dir / name)
            for name in sorted(weights | {"adapter_config.json"})}


def _marker(adapter_dir, stage):
    names = custody._names(adapter_dir)
    markers = {name for name in names if name in ("CANDIDATE", "DONE") or name.startswith("REJECTED_")}
    _require(markers == {stage}, "selection requires unambiguous " + stage)
    return _sha(custody._read(adapter_dir / stage))


def _summary(config, rounds, complete=True):
    from .batch_loop import _MARK

    _validate_config(config)
    _require(isinstance(rounds, list) and len(rounds) <= 3, "invalid canary round count")
    active = config["episode_ids"]
    parse_ok = total = 0
    for round_index, batch in enumerate(rounds):
        _require(bool(active), "round after all drivers finished")
        _fields(batch, ("episode_ids", "prompts", "prompt_sha256", "outputs", "output_sha256",
                        "seeds", "done_after", "parseable"))
        _require(_same(batch["episode_ids"], active), "active canary episode identity mismatch")
        for text_field, hash_field in (("prompts", "prompt_sha256"), ("outputs", "output_sha256")):
            texts = batch[text_field]
            _require(isinstance(texts, list) and all(isinstance(text, str) for text in texts),
                     "nontext canary batch")
            _require(_same(batch[hash_field], [_sha(text.encode()) for text in texts]),
                     "canary text hash mismatch")
        _require(len(batch["prompts"]) == len(active), "prompt cardinality mismatch")
        _require(_same(batch["seeds"], [4242 + index for index in range(len(active))]),
                 "canary seed mismatch")
        done = batch["done_after"]
        _require(isinstance(done, list) and len(done) == len(active)
                 and all(type(value) is bool for value in done), "invalid driver completion flags")
        consumed = batch["outputs"][:len(active)]
        parsed = [bool(re.search(PATTERN, output, re.M)) for output in consumed]
        _require(_same(batch["parseable"], parsed), "false parseability verdict")
        terminal = [round_index == 2 or (config["driver"].endswith(".EpisodeDriver")
                    and any(mark.group(1) == "DONE" for mark in _MARK.finditer(output)))
                    for output in consumed]
        terminal += [False] * (len(active) - len(consumed))
        _require(_same(done, terminal), "driver completion contradicts frozen canary behavior")
        total += len(consumed)
        parse_ok += sum(parsed)
        active = [episode for episode, finished in zip(active, done) if not finished]
    _require(not complete or len(rounds) == 3 or not active, "incomplete canary evaluation")
    rate = parse_ok / max(1, total)
    return dict(parse_ok=parse_ok, total=total, rate=rate,
                decision="DONE" if rate >= config["threshold"] else "REJECTED_CANARY")


class SelectionRecorder:
    @_api
    def __init__(self, model, *, model_input, adapter_dir, config, previous_manifest_sha256):
        self.model = model
        self.adapter_dir = custody._absolute(adapter_dir)
        self.model_input = str(model_input)
        self.adapter_input = str(adapter_dir)
        self.config = _copy(config)
        _validate_config(self.config)
        self.previous = _hash(previous_manifest_sha256)
        self.marker_sha256 = _marker(self.adapter_dir, "CANDIDATE")
        self.identity = self._identity()
        self.rounds = []
        self.pending = None
        self.setup_checked = False

    @_api
    def check_setup(self, *, episode_ids, birth_prompt, driver, threshold):
        """Observe the evaluator's actual setup values before creating its drivers."""
        _require(not self.setup_checked, "canary setup already recorded")
        _require(_same(list(episode_ids), self.config["episode_ids"])
                 and _same(birth_prompt, self.config["birth_prompt"])
                 and _same(threshold, self.config["threshold"])
                 and f"{driver.__module__}.{driver.__qualname__}" == self.config["driver"],
                 "actual evaluator setup differs from selected config")
        self.setup_checked = True

    def _identity(self):
        files = _adapter_files(self.adapter_dir)
        expected = configured_generation_identity(self.model_input, self.adapter_input)
        reported = _copy(self.model.generation_identity())
        _require(_same(reported, expected) and reported["adapter_files"] == files,
                 "backend/candidate identity mismatch")
        return reported

    @_api
    def batch(self, drivers, prompts, seeds):
        _require(self.setup_checked, "actual canary setup not recorded")
        _require(self.pending is None and len(self.rounds) < 3, "unfinished or excess canary round")
        _require(_same(self._identity(), self.identity), "candidate identity changed")
        ids = [driver.ep.eid for driver in drivers]
        expected = (self.config["episode_ids"] if not self.rounds else
                    [episode for episode, done in zip(self.rounds[-1]["episode_ids"],
                                                       self.rounds[-1]["done_after"]) if not done])
        _require(ids and ids == expected and len(prompts) == len(ids), "active driver mismatch")
        _require(all(isinstance(prompt, str) for prompt in prompts), "nontext canary prompt")
        _require(_same(seeds, [4242 + index for index in range(len(ids))]), "canary seed mismatch")
        inputs, requested_seeds = list(prompts), list(seeds)
        outputs = self.model.batch(prompts, seeds=seeds)
        _require(isinstance(outputs, (list, tuple)) and all(isinstance(output, str) for output in outputs),
                 "nontext canary output")
        _require(_same(self._identity(), self.identity), "candidate identity changed during generation")
        self.pending = dict(episode_ids=ids, prompts=inputs, seeds=requested_seeds, outputs=list(outputs),
                            prompt_sha256=[_sha(text.encode()) for text in inputs],
                            output_sha256=[_sha(text.encode()) for text in outputs],
                            parseable=[bool(re.search(PATTERN, output, re.M)) for output in outputs[:len(ids)]])
        return outputs

    @_api
    def finish_round(self, drivers):
        _require(self.pending is not None, "no pending canary round")
        _require([driver.ep.eid for driver in drivers] == self.pending["episode_ids"],
                 "completed driver identity mismatch")
        batch = dict(self.pending, done_after=[driver.done for driver in drivers])
        _summary(self.config, self.rounds + [batch], complete=False)
        self.rounds.append(batch)
        self.pending = None

    @_api
    def write(self, directory, *, ok, rate):
        _require(self.setup_checked, "actual canary setup not recorded")
        _require(self.pending is None, "unfinished canary round")
        summary = _summary(self.config, self.rounds)
        _require(type(ok) is bool and ok == (summary["decision"] == "DONE")
                 and type(rate) in (int, float) and _same(rate, summary["rate"]), "false canary verdict")
        _require(_same(self._identity(), self.identity), "candidate identity changed before selection")
        _require(_marker(self.adapter_dir, "CANDIDATE") == self.marker_sha256, "candidate marker changed")
        directory = custody._absolute(directory)
        _require(directory.parent == self.adapter_dir.parent and directory != self.adapter_dir,
                 "selection evidence must be a sibling of the candidate adapter")
        trace = _encoded(dict(schema=TRACE_SCHEMA, rounds=self.rounds))
        receipt = dict(schema=SCHEMA, candidate=self.identity, candidate_sha256=_sha(_encoded(self.identity)),
                       candidate_marker_sha256=self.marker_sha256, previous_manifest_sha256=self.previous,
                       config=self.config, config_sha256=_sha(_encoded(self.config)),
                       trace_sha256=_sha(trace), **summary)
        content = _encoded(receipt)
        _require(max(len(trace), len(content)) <= custody.MAX_TEXT_BYTES, "selection evidence too large")
        custody._mkdir(directory)
        custody._write(directory / "trace.json", trace)
        _require(_same(self._identity(), self.identity), "candidate changed during selection publication")
        _require(_marker(self.adapter_dir, "CANDIDATE") == self.marker_sha256, "candidate marker changed")
        digest = custody._write(directory / "receipt.json", content)
        selected = dict(schema="nursery-canary-selected-v1", receipt_sha256=digest,
                        config=self.config, candidate=self.identity,
                        previous_manifest_sha256=self.previous)
        selected_digest = custody._write(directory / "selected.json", _encoded(selected))
        for path in (directory, directory.parent):
            with custody._directory(path) as descriptor:
                os.fsync(descriptor)
        return dict(receipt_path=str(directory / "receipt.json"), receipt_sha256=digest,
                    selection_path=str(directory / "selected.json"), selection_sha256=selected_digest,
                    trace_path=str(directory / "trace.json"), trace_sha256=_sha(trace), **summary)


@_api
def verify_selection(receipt_path, *, expected_receipt_sha256, adapter_dir, expected_model_input,
                     expected_adapter_input, expected_config, previous_manifest_sha256,
                     stage="CANDIDATE", require_acceptance=True):
    """Verify exact custody bytes and independently recompute the frozen parse verdict.

    stage='DONE' supports post-promotion/snapshotted adapters; expected_adapter_input
    remains the ORIGINAL candidate loader path, not the later snapshot path.
    Caller-selected expected config and digest are mandatory, not self-read pins.
    """
    path, adapter = custody._absolute(receipt_path), custody._absolute(adapter_dir)
    content, receipt = _load(path)
    _require(_sha(content) == _hash(expected_receipt_sha256), "external selection receipt pin mismatch")
    _fields(receipt, ("schema", "candidate", "candidate_sha256", "candidate_marker_sha256",
                      "previous_manifest_sha256", "config", "config_sha256", "trace_sha256",
                      "parse_ok", "total", "rate", "decision"))
    _require(receipt["schema"] == SCHEMA, "unsupported selection receipt")
    _require(receipt["previous_manifest_sha256"] == _hash(previous_manifest_sha256), "wrong predecessor")
    _validate_config(expected_config)
    _require(_same(receipt["config"], expected_config)
             and receipt["config_sha256"] == _sha(_encoded(expected_config)), "evaluation config mismatch")
    identity = receipt["candidate"]
    _require(receipt["candidate_sha256"] == _sha(_encoded(identity)), "candidate hash mismatch")
    _require(identity.get("model_input") == str(expected_model_input)
             and identity.get("adapter_input") == str(expected_adapter_input), "candidate input mismatch")
    files = _adapter_files(adapter)
    expected = configured_generation_identity(str(expected_model_input), str(adapter))
    _require(expected["adapter_files"] == files, "adapter changed during verification")
    expected["adapter_input"] = str(expected_adapter_input)
    _require(_same(identity, expected), "candidate adapter/config identity mismatch")
    _require(stage in ("CANDIDATE", "DONE", "REJECTED_CANARY"), "unsupported selection stage")
    _require(_marker(adapter, stage) == receipt["candidate_marker_sha256"], "candidate marker mismatch")
    trace_bytes, trace = _load(path.parent / "trace.json")
    _require(_sha(trace_bytes) == _hash(receipt["trace_sha256"]), "selection trace hash mismatch")
    _fields(trace, ("schema", "rounds"))
    _require(trace["schema"] == TRACE_SCHEMA, "unsupported selection trace")
    summary = _summary(expected_config, trace["rounds"])
    _require(all(_same(receipt[key], value) for key, value in summary.items()), "false canary verdict")
    _require(stage == "CANDIDATE" or stage == summary["decision"], "marker/verdict mismatch")
    _require(type(require_acceptance) is bool, "invalid acceptance requirement")
    _require(not require_acceptance or summary["decision"] == "DONE", "canary selection rejected")
    return receipt


@_api
def verify_selected(selection_path, *, expected_selection_sha256, adapter_dir,
                    previous_manifest_sha256, expected_model_input=None, expected_adapter_input=None,
                    stage="CANDIDATE", require_acceptance=True):
    """Use a runner-selected or historical manifest-bound intent, never a self-read pin.

    New publication supplies both expected input strings from the actual runner.
    Replay may use the original strings from the externally pinned historical
    intent while checking the copied adapter bytes in adapter_dir.
    """
    path = custody._absolute(selection_path)
    content, selected = _load(path)
    _require(_sha(content) == _hash(expected_selection_sha256), "external selection intent pin mismatch")
    _fields(selected, ("schema", "receipt_sha256", "config", "candidate", "previous_manifest_sha256"))
    _require(selected["schema"] == "nursery-canary-selected-v1", "unsupported selection intent")
    _require(selected["previous_manifest_sha256"] == _hash(previous_manifest_sha256), "wrong selected predecessor")
    identity = selected["candidate"]
    receipt = verify_selection(
        path.parent / "receipt.json", expected_receipt_sha256=selected["receipt_sha256"],
        adapter_dir=adapter_dir, expected_model_input=(identity["model_input"] if expected_model_input is None
                                                     else expected_model_input),
        expected_adapter_input=(identity["adapter_input"] if expected_adapter_input is None
                                else expected_adapter_input), expected_config=selected["config"],
        previous_manifest_sha256=previous_manifest_sha256, stage=stage, require_acceptance=require_acceptance)
    _require(_same(receipt["candidate"], identity), "selected candidate identity mismatch")
    return receipt
