"""Reuse the verified single-attempt, node-mirrored Astra transport after posting."""

import argparse
import json
from pathlib import Path
import re

from gpu import orch_route_parent_campaign_canonical_parent as broker
from organism_v6 import orch_route_parent_creative_backfill as policy


SYSTEM = ('You are a creative, supportive-positive route-learning parent. '
    'Encourage alternative evidence-grounded representations and approaches under the SAME supplied givens. '
    'Help the learner compare candidate paths and learn from rejected attempts, without micromanaging commands. '
    'Do not change premises, invent observations, or supply a gold route. Failures are not correct answers. '
    'Treat coaching as training wheels and preserve the learner\'s own explanation. No tools. '
    'Return only JSON with speak (boolean), message (at most 90 words), rationale (string); '
    'if silent, message must be empty.')


def configure():
    broker.ROOT = policy.ROOT
    broker.policy = policy
    broker.PATTERN = re.compile(r'(?P<index>\d{4})_(?P<arm>GUIDED)_C(?P<cycle>[1-4])\.request\.json')
    broker.SYSTEM = SYSTEM


def serve(host):
    configure()
    root = policy.ROOT
    ready = json.loads(broker.remote(host,f'cat {root}/READY.json'))
    posted = json.loads(broker.remote(host,f'cat {root}/MAIN_POSTED.json'))
    ready_sha = broker.remote(host,f'sha256sum {root}/READY.json').split()[0]
    proposal_sha = broker.remote(host,f'sha256sum {root}/PROPOSAL.json').split()[0]
    policy.validate_posted(posted,ready_sha,proposal_sha)
    tree = Path(__file__).resolve().parents[1]
    for relative in ('gpu/orch_route_parent_creative_backfill_parent.py','organism_v6/orch_route_parent_creative_backfill.py',
                     'gpu/orch_route_parent_campaign_canonical_parent.py','gpu/orch_route_parent_campaign_providers.py'):
        policy.require(broker.providers.file_sha256(tree/relative)==ready['source_files'][relative], 'broker_frozen_source_binding')
    start = json.loads(broker.remote(host,f'cat {root}/START.json'))
    dispatch = json.loads(broker.remote(host,f'cat {root}/DISPATCH.json'))
    release = json.loads(broker.remote(host,f'cat {root}/STRICT_RELEASE.json'))
    policy.require(release['clear'] and release['privileged'] and release['physical_index']==1
        and dispatch['ready_sha256']==ready_sha and start['caps']==policy.CAPS
        and start['hard_deadline_unix']-start['started_unix']==7200, 'exact_activation_before_parent_calls')
    policy.require(broker.remote(host,f'mkdir {root}/BROKER_CLAIM && echo CLAIMED').strip()=='CLAIMED', 'single_broker_no_restart')
    broker.serve(host,start['hard_deadline_unix'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',required=True)
    serve(parser.parse_args().host)
