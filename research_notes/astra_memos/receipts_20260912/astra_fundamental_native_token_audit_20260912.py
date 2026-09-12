import hashlib
import json
from pathlib import Path

from transformers import AutoTokenizer
from organism_v6 import fundamental_teaching_corpus as corpus

model = Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
candidate = corpus.build_candidate()
sources = {row['id']: row for row in candidate['source_records']}
variants = []
selected = None
for label in corpus.RESULT_LABEL_VARIANTS:
    rows = []
    for teach, control in zip(candidate['train_teach'], candidate['train_control']):
        assert teach['case_id'] == control['case_id'] and teach['context'] == control['context']
        response = control['response']
        if teach['kind'] == 'addition':
            event = sources[teach['source_event_ids'][0]]
            response = corpus.arithmetic_response(event['left'], event['right'], 'control', label)
        teach_ids = tokenizer.encode(teach['response'], add_special_tokens=False)
        control_ids = tokenizer.encode(response, add_special_tokens=False)
        rendered = tokenizer.apply_chat_template([dict(role='user', content=teach['context'])],
            tokenize=False, add_generation_prompt=True)
        rows.append(dict(case_id=teach['case_id'], context_tokens=len(tokenizer.encode(rendered, add_special_tokens=False)),
            teach_target_tokens=len(teach_ids) + 1, control_target_tokens=len(control_ids) + 1))
    matched = all(row['teach_target_tokens'] == row['control_target_tokens'] for row in rows)
    variants.append(dict(label=label, all_rows_matched=matched, rows=rows))
    if selected is None and matched:
        selected = label
output = Path.home() / 'astra_diagnostics/astra_fundamental_native_tokens_20260912_attempt1'
output.mkdir()
result = dict(status='TOKEN_MATCHED_FULL_ENCODER_AUDIT_PENDING' if selected else 'NO_PREDECLARED_TOKEN_MATCH',
    selected_label=selected, variants=variants, model=str(model), model_calls=0, fitting=False,
    source_sha256=hashlib.sha256(Path(corpus.__file__).read_bytes()).hexdigest(),
    tokenizer_files={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in model.iterdir() if path.is_file() and path.suffix in ('.json', '.txt')},
    no_model_or_outcome_selection=True, synthetic_eos_tokens_per_row=1)
with (output / 'native_audit.json').open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
print(json.dumps(dict(root=str(output), status=result['status'], selected_label=selected,
    variants=[dict(label=row['label'], all_rows_matched=row['all_rows_matched'],
        total_teach=sum(item['teach_target_tokens'] for item in row['rows']),
        total_control=sum(item['control_target_tokens'] for item in row['rows'])) for row in variants]), sort_keys=True))
