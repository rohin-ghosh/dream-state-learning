"""Render metadata evidence and append it without rewriting COORDINATION."""

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def checkpoint_list(values):
    return ','.join(map(str, values)) if values else 'none'


def render(report, blockers, coverage_path, blockers_path):
    observed = datetime.fromtimestamp(report['observed_unix'], ZoneInfo('America/Los_Angeles'))
    cutoff = datetime.fromtimestamp(report['last_full_job_admission_before_unix'], ZoneInfo('America/Los_Angeles'))
    failures = {entry['life_id']: entry for node in blockers['nodes'] for entry in node['failures']}
    lines = ['', '## R159 evaluation coverage — R167 metadata only — ' + observed.strftime('%Y-%m-%d %H:%M:%S PDT'), '',
        '**Fresh receiving-node snapshot, not the earlier07:25 provisional. No responses, object/condition scores, or qualitative/aggregate retention outcomes are included.**', '',
        '**(a) What has actually been measured, per child:** The table records actual completed three-question checkpoint/condition jobs only. Each completed job makes one independent original-birth-only call to each of the object-continuation, work-method, and attention-choice prompts. These are answer-based instruments, not demonstrated perception/behavior improvement. Initial checkpoint0 is a baseline, not post-sleep persistence evidence; execution or copy counts do not establish retention. No private outcome is released to Main/active parents.', '',
        f"Current totals: {report['completed_jobs']} completed condition jobs / {report['completed_calls']} completed calls; {report['matched_completed_checkpoints']} matched completed checkpoints; {report['completed_future_sleep_jobs']} completed forward-sleep jobs. {report['charged_calls']}/504 calls and {report['charged_calls']*512}/258,048 generation tokens charged. {report['receiving_checkpoints']} receiving-verified checkpoint copies.", '',
        '**Scope is21 declared identities,19 source-admitted registrations—not all22 deployed.** C5 and repo_reader have no accepted frontier registration. The requested22nd identity has no entry in this immutable registry; no identity is invented, aliased, added, or funded here. A historical source registration does not prove that its learner is still live now. This observation verifies evaluator liveness, not the current learner/parent roster.', '',
        'Checkpoint numbers below are the predeclared target set, not a newly observed learner frontier. Receiving copies/completions/current jobs are fresh observations. Every completed condition-checkpoint contributes3 calls; every completed-call count also determines equal per-prompt execution counts. Future indices present in the copy column are still queued unless explicitly listed as completed.', '',
        '| Life | Fixed checkpoints | Verified receiving copies | ON completed checkpoints / calls | OFF completed checkpoints / calls | Current work / explicit missingness |',
        '|---|---|---|---|---|---|']
    for row in report['lives']:
        notes = []
        if not row['registered']:
            notes.append('not source-admitted: '+str(row['hold']))
        if row['life_id'] in failures:
            notes.append('source stopped: '+failures[row['life_id']]['error_class']+'; no retry/extension')
        for missing in row['permanent_missing']:
            notes.append(f"{missing['condition']} checkpoint{missing['sleep']}: {missing['reason']}")
        for active in row['current']:
            state = 'native identity live' if active['native_live'] else 'entered/pending; native live not proven'
            notes.append(f"{active['condition']} checkpoint{active['sleep']}: {state}")
        if row['missing_captures']:
            notes.append('not captured: '+checkpoint_list(row['missing_captures']))
        if row['registered']:
            pending = {condition: [sleep for sleep in row['fixed_checkpoints']
                if sleep not in row['complete'][condition]] for condition in ('LORA_ON', 'LORA_OFF')}
            if any(pending.values()):
                notes.append('remaining fixed cells pending/missing, not scored')
        lines.append('| '+row['life_id']+' | '+checkpoint_list(row['fixed_checkpoints'])+' | '
            +checkpoint_list(row['receiving_checkpoints'])+' | '
            +checkpoint_list(row['complete']['LORA_ON'])+' / '+str(row['completed_calls']['LORA_ON'])+' | '
            +checkpoint_list(row['complete']['LORA_OFF'])+' / '+str(row['completed_calls']['LORA_OFF'])+' | '
            +'; '.join(notes)+' |')
    lines.extend(['', '**(b) Forward schedule and actual gates:** This is initial plus the next THREE completed sleeps frozen from each admitted life\'s honest registration frontier. It is not indefinite every-sleep coverage and not retrospective backfill of all sleeps. Each condition queue is initial-first across eligible lives; then first selected future sleep across lives, then second, then third. Missing peers do not block independent eligible cells; consumed refused/failed/uncertain cells are never retried.', ''])
    for controller in report['controllers']:
        identity = controller['identity']
        lines.append(f"- {controller['role']} controller PID{identity['pid']}/start_ticks{identity['start_ticks']}: exact identity live={controller['live']}; frozen runtime/controller source verified={controller['actual_controller_source_verified']}.")
    for current in report['current_jobs']:
        identity = current['native_identity']
        identity_text = f"PID{identity['pid']}/start_ticks{identity['start_ticks']}" if identity else 'no native identity receipt yet'
        lines.append(f"- Current physical{current['physical']}: {current['life_id']} checkpoint{current['sleep']} {current['condition']}; {identity_text}; native live={current['native_live']}.")
    for condition in ('LORA_ON', 'LORA_OFF'):
        next_cells = report['next_eligible'][condition]
        following = f"{next_cells[0]['life_id']} checkpoint{next_cells[0]['sleep']}" if next_cells else 'none currently eligible'
        lines.append(f"- {condition}: {report['eligible_unattempted_initial'][condition]} initial jobs still unattempted beyond current work; next eligible candidate is {following}. This is queue order, not a GPU-admission promise.")
    lines.extend(['',
        'Forward-sleep calls can begin on each slot only after its remaining initial queue clears, prior native/timeout/wrapper identities naturally release, the exact copied-cell CPU/provenance/source bindings validate, and a fresh unchanged strict device scan passes. A copied checkpoint alone is not GPU admission; future scans have not been predeclared green while a current job occupies the device. No extrapolated all-life wall-clock completion promise is made.',
        'The actual frozen runtimes require a900-second job plus15-second margin. A new full job must be admitted strictly before '+cutoff.strftime('%H:%M:%S PDT')+' (15:14:45 UTC), and all model work remains inside **September17 08:30 PDT /15:30 UTC**. The same aggregate504-call/258,048-token ceilings and source-read caps remain in force. There is no authorized22-child every-sleep rollout or automatic extension past this wall. Uncaptured/unfinished cells remain explicit missing, not negative.', '',
        '**Private scientific interpretation for Rohin only:** `/localhome/local-rohing/orch_r167_object_survival_20260917/private_appendices/retention_report_20260917_generation1/REPORT.private.md`. This is the separate retrospective report, not a scored per-life fleet report. Main/parents/repo_reader must not open it. Safe readiness, hashes, controls/coverage limitations and release rule: `research_loop/workers/r167_object_survival/RETENTION_REPORT_READY_20260917.md`. The rule forbids qualitative/aggregate success feedback to parenting; no such result is supplied here.', '',
        '**(c) Retelling/replay timing remains Main/Ampere-owned.** This evaluator adds no claim that the4-dose intervention executed or that retelling entered training. No notebook text grants extra evaluator calls, retries, or budget.', '',
        'Evidence: `'+str(coverage_path)+'`; source missingness `'+str(blockers_path)+'`; runtime/job/identity paths are recorded there. Existing bounded fleet controllers and minute-by-minute operational monitor are unchanged. This subsection is appended at the notebook END; no top-section edit or source/parent/model action.', ''])
    return '\n'.join(lines).encode()


