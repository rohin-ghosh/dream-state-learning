"""Reuse the existing strong parent with current-shell credentials, never persist them."""

import inspect
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import caption_parent as previous


def renewed_source(source):
    seam = "deadline = min(epoch['baseline']['identity']['hard_end_unix'] - 60, time.time() + 10800)"
    if source.count(seam) != 1:
        raise ValueError('exact_existing_finite_parent_deadline_seam')
    return source.replace(seam, "deadline = epoch['baseline']['identity']['hard_end_unix'] - 60")


def main():
    previous.PRIVATE = HERE / 'caption_parent.private'
    previous.PUBLIC = HERE / 'caption_parent_public'
    previous.REMOTE = '/localhome/local-rohing/orch_rohin233_focus_node2_20260918/recovery_20260918T1646Z/caption_endpoint.py'
    previous.INSTRUCTION += (
        ' This is a finite renewal of the SAME R233 parented treatment after a runtime-wall outage, '
        'not a new birth or a fresh unparented control. Address only actual post-recovery output. '
        'Earlier incomplete sleep updates were archived, not claimed retained. Missing judge feedback '
        'is a service absence, not a caption verdict. No score or private judge content is available to you.')
    source = renewed_source(inspect.getsource(previous.serve))
    namespace = dict(previous.serve.__globals__)
    exec(compile(source, __file__ + ':renewed_finite_epoch', 'exec'), namespace)
    namespace['serve']()


if __name__ == '__main__':
    main()
