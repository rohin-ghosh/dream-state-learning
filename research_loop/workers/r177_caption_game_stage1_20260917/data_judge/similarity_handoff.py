"""Expose only train-pool metadata and factual scenes to the similarity worker."""

import json
from pathlib import Path

from gpu import ny_caption_data as data


def build():
    root = Path(__file__).resolve().parent
    status = json.loads((root/'private/released_all_v1/PUBLIC_STATUS.json').read_bytes())
    manifest = data.load_manifest(status['data_manifest'])
    plan = data.bound(status['development_plan'])
    catalog = data.bound(status['scene_catalog'])
    names = set(plan['subsets']['judge_train'])
    groups = sorted([group for group in manifest['scene_groups'] if set(group) <= names],
        key=lambda group: data.digest(dict(scope='R177_SIMILARITY_TRAIN_ONLY_V1', seed=177, group=sorted(group))))
    splits = {'fitting': [], 'calibration_holdout': []}
    for index, group in enumerate(groups):
        splits['calibration_holdout' if index % 5 == 0 else 'fitting'].extend(group)
    packet = dict(schema='NY_SIMILARITY_TRAIN_INPUT_V1', permitted_pool='judge_train',
        source_manifest=status['data_manifest'], source_plan=status['development_plan'], scene_catalog=status['scene_catalog'],
        scene_policy=data.RELEASED_JUDGE_SCENE_POLICY, scene_groups=groups, partitions=splits,
        partition_rule='HASH_SEED177_WHOLE_GROUPS_EVERY_FIFTH_CALIBRATION_BEFORE_CAPTION_OR_LABEL_READ',
        contests={name: dict(rows=manifest['contests'][name]['rows'], canonical_scene=data.released_judge_scene(catalog['scenes'][name]['facts']),
            scene_facts_sha256=catalog['scenes'][name]['facts_sha256']) for name in sorted(names)},
        judge_dev_used=False, locked_validation_used=False, FINAL_used=False, prior_judge_checkpoint_used=False,
        provisional=True, human_validated=False)
    reference = data.private_write(root/'private/SIMILARITY_TRAIN_INPUT.private.json', packet)
    handoff = dict(schema='NY_SIMILARITY_TRAIN_HANDOFF_V1', status='READY_TRAIN_ONLY_NO_JUDGE_CHECKPOINT_DEPENDENCY',
        private_input=reference, scene_policy=data.RELEASED_JUDGE_SCENE_POLICY,
        dataset_revision=manifest['revision'], scene_source_sha256=status['scene_source_sha256'],
        scene_fields=['canny', 'location', 'entities'], uncanny_included=False,
        partition_counts={name: len(values) for name, values in splits.items()}, available_training_contests=len(names),
        available_training_rating_rows=sum(manifest['contests'][name]['rows']['rows'] for name in names),
        missing_training_descriptions=status['missing_or_invalid_contests']['judge_train'],
        pretrained_encoder_manifest=data.file_ref(root/'private/PRETRAINED_ENCODER_MANIFEST_20260917_v1.json'),
        captions_in_public_reply=False, contest_ids_in_public_reply=False,
        locked_validation_included=False, FINAL_included=False, provisional=True)
    result = data.private_write(root/'SIMILARITY_TRAIN_HANDOFF.json', handoff)
    print(json.dumps(dict(handoff=result, partition_counts=handoff['partition_counts'], available_training_contests=len(names))))


if __name__ == '__main__':
    build()
