from collections import Counter
import json
from pathlib import Path
import re

root = Path('/tmp/astra_fundamental_followup_terminal_20260912')
rep = root / 'astra_fundamental_replications_20260912_attempt1'
memory = root / 'astra_fundamental_memory_trainprompt_20260912_attempt1'
seed0 = Path('/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1')
primary = {}
for seed, location in ((0, seed0), (1, rep / 'seed1'), (2, rep / 'seed2')):
    for arm in ('teach', 'control'):
        result = json.loads((location / 'readouts' / arm / 'reduction.json').read_text())
        assert result['complete'] and result['native_token_text_audit']
        primary[str(seed) + '_' + arm] = dict(counts=result['counts'],
            memory_answers=dict(Counter(row['raw_text'] for row in result['rows'] if row['kind'] == 'memory_recall')))
diagnostic = {}
for cell in ('OFF', 'teach', 'control'):
    result = json.loads((memory / cell / 'reduction.json').read_text())
    assert result['label'] == 'IN_SAMPLE_TRAINING_PROMPT_DIAGNOSTIC_NOT_HELDOUT'
    diagnostic[cell] = dict(counts=result['counts'], cost=result['cost'], supervised_seconds=result['reserved_seconds'])
fit_release = json.loads((rep / 'fit_main_release.json').read_text())
read_release = json.loads((rep / 'readout_main_release.json').read_text())
seed0_analysis = json.loads(Path('/tmp/astra_fundamental_seed0_main_analysis_20260912.json').read_text())
total_seconds = seed0_analysis['supervised_fit_plus_readout_seconds'] + fit_release['supervised_seconds'] + read_release['totals']['supervised_readout_seconds'] + sum(row['supervised_seconds'] for row in diagnostic.values())
summary = dict(primary=primary, shared_off=dict(addition_correct=32, adherence=0, memory_correct=0, memory_invalid=16),
    seed0_training_prompt_diagnostic=diagnostic, replication_cost=read_release['totals'],
    replication_fit_supervised_seconds=fit_release['supervised_seconds'],
    cumulative_supervised_seconds=total_seconds, cumulative_supervised_A40_minutes=total_seconds/60,
    remaining_initial_90_A40_minutes=90-total_seconds/60, confirmation_requests=0,
    limits='Shared development cases across three trainer seeds; no confirmation, parenting, conditional intelligence or reliable memory-binding claim.')
destination = Path('/tmp/astra_fundamental_followups_main_analysis_20260912.json')
with destination.open('x') as output:
    json.dump(summary, output, indent=2, sort_keys=True)
pattern = re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,}|ipp2-ovx-|a4u8g-')
flagged = [str(path.relative_to(root)) for path in root.rglob('*') if path.is_file() and pattern.search(path.read_bytes())]
assert not flagged, flagged
print(json.dumps(dict(primary=primary, cumulative_supervised_seconds=total_seconds,
    cumulative_supervised_A40_minutes=total_seconds/60, bounded_scan_flagged_files=flagged), indent=2))
