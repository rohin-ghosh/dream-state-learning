"""Prospective TRAIN-only R111/R115 cohort extension; no dispatch or held reads."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake_r111 as recipe


ORIGINAL_CYCLES = 96
TASKS_PER_CYCLE = 2
MAX_NONCES = 10000
NONCE_STRIDE = 1001
TRAIN_NAMESPACE = 'R111_F2_TRAIN'


def make_train_task(cycle, position):
    task = recipe.source.make_task(TRAIN_NAMESPACE, cycle, position)
    task['split'] = 'TRAIN'
    return task


def validate_train(training):
    recipe.require(isinstance(training, list) and len(training) >= ORIGINAL_CYCLES,
        'complete_96_cycle_train_prefix_required')
    identifiers, questions = set(), set()
    for cycle, group in enumerate(training, 1):
        recipe.require(isinstance(group, list) and len(group) == TASKS_PER_CYCLE,
            'two_tasks_per_cycle_required')
        for episode, task in enumerate(group):
            recipe.require(isinstance(task, dict) and task.get('split') == 'TRAIN', 'train_only')
            prefix = f'{recipe.source.SEED}_{TRAIN_NAMESPACE}_C{cycle}_E'
            identifier = task.get('id')
            recipe.require(isinstance(identifier, str) and identifier.startswith(prefix),
                'original_train_namespace_and_cycle_required')
            suffix = identifier[len(prefix):]
            recipe.require(suffix.isascii() and suffix.isdigit(), 'original_position_required')
            position = int(suffix)
            recipe.require(position >= episode and (position - episode) % NONCE_STRIDE == 0
                and (position - episode) // NONCE_STRIDE < MAX_NONCES, 'original_retry_recipe_required')
            recipe.require(task == make_train_task(cycle, position), 'original_generator_schema_required')
            recipe.require(identifier not in identifiers and task['question_sha256'] not in questions,
                'duplicate_train_id_or_question')
            identifiers.add(identifier)
            questions.add(task['question_sha256'])
    return identifiers, questions


def extend_train(training, *, additional_cycles=96, excluded_ids=(), excluded_question_sha256=()):
    """Return a deep-copied exact prefix plus deterministic, collision-filtered TRAIN.

    Exclusions apply only to new tasks. An isolated custodian must supply complete
    held/prior exclusions or separately clear the candidate before consumption.
    """
    recipe.require(type(additional_cycles) is int and additional_cycles > 0, 'positive_additional_cycles')
    identifiers, questions = validate_train(training)
    identifiers.update(excluded_ids)
    questions.update(excluded_question_sha256)
    result = deepcopy(training)
    for cycle in range(len(training) + 1, len(training) + additional_cycles + 1):
        group = []
        for episode in range(TASKS_PER_CYCLE):
            for nonce in range(MAX_NONCES):
                task = make_train_task(cycle, episode + nonce * NONCE_STRIDE)
                if task['id'] not in identifiers and task['question_sha256'] not in questions:
                    identifiers.add(task['id'])
                    questions.add(task['question_sha256'])
                    group.append(task)
                    break
            else:
                raise ValueError('fresh_candidates_exhausted_before_dispatch')
        result.append(group)
    return result


def prepare(train, output, *, expected_train_sha256, additional_cycles=96):
    """Create a new local candidate file; never replace the input or admit a run."""
    raw = Path(train).read_bytes()
    input_sha256 = hashlib.sha256(raw).hexdigest()
    recipe.require(input_sha256 == expected_train_sha256, 'exact_train_file_binding_required')
    training = json.loads(raw)
    extended = extend_train(training, additional_cycles=additional_cycles)
    encoded = (json.dumps(extended, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    with Path(output).open('xb') as stream:
        stream.write(encoded)
    return dict(schema='R149_MATH_TRAIN_COHORT_CANDIDATE_V1',
        status='CANDIDATE_PENDING_ISOLATED_COLLISION_CHECK',
        input_sha256=input_sha256, output_sha256=hashlib.sha256(encoded).hexdigest(),
        input_cohort_sha256=recipe.digest(training), output_cohort_sha256=recipe.digest(extended),
        original_prefix_sha256=recipe.digest(extended[:ORIGINAL_CYCLES]),
        preserved_cycles=len(training), preserved_tasks=len(training) * TASKS_PER_CYCLE,
        first_new_cycle=len(training) + 1, last_cycle=len(extended),
        added_cycles=additional_cycles, added_tasks=additional_cycles * TASKS_PER_CYCLE,
        train_per_cycle=TASKS_PER_CYCLE, exact_prefix_preserved=True,
        old_train_id_collisions=0, old_train_question_hash_collisions=0,
        held_and_inherited_pool_collision_check='NOT_PERFORMED', dispatch_authorized=False,
        native_calls=0, parent_calls=0, held_reads=0,
        generator='organism_v6/orch_math_pipeline_l2.py:make_task',
        generator_sha256=recipe.sha(Path(recipe.source.__file__)),
        recipe='organism_v6/orch_math_feedback_uptake_r111.py:cohort',
        recipe_sha256=recipe.sha(Path(recipe.__file__)),
        seed=recipe.source.SEED, train_namespace=TRAIN_NAMESPACE,
        nonce_stride=NONCE_STRIDE, max_nonces=MAX_NONCES)


def prepare_service(train, service, *, expected_train_sha256, additional_cycles=96):
    """Create read-only TRAIN.json and COHORT.json; held clearance stays separate."""
    service = Path(service)
    output, manifest_path = service / 'TRAIN.json', service / 'COHORT.json'
    recipe.require(not output.exists() and not manifest_path.exists(), 'new_service_artifacts_required')
    service.mkdir(parents=True, exist_ok=True)
    summary = prepare(train, output, expected_train_sha256=expected_train_sha256,
        additional_cycles=additional_cycles)
    output.chmod(0o444)
    training = json.loads(output.read_bytes())
    summary.update(original_train_sha256=summary['input_sha256'], train_sha256=summary['output_sha256'],
        cycles_before=summary['preserved_cycles'], cycles_after=summary['last_cycle'],
        task_id_collisions=0, question_hash_collisions=0,
        collision_scope='ORIGINAL_TRAIN_AND_NEW_TRAIN_ONLY',
        source_sha256={
            'gpu/orch_r149_math_cohort.py': recipe.sha(Path(__file__)),
            'organism_v6/orch_math_feedback_uptake_r111.py': summary['recipe_sha256'],
            'organism_v6/orch_math_pipeline_l2.py': summary['generator_sha256'],
            'organism_v6/orch_math_rich.py': recipe.sha(Path(recipe.source.original.__file__)),
        })
    manifest = dict(summary, train_file='TRAIN.json',
        train_tasks={task['id']: task['question_sha256'] for group in training for task in group})
    encoded = (json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    with manifest_path.open('xb') as stream:
        stream.write(encoded)
    manifest_path.chmod(0o444)
    return dict(summary, manifest_sha256=hashlib.sha256(encoded).hexdigest())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train', type=Path, required=True)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument('--output', type=Path)
    destination.add_argument('--service', type=Path)
    parser.add_argument('--expected-train-sha256', required=True)
    parser.add_argument('--additional-cycles', type=int, default=96)
    args = parser.parse_args(argv)
    prepare_function = prepare_service if args.service is not None else prepare
    output = args.service if args.service is not None else args.output
    print(json.dumps(prepare_function(args.train, output, expected_train_sha256=args.expected_train_sha256,
        additional_cycles=args.additional_cycles), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
