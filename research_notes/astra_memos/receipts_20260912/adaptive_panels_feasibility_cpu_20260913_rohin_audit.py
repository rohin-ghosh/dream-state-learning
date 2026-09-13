"""Read-only, standard-library CPU certificate for the adaptive-panels audit."""

from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, combinations_with_replacement, product
import json
from pathlib import Path
import platform


ROWS = tuple(range(8))
UNIVERSE = 255
CELLS = tuple(product((0, 1), repeat=3))


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def signatures(columns):
    return [tuple((column >> row) & 1 for column in columns) for row in ROWS]


def fibers(columns):
    return Counter(signatures(columns))


def pair_uniform(left, right):
    return sorted(fibers((left, right)).values()) == [2, 2, 2, 2]


def injective(columns):
    return len(fibers(columns)) == 8


def canonical(column):
    return column ^ UNIVERSE if column & 1 else column


def decision_solver(columns):
    @lru_cache(None)
    def solve(candidates, remaining):
        if candidates.bit_count() <= 1:
            return True
        if remaining == 0 or candidates.bit_count() > 2 ** remaining:
            return False
        for column in columns:
            positive = candidates & column
            negative = candidates & (UNIVERSE ^ column)
            if positive and negative and solve(negative, remaining - 1) and solve(
                positive, remaining - 1
            ):
                return True
        return False

    return solve


