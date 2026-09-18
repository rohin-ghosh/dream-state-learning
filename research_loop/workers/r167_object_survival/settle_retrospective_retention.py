"""Settle frozen retrospective judgments privately, without any provider calls."""

from collections import Counter
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
FROZEN_SOURCE = HERE / 'semantic51_generation1/source'
sys.path.insert(0, str(FROZEN_SOURCE))
import semantic_judge as judge
import semantic_judge_continuation as continuation

protocol = judge.protocol
PRIVATE = Path('/tmp/orch_r167_retention_report_20260917_generation1_private')
REMOTE = protocol.CAMPAIGN / 'private_appendices/retention_report_20260917_generation1'
POSITIVE = {'SPECIFIC_IDENTITY', 'SPECIFIC_IDENTITY_WITH_RELATIONAL_DETAIL'}
NON_IDENTIFICATION = {'NO_IDENTIFIABLE_EVIDENCE', 'GENERIC_CATEGORY_ONLY'}


def identity_state(cell):
    if cell['status'] != 'ANNOTATED':
        return 'MISSING'
    label = cell['annotation']['identity']
    if label in POSITIVE:
        return 'IDENTIFIABLE'
    if label in NON_IDENTIFICATION:
        return 'NON_IDENTIFICATION'
    protocol.require(label in {'AMBIGUOUS', 'CONFLICTING_FEATURES'}, 'unchanged_identity_labels')
    return 'INDETERMINATE'


def paired(on, off):
    states = (identity_state(on), identity_state(off))
    if 'MISSING' in states:
        return 'MISSING'
    if 'INDETERMINATE' in states:
        return 'INDETERMINATE'
    return {('IDENTIFIABLE', 'NON_IDENTIFICATION'): 'ON_NOT_OFF',
        ('IDENTIFIABLE', 'IDENTIFIABLE'): 'ON_AND_OFF',
        ('NON_IDENTIFICATION', 'IDENTIFIABLE'): 'OFF_ONLY',
        ('NON_IDENTIFICATION', 'NON_IDENTIFICATION'): 'NEITHER_IDENTIFIED'}[states]


def make_rows(entries, annotations):
    lookup = {}
    for entry in entries:
        address = (entry['comparison_sleep'], entry['key'], entry['position'])
        protocol.require(address not in lookup, 'no_duplicate_comparison_cells')
        protocol.require(entry['comparison_sleep'] in range(8, 26) and entry['position'] in range(3), 'registered_comparison_only')
        protocol.require(entry['key'] in {f'{sleep}_{condition}' for sleep in (0, entry['comparison_sleep'])
            for condition in ('LORA_ON', 'LORA_OFF')}, 'exact_checkpoint_comparison_join')
        record = annotations[entry['opaque_id']]
        lookup[address] = dict(record, mapping=entry)
    rows = []
    for sleep in range(8, 26):
        for position in range(3):
            cells = {}
            for checkpoint in (0, sleep):
                for condition in ('LORA_ON', 'LORA_OFF'):
                    key = f'{checkpoint}_{condition}'
                    cells[key] = lookup.get((sleep, key, position), dict(status='NOT_IN_FIXED_SEMANTIC_BATCH'))
            on, off = cells[f'{sleep}_LORA_ON'], cells[f'{sleep}_LORA_OFF']
            comparison = paired(on, off)
            cue_clear = comparison == 'ON_NOT_OFF' and all(cell['annotation']['cueing'] == 'UNCUED' for cell in (on, off))
            rows.append(dict(sleep=sleep, prompt=position + 1, cells=cells,
                checkpoint_pair=comparison, initial_pair=paired(cells['0_LORA_ON'], cells['0_LORA_OFF']),
                paired_uncued_interpretation_ready=cue_clear,
                baseline_and_other_prompts_are_not_primary_gates=True))
    return rows


