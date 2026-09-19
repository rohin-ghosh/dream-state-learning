"""Quarantine human speaker labels in an opt-in child-authored target."""

import hashlib
import re


POLICY = 'R220_FABRICATED_HUMAN_TURNS_V1'
MAX_CHARACTERS = 65_536
HUMAN_LABEL = re.compile(r'(?im)^[ \t]*(?:>[ \t]*)?(?:[-*][ \t]+)?'
    r'(?:\*\*|__)?Rohin[ \t]*:(?:\*\*|__)?')


def speaker_labels(text):
    if type(text) is not str:
        raise ValueError('speaker_filter_original_text_required')
    if len(text) > MAX_CHARACTERS:
        raise ValueError('speaker_filter_scan_limit')
    return [dict(start=match.start(), end=match.end(), speaker='Rohin',
        label_sha256=hashlib.sha256(match.group().encode()).hexdigest())
        for match in HUMAN_LABEL.finditer(text)]


def apply_speaker_policy(text, evidence, policy):
    if policy != POLICY:
        raise ValueError('known_speaker_target_filter_policy')
    limited = len(text) > MAX_CHARACTERS
    labels = [] if limited else speaker_labels(text)
    result = dict(evidence, fabricated_speaker_filter=dict(policy=POLICY,
        labels=labels, scan_truncated=limited, raw_modified=False,
        semantic_falsehood_claimed=False,
        reason='HUMAN_SPEAKER_LABEL_IN_CHILD_TARGET_NOT_AUTHENTICATED_HUMAN_INPUT'))
    if labels:
        result.update(eligible=False, classification='fabricated_human_turn')
    elif limited:
        result.update(eligible=False, classification='uncertain', scan_truncated=True)
    return result
