"""Package the existing R209 release plus node1-owned receiver adaptations."""

import ast
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]
BASE = '/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET'
BUNDLE = REPO/'research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201/R209_FLEET_BUNDLE'
ARCHIVE_SHA = 'ccd62dbb0483240c23ac5caddc23cf5e7ee4a54b45e6896e49267f5f2efd60ec'
ARMS = {2: 'r203_math_comm_b2', 3: 'r203_repo_evidence_c3', 4: 'r203_creative_structured_a4',
        5: 'r203_math_self_derive_c5', 7: 'creative_b1'}


def adapted_driver(released, private):
    old = ast.parse(private)
    method = next(node for node in ast.walk(old) if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    branch = method.body[0]
    assert isinstance(branch, ast.If)
    branch_text = ''.join(private.splitlines(keepends=True)[branch.lineno-1:branch.end_lineno])
    marker = '    def _cpu(self, origin):\n'
    assert released.count(marker) == 1
    result = released.replace(marker, marker+branch_text, 1)
    marker = '    def _generate_stage(self, stage, *, incoming, extra=\'\', think_remaining=1, console_events=()):\n'
    assert result.count(marker) == 1
    result = result.replace(marker, marker+'        from gpu.r210_inbox import think_incoming\n'
                            '        incoming = think_incoming(incoming, stage)\n', 1)
    tree = ast.parse(result)
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    method.body.pop(0)
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == '_generate_stage')
    del method.body[:2]
    assert ast.dump(tree) == ast.dump(ast.parse(released)), 'no_other_shared_runtime_delta'
    return result


def main():
    assert hashlib.sha256((BUNDLE/'runtime_overlay.tar.gz').read_bytes()).hexdigest() == ARCHIVE_SHA
    ready = json.loads((BUNDLE/'READY.json').read_bytes())
    ready_sha = hashlib.sha256((BUNDLE/'READY.json').read_bytes()).hexdigest()
    with tarfile.open(BUNDLE/'runtime_overlay.tar.gz') as archive:
        released = archive.extractfile('gpu/orch_r184_think_act_learn.py').read()
    assert hashlib.sha256(released).hexdigest() == ready['files']['gpu/orch_r184_think_act_learn.py']
    private = (OWN/'r206_receiving/gpu/orch_r184_think_act_learn.py').read_text()
    files = {'gpu/orch_r184_think_act_learn.py': adapted_driver(released.decode(), private).encode(),
             'gpu/r184_cpu_bridge.py': (OWN/'r206_receiving/gpu/r184_cpu_bridge.py').read_bytes(),
             'gpu/r210_inbox.py': (OWN/'r210_inbox.py').read_bytes()}
    output = OWN/'R210_PACKAGE'
    output.mkdir(mode=0o700)
    with tarfile.open(output/'RECEIVING_ADAPTER.tar', 'w') as archive:
        for name, payload in files.items():
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            archive.addfile(member, io.BytesIO(payload))
    (output/'ADAPTER_FILES.json').write_text(json.dumps({name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()}, sort_keys=True))
    with tarfile.open(output/'DELIVERY.tar', 'w') as archive:
        for name in ('r210_phase.py', 'continue_r204.py', 'r203_receive.py'):
            archive.add(OWN/name, arcname=name)
        for name in ('READY.json', 'runtime_overlay.tar.gz'):
            archive.add(BUNDLE/name, arcname=name)
        for name in ('ADAPTER_FILES.json', 'RECEIVING_ADAPTER.tar'):
            archive.add(output/name, arcname=name)
    for physical, name in ARMS.items():
        root = BASE+'/'+name+'_r210'
        request = dict(old_root=BASE+'/'+name, old_control=BASE+'/'+name+'_r204/control',
                       phase='R210_PARENTED_ENRICHMENT', max_sleeps=69, ready_sha256=ready_sha,
                       group=[2, 3, 4] if physical in (2, 3, 4) else [5, 7])
        (output/f'REQUEST_{physical}.json').write_text(json.dumps(request, sort_keys=True))
        command = 'umask 077; mkdir '+shlex.quote(root)+' && tar -xf - -C '+shlex.quote(root)
        with (output/'DELIVERY.tar').open('rb') as incoming:
            subprocess.run(['bash', 'gpu/a100_ssh.sh', command], cwd=REPO, stdin=incoming, check=True, timeout=35)
        subprocess.run(['bash', 'gpu/a100_scp.sh', str(output/f'REQUEST_{physical}.json'), 'NODE:'+root+'/REQUEST.json'],
                       cwd=REPO, check=True, timeout=30)
        command = ('cp '+shlex.quote(BASE+'/'+name+'_r204/receive_creative_b_v3.py')+' '+shlex.quote(root+'/receive_creative_b_v3.py')+
                   '; CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B '+
                   shlex.quote(root+'/r210_phase.py')+' stage')
        result = subprocess.run(['bash', 'gpu/a100_ssh.sh', command], cwd=REPO, capture_output=True, text=True, timeout=80)
        (output/f'STAGE_{physical}.log').write_text(result.stdout+result.stderr)
        print(json.dumps(dict(physical=physical, returncode=result.returncode, stdout=result.stdout.strip())), flush=True)
        if result.returncode:
            raise RuntimeError('receiving_stage_failed_see_owned_log')


if __name__ == '__main__':
    main()
