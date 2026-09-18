"""Package the exact tested R209 delta without changing frozen releases or recipes."""

from copy import deepcopy
import datetime
import difflib
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parent
REPOSITORY = Path.cwd()
BASE = REPOSITORY / 'research_loop/workers/rohin201_c2_clones_20260917/r206_ready'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert not (ROOT / 'READY.json').exists(), 'published_bundle_is_immutable'
    base_bytes = (BASE / 'READY.json').read_bytes()
    base = json.loads(base_bytes)
    archive_bytes = (BASE / 'runtime_overlay.tar.gz').read_bytes()
    assert digest(archive_bytes) == base['archive_sha256'] == (
        'ab7c3ada0780d8414aba30e59721df1bb8c51fdee747105359682bae3c144f84')
    tests = json.loads((ROOT / 'SHARED_TEST_RECEIPT.json').read_bytes())
    deployed = json.loads((ROOT.parent / 'R206_PROSE_REPAIR/READY.json').read_bytes())
    assert tests['passed'] and tests['tests_run'] == 62 and tests['skipped'] == 0
    original = {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:gz') as archive:
        for name, expected in base['files'].items():
            member = archive.getmember(name)
            assert member.isfile() and not Path(name).is_absolute() and '..' not in Path(name).parts
            original[name] = archive.extractfile(member).read()
            assert digest(original[name]) == expected
    assert len(original) == 42
    files = dict(original)
    for name, expected in deployed['files'].items():
        files[name] = (REPOSITORY / name).read_bytes()
        assert digest(files[name]) == expected == tests['source_files'][name]
    changed = [name for name in files if files[name] != original[name]]
    assert set(changed) == set(deployed['files']) and len(changed) == 2
    patches = {}
    for patch_name, baselines, names in (
        ('runtime_delta.patch', original, sorted(changed)),
        ('regression_tests.patch', {name: (ROOT / 'build_inputs' / name).read_bytes()
            for name in tests['test_files']}, sorted(tests['test_files'])),
    ):
        parts = []
        for name in names:
            current = (REPOSITORY / name).read_bytes()
            if name in tests['test_files']:
                assert digest(current) == tests['test_files'][name]
            parts.extend(difflib.unified_diff(baselines[name].decode().splitlines(keepends=True),
                current.decode().splitlines(keepends=True), fromfile='a/' + name, tofile='b/' + name))
        raw = ''.join(parts).encode()
        (ROOT / patch_name).write_bytes(raw)
        patches[patch_name] = digest(raw)
        with tempfile.TemporaryDirectory(prefix='r209-patch-check-') as directory:
            for name in names:
                target = Path(directory) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(baselines[name])
            subprocess.run(['git', 'apply', '--check', str(ROOT / patch_name)], cwd=directory, check=True)
    archive_path = ROOT / 'runtime_overlay.tar.gz'
    with archive_path.open('xb') as output:
        with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                for name in sorted(files):
                    member = tarfile.TarInfo(name)
                    member.mode = 0o644
                    member.size = len(files[name])
                    archive.addfile(member, io.BytesIO(files[name]))
    with tarfile.open(archive_path) as archive:
        assert set(archive.getnames()) == set(files)
        assert all(archive.extractfile(name).read() == raw for name, raw in files.items())
    native_options = {name: base['required_native_options'][name]
        for name in ('code_target_filter', 'learn_review_filter')}
    driver_options = {name: base['required_driver_options'][name] for name in (
        'console_reply_policy', 'pinned_messages_policy', 'learn_review_filter', 'stage_boundary_policy')}
    driver_options['prose_target_filter'] = deployed['prose_target_filter']
    cases = 0
    for presentations in (4, 16, 32):
        for multiplier in (.3, 1, 3):
            plan = dict(new_presentations=presentations, rehearsal_presentations=0, anchor_lambda=.25,
                plasticity=dict(schema='R186_PLASTICITY_V1', learning_rate_multiplier=multiplier),
                optimizer_param_groups=[dict(lr=3e-5 * multiplier)],
                think_act_learn=dict(trial_id='existing-arm', think_segments=2))
            preserved = deepcopy(plan)
            plan.update(native_options)
            plan['think_act_learn'].update(driver_options)
            assert all(plan[name] == preserved[name] for name in (
                'new_presentations', 'rehearsal_presentations', 'anchor_lambda', 'plasticity',
                'optimizer_param_groups'))
            assert all(plan['think_act_learn'][name] == value
                for name, value in preserved['think_act_learn'].items())
            cases += 1
    assert (BASE / 'READY.json').read_bytes() == base_bytes
    assert (BASE / 'runtime_overlay.tar.gz').read_bytes() == archive_bytes
    ready = dict(schema='R209_TRANSFERABLE_SOURCE_OVERLAY_V1', status='CPU_TESTED',
        created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        archive='runtime_overlay.tar.gz', archive_sha256=digest(archive_path.read_bytes()),
        base_ready_path=str(BASE.relative_to(REPOSITORY) / 'READY.json'),
        base_ready_sha256=digest(base_bytes), base_archive_sha256=base['archive_sha256'],
        files={name: digest(raw) for name, raw in files.items()}, changed_files=deployed['files'],
        unchanged_base_files=40, patch_sha256=patches, cpu_validation=tests,
        test_receipt_sha256=digest((ROOT / 'SHARED_TEST_RECEIPT.json').read_bytes()),
        required_native_options=native_options, required_driver_options=driver_options,
        required_existing_native_options=dict(rehearsal_presentations=0),
        preserve_existing_plan_and_checkpoint=True,
        recipe_fields_not_overridden=['new_presentations', 'plasticity', 'optimizer_param_groups',
            'learning_rate', 'rehearsal_presentations', 'anchor_lambda'],
        recipe_preservation_packaging_cases=cases,
        original_c2_live=dict(loaded_record_index=6544, loaded_at_utc='2026-09-18T04:43:24.939955+00:00',
            first_live_filter_record_index=6576, first_live_exclusion_count=0,
            prior_corrupt_console_updates_preserved=16, prior_updates_undone=False),
        fleet_deployments_performed_by_this_transfer=0, english_child_new_targets_only=True,
        raw_modified=False, targets_normalized=False,
        recipe_warning='Merge feature options into the existing plan; never import R206 new_presentations=16.')
    (ROOT / 'READY.json').write_text(json.dumps(ready, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(archive_sha256=ready['archive_sha256'], files=len(files), changed_files=changed,
        tests=tests['tests_run'], recipe_preservation_cases=cases, frozen_base_unchanged=True)))


if __name__ == '__main__':
    main()
