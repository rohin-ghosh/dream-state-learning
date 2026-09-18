"""Read-only CPU counterfactual of frozen2762; no generation or native import."""

import json
from pathlib import Path
import subprocess


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[3]


def main():
    modules = {name: (OWN / 'fork' / relative).read_text() for name, relative in (
        ('organism_v6.orch_r124_train_history', 'organism_v6/orch_r124_train_history.py'),
        ('organism_v6.orch_r125_continual_stream', 'organism_v6/orch_r125_continual_stream.py'))}
    code = 'MODULES = ' + repr(modules) + '\n' + '''
from datetime import datetime, timezone
import hashlib, json, sys, types
from pathlib import Path
source = Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918/extension_oct01_preview_20260918T1742Z/source')
sys.path.insert(0, str(source))
for name, text in MODULES.items():
    module = types.ModuleType(name)
    module.__file__ = 'CPU_ONLY_IN_MEMORY_FORK/' + name
    sys.modules[name] = module
    exec(compile(text, module.__file__, 'exec'), module.__dict__)
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from transformers import AutoTokenizer
model = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)
def count(messages):
    return len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
record = json.loads(Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918/raw/stream/records/00000000000000002762.json').read_bytes())
assert record['index'] == 2762 and record['journal_id'] == '30fa18c869b34fd496a2758a4a28e197'
assert record['sha256'] == digest({key:value for key,value in record.items() if key != 'sha256'})
state = record['document']['state']
assert state['sha256'] == digest(state['state'])
identifier = 'parent:inbox:910c908bf27745289ac7155581abedf0'
results = []
for retained in (None, identifier):
    history = TrainHistory.from_json(json.dumps(state['state']['history']))
    stream = ContinualStream(history, context_limit=6144, segment_tokens=512, segments_per_sleep=3,
        deadline_unix=9999999999, model_state_sha256='f'*64)
    stream.presentation = state['state'].get('presentation')
    parent = next(event for event in history.events if event.event_id == identifier)
    receipts = []
    rendered = stream.compact_for_prompt(count, lambda kind, document: receipts.append((kind, document)),
        threshold=4608, protected_from=record['document']['protected_from'], retained_parent_event_id=retained)
    compact = next(document for kind, document in receipts if kind == 'COMPACTION')
    results.append(dict(retained=retained is not None, before_tokens=compact['before_tokens'],
        after_tokens=rendered.token_count, through_event_count=compact['through_event_count'],
        parent_verbatim_count=sum(parent.text in message['content'] for message in rendered.messages),
        all_history_masked=all(label == -100 for label in rendered.labels), threshold=4608,
        context_limit=6144, generation_cap=512))
print(json.dumps(dict(observed_utc=datetime.now(timezone.utc).isoformat(),
    source_record_index=2762, source_record_sha256=record['sha256'],
    parent_event_id=identifier, parent_source_sha256=parent.source_sha256, results=results,
    scope='CPU_TOKENIZER_COUNTERFACTUAL_NOT_NATIVE_ADOPTION',
    native_signals=0, live_writes=0, model_generations=0,
    tokenizer_file_sha256={name:hashlib.sha256((Path(model)/name).read_bytes()).hexdigest()
        for name in ('tokenizer.json','tokenizer_config.json')},
    fork_sha256={name:hashlib.sha256(text.encode()).hexdigest() for name,text in MODULES.items()})))
'''
    command = ['bash', str(REPOSITORY / 'gpu/ovx4_ssh.sh'),
        "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false /localhome/local-rohing/v2/venv/bin/python -B -"]
    result = subprocess.run(command, input=code, text=True, capture_output=True, timeout=75)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    document = json.loads(result.stdout)
    (OWN / 'ACTUAL_BUDGET_REPLAY.json').write_text(json.dumps(document, indent=2) + '\n')
    print(json.dumps(document, indent=2))


if __name__ == '__main__':
    main()