def run_certificate():
    balanced = tuple(
        sum(1 << row for row in subset) for subset in combinations(ROWS, 4)
    )
    partitions = tuple(column for column in balanced if not column & 1)
    check(len(balanced) == 70 and len(partitions) == 35, "partition universe")
    check(set(map(canonical, balanced)) == set(partitions), "complement quotient")

    raw_pair_types = Counter()
    for left, right in combinations_with_replacement(balanced, 2):
        sizes = sorted(fibers((left, right)).values())
        redundant = canonical(left) == canonical(right)
        uniform = pair_uniform(left, right)
        check((1 not in sizes) == (redundant or uniform), "pair classification")
        check(sizes in ([4, 4], [2, 2, 2, 2], [1, 1, 3, 3]), "pair sizes")
        raw_pair_types["redundant" if redundant else "uniform" if uniform else "singleton"] += 1

    compatible = {
        frozenset(pair)
        for pair in combinations(partitions, 2)
        if pair_uniform(*pair)
    }
    check(len(compatible) == 315, "canonical compatible pairs")
    triple_types = Counter()
    injective_triples = set()
    for triple in combinations(partitions, 3):
        counts = fibers(triple)
        if len(counts) == 8:
            injective_triples.add(frozenset(triple))
        if all(frozenset(pair) in compatible for pair in combinations(triple, 2)):
            if len(counts) == 8:
                check(set(counts.values()) == {1}, "injective triple cells")
                triple_types["eight_singletons"] += 1
            else:
                check(len(counts) == 4 and set(counts.values()) == {2}, "parity cells")
                check(len({sum(cell) % 2 for cell in counts}) == 1, "parity support")
                check(triple[0] ^ triple[1] ^ triple[2] == 0, "canonical xor closure")
                triple_types["four_parity_doubles"] += 1
        else:
            triple_types["not_pairwise_uniform"] += 1
    check(triple_types == {
        "eight_singletons": 840,
        "four_parity_doubles": 105,
        "not_pairwise_uniform": 5600,
    }, "canonical triple totals")

    margin_solutions = []
    for counts in product(range(3), repeat=8):
        if sum(counts) != 8:
            continue
        valid = all(
            sum(count for cell, count in zip(CELLS, counts)
                if (cell[first], cell[second]) == outcomes) == 2
            for first, second in combinations(range(3), 2)
            for outcomes in product((0, 1), repeat=2)
        )
        if valid:
            margin_solutions.append(counts)
    check(len(margin_solutions) == 3, "independent integer-margin enumeration")
    check(set(margin_solutions) == {
        (1,) * 8,
        tuple(2 if sum(cell) % 2 == 0 else 0 for cell in CELLS),
        tuple(2 if sum(cell) % 2 else 0 for cell in CELLS),
    }, "integer-margin solutions")

    family_counts = Counter()
    maximum_signatures = 0
    adaptive_successes = 0

    def enumerate_families(family, start):
        nonlocal maximum_signatures, adaptive_successes
        family_counts[len(family)] += 1
        maximum_signatures = max(maximum_signatures, len(fibers(family)))
        adaptive_successes += int(decision_solver(family)(UNIVERSE, 3))
        check(len(fibers(family)) <= 4, "strong-family total distinguishability")
        for index in range(start, len(partitions)):
            column = partitions[index]
            if any(frozenset((other, column)) not in compatible for other in family):
                continue
            if any(frozenset((*pair, column)) in injective_triples
                   for pair in combinations(family, 2)):
                continue
            enumerate_families((*family, column), index + 1)

    enumerate_families((), 0)
    check(family_counts == {0: 1, 1: 35, 2: 315, 3: 105}, "all admissible subsets")
    check(adaptive_successes == 0, "strong-family adaptive impossibility")

    branch_types = Counter()
    for root in partitions:
        seconds = [column for column in partitions if pair_uniform(root, column)]
        check(len(seconds) == 18, "balanced second choices")
        for left_second, right_second in product(seconds, repeat=2):
            same_on_branch = []
            for branch in (UNIVERSE ^ root, root):
                left_positive = branch & left_second
                right_positive = branch & right_second
                same_on_branch.append(
                    left_positive == right_positive
                    or left_positive == (branch ^ right_positive)
                )
            fixed_injective = injective((root, left_second, right_second))
            check(fixed_injective == (not any(same_on_branch)), "branch transfer lemma")
            branch_types["fixed_injective" if fixed_injective else "transfer_possible"] += 1
    check(sum(branch_types.values()) == 11340, "root/ordered-seconds exhaustive count")

    weak_columns = (30, 46, 86, 170, 78, 142, 166)
    check(len(set(weak_columns)) == 7, "seven distinct weak-witness partitions")
    check(all(column in partitions for column in weak_columns), "weak witness balance")
    fixed_sequence_histogram = Counter(
        len(fibers(sequence)) for sequence in product(weak_columns, repeat=3)
    )
    check(8 not in fixed_sequence_histogram, "all 343 weak fixed sequences fail")
    check(not any(injective(pair) for pair in product(weak_columns, repeat=2)), "weak pairs")
    singleton_example = next(
        (row, first, second)
        for first, second in combinations(range(7), 2)
        for row in ROWS
        if fibers((weak_columns[first], weak_columns[second]))[
            signatures((weak_columns[first], weak_columns[second]))[row]
        ] == 1
    )
    solve_weak = decision_solver(weak_columns)
    check(solve_weak(UNIVERSE, 3) and not solve_weak(UNIVERSE, 2), "weak adaptive depth")

    def build_tree(candidates, remaining):
        if candidates.bit_count() == 1:
            return {"candidate": candidates.bit_length() - 1}
        for index, column in enumerate(weak_columns):
            negative = candidates & (UNIVERSE ^ column)
            positive = candidates & column
            if negative and positive and solve_weak(negative, remaining - 1) and solve_weak(
                positive, remaining - 1
            ):
                return {
                    "probe": index + 1,
                    "0": build_tree(negative, remaining - 1),
                    "1": build_tree(positive, remaining - 1),
                }
        raise AssertionError("tree reconstruction failed")

    tree = build_tree(UNIVERSE, 3)
    for row in ROWS:
        current = tree
        transcript = []
        while "probe" in current:
            probe = current["probe"] - 1
            outcome = (weak_columns[probe] >> row) & 1
            transcript.append((probe, outcome))
            matching = [candidate for candidate in ROWS if all(
                ((weak_columns[seen_probe] >> candidate) & 1) == seen_outcome
                for seen_probe, seen_outcome in transcript
            )]
            check(len(matching) == 2 ** (3 - len(transcript)), "tree posterior sizes")
            current = current[str(outcome)]
        check(len(transcript) == 3 and current["candidate"] == row, "tree replay")

    optimal_roots = []
    for root_index, root in enumerate(weak_columns):
        second_choices = []
        for branch in (UNIVERSE ^ root, root):
            second_choices.append([
                index + 1 for index, column in enumerate(weak_columns)
                if solve_weak(branch & column, 1)
                and solve_weak(branch & (UNIVERSE ^ column), 1)
            ])
        if all(second_choices):
            common = sorted(set(second_choices[0]) & set(second_choices[1]))
            check(bool(common), "weak witness does not satisfy required different seconds")
            optimal_roots.append({
                "root": root_index + 1,
                "second_choices_by_outcome": second_choices,
                "common_choices": common,
            })

    script_path = Path(__file__).resolve()
    binding_path = script_path.parents[3] / (
        "research_notes/analysis/"
        "2026-09-13_adaptive_parenting_dev_gate01_binding_successor_v1.md"
    )
    binding_bytes = binding_path.read_bytes()
    section_one = b"## 1." + binding_bytes.split(b"## 1.", 1)[1].split(b"## 2.", 1)[0]
    return {
        "status": "PASS",
        "scope": "local CPU only; read-only execution; no generators/models/GPU/remote",
        "python": platform.python_version(),
        "script_sha256": sha256(script_path.read_bytes()).hexdigest(),
        "binding_sha256": sha256(binding_bytes).hexdigest(),
        "binding_section_1_sha256": sha256(section_one).hexdigest(),
        "raw_balanced_columns": len(balanced),
        "canonical_partitions": len(partitions),
        "raw_pairs_with_replacement": dict(sorted(raw_pair_types.items())),
        "canonical_uniform_pairs": len(compatible),
        "canonical_triples": dict(sorted(triple_types.items())),
        "independent_integer_margin_solutions": margin_solutions,
        "strong_admissible_families_by_size": dict(sorted(family_counts.items())),
        "strong_maximum_complete_signatures": maximum_signatures,
        "strong_depth_three_successes": adaptive_successes,
        "branch_transfer_cases": dict(sorted(branch_types.items())),
        "weak_witness_masks": weak_columns,
        "weak_witness_rows": ["".join(map(str, row)) for row in signatures(weak_columns)],
        "weak_fixed_sequence_signature_histogram": dict(sorted(fixed_sequence_histogram.items())),
        "weak_singleton_example_zero_based": singleton_example,
        "weak_adaptive_tree": tree,
        "weak_optimal_roots": optimal_roots,
    }


if __name__ == "__main__":
    print(json.dumps(run_certificate(), indent=2, sort_keys=True))
