"""Read-only, separately published inactivity supplements; no daemon replacement."""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from research_loop.workers.rohin221_continuous_caption_20260918 import publish_hourly as publication
from research_loop.workers.rohin221_continuous_caption_20260918.hourly_report import save, utc, window_counts


ROOT = Path(__file__).resolve().parent
REMOTE = r'''
import datetime,hashlib,json,pathlib,subprocess,time
original=pathlib.Path('/localhome/local-rohing/orch_r224_continuous_base_20260918')
phase=pathlib.Path('/localhome/local-rohing/orch_r226_base_schedule_20260918')
def read(path): return json.loads(path.read_bytes())
def reference(path): return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mtime_unix=path.stat().st_mtime)
pointer=read(phase/'CURRENT.json')
if pointer['root']!=str(phase/'attempt2') or pointer['scorer_root']!=str(phase/'recovery_scorer'):
 raise ValueError('different_base_epoch_requires_new_binding')
loaded=read(phase/'attempt2/LOADED.json');scorer_loaded=read(phase/'recovery_scorer/LOADED.json')
if loaded['pid']!=48524 or scorer_loaded['pid']!=48502 or pointer['loaded']['pid']!=48524:
 raise ValueError('registered_epoch_pid_changed')
controller=read(original/'player/ATTEMPTS.public.json')
state=read(original/'player/private/state.json')
scorer=read(original/'scorer/SESSION_STATE.private.json')
events=controller['events']
if events!=state['events'] or len({event['source']['request_id'] for event in events})!=len(events):
 raise ValueError('complete_unique_controller_history_required')
if set(scorer['seen'])!={event['source']['request_id'] for event in events}:
 raise ValueError('scorer_controller_seen_prefix_mismatch')
units={}
for role,unit in [('player','orch-r226-base-schedule-recovery-20260918'),('scorer','orch-r226-base-scorer-recovery-20260918')]:
 raw=subprocess.check_output(['systemctl','show',unit,'--property=MainPID,Result,ActiveState,ExecMainStatus,ExecMainStartTimestamp,ExecMainExitTimestamp'],text=True)
 value=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
 exit_time=datetime.datetime.strptime(value['ExecMainExitTimestamp'],'%a %Y-%m-%d %H:%M:%S %Z').replace(tzinfo=datetime.timezone.utc).timestamp()
 units[role]=dict(main_pid=int(value['MainPID']),result=value['Result'],active_state=value['ActiveState'],exit_status=int(value['ExecMainStatus']),exit_unix=exit_time)
plan=read(original/'LAUNCH_PLAN.json')
result=dict(schema='R232_BASE_ACTIVITY_EVIDENCE_V1',observed_unix=time.time(),epoch='R226_recovery_attempt2',
 player_pid=48524,scorer_pid=48502,player_present=pathlib.Path('/proc/48524').exists(),scorer_present=pathlib.Path('/proc/48502').exists(),
 units=units,hard_end_unix=plan['hard_end_unix'],maximum_GPU_hours=plan['maximum_GPU_hours'],
 completed_opportunities=controller['completed_opportunities'],controller_attempts=len(events),
 total_generated_tokens=controller['total_generated_tokens'],controller_pending=state['pending'] is not None,
 controller_stage=state['stage'],controller_event_times=[event['finished_unix'] for event in events],
 scorer_seen_count=len(scorer['seen']),scorer_phase=scorer['phase'],complete_controller_and_scorer_history=True,
 retained_references={name:reference(original/relative) for name,relative in [('launch_plan','LAUNCH_PLAN.json'),('controller_public','player/ATTEMPTS.public.json'),('controller_private','player/private/state.json'),('scorer_private','scorer/SESSION_STATE.private.json')]},
 pointer_sha256=reference(phase/'CURRENT.json')['sha256'],native_or_service_signals=[])
print(json.dumps(result))
'''


def observe():
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=REMOTE,
        text=True, capture_output=True, timeout=25)
    if result.returncode:
        raise ValueError('remote_base_activity_collection_failed')
    return json.loads(result.stdout)


def verified_empty(evidence, start, end):
    if evidence.get('complete_controller_and_scorer_history') is not True:
        return False
    if evidence['observed_unix'] < end or evidence['hard_end_unix'] > start:
        return False
    if evidence['player_present'] or evidence['scorer_present']:
        return False
    if any(unit['main_pid'] != 0 or unit['result'] != 'timeout'
           or unit['exit_unix'] > start for unit in evidence['units'].values()):
        return False
    return not any(start <= moment < end for moment in evidence['controller_event_times'])


