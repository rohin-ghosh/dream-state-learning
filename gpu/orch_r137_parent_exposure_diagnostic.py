"""One-shot, read-only diagnosis of the frozen node3 exposure monitor."""

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback


DEFAULT_CONFIG = Path('/data/home/rohing/courier/r133_programme_parents_20260916/R137_LATENCY_CUMULATIVE_MONITOR_CONFIG.json')
DEFAULT_BYTES = 128 * 1024 * 1024
MAX_BYTES = 512 * 1024 * 1024
ROOTS = {
    'SUPPORT_PERSISTENT_PREFETCH_POLL025': '/localhome/local-rohing/orch_r133_support_free_20260916_attempt1/run1',
    'BRAIN_PERSISTENT_POLL025': '/localhome/local-rohing/orch_r133_brain_free_20260916_attempt1/run1',
}
LOCAL_OVERLAYS = {
    'gpu/orch_r133_programme_parent.py': '931238db8938648c191f9e8dc48f1b4217f856a5b40c0caa0651cdc54122264a',
    'gpu/orch_route_parent_campaign_providers.py': '4d99658252310c7f57986750ff3002443d5c4038139f79b0381ff6eafbde837e',
    'tests/test_orch_r133_programme_parent.py': 'eecd2bc5f670b827d2857cccc057fd38db0ac2f04042d2a3af55e5686183dc97',
    'tests/test_orch_route_parent_campaign_providers.py': 'f62d1e716992b578dc9977a373b6f106d972bfad371951e86a426ca791062c9a',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)


def with_budget(script, max_bytes):
    if max_bytes is None:
        return script
    require(type(max_bytes) is int and DEFAULT_BYTES <= max_bytes <= MAX_BYTES, 'bounded_explicit_snapshot_budget')
    tree = ast.parse(script)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'snapshot']
    require(len(calls) == 1 and len(calls[0].args) == 1
            and [keyword.arg for keyword in calls[0].keywords] == ['publications'], 'exact_original_snapshot_call')
    calls[0].keywords.append(ast.keyword(arg='max_bytes', value=ast.Constant(max_bytes)))
    return ast.unparse(ast.fix_missing_locations(tree))


class PreparedLocally(Exception):
    pass


class WrapperFailure(RuntimeError):
    pass


class OneShotTransport:
    def __init__(self, output, root, remote_source, *, execute=False, clearance='', max_bytes=None, runner=None):
        self.output, self.root, self.remote_source = Path(output), root, remote_source
        self.execute, self.clearance, self.max_bytes = execute, clearance, max_bytes
        self.runner = subprocess.run if runner is None else runner
        self.calls = 0
        self.executions = 0

    def __call__(self, repository, config, script):
        require(self.calls == 0, 'one_wrapper_call_no_retry')
        self.calls += 1
        require(config['node'] == 'ovx2' and config['root'] == self.root
                and config['source_root'] == self.remote_source, 'only_selected_node3_lineage')
        if self.execute:
            require(bool(self.clearance.strip()), 'Main_admission_clearance_required_before_node3_probe')
        actual = with_budget(script, self.max_bytes)
        (self.output / 'ORIGINAL_REMOTE.py').write_bytes(script.encode())
        (self.output / 'PROPOSED_REMOTE.py').write_bytes(actual.encode())
        wrapper = Path(repository) / 'gpu/ovx2_ssh.sh'
        command = ['bash', str(wrapper), 'PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH='
                   + shlex.quote(self.remote_source) + ' python3 -c ' + shlex.quote(actual)]
        write(self.output / 'COMMAND.json', dict(command=command, wrapper_sha256=sha(wrapper),
            original_script_sha256=sha(self.output / 'ORIGINAL_REMOTE.py'),
            actual_script_sha256=sha(self.output / 'PROPOSED_REMOTE.py'),
            max_bytes=self.max_bytes if self.max_bytes is not None else DEFAULT_BYTES,
            max_records=10000, max_record_bytes=16 * 1024 * 1024, timeout_seconds=45,
            admission_clearance=self.clearance, executed=self.execute))
        if not self.execute:
            raise PreparedLocally('local_publications_validated_no_remote_call')
        started = time.time()
        try:
            self.executions += 1
            result = self.runner(command, capture_output=True, timeout=45)
        except subprocess.TimeoutExpired as error:
            self._capture(error.stdout or b'', error.stderr or b'', dict(
                status='WRAPPER_TIMEOUT', started_unix=started, finished_unix=time.time(), timeout_seconds=45))
            raise WrapperFailure('wrapper_timeout_full_partial_streams_preserved') from error
        self._capture(result.stdout, result.stderr, dict(status='WRAPPER_RETURNED', returncode=result.returncode,
                      started_unix=started, finished_unix=time.time()))
        if result.returncode != 0:
            raise WrapperFailure('wrapper_nonzero:' + str(result.returncode) + ':see_STDERR.bin')
        return json.loads(result.stdout)

    def _capture(self, stdout, stderr, metadata):
        for name, raw in [('STDOUT.bin', stdout), ('STDERR.bin', stderr)]:
            with (self.output / name).open('xb') as stream:
                stream.write(raw)
        write(self.output / 'TRANSPORT.json', dict(metadata, stdout_sha256=sha(self.output / 'STDOUT.bin'),
              stderr_sha256=sha(self.output / 'STDERR.bin'), stdout_bytes=len(stdout), stderr_bytes=len(stderr)))