def append_once(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        identity = os.fstat(descriptor)
        if (os.stat(path).st_dev, os.stat(path).st_ino) != (identity.st_dev, identity.st_ino):
            raise RuntimeError('coordination_replaced_before_append')
        if os.write(descriptor, raw) != len(raw):
            raise RuntimeError('partial_append_preserved_no_automatic_retry')
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    current = path.read_bytes()
    if current.count(raw) != 1:
        raise RuntimeError('append_not_uniquely_verified_preserve_payload')
    start = current.index(raw)
    return dict(start_line=current[:start].count(b'\n')+1,
        end_line=current[:start+len(raw)].count(b'\n'), bytes_appended=len(raw),
        payload_sha256=hashlib.sha256(raw).hexdigest(), append_only=True, verified_unix=time.time())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--coverage', type=Path, required=True)
    parser.add_argument('--blockers', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.coverage.read_bytes())
    blockers = json.loads(args.blockers.read_bytes())
    if report['status'] != 'R159_SAFE_PER_LIFE_R167_EXECUTION_COVERAGE' or report['score_or_response_content_read']:
        raise ValueError('metadata_projection_required')
    raw = render(report, blockers, args.coverage, args.blockers)
    destination = HERE / 'fleet_generation2' / ('R159_COORDINATION_PAYLOAD_'+str(time.time_ns())+'.md')
    with destination.open('xb') as stream:
        stream.write(raw)
    receipt = append_once(REPO / 'research_loop/COORDINATION.md', raw)
    receipt.update(status='R159_COVERAGE_APPENDED_AT_END', payload=str(destination), coverage=str(args.coverage),
        blockers=str(args.blockers), provider_calls=0, model_calls=0)
    receipt_path = destination.with_suffix('.RECEIPT.json')
    with receipt_path.open('x') as stream:
        json.dump(receipt, stream, sort_keys=True)
    print(json.dumps(dict(receipt, receipt_path=str(receipt_path)), sort_keys=True))


if __name__ == '__main__':
    main()