def validate_annotation(record, packet, base, clarified):
    judge.packet_validate(packet)
    protocol.require(record['opaque_id'] == packet['opaque_id'] and record['parent_access'] is False,
        'annotation_exact_packet_and_visibility')
    protocol.require(record['judge_model'] == judge.MODEL and record['effort'] == 'high'
        and record['max_output_tokens'] == 4096 and record['configuration'] == base['provider_config'], 'historical_judge_provenance')
    envelope = dict(speak=True, message='Private annotation recorded.', rationale=protocol.json.dumps(record['annotation']))
    protocol.require(judge.annotation(envelope, packet) == record['annotation'], 'unchanged_strict_validator_no_reannotation')
    payload = continuation.request(packet, RUBRIC_TEXT) if clarified else judge.request(packet, RUBRIC_TEXT)
    protocol.require(protocol.digest(protocol.parse(payload)) == record['request_sha256'], 'exact_historical_request')
    if clarified:
        protocol.require(record['representation'] == continuation.REPRESENTATION and
            record['rendered_evidence_sha256'] == protocol.digest(continuation.rendered_evidence(packet)), 'clarification_not_new_rubric')


def collect(plan, base, inventory, freeze, settlement):
    records = {}
    packet_by_path = {entry['path']: entry for entry in inventory['packets']}
    protocol.require(len(packet_by_path) == 60 and len(freeze['terminals']) == 51, 'exact_fixed60_and51')
    protocol.require(plan['remaining_packets'] == continuation.partition(inventory, settlement), 'unchanged_unconsumed_partition')
    valid_original = 0
    for item in settlement['consumed']:
        reference = item['packet']
        protocol.require(packet_by_path.get(reference['path']) == reference, 'original_registered_packet')
        packet_id = Path(reference['path']).stem
        reservation = protocol.bound(item['reservation'])
        protocol.require(reservation['packet'] == reference and reservation['calls_charged'] == 1, 'original_charge_preserved')
        protocol.bound(item['dispatch'])
        protocol.bound(item['worker_once'])
        record = dict(opaque_id=packet_id, packet=reference, generation='ORIGINAL9',
            original_disposition=item['disposition'], original_controller_terminal=item['original_controller_terminal'],
            source_settlement=item, status='ORIGINAL_INVALID_MISSING', calls_charged=1)
        if item['annotation'] is not None:
            annotation = protocol.bound(item['annotation'])
            packet_path = Path(base['private_vm_root']) / packet_id / 'PACKET.private.json'
            protocol.require(protocol.sha(packet_path) == reference['sha256'], 'original_exact_frozen_packet')
            packet = protocol.read(packet_path)
            validate_annotation(annotation, packet, base, False)
            protocol.require(annotation['annotation_frozen_unix'] <= settlement['observed_unix'], 'original_annotation_precedes_settlement')
            record.update(status='ANNOTATED', annotation=annotation['annotation'], annotation_receipt=item['annotation'],
                annotation_envelope=annotation, truncated=packet['truncated'], terminal=packet['terminal'])
            valid_original += 1
        protocol.require(packet_id not in records, 'unique_original_packet')
        records[packet_id] = record
    protocol.require(valid_original == 1, 'preserve_exact_original_one_valid_eight_missing')
    remaining = {Path(reference['path']).stem: reference for reference in plan['remaining_packets']}
    for terminal_ref in freeze['terminals']:
        packet_id = Path(terminal_ref['path']).parent.name
        protocol.require(packet_id in remaining and packet_id not in records, 'exact_new_packet_not_original_retry')
        terminal = protocol.bound(terminal_ref)
        protocol.require(terminal['status'] == 'COMPLETE' and terminal['calls_charged'] == 1, 'all51_frozen_complete')
        annotation = protocol.bound(terminal['annotation'])
        protocol.require(terminal['uploaded']['sha256'] == terminal['annotation']['sha256'], 'uploaded_annotation_binding')
        directory = Path(plan['private_vm_root']) / packet_id
        reservation = protocol.read(directory / 'RESERVED.json')
        protocol.require(reservation['packet'] == remaining[packet_id] and reservation['calls_charged'] == 1, 'continuation_charge_preserved')
        protocol.require((directory / 'DISPATCH.json').exists() and (directory / 'WORKER_ONCE.json').exists(), 'actual_once_dispatch_witness')
        packet_path = directory / 'PACKET.private.json'
        protocol.require(protocol.sha(packet_path) == remaining[packet_id]['sha256'], 'exact_continuation_packet')
        packet = protocol.read(packet_path)
        validate_annotation(annotation, packet, base, True)
        protocol.require(annotation['annotation_frozen_unix'] <= freeze['frozen_unix'], 'annotation_precedes_unblinding_freeze')
        records[packet_id] = dict(opaque_id=packet_id, packet=remaining[packet_id], generation='CONTINUATION51',
            status='ANNOTATED', annotation=annotation['annotation'], annotation_receipt=terminal['annotation'],
            annotation_envelope=annotation, terminal_receipt=terminal_ref, remote_annotation=terminal['uploaded'],
            calls_charged=1, truncated=packet['truncated'], terminal=packet['terminal'])
    protocol.require(len(records) == 60 and sum(row['status'] == 'ANNOTATED' for row in records.values()) == 52,
        'exact52_valid_eight_missing_no_new_judgment')
    return records


