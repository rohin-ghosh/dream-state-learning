"""CPU-only, aggregate-only rederivation of completed R132 matched readouts."""

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import statistics
import sys
import time


SOURCE_PINS = {
    'organism_v6/orch_r107_capability.py': 'f8398dbf755c041508ee9268a46f7411c09146ccbe02b8bee254c027a85ebbc9',
    'organism_v6/experienced_event_reader_audit_lesson.py': '81e447afb444d4f929f0d8e0ae21c0fc21ad0f2ffda48f931b7d272606ecc745',
    'organism_v6/orch_code_bounded.py': 'b8cffeb779d394cc5f2f96a6d70cadeb8da3a3d2054ecaccb513239815bc5a2d',
}
SUITE = '32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c'
HELD = '4528215d24a80aff62e27b834e58305f492a2b0fa640bd0b89382e5266bd69e4'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def safe_child(root, relative):
    path = Path(root) / relative
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
        'checkpoint_relative_path_required')
    require(path.resolve().is_relative_to(Path(root).resolve()), 'checkpoint_path_escape')
    return path


def compare(left, right):
    require(set(left) == set(right), 'paired_case_set_mismatch')
    require(bool(left), 'empty_comparison')
    return dict(denominator=len(left), left_correct=sum(row['passed'] for row in left.values()),
        right_correct=sum(row['passed'] for row in right.values()),
        newly_passing=sum(not left[key]['passed'] and right[key]['passed'] for key in left),
        newly_failing=sum(left[key]['passed'] and not right[key]['passed'] for key in left),
        identical_raw_outputs=sum(left[key]['raw_hash'] == right[key]['raw_hash'] for key in left))


def shape(responses):
    lengths = [len(response['token_ids']) for response in responses]
    require(bool(lengths), 'empty_shape')
    return dict(responses=len(responses), generated_tokens_including_eos=sum(lengths),
        median_generated_tokens=statistics.median(lengths),
        single_line=sum('\n' not in response['raw'].strip() for response in responses),
        terminal=sum(response['terminal'] for response in responses),
        truncated=sum(response['truncated'] for response in responses),
        interpretation='DESCRIPTIVE_SHAPE_NOT_PERSISTENCE_OR_METACOGNITION')


def process_key(identity):
    require(set(('pid', 'start_ticks', 'boot_id')).issubset(identity), 'native_identity_required')
    return identity['boot_id'], identity['pid'], str(identity['start_ticks'])


class Audit:
    def __init__(self):
        self.files = {}

    def record(self, path):
        path = Path(path)
        actual = sha(path)
        require(str(path) not in self.files or self.files[str(path)] == actual, 'artifact_changed')
        self.files[str(path)] = actual
        return actual

    def read(self, path):
        self.record(path)
        return json.loads(Path(path).read_text())

    def verify_unchanged(self):
        for path, expected in self.files.items():
            require(sha(path) == expected, 'artifact_changed')


def load_policies(source, audit):
    source = Path(source).resolve()
    for relative, expected in SOURCE_PINS.items():
        require(audit.record(source / relative) == expected, 'frozen_scorer_source_mismatch')
    sys.path.insert(0, str(source))
    capability = importlib.import_module('organism_v6.orch_r107_capability')
    behavior = importlib.import_module('organism_v6.experienced_event_reader_audit_lesson')
    for module in (capability, behavior):
        require(Path(module.__file__).resolve().is_relative_to(source), 'wrong_loaded_scorer')
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).resolve().is_relative_to(source):
            audit.record(filename)
    require(capability.digest(capability.tasks()) == SUITE, 'fixed_suite_mismatch')
    return capability, behavior


