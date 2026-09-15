"""Strict, lossless normalization of a provider's JSON result envelope."""

import json
import re


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('non_json_constant:' + value)


def parse_json_envelope(text: str) -> dict:
    """Parse one object; unwrap only a full json fence and one top-level alias.

    Pass the provider's result string, not its outer usage/status envelope.
    The caller retains raw bytes and validates provider status and task schema.
    No message, target, review, rubric, or decision value is rewritten.
    """
    if not isinstance(text, str):
        raise ValueError('json_result_string_required')
    body = text.strip(' \t\r\n')
    if body.startswith('```'):
        fenced = re.fullmatch(r'```json\r?\n(?P<body>[\s\S]*)\r?\n```', body)
        if fenced is None:
            raise ValueError('full_json_fence_required')
        body = fenced.group('body')
    result = json.loads(body, object_pairs_hook=_unique_object,
                        parse_constant=_reject_constant)
    if not isinstance(result, dict):
        raise ValueError('json_object_required')
    if 'distillation_for_rohin' in result:
        if 'distillation' in result:
            raise ValueError('ambiguous_distillation_alias')
        result = {('distillation' if key == 'distillation_for_rohin' else key): value
                  for key, value in result.items()}
    return result
