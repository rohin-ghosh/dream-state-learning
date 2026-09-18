"""Bind the working R166 outbound route and record the actual HTTP send."""

import hashlib
import json
import os
from pathlib import Path
import time
import types
import urllib.request


MODEL = 'openai/openai/gpt-6-astra'
ENDPOINT = 'https://[REDACTED_HOST]/v1/responses'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write('\n')


def routed(original, directory):
    request_module = original.__globals__['urllib'].request
    original_builder = request_module.build_opener

    class BoundOpener:
        def __init__(self, opener):
            self.opener = opener

        def open(self, request, timeout):
            body = json.loads(request.data)
            require(body['model'] == MODEL, 'actual_outbound_model')
            require(request.get_method() == 'POST', 'actual_outbound_POST')
            before = request.full_url
            require(request.full_url == ENDPOINT, 'known_working_route_no_URL_rewrite')
            key = os.environ.get('NVIDIA_API_KEY')
            require(bool(key) and request.get_header('Authorization') == 'Bearer ' + key,
                    'existing_privately_inherited_key_only')
            write(directory / 'OUTBOUND_ROUTE.json', dict(observed_unix=time.time(),
                actual_url=request.full_url, original_url=before, route_changed=before != ENDPOINT,
                actual_model=body['model'], method=request.get_method(),
                inherited_key_present=True, authorization_matches_inherited_key=True,
                source=original.__code__.co_filename, source_sha256=hashlib.sha256(
                    Path(original.__code__.co_filename).read_bytes()).hexdigest(),
                http_attempts=1, retry=False, redirects_allowed=False,
                secret_values_or_hashes_exported=False))
            return self.opener.open(request, timeout=timeout)

    def build_opener(*handlers):
        return BoundOpener(original_builder(*handlers))

    proxy = types.SimpleNamespace(**{name: getattr(request_module, name) for name in dir(request_module)})
    proxy.build_opener = build_opener
    module = types.SimpleNamespace(request=proxy, error=original.__globals__['urllib'].error)
    namespace = dict(original.__globals__, urllib=module)
    cloned = types.FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
    cloned.__kwdefaults__ = original.__kwdefaults__
    return cloned


def install(policy, source):
    from gpu import orch_route_parent_campaign_providers as providers
    original = providers.strong
    require(Path(original.__code__.co_filename).resolve() == source / 'gpu/orch_route_parent_campaign_providers.py',
            'actual_owned_provider_function')

    def strong(prompt, directory, deadline, instruction=providers.SYSTEM, *, reasoning_effort=None):
        cloned = routed(original, directory)
        return cloned(prompt, directory, deadline, instruction, reasoning_effort=reasoning_effort)

    providers.strong = strong
    policy.parent.strong = strong
    return dict(provider_function=original.__code__.co_filename, wrapper=__file__, endpoint=ENDPOINT,
                model=MODEL, both_provider_and_imported_parent_alias_bound=True,
                actual_HTTP_proof='Per-call OUTBOUND_ROUTE.json immediately before opener.open')
