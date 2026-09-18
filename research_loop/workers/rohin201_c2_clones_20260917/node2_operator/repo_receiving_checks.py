"""Receiving-only repository smoke and targeted ACT routing tests."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'tests')]
from prepare_repo_c import read, write, sha, require
from research_loop.workers.rohin183_repo_learning_20260917 import tools
from tests.test_orch_r184_think_act_learn import ThinkActLearnTests


class RepoRouting(unittest.TestCase):
    def run_action(self, text):
        fixture = ThinkActLearnTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        fixture.config['trial_id'] = 'R202_REPO_C_node2_clone1'
        calls = []
        driver = fixture.driver([text], lambda origin: calls.append(origin) or {'status': 'PUBLISHED', 'executed': False})
        result = driver.act()
        return calls, result

    def test_actual_repo_action_dispatches(self):
        calls, result = self.run_action('repo_read gpu/orch_r125_continual_native.py 0')
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['status'], 'PUBLISHED')

    def test_prose_without_repo_request_is_not_dispatched(self):
        calls, result = self.run_action('I have not inspected the file yet.')
        self.assertEqual(calls, [])
        self.assertNotEqual(result['status'], 'PUBLISHED')

    def test_malformed_action_reaches_refusing_dispatcher_without_killing_life(self):
        calls, unused_result = self.run_action('repo_action {broken_json')
        self.assertEqual(len(calls), 1)


def main():
    test_result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(RepoRouting))
    require(test_result.wasSuccessful(), 'receiving_repo_ACT_route')
    config = read(ROOT / 'TOOLS.json')
    inventory = tools.manifest(config)
    smoke = ROOT / 'repository_smoke_only_not_child'
    (smoke / 'life/stream/inbox').mkdir(parents=True)
    (smoke / 'workspace').mkdir()
    (smoke / 'receipts').mkdir()
    synthetic = dict(config, root=str(smoke / 'life'), workspace=str(smoke / 'workspace'), receipts=str(smoke / 'receipts'))
    target = 'gpu/orch_r125_continual_native.py'
    require(target in inventory['files'], 'real_snapshot_file')
    origin = dict(actor='child', split='TRAIN', record_index=0, record_sha256='0' * 64,
        synthetic_builder_test=True, not_an_actual_child_response=True)
    references = []
    for sequence, action in enumerate([dict(action='list', path='gpu'), dict(action='read', path=target, offset=0),
        dict(action='propose', path='synthetic_probe.md', content='Synthetic receiving-only proposal. Not applied; no child authored this test.')]):
        references.append(tools.execute(synthetic, action, origin, sequence))
    receipt = read(smoke / 'receipts/ACTION_000001.json')
    require(receipt['source_sha256'] == inventory['files'][target]['sha256'] and receipt['returned_bytes'] > 0, 'actual_bound_file_bytes_returned')
    proposal = read(smoke / 'receipts/ACTION_000002.json')
    require(Path(proposal['workspace_path']).is_relative_to(smoke / 'workspace')
        and not proposal['applied_to_repository'] and not proposal['executed_code'], 'private_proposal_not_applied_or_executed')
    denied = False
    try:
        tools.execute(synthetic, dict(action='read', path='../outside'), origin, 3)
    except ValueError:
        denied = True
    require(denied, 'path_escape_denied')
    write(ROOT / 'REPOSITORY_SMOKE.json', dict(status='PASS', observed_unix=time.time(), tests_run=2,
        snapshot_manifest_sha256=config['snapshot_manifest']['sha256'], snapshot_files=len(inventory['files']),
        snapshot_bytes=sum(item['bytes'] for item in inventory['files'].values()), actual_list_read_private_proposal=True,
        path_escape_denied=True, code_and_tests_execution_available=False, live_repo_modified=False,
        synthetic_builder_test=True, no_actual_child_response_claim=True, references=references))
    print(json.dumps(dict(status='PASS', tests_run=2, actual_repository_smoke=True, snapshot_files=len(inventory['files']))))


if __name__ == '__main__':
    main()
