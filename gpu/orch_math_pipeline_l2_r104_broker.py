"""Preserve existing parent contexts; add one explicitly bound training-wheels segment."""

import argparse
from contextlib import contextmanager
import functools
import hashlib
import json
from pathlib import Path
import shlex

from gpu import orch_math_pipeline_l2_r102_broker as previous
from gpu import orch_math_pipeline_l2_r104_run as runner


@contextmanager
def training_context():
    parent = previous.transport.parent
    validator, instructions = parent.policy.validate_parent_payload, parent.INSTRUCTIONS
    parent.policy.validate_parent_payload = functools.partial(previous.policy.validate_parent_payload,
        parenting=runner.CONFIG['parenting'])
    parent.INSTRUCTIONS = instructions + ('\nTraining-wheels/long/supportive: scaffold the child\'s own thinking with '
        'stepwise questions about what to learn and how to check it, including unsuccessful attempts. '
        'Ask for alternatives and an explicit rejected approach; never supply solutions or lesson targets.')
    try:
        yield
    finally:
        parent.policy.validate_parent_payload, parent.INSTRUCTIONS = validator, instructions


def serve(options):
    registration = json.loads(options.extra_registration.read_text())
    assert registration['aggregate_native_cap'] == 2064 and registration['aggregate_parent_cap'] == 36
    assert registration['broker_sha256'] == previous.transport.parent.sha(Path(__file__))
    original = previous.transport.process_request
    def dispatch(store, request, buffer, receipts, config, deadline):
        if request.parent.parent.name != runner.CAMPAIGN:
            return original(store, request, buffer, receipts, config, deadline)
        text = store.shell('cat ' + shlex.quote(str(request.parent.parent / 'R104_READY.json'))).stdout
        assert hashlib.sha256(text.encode()).hexdigest() == registration['ready_sha256']
        ready = json.loads(text)
        assert ready['config'] == runner.CONFIG
        assert ready['policy_sha256'] == previous.transport.parent.sha(Path(previous.policy.__file__))
        with training_context():
            return original(store, request, buffer, receipts, config, deadline)
    previous.transport.process_request = dispatch
    previous.serve(options.repository, options.root, options.buffer, options.receipts,
        options.registration, options.deadline)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--extra-registration', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    serve(parser.parse_args())
