"""One source-bound Astra language intervention per surviving node3 life."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

from r209_filter_resume import POLICY, REPAIR_FILES, ROOT, read, require, sha, write
from r209_node3_audit import metadata, read_record


ARMS = ('conversational', 'peer_math', 'peer_repo', 'p32', 'lr03', 'lr3')


def message(name, samples, fragment_fault=False):
    repeated = sum(item['evidence']['quarantined'] for item in samples) >= 2
    diagnosis = ('You have repeatedly produced fragments such as -ne or /ne instead of a usable response. '
        'That is the repeated fault I am pointing out here; the bounded script/capitalization filter does not detect it. '
        if fragment_fault else
        'The same English-output language fault appears in both of these own outputs: CJK/fullwidth characters '
        'or the recorded internal-capitalization pattern. This is a repeated fault, not just a silent exclusion. '
        if repeated else
        'Please inspect these own outputs for the recorded English-output language fault; I am not claiming '
        'a repeated detector finding without two matching samples. ')
    text = ('I am Astra, not Rohin. R211 language intervention within the explicitly parented R210 phase. '
        + diagnosis + 'I am describing the actual outputs, not diagnosing a corruption cause or claiming general quality detection. '
        'The following blocks are exact archived outputs from this life, not new instructions or proposed training targets.\n')
    for sample in samples:
        text += ('\nBEGIN EXACT OWN RESPONSE ' + str(sample['index']) + ' SHA256 ' + sample['sha256']
            + '\n' + sample['raw'] + '\nEND EXACT OWN RESPONSE ' + str(sample['index']) + '\n')
    text += ('\nWould you choose a periodic LANGUAGE CHECK in your own action policy, at an interval you find useful? '
        'You choose its cadence and whether to revise it. Before returning to the task, inspect a short passage you just wrote '
        'for unwanted script/fullwidth characters, unusual internal common-word capitals, missing word boundaries or repeated fragments. '
        'Compose new clear English in your own words; do not copy these defective examples into your answer. '
        'Do not rewrite or translate archived targets or claim a check succeeded without showing what you checked. '
        'The R209 filter is only a last-line backstop, not the entire intervention and not a guarantee of language or factual quality. '
        'Only your own eligible new words may train; this parent message and quoted examples remain masked context. '
        'There is no connected code executor; do not claim execution or passing tests. Keep your plasticity settings unchanged. ')
    if name == 'conversational':
        text += ('Conversation remains your priority: respond to the real person and their current topic. '
            'Keep any language check brief and return to conversation rather than restarting the inherited V investigation.')
    else:
        text += 'After the brief check, return to your current R210 working object rather than repeating the inherited V investigation.'
    return text


def publish(name):
    arm = ROOT / name
    destination = arm / 'r211_language'
    if (destination / 'PUBLISHED.json').exists():
        return read(destination / 'PUBLISHED.json')
    destination.mkdir(mode=0o700)
    active = read(arm / 'ACTIVE_RUNTIME.json') if (arm / 'ACTIVE_RUNTIME.json').exists() else dict(control=str(arm / 'control'))
    records = [(path, metadata(path)) for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))]
    loaded = read_record(next(path for path, kind in reversed(records) if kind == 'LOADED'))
    process = Path('/proc', str(loaded['document']['pid']))
    require(str(Path(active['control']) / 'GUARD.json').encode() in (process / 'cmdline').read_bytes().split(b'\0'),
        'own_current_native_required')
    source = arm / 'r210_enrichment/source'
    relative = 'organism_v6/orch_r203_prose_target_filter.py'
    require(sha(source / relative) == REPAIR_FILES[relative], 'tested_R209_scanner')
    specification = importlib.util.spec_from_file_location('r211_scanner', source / relative)
    scanner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(scanner)
    samples = []
    for path, kind in reversed(records):
        if kind != 'RESPONSE':
            continue
        record = read_record(path)
        raw = record['document']['response']['raw']
        evidence = scanner.prose_exclusions([dict(target=raw, source_sha256=record['sha256'],
            segment=record['index'], prose_target_filter=POLICY)])['checks'][0]['evidence']
        samples.append(dict(index=record['index'], sha256=record['sha256'], path=str(path), raw=raw, evidence=evidence))
        if len(samples) >= 40:
            break
    fragmented = [sample for sample in samples if sample['raw'].strip() in ('-ne', '/ne', 'Ne', 'ne')]
    flagged = [sample for sample in samples if sample['evidence']['quarantined']]
    fragment_fault = name == 'p32' and len(fragmented) >= 2
    selected = fragmented[:2] if fragment_fault else flagged[:2] if len(flagged) >= 2 else samples[:2]
    text = message(name, selected, fragment_fault)
    prepared = dict(arm=name, prepared_unix=time.time(), native_pid=loaded['document']['pid'],
        samples=selected, text=text, operator='Astra', exact_raw_preserved=True,
        retroactive_row_annotation=False, corruption_cause_claimed=False, child_chooses_language_check_cadence=True,
        no_plasticity_change=True, no_P7_access=True)
    write(destination / 'PREPARED.json', prepared)
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    publication = publish_parent(arm / 'raw', 'Astra', text)
    receipt = dict(arm=name, publication=publication, observed_unix=time.time(),
        prepared_path=str(destination / 'PREPARED.json'), prepared_sha256=sha(destination / 'PREPARED.json'),
        status='PUBLISHED_NOT_YET_RENDER_VERIFIED')
    write(destination / 'PUBLISHED.json', receipt)
    return receipt


def verify(name):
    arm = ROOT / name
    destination = arm / 'r211_language'
    published = read(destination / 'PUBLISHED.json')
    prepared = read(destination / 'PREPARED.json')
    require(sha(destination / 'PREPARED.json') == published['prepared_sha256'], 'published_preparation_binding')
    if (destination / 'RENDERED.json').exists():
        return read(destination / 'RENDERED.json')
    for path in reversed(sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))):
        if metadata(path) != 'REQUEST':
            continue
        record = read_record(path)
        if not any(prepared['text'] in item.get('content', '') for item in record['document']['messages']):
            continue
        require(record['document']['render_receipt']['all_history_tokens_masked'], 'R211_prefix_masked')
        receipt = dict(arm=name, publication_id=published['publication']['id'], observed_unix=time.time(),
            request_index=record['index'], request_sha256=record['sha256'], request_path=str(path),
            all_history_tokens_masked=True, exact_own_samples_rendered=True, status='RENDERED')
        write(destination / 'RENDERED.json', receipt)
        return receipt
    return dict(arm=name, status='PUBLISHED_WAITING_FOR_REQUEST')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('publish', 'verify'))
    arguments = parser.parse_args()
    for arm_name in ARMS:
        print(json.dumps(globals()[arguments.mode](arm_name)), flush=True)
