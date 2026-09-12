import hashlib
import json
from pathlib import Path
from gpu.prepare_memory_seed_run import prepare_run

home = Path.home()
source = home / 'astra_sources/52e0e4db0d67d54defa4151cb091ccc925cd9e8c'
baseline = home / 'astra_diagnostics/astra_lowerlr_baseline_inputs_20260912'
expected = {
    'manifest.json': 'b2d82e650c51f9c453f7978a56840eade533f253e732b6c897c43b690ccaf35f',
    'distractor.json': '4ad56576f6d0a9ae211207ab06daef767ccca6a3968c7d9542505406137a9fdc',
    'banks/bank0.json': '87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31',
    'banks/bank1.json': 'b63d649fa16a2b921c694e88a379fa01b174d5c101111c0ddaaf26e9c098e362',
    'banks/bank2.json': 'a4ca0376a7cba887d2f571083ec5f4b0aa36b8fa366c1060fb01579a803a76e4',
    'corpora/bank0/F_r16k16/across/sleep4/corpus.json': 'f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d',
    'seed_run_receipt.json': '2939b7812d36f59d571659d02c2088fb727d87a59965b5cae13bef39d27dfc3d',
    'adapters/bank0/F_r16k16/across/sleep4/r8/train_meta.json': 'b046eb082ec8bc488d202e94fc1a09108e35b00d32a45bf2464534a8b5e3493c',
    'eval/bank0__F_r16k16__across__sleep4__r8__lam1.json': '970e1be480133cb81d62b53e9762bd4ef77b5c0b1d11e3a85d21b7e3dab64386',
}
for name, digest in expected.items():
    assert hashlib.sha256((baseline / name).read_bytes()).hexdigest() == digest, name
for name, digest in {'organism_v6/memory_dose.py': 'ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3', 'gpu/prepare_memory_seed_run.py': '1f216a2ca7392f47cb2067121350606dc227beb8ee887a2d794169bf2cf24d9e'}.items():
    assert hashlib.sha256((source / name).read_bytes()).hexdigest() == digest, name
results = []
for rate in ('3e5', '1e5'):
    output = home / ('astra_diagnostics/astra_A1_lowerlr_bank0_ts2_' + rate + '_20260912_attempt1')
    receipt = prepare_run(baseline, output, 2, 'F_r16k16', banks=[0])
    (output / 'logs').mkdir()
    (output / 'provenance').mkdir()
    provenance = dict(baseline_root=str(baseline), baseline_hashes=expected, source_commit=source.name, baseline_node=2, execution_node=3, learning_rate=float('3e-5' if rate == '3e5' else '1e-5'), historical_lr=1e-4, original_source_commit='f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d', original_native_evaluator_unchanged=True, historical_baseline_not_retrained=True, training_seed=2, source_bank_seed=1, no_new_material=True, clean_lineage=False)
    with (output / 'provenance/comparison.json').open('x') as target:
        json.dump(provenance, target, sort_keys=True, indent=2)
    results.append(dict(output=str(output), preparation=receipt, comparison=provenance))
print(json.dumps(results, sort_keys=True))
