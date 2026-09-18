"""Read a coherent queued adapter and audit source exposure before any GPU use."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True)


def prepare(root, source_root, original, queued, life):
    if root.exists() or root.resolve() != root or queued.is_symlink():
        raise ValueError('new_canonical_probe_root')
    source = read(queued / 'SOURCE.json')
    for name, expected in source['copy_files'].items():
        if sha(queued / name) != expected['sha256']:
            raise ValueError('immutable_queue_copy_changed')
    old_manifest = read(source_root / 'SOURCE_MANIFEST.json')
    if any(sha(source_root / 'source' / name) != checksum for name, checksum in old_manifest.items()):
        raise ValueError('old_frozen_source_closure_changed')
    root.mkdir(mode=0o700)
    shutil.copytree(source_root / 'source', root / 'source', ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('probe.py', 'prepare_probe.py', 'enroll.py', 'source_exposure.py'):
        destination = root / 'source/research_loop/workers/rohin233_kept_age_probe_20260918' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).parent / name, destination)
    shutil.copytree(original / 'assets', root / 'assets')
    for name in ('GAME_MANIFEST.json', 'SELECTION.json'):
        shutil.copyfile(original / name, root / name)
    (root / 'judge').mkdir()
    shutil.copyfile(original / 'judge/REFERENCE_PANELS.private.json', root / 'judge/REFERENCE_PANELS.private.json')
    destination = root / 'sources' / source['source_relative']
    for name in source['copy_files']:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(queued / name, target)
        if sha(target) != source['copy_files'][name]['sha256'] or sha(queued / name) != source['copy_files'][name]['sha256']:
            raise ValueError('before_copy_after_source_identity')
    cut = source['sleep_complete_index']
    sys.path.insert(0, str(root / 'source'))
    from research_loop.workers.rohin233_kept_age_probe_20260918 import enroll, source_exposure as exposure
    complete = enroll.read_record(life / 'stream/records' / f'{cut:020d}.json', source,
        source['sleep_complete_sha256'])
    if (complete['document']['total_optimizer_steps'] != source['optimizer_steps']
            or complete['document']['after_adapter_sha256'] != source['adapter_state_sha256']):
        raise ValueError('same_completed_sleep_source')
    scenes = read(root / 'GAME_MANIFEST.json')
    selection = read(root / 'SELECTION.json')
    identifiers = selection['selected']
    image_packet = read(original / 'images/IMAGE_PACKET.json')
    image_refs = {row['handle']: row for row in image_packet['images']}
    if image_packet['mode'] != 'DEVELOPMENT' or any(sha(Path(row['path'])) != row['sha256']
            for row in image_packet['images']):
        raise ValueError('original_released_development_images')
    if any(scene['split'] != 'agent_development' or scene['contest_id'] !=
            'agentdev_' + hashlib.sha256(identifier.encode()).hexdigest()[:20]
            for identifier, scene in zip(identifiers, scenes['contests'], strict=True)):
        raise ValueError('same_development_selection_order')
    signatures = [re.compile('|'.join([re.escape(scene['contest_id']), re.escape(image_refs[scene['image']]['sha256']),
        r'(?i:contest|cartoon|scene)[\s_:#-]*' + re.escape(identifier) + r'\b',
        r'(?<!\d)' + re.escape(identifier) + r'\.(?:jpg|png)']))
        for identifier, scene in zip(identifiers, scenes['contests'], strict=True)]
    matches = {identifier: [] for identifier in identifiers}
    checked = []
    unresolved = []
    for path in sorted((life / 'stream/records').iterdir()):
        if not re.fullmatch(r'\d{20}\.json', path.name) or int(path.stem) > cut:
            continue
        record = enroll.read_record(path, source)
        if record['kind'] not in ('REQUEST', 'INBOX', 'SLEEP_COMPLETE', 'LOADED'):
            continue
        document = record['document']
        if record['kind'] == 'REQUEST':
            if not isinstance(document.get('messages'), list):
                unresolved.append(record['index'])
            elif any(not isinstance(message.get('content'), str) for message in document['messages']):
                unresolved.append(record['index'])
        texts = list(exposure.strings(document))
        for identifier, pattern in zip(identifiers, signatures, strict=True):
            if any(pattern.search(text) for text in texts):
                matches[identifier].append(record['index'])
        checked.append(dict(index=record['index'], sha256=record['sha256']))
    capture = dict(head_index=cut, head_sha256=source['sleep_complete_sha256'], sources=[source],
        exposure=dict(complete=not unresolved, identifier_matches=matches,
            unresolved_request_records=unresolved, checked_records=len(checked),
            input_manifest_sha256=enroll.digest(checked)),
        inherited_context_audited_not_loaded=True)
    semantic = exposure.audit(life, scenes, capture)
    semantic['identifier_matches'] = matches
    semantic['eligible'] = semantic['eligible'] and not any(matches.values()) and not unresolved
    if not semantic['eligible']:
        write(root / 'EXPOSURE_INELIGIBLE.json', semantic)
        raise ValueError('fresh_development_scene_exposure_unresolved_or_seen')
    source['source_name'] = 'R231_FRESH_LEARNING_BIRTH'
    condition = 'R233_FRESH_R231_s' + str(source['absolute_sleep'])
    identity = read(source_root / 'CONDITION.json')
    identity.update(condition=condition, source_name=source['source_name'], absolute_sleep=source['absolute_sleep'],
        sleep_complete_sha256=source['sleep_complete_sha256'], parent_tokens=0,
        original_results_immutable=True, optimizer_loaded=False, source_parent_text_loaded=False)
    write(root / 'CONDITION.json', identity)
    write(root / 'sources/CAPTURE.json', capture)
    write(root / 'FRESHNESS_VERIFIED.json', semantic)
    (root / 'queue').mkdir()
    manifest = {str(path.relative_to(root / 'source')): sha(path) for path in (root / 'source').rglob('*')
        if path.is_file() and '__pycache__' not in path.parts}
    write(root / 'SOURCE_MANIFEST.json', manifest)
    from research_loop.workers.rohin233_kept_age_probe_20260918.probe import same_battery
    same_battery(root)
    receipt = dict(unix=time.time(), condition=condition, absolute_sleep=source['absolute_sleep'],
        journal_id=source['journal_id'], sleep_complete_sha256=source['sleep_complete_sha256'],
        adapter_state_sha256=source['adapter_state_sha256'], optimizer_steps=source['optimizer_steps'],
        source_manifest_sha256=sha(root / 'SOURCE_MANIFEST.json'),
        freshness_sha256=sha(root / 'FRESHNESS_VERIFIED.json'), parent_tokens=0,
        learner_signals=[], status='CPU_SOURCE_READY_NOT_LOADED')
    write(root / 'CPU_PROVENANCE.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for field in ('root', 'source-root', 'original', 'queued', 'life'):
        parser.add_argument('--' + field, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.source_root, args.original, args.queued, args.life)))
