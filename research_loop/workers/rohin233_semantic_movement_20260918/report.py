"""Project source-bound manual judgments without publishing conversation text."""

from collections import Counter
import json
import re

from annotations import CUT_SHA256, REVIEWS
from prepare import CANON, CANONICAL, OWN, act_pairs, event_key, sha, utc


def verify_bytes(raw, expected):
    if sha(raw) != expected:
        raise ValueError('source_hash_changed')


def event_catalog(evidence):
    catalog = {}
    for frame in CANON.frames(evidence):
        for event in frame['request']['external']:
            key = event_key(event)
            if key not in catalog:
                catalog[key] = dict(event=event, requests=[])
            elif event != catalog[key]['event']:
                raise ValueError('inconsistent_rendered_event')
            catalog[key]['requests'].append(frame['request'])
    return catalog


def event_ref(entry):
    event = entry['event']
    return dict(event_id=event['event_id'], source_sha256=event['source_sha256'],
                text_sha256=CANON.text_sha(event['text']), actor=event['actor'],
                first_rendered_in_window=CANON.ref(entry['requests'][0]),
                last_rendered_in_window=CANON.ref(entry['requests'][-1]))


def resolve(catalog, event_id):
    matches = [entry for entry in catalog.values() if entry['event']['event_id'] == event_id]
    if len(matches) != 1:
        raise ValueError('one_exact_rendered_event_required')
    return matches[0]


def require_evaluator(event):
    allowed = ('Tool: {', 'Tool: Existing caption-game feedback.', 'Tool: Caption-game judgment ')
    if event['actor'] != 'environment' or event.get('phase') != 'feedback' or not event['text'].startswith(allowed):
        raise ValueError('not_attributed_evaluator_feedback')


def response_link(event, frame):
    require_evaluator(event)
    response = frame['response']
    payload = json.loads(event['text'].removeprefix('Tool: '))
    if payload['response_record'] != response['index'] or payload['response_digest'] != response['sha256']:
        raise ValueError('response_identity_mismatch')
    return dict(method='exact_response_index_and_record_sha256', response=CANON.ref(response),
                error=payload.get('error'), recovered_count=payload.get('format_status', {}).get('recovered_count'),
                scored_observations=len(payload.get('observations', [])), scorer_receipt=payload.get('scorer_receipt'))


def caption_matches(event, frame, numbers):
    require_evaluator(event)
    pattern = r'Caption (\d+), scene [^\n]+, source ACT: "([^\n]+)"\nRank (\d+)/(\d+); accepted=(true|false); novelty=([^;]+);'
    parsed = {int(match[0]): match for match in re.findall(pattern, event['text'])}
    results = []
    for number in numbers:
        if number not in parsed:
            raise ValueError('caption_not_in_evaluator')
        _, literal, rank, panel, accepted, novelty = parsed[number]
        start = frame['response']['text'].find(literal)
        if start < 0:
            raise ValueError('caption_not_in_selected_response')
        results.append(dict(caption_number=number, rank=int(rank), panel=int(panel),
                            accepted=accepted == 'true', novelty=novelty,
                            response=CANON.ref(frame['response']), start=start, end=start + len(literal),
                            literal_sha256=CANON.text_sha(literal),
                            method='exact_literal_only_not_unique_submission_identity'))
    return results


def selected_ref(frame):
    response = frame['response']
    return CANON.validate_span(frame, dict(index=response['index'], sha256=response['sha256'],
                              start=0, end=len(response['text']), span_sha256=CANON.text_sha(response['text'])))


