"""Load a hash-bound CPU-only F4 overlay without editing a running source tree."""

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def bootstrap(root):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_empty_visibility_required')
    manifest = json.loads((root / 'SOURCE_SHA256.json').read_text())
    for name, expected in manifest.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
            raise ValueError('CPU_source_snapshot_drift:' + name)
    names = ('organism_v6.orch_r109_grid', 'organism_v6.orch_r111_grid',
        'organism_v6.orch_r111_grid_v4', 'gpu.orch_r110_claude_broker',
        'gpu.orch_r111_grid_prepare', 'gpu.orch_r111_grid_prepare_v4', 'gpu.orch_r111_grid_release')
    for name in names:
        parent_name, attribute = name.rsplit('.', 1)
        parent = importlib.import_module(parent_name)
        spec = importlib.util.spec_from_file_location(name, root / (name.replace('.', '/') + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        setattr(parent, attribute, module)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('test', 'prepare'))
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    bootstrap(arguments.source_root)
    if arguments.mode == 'test':
        import pytest
        sys.exit(pytest.main([str(arguments.source_root / 'tests' / name) for name in
            ('test_orch_r111_grid_v4.py', 'test_orch_r111_grid.py', 'test_orch_r111_grid_release.py')]
            + ['-q', '-p', 'no:cacheprovider']))
    from gpu import orch_r111_grid_prepare_v4 as preparation
    if arguments.output is None:
        raise ValueError('native_output_required')
    print(json.dumps(preparation.prepare(arguments.source_root, arguments.output), sort_keys=True))
