"""Strict weights-only recovery in an exclusively owned, single-threaded process."""

from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api


def load_exclusive(directory, *, torch):
    """Temporarily remove ambient privileges; restore them even on failure.

    Caller must exclude concurrent deserialization/registry mutation. This is
    not a process-wide concurrency abstraction or an unsafe loading fallback.
    """
    original = list(torch.serialization.get_safe_globals())
    torch.serialization.clear_safe_globals()
    try:
        return checkpoint_api.load_checkpoint(directory)
    finally:
        torch.serialization.clear_safe_globals()
        torch.serialization.add_safe_globals(original)
