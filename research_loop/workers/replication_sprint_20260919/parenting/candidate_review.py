"""Offline review flags for unsent parent drafts, never a runtime/LEARN gate."""

import json
import re


def review_draft(draft, latest, *, previous_messages=(), pending_human=False, word_budget=90):
    findings = []
    if not isinstance(draft, dict) or set(draft) != {'speak', 'message', 'rationale'}:
        return ['existing_response_schema_required']
    if type(draft['speak']) is not bool or not isinstance(draft['message'], str):
        return ['existing_response_types_required']
    if not isinstance(draft['rationale'], str):
        return ['existing_rationale_string_required']
    message = draft['message'].strip()
    if draft['speak']:
        if pending_human:
            findings.append('genuine_human_priority')
        if not message or len(message.split()) > word_budget or len(message.encode()) > 4096:
            findings.append('public_turn_budget')
        if message in {prior.strip() for prior in previous_messages}:
            findings.append('identical_parent_turn')
    elif message:
        findings.append('silent_message_must_be_empty')
    elif not pending_human:
        findings.append('persistent_baseline_uncovered_slot')
    if re.search(r'^\s*(?:Rohin|Fable|Human|User)\s*:', message, re.IGNORECASE | re.MULTILINE):
        findings.append('fabricated_speaker_line')
    if any(token in message for token in ('<|im_start|>', '<|im_end|>', '<tool_call>')):
        findings.append('runtime_or_template_tokens')
    try:
        rationale = json.loads(draft['rationale'])
    except (ValueError, TypeError):
        return findings + ['source_bound_rationale_required']
    if not isinstance(rationale, dict) or not isinstance(rationale.get('latest'), dict):
        return findings + ['source_bound_rationale_required']
    reference = rationale['latest']
    if (type(reference.get('record_index')) is not int
            or reference['record_index'] != latest.get('record_index')
            or reference.get('record_sha256') != latest.get('record_sha256')
            or not re.fullmatch(r'[0-9a-f]{64}', str(reference.get('record_sha256', '')))):
        findings.append('exact_observed_record_required')
    quote = reference.get('quote')
    if (not isinstance(quote, str) or not 0 < len(quote) <= 240
            or quote not in latest.get('text', '')):
        findings.append('literal_observed_quote_required')
    if not isinstance(rationale.get('comparison'), str) or not rationale['comparison'].strip():
        findings.append('intervention_explanation_required')
    return findings