def life_report(evidence, annotation):
    ordered = CANON.frames(evidence)
    pair = act_pairs(evidence)
    if len(pair) != 2 or [frame['response']['index'] for frame in pair] != [act['index'] for act in annotation['acts']]:
        raise ValueError('last_two_ACT_identity_mismatch')
    preceding = [frame for frame in ordered if frame['stage'] == 'THINK' and frame['response']['index'] < pair[0]['response']['index']]
    start = preceding[-1]['request']['index'] if preceding else pair[0]['request']['index']
    end = pair[-1]['request']['index']
    catalog = event_catalog(evidence)
    parents = [entry for entry in catalog.values() if entry['event']['actor'] == 'parent'
               and any(start <= request['index'] <= end for request in entry['requests'])]
    new_between = [entry for entry in catalog.values()
                   if pair[0]['response']['index'] < entry['requests'][0]['index'] <= end
                   and (entry['event']['actor'] == 'parent' or entry['event']['text'].startswith('Tool:'))]
    reviewed = [resolve(catalog, event_id) for event_id in annotation['event_ids']]
    parent_refs = [event_ref(entry) for entry in parents]
    latest_parents = sorted(parent_refs, key=lambda item: item['first_rendered_in_window']['index'])[-3:]
    result = dict(journal_id=evidence['journal_id'],
                  acts=[dict(**assessment, source=selected_ref(frame),
                             response_utc=utc(frame['response']['time_unix']))
                        for frame, assessment in zip(pair, annotation['acts'])],
                  checked_result=annotation['checked_result'], recent_parent=annotation['recent_parent'],
                  next_artifact=annotation['next_artifact'], movement_status=annotation['movement_status'],
                  recent_request_interval=dict(start=start, end=end),
                  recent_rendered_parent_event_count=len(parent_refs),
                  recent_parent_refs_sha256=CANON.text_sha(json.dumps(parent_refs, sort_keys=True)),
                  latest_three_rendered_parents=latest_parents,
                  total_parent_events_in_evidence=len([entry for entry in catalog.values() if entry['event']['actor'] == 'parent']),
                  newly_visible_guidance_or_Tool_between_ACTs=[event_ref(entry) for entry in new_between],
                  reviewed_context=[event_ref(entry) for entry in reviewed],
                  adapter_improvement='unknown_not_tested_by_this_review')
    return result, pair, catalog


