"""Bounded retries for explicit prepublication HTTP404/503, never unknown sends."""

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import types
import urllib.error
import urllib.parse

import node3_route_binding as route
import receipt_rebind as current
import takeover as base
from takeover import HERE, REPO, read, write, reference, require


def bounded_strong(original, prompt, directory, deadline, instruction, effort, *, record=write, sleep=time.sleep):
    directory = Path(directory)
    deadline = min(deadline, time.time() + 120)
    for attempt_index in range(2):
        destination = directory if attempt_index == 0 else directory / 'provider_retry_1'
        if attempt_index:
            require(not (directory / 'PUBLISH_INTENT.json').exists(), 'never_retry_publication_intent')
            require(time.time() < deadline - 2, 'bounded_retry_deadline')
            destination.mkdir(exist_ok=False)
        try:
            result = original(prompt, destination, deadline, instruction, reasoning_effort=effort)
            record(directory / 'PROVIDER_COMPLETION.json', dict(status='ACTUAL_PROVIDER_RETURN',
                attempt_index=attempt_index, provider_artifact_directory=str(destination), completed_unix=time.time()))
            return result
        except urllib.error.HTTPError as error:
            record(destination / 'HTTP_FAILURE.json', dict(status='KNOWN_HTTP_PREPUBLICATION_FAILURE',
                http_status=error.code, attempt_index=attempt_index, observed_unix=time.time(),
                publication_intent_present=(directory / 'PUBLISH_INTENT.json').exists(),
                error_body_preserved='http_error_response.txt'))
            if error.code not in (404, 503) or attempt_index or (directory / 'PUBLISH_INTENT.json').exists():
                raise
            record(directory / 'BOUNDED_RETRY.json', dict(reason='Main-confirmed intermittent gateway rejection',
                prior_http_status=error.code, same_input=True, maximum_additional_calls=1,
                publication_intent_present=False, attempt_index=1, deadline_unix=deadline))
            sleep(.5)


def runtime(physical, config_path):
    parent, provider, config, helper = current.runtime(physical, config_path)
    original = provider.strong
    request_namespace = types.SimpleNamespace(**vars(provider.urllib.request))
    original_build = request_namespace.build_opener
    context = {}

    def build_opener(*handlers):
        delegate = original_build(*handlers)

        class ObservedOpener:
            def open(self, request, *args, **kwargs):
                parsed = urllib.parse.urlsplit(request.full_url)
                require(request.full_url == 'https://[REDACTED_HOST]/v1/responses', 'unchanged_working_URL')
                body = json.loads(request.data)
                require(body['model'] == base.MODEL, 'exact_working_alias')
                key = os.environ.get('NVIDIA_API_KEY', '')
                matches = bool(key) and hmac.compare_digest(request.get_header('Authorization', ''), 'Bearer ' + key)
                require(matches, 'privately_inherited_current_key')
                write(context['directory'] / 'ACTUAL_OUTBOUND_REQUEST.json', dict(host=parsed.hostname,
                    path=parsed.path, model=body['model'], reasoning=body.get('reasoning'),
                    inherited_key_present=bool(key), authorization_matches_inherited_key=matches,
                    credentials_or_credential_hashes_recorded=False, URL_rewritten=False, observed_unix=time.time()))
                return delegate.open(request, *args, **kwargs)

        return ObservedOpener()

    request_namespace.build_opener = build_opener
    provider.urllib = types.SimpleNamespace(request=request_namespace, error=provider.urllib.error)

    def observed(prompt, directory, deadline, instruction, *, reasoning_effort=None):
        context['directory'] = Path(directory)
        try:
            return original(prompt, directory, deadline, instruction, reasoning_effort=reasoning_effort)
        finally:
            context.clear()

    def strong(prompt, directory, deadline, instruction=provider.SYSTEM, *, reasoning_effort=None):
        return bounded_strong(observed, prompt, directory, deadline, instruction, reasoning_effort)

    provider.strong = strong
    parent.strong = strong
    return parent, provider, config, helper


def bind(physical):
    folder = route.folder_for(physical)
    require(not (folder / 'RETRY_TAKEOVER_ONCE.json').exists(), 'one_retry_binding')
    receipt = folder / 'ROUTE_IDENTITY_CONFIRMED.json'
    expected = read(receipt if receipt.exists() else folder / 'ROUTE_SPAWNED.json')['identity']
    config = read(folder / 'CONFIG.json')
    base.ledger = current.metadata.modern_ledger
    descriptor, reserved = base.quiet_pause(expected, str(folder / 'parent'), config, time.monotonic() + 120)
    terminated = False
    try:
        require(current.metadata.modern_ledger(folder / 'parent', config) == reserved
                and base.same(expected, base.identity(expected['pid'])), 'quiet_settled_parent_identity')
        write(folder / 'RETRY_TAKEOVER_ONCE.json', dict(predecessor=expected, settled_ledger=reserved,
            wrapper=reference(__file__), unchanged_config=reference(folder / 'CONFIG.json'),
            unchanged_seed=reference(folder / 'SEED.json'), new_baseline=False, no_cursor_reseed=True,
            URL_rewrite=False, at_unix=time.time()))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        terminated = True
        require(bool(select.select([descriptor], [], [], 20)[0]), 'one_parent_exit_before_successor')
        process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--physical', str(physical)],
            cwd=REPO, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        expected_argv = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--physical', str(physical)]
        for unused in range(100):
            actual = base.identity(process.pid)
            if actual['argv'] == expected_argv:
                break
            time.sleep(.01)
        require(actual['argv'] == expected_argv, 'post_exec_parent_identity')
        receipt = dict(status='BOUNDED_RETRY_PARENT_STARTED_NOT_PROVIDER_SUCCESS', physical=physical,
            identity=actual, predecessor=expected, at_unix=time.time(), child_signals=0)
        write(folder / 'RETRY_SPAWNED.json', receipt)
        return receipt
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def serve(physical):
    folder = route.folder_for(physical)
    offset = max((int(path.stem.split('_')[1]) for path in folder.glob('STATUS_*.json')), default=-1) + 1

    def preserved_write(path, document):
        path = Path(path)
        if path == folder / 'parent/STARTED.json':
            path = folder / 'parent/RETRY_STARTED.json'
            document = dict(document, retry_wrapper=reference(__file__), retries_only_for=[404, 503],
                maximum_additional_calls=1, unknown_publications_never_retried=True)
        elif path.parent == folder and path.name.startswith('STATUS_'):
            path = folder / ('STATUS_%06d.json' % (offset + int(path.stem.split('_')[1])))
        write(path, document)

    namespace = dict(current.metadata.__dict__, STATE=folder.parent.parent, runtime=runtime,
                     hashlib=hashlib, write=preserved_write, __file__=str(Path(__file__).resolve()))
    types.FunctionType(current.metadata.serve.__code__, namespace, 'serve')(physical)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('bind', 'serve'))
    parser.add_argument('--physical', type=int, choices=base.PHYSICALS, required=True)
    args = parser.parse_args()
    if args.action == 'bind':
        print(json.dumps(bind(args.physical)))
    else:
        serve(args.physical)
