"""Same bounded parent transport bound only to the new sibling root."""

import importlib.util
from pathlib import Path


ROOT = Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')


if __name__ == '__main__':
    spec = importlib.util.spec_from_file_location('r232_original_parent_io', ROOT / 'parent_io_original.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.main()
