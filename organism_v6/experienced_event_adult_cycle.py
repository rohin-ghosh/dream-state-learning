"""Parent-free offered experience, not autonomous selection or an H2 claim.

Only final EVENT LF count is canonicalized. The caller authenticates the actor
adapter and source bytes; captured replay checks consistency, not authenticity.
No model, tokenizer, fitting, filesystem writes, or launch is performed here.
"""

import json

from gpu import astra_experienced_event_microloop as source
from gpu import astra_experienced_event_cue_collect as collector
from gpu import astra_experienced_event_cue_sleep as cue_sleep
from organism_v6 import experienced_event_microloop as micro


SCHEMA = "DEV_PARENT_FREE_ADULT_CYCLE_COLLECTION_V1"
MASTER = "ASTRA-CUE-ADULT-CYCLE-20260914-A1"
SERIALIZATION = "FINAL_LF_ONLY"
CLAIM = "EXOGENOUS_OFFERED_EXPERIENCE_FORMAT_SCAFFOLD_NOT_AUTONOMOUS_SELECTION_OR_H2"
MAX_CALLS = 8
UPDATES = 400
OLD_ROW_COUNT = 32
CUE_ROW_COUNT = 20
NEW_ROW_COUNT = 32
require = micro._require


def _bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii")


def _copy(value):
    return json.loads(_bytes(value))


def _same(actual, expected, reason):
    require(_bytes(actual) == _bytes(expected), reason)


def _identities(bank):
    micro._check_bank(bank)
    return {fact[key] for fact in bank
            for key in ("world", "event", "node", "port", "outcome", "receipt")}


def build_bank():
    bank = micro.build_bank(MASTER)
    training_banks = collector.training_banks()
    require(len(training_banks) == 2, "two_cue_training_banks_required")
    excluded = [micro.build_bank(source.MASTER), *training_banks]
    excluded.extend(micro.build_bank(cue_sleep.HELD_MASTER + "-" + str(index)) for index in range(2))
    identities = _identities(bank)
    require(all(not identities.intersection(_identities(previous)) for previous in excluded),
            "adult_identity_overlap")
    return bank


def _generation(response, messages):
    require(type(response) is dict and type(response.get("raw")) is str
            and type(response.get("terminal")) is bool and type(response.get("truncated")) is bool,
            "generation_dict_raw_terminal_truncated_required")
    if "messages" in response:
        _same(response["messages"], messages, "generation_prompt_drift")
    require(response["terminal"] is True and response["truncated"] is False,
            "terminal_untruncated_generation_required")
    return response


def _collect(invoke):
    bank, episodes, captures = build_bank(), [], []

    def generate(messages, episode_index, phase):
        require(len(captures) < MAX_CALLS, "adult_call_cap")
        outcome = invoke(_copy(messages))
        capture = dict(call_index=len(captures), episode_index=episode_index,
                       phase=phase, messages=_copy(messages), **_copy(outcome))
        captures.append(capture)
        return capture

    for episode_index, fact in enumerate(bank):
        episode = dict(fact=_copy(fact), exploration=None, event=None, accepted=False,
                       infrastructure_failure=False, error=None)
        episodes.append(episode)
        try:
            messages = micro.exploration_messages(fact)
            capture = generate(messages, episode_index, "exploration")
            episode["exploration"] = _copy(capture["response"])
            if capture["error"] is not None:
                episode.update(infrastructure_failure=True, error=_copy(capture["error"]))
            require(capture["error"] is None, "exploration_callback_failure")
            exploration = _generation(episode["exploration"], messages)
            messages = micro.observation_messages(fact, exploration["raw"])
            capture = generate(messages, episode_index, "event")
            episode["event"] = _copy(capture["response"])
            if capture["error"] is not None:
                episode.update(infrastructure_failure=True, error=_copy(capture["error"]))
            require(capture["error"] is None, "event_callback_failure")
            event = _generation(episode["event"], messages)
            micro.validate_episode(fact, exploration["raw"], micro.canonical_event(event["raw"]))
            episode["accepted"] = True
        except ValueError as error:
            if episode["error"] is None:
                episode["error"] = dict(type=type(error).__name__, message=str(error))
    accepted = sum(episode["accepted"] for episode in episodes)
    rows = micro.compile_rows(bank, episodes, serialization=SERIALIZATION) if accepted == 4 else []
    require(not rows or len(rows) == NEW_ROW_COUNT, "all_four_grounded_events_before_rows")
    return dict(schema=SCHEMA, master=MASTER, serialization=SERIALIZATION, claim=CLAIM,
                new_material=True, clean_claim=False, parent_present=False, fits=0,
                bank=bank, episodes=episodes, rows=rows, captures=captures,
                count=len(captures), accepted_events=accepted, event_denominator=4,
                infrastructure_failures=sum(episode["infrastructure_failure"] for episode in episodes),
                status="COLLECTION_COMPLETE_NO_FIT" if accepted == 4 else "COLLECTION_FAILED_NO_FIT")


def collect(generate):
    """Offer four experiences, retaining every attempted call and failed output."""
    require(callable(generate), "generation_callback_required")

    def invoke(messages):
        response = None
        try:
            response = generate(_copy(messages))
            return dict(response=_copy(response), error=None)
        except Exception as error:
            available = None
            if type(response) is dict:
                available = {key: response.get(key) for key in ("raw", "terminal", "truncated")
                             if type(response.get(key)) in (str, bool, int, type(None))}
            return dict(response=available, error=dict(type=type(error).__name__, message=str(error)))

    return _collect(invoke)


def replay_collection(record):
    """Recompute all prompts, admission, failures and rows; reject any drift.

    A faithfully retained failed collection replays to no rows. Coherently
    replaced captures require the caller's independent source authentication.
    """
    require(type(record) is dict and type(record.get("captures")) is list,
            "captured_collection_required")
    captures = _copy(record["captures"])
    require(4 <= len(captures) <= MAX_CALLS, "bounded_actual_calls_required")
    cursor = 0

    def invoke(messages):
        nonlocal cursor
        require(cursor < len(captures), "missing_actual_call")
        capture = captures[cursor]
        cursor += 1
        require(type(capture) is dict and all(key in capture for key in ("messages", "response", "error")),
                "actual_call_record_required")
        _same(capture["messages"], messages, "captured_prompt_drift")
        return dict(response=capture["response"], error=capture["error"])

    replayed = _collect(invoke)
    require(cursor == len(captures), "unused_actual_calls")
    _same(record, replayed, "adult_collection_replay_drift")
    return replayed["rows"]


def adult_indexes(update, cue_count):
    """Fixed OLD32 + CUE20 + NEW32 layout: one old, one cue, two new."""
    require(type(update) is int and 1 <= update <= UPDATES, "fixed_400_update_range")
    require(type(cue_count) is int and cue_count == CUE_ROW_COUNT, "exact_twenty_cue_rows_required")
    offset = update - 1
    new_start = OLD_ROW_COUNT + cue_count
    return (offset % OLD_ROW_COUNT, OLD_ROW_COUNT + offset % cue_count,
            new_start + (2 * offset) % NEW_ROW_COUNT,
            new_start + (2 * offset + 1) % NEW_ROW_COUNT)
