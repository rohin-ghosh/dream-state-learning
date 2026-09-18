"""Assemble one fresh birth with actual CPU/source/lease references, no launch."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write,digest,require


ROOT=Path(__file__).resolve().parent
REMOTE=Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
DEVICE='GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'


def prepare():
    discovered=json.loads((ROOT/'DISCOVERY_2.json').read_bytes())
    build=json.loads((ROOT/'SOURCE_BUILD.json').read_bytes())
    source=ROOT/'runtime_source'
    require(discovered['lease_gpu_uuid']==DEVICE and discovered['model_exists'] and discovered['anchors_exists'],'actual_receiving_dependencies')
    command=[sys.executable,'-B','-m','unittest','tests.test_orch_r125_stream_journal',
        'tests.test_orch_r125_continual_native','tests.test_orch_r125_continual_stream',
        'tests.test_orch_r127_pilot_console',
        'research_loop.workers.rohin183_repo_learning_20260917.test_runtime','-q']
    result=subprocess.run(command,cwd=source,env=dict(os.environ,TMPDIR='/tmp',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=write(ROOT/('AUTHOR_NATIVE_CPU_'+str(time.time_ns())+'.log'),result.stdout.encode())
    require(result.returncode==0,'author_native_CPU_failed')
    cpu=write(ROOT/'AUTHOR_CPU.json',dict(passed=True,observed_unix=time.time(),exit_code=result.returncode,
        command=command,log=log,source_pins=build['source_pins'],GPU_model_calls=0,provenance=build))
    sys.path.insert(0,str(source))
    from gpu import orch_r125_continual_native as native
    from organism_v6.orch_r125_plain_context import VERSION
    hard_end=min(int(time.time())+21600,discovered['lease']['hard_end_unix'])
    startup=(source/'STARTUP.md').read_bytes()
    plan=dict(schema=native.SCHEMA,base_sha256=native.BASE_SHA256,source_root=str(REMOTE/'source'),root=str(REMOTE/'life'),
        startup_context=dict(version='R127_STARTUP_V1',path=str(REMOTE/'source/STARTUP.md'),sha256=digest(startup)),
        birth_prompt=startup.decode(),system_prompt=native.SYSTEM,seed=0,presleep_variant='free_distillation',
        compaction_invitation=native.COMPACTION_INVITATION,presentation_version=VERSION,
        new_presentations=16,rehearsal_presentations=0,anchor_lambda=0.25,segment_tokens=512,segments_per_sleep=2,
        context_limit=16384,max_sleeps=None,physical=2,gpu_uuid=DEVICE,hard_end_unix=hard_end,
        lease_end_unix=discovered['lease']['lease_end_unix'],model_dir=discovered['model_dir'],anchors=discovered['anchors'],
        decoder=dict(temperature=0.7,top_p=0.95,repetition_penalty=1.05,no_repeat_ngram_size=16))
    package=ROOT/'control_bundle'
    plan_ref=write(package/'control/PLAN.json',plan)
    lease=dict(discovered['lease'],original_bound_lease_path=discovered['lease']['path'],
        original_bound_lease_sha256=discovered['lease']['sha256'],experiment_hard_end_unix=hard_end,
        machine_lease_changed=False)
    lease_ref=write(package/'LEASE.json',lease)
    write(package/'AUTHOR_CPU.json',(ROOT/'AUTHOR_CPU.json').read_bytes())
    allocation=dict(schema='R125_NATIVE_ALLOCATION_V1',builder_entry='R183 own CPU/source/safe visibility gate',
        builder_entry_logged=True,builder_entry_pushed=False,cpu_tests_passed=True,
        cpu_receipt_path=str(REMOTE/'AUTHOR_CPU.json'),cpu_receipt_sha256=cpu['sha256'],
        declared_unix=time.time(),gpu_uuid=DEVICE,physical=2,plan_sha256=plan_ref['sha256'])
    allocation_ref=write(package/'control/ALLOCATION.json',allocation)
    config=dict(schema='R125_CONTINUAL_GUARD_V1',allocation_path=str(REMOTE/'control/ALLOCATION.json'),
        allocation_sha256=allocation_ref['sha256'],attempt_dir=str(REMOTE/'control'),hard_end_unix=hard_end,
        host_sha256=discovered['host_sha256'],lease_path=str(REMOTE/'LEASE.json'),lease_sha256=lease_ref['sha256'],
        next_reserved_unix=lease['lease_end_unix'],plan_path=str(REMOTE/'control/PLAN.json'),plan_sha256=plan_ref['sha256'],
        resume=False,source_pins=build['source_pins'])
    config_ref=write(package/'control/GUARD.json',config)
    write(package/'TOOLS.json',dict(schema='R183_REPO_TOOLS_V1',root=str(REMOTE/'life'),workspace=str(REMOTE/'workspace'),
        snapshot=str(REMOTE/'snapshot'),snapshot_manifest=dict(path=str(REMOTE/'SNAPSHOT_MANIFEST.json'),
        sha256=digest((ROOT/'SNAPSHOT_MANIFEST.json').read_bytes())),receipts=str(REMOTE/'tool_receipts'),hard_end_unix=hard_end))
    write(package/'SOURCE_BUILD.json',(ROOT/'SOURCE_BUILD.json').read_bytes())
    write(package/'receiving.py',(ROOT/'receiving.py').read_bytes())
    with tarfile.open(ROOT/'RUNTIME_PACKAGE.tar.gz','x:gz') as archive:
        archive.add(source,arcname='source')
        for path in sorted(package.rglob('*')):
            if path.is_file():
                archive.add(path,arcname=str(path.relative_to(package)),recursive=False)
    return write(ROOT/'PREPARED.json',dict(remote=str(REMOTE),plan_sha256=plan_ref['sha256'],guard_sha256=config_ref['sha256'],
        source=build,hard_end_unix=hard_end,CPU=cpu,launch_attempted=False,protected_carry_implemented=False))


if __name__=='__main__':
    print(json.dumps(prepare(),sort_keys=True))
