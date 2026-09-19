"""Bounded read-only cache/custody review; never deletes or archives anything."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
NAMES = ['r213_math_a', 'r213_math_b_fork', 'r213_math_c',
    *[f'r213_r226_caption_{role}_fork' for role in
        ('observation', 'perspective', 'revision', 'selfderive', 'unparented')]]
CANDIDATES = [Path('/localhome/local-rohing') / suffix for suffix in (
    '.triton/cache', '.cache/flashinfer', '.cache/matplotlib')]
ARCHIVES = [ROOT / name for name in ('r233_retirement_20260918T1144Z',
    'r225_siege_retirement_20260918', 'r224_challenger_retirement_20260918')]


def main():
    directories = CANDIDATES + ARCHIVES
    needles = [str(path).encode() for path in directories]
    references = {str(path): [] for path in directories}
    unscanned = []
    scanned = 0
    original_plans = []
    for name in NAMES:
        active = json.loads((ROOT / name / 'ACTIVE_RUNTIME.json').read_bytes())
        control, source = Path(active['control']), Path(active['source'])
        guard = json.loads((control / 'GUARD.json').read_bytes())
        original_plans.append(dict(life=name,
            model_dir=json.loads((control / 'PLAN.json').read_bytes())['model_dir'],
            source_root=str(source), plan_sha256=guard['plan_sha256']))
        files = [control / 'PLAN.json', control / 'GUARD.json', ROOT / name / 'ACTIVE_RUNTIME.json']
        files += [source / relative for relative in guard['source_pins']]
        for path in files:
            if path.stat().st_size > 4 * 1024 * 1024:
                unscanned.append(str(path))
                continue
            raw = path.read_bytes()
            scanned += 1
            for directory, needle in zip(directories, needles):
                if needle in raw:
                    references[str(directory)].append(str(path))
    descriptors = {str(path): [] for path in directories}
    permission_denied = []
    processes = 0
    for entry in list(Path('/proc').iterdir()):
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            processes += 1
            for descriptor in (entry / 'fd').iterdir():
                target = os.readlink(descriptor)
                for directory in directories:
                    if target == str(directory) or target.startswith(str(directory) + '/'):
                        descriptors[str(directory)].append(dict(pid=int(entry.name), path=target))
        except (PermissionError, ProcessLookupError, FileNotFoundError):
            permission_denied.append(entry.name)
    rows = []
    for directory in directories:
        status = directory.lstat()
        allocated = int(subprocess.check_output(['du', '-sx', '-B1', str(directory)],
            text=True).split()[0])
        samples = []
        if directory in CANDIDATES:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and not path.is_symlink():
                    samples.append(dict(relative=str(path.relative_to(directory)),
                        bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        rows.append(dict(path=str(directory), realpath=str(directory.resolve()),
            uid=status.st_uid, directory_symlink=directory.is_symlink(), allocated_bytes=allocated,
            protected_experiment_archive=directory in ARCHIVES,
            classification=('PRESERVE_EXPERIMENT_STATE_ARCHIVE_REVIEW_ONLY' if directory in ARCHIVES
                else 'REGENERABLE_COMPILER_OR_FONT_CACHE_MAIN_REVIEW_REQUIRED'),
            scanned_pinned_source_control_literal_references=references[str(directory)],
            owner_process_open_descriptors=descriptors[str(directory)], files=samples,
            removal_authorized=False))
    print(json.dumps(dict(captured_unix=time.time(), read_only=True,
        pinned_source_control_files_scanned=scanned, unscanned_files=unscanned,
        owner_processes_inspected=processes, inaccessible_or_exited_processes=permission_denied,
        reference_scope='EXACT_LITERAL_PATHS_IN_EIGHT_ORIGINAL_CONTROLS_AND_PINNED_SOURCE_PLUS_OWNER_FDS',
        universal_absence_of_references_claimed=False, original_models_and_sources=original_plans,
        candidates=rows), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
