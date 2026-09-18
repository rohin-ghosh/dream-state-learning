"""Prepare and test a separate math-package profile; never deploy it to a life."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ORIGINAL_SOURCE = Path('/localhome/local-rohing/orch_r153_r188_C2_20260917_recovery1/source')
ORIGINAL_PROFILE_SHA = '9117c4d72cdbb700e351f4625e763f96cf94341a3cf6d2a2cf3445687bfae48b'
PROFILE = 'gpu/orch_r125_cpu_confinement_probe.py'
PACKAGE_NAMES = ('sympy', 'mpmath', 'sympy-1.14.0.dist-info', 'mpmath-1.3.0.dist-info')
SMOKE = '''import errno,importlib.util,json,os,pathlib,sys
import sympy,mpmath
amount=sympy.symbols('amount')
answer=sympy.solve(sympy.Eq(3*amount+2,23),amount)
assert answer==[7]
assert sympy.diff(amount**3,amount)==3*amount**2
assert sympy.__version__=='1.14.0' and mpmath.__version__=='1.3.0'
assert sys.executable=='/usr/bin/python3' and sys.flags.isolated==1
assert importlib.util.find_spec('torch') is None
assert not pathlib.Path('/localhome').exists()
try:
 with open(sympy.__file__,'a') as output:output.write('not_allowed')
except OSError as error:
 assert error.errno in (errno.EACCES,errno.EPERM,errno.EROFS)
else:raise AssertionError('math_bundle_writable')
print(json.dumps(dict(executable=sys.executable,python=sys.version.split()[0],sympy=sympy.__version__,mpmath=mpmath.__version__,solution=[int(value) for value in answer],sympy_path=sympy.__file__,bundle_readonly=True,torch_exposed=False,host_home_exposed=False)))
'''
SYNTAX_FAILURE = 'quantity=1\n// this must remain invalid Python\nprint(quantity)\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def profile_source(original, bundle, manifest_path, manifest_sha):
    require(hashlib.sha256(original.encode()).hexdigest() == ORIGINAL_PROFILE_SHA,
            'exact_original_C2_profile')
    require(bundle.is_absolute() and bundle.resolve() == bundle and
            manifest_path.parent == bundle.parent, 'owned_absolute_bundle')
    bootstrap = "import runpy,sys;sys.path.append('/opt/r188-c2-math');sys.argv=['/job.py'];runpy.run_path('/job.py',run_name='__main__')"
    addition = '''
_r188_base_command = command


def command(root, unit):
    bundle = Path(BUNDLE)
    manifest_path = Path(MANIFEST)
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError('bound_math_bundle_manifest')
    manifest = json.loads(manifest_path.read_bytes())
    actual = {str(path.relative_to(bundle)): path for path in bundle.rglob('*') if path.is_file()}
    if set(actual) != set(manifest['files']) or any(path.is_symlink() for path in bundle.rglob('*')):
        raise ValueError('exact_math_bundle_inventory')
    for name, path in actual.items():
        if path.resolve() != path or hashlib.sha256(path.read_bytes()).hexdigest() != manifest['files'][name]:
            raise ValueError('bound_math_package_bytes')
    invocation = _r188_base_command(root, unit)
    prefix = '--property=BindReadOnlyPaths='
    positions = [position for position, value in enumerate(invocation) if value.startswith(prefix)]
    if len(positions) != 1 or invocation[-3:] != ['/usr/bin/python3', '-I', '/job.py']:
        raise ValueError('unchanged_original_CPU_command')
    invocation[positions[0]] += ' ' + str(bundle) + ':/opt/r188-c2-math'
    return invocation[:-3] + ['/usr/bin/python3', '-I', '-c', BOOTSTRAP]


'''.replace('BUNDLE', repr(str(bundle))).replace('MANIFEST_SHA', repr(manifest_sha)).replace('MANIFEST', repr(str(manifest_path))).replace('BOOTSTRAP', repr(bootstrap))
    marker = "if __name__ == '__main__':"
    require(original.count(marker) == 1, 'single_module_main_guard')
    updated = original.replace(marker, addition + marker)
    compile(updated, PROFILE, 'exec')
    return updated


def prepare(root):
    require(root.parent == Path('/localhome/local-rohing') and not root.exists()
            and root.name.startswith('orch_r153_cpu_smoke_'), 'fresh_cpu_probe_root')
    require(sha(ORIGINAL_SOURCE / PROFILE) == ORIGINAL_PROFILE_SHA, 'unchanged_live_original_source')
    require(shutil.disk_usage(root.parent).free > 512 * 1024 * 1024, 'disk_before_package_copy')
    root.mkdir(mode=0o755)
    source = root / 'source'
    shutil.copytree(ORIGINAL_SOURCE, source)
    source.chmod(0o755)
    (source / 'gpu').chmod(0o755)
    bundle = root / 'math_bundle'
    bundle.mkdir(mode=0o755)
    installed = Path('/localhome/local-rohing/v2/venv/lib/python3.12/site-packages')
    for name in PACKAGE_NAMES:
        origin = installed / name
        require(origin.is_dir() and not origin.is_symlink(), 'exact_installed_package_' + name)
        shutil.copytree(origin, bundle / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
    files = {}
    for path in bundle.rglob('*'):
        require(not path.is_symlink(), 'no_package_symlinks')
        if path.is_file():
            require(path.suffix not in ('.so', '.pth'), 'pure_packages_no_native_or_pth')
            files[str(path.relative_to(bundle))] = sha(path)
            path.chmod(0o444)
        else:
            path.chmod(0o555)
    bundle.chmod(0o555)
    manifest = root / 'MATH_BUNDLE.json'
    write(manifest, dict(schema='R188_ORIGINAL_C2_MATH_BUNDLE_V1', files=files,
        packages={'sympy': '1.14.0', 'mpmath': '1.3.0'}, source='existing_public_packages_in_host_venv',
        original_C2_only=True, bytes=sum((bundle / name).stat().st_size for name in files)))
    manifest.chmod(0o444)
    profile = source / PROFILE
    profile.chmod(0o644)
    profile.write_text(profile_source((ORIGINAL_SOURCE / PROFILE).read_text(), bundle, manifest, sha(manifest)))
    profile.chmod(0o444)
    original_files = {str(path.relative_to(ORIGINAL_SOURCE)): sha(path) for path in ORIGINAL_SOURCE.rglob('*') if path.is_file()}
    candidate_files = {str(path.relative_to(source)): sha(path) for path in source.rglob('*') if path.is_file()}
    require(set(original_files) == set(candidate_files), 'same_source_inventory')
    require([name for name in original_files if original_files[name] != candidate_files[name]] == [PROFILE],
            'only_CPU_profile_changes')
    write(root / 'CANDIDATE.json', dict(status='STAGED_NOT_DEPLOYED', original_source=str(ORIGINAL_SOURCE),
        original_profile_sha256=ORIGINAL_PROFILE_SHA, candidate_profile_sha256=sha(profile),
        bundle_manifest_sha256=sha(manifest), source_files=candidate_files,
        deployment_not_before='original C2 complete44; separate prospective environment-repair phase',
        no_learner_restart=True, no_parent_publication=True, no_frozen_copy_change=True,
        original_failed_attempts_preserved=True, created_unix=time.time()))
    return root


def test_candidate(root):
    source = root / 'source'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_cpu_experiment as cpu
    from organism_v6.orch_r125_experiment_request import make_request
    gate = root / 'gate'
    gate.mkdir()
    results = {}
    outcome = dict(started_unix=time.time(), status='RUNNING_TESTS_NOT_DEPLOYED', learner_calls=0,
        parent_publications=0, live_changes=0, historical_requests_replayed=0)
    try:
        for mode in ('basic', 'output', 'timeout', 'memory', 'files'):
            result = cpu.profile.run(root / ('probe_' + mode), mode)
            write(gate / (mode + '.json'), result)
            require(result['passed'] is True, 'confinement_' + mode)
            results[mode] = dict(passed=True, receipt_sha256=sha(gate / (mode + '.json')))
        verified = cpu.verify_gate(gate)
        for name, payload in (('synthetic_math', SMOKE), ('syntax_remains_failure', SYNTAX_FAILURE)):
            request = make_request(payload, dict(kind='BUILDER_TEST', record_index=0,
                record_sha256=hashlib.sha256(('R188_SYNTHETIC_' + name).encode()).hexdigest()))
            result = cpu.run_request(json.dumps(request).encode(), root / 'synthetic_spool', gate)
            require(result['cgroup_removed_after_stop'], 'test_cgroup_cleanup')
            if name == 'synthetic_math':
                require(result['status'] == 'COMPLETE' and result['returncode'] == 0, 'real_math_import_and_calculation')
                actual = json.loads(result['stdout'])
                require(actual['solution'] == [7] and actual['bundle_readonly'], 'actual_synthetic_result')
            else:
                require(result['status'] == 'PROCESS_FAILED' and result['returncode'] != 0
                        and 'SyntaxError' in result['stderr'], 'syntax_failure_not_rewritten')
            results[name] = {key: result.get(key) for key in ('status', 'returncode', 'stdout', 'stderr', 'cgroup_removed_after_stop')}
        require(sha(ORIGINAL_SOURCE / PROFILE) == ORIGINAL_PROFILE_SHA, 'live_profile_not_modified')
        outcome.update(status='PASS_NOT_DEPLOYED', gate_root=str(gate), gate_sha256=cpu.digest(verified))
    except BaseException as error:
        outcome.update(status='FAILED_NOT_DEPLOYED', error_type=type(error).__name__, reason=str(error))
        raise
    finally:
        outcome.update(results=results, finished_unix=time.time())
        write(root / 'RESULT.json', outcome)
        print(json.dumps(outcome))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'test'))
    parser.add_argument('--root', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'prepare':
        print(json.dumps(dict(root=str(prepare(arguments.root)), status='STAGED_NOT_DEPLOYED')))
    else:
        test_candidate(arguments.root)
