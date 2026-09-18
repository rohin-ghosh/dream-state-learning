"""Observe the fixed C2 pilot without publishing or changing its live state."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONFIG_SHA = 'ee32ad40a7867c378ecd1f3e3b7885739c10a7f0d06f434f5308ba50dfa9ad97'
TRACE_SHA = 'ab44d2a333bdb935844a822c0b83e606024367f1d3a84af23f980cd68d837836'
WRAPPER_SHA = 'e7be79c608da97bcdf218e430ee5151e78636694bd3b1b337dd7f724a92a2b56'
REMOTE_TRACE = '/tmp/orch_r175_c2_trace_20260917/trace.py'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)


def summarize(document, config):
    checkpoint = config['pre_intervention_checkpoint']
    require(document['schema'] == 'R175_PINNED_LESSON_TRACE_V1' and
            document['root'] == config['source_life'] and
            document['journal_id'] == config['source_journal_id'] and
            document['anchor_index'] == checkpoint['sleep_record_index'] and
            document['anchor_sha256'] == checkpoint['sleep_record_sha256'], 'fixed_source_binding')
    require(document['caught_up'] and document['no_writes_to_life'] and
            document['success_claim'] is False, 'complete_readonly_trace')
    exposure = document['first_rendered_guidance']
    responses = document['guided_committed_responses']
    selected = document['first_eligible_completed_sleep']
    require(not exposure or exposure['inbox_id'] ==
            config['already_published_guidance']['rohin_inbox_id'], 'bound_Rohin_exposure')
    require(exposure or (responses == 0 and selected is None), 'no_guidance_no_guided_phase')
    require(selected is None or responses >= config['guided_phase']['minimum_committed_child_responses'],
            'four_committed_responses_before_selection')
    return dict(schema='R172_GUIDED_OBSERVER_STATUS_V1', observed_utc=document['observed_utc'],
                status=document['status'], head_index=document['end_index'],
                head_sha256=document['head_sha256'], first_rendered_guidance=exposure,
                guided_committed_responses=responses, guided_generated_tokens=document['guided_generated_tokens'],
                first_eligible_completed_sleep=selected,
                question_review_due=responses >= 1 and selected is None,
                question_not_automatically_sent=True,
                over_generated_budget=document['guided_generated_tokens'] >
                    config['guided_phase']['maximum_generated_tokens'],
                checkpoint_selection_not_a_success_claim=True, child_writes=0, parent_calls=0,
                fixed_config_sha256=CONFIG_SHA)


def command(config):
    checkpoint = config['pre_intervention_checkpoint']
    arguments = ['python3', REMOTE_TRACE, '--root', config['source_life'],
                 '--journal-id', config['source_journal_id'],
                 '--anchor-index', str(checkpoint['sleep_record_index']),
                 '--anchor-sha256', checkpoint['sleep_record_sha256'],
                 '--inbox-id', config['already_published_guidance']['rohin_inbox_id']]
    verification = shlex.join(['printf', '%s\n', TRACE_SHA + '  ' + REMOTE_TRACE])
    return ['bash', str(REPO / 'gpu/ovx3_ssh.sh'),
            verification + ' | sha256sum -c >/dev/null && ' + shlex.join(arguments)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--interval-seconds', type=int, default=120)
    parser.add_argument('--duration-seconds', type=int, default=14400)
    parser.add_argument('--once', action='store_true')
    arguments = parser.parse_args()
    require(60 <= arguments.interval_seconds <= 600 and
            1 <= arguments.duration_seconds <= 14400, 'bounded_readonly_monitor')
    require(sha(HERE / 'PILOT_CONFIG_V1.json') == CONFIG_SHA and
            sha(REPO / 'gpu/ovx3_ssh.sh') == WRAPPER_SHA, 'pinned_config_and_node_wrapper')
    config = json.loads((HERE / 'PILOT_CONFIG_V1.json').read_text())
    output = Path(arguments.output).resolve()
    require(output.parent == HERE, 'observer_output_only_in_owned_worker_directory')
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    write(output / 'STARTED.json', dict(observed_utc=datetime.now(timezone.utc).isoformat(),
          monitor_sha256=sha(__file__), fixed_config_sha256=CONFIG_SHA, trace_sha256=TRACE_SHA,
          wrapper_sha256=WRAPPER_SHA, duration_seconds=arguments.duration_seconds,
          interval_seconds=arguments.interval_seconds, child_writes=0, parent_calls=0))
    failures, previous = 0, None
    while time.monotonic() - started < arguments.duration_seconds:
        stamp = str(time.time_ns())
        try:
            require(sha(HERE / 'PILOT_CONFIG_V1.json') == CONFIG_SHA and
                    sha(REPO / 'gpu/ovx3_ssh.sh') == WRAPPER_SHA, 'pins_unchanged')
            result = subprocess.run(command(config), capture_output=True, text=True, timeout=45)
            require(result.returncode == 0, 'readonly_node_transport_failed')
            require(len(result.stdout) <= 32 * 1024 * 1024, 'bounded_trace_output')
            document = json.loads(result.stdout)
            status = summarize(document, config)
            write(output / ('STATUS_' + stamp + '.json'), status)
            if document['head_sha256'] != previous:
                write(output / ('TRACE_' + stamp + '.json'), document)
                previous = document['head_sha256']
            failures = 0
            print(json.dumps(status, sort_keys=True), flush=True)
            if status['first_eligible_completed_sleep'] or status['over_generated_budget']:
                break
        except (ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as error:
            failures += 1
            write(output / ('READ_FAILURE_' + stamp + '.json'),
                  dict(error_type=type(error).__name__, consecutive_failures=failures,
                       observed_utc=datetime.now(timezone.utc).isoformat(), child_writes=0))
            if failures >= 3:
                break
        if arguments.once:
            break
        time.sleep(min(arguments.interval_seconds,
                       max(0, arguments.duration_seconds - (time.monotonic() - started))))
    write(output / 'EXIT.json', dict(observed_utc=datetime.now(timezone.utc).isoformat(),
          consecutive_read_failures=failures, child_writes=0, parent_calls=0,
          reason='READONLY_MONITOR_STOPPED_NO_AUTOMATIC_CHILD_ACTION'))


if __name__ == '__main__':
    main()
