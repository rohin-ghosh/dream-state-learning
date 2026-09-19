"""Snapshot tested prefix operator dependencies locally; no execution or delivery."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from prepare_epoch2 import HERE, REPOSITORY, document, publish, require, seal_source


PAIR = 'research_loop/workers/post_recovery_pair_retention_receiver_20260919'
BOUNDARY = 'research_loop/workers/post_recovery_retention_boundary_20260918'


def package(output, receipt_path):
    output = Path(output).absolute()
    require(output.resolve() == output and output.is_relative_to(HERE) and not output.exists(),
        'new_own_prefix_operator_bundle_only')
    receipt_path = Path(receipt_path).absolute()
    require(receipt_path.is_relative_to(HERE), 'own_CPU_receipt_required')
    receipt = json.loads(receipt_path.read_bytes())
    require(receipt['passed'] and all(result['returncode'] == 0 for result in receipt['results']), 'passing_CPU_receipt')
    files = {PAIR + '/' + name: (HERE / name).read_bytes() for name in
        ('receiver.py', 'pair_operations.py', 'parent_dependency_bridge.py', 'integration.py', 'cpu_probe.py',
         'reserved_preflight.py', 'prefix_receiver.py', 'prefix_authority.py', 'cpu_probe_prefix.py',
         'source_checks.py', 'prefix_source_checks.py')}
    files.update({BOUNDARY + '/' + name: (REPOSITORY / BOUNDARY / name).read_bytes()
        for name in ('boundary.py', 'coordinator.py', 'operations.py')})
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    require(all(receipt['source_pins'].get(name) == expected for name, expected in hashes.items()),
        'same_tested_operator_bytes')
    for directory in ('research_loop', 'research_loop/workers', PAIR, BOUNDARY):
        files[directory + '/__init__.py'] = b''
    for name, content in files.items():
        compile(content, name, 'exec')
        publish(output / name, content)
    source = HERE / 'prepared_epoch4_v1'
    manifest = dict(schema='PAIR_PREFIX_OPERATOR_ONLY_BUNDLE_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        status='CPU_REVIEW_READY_NOT_ACTIVATED', source_files={name: hashlib.sha256(content).hexdigest()
            for name, content in files.items()}, CPU_receipt=dict(path=str(receipt_path), sha256=hashlib.sha256(
                receipt_path.read_bytes()).hexdigest()), source_summary=dict(path=str(source / 'SUMMARY.json'),
                sha256=hashlib.sha256((source / 'SUMMARY.json').read_bytes()).hexdigest()),
        namespace_ABI='prefix_proof={guard_path,guard_sha256}; prefix_admission={path,sha256,field_path}',
        native_signals=[], reservations=[], parent_actions=[], dispatches=[], actual_namespace_route_tested=False)
    document(output / 'MANIFEST.json', manifest)
    publish(output / 'BUILDER_PROVENANCE.md', ('[Builder] ' + manifest['observed_utc'] +
        ' Offline prefix operator package; exact source tests and CPU regression receipt pinned. '
        'Reuses unchanged <=30s reserved coordinator and original parent owner bridge. '
        'No original native, parent, guard, admission, source, namespace or service action.\n').encode())
    seal_source(output)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--test-receipt', required=True, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(package(arguments.output, arguments.test_receipt), sort_keys=True, indent=2))
