"""Read-only actual-request/raw-record V3 projection; no selection or training.

Main's existing formation audit additionally needs ``record_review`` with
decision="accept", nonempty notes, scope="actual_record_context_and_target",
and selection_sha256=diagnostic.value_hash(the unchanged fixed selection).
This is Main's explicit semantic assessment, never an automatic nonleakage certificate.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import re

from . import rulegame_parenting_diagnostic as diagnostic
from . import train_adapter_v3 as trainer


def _words(text):
    return re.findall(r"\w+", text.casefold())


def _payload_spans(texts, protocol="strict_v1"):
    shared = set(_words(diagnostic.record_instruction(protocol) + " ACT TRY PREDICT T F true false null"))
    shared.update("a an the and or of to in on with is are be your my i it that this".split())
    spans = set()
    for text in texts:
        words = _words(text)
        parts = [text, *re.split(r"\n|(?<=[.!?])\s+", text)]
        candidates = [(_words(part), 1) for part in parts]
        candidates.extend((words[index:index + 6], 2) for index in range(max(0, len(words) - 5)))
        for candidate, minimum in candidates:
            substantive = {word for word in candidate if word.isalpha() and word not in shared}
            if len(substantive) >= minimum and len(" ".join(candidate)) >= 12:
                spans.add(" " + " ".join(candidate) + " ")
    return spans


def _check_payload(text, spans, location):
    normalized = " " + " ".join(_words(text)) + " "
    diagnostic.require(not any(span in normalized for span in spans),
                       "copied parent/restatement prose in " + location + "; no stripping or replacement")


def _text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _call(path, call_id, files):
    diagnostic.require(isinstance(call_id, str) and re.fullmatch(r"[0-9]{4}", call_id), "invalid call ID")
    names = [f"calls/{call_id}.{kind}.json" for kind in ("request", "response")]
    for name in names:
        diagnostic.require(diagnostic.digest(path / name) == files[name], "call bytes changed: " + name)
    request, response = (diagnostic.read(path / name) for name in names)
    return request, response, {name: files[name] for name in names}


def _encode(prompt, response, row, tokenizer, max_len, spans, ordinal):
    raw = response["text"]
    _check_payload(prompt, spans, "raw record context")
    _check_payload(response["rendered_prompt"], spans, "rendered record context")
    _check_payload(raw, spans, "raw record target")
    rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                                              tokenize=False, add_generation_prompt=True)
    diagnostic.require(rendered == response["rendered_prompt"], "actual record rendering mismatch")
    context_ids = tokenizer.encode(rendered, add_special_tokens=False)
    raw_ids = tokenizer.encode(raw, add_special_tokens=False)
    eos = tokenizer.eos_token_id
    diagnostic.require(context_ids == response["prompt_token_ids"], "actual record input IDs mismatch")
    diagnostic.require(raw.strip() and context_ids and raw_ids, "empty record context or target")
    diagnostic.require(eos not in raw_ids, "raw target already contains EOS")
    target_ids = raw_ids + [eos]
    diagnostic.require(len(context_ids) + len(target_ids) <= max_len, "overlength; no truncation or splitting")
    item = dict(spans=[[rendered, False, "record_context"], [raw, True, "own_raw_record"]],
                group=row["execution_id"], view="actual_record_request", order=ordinal,
                meta={key: row[key] for key in ("arm", "eid", "execution_id", "source_call_id", "call_id")})
    encoded = trainer.encode_item_segments(item, tokenizer, max_len, chat_template=False,
                                           add_eos=True, item_index=ordinal, overflow="split")
    diagnostic.require(len(encoded) == 1 and encoded[0].context_dropped == encoded[0].target_dropped == 0
                       and encoded[0].n_splits == 1, "trainer dropped/split record material")
    batch = trainer.collate([encoded], eos)
    expected_ids = context_ids + target_ids
    expected_labels = [-100] * len(context_ids) + target_ids
    diagnostic.require(batch["input_ids"] == [expected_ids] and batch["labels"] == [expected_labels],
                       "causal input/labels/EOS mismatch")
    predictors = [index for index, label in enumerate(batch["labels"][0][1:]) if label != -100]
    diagnostic.require(predictors == list(range(len(context_ids) - 1, len(expected_ids) - 1))
                       and batch["n_target"] == len(target_ids), "causal target boundary mismatch")
    return item, dict(input_tokens=len(expected_ids), target_tokens=len(target_ids),
                      first_target_predictor=len(context_ids) - 1,
                      input_ids_sha256=diagnostic.value_hash(expected_ids),
                      labels_sha256=diagnostic.value_hash(expected_labels),
                      prompt_utf8_sha256=_text_hash(prompt), rendered_utf8_sha256=_text_hash(rendered),
                      target_utf8_sha256=_text_hash(raw))


def build_record_pair(capture_root, main_audit, fixed_selection, tokenizer, max_len=4096,
                      *, replay_verified_capture):
    """Return both V3 corpora and receipts, or raise before returning either arm.

    ``capture_root`` is formation/data, not a historical material directory.
    Replay is rerun and must exactly match the supplied CPU replay evidence.
    A caller-supplied tokenizer is mandatory; nothing loads a model or writes.
    Use returned corpora with chat_template=False, add_eos=True, pack=False.
    Hashes bind supplied artifacts, not model authenticity or semantic safety.
    """
    diagnostic.require(type(max_len) is int and 1 <= max_len <= diagnostic.MAX_MODEL_LEN, "invalid max_len")
    diagnostic.require(all(isinstance(value, dict) for value in (main_audit, fixed_selection, replay_verified_capture)),
                       "audit, fixed selection and replay evidence must be objects")
    diagnostic.require(type(getattr(tokenizer, "eos_token_id", None)) is int
                       and tokenizer.eos_token_id >= 0, "tokenizer EOS required")
    path = Path(capture_root)
    decision, selection = copy.deepcopy(main_audit), copy.deepcopy(fixed_selection)
    formation_hash = diagnostic.digest(path / "manifest.json")
    files = diagnostic.read(path / "manifest.json")["files"]
    header = diagnostic.read(path / "identity.json")
    protocol = header.get("protocol", "strict_v1")
    diagnostic.require(protocol in diagnostic.PROTOCOLS, "unknown capture protocol")
    diagnostic.require(header["stage"] == "formation", "only formation records allowed")
    audit = diagnostic.check_capture(path)
    diagnostic.require(audit["ok"], "capture replay failed: " + str(audit["failures"]))
    diagnostic.require(diagnostic.value_hash(audit) == diagnostic.value_hash(replay_verified_capture),
                       "supplied replay evidence differs from actual capture")
    diagnostic.require(audit["result"]["status"] == "AWAITING_MAIN_AUDIT", "formation not complete")
    diagnostic.require(diagnostic.validate_main_audit(decision, diagnostic.audit_template(path)),
                       "Main declined material; no export")
    diagnostic.require(diagnostic.value_hash(selection) == diagnostic.value_hash(diagnostic.select_records(audit)),
                       "fixed first-two selection changed; no reselection")
    diagnostic.require(all(len(selection["selected"][arm]) == 2 for arm in diagnostic.ARMS),
                       "paired shortage; no replacement or partial pair")
    review = decision.get("record_review", {})
    diagnostic.require(isinstance(review, dict) and review.get("decision") == "accept"
                       and review.get("scope") == "actual_record_context_and_target"
                       and review.get("selection_sha256") == diagnostic.value_hash(selection)
                       and isinstance(review.get("notes"), str) and review["notes"].strip(),
                       "Main semantic record context/target review required and bound to fixed selection")
    diagnostic.audit_native_calls(tokenizer, path)
    payloads, teacher_receipts = [], []
    for interaction in audit["result"]["interactions"]:
        for field, id_field, role in (("parent", "parent_call_id", "parent"),
                                      ("restatement", "restatement_call_id", "restate")):
            request, response, hashes = _call(path, interaction[id_field], files)
            diagnostic.require(request["request"]["role"] == role
                               and request["request"]["arm"] == interaction["arm"]
                               and response["response"]["text"] == interaction[field], "teacher source join mismatch")
            payloads.append(interaction[field])
            teacher_receipts.append(dict(call_id=interaction[id_field], files=hashes,
                                         text_utf8_sha256=_text_hash(interaction[field])))
    spans = _payload_spans(payloads, protocol)
    corpora, receipts = {}, {}
    for arm in diagnostic.ARMS:
        items, sources = [], []
        for ordinal, row in enumerate(selection["selected"][arm]):
            matches = [(index, event) for index, event in enumerate(audit["events"])
                       if event["kind"] == "execution" and event["execution_id"] == row["execution_id"]]
            diagnostic.require(len(matches) == 1, "execution join not unique")
            execution_index, execution = matches[0]
            record_index = audit["events"].index(row)
            diagnostic.require(execution_index < record_index and execution["action_kind"] == "try"
                               and all(execution[key] == row[key] for key in ("arm", "eid"))
                               and execution["call_id"] == row["source_call_id"], "record/execution join mismatch")
            record_request, record_response, record_hashes = _call(path, row["call_id"], files)
            wake_request, wake_response, wake_hashes = _call(path, row["source_call_id"], files)
            for request, role in ((record_request, "record"), (wake_request, "wake")):
                diagnostic.require(request["request"]["role"] == role
                                   and all(request["request"][key] == execution[key] for key in ("arm", "eid", "tick")),
                                   "wrong record/wake request context")
            diagnostic.require(wake_response["ended"] <= record_request["started"], "wake/record chronology mismatch")
            raw = record_response["response"]["text"]
            diagnostic.require(raw == row["text"] and row["eligible"] is True and not row["failures"]
                               and diagnostic.judge_record(raw, execution)["eligible"], "unfaithful or changed raw record")
            expected = diagnostic.record_prompt(execution, wake_response["response"]["text"], protocol)
            prompt = record_request["request"]["prompt"]
            diagnostic.require(prompt == expected, "actual record prompt mismatch; no synthetic fallback")
            item, encoding = _encode(prompt, record_response["response"], row, tokenizer, max_len, spans, ordinal)
            items.append(item)
            sources.append(dict(**item["meta"], selection_ordinal=ordinal, record_event_index=record_index,
                                execution_event_index=execution_index, record_sha256=diagnostic.value_hash(row),
                                execution_sha256=diagnostic.value_hash(execution),
                                files={**wake_hashes, **record_hashes}, encoding=encoding))
        corpora[arm] = dict(recipe="rulegame_actual_record_v3", corpus=items)
        receipts[arm] = sources
    diagnostic.require(diagnostic.digest(path / "manifest.json") == formation_hash
                       and diagnostic.tree_hashes(path, ("manifest.json",)) == files, "capture changed during export")
    return dict(corpora=corpora, source_receipts=receipts, teacher_receipts=teacher_receipts,
                formation_sha256=formation_hash, capture_files=files, identity=header,
                replay_sha256=diagnostic.value_hash(audit), main_audit=decision,
                selection_sha256=diagnostic.value_hash(selection), main_audit_sha256=diagnostic.value_hash(decision),
                encoding_options=dict(max_len=max_len, chat_template=False, add_eos=True, pack=False),
                semantic_no_answer_certification=False, model_authentication_certified=False,
                content_decision="Main semantic review; copied-span checks are conservative, not a nonleakage proof")
