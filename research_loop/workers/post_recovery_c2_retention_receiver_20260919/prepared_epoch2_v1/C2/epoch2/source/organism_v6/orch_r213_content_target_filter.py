"""Opt-in, provisional content eligibility for original child targets.

This bounded lexical check excludes meta-only and uncertain targets without
rewriting them. Eligibility is not a correctness, novelty, receipt, language,
or task-completion judgment. Those checks remain independent. Mixed rows keep
their original bytes; the evidence records both content and meta units.
"""

import ast
import hashlib
import re


POLICY = 'R213_CONTENT_BEARING_TARGETS_V1'
MAX_SCAN_CHARACTERS = 65_536
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
FENCE = re.compile(r'^\s*(`{3,}|~{3,})([^\n]*)\n(.*?)(?:^\s*\1\s*$|\Z)', re.M | re.S)
LABEL = re.compile(r'^\s*(?:[-*>#]+\s*)?(?:(?:continue|continuing) thinking|intention|'
    r'judgment|judgement|final message|working state|preserved|changed|created|modified|'
    r'next action|plan|answer|caption|paragraph\s+\d+|iteration\s+\d+)\s*:\s*', re.I)
DEFERRED_QUESTION = re.compile(r'\b(?:I|we)\s+(?:(?:will|would|should|must|need to|plan to|'
    r'intend to|want to)\s+)?(?:ask|request|seek clarification|wait for)\b', re.I)
META = re.compile(r'\b(?:I|we)\s+(?:(?:believe|think|feel|hope)\s+(?:that\s+)?)?'
    r'(?:(?:I|we)\s+)?(?:(?:have|had|has|am|are|will|would|should|can|now|already|'
    r'adequately|successfully|carefully|fully|been|be)\s+)*'
    r'(?:reviewed|understood|identified|checked|completed|demonstrated|modified|'
    r'improved|incorporated|refined|addressed|considered|ensured|learned|understanding|'
    r'ready|confident|committed|prepared)\b|'
    r'\b(?:adequate|better|deeper|clear|comprehensive)\s+understanding\b|'
    r'\b(?:demonstrate|demonstrating)\s+(?:my|our)\s+understanding\b|'
    r'\b(?:all|every)\s+(?:requested\s+)?tasks?\s+(?:have been\s+)?(?:completed|done)\b|'
    r'\b(?:I|we)\s+(?:believe|think|hope)\s+(?:that\s+)?'
    r'(?:restating|explaining|verifying|incorporating|self.regulation|metacognition)\b|'
    r'^(?:nothing changed|ready to act|continue thinking|done|understood|yes|no)[.!]?$', re.I)
VAGUE_FUTURE = re.compile(r'\b(?:I|we)\s+(?:will|would|should|must|need to|plan to|'
    r'intend to|want to)\b|\b(?:will|would|should|can)\s+(?:help|demonstrate|improve|'
    r'enhance|ensure|strengthen|enrich)\b', re.I)
ACTION = re.compile(r'\b(?:substitute|calculate|compute|compare|test|print|read|open|'
    r'write|rewrite|replace|remove|cut|add|check|count|measure|run|verify|revise)\b', re.I)
SPECIFIC_METHOD = re.compile(r'\b(?:by|using|against|with|where|when|until|before|after|'
    r'instead of|rather than|from)\b', re.I)
OBJECT = re.compile(r'\b(?:paragraph|sentence|caption|draft|scene|dialogue|story|equation|'
    r'formula|sum|identity|file|function|test|output|receipt|adapter|map|boat|Byte|C2)\b|'
    r'\b[\w./-]+\.(?:py|md|json|txt|cu)\b|\b(?:n|V)\s*=\s*[-+]?\d', re.I)
ARITHMETIC = re.compile(r'(?:\d|\b[A-Za-z])\s*(?:\*\*|[+*/=−-])\s*[-+]?(?:\d|[A-Za-z]\b)')
PREDICATE = re.compile(r'\b(?:is|are|was|were|means|stores|survives|survive|keeps|kept|'
    r'preserves|preserve|trains|train|updates|update|changes|change|contains|needs|need|'
    r'because|while|but|instead|knows|knew|said|asked|walked|saw|felt|found|took|'
    r'opened|waited|decided|prefer|choose|want|cannot|can\x27t)\b', re.I)
