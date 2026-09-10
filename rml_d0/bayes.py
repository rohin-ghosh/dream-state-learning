"""Exact reduced first-accept counting toys for Stage A."""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations, product
from typing import Any, Callable


def _bernoulli_recurrence(cap: int, acceptance: Fraction) -> tuple[list[Fraction], Fraction]:
    survival = Fraction(1)
    attempts: list[Fraction] = []
    for _ in range(cap):
        attempts.append(survival * acceptance)
        survival *= 1 - acceptance
    return attempts, survival


def validate_attempt_solver(
    solver: Callable[[int, Fraction], tuple[list[Fraction], Fraction]],
) -> list[str]:
    errors: list[str] = []
    for cap in range(1, 5):
        actual = solver(cap, Fraction(1, 4))
        brute = _bernoulli_brute(cap, 4, frozenset({0}))
        closed = (
            [Fraction(3, 4) ** index * Fraction(1, 4) for index in range(cap)],
            Fraction(3, 4) ** cap,
        )
        if actual != brute:
            errors.append(f"cap_{cap}_brute")
        if actual != closed:
            errors.append(f"cap_{cap}_closed")
    return errors


def validate_heterogeneous_solver(
    solver: Callable[[int, Fraction, Fraction], tuple[int, int]],
) -> list[str]:
    expected = ((1, 2), (7, 12), (37, 56), (35, 48))
    errors: list[str] = []
    for cap, expected_weights in enumerate(expected, 1):
        actual = solver(cap, Fraction(1, 4), Fraction(1, 2))
        if actual != expected_weights:
            errors.append(f"cap_{cap}_posterior")
    return errors


