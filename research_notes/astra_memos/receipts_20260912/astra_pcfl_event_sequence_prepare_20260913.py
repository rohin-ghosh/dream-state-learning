import hashlib
import json
import os
from pathlib import Path
import sys

source = Path('/tmp/astra_pcfl_event_sequence_source_20260913_attempt1')
sys.path.insert(0, str(source))
os.environ.update({name: '1' for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY', 'VLLM_NO_USAGE_STATS')})
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from organism_v6 import pcfl_event_sequence as sequence
from transformers import AutoTokenizer

prior = json.loads(Path('/localhome/local-rohing/astra_diagnostics/pcfl_event_only_20260913_attempt1/spec.json').read_text())
replay_path = Path(prior['replay_receipt']['path'])
if hashlib.sha256(replay_path.read_bytes()).hexdigest() != prior['replay_receipt']['sha256']:
    raise ValueError('original replay file pin mismatch')
replay = json.loads(replay_path.read_text())
imported = sequence.prefix.build_import(sequence.prefix.load_evidence(prior['archive']['path']), replay, replay['sha256'])
tokenizer = AutoTokenizer.from_pretrained(prior['model_path'], local_files_only=True, trust_remote_code=False)
exported = sequence.export_material(imported, imported['sha256'], tokenizer)
destination = Path('/tmp/astra_pcfl_event_sequence_material_20260913_attempt1.json')
with destination.open('xb') as stream:
    stream.write(sequence.prefix.canonical(exported) + b'\n')
print(json.dumps({'status': exported['status'], 'path': str(destination),
    'file_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'export_sha256': exported['sha256'],
    'spec_sha256': exported['spec']['sha256'], 'import_sha256': imported['sha256'],
    'source_commit': '8a880ddd031f9432270c01b03c70a6e0194ef9d4',
    'phases': {name: {key: phase[key] for key in ('parent_phase', 'updates', 'presentations', 'supervised_tokens', 'input_tokens', 'context_dropped', 'target_dropped')}
               for name, phase in exported['phases'].items()}, 'fits': 0, 'updates_executed': 0}, sort_keys=True, indent=2))
