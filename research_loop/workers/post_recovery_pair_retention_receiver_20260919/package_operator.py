"""Package only operator code locally; never import or execute receiving operations."""

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
BOUNDARY = 'research_loop/workers/post_recovery_retention_boundary_20260918'
PAIR = 'research_loop/workers/post_recovery_pair_retention_receiver_20260919'


def package(output, *, test_receipt):
    output = Path(output).absolute()
    if output.resolve() != output or not output.is_relative_to(HERE) or output.exists():
        raise ValueError('new_local_operator_bundle_only')
    files = {f'{PAIR}/{name}': (HERE / name).read_bytes() for name in
        ('receiver.py', 'pair_operations.py', 'parent_dependency_bridge.py', 'integration.py', 'cpu_probe.py',
            'reserved_preflight.py')}
    files.update({f'{BOUNDARY}/{name}': (REPOSITORY / BOUNDARY / name).read_bytes()
        for name in ('boundary.py', 'coordinator.py', 'operations.py')})
    test_receipt = Path(test_receipt).resolve()
    if not test_receipt.is_relative_to(HERE):
        raise ValueError('own_worker_test_receipt_required')
    test_bytes = test_receipt.read_bytes()
    evidence = json.loads(test_bytes)
    if not evidence['results'] or not all(entry['returncode'] == 0 for entry in evidence['results']):
        raise ValueError('passing_operator_test_receipt_required')
    if not all(evidence['source_pins'].get(name) == hashlib.sha256(content).hexdigest()
            for name, content in files.items()):
        raise ValueError('operator_bytes_must_match_tested_bytes')
    for directory in ('research_loop', 'research_loop/workers', PAIR, BOUNDARY):
        files[directory + '/__init__.py'] = b''
    output.mkdir()
    for name, content in files.items():
        ast.parse(content, filename=name)
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(content)
    manifest = dict(schema='PAIR_OPERATOR_ONLY_BUNDLE_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        status='REVIEW_READY_NOT_ACTIVATED', source_files={name: hashlib.sha256(content).hexdigest()
            for name, content in sorted(files.items())}, receiving_source_modified=False,
        native_signals=[], reservations=[], parent_actions=[], transport_executed=False,
        test_receipt_path=str(test_receipt), test_receipt_sha256=hashlib.sha256(test_bytes).hexdigest(),
        remaining=['real_reserved_total_cost_bound_and_exact_strategy_approval', 'real_Kuhn_fence_dependency',
            'reviewed_authenticated_CPU_owner_transport', 'real_guard_and_confinement_admission',
            'actual_LOADED_before_separate_owner_rebind'])
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    (output / 'BUILDER_PROVENANCE.md').write_text('[Builder] ' + manifest['observed_utc'] +
        ' Operator-only exact dependency/dispatch integration; optional reserved preflight has distinct approval. '
        'CPU tests and exact tested operator bytes are bound in the manifest test receipt. '
        'No receiving source or history edit, remote probe, live fence, signal, reservation, handoff, '
        'service management or dispatch. Historical cutoff proof is not current boundary authority.\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--test-receipt', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(package(arguments.output, test_receipt=arguments.test_receipt), sort_keys=True, indent=2))
