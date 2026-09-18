"""Receiving CPU preparation: copy completed ages; keep scoring epoch separate."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

from epoch import ADAPTER_SHA, DEADLINE, require_config, sha


BASE = Path('/localhome/local-rohing')
BATCH = BASE / 'orch_post_recovery_age_20260918'
TEMPLATE = BASE / 'orch_r233_recovery_s24_probe_20260918'
ORIGINAL = BASE / 'orch_r232_age_probe_20260918'
MODULE = Path('research_loop/workers/post_recovery_age_queue_20260918')
PRIMARY = BASE / 'orch_r233_judge15625_20260918/judge15625-base-v1/primary_scalar.json'


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)


def finish(root, plain_base):
    for path in Path(__file__).parent.glob('*.py'):
        destination = root / 'source' / MODULE / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    manifest = {str(path.relative_to(root / 'source')): sha(path) for path in (root / 'source').rglob('*')
        if path.is_file() and '__pycache__' not in path.parts}
    source_manifest = root / 'SOURCE_MANIFEST.json'
    source_manifest.write_text(json.dumps(manifest, sort_keys=True))
    identity = json.loads((root / 'CONDITION.json').read_bytes())
    config = dict(root=str(root), epoch_root=str(BATCH / 'epoch'), identity=identity,
        primary_config=str(PRIMARY), primary_config_sha256=sha(PRIMARY), adapter_sha256=ADAPTER_SHA,
        judge_rank=8, judge_step=15625, token_budget=6144, seeds=[23201, 23202], scenes=3,
        parent_tokens=0, source_context_loaded=False, training_updates=0, plain_base=plain_base,
        player_physical=2, judge_physical=7, deadline_unix=DEADLINE,
        source_manifest_sha256=sha(source_manifest), freshness_sha256=sha(root / 'FRESHNESS_VERIFIED.json'))
    require_config(config, time.time())
    write(root / 'CONFIG.json', config)
    return dict(root=str(root), condition=identity['condition'], config_sha256=sha(root / 'CONFIG.json'),
        source_manifest_sha256=config['source_manifest_sha256'], plain_base=plain_base,
        source_age=identity.get('absolute_sleep'), state='CPU_PREPARED_NOT_LOADED')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=['base', 'learner24', 'frozen24'], required=True)
    options = parser.parse_args()
    BATCH.mkdir(mode=0o700, exist_ok=True)
    (BATCH / 'epoch').mkdir(mode=0o700, exist_ok=True)
    root = BATCH / options.arm
    if root.exists():
        raise ValueError('new_probe_root_only_no_result_overwrite')
    sys.path.insert(0, str(TEMPLATE / 'source'))
    from research_loop.workers.rohin233_kept_age_probe_20260918.prepare_probe import prepare
    if options.arm == 'base':
        root.mkdir(mode=0o700)
        for name in ('source', 'assets'):
            shutil.copytree(TEMPLATE / name, root / name, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('GAME_MANIFEST.json', 'SELECTION.json'):
            shutil.copyfile(TEMPLATE / name, root / name)
        (root / 'judge').mkdir()
        shutil.copyfile(TEMPLATE / 'judge/REFERENCE_PANELS.private.json', root / 'judge/REFERENCE_PANELS.private.json')
        identity = json.loads((TEMPLATE / 'CONDITION.json').read_bytes())
        identity.update(condition='R233_ADOPTED_BASE', source_name='PLAIN_BASE', absolute_sleep=None,
            sleep_complete_sha256=None, parent_tokens=0, source_parent_text_loaded=False)
        write(root / 'CONDITION.json', identity)
        write(root / 'FRESHNESS_VERIFIED.json', dict(eligible=True, source_context_loaded=False,
            basis='Plain frozen base with no agent-history context; selected DEVELOPMENT scenes unchanged.',
            limits='No claim about base pretraining exposure.', selection_sha256=sha(root / 'SELECTION.json')))
        (root / 'queue').mkdir()
    else:
        label = 'FRESH_R231' if options.arm == 'learner24' else 'R232_SIBLING_FROZEN'
        queue = BASE / 'orch_r233_retained_source_queue_20260918' / label
        candidates = list(queue.glob(label + '_sleep_000024_*/SOURCE.json'))
        if len(candidates) != 1:
            raise ValueError('one_completed_captured_age24')
        life = BASE / ('orch_r231_curriculum_birth_20260918/raw' if options.arm == 'learner24'
            else 'orch_r232_curriculum_frozen_20260918/raw')
        prepare(root, TEMPLATE, ORIGINAL, candidates[0].parent, life, 'R233_ADOPTED_' + label + '_s24')
    receipt = finish(root, options.arm == 'base')
    write(root / 'ADOPTED_CPU_PREPARED.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
