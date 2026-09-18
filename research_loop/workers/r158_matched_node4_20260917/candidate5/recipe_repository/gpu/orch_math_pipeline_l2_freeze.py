"""Freeze local corpus exclusions and source before any campaign outcome."""

import argparse
import io
from pathlib import Path
import tarfile

from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from organism_v6 import orch_l1_bootstrap_transfer as exclusion_source
from organism_v6 import orch_math_pipeline_l2 as policy


def freeze(repository, output):
    assert not (output / 'COHORT.json').exists(), 'cohort_already_frozen'
    identifiers, questions, manifests = set(), set(), {}
    names = {'COHORT.json', 'ROSTER.json', 'ADMITTED.json', 'CORPUS_MANIFEST.json'}
    for directory in ('research_notes/analysis', 'gpu_artifacts_local'):
        for path in sorted((repository / directory).rglob('*.json')):
            if output in path.parents or any(part.startswith('source') for part in path.parts):
                continue
            if path.name not in names and not path.name.startswith('TASKS'):
                continue
            document = read(path)
            found_ids, found_questions = exclusion_source.exclusions([document])
            identifiers.update(found_ids)
            questions.update(found_questions)
            manifests[str(path.relative_to(repository))] = sha(path)
    assert len(identifiers) >= 1472 and manifests
    write(output / 'COHORT.json', policy.cohort(identifiers, questions))
    write(output / 'DATA_PROVENANCE.json', dict(manifests=manifests, prospective=True,
        native_calls=0, outcomes_read=False, cohort_sha256=sha(output / 'COHORT.json'),
        excluded_ids=len(identifiers), excluded_question_hashes=len(questions),
        source='Deterministic cheap exact-verifiable math gym; no downloads or new model.',
        novelty='Disjoint registered experiment IDs and normalized questions, not pretraining novelty.'))


def archive(repository, output):
    baseline = repository / 'research_notes/analysis/orch_l2_rich_math_20260915_attempt1/source.tar'
    additions = [path for directory in ('gpu', 'organism_v6', 'tests')
        for path in (repository / directory).glob('orch_math_pipeline_l2*.py')]
    additions.extend(repository / name for name in ('gpu/orch_rich_hot_a100_scan.py',
        'gpu/orch_rich_hot_a100_minor_scan.py', 'organism_v6/orch_rich_hot_a100.py',
        'organism_v6/orch_l1_bootstrap_transfer.py'))
    replacements = {str(path.relative_to(repository)): path for path in additions}
    with tarfile.open(baseline) as source, tarfile.open(output / 'source.tar', 'w') as target:
        for member in source:
            if member.name.removeprefix('./') in replacements:
                continue
            assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            assert member.isfile() or member.isdir()
            target.addfile(member, source.extractfile(member) if member.isfile() else None)
        for name, path in sorted(replacements.items()):
            data = path.read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            target.addfile(info, io.BytesIO(data))
    print('source_sha256=' + sha(output / 'source.tar'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('cohort', 'archive'))
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    (freeze if options.phase == 'cohort' else archive)(options.repository.resolve(), options.output.resolve())
