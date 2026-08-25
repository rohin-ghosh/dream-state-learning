"""Prior-anchored hierarchical lifetime-memory benchmark.

The public entry point is :class:`SemanticWorld`.  The package is CPU-only;
model dreaming and LoRA transport plug in after the world/evaluator gates.
"""

from .model import (
    AtomicMemory,
    Claim,
    Episode,
    Goal,
    GoalDepth,
    Lifetime,
    MemoryClaim,
    Observation,
    ProofGraph,
    ReachoutBudget,
    VerificationBudget,
    VerificationResult,
    WorldConfig,
)
from .world import SemanticWorld
from .reachout import ReachoutSession
from .claims import ClaimCodec
from .corpus import CorpusRecipe, build_atomic_corpus

__all__ = [
    "Claim",
    "ClaimCodec",
    "CorpusRecipe",
    "AtomicMemory",
    "Episode",
    "Goal",
    "GoalDepth",
    "Lifetime",
    "MemoryClaim",
    "Observation",
    "ProofGraph",
    "ReachoutBudget",
    "ReachoutSession",
    "SemanticWorld",
    "VerificationBudget",
    "VerificationResult",
    "WorldConfig",
    "build_atomic_corpus",
]
