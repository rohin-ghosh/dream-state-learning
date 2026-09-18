"""Same-life saved-boundary recovery; retain each existing confined entrypoint."""

from pathlib import Path


CAPTIONS = {
    'r213_r226_caption_observation_fork': 0,
    'r213_r226_caption_perspective_fork': 3,
    'r213_r226_caption_revision_fork': 5,
    'r213_r226_caption_selfderive_fork': 6,
    'r213_r226_caption_unparented_fork': 7,
}
MATH = {'r213_math_a': 1, 'r213_math_b_fork': 2, 'r213_math_c': 4}


def entrypoint(plan):
    name = Path(plan['source_root']).parent.name
    allowed = dict(CAPTIONS, **MATH)
    if name not in allowed or plan['physical'] != allowed[name]:
        raise ValueError('only_eight_exact_kept_lives_on_original_devices')
    return 'gpu.r227_caption_runtime' if name in CAPTIONS else 'gpu.r226_math_runtime'


def main():
    import importlib
    import json
    import sys
    from gpu import r205_runtime as runtime
    from gpu.r213_recovery_runtime import RecoveryJournal

    config = json.loads(Path(sys.argv[sys.argv.index('--config') + 1]).read_bytes())
    plan = json.loads(Path(config['plan_path']).read_bytes())
    original_main = runtime.main

    def recovered_main():
        runtime.MODULE = 'gpu.r233_recovery_runtime'
        runtime.ControlJournal = RecoveryJournal
        return original_main()

    runtime.main = recovered_main
    importlib.import_module(entrypoint(plan)).main()


if __name__ == '__main__':
    main()
