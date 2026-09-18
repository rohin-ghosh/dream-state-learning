"""Prospective lexical repair only: preserve raw and reject ambiguous extra text."""

from contextlib import contextmanager
from copy import deepcopy
import json

from gpu import orch_math_pipeline_l2_parent_strong as strong


STRICT_PARSE = strong.parse


def text_part(envelope):
    parts = [part for item in envelope.get('output', []) if item.get('type') == 'message'
             for part in item.get('content', []) if part.get('type') == 'output_text']
    assert len(parts) == 1, 'single_actual_parent_text'
    return parts[0]


def decode(envelope):
    text = text_part(envelope)['text']
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    plan, end = json.JSONDecoder().raw_decode(text.lstrip())
    text = text.lstrip()
    suffix = text[end:].strip()
    assert isinstance(plan, dict) and suffix in ('', '}'), 'ambiguous_parent_suffix_rejected'
    return text[:end], 'SINGLE_REDUNDANT_CLOSING_BRACE' if suffix else 'STRICT_JSON'


def protocol_status(envelope):
    return decode(envelope)[1]


def parse(envelope, identifiers):
    try:
        return STRICT_PARSE(envelope, identifiers)
    except json.JSONDecodeError:
        canonical, status = decode(envelope)
        assert status == 'SINGLE_REDUNDANT_CLOSING_BRACE', 'no_other_parent_protocol_repair'
        repaired = deepcopy(envelope)
        text_part(repaired)['text'] = canonical
        return STRICT_PARSE(repaired, identifiers)


@contextmanager
def parsing_context():
    previous = strong.parse
    strong.parse = parse
    try:
        yield
    finally:
        strong.parse = previous
