"""Owned node2 C2 copy runtime, canonical R184 plus three explicit adapters."""
import json,tarfile
from pathlib import Path
from research_loop.workers.rohin183_repo_learning_20260917.build_source import dependencies,adapt_guard
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write,digest,require

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]


def build():
    files=dependencies(REPO,['gpu/orch_r125_continual_guard.py','gpu/orch_r125_continual_native.py',
        'gpu/orch_r125_continual_readout.py','gpu/orch_r184_think_act_learn.py',
        'research_loop/workers/rohin183_repo_learning_20260917/confinement.py','tests/test_orch_r184_think_act_learn.py'])
    original={name:digest(raw) for name,raw in files.items()}
    native=files['gpu/orch_r125_continual_native.py'].decode()
    branch="            if plan.get('think_act_learn') is not None:\n                from gpu.orch_r184_think_act_learn import run_loop\n                return run_loop(child, stream, journal, anchors, plan, root, plan_path, completed_sleeps)\n"
    require(native.count(branch)==1,'exact_R184_optin')
    native=native.replace(branch,'')
    before='            for readout_cycle in range(completed_sleeps+1):\n'
    require(native.count(before)==1,'exact_historical_readout_loop')
    files['gpu/orch_r125_continual_native.py']=native.replace(before,branch+before).encode()
    driver=files['gpu/orch_r184_think_act_learn.py'].decode()
    begin=driver.index('        from gpu.orch_r153_community_transport import cpu_once',driver.index('    def _cpu('))
    end=driver.index('\n    def act(',begin)
    driver=driver[:begin]+"        from gpu.r184_cpu_bridge import call\n        return call({'bridge_config': str(Path(self.child.plan['source_root']).parent/'BRIDGE.json')}, origin)\n"+driver[end:]
    files['gpu/orch_r184_think_act_learn.py']=driver.encode()
    files['gpu/orch_r125_continual_guard.py']=adapt_guard(files['gpu/orch_r125_continual_guard.py'])
    files['gpu/r184_cpu_bridge.py']=(ROOT/'r184_cpu_bridge.py').read_bytes()
    for physical,device,pci,label in ((3,'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733','0000:57:00.0','explicit'),
        (4,'GPU-d304a15c-516a-16a0-a926-a560304077cc','0000:ce:00.0','brief')):
        changed=dict(files)
        containment=(ROOT/'confinement.py').read_text().replace('GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05',device)
        containment=containment.replace('MINOR=2','MINOR='+str(physical)).replace("MODULE='research_loop.workers.rohin183_repo_learning_20260917.confinement'","MODULE='gpu.r184_node2_confinement'")
        containment=containment.replace('/dev/nvidia2','/dev/nvidia'+str(physical)).replace('0000:56:00.0',pci)
        containment=containment.replace('[0,1,3,4,5,6,7]',str([index for index in range(8) if index!=physical]))
        containment=containment.replace("remaining=int(plan['hard_end_unix']-now-15)","remaining=min(7200,int(plan['hard_end_unix']-now-15))")
        containment=containment.replace("'orch-r183-repo-'","'orch-r184-c2-"+label+"-'")
        containment=containment.replace("require(not Path(plan['root']).exists() and not (attempt/'OUTER_STARTED.json').exists(),'fresh_birth_no_replay')","require(Path(config['copy_raw']).is_dir() and not (attempt/'OUTER_STARTED.json').exists(),'once_only_saved41_copy')")
        containment=containment.replace("devices=['/dev/null rw'","properties['BindPaths']=config['copy_raw']+':'+plan['root']\n    devices=['/dev/null rw'")
        changed['gpu/r184_node2_confinement.py']=containment.encode()
        source=ROOT/('r184_'+label+'_source')
        for name,raw in changed.items():
            write(source/name,raw)
        write(ROOT/('R184_'+label.upper()+'_SOURCE.json'),dict(source_pins={name:digest(raw) for name,raw in changed.items()},original_pins=original,
            deltas=['R184_before_historical_readout_catchup','C2_CPU_executor_external_fixed_origin_bridge','R183_strict_device_policy_parameterized'],
            complete_episode_encoder_integrated=False))
        with tarfile.open(ROOT/('R184_'+label.upper()+'.tar.gz'),'x:gz') as archive:
            archive.add(source,arcname='source')
            archive.add(ROOT/('R184_'+label.upper()+'_SOURCE.json'),arcname='SOURCE.json')
            archive.add(ROOT/'r184_receive.py',arcname='receive.py')


if __name__=='__main__':
    build()
