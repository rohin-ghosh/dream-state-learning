"""Final bounded GRID startup era, preserving both failed-session chains."""

import importlib.util
import os
from pathlib import Path
import time


PRIOR_SHA = '5663c96db2de0bff681be98684bba66d2e016d526f2dccca56043e03403fecf7'
SECOND_SESSION_SHA = '2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641'
TERMINAL = 'R118_GRID_PARALLEL_RECOVERY_V2_TERMINAL.json'
STARTUP_END = 1789490100

_path = Path(__file__).resolve().with_name('orch_r118_grid_failed_startup_run.py')
_spec = importlib.util.spec_from_file_location('private_grid_previous_startup', _path)
prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prior)
require, read, ref, write = prior.require, prior.read, prior.ref, prior.write
require(ref(_path)['sha256'] == PRIOR_SHA, 'unchanged_previous_startup_source')
_verify_first = prior.verify_failed_start
_validate_active = prior.validate_active_session


def validate_second_proof(proof, branch):
    require(proof['session']['sha256'] == SECOND_SESSION_SHA and proof['GO_exists'] is False,
            'exact_second_failed_session_without_GO')
    own = proof['branches'][branch]
    require(own['native_process_dispatched'] is False and own['model_load_attempted'] is False and
            own['new_generation_calls'] == own['new_provider_charges'] == own['optimizer_steps'] == 0 and
            not any(own['execution_markers'].values()) and not own['canonical_bootstrap_exists'] and
            not own['bootstrap_start_exists'] and not own['preserved_mismatches'] and
            not own['new_call_parent_triple_files'], 'second_failure_strictly_before_native_dispatch')
    require(own['ledger_counts'] == {'NATIVE':565 if branch == 'F4' else 567,'PARENT':40},
            'unchanged_actual_charges')
    return own


def verify_chain(plan, handoff):
    chain = read(plan['second_failed_startup'])
    previous_plan = read(chain['previous_plan'])
    original = _verify_first(previous_plan, handoff)
    require(plan['root'] == previous_plan['root'] and plan['branch'] == previous_plan['branch'] and
            plan['bounds'] == previous_plan['bounds'] and plan['boundary'] == previous_plan['boundary'] and
            plan['previous_final_plan'] == previous_plan['previous_final_plan'], 'same_state_caps_final_custody')
    root = Path(plan['root']).resolve(strict=True)
    require(Path(plan['directory']) == root / 'parallel_recovery_1624' and
            plan['directory'] != previous_plan['directory'], 'new_single_use_final_namespace')
    proof = read(chain['observation'])
    own = validate_second_proof(proof, plan['branch'])
    failure = read(proof['dispatcher_failure'])
    require(failure['session_sha256'] == SECOND_SESSION_SHA and failure['retry_allowed'] is False,
            'never_retry_second_failed_session')
    session = read(proof['session'])
    control = Path(proof['session']['path']).parent / 'SESSION.dispatch'
    require(not (control/'GO.json').exists() and
            not Path(session['owners'][plan['branch']]['bootstrap_path']).exists(), 'no_late_second_GO_or_bootstrap')
    terminal = read(own['terminal'])
    require(terminal['status'] == 'FAILED' and
            terminal['error'] == 'ValueError: new_session_live_before_any_model_load', 'actual_second_failure_retained')
    for name, digest in chain['preserved_files'].items():
        require(ref(handoff.inside(root,name))['sha256'] == digest, 'all_failed_era_bytes_preserved')
    handoff.parallel.predecessor_released(handoff.central_identity(own['guard']['expected']))
    require(ref(root/'LEDGER.jsonl') == own['ledger'] and ref(root/'CARRY.json') == own['carry'],
            'unchanged_ledger_carry')
    return original


def validate_active(plan, handoff):
    require(time.time() < STARTUP_END and os.environ.get('R118_PARALLEL_SESSION_SHA256') != SECOND_SESSION_SHA,
            'final_startup_before_1635_no_second_session_replay')
    session = _validate_active(plan, handoff)
    require(session['startup_deadline_unix'] <= STARTUP_END, 'no_sliding_startup_after_1635')
    return session


prior.__file__ = __file__
prior.TERMINAL = TERMINAL
prior.verify_failed_start = verify_chain
prior.validate_active_session = validate_active
configured_runner = prior.configured_runner
bind_campaign = prior.bind_campaign


if __name__ == '__main__':
    prior.main()
