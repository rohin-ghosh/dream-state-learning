"""Explicit, source-bound continuation clocks without resetting learner state."""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time


SCHEMA = 'R119_LEASE_CONTINUATION_CLOCK_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(reference):
    require(set(reference) == {'path', 'sha256'}, 'exact_reference')
    path = Path(reference['path'])
    require(path.is_absolute() and sha(path) == reference['sha256'], 'bound_reference')
    return json.loads(path.read_text())


def timestamp(value):
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(parsed.tzinfo is not None, 'timezone_required')
        value = parsed.astimezone(timezone.utc).timestamp()
    require(type(value) in (int, float) and math.isfinite(value), 'finite_timestamp')
    return value


def field(document, keys):
    require(isinstance(keys, list) and keys and all(isinstance(key, str) for key in keys),
            'explicit_lease_expiry_field')
    for key in keys:
        document = document[key]
    return document


def validate(reference, *, backend_path=None, now=None):
    policy = checked(reference)
    require(policy['schema'] == SCHEMA, 'lease_clock_schema')
    authorization = checked(policy['authorization'])
    require(authorization['scope'] == 'REPORT_CUT_NOT_RUN_END_LEASE_CONTINUATION'
            and authorization['node'] == policy['node']
            and authorization['preserve_checkpoint_optimizer_counters'] is True
            and authorization['preserve_final_evaluation'] is True,
            'explicit_continuation_scope')
    lease = checked(policy['lease'])
    expiry = timestamp(field(lease, policy['lease_expiry_field']))
    margin = policy['lease_margin_seconds']
    reserve = policy['commit_reserve_seconds']
    require(type(margin) is int and margin >= 21600, 'six_hour_minimum_lease_margin')
    require(type(reserve) is int and 30 <= reserve <= 600, 'bounded_commit_reserve')
    hard_end = timestamp(policy['hard_end_unix'])
    train_end = timestamp(policy['train_end_unix'])
    require(hard_end <= expiry - margin and train_end == hard_end - reserve,
            'lease_based_wall_and_commit_reserve')
    require(hard_end == timestamp(authorization['hard_end_unix']), 'authorized_wall')
    current = time.time() if now is None else now
    require(current < train_end, 'continuation_clock_expired')
    initial = checked(policy['state_at_authorization'])
    config = checked(policy['shared_config'])
    require(initial['config_sha256'] == policy['shared_config']['sha256'],
            'unchanged_shared_recipe')
    require(config['owner'] == 'F1' and len(config['branches']) == 8
            and config['episodes_per_branch'] == 2
            and config['new_presentations'] == 16
            and config['rehearsal_presentations'] == 1
            and config['anchor_loss_weight'] == .25, 'unchanged_shared_learning_contract')
    require(initial['generation'] >= 1 and initial['checkpoint']['optimizer_path_sha256'],
            'committed_learner_optimizer_required')
    root = Path(policy['shared_root'])
    require(root.is_absolute() and sha(root / 'CONFIG.json') == policy['shared_config']['sha256'],
            'same_common_root_and_config')
    current_state = json.loads((root / 'STATE.json').read_text())
    require(current_state['config_sha256'] == initial['config_sha256']
            and current_state['generation'] >= initial['generation'], 'no_state_reset')
    for metric in ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures'):
        prior = initial.get(metric)
        present = current_state.get(metric)
        require(prior is None or type(present) is int and present >= prior,
                'no_counter_reset:' + metric)
    if current_state['generation'] == initial['generation']:
        require(current_state['checkpoint'] == initial['checkpoint'], 'same_generation_same_checkpoint')
    if backend_path is not None:
        require(sha(backend_path) == policy['backend_sha256'], 'bound_continuation_backend')
    return dict(train_end_unix=train_end, hard_end_unix=hard_end,
                lease_end_unix=expiry, lease_margin_seconds=margin,
                initial_generation=initial['generation'], current_generation=current_state['generation'],
                policy_sha256=reference['sha256'], node=policy['node'])


def from_environment(environment, backend_path):
    path = environment.get('ORCH_R119_LEASE_CLOCK')
    digest = environment.get('ORCH_R119_LEASE_CLOCK_SHA256')
    if path is None and digest is None:
        return None
    require(bool(path) and bool(digest), 'complete_lease_clock_environment')
    return validate(dict(path=path, sha256=digest), backend_path=backend_path)
