"""Read-only coherent adapter capture and identifier-based lifetime exposure audit."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def capture(life, output, candidates):
    records = sorted(path for path in (life / 'stream/records').iterdir()
        if re.fullmatch(r'\d{20}\.json', path.name))
    cut = json.loads(records[-1].read_bytes())
    sleeps = {}
    for path in reversed(records):
        record = json.loads(path.read_bytes())
        document = record['document']
        if record['kind'] == 'SLEEP_COMPLETE' and document.get('status') == 'COMPLETE':
            sleeps.setdefault(document['cycle'], (record, path))
            if 51 in sleeps and max(sleeps) > 51:
                break
    chosen = [51, max(sleeps)]
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    sources = []
    for cycle in chosen:
        record, record_path = sleeps[cycle]
        checkpoint = life / 'checkpoints' / f'sleep_{cycle:06d}'
        commit_path = checkpoint / 'COMMIT.json'
        commit = json.loads(commit_path.read_bytes())
        assert commit['optimizer_steps'] == record['document']['total_optimizer_steps']
        assert commit['adapter_state_sha256'] == record['document']['after_adapter_sha256']
        targets = ['COMMIT.json'] + ['adapter/' + name for name in commit['adapter_files']]
        assert all(Path(name).name == name for name in commit['adapter_files'])
        assert set(commit['adapter_files']) == {'README.md', 'adapter_config.json', 'adapter_model.safetensors'}
        before = {name: dict(sha256=sha(checkpoint/name), bytes=(checkpoint/name).stat().st_size,
            mtime_ns=(checkpoint/name).stat().st_mtime_ns) for name in targets}
        destination = output / f'sleep_{cycle:06d}'
        (destination / 'adapter').mkdir(parents=True)
        for name in targets:
            shutil.copyfile(checkpoint/name, destination/name)
            assert sha(destination/name) == before[name]['sha256']
        after = {name: dict(sha256=sha(checkpoint/name), bytes=(checkpoint/name).stat().st_size,
            mtime_ns=(checkpoint/name).stat().st_mtime_ns) for name in targets}
        assert before == after
        sources.append(dict(absolute_sleep=cycle, relative_sleep=cycle-51,
            optimizer_steps=commit['optimizer_steps'], relative_optimizer_steps=commit['optimizer_steps']-4908,
            adapter_state_sha256=commit['adapter_state_sha256'], base_sha256=commit['base_sha256'],
            checkpoint_created_unix=commit['created_unix'], sleep_complete_index=record['index'],
            sleep_complete_sha256=record['sha256'], sleep_complete_file_sha256=sha(record_path),
            copy_files=before, before_after_equal=True, cumulative_training_tokens=None,
            cumulative_training_seconds=None, source_relative=f'sleep_{cycle:06d}'))
    patterns = {}
    for candidate in candidates:
        identifier = str(candidate['contest_id'])
        handle = 'agentdev_' + hashlib.sha256(identifier.encode()).hexdigest()[:20]
        patterns[identifier] = re.compile('|'.join([re.escape(handle), re.escape(candidate['image_sha256']),
            r'(?i:contest|cartoon|scene)[\s_:#-]*' + re.escape(identifier) + r'\b',
            r'(?<!\d)' + re.escape(identifier) + r'\.(?:jpg|png)']))
    matched = {identifier: [] for identifier in patterns}
    request_count, unresolved = 0, 0
    input_hashes = []
    for path in records:
        record = json.loads(path.read_bytes())
        if record['kind'] not in ('REQUEST', 'INBOX'):
            continue
        document = record['document']
        if record['kind'] == 'REQUEST':
            request_count += 1
            messages = document.get('messages')
            if not isinstance(messages, list):
                unresolved += 1
                continue
            texts = []
            for message in messages:
                content = message.get('content')
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    for part in content:
                        if part.get('type') == 'text':
                            texts.append(part['text'])
                        else:
                            unresolved += 1
                else:
                    unresolved += 1
            text = '\n'.join(texts)
        else:
            text = json.dumps(document, ensure_ascii=False)
        input_hashes.append(dict(index=record['index'], kind=record['kind'], sha256=record['sha256']))
        for identifier, pattern in patterns.items():
            if pattern.search(text):
                matched[identifier].append(record['index'])
    result = dict(schema='R232_DURABLE_SOURCE_CAPTURE_V1', unix=time.time(),
        life_source_alias='original_C2', head_index=cut['index'], head_sha256=cut['sha256'],
        sources=sources, exposure=dict(complete=unresolved == 0, request_count=request_count,
            unresolved_request_content=unresolved, excluded_contest_ids=[key for key, values in matched.items() if values],
            matches=matched, input_record_manifest_sha256=hashlib.sha256(canonical(input_hashes)).hexdigest(),
            method='all_recorded_REQUEST_text_plus_INBOX_identifiers_and_image_hashes',
            limitation='unidentified_paraphrased_scene_exposure_requires_separate_description_overlap_check'))
    (output / 'CAPTURE.json').write_bytes(canonical(result) + b'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--life', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidates', type=Path, required=True)
    args = parser.parse_args()
    capture(args.life, args.output, json.loads(args.candidates.read_bytes()))
