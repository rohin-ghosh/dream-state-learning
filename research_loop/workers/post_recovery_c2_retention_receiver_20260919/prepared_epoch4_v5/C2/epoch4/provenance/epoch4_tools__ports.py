"""Exact offline C2 epoch4 ports; immutable inputs are never edited."""

import ast
import hashlib
from pathlib import Path


READER = 'gpu/checkpoint_tail_runtime.py'
PROOF = 'gpu/immutable_prefix_proof.py'
AUTHORITY = 'gpu/c2_prefix_authority.py'
RUNTIME = 'gpu/c2_retention_runtime.py'
GUARD = 'gpu/orch_r125_continual_guard.py'
EXPECTED = {
    READER: '972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e',
    RUNTIME: '350802c5c996c3f5856fbb84f771f663df364a67abe87b809ada15840c7591e1',
    GUARD: '1b12ff40ae7d88c06b956cf8c624aa8b010781f66a4eb0f630455f1be5e9dab6',
}


def sha(content):
    return hashlib.sha256(content).hexdigest()


def replace_once(content, before, after):
    if content.count(before.encode()) != 1:
        raise ValueError('one_exact_C2_epoch4_seam_required:' + before[:70])
    result = content.replace(before.encode(), after.encode(), 1)
    compile(result, '<offline_C2_epoch4_candidate>', 'exec')
    return result


def authority_port(pair_bytes):
    result = pair_bytes.replace(b'PAIR_', b'C2_').replace(b'pair_', b'c2_')
    result = replace_once(result,
        "    require(proof['binding']['journal_type'] == ('gpu.r232_recovery:FrozenJournal' if plan['physical'] == 1\n"
        "        else 'gpu.r232_recovery:LearnerJournal'), 'original_c2_journal_family')\n",
        "    require(plan['physical'] == 1 and plan['hard_end_unix'] == 1789927200\n"
        "        and plan['gpu_uuid'] == 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'\n"
        "        and plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance'\n"
        "        and proof['binding']['journal_type'] == 'gpu.orch_r125_stream_journal:StreamJournal',\n"
        "        'original_learned_C2_journal_and_identity')\n")
    return result


def proposed(source, reader_port, proof_bytes, authority_bytes):
    source = Path(source)
    for name, expected in EXPECTED.items():
        if sha((source / name).read_bytes()) != expected:
            raise ValueError('exact_epoch3_preimage_required:' + name)
    if any((source / name).exists() for name in (PROOF, AUTHORITY)):
        raise ValueError('new_epoch4_helper_must_not_replace_existing_file')
    runtime = replace_once((source / RUNTIME).read_bytes(),
        '    class RetentionJournal(base):\n',
        '    from gpu.c2_prefix_authority import reader_arguments\n'
        '    prefix_arguments = reader_arguments(plan, token, selection)\n\n'
        '    class RetentionJournal(base):\n'
        '        def _scan(self):\n'
        '            if prefix_arguments["prefix_proof"] is None or self._checkpoint_tail is None:\n'
        '                return super()._scan()\n'
        '            from gpu.checkpoint_tail_runtime import scan\n'
        '            return scan(self, self._checkpoint_tail, **prefix_arguments)\n\n')
    guard = replace_once((source / GUARD).read_bytes(),
        "    child.run(config['plan_path'], resume=config['resume'])\n",
        '    from gpu.c2_prefix_authority import admitted_prefix\n'
        '    with admitted_prefix(config, plan, guard_path=config_path):\n'
        "        child.run(config['plan_path'], resume=config['resume'])\n")
    original_functions = {item.name: ast.dump(item) for item in ast.parse((source / GUARD).read_bytes()).body
        if isinstance(item, ast.FunctionDef) and item.name != 'native_entry'}
    candidate_functions = {item.name: ast.dump(item) for item in ast.parse(guard).body
        if isinstance(item, ast.FunctionDef) and item.name != 'native_entry'}
    if original_functions != candidate_functions:
        raise ValueError('original_admission_validate_supervise_dispatch_functions_unchanged')
    files = {READER: reader_port((source / READER).read_bytes()), PROOF: proof_bytes,
        AUTHORITY: authority_bytes, RUNTIME: runtime, GUARD: guard}
    for name, content in files.items():
        compile(content, name, 'exec')
    return files
