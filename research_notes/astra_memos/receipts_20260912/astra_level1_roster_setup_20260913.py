import hashlib
import json
from pathlib import Path


def pin(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


root = Path('/tmp/astra_level1_roster_20260913_attempt1')
root.mkdir()
repo = Path('/data/home/rohing/dream-state')
protocol = repo / 'research_notes/astra_memos/ASTRA_LEVEL1_SKILL_ROSTER_PROTOCOL_2026-09-13.md'
identities = json.loads(Path('/tmp/astra_level1_precheck_identities_20260913.json').read_text())['nodes']
uuids = {
    'node1': ['GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d', 'GPU-4b071167-a06a-773c-f947-60cb8c2f7512',
              'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14',
              'GPU-f83fb491-34ce-4176-5852-c94652151a9f', 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30'],
    'node2': ['GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4', 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05',
              'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733', 'GPU-d304a15c-516a-16a0-a926-a560304077cc',
              'GPU-0cc84073-37a0-4f7a-e555-11671425bd03', 'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf']}
skills = {'node1': ['prediction', 'goal_completion'], 'node2': ['contradiction', 'update_judgement']}
source_files = {str(path.relative_to(repo)): pin(path)['sha256'] for path in
                [repo / 'organism_v6' / name for name in ('__init__.py', 'birth_skill_corpus.py', 'rulegame_parenting_diagnostic.py', 'train_adapter_v3.py')]}
entries, prechecks = [], {}
for node, selected_skills in skills.items():
    base_index = 0 if node == 'node1' else 1
    prechecks[node] = {key: identities[node][key] for key in ('host_boot_id', 'uid', 'daemon_identities')}
    prechecks[node]['gpus'] = {str(index + base_index): uuid for index, uuid in enumerate(uuids[node])}
    for skill_index, skill in enumerate(selected_skills):
        material = '/tmp/astra_level1_prediction_goal_material_20260913.py' if node == 'node1' else '/tmp/astra_level1_discrimination_material_20260913.py'
        for seed in range(3):
            offset = 3 * skill_index + seed
            specification = dict(source='/tmp/astra_level1_source_20260913_attempt1', source_files=source_files,
                model='/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
                runner_sha256=pin('/tmp/astra_level1_skill_run_20260913.py')['sha256'], material=pin(material),
                public=pin('/tmp/astra_birth_skill_probe_run_20260913.py'), reflection=pin('/tmp/astra_reflection_fit_run_20260913.py'),
                protocol=dict(path='/tmp/' + protocol.name, sha256=pin(protocol)['sha256']),
                binding=dict(path='/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json', sha256='e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019'),
                skill=skill, learner_seed=seed, material_seed=0, gpu_index=base_index + offset, gpu_uuid=uuids[node][offset],
                lease_end=1789427640 if node == 'node1' else 1789980180)
            path = root / f'{skill}_seed{seed}.json'
            with path.open('x') as stream:
                stream.write(json.dumps(specification, sort_keys=True) + '\n')
            entries.append(dict(node=node, name=f'{skill}_seed{seed}', spec=pin(path),
                root=f'/localhome/local-rohing/astra_diagnostics/level1_{skill}_seed{seed}_20260913_attempt1',
                gpu_index=specification['gpu_index'], gpu_uuid=specification['gpu_uuid']))
with (root / 'prechecks.json').open('x') as stream:
    stream.write(json.dumps(prechecks, sort_keys=True) + '\n')
with (root / 'roster.json').open('x') as stream:
    stream.write(json.dumps(dict(entries=entries, prechecks=pin(root / 'prechecks.json')), sort_keys=True) + '\n')
print(json.dumps(dict(roster=pin(root / 'roster.json'), prechecks=pin(root / 'prechecks.json')), sort_keys=True))
