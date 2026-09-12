import json
from pathlib import Path

from organism_v6 import citation_sleep_diagnostic as diagnostic

home = Path.home()
source_run = home / 'astra_diagnostics/astra_demonstration_20260912_attempt1'
source_preparation = home / 'astra_diagnostics/astra_demonstration_preparation_20260912_attempt1'
out = home / 'astra_diagnostics/astra_citation_sleep_preparation_20260912_attempt1'
config = diagnostic.read(source_preparation / 'config.json')
result = diagnostic.prepare(out, source_run, source_preparation,
                            config['model_path'], config['expected_files'])
assert result['status'] == 'READY'
check = diagnostic.read(out / 'preflight.json')
result.update(status='NATIVE_CITATION_SLEEP_PREPARATION_PASS',
              source=str(Path(diagnostic.__file__).resolve().parents[1]),
              selected_raw_sha256=diagnostic.TARGET_SHA,
              prefix_sha256=check['prefix_sha256'],
              input_tokens=check['proof']['full']['input_tokens'],
              eos_appended=check['eos_appended'],
              protocol=diagnostic.PROTOCOL,
              model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
print(json.dumps(result, sort_keys=True))
