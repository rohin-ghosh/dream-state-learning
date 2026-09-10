"""RML-D0 Stage-A CPU micro-preflight only.

This package is a deterministic CPU micro-preflight.  Its sole authority is
the ratified Candidate-B protocol bound below.
"""

from __future__ import annotations

PROTOCOL = "RML-D0-FT-B-V1"
CANDIDATE_B_SHA256 = (
    "bd2a3b2bc11dd0b7f9591266ca9b9094e89195a0af581e248bc09e41e481805b"
)
CLAIM_FIREWALL = "CPU_STAGE_A_INSTRUMENT_CONFORMANCE"
STAGE = "STAGE_A_MICRO_PREFLIGHT"

STAGE_A_LIMITS = {
    "workers": 1,
    "wall_ms": 60_000,
    "peak_rss_bytes": 512 * 1024 * 1024,
    "temp_bytes": 50 * 1024 * 1024,
    "sealed_bytes": 25 * 1024 * 1024,
    "transitions": 2_000_000,
}

__all__ = [
    "CANDIDATE_B_SHA256",
    "CLAIM_FIREWALL",
    "PROTOCOL",
    "STAGE",
    "STAGE_A_LIMITS",
]
