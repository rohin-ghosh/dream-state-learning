import importlib.util
from pathlib import Path


def load_parent():
    path = Path(__file__).resolve().parents[1] / 'gpu/r216_c0_parent.py'
    spec = importlib.util.spec_from_file_location('c0_parent', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_c0_new_identity_and_quitting_point():
    parent = load_parent()
    assert 'name is C0' in parent.prompt(0)
    assert 'not the continuing original C2' in parent.prompt(0)
    assert 'second turn' in parent.prompt(1)
    assert parent.PROBLEMS[0] in parent.prompt(1)
    assert parent.PROBLEMS[1] in parent.prompt(2)
    assert 'no code executor is connected' in parent.prompt(2)


def test_parent_never_claims_child_completion_or_gives_old_answer():
    parent = load_parent()
    for turn in range(12):
        text = parent.prompt(turn)
        assert 'V = 3' not in text
        assert 'You completed' not in text
        assert text.isascii()
