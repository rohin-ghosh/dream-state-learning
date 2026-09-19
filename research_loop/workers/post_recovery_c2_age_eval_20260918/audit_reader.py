"""Read completed probe metadata only; never import or launch a probe."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


BASE = Path('/localhome/local-rohing')
BLOCKS = {
    'c2': ('orch_post_recovery_c2_age_eval_20260918', ('base', 'c2sleep51', 'c2sleep117')),
    'earlier': ('orch_post_recovery_age_20260918_attempt3', ('base',)),
}
RESULT_FIELDS = ('rank', 'accepted', 'status', 'cached', 'replayed', 'submission_id',
    'pixel_id', 'pixel_count', 'contest_id', 'ok', 'rejection_reason')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def collect():
    observed = datetime.now(timezone.utc)
    if observed >= datetime(2026, 10, 1, tzinfo=timezone.utc):
        raise ValueError('separate_node_metadata_read_scope_expired')
    files = {}

    def read(path):
        if path.is_symlink():
            raise ValueError('unexpected_symlink')
        raw = path.read_bytes()
        files[str(path)] = dict(sha256=digest(raw), bytes=len(raw))
        return json.loads(raw)

    blocks = {}
    for label, (directory, arms) in BLOCKS.items():
        root = BASE / directory
        block = dict(root=str(root), batch=read(root / 'BATCH_STATUS.json'), rows=[])
        for arm in arms:
            source = root / arm
            config = read(source / 'CONFIG.json')
            manifest = read(source / 'SOURCE_MANIFEST.json')
            for relative, expected in manifest.items():
                path = source / 'source' / relative
                if digest(path.read_bytes()) != expected:
                    raise ValueError('source_closure_changed: ' + str(path))
            game_manifest = read(source / 'GAME_MANIFEST.json')
            output = source / 'players' / config['identity']['condition']
            loaded = read(output / 'LOADED.json')
            complete = read(output / 'COMPLETE.json')
            row = dict(arm=arm, root=str(source), output=str(output), config=config,
                source_manifest=manifest, source_closure_verified=True,
                scene_ids=[scene['contest_id'] for scene in game_manifest['contests']],
                loaded={key: value for key, value in loaded.items() if key in (
                    'unix', 'pid', 'identity', 'source_age', 'judge_epoch_sha256',
                    'parent_tokens', 'source_parent_text_loaded', 'training_updates', 'token_budget', 'seeds')},
                complete={key: value for key, value in complete.items() if key != 'cells'}, cells=[])
            for completed_cell in complete['cells']:
                contest, seed = completed_cell['contest_id'], completed_cell['seed']
                cell_path = output / f'{contest}_{seed}'
                result = read(cell_path / 'RESULT.json')
                if result != completed_cell:
                    raise ValueError('complete_and_result_disagree')
                event_paths = sorted(cell_path.glob('[0-9]*.json'))
                if len(event_paths) != len(result['events']):
                    raise ValueError('event_file_count_disagrees')
                events = []
                for event_path, event in zip(event_paths, result['events'], strict=True):
                    if read(event_path)['event'] != event:
                        raise ValueError('event_file_and_result_disagree')
                    events.append(dict(file=str(event_path), canonical_event_sha256=canonical(event),
                        actual_generated_tokens=event['actual_generated_tokens'], origin=event['origin'],
                        score=dict(new_pixels=event['score']['new_pixels'],
                            judge_epoch_sha256=event['score']['judge_epoch_sha256'],
                            results=[dict(caption_sha256=scored['caption_sha256'],
                                result={key: scored['result'][key] for key in RESULT_FIELDS
                                    if key in scored['result']}) for scored in event['score']['results']])))
                row['cells'].append(dict(contest_id=contest, seed=seed, events=events,
                    generated_tokens=result['generated_tokens'], budget=result['budget'],
                    initial_context_sha256=result['initial_context_sha256'],
                    parent_tokens=result['parent_tokens'], no_updates=result['no_updates']))
            block['rows'].append(row)
        blocks[label] = block
    for name, receipt in files.items():
        if digest(Path(name).read_bytes()) != receipt['sha256']:
            raise ValueError('completed_file_changed_during_read')
    return dict(observed_utc=observed.isoformat(), scope='completed_files_metadata_only',
        authority='User-authorized node scope through October 1; expired eval dispatch scope not used.',
        no_dispatch=True, no_model_loaded=True, no_life_signals=True, no_parent_delivery=True,
        no_caption_or_reference_text_exported=True, all_files_stable=True, files=files, blocks=blocks)


if __name__ == '__main__':
    print(json.dumps(collect(), sort_keys=True))
