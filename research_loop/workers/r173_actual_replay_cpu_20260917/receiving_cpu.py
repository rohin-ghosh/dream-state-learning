"""One create-only receiving CPU experiment, never a staging/admission receipt."""

import ast
import base64
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.abc
import importlib.machinery
import io
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import tempfile
import traceback
import unittest


SCRATCH = '/localhome/local-rohing/orch_r173_actual_replay_cpu_20260917_attempt1'
OLD_SOURCE = '/localhome/local-rohing/orch_r144_node3_targets_20260916t1515z_2/physical1/source'
OLD_GUARD = '/localhome/local-rohing/orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json'
GUARD_SHA256 = '8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d'
NATIVE_PATH = 'gpu/orch_r125_continual_native.py'
NATIVE_SHA256 = 'cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48'
ORIGINAL_GUARD_SHA256 = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'
PLAIN_SHA256 = 'b3859e4a45d53fc67c51add5dad8431985ca0adda901389e0206819a56245d92'
HELPERS = {
    'gpu/orch_r168_targeted_replay.py': '4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3',
    'gpu/orch_r168_targeted_replay_native.py': '12e512ba08be73a1881bc75c52f60458163aa929c5b0bc682814c9c0bf93e304',
    'gpu/orch_r168_targeted_replay_driver.py': '43295e6b98ebb10c7e99247e8b26720948b25556d5da13e34759c1f2d0088351',
}
TESTS = {
    'tests/test_orch_r168_targeted_replay_native.py': '787fa8387a23792f57951289f3571211fbe439b0b69c5eed768ecd2845d552d8',
    'tests/test_orch_r168_targeted_replay.py': '07d105f3bfd8ea366edeb55746e2856ee0d04004b6ffb71fbdb6320685f118e3',
    'tests/test_orch_r168_targeted_replay_driver.py': 'afabb2774f8fb1afcb6c674799a693b176fc303d3769b11dd11e1f94f77c1b4e',
    'tests/test_orch_r168_targeted_replay_driver_review.py': '96f5cd24f6600317fcb4b90996b7a34439a49ab3721f6105b22cd7791a72606c',
}
FIXTURE = 'research_loop/workers/r168_replay_candidates_20260917/ROW118_TRAIN_FIXTURE.json'
FIXTURE_SHA256 = '1b046cc2fff07b793386d51d90ede5e4e17b0c630956c1cd5e6cee2418390c28'
DEPENDENCIES = ('gpu.orch_r108_guided_native', 'gpu.orch_r144_sleep_targets',
                'organism_v6.orch_r125_plain_context')