def build():
    cut_raw = (OWN / 'private/CUT.json').read_bytes()
    verify_bytes(cut_raw, CUT_SHA256)
    cut = json.loads(cut_raw)
    verify_bytes(CANONICAL.read_bytes(), cut['canonical_frames_source']['sha256'])
    if {item['label'] for item in cut['inputs']} != set(REVIEWS) or len(cut['inputs']) != 16:
        raise ValueError('exactly_16_reviewed_lives_required')
    lives = []
    for source in cut['inputs']:
        raw = (OWN / 'private' / source['label'] / 'EVIDENCE.json').read_bytes()
        verify_bytes(raw, source['evidence_sha256'])
        evidence = json.loads(raw)
        result, pair, catalog = life_report(evidence, REVIEWS[source['label']])
        result['label'] = source['label']
        result['input'] = {key: source[key] for key in ('source_path', 'evidence_sha256', 'evidence_bytes', 'observed_utc', 'coverage_start', 'caught_up')}
        result['input']['through'] = CANON.ref(source['through'])
        result['tool_links'] = []
        if source['label'] == 'GAME_N3_0':
            entry = resolve(catalog, 'environment:inbox:f0cdfe2615e6498b949bf95ea23119b7')
            result['tool_links'].append(dict(event=event_ref(entry), matches=caption_matches(entry['event'], pair[1], [1, 2]),
                                             excluded_scored_meta_items=[3]))
        elif source['label'] == 'GAME_UNPARENTED_N2':
            for frame in pair:
                entry = resolve(catalog, 'caption:' + frame['response']['sha256'])
                result['tool_links'].append(dict(event=event_ref(entry), link=response_link(entry['event'], frame)))
        elif source['label'] == 'GAME1_P3':
            entry = resolve(catalog, 'environment:inbox:4f32bb8d69774e9f8bef2f7d379104b6')
            require_evaluator(entry['event'])
            match = re.search(r'ACT response (\d+) \(([a-f0-9]{12})\)', entry['event']['text'])
            if not match or int(match[1]) != pair[0]['response']['index'] or match[2] != pair[0]['response']['sha256'][:12]:
                raise ValueError('short_response_identity_mismatch')
            result['tool_links'].append(dict(event=event_ref(entry), response=CANON.ref(pair[0]['response']),
                                             method='response_index_and_12_hex_record_sha_prefix', status='no_judgment'))
        lives.append(result)
    report = dict(schema='R233_SEMANTIC_MOVEMENT_V1', prepared_utc=cut['prepared_utc'],
                  cut_start=min(source['observed_utc'] for source in cut['inputs']),
                  cut_end=max(source['observed_utc'] for source in cut['inputs']),
                  private_cut_sha256=CUT_SHA256, canonical_frames_source=cut['canonical_frames_source'],
                  review_source_sha256={name: sha((OWN / name).read_bytes()) for name in ('annotations.py', 'prepare.py', 'report.py')},
                  method='Manual semantic review of exactly the last two canonical committed ACTs per frozen source; not keyword classification.',
                  limits=['Non-simultaneous evidence collection, not current runtime status.',
                          'Projection is hash-bound but does not independently reverify remote journals; R184_ACT execution receipts are not included.',
                          'First visible event means first within this window, not delivery time; retained context may be left-censored.',
                          'Recent parents are those rendered from the THINK preceding the first ACT through the second ACT request. Counts cover all events; only the latest three by first visibility are projected, with a hash of the complete reference list.',
                          'A concrete attempt may be wrong or off task; plans, meta code and promises do not count as task artifacts.',
                          'Feedback may precede a changed artifact without causing it; no retention, adaptation or fleet success-rate inference.',
                          'Tool-prefixed child/peer replies are not independent evaluator evidence.',
                          'This sample excludes services and non-native players outside the 16 supplied roots.'],
                  summary=dict(lives=len(lives), acts=sum(len(life['acts']) for life in lives),
                               categories=dict(Counter(act['category'] for life in lives for act in life['acts'])),
                               lives_with_recent_rendered_parent=sum(bool(life['recent_rendered_parent_event_count']) for life in lives)), lives=lives)
    public = json.dumps(report, ensure_ascii=True, indent=2) + '\n'
    for source in cut['inputs']:
        evidence = json.loads((OWN / 'private' / source['label'] / 'EVIDENCE.json').read_bytes())
        for frame in CANON.frames(evidence):
            texts = [frame['response']['text']] + [event['text'] for event in frame['request']['external']]
            for text in texts:
                if len(text) >= 50 and (text in public or json.dumps(text, ensure_ascii=True)[1:-1] in public):
                    raise ValueError('raw_turn_in_public_projection')
    return report


def markdown(report):
    lines = ['# R233 semantic movement: frozen 16-life cut', '',
             f"Collection cut: **{report['cut_start']} through {report['cut_end']}** (UTC). Not simultaneous or a live-status report.", '',
             'Exactly 32 committed ACTs, two per life. Concrete means substantive attempted content, not correctness, execution, novelty or task completion.',
             'All judgments are manual and source-bound; REPORT.json carries input SHA256s, journal/record identities, full-response span hashes and rendered-event references. Raw turns remain private.', '',
             '## 16-life review', '',
             '| Life | ACT records / artifact classification | Checked result | Recent rendered parent | Next artifact after available feedback |',
             '|---|---|---|---|---|']
    for life in report['lives']:
        acts = '; '.join(f"{act['index']}: {act['category']}" for act in life['acts'])
        cells = [life['label'], acts, life['checked_result'], life['recent_parent'], life['next_artifact']]
        lines.append('| ' + ' | '.join(cell.replace('|', '\\|') for cell in cells) + ' |')
    lines.extend(['', '## Boundaries', ''] + ['- ' + limit for limit in report['limits']])
    lines.extend(['', '## Exact source cuts', '', '| Life | Observed UTC | Journal coverage start / head | ACT UTC timestamps |', '|---|---|---|---|'])
    for life in report['lives']:
        source = life['input']
        lines.append(f"| {life['label']} | {source['observed_utc']} | {source['coverage_start']} / {source['through']['index']} | " + '; '.join(act['response_utc'] for act in life['acts']) + ' |')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    result = build()
    (OWN / 'REPORT.json').write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n')
    (OWN / 'REPORT.md').write_text(markdown(result))
    print(json.dumps(result['summary'], sort_keys=True))
