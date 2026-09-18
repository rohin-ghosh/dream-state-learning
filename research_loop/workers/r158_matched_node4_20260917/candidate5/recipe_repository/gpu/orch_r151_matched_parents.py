"""Prepare and verify local R151 parent configs; never contact a provider or node."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shlex

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r150_matched_native as matched
from organism_v6.orch_r150_matched_stream import matched_binding


SCHEMA = 'R151_MATCHED_PARENTS_V1'
BRANCH = 'R151_MATCHED'
SOURCE_FILES = (
    'gpu/orch_r151_matched_parents.py',
    'gpu/orch_r133_programme_parent.py',
    'gpu/orch_route_parent_campaign_providers.py',
    'gpu/orch_route_parent_campaign_parent.py',
    'gpu/orch_l2_long_backend.py',
    'gpu/orch_l2_shared_run.py',
    'gpu/orch_r125_stream_console.py',
    'gpu/orch_r127_pilot_console.py',
    'gpu/orch_r125_stream_journal.py',
    'gpu/orch_r125_continual_native.py',
    'gpu/orch_r150_matched_native.py',
    'gpu/orch_r150_matched_journal.py',
    'organism_v6/orch_guided_bridge.py',
    'organism_v6/orch_route_parent_campaign.py',
    'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r125_plain_context.py',
    'organism_v6/orch_r150_matched_stream.py',
    'gpu/ovx3_ssh.sh',
)
ALLOCATION_KEYS = {'root', 'gpu_uuid', 'physical', 'matched_arm', 'parent_enabled'}


def local_file(path):
    path = Path(path)
    parent.require('..' not in path.parts and not path.is_symlink(), 'regular_local_input')
    parent.require(not any(re.search(r'(^|[_ .-])(held|final|readout|sealed)([_ .-]|$)',
        part, re.IGNORECASE) for part in path.parts), 'no_evaluation_input')
    path = path.resolve()
    parent.require(path.is_file(), 'regular_local_input')
    return path


def pin(path):
    path = local_file(path)
    return dict(path=str(path), sha256=parent.sha(path))


def read_pinned(reference):
    path = local_file(reference['path'])
    raw = path.read_bytes()
    parent.require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'immutable_input_pin')
    return json.loads(raw)


def validate_triplet(cohort, plans, cohort_sha256):
    parent.require(set(plans) == set(matched.ARMS), 'exact_three_matched_plans')
    reconstructed = matched.cohort_document(list(plans.values()), cohort['initial_directory'])
    parent.require(cohort == reconstructed, 'exact_cohort_contract')
    common = None
    cohort_path = None
    for arm in matched.ARMS:
        plan = plans[arm]
        parent.require(plan['matched_arm'] == arm, 'plan_arm_binding')
        reference = plan['matched_cohort']
        parent.require(set(reference) == {'path', 'sha256'}
            and reference['sha256'] == cohort_sha256, 'immutable_matched_cohort')
        path = Path(reference['path'])
        parent.require(path.is_absolute() and '..' not in path.parts, 'absolute_runtime_cohort')
        parent.require(cohort_path in (None, reference['path']), 'same_runtime_cohort_path')
        cohort_path = reference['path']
        normalized = {key: value for key, value in plan.items() if key not in ALLOCATION_KEYS}
        parent.require(common is None or normalized == common, 'only_matched_condition_and_allocation_differ')
        common = normalized
        parent.require(plan['schema'] == matched.native.SCHEMA
            and plan['base_sha256'] == matched.native.BASE_SHA256, 'frozen_native_contract')
        parent.require(plan.get('authorized_wall_extension') is None
            and plan.get('preupdate_recovery') is None, 'no_handoff_or_lease_change')
    return cohort_path


def build_bundle(repository, cohort_reference, plan_references, template_reference):
    repository = Path(repository).resolve()
    cohort = read_pinned(cohort_reference)
    plans = {arm: read_pinned(reference) for arm, reference in plan_references.items()}
    runtime_cohort = validate_triplet(cohort, plans, cohort_reference['sha256'])
    template = read_pinned(template_reference)
    parent.require(template.get('schema') == 'R133_PROGRAMME_PARENT_V1', 'existing_R133_template')
    parent.require(template.get('parent_reasoning_effort') in ('low', 'medium', 'high', 'xhigh'),
        'explicit_shared_effort_not_provider_default')
    sources = {}
    for name in ('programme', 'principles'):
        reference = pin(template[name+'_path'])
        parent.require(reference['sha256'] == template[name+'_sha256'], 'fixed_parent_source')
        sources[name] = reference
    common = dict(schema='R133_PROGRAMME_PARENT_V1', node='ovx3',
        programme=template['programme'], branch=BRANCH,
        source_root=cohort['common']['source_root'],
        programme_path=sources['programme']['path'], programme_sha256=sources['programme']['sha256'],
        principles_path=sources['principles']['path'], principles_sha256=sources['principles']['sha256'],
        parent_style=template.get('parent_style', 'responsive'),
        parent_reasoning_effort=template['parent_reasoning_effort'],
        cadence_label='PERSISTENT', cadence_responses=1, minimum_duration_seconds=3600,
        schedule_on='request', poll_interval_seconds=0.25,
        start_after_response_count=0, start_after_request_count=0,
        hard_end_unix=cohort['common']['hard_end_unix'])
    parent.require(common['hard_end_unix'] <= cohort['common']['lease_end_unix']-120,
        'within_existing_lease_wall')
    configs = {}
    arms = {}
    for arm in matched.ARMS:
        binding = matched_binding(arm, cohort_reference['sha256'])
        enabled = arm != 'unparented_learning'
        arms[arm] = dict(plan=plan_references[arm], matched_policy=binding,
            parent_enabled=enabled, config_file=arm+'.PARENT.json' if enabled else None,
            learning_enabled=binding['learning'] == 'lora', runtime_root=plans[arm]['root'])
        if enabled:
            config = dict(deepcopy(common), root=plans[arm]['root'])
            parent.validate(config)
            parent.require(parent.time.time()+config['minimum_duration_seconds'] < config['hard_end_unix'],
                'time_for_full_persistent_segment')
            configs[arm] = config
    state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[])
    prompts = [parent.prompt(config, state) for config in configs.values()]
    parent.require(prompts[0] == prompts[1], 'identical_parent_prompt_and_identity')
    source_pins = {name: pin(repository/name) for name in SOURCE_FILES}
    parent.require(Path(parent.__file__).resolve() == Path(source_pins[
        'gpu/orch_r133_programme_parent.py']['path']), 'executed_parent_source_binding')
    parent.require(Path(matched.__file__).resolve() == Path(source_pins[
        'gpu/orch_r150_matched_native.py']['path']), 'executed_matched_source_binding')
    document = dict(schema=SCHEMA, status='PREPARED_CPU_ONLY_NOT_REGISTERED',
        repository=str(repository), cohort=cohort_reference, template=template_reference,
        runtime_cohort_path=runtime_cohort, arms=arms, parent_sources=sources, source_pins=source_pins,
        parent_contract=dict(model=parent.STRONG, provider='gpu.orch_route_parent_campaign_providers.strong',
            prompt='gpu.orch_r133_programme_parent.prompt', cadence='persistent1', asynchronous=True,
            schedule_on='request', parent_identity=BRANCH, speaker='Astra', split='TRAIN',
            tools=False, arm_labels_visible=False, parent_and_environment_targets=False,
            system_sha256=hashlib.sha256(prompts[0][0].encode()).hexdigest(),
            empty_train_payload_sha256=hashlib.sha256(prompts[0][1].encode()).hexdigest(),
            realized_coverage='UNMEASURED', parenting_success_claim=False),
        registration=dict(publisher='gpu.orch_r127_pilot_console.publish_parent',
            reader='gpu.orch_r125_stream_console._read_record',
            consumer='gpu.orch_r150_matched_journal.MatchedJournal',
            consumer_owner='gpu.orch_r150_matched_native.run',
            r133_opens_journal=False, shared_file_patch_required=False,
            runtime_verified=False, require_main_bound_source_and_plan_verification=True),
        provider_calls=0, GPU_calls=0, remote_writes=0, launches=0)
    return document, configs


def write_once(path, document):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(document, output, sort_keys=True, indent=2, allow_nan=False)
        output.write('\n')
        output.flush()
        os.fchmod(output.fileno(), 0o400)
        os.fsync(output.fileno())


def prepare(repository, cohort_path, cohort_sha256, plan_paths, template_path, output):
    cohort_reference = pin(cohort_path)
    parent.require(cohort_reference['sha256'] == cohort_sha256, 'expected_cohort_pin')
    plan_references = {arm: pin(path) for arm, path in plan_paths.items()}
    template_reference = pin(template_path)
    document, configs = build_bundle(repository, cohort_reference, plan_references, template_reference)
    output = Path(output).absolute()
    parent.require(not output.exists() and not output.is_symlink()
        and output == output.resolve(), 'new_canonical_local_output')
    parent.require(not str(output).startswith('/localhome/'), 'controller_output_only')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    config_pins = {}
    for arm, config in configs.items():
        path = output/document['arms'][arm]['config_file']
        write_once(path, config)
        config_pins[arm] = pin(path)
    document['configs'] = config_pins
    write_once(output/'PREPARED.json', document)
    reference = pin(output/'PREPARED.json')
    write_once(output/'PREPARED.sha256.json', reference)
    return reference


def verify(manifest_path, expected_sha256):
    reference = pin(manifest_path)
    parent.require(reference['sha256'] == expected_sha256, 'expected_manifest_pin')
    document = read_pinned(reference)
    parent.require(document.get('schema') == SCHEMA, 'prepared_parent_schema')
    expected, configs = build_bundle(document['repository'], document['cohort'],
        {arm: value['plan'] for arm, value in document['arms'].items()}, document['template'])
    supplied = deepcopy(document)
    config_references = supplied.pop('configs')
    parent.require(supplied == expected, 'exact_prepared_contract')
    parent.require(set(config_references) == set(configs), 'exact_two_parent_configs')
    for arm, config in configs.items():
        parent.require(read_pinned(config_references[arm]) == config, 'exact_bound_parent_config')
    return dict(status='VERIFIED_CPU_ONLY_NOT_REGISTERED', manifest=reference,
        parenting_success_claim=False, runtime_verified=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    preparing = commands.add_parser('prepare')
    for option in ('repository', 'cohort', 'template', 'output'):
        preparing.add_argument('--'+option, type=Path, required=True)
    preparing.add_argument('--cohort-sha256', required=True)
    for arm in matched.ARMS:
        preparing.add_argument('--'+arm.replace('_', '-')+'-plan', type=Path, required=True)
    verifying = commands.add_parser('verify')
    verifying.add_argument('--manifest', type=Path, required=True)
    verifying.add_argument('--sha256', required=True)
    args = parser.parse_args(argv)
    if args.action == 'prepare':
        result = prepare(args.repository, args.cohort, args.cohort_sha256,
            {arm: getattr(args, arm+'_plan') for arm in matched.ARMS}, args.template, args.output)
        result['verify_command'] = shlex.join(['python3', '-m', 'gpu.orch_r151_matched_parents',
            'verify', '--manifest', result['path'], '--sha256', result['sha256']])
    else:
        result = verify(args.manifest, args.sha256)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
