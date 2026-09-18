"""Explicit first-block execution syntax with preserved raw-source provenance."""

import hashlib
import io
import re
import string
import tokenize
import unicodedata


POLICY = 'R153_FIRST_CODE_BLOCK_ASCII_PUNCTUATION_V1'
LEGACY = 'R125_EXACT_EXPERIMENT_FENCE_V1'
MAX_BYTES = 1024 * 1024
LANGUAGES = frozenset(('', 'python', 'py', 'python experiment', 'triton', 'cuda', 'c++', 'cpp'))
PUNCTUATION = {'‘': "'", '’': "'", '“': '"', '”': '"', '−': '-', '–': '-',
               '—': '-', '\u00a0': ' ', '\u2007': ' ', '\u202f': ' '}


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize_punctuation(source):
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    protected = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type in (tokenize.STRING, tokenize.COMMENT):
                start = offsets[token.start[0] - 1] + token.start[1]
                end = offsets[token.end[0] - 1] + token.end[1]
                protected.update(range(start, end))
    except (tokenize.TokenError, IndentationError):
        pass
    result, changes = [], []
    for position, character in enumerate(source):
        replacement = character
        if position not in protected:
            replacement = PUNCTUATION.get(character, character)
            folded = unicodedata.normalize('NFKC', replacement)
            if len(folded) == 1 and folded in string.punctuation:
                replacement = folded
        if replacement != character:
            changes.append(dict(offset=position, original=character, replacement=replacement))
        result.append(replacement)
    return ''.join(result), changes


def extract(raw):
    if type(raw) is not str or len(raw.encode('utf-8')) > MAX_BYTES:
        raise ValueError('bounded_child_source_text_required')
    report = dict(policy=POLICY, attempted=False, source=None, raw_source=None,
                  raw_text_sha256=sha(raw), reason='NO_CODE_BLOCK')
    lines = raw.splitlines(keepends=True)
    position = 0
    opening = None
    for line in lines:
        if opening is None:
            match = re.fullmatch(r'[ \t]{0,8}(`{3,}|~{3,})[ \t]*([^\r\n]*)\r?\n?', line)
            if match:
                marker, language = match.groups()
                language = language.strip().lower()
                report.update(attempted=True, language=language)
                if language not in LANGUAGES:
                    report['reason'] = 'FIRST_BLOCK_LANGUAGE_NOT_EXECUTABLE'
                    return report
                opening = (marker, position + len(line))
        else:
            marker, start = opening
            if re.fullmatch(r'[ \t]{0,8}' + re.escape(marker[0]) + '{' + str(len(marker)) + r',}[ \t]*\r?\n?', line):
                original = raw[start:position]
                if not original.strip():
                    report['reason'] = 'EMPTY_CODE_BLOCK'
                    return report
                source, changes = normalize_punctuation(original)
                report.update(source=source, raw_source=original, raw_source_sha256=sha(original),
                              source_sha256=sha(source), transformations=changes,
                              span_start=start, span_end=position, reason='FIRST_CODE_BLOCK')
                return report
        position += len(line)
    if opening is not None:
        report['reason'] = 'UNCLOSED_FIRST_CODE_BLOCK'
    return report


def metadata(report):
    return {key: value for key, value in report.items() if key not in ('source', 'raw_source')}
