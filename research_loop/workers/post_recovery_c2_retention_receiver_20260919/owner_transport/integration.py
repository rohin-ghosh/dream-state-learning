"""Concrete C2 owner RPC, original r188 dispatch, and shared-budget operations."""

from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

import common as core
from common import DEADLINE, digest, pinned, pins_match, require, sha, write_once
from coordinator import execution_digest
from transport import OwnerBridge
from research_loop.workers.post_recovery_retention_boundary_20260918 import boundary as original_boundary
from research_loop.workers.post_recovery_retention_boundary_20260918 import coordinator as original_coordinator
from research_loop.workers.post_recovery_retention_boundary_20260918 import operations as original_operations
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import read_boundary, journal_identity
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import LinuxOperations


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


class ConcreteRoute:
    def __init__(self, configuration, owner, prefix):
        self.configuration, self.owner, self.prefix = configuration, owner, prefix

    def preflight(self, binding, prepared):
        require(binding == self.configuration['binding'] and prepared == self.configuration['prepared'], 'exact_Main_route_scope')
        self.owner.check(binding, prepared['epoch_id'])
        receipt = pinned(self.configuration['route_receipt'])
        require(receipt['life_binding_sha256'] == digest(binding) and receipt['prepared_sha256'] == digest(prepared)
            and receipt['source_pins_sha256'] == digest(prepared['new_source_pins'])
            and receipt['owner_dependency'] == self.owner.dependency, 'source_bound_actual_route_receipt')
        pins_match(self.configuration['route_evidence_pins'])
        return receipt

    def dependents_clear(self, handle):
        self.owner.check(self.configuration['binding'], self.configuration['prepared']['epoch_id'])
        return True

    def dispatch_once(self, token):
        require(self.prefix.reservation_budget is not None, 'dispatch_under_same_remaining_budget')
        self.prefix.reservation_budget.check()
        binding, prepared = self.configuration['binding'], self.configuration['prepared']
        self.preflight(binding, prepared)
        require(token['life_binding_sha256'] == digest(binding) and token['old_native_exited'] is True
            and token['new_source_pins'] == prepared['new_source_pins'] and token['deadline_unix'] == DEADLINE,
            'exact_source_handoff_before_original_r188_only_dispatch')
        source = Path(prepared['new_plan']['source_root'])
        guard_path = token['receiver']['guard_path']
        require(sha(source / 'gpu/r188_node5_confinement.py') ==
            '75eed0e5e57cd7463e46fa10adeeebdb80b9ef1ce5e76a9b527c034d1e8e6481', 'unchanged_original_r188')
        command = [self.configuration['python_executable'], '-B', '-m', 'gpu.r188_node5_confinement',
            'dispatch', '--config', guard_path]
        attempt = Path(guard_path).parent
        with (attempt / 'C2_R188_OUTER.log').open('xb') as log:
            process = subprocess.Popen(command, cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source)), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True)
        return dict(outer_pid=process.pid, native_pid=None, loaded=False, parent_rebind_allowed=False,
            command=command, source_epoch=prepared['epoch_id'], admission_bypassed=False)


class C2Operations(LinuxOperations):
    def __init__(self, configuration, receiver, owner, prefix, approved):
        super().__init__(configuration['binding'], receiver.hooks(), approved_execution_sha256=approved,
            control_root=configuration['control_root'])
        self.configuration, self.receiver, self.owner, self.prefix = configuration, receiver, owner, prefix
        self.gate = Path(configuration['control_root']) / 'C2_RESERVED_REVIEW_REQUIRED.json'

    def verify_static(self, prepared):
        require(not self.gate.exists(), 'prior_attempt_requires_Main_reconciliation_no_blind_retry')
        self.prefix.verify_before_reservation(self.binding, prepared)
        self.hooks.verify_prepared(prepared)

    def begin_attempt(self, candidate):
        write_once(self.gate, dict(execution_sha256=self.approved_execution_sha256, candidate_sha256=digest(candidate),
            created_unix=time.time(), automatic_retry_allowed=False))

    @contextmanager
    def bounded_path(self, deadline):
        with self.prefix.budget(deadline, clock=self.monotonic) as budget:
            require(self.owner.budget is None, 'one_owner_budget')
            self.owner.budget = budget
            try:
                yield budget
            finally:
                self.owner.budget = None

    def observe(self, binding, *, durable=False):
        self._bound(binding)
        require(journal_identity(binding) == self.bound_journal, 'original_journal_objects')
        return read_boundary(binding, max_records=2, durable=durable)

    @staticmethod
    def monotonic():
        return time.monotonic()


def build(configuration, approved):
    require(approved == execution_digest(configuration), 'explicit_exact_Main_execution_hash')
    verify_coordinator_source(configuration['coordinator_source_pins'])
    bundle = Path(configuration['bundle'])
    manifest = pinned(configuration['bundle_manifest'])
    require(configuration['bundle_manifest']['path'] == str(bundle / 'EPOCH4_SOURCE.json'), 'exact_epoch4_bundle')
    pins_match({str(bundle / 'tools' / name): expected for name, expected in manifest['helper_pins'].items()})
    source = Path(configuration['prepared']['new_plan']['source_root'])
    require({str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
        == configuration['prepared']['new_source_pins'] == manifest['new_source_pins'], 'whole_exact_production_source')
    for name, entry in manifest['additional_assets'].items():
        require(sha(source / name) == entry['sha256'], 'exact_startup_asset')
    for name, module in tuple(sys.modules.items()):
        if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
            require(Path(module.__file__).resolve().is_relative_to(source), 'no_foreign_runtime_import')
    sys.path.insert(0, str(bundle / 'tools'))
    sys.path.insert(0, str(source))
    receiving = load('c2_owner_exact_receiving', bundle / 'tools/receiving_core.py')
    preflight = load('c2_owner_exact_prefix_preflight', bundle / 'tools/prefix_preflight.py')
    from gpu import c2_prefix_authority as api
    prefix = preflight.PrefixPreflight(api, configuration['prefix_authority'], configuration['prefix_policy'])
    owner = OwnerBridge(**configuration['owner_bridge'])
    route = ConcreteRoute(configuration, owner, prefix)
    receiver = receiving.C2Receiver(configuration['binding'], configuration['staged'],
        cpu_receipt_path=configuration['cpu_receipt_path'], consumed_wall_receipt=configuration['consumed_wall_receipt'],
        python_executable=configuration['python_executable'], prefix_control=prefix,
        route=receiving.MainRoute(route.preflight, route.dependents_clear, route.dispatch_once))
    return C2Operations(configuration, receiver, owner, prefix, approved)


def verify_coordinator_source(pins):
    boundary = core.REPO / 'research_loop/workers/post_recovery_retention_boundary_20260918'
    required = {*map(str, core.HERE.glob('*.py')),
        *(str(boundary / name) for name in ('boundary.py', 'coordinator.py', 'operations.py'))}
    require(required <= set(pins), 'whole_exact_owner_coordinator_and_original_guardian_sources')
    require(all(Path(module.__file__).resolve() == boundary / name for name, module in (
        ('boundary.py', original_boundary), ('coordinator.py', original_coordinator), ('operations.py', original_operations))),
        'original_guardian_imports_not_foreign_cached_modules')
    pins_match(pins)
