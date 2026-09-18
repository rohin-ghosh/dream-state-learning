"""CPU-only immutable C2 source capture and incremental exposure audit."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import time


TARGET = dict(label='C2_NOW', journal_id='260be8b8710a42559b291797c6e14983',
    root='/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life',
    initial_loaded=dict(index=1, sha256='70ee9265d12bf33abd0bbbba92dae7bc1f16e48f7691097b3ec9f16ca06d8945'))
NODE5_END = 1789927200
OVX4_END = 1790726400
JUDGE_ADAPTER = 'a070b28ef0bf1f57ad994e5bd715db77e2649d196960cea422971523696be3c4'
KINDS = {'REQUEST', 'INBOX', 'LOADED', 'SLEEP_COMPLETE'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable_output_already_exists')
        return
    with path.open('xb') as stream:
        stream.write(raw)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules(directory):
    return tuple(load_module(name, directory / (name + '.py'))
        for name in ('capture_retained', 'reader', 'source_exposure'))


def validate_baseline(inputs):
    capture, exposure = inputs['baseline_capture'], inputs['baseline_exposure']
    scenes, selection = inputs['scenes'], inputs['selection']
    if not capture['exposure']['complete'] or not exposure['eligible']:
        raise ValueError('eligible_original_exposure_required')
    if (exposure['source_cut_index'], exposure['source_cut_sha256']) != (capture['head_index'], capture['head_sha256']):
        raise ValueError('same_original_audit_cut')
    scene_sha = hashlib.sha256(json.dumps(scenes, sort_keys=True).encode()).hexdigest()
    if exposure['scenes_sha256'] != scene_sha or selection['selected'] != ['564', '654', '703']:
        raise ValueError('original_three_scenes_only')
    if any(capture['exposure']['matches'].get(identifier) for identifier in selection['selected']):
        raise ValueError('prior_identifier_exposure')
    for identifier, scene in zip(selection['selected'], scenes['contests'], strict=True):
        if scene['split'] != 'agent_development' or scene['contest_id'] != 'agentdev_' + hashlib.sha256(identifier.encode()).hexdigest()[:20]:
            raise ValueError('original_development_scene_identity')
    return capture['head_index'], capture['head_sha256']


def latest(life, reader, target):
    paths = sorted((life / 'stream/records').glob('[0-9]' * 20 + '.json'))
    head = reader.metadata(paths[-1])
    selected_unix = time.time()
    for path in reversed(paths):
        header = reader.metadata(path)
        if header['kind'] != 'SLEEP_COMPLETE':
            continue
        record, unused = reader.verified(path, target['journal_id'])
        if record['document']['status'] == 'COMPLETE':
            return dict(selected_unix=selected_unix, selection_head=head,
                record_index=record['index'], record_sha256=record['sha256'], sleep=record['document']['cycle'])
    raise ValueError('no_completed_source')


def audit_exposure(life, source, inputs, reader, exposure):
    prior_cut, prior_sha = validate_baseline(inputs)
    journal = source['journal_id']
    anchor, unused = reader.verified(life / 'stream/records' / f'{prior_cut:020d}.json', journal)
    if anchor['sha256'] != prior_sha:
        raise ValueError('canonical_original_audit_anchor')
    cut = source['sleep_complete_index']
    scenes = inputs['scenes']['contests']
    image_refs = {row['handle']: row for row in inputs['image_packet']['images']}
    patterns = {scene['contest_id']: re.compile('|'.join([re.escape(scene['contest_id']),
        re.escape(image_refs[scene['image']]['sha256']), r'(?i:contest|cartoon|scene)[\s_:#-]*' + identifier + r'\b',
        r'(?<!\d)' + identifier + r'\.(?:jpg|png)']))
        for identifier, scene in zip(inputs['selection']['selected'], scenes, strict=True)}
    probes = {scene['contest_id']: exposure.shingles(scene['canonical_scene'].split('\n')[0]) for scene in scenes}
    identifier_hits, semantic_hits = ({key: [] for key in probes} for unused in range(2))
    maximum = {key: 0 for key in probes}
    checked, unresolved = [], []
    counts = {kind: 0 for kind in KINDS}
    full_bytes, header_bytes, ignored = 0, 0, 0
    previous_index, previous_sha = prior_cut, prior_sha
    selected = {1, cut}
    paths = sorted((life / 'stream/records').glob('[0-9]' * 20 + '.json'))
    for path in paths:
        index = int(path.stem)
        if index > cut or (index <= prior_cut and index not in selected):
            continue
        header = reader.metadata(path)
        header_bytes += min(path.stat().st_size, 4096)
        if header['journal_id'] != journal or header['index'] != index:
            raise ValueError('same_journal_header')
        if index > prior_cut:
            if index != previous_index + 1 or header['previous_sha256'] != previous_sha:
                raise ValueError('contiguous_tail_headers')
            previous_index, previous_sha = index, header['sha256']
        if header['kind'] not in KINDS:
            ignored += 1
            continue
        record, unused = reader.verified(path, journal)
        if record['sha256'] != header['sha256']:
            raise ValueError('header_full_record_binding')
        full_bytes += path.stat().st_size
        counts[record['kind']] += 1
        checked.append(dict(index=index, kind=record['kind'], sha256=record['sha256']))
        document = record['document']
        if record['kind'] == 'REQUEST':
            content = document.get('messages')
            if not isinstance(content, list) or any(not isinstance(item.get('content'), str) for item in content):
                unresolved.append(index)
        else:
            content = document
        for text in exposure.strings(content):
            shingles = exposure.shingles(text) if len(text) >= 20 else set()
            for identifier, probe in probes.items():
                if patterns[identifier].search(text):
                    identifier_hits[identifier].append(index)
                overlap = len(probe & shingles)
                maximum[identifier] = max(maximum[identifier], overlap)
                if overlap >= 3 or overlap / max(1, len(probe)) >= 0.15:
                    semantic_hits[identifier].append(index)
    if cut > prior_cut and (previous_index, previous_sha) != (cut, source['sleep_complete_sha256']):
        raise ValueError('audit_reaches_exact_selected_complete')
    return dict(schema='C2_BOUNDED_INCREMENTAL_EXPOSURE_V1', eligible=not unresolved
        and not any(identifier_hits.values()) and not any(semantic_hits.values()),
        source_cut_index=cut, source_cut_sha256=source['sleep_complete_sha256'],
        prior_audit_cut=prior_cut, prior_audit_sha256=inputs['pins']['FRESHNESS_VERIFIED.json'],
        baseline_capture_sha256=inputs['pins']['sources/CAPTURE.json'],
        reused_prefix_requests=inputs['baseline_exposure']['requests_scanned'],
        incremental_range=[prior_cut + 1, cut] if cut > prior_cut else None,
        explicit_initial_LOADED_and_selected_COMPLETE=True, canonical_record_counts=counts,
        canonical_record_manifest_sha256=digest(checked), full_canonical_bytes=full_bytes,
        bounded_header_bytes=header_bytes, header_only_noninput_records=ignored,
        identifier_matches={key: sorted(set(value)) for key, value in identifier_hits.items()},
        semantic_matches={key: sorted(set(value)) for key, value in semantic_hits.items()},
        maximum_shared_fivegrams=maximum, unresolved_requests=unresolved,
        semantic_threshold=dict(minimum_shared_fivegrams=3, minimum_fraction=0.15, connective='OR'),
        source_context_loaded=False, parent_tokens=0,
        limits='Reuses hash-bound original prefix audit; not a new full-body verification of prefix/UPDATE/RESPONSE records. Recorded source and inherited context only, not unseen pretraining or exhaustive paraphrase detection.')


def capture_current(directory):
    if time.time() >= NODE5_END:
        raise ValueError('node5_source_lease_bound')
    capture, reader, exposure = modules(directory / 'operator')
    inputs = json.loads((directory / 'INPUTS.private.json').read_text())
    validate_baseline(inputs)
    life = Path(TARGET['root'])
    selection = latest(life, reader, TARGET)
    write_once(directory / 'SELECTION.private.json', selection)
    current = capture.capture(TARGET, selection, directory / 'captured')
    current_exposure = audit_exposure(life, current, inputs, reader, exposure)
    source51 = next(row for row in inputs['baseline_capture']['sources'] if row['absolute_sleep'] == 51)
    source51 = dict(source51, journal_id=TARGET['journal_id'])
    original = capture.record(life, source51['sleep_complete_index'], TARGET['journal_id'], source51['sleep_complete_sha256'])
    if original['document']['after_adapter_sha256'] != source51['adapter_state_sha256']:
        raise ValueError('same_sleep51_adapter')
    baseline_exposure = audit_exposure(life, source51, inputs, reader, exposure)
    write_once(directory / 'captured' / current['source_relative'] / 'EXPOSURE.json', current_exposure)
    result = dict(selected=selection, current=current, current_exposure=current_exposure,
        baseline=source51, baseline_exposure=baseline_exposure,
        no_gpu_dispatch=True, learner_signals=[], original_records_mutated=False)
    write_once(directory / 'CAPTURED.private.json', result)
    return result


def stage_adapter(source, target, receipt):
    if target.exists():
        raise ValueError('new_receiving_source_only')
    if set(receipt['copy_files']) != {'COMMIT.json', 'adapter/README.md', 'adapter/adapter_config.json', 'adapter/adapter_model.safetensors'}:
        raise ValueError('adapter_only_source_allowlist')
    target.mkdir(parents=True, mode=0o700)
    for name, expected in receipt['copy_files'].items():
        original, destination = source / name, target / name
        if original.is_symlink() or sha(original) != expected['sha256']:
            raise ValueError('source_adapter_hash')
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(original, destination)
        if sha(original) != expected['sha256'] or sha(destination) != expected['sha256']:
            raise ValueError('receiving_before_copy_after_hash')
    return dict(adapter_only=True, optimizer_rng_loaded=False, source_context_loaded=False, parent_tokens=0)
