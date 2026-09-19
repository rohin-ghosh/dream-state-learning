"""Versioned eligibility exception for actual, addressed Fable questions."""

import hashlib
import re


POLICY = 'R220_EXPLICIT_FABLE_QUESTIONS_V1'
MAX_CHARACTERS = 65_536
NAME = re.compile(r'\bFable\b', re.I)
FENCE = re.compile(r'^\s*(`{3,}|~{3,})')


def question_lines(text):
    if type(text) is not str:
        raise ValueError('question_channel_original_text_required')
    if len(text) > MAX_CHARACTERS:
        return []
    results, offset, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        marker = FENCE.match(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None and NAME.search(line) and '?' in line:
            content = line.rstrip('\r\n')
            results.append(dict(start=offset, end=offset + len(content), text=content,
                text_sha256=hashlib.sha256(content.encode()).hexdigest()))
        offset += len(line)
    return results


def apply_question_policy(text, evidence, policy):
    if policy != POLICY:
        raise ValueError('known_question_target_filter_policy')
    questions = question_lines(text)
    result = dict(evidence, question_target_filter=dict(policy=POLICY,
        questions=[{key: value for key, value in question.items() if key != 'text'}
                   for question in questions], raw_modified=False,
        delivery_claimed=False, answer_claimed=False))
    if (questions and not evidence.get('scan_truncated')
            and not evidence.get('repetition_findings')
            and not evidence.get('code_wrapped_prose')
            and evidence.get('classification') in ('meta_only', 'uncertain')):
        result.update(eligible=True, classification='addressed_question',
                      base_classification=evidence['classification'])
    return result
