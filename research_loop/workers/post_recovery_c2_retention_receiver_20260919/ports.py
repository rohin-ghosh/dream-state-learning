"""Propose exact new-source bytes only; never edit or stage any input source."""

import hashlib
from pathlib import Path


NATIVE = 'gpu/orch_r125_continual_native.py'
RUNTIME = 'gpu/c2_retention_runtime.py'
NATIVE_BEFORE = '1bf18d5f34d2f027be1c79120ec654afe9869e647150245a29c8a19ebda81ff6'


def proposed_ports(source):
    source = Path(source)
    original = (source / NATIVE).read_bytes()
    if hashlib.sha256(original).hexdigest() != NATIVE_BEFORE:
        raise ValueError('exact_staged_C2_native_preimage_required')
    if (source / RUNTIME).exists():
        raise ValueError('new_C2_runtime_path_must_not_replace_existing_code')
    needle = b"    plan = validate_plan(read(plan_path))\n    require(resume or plan.get('authorized_wall_extension') is None, 'wall_extension_resume_only')"
    replacement = b"    plan = validate_plan(read(plan_path))\n    from gpu.c2_retention_runtime import bind_journal\n    StreamJournal = bind_journal(StreamJournal, plan)\n    require(resume or plan.get('authorized_wall_extension') is None, 'wall_extension_resume_only')"
    if original.count(needle) != 1:
        raise ValueError('one_exact_C2_run_entry_seam')
    return {NATIVE: original.replace(needle, replacement),
        RUNTIME: Path(__file__).with_name('c2_retention_runtime.py').read_bytes()}


def changes_for(source):
    outputs = proposed_ports(source)
    return {name: dict(before=NATIVE_BEFORE if name == NATIVE else None,
        after=hashlib.sha256(data).hexdigest()) for name, data in outputs.items()}
