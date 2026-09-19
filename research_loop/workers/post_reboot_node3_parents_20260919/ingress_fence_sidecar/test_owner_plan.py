"""Unmodified pinned bridge Handler under fake sockets; no network inspection."""

import ast
from io import BytesIO
import json
import os
from pathlib import Path
import socketserver
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research_loop.workers.post_reboot_node3_parents_20260919.ingress_fence_sidecar import owner_plan


REPO = Path(__file__).resolve().parents[4]


def original_handler(root, clock, socket_factory):
    source = owner_plan.pinned(REPO / owner_plan.BRIDGE, owner_plan.SOURCE_PINS[owner_plan.BRIDGE])
    tree = ast.parse(source)
    serve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve')
    handler = next(node for node in serve.body if isinstance(node, ast.ClassDef) and node.name == 'Handler')
    module = ast.Module(body=[handler], type_ignores=[])
    namespace = dict(socketserver=socketserver, json=json, root=root, LIMIT=16777216,
        config=dict(deadline_unix=1005), time=SimpleNamespace(time=lambda: clock[0], sleep=lambda seconds: None),
        socket=SimpleNamespace(socket=socket_factory, AF_UNIX='FAKE_UNIX', SOCK_STREAM='FAKE_STREAM'))
    exec(compile(module, '<pinned-original-bridge-handler-cpu-fixture>', 'exec'), namespace)
    instance = object.__new__(namespace['Handler'])
    instance.connection = SimpleNamespace(settimeout=lambda seconds: None)
    instance.rfile = BytesIO(b'{"session_id":"synthetic","request":{},"records":[]}\n')
    instance.wfile = BytesIO()
    return instance


class FakeUpstream:
    def __init__(self, ready, release):
        self.ready, self.release = ready, release
        self.target, self.timeout, self.payload = None, None, None

    def __enter__(self):
        self.ready.set()
        if not self.release.wait(3):
            raise TimeoutError('CPU_FIXTURE_BARRIER')
        return self

    def __exit__(self, *unused):
        return False

    def settimeout(self, value):
        self.timeout = value

    def connect(self, path):
        self.target = path

    def sendall(self, payload):
        self.payload = payload

    def makefile(self, mode):
        return BytesIO(b'{"fixture_only":true}\n')


class ExistingBridgeRaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.clock = [1000]
        self.ready, self.release = threading.Event(), threading.Event()
        self.upstream = FakeUpstream(self.ready, self.release)
        self.errors = []
        self.set_target('/synthetic/old-scorer.sock')

    def set_target(self, value):
        temporary = self.root / 'TARGET.pending'
        temporary.write_text(json.dumps(dict(socket=value)))
        os.replace(temporary, self.root / 'TARGET.json')

    def start(self):
        handler = original_handler(self.root, self.clock, lambda *unused: self.upstream)
        def execute():
            try:
                handler.handle()
            except BaseException as error:
                self.errors.append(error)
        worker = threading.Thread(target=execute)
        worker.start()
        self.assertTrue(self.ready.wait(2))
        return worker

    def finish(self, worker):
        self.release.set()
        worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(self.errors, [])

    def test_target_replacement_before_read_redirects_new_handler(self):
        self.set_target('/synthetic/fence.sock')
        worker = self.start()
        self.finish(worker)
        self.assertEqual(self.upstream.target, '/synthetic/fence.sock')

    def test_atomic_target_replacement_does_not_revoke_captured_target(self):
        worker = self.start()
        self.set_target('/synthetic/fence.sock')
        self.finish(worker)
        self.assertEqual(self.upstream.target, '/synthetic/old-scorer.sock')
        self.assertIsNotNone(self.upstream.payload)

    def test_past_stop_and_deadline_still_connects_with_point_one_timeout(self):
        worker = self.start()
        self.set_target('/synthetic/fence.sock')
        self.clock[0] = 1000000
        self.finish(worker)
        self.assertEqual(self.upstream.timeout, .1)
        self.assertEqual(self.upstream.target, '/synthetic/old-scorer.sock')
        self.assertIsNotNone(self.upstream.payload)

    def test_removing_target_file_does_not_revoke_captured_target(self):
        worker = self.start()
        (self.root / 'TARGET.json').unlink()
        self.finish(worker)
        self.assertEqual(self.upstream.target, '/synthetic/old-scorer.sock')


class OwnerPlanTests(unittest.TestCase):
    def test_permitted_evidence_cannot_produce_a_ready_live_plan(self):
        result = owner_plan.analyze(REPO)
        self.assertFalse(result['ready'])
        self.assertEqual(result['executable_live_actions'], [])
        self.assertEqual(result['live_observations'], [])
        self.assertTrue(result['evidence_cut']['explicitly_not_a_fresh_drain'])
        self.assertFalse(result['evidence_cut']['admission_closed'])
        self.assertFalse(result['evidence_cut']['kernel_backlog_observed'])
        self.assertTrue(result['precise_blocker']['no_alternative_procfs_netlink_socket_or_packet_probe'])

    def test_actual_two_recorded_target_files_are_identified(self):
        result = owner_plan.analyze(REPO)
        self.assertEqual([row['routing_file'] for row in result['recorded_retained_routes']], [
            '/localhome/local-rohing/orch_r233_lease_renewal_20260918/attempt2/shared2/bridge/TARGET.json',
            '/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-shared2-v1/bridge/TARGET.json'])

    def test_changed_source_fails_closed(self):
        with patch.dict(owner_plan.SOURCE_PINS, {owner_plan.BRIDGE: '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'source_or_artifact_changed'):
                owner_plan.source_evidence(REPO)

    def test_wrapper_has_no_remote_kernel_or_live_socket_api(self):
        tree = ast.parse(Path(owner_plan.__file__).read_bytes())
        imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
        self.assertEqual(imports, {'argparse', 'ast', 'hashlib', 'json'})
        self.assertNotIn('socket', imports)
        self.assertNotIn('subprocess', imports)


if __name__ == '__main__':
    unittest.main()
