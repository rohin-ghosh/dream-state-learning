from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tarfile

spec = importlib.util.spec_from_file_location('parity', '/tmp/astra_fundamental_hf_parity_20260912.py')
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)
parity.bind(Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903')
from gpu.astra_mini_sudoku_diagnostic import check_free
root = Path.home() / 'astra_diagnostics/astra_fundamental_hf_parity_20260912_attempt1'
launch = parity.base.read(root / 'launch' / 'launch.json')
assert not (Path('/proc') / str(launch['pid'])).exists()
plan = parity.verify(root)
result = parity.reduce(root)
gpu, xml = check_free('0')
observed = datetime.datetime.now(datetime.timezone.utc)
with (root / 'main_release.xml').open('x') as output:
    output.write(xml)
release = dict(full_release=True, controller_pid=launch['pid'], release_utc=observed.isoformat(),
    device='0', gpu=gpu, full_reservation_seconds=(observed - datetime.datetime.fromisoformat(launch['started_utc'])).total_seconds())
parity.write(root / 'main_release.json', release)
rows = [dict(case_id=saved['case_id'], expected=declared['expected'], hf_top1=saved['top1_text'],
             hf_top1_gold=saved['prefix']['top1_id'] == declared['gold_id'],
             hf_gold_probability=math.exp(saved['prefix']['gold_logprob']),
             gold_minus_vllm_logit=saved['hf_gold_minus_vllm_logit'],
             color_nll=saved['color_nll'], eos_nll=saved['eos_nll'])
        for saved, declared in zip(result['rows'], plan['rows'], strict=True)]
summary = dict(complete=True, original_seed0_teach=True, hf_vllm_top1_agreements=result['hf_vllm_top1_agreements'],
    hf_top1_gold=sum(row['hf_top1_gold'] for row in rows), total=16,
    hf_top1_distribution=dict(Counter(row['hf_top1'] for row in rows)),
    mean_color_nll=sum(row['color_nll'] for row in rows) / 16,
    mean_eos_nll=sum(row['eos_nll'] for row in rows) / 16,
    max_prefix_full_logit_difference=max(row['prefix_full_max_abs_logit_difference'] for row in result['rows']),
    max_hf_reported_loss_difference=max(abs(row['hf_loss_minus_recomputed']) for row in result['rows']),
    reserved_seconds=result['reserved_seconds'], rows=rows, new_vllm_calls=0, optimizer_steps=0)
parity.write(root / 'main_summary.json', summary)
archive = Path('/tmp/astra_fundamental_hf_parity_terminal_20260912.tgz')
files = [path for path in sorted(root.rglob('*')) if path.is_file()]
manifest = {str(path.relative_to(Path.home())): parity.base.digest(path) for path in files}
with tarfile.open(archive, 'x:gz') as output:
    for path in files:
        output.add(path, arcname=str(path.relative_to(Path.home())), recursive=False)
with tarfile.open(archive, 'r:gz') as archived:
    for name, expected in manifest.items():
        assert hashlib.sha256(archived.extractfile(name).read()).hexdigest() == expected
assert manifest == {str(path.relative_to(Path.home())): parity.base.digest(path) for path in files}
validation = dict(archive=str(archive), sha256=parity.base.digest(archive), files=manifest)
parity.write(Path(str(archive) + '.validation.json'), validation)
print(json.dumps(dict(archive=str(archive), sha256=validation['sha256'], files=len(files),
                     release=release, summary=summary), sort_keys=True), flush=True)
