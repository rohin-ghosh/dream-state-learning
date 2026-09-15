"""Tool-free existing Claude evaluator runtime for LONG parent decisions."""

import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from organism_v6.orch_l2_long_parent import PARENT_SYSTEM, digest, validate_request


BACKEND = 'existing_authorized_claude_cli_tool_free'
LOCK_PATH = Path('/tmp/orch_l2_evaluator.lock')
MIN_AVAILABLE_BYTES = 1536 * 1024 * 1024


def available_memory():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise RuntimeError('vm_available_memory_unknown')


def command():
    return ['claude', '-p', '--output-format', 'json', '--tools', '',
            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
            '--disable-slash-commands', '--no-session-persistence',
            '--safe-mode', '--max-turns', '1', '--effort', 'low', '--system-prompt', PARENT_SYSTEM]


def write(path, document):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def parse_output(text):
    envelope = json.loads(text)
    if envelope.get('is_error') or envelope.get('type') != 'result':
        raise ValueError('authorized_evaluator_failed_no_fallback')
    raw = envelope.get('result', '')
    if raw.startswith('```json\n') and raw.endswith('\n```'):
        raw = raw[8:-4]
    document = json.loads(raw)
    if set(document) != {'decision', 'message', 'reason', 'distillation'}:
        raise ValueError('exact_parent_response_schema_required')
    if not all(isinstance(value, str) for value in document.values()):
        raise ValueError('parent_response_strings_required')
    return document, dict(usage=envelope.get('usage'), model_usage=envelope.get('modelUsage'),
                          total_cost_usd=envelope.get('total_cost_usd'),
                          duration_ms=envelope.get('duration_ms'),
                          duration_api_ms=envelope.get('duration_api_ms'))


class EvaluatorBackend:
    def __init__(self, output, charge_call, *, timeout=180, deadline=None,
                 lock_path=LOCK_PATH, memory=available_memory):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.charge_call = charge_call
        self.timeout = timeout
        self.deadline = deadline
        self.lock_path = Path(lock_path)
        self.memory = memory

    def __call__(self, request):
        validate_request(request)
        request_id = digest(request)
        directory = self.output / request_id
        directory.mkdir(exist_ok=False)
        write(directory / 'REQUEST.json', request)
        started = time.time()
        cutoff = min(started + self.timeout, self.deadline or float('inf'))
        with self.lock_path.open('a') as lock:
            while True:
                if time.time() >= cutoff:
                    write(directory / 'FAILED.json', dict(error='lock_deadline', dispatched=False))
                    raise TimeoutError('parent_lock_deadline')
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    time.sleep(0.25)
            memory = self.memory()
            if memory < MIN_AVAILABLE_BYTES:
                write(directory / 'FAILED.json', dict(error='vm_memory_floor', dispatched=False,
                                                       available_bytes=memory))
                raise RuntimeError('no_new_parent_process_below_1_5GiB')
            self.charge_call()
            write(directory / 'DISPATCH.json', dict(backend=BACKEND, command=command(),
                request_sha256=request_id, available_bytes=memory, started_unix=time.time(),
                deadline_unix=cutoff, process_fanout=1, scope='training', retries=0))
            environment = dict(os.environ, CLAUDE_CODE_MAX_OUTPUT_TOKENS='1024')
            child = None
            try:
                with (directory / 'stdout.json').open('w') as stdout, (directory / 'stderr.txt').open('w') as stderr:
                    child = subprocess.Popen(command(), cwd=directory, env=environment,
                        stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                        text=True, start_new_session=True)
                    child.communicate(json.dumps(request, sort_keys=True),
                                      timeout=max(0.01, cutoff - time.time()))
                if child.returncode:
                    raise RuntimeError('parent_runtime_denied_or_failed_no_fallback')
                response, usage = parse_output((directory / 'stdout.json').read_text())
                receipt = dict(backend=BACKEND, request_sha256=request_id,
                    response_sha256=digest(response), started_unix=started,
                    finished_unix=time.time(), evaluator_json_output_limit=1024,
                    message_limit_enforced_by_child_tokenizer=256, **usage)
                write(directory / 'RECEIPT.json', receipt)
                return dict(response, backend_receipt=receipt)
            except BaseException as error:
                if child is not None and child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)
                write(directory / 'FAILED.json', dict(error=type(error).__name__, dispatched=True,
                                                       finished_unix=time.time()))
                raise


def evaluate_queued(request, directory, *, deadline=None):
    if (set(request) != {'id', 'payload', 'cap_response_tokens'}
            or not re.fullmatch(r'\d{4}_LONG_C[123]', request['id'])
            or set(request['payload']) != {'kind', 'long_request'}
            or request['payload']['kind'] != 'long_coach'):
        raise ValueError('exact_shared_long_queue_request_required')
    payload = validate_request(request['payload']['long_request'])
    if request['id'][-1] != str(payload['cycle']):
        raise ValueError('long_queue_cycle_drift')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / 'QUEUED_RESERVATION.json', dict(id=request['id'],
        bucket='PARENT_LONG', request_sha256=digest(request),
        counted_by='shared_parent_request_before_queue_publication', duplicate_debit=False))

    def already_reserved():
        if not (directory / 'QUEUED_RESERVATION.json').is_file():
            raise ValueError('shared_queue_reservation_required')

    backend = EvaluatorBackend(directory / 'evaluator', already_reserved, deadline=deadline)
    result = backend(payload)
    write(directory / 'RESULT.json', result)
    return result
