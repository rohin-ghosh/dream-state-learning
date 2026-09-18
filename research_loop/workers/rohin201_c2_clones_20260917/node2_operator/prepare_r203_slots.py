"""Prepare only the two assigned new slots from the immutable shared cut."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import time


BASE = Path(__file__).resolve().parent
MATH = BASE / 'math_d1'
SNAPSHOT = BASE / 'snapshot'
PACKET = Path('/localhome/local-rohing/orch_r153_r184_staging_20260917/orch_r184_C2_sleep41_1789684294308387719')
ARMS = {
    'creative_d1': dict(name='CREATIVE-D', physical=4, gpu_uuid='GPU-d304a15c-516a-16a0-a926-a560304077cc',
        pci='0000:ce:00.0', trial_id='R203_CREATIVE_D_node2_clone1', math_tool=False,
        environment_facts='Your present environment is a prose workshop: write and revise your own scenes, dialogue, imagery or arguments. ACT is the actual draft you produce, not a claim that an external tool ran. Your parent can give qualitative feedback, not a numerical judge or sealed score. No code executor, network, repository write or external creative-test passage is supplied to this arm.'),
    'math_transfer_c1': dict(name='MATH-TRANSFER-C', physical=6, gpu_uuid='GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf',
        pci='0000:d5:00.0', trial_id='R203_MATH_TRANSFER_C_node2_clone1', math_tool=True,
        environment_facts='Your present environment supports modular-arithmetic and divisibility puzzles, worked prose, and a confined Python tool with read-only SymPy 1.14.0 and mpmath 1.3.0. There is no network, GPU, home access or Torch. Choose small puzzles, test examples or counterexamples, and distinguish actual sandbox results from your conjectures. The parent offers questions rather than worked solutions.'),
}


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, document):
    with path.open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    require(BASE.name == 'orch_r153_r201_node2_clones_20260917_operator1', 'owned_node2_parent_root')
    require(sha(SNAPSHOT / 'MANIFEST.json') == '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84', 'same_fixed_C2_capture')
    require(sha(MATH / 'FIXED_PREFIX_SUFFIX.tar.gz') == '271a13510cb0d9b14d8696efac9eb19d6ac5e29ba549a6a4d368b3ac27307aa0', 'same_fixed_prefix_suffix')
    require(sha(PACKET / 'PRESERVATION_RECEIPT.json') == 'cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e', 'same_original_prefix')
    require({str(path.relative_to(MATH / 'source')): sha(path) for path in (MATH / 'source').rglob('*.py')}
        == read(MATH / 'SOURCE.json')['source_pins'], 'live_math_source_unchanged_read_only_template')
    for name, config in ARMS.items():
        root = BASE / name
        root.mkdir(mode=0o700)
        write(root / 'PREPARING.json', dict(started_unix=time.time(), assignment=config,
            launch_authorized=True, R203_overlay_applied=False, original_C2_writes=0, peer_active=False))
        source = root / 'source'
        shutil.copytree(MATH / 'source', source)
        shutil.copytree(MATH / 'test_support', root / 'test_support')
        raw = root / 'raw'
        (raw / 'stream').mkdir(parents=True)
        shutil.copy2(PACKET / 'stream/JOURNAL.json', raw / 'stream/JOURNAL.json')
        shutil.copytree(PACKET / 'stream/records', raw / 'stream/records')
        with tarfile.open(MATH / 'FIXED_PREFIX_SUFFIX.tar.gz') as archive:
            for member in archive.getmembers():
                require(member.isfile() and len(Path(member.name).parts) == 2
                    and Path(member.name).parts[0] in ('records', 'inbox') and not (raw / 'stream' / member.name).exists(), 'fixed_safe_suffix_only')
            archive.extractall(raw / 'stream', filter='data')
        (raw / 'stream/WRITER.lock').touch(exist_ok=False)
        shutil.copytree(SNAPSHOT / 'complete', raw / 'checkpoints/sleep_000051')
        require(len(list((raw / 'stream/records').glob('*.json'))) == 11694, 'same5847_record_prefix_with_intents')
        require(read(raw / 'stream/records/00000000000000005846.json')['sha256'] == read(SNAPSHOT / 'MANIFEST.json')['console_record']['sha256'], 'same_context5846')
        for filename in ('receive_math_d.py', 'validate_math_d_restore.py', 'LEASE.json'):
            shutil.copy2(MATH / filename, root / filename)
        shutil.copy2(MATH / 'math_d_bridge.py', root / 'math_bridge.py')
        shutil.copy2(BASE / 'repo_c1/clone_parent.py', root / 'clone_parent.py')
        shutil.copy2(BASE / 'repo_c1/R202_PART_ONE.txt', root / 'R202_PART_ONE.txt')
        confinement = source / 'gpu/r184_node2_confinement.py'
        text = confinement.read_text()
        substitutions = {'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4': config['gpu_uuid'], 'MINOR=1': 'MINOR=' + str(config['physical']),
            '/dev/nvidia1': '/dev/nvidia' + str(config['physical']), '0000:52:00.0': config['pci'],
            '[0, 2, 3, 4, 5, 6, 7]': str([minor for minor in range(8) if minor != config['physical']]),
            "'orch-r201-math-d1-'": repr('orch-r203-' + name.replace('_', '-') + '-')}
        for before, after in substitutions.items():
            require(before in text, 'existing_strict_confinement_token')
            text = text.replace(before, after)
        confinement.write_text(text)
        plan = deepcopy(read(MATH / 'control/PLAN.json'))
        plan.update(source_root=str(source), physical=config['physical'], gpu_uuid=config['gpu_uuid'])
        plan['startup_context']['path'] = str(source / 'context/R153_STARTUP.md')
        plan['think_act_learn'].update(trial_id=config['trial_id'], environment_facts=config['environment_facts'])
        (root / 'control').mkdir()
        write(root / 'control/PLAN_PRE_R203.json', plan)
        write(root / 'ARM.json', config)
        write(root / 'STAGED.json', dict(status='FIXED_SOURCE_STAGED_WAITING_MAIN_R203_OVERLAY', observed_unix=time.time(),
            physical=config['physical'], gpu_uuid=config['gpu_uuid'], records=5847, complete_cycle=51, optimizer_steps=4908,
            context_record=5846, capture_manifest_sha256=sha(SNAPSHOT / 'MANIFEST.json'), launches=0, native_signals=0,
            parent_reference_sha256='3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d', peer_active=False))
        print(json.dumps(read(root / 'STAGED.json')))


if __name__ == '__main__':
    main()
