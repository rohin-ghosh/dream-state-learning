"""Final explicitly allocated terminal era; original provider and claims unchanged."""

import hashlib
import importlib.util
from pathlib import Path


def configured():
    path = Path(__file__).with_name('orch_r118_claude_recovery_rebind.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != '105f9a607608e4880c8b5e76ef4988785407f853ec631b5921de7f9130de5eb5':
        raise ValueError('exact_settled_identity_dependency')
    spec = importlib.util.spec_from_file_location('settled_recovery', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    custody = module.configure(module.load_custody(path.with_name('orch_r118_claude_terminal_rebind.py')))
    custody.TERMINALS['F4'] = 'R118_GRID_PARALLEL_RECOVERY_V2_TERMINAL.json'
    custody.__file__ = str(Path(__file__).resolve())
    return custody


if __name__ == '__main__':
    configured().main()
