"""Minimal parent-only canonical route binding; reuse every existing state artifact."""

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
import urllib.parse

import brain_baseline as brain
import receipt_rebind as current
import support_fallback as support
import takeover as base
from takeover import HERE, REPO, require, read, write, sha, reference

HOST = 'inference-api.nvidia.com'
ROUTE = '/v1/responses'


def folder_for(physical):
    state = support.STATE if physical == 0 else brain.STATE if physical == 2 else current.STATE
    return state / 'parents' / ('physical' + str(physical))


def canonical_route(url):
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == 'https' and parsed.hostname == HOST and parsed.port in (None, 443)
            and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment,
            'exact_private_provider_host_no_redirect')
    require(parsed.path in ('/responses', ROUTE), 'known_responses_route_only')
    return 'https://' + HOST + ROUTE


def runtime(physical, config_path):
    parent, provider, config, helper = current.runtime(physical, config_path)
    original_strong = provider.strong
    original_urllib = provider.urllib
    original_build = original_urllib.request.build_opener
    context = {}

    def build_opener(*handlers):
        delegate = original_build(*handlers)

        class BoundOpener:
            def open(self, request, *args, **kwargs):
                require('directory' in context, 'owned_provider_call_context')
                before = urllib.parse.urlsplit(request.full_url)
                request.full_url = canonical_route(request.full_url)
                body = json.loads(request.data)
                require(request.get_method() == 'POST' and body['model'] == base.MODEL, 'actual_outbound_POST_exact_Astra')
                key = os.environ.get('NVIDIA_API_KEY', '')
                authorization = request.get_header('Authorization', '')
                matches = bool(key) and hmac.compare_digest(authorization, 'Bearer ' + key)
                require(matches, 'current_private_inherited_key_required')
                write(context['directory'] / 'OUTBOUND_ROUTE.json', dict(status='ACTUAL_OPENER_OPEN_ENTERED',
                    original_host=before.hostname, original_path=before.path, effective_host=HOST,
                    effective_path=ROUTE, model=body['model'], method=request.get_method(),
                    missing_v1_corrected=before.path != ROUTE, inherited_key_present=bool(key),
                    authorization_matches_inherited_key=matches, credential_values_or_hashes_logged=False,
                    at_unix=time.time(), wrapper=reference(__file__), provider_source=reference(provider.__file__)))
                return delegate.open(request, *args, **kwargs)

        return BoundOpener()

    request_namespace = types.SimpleNamespace(**vars(original_urllib.request))
    request_namespace.build_opener = build_opener
    provider.urllib = types.SimpleNamespace(request=request_namespace, error=original_urllib.error)

    def strong(prompt, directory, deadline, instruction=provider.SYSTEM, *, reasoning_effort=None):
        require(not context, 'one_provider_call_at_a_time')
        require(Path(directory).resolve().is_relative_to(HERE), 'owned_attempt_only')
        context['directory'] = Path(directory)
        try:
            return original_strong(prompt, directory, deadline, instruction, reasoning_effort=reasoning_effort)
        finally:
            context.clear()

    provider.strong = strong
    parent.strong = strong
    return parent, provider, config, helper


def bind(physical):
    folder = folder_for(physical)
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'privately_sourced_key_present')
    require(not (folder / 'ROUTE_TAKEOVER_ONCE.json').exists(), 'one_route_binding_no_replay')
    expected = read(folder / 'SPAWNED.json')['identity']
    config = read(folder / 'CONFIG.json')
    base.ledger = current.metadata.modern_ledger
    descriptor, reserved = base.quiet_pause(expected, str(folder / 'parent'), config, time.monotonic() + 120)
    terminated = False
    try:
        require(current.metadata.modern_ledger(folder / 'parent', config) == reserved
                and base.same(expected, base.identity(expected['pid'])), 'essential_identity_settled_publication_check')
        write(folder / 'ROUTE_TAKEOVER_ONCE.json', dict(predecessor=expected, wrapper=reference(__file__),
            config=reference(folder / 'CONFIG.json'), preserved_seed=reference(folder / 'SEED.json'),
            settled_ledger=reserved, no_new_baseline=True, no_cursor_reseed=True, learner_signals=0,
            canonical_host=HOST, canonical_path=ROUTE, actual_model=base.MODEL, at_unix=time.time()))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        terminated = True
        require(bool(select.select([descriptor], [], [], 20)[0]), 'old_parent_exit_before_replacement')
        process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--physical', str(physical)],
            cwd=REPO, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        result = dict(status='ROUTE_BOUND_PARENT_STARTED_NOT_NEW_PUBLICATION', physical=physical,
            identity=base.identity(process.pid), predecessor=expected, active_folder=str(folder),
            child_restarts=0, source=reference(__file__), at_unix=time.time())
        write(folder / 'ROUTE_SPAWNED.json', result)
        return result
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def serve(physical):
    folder = folder_for(physical)
    previous = [int(path.stem.split('_')[1]) for path in folder.glob('STATUS_*.json')]
    offset = max(previous, default=-1) + 1

    def preserved_write(path, document):
        path = Path(path)
        if path == folder / 'parent/STARTED.json':
            path = folder / 'parent/ROUTE_STARTED.json'
            document = dict(document, route_wrapper=reference(__file__), canonical_path=ROUTE)
        elif path.parent == folder and path.name.startswith('STATUS_'):
            sequence = int(path.stem.split('_')[1])
            path = folder / ('STATUS_%06d.json' % (offset + sequence))
        write(path, document)

    namespace = dict(current.metadata.__dict__, STATE=folder.parent.parent, runtime=runtime,
                     hashlib=hashlib, write=preserved_write, __file__=str(Path(__file__).resolve()))
    types.FunctionType(current.metadata.serve.__code__, namespace, 'serve')(physical)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('bind', 'serve'))
    parser.add_argument('--physical', type=int, choices=base.PHYSICALS, required=True)
    args = parser.parse_args()
    if args.action == 'bind':
        print(json.dumps(bind(args.physical), sort_keys=True))
    else:
        serve(args.physical)


if __name__ == '__main__':
    main()
