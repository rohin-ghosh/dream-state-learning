"""One bounded read-only wrapper observation per node; no messages or journal reads."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROSTER = REPO / 'research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json'
NODES = ('a100', 'a40r', 'ovx2', 'ovx3')
SOURCE_NAMES = ('gpu/orch_r127_pilot_console.py', 'gpu/orch_r125_stream_console.py',
    'gpu/orch_r125_stream_journal.py', 'gpu/orch_r125_continual_native.py')


def inspect(request):
    import ast
    import stat

    maximum = 4 * 1024 ** 2
    used = 0
    attempts = 0

    def raw(path, limit):
        nonlocal used, attempts
        attempts += 1
        if attempts > 96 or used + limit > maximum:
            raise ValueError('bounded_read_allowance_exhausted')
        used += limit
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb', buffering=0) as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('regular_metadata_or_source_only')
            value = stream.read(limit)
        if len(value) >= limit:
            raise ValueError('bounded_file_limit')
        return value

    boot = raw('/proc/sys/kernel/random/boot_id', 256).decode().strip()
    cache = {}
    rows = []
    for requested in request['rows']:
        row = dict(requested, observed_unix=time.time(), status='UNVERIFIED')
        try:
            process = Path('/proc') / str(requested['pid'])
            before = raw(process / 'stat', 4096).decode().rsplit(')', 1)[1].split()
            if before[0] in ('Z', 'X') or before[19] != requested['start_ticks']:
                raise ValueError('snapshot_native_identity_not_current')
            argv = raw(process / 'cmdline', 32768).rstrip(b'\0').decode().split('\0')
            if 'native' not in argv or 'gpu.orch_r125_continual_guard' not in argv:
                raise ValueError('unexpected_native_module')
            source = Path(os.readlink(process / 'cwd'))
            if not str(source).startswith('/localhome/local-rohing/orch_'):
                raise ValueError('unexpected_source_root')
            python = argv[0]
            descriptors = list((process / 'fd').iterdir())
            if len(descriptors) > 256:
                raise ValueError('bounded_descriptor_limit')
            inboxes = set()
            for descriptor in descriptors:
                try:
                    target = os.readlink(descriptor)
                except FileNotFoundError:
                    continue
                if target.startswith('/localhome/local-rohing/orch_') and target.endswith('/stream/inbox'):
                    inboxes.add(target)
            sources = {}
            for relative in request['source_names']:
                path = source / relative
                if str(path) not in cache:
                    content = raw(path, 65536)
                    functions = [entry.name for entry in ast.parse(content).body
                        if isinstance(entry, (ast.FunctionDef, ast.ClassDef))]
                    cache[str(path)] = dict(path=str(path), sha256=hashlib.sha256(content).hexdigest(),
                        bytes=len(content), functions=functions,
                        attributed_schema=b'R127_ATTRIBUTED_INBOX_V1' in content,
                        rohin_supported=b"'Rohin'" in content,
                        read_inbox_call=b'journal.read_inbox()' in content)
                sources[relative] = cache[str(path)]
            if len(inboxes) != 1:
                raise ValueError('one_open_consumer_inbox_not_verified')
            inbox = Path(next(iter(inboxes)))
            root = inbox.parent.parent
            names = []
            with os.scandir(inbox) as listing:
                for entry in listing:
                    if len(names) >= 4096:
                        raise ValueError('bounded_inbox_listing_limit')
                    names.append(entry.name)
            after = raw(process / 'stat', 4096).decode().rsplit(')', 1)[1].split()
            if after[0] in ('Z', 'X') or after[19] != before[19]:
                raise ValueError('native_changed_during_observation')
            row.update(status='LIVE_NATIVE_OPEN_INBOX_AND_SOURCE_VERIFIED', source_root=str(source),
                python=python, interpreter_exe=os.readlink(process / 'exe'), boot_id=boot,
                uid=process.stat().st_uid, native_state=after[0], actual_root=str(root),
                open_inbox=str(inbox), source_files=sources,
                inbox_json_names=sum(name.endswith('.json') for name in names),
                inbox_partial_names=sum(name.endswith('.partial') for name in names),
                inbox_contents_read=False, ingestion_proven=False,
                original_pid_source_match=str(source) == requested['snapshot_source'])
        except Exception as error:
            row.update(status='HELD_METADATA_UNCERTAINTY', error_type=type(error).__name__,
                reason=str(error) if isinstance(error, ValueError) else 'BOUND_METADATA_PATH_UNAVAILABLE')
        rows.append(row)
    return dict(schema='ROHIN162_READ_ONLY_CONSOLE_ROUTES_V1', node=request['node'],
        observed_unix=time.time(), rows=rows, reserved_read_bytes=used, read_attempts=attempts,
        maximum_read_bytes=maximum, journal_content_reads=0, inbox_content_reads=0,
        sealed_reads=0, messages_sent=0, signals_sent=0, model_calls=0)


def collect():
    roster_raw = ROSTER.read_bytes()
    roster = json.loads(roster_raw)
    rows = [row for row in roster['rows'] if row['status'] == 'LIVE' and row['training']['training_enabled'] is True]
    if len(rows) != 24:
        raise ValueError('exact_24_roster_required')
    environment = dict(PATH=os.environ.get('PATH', '/usr/bin:/bin'), HOME=os.environ['HOME'],
        CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    requests = []
    for node in NODES:
        request = dict(node=node, source_names=SOURCE_NAMES, rows=[])
        for row in rows:
            if row['node'] == node:
                native = row['natives'][0]
                request['rows'].append(dict(labels=row['labels'], roster_root=row['life_root'],
                    pid=native['identity']['pid'], start_ticks=str(native['identity']['start_ticks']),
                    snapshot_source=native['identity']['cwd'], roster_observed_unix=row['observed_unix']))
        requests.append(request)
    script = 'import hashlib,json,os,time\nfrom pathlib import Path\n\ndef inspect(request):' + \
        Path(__file__).read_text().split('def inspect(request):', 1)[1].split('\n\ndef collect():', 1)[0]

    def run(request):
        output = HERE / (request['node'] + '.json')
        if output.exists():
            raise ValueError('one_pass_receipt_already_exists_no_retry')
        payload = script + '\nprint(json.dumps(inspect(' + repr(request) + '),sort_keys=True))\n'
        result = subprocess.run(['bash', str(REPO / 'gpu' / (request['node'] + '_ssh.sh')),
            "env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/python3 -B -"],
            input=payload.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=60, env=environment, cwd=REPO)
        if result.returncode:
            document = dict(node=request['node'], status='WRAPPER_READ_FAILED_NO_RETRY',
                returncode=result.returncode, stderr_sha256=hashlib.sha256(result.stderr).hexdigest(),
                stdout_sha256=hashlib.sha256(result.stdout).hexdigest(), observed_unix=time.time())
        else:
            document = json.loads(result.stdout)
        with output.open('x') as stream:
            json.dump(document, stream, sort_keys=True, indent=2)
            stream.write('\n')
        return dict(node=request['node'], status=document.get('status', 'METADATA_OBSERVATION_COMPLETE'),
            verified=sum(row['status'] == 'LIVE_NATIVE_OPEN_INBOX_AND_SOURCE_VERIFIED' for row in document.get('rows', [])),
            held=[row['labels'] for row in document.get('rows', []) if row['status'] != 'LIVE_NATIVE_OPEN_INBOX_AND_SOURCE_VERIFIED'],
            receipt=str(output), sha256=hashlib.sha256(output.read_bytes()).hexdigest())

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(run, requests))
    document = dict(scope='ROHIN162_READ_ONLY_METADATA_ONLY', roster=dict(path=str(ROSTER),
        sha256=hashlib.sha256(roster_raw).hexdigest()), reported_recalled_count=22, roster_learning_count=24,
        receipts=outcomes, observed_unix=time.time(), messages_sent=0, remote_passes=4,
        key_files_read=0, inbox_and_journal_contents_read=False)
    with (HERE / 'COLLECTION.json').open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(document, sort_keys=True))


if __name__ == '__main__':
    collect()
