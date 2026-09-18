"""Reuse the identity-bound drained P3 CPU handoff, preserving its first epoch."""

from pathlib import Path

import p3_handoff
import p3_parent_v2


def exact_parent(arguments, manifest):
    expected = ['-B', str(p3_parent_v2.HERE / 'p3_parent.py'), 'serve',
        '--manifest-sha256', manifest['predecessor_manifest_sha256']]
    if arguments[1:] != expected or Path(arguments[0]).name not in ('python', 'python3'):
        raise ValueError('exact_running_R233_P3_CPU_publisher_required')


def main():
    replacements = tuple((before, after) for before, after in (
        ('P3_MANIFEST.json', 'P3_VALIDATION_MANIFEST.json'),
        ('P3_HANDOFF.lock', 'P3_VALIDATION_HANDOFF.lock'),
        ('P3_HANDOFF.json', 'P3_VALIDATION_HANDOFF.json'),
        ('P3_LIVE.json', 'P3_VALIDATION_LIVE.json'),
        ('P3_PARENT.log', 'P3_PARENT_VALIDATION.log'),
        ("'p3_parent.py'", "'p3_parent_v2.py'"),
        ('NEW_R233_STRONG_PARENT_TREATMENT', 'NON_MATERIAL_PARENT_VALIDATOR_REPAIR')))
    source = p3_parent_v2.repair.inspect.getsource(p3_handoff.main)
    namespace = dict(p3_handoff.main.__globals__, p3_parent=p3_parent_v2,
        exact_parent=exact_parent)
    for before, after in replacements:
        if before not in source:
            raise ValueError('bound_handoff_projection:' + before)
        source = source.replace(before, after)
    exec(compile(source, __file__ + ':main', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
