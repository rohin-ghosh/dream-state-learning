#!/usr/bin/env bash
set -euo pipefail
test ! -e /tmp/astra_correction_utility_terminal_20260912.tgz
bash gpu/ovx2_ssh.sh 'env PYTHONPATH="$HOME/astra_sources/e5c78cc8f0bd9b669a11ffac68b698fb4aac7142" CUDA_VISIBLE_DEVICES="" "$HOME/v2/venv/bin/python" -B -' <<'PY'
import datetime,json
from pathlib import Path
from gpu import astra_correction_utility_diagnostic as runner
from gpu.astra_mini_sudoku_diagnostic import check_free,write_new
from organism_v6.neutral_pair_custody import validate_pair
root=Path.home()/'astra_diagnostics/astra_correction_utility_20260912_attempt1'
material=root/'preparation'
report,panel=runner.inspect_preparation(material,Path('/tmp/astra_correction_utility_panel_20260912.json'))
receipts=[]
for seed in [0,1,2]:
    for arm in ['whole_raw','act_only']:
        out=root/'recipient_logs'/arm/f'seed{seed}'
        launch=runner.read(root/'launch_logs'/arm/f'seed{seed}'/'launch.json')
        complete=runner.read(out/'COMPLETED.json')
        assert not (out/'FAILED.json').exists() and not Path(f"/proc/{launch['pid']}").exists()
        commands=runner.read(material/arm/'training_commands.json')['commands']
        command=next(item for item in commands if item['seed']==seed)
        adapter=Path(command['output'])
        manifest,hashes=runner.verify_fit(adapter,command,runner.read(material/arm/'tokenizer_preflight.json'))
        assert hashes==complete['adapter_sha256']
        done=runner.read(out/'probes/pair/PAIR_DONE.json')
        receipt=validate_pair(out/'probes/pair',done['spec_sha256'],done['workers'],done['source_snapshot'])
        assert receipt==done['receipt_sha256']
        for path in out.rglob('*.cleanup.json'):
            cleanup=runner.read(path)
            assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
        gpu,xml=check_free(launch['device'])
        receipts.append(dict(arm=arm,seed=seed,device=launch['device'],pid=launch['pid'],controller_absent=True,
            native_pair_receipt=receipt,adapter_hashes=hashes,gpu=gpu,xml=xml,released=True))
write_new(root/'MAIN_TERMINAL_AUDIT.json',dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),recipients=receipts))
print(json.dumps(dict(status='SIX_NATIVE_PAIRS_AND_RELEASE_PASS',recipients=len(receipts))))
PY
bash gpu/ovx2_ssh.sh 'bash -se' <<'REMOTE'
set -euo pipefail
test ! -e /tmp/astra_correction_utility_terminal_20260912.tgz
tar --exclude='*.safetensors' --exclude='*.bin' --exclude='*/source_capsule' -czf /tmp/astra_correction_utility_terminal_20260912.tgz -C "$HOME/astra_diagnostics" astra_correction_utility_20260912_attempt1
sha256sum /tmp/astra_correction_utility_terminal_20260912.tgz
REMOTE
bash gpu/ovx2_scp.sh NODE:/tmp/astra_correction_utility_terminal_20260912.tgz /tmp/
sha256sum /tmp/astra_correction_utility_terminal_20260912.tgz
mkdir /tmp/astra_correction_utility_terminal_20260912
tar -xzf /tmp/astra_correction_utility_terminal_20260912.tgz -C /tmp/astra_correction_utility_terminal_20260912
