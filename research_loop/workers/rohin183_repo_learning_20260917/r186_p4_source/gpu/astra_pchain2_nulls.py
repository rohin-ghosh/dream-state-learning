"""P-CHAIN-2 section-5 prelabel nulls and bounded source assignment only.

Build and seal the registry before assigning targets. Its only inputs are source
strings, candidate strings in presealed display order, and supplied token lengths.
Nonconstant means variation across candidates in at least one question, NOT
variation across questions. No labels, NEXT rows, scores, model outputs, seeds,
roots, tokenizer or native model interfaces are accepted by the registry.

No import-time I/O or optional imports. Main owns prospective input/registry
sealing, the real data pipeline, material admission and GPU decisions. Missing
byte positions have no definition in section 5: ragged candidate byte widths
are rejected, not padded or silently omitted. Endpoint lengths must agree across
appearances under the supplied frozen-tokenizer identifier-length definition.
These structural requirements do not qualify grammar or native tokenization.
"""

from collections import Counter
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from itertools import combinations
import json
import math
import time
import unicodedata


STATUS = "SOURCE_ONLY_PCHAIN2_NULLS"
FORMAT = "pchain2-section5-null-registry-v1"
SCIPY_VERSION = "1.15.3"
NUMPY_VERSION = "1.26.4"
TOTAL_SECONDS = 60.0
INTEGRAL_TOLERANCE = 1e-6
PI = tuple(index ^ 1 for index in range(16))
SIGNS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
MEMBERSHIP_RULE = "varies_across_candidates_in_at_least_one_question"
REMAINING_INTERFACES = (
    "Main must prospectively seal real identifiers, candidate orders, tokenizer-length "
    "provenance and registry hash before assigning labels; no seed/root/order redraw.",
    "Main maps assignment indices into its A/B/C chains and existing preparation "
    "with pi=i^1. This module receives no middle IDs, training rows or batch tape.",
    "Endpoint identity/token-length marginals are checked here; complete role, "
    "token-ID, rendered-output and batchwise token marginals require the caller's "
    "renderer/tokenizer/tape evidence. No material or native admission is returned.",
)


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


@dataclass(frozen=True)
class RawFeature:
    name: str
    values: tuple


@dataclass(frozen=True)
class NullPolicy:
    name: str
    positions: tuple


@dataclass(frozen=True)
class NullRegistry:
    sources: tuple
    candidate_orders: tuple
    token_lengths: tuple
    features: tuple
    nonconstant_features: tuple
    policies: tuple
    inputs_sha256: str
    membership_sha256: str
    registry_sha256: str


def _prefix(left, right):
    return next((index for index, (first, second) in enumerate(zip(left, right))
                 if first != second), min(len(left), len(right)))


def _levenshtein(left, right):
    previous = list(range(len(right) + 1))
    for row, first in enumerate(left, 1):
        current = [row]
        for column, second in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (first != second)))
        previous = current
    return previous[-1]


def _ranks(values):
    order = sorted(range(8), key=lambda position: (values[position], position))
    return tuple(order.index(position) for position in range(8))


def _pick(values, sign=1):
    return min(range(8), key=lambda position: (sign * values[position], position))


def _registry_payload(registry):
    return dict(format=FORMAT, sources=registry.sources, candidate_orders=registry.candidate_orders,
                token_lengths=registry.token_lengths, features=[asdict(item) for item in registry.features],
                nonconstant_features=registry.nonconstant_features, membership_rule=MEMBERSHIP_RULE,
                signs=SIGNS, policies=[asdict(item) for item in registry.policies],
                inputs_sha256=registry.inputs_sha256, membership_sha256=registry.membership_sha256)


