"""CPU-only explicit incarnation adapter; no publisher, provider or native launch."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path


TARGET = 'r213_math_b_fork'
MEMBERS = ('r213_math_a', TARGET, 'r213_math_c',
    'r213_r226_caption_observation_fork', 'r213_r226_caption_perspective_fork',
    'r213_r226_caption_revision_fork', 'r213_r226_caption_selfderive_fork')
FIELDS = ('pid', 'start_ticks', 'boot_id', 'uid', 'command_sha256', 'source', 'guard_path',
    'guard_sha256', 'plan_sha256', 'loaded_index', 'loaded_sha256', 'gpu_uuid')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_cohort(expected, observed):
    require(set(expected) == set(observed) == set(MEMBERS), 'exact_seven_member_cohort')
    require(expected[TARGET]['state'] == observed[TARGET]['state'] == 'LOADED_ALIVE', 'actual_loaded_MathB_required')
    require(all(expected[TARGET][key] == observed[TARGET][key] for key in FIELDS),
        'exact_native_incarnation_source_guard_and_LOADED')
    require(observed[TARGET]['native_matches'] == [observed[TARGET]['pid']]
        and observed[TARGET]['compute_pids'] == [observed[TARGET]['pid']], 'exclusive_original_GPU2_native')
    require(observed[TARGET]['physical'] == 2 and observed[TARGET]['uid'] == 2524
        and observed[TARGET]['status'] not in ('Z', 'X'), 'original_owner_device_alive')
    for name in MEMBERS:
        if name == TARGET:
            continue
        before, current = expected[name], observed[name]
        require(before['state'] == current['state'] == 'EXPECTED_DOWN', 'no_impersonated_live_peer:' + name)
        require(current['native_matches'] == current['compute_pids'] == []
            and current['legacy_pid_exists'] is False, 'down_cohort_changed_rebind_required:' + name)
        require(current['old_binding_sha256'] == before['old_binding_sha256']
            and current['active_sha256'] == before['active_sha256'], 'preserved_down_binding:' + name)
    return True


class BoundHelper:
    def __init__(self, original, root, expected, old_bindings, target_binding, observe):
        require(set(old_bindings) == set(MEMBERS), 'preserve_all_original_binding_descriptors')
        require(target_binding['native_pid'] == expected[TARGET]['pid']
            and target_binding['source'] == expected[TARGET]['source']
            and target_binding['loaded'] == dict(index=expected[TARGET]['loaded_index'],
                sha256=expected[TARGET]['loaded_sha256'])
            and target_binding['guard_path'] == expected[TARGET]['guard_path'], 'truthful_target_binding')
        self.original = original
        self.root = Path(root)
        self.expected = deepcopy(expected)
        self.old_bindings = deepcopy(old_bindings)
        self.target_binding = deepcopy(target_binding)
        self.observe = observe

    def __getattr__(self, name):
        return getattr(self.original, name)

    def check(self):
        return validate_cohort(self.expected, self.observe())

    def bind(self, root, name):
        require(Path(root) == self.root and name in MEMBERS, 'only_original_root_and_classroom')
        self.check()
        result = deepcopy(self.target_binding if name == TARGET else self.old_bindings[name])
        result['ws6_expected_life'] = name
        result['ws6_expected_state'] = self.expected[name]['state']
        return result

    def alive(self, binding):
        self.check()
        name = binding.get('ws6_expected_life')
        require(name in MEMBERS and binding == self.bind(self.root, name), 'binding_not_fabricated_or_mutated')
        return name == TARGET

    def allow_target(self, name):
        self.check()
        require(name == TARGET, 'MathB_only_no_other_publication')


def provider_disposition(ledger):
    require(ledger['cumulative_usage_complete'] in (True, False), 'usage_completeness_explicit')
    preserved = dict(prior_usage=deepcopy(ledger['cumulative_usage']),
        prior_usage_complete=ledger['cumulative_usage_complete'],
        pending_request_sha256=ledger['pending_request_sha256'],
        next_turn=ledger['next_turn'], service_end_unix=ledger['service_end_unix'],
        ledger_sha256=ledger['ledger_sha256'], original_credential_scope_unchanged=True,
        new_provider_calls=0, cumulative_budget_reset=False, provider_retry_allowed=False)
    if ledger.get('http_status') == 401:
        return dict(preserved, status='AUTH401_TERMINAL_NO_NEW_REQUEST_OR_RETRY')
    if not ledger.get('pending_result_authenticated'):
        return dict(preserved, status='PRESERVE_PENDING_REQUEST_WAIT_AUTHENTICATED_RESULT')
    return dict(preserved, status='EXISTING_RESULT_ONLY_REQUIRES_MAIN_PUBLICATION_AUTHORIZATION')
