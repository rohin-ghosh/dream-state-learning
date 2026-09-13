import json
from pathlib import Path
import sys
import time

SOURCE = Path('/localhome/local-rohing/astra_sources/q0_readout_supplement_20260913_attempt1')
sys.path.insert(0, str(SOURCE))
from gpu import astra_q0_readout_supplement as supplement

assert supplement.q0.file_hash(SOURCE / 'gpu/astra_q0_readout_supplement.py') == '6c0e40d242f6903fab53b303112c4f2e25afde62c696be02ee80a5c8ebd4ad08'
assert supplement.q0.file_hash(SOURCE / 'tests/test_astra_q0_readout_supplement.py') == '109d9fb67004b4b8bdabe319acf4b7c54d625f36a31c1947e8a430fe2738dccc'
original = Path('/localhome/local-rohing/astra_diagnostics/q0_fulldose_R1_20260913_attempt1')
custody = Path('/tmp/astra_q0_R1_tar_verification_20260913.json')
assert supplement.q0.file_hash(custody) == '9e32dbc7f40778af0a6338a563a4b9c149ef5a8d987408ce2a971e6001a462f3'
assert json.loads(custody.read_bytes())['status'] == 'PASS_CUSTODY'
config = supplement.read_json(original / 'manifest.json')['config']
config.update(builder_preflight_reference='Main21CPU tests PASS40.771s; preserved R1 full-root17567-file custody matches independent Fable digest; separate single-readout supplement',
              approved_intake='Rohin standing authorization/simple hygiene; separately versioned saved-checkpoint diagnostic, no original primary replacement')
root = Path('/localhome/local-rohing/astra_diagnostics/q0_R1_readout_supplement_20260913_attempt1')
started = time.time()
plan = supplement.prepare(root, original, custody, supplement.q0.file_hash(custody), config,
                          seal_sha256='d3a7fa5b18b74821955d06c5e4b28c88fd92586479fbd6d284e6c2ba8885ab87',
                          finalized_sha256='ec1c4212ff93b5bfb4b20963a83dfc61c9ffa731944968b6f77568762d5e3eb0', joined=True)
receipt = dict(status='PREPARED_SUPPLEMENT_NOT_LAUNCHED', root=str(root), source=str(SOURCE),
               manifest_sha256=supplement.q0.file_hash(root / 'manifest.json'), prepared_sha256=supplement.q0.file_hash(root / 'PREPARED.json'),
               source_pins=plan['source_pins'], original_primary_label=plan['admission']['original_primary_label'],
               original_adapter=plan['admission']['adapter'], elapsed_seconds=time.time() - started)
supplement.q0.write_once(Path('/tmp'), 'astra_q0_supplement_prepared_20260913_attempt1.json', receipt)
print(json.dumps({key: value for key, value in receipt.items() if key not in ('source_pins', 'original_adapter')}, sort_keys=True))
