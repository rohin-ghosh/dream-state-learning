"""Exact R170 v1 adapter with narrow death-recovery and guard-reference repairs."""

import ast
import hashlib
import importlib.util
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
V1_SHA256 = 'e2c0307936d8be5cde38633464641e921761369bf5c2ca3f65f960f69dbdd69f'
RECOVERY_SHA256 = '4864af9e8e21aa3fa5fc0b141bddbb09900908aabf52d8141a730375b3c7553a'


def load_pinned(path, checksum):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError('frozen_recovery_dependency')
    return raw


def repaired_handoff(family, source):
    tree = ast.parse(source)
    handoff = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
    outer = handoff.body[-1]
    if not isinstance(outer, ast.Try):
        raise ValueError('frozen_handoff_outer_try')
    expected = ast.parse('''helper.resume_paused(paused, descriptors)
for descriptor in descriptors.values():
    os.close(descriptor)
os.close(lock)
for signum, handler in handlers.items():
    signal.signal(signum, handler)
''').body
    if [ast.dump(node) for node in outer.finalbody] != [ast.dump(node) for node in expected]:
        raise ValueError('frozen_cleanup_structure')
    outer.finalbody = ast.parse('pause_recovery.cleanup(paused, descriptors, lock, handlers, output)').body

    class Calls(ast.NodeTransformer):
        def __init__(self):
            self.pauses = 0
            self.resumes = 0

        def visit_Call(self, node):
            if ast.dump(node.func) == ast.dump(ast.parse('helper.pause_exact', mode='eval').body):
                if ast.dump(node) != ast.dump(ast.parse(
                        "helper.pause_exact(request['processes'][name], descriptors[name])", mode='eval').body):
                    raise ValueError('frozen_pause_call')
                self.pauses += 1
                return ast.copy_location(ast.parse(
                    "pause_recovery.pause(helper, request['processes'][name], descriptors[name], "
                    "request['processes'], descriptors, output)", mode='eval').body, node)
            if ast.dump(node.func) == ast.dump(ast.parse('helper.resume_paused', mode='eval').body):
                if ast.dump(node) != ast.dump(ast.parse('helper.resume_paused(paused, descriptors)', mode='eval').body):
                    raise ValueError('frozen_resume_call')
                self.resumes += 1
                return ast.copy_location(ast.parse('pause_recovery.resume(paused, descriptors)', mode='eval').body, node)
            return self.generic_visit(node)

    changes = Calls()
    handoff = changes.visit(handoff)
    if (changes.pauses, changes.resumes) != (1, 1):
        raise ValueError('exact_recovery_delta_only')
    module = ast.fix_missing_locations(ast.Module(body=[handoff], type_ignores=[]))
    exec(compile(module, family['__file__'], 'exec'), family)
    return family['handoff']


def adapter_namespace():
    raw = load_pinned(HERE / 'OPERATOR.py', V1_SHA256)
    load_pinned(HERE / 'RECOVERY.py', RECOVERY_SHA256)
    specification = importlib.util.spec_from_file_location('r170_recovery_v2', HERE / 'RECOVERY.py')
    recovery = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(recovery)
    adapter = dict(__name__='r170_frozen_adapter_v1', __file__=str(Path(__file__).resolve()))
    exec(compile(raw, adapter['__file__'], 'exec'), adapter)
    original_factory = adapter['family_namespace']
    original_guard = adapter['patched_guard']

    def factory():
        family = original_factory()
        family['pause_recovery'] = recovery.Recovery()
        source = load_pinned(HERE / 'FAMILY.py', adapter['FAMILY_SHA'])
        repaired_handoff(family, source)
        return family

    def patched_guard(source, reference):
        if (type(reference) is not dict or set(reference) != {'path', 'sha256'}
                or type(reference['sha256']) is not str or re.fullmatch('[0-9a-f]{64}', reference['sha256']) is None):
            raise ValueError('exact_hash_reference')
        path = Path(reference['path'])
        if not path.is_absolute() or '..' in path.parts or path != path.resolve():
            raise ValueError('canonical_absolute_path')
        return original_guard(source, reference)

    adapter.update(family_namespace=factory, patched_guard=patched_guard)
    return adapter


if __name__ == '__main__':
    adapter_namespace()['main']()
