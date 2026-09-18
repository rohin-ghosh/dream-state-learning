"""Publish derived, sanitized worker evidence without changing the raw originals."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


OMIT_TREES = {'.git', 'commit-worktree', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
TEXT_SUFFIXES = {'.json', '.jsonl', '.md', '.txt', '.py', '.sh', '.log', '.tsv', '.csv', '.yaml', '.yml',
                 '.toml', '.ini', '.patch', '.diff', '.stderr', '.stdout', '.complete', ''}
IP = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
HOST = re.compile(r'\b(?:ipp2-[a-z0-9-]+|a4u8g-[a-z0-9-]+)\b', re.I)
TOKEN = re.compile(r'\b(?:sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|'
                   r'xox[baprs]-[A-Za-z0-9-]+|AKIA[A-Z0-9]{16})\b')
PRIVATE_KEY = re.compile(r'-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----', re.S)
AUTH = re.compile(r'(?i)(Bearer\s+)[A-Za-z0-9._~+/-]{12,}=*')
SECRET_FIELD = re.compile(r'(?i)(["\'](?:api_key|access_token|refresh_token|id_token|client_secret|'
                          r'private_key|password|passwd|authorization|cookie|aws_secret_access_key)["\']\s*:\s*)'
                          r'(["\'])(.*?)(\2)')


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def digest_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def host_tokens(root):
    tokens = set()
    path = root / 'gpu/hosts.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if '_NODE=' not in line or line.lstrip().startswith('#'):
                continue
            value = line.split('=', 1)[1].strip().strip('"\'').split('@')[-1].split(':')[0]
            if value and re.fullmatch(r'[A-Za-z0-9.-]+', value):
                tokens.add(value)
    return sorted(tokens, key=len, reverse=True)


def sanitize(text, hosts):
    changes = Counter()
    for name, pattern, replacement in (
        ('private_key', PRIVATE_KEY, '[REDACTED_PRIVATE_KEY]'),
        ('credential', TOKEN, '[REDACTED_CREDENTIAL]'),
        ('authorization', AUTH, r'\1[REDACTED_CREDENTIAL]'),
        ('secret_field', SECRET_FIELD, r'\1\2[REDACTED_SECRET]\2'),
        ('address', IP, '[REDACTED_ADDRESS]'),
        ('hostname', HOST, '[REDACTED_HOST]'),
    ):
        text, count = pattern.subn(replacement, text)
        changes[name] += count
    for host in hosts:
        count = text.count(host)
        if count:
            text = text.replace(host, '[REDACTED_HOST]')
            changes['hostname'] += count
    return text, {key: value for key, value in changes.items() if value}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def coordination(root, worktree, hosts):
    relative = Path('research_loop/COORDINATION.md')
    raw = (root / relative).read_bytes()
    local = raw.decode()
    base = subprocess.check_output(['git', 'show', 'HEAD:' + str(relative)], cwd=root, text=True)
    remote = (worktree / relative).read_text()
    known = set(base.split('\n\n')) | set(remote.split('\n\n'))
    additions = []
    for block in local.split('\n\n'):
        if block.strip() and block not in known:
            additions.append(block)
            known.add(block)
    appendix = '\n\n'.join(additions)
    clean, changes = sanitize(appendix, hosts)
    heading = ('\n\n## VM-only evidence preservation — ' + datetime.now(timezone.utc).isoformat() +
               '\n\nMerged append-only; existing origin entries retained. Infrastructure/credentials '
               'are redacted in this published derivative. Original local bytes remain unchanged; '
               'source SHA256 `' + digest_bytes(raw) + '`.\n\n')
    (worktree / relative).write_text(remote.rstrip() + heading + clean + '\n')
    return dict(source_sha256=digest_bytes(raw), added_blocks=len(additions), redactions=changes,
                published_sha256=digest_file(worktree / relative))


def reason(path, relative, size):
    parts = [part.lower() for part in relative.parts]
    name = path.name.lower()
    if any(part == 'private' or 'credentials' in part for part in parts) or '.private.' in name:
        return 'private_or_credentials_manifest_only'
    if 'reference_panels' in name or name in {'hosts.env', '.env', 'api_request.json', 'auth.json'}:
        return 'private_input_manifest_only'
    if any(part == 'snapshot' or part == 'source' or part.startswith('source_') for part in parts[:-1]):
        return 'copied_source_tree_manifest_only'
    if size > 1048576:
        return 'large_file_manifest_only'
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return 'binary_or_nontext_manifest_only'
    return None


def workers(root, worktree, hosts, report):
    base = root / 'research_loop/workers'
    selected = [directory for directory in base.iterdir() if directory.is_dir() and
                (re.search(r'202609(?:17|18)', directory.name) or
                 directory.name in {'r167_a100_parent_rollout', 'r167_legacy_parent_rollout',
                                    'r167_object_survival', 'r168_targeted_replay'})]
    totals = Counter()
    report['directories'] = []
    for directory in sorted(selected):
        records, counts = [], Counter()
        for parent, children, filenames in os.walk(directory):
            children[:] = sorted(name for name in children if name not in OMIT_TREES)
            for name in sorted(filenames):
                path = Path(parent) / name
                relative = path.relative_to(root)
                if path.is_symlink():
                    counts['symlink_not_followed'] += 1
                    continue
                try:
                    before = path.stat()
                    raw_sha = digest_file(path)
                    entry = dict(path=sanitize(str(relative), hosts)[0], raw_sha256=raw_sha,
                                 bytes=before.st_size, storage='orchestrator_VM_original_path',
                                 node_aliases=[part for part in relative.parts if re.fullmatch(r'(?:node|ovx)[0-9]+', part)])
                    decision = reason(path, relative, before.st_size)
                    if decision is None:
                        raw = path.read_bytes()
                        if digest_bytes(raw) != raw_sha:
                            decision = 'changed_during_snapshot_manifest_only'
                        else:
                            try:
                                text = raw.decode('utf-8')
                            except UnicodeError:
                                decision = 'binary_manifest_only'
                    if decision is None:
                        cleaned, changes = sanitize(text, hosts)
                        destination = worktree / entry['path']
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_text(cleaned)
                        entry.update(published_sha256=digest_bytes(cleaned.encode()), redactions=changes)
                        counts['published_text'] += 1
                    else:
                        entry['omitted_reason'] = decision
                        counts[decision] += 1
                    after = path.stat()
                    entry['source_changed_while_hashing'] = (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
                    records.append(entry)
                except FileNotFoundError:
                    counts['concurrent_removed_file'] += 1
        manifest = worktree / directory.relative_to(root) / 'PRESERVATION_MANIFEST_20260918.jsonl'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        with manifest.open('w') as stream:
            for entry in records:
                stream.write(json.dumps(entry, sort_keys=True) + '\n')
        report['directories'].append(dict(directory=directory.name, records=len(records), counts=dict(counts),
                                          manifest_sha256=digest_file(manifest)))
        totals.update(counts)
        print(json.dumps(dict(directory=directory.name, counts=dict(counts))), flush=True)
        write_json(worktree / 'research_loop/workers/rohin206_code_preservation_20260918/PRESERVATION_PROGRESS.json', report)
    report['totals'] = dict(totals)
    report['complete_utc'] = datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--worktree', type=Path, required=True)
    parser.add_argument('--workers', action='store_true')
    args = parser.parse_args()
    root, worktree = args.root.resolve(), args.worktree.resolve()
    hosts = host_tokens(root)
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(), scope='sanitized_derivative_not_original_bytes',
                  original_files_modified=False, coordinate=coordination(root, worktree, hosts))
    if args.workers:
        workers(root, worktree, hosts, report)
    write_json(worktree / 'research_loop/workers/rohin206_code_preservation_20260918/PRESERVATION_RECEIPT.json', report)
    print(json.dumps({key: value for key, value in report.items() if key != 'directories'}), flush=True)


if __name__ == '__main__':
    main()
