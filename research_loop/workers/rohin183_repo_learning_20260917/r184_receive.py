"""Saved41 copy assembly and focused CPU gate, followed by existing strict launch."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    with Path(path).open('x') as output:
        json.dump(value,output,sort_keys=True)


def main():
    root=Path(__file__).resolve().parent
    source=root/'source'
    sys.path.insert(0,str(source))
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r125_cpu_experiment import digest,verify_gate
    physical=int(sys.argv[1]); label='explicit' if physical==3 else 'brief'
    device={3:'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733',4:'GPU-d304a15c-516a-16a0-a926-a560304077cc'}[physical]
    stage=Path('/localhome/local-rohing/orch_r153_r184_staging_20260917')
    packet=stage/'orch_r184_C2_sleep41_1789684294308387719'
    cached=stage/'orch_r181_node5_c2_1789683406847361492'
    assert sha(packet/'PRESERVATION_RECEIPT.json')=='cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e'
    receipt=json.loads((packet/'PRESERVATION_RECEIPT.json').read_bytes())
    raw=root/'raw'
    shutil.copytree(packet,raw)
    (raw/'stream/inbox').mkdir()
    (raw/'stream/WRITER.lock').touch(exist_ok=False)
    for path in (stage/'registered_inbox').iterdir():
        shutil.copy2(path,raw/'stream/inbox'/path.name)
    for name,expected in receipt['checkpoint_files'].items():
        assert sha(raw/'checkpoints/sleep_000041'/name)==expected
    saved=json.loads((raw/'SAVED_STATE.json').read_bytes())
    assert saved['sha256']==receipt['saved_state_sha256'] and saved['state']['pending'] is None
    assert saved['state']['sleep_frontier']==len(saved['state']['rows'])
    assert len(list((raw/'stream/records').glob('[0-9]'*20+'.json')))==5129
    plan=json.loads((cached/'PLAN.json').read_bytes())
    logical=Path(plan['root'])
    logical.mkdir(parents=True,exist_ok=True)
    (source/'context').mkdir(exist_ok=True)
    shutil.copy2(cached/'source/context/R153_STARTUP.md',source/'context/R153_STARTUP.md')
    plan.update(source_root=str(source),physical=physical,gpu_uuid=device,rehearsal_presentations=0)
    plan['startup_context']['path']=str(source/'context/R153_STARTUP.md')
    plan['hard_end_unix']=saved['state']['deadline_unix']
    plan['think_act_learn']=dict(schema='R184_THINK_ACT_LEARN_V1',trial_id='C2_'+label+'_v1',reflection_policy=label,
        think_segments=1,cpu_gate_root='/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2242z/gate',
        cpu_gate_sha256='5241727deccc099cdf93d6bde213d44df2ae52ba4b6b73103d10abbb5bfc0a89')
    gate=plan['think_act_learn']
    assert digest(verify_gate(gate['cpu_gate_root']))==gate['cpu_gate_sha256']
    command=[sys.executable,'-B','-m','unittest','tests.test_orch_r184_think_act_learn','-q']
    result=subprocess.run(command,cwd=source,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',TMPDIR='/tmp',PYTHONPATH=str(source)),timeout=40)
    (root/'CPU.log').write_text(result.stdout)
    assert result.returncode==0,result.stdout[-1500:]
    pins={str(path.relative_to(source)):sha(path) for path in source.rglob('*.py')}
    declared=json.loads((root/'SOURCE.json').read_bytes())['source_pins']
    assert pins==declared
    cpu=dict(passed=True,source_pins=pins,observed_unix=time.time(),log_sha256=sha(root/'CPU.log'),
        original_packet_sha256=sha(packet/'PRESERVATION_RECEIPT.json'),no_suffix42=True,complete_episode_encoder_integrated=False)
    write(root/'CPU.json',cpu)
    control=root/'control';control.mkdir()
    write(control/'RECEIVING_CPU.json',cpu)
    write(control/'PLAN.json',plan)
    write(root/'LEASE.json',dict(hard_end_unix=plan['hard_end_unix'],lease_end_unix=plan['lease_end_unix'],
        existing_node2_original='/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json',
        existing_node2_original_sha256='621e1391285bcad9ee075106b4afab28970616b663876dc4ebeba7834e7b81e3',machine_lease_changed=False))
    original=Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
    assert sha(original)=='621e1391285bcad9ee075106b4afab28970616b663876dc4ebeba7834e7b81e3'
    assert plan['hard_end_unix']<=json.loads(original.read_bytes())['hard_deadline_unix']
    write(control/'ALLOCATION.json',dict(plan_sha256=sha(control/'PLAN.json'),cpu_tests_passed=True,
        gpu_uuid=device,physical=physical,builder_entry_logged=True,cpu_receipt_path=str(root/'CPU.json'),
        cpu_receipt_sha256=sha(root/'CPU.json'),declared_unix=time.time()))
    import socket
    config=dict(schema='R125_CONTINUAL_GUARD_V1',source_pins=pins,resume=True,copy_raw=str(raw),
        plan_path=str(control/'PLAN.json'),plan_sha256=sha(control/'PLAN.json'),attempt_dir=str(control),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),hard_end_unix=plan['hard_end_unix'],
        lease_path=str(root/'LEASE.json'),lease_sha256=sha(root/'LEASE.json'),next_reserved_unix=plan['lease_end_unix'],
        allocation_path=str(control/'ALLOCATION.json'),allocation_sha256=sha(control/'ALLOCATION.json'))
    write(control/'GUARD.json',config)
    guard.validate(control/'GUARD.json')
    journal=json.loads((raw/'stream/JOURNAL.json').read_bytes())
    bridge=dict(raw_root=str(raw),journal_id=journal['journal_id'],socket='/tmp/r184_c2_'+label+'_1.sock',
        gate_root=gate['cpu_gate_root'],gate_sha256=gate['cpu_gate_sha256'],stop_unix=min(time.time()+7200,plan['hard_end_unix']))
    write(root/'BRIDGE.json',bridge)
    processes={}
    for name,argv in (('cpu_bridge',[sys.executable,'-B','-m','gpu.r184_cpu_bridge','--config',str(root/'BRIDGE.json')]),
        ('supervisor',[sys.executable,'-B','-m','gpu.r184_node2_confinement','dispatch','--config',str(control/'GUARD.json')])):
        with (root/(name+'.log')).open('x') as log:
            process=subprocess.Popen(argv,cwd=source,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        ticks=Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
        processes[name]=dict(pid=process.pid,startticks=ticks)
    started=dict(started_unix=time.time(),physical=physical,gpu_uuid=device,source_root=str(source),raw_root=str(raw),logical_root=str(logical),
        guard_sha256=sha(control/'GUARD.json'),source_pins=pins,processes=processes,complete_episode_encoder_integrated=False)
    write(root/'STARTED.json',started)
    print(json.dumps({key:value for key,value in started.items() if key!='source_pins'},sort_keys=True))


if __name__=='__main__':
    main()