def read_mapping_after_freeze(base, inventory, freeze_ref):
    frozen = protocol.bound(freeze_ref)
    protocol.require(frozen['status'] == 'ALL60_DISPOSITIONS_FROZEN_BEFORE_PRIVATE_JOIN' and
        frozen['valid_annotations'] == 52 and frozen['original_invalid_missing'] == 8 and frozen['unblinded'] is False,
        'combined_freeze_required_before_map')
    return protocol.parse(judge.remote_read(base, inventory['mapping']))


def audit_raw_receipts(base, plan_ref):
    script = r'''import hashlib,json,time
from pathlib import Path
root=Path(ROOT_VALUE);reference=PLAN_VALUE
def sha(path):
 path=Path(path)
 assert all(not part.is_symlink() for part in (path,*path.parents))
 return hashlib.sha256(path.read_bytes()).hexdigest()
def bound(item):
 assert sha(item['path'])==item['sha256']
 return json.loads(Path(item['path']).read_bytes())
plan=bound(reference)
assert plan['call_cap']==114 and plan['job_cap']==38 and plan['checkpoint_cap']==19
expected={f'{sleep}_{condition}' for sleep in [0,*range(8,26)] for condition in ('LORA_ON','LORA_OFF')}
assert set(plan['slots'])==expected
jobs={}
for key in sorted(expected):
 terminal_path=root/'ledger'/(key+'.COMPLETE.json')
 if not terminal_path.exists():
  jobs[key]={'status':'MISSING_RAW_EXECUTION'}
  continue
 terminal=json.loads(terminal_path.read_bytes());reservation=bound(terminal['reservation'])
 complete_path=root/'attempts'/key/'sealed/COMPLETE.json'
 complete=json.loads(complete_path.read_bytes())
 assert complete['status']=='COMPLETE' and complete['calls']==3
 assert complete['execution_sha256']==reservation['execution']['sha256']
 execution=bound(reservation['execution'])
 assert execution['condition']==key.split('_',1)[1] and execution['milestone']==int(key.split('_',1)[0])
 raw={}
 for position in range(3):
  path=complete_path.parent/f'{position}.RAW.private.json'
  assert sha(path)==complete['receipts'][path.name]
  raw[str(position)]={'path':str(path),'sha256':complete['receipts'][path.name]}
 jobs[key]={'status':'COMPLETE','calls':3,'execution':reservation['execution'],
  'complete':{'path':str(complete_path),'sha256':sha(complete_path)},'raw':raw,
  'checkpoint_commit_sha256':complete['checkpoint_commit_sha256'],'completed_unix':complete['completed_unix']}
for sleep in [0,*range(8,26)]:
 on,off=jobs[f'{sleep}_LORA_ON'],jobs[f'{sleep}_LORA_OFF']
 if on['status']==off['status']=='COMPLETE':assert on['checkpoint_commit_sha256']==off['checkpoint_commit_sha256']
lexical=root/'private_appendices/lexical_full_generation1/APPENDIX.private.json'
print(json.dumps({'observed_unix':time.time(),'plan':reference,'source_plan':plan,'jobs':jobs,
 'complete_jobs':sum(job['status']=='COMPLETE' for job in jobs.values()),
 'lexical_appendix':{'path':str(lexical),'sha256':sha(lexical)} if lexical.exists() else None}))
'''.replace('ROOT_VALUE', repr(str(protocol.CAMPAIGN))).replace('PLAN_VALUE', repr(plan_ref))
    result = subprocess.run(['bash', base['transport']['path'], 'python3 -B -c ' + shlex.quote(script)],
        capture_output=True, timeout=45, check=True)
    return protocol.parse(result.stdout)


