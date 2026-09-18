"""One Main-authorized same-input correction in the original failed attempt directory."""

import importlib.util
import json
import os
from pathlib import Path
import signal
import time
import urllib.error

from inventory_node1 import HERE, Reader, digest, identity, require, unchanged
from parent_custody import transport_children, write
from parent_runner import load
from forward_parent import guarded_provider, PARSER_SHA


class Output:
    def __init__(self, directory, index):
        self.directory, self.index = directory, index

    def __truediv__(self, name):
        require(Path(name).name == name, 'flat_corrective_artifacts')
        return self.directory / ('CORRECTIVE_' + str(self.index) + '_' + name)


def main():
    old = HERE / 'lane3_activation_1789678193752538745'
    active = HERE / 'lane3_activation_route_1789681442598702261'
    spec = json.loads(Reader().raw(old / 'SPEC.json'))
    activation = json.loads(Reader().raw(active / 'PARENT_ACTIVATED.json'))
    attempt = old / 'parent/parent_000000'
    result = json.loads(Reader().raw(attempt / 'RESULT.json'))
    require(result['status'] == 'MISSING' and result['error_type'] == 'HTTPError' and 'sent_unix' not in result,
            'known_prepublication_failure_only')
    error = Reader().raw(attempt / 'http_error_response.txt').decode()
    require('404' in error and ('NotFoundError' in error or 'not_found' in error.lower()), 'actual_prior_404')
    require(not (attempt / 'ARM_PUBLISHED.json').exists(), 'no_prior_corrective_publication')
    output = Output(attempt, 1)
    request = json.loads(Reader().raw(attempt / 'API_REQUEST.json'))
    parent, config, provider, selected = load(spec)
    parser_path = Path(spec['repository']) / 'gpu/orch_r175_parent_response.py'
    require(digest(Reader().raw(parser_path)) == PARSER_SHA, 'exact_lossless_private_parser')
    module_spec = importlib.util.spec_from_file_location('bound_parser', parser_path)
    parser = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(parser)
    provider.response_schema = parser.compatible_parser(provider.response_schema)
    expected = activation['actor']
    require(expected['uid'] == os.getuid() and expected['argv'][2] == str(HERE / 'forward_parent.py'), 'exact_own_active_parent')
    process = Path('/proc') / str(expected['pid'])
    require(unchanged(expected, identity(process)), 'current_parent_identity')
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    try:
        deadline = time.monotonic() + 120
        while True:
            require(unchanged(expected, identity(process)), 'parent_identity_before_pause')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if identity(process)['state'] in ('T', 't'):
                    break
                time.sleep(.01)
            require(identity(process)['state'] in ('T', 't'), 'parent_actually_paused')
            pending = [path for path in (active / 'parent').glob('parent_*') if not (path / 'RESULT.json').exists()]
            if not pending and not transport_children(expected['pid']):
                break
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            require(time.monotonic() < deadline, 'inflight_not_overridden')
            time.sleep(.5)
        write(output / 'RESERVED.json', dict(attempt_index=1, observed_unix=time.time(), active_parent=expected,
              original_request_sha256=digest(Reader().raw(attempt / 'API_REQUEST.json')),
              same_input=True, credential_source='current_Main_authorized_nvidia.env', child_signals=0))
        started = time.time()
        try:
            response, model, usage = guarded_provider(provider.strong, output, request['input'],
                min(config['hard_end_unix'], started + 120), request['instructions'], digest(Reader().raw(old / 'SPEC.json')))
        except urllib.error.HTTPError as failure:
            body = Reader().raw(output / 'http_error_response.txt', maximum=1024 * 1024).decode(errors='replace')
            classification = 'UPSTREAM_MODEL_ROUTE_NOT_FOUND_NO_FALLBACK' if failure.code == 404 and 'NotFoundError' in body else 'UPSTREAM_HTTP_FAILURE'
            receipt = dict(status='KNOWN_PREPUBLICATION_HTTP_FAILURE', http_status=failure.code,
                  classification=classification, attempts=1, published=False, child_signals=0, observed_unix=time.time())
            write(output / 'RESULT.json', receipt)
            print(json.dumps(receipt), flush=True)
            return
        require(request['model'] == model and response['speak'], 'actual_speaking_canonical_model_required')
        message = response['message']
        require(len(message.split()) <= selected['words'] and len(message.encode()) <= 4096, 'unchanged_publication_caps')
        audit = json.loads(Reader().raw(HERE / 'CURRENT_INBOX_AND_SLEEP_1789681528030349531.json'))
        prior = next(row for row in audit['rows'] if row['root'] == spec['root'])
        require(digest(message.encode()) not in {entry['text_sha256'] for entry in prior['inbox']}, 'no_duplicate_common_or_own_message')
        write(output / 'PUBLISH_INTENT.json', dict(message_sha256=digest(message.encode()), observed_unix=time.time(),
              origin='PROVIDER_MAIN_AUTHORIZED_SAME_INPUT_404_CORRECTION_NOT_COMMON_BASELINE'))
        try:
            publication = parent['publish'](Path(spec['repository']), config, message)
        except Exception as failure:
            write(output / 'PUBLICATION_UNKNOWN.json', dict(error_type=type(failure).__name__, retry=False, observed_unix=time.time()))
            raise
        receipt = dict(arm=spec['arm'], root=spec['root'], publication=publication, parent_pid=os.getpid(),
              policy_sha256=spec['policy_sha256'], assignment_sha256=spec['assignment_sha256'],
              message_sha256=digest(message.encode()), word_count=len(message.split()), word_cap=selected['words'],
              byte_count=len(message.encode()), publication_started_unix=started, publication_returned_unix=time.time(),
              request_exposure_verified=False, config_sha256=digest(Reader().raw(spec['config'])),
              origin='PROVIDER_MAIN_AUTHORIZED_SAME_INPUT_404_CORRECTION_NOT_COMMON_BASELINE', attempt_index=1)
        write(attempt / 'ARM_PUBLISHED.json', receipt)
        write(output / 'RESULT.json', dict(status='PUBLISHED_NOT_RENDERED', publication=publication, actual_model=model,
              usage=usage, response=response, observed_unix=time.time(), same_input=True, child_signals=0))
        print(json.dumps(dict(status='PUBLISHED_NOT_RENDERED', publication=publication,
              observed_unix=receipt['publication_returned_unix'], word_count=receipt['word_count'])), flush=True)
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            write(output / 'PARENT_RESUMED.json', dict(pid=expected['pid'], child_signals=0, observed_unix=time.time()))
        os.close(descriptor)


if __name__ == '__main__':
    main()