def reduce_panel(root, arm, segment, condition, policies, audit):
    capability, behavior = policies
    stage = Path(root) / arm / f'segment{segment:03d}'
    binding = audit.read(stage / 'BINDING.json')
    require(binding['arm'] == arm and binding['segment'] == segment, 'stage_binding_mismatch')
    require(binding['campaign_sha256'] == audit.record(Path(root) / 'CAMPAIGN.json'), 'campaign_mismatch')
    require((stage / 'PAIRED_COMPLETE.json').is_file(), 'paired_readout_not_complete')
    audit.read(stage / 'PAIRED_COMPLETE.json')
    fit = stage / 'fit' / arm / stage.name
    trained = audit.read(fit / 'COMPLETE.json')
    require(trained['update'] == binding['end_update'], 'update_mismatch')
    checkpoint = Path(trained['checkpoint'])
    require(checkpoint == stage / 'fit' / arm / 'checkpoints' / f"{trained['update']:09d}",
        'checkpoint_path_mismatch')
    commit = audit.read(checkpoint / 'COMMIT.json')
    require(audit.record(checkpoint / 'COMMIT.json') == trained['commit_sha256'], 'commit_mismatch')
    require(commit['metadata']['update'] == trained['update'], 'commit_update_mismatch')
    require(commit['metadata']['adapter'] == trained['adapter'], 'commit_adapter_mismatch')
    require(trained['adapter']['base_sha256'] == BASE, 'base_mismatch')
    for relative, expected in commit['files'].items():
        require(audit.record(safe_child(checkpoint, relative)) == expected, 'checkpoint_file_mismatch')
    launch = audit.read(stage / f'readout_{condition}_LAUNCH.json')
    training_launch = audit.read(stage / 'train_None_LAUNCH.json')
    require(launch['binding_sha256'] == audit.record(stage / 'BINDING.json'), 'launch_binding_mismatch')
    require(launch['resume'] == str(checkpoint), 'readout_checkpoint_mismatch')
    identity = process_key(launch['identity'])
    require(identity != process_key(training_launch['identity']), 'readout_reused_training_process')
    require(audit.read(stage / f'readout_{condition}_EXIT.json')['returncode'] == 0, 'readout_exit_failure')
    output = fit / 'readout' / condition
    complete = audit.read(output / 'COMPLETE.json')
    require(complete['status'] == 'COMPLETE' and complete['condition'] == condition, 'incomplete_condition')
    require(complete['parent_access'] is False and complete['training_ingestion'] is False,
        'evaluation_visibility_mismatch')
    require(complete['base_and_adapter_unchanged'] is True, 'missing_readonly_postcheck')
    require(complete['checkpoint_state_sha256'] == trained['adapter']['state_sha256'], 'state_mismatch')
    require(complete['fixed32_suite_sha256'] == SUITE and complete['held_behavior_sha256'] == HELD,
        'panel_suite_mismatch')
    records = []
    cases = {'capability': {}, 'held': {}}
    for position, task in enumerate(capability.tasks()):
        record = audit.read(output / f'CAPABILITY_{position:03d}.json')
        reconstructed = capability.capture(task, condition, record['response'],
            checkpoint_sha256=trained['adapter']['state_sha256'], base_sha256=BASE,
            lora_enabled=condition == 'ON')
        require(record == reconstructed, 'capability_reconstruction_mismatch')
        records.append(record)
        cases['capability'][task['id']] = dict(passed=record['result']['passed'],
            raw_hash=digest(record['response']['raw']))
    require(complete['capability_calls'] == len(records) == 32, 'capability_call_count')
    require(len(list(output.glob('CAPABILITY_*.json'))) == 32, 'extra_capability_capture')
    held = audit.read(stage / 'input/prior/LEGACY_READOUT.json')['held']
    require(capability.digest(held) == HELD and held['split'] == 'HELD', 'held_bundle_mismatch')
    responses = [audit.read(path) for path in sorted(output.glob('BEHAVIOR_*.json'))]
    require(complete['behavior_calls'] == len(responses) == 16, 'held_call_count')
    cursor = iter(responses)

    def replay_capture(messages):
        response = next(cursor)
        require(response['messages'] == messages, 'held_prompt_mismatch')
        return response

    rederived = behavior.collect_cases(held, replay_capture, coached=False)
    require(all(row['error'] is None for row in rederived['captures']), 'held_reconstruction_error')
    require(rederived['rows'] == [] and rederived['fits'] == 0, 'held_generated_training_rows')
    require(rederived['summary'] == complete['behavior'], 'held_score_mismatch')
    for position, capture in enumerate(rederived['captures']):
        cases['held'][str(position)] = dict(passed=capture['success'],
            raw_hash=digest(capture['response']['raw']))
    families = {family: dict(passed=sum(row['result']['passed'] for row in records if row['family'] == family),
        denominator=sum(row['family'] == family for row in records)) for family in capability.FAMILIES}
    summary = dict(update=trained['update'], checkpoint=str(checkpoint),
        commit_sha256=trained['commit_sha256'], state_sha256=trained['adapter']['state_sha256'],
        complete_sha256=audit.record(output / 'COMPLETE.json'), native_identity=list(identity),
        capability=dict(passed=sum(row['result']['passed'] for row in records), denominator=32),
        families=families, held=rederived['summary'],
        code_categories=dict(Counter(row['result']['category'] for row in records if row['family'] == 'code')),
        capability_shape=shape([row['response'] for row in records]), held_shape=shape(responses),
        fresh_process=True, readonly_postcheck=True, original_records_reconstructed=True)
    return summary, cases


