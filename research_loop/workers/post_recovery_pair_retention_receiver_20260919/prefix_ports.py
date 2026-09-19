"""Propose exact new epoch bytes only; old epochs and shared files are read-only."""

import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent


def replace_once(content, before, after):
    if content.count(before.encode()) != 1:
        raise ValueError('exact_one_prefix_integration_seam_required')
    result = content.replace(before.encode(), after.encode(), 1)
    compile(result, '<pair_epoch4_source_port>', 'exec')
    return result


def proposed(source, reader_bytes, proof_bytes):
    source = Path(source)
    runtime = (source / 'gpu/pair_retention_runtime.py').read_bytes()
    runtime = replace_once(runtime, '    class RetentionJournal(base):\n',
        '    from gpu.pair_prefix_authority import reader_argument, admission_argument\n'
        '    prefix_proof = reader_argument(plan, token, selection)\n\n'
        '    prefix_admission = admission_argument(plan, token, selection)\n\n'
        '    class RetentionJournal(base):\n')
    runtime = replace_once(runtime, '            return scan(self, selection)\n',
        '            return scan(self, selection, prefix_proof=prefix_proof, prefix_admission=prefix_admission)\n')
    original = (source / 'gpu/r205_runtime.py').read_bytes()
    native = replace_once(original,
        "    elif args.mode == 'native':\n        install_runtime(plan)\n        guard.native_entry(args.config)\n",
        "    elif args.mode == 'native':\n"
        '        from gpu.pair_prefix_authority import admitted_prefix\n'
        '        with admitted_prefix(config, plan, guard_path=args.config):\n'
        '            install_runtime(plan)\n            guard.native_entry(args.config)\n')
    if hashlib.sha256((source / 'gpu/checkpoint_tail_runtime.py').read_bytes()).hexdigest() != '972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e':
        raise ValueError('exact_original_reader_required')
    files = {'gpu/checkpoint_tail_runtime.py': reader_bytes,
        'gpu/immutable_prefix_proof.py': proof_bytes, 'gpu/pair_prefix_authority.py': (HERE / 'prefix_authority.py').read_bytes(),
        'gpu/pair_retention_runtime.py': runtime, 'gpu/r205_runtime.py': native}
    for name, content in files.items():
        compile(content, name, 'exec')
    return files, {name: {'before': hashlib.sha256((source / name).read_bytes()).hexdigest()
        if (source / name).exists() else None, 'after': hashlib.sha256(content).hexdigest()}
        for name, content in files.items()}
