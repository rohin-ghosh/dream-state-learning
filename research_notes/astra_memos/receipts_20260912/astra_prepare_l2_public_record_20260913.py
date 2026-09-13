import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

SOURCE = Path('/localhome/local-rohing/astra_sources/l2_public_record_20260913_attempt1')
ROOT = Path('/localhome/local-rohing/astra_diagnostics/l2_public_record_20260913_attempt1')
SPEC_PATH = Path('/tmp/astra_l2_public_record_spec_20260913_attempt1.json')
specification = importlib.util.spec_from_file_location('l2_native_prepare', SOURCE / 'gpu/astra_l2_public_record_dev.py')
runtime = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runtime)
assert runtime.digest(runtime.SELF) == '213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e'
model = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28').resolve(strict=True)
spec = dict(schema=runtime.SCHEMA, source=str(SOURCE), source_files=runtime.tree(SOURCE),
            core_schema='l2_public_record_dev_v0', helpers={
                'reflection': dict(path='/tmp/astra_reflection_fit_run_20260913.py', sha256='0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc'),
                'public': dict(path='/localhome/local-rohing/astra_sources/perception_fit_20260913_attempt1/astra_birth_skill_probe_run_20260913.py', sha256='59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c')},
            model=str(model), model_binding=dict(path='/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json', sha256='e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019'),
            protocol=dict(path='/tmp/ASTRA_L2_PUBLIC_RECORD_PROTOCOL_2026-09-13.md', sha256=runtime.digest('/tmp/ASTRA_L2_PUBLIC_RECORD_PROTOCOL_2026-09-13.md')),
            gpu_uuid='GPU-e1277146-04f2-c38f-d1ae-1a98132f907e', gpu_index=3, lease_end=1790391780)
runtime.offline()
core, trainer, probe, reflection = runtime.load_apis(spec)
tokenizer = probe.native_tokenizer(str(model))
world = core.build_world(runtime.SEEDS['vocabulary'], runtime.SEEDS['truth'])
public = core.public_view(world)
captures = []
audits = []
for block in (1, 2):
    episodes = []
    lineage = 'SHARED' if block == 1 else 'PROMOTE'
    for slot in public.slots[(block - 1) * 8:block * 8]:
        sequence = 100 + slot.index * 3
        action = core.make_receipt(public, slot.slot_id, 'action', public.actions[0].encode(), sequence=sequence, lineage=lineage)
        outcome = core.feedback(world, action, sequence=sequence + 1)
        target = public.actions[0] if outcome.raw == b'SUCCESS' else public.actions[1]
        record = core.make_receipt(public, slot.slot_id, 'record', target.encode(), sequence=sequence + 2, lineage=lineage, previous=outcome)
        episodes.append(core.Episode(action, outcome, record))
    capture = core.capture_block(public, block, lineage, tuple(episodes))
    captures.append(capture)
    corpus = core.compile_corpus(public, tuple(captures), expected_hashes=tuple(core.digest(value) for value in captures))
    encoded = runtime.encode_training(core, public, corpus, tokenizer, trainer, probe)
    assert encoded['rows'] == block * 8 and encoded['steps'] == block * 20
    audits.append(dict(block=block, rows=encoded['rows'], steps=encoded['steps'], target_tokens=encoded['target_tokens'], total_tokens=encoded['total_tokens'], encoding_sha256=runtime.value_hash(encoded)))
runtime.write('/tmp/astra_l2_native_encoding_20260913_attempt1.json', dict(status='PASS_NATIVE_TOKENIZER_CPU', synthetic_records_not_training_data=True, audits=audits, source_files=spec['source_files'], helpers=spec['helpers'], checked_unix=time.time()))
runtime.write(SPEC_PATH, spec)
result = runtime.prepare(SPEC_PATH, runtime.digest(SPEC_PATH), ROOT, allow_native=True)
runtime.write('/tmp/astra_l2_native_prepared_20260913_attempt1.json', dict(result=result, spec_sha256=runtime.digest(SPEC_PATH), encoding_sha256=runtime.digest('/tmp/astra_l2_native_encoding_20260913_attempt1.json')))
print(json.dumps(result, sort_keys=True))