def run(root, source, before, after):
    require(0 <= before < after, 'ordered_distinct_segments_required')
    audit = Audit()
    policies = load_policies(source, audit)
    panels, cases = {}, {}
    for segment in (before, after):
        for arm in ('FULL', 'CONTROL'):
            for condition in ('ON', 'OFF'):
                key = f'{arm}_{segment:03d}_{condition}'
                panels[key], cases[key] = reduce_panel(root, arm, segment, condition, policies, audit)
        updates = {panels[f'{arm}_{segment:03d}_{condition}']['update']
            for arm in ('FULL', 'CONTROL') for condition in ('ON', 'OFF')}
        require(len(updates) == 1, 'unmatched_update_counts')
        identities = [tuple(panels[f'{arm}_{segment:03d}_{condition}']['native_identity'])
            for arm in ('FULL', 'CONTROL') for condition in ('ON', 'OFF')]
        require(len(set(identities)) == 4, 'readout_process_reused')
    pairs = [(f'{arm}_{before:03d}_{condition}', f'{arm}_{after:03d}_{condition}')
        for arm in ('FULL', 'CONTROL') for condition in ('ON', 'OFF')]
    pairs += [(f'FULL_{after:03d}_ON', f'CONTROL_{after:03d}_ON')]
    pairs += [(f'{arm}_{after:03d}_OFF', f'{arm}_{after:03d}_ON') for arm in ('FULL', 'CONTROL')]
    comparisons = [dict(left=left, right=right,
        panels={name: compare(cases[left][name], cases[right][name]) for name in ('capability', 'held')})
        for left, right in pairs]
    audit.verify_unchanged()
    return dict(schema='R138_R132_MATCHED_AUDIT_V1', observed_unix=time.time(),
        root=str(root), before_segment=before, after_segment=after, panels=panels, comparisons=comparisons,
        pinned_scorers=SOURCE_PINS, fixed_suite_sha256=SUITE, held_suite_sha256=HELD,
        artifact_count=len(audit.files), artifact_manifest_sha256=digest(audit.files),
        source_manifest=audit.files, artifacts_unchanged=True, new_model_calls=0, provider_calls=0,
        training_updates=0, raw_text_exported=False,
        retention_scope='PARENT_FREE_SOURCE_PRESENT_DISCRIMINATION_NOT_FILE_FREE_RETENTION')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--before', type=int, default=56)
    parser.add_argument('--after', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = run(arguments.root, arguments.source, arguments.before, arguments.after)
    with arguments.output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    result.pop('source_manifest')
    print(json.dumps(result, sort_keys=True))
