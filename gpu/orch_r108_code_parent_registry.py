"""Bounded metadata-only exclusions; no raw outcomes or provider transcripts."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from organism_v6 import orch_r108_code_parent as policy


def collect(roots):
    identifiers, prompts, questions, files = set(), set(), set(), {}
    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            for key in ('task_id', 'id'):
                if isinstance(value.get(key), (str, int)):
                    identifiers.add(str(value[key]))
            for key in ('prompt_sha256', 'prompt_hash'):
                if isinstance(value.get(key), str):
                    prompts.add(value[key])
            for key in ('question_sha256', 'question_hash'):
                if isinstance(value.get(key), str):
                    questions.add(value[key])
            for key in ('prompt', 'question', 'text'):
                if isinstance(value.get(key), str):
                    prompts.add(policy.digest(value[key]))
                    questions.add(policy.question_hash(value[key]))
            for key, item in value.items():
                if key not in ('oracle', 'tests', 'response', 'outcome', 'raw', 'expected', 'messages'):
                    visit(item)
    for root in roots:
        if not root.exists():
            continue
        for directory, children, names in os.walk(root):
            children[:] = [name for name in children if name not in ('source', 'native', 'readout', 'raw',
                'raw_archive', 'parent_transcripts', '.git', '.cache', 'venv', '__pycache__', 'gpu_artifacts_local')
                and not Path(directory, name).is_symlink()]
            for name in names:
                if not name.endswith('.json') or not any(word in name.upper()
                        for word in ('COHORT', 'ROSTER', 'REGISTRY', 'TASKS', 'EXCLUSION')):
                    continue
                path = Path(directory) / name
                if path.is_symlink() or path.stat().st_size > 8_000_000:
                    continue
                content = path.read_bytes()
                visit(json.loads(content))
                files[str(path)] = hashlib.sha256(content).hexdigest()
    visit(policy.anchors.tasks() + policy.capability.tasks())
    return dict(task_ids=sorted(identifiers), prompt_hashes=sorted(prompts), question_hashes=sorted(questions),
        metadata_sources=files, raw_included=False, fixed32_and_all64anchors=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('roots', nargs='+', type=Path)
    arguments = parser.parse_args()
    print(json.dumps(collect(arguments.roots), sort_keys=True))