def historical_failures(directory, output):
    histories = {label: [] for label in ROOTS}
    paths = sorted(Path(directory).glob('AUDIT_*.json'))
    require(len(paths) <= 10000, 'bounded_local_audit_inventory')
    for path in paths:
        raw = path.read_bytes()
        audit = json.loads(raw)
        for row in audit['rows']:
            label = next((name for name in ROOTS if ('SUPPORT' in name) == ('SUPPORT' in row['branch'].upper())), None)
            require(label is not None and any(name in row['branch'].upper() for name in ('SUPPORT', 'BRAIN')), 'known_historical_branch')
            histories[label].append((path, raw, row))
    result = {}
    for label, history in histories.items():
        success = [item for item in history if 'error' not in item[2]]
        errors = [item for item in history if 'error' in item[2]]
        selected = {}
        for name, items in [('last_success', success[-1:]), ('first_error', errors[:1])]:
            if not items:
                continue
            path, raw, row = items[0]
            copy = Path(output) / (label + '_' + name + '.json')
            with copy.open('xb') as stream:
                stream.write(raw)
            used = row.get('snapshot_state', {}).get('journal_bytes_read')
            selected[name] = dict(path=str(path), copied_path=str(copy), sha256=sha(copy),
                row_observed_utc=datetime.fromtimestamp(row['observed_unix'], timezone.utc).isoformat(),
                error=row.get('error'), coverage=row.get('coverage'),
                journal_bytes_read=used, remaining_default_bytes=DEFAULT_BYTES - used if used is not None else None,
                record_count=row.get('snapshot_state', {}).get('record_count'))
        result[label] = dict(selected, successes=len(success), errors=len(errors))
    return dict(audit_count=len(paths), lineages=result, production_cause_confirmed=False,
                hypothesis='cumulative_snapshot_byte_budget_exhaustion_hidden_by_wrapper', remote_calls=0)


def compare_historical(previous, current, baseline):
    basis = 'verified_parent_REQUEST_exposure_not_registration'
    require(type(baseline) is int and baseline >= 0, 'original_nonnegative_baseline')
    mappings = []
    for row in (previous, current):
        state = row['snapshot_state']
        require(state['coverage_basis'] == basis and row['coverage']['coverage_basis'] == basis, 'strict_exposure_comparison')
        indices = [event['record_index'] for event in state['parent_consumptions']]
        boundaries = {(item['record_index'], item['record_sha256'], item['next_request_index']):
            any(item['record_index'] < index < item['next_request_index'] for index in indices)
            for item in state['boundaries'] if item['response_count'] > baseline and item['next_request_index'] is not None}
        covered = sum(boundaries.values())
        require(row['coverage'] == dict(closed_boundaries=len(boundaries), covered_boundaries=covered,
                missing_boundaries=len(boundaries) - covered, coverage_basis=basis), 'same_original_baseline_and_counts')
        mappings.append(boundaries)
    old, new = mappings
    require(all(key in new and new[key] == value for key, value in old.items()), 'historical_closed_boundary_credit_unchanged')
    old_publications = {json.dumps(item, sort_keys=True) for item in previous['publications']}
    new_publications = {json.dumps(item, sort_keys=True) for item in current['publications']}
    require(old_publications <= new_publications, 'original_publication_union_preserved')
    return dict(status='HISTORICAL_COMPARISON_PASS', baseline=baseline,
        historical_closed_boundaries=len(old), historical_missing_boundaries=[list(key) for key, value in old.items() if not value],
        new_closed_boundaries=len(new) - len(old), new_covered_boundaries=sum(new.values()) - sum(old.values()),
        old_coverage=previous['coverage'], current_coverage=current['coverage'],
        every_historical_boundary_credit_preserved=True, publication_union_preserved=True)


