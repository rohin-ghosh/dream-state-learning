"""Reconstruct complete legacy caption state without rescoring old attempts."""

import hashlib
import json
from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def export_session(root, descriptors, *, verify_origin):
    root = Path(root).resolve()
    loaded, loaded_sha = read(root / 'LOADED.json')
    life_root = Path(loaded['life_root']).resolve()
    require(loaded['top_k'] == 50 and loaded['tau'] is None, 'same_relative_rank_rule')
    attempts = []
    required = {'REQUEST.json', 'BEFORE.json', 'AFTER.json', 'RESULT.json'}
    for directory in (root / 'attempts').iterdir():
        require(directory.is_dir() and len(directory.name) == 64
                and all(character in '0123456789abcdef' for character in directory.name),
                'only_source_hash_attempt_directories')
        require(required <= {path.name for path in directory.iterdir()}, 'incomplete_attempt_no_export')
        request, request_sha = read(directory / 'REQUEST.json')
        before, before_sha = read(directory / 'BEFORE.json')
        after, after_sha = read(directory / 'AFTER.json')
        result, result_sha = read(directory / 'RESULT.json')
        origin = request['request']['origin']
        require(origin['record_sha256'] == directory.name and result['origin'] == origin,
                'same_attempt_origin')
        actual_raw = verify_origin(life_root, origin)
        require(actual_raw == request['raw_act'] == result['raw_act'], 'same_actual_child_text')
        require(set(before) == set(after) == {'game', 'policy'}, 'complete_snapshot_shape')
        require(request['unix'] <= result['unix'], 'ordered_attempt_times')
        attempts.append(dict(identifier=directory.name, started=request['unix'], ended=result['unix'],
            before=before, after=after, hashes=dict(request=request_sha, before=before_sha,
                after=after_sha, result=result_sha)))
    require(attempts, 'at_least_one_complete_attempt')
    attempts.sort(key=lambda attempt: (attempt['started'], attempt['identifier']))
    for prior, following in zip(attempts, attempts[1:]):
        require(prior['ended'] <= following['started'], 'serialized_legacy_attempts')
        require(prior['after'] == following['before'], 'unbroken_snapshot_chain')
    final = attempts[-1]['after']
    state = dict(schema='R223_CAPTION_SESSION_STATE_V1', life_root=str(life_root),
        scene_ids=descriptors, phase='COMPLETE', game=final['game'], policy=final['policy'],
        seen=sorted(attempt['identifier'] for attempt in attempts),
        source_mode='NATIVE_JOURNAL', session_binding=None,
        format_policy='R223_FREEFORM_CAPTION_QA_V1')
    receipt = dict(schema='R224_LEGACY_CAPTION_STATE_EXPORT_V1', loaded_sha256=loaded_sha,
        complete_attempts=len(attempts), historical_rescoring=False, novelty_reset=False,
        final_attempt=attempts[-1]['identifier'],
        attempts=[dict(identifier=attempt['identifier'], hashes=attempt['hashes']) for attempt in attempts])
    return state, receipt
