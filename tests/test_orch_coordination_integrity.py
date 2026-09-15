from pathlib import Path


def test_current_coordination_has_no_unresolved_merge_markers():
    root = Path(__file__).resolve().parents[1]
    document = root / 'research_loop' / 'COORDINATION.md'
    markers = [number for number, line in enumerate(document.read_text().splitlines(), 1)
               if line.startswith(('<<<<<<< ', '>>>>>>> ')) or line == '=======']
    assert not markers, f'Unresolved merge markers at lines {markers}'