def public_readiness(report_refs, freeze_ref, checks):
    return dict(status='PRIVATE_RETROSPECTIVE_RETENTION_REPORT_READY_FOR_ROHIN',
        private_reports=report_refs, combined_annotation_freeze=freeze_ref, verification=checks,
        original_fixed_packets=60, valid_frozen_annotations=52, original_invalid_missing=8,
        new_provider_calls=0, new_model_calls=0, total_historical_provider_calls_charged=60,
        report_includes_all_18_selected_sleeps=True, partial_semantic_batch_not_full114_adjudication=True,
        parent_access=False, aggregate_success_claim_released=False, qualitative_results_withheld=True,
        observed_unix=time.time())


def render(report):
    primary = [row for row in report['rows'] if row['prompt'] == 1]
    counts = Counter(row['checkpoint_pair'] for row in primary)
    candidates = [row['sleep'] for row in primary if row['checkpoint_pair'] == 'ON_NOT_OFF']
    uncued = [row['sleep'] for row in primary if row['paired_uncued_interpretation_ready']]
    lines = ['# PRIVATE — R167 retrospective retention report for Rohin', '',
        '**Excluded from Main, active parents, repo_reader, and public feedback.**', '',
        '## Status and interpretation', '',
        'This is a completed deterministic settlement of the fixed semantic batch, not full-sweep semantic adjudication or proof that learning occurred.',
        '52 immutable valid annotations (51 continuation +1 original) are retained;8 originally invalid/uncertain annotations remain missing. No new provider/model calls or retries.',
        f"The retrospective raw sweep has {report['raw_execution']['complete_jobs']}/38 completed condition jobs; each complete job has3 calls. Raw execution completeness is not semantic coverage.",
        'Prompt1 is the primary exploratory ON-not-OFF comparison. Prompt2 is independent; prompt3 reports attention practices, not demonstrated capability.',
        'Primary bookkeeping across all18 selected sleeps: '+json.dumps(dict(counts),sort_keys=True)+'.',
        'Primary ON-not-OFF labels at selected sleeps: '+json.dumps(candidates)+'. This list is not an onset date or a causal learning claim.',
        'Subset with both frozen cueing labels UNCUED: '+json.dumps(uncued)+'. Cueing qualification is shown separately; it does not redefine the primary flag using baseline or prompt2.',
        'Initial controls, checkpoint OFF results, indeterminate labels and missing comparisons are explicit below. The report does not infer absent memory from an uninformative answer.', '',
        '## Provenance and custody', '',
        'Report source/tests, frozen validator, rubric, original settlement,51-annotation freeze and combined60-disposition freeze are hash-bound. All52 annotations passed the unchanged strict evidence-span validator before the private condition/checkpoint join.',
        'Original provider configuration is a historical hash/reference only: it was not loaded to launch a provider and no key was read. The continuation changed literal evidence rendering, not labels/rubric/validator; the original1 and continuation51 origins remain recorded.',
        'Exact mapping packets join to hashed completed raw-response receipts and matched checkpoint commit hashes. The private JSON includes all dispositions, annotation evidence spans, uncertainties, raw references and report checks.', '',
        '## Controls and all selected checkpoint comparisons', '',
        'A missing semantic annotation is never filled from the lexical appendix, an OFF baseline, a repeated response, or a later checkpoint. Initial responses are compared only where the prebuilt packet map provides that checkpoint-specific TRAIN fingerprint.',
        'Legend: ANNOTATED cells show identity / cueing / continuation and truncation; ORIGINAL_INVALID_MISSING preserves a consumed invalid case; NOT_IN_FIXED_SEMANTIC_BATCH has no authorized semantic judgment.', '']
    for prompt in (1, 2, 3):
        lines.extend([f'### Prompt{prompt}', '',
            '| Sleep | Checkpoint ON | Checkpoint OFF | Initial ON | Initial OFF | Checkpoint pair | Initial pair |',
            '|---|---|---|---|---|---|---|'])
        for row in report['rows']:
            if row['prompt'] != prompt:
                continue
            sleep = row['sleep']
            rendered = []
            for key in (f'{sleep}_LORA_ON', f'{sleep}_LORA_OFF', '0_LORA_ON', '0_LORA_OFF'):
                cell = row['cells'][key]
                if cell['status'] != 'ANNOTATED':
                    rendered.append(cell['status'])
                    continue
                annotation = cell['annotation']
                text = ' / '.join(annotation[field] for field in ('identity', 'cueing', 'continuation'))
                text += '; truncated=' + str(cell['truncated'])
                text += '; uncertainty_count=' + str(len(annotation['uncertain_features']))
                text += '; contradictions=' + str(len(annotation['contradicting_spans']))
                if prompt == 3:
                    text += '; attention=' + ','.join(f'{name}:{value}' for name, value in annotation['attention'].items())
                rendered.append(text)
            lines.append('| '+str(sleep)+' | '+' | '.join(rendered)+' | '+row['checkpoint_pair']+' | '+row['initial_pair']+' |')
        lines.append('')
    lines.extend(['## Limitations and permitted conclusions', '',
        '- The fixed60 packet inventory is a partial execution-progress snapshot, not all114 decoded answers or all216 checkpoint-specific answer/fingerprint comparison cells. All unadjudicated cells stay missing.',
        '- Eight invalid/uncertain original provider attempts are still charged. Missingness may be selective; denominators are explicit, and invalid cases are not successes or failures of retention.',
        '- Semantic evidence is restricted to frozen TRAIN fingerprint anchors/five-gram witnesses, not unrestricted full training history. Ambiguous/conflicting judgments and uncertain features are preserved.',
        '- A single stateless judge and deterministic decoder do not provide independent replication. Reused initial/OFF responses and correlated checkpoints must not be counted as independent trials.',
        '- Strict validation establishes allowed labels, structure and verbatim quoted substrings, not an independent finding that the semantic judgment or feature distinctiveness is correct. Frozen judgments are not upgraded by this report.',
        '- Retrospective object selection and repeated checkpoint comparisons preclude an onset claim or confirmatory significance claim. This report supplies no p-value, causal attribution, or population generalization.',
        '- Initial ON/OFF and checkpoint OFF positives, cueing, generic-category overlap, and possible model-prior knowledge limit a weight-specific recovery interpretation. Initial controls are reported, never silently added as a new primary gate.',
        '- Faithful recurrence can support identity without novelty or EOS. Coherent extension is a separate frozen judgment; arbitrary novelty is not continuation. Truncation limits continuation conclusions, not already visible evidence.',
        '- Attention fields describe an answer about what/how/how-much to examine, not demonstrated attention control, improved performance, consciousness, or broad learning gain.',
        '- English lexical noncoverage is not semantic absence, especially across languages. The unchanged lexical appendix is separate supporting evidence, not a replacement for missing semantic adjudication.',
        '- The retrospective lineage and schedule are distinct from the prospective fleet and the current parenting/targeted-replay intervention. No result here is fed back to active parents.',
        '-0700/0600 permissions do not isolate same-account agents; the explicit parent/repo_reader exclusion remains essential.', '',
        '## Authoritative artifacts', '',
        'Machine-readable report: REPORT.private.json. Full frozen packet dispositions and quotes: included in that private report. Exact rubric: RUBRIC.md. Combined freeze: COMBINED_ANNOTATION_FREEZE.json.',
        'Historical lexical appendix (not semantic substitution): '+json.dumps(report['raw_execution']['lexical_appendix'], sort_keys=True),
        'Report-generation provenance: '+json.dumps(report['provenance'], sort_keys=True), ''])
    return '\n'.join(lines).encode()


