"""Preserve R209 receipts, stop only its exact units, and dispatch tested R210 states."""

import datetime
import json
import os
from pathlib import Path
import subprocess
import time

from ddp_pilot import require, sha, write


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'


def systemctl(*arguments):
    return subprocess.check_output(['sudo','-n','systemctl',*arguments],text=True,timeout=40).strip()


def main():
    require(os.uname().nodename=='[REDACTED_HOST]','exact_assigned_training_host')
    os.umask(0o077)
    prepared = []
    for rank in [8,16]:
        root=Path(f'/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank{rank}_20260918_continuation1')
        config=json.loads((root/'PILOT_CONFIG.json').read_bytes())
        cpu=json.loads((root/'RECEIVING_CPU.json').read_bytes())
        require(cpu['passed'] and cpu['config_sha256']==sha(root/'PILOT_CONFIG.json'),'tested_exact_receiving_config')
        for name,expected in config['source_pin'].items():
            require(sha(root/name)==expected,'preserved_exact_sources_and_resume_state')
        prior=Path(config['prior_root']);old=json.loads((prior/'PILOT_CONFIG.json').read_bytes())
        unit=old['unit_prefix']+'pilot.service'
        pid=int(systemctl('show',unit,'--property=MainPID','--value'))
        arguments=(Path('/proc')/str(pid)/'cmdline').read_bytes().decode().split('\0')
        require(str(prior) in arguments and str(prior/'ddp_pilot.py') in arguments,'only_exact_prior_training_owner')
        group=systemctl('show',unit,'--property=ControlGroup','--value')
        require(group.startswith('/system.slice/') and unit in group,'exact_prior_systemd_group')
        prepared.append((rank,root,config,prior,unit,pid,group))
    for rank,root,config,prior,unit,pid,group in prepared:
        write(root/'TRANSITION_INTENT.json',dict(started_unix=time.time(),prior_unit=unit,prior_main_pid=pid,
            directive='R210_CROSSED_SCENE_NEGATIVE_CONTINUATION',resume_step=config['resume_step'],
            old_complete_checkpoint_preserved=True,old_unsaved_suffix_will_be_explicitly_discarded=True))
        diagnostic='orch-r209-rank'+str(rank)+'-diagnostics.service'
        diagnostic_pid=int(systemctl('show',diagnostic,'--property=MainPID','--value') or 0)
        if diagnostic_pid:
            diagnostic_args=(Path('/proc')/str(diagnostic_pid)/'cmdline').read_bytes().decode().split('\0')
            require(str(prior) in diagnostic_args and 'watch' in diagnostic_args,'only_prior_candidate_diagnostic_watcher')
            systemctl('stop',diagnostic)
        systemctl('kill','--signal=SIGSTOP','--kill-whom=all',unit)
        deadline=time.monotonic()+10
        identities=[]
        while time.monotonic()<deadline:
            pids=[int(value) for value in (Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_text().split()]
            identities=[]
            for member in pids:
                fields=(Path('/proc')/str(member)/'stat').read_text().rsplit(')',1)[1].split()
                identities.append(dict(pid=member,state=fields[0],start_ticks=fields[19]))
            if len(identities)>=5 and all(item['state'] in ['T','t'] for item in identities):
                break
            time.sleep(.1)
        require(len(identities)>=5 and all(item['state'] in ['T','t'] for item in identities),'all_prior_rank_processes_frozen_before_receipt')
        progress_paths=sorted((prior/'training').glob('PROGRESS_*.json'))
        parsed=[];partial=[]
        for path in progress_paths[-2:]:
            try:parsed.append(json.loads(path.read_bytes()))
            except json.JSONDecodeError:partial.append(path.name)
        require(parsed,'documented_old_progress_exists')
        last=parsed[-1];completed=last['completed_updates'];resume=config['resume_step']
        frozen=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_unit=unit,
            prior_main_pid=pid,processes=identities,last_complete_progress=last,partial_progress_files=partial,
            source_checkpoint=str(prior/'training/pilot_checkpoint'),resume_step=resume,
            first_new_mix_step=resume+1,discarded_documented_updates=completed-resume,
            discarded_documented_pair_draws=(completed-resume)*64,
            additional_unlogged_completed_updates_bounds=[0,10],additional_inflight_work_possible=True,
            exact_discarded_suffix_count_unknown_due_to_prior_ten_step_logging=True,
            no_weights_or_optimizer_reset=True,original_phase_files_retained=True)
        write(root/'R209_FROZEN_SUFFIX.json',frozen)
        systemctl('kill','--signal=SIGKILL','--kill-whom=all',unit)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            alive=[]
            for identity in identities:
                path=Path('/proc')/str(identity['pid'])/'stat'
                if path.exists() and path.read_text().rsplit(')',1)[1].split()[0] not in ['Z','X']:
                    alive.append(identity['pid'])
            if not alive:break
            time.sleep(.2)
        require(not alive,'all_exact_prior_training_owners_stopped')
        write(root/'R210_TRANSITION.json',dict(frozen,old_owner_stopped=True,stopped_unix=time.time(),
            transition_reason='EXPLICIT_R210_RECIPE_CHANGE_OLD_WRITER_HAS_NO_ON_DEMAND_FULL_CHECKPOINT',
            planned_stop_not_scientific_failure=True,checkpoint_manifest_sha256=config['checkpoint_manifest_sha256'],
            declared_crossed_fraction=0.25,declared_within_fraction=0.75))
        print(json.dumps(dict(rank=rank,status='PRIOR_STOPPED_EXACT_CHECKPOINT_RETAINED',resume_step=resume,
            discarded_documented_updates=completed-resume,additional_unlogged_completed_updates_bounds=[0,10])),flush=True)
    for rank,root,config,prior,unit,pid,group in prepared:
        with (root/'OUTER.log').open('x') as log:
            process=subprocess.Popen([PYTHON,'-B',str(root/'four_gpu_admission.py'),'dispatch','--root',str(root)],
                cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(root/'DISPATCHED.json',dict(dispatched_unix=time.time(),supervisor_pid=process.pid,status='DISPATCHED_NOT_LOADED',no_automatic_retry=True))
        print(json.dumps(dict(rank=rank,status='R210_DISPATCHED_NOT_LOADED',supervisor_pid=process.pid)),flush=True)


if __name__ == '__main__':
    main()
