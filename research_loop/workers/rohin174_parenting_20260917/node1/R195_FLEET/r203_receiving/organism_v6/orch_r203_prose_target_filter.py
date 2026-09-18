"""Non-material, opt-in NEW-target quarantine; never rewrite source targets.

R203_INTERNAL_COMMON_WORD_CAPITALIZATION_V1 provisionally excludes only when a
prose paragraph has at least 20 sentence-internal common-word opportunities,
at least 10 initial-capital variants and a rate >= 0.35. The fixed lexicon omits names,
name-like modals (May/Will), and I; all-caps multi-letter tokens are ignored.
Sentence/paragraph starts, Markdown headings, fenced/inline code and indented
code are omitted. Only the first 65,536 characters are inspected.

This is not corruption-cause inference or general quality detection. Deliberate
stylization, quotations, unmarked titles and names sharing lexicon words can
still cause false positives; the thresholds and exclusions are provisional.
Synthetic regressions do not estimate a real-world false-positive rate.

scan_target returns whole-scan counts, thresholds, bounded-scan metadata and
source-line-bound qualifying_paragraphs; quarantined means ANY paragraph meets
all three thresholds, not that the aggregate capitalization rate qualifies.
"""

import hashlib
import re


POLICY = 'R203_INTERNAL_COMMON_WORD_CAPITALIZATION_V1'
EXCLUSION_REASON = 'provisional_internal_common_word_capitalization_quarantine'
MIN_ELIGIBLE_COMMON_WORDS = 20
MIN_CAPITALIZED_COMMON_WORDS = 10
MIN_RATE_NUMERATOR = 35
MIN_RATE_DENOMINATOR = 100
MAX_SCAN_CHARACTERS = 65_536
COMMON_WORDS = frozenset('a an the and or but nor if as at by for from in into of on onto '
    'than that then these this those though to upon whether which while with without '
    'because be been being is are was were has have had do does did not both either '
    'neither each every any some such their them its our your'.split())
FENCE_PREFIX = r'[ \t]*(?:>[ \t]*)*'
FENCE = re.compile(FENCE_PREFIX + r'(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$')
HEADING = re.compile(FENCE_PREFIX + r'#{1,6}(?:[ \t]+|$)')
SETEXT = re.compile(FENCE_PREFIX + r'(?:={3,}|-{3,})[ \t]*$')
LIST_START = re.compile(FENCE_PREFIX + r'(?:[-+*]|\d+[.)])[ \t]+')
INLINE_CODE = re.compile(r'(`+)[^`]*\1(?!`)')
WORD = re.compile(r"(?<![\w'’\-])[A-Za-z]+(?:['’][A-Za-z]+)*(?![\w'’\-])")
SENTENCE_END = re.compile(r'[.!?]')


def _statistics(eligible, capitalized):
    return dict(eligible_common_word_opportunities=eligible, capitalized_common_words=capitalized,
        capitalized_rate=capitalized / eligible if eligible else 0.0,
        quarantined=(eligible >= MIN_ELIGIBLE_COMMON_WORDS and capitalized >= MIN_CAPITALIZED_COMMON_WORDS
            and capitalized * MIN_RATE_DENOMINATOR >= eligible * MIN_RATE_NUMERATOR))


def scan_target(text):
    if type(text) is not str:
        raise ValueError('prose_target_filter_original_text_required')
    scanned = text[:MAX_SCAN_CHARACTERS]
    if len(text) > len(scanned) and re.match(r"[\w'’\-]", text[len(scanned)]):
        trailing = re.search(r"[^\w'’\-][\w'’\-]*$", scanned)
        scanned = scanned[:trailing.start() + 1] if trailing else ''
    lines = scanned.splitlines()
    marker, width, sentence_start = None, 0, True
    eligible, capitalized = 0, 0
    paragraphs, paragraph = [], None
    for index, line in enumerate(lines):
        if marker is not None:
            if re.fullmatch(FENCE_PREFIX + re.escape(marker) + '{' + str(width) + r',}[ \t]*', line):
                marker = None
            continue
        opening = FENCE.fullmatch(line)
        if opening is not None:
            fence, tail = opening.groups()
            marker, width, sentence_start = fence[0], len(fence), True
            paragraph = None
            if re.search(re.escape(marker) + '{' + str(width) + r',}[ \t]*$', tail):
                marker = None
            continue
        if (not line.strip() or HEADING.match(line) or SETEXT.fullmatch(line)
                or (index + 1 < len(lines) and SETEXT.fullmatch(lines[index + 1]))
                or line.startswith(('    ', '\t'))):
            sentence_start = True
            paragraph = None
            continue
        if LIST_START.match(line):
            sentence_start = True
            paragraph = None
        if paragraph is None:
            paragraph = dict(start_line=index + 1, end_line=index + 1,
                eligible_common_word_opportunities=0, capitalized_common_words=0)
            paragraphs.append(paragraph)
        paragraph['end_line'] = index + 1
        prose = INLINE_CODE.sub(' ', line)
        previous_end = 0
        for match in WORD.finditer(prose):
            if SENTENCE_END.search(prose[previous_end:match.start()]):
                sentence_start = True
            word = match.group()
            lower = word.lower()
            if (not sentence_start and lower in COMMON_WORDS
                    and (word == lower or word == lower.capitalize())
                    and not (len(word) > 1 and word.isupper())):
                eligible += 1
                capitalized += int(word != lower)
                paragraph['eligible_common_word_opportunities'] += 1
                paragraph['capitalized_common_words'] += int(word != lower)
            sentence_start = False
            previous_end = match.end()
        if SENTENCE_END.search(prose[previous_end:]):
            sentence_start = True
    qualifying = []
    for paragraph in paragraphs:
        stats = _statistics(paragraph['eligible_common_word_opportunities'], paragraph['capitalized_common_words'])
        if stats['quarantined']:
            qualifying.append(dict(paragraph, capitalized_rate=stats['capitalized_rate'], quarantined=True))
    result = _statistics(eligible, capitalized)
    result.update(quarantined=bool(qualifying), qualifying_paragraphs=qualifying,
        decision_scope='ANY_PROSE_PARAGRAPH',
        thresholds=dict(min_eligible_common_words=MIN_ELIGIBLE_COMMON_WORDS,
            min_capitalized_common_words=MIN_CAPITALIZED_COMMON_WORDS,
            min_capitalized_rate=MIN_RATE_NUMERATOR / MIN_RATE_DENOMINATOR),
        scanned_characters=len(scanned), scan_character_limit=MAX_SCAN_CHARACTERS,
        scan_truncated=len(scanned) < len(text))
    return result


def prose_exclusions(new_rows):
    checks, excluded = [], []
    for index, row in enumerate(new_rows):
        if 'prose_target_filter' not in row:
            continue
        if type(row['prose_target_filter']) is not str or row['prose_target_filter'] != POLICY:
            raise ValueError('known_prose_target_filter_policy')
        evidence = scan_target(row['target'])
        check = dict(source_sha256=row['source_sha256'], segment=row['segment'], cohort='NEW',
            row_index=index, raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
            policy=POLICY, evidence=evidence)
        checks.append(check)
        if evidence['quarantined']:
            excluded.append(dict(check, reason=EXCLUSION_REASON))
    return dict(policy=POLICY, checks=checks, excluded=excluded, raw_modified=False,
        targets_normalized=False, provisional=True, corruption_cause_claimed=False,
        general_quality_detection_claimed=False,
        claim_scope='BOUNDED_INTERNAL_COMMON_WORD_CAPITALIZATION_ONLY')
