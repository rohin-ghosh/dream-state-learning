"""Pure offline arithmetic for completed Q1_MAP_DYNAMICS_SIDECAR_v1.

Inputs are lists of 4 or 128 finite real numbers, grouped in quartet order
(00, 01, 10, 11). Margins mean z_mem2reg - z_gvn. AUTH target signs are
(+1, -1, -1, +1); DERANGED uses their negatives. No artifacts are read and
no trajectory classification, primary labels, or launch decisions are made.
"""

import math
from numbers import Real
import statistics


_AUTH_SIGNS = (1, -1, -1, 1)
_BASIS = {
    "C": (1, 1, 1, 1),
    "O": (1, 1, -1, -1),
    "M": (1, -1, 1, -1),
    "X": _AUTH_SIGNS,
}


def _finite(value):
    if not math.isfinite(value):
        raise ValueError("arithmetic result is outside finite float range")
    return value


def _validate(values, name):
    if not isinstance(values, list) or len(values) not in (4, 128):
        raise ValueError(f"{name} must be a list of length 4 or 128")
    converted = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name} must contain finite real numbers, not bool")
        try:
            converted.append(_finite(float(value)))
        except (OverflowError, ValueError) as error:
            raise ValueError(f"{name} must contain finite float-representable numbers") from error
    return converted


def _quantile(ordered, numerator, denominator):
    """Inclusive linear interpolation at rank (n - 1) * probability."""
    lower, remainder = divmod((len(ordered) - 1) * numerator, denominator)
    if remainder == 0:
        return ordered[lower]
    return float(statistics.mean(
        [ordered[lower]] * (denominator - remainder)
        + [ordered[lower + 1]] * remainder
    ))


def _summary(vector):
    ordered = sorted(vector)
    q25 = _quantile(ordered, 1, 4)
    q75 = _quantile(ordered, 3, 4)
    return {
        "vector": vector,
        "stats": {
            "mean": float(statistics.mean(vector)),
            "median": _quantile(ordered, 1, 2),
            "q25": q25,
            "q75": q75,
            "iqr": _finite(q75 - q25),
            "quantile_method": "inclusive",
            "sign_counts": {
                "positive": sum(value > 0 for value in vector),
                "negative": sum(value < 0 for value in vector),
                "zero": sum(value == 0 for value in vector),
            },
        },
    }


def _signed_margins(margins, arm):
    direction = 1 if arm == "P_AUTH" else -1
    return [
        direction * _AUTH_SIGNS[index % 4] * margin
        for index, margin in enumerate(margins)
    ]


def _reduce_arm(off_margins, margins, arm):
    delta = [_finite(margin - off) for off, margin in zip(off_margins, margins)]
    result = {}
    for name, signs in _BASIS.items():
        coefficients = [
            float(statistics.mean(
                sign * value for sign, value in zip(signs, delta[start:start + 4])
            ))
            for start in range(0, len(delta), 4)
        ]
        result[name] = _summary(coefficients)
    signed = _signed_margins(margins, arm)
    result["delta"] = delta
    result["own_map_signed_margin"] = {
        "mean": float(statistics.mean(signed)),
        "median": _quantile(sorted(signed), 1, 2),
        "correct_count": sum(value > 0 for value in signed),
        "incorrect_count": sum(value < 0 for value in signed),
        "zero_count": sum(value == 0 for value in signed),
        "total": len(signed),
    }
    direction = 1 if arm == "P_AUTH" else -1
    result["map_aligned_X"] = _summary([
        direction * value for value in result["X"]["vector"]
    ])
    return result


def reduce_arm(off_margins, margins, arm):
    """Return C/O/M/X and map_aligned_X as {vector, stats} dictionaries.

Stats contain mean, median, q25, q75, iqr, quantile_method='inclusive',
and sign_counts (positive, negative, zero). Singleton quantiles equal the
sole coefficient. Delta is a full row vector. Own-map signed-margin stats
use raw margins, not deltas, and include mean, median, correct_count (>0),
incorrect_count (<0), zero_count, and total (the supplied row count).

Only P_AUTH and P_DERANGED are accepted. Invalid inputs, mismatched lengths,
or unrepresentable finite-float results raise ValueError. Inputs are not
mutated. The caller owns archived-source provenance and terminal gating.
"""
    if not isinstance(arm, str) or arm not in ("P_AUTH", "P_DERANGED"):
        raise ValueError("arm must be P_AUTH or P_DERANGED")
    off_values = _validate(off_margins, "off_margins")
    margin_values = _validate(margins, "margins")
    if len(off_values) != len(margin_values):
        raise ValueError("off_margins and margins must have equal lengths")
    return _reduce_arm(off_values, margin_values, arm)


def _cosine(first, second):
    first_scale = max(abs(value) for value in first)
    second_scale = max(abs(value) for value in second)
    if first_scale == 0 or second_scale == 0:
        return None
    first_scaled = [value / first_scale for value in first]
    second_scaled = [value / second_scale for value in second]
    dot = math.fsum(left * right for left, right in zip(first_scaled, second_scaled))
    return dot / (math.hypot(*first_scaled) * math.hypot(*second_scaled))


def reduce_pair(off, auth, deranged):
    """Return arms, C_shared, X_split, delta_cosine, and both_correct.

Arms maps P_AUTH/P_DERANGED to reduce_arm results. C_shared and X_split
have the same {vector, stats} shape as arm coefficients. Delta cosine uses
all supplied rows and is None if either delta has exactly zero norm.
Both_correct counts matched rows with both own-map raw signed margins >0.
Input validation and quantile conventions match reduce_arm.
"""
    off_values = _validate(off, "off")
    auth_values = _validate(auth, "auth")
    deranged_values = _validate(deranged, "deranged")
    if len({len(off_values), len(auth_values), len(deranged_values)}) != 1:
        raise ValueError("off, auth, and deranged must have equal lengths")
    auth_result = _reduce_arm(off_values, auth_values, "P_AUTH")
    deranged_result = _reduce_arm(off_values, deranged_values, "P_DERANGED")
    return {
        "arms": {"P_AUTH": auth_result, "P_DERANGED": deranged_result},
        "C_shared": _summary([
            float(statistics.mean((auth_value, deranged_value)))
            for auth_value, deranged_value in zip(
                auth_result["C"]["vector"], deranged_result["C"]["vector"]
            )
        ]),
        "X_split": _summary([
            float(statistics.mean((auth_value, -deranged_value)))
            for auth_value, deranged_value in zip(
                auth_result["X"]["vector"], deranged_result["X"]["vector"]
            )
        ]),
        "delta_cosine": _cosine(auth_result["delta"], deranged_result["delta"]),
        "both_correct": sum(
            auth_signed > 0 and deranged_signed > 0
            for auth_signed, deranged_signed in zip(
                _signed_margins(auth_values, "P_AUTH"),
                _signed_margins(deranged_values, "P_DERANGED"),
            )
        ),
    }
