"""CPU-only, hash-bound dry run and non-runnable source overlay. Never deploys."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[2]
PHASE2 = OWN.parent / 'post_recovery_pair_evidence_20260918/phase2'
BOUND = {
    'MANIFEST.json': '0eeb164c62825005b5416a97eef90af5474142fa5cc0202e5ccaee15800f4680',
    'PROVENANCE.json': '5435678914ecda03d2086ceec45c9be3907834ba35b0f16241c166c4b8bd766d',
    'REPAIR.patch': '7053d826efcfbc6ee6a8f44f36a8dbe8c179dd4d9ffb485a7ac548a075e876f1',
    'private/capture.json': 'b48a4ecd37bc8a04ad025f1fcb365d916cec780dfe3a23b961c67d5335a99163',
}
CHANGED = (
    'gpu/orch_r184_think_act_learn.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write_new(path, document):
    with path.open('x') as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write('\n')


def verify_phase2():
    for name, expected in BOUND.items():
        require(sha((PHASE2 / name).read_bytes()) == expected, 'phase2_binding:' + name)
    manifest = read(PHASE2 / 'MANIFEST.json')
    for name, expected in manifest.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'manifest_relative_path')
        require(sha((PHASE2 / name).read_bytes()) == expected, 'phase2_artifact_changed:' + name)
    return read(PHASE2 / 'PROVENANCE.json')


def validate_observation(observation, provenance, captured):
    require(observation['schema'] == 'RETENTION_SOURCE_OBSERVATION_V1', 'observation_schema')
    require(set(observation['targets']) == {'learner', 'frozen'}, 'both_pair_members_required')
    for label, original in provenance['sources'].items():
        current = observation['targets'][label]
        previous = captured[label]
        for key in ('pid', 'start_ticks'):
            require(current['native'][key] == original[key], 'phase2_process_identity:' + key)
        for key in ('cwd', 'argv'):
            require(current['native'][key] == previous['native'][key], 'phase2_process_binding:' + key)
        require(current['native']['process_state'] not in ('Z', 'X'), 'native_not_live')
        require(current['guard_sha256'] == original['guard_sha256'], 'phase2_guard_identity')
        require(current['guard_path'] == previous['native']['guard_path'], 'phase2_guard_path')
        require(current['root'] == str(Path(previous['native']['cwd']).parents[1] / 'raw'), 'same_life_root')
        require(current['source_pins'] == previous['guard']['source_pins'], 'whole_source_closure_changed')
        require(current['disk_hashes'] == current['source_pins'], 'disk_guard_mismatch')
        require(current['plan_sha256'] == previous['guard']['plan_sha256'], 'plan_changed')
        require(current['lease_sha256'] == previous['guard']['lease_sha256'], 'lease_changed')
        require(current['hard_end_unix'] == previous['guard']['hard_end_unix'], 'hard_end_changed')
        require(observation['observed_unix'] <= observation['finished_unix'] < current['hard_end_unix'],
            'observation_outside_current_guard_window')
        for relative, binding in original['files'].items():
            require(current['disk_hashes'][relative] == binding['running_disk_sha256']
                == binding['native_guard_source_pin'], 'phase2_source_baseline:' + relative)


def candidate_bytes(provenance):
    outputs = {}
    with tempfile.TemporaryDirectory(prefix='patch-check-', dir=OWN) as temporary:
        directory = Path(temporary)
        for relative in CHANGED:
            baseline = (PHASE2 / 'private/learner' / relative).read_bytes()
            for label in ('learner', 'frozen'):
                require(sha(baseline) == provenance['sources'][label]['files'][relative]['running_disk_sha256'],
                    'exact_patch_preimage:' + relative)
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(baseline)
        patch = PHASE2 / 'REPAIR.patch'
        headers = [line[6:] for line in patch.read_text().splitlines() if line.startswith('+++ b/')]
        require(sorted(headers) == sorted(CHANGED), 'three_file_patch_only')
        for options in (['--check'], []):
            subprocess.run(['git', 'apply', '--whitespace=error', *options, str(patch)],
                cwd=directory, check=True, capture_output=True)
        for relative in CHANGED:
            result = (directory / relative).read_bytes()
            for label in ('learner', 'frozen'):
                require(sha(result) == provenance['sources'][label]['files'][relative]['proposed_fork_sha256'],
                    'exact_patch_postimage:' + relative)
            outputs[relative] = result
    return outputs


def confined_new_directory(name):
    require(name not in ('', '.', '..') and Path(name).name == name, 'worker_direct_child_only')
    destination = OWN / name
    require(not destination.exists() and not destination.is_symlink(), 'never_overwrite_staging')
    return destination


def build_receipt(observation, provenance, outputs):
    require(set(outputs) == set(CHANGED), 'three_file_overlay_only')
    for relative, content in outputs.items():
        for label in ('learner', 'frozen'):
            require(sha(content) == provenance['sources'][label]['files'][relative]['proposed_fork_sha256'],
                'receipt_postimage_binding:' + relative)
    staged_pins = {}
    for label, current in observation['targets'].items():
        pins = dict(current['source_pins'])
        for relative, content in outputs.items():
            pins[relative] = sha(content)
        require({name for name in pins if pins[name] != current['source_pins'][name]} == set(CHANGED),
            'only_retention_three_file_delta')
        staged_pins[label] = pins
    return dict(schema='PARENT_RETENTION_ADOPTION_DRY_RUN_V1',
        prepared_utc=datetime.now(timezone.utc).isoformat(), phase2_bindings=BOUND,
        decision='NO_GO_LIVE_ADOPTION_NO_SUPPORTED_SOURCE_CHANGING_BOUNDARY_HOOK',
        artifact_type='NON_RUNNABLE_THREE_FILE_OVERLAY', deployable=False,
        phase2_sources_exactly_applicable=True, source_baselines=provenance['sources'],
        proposed_source_pins=staged_pins, preserved_files_per_target={label: len(pins) - len(CHANGED)
            for label, pins in staged_pins.items()}, changed_paths=list(CHANGED),
        observation=observation, native_signals=0, remote_writes=0, GPU_jobs=0,
        checkpoint_state_verified=False, boundary_reserved=False,
        observation_is_historical_not_current_authorization=True,
        next_action='Main may integrate allowlisted artifacts; no restart, hot patch, lease change, or dispatch.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('capture', 'dry-run', 'stage'))
    parser.add_argument('--observation', default='SOURCE_OBSERVATION.json')
    parser.add_argument('--output', default='stage')
    arguments = parser.parse_args()
    provenance = verify_phase2()
    captured = read(PHASE2 / 'private/capture.json')
    for label, previous in captured.items():
        require(previous['native']['guard_sha256'] == provenance['sources'][label]['guard_sha256'],
            'phase2_capture_identity')
        require(previous['guard']['source_pins'][CHANGED[0]] ==
            provenance['sources'][label]['files'][CHANGED[0]]['native_guard_source_pin'], 'capture_pins')
    require(Path(arguments.observation).name == arguments.observation, 'worker_observation_only')
    observation_path = OWN / arguments.observation
    require(not observation_path.is_symlink(), 'observation_symlink_refused')
    if arguments.action == 'capture':
        require(not observation_path.exists(), 'never_overwrite_observation')
        targets = {label: dict(previous['native'], source_pins=previous['guard']['source_pins'],
            root='/localhome/local-rohing/' + ('orch_r231_curriculum_birth_20260918' if label == 'learner'
            else 'orch_r232_curriculum_frozen_20260918') + '/raw') for label, previous in captured.items()}
        program = 'TARGETS = ' + repr(targets) + '\n' + (OWN / 'remote_metadata.py').read_text()
        received = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx4_ssh.sh'),
            "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -"],
            input=program, text=True, capture_output=True, check=True, timeout=90)
        observation = json.loads(received.stdout)
        validate_observation(observation, provenance, captured)
        write_new(observation_path, observation)
        print('Captured read-only metadata for both exact phase2 natives.')
        return
    observation = read(observation_path)
    validate_observation(observation, provenance, captured)
    outputs = candidate_bytes(provenance)
    receipt = build_receipt(observation, provenance, outputs)
    receipt['observation_file_sha256'] = sha(observation_path.read_bytes())
    if arguments.action == 'stage':
        destination = confined_new_directory(arguments.output)
        destination.mkdir()
        for relative, content in outputs.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        write_new(destination / 'STAGING_RECEIPT.json', receipt)
    print(json.dumps({key: receipt[key] for key in ('decision', 'deployable',
        'phase2_sources_exactly_applicable', 'preserved_files_per_target')}, indent=2))


if __name__ == '__main__':
    main()
