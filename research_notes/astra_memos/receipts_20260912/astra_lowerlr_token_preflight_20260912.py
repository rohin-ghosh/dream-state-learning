import json
import math
from pathlib import Path
from transformers import AutoTokenizer
from organism_v6 import memory_dose as memory

home = Path.home()
root = home / 'astra_diagnostics/astra_lowerlr_baseline_inputs_20260912'
corpus = json.loads((root / 'corpora/bank0/F_r16k16/across/sleep4/corpus.json').read_text())
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', local_files_only=True)
encoded = [memory.encode_item(tokenizer, item) for item in corpus['corpus']]
result = dict(items=len(encoded), steps=3 * math.ceil(len(encoded) / 4), input_tokens=3 * sum(len(row['input_ids']) for row in encoded), supervised_tokens=3 * sum(sum(token != -100 for token in row['labels'][1:]) for row in encoded), straddles=sum(row['n_straddle'] for row in encoded), truncated=sum(row['truncated'] for row in encoded), tokenizer=type(tokenizer).__name__, inference=False, training=False)
assert result['items'] == 12924 and result['steps'] == 9693
assert result['input_tokens'] == 749985 and result['supervised_tokens'] == 711213
assert result['straddles'] == result['truncated'] == 0
for rate in ('3e5', '1e5'):
    output = home / ('astra_diagnostics/astra_A1_lowerlr_bank0_ts2_' + rate + '_20260912_attempt1/provenance/token_preflight.json')
    with output.open('x') as target:
        json.dump(result, target, sort_keys=True, indent=2)
print(json.dumps(result, sort_keys=True))