META_REFERENCE = re.compile(r'\b(?:narrative|paragraph|story|draft|reflections?|'
    r'characterization|reader engagement|understanding|modifications?|refinement|'
    r'improvement|current status|this approach|this change|these changes|previous attempts?|'
    r'previous update|advice|still room|complete[d]?|derived|set up|implementation|'
    r'attention to detail|writing skills|opportunity to practice)\b', re.I)
GENERIC_REVIEW = re.compile(r'\b(?:correct analytical solution|syntaxerrors?|'
    r'double.check all|realism|realistic|engaging|three.dimensional character|'
    r'enhance|enhancement|develop his personality)\b', re.I)
SHORT_EQUATION = re.compile(r'^(?:(?:the\s+)?(?:answer|solution|result)\s+is\s+)?'
    r'[^.!?\n]{0,24}?[A-Za-z]\s*=\s*[-+]?\d+(?:\.\d+)?[.!]?$', re.I)
PROSE_LABEL = re.compile(r'\b(?:story|paragraph|reply|narrative|redraft)\b|'
    r'^\s*(?:modified|revised|iteration\s*\d+)\s*:', re.I | re.M)


def repetition_findings(sequence, unit):
    findings = []
    for width, threshold in ((1, 5), (3, 4)):
        starts, counts = {}, {}
        for index in range(max(0, len(sequence) - width + 1)):
            block = tuple(sequence[index:index + width])
            previous = index - width
            count = counts.get(previous, 1) + 1 if starts.get(previous) == block else 1
            starts[index], counts[index] = block, count
            if count == threshold:
                findings.append(dict(unit=unit, width=width, repetitions=count,
                    start_index=index - (count - 1) * width, threshold=threshold))
    return findings


def _unit_evidence(text):
    stripped = text.strip()
    previous = None
    while previous != stripped:
        previous = stripped
        stripped = LABEL.sub('', stripped).strip()
    words = WORD.findall(stripped)
    if not stripped or not words and not re.search(r'\d', stripped):
        return 'unknown', 'empty_or_layout'
    if DEFERRED_QUESTION.search(stripped):
        return 'meta', 'deferred_question_not_an_artifact'
    arithmetic = list(ARITHMETIC.finditer(stripped))
    concrete = (ACTION.search(stripped) and OBJECT.search(stripped)
        and SPECIFIC_METHOD.search(stripped) and len(words) >= 10)
    if concrete:
        return 'content', 'concrete_object_and_method'
    if len(arithmetic) >= 2 or SHORT_EQUATION.fullmatch(stripped) and not META.search(stripped):
        return 'content', 'explicit_calculation_or_equation'
    if (META.search(stripped) or VAGUE_FUTURE.search(stripped)
            or META_REFERENCE.search(stripped) or GENERIC_REVIEW.search(stripped)):
        return 'meta', 'intent_understanding_or_completion_without_artifact'
    if len(words) >= 5 and not stripped.endswith('?') and PREDICATE.search(stripped):
        return 'content', 'substantive_declarative_or_narrative'
    return 'unknown', 'no_bounded_content_evidence'


