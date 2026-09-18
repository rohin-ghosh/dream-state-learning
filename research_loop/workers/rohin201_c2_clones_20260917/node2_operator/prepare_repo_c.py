"""Fresh REPO-C using the fixed C2 cut and existing real repository tools."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
MATH = HERE.parent / 'math_d1'
ROOT = HERE
SOURCE = ROOT / 'source'
SNAPSHOT = ROOT.parent / 'snapshot'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
DEVICE = 'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733'
PACKET = Path('/localhome/local-rohing/orch_r153_r184_staging_20260917/orch_r184_C2_sleep41_1789684294308387719')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def main():
    require(ROOT.name == 'repo_c1' and not (ROOT / 'PREPARE_ATTEMPT.json').exists(), 'new_repo_clone_only')
    write(ROOT / 'PREPARE_ATTEMPT.json', dict(started_unix=time.time(), no_implicit_retry=True))
    require(sha(SNAPSHOT / 'MANIFEST.json') == '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84', 'same_C2_snapshot')
    frozen = read(MATH / 'SOURCE.json')['source_pins']
    require({str(path.relative_to(MATH / 'source')): sha(path) for path in (MATH / 'source').rglob('*.py')} == frozen, 'unchanged_tested_math_closure')
    shutil.copytree(MATH / 'source', SOURCE)
    raw = ROOT / 'raw'
    (raw / 'stream').mkdir(parents=True, mode=0o700)
    require(sha(PACKET / 'PRESERVATION_RECEIPT.json') == 'cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e', 'fixed_prefix_provenance')
    shutil.copy2(PACKET / 'stream/JOURNAL.json', raw / 'stream/JOURNAL.json')
    shutil.copytree(PACKET / 'stream/records', raw / 'stream/records')
    with tarfile.open(MATH / 'FIXED_PREFIX_SUFFIX.tar.gz') as archive:
        for member in archive.getmembers():
            require(member.isfile() and len(Path(member.name).parts) == 2
                and Path(member.name).parts[0] in ('records', 'inbox') and not (raw / 'stream' / member.name).exists(), 'safe_fixed_prefix')
        archive.extractall(raw / 'stream', filter='data')
    (raw / 'stream/WRITER.lock').touch(exist_ok=False)
    require(len(list((raw / 'stream/records').glob('*.json'))) == 5847 * 2, 'same_exact_prefix_length')
    require(read(raw / 'stream/records/00000000000000005846.json')['sha256'] == read(SNAPSHOT / 'MANIFEST.json')['console_record']['sha256'], 'same_context_cut')
    shutil.copytree(SNAPSHOT / 'complete', raw / 'checkpoints/sleep_000051')
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text().replace("'R201_MATH_D_node2_clone1'", "'R202_REPO_C_node2_clone1'")
    marker = "        if route == 'CPU':\n"
    require(text.count(marker) == 1, 'single_actual_ACT_dispatch')
    text = text.replace(marker, "        if self.config['trial_id'] == 'R202_REPO_C_node2_clone1':\n            from research_loop.workers.rohin183_repo_learning_20260917.tools import request\n            try:\n                action = request(raw_act)\n            except (ValueError, TypeError):\n                route = 'REPO'\n            else:\n                if action is not None:\n                    route = 'REPO'\n        if route in ('CPU', 'REPO'):\n")
    text = text.replace("self.record_outcome(outcome, dispatched=route == 'CPU')", "self.record_outcome(outcome, dispatched=route in ('CPU', 'REPO'))")
    driver.write_text(text)
    confinement = SOURCE / 'gpu/r184_node2_confinement.py'
    text = confinement.read_text()
    for before, after in {'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4': DEVICE,
        'MINOR=1': 'MINOR=3', '/dev/nvidia1': '/dev/nvidia3', '0000:52:00.0': '0000:57:00.0',
        '[0, 2, 3, 4, 5, 6, 7]': '[0, 1, 2, 4, 5, 6, 7]', "'orch-r201-math-d1-'": "'orch-r202-repo-c1-'"}.items():
        require(before in text, 'exact_GPU3_confinement_substitution')
        text = text.replace(before, after)
    confinement.write_text(text)
    shutil.copy2(ROOT / 'repo_c_bridge.py', SOURCE / 'gpu/r184_cpu_bridge.py')
    tools_dir = SOURCE / 'research_loop/workers/rohin183_repo_learning_20260917'
    for filename in ('tools.py', 'test_tools.py'):
        shutil.copy2(ROOT / filename, tools_dir / filename)
    plan = deepcopy(read(MATH / 'control/PLAN.json'))
    plan.update(source_root=str(SOURCE), physical=3, gpu_uuid=DEVICE)
    plan['startup_context']['path'] = str(SOURCE / 'context/R153_STARTUP.md')
    plan['think_act_learn']['trial_id'] = 'R202_REPO_C_node2_clone1'
    plan['think_act_learn']['environment_facts'] = (
        'This repository environment exposes only byte-pinned safe repository files and your private immutable proposal workspace. '
        'During ACT, use one literal line: repo_list . ; repo_read relative/path.py 0 ; or repo_action followed by JSON with '
        'action note/propose/workspace_read, path, and content for writes. Use exactly one action, not the semicolon-separated examples. '
        'No child code/test execution, shell, network, GPU, credential access, repository merge, or live learner changes are provided. '
        'A proposal is not an applied patch or passing test. Use actual repository-tool receipts, never invent them.')
    (ROOT / 'control').mkdir()
    write(ROOT / 'control/PLAN.json', plan)
    shutil.copy2(MATH / 'LEASE.json', ROOT / 'LEASE.json')
    reference = Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
    original = read(reference / 'TOOLS.json')
    require(original['snapshot_manifest']['sha256'] == '1af9ee41cb041f9a6e505f18001f845e9a73df52c24a35e34bafa6a2fd8a58cb'
        and sha(original['snapshot_manifest']['path']) == original['snapshot_manifest']['sha256'], 'actual_retained_repo_snapshot')
    config = dict(schema='R183_REPO_TOOLS_V1', root=str(raw), snapshot=original['snapshot'],
        snapshot_manifest=original['snapshot_manifest'], workspace=str(ROOT / 'workspace'),
        receipts=str(ROOT / 'tool_receipts'), hard_end_unix=plan['hard_end_unix'])
    for name in ('workspace', 'tool_receipts'):
        (ROOT / name).mkdir(mode=0o700)
    write(ROOT / 'TOOLS.json', config)
    shutil.copytree(MATH / 'test_support', ROOT / 'test_support')
    main_ready = read(ROOT.parent / 'main_ready/READY.json')
    files = [name for name in main_ready['files'] if name.startswith('tests/')]
    files.append('research_loop/workers/rohin183_repo_learning_20260917/test_tools.py')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=os.pathsep.join((str(SOURCE), str(SOURCE / 'tests'), str(ROOT / 'test_support'))))
    with (ROOT / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *files], cwd=SOURCE,
            env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'receiving_repo_source_tests')
    import re
    count = int(re.search(r'(\d+) passed', (ROOT / 'CPU.log').read_text())[1])
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    cpu = dict(passed=True, tests_run=count, source_pins=pins, log_sha256=sha(ROOT / 'CPU.log'), observed_unix=time.time(),
        actual_repo_manifest_sha256=config['snapshot_manifest']['sha256'], python_execution=False)
    write(ROOT / 'SOURCE.json', dict(source_root=str(SOURCE), source_pins=pins, Main_READY_sha256=sha(ROOT.parent / 'main_ready/READY.json'),
        snapshot_manifest_sha256=sha(SNAPSHOT / 'MANIFEST.json'), delta='Bound REPO ACT routing + actual no-code-execution repository bridge + GPU3 confinement'))
    write(ROOT / 'CPU.json', cpu)
    write(ROOT / 'control/RECEIVING_CPU.json', cpu)
    print(json.dumps(dict(status='REPO_C_ASSEMBLED_CPU_PASS_NOT_LAUNCHED', tests_run=count, repo_manifest_sha256=config['snapshot_manifest']['sha256'])))


if __name__ == '__main__':
    main()
