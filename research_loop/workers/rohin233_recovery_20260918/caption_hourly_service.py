"""Lease-bounded, single-owner adopted-epoch reporting and aggregate-only publication."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from judge_epoch_report import collect_fleet, counters


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DESTINATION = REPO/'research_loop/workers/rohin221_continuous_caption_20260918'
sys.path.insert(0,str(DESTINATION))
from publish_hourly import git, privacy_scan


def encoded(document):
    return (json.dumps(document,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def save(path,document):
    temporary=path.with_suffix(path.suffix+'.next')
    with temporary.open('wb') as output:
        output.write(encoded(document))
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def project(audit,source):
    players=[]
    for role in audit['roles']:
        for player in role.get('players',[]):
            players.append(dict(player=player['player'],judge_epoch_sha256=player['epoch_sha256'],
                cumulative=player['totals'],UTC_hours=player['hours'],
                parsed_captions=None,format_faults=None,no_caption_acts=None,generated_tokens=None))
    return dict(schema='R233_ADOPTED_EPOCH_HOURLY_V1',observed_cut_utc=audit['observed_utc'],
        primary_judge=dict(rank=8,step=15625,top_k=50),players=players,
        errors=[dict(role=role['role'],status=role['status']) for role in audit['roles'] if 'players' not in role],
        source_receipt=source,private_caption_payload_included=False,private_panels_included=False,
        old_and_new_epochs_combined=False,scoring_calls_made=0,historical_resubmissions=0,
        definitions=dict(attempts='Distinct ACT origins reaching the scorer, not all native cycles.',
            accepted='Distinct exact strings per scene/player scored accepted in this epoch; cached history excluded.',
            new_pixels='New per-scene novelty clusters recorded by the game; not independently verified joke ideas.',
            missing='Parsed totals, format faults, no-caption ACTs and generated tokens are absent from this epoch ledger; null is unknown, never zero.',
            hours='Absolute UTC counts, partial current hour, no extrapolation. Historical pre-adoption hours are not reconstructed here.'))


def markdown(document):
    lines=['# Hourly caption counts — adopted judge', '', 'Cut: '+document['observed_cut_utc'],
        '', 'Judge: rank8 / step15625 / top50. Each row retains its own epoch; no pre/post mixing.',
        'Attempts are ACT origins reaching the scorer. Acceptance is not certified humor. Current hour is partial.',
        '', '| UTC hour | Player | Epoch | Attempts | Distinct scored | Accepted | New pixels | Accept rate |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for player in document['players']:
        for hour,bucket in sorted(player['UTC_hours'].items()):
            rate=bucket['distinct_accept_rate']
            values=[hour,player['player'],player['judge_epoch_sha256'][:12],bucket['act_origins'],
                bucket['distinct_scored'],bucket['distinct_accepted'],bucket['distinct_new_pixels'],
                f'{rate:.1%}' if rate is not None else 'n/a']
            lines.append('| '+' | '.join(map(str,values))+' |')
    for error in document['errors']:
        lines.append('\n'+error['role']+': '+error['status']+'; no zero counts substituted.')
    lines.extend(['','Parsed counts / format faults / no-caption ACTs / generated tokens: not recorded by this ledger.',
        'Zero activity is not proof of uptime. Retrospective rescoring and inherited cached scores are not new outcomes.',
        'Source receipt: `'+document['source_receipt']['path']+'`'])
    return '\n'.join(lines)+'\n'


def publish(paths,worktree):
    if git(worktree,'status','--porcelain').stdout.strip():
        raise ValueError('hourly_publication_worktree_must_be_clean')
    git(worktree,'fetch','origin','main')
    git(worktree,'rebase','origin/main')
    relative=[]
    for path in paths:
        content=path.read_bytes()
        if path.is_symlink() or len(content)>2_000_000:
            raise ValueError('bounded_regular_aggregate_only')
        privacy_scan(content.decode())
        target=path.relative_to(REPO)
        if not (target.parts[:3]==('research_loop','workers','rohin221_continuous_caption_20260918')
                or target.parts[:3]==('research_loop','workers','rohin233_recovery_20260918')):
            raise ValueError('explicit_hourly_worker_scope')
        output=worktree/target
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(content)
        relative.append(str(target))
    git(worktree,'add','--',*relative)
    if not git(worktree,'diff','--cached','--quiet',check=False).returncode:
        return None
    git(worktree,'diff','--cached','--check')
    git(worktree,'commit','-m','Publish source-bound adopted-judge hourly caption counts')
    for attempt in range(3):
        result=git(worktree,'push','origin','HEAD:main',check=False)
        if result.returncode==0:
            return git(worktree,'rev-parse','HEAD').stdout.decode().strip()
        git(worktree,'fetch','origin','main')
        git(worktree,'rebase','origin/main')
    raise ValueError('hourly_push_not_confirmed')


def once(worktree=None):
    audit_path=collect_fleet()
    audit=json.loads(audit_path.read_bytes())
    stamp=datetime.fromisoformat(audit['observed_utc']).strftime('%Y%m%dT%H%M%SZ')
    source=dict(path=str(audit_path.relative_to(REPO)),sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest())
    document=project(audit,source)
    json_path=DESTINATION/('R227_HOURLY_'+stamp+'.json')
    text_path=json_path.with_suffix('.md')
    save(json_path,document)
    text_path.write_text(markdown(document))
    fleet_path=DESTINATION/('R227_FLEET_SOURCE_'+stamp+'.json')
    save(fleet_path,dict(schema='R233_HOURLY_FLEET_SOURCE_V1',observed_cut_utc=audit['observed_utc'],
        source_receipt=source,reader_sha256=audit['reader_sha256'],
        sources=[dict(role=role['role'],process=role.get('process'),config_sha256=role.get('config_sha256'),
            status='ACTUAL_SCORER_IDENTITY_VERIFIED' if 'players' in role else role['status'],
            epochs=[dict(player=player['player'],epoch_sha256=player['epoch_sha256'])
                for player in role.get('players',[])]) for role in audit['roles']],
        learner_liveness_inferred=False,GPU_work=0))
    latest=DESTINATION/'R227_HOURLY_LATEST.json'
    receipt=dict(published_utc=datetime.now(timezone.utc).isoformat(),json=str(json_path.relative_to(REPO)),
        markdown=str(text_path.relative_to(REPO)),sha256=hashlib.sha256(json_path.read_bytes()).hexdigest(),
        fleet_source=str(fleet_path.relative_to(REPO)),epoch_separated=True,pid=os.getpid())
    save(latest,receipt)
    paths=[audit_path,audit_path.with_suffix('.md'),json_path,text_path,fleet_path,latest]
    commit=publish(paths,worktree) if worktree else None
    return dict(receipt,git_commit=commit,collection_errors=document['errors'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--until-unix',type=float,required=True)
    parser.add_argument('--worktree',type=Path)
    arguments=parser.parse_args()
    if not time.time()<arguments.until_unix<=1790791200:
        raise ValueError('within_existing_latest_fleet_lease')
    with (HERE/'CAPTION_HOURLY.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fields=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()
        save(HERE/'CAPTION_HOURLY_STARTED.json',dict(pid=os.getpid(),start_ticks=fields[19],
            started_utc=datetime.now(timezone.utc).isoformat(),until_unix=arguments.until_unix,
            cadence='Immediate and each UTC hour; read failures retry after 60 seconds.',
            replaced_expired_schedule='R227 until 2026-09-18T14:09:07.497640Z',
            every_remote_read_obeys_its_own_source_cutoff=True,native_signals=[]))
        while time.time()<arguments.until_unix:
            try:
                result=once(arguments.worktree)
                save(HERE/'CAPTION_HOURLY_LAST_SUCCESS.json',result)
                print(json.dumps(result),flush=True)
                next_run=(int(time.time()//3600)+1)*3600
            except Exception as error:
                result=dict(observed_utc=datetime.now(timezone.utc).isoformat(),
                    error_type=type(error).__name__,error=str(error)[:200],success_claimed=False)
                save(HERE/'CAPTION_HOURLY_LAST_ERROR.json',result)
                print(json.dumps(result),flush=True)
                next_run=time.time()+60
            save(HERE/'CAPTION_HOURLY_HEARTBEAT.json',dict(pid=os.getpid(),observed_unix=time.time(),
                next_run_unix=min(next_run,arguments.until_unix)))
            time.sleep(max(0,min(next_run,arguments.until_unix)-time.time()))


if __name__=='__main__':
    main()
