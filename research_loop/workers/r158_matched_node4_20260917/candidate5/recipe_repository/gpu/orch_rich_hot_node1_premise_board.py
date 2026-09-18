"""Require a matching published Main BOARD line before any stop or launch."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import time

from organism_v6 import orch_rich_hot_node1_premise as policy


def expected_line(source_sha, protocol_sha, lifetime_sha):
    return (f'[Main BOARD allocation] {policy.ARM} node1 physical3 uuid={policy.UUIDS[3]} '
            f'root={policy.ROOT} source_sha256={source_sha} protocol_sha256={protocol_sha} '
            f'lifetime_sha256={lifetime_sha} shared_call_cap={policy.MAX_CALLS} '
            'output_cap=16384 context=32768 hard_end=2026-09-15T15:45:10.822773Z')


def observation(board_text, requirement):
    line = requirement['expected_line']
    policy.require(line in board_text.splitlines(), 'main_board_exact_allocation_not_published')
    return dict(board_path='research_loop/BOARD.md', board_excerpt=line,
        board_sha256=hashlib.sha256(board_text.encode()).hexdigest(),
        observed_unix=time.time(), index=policy.INDEX, uuid=policy.UUIDS[policy.INDEX], root=policy.ROOT)


def require_board(root, index):
    policy.allocation(index)
    policy.require(str(root) == policy.ROOT, 'board_root_mismatch')
    publication = json.loads((root/'PUBLICATION.json').read_text())
    requirement_path = root/'BOARD_REQUIREMENT.json'
    requirement_sha = hashlib.sha256(requirement_path.read_bytes()).hexdigest()
    policy.require(publication['files']['BOARD_REQUIREMENT.json'] == requirement_sha,
                   'board_requirement_changed_after_cpu_publication')
    requirement = json.loads(requirement_path.read_text())
    approval = json.loads((root/'BOARD_APPROVAL.json').read_text())
    policy.require(approval['requirement_sha256'] == requirement_sha, 'board_allocation_binding_changed')
    policy.require(approval['index'] == index and approval['uuid'] == policy.UUIDS[index]
        and approval['root'] == str(root), 'board_slot_identity_mismatch')
    policy.require(approval['board_path'] == 'research_loop/BOARD.md'
        and approval['board_excerpt'] == requirement['expected_line']
        and re.fullmatch(r'[0-9a-f]{64}',approval['board_sha256']), 'board_publication_evidence_missing')
    lifetime = json.loads((root/'LIFETIME.json').read_text())
    policy.require(approval['observed_unix'] <= time.time() < lifetime['native_deadline_unix'],
                   'original_deadline_or_board_observation_invalid')
    return approval


def publish_observed_board(requirement_path):
    from gpu.orch_rich_hot_node1_exhaustion_roll import remote
    repository = Path(__file__).resolve().parents[1]
    board = repository/'research_loop/BOARD.md'
    requirement = json.loads(requirement_path.read_text())
    approval = observation(board.read_text(), requirement)
    approval['requirement_sha256'] = hashlib.sha256(requirement_path.read_bytes()).hexdigest()
    code = ('from pathlib import Path;import os;path=Path(' + repr(policy.ROOT+'/BOARD_APPROVAL.json')
        + ');assert not path.exists();temporary=path.with_suffix(".tmp");temporary.write_text('
        + repr(json.dumps(approval)) + ');os.replace(temporary,path)')
    remote('gpu/a40r_ssh.sh','python3 -c '+shlex.quote(code))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--requirement',type=Path,required=True)
    publish_observed_board(parser.parse_args().requirement)
