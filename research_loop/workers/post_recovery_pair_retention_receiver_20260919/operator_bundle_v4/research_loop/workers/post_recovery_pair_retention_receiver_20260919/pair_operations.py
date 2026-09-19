"""Move expensive preparation into retryable observation, before any reservation."""

from contextlib import contextmanager
from copy import deepcopy

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import ObservationRace, require, same_boundary
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import LinuxOperations


class PairLinuxOperations(LinuxOperations):
    def __init__(self, binding, hooks, *, prepared, **arguments):
        super().__init__(binding, hooks, **arguments)
        self.prepared_pair = deepcopy(prepared)
        self.reservation_active = False
        self.prepared_cache = None

    def observe(self, binding, *, durable=False):
        candidate = super().observe(binding, durable=durable)
        if self.reservation_active or candidate is None:
            return candidate
        self.prepared_cache = None
        proof = super().verify_checkpoint(candidate)
        receiver = super().prepare_receiver(candidate, self.prepared_pair, proof)
        current = super().observe(binding)
        if current is None or current['complete_index'] > candidate['complete_index']:
            raise ObservationRace('COMPLETE_advanced_during_preparation_reobserve_same_handle')
        current = same_boundary(candidate, current)
        self.prepared_cache = (deepcopy(current), deepcopy(proof), deepcopy(receiver))
        return current

    def verify_checkpoint(self, candidate):
        require(self.prepared_cache is not None and not self.reservation_active, 'prestop_pair_preparation_required')
        same_boundary(self.prepared_cache[0], candidate)
        return deepcopy(self.prepared_cache[1])

    def prepare_receiver(self, candidate, prepared, proof):
        require(prepared == self.prepared_pair and proof == self.prepared_cache[1], 'same_prepared_pair_cache')
        same_boundary(self.prepared_cache[0], candidate)
        return deepcopy(self.prepared_cache[2])

    @contextmanager
    def reserve(self, handle, seconds):
        require(self.prepared_cache is not None, 'no_reservation_without_complete_preparation')
        self.reservation_active = True
        try:
            with super().reserve(handle, seconds) as reservation:
                yield reservation
        finally:
            self.reservation_active = False
            self.prepared_cache = None
