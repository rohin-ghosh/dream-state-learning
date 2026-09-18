"""The same read-only birth observer, bound to the assigned frozen sibling."""

import importlib.util
from pathlib import Path


if __name__ == '__main__':
    root = Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')
    spec = importlib.util.spec_from_file_location('r232_birth_observer', root / 'observe_birth_source.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    module.main()
