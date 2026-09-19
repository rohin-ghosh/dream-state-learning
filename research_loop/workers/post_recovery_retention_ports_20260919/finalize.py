"""Bind CPU-tested three-file overlays to immutable full-source pin sets."""

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

from port import port_text, reference_edits
from prepare import FILES, HERE, PHASE2, ROLLOUT, VARIANTS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def finalize(life):
    root = HERE / life
    inputs = json.loads((HERE / 'INPUT_RECEIPT.json').read_bytes())
    source = inputs['variants'][life]
    if sha(ROLLOUT / source['inventory_file']) != inputs['inventory_sha256'][source['inventory_file']]:
        raise ValueError('immutable_inventory_changed')
    tests = json.loads((root / 'TEST_RECEIPT.json').read_bytes())
    if tests['status'] != 'PASS' or not tests['imported_support_matches_source_pins']:
        raise ValueError('isolated_pinned_test_pass_required')
    if {name: outcome['tests'] for name, outcome in tests['tests'].items()} != dict(
            TESTS=17, LEGACY_TESTS=5, PRESERVATION_TESTS=5):
        raise ValueError('exact_17_plus_5_plus_5_required')
    for name, outcome in tests['tests'].items():
        if outcome['skipped'] or sha(root / (name + '.log')) != outcome['log_sha256']:
            raise ValueError('complete_unchanged_test_logs')
    before = json.loads((root / 'SOURCE_PINS.before.json').read_bytes())
    after, changes, patch = dict(before), {}, []
    edits = reference_edits()
    for relative in FILES:
        preimage, overlay = root / 'preimage' / relative, root / 'fork' / relative
        if sha(preimage) != before[relative] or sha(preimage) != source['before'][relative]:
            raise ValueError('captured_preimage_mismatch')
        if overlay.read_text() != port_text(preimage.read_text(), edits[relative]):
            raise ValueError('only_exact_scoped_phase2_delta')
        after[relative] = sha(overlay)
        changes[relative] = dict(before=before[relative], after=after[relative],
            preimage=str(preimage.relative_to(HERE)), overlay=str(overlay.relative_to(HERE)))
        patch.extend(difflib.unified_diff(preimage.read_text().splitlines(keepends=True),
            overlay.read_text().splitlines(keepends=True), fromfile='a/' + relative, tofile='b/' + relative))
    if (root / 'RETENTION.patch').read_text() != ''.join(patch):
        raise ValueError('minimal_patch_must_match_exact_overlay')
    if {name for name in before if before[name] != after[name]} != set(FILES):
        raise ValueError('exactly_three_source_pins_change')
    patch_checks = []
    for directory, reverse in (('preimage', False), ('fork', True)):
        command = ['git', 'apply', '--check'] + (['--reverse'] if reverse else [])
        command += ['--directory=' + str((root / directory).relative_to(HERE.parents[2])),
            str(root / 'RETENTION.patch')]
        checked = subprocess.run(command, cwd=HERE.parents[2], capture_output=True, text=True)
        patch_checks.append(dict(command=command, exit_code=checked.returncode,
            stdout=checked.stdout, stderr=checked.stderr))
        if checked.returncode:
            raise ValueError('patch_dry_run_failed: ' + checked.stderr)
    write(root / 'SOURCE_PINS.after.json', after)
    receipt = dict(status='LOCAL_PORT_CPU_READY_NOT_STAGED', variant=life, node=VARIANTS[life],
        prepared_utc=datetime.now(timezone.utc).isoformat(), source=source,
        source_files=len(before), unchanged_source_pins=len(before)-3, changed_source_files=changes,
        before_fullsourcepins_sha256=sha(root / 'SOURCE_PINS.before.json'),
        after_fullsourcepins_sha256=sha(root / 'SOURCE_PINS.after.json'),
        inventory_sha256=inputs['inventory_sha256'][source['inventory_file']],
        reference_patch_sha256=inputs['phase2_sha256']['REPAIR.patch'],
        port_patch_sha256=sha(root / 'RETENTION.patch'), patch_dry_runs=patch_checks,
        test_receipt=dict(path=str((root / 'TEST_RECEIPT.json').relative_to(HERE)), sha256=sha(root / 'TEST_RECEIPT.json')),
        test_counts={name: outcome['tests'] for name, outcome in tests['tests'].items()},
        test_scripts_sha256={name: sha(HERE / name) for name in ('prepare.py', 'port.py', 'validate_variant.py', 'finalize.py')},
        phase2_tests_sha256=sha(root / 'test_retention.py'),
        legacy_tests_sha256=json.loads((HERE / 'TEST_INPUTS.json').read_bytes()),
        receiving_required='Main must reverify full current closure and stage/adopt through its separately authorized receiving hook.',
        independent_of_live_source=True, receiving_hook_generated=False, applied_to_live=False,
        native_signals=[], remote_writes=[], dispatches=[], parent_deliveries=[], git_commits=[])
    write(root / 'READY.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=VARIANTS)
    selected = parser.parse_args().variant
    names = [selected] if selected else list(VARIANTS)
    receipts = {name: finalize(name) for name in names}
    if selected is None:
        write(HERE / 'MANIFEST.json', dict(status='FIVE_LOCAL_PORTS_CPU_READY_NOT_STAGED',
            variants={name: dict(ready_path=name + '/READY.json', ready_sha256=sha(HERE / name / 'READY.json'),
                changed_source_files=receipt['changed_source_files'], test_counts=receipt['test_counts'])
                for name, receipt in receipts.items()}, total_tests=135,
            input_receipt_sha256=sha(HERE / 'INPUT_RECEIPT.json'), no_live_changes=True))
    for name, receipt in receipts.items():
        print(name + ': READY; 17+5+5 PASS; exactly three pins changed; patch/reverse dry-runs PASS')


if __name__ == '__main__':
    main()
