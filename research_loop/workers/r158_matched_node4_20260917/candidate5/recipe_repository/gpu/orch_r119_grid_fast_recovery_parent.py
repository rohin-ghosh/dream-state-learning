"""A4 low-effort broker recovery era; existing request claims remain final."""

import importlib.util
from pathlib import Path


def source():
    path = Path(__file__).with_name('orch_r119_grid_fast_parent.py')
    spec = importlib.util.spec_from_file_location('prior_fast_parent', path)
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    text = previous.source()
    for before, after in {
        "('independent_r119_v1',)": "('independent_r119_recovery_v1', 'independent_r119_recovery_v2')",
        "('R119_GRID_INDEPENDENT_TERMINAL.json',)": "('R119_GRID_INDEPENDENT_RECOVERY_TERMINAL.json', 'R119_GRID_INDEPENDENT_RECOVERY_V2_TERMINAL.json')",
    }.items():
        if text.count(before) != 1:
            raise ValueError('exact_recovery_terminal_binding')
        text = text.replace(before, after)
    return text


if __name__ == '__main__':
    exec(compile(source(), __file__, 'exec'), {'__name__': '__main__', '__file__': __file__})
