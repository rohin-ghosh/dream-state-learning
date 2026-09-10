"""CPU-testable RML-G1 supplied-gold recurrent action harness.

This package is deliberately isolated from ``rml_d0``.  It imports D0's
public world/target authorities but never changes them and contains no model,
network, GPU, DREAM, SLEEP, or training implementation.
"""

from .contract import CHANGE_ID, PROTOCOL, RESOURCE_CEILINGS, build_roster

__all__ = ["CHANGE_ID", "PROTOCOL", "RESOURCE_CEILINGS", "build_roster"]
