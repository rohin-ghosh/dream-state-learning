"""Prepare/verify node4 R158 parent configs locally; never register or launch."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shlex

from gpu import orch_r151_matched_parents as previous
from gpu import orch_r158_matched_node4 as node4


parent = previous.parent
matched = previous.matched
SCHEMA = 'R158_MATCHED_PARENTS_V1'
BRANCH = 'R158_MATCHED'
NODE = 'a40r'
WRAPPER = 'gpu/a40r_ssh.sh'
WRAPPER_SHA256 = 'ae7ded3d683311e7f5c3f95e581962e32ada4de277530537f96e6c39d34bec97'
LEASE_END = 1789776000
SAFETY_MARGIN = 21600
SOURCE_FILES = tuple(name for name in previous.SOURCE_FILES if name != 'gpu/ovx3_ssh.sh') + (
    'gpu/orch_r158_matched_parents.py', 'gpu/orch_r158_matched_node4.py', WRAPPER)


def pin(path):
    path = Path(path).absolute()
    parent.require(not any(part.is_symlink() for part in (path, *path.parents)), 'unlinked_local_input')
    return previous.pin(path)


def read_pinned(reference):
    parent.require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_input_reference')
    actual = pin(reference['path'])
    raw = Path(actual['path']).read_bytes()
    parent.require(actual == reference and hashlib.sha256(raw).hexdigest() == reference['sha256'], 'immutable_input_pin')
    return json.loads(raw)


def validate_node4(cohort, plans, cohort_sha256, budget):
    runtime_cohort = previous.validate_triplet(cohort, plans, cohort_sha256)
    parent.require(budget.get('schema') == 'R158_EXISTING_NODE4_COHORT_BUDGET_V1'
        and budget.get('derived_from') == dict(path=str(node4.LEASE_PATH), sha256=node4.LEASE_SHA256)
        and budget.get('host_sha256') == node4.HOST_SHA256
        and budget.get('physical_devices') == [5, 6, 7]
        and budget.get('lease_extended') is False and budget.get('existing_life_wall_changed') is False
        and budget.get('purchase_performed') is False, 'bound_existing_node4_budget_only')
    for field, expected in (('hard_end_unix', node4.WALL), ('lease_end_unix', LEASE_END),
                            ('safety_margin_seconds', SAFETY_MARGIN)):
        parent.require(type(budget.get(field)) is int and budget[field] == expected, 'exact_node4_budget_wall')
    parent.require(budget['hard_end_unix'] <= budget['lease_end_unix']-budget['safety_margin_seconds'],
                   'node4_reserve_not_relaxed')
    base = Path(cohort['initial_directory']).parent
    parent.require(base.parent == node4.BASE and base.name.startswith('orch_r158_matched_node4_')
        and len(base.name) > len('orch_r158_matched_node4_') and '..' not in base.parts
        and cohort['initial_directory'] == str(base/'common_initial')
        and runtime_cohort == str(base/'COHORT.json'), 'new_R158_node4_cohort_roots')
    for arm, plan in plans.items():
        physical = node4.ARMS[arm]
        parent.require(type(plan['physical']) is int and plan['physical'] == physical
            and plan['gpu_uuid'] == node4.DEVICES[physical], 'exact_node4_arm_device_UUID')
        parent.require(plan['root'] == str(base/arm) and plan['source_root'] == str(base/'source'),
                       'new_R158_node4_arm_roots')
        parent.require(type(plan['hard_end_unix']) in (int, float) and plan['hard_end_unix'] == budget['hard_end_unix']
            and type(plan['lease_end_unix']) in (int, float) and plan['lease_end_unix'] == budget['lease_end_unix'],
            'node4_plan_within_bound_budget')
        parent.require(plan['context_limit'] == 16384 and plan['segment_tokens'] == 512
            and plan.get('initialization_validation_schema') == 'R151_MATCHED_INITIAL_CAPACITY_V1',
            'node4_matched_capacity_contract')
    return runtime_cohort


def build_bundle(repository, cohort_reference, plan_references, template_reference, budget_reference):
    repository = Path(repository).resolve()
    cohort = read_pinned(cohort_reference)
    plans = {arm: read_pinned(reference) for arm, reference in plan_references.items()}
    budget = read_pinned(budget_reference)
    runtime_cohort = validate_node4(cohort, plans, cohort_reference['sha256'], budget)
    template = read_pinned(template_reference)
    parent.require(template.get('schema') == 'R133_PROGRAMME_PARENT_V1', 'existing_R133_template')
    parent.require(template.get('parent_reasoning_effort') == 'low', 'explicit_identical_low_effort')
    sources = {name: pin(template[name+'_path']) for name in ('programme', 'principles')}
    parent.require(all(reference['sha256'] == template[name+'_sha256'] for name, reference in sources.items()),
                   'fixed_parent_source')
    source_pins = {name: pin(repository/name) for name in SOURCE_FILES}
    parent.require(source_pins[WRAPPER]['sha256'] == WRAPPER_SHA256
        and source_pins[WRAPPER]['path'] == str(repository/WRAPPER), 'exact_node4_a40r_wrapper')
    for module in (parent, matched, previous, node4):
        name = 'gpu/'+Path(module.__file__).name
        parent.require(str(Path(module.__file__).resolve()) == source_pins[name]['path'], 'executed_source_binding')
    parent.require(str(Path(__file__).resolve()) == source_pins['gpu/orch_r158_matched_parents.py']['path'],
                   'executed_R158_source_binding')
    common = dict(schema='R133_PROGRAMME_PARENT_V1', node=NODE, programme=template['programme'], branch=BRANCH,
        source_root=cohort['common']['source_root'],
        programme_path=sources['programme']['path'], programme_sha256=sources['programme']['sha256'],
        principles_path=sources['principles']['path'], principles_sha256=sources['principles']['sha256'],
        parent_style=template.get('parent_style', 'responsive'), parent_reasoning_effort='low',
        cadence_label='PERSISTENT', cadence_responses=1, minimum_duration_seconds=3600,
        schedule_on='request', poll_interval_seconds=0.25, start_after_response_count=0, start_after_request_count=0,
        hard_end_unix=budget['hard_end_unix'])
    configs, arms = {}, {}
    for arm in matched.ARMS:
        enabled = arm != 'unparented_learning'
        binding = previous.matched_binding(arm, cohort_reference['sha256'])
        arms[arm] = dict(plan=plan_references[arm], matched_policy=binding, parent_enabled=enabled,
            config_file=arm+'.PARENT.json' if enabled else None, learning_enabled=binding['learning'] == 'lora',
            runtime_root=plans[arm]['root'], physical=plans[arm]['physical'], gpu_uuid=plans[arm]['gpu_uuid'])
        if enabled:
            config = dict(deepcopy(common), root=plans[arm]['root'])
            parent.validate(config)
            parent.require(parent.time.time()+3600 < config['hard_end_unix'], 'time_for_full_persistent_segment')
            configs[arm] = config
    state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[])
    prompts = [parent.prompt(config, state) for config in configs.values()]
    parent.require(prompts[0] == prompts[1], 'identical_parent_prompt_and_identity')
    parent.require({name: pin(repository/name) for name in SOURCE_FILES} == source_pins, 'unchanged_controller_sources')
    document = dict(schema=SCHEMA, status='PREPARED_CPU_ONLY_NOT_REGISTERED', repository=str(repository),
        cohort=cohort_reference, template=template_reference, budget=budget_reference,
        runtime_cohort_path=runtime_cohort, arms=arms, parent_sources=sources, source_pins=source_pins,
        node_contract=dict(node=NODE, host=node4.HOST, host_sha256=node4.HOST_SHA256,
            wrapper=source_pins[WRAPPER], physical_devices=[5, 6, 7], hard_end_unix=budget['hard_end_unix'],
            remote_identity_verified=False),
        parent_contract=dict(model=parent.STRONG, provider='gpu.orch_route_parent_campaign_providers.strong',
            prompt='gpu.orch_r133_programme_parent.prompt', cadence='persistent1', asynchronous=True,
            schedule_on='request', parent_identity=BRANCH, speaker='Astra', split='TRAIN', reasoning_effort='low',
            tools=False, arm_labels_visible=False, parent_and_environment_targets=False,
            system_sha256=hashlib.sha256(prompts[0][0].encode()).hexdigest(),
            empty_train_payload_sha256=hashlib.sha256(prompts[0][1].encode()).hexdigest(),
            realized_coverage='UNMEASURED', parenting_success_claim=False),
        registration=dict(publisher='gpu.orch_r127_pilot_console.publish_parent',
            reader='gpu.orch_r125_stream_console._read_record', consumer='gpu.orch_r150_matched_journal.MatchedJournal',
            consumer_owner='gpu.orch_r150_matched_native.run', r133_opens_journal=False,
            shared_file_patch_required=False, runtime_verified=False,
            require_main_bound_source_and_plan_verification=True, require_admitted_births=True,
            require_node4_wrapper_destination_verification=True),
        provider_calls=0, GPU_calls=0, remote_writes=0, launches=0)
    return document, configs


def prepare(repository, cohort_path, cohort_sha256, plan_paths, template_path, budget_path, budget_sha256, output):
    cohort_reference, budget_reference = pin(cohort_path), pin(budget_path)
    parent.require(cohort_reference['sha256'] == cohort_sha256, 'expected_cohort_pin')
    parent.require(budget_reference['sha256'] == budget_sha256, 'expected_budget_pin')
    document, configs = build_bundle(repository, cohort_reference, {arm: pin(path) for arm, path in plan_paths.items()},
                                    pin(template_path), budget_reference)
    output = Path(output).absolute()
    parent.require(not output.exists() and not output.is_symlink() and output == output.resolve()
        and '..' not in output.parts and not any(part.is_symlink() for part in output.parents), 'new_canonical_local_output')
    parent.require(not str(output).startswith('/localhome/'), 'controller_output_only')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    document['configs'] = {}
    for arm, config in configs.items():
        path = output/document['arms'][arm]['config_file']
        previous.write_once(path, config)
        document['configs'][arm] = pin(path)
    previous.write_once(output/'PREPARED.json', document)
    reference = pin(output/'PREPARED.json')
    previous.write_once(output/'PREPARED.sha256.json', reference)
    return reference


def verify(manifest_path, expected_sha256):
    reference = pin(manifest_path)
    parent.require(reference['sha256'] == expected_sha256, 'expected_manifest_pin')
    document = read_pinned(reference)
    parent.require(document.get('schema') == SCHEMA, 'prepared_parent_schema')
    expected, configs = build_bundle(document['repository'], document['cohort'],
        {arm: value['plan'] for arm, value in document['arms'].items()}, document['template'], document['budget'])
    supplied = deepcopy(document)
    config_references = supplied.pop('configs')
    parent.require(supplied == expected, 'exact_prepared_contract')
    parent.require(set(config_references) == set(configs), 'exact_two_parent_configs')
    for arm, config in configs.items():
        parent.require(config_references[arm]['path'] == str(Path(reference['path']).parent/expected['arms'][arm]['config_file']),
                       'bound_config_location')
        parent.require(read_pinned(config_references[arm]) == config, 'exact_bound_parent_config')
    return dict(status='VERIFIED_CPU_ONLY_NOT_REGISTERED', manifest=reference,
        parenting_success_claim=False, runtime_verified=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    preparing = commands.add_parser('prepare')
    for option in ('repository', 'cohort', 'template', 'budget', 'output'):
        preparing.add_argument('--'+option, type=Path, required=True)
    for option in ('cohort-sha256', 'budget-sha256'):
        preparing.add_argument('--'+option, required=True)
    for arm in matched.ARMS:
        preparing.add_argument('--'+arm.replace('_', '-')+'-plan', type=Path, required=True)
    verifying = commands.add_parser('verify')
    verifying.add_argument('--manifest', type=Path, required=True)
    verifying.add_argument('--sha256', required=True)
    args = parser.parse_args(argv)
    if args.action == 'prepare':
        result = prepare(args.repository, args.cohort, args.cohort_sha256,
            {arm: getattr(args, arm+'_plan') for arm in matched.ARMS}, args.template, args.budget, args.budget_sha256, args.output)
        result['verify_command'] = shlex.join(['python3', '-B', '-m', 'gpu.orch_r158_matched_parents',
            'verify', '--manifest', result['path'], '--sha256', result['sha256']])
    else:
        result = verify(args.manifest, args.sha256)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