def build_null_registry(*, sources, candidate_orders, token_lengths):
    """Pure prelabel registry. All collections are immutable tuples.

    token_lengths[query][display_position] is the supplied positive identifier
    token count, not computed here. Every raw feature gets min/max even when
    constant; all eight positions and lex min/max remain explicit duplicates.
    Pair membership is sealed before any assignment: no deduplication, fitting,
    post-label policy selection, rank averaging or sign-dependent re-ranking.
    """
    _require(type(sources) is tuple and len(sources) == 16
             and type(candidate_orders) is tuple and len(candidate_orders) == 16
             and type(token_lengths) is tuple and len(token_lengths) == 16,
             "sixteen_presealed_queries_required")
    _require(all(type(order) is tuple and len(order) == 8 for order in candidate_orders)
             and all(type(lengths) is tuple and len(lengths) == 8 for lengths in token_lengths),
             "eight_candidates_and_lengths_per_query_required")
    identifiers = sources + tuple(value for order in candidate_orders for value in order)
    _require(all(type(value) is str and bool(value) and value.isprintable()
                 and not any(character.isspace() for character in value)
                 and unicodedata.normalize("NFC", value) == value for value in identifiers),
             "nonempty_nfc_identifier_strings_required")
    _require(len(set(sources)) == 16 and all(len(set(order)) == 8 for order in candidate_orders),
             "distinct_sources_and_candidates_required")
    _require(all(set(order) == set(candidate_orders[query // 8 * 8])
                 for query, order in enumerate(candidate_orders))
             and set(candidate_orders[0]).isdisjoint(candidate_orders[8])
             and set(sources).isdisjoint(value for order in candidate_orders for value in order),
             "two_disjoint_eight_endpoint_blocks_required")
    _require(all(type(length) is int and length > 0 for lengths in token_lengths for length in lengths),
             "positive_supplied_token_lengths_required")
    endpoint_lengths = {}
    for order, lengths in zip(candidate_orders, token_lengths):
        for identifier, length in zip(order, lengths):
            _require(endpoint_lengths.setdefault(identifier, length) == length,
                     "same_identifier_token_length_drift")
    byte_orders = tuple(tuple(value.encode("utf-8") for value in order) for order in candidate_orders)
    widths = {len(value) for order in byte_orders for value in order}
    _require(len(widths) == 1, "ragged_candidate_byte_positions_unbound")
    width = next(iter(widths))
    names = ("display_position", "lexicographic_rank", "byte_length", "tokenizer_length",
             "common_byte_prefix", "common_byte_suffix", "byte_levenshtein") + tuple(
                 f"byte_{position}" for position in range(width)) + ("byte_sum_mod_257",)
    rows = []
    for query, candidates in enumerate(byte_orders):
        source = sources[query].encode("utf-8")
        rows.append((tuple(range(8)), _ranks(candidates), tuple(map(len, candidates)), token_lengths[query],
                     tuple(_prefix(source, value) for value in candidates),
                     tuple(_prefix(source[::-1], value[::-1]) for value in candidates),
                     tuple(_levenshtein(source, value) for value in candidates)) + tuple(
                         tuple(value[position] for value in candidates) for position in range(width)) + (
                             tuple(sum(value) % 257 for value in candidates),))
    features = tuple(RawFeature(name, tuple(row[index] for row in rows)) for index, name in enumerate(names))
    nonconstant = tuple(feature.name for feature in features
                        if any(len(set(values)) > 1 for values in feature.values))
    inputs_hash = _digest(dict(sources=sources, candidate_orders=candidate_orders, token_lengths=token_lengths))
    membership_hash = _digest(dict(inputs_sha256=inputs_hash, rule=MEMBERSHIP_RULE,
                                   membership=[(name, name in nonconstant) for name in names]))
    policies = [NullPolicy(f"single:{feature.name}:{direction}", tuple(_pick(values, sign)
                 for values in feature.values)) for feature in features for direction, sign in (("min", 1), ("max", -1))]
    policies.extend(NullPolicy(f"position:{position}", (position,) * 16) for position in range(8))
    lexical = features[1].values
    policies.extend(NullPolicy(f"lex:{direction}", tuple(_pick(values, sign) for values in lexical))
                    for direction, sign in (("min", 1), ("max", -1)))
    ranked = {feature.name: tuple(_ranks(values) for values in feature.values)
              for feature in features if feature.name in nonconstant}
    for first, second in combinations(nonconstant, 2):
        for first_sign, second_sign in SIGNS:
            positions = tuple(_pick(tuple(first_sign * left[position] + second_sign * right[position]
                                          for position in range(8)))
                              for left, right in zip(ranked[first], ranked[second]))
            policies.append(NullPolicy(f"pair:{first}:{second}:{first_sign:+d},{second_sign:+d}", positions))
    registry = NullRegistry(sources, candidate_orders, token_lengths, features, nonconstant,
                            tuple(policies), inputs_hash, membership_hash, "")
    return NullRegistry(**(vars(registry) | {"registry_sha256": _digest(_registry_payload(registry))}))


@dataclass(frozen=True)
class BinaryConstraint:
    name: str
    indices: tuple
    lower: int
    upper: int


def _constraints(registry, endpoint_ids):
    endpoint_index = {identifier: index for index, identifier in enumerate(endpoint_ids)}
    constraints = [BinaryConstraint(f"row:{query}", tuple(range(query * 8, query * 8 + 8)), 1, 1)
                   for query in range(16)]
    constraints.extend(BinaryConstraint(f"column:{endpoint}", tuple(query * 8 + endpoint % 8
                       for query in range(endpoint // 8 * 8, endpoint // 8 * 8 + 8)), 1, 1)
                       for endpoint in range(16))
    for arm, mapping in (("AUTH", tuple(range(16))), ("DERANGED", PI)):
        for position in range(8):
            indices = tuple(mapping[query] * 8 + endpoint_index[order[position]] % 8
                            for query, order in enumerate(registry.candidate_orders))
            constraints.append(BinaryConstraint(f"position:{arm}:{position}", indices, 2, 2))
        for policy in registry.policies:
            indices = tuple(mapping[query] * 8 + endpoint_index[order[position]] % 8
                            for query, (order, position) in enumerate(zip(registry.candidate_orders, policy.positions)))
            constraints.append(BinaryConstraint(f"null:{arm}:{policy.name}", indices, 0, 4))
    return tuple(constraints)


def _exact_constraints(vector, constraints):
    for constraint in constraints:
        total = sum(vector[index] for index in constraint.indices)
        _require(constraint.lower <= total <= constraint.upper, "exact_constraint_failed:" + constraint.name)


def _rounded_solution(outcome, objective, constraints):
    _require(outcome.status == 0 and bool(outcome.success), "optimal_solver_status_required")
    values = tuple(float(value) for value in outcome.x)
    _require(len(values) == 128 and all(math.isfinite(value) for value in values), "finite_128_variable_solution_required")
    rounded = tuple(round(value) for value in values)
    _require(all(value in (0, 1) and abs(raw - value) <= INTEGRAL_TOLERANCE
                 for raw, value in zip(values, rounded)), "rounded_binary_integrality_required")
    _exact_constraints(rounded, constraints)
    optimum = sum(coefficient * value for coefficient, value in zip(objective, rounded))
    _require(math.isfinite(float(outcome.fun)) and abs(float(outcome.fun) - optimum) <= INTEGRAL_TOLERANCE
             and float(outcome.mip_gap) == 0.0 and math.isfinite(float(outcome.mip_dual_bound))
             and abs(float(outcome.mip_dual_bound) - optimum) <= INTEGRAL_TOLERANCE,
             "exact_integer_objective_and_optimality_bound_required")
    return rounded, optimum


def _scipy_solver():
    """Lazy pinned backend. No environment installation or fallback solver.

    API: https://[REDACTED_HOST]/doc/scipy-1.15.3/reference/generated/scipy.optimize.milp.html
    milp accepts Bounds, LinearConstraint, time_limit and mip_rel_gap. The
    documented default relative gap is not exact, so it is explicitly zero.
    """
    import numpy
    import scipy
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import coo_matrix

    _require((scipy.__version__, numpy.__version__) == (SCIPY_VERSION, NUMPY_VERSION),
             "pinned_scipy_numpy_versions_required")

    def solve(objective, constraints, time_limit):
        started = time.monotonic()
        coordinates = [(row, column) for row, constraint in enumerate(constraints) for column in constraint.indices]
        matrix = coo_matrix((numpy.ones(len(coordinates)),
                             (numpy.array([row for row, _ in coordinates]),
                              numpy.array([column for _, column in coordinates]))),
                            shape=(len(constraints), 128)).tocsc()
        linear = LinearConstraint(matrix, [item.lower for item in constraints], [item.upper for item in constraints])
        remaining = time_limit - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("total_60_second_budget_exhausted")
        return milp(c=objective, integrality=numpy.ones(128, dtype=int), bounds=Bounds(0, 1),
                    constraints=linear, options=dict(time_limit=remaining, mip_rel_gap=0.0, disp=False))

    return solve


@dataclass
class AssignmentAttempt:
    registry: NullRegistry
    endpoint_ids: tuple
    registry_sha256: str
    membership_sha256: str
    inputs_sha256: str
    backend: str
    constraints_sha256: str | None = None
    assignment: tuple | None = None
    deranged_assignment: tuple | None = None
    solution_sha256: str | None = None
    fixed_prefix: tuple = ()
    steps: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    error: BaseException | None = None
    terminal_reason: str = "incomplete"
    remaining_interfaces: tuple = REMAINING_INTERFACES
    status: str = STATUS


def _assignment_stats(registry, endpoint_ids, assignment):
    lengths = {identifier: length for order, counts in zip(registry.candidate_orders, registry.token_lengths)
               for identifier, length in zip(order, counts)}
    stats = {}
    for arm, mapping in (("AUTH", tuple(range(16))), ("DERANGED", PI)):
        endpoints = tuple(endpoint_ids[assignment[query]] for query in mapping)
        positions = tuple(order.index(endpoint) for order, endpoint in zip(registry.candidate_orders, endpoints))
        policy_scores = tuple((policy.name, sum(predicted == correct for predicted, correct in zip(policy.positions, positions)))
                              for policy in registry.policies)
        _require(Counter(endpoints) == Counter(endpoint_ids), "endpoint_role_marginal_drift")
        histogram = Counter(lengths[endpoint] for endpoint in endpoints)
        _require(histogram == Counter(lengths[endpoint] for endpoint in endpoint_ids), "endpoint_token_length_marginal_drift")
        counts = tuple(positions.count(position) for position in range(8))
        _require(counts == (2,) * 8 and all(score <= 4 for _, score in policy_scores), "postsolve_null_or_position_failure")
        stats[arm] = dict(position_counts=counts, policy_scores=policy_scores,
                          max_policy_score=max(score for _, score in policy_scores),
                          endpoint_counts=tuple(endpoints.count(endpoint) for endpoint in endpoint_ids),
                          endpoint_token_length_histogram=tuple(sorted(histogram.items())))
    return stats


def solve_assignment(registry, *, endpoint_ids, expected_registry_sha256, _solver=None, _clock=None):
    """Lexicographically smallest endpoint-index bijection, or a retained failure.

    endpoint_ids has two consecutive eight-item blocks, in the prospectively
    frozen optimization index order. There are exactly 128 binary variables:
    x[query, local_endpoint] at query*8+local_endpoint; all other edges are absent.
    DERANGED query i uses x[i^1,j], never a shifted candidate/target index.

    Sixteen sequential global minimizations fix each optimal row. One 60-second
    wall-clock budget includes import, validation, assembly and all solves. Each
    call receives only the remaining budget; overruns/unknown/feasible-only
    outcomes never produce an assignment. No redraw, relaxation or retry exists.
    A tolerance only checks proximity to binary values and objective roundoff;
    every constraint is then checked with exact integer arithmetic.

    _solver(objective, constraints, remaining_seconds) and _clock are synthetic
    test seams only. Injected outcomes need the same optimality/binary checks,
    but cannot constitute authentic solver evidence. Main must use the pinned
    default backend for its prospective binding. Failed prefixes/raw outcomes
    are retained, but assignment and solution_sha256 remain None on any failure.
    """
    clock = time.monotonic if _clock is None else _clock
    started = clock()
    result = AssignmentAttempt(registry, endpoint_ids, registry.registry_sha256, registry.membership_sha256,
                               registry.inputs_sha256, "scipy.optimize.milp" if _solver is None else "injected_test_solver")
    try:
        _require(type(registry) is NullRegistry and expected_registry_sha256 == registry.registry_sha256
                 == _digest(_registry_payload(registry)), "prelabel_registry_hash_mismatch")
        _require(type(endpoint_ids) is tuple and len(endpoint_ids) == 16
                 and all(type(identifier) is str for identifier in endpoint_ids) and len(set(endpoint_ids)) == 16
                 and all(set(endpoint_ids[block:block + 8]) == set(registry.candidate_orders[block]) for block in (0, 8)),
                 "presealed_endpoint_index_blocks_required")
        constraints = _constraints(registry, endpoint_ids)
        result.constraints_sha256 = _digest(dict(endpoint_ids=endpoint_ids, registry_sha256=registry.registry_sha256,
                                                pi=PI, constraints=[asdict(item) for item in constraints],
                                                scipy=SCIPY_VERSION, numpy=NUMPY_VERSION))
        result.stats.update(variables=128, constraints=len(constraints), policies=len(registry.policies),
                            nonconstant_features=registry.nonconstant_features, budget_seconds=TOTAL_SECONDS,
                            pinned_versions=dict(scipy=SCIPY_VERSION, numpy=NUMPY_VERSION))
        if clock() - started >= TOTAL_SECONDS:
            raise TimeoutError("total_60_second_budget_exhausted")
        solver = _scipy_solver() if _solver is None else _solver
        fixed = ()
        for query in range(16):
            objective = tuple(query // 8 * 8 + column if row == query else 0
                              for row in range(16) for column in range(8))
            remaining = TOTAL_SECONDS - (clock() - started)
            if remaining <= 0:
                raise TimeoutError("total_60_second_budget_exhausted")
            step = dict(query=query, time_limit=remaining, outcome=None)
            result.steps.append(step)
            outcome = solver(objective, constraints + fixed, remaining)
            step["outcome"] = outcome
            if clock() - started >= TOTAL_SECONDS:
                raise TimeoutError("total_60_second_budget_exhausted")
            rounded, optimum = _rounded_solution(outcome, objective, constraints + fixed)
            result.fixed_prefix += (optimum,)
            fixed += (BinaryConstraint(f"fixed:{query}", (query * 8 + optimum % 8,), 1, 1),)
        _exact_constraints(rounded, constraints + fixed)
        assignment = result.fixed_prefix
        _require(all(endpoint // 8 == query // 8 for query, endpoint in enumerate(assignment))
                 and len(set(assignment)) == 16, "exact_within_block_bijection_required")
        result.stats.update(_assignment_stats(registry, endpoint_ids, assignment))
        solution_hash = _digest(dict(registry_sha256=registry.registry_sha256, endpoint_ids=endpoint_ids,
                                     constraints_sha256=result.constraints_sha256, assignment=assignment,
                                     pi=PI, backend=result.backend))
        if clock() - started >= TOTAL_SECONDS:
            raise TimeoutError("total_60_second_budget_exhausted")
        result.assignment, result.deranged_assignment = assignment, tuple(assignment[index] for index in PI)
        result.solution_sha256 = solution_hash
        result.terminal_reason = "source_solution"
    except BaseException as error:
        result.error = error
        result.terminal_reason = "time_budget_exhausted" if isinstance(error, TimeoutError) else "failed"
    result.stats["elapsed_seconds"] = clock() - started
    return result
