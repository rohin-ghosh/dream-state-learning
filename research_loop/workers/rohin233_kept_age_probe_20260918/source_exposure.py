"""Supplement identifier audit using actual prompt and checkpoint-context text."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import time


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def shingles(text, width=5):
    words = re.findall(r'[a-z]+', text.casefold())
    return {tuple(words[index:index+width]) for index in range(len(words)-width+1)}


def audit(life, scenes, capture):
    probes = {row['contest_id']: shingles(row['canonical_scene'].split('\n')[0]) for row in scenes['contests']}
    matches = {key: [] for key in probes}
    maximum = {key: 0 for key in probes}
    scanned, inherited = 0, 0
    sleep_indices = {row['sleep_complete_index'] for row in capture['sources']}
    for path in sorted((life/'stream/records').iterdir()):
        if not re.fullmatch(r'\d{20}\.json', path.name) or int(path.stem) > capture['head_index']:
            continue
        record = json.loads(path.read_bytes())
        if record['kind'] == 'REQUEST':
            contents = record['document']['messages']
            scanned += 1
        elif record['index'] in sleep_indices:
            contents = record['document'].get('resume_state', {})
            inherited += 1
        elif record['kind'] == 'INBOX':
            contents = record['document']
        else:
            continue
        for text in strings(contents):
            if len(text) < 20:
                continue
            source = shingles(text)
            for key, probe in probes.items():
                overlap = len(probe & source)
                maximum[key] = max(maximum[key], overlap)
                if overlap >= 3 or overlap / max(1, len(probe)) >= 0.15:
                    matches[key].append(record['index'])
    return dict(schema='R232_SOURCE_SCENE_EXPOSURE_AUDIT_V1', unix=time.time(),
        eligible=not any(matches.values()) and capture['exposure']['complete'],
        selected_contests=list(probes), matched_record_indices={key: sorted(set(value)) for key, value in matches.items()},
        maximum_shared_fivegrams=maximum, requests_scanned=scanned, completed_source_states_scanned=inherited,
        source_cut_index=capture['head_index'], source_cut_sha256=capture['head_sha256'],
        scenes_sha256=hashlib.sha256(json.dumps(scenes, sort_keys=True).encode()).hexdigest(),
        method='identifier_image_hash_audit_plus_prompt_and_inherited_context_fivegram_overlap',
        limits='Recorded source-life exposures only; not a claim of unseen base pretraining or exhaustive semantic paraphrase detection.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--life', type=Path, required=True)
    parser.add_argument('--scenes', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.life, json.loads(args.scenes.read_bytes()), json.loads(args.capture.read_bytes()))))
