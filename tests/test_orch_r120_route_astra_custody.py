from copy import deepcopy
import unittest

from gpu import orch_r120_route_astra_custody as custody


class AstraLeaseCustodyTests(unittest.TestCase):
    def setUp(self):
        self.control = dict(root=custody.ROOT, terminal=custody.TERMINAL,
            plan=dict(path=custody.ROOT+'/R118_PARALLEL_PLAN.json', sha256='plan'),
            parent_wait_seconds=120, deadline_unix=1789596240,
            lease_policy=dict(path='/clock', sha256='a1aa51349c1784ec9f78e6411912576be43b55942c5fcdf1858ca391fd81c510'),
            native_source=custody.reference(custody.__file__))

    def test_only_verified_lease_bound_changes(self):
        custody.verify_control(self.control)
        for field, value in [('deadline_unix',1789491720),('deadline_unix',1789596241),('parent_wait_seconds',600)]:
            changed = dict(self.control, **{field:value})
            with self.assertRaises(ValueError):
                custody.verify_control(changed)

    def test_other_root_or_clock_rejected(self):
        changed = deepcopy(self.control)
        changed['root'] += '_other'
        with self.assertRaises(ValueError):
            custody.verify_control(changed)
        changed = deepcopy(self.control)
        changed['lease_policy']['sha256'] = 'unbound'
        with self.assertRaises(ValueError):
            custody.verify_control(changed)

    def test_fresh_actual_worker_heartbeat_still_required(self):
        control = dict(self.control, config_sha256='config',control_sha256='control')
        heartbeat = dict(control_sha256='control',config_sha256='config',plan=control['plan'],
            exclusive_queue_lock_acquired=True,time_unix=100,identity_role='VM_HTTP_PROVIDER_WORKER',
            identity=dict(pid=123),host_binding_sha256='h'*64)
        custody.validate_heartbeat(heartbeat,control,110)
        with self.assertRaises(ValueError):
            custody.validate_heartbeat(heartbeat,control,131)
