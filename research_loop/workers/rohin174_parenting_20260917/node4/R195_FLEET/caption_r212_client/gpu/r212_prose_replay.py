"""Reuse the exact original proof builder for explicitly R203-only history."""

import hashlib
from pathlib import Path


LEGACY_SHA = 'd9cc89488fa38a4c478b24ecaad7ae1228d37e6a505de530a25dd74e362bb5be'


def activate():
    from organism_v6 import orch_r203_prose_target_filter as current
    from organism_v6 import r212_legacy_prose as legacy
    if hashlib.sha256(Path(legacy.__file__).read_bytes()).hexdigest() != LEGACY_SHA:
        raise ValueError('exact_original_R203_proof_source')
    if getattr(current, '_r212_legacy_replay_bound', False):
        return
    original = current.prose_exclusions

    def versioned_proof(rows):
        annotations = [row['prose_target_filter'] for row in rows if 'prose_target_filter' in row]
        if annotations and all(policy == legacy.POLICY for policy in annotations):
            return legacy.prose_exclusions(rows)
        return original(rows)

    current.prose_exclusions = versioned_proof
    current._r212_legacy_replay_bound = True
