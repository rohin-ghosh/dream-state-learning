"""Fixed-presentation comparison of two already author-qualified corpora."""

from collections import Counter
from dataclasses import dataclass
import hashlib

from organism_v6 import orch_l1_bootstrap_transfer as transfer
from organism_v6 import orch_l2_rich_math as encoding
from organism_v6 import orch_math_rich as original
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


FIRST_SHA = '52197d8d0f73528af69b61e6f244e5b1570f2bcfafd5ebb79d4058c959946837'
ADDITIONAL_SHA = '252da00e7e2d8532bb87922142632eaa128a1994c881ca0053f1e2eb87f89f0d'
COMBINED_SHA = '2003c75dc43a9337ac67178a6024fc3511c4c38c1ac736dcfbc0f9f578952fc2'
MANIFEST_SHA = '23698108754fb0b8ff7f6a9bede3709934cc736a411ce7548d0785e67b8f4ec5'
SEED = 'RICH_BREADTH_BOOTSTRAP_20260915_ATTEMPT1_V1'
QUOTAS = dict(percentages=8, work_rates=8, fractional_quantities=8, group_accounting=8)
CELLS = ('ORIGINAL16_FULL', 'ORIGINAL16_OFF', 'EXPANDED26_FULL', 'EXPANDED26_OFF')
DEVICES = dict(zip(CELLS, (
    (0, 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939'),
    (1, 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'),
    (2, 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'),
    (3, 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e'))))
SECONDS = 7200
GPU_HOURS = 8
MATH_CAP = 1536
MATH_TASKS = 32
LEGACY_CAP = 160
CALLS_PER_CELL = 80
CALLS_TOTAL = 320
BASELINE = GoalReplayLayout(16, 16)


@dataclass(frozen=True)
class BreadthLayout(GoalReplayLayout):
    trajectory_presentations: int = 16

    def __post_init__(self):
        if type(self.new_trajectory_rows) is not int or self.new_trajectory_rows not in (16, 26):
            raise ValueError('only_frozen_16_or_26_rows')
        if type(self.trajectory_presentations) is not int or self.trajectory_presentations != 16:
            raise ValueError('fixed_original16x16_schedule')

    @property
    def updates(self):
        return 224

    def training_indexes(self, update):
        indexes = BASELINE.training_indexes(update)
        if self.new_trajectory_rows == 16:
            return indexes
        mapped = []
        for slot, index in enumerate(indexes):
            if index >= 222:
                position = 2 * (update - 1) + slot - 2
                ordinal = (position // 28) * 16 + position % 28 - 12
                mapped.append(222 + ordinal % 26)
            else:
                mapped.append(index)
        return tuple(mapped)

    def presentation_counts(self):
        counts = Counter(index for update in range(1, 225) for index in self.training_indexes(update))
        return tuple(counts[index] for index in range(self.row_count))

    def manifest(self, arm):
        result = super().manifest(arm)
        result.update(schema='RICH_BREADTH_BOOTSTRAP_LAYOUT_V1',
            trajectory_presentations='original16x16_slot_schedule_not_uniform26',
            new_target_presentations=256,
            new_supervised_presentations=0 if self.masked_row_indexes(arm) else 256,
            new_slot_mapping='identity16; ascending immutable row-order cycle26',
            comparison='expanded content at fixed presentations and legacy dose; not token-matched')
        return result


def validate_packets(first, additional, combined):
    encoding.validate_packet(first)
    assert len(additional) == 10 and combined == first + additional and len(combined) == 26
    assert {row['task_id'] for row in additional} == {
        'gsm8k-train-1614', 'gsm8k-train-971', 'gsm8k-train-5643'}
    assert len({row['task_id'] for row in first}) == 6
    assert {row['family'] for row in first} == {'percentages'}
    assert len({row['task_id'] for row in combined}) == 9
    assert set(row['family'] for row in combined) == set(QUOTAS)
    assert len({row['target_sha256'] for row in combined}) == 26
    for row in combined:
        assert row['admitted'] and row['semantic_status'] == 'PASS' and row['candidate']
        assert row['outcome_pass'] and row['token_contract_pass']
        assert 150 <= row['generated_tokens'] <= 400
        assert hashlib.sha256(row['target'].encode()).hexdigest() == row['target_sha256']
        assert original.digest(row['student_prefix']) == row['student_prefix_sha256']
        assert row['target'] == row['call']['raw']
        assert row['student_prefix'][-1]['role'] == 'user'
        assert not any(message['role'] == 'system' for message in row['student_prefix'])
    return dict(rows=26, tasks=9, families=4, new_admission=False, author_only_qualification=True)


def cohort(records, documents):
    identifiers, hashes = transfer.exclusions(documents)
    pools = {family: [] for family in QUOTAS}
    seen = set(hashes)
    for index, record in enumerate(records):
        identity = f'gsm8k-train-{index}'
        question = record['question'].strip()
        digest = transfer.question_hash(question)
        family = original.family(question)
        if identity in identifiers or digest in seen or family not in pools:
            continue
        seen.add(digest)
        pools[family].append(dict(id=identity, question=question, question_sha256=digest,
            gold=str(original.number(record['answer'].rsplit('####', 1)[1])), family=family))
    tasks = []
    for family, count in QUOTAS.items():
        assert len(pools[family]) >= count, ('insufficient_fresh_pool', family)
        tasks.extend(sorted(pools[family], key=lambda task: original.digest(SEED + ':' + task['id']))[:count])
    tasks.sort(key=lambda task: original.digest(SEED + ':ORDER:' + task['id']))
    assert len(tasks) == len({task['id'] for task in tasks}) == 32
    assert len({task['question_sha256'] for task in tasks}) == 32
    assert Counter(task['family'] for task in tasks) == QUOTAS
    return dict(tasks=tasks, prompts=[original.prompt(task, 'rich')[0] for task in tasks],
        quotas=QUOTAS, seed=SEED, denominator=32,
        pool_counts={family: len(pool) for family, pool in pools.items()},
        excluded_ids=sorted(identifiers), excluded_question_hashes=sorted(hashes),
        max_new_tokens=MATH_CAP, max_readout_calls=CALLS_TOTAL, training_generation=0,
        parent_calls=0, retries=0, seconds=SECONDS, gpu_hours=GPU_HOURS)