def supplement(primary, evidence, primary_sha256):
    cut = datetime.datetime.fromisoformat(primary['observed_cut_utc']).timestamp()
    end = int(cut // 3600) * 3600
    start = end - 3600
    rows = []
    for player in primary['players']:
        matches = [window for window in player['UTC_windows']
            if window['window_start_utc'] == utc(start) and window['window_end_utc'] == utc(end)]
        if len(matches) > 1:
            raise ValueError('duplicate_absolute_window')
        status = 'RECORDED_ACTIVITY' if matches else 'MISSING_NOT_ZERO'
        window = matches[0] if matches else None
        if player['player'] == 'frozen_base_no_optimizer' and verified_empty(evidence, start, end):
            if matches and any(matches[0][field] for field in ('ACT_attempts', 'newly_scored_strings', 'cached_results')):
                raise ValueError('activity_contradicts_inactivity_evidence')
            window = dict(window_counts([], [], start, end, completed=0, planned_unknown=0), partial_UTC_hour=False)
            status = 'VERIFIED_NO_ACTIVITY_EXPIRED_BUDGET'
        rows.append(dict(player=player['player'], status=status, counts=window))
    return dict(schema='R232_HOURLY_ACTIVITY_SUPPLEMENT_V1', observed_cut_utc=primary['observed_cut_utc'],
        created_utc=utc(time.time()), primary_report_sha256=primary_sha256,
        window_start_utc=utc(start), window_end_utc=utc(end), players=rows, base_evidence=evidence,
        missing_is_not_zero=True, raw_counts_unchanged=True, original_reports_modified=False,
        historical_resubmissions=0, scoring_calls=0, native_or_service_signals=[],
        base_continuation='NOT_RELAUNCHED_DECLARED_BUDGET_EXPIRED_REQUIRES_NEW_BOUNDED_ALLOCATION',
        caveat='Accepted strings include repeats and unreviewed commentary; pixels are provisional events, not hourly-rate or H2 claims.')


def markdown(report):
    lines = ['# R232 hourly activity supplement', '',
        f"Original cut: {report['observed_cut_utc']}. UTC window {report['window_start_utc']} to {report['window_end_utc']}.", '',
        '| Player | Activity status | ACT attempts | Parsed | New scored | Accepted | New pixels | Format / routing |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in report['players']:
        counts = row['counts']
        values = [str(counts[field]) for field in ('ACT_attempts', 'parsed_candidate_strings',
            'newly_scored_strings', 'accepted_before_novelty', 'new_pixels')] if counts else ['unknown'] * 5
        faults = f"{counts['format_fault_attempts']} / {counts['routing_ambiguity_attempts']}" if counts else 'unknown'
        lines.append('| ' + ' | '.join([row['player'], row['status'], *values, faults]) + ' |')
    evidence = report['base_evidence']
    if evidence.get('complete_controller_and_scorer_history'):
        lines += ['', f"Registered base player and dedicated scorer exited at {utc(evidence['units']['player']['exit_unix'])}; both systemd results timeout at the declared budget end.",
            f"Retained controller: {evidence['completed_opportunities']} completed opportunities, {evidence['controller_attempts']} attempts, {evidence['total_generated_tokens']} generated tokens; scorer retains {evidence['scorer_seen_count']} seen origins.",
            'Shared native scorers are separate processes; their presence does not establish base-player uptime.',
            'No continuation was launched under the expired allocation. Context, novelty and dedup state are retained; any continuation must bind a new explicit epoch and budget.']
    else:
        lines += ['', 'Activity evidence could not be collected; omitted primary rows remain unknown, never synthetic zeros.']
    return '\n'.join(lines + ['', report['caveat'], 'Original hourly reporter/publisher and all lives remain unchanged.', ''])


def publish(worktree, name, report):
    if not re.fullmatch(r'R232_HOURLY_STATUS_\d{8}T\d{6}Z', name):
        raise ValueError('safe_status_filename_required')
    relative = publication.WORKER / (name + '.json')
    contents = {relative: publication.encode(report), relative.with_suffix('.md'): markdown(report).encode()}
    for content in contents.values():
        publication.privacy_scan(content.decode())
    publication.ensure_clean(worktree)
    publication.git(worktree, 'fetch', 'origin', 'main')
    if publication.git(worktree, 'rev-list', '--count', 'origin/main..HEAD').stdout.strip() != b'0':
        raise ValueError('unpublished_commit_requires_operator_resolution')
    publication.git(worktree, 'checkout', '--detach', 'origin/main')
    existing = {path: publication.remote_file(worktree, 'origin/main', path) for path in contents}
    if any(value is not None for value in existing.values()):
        if existing != contents:
            raise ValueError('immutable_existing_status_conflict')
        return dict(status='already_published', commit=publication.git(worktree, 'log', '-1', '--format=%H', '--', relative).stdout.decode().strip())
    coordination = worktree / publication.COORDINATION
    before = coordination.read_text()
    entry = '\n\n[Builder/Leibniz R232 HOURLY ACTIVITY] ' + utc(time.time()) + ' — cut ' + report['observed_cut_utc'] + '; table `' + relative.with_suffix('.md').as_posix() + '`. Verified inactivity distinguished from missing collection; original counts retained. No life/service controls.\n'
    patch = ['*** Begin Patch']
    for path, content in contents.items():
        patch += ['*** Add File: ' + str(worktree / path)] + ['+' + line for line in content.decode().splitlines()]
    patch += ['*** Update File: ' + str(coordination), '@@']
    patch += [' ' + line for line in before.splitlines()[-3:]] + ['+' + line for line in entry.splitlines()] + ['*** End Patch']
    subprocess.run(['apply_patch', '\n'.join(patch) + '\n'], check=True, capture_output=True)
    expected = {str(path) for path in contents} | {str(publication.COORDINATION)}
    publication.git(worktree, 'add', '--', *sorted(expected))
    if set(publication.git(worktree, 'diff', '--cached', '--name-only').stdout.decode().splitlines()) != expected:
        raise ValueError('status_publication_allowlist_mismatch')
    publication.git(worktree, 'commit', '-m', 'Publish R232 activity status ' + name)
    for attempt in range(3):
        upstream = publication.remote_file(worktree, 'origin/main', publication.COORDINATION)
        after = publication.remote_file(worktree, 'HEAD', publication.COORDINATION)
        if after != upstream + entry.encode():
            raise ValueError('append_only_coordination_required')
        if any(publication.remote_file(worktree, 'HEAD', path) != content for path, content in contents.items()):
            raise ValueError('published_status_bytes_changed')
        if publication.git(worktree, 'push', 'origin', 'HEAD:main', check=False).returncode == 0:
            return dict(status='pushed', commit=publication.git(worktree, 'rev-parse', 'HEAD').stdout.decode().strip(), attempts=attempt + 1)
        publication.git(worktree, 'fetch', 'origin', 'main')
        if publication.git(worktree, 'rebase', 'origin/main', check=False).returncode:
            publication.git(worktree, 'rebase', '--abort')
            return dict(status='skipped_rebase_conflict', preserved_commit=publication.preserve_unpushed(worktree))
    return dict(status='skipped_push_retries', preserved_commit=publication.preserve_unpushed(worktree))


def cycle(worktree, state):
    latest = json.loads((ROOT / 'R227_HOURLY_LATEST.json').read_bytes())
    source = ROOT / Path(latest['json']).name
    stamp = publication.CUT_PATTERN.fullmatch(source.name)
    if not stamp:
        raise ValueError('invalid_primary_cut_name')
    name = 'R232_HOURLY_STATUS_' + stamp[1]
    if name in state:
        print(json.dumps(dict(cut=name, status='already_processed', publication=state[name])), flush=True)
        return
    target = ROOT / (name + '.json')
    if target.exists():
        report = json.loads(target.read_bytes())
    else:
        raw = source.read_bytes()
        primary = publication.normalized_report(json.loads(raw))
        try:
            evidence = observe()
        except Exception:
            evidence = dict(status='COLLECTION_MISSING_NO_ZERO', complete_controller_and_scorer_history=False)
        report = supplement(primary, evidence, hashlib.sha256(raw).hexdigest())
        save(target, publication.encode(report).decode())
        save(target.with_suffix('.md'), markdown(report))
    result = publish(worktree, name, report)
    state[name] = result
    save(ROOT / 'R232_BASE_ACTIVITY_PUBLICATION.json', publication.encode(state).decode())
    print(json.dumps(dict(cut=name, **result)), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worktree', type=Path, required=True)
    parser.add_argument('--until-unix', type=float, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if not 0 < args.until_unix - time.time() <= 14400:
        raise ValueError('bounded_reporting_only_expiry')
    lock = (ROOT / 'R232_BASE_ACTIVITY.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    worktree = publication.ensure_worktree(Path.cwd(), args.worktree)
    state_path = ROOT / 'R232_BASE_ACTIVITY_PUBLICATION.json'
    state = json.loads(state_path.read_bytes()) if state_path.exists() else {}
    save(ROOT / 'R232_BASE_ACTIVITY_STARTED.json', publication.encode(dict(pid=os.getpid(),
        started_utc=utc(time.time()), expires_utc=utc(args.until_unix), poll_seconds=30,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), GPU_work=False,
        replaced_daemons=[], purpose='Additive absolute-window activity proof and safe publication')).decode())
    while time.time() < args.until_unix:
        try:
            cycle(worktree, state)
        except Exception as error:
            print(json.dumps(dict(utc=utc(time.time()), status='SKIPPED_ERROR', error_type=type(error).__name__)), flush=True)
            if args.once:
                raise
        if args.once:
            return
        time.sleep(min(30, max(0, args.until_unix-time.time())))


if __name__ == '__main__':
    main()
