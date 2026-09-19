"""Transmit the published exact Builder text over the original node route, CPU only."""

import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
COMMIT = '4813989c2e26fb3f3bfd72f0db4f6857187b6ed8'
DOCUMENT = 'research_loop/workers/replication_sprint_20260919/operations/BUILDER_ENTRIES.txt'


def main():
    raw = subprocess.run(['git', 'show', COMMIT + ':' + DOCUMENT], cwd=REPO,
        check=True, capture_output=True).stdout
    entry = [line for line in raw.decode().splitlines() if line.startswith('[Builder] 2026-09-19T14:31Z')]
    if len(entry) != 1:
        raise ValueError('exact_published_builder_entry_required')
    publication = dict(git_commit=COMMIT, repo_path=DOCUMENT,
        published_document_sha256=hashlib.sha256(raw).hexdigest(), entry=entry[0],
        entry_sha256=hashlib.sha256(entry[0].encode()).hexdigest())
    program = (HERE / 'math_b_admission_cpu.py').read_text() + '\nmain(' + repr(publication) + ')\n'
    with (HERE / 'MATH_B_BUILDER1431_CPU_ADMISSION.json').open('x') as output, \
            (HERE / 'MATH_B_BUILDER1431_CPU_ADMISSION.stderr').open('x') as errors:
        result = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'),
            'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -'],
            cwd=REPO, input=program, text=True, stdout=output, stderr=errors, timeout=250)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
