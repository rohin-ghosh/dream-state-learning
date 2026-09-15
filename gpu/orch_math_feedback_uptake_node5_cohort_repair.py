"""Prospective collision-only fallback; never changes a live cohort or oracle."""

import argparse
from pathlib import Path

from gpu import orch_math_feedback_uptake_node5_run as runner
from organism_v6 import orch_math_feedback_uptake_node5 as policy


def select(identifiers, questions, attempts=10000):
    identifiers, questions = set(identifiers), set(questions)
    cohort = dict(schema=policy.SCHEMA, train=[], held=[], excluded_ids=sorted(identifiers),
        excluded_question_sha256=sorted(questions))
    fallbacks = []
    for cycle in range(1, policy.CYCLES + 1):
        for split, count, destination in (('TRAIN', 2, 'train'), ('HELD', 8, 'held')):
            group = []
            for position in range(count):
                chosen = None
                for departure in range(4):
                    for nonce in range(attempts):
                        task = policy.base.history.source.make_task(f'R110_NODE5_3_{split}', cycle,
                            position + departure + nonce * 1000)
                        task['split'] = split
                        if task['id'] not in identifiers and task['question_sha256'] not in questions:
                            chosen = task
                            break
                    if chosen is not None:
                        if departure:
                            fallbacks.append(dict(cycle=cycle, split=split, position=position,
                                family_departure=departure, actual_family=chosen['family'],
                                reason='prior_id_or_question_collision_only'))
                        break
                policy.require(chosen is not None, 'bounded_all_family_collision_exhaustion')
                identifiers.add(chosen['id'])
                questions.add(chosen['question_sha256'])
                group.append(chosen)
            cohort[destination].append(group)
    return cohort, fallbacks


def prepare(root):
    policy.require(root == runner.ROOT, 'exact_existing_node5_root')
    lane = root / 'campaign_node5_style3'
    policy.require(lane.is_dir() and not any(lane.glob('*.json')), 'only_unprepared_zero_call_lane3')
    runner.validate(root)
    inherited = runner.common.read(root / 'INHERITED_EXCLUSION_REGISTRY.json')
    peer = runner.common.read(root / 'campaign_node5_style2/COHORT.json')
    identifiers, questions = set(inherited['excluded_ids']), set(inherited['excluded_question_sha256'])
    for group in peer['train'] + peer['held']:
        for task in group:
            identifiers.add(task['id'])
            questions.add(task['question_sha256'])
    cohort, fallbacks = select(identifiers, questions)
    tokenizer = runner.machinery.previous.reuse.seam.native.source.native.load_local_tokenizer(
        runner.machinery.previous.existing.MODEL)
    for group in cohort['train'] + cohort['held']:
        for task in group:
            prompt = policy.messages(task, purpose='experience' if task['split'] == 'TRAIN' else 'held')
            policy.require(len(tokenizer.apply_chat_template(prompt, tokenize=True,
                add_generation_prompt=True, return_dict=False)) < 2048, 'actual_tokenizer_prompt_bound')
    runner.common.write(lane / 'COHORT.json', cohort)
    selection = dict(selector_sha256=runner.common.sha(__file__), fallbacks=fallbacks,
        inherited_registry_sha256=runner.common.sha(root / 'INHERITED_EXCLUSION_REGISTRY.json'),
        peer_cohort_sha256=runner.common.sha(root / 'campaign_node5_style2/COHORT.json'),
        no_result_access=True, no_exclusion_removal=True, changed_family_mix_not_matched_contrast=True)
    runner.common.write(lane / 'SELECTION_REPAIR.json', selection)
    ready = runner.common.read(root / 'campaign_node5_style2/READY.json')
    ready.update(index=3, uuid=policy.DEVICES[3], budget=policy.budget(3),
        cohort_sha256=runner.common.sha(lane / 'COHORT.json'),
        selection_repair_sha256=runner.common.sha(lane / 'SELECTION_REPAIR.json'))
    runner.common.write(lane / 'READY.json', ready)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=runner.ROOT)
    prepare(parser.parse_args().root)