SUFFIX_FILES = {'gpu/orch_r145_suffix_boundary.py', 'gpu/orch_r145_suffix_loss.py'}
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_OPERATIONAL_BYTES = 64 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(document):
    return json.dumps(document, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def relative_python(name):
    path = Path(name)
    require(isinstance(name, str) and not path.is_absolute() and '..' not in path.parts
            and str(path) == name and path.suffix == '.py', 'canonical_relative_python_path')
    return path


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def validate_pins(pins):
    require(isinstance(pins, dict) and pins, 'nonempty_guard_source_pins')
    require(not set(pins).intersection(HELPERS), 'old_source_has_no_replay_helpers')
    require(not set(pins).intersection(SUFFIX_FILES), 'no_suffix_optimization_copy')
    for name, checksum in pins.items():
        relative_python(name)
        require(valid_hash(checksum), 'known_full_source_hash')
    require(pins.get(NATIVE_PATH) == NATIVE_SHA256, 'exact_cdb_native')
    require(pins.get('gpu/orch_r125_continual_guard.py') == ORIGINAL_GUARD_SHA256,
            'exact_original_guard_code')
    require(pins.get('organism_v6/orch_r125_plain_context.py') == PLAIN_SHA256,
            'actual_old_plain_context_not_workspace_version')


class BoundReader:
    def __init__(self):
        self.bytes_read = 0
        self.references = []

    def read(self, path, checksum):
        path = Path(path)
        require(valid_hash(checksum), 'known_full_read_hash')
        require(path.is_absolute() and path == path.resolve(), 'no_symlink_or_relative_source')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_FILE_BYTES,
                    'bounded_regular_source')
            require(self.bytes_read + before.st_size <= MAX_OPERATIONAL_BYTES,
                    'bounded_total_operational_read')
            raw = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
        self.bytes_read += len(raw)
        require(len(raw) == before.st_size and all(getattr(before, field) == getattr(after, field)
                for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                'source_changed_during_read')
        require(sha(raw) == checksum, 'source_hash_mismatch:' + str(path))
        self.references.append(dict(path=str(path), sha256=checksum, bytes=len(raw)))
        return raw


def write_once(path, raw):
    if not path.parent.is_dir():
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def unpack_payload(payload):
    expected = dict(HELPERS, **TESTS, **{FIXTURE: FIXTURE_SHA256})
    require(set(payload['files']) == set(expected), 'exact_payload_whitelist')
    result = {}
    for name, checksum in expected.items():
        raw = base64.b64decode(payload['files'][name], validate=True)
        require(len(raw) <= MAX_FILE_BYTES and sha(raw) == checksum, 'payload_pin:' + name)
        result[name] = raw
    return result


def adapt_test(name, raw, source, fixtures):
    text = raw.decode()
    replacements = []
    if name == 'tests/test_orch_r168_targeted_replay_native.py':
        replacements = [
            ("Path(__file__).resolve().parents[1] / 'research_loop/workers/r168_replay_candidates_20260917'",
             'Path(' + repr(str(fixtures)) + ')', 1),
            ("FIXTURES / 'NATIVE_cdb542.py'", 'Path(' + repr(str(source / NATIVE_PATH)) + ')', 2),
        ]
    elif name == 'tests/test_orch_r168_targeted_replay_driver.py':
        replacements = [("Path(__file__).resolve().parents[1] / 'gpu/orch_r125_continual_guard.py'",
                         'Path(' + repr(str(source / 'gpu/orch_r125_continual_guard.py')) + ')', 1)]
    for original, replacement, count in replacements:
        require(text.count(original) == count, 'exact_path_adaptation_count:' + name)
        text = text.replace(original, replacement)
    adapted = text.encode()
    compile(adapted, name, 'exec')
    original_tests = [node.name for node in ast.walk(ast.parse(raw))
                      if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
    adapted_tests = [node.name for node in ast.walk(ast.parse(adapted))
                     if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
    require(original_tests == adapted_tests, 'all_original_test_methods_retained')
    return adapted, [dict(original=original, replacement=replacement, occurrences=count)
                     for original, replacement, count in replacements]


class CandidateImports(importlib.abc.MetaPathFinder):
    def __init__(self, source, pins):
        self.source = source
        self.pins = pins

    def find_spec(self, fullname, path=None, target=None):
        namespace = fullname.split('.')[0]
        if namespace in ('transformers', 'peft', 'datasets', 'openai', 'anthropic', 'bitsandbytes'):
            raise ImportError('R173_forbids_model_provider_or_dataset_import:' + fullname)
        if namespace not in ('gpu', 'organism_v6'):
            return None
        search = [str(self.source)] if path is None else path
        specification = importlib.machinery.PathFinder.find_spec(fullname, search)
        if specification is None:
            raise ModuleNotFoundError('not_in_actual_guard_plus_three_helper_closure:' + fullname,
                                      name=fullname)
        if specification.origin is None:
            require(all(Path(location).is_relative_to(self.source)
                        for location in specification.submodule_search_locations),
                    'namespace_only_in_candidate')
        else:
            origin = Path(specification.origin).resolve()
            require(origin.is_relative_to(self.source)
                    and str(origin.relative_to(self.source)) in self.pins,
                    'project_import_only_from_candidate:' + fullname)
        return specification


class RuntimeFence:
    def __init__(self, scratch, pins):
        self.scratch = scratch
        self.source = scratch / 'source'
        self.pins = pins
        self.loaded = {}
        self.denied = []
        self.open_context = []
        self.read_roots = [scratch, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(),
                           Path('/usr'), Path('/lib'), Path('/lib64'), Path('/etc')]
        self.special_reads = {'/dev/null', '/dev/urandom', '/proc/cpuinfo', '/proc/meminfo',
                              '/proc/self/maps', '/proc/self/status', '/proc/self/stat'}

    def deny(self, reason):
        self.denied.append(reason)
        raise PermissionError('R173_CPU_fence:' + reason)

    def path_for(self, value, directory_fd=None):
        if isinstance(value, int):
            return Path(os.readlink('/proc/self/fd/' + str(value))).resolve()
        path = Path(os.fsdecode(value))
        if not path.is_absolute() and directory_fd not in (None, -1):
            path = Path(os.readlink('/proc/self/fd/' + str(directory_fd))) / path
        return path.resolve()

    def check_file(self, path, writing):
        if writing:
            if not path.is_relative_to(self.scratch / 'tmp') and path != self.scratch / 'RECEIVING_CPU.json':
                self.deny('write_outside_fixture_tmp:' + str(path))
        elif not (any(path.is_relative_to(root) for root in self.read_roots)
                  or str(path) in self.special_reads):
            self.deny('read_outside_candidate_or_installed_runtime:' + str(path))

    def audit(self, event, arguments):
        if event in ('subprocess.Popen', 'os.system', 'os.fork', 'os.forkpty', 'os.posix_spawn',
                     'os.exec', 'os.kill', 'os.killpg') or (
                         event.startswith('socket.') and event != 'socket.gethostname'):
            self.deny('process_signal_or_network:' + event)
        if event == 'open':
            filename, mode, flags = arguments
            path = self.open_context[-1] if self.open_context else self.path_for(filename)
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            self.check_file(path, writing)
        if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate'):
            directory_fd = arguments[-1] if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod') else None
            self.check_file(self.path_for(arguments[0], directory_fd), True)
        if event in ('os.rename', 'os.link', 'os.symlink'):
            self.check_file(self.path_for(arguments[1], arguments[-1]), True)
            if event != 'os.symlink':
                self.check_file(self.path_for(arguments[0], arguments[-2]), True)
        if event == 'exec':
            filename = arguments[0].co_filename
            if filename.startswith(str(self.source) + '/'):
                path = Path(filename)
                relative = str(path.relative_to(self.source))
                require(relative in self.pins, 'executed_only_pinned_project_file')
                actual = sha(path.read_bytes())
                require(actual == self.pins[relative], 'executed_file_hash_matches_manifest')
                previous = self.loaded.get(relative, {})
                self.loaded[relative] = dict(path=str(path), sha256=actual,
                    executions=previous.get('executions', 0) + 1)

    def install(self):
        original_open = os.open

        def scoped_open(path, flags, mode=0o777, *, dir_fd=None):
            absolute = self.path_for(path, dir_fd)
            self.open_context.append(absolute)
            try:
                return original_open(path, flags, mode, dir_fd=dir_fd)
            finally:
                self.open_context.pop()

        def forbidden_signal(*arguments, **keywords):
            self.deny('real_signal_or_timer')

        os.open = scoped_open
        for name in ('signal', 'setitimer', 'alarm', 'pthread_kill', 'pthread_sigmask'):
            if hasattr(signal, name):
                setattr(signal, name, forbidden_signal)
        sys.addaudithook(self.audit)


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.outcomes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes.append(dict(test=test.id(), status='PASS'))

    def addError(self, test, error):
        super().addError(test, error)
        self.outcomes.append(dict(test=test.id(), status='ERROR', traceback=self.errors[-1][1]))

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.outcomes.append(dict(test=test.id(), status='FAIL', traceback=self.failures[-1][1]))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes.append(dict(test=test.id(), status='SKIP', reason=reason))


def inventory(source, expected):
    observed = {}
    for path in source.rglob('*'):
        require(not path.is_symlink(), 'no_candidate_symlinks')
        if path.is_file():
            observed[str(path.relative_to(source))] = sha(path.read_bytes())
    require(observed == expected, 'candidate_exact_whitelist_and_hashes')
    return observed


def execute(payload):
    receipt = dict(schema='R173_ACTUAL_RECEIVING_CPU_V1', started_utc=utc_now(),
        scratch=SCRATCH, old_source_root=OLD_SOURCE,
        old_guard_ref=dict(path=OLD_GUARD, sha256=GUARD_SHA256),
        attempt_limit=1, retry_permitted=False, success=False, evidence_rebind_eligible=False,
        scope='TRAIN fixture CPU tests; native model/tokenizer/optimizer/checkpoint/lifecycle are stubs; '
              'optional real Torch tiny CPU optimizer only; no actual saved-life restore or replay',
        operational_GO_created=False, saved_handoff_created=False, full_source_approval=False,
        saved_state_ownership_established=False, evaluator_admission=False,
        numerical_tolerances_changed=False, test_assertions_changed=False,
        original_test_methods_removed=0,
        known_coverage_issue='Two original native tests import prohibited R145 suffix helpers; '
                             'run them unchanged and report errors, never silently skip or copy those helpers.')
    scratch = Path(SCRATCH)
    created = False
    reader = BoundReader()
    fence = None
    try:
        files = unpack_payload(payload)
        require(scratch.parent == Path('/localhome/local-rohing') and scratch == scratch.resolve(),
                'independent_exact_scratch')
        scratch.mkdir(exist_ok=False)
        created = True
        write_once(scratch / 'ATTEMPT_STARTED.json', encoded(receipt))
        runner_raw = base64.b64decode(payload['runner'], validate=True)
        require(sha(runner_raw) == payload['runner_sha256'], 'runner_transfer_hash')
        write_once(scratch / 'receiving_cpu.py', runner_raw)
        receipt['runner_ref'] = dict(path=str(scratch / 'receiving_cpu.py'), sha256=sha(runner_raw))
        guard_raw = reader.read(OLD_GUARD, GUARD_SHA256)
        guard = json.loads(guard_raw)
        require(guard['schema'] == 'R125_CONTINUAL_GUARD_V1', 'original_guard_schema')
        plan_ref = dict(path=guard['plan_path'], sha256=guard['plan_sha256'])
        require(Path(plan_ref['path']).parent == Path(OLD_SOURCE).parent, 'bound_old_plan_location')
        plan_raw = reader.read(plan_ref['path'], plan_ref['sha256'])
        plan = json.loads(plan_raw)
        require(plan['source_root'] == OLD_SOURCE and type(plan['physical']) is int
                and plan['physical'] == 1 and plan['presleep_variant'] == 'reread_select',
                'actual_physical1_reread_source')
        require(plan['root'] == '/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1',
                'exact_creative_reread_life')
        receipt.update(old_plan_ref=plan_ref, old_life_root=plan['root'],
                       hard_end_unix_unmodified=plan['hard_end_unix'])
        pins = guard['source_pins']
        validate_pins(pins)
        source = scratch / 'source'
        source.mkdir()
        write_once(scratch / 'provenance/OLD_GUARD.json', guard_raw)
        write_once(scratch / 'provenance/OLD_PLAN.json', plan_raw)
        for name, checksum in sorted(pins.items()):
            write_once(source / relative_python(name), reader.read(Path(OLD_SOURCE) / name, checksum))
        for name in HELPERS:
            write_once(source / name, files[name])
        expected = dict(pins, **HELPERS)
        receipt['candidate_source_sha256'] = inventory(source, expected)
        receipt['candidate_source_manifest_sha256'] = sha(encoded(expected))
        receipt['candidate_source_root'] = str(source)
        receipt['old_python_files_copied'] = len(pins)
        receipt['added_python_files'] = HELPERS
        receipt['startup_copied'] = False
        receipt['runtime_dependencies'] = {name: dict(path=str(source / (name.replace('.', '/') + '.py')),
            sha256=expected[name.replace('.', '/') + '.py']) for name in DEPENDENCIES}
        harness = scratch / 'harness'
        fixtures = harness / 'fixtures'
        write_once(fixtures / 'ROW118_TRAIN_FIXTURE.json', files[FIXTURE])
        receipt['train_fixture_ref'] = dict(path=str(fixtures / 'ROW118_TRAIN_FIXTURE.json'), sha256=FIXTURE_SHA256)
        receipt['tests'] = {}
        for name in TESTS:
            write_once(harness / 'originals' / name, files[name])
            adapted, changes = adapt_test(name, files[name], source, fixtures)
            write_once(harness / name, adapted)
            receipt['tests'][name] = dict(original_sha256=sha(files[name]),
                adapted_path=str(harness / name), adapted_sha256=sha(adapted), path_only_changes=changes)
        write_once(harness / 'tests/__init__.py', b'')
        (scratch / 'tmp').mkdir()
        os.chdir(scratch)
        tempfile.tempdir = str(scratch / 'tmp')
        sys.path[:0] = [str(harness), str(source)]
        require(not any(name.split('.')[0] in ('gpu', 'organism_v6', 'tests') for name in sys.modules),
                'no_preloaded_project_or_test_modules')
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and sys.dont_write_bytecode,
                'CPU_visibility_and_no_bytecode')
        sys.meta_path.insert(0, CandidateImports(source, expected))
        fence = RuntimeFence(scratch, expected)
        fence.install()
        receipt['interpreter'] = dict(executable=sys.executable, version=sys.version,
                                     prefix=sys.prefix, sys_path=sys.path.copy())
        receipt['environment'] = {name: os.environ.get(name) for name in (
            'CUDA_VISIBLE_DEVICES', 'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'OMP_NUM_THREADS',
            'MKL_NUM_THREADS', 'PYTHONDONTWRITEBYTECODE')}
        output = io.StringIO()
        modules = [name[:-3].replace('/', '.') for name in TESTS]
        with redirect_stdout(output), redirect_stderr(output):
            suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
            result = unittest.TextTestRunner(stream=output, verbosity=2,
                                            resultclass=RecordedResult).run(suite)
        receipt.update(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
            skipped=[dict(test=test.id(), reason=reason) for test, reason in result.skipped],
            outcomes=result.outcomes, test_output=output.getvalue(), modules=modules,
            test_suite_success=result.wasSuccessful())
        torch = sys.modules.get('torch')
        receipt['torch'] = dict(imported=torch is not None,
            version=str(getattr(torch, '__version__', 'unavailable')),
            path=getattr(torch, '__file__', None),
            cuda_initialized=None if torch is None else torch.cuda.is_initialized(),
            real_torch_test=[entry for entry in result.outcomes if 'actual_torch_CPU' in entry['test']])
        require(torch is None or not torch.cuda.is_initialized(), 'no_actual_CUDA_initialization')
        receipt['source_unchanged_after_tests'] = inventory(source, expected) == expected
        receipt['loaded_project_modules'] = {name: dict(path=str(Path(module.__file__).resolve()),
            sha256=sha(Path(module.__file__).read_bytes())) for name, module in sorted(sys.modules.items())
            if name.split('.')[0] in ('gpu', 'organism_v6') and getattr(module, '__file__', None)}
        require(all(name.replace('.', '/') + '.py' in fence.loaded for name in DEPENDENCIES),
                'actual_dependencies_executed')
        require(NATIVE_PATH in fence.loaded, 'actual_native_file_executed_not_archived_workspace_fixture')
        require(not fence.denied, 'no_forbidden_runtime_operations')
        receipt['success'] = result.wasSuccessful()
        receipt['status'] = 'CPU_TESTS_PASS_NOT_ADMISSION' if receipt['success'] else 'CPU_TESTS_FAILED_NO_REBIND'
        receipt['evidence_rebind_eligible'] = receipt['success'] and not result.skipped
    except BaseException as error:
        receipt.update(status='FAILED_NO_RETRY', failure_type=type(error).__name__,
                       failure=str(error), traceback=traceback.format_exc())
    receipt['operational_bytes_read'] = reader.bytes_read
    receipt['receiving_bound_reads'] = reader.references
    if fence is not None:
        receipt['executed_project_files'] = fence.loaded
        receipt['denied_runtime_operations'] = fence.denied
    receipt['ended_utc'] = utc_now()
    raw = encoded(receipt)
    if created:
        write_once(scratch / 'RECEIVING_CPU.json', raw)
    return raw
