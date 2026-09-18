"""Bounded live parent configuration inventory; no provider or process changes."""

import json
from pathlib import Path
import time

import legacy_takeover as legacy


def observe():
    rows = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            identity = legacy.identity(int(directory.name))
            argv = identity['argv']
            if (not Path(argv[0]).name.startswith('python') or '--config' not in argv
                    or not any('parent' in argument.lower() for argument in argv[:5])):
                continue
            config_path = Path(argv[argv.index('--config') + 1])
            if config_path.stat().st_size > 1048576:
                continue
            config = json.loads(legacy.read(config_path))
            output = Path(argv[argv.index('--output') + 1]) if '--output' in argv else None
            results = []
            if output:
                for path in sorted(output.glob('parent_*/RESULT.json'))[:1000]:
                    if path.stat().st_size > 1048576:
                        continue
                    result = json.loads(legacy.read(path))
                    results.append(dict(reference=legacy.ref(path), status=result.get('status'),
                        finished_unix=result.get('finished_unix'),
                        publication=result.get('inbox_publication')))
            after = legacy.identity(identity['pid'])
            if any(after[key] != identity[key] for key in ('start_ticks', 'argv', 'uid')):
                continue
            rows.append(dict(identity=identity, config=legacy.ref(config_path),
                fields={key: config[key] for key in ('root', 'node', 'branch', 'source_root',
                    'hard_end_unix', 'principles_path', 'principles_sha256', 'remote_root',
                    'deadline_unix', 'schema') if key in config},
                output=str(output) if output else None, results=results))
        except (OSError, ValueError, IndexError):
            continue
    receipt = legacy.HERE / ('COVERAGE_LOCAL_' + str(time.time_ns()) + '.json')
    legacy.write(receipt, dict(observed_unix=time.time(), parents=rows,
        limits=dict(config_bytes=1048576, results_per_output=1000), no_signals=True))
    print(json.dumps(legacy.ref(receipt)))


if __name__ == '__main__':
    observe()