def verify_local_source(source, manifest):
    differences = {}
    for relative, digest in manifest['files'].items():
        actual = sha(source / relative)
        require(actual == LOCAL_OVERLAYS.get(relative, digest), 'original_local_snapshot_bytes:' + relative)
        if actual != digest:
            differences[relative] = dict(remote_manifest_sha256=digest, observed_local_sha256=actual)
    return dict(local_source=str(source), local_remote_manifest_differences=differences,
                all_other_manifest_files_exact=True, local_snapshot_is_identical_to_remote_manifest=not differences)


def frozen_runtime(config, output):
    require('gpu' not in sys.modules and 'organism_v6' not in sys.modules, 'run_standalone_fresh_interpreter')
    source = Path(config['monitor_source']).resolve()
    receipt = source / 'CPU_AND_SOURCE.json'
    require(sha(receipt) == config['remote_source_receipt_sha256'], 'exact_frozen_CPU_source_manifest')
    manifest = json.loads(receipt.read_text())
    require(manifest['passed'] is True, 'original_CPU_gate_passed')
    provenance = verify_local_source(source, manifest)
    write(Path(output) / 'LOCAL_SOURCE_PROVENANCE.json', provenance)
    require(sha(config['helper_path']) == config['helper_sha256'], 'exact_frozen_cumulative_helper')
    sys.path.insert(0, str(source))
    monitor = importlib.import_module('gpu.orch_r137_parent_monitor')
    require(Path(monitor.__file__).resolve() == source / 'gpu/orch_r137_parent_monitor.py', 'frozen_monitor_import')
    spec = importlib.util.spec_from_file_location('pinned_r137_cumulative', config['helper_path'])
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(not any(name in sys.modules for name in ('torch', 'transformers', 'peft')), 'no_model_runtime_import')
    return helper, monitor


def run(config_path, output, label, *, execute=False, clearance='', max_bytes=None):
    require(label in ROOTS, 'explicit_healthy_monitored_lineage')
    require(not execute or bool(clearance.strip()), 'Main_admission_clearance_required_before_node3_probe')
    output = Path(output)
    output.mkdir(exist_ok=False)
    transport, monitor, original = None, None, None
    result = dict(label=label, config_path=str(config_path),
                  persistent_monitor_changed=False, children_parents_changed=False)
    try:
        config = json.loads(Path(config_path).read_text())
        require(config['schema'] == 'R137_PARENT_LATENCY_MONITOR_V1', 'exact_monitor_configuration')
        history = historical_failures(Path(config_path).parent / 'R137_LATENCY_CUMULATIVE_MONITOR', output)
        write(output / 'HISTORICAL_FAILURES.json', history)
        helper, monitor = frozen_runtime(config, output)
        items = [item for item in config['items'] if item['label'] == label]
        require(len(items) == 1, 'single_configured_lineage')
        transport = OneShotTransport(output, ROOTS[label], config['remote_source'], execute=execute,
                                     clearance=clearance, max_bytes=max_bytes)
        original = monitor.remote
        monitor.remote = transport
        result.update(config_sha256=sha(config_path), helper_sha256=sha(config['helper_path']),
                      frozen_manifest_sha256=config['remote_source_receipt_sha256'])
        row = helper.cumulative_sample(items[0], config)
        require(row['coverage']['coverage_basis'] == 'verified_parent_REQUEST_exposure_not_registration', 'strict_exposure_only')
        write(output / 'MEASUREMENT.json', row)
        result.update(status='VERIFIED_ONE_SHOT_MEASUREMENT', coverage=row['coverage'], measurement_sha256=sha(output / 'MEASUREMENT.json'))
    except PreparedLocally:
        result.update(status='LOCAL_PREPARED_REMOTE_NOT_RUN', measurement_available=False)
    except Exception as error:
        (output / 'LOCAL_TRACEBACK.txt').write_text(traceback.format_exc())
        result.update(status='DIAGNOSTIC_FAILED_NO_MEASUREMENT', error_type=type(error).__name__,
                      error_message=str(error), traceback_sha256=sha(output / 'LOCAL_TRACEBACK.txt'), measurement_available=False)
    finally:
        if original is not None:
            monitor.remote = original
    result.update(observed_utc=datetime.now(timezone.utc).isoformat(), remote_calls=transport.executions if transport else 0)
    write(output / 'OBSERVATION.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', choices=sorted(ROOTS), required=True)
    parser.add_argument('--execute-once', action='store_true')
    parser.add_argument('--admission-clearance', default='')
    parser.add_argument('--max-bytes', type=int)
    arguments = parser.parse_args()
    result = run(arguments.config, arguments.output, arguments.label, execute=arguments.execute_once,
                 clearance=arguments.admission_clearance, max_bytes=arguments.max_bytes)
    print(json.dumps(result, sort_keys=True))
    sys.exit(1 if result['status'] == 'DIAGNOSTIC_FAILED_NO_MEASUREMENT' else 0)
