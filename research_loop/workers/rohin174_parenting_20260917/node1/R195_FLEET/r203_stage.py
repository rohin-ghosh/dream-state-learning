"""Stage the four explicitly selected node1 arms using the existing receiver."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import time


OWN = Path(__file__).resolve().parent
BASE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
TEMPLATE = BASE / 'creative_b1'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
ARMS = {
    2: ('MATH-COMM-B', 'r203_math_comm_b2', False,
        'Teach by answering concrete mathematical questions with actual obtained results. '
        'Choose a small question, derive or calculate an answer, and explain it clearly; '
        'distinguish evidence from a plan or an unexecuted tool call.'),
    3: ('REPO-EVIDENCE-C', 'r203_repo_evidence_c3', False,
        'Investigate read-only repository hypotheses using explicitly supplied, source-bound excerpts. '
        'The Python sandbox cannot read the host repository. Ask the parent for a specific path '
        'or symbol; only a supplied source receipt supports a repository observation. '
        'Never claim edits, tests or commands occurred without a real receipt.'),
    4: ('CREATIVE-STRUCTURED-A', 'r203_creative_structured_a4', True,
        'Choose an original scene or dialogue, write it, and revise using actual attributed '
        'parent judgment. Use wide/narrow/wide structured THINK. No peer is connected; '
        'creative feedback is a reader judgment, never an objective quality score.'),
    5: ('MATH-SELF-DERIVE-C', 'r203_math_self_derive_c5', False,
        'Use open THINK to choose and independently derive a mathematical relationship. '
        'Test a discriminating example when useful, retain actual results, and revise '
        'your own conjecture. Do not replace derivation with a repeated plan.'),
}
FIXED = {
    'MANIFEST.json': '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84',
    'SNAPSHOT.tar': '9beaf7a79063c5cf4af2868e1f3122dfea7f4fa5ce3f7d3f2f51716676cdee34',
    'RETAINED_PREFIX_0_5128.tar.gz': '3a3b0a2f1cdb9144b30a6c3fba82de246e3db27d164d45b2addff0bd3968d57f',
    'FIXED_PREFIX_SUFFIX.tar.gz': '271a13510cb0d9b14d8696efac9eb19d6ac5e29ba549a6a4d368b3ac27307aa0',
}


def sha(path):
    with Path(path).open('rb') as incoming:
        return hashlib.file_digest(incoming, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def local_specs():
    previous = read(OWN / 'R203_CANDIDATES_20260918T030441Z.json')
    specs = []
    for selected in previous['lives']:
        physical = selected['physical']
        name, basename, structured, task = ARMS[physical]
        specs.append(dict(physical=physical, name=name, remote_root=str(BASE / basename),
            trial_id='R203_' + name.replace('-', '_') + '_node1_clone1',
            structured=structured, task=task,
            old_life=selected['life'], old_pid=selected['pid'], old_start_ticks=selected['start_ticks'],
            old_root=selected['root'], old_guard=selected['guard_path'],
            old_guard_sha256=selected['guard_sha256'], old_plan_sha256=selected['plan_sha256'],
            gpu_uuid=selected['gpu_uuid'], device_minor=selected['device_minor'],
            hard_end_unix=selected['hard_end_unix'], lease_end_unix=selected['lease_end_unix'],
            resource_reallocation_not_scientific_failure=True,
            protected={2258434: '28070412', 2245391: '28062062', 183848: '40797822',
                       2204208: '42144998'},
            source_complete=51, source_optimizer_steps=4908, console_cut=5846,
            no_future_original_inbox=True, parent_guided_cycles=[52, 53, 54],
            parent_withdrawn_cycles=[55, 56, 57], no_peer_treatment=True,
            parent_reference_sha256='3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d'))
    write(OWN / 'R203_SELECTED_ARMS.json', dict(created_unix=time.time(), arms=specs,
        authorization='Rohin R203 explicit node1 GPU2/3/4/5 resource reallocation',
        source='fixed C2 complete51/context5846; no existing clone continuation copied'))
    return specs


def remote_stage(spec):
    assert socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 1395
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    root = Path(spec['remote_root'])
    assert root.parent == BASE and root.name == ARMS[spec['physical']][1]
    assert sha(spec['old_guard']) == spec['old_guard_sha256']
    guard = read(spec['old_guard'])
    assert sha(guard['plan_path']) == spec['old_plan_sha256']
    plan = read(guard['plan_path'])
    assert plan['physical'] == spec['physical'] and plan['gpu_uuid'] == spec['gpu_uuid']
    assert guard['device_containment']['minor'] == spec['device_minor']
    identity = (Path('/proc') / str(spec['old_pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()
    assert identity[19] == spec['old_start_ticks']
    original_source = TEMPLATE / 'source'
    source_pins = read(TEMPLATE / 'R202_SOURCE.json')['source_pins']
    assert {str(path.relative_to(original_source)): sha(path) for path in original_source.rglob('*.py')} == source_pins
    assert all(sha(TEMPLATE / name) == expected for name, expected in FIXED.items())
    assert shutil.disk_usage(BASE).free > 12 * 1024**3
    root.mkdir(mode=0o700)
    write(root / 'ARM.json', spec)
    for name in (*FIXED, 'READY.json', 'runtime_overlay.tar.gz', 'R202_READY.json',
                 'structured_think_overlay.tar.gz', 'assemble_fixed_prefix.py'):
        shutil.copy2(TEMPLATE / name, root / name)
    shutil.copytree(TEMPLATE / 'snapshot', root / 'snapshot')
    shutil.copytree(original_source, root / 'source')
    for path in [root / 'source', *(root / 'source').rglob('*')]:
        assert not path.is_symlink() and path.stat().st_uid == os.getuid()
        if path.is_file():
            donor = original_source / path.relative_to(root / 'source')
            assert path.stat().st_nlink == 1 and path.stat().st_ino != donor.stat().st_ino
        path.chmod(0o700 if path.is_dir() else 0o600)
    assembly_spec = importlib.util.spec_from_file_location('existing_fixed_prefix', root / 'assemble_fixed_prefix.py')
    assembly = importlib.util.module_from_spec(assembly_spec)
    assembly_spec.loader.exec_module(assembly)
    assembly.ROOT = root
    assembly.REMOTE = root
    assembly.main()
    draft = read(TEMPLATE / 'control/PLAN.json')
    draft.update(source_root=str(root / 'source'), physical=spec['physical'],
        gpu_uuid=spec['gpu_uuid'], hard_end_unix=spec['hard_end_unix'], lease_end_unix=spec['lease_end_unix'])
    draft['think_act_learn'].update(trial_id=spec['trial_id'], environment_facts=spec['task'])
    if not spec['structured']:
        draft['think_act_learn'].pop('structured_think_policy', None)
    write(root / 'PLAN_DRAFT_WAIT_R203.json', dict(plan=draft, executable=False,
        pending='Main tested R203 overlay and receiving config binding',
        console_target_policy_unchanged=True, no_historical_retrotraining=True))
    write(root / 'STAGED.json', dict(observed_unix=time.time(), arm=spec['name'],
        physical=spec['physical'], source_complete=51, optimizer_steps=4908, console_cut=5846,
        full_fixed_prefix_verified=True, private_source_copies=True, old_native_identity_verified=True,
        native_launches=0, retirements=0, signals=0, original_C2_calls=0,
        status='STAGED_EXACT_FIXED_SOURCE_WAIT_MAIN_R203_NOT_LIVE'))
    print(json.dumps(read(root / 'STAGED.json')))


def stage_all():
    repo = OWN.parents[4]
    specs = local_specs()
    for spec in specs:
        code = ("namespace={'__name__':'node1_r203_stage','__file__':" + repr(str(BASE / 'r203_stage.py')) +
            '};exec(' + repr(Path(__file__).read_text()) + ',namespace);namespace["remote_stage"](' + repr(spec) + ')')
        result = subprocess.run(['bash', 'gpu/a100_ssh.sh',
            'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 ' + PYTHON + ' -B -c ' + shlex.quote(code)],
            cwd=repo, capture_output=True, text=True, timeout=180)
        prefix = OWN / ('R203_STAGE_' + str(spec['physical']))
        prefix.with_suffix('.stdout').write_text(result.stdout)
        prefix.with_suffix('.stderr').write_text(result.stderr)
        if result.returncode:
            raise RuntimeError('stage_failed_preserve_receiver_no_retry_slot_' + str(spec['physical']))
        print(spec['name'] + ': STAGED_FIXED51_CONTEXT5846_NOT_LIVE', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage',))
    parser.parse_args()
    stage_all()
