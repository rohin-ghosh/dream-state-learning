"""Read bounded completed-evaluation metadata on ovx4; never launch or write."""

import hashlib
import json
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing')
QUEUE = BASE / 'post_reboot_probe_queue_20260919'
JOB = '4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f'
ROOTS = {
    'original_learner24': BASE / 'orch_r233_recovery_s24_probe_20260918',
    'original_sibling24': QUEUE / 'jobs' / JOB,
    'adopted_learner24': BASE / 'orch_post_recovery_age_20260918_attempt3/learner24',
    'adopted_sibling24': BASE / 'orch_post_recovery_age_20260918_attempt3/frozen24',
    'base': BASE / 'orch_post_recovery_c2_age_eval_20260918/base',
    'c2sleep51': BASE / 'orch_post_recovery_c2_age_eval_20260918/c2sleep51',
    'c2sleep117': BASE / 'orch_post_recovery_c2_age_eval_20260918/c2sleep117',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    if path.is_symlink() or path.stat().st_size > 4_194_304:
        raise ValueError('bounded_regular_metadata_only')
    return json.loads(path.read_bytes())


def ref(path):
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def reduce_cells(cells):
    states = {}
    seen = {}
    for cell in cells:
        seed = str(cell['seed'])
        state = states.setdefault(seed, dict(generated_tokens=0, act_attempts=0,
            distinct_scored=0, distinct_accepted=0, new_pixels=0,
            acts_without_scored_strings=0, unscored_outcomes=0))
        captions = seen.setdefault(seed, set())
        state['generated_tokens'] += cell['generated_tokens']
        for event in cell['events']:
            results = event['score']['results']
            is_act = event['origin']['stage'] == 'ACT'
            state['act_attempts'] += int(is_act)
            state['acts_without_scored_strings'] += int(is_act and not results)
            for row in results:
                key = (cell['contest_id'], row['caption_sha256'])
                if key in captions or row['result'].get('cached', False):
                    continue
                captions.add(key)
                result = row['result']
                state['distinct_scored'] += int(result.get('rank') is not None)
                state['unscored_outcomes'] += int(result.get('rank') is None)
                state['distinct_accepted'] += int(result.get('accepted') is True)
                state['new_pixels'] += int(result.get('status') == 'new_pixel')
    return states


def inspect(root):
    identity = read(root / 'CONDITION.json')
    output = root / 'players' / identity['condition']
    loaded = read(output / 'LOADED.json')
    complete = read(output / 'COMPLETE.json')
    source = loaded.get('source_age')
    result = dict(root=str(root), condition=identity['condition'],
        completed_unix=complete['unix'], elapsed_seconds=complete['elapsed_seconds'],
        actual_generated_tokens=complete['actual_generated_tokens'],
        source_age=source, identity=loaded['identity'],
        per_seed=reduce_cells(complete['cells']),
        cell_budgets=[dict(contest_id=cell['contest_id'], seed=cell['seed'],
            generated_tokens=cell['generated_tokens'], status=cell['status']) for cell in complete['cells']],
        unchanged_identity=complete['unchanged_identity'], files={})
    for name in ('CONDITION.json', 'CONFIG.json', 'SOURCE_MANIFEST.json', 'GAME_MANIFEST.json',
            'SELECTION.json', 'FRESHNESS_VERIFIED.json', 'assets/RULE.json',
            'assets/pixel_config.json', 'assets/adapter/adapter_model.safetensors',
            'judge/REFERENCE_PANELS.private.json', 'sources/CAPTURE.json',
            'runtime_v4/JOB_CONFIG.json', 'runtime/LEASE_AUTHORITY.json'):
        path = root / name
        if path.is_file():
            result['files'][name] = ref(path)
    for name in ('LOADED.json', 'COMPLETE.json'):
        result['files']['players/' + identity['condition'] + '/' + name] = ref(output / name)
    if (root / 'CONFIG.json').exists():
        config = read(root / 'CONFIG.json')
        result['config'] = config
        shared = Path(config['epoch_root'])
        result['judge_epoch'] = read(shared / 'JUDGE_EPOCH.json')
        result['judge_epoch_sha256'] = loaded['judge_epoch_sha256']
        result['files']['JUDGE_EPOCH.json'] = ref(shared / 'JUDGE_EPOCH.json')
        result['files']['PRIMARY_PANELS.private.json'] = ref(shared / 'PRIMARY_PANELS.private.json')
    result['source_closure'] = read(root / 'SOURCE_MANIFEST.json')
    return result


def main():
    document = dict(schema='REPLICATION_READ_ONLY_ORIGINALS_V1', observed_unix=time.time(),
        metadata_only=True, no_model_loads=True, no_signals=True, no_remote_writes=True,
        private_panel_text_exported=False, rows={})
    for name, root in ROOTS.items():
        try:
            document['rows'][name] = inspect(root)
        except (OSError, ValueError, KeyError) as error:
            document['rows'][name] = dict(root=str(root), error_type=type(error).__name__, error=str(error))
    document['queue'] = dict(
        registry=read(QUEUE / 'inputs/capsules_v4.json'),
        registry_ref=ref(QUEUE / 'inputs/capsules_v4.json'),
        policy=read(QUEUE / 'inputs/policy.json'),
        policy_ref=ref(QUEUE / 'inputs/policy.json'),
        history=read(QUEUE / 'candidate_v4/history.json'),
        history_ref=ref(QUEUE / 'candidate_v4/history.json'),
        freeze_ref=ref(QUEUE / 'candidate_v4/SOURCE_FREEZE_V4_REBIND.json'))
    print(json.dumps(document, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
