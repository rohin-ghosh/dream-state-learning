"""Exact validator copy from the hash-pinned receiving journal; no journal I/O."""

import math
import re

from research_loop.workers.post_recovery_node2_sleep_20260919.restart_contract import require


WALL_EXTENSION_SCHEMA = 'R131_SAVED_STATE_WALL_EXTENSION_V1'


def validate_wall_extension(authorization):
    require(type(authorization) is dict and set(authorization) == {
        'schema', 'previous_deadline_unix', 'previous_stream_sha256', 'new_deadline_unix',
        'lease_end_unix', 'safety_margin_seconds'}
        and authorization['schema'] == WALL_EXTENSION_SCHEMA, 'exact_wall_extension_authorization')
    require(type(authorization['previous_stream_sha256']) is str
        and re.fullmatch(r'[0-9a-f]{64}', authorization['previous_stream_sha256']), 'wall_extension_prior_digest')
    for name in ('previous_deadline_unix', 'new_deadline_unix', 'lease_end_unix', 'safety_margin_seconds'):
        value = authorization[name]
        require(type(value) in (int, float) and 0 <= value < float('inf') and math.isfinite(value),
                'finite_wall_extension_budget')
    require(authorization['safety_margin_seconds'] >= 120
        and authorization['previous_deadline_unix'] < authorization['new_deadline_unix']
        <= authorization['lease_end_unix'] - authorization['safety_margin_seconds'], 'wall_extension_lease_bound')
    return authorization
