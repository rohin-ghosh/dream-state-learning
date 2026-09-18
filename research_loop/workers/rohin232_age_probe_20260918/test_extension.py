from types import SimpleNamespace

import pytest

from research_loop.workers.rohin232_age_probe_20260918.extension import panel_scores


def test_original_panels_reused_without_reselection_or_model_call():
    scenes=SimpleNamespace(contests=[SimpleNamespace(canonical_scene=scene) for scene in ('scene one','scene two','scene three')])
    rows=[dict(selected=[dict(scene=scene.canonical_scene,caption='synthetic private reference')]*64,
        scores=[0.25]*64) for scene in scenes.contests]
    panels=panel_scores(rows,scenes)
    assert len(panels)==3 and all(scores==[0.25]*64 for scores in panels.values())
    with pytest.raises(ValueError,match='same_three_panel_scenes'):
        panel_scores(rows[:2],scenes)
    with pytest.raises(ValueError,match='original_64_reference_panel'):
        panel_scores([dict(rows[0],scores=[0.25])]+rows[1:],scenes)
