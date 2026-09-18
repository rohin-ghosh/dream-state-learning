"""Lossless parent-private JSON-object compatibility; preserves strict validation."""

import json


def normalize_rationale(raw):
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > 65536:
        raise ValueError('bounded_parent_wire_text')
    payload = raw[8:-4] if raw.startswith('```json\n') and raw.endswith('\n```') else raw
    response = json.loads(payload)
    if isinstance(response, dict) and isinstance(response.get('rationale'), dict):
        response['rationale'] = json.dumps(response['rationale'], sort_keys=True, separators=(',', ':'), allow_nan=False)
        return json.dumps(response, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return raw


def compatible_parser(original):
    def parse(raw):
        return original(normalize_rationale(raw))
    return parse
