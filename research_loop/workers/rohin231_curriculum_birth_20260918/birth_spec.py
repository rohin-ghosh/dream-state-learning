"""Exact R231 source extraction and evidence-bound parent stage accounting."""

import hashlib


DOCUMENT_SHA = '15a62a265a7d10624f43a9240645a68f07b2e309c852cbdc090f52d73af8a2db'
POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
TRIAL = 'R231_BASE_CURRICULUM_FROM_BIRTH'
STAGE0_OBJECT = 'Calculate 17 + 8 - 6 in plain digits. Show the calculation, then check it in a second way. Do not merely describe a plan.'


def extract_birth(document):
    if hashlib.sha256(document).hexdigest() != DOCUMENT_SHA:
        raise ValueError('exact_origin_document_required')
    text = document.decode('utf-8')
    section = text.split('## 1. The birth prompt', 1)[1].split('## 2. The parenting schedule', 1)[0]
    lines = [line[2:] if line.startswith('> ') else '' for line in section.splitlines()
             if line.startswith('> ') or line == '>']
    if len(lines) != 11 or any(not lines[index] for index in range(0, 11, 2)):
        raise ValueError('six_exact_birth_paragraphs')
    return '\n'.join(lines)


def stage0_metrics(assessments):
    consecutive = 0
    for item in assessments:
        if item.get('correct_checked_result') is True and item.get('evidence_verified') is True:
            consecutive += 1
        else:
            consecutive = 0
    recent = assessments[-3:]
    known = len(recent) == 3 and all(type(item.get('intention_only_act')) is bool for item in recent)
    intentions = sum(item.get('intention_only_act') is True for item in recent)
    return dict(consecutive_parent_judged_checked_results=consecutive,
                recent_intention_only_count=intentions, recent_assessments=len(recent),
                all_three_intention_labels_known=known,
                advance_eligible=consecutive >= 3 and known and intentions == 0,
                assessment_type='attributed_parent_judgment_not_independent_machine_score')