def scan_target(text, token_ids=None):
    if type(text) is not str:
        raise ValueError('content_filter_original_text_required')
    if len(text) > MAX_SCAN_CHARACTERS:
        return dict(eligible=False, classification='uncertain', units=[], content_units=0,
            meta_units=0, unknown_units=1, scan_truncated=True,
            reason='content_scan_limit_exceeded', scanned_characters=0,
            scan_character_limit=MAX_SCAN_CHARACTERS, correctness_claimed=False)
    units = []
    repeated = repetition_findings(re.findall(r"\w+(?:['’]\w+)*", text.casefold()), 'word')
    if token_ids is not None:
        if not isinstance(token_ids, (list, tuple)) or any(type(token) is not int for token in token_ids):
            raise ValueError('content_filter_original_integer_tokens_required')
        repeated += repetition_findings(token_ids, 'model_token')
    wrapped_prose = []
    prose = list(text)
    for match in FENCE.finditer(text):
        language, body = match.group(2).strip().lower(), match.group(3)
        if language not in ('md', 'markdown', 'text', 'txt', 'plaintext') and PROSE_LABEL.search(text):
            if len(WORD.findall(body)) >= 8:
                wrapped_prose.append(dict(start=match.start(), end=match.end(), language=language,
                    reason='child_labelled_prose_inside_code_fence'))
        if language in ('md', 'markdown', 'text', 'txt', 'plaintext'):
            prose[match.start():match.start(3)] = ' ' * (match.start(3) - match.start())
            prose[match.end(3):match.end()] = ' ' * (match.end() - match.end(3))
            continue
        classification, reason = 'unknown', 'unverified_code_content'
        if language in ('', 'py', 'python', 'python3'):
            try:
                tree = ast.parse(body)
                executable = [node for node in tree.body if not isinstance(node, ast.Pass)
                    and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
                    and not (isinstance(node, ast.AnnAssign) and node.value is None)]
                if executable:
                    classification, reason = 'content', 'syntactically_valid_code_artifact'
            except (SyntaxError, ValueError, RecursionError):
                pass
        units.append(dict(start=match.start(), end=match.end(), classification=classification, reason=reason))
        prose[match.start():match.end()] = ' ' * (match.end() - match.start())
    remainder = ''.join(prose)
    for match in re.finditer(r'[^\n]+', remainder):
        line = match.group()
        for sentence in re.finditer(r'.+?(?:[.!?](?=\s|$)|$)', line):
            unit = sentence.group().strip()
            if not unit or re.fullmatch(r'[\W_]+', unit):
                continue
            classification, reason = _unit_evidence(unit)
            units.append(dict(start=match.start() + sentence.start(), end=match.start() + sentence.end(),
                classification=classification, reason=reason))
    content = sum(unit['classification'] == 'content' for unit in units)
    meta = sum(unit['classification'] == 'meta' for unit in units)
    unknown = sum(unit['classification'] == 'unknown' for unit in units)
    classification = ('mixed' if meta or unknown else 'content') if content else ('meta_only' if meta else 'uncertain')
    eligible = bool(content) and not repeated and not wrapped_prose
    if repeated:
        classification = 'repetition_collapse'
    elif wrapped_prose:
        classification = 'code_wrapped_prose'
    return dict(eligible=eligible, classification=classification, units=units,
        content_units=content, meta_units=meta, unknown_units=unknown, scan_truncated=False,
        scanned_characters=len(text), scan_character_limit=MAX_SCAN_CHARACTERS,
        repetition_findings=repeated, code_wrapped_prose=wrapped_prose, correctness_claimed=False)


def content_exclusions(rows):
    checks, excluded = [], []
    for index, row in enumerate(rows):
        if 'content_target_filter' not in row:
            if 'question_target_filter' in row or 'fabricated_speaker_filter' in row:
                raise ValueError('question_and_speaker_targets_require_content_filter')
            continue
        if row['content_target_filter'] != POLICY:
            raise ValueError('known_content_target_filter_policy')
        if (row.get('actor') != 'child' or row.get('split') != 'TRAIN'
                or row.get('prefix_loss') is not False or row.get('target_loss') is not True):
            raise ValueError('content_filter_child_targets_only')
        evidence = scan_target(row['target'], row.get('token_ids'))
        if 'question_target_filter' in row:
            from organism_v6.orch_r220_question_target_filter import apply_question_policy
            evidence = apply_question_policy(row['target'], evidence, row['question_target_filter'])
        if 'fabricated_speaker_filter' in row:
            from organism_v6.orch_r220_speaker_target_filter import apply_speaker_policy
            evidence = apply_speaker_policy(row['target'], evidence, row['fabricated_speaker_filter'])
        check = dict(source_sha256=row['source_sha256'], segment=row['segment'], cohort='NEW',
            row_index=index, raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
            policy=POLICY, evidence=evidence)
        checks.append(check)
        if not evidence['eligible']:
            reasons = dict(meta_only='meta_only_target', repetition_collapse='repetition_collapse_target',
                code_wrapped_prose='labelled_prose_inside_code_fence',
                fabricated_human_turn='fabricated_human_speaker_target')
            excluded.append(dict(check, reason=reasons.get(evidence['classification'], 'uncertain_content_target')))
    return dict(policy=POLICY, checks=checks, excluded=excluded, raw_modified=False,
        targets_normalized=False, provisional=True, semantic_correctness_claimed=False,
        claim_scope='OPT_IN_CHILD_TARGET_CONTENT_HEURISTIC_NOT_TRUTH_OR_COMPLETION')
