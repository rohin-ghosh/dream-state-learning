"""Check only explicitly staged node1 evidence and the coordination append."""

import argparse
import json
from pathlib import Path
import re
import subprocess


SCOPE = 'research_loop/workers/rohin233_focus_node1_20260918/'
FORBIDDEN = (
    rb'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    rb'(?i)\b(?:ipp[0-9]-[a-z0-9-]+|a4u8g-[a-z0-9-]+)\b',
    rb'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    rb'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b',
    rb'(?i)(?:https?|ssh)://',
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('worktree', type=Path)
    arguments = parser.parse_args()

    def git(*command):
        return subprocess.check_output(['git', '-C', str(arguments.worktree), *command])

    paths = git('diff', '--cached', '--name-only', '-z').decode().split('\0')
    rows = []
    for path in filter(None, paths):
        if path != 'research_loop/COORDINATION.md' and not path.startswith(SCOPE):
            raise ValueError('unexpected_staged_scope:' + path)
        if any(part in Path(path).parts for part in ('private', 'publish-worktree', '__pycache__')):
            raise ValueError('private_artifact_staged:' + path)
        content = git('show', ':' + path)
        if path == 'research_loop/COORDINATION.md':
            original = git('show', 'HEAD:' + path)
            if not content.startswith(original):
                raise ValueError('coordination_not_append_only')
            content = content[len(original):]
        if len(content) > 2_000_000 or b'\x00' in content:
            raise ValueError('binary_or_oversized_file:' + path)
        for pattern in FORBIDDEN:
            if re.search(pattern, content):
                raise ValueError('hostname_address_or_secret_pattern:' + path)
        rows.append(dict(path=path, checked_bytes=len(content)))
    print(json.dumps(dict(status='PASS', staged_files=rows,
          scope_and_append_only_checked=True, binary_size_and_sensitive_patterns_checked=True), indent=2))


if __name__ == '__main__':
    main()
