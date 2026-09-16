"""Prospective F4 optional head-field compatibility; no model calls in diagnose."""

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace


SCRATCH_SOURCE = Path('/data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1/gpu/orch_r139_grid_broker_scratch.py')
SCRATCH_SHA = '790d65d1e69b4dd6d514ed3572fb458b1e7d6d748cea3feddd373333e6b3300b'
PROMPTS = Path('/data/home/rohing/courier/swarm/prompts')
CONFIG = SCRATCH_SOURCE.parent.parent / 'F4_ASTRA_CONFIG.json'
REQUIRED = {'GAME', 'STYLE', 'NUDGING', 'FOCUS', 'REFLECTION'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_ref():
    return dict(path=str(Path(__file__).resolve()), sha256=sha(__file__))


def dependencies():
    require(sha(SCRATCH_SOURCE) == SCRATCH_SHA, 'frozen_scratch_source')
    spec = importlib.util.spec_from_file_location('r139_head_frozen_scratch', SCRATCH_SOURCE)
    scratch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scratch)
    handoff, http = scratch.load_runtime()
    return scratch, handoff, http


def replace_one(text, before, after):
    require(text.count(before) == 1, 'exact_frozen_prompt_site')
    return text.replace(before, after, 1)


def prompt_view(scratch, transport):
    def render(fields):
        require(isinstance(fields, dict) and REQUIRED <= set(fields) <= REQUIRED | {'NEXT_GUIDANCE'},
                'head_fields_keys')
        if 'NEXT_GUIDANCE' in fields:
            require(isinstance(fields['NEXT_GUIDANCE'], str)
                    and len(fields['NEXT_GUIDANCE'].encode()) <= 1024, 'bounded_next_guidance')
        return transport.render_parent_prompt({key: value for key, value in fields.items() if key in REQUIRED})

    head = scratch.bind(transport.head_binding, render_parent_prompt=render)
    source = inspect.getsource(transport.build_system)
    source = replace_one(source,
        "    parent_policy = prompt + '\\n\\n' + principles + '\\n\\n' + SYSTEM_CONTRACT",
        "    parent_policy = prompt + '\\n\\n' + principles\n"
        "    next_guidance = settings['fields'].get('NEXT_GUIDANCE', '')\n"
        "    if next_guidance:\n"
        "        parent_policy += '\\n\\nASYNCHRONOUS HEAD NEXT_GUIDANCE:\\n' + next_guidance\n"
        "    parent_policy += '\\n\\n' + SYSTEM_CONTRACT")
    source = replace_one(source,
        '        head_settings=settings, head_settings_sha256=digest(settings),',
        '        head_settings=settings, head_settings_sha256=digest(settings),\n'
        "        next_guidance_sha256=hashlib.sha256(next_guidance.encode()).hexdigest(),\n"
        '        head_waited=False,')
    namespace = dict(transport.build_system.__globals__, render_parent_prompt=render, head_binding=head)
    exec(compile(source, __file__ + ':pinned_F4_build_system', 'exec'), namespace)
    build = namespace['build_system']
    def build_F4(transcript, config, prompt_root, principles_path):
        require(config['branch'] == 'F4' and config['family'] == 'grid', 'F4_grid_only')
        return build(transcript, config, prompt_root, principles_path)
    return SimpleNamespace(**dict(vars(transport), render_parent_prompt=render, head_binding=head, build_system=build_F4))


def authorize(scratch, handoff, plan, publication, plan_sha, mode, now, floor):
    scratch.authorize(handoff, plan, publication, plan_sha, mode, now)
    require(publication.get('head_fields_wrapper') == source_ref()
            and type(floor) is int and 323 <= floor < plan['cumulative_caps']['PARENT']
            and publication.get('repair_after_parent') == floor
            and publication.get('P0323_preserved_no_retry') is True, 'Main_published_prospective_head_repair')