def heterogeneous_posterior_solver(
    cap: int, acceptance0: Fraction, acceptance1: Fraction
) -> tuple[int, int]:
    accepted0 = 1 - (1 - acceptance0) ** cap
    accepted1 = 1 - (1 - acceptance1) ** cap
    from math import gcd

    denominator = accepted0.denominator * accepted1.denominator
    raw = (
        accepted0.numerator * (denominator // accepted0.denominator),
        accepted1.numerator * (denominator // accepted1.denominator),
    )
    divisor = gcd(*raw)
    return raw[0] // divisor, raw[1] // divisor


def _bernoulli_brute(
    cap: int, domain_size: int, accepted_values: frozenset[int]
) -> tuple[list[Fraction], Fraction]:
    counts = [0] * cap
    exhausted = 0
    for sequence in product(range(domain_size), repeat=cap):
        first = next(
            (index for index, value in enumerate(sequence) if value in accepted_values),
            None,
        )
        if first is None:
            exhausted += 1
        else:
            counts[first] += 1
    denominator = domain_size**cap
    return [Fraction(count, denominator) for count in counts], Fraction(
        exhausted, denominator
    )


def _recurrence(cap: int, accepted_descriptor: int) -> tuple[dict[int, Fraction], Fraction]:
    residual = Fraction(1, 1)
    weights = {0: Fraction(0, 1), 1: Fraction(0, 1)}
    for _ in range(cap):
        weights[accepted_descriptor] += residual * Fraction(1, 2)
        residual *= Fraction(1, 2)
    return weights, residual


def _brute(cap: int, accepted_descriptor: int) -> tuple[dict[int, Fraction], Fraction, int]:
    weights = {0: Fraction(0, 1), 1: Fraction(0, 1)}
    residual = Fraction(0, 1)
    sequence_mass = Fraction(1, 2**cap)
    sequence_count = 0
    for sequence in product(range(2), repeat=cap):
        sequence_count += 1
        accepted: int | None = None
        for descriptor in sequence:
            if descriptor == accepted_descriptor:
                accepted = descriptor
                break
        if accepted is None:
            residual += sequence_mass
        else:
            weights[accepted] += sequence_mass
    return weights, residual, sequence_count


def _fraction(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def first_accept_toy_goldens() -> dict[str, Any]:
    roles = tuple((hidden, side) for hidden in range(2) for side in range(2))
    caps: list[dict[str, Any]] = []
    proposal_sequences = 0
    mixture_checks = 0
    for cap in range(1, 5):
        role_rows: list[dict[str, Any]] = []
        recurrence_by_role: dict[tuple[int, int], tuple[dict[int, Fraction], Fraction]] = {}
        brute_by_role: dict[tuple[int, int], tuple[dict[int, Fraction], Fraction]] = {}
        for hidden, side in roles:
            effective = hidden ^ side
            recurrence_weights, recurrence_residual = _recurrence(cap, effective)
            brute_weights, brute_residual, sequence_count = _brute(cap, effective)
            proposal_sequences += sequence_count
            if (recurrence_weights, recurrence_residual) != (
                brute_weights,
                brute_residual,
            ):
                raise AssertionError("first-accept recurrence differs from brute force")
            expected_residual = Fraction(1, 2**cap)
            if recurrence_residual != expected_residual:
                raise AssertionError("first-accept residual has wrong closed form")
            recurrence_by_role[(hidden, side)] = (
                recurrence_weights,
                recurrence_residual,
            )
            brute_by_role[(hidden, side)] = (brute_weights, brute_residual)
            role_rows.append(
                {
                    "accepted_descriptor": effective,
                    "hidden": hidden,
                    "residual": _fraction(recurrence_residual),
                    "side": side,
                    "weights": [
                        _fraction(recurrence_weights[0]),
                        _fraction(recurrence_weights[1]),
                    ],
                }
            )

        # "Every hidden slot mixture" in the reduced toy is the complete
        # finite set of nonempty uniform subsets of its four hidden roles.
        for size in range(1, len(roles) + 1):
            for subset in combinations(roles, size):
                mixture_checks += 1
                recurrence_mix = [Fraction(0), Fraction(0)]
                brute_mix = [Fraction(0), Fraction(0)]
                recurrence_residual = Fraction(0)
                brute_residual = Fraction(0)
                for role in subset:
                    factor = Fraction(1, size)
                    rw, rr = recurrence_by_role[role]
                    bw, br = brute_by_role[role]
                    for descriptor in range(2):
                        recurrence_mix[descriptor] += factor * rw[descriptor]
                        brute_mix[descriptor] += factor * bw[descriptor]
                    recurrence_residual += factor * rr
                    brute_residual += factor * br
                if (recurrence_mix, recurrence_residual) != (
                    brute_mix,
                    brute_residual,
                ):
                    raise AssertionError("a hidden-role mixture count differs")
        caps.append({"cap": cap, "roles": role_rows})
    quarter_rows: list[dict[str, Any]] = []
    for cap in range(1, 5):
        attempts, residual = _bernoulli_recurrence(cap, Fraction(1, 4))
        brute_attempts, brute_residual = _bernoulli_brute(cap, 4, frozenset({0}))
        closed_attempts = [
            Fraction(3, 4) ** index * Fraction(1, 4) for index in range(cap)
        ]
        closed_residual = Fraction(3, 4) ** cap
        if (attempts, residual) != (brute_attempts, brute_residual) or (
            attempts,
            residual,
        ) != (closed_attempts, closed_residual):
            raise AssertionError("a=1/4 recurrence/closed/brute disagreement")
        accepted = sum(attempts, Fraction(0))
        if accepted != 1 - residual:
            raise AssertionError("a=1/4 attempt vector does not close")
        quarter_rows.append(
            {
                "accepted_mass": _fraction(accepted),
                "attempt_vector": [_fraction(value) for value in attempts],
                "cap": cap,
                "residual": _fraction(residual),
            }
        )

    expected_weights = ((1, 2), (7, 12), (37, 56), (35, 48))
    heterogeneous_rows: list[dict[str, Any]] = []
    for cap, expected in enumerate(expected_weights, 1):
        h0_attempts, h0_residual = _bernoulli_recurrence(cap, Fraction(1, 4))
        h1_attempts, h1_residual = _bernoulli_recurrence(cap, Fraction(1, 2))
        h0_brute, h0_brute_residual = _bernoulli_brute(cap, 4, frozenset({0}))
        h1_brute, h1_brute_residual = _bernoulli_brute(cap, 2, frozenset({0}))
        h0 = sum(h0_attempts, Fraction(0))
        h1 = sum(h1_attempts, Fraction(0))
        if (h0_attempts, h0_residual) != (h0_brute, h0_brute_residual):
            raise AssertionError("heterogeneous h0 recurrence/brute disagreement")
        if (h1_attempts, h1_residual) != (h1_brute, h1_brute_residual):
            raise AssertionError("heterogeneous h1 recurrence/brute disagreement")
        if h0 != 1 - Fraction(3, 4) ** cap or h1 != 1 - Fraction(1, 2) ** cap:
            raise AssertionError("heterogeneous recurrence/closed disagreement")
        common_denominator = h0.denominator * h1.denominator
        raw = (
            h0.numerator * (common_denominator // h0.denominator),
            h1.numerator * (common_denominator // h1.denominator),
        )
        from math import gcd

        divisor = gcd(*raw)
        weights = (raw[0] // divisor, raw[1] // divisor)
        if weights != expected:
            raise AssertionError("heterogeneous acceptance posterior weights differ")
        posterior_h0 = Fraction(weights[0], weights[0] + weights[1])
        heterogeneous_rows.append(
            {
                "acceptance_probabilities": [_fraction(h0), _fraction(h1)],
                "cap": cap,
                "posterior_h0": _fraction(posterior_h0),
                "posterior_integer_weights": list(weights),
            }
        )

    attempt_integer_vectors: list[list[int]] = []
    survival_vector: list[list[int]] = []
    for row in quarter_rows:
        fractions = [Fraction(*value) for value in row["attempt_vector"]]
        denominator = max(value.denominator for value in fractions)
        integers = [value.numerator * (denominator // value.denominator) for value in fractions]
        attempt_integer_vectors.append(integers)
        survival_vector.append(row["residual"])
    heterogeneous_weights = [
        row["posterior_integer_weights"] for row in heterogeneous_rows
    ]

    return {
        "caps": caps,
        "heterogeneous_acceptance": heterogeneous_rows,
        "hidden_mixture_checks": mixture_checks,
        "oracle_vector": {
            "attempt_weights_by_cap": attempt_integer_vectors,
            "heterogeneous_posterior_h0_h1": heterogeneous_weights,
            "survival": survival_vector,
        },
        "production_quarter_acceptance": quarter_rows,
        "proposal_sequences": proposal_sequences,
    }
