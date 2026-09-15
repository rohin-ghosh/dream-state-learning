from pathlib import Path
import subprocess


def test_current_coordination_has_no_unresolved_merge_markers():
    root = Path(__file__).resolve().parents[1]
    document = root / 'research_loop' / 'COORDINATION.md'
    markers = [number for number, line in enumerate(document.read_text().splitlines(), 1)
               if line.startswith(('<<<<<<< ', '>>>>>>> ')) or line == '=======']
    assert not markers, f'Unresolved merge markers at lines {markers}'


def test_raw_evidence_is_ignored_but_compact_manifests_are_not():
    root = Path(__file__).resolve().parents[1]
    for suffix in ('source.tar', 'capture.tar.gz', 'adapter.safetensors',
                   'CAPSULE.json', 'CALL_0001.json', 'raw/shard0/task.json'):
        result = subprocess.run(['git', 'check-ignore', '--no-index',
                                 f'research_notes/analysis/storage_policy_probe/{suffix}'],
                                cwd=root, capture_output=True, text=True)
        assert result.returncode == 0, suffix
    result = subprocess.run(['git', 'check-ignore', '--no-index',
                             'research_notes/analysis/storage_policy_probe/MANIFEST.json'],
                            cwd=root, capture_output=True, text=True)
    assert result.returncode == 1
