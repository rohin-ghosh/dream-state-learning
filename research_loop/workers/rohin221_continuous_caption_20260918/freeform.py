"""Literal freeform caption extraction; no model calls, scoring, or execution."""

import hashlib
import re
import unicodedata


FORMAT_POLICY = 'R223_FREEFORM_CAPTION_QA_V1'


def extract_batches(raw, scenes, *, explicit_candidates_only=False):
    if not isinstance(raw, str) or len(raw.encode()) > 65536:
        raise ValueError('bounded_ACT_text')
    roster = [dict(contest_id=scene) if isinstance(scene, str) else scene for scene in scenes]
    if not roster or any(not isinstance(scene.get('contest_id'), str) for scene in roster):
        raise ValueError('scene_roster')

    def resolve(hint):
        hint = unicodedata.normalize('NFKC', hint).strip(' .:#').casefold()
        hint = re.sub(r'^(?:here\s+are\s+)?(?:captions?|jokes?|options?|candidates?)\s+(?:for|about)\s+', '', hint)
        hint = re.sub(r'^the\s+|\s+(?:scene|cartoon)$', '', hint)
        if re.fullmatch(r'[0-9]+', hint):
            number = int(hint)
            return roster[number - 1]['contest_id'] if 1 <= number <= len(roster) else None
        if not hint or '/' in hint or '\\' in hint or '..' in hint:
            return None
        found = []
        for scene in roster:
            aliases = [scene.get(key, '') for key in ['name', 'title', 'label', 'canonical_scene']]
            aliases += scene.get('aliases', [])
            matched = any(hint == unicodedata.normalize('NFKC', alias).strip().casefold() for alias in aliases)
            if not matched and len(hint) >= 4 and len(hint.split()) <= 5:
                matched = bool(re.search(r'(?<!\w)' + re.escape(hint) + r'(?!\w)',
                    unicodedata.normalize('NFKC', scene.get('canonical_scene', '')).casefold()))
            if matched:
                found.append(scene['contest_id'])
        return found[0] if len(found) == 1 else None

    groups, sources, unparsed = {}, [], []
    current, declared, offset, fenced, unprefixed = None, None, 0, False, 0
    for number, full_line in enumerate(raw.splitlines(keepends=True), 1):
        line = full_line.rstrip('\r\n')
        base, offset = offset, offset + len(full_line)
        if not line.strip():
            continue
        if line.strip().startswith('```'):
            fenced = not fenced
            unparsed.append(dict(line=number, text=line, reason='code_not_executed'))
            continue
        if fenced or re.match(r'\s*(?:import\s|from\s+\w+\s+import\s|__import__\s*\(|exec\s*\()', line):
            unparsed.append(dict(line=number, text=line, reason='code_not_executed'))
            continue
        field = re.fullmatch(r'\s*(Count|Direction|Check|Incorporation|Explanation)\s*[:：]\s*(.*)', line, re.I)
        if field:
            if field.group(1).casefold() == 'count':
                value = unicodedata.normalize('NFKC', field.group(2)).strip()
                declared = int(value) if re.fullmatch(r'[0-9]{1,6}', value) else None
            continue
        routed = re.search(r'\b(?:scene|cartoon)\s*[:：#]?\s*([0-9０-９]+)\b', line, re.I)
        named = re.fullmatch(r'\s*(?:for\s+)?([^:：]{1,160})[:：]\s*(.*)', line, re.I)
        header = bool(routed and (re.match(r'\s*(?:for\s+)?(?:scene|cartoon)(?=\s|[:：#0-9０-９])', line, re.I)
            or re.search(r'\b(?:captions?|jokes?|options?|candidates?)\s+(?:for|about)\s+(?:the\s+)?(?:scene|cartoon)', line, re.I)))
        if header or (named and resolve(named.group(1)) is not None):
            current = resolve(routed.group(1)) if header else resolve(named.group(1))
            if current is None:
                unparsed.append(dict(line=number, text=line, reason='scene_not_unambiguously_identified'))
                continue
            tail_start = routed.end() if header else named.start(2)
            tail = line[tail_start:]
            inline = re.match(r'\s*[:：—–-]\s*(.+)', tail) if header else re.match(r'(.+)', tail)
            if inline is None:
                continue
            base += tail_start + inline.start(1)
            line = inline.group(1)
        elif re.match(r'\s*(?:scene|cartoon)\s*[:：#]', line, re.I):
            hint = re.split(r'[:：#]', line, maxsplit=1)[1]
            current = resolve(hint)
            if current is None:
                unparsed.append(dict(line=number, text=line, reason='scene_not_unambiguously_identified'))
            continue
        elif named and (not named.group(2).strip() or re.match(r'\s*for\s+', line, re.I)):
            current = None
            unparsed.append(dict(line=number, text=line, reason='scene_not_unambiguously_identified'))
            continue
        if re.match(r'\s*(?:Question|Clarification|Feedback)\s*[:：?]', line, re.I) or (
                re.match(r'\s*(?:how|what|can|could|should|which)\b', line, re.I)
                and line.rstrip().endswith('?') and re.search(r'\b(?:submit|rank|score|format|rules|novelty|accepted)\b', line, re.I)):
            unparsed.append(dict(line=number, text=line, reason='question_for_next_input'))
            continue
        prefix = re.match(r'\s*(?:(?:[-*•]|\d+[.)])\s+)?(?:(?:Caption|Option|Candidate)(?:\s+[A-Za-z0-9]+)?\s*[:：][ \t]?)?', line, re.I)
        start, end = prefix.end(), len(line)
        text = line[start:end]
        labelled = bool(re.search(r'\b(?:caption|option|candidate)\b', line[:start], re.I))
        bullet = bool(re.match(r'\s*(?:[-*•]|\d+[.)])\s+', line))
        quoted = len(text.strip()) >= 2 and (text[0], text.rstrip()[-1]) in [('"','"'),("'","'"),('“','”'),('‘','’')]
        if quoted:
            end = start + len(text.rstrip()) - 1
            start += 1
            text = line[start:end]
        commentary = bool(re.match(r'\s*(?:these\s+(?:captions|jokes|options)|both\s+(?:captions|jokes)|'
            r'I\s+(?:hope|think|chose|chose|will)|let\s+me\s+know|please\s+(?:rank|score|judge)|'
            r'hope\s+(?:these|you)|they\s+(?:both|aim)|this\s+(?:captures|caption)|'
            r'now\s+(?:please|we)|ready\s+for)\b', line, re.I))
        if not (labelled or quoted or bullet) and commentary:
            unparsed.append(dict(line=number, text=line, reason='commentary_not_caption'))
            continue
        if explicit_candidates_only and not (labelled or quoted or bullet):
            continue
        if current is None or not text.strip():
            unparsed.append(dict(line=number, text=line, reason='scene_not_unambiguously_identified'))
            continue
        if len(text.split()) > 50 or len(text.encode()) > 4096 or len(sources) >= 100:
            unparsed.append(dict(line=number, text=line, reason='caption_resource_bounds'))
            continue
        captions = groups.setdefault(current, [])
        captions.append(text)
        unprefixed += int(not labelled)
        sources.append(dict(contest_id=current, caption_ordinal=len(captions), line=number,
            start=base + start, end=base + end, text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    actions = [dict(tool='caption_batch', contest_id=contest, direction='Freeform child captions',
                    count=len(captions), captions=captions) for contest, captions in groups.items()]
    unresolved = [item for item in unparsed if item['reason'] != 'commentary_not_caption']
    reason = None if actions else ('scene_not_unambiguously_identified' if current is None else 'no_readable_bounded_caption_lines')
    return actions, dict(format_policy=FORMAT_POLICY, format_fault=bool(unresolved) or not actions,
        clarification_needed=bool(unresolved) or not actions,
        unparsed_lines=[dict(item, text=item['text'][:256]) for item in unparsed[:32]],
        unparsed_line_count=len(unparsed), unscored_reason=reason,
        declared_count=declared, recovered_count=len(sources), unprefixed_lines=unprefixed,
        caption_sources=sources, caption_text_normalized=False, planned_count_required=False)


def extract_batch(raw, scenes):
    actions, metrics = extract_batches(raw, scenes)
    if len(actions) > 1:
        return None, dict(metrics, unscored_reason='multiple_scenes_use_extract_batches', format_fault=True)
    if metrics['declared_count'] is not None:
        metrics['format_fault'] |= metrics['declared_count'] != metrics['recovered_count'] or bool(metrics['unprefixed_lines'])
    return (actions[0] if actions else None), metrics