def broker_builder(scratch, handoff, http, floor):
    transport = prompt_view(scratch, http.astra.transport)
    astra = SimpleNamespace(**dict(vars(http.astra), transport=transport))
    view = SimpleNamespace(**dict(vars(http), astra=astra,
        evaluate=scratch.bind(http.evaluate, transport=transport)))
    def guarded_authorize(current_handoff, plan, publication, plan_sha, mode, now):
        return authorize(scratch, handoff, plan, publication, plan_sha, mode, now, floor)
    factory = scratch.bind(scratch.broker_builder, authorize=guarded_authorize)(handoff, scratch.runtime_path(scratch.SCRATCH))
    def build(unused_http, boundary, plan, publication, plan_sha):
        serving = factory(view, boundary, plan, publication, plan_sha)
        original = serving.__globals__['process_request']
        def process_request(store, config, launch, name, buffer, prompt_root, principles_path):
            require(re.fullmatch(r'P[0-9]{4,}\.request\.json', name), 'numbered_request')
            if int(name.split('.')[0][1:]) <= floor:
                return 'PRE_REPAIR_HISTORICAL_NO_REDISPATCH'
            return original(store, config, launch, name, buffer, prompt_root, principles_path)
        return scratch.bind(serving, process_request=process_request)
    return build


def diagnose(scratch, handoff, http):
    transport = http.astra.transport
    repaired = prompt_view(scratch, transport)
    prompt_path = PROMPTS / 'F4.md'
    settings_path = prompt_path.with_suffix('.fields.json')
    principles = handoff.BROKER_RUNTIME / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
    paths = [prompt_path, settings_path, CONFIG, principles]
    before = {str(path): sha(path) for path in paths}
    config = transport.loads(CONFIG.read_text())
    fields = transport.loads(settings_path.read_text())['fields']
    transcript = dict(game='grid', cycle=111, episode=0, phase='experience')
    report = dict(schema='R139_F4_HEAD_FIELDS_CPU_DIAGNOSTIC_V1', source_sha256=sha(__file__),
        files_sha256=before, transport_sha256=sha(transport.__file__), field_keys=sorted(fields),
        next_guidance_bytes=len(fields['NEXT_GUIDANCE'].encode()) if isinstance(fields.get('NEXT_GUIDANCE'), str) else None,
        synthetic_transcript_only=True, actual_request_read=False, provider_calls=0)
    for name, callback in [('original_head_binding', lambda: transport.head_binding(prompt_path, prompt_path.read_bytes())),
                           ('original_build_system', lambda: transport.build_system(transcript, config, PROMPTS, principles))]:
        try:
            callback()
            report[name] = dict(status='PASS')
        except ValueError as error:
            report[name] = dict(status='ERROR', type=type(error).__name__,
                code=str(error) if str(error) in {'head_fields_keys', 'fixed_v4_parent_prompt_drift', 'principles_hash_changed'} else 'OTHER_VALUE_ERROR')
    system, prompt, binding = repaired.build_system(transcript, config, PROMPTS, principles)
    report['repaired'] = dict(status='PASS', prompt_sha256=hashlib.sha256(prompt).hexdigest(),
        binding_status=binding['head_settings']['status'], system_sha256=hashlib.sha256(system.encode()).hexdigest(),
        next_guidance_sha256=binding['next_guidance_sha256'], transport_contract_sha256=binding['transport_contract_sha256'],
        prompt_bytes_unchanged=prompt == prompt_path.read_bytes(), head_waited=binding['head_waited'])
    require(before == {str(path): sha(path) for path in paths}, 'diagnostic_inputs_unchanged')
    report['inputs_unchanged'] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('diagnose', 'broker'))
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--publication', type=Path)
    args = parser.parse_args()
    require(sha(__file__) == args.expected_self_sha256 and sys.dont_write_bytecode, 'immutable_no_bytecode_command')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    if args.mode == 'diagnose':
        print(json.dumps(diagnose(*dependencies()), sort_keys=True, indent=2))
        return
    require(args.plan is not None and args.publication is not None, 'explicit_Main_publication')
    scratch, handoff, http = dependencies()
    require(args.plan_sha256 == scratch.PLAN_SHA and sha(args.plan) == scratch.PLAN_SHA, 'exact_frozen_plan')
    scratch.runtime_path(args.plan)
    scratch.runtime_path(args.publication)
    plan, publication = handoff.read(args.plan.resolve()), handoff.read(args.publication.resolve())
    floor = publication.get('repair_after_parent')
    authorize(scratch, handoff, plan, publication, scratch.PLAN_SHA, 'broker', time.time(), floor)
    scratch.private_scratch()
    broker = scratch.bind(handoff.broker, broker_functions=broker_builder(scratch, handoff, http, floor))
    broker(plan, publication, scratch.PLAN_SHA, args.publication.resolve())


if __name__ == '__main__':
    main()