def main():
    global RUBRIC_TEXT
    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, exist_ok=False)
    protocol.write(PRIVATE / 'ONCE.json', dict(status='NO_CALLS_PRIVATE_REPORT_SETTLEMENT', started_unix=time.time(),
        source=protocol.ref(__file__), authority=protocol.ref(HERE / 'RETENTION_REPORT_SCOPE_20260917.md')))
    plan_path = HERE / 'semantic51_generation1/PLAN.json'
    plan = protocol.read(plan_path)
    base = protocol.bound(plan['original_plan'])
    for name, checksum in plan['source_pins'].items():
        protocol.require(protocol.sha(FROZEN_SOURCE / name) == checksum, 'actual_unchanged_frozen_semantic_source')
    protocol.require(protocol.sha(judge.__file__) == base['source_pins']['semantic_judge.py'], 'original_strict_validator_pin')
    protocol.require(protocol.sha(base['transport']['path']) == base['transport']['sha256'], 'existing_repo_wrapper_pin')
    protocol.require(Path(base['transport']['path']).resolve() == HERE.parents[2] / 'gpu/ovx_ssh.sh', 'wrapper_only_remote')
    inventory = protocol.bound(base['packet_inventory'])
    rubric = judge.remote_read(base, base['rubric'])
    protocol.require(base['rubric']['sha256'] == '7b630704b1be85abc56698b816e333f318a66004d419e8c6e474e67edf4b4165'
        and protocol.sha(HERE / 'SEMANTIC_ADJUDICATION_PROTOCOL.md') == base['rubric']['sha256'], 'frozen_rubric_and_no_parent_qualitative_release')
    RUBRIC_TEXT = rubric.decode()
    protocol.write(PRIVATE / 'RUBRIC.md', rubric)
    settlement = protocol.bound(plan['settlement'])
    protocol.require(settlement['status'] == 'STOPPED_ADMISSIONS_ALL_WORKERS_SETTLED' and settlement['invalid_remain_missing'] is True,
        'original_settlement_required')
    freeze_path = Path(plan['private_vm_root']) / 'ANNOTATION_FREEZE.json'
    freeze = protocol.read(freeze_path)
    protocol.require(freeze['status'] == 'ANNOTATIONS_FROZEN_NO_MAP_READ' and freeze['unblinded'] is False
        and freeze['plan'] == protocol.ref(plan_path) and freeze['original_settlement'] == plan['settlement'], 'existing51_freeze_required')
    public = protocol.read(Path(plan['private_vm_root']) / 'PUBLIC_METADATA.json')
    protocol.require(public['combined_calls_charged'] == 60 and public['complete_annotations'] == 51, 'existing_terminal_counts')
    protocol.require(judge.remote_read(base, public['annotation_freeze']) == freeze_path.read_bytes(), 'remote51_freeze_matches')
    records = collect(plan, base, inventory, freeze, settlement)
    cpu = protocol.read(HERE / 'retention_report_generation1/CPU_GATE.json')
    protocol.require(cpu['status'] == 'PASS' and cpu['report_source'] == protocol.ref(__file__), 'actual_report_CPU_gate')
    combined_ref = protocol.write(PRIVATE / 'COMBINED_ANNOTATION_FREEZE.json', dict(
        status='ALL60_DISPOSITIONS_FROZEN_BEFORE_PRIVATE_JOIN', valid_annotations=52, original_invalid_missing=8,
        calls_charged=60, new_calls=0, unblinded=False, frozen_unix=time.time(),
        original_settlement=plan['settlement'], continuation_freeze=protocol.ref(freeze_path),
        packet_inventory=base['packet_inventory'], rubric=base['rubric'],
        entries=[{key: value for key, value in record.items() if key not in ('annotation', 'annotation_envelope')}
            for record in records.values()], report_source=protocol.ref(__file__), cpu_gate=protocol.ref(HERE / 'retention_report_generation1/CPU_GATE.json')))
    publishing = dict(base, private_remote_root=str(REMOTE))
    published_freeze = judge.remote_upload(publishing, 'COMBINED_ANNOTATION_FREEZE.json', Path(combined_ref['path']).read_bytes())
    mapping = read_mapping_after_freeze(base, inventory, combined_ref)
    protocol.require(len(mapping['entries']) == 60 and {entry['opaque_id'] for entry in mapping['entries']} == set(records), 'exact60_private_mapping')
    protocol.write(PRIVATE / 'MAP.private.json', protocol.canonical(mapping))
    audit = audit_raw_receipts(base, mapping['plan'])
    protocol.write(PRIVATE / 'RAW_RECEIPT_AUDIT.private.json', audit)
    for entry in mapping['entries']:
        record = records[entry['opaque_id']]
        protocol.require(entry['packet'] == record['packet'], 'exact_packet_mapping_join')
        raw_job = audit['jobs'][entry['key']]
        protocol.require(raw_job['status'] == 'COMPLETE' and entry['complete'] == raw_job['complete']
            and entry['raw'] == raw_job['raw'][str(entry['position'])], 'exact_completed_checkpoint_response_join')
    rows = make_rows(mapping['entries'], records)
    provenance = dict(authority=protocol.ref(HERE / 'RETENTION_REPORT_SCOPE_20260917.md'),
        source=protocol.ref(__file__), validator=protocol.ref(judge.__file__), rubric=base['rubric'],
        cpu_gate=protocol.ref(HERE / 'retention_report_generation1/CPU_GATE.json'), combined_freeze=combined_ref,
        continuation_plan=protocol.ref(plan_path), original_plan=plan['original_plan'], mapping=inventory['mapping'],
        original_settlement=plan['settlement'], continuation_freeze=protocol.ref(freeze_path))
    report = dict(schema='R167_PRIVATE_RETROSPECTIVE_RETENTION_REPORT_V1',
        status='FROZEN52_VALID_EIGHT_MISSING_SETTLED', created_unix=time.time(), provenance=provenance,
        source_scope='RETROSPECTIVE_ONLY_NOT_CURRENT_FLEET_OR_PARENT_INTERVENTION',
        rubric_unchanged=True, annotation_labels_unchanged=True, new_provider_calls=0, new_model_calls=0,
        aggregate_success_claim_to_parents_permitted=False, rows=rows, packets=list(records.values()), raw_execution=audit,
        missing_original_invalid=8, valid_annotations=52, registered_packets=60, all_comparison_cells=216,
        semantic_unadjudicated_comparison_cells=156, annotation_freeze_precedes_mapping=True)
    protocol.write(PRIVATE / 'REPORT.private.json', report)
    protocol.write(PRIVATE / 'REPORT.private.md', render(report))
    artifacts = {}
    for name in ('REPORT.private.json', 'REPORT.private.md', 'RUBRIC.md', 'RAW_RECEIPT_AUDIT.private.json'):
        artifacts[name] = judge.remote_upload(publishing, name, (PRIVATE / name).read_bytes())
        protocol.require(judge.remote_read(base, artifacts[name]) == (PRIVATE / name).read_bytes(), 'published_exact_private_artifact')
    checks = dict(frozen_validator='PASS_52', historical_request_hashes='PASS_52',
        packet_condition_checkpoint_joins='PASS_60', raw_receipt_audit='PASS', matched_checkpoint_commit_hashes='PASS',
        all18_sleep_matrix='PASS', eight_original_invalid_preserved='PASS', no_new_calls='PASS',
        source_CPU_gate='PASS', private_remote_byte_verification='PASS', parent_result_release='NOT_PERMITTED')
    readiness = public_readiness(artifacts, published_freeze, checks)
    protocol.write(PRIVATE / 'READINESS.json', readiness)
    judge.remote_upload(publishing, 'READINESS.json', (PRIVATE / 'READINESS.json').read_bytes())
    protocol.write(HERE / 'retention_report_generation1/READINESS.json', readiness)
    protocol.write(PRIVATE / 'COMPLETE.json', dict(status='PRIVATE_REPORT_PUBLISHED_AND_VERIFIED', artifacts=artifacts,
        completed_unix=time.time(), new_provider_calls=0, no_retry=True))
    print(protocol.json.dumps(readiness, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if PRIVATE.exists() and not (PRIVATE / 'FAILURE.json').exists():
            protocol.write(PRIVATE / 'FAILURE.json', dict(status='REPORT_FAILURE_PRESERVED_NO_CALLS',
                error_type=type(error).__name__, error_class=str(error), observed_unix=time.time()))
        print(protocol.json.dumps(dict(status='PRIVATE_REPORT_NOT_READY_FAILURE_PRESERVED',
            error_type=type(error).__name__, private_evidence=str(PRIVATE), new_provider_calls=0)))
        raise SystemExit(1)
