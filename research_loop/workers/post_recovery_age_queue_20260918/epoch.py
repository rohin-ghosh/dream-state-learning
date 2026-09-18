"""CPU-only identity and result separation for the adopted-judge age epoch."""

import hashlib
import json
import math
from pathlib import Path


ADAPTER_SHA = 'a070b28ef0bf1f57ad994e5bd715db77e2649d196960cea422971523696be3c4'
LEASE_END = 1790812800
DEADLINE = 1790791170
SEEDS = (23201, 23202)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require_config(config, now):
    if not now < config['deadline_unix'] <= DEADLINE <= LEASE_END - 21600:
        raise ValueError('existing_receiving_lease_bound')
    if config['parent_tokens'] != 0 or config['source_context_loaded'] or config['training_updates'] != 0:
        raise ValueError('parent_free_frozen_evaluation')
    if (config['judge_rank'], config['judge_step'], config['adapter_sha256']) != (8, 15625, ADAPTER_SHA):
        raise ValueError('human_adopted_judge_only')
    if config['token_budget'] != 6144 or tuple(config['seeds']) != SEEDS or config['scenes'] != 3:
        raise ValueError('unchanged_budget_and_replicates')
    if config['player_physical'] != 2 or config['judge_physical'] != 7:
        raise ValueError('newly_free_owned_devices_only')


def rescore_panels(rows, scorer):
    if len(rows) != 3:
        raise ValueError('three_original_panels')
    panels, receipts = {}, []
    for row in rows:
        selected = row['selected']
        if len(selected) != 64 or any(not isinstance(item.get('caption'), str) for item in selected):
            raise ValueError('exact_private_64_caption_panel')
        scene = selected[0]['scene']
        if scene in panels or any(item['scene'] != scene for item in selected):
            raise ValueError('unambiguous_panel_scene')
        scores = list(scorer.score(selected))
        if len(scores) != 64 or any(not math.isfinite(value) for value in scores):
            raise ValueError('complete_finite_adopted_scores')
        panels[scene] = scores
        receipts.append(dict(selected=selected, scores=scores, original_selected_sha256=digest(selected)))
    return panels, receipts


def bound_result(request, reply, epoch_sha):
    if reply.get('request_sha256') != digest(request) or reply.get('judge_epoch_sha256') != epoch_sha:
        raise ValueError('same_request_and_judge_epoch')
    return reply


def model_scene(contest):
    return {key: contest[key] for key in ('contest_id', 'canonical_scene')}
