import collections
import json
from pathlib import Path
from transformers import AutoTokenizer
from organism_v6 import memory_dose as memory

root = Path.home() / 'astra_diagnostics/astra_lowerlr_baseline_inputs_20260912'
corpus = json.loads((root / 'corpora/bank0/F_r16k16/across/sleep4/corpus.json').read_text())
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', local_files_only=True)
counts = collections.Counter()
examples = []
spans = collections.Counter()
for item in corpus['corpus']:
    before = memory.encode_item(tokenizer, item)
    changed = dict(item, mask_context=item['kind'] in ('fact', 'lesson'))
    after = memory.encode_item(tokenizer, changed)
    assert before['input_ids'] == after['input_ids']
    counts['items'] += 1
    counts['input_tokens'] += len(after['input_ids'])
    counts['new_supervised'] += sum(label != -100 for label in after['labels'][1:])
    counts['old_supervised'] += sum(label != -100 for label in before['labels'][1:])
    counts['changed_label_items'] += before['labels'] != after['labels']
    counts['straddles'] += after['n_straddle']
    counts['truncations'] += after['truncated']
    if after['n_straddle']:
        full = item['context'] + item['target']
        cut = len(item['context'])
        offsets = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)['offset_mapping']
        for start, end in offsets:
            if start < cut < end:
                spans[(full[start:cut], full[cut:end])] += 1
                if len(examples) < 3:
                    examples.append(dict(kind=item['kind'], full=full, cut=cut,
                                         crossing_token=full[start:end], target_prefix=full[cut:end]))
result = dict(counts=dict(counts), boundary_spans=[dict(context_tail=key[0], target_prefix=key[1], count=value)
              for key, value in spans.items()], examples=examples, model_inference=False)
print(json.dumps(result, indent=2, sort_keys=True))
