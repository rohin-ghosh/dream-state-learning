"""Allowlisted sanitized source/report publication from a separate checkout."""

import json
import os
from pathlib import Path
import shutil
import subprocess


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
RELATIVE = OWN.relative_to(REPO)
CHECKOUT = OWN / '.publication'
CODE = ('.gitignore', 'reader.py', 'audit.py', 'collect.py', 'publish.py', 'service.py',
        'test_audit.py', 'test_reader.py', 'README.md', 'TO_OWNERS.md')


def git(*arguments):
    return subprocess.run(['git', '-C', str(CHECKOUT), *arguments], check=True,
        text=True, capture_output=True).stdout.strip()


def safe_public(path):
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('bounded_public_artifact')
    for forbidden in (b'/localhome/', b'/data/home/', b'BEGIN PRIVATE KEY', b'Authorization:', b'Bearer ', b'OPENAI_API_KEY', b'NVIDIA_API_KEY'):
        if forbidden in raw:
            raise ValueError('public_privacy_scan')
    if path.suffix == '.json':
        def scan(value):
            if isinstance(value, dict):
                if set(value) & {'text', 'raw', 'messages', 'resume_state', 'source_response', 'prompt', 'api_key'}:
                    raise ValueError('raw_content_not_public')
                for child in value.values():
                    scan(child)
            elif isinstance(value, list):
                for child in value:
                    scan(child)
        scan(json.loads(raw))
    return raw


def publish():
    if not CHECKOUT.is_dir():
        raise ValueError('separate_publication_checkout_required')
    if git('status', '--porcelain'):
        raise ValueError('clean_publication_checkout_required')
    git('fetch', 'origin', 'main')
    git('merge', '--ff-only', 'FETCH_HEAD')
    target = CHECKOUT / RELATIVE
    target.mkdir(parents=True, exist_ok=True)
    selected = []
    for name in CODE:
        source = OWN / name
        if not source.is_file():
            continue
        shutil.copyfile(source, target / name)
        selected.append(str(RELATIVE / name))
    for source in sorted((OWN / 'public').rglob('*')):
        if not source.is_file() or source.suffix not in ('.json', '.md'):
            continue
        data = safe_public(source)
        relative = source.relative_to(OWN)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        selected.append(str(RELATIVE / relative))
    git('add', '--', *selected)
    git('diff', '--cached', '--check')
    names = git('diff', '--cached', '--name-only').splitlines()
    if not names:
        return dict(commit=git('rev-parse', 'HEAD'), changed=False)
    if not set(names) <= set(selected):
        raise ValueError('publication_scope_changed')
    git('commit', '-m', 'Publish bounded R232 correction-sequence audit')
    try:
        git('push', 'origin', 'HEAD:main')
    except subprocess.CalledProcessError:
        git('fetch', 'origin', 'main')
        git('rebase', 'FETCH_HEAD')
        git('push', 'origin', 'HEAD:main')
    return dict(commit=git('rev-parse', 'HEAD'), changed=True, files=names)


if __name__ == '__main__':
    print(json.dumps(publish(), sort_keys=True))
