"""Read-only parent exposure monitoring with compact, attributed notebook updates."""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from gpu.orch_r133_programme_parent import boundary_coverage, remote, write
from gpu.orch_r137_parent_exposure import publications_from_results


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parent_alive(output):
    started = json.loads((Path(output)/'STARTED.json').read_text())
    try:
        command = Path('/proc', str(started['pid']), 'cmdline').read_bytes().split(b'\0')
    except FileNotFoundError:
        return False
    return b'gpu.orch_r133_programme_parent' in command and str(output).encode() in command


def sample(item, config):
    path, output = Path(item['parent_config']), Path(item['parent_output'])
    parent = json.loads(path.read_text())
    publications = publications_from_results(output, programme=parent['programme'], branch=parent['branch'])
    script = ('import json,hashlib; from pathlib import Path; '
        'from gpu.orch_r137_parent_exposure import snapshot; '
        'assert hashlib.sha256(Path(' + repr(config['remote_source']+'/CPU_AND_SOURCE.json')
        + ').read_bytes()).hexdigest()==' + repr(config['remote_source_receipt_sha256']) + '; '
        'state=snapshot(' + repr(parent['root']) + ',publications=' + repr(publications) + '); '
        'state.pop("events");state.pop("latest_request");print(json.dumps(state))')
    state = remote(config['repository'], dict(parent, source_root=config['remote_source']), script)
    if state['coverage_basis'] != 'verified_parent_REQUEST_exposure_not_registration':
        raise ValueError('verified_exposure_required')
    coverage = boundary_coverage(state, parent.get('start_after_response_count', 0))
    coverage['coverage_basis'] = state['coverage_basis']
    statuses = {}
    for result in output.glob('parent_*/RESULT.json'):
        status = json.loads(result.read_text())['status']
        statuses[status] = statuses.get(status, 0) + 1
    started = json.loads((output/'STARTED.json').read_text())
    return dict(branch=parent['branch'], parent_output=str(output), parent_alive=parent_alive(output),
        observed_unix=time.time(), parent_started_unix=started['started_unix'],
        parent_config_sha256=sha(path), coverage=coverage, call_statuses=statuses,
        request_count=state['request_count'], response_count=state['response_count'],
        verified_exposures=len(state['parent_exposures']), record_count=state['record_count'],
        head_sha256=state['head_sha256'], exposure_scope=state['attribution_scope'],
        snapshot_state=state)


def status_text(rows, observed_unix):
    stamp = datetime.fromtimestamp(observed_unix, ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %I:%M:%S %p %Z')
    lines = ['\n## [Builder — R137 exposure monitor] ' + stamp,
             'Measured rendered-REQUEST exposure, not INBOX registration or provider publication.']
    for row in rows:
        if 'error' in row:
            lines.append('- ' + row['branch'] + ': audit ERROR; no coverage claim. ' + row['error'])
            continue
        coverage = row['coverage']
        elapsed = (observed_unix-row['parent_started_unix'])/60
        lines.append('- ' + row['branch'] + ': parent_alive=' + str(row['parent_alive'])
            + ', elapsed_minutes=' + str(round(elapsed, 1))
            + ', verified_covered/closed=' + str(coverage['covered_boundaries']) + '/'
            + str(coverage['closed_boundaries']) + ', missing=' + str(coverage['missing_boundaries'])
            + ', responses=' + str(row['response_count']) + ', calls=' + json.dumps(row['call_statuses'], sort_keys=True) + '.')
    lines.append('Elapsed wall time alone is not proof of a sustained successful hour; inspect the complete coverage history.\n')
    return '\n'.join(lines)


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    if config.get('schema') != 'R137_PARENT_MONITOR_V1' or not 10 <= config['interval_seconds'] <= 300:
        raise ValueError('bounded_monitor_configuration')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), config_sha256=sha(config_path)))
    last_notebook = 0
    while time.time() < config['stop_after_unix']:
        rows = []
        for item in config['items']:
            try:
                rows.append(sample(item, config))
            except Exception as error:
                rows.append(dict(branch=item['label'], error=type(error).__name__, observed_unix=time.time()))
        observed = time.time()
        receipt = output/('AUDIT_' + str(time.time_ns()) + '.json')
        write(receipt, dict(observed_unix=observed, rows=rows))
        if observed-last_notebook >= 1800:
            text = status_text(rows, observed)
            text += 'Audit receipt: `' + str(receipt) + '`, SHA256 `' + sha(receipt) + '`.\n'
            descriptor = os.open(config['notebook'], os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC)
            try:
                raw = text.encode()
                if os.write(descriptor, raw) != len(raw):
                    raise OSError('short_notebook_append')
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            last_notebook = observed
        time.sleep(min(config['interval_seconds'], max(0, config['stop_after_unix']-time.time())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.config, arguments.output)
