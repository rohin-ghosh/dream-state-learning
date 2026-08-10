"""StructMem-Bench — a benchmark for structure-vs-detail retention in consolidated
agent memory. Abstract (CPU) tier. See BENCHMARK_SPEC.md.
"""

from .config import BenchConfig
from .tasks import generate, Stream, TYPE_NAMES
from . import memory, metrics, stats, harness

__all__ = ["BenchConfig", "generate", "Stream", "TYPE_NAMES",
           "memory", "metrics", "stats", "harness"]
__version__ = "0.1.0"
