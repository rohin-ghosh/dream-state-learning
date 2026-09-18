"""Lossless overflow repair for canonical user-message JSON serialization."""

from copy import deepcopy
import hashlib
import json


class ContextCapacityError(ValueError):
    def __init__(self, metadata):
        super().__init__('lossless_json_still_exceeds_context')
        self.metadata = metadata


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite_json_constant')


def canonical_user_json(text):
    try:
        value = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
        if not isinstance(value, (dict, list)):
            return None
        original = json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)
        if original != text:
            return None
        normalized = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        normalized.encode('utf-8', errors='strict')
        require(json.loads(normalized) == value, 'lossless_json_roundtrip')
        return normalized
    except (ValueError, TypeError, UnicodeError):
        return None


def token_count(tokenizer, messages):
    tokens = tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=True, return_dict=False)
    require(isinstance(tokens, list) and all(type(token) is int for token in tokens),
            'flat_token_ids_not_BatchEncoding')
    return len(tokens)


def normalize_messages(tokenizer, messages, cap, limit=16384):
    require(type(cap) is int and type(limit) is int and 0 < cap < limit, 'unchanged_valid_decoder_budget')
    require(isinstance(messages, list) and all(isinstance(message, dict) and
            isinstance(message.get('content'), str) for message in messages), 'text_message_list_required')
    actual = deepcopy(messages)
    original_tokens = token_count(tokenizer, messages)
    metadata = dict(schema='R140_LOSSLESS_JSON_OVERFLOW_V1', applied=False,
        original_prompt_tokens=original_tokens, actual_prompt_tokens=original_tokens,
        generation_cap=cap, context_limit=limit, original_messages_sha256=digest(messages),
        actual_messages_sha256=digest(actual), reencoded_message_indices=[],
        content_removed=False, model_budget_changed=False, historical_model_calls_replayed=False)
    if original_tokens + cap <= limit:
        return actual, metadata
    for index, message in enumerate(actual):
        if message.get('role') != 'user':
            continue
        normalized = canonical_user_json(message['content'])
        if normalized is not None and normalized != message['content']:
            message['content'] = normalized
            metadata['reencoded_message_indices'].append(index)
    metadata.update(applied=bool(metadata['reencoded_message_indices']),
        actual_prompt_tokens=token_count(tokenizer, actual), actual_messages_sha256=digest(actual))
    require(recover_original_messages(actual, metadata) == messages, 'exact_original_messages_recoverable')
    if metadata['actual_prompt_tokens'] + cap > limit:
        raise ContextCapacityError(metadata)
    return actual, metadata


def recover_original_messages(actual, metadata):
    require(digest(actual) == metadata['actual_messages_sha256'], 'actual_message_hash')
    restored = deepcopy(actual)
    indices = metadata['reencoded_message_indices']
    require(len(indices) == len(set(indices)), 'unique_reencoded_indices')
    for index in indices:
        require(type(index) is int and 0 <= index < len(restored), 'valid_reencoded_index')
        message = restored[index]
        require(message.get('role') == 'user', 'only_user_JSON_reencoded')
        value = json.loads(message['content'], object_pairs_hook=unique_object, parse_constant=reject_constant)
        require(isinstance(value, (dict, list)), 'container_JSON_required')
        message['content'] = json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)
    require(digest(restored) == metadata['original_messages_sha256'], 'exact_original_message_hash')
    return restored
