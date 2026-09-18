"""Capture the actual constructed HTTP request without sending or recording credentials."""

import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
from unittest import mock

from inventory_node1 import HERE, Reader, digest, identity, require
from parent_custody import write


class Captured(Exception):
    pass


def capture(provider, directory):
    observed = {}

    def intercept(request, timeout):
        body = json.loads(request.data)
        observed.update(url=request.full_url, method=request.get_method(), model=body['model'],
                        timeout=timeout, tools=body.get('tools'), store=body.get('store'),
                        authorization_present=bool(request.get_header('Authorization')),
                        credential_match=request.get_header('Authorization') == 'Bearer ' + os.environ['NVIDIA_API_KEY'],
                        captured_before_network=True, provider_calls=0)
        raise Captured()

    with mock.patch.object(urllib.request, 'build_opener', return_value=mock.Mock(open=intercept)):
        try:
            provider('CPU ROUTE CAPTURE ONLY', directory, time.time() + 120, 'CPU ONLY')
        except Captured:
            pass
    require(observed.get('captured_before_network'), 'actual_request_capture_required')
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--working-binding', type=Path)
    arguments = parser.parse_args()
    require(bool(arguments.spec) != bool(arguments.working_binding), 'one_actual_provider_binding')
    directory = HERE / ('ROUTE_CAPTURE_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    if arguments.spec:
        from parent_runner import load
        spec = json.loads(Reader().raw(arguments.spec))
        unused_parent, unused_config, provider, unused_selected = load(spec)
        source = Path(provider.__file__)
        strong = provider.strong
        binding_path = arguments.spec
        actor = json.loads(Reader().raw(arguments.spec.parent / 'PARENT_ACTIVATED.json'))['actor']
    else:
        binding_path = arguments.working_binding
        binding = json.loads(Reader().raw(binding_path))
        source = Path(binding['provider_copy'])
        require(digest(Reader().raw(source)) == binding['provider_sha256'], 'working_provider_source_pin')
        actor = identity(Path('/proc') / str(json.loads(Reader().raw(Path(binding['output']) / 'STARTED.json'))['pid']))
        sys.path.insert(0, actor['cwd'])
        provider = dict(__name__='actual_working_provider', __file__=str(source))
        exec(compile(Reader().raw(source), str(source), 'exec'), provider)
        strong = provider['strong']
    current = identity(Path('/proc') / str(actor['pid']))
    require(current['ticks'] == actor['ticks'] and current['argv_sha256'] == actor['argv_sha256'], 'actual_bound_parent_still_same')
    receipt = dict(capture(strong, directory), source_path=str(source), source_sha256=digest(Reader().raw(source)),
                   binding_path=str(binding_path), binding_sha256=digest(Reader().raw(binding_path)),
                   actor=current, observed_unix=time.time(), scope='ACTUAL_SOURCE_CPU_INTERCEPT_NOT_HISTORICAL_WIRE_PROOF')
    write(directory / 'RECEIPT.json', receipt)
    print(json.dumps(dict(receipt=str(directory / 'RECEIPT.json'), **{name: receipt[name] for name in
                     ('url', 'model', 'credential_match', 'source_sha256', 'scope')})))


if __name__ == '__main__':
    main()
