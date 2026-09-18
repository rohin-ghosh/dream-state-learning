"""Pure authored copy replay derived only from caller-validated training calls.

The caller must first authenticate actual successful training trajectories with
the existing collection loader. Row shape and hashes cannot authenticate model
execution or exclude held data by themselves. No evaluator, witness, source
allocator, tokenizer, or model is consulted here.
"""

from hashlib import sha256
import json

from organism_v6 import composition_birth_stage2a as wire


FAMILIES = ("READ INDEX", "READ RELATION", "STEP", "THINK KEEP", "THINK REVISE", "STOP")
COPY_PROMPT = "Return the following text verbatim, without explanation:\n{actual_action}"
LOSS_POLICY = {"prefix": "MASK_ALL", "assistant": "TRAIN", "eot": "TRAIN"}
REPLAY_COUNT = 12
UPDATES = 256
BATCH_SIZE = 4


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _row_hash(row):
    raw = json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False,
                     separators=(",", ":")).encode("ascii")
    return sha256(raw).hexdigest()


def _family(row):
    _require(type(row) is dict and row.get("status") == "DRAFT_NOT_RELEASED",
             "validated_collector_draft_required")
    _require(type(row.get("source_call_index")) is int and row["source_call_index"] >= 0,
             "actual_source_call_index_required")
    _require(type(row.get("episode_id")) is str and bool(row["episode_id"]),
             "source_episode_required")
    prefix = row.get("prefix")
    _require(type(prefix) is list and len(prefix) >= 2 and
             prefix[0] == {"role": "system", "content": wire.SYSTEM_MESSAGE} and
             all(type(message) is dict and set(message) == {"role", "content"} and
                 type(message["content"]) is str and message["role"] in ("user", "assistant")
                 for message in prefix[1:]) and prefix[-1]["role"] == "user",
             "unassisted_source_prefix_required")
    _require(row.get("target_eot") == "<|im_end|>" and row.get("loss_policy") == LOSS_POLICY,
             "assistant_eot_only_source_required")
    action = wire.parse_action(row.get("assistant"))
    return action.operation + (" " + action.verb if action.verb is not None else "")


def compile_copy_rows(actual_validated_rows) -> tuple[tuple[dict, ...], dict]:
    """Return two actual calls per family, ordered by FAMILIES then call index.

    Input is one validated collection's rows. Duplicate call indices, missing
    families, or fewer than two calls per family fail; never repeat a missing
    call or synthesize an action. Equal action bytes from distinct calls (STOP,
    for example) are allowed. First means lowest source_call_index, not a
    performance-based selection. Source rows are neither edited nor retained by
    reference. Only the new public copy prompt and exact SYSTEM enter prefixes.

    Returns (rows_tuple, metadata_dict). Rows retain the seven essential input
    keys, including status, call and episode identifiers. metadata['rows'] maps
    each output row_index to source_row_index/episode/call and hashes. Hashes use
    sorted compact ASCII JSON for complete original rows and UTF-8 for actions.
    Metadata labels these authored copy tasks, not new experienced trajectories;
    the unchanged row status is compatibility data, not renewed source admission.
    """
    _require(type(actual_validated_rows) in (list, tuple) and bool(actual_validated_rows),
             "nonempty_validated_training_rows_required")
    groups = {family: [] for family in FAMILIES}
    seen = set()
    for source_row_index, row in enumerate(actual_validated_rows):
        family = _family(row)
        _require(row["source_call_index"] not in seen, "duplicate_source_call_index")
        seen.add(row["source_call_index"])
        groups[family].append((source_row_index, row))
    _require(all(len(groups[family]) >= 2 for family in FAMILIES),
             "two_actual_calls_per_family_required")
    result = []
    origins = []
    for family in FAMILIES:
        selected = sorted(groups[family], key=lambda item: item[1]["source_call_index"])[:2]
        for source_row_index, row in selected:
            actual_action = row["assistant"]
            result.append(dict(
                status=row["status"], episode_id=row["episode_id"],
                source_call_index=row["source_call_index"],
                prefix=[
                    dict(role="system", content=wire.SYSTEM_MESSAGE),
                    dict(role="user", content=COPY_PROMPT.format(actual_action=actual_action)),
                ],
                assistant=actual_action, target_eot=row["target_eot"],
                loss_policy=dict(LOSS_POLICY),
            ))
            origins.append(dict(
                row_index=len(result) - 1, family=family, source_row_index=source_row_index,
                source_call_index=row["source_call_index"], source_episode_id=row["episode_id"],
                source_row_sha256=_row_hash(row),
                source_assistant_sha256=sha256(actual_action.encode("utf-8")).hexdigest(),
            ))
    return tuple(result), dict(
        kind="ACTUAL_TRAINING_ACTION_AUTHORED_COPY_PROMPT", source_rows=len(actual_validated_rows),
        copy_rows=REPLAY_COUNT, families=list(FAMILIES), rows=origins,
    )


def scheduled_indexes(outcome_count, replay_count, update_number) -> tuple[int, ...]:
    """First three original cyclic slots; replace only slot four with copy replay.

    Index into outcome rows followed by the 12 copy rows. Across 256 batch-four
    updates this is 768 outcome + 256 copy presentations, not outcome-dose,
    supervised-token, or compute matched to the unchanged outcome-only arm.
    No branch rebalancing or recovery of the displaced fourth slots is done.
    """
    _require(type(outcome_count) is int and outcome_count > 0, "positive_outcome_count_required")
    _require(type(replay_count) is int and replay_count == REPLAY_COUNT, "exactly_12_copy_rows_required")
    _require(type(update_number) is int and 1 <= update_number <= UPDATES, "update_must_be_1_to_256")
    original_start = (update_number - 1) * BATCH_SIZE
    return tuple((original_start + slot) % outcome_count for slot in range(3)) + (
        outcome_count + (update_number - 1) % replay_count,
    )
