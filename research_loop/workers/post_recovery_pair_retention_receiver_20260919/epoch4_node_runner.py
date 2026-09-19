"""Main-authorized pair staging/CPU transport only; no live management operations."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
BASE = '/localhome/local-rohing/orch_retention_20260919'
LIVES = ('curriculum_learner', 'curriculum_frozen_sibling')


def digest(content):
    return hashlib.sha256(content).hexdigest()


def write_once(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError('existing_local_transport_artifact_mismatch')
        return
    with path.open('xb') as handle:
        handle.write(content)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def observations():
    path = HERE.parent / 'post_recovery_retention_rollout_20260919/ovx4_INVENTORY2.json'
    rows = json.loads(path.read_bytes())['results']
    return {row['life']: {key: value for key, value in row.items() if key != 'files'}
        for row in rows if row['life'] in LIVES}


def archive(checks_name, selected):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as bundle:
        for life in LIVES:
            path = HERE / 'prepared_epoch4_v1' / life / 'epoch4'
            bundle.add(path, arcname=life + '/epoch4')
        bundle.add(HERE / 'operator_bundle_v4', arcname='pair_operator_bundle_v4')
        bundle.add(HERE / 'prepared_epoch4_v1/operator_prefix_producer', arcname='pair_prefix_producer_v4')
        directory = tarfile.TarInfo(checks_name)
        directory.type, directory.mode = tarfile.DIRTYPE, 0o700
        bundle.addfile(directory)
        files = {name: (HERE / name).read_bytes() for name in
            ('remote_epoch4_stage.py', 'node_epoch4_probe.py', 'node_epoch4_driver.py')}
        files['native_view_probe.py'] = (HERE.parent /
            'post_recovery_pair_receiving_checks_20260919/native_view_probe.py').read_bytes()
        files['OBSERVATIONS.json'] = encoded(selected)
        files['CODE_PINS.json'] = encoded({name: digest(content) for name, content in files.items()})
        for name, content in files.items():
            entry = tarfile.TarInfo(checks_name + '/' + name)
            entry.mode, entry.size = 0o444, len(content)
            bundle.addfile(entry, io.BytesIO(content))
    return buffer.getvalue()


def run(output, phase, life=None):
    output = Path(output).absolute()
    if output.resolve() != output or not output.is_relative_to(HERE):
        raise ValueError('own_local_receipts_only')
    configuration = output / 'SESSION.json'
    if configuration.exists():
        session = json.loads(configuration.read_bytes())
    else:
        session = dict(checks_name='pair_epoch4_cpu_20260919_' + str(time.time_ns()), observations=observations(),
            operator_path=BASE + '/pair_operator_bundle_v4', created_utc=datetime.now(timezone.utc).isoformat())
        write_once(configuration, encoded(session))
    command = ['bash', str(REPOSITORY / 'gpu/ovx4_ssh.sh')]
    payload = None
    if phase in ('inspect', 'stage'):
        code = (HERE / 'remote_epoch4_stage.py').read_text()
        request = dict(observations=session['observations'], checks_name=session['checks_name'])
        if phase == 'stage':
            raw = archive(session['checks_name'], session['observations'])
            write_once(output / 'STAGING_ARCHIVE.tar.gz', raw)
            request.update(archive=base64.b64encode(raw).decode(), archive_sha256=digest(raw))
            call = 'stage(request)'
        else:
            call = "dict(status='READ_ONLY_EXACT_NATIVE_INSPECTION', results={life: exact_native(value) for life,value in request['observations'].items()})"
        payload = code + '\nrequest = json.loads(' + repr(json.dumps(request)) + ')\nprint(json.dumps(' + call + ', sort_keys=True))\n'
        command.append('python3 -B -')
    else:
        if life not in LIVES or phase not in ('source-tests', 'select', 'checkpoint', 'produce', 'read', 'native-view'):
            raise ValueError('known_pair_CPU_phase_only')
        command.append('/localhome/local-rohing/v2/venv/bin/python -B ' + BASE + '/' + session['checks_name']
            + '/node_epoch4_driver.py ' + phase + ' ' + life)
    started = time.monotonic()
    process = subprocess.run(command, input=payload, text=True, capture_output=True, timeout=620, check=False)
    result = json.loads(process.stdout) if process.returncode == 0 else None
    receipt = dict(phase=phase, life=life, observed_utc=datetime.now(timezone.utc).isoformat(),
        transport_elapsed_seconds=time.monotonic() - started, returncode=process.returncode,
        result=result, stderr=process.stderr[-4096:], source_pins={name: digest((HERE / name).read_bytes())
            for name in ('remote_epoch4_stage.py', 'node_epoch4_probe.py', 'node_epoch4_driver.py', 'epoch4_node_runner.py')})
    path = output / ((life + '_' if life else '') + phase.upper() + '_' + str(time.time_ns()) + '.json')
    write_once(path, encoded(receipt))
    print(json.dumps(dict(receipt_path=str(path), **receipt), sort_keys=True))
    if process.returncode:
        raise ValueError('remote_CPU_action_refused_see_receipt')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('inspect', 'stage', 'source-tests', 'select', 'checkpoint', 'produce', 'read', 'native-view'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--life', choices=LIVES)
    args = parser.parse_args()
    run(args.output, args.phase, args.life)
