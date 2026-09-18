"""Recover literal ACT lines from the same frozen generations; never resample."""

import argparse
import json
from pathlib import Path
import time

from gpu.ny_caption_life import extract_batch
from research_loop.workers.rohin209_first_game_20260918.generate_c2 import (
    ADAPTER_STATE_SHA256, BASE_SHA256, digest, file_ref, load_scenes, require, write,
)


def recover(source, manifest_path, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    scenes, manifest = load_scenes(manifest_path)
    bindings = json.loads((source / 'INPUT_BINDINGS.json').read_text())
    frozen = json.loads((source / 'FROZEN_AFTER.json').read_text())
    generation = json.loads((source / 'ACT_GENERATION.json').read_text())
    request = json.loads((source / 'ACT_INPUT.json').read_text())
    initial = json.loads((source / 'THINK_INPUT.json').read_text())
    require(bindings['manifest']['sha256'] == manifest['sha256'], 'same_scenes')
    require(digest(initial['messages']) == bindings['initial_messages_sha256'], 'same_initial_context')
    require(generation['messages'] == request['messages'], 'same_actual_ACT_input')
    require(frozen['base_sha256'] == BASE_SHA256 and frozen['all_parameters_frozen'], 'verified_frozen_base')
    require(frozen['adapter_state_sha256'] == (ADAPTER_STATE_SHA256 if bindings['mode'] == 'c2' else None),
            'same_matched_player_identity')
    action, metrics = extract_batch(generation['raw'], [scene['contest_id'] for scene in scenes])
    reference = file_ref(source / 'ACT_GENERATION.json')
    actions = [dict(contest_id=action['contest_id'], text=caption,
                    origin=dict(kind='FROZEN_MATCHED_PLAYER_GENERATION', generation_sha256=reference['sha256'],
                                caption_ordinal=index, extraction='R213_LITERAL_ACT_LINE_SALVAGE_V1'))
               for index, caption in enumerate(action['captions'] if action else [], 1)]
    write(output / 'actions.json', actions)
    write(output / 'RECOVERY.json', dict(policy='R213_LITERAL_ACT_LINE_SALVAGE_V1', unix=time.time(),
        mode=bindings['mode'], raw_generation=reference, source_bindings=file_ref(source / 'INPUT_BINDINGS.json'),
        frozen_after=file_ref(source / 'FROZEN_AFTER.json'), extractor=file_ref(Path(__file__)),
        caption_extractor=file_ref(Path(__file__).parents[3] / 'gpu' / 'ny_caption_life.py'),
        initial_messages_sha256=bindings['initial_messages_sha256'], actual_captions=len(actions),
        metrics=metrics, new_generation=False, THINK_captions_scored=False, caption_text_modified=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'game-manifest', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    recover(args.source, args.game_manifest, args.output)


if __name__ == '__main__':
    main()
