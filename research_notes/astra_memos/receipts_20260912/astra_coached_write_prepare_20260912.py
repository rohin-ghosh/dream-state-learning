import json
from pathlib import Path
from organism_v6.parent_note_replay_write import prepare_write

home = Path.home()
replay = home / 'astra_diagnostics/astra_coached_note_replay_20260912_attempt1'
output = home / 'astra_diagnostics/astra_coached_note_write_20260912_attempt1'
output.mkdir()
(output / 'adapters').mkdir()
(output / 'logs').mkdir()
report = prepare_write(replay, output / 'preparation', adapter_dirs={arm: output / 'adapters' / arm for arm in ('lesson', 'sham')}, trainer_logs={arm: output / 'logs' / (arm + '.log') for arm in ('lesson', 'sham')})
print(json.dumps(report, sort_keys=True))
