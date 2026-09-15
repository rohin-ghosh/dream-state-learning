"""Native CPU-only compiler. No model loading, provider dispatch or GPU allocation."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from organism_v6 import orch_teacher_branching_pilot as pilot


PUBLICATION = 'research_notes/analysis/orch_route_parent_campaign_20260915_teacher_exemplar_publication/'
MATH = 'research_notes/analysis/orch_math_pipeline_l2_20260915_attempt1/COHORT.json'
ROUTE = 'research_notes/analysis/orch_route_parent_campaign_20260915_monitor_v2/matched_complete/'
MAIN = 'research_notes/analysis/orch_branching_method_correction_20260915_0556.md'
INVENTORY_SHA = 'e635c8c06d6287f9782569f65ae9e6897b16849ad22d560ce1a21b4f1f257592'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
AUDIT_SHA = '00879122082c15c1b2ed7c496aeb955a68f7bcc423060480757ef4da3ea18139'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_once(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def compile_native(inputs, raw, legacy, output):
    from transformers import AutoTokenizer
    from gpu import astra_portable_actor_bundle as portable
    from gpu.orch_l2_shared_run import legacy_encode

    pilot.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_visible_devices_empty')
    pilot.require(str(output.resolve()).startswith('/localhome/local-rohing/orch_teacher_branching_pilot_'),
                  'native_only_teacher_output_root')
    output.mkdir(exist_ok=False)
    inventory_path = inputs / PUBLICATION / 'NODE_RAW_INVENTORY.json'
    pilot.require(sha(inventory_path) == INVENTORY_SHA, 'published_native_inventory_pin')
    inventory = read(inventory_path)
    bindings = {}
    for entry in inventory:
        path = raw / entry['path']
        pilot.require(raw.resolve() in path.resolve().parents and not path.is_symlink(), 'native_inventory_scope')
        pilot.require(path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256'], 'native_source_hash')
        bindings[entry['path']] = dict(path=str(path), sha256=entry['sha256'])
    roster, oracles = read(raw / 'ROSTER.json'), read(raw / 'PRIVATE_CHECKS.json')
    for relative in (MATH, ROUTE + 'COHORT.json', ROUTE + 'SOURCE.json'):
        pilot.require(sha(inputs / relative) == roster['source_files'][relative], 'original_cohort_hash')
    math_cohort, route_cohort = read(inputs / MATH), read(inputs / ROUTE / 'COHORT.json')
    tasks, checks, exclusions = pilot.teacher.freeze_tasks(math_cohort, route_cohort, read(inputs / ROUTE / 'SOURCE.json'))
    pilot.require(tasks == roster['tasks'] and checks == oracles, 'exact_original_train_roster_and_gold')
    audit_path = inputs / PUBLICATION / 'METHOD_AUDIT_REMAINING_20260915.json'
    pilot.require(sha(audit_path) == AUDIT_SHA, 'published_remaining_audit_pin')
    audit = read(audit_path)
    pilot.require(sha(inputs / MAIN) == audit['main_correction']['sha256'], 'published_main_six_audit')
    pilot.require(sha(inputs / audit['native_checks']['path']) == audit['native_checks']['sha256'], 'published_remaining_native_checks')
    pilot.require(audit['source_label'] == pilot.LABEL and audit['independent_review_verdict'] is False
        and audit['native_inventory_sha256'] == INVENTORY_SHA
        and sorted(audit['scope_ordinals']) == [4, 5, 6, 7, 10, 11, 12, 13, 14, 15], 'remaining_audit_scope')
    annotations = {entry['ordinal']: entry for entry in audit['annotations']}
    pilot.require(len(annotations) == 10 and all(entry['same_given_grounded']
        and entry['full_prompt_methods_checks_limitations_read'] and not entry['errors_detected']
        for entry in annotations.values()), 'author_grounding_supported')
    held_ids = {task['id'] for group in math_cohort['held'] for task in group}
    held_ids.update(value for group in route_cohort['held'] for world in group
                    for edge in world['edges'] for value in edge.values())
    rows = []
    for ordinal, task in enumerate(tasks):
        call = f'calls/{ordinal:02d}/'
        prompt_path = f'prompts/{ordinal:02d}/USER.json'
        pilot.require(read(raw / prompt_path) == task, 'original_teacher_prompt')
        response = pilot.teacher.parse_response(read(raw / call / 'RAW_RESPONSE.json'))
        pilot.require(response == read(raw / call / 'TEACHER_EXEMPLAR.json'), 'exact_provider_exemplar')
        if ordinal in annotations:
            pilot.require(annotations[ordinal]['source_hashes']['TEACHER_EXEMPLAR.json'] ==
                bindings[call + 'TEACHER_EXEMPLAR.json']['sha256'], 'audit_response_hash')
        support = dict(author_supported=True, independent_certification=False,
            audit_path=str(audit_path if ordinal in annotations else inputs / MAIN),
            audit_sha256=sha(audit_path if ordinal in annotations else inputs / MAIN),
            diversity=annotations[ordinal]['diversity'] if ordinal in annotations else
                ('WEAK_ALGEBRAIC_REARRANGEMENT' if ordinal in (1, 3) else 'MAIN_AUTHOR_SUPPORTED_PAIR'),
            repetition_semantics='NOT_EXHAUSTIVELY_CERTIFIED', method_count_selfreported=len(response['methods']))
        refs = {name: bindings[call + name] for name in
                ('RAW_RESPONSE.json', 'TEACHER_EXEMPLAR.json', 'ANSWER_CHECK.json', 'RECEIPT.json', 'REQUEST.json')}
        refs['USER.json'] = bindings[prompt_path]
        rows.append(pilot.compile_row(task, response, checks[task['task_id']], held_ids, refs, support))
    prepared = read(legacy / 'PREPARE.json')
    pilot.require(prepared['initial']['state_sha256'] == pilot.STATE
                  and prepared['initial']['base_sha256'] == pilot.BASE, 'original37ec_initial_state')
    bundle, model = Path(prepared['bundle']), Path(prepared['model_dir'])
    base = portable.verify_base_files(bundle, model, expected_manifest_sha256=BUNDLE_SHA)
    for name, expected in prepared['initial']['files']:
        pilot.require(sha(Path(prepared['initial']['path']) / name) == expected, 'initial_adapter_hash')
    model_config = read(model / 'config.json')
    pilot.require(model_config['max_position_embeddings'] >= pilot.CONTEXT, 'base_context_support')
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    old = legacy_encode(legacy, tokenizer)
    encoded = pilot.encode_rows(rows, tokenizer)
    rehearsal = pilot.paired_rehearsal(old, encoded)
    write_once(output / 'ROWS.json', rows)
    write_once(output / 'ENCODED_TEACHER.json', [asdict(row) for row in encoded])
    write_once(output / 'REHEARSAL.json', rehearsal)
    write_once(output / 'PROTOCOL.json', pilot.protocol())
    write_once(output / 'READOUT_COHORT.json', pilot.readout_cohort(math_cohort, route_cohort))
    source_root = Path(__file__).resolve().parents[1]
    source_files = {str(path.relative_to(source_root)): sha(path) for folder in ('gpu', 'organism_v6')
                    for path in (source_root / folder).rglob('*.py')}
    manifest = dict(schema='ORCH_TEACHER_BRANCHING_PILOT_NATIVE_COMPILE_V1',
        status='CPU_COMPILED_NOT_ALLOCATED_NOT_TRAINED', authored_utc=datetime.now(timezone.utc).isoformat(),
        source_label=pilot.LABEL, rows=16, math_rows=8, route_rows=8,
        training_application_allowed=False, ongoing_l1_allowed=False, provider_calls=0, gpu_calls=0,
        source_inventory_sha256=INVENTORY_SHA, verified_source_files=len(bindings),
        source_root=str(source_root), runtime_source_sha256=pilot.digest(source_files),
        runtime_source_files=source_files, original_initial=prepared['initial'], base_verified=base,
        base_max_position_embeddings=model_config['max_position_embeddings'],
        held_exclusions=exclusions, teacher_prompt_excluded=True, parents_blind=True,
        independent_certification=False, own_trajectory_success=False,
        token_counts=[dict(ordinal=ordinal, context=len(row.input_ids), supervised=len(row.target_ids))
                      for ordinal, row in enumerate(encoded)],
        legacy_refs={name: dict(path=str(legacy / name), sha256=sha(legacy / name))
                     for name in ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json')},
        files={path.name: dict(path=str(path), sha256=sha(path)) for path in sorted(output.iterdir())})
    write_once(output / 'MANIFEST.json', manifest)
    return dict(native_manifest=str(output / 'MANIFEST.json'), sha256=sha(output / 'MANIFEST.json'),
                rows=16, status=manifest['status'], token_counts=manifest['token_counts'],
                runtime_source_sha256=manifest['runtime_source_sha256'], rehearsal=rehearsal,
                protocol=pilot.protocol(), held_exclusions=exclusions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'raw', 'legacy', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compile_native(args.inputs, args.raw, args.legacy, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
