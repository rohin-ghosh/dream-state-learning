"""Audit a completed derived publication, preserving hashes of every redaction."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat

from preserve_latest import digest_bytes, digest_file, host_tokens, sanitize, write_json


HOST_FIELD = re.compile(r'(?i)("(?:host|hostname|node_hostname|remote_host)"\s*:\s*)"[^"\n]*"')
URL_HOST = re.compile(r'(?i)((?:https?|ssh)://)(?:[^/@\s"\']+@)?[A-Za-z0-9.-]+(?=[:/\s"\'])')
EMAIL = re.compile(r'(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}\b')
JWT = re.compile(r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b')
IPV6 = re.compile(r'(?i)(?<![\w:])(?:[0-9a-f]{0,4}:){4,7}[0-9a-f]{0,4}(?![\w:])')
ESCAPED_SECRET = re.compile(r'(?i)(\\"(?:api_key|access_token|refresh_token|client_secret|password|authorization)\\"\s*:\s*\\")[^"\n]*?(\\")')
EXTRA_TOKEN = re.compile(r'\b(?:gh[ousr]_[A-Za-z0-9]{25,}|hf_[A-Za-z0-9]{25,}|ASIA[A-Z0-9]{16})\b')
ASSIGNMENT = re.compile(r'(?i)(\b(?:[A-Z0-9_]+_)?(?:api_key|access_token|refresh_token|auth_token|client_secret|secret_key|password|passwd)\b\s*=\s*)(["\'])([^"\'\r\n]{8,})(["\'])')
PRIVATE_FLAG = re.compile(r'"(?:private_do_not_export_raw|private_examples|sealed_raw)"\s*:\s*true', re.I)
PRIVATE_KEYS = {'reference_panel', 'reference_panels', 'reference_captions', 'panel_captions',
                'reference_texts', 'private_examples', 'sealed_raw', 'calibration_curve',
                'calibration_curves', 'heldout_rows', 'heldout_examples', 'caption_rows'}
DENIED_PARTS = {'private', 'sealed', 'final', 'credentials', 'secrets', '.ssh', '.git',
                'reference_panel', 'reference_panels', 'data', 'payload', 'payloads', 'rows', 'weights'}
DATA_SUFFIXES = {'.json', '.jsonl', '.csv', '.tsv', '.txt', '.log', '.stderr', '.stdout'}
MAX_BYTES = 1048576


def atomic_text(path, text):
    temporary = path.with_name(path.name + '.publication-tmp')
    temporary.write_text(text)
    os.replace(temporary, path)


def path_omission(relative):
    parts = [part.lower() for part in relative.parts]
    if relative.is_absolute() or '..' in parts or parts[:2] != ['research_loop', 'workers']:
        return 'unsafe_publication_path'
    if any(part in DENIED_PARTS for part in parts):
        return 'private_or_dataset_path_manifest_only'
    if relative.name.lower() in {'hosts.env', '.env', 'auth.json', 'api_request.json'}:
        return 'credentials_path_manifest_only'
    if relative.suffix.lower() in DATA_SUFFIXES:
        if re.search(r'private|sealed|held.?out|reference.?panels?|locked.?final|(?:^|_)final(?:_|\.)', relative.name, re.I):
            return 'private_or_final_filename_manifest_only'
        if any(part in {'data_judge', 'similarity_runtime', 'generation_profile', 'pixels_game'} for part in parts):
            if not relative.name.upper().startswith('PUBLIC_'):
                return 'ambiguous_judge_payload_manifest_only'
    return None


def private_payload(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() in PRIVATE_KEYS and nested not in (None, False, [], {}, ''):
                return True
            if private_payload(nested):
                return True
    elif isinstance(value, list):
        return any(private_payload(nested) for nested in value)
    return False


def audit_entry(entry, worktree, hosts, cache):
    worktree = worktree.resolve()
    relative = Path(entry['path'])
    reason = path_omission(relative)
    if reason:
        return reason, False
    target = worktree / relative
    if not target.exists():
        return 'missing_after_interrupted_audit_manifest_only', False
    info = target.lstat()
    if target.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or target.resolve() != target.absolute():
        return 'nonregular_publication_path_manifest_only', False
    if info.st_size > MAX_BYTES:
        return 'large_file_manifest_only', False
    raw = target.read_bytes()
    current_hash = digest_bytes(raw)
    if current_hash != entry['published_sha256']:
        return 'changed_or_interrupted_derivative_manifest_only', False
    cache_key = (current_hash, relative.suffix.lower())
    if cache_key not in cache:
        try:
            text = raw.decode('utf-8')
        except UnicodeError:
            return 'binary_manifest_only', False
        if '\x00' in text:
            return 'binary_manifest_only', False
        if relative.suffix.lower() in DATA_SUFFIXES and PRIVATE_FLAG.search(text):
            return 'explicit_private_payload_classification_manifest_only', False
        if relative.suffix.lower() == '.json':
            try:
                if private_payload(json.loads(text)):
                    return 'private_payload_structure_manifest_only', False
            except (ValueError, RecursionError):
                return 'unparseable_json_manifest_only', False
        if relative.suffix.lower() == '.jsonl':
            try:
                if any(private_payload(json.loads(line)) for line in text.splitlines() if line.strip()):
                    return 'private_payload_structure_manifest_only', False
            except (ValueError, RecursionError):
                return 'unparseable_jsonl_manifest_only', False
        clean, changes = clean_public(text, hosts)
        if clean_public(clean, hosts)[0] != clean:
            return 'non_idempotent_safety_filter_manifest_only', False
        cache[cache_key] = (clean, changes)
    clean, changes = cache[cache_key]
    changed = clean.encode() != raw
    if changed:
        atomic_text(target, clean)
        entry['publication_additional_redactions'] = changes
    entry['published_sha256'] = digest_bytes(clean.encode())
    entry['published_bytes'] = len(clean.encode())
    return None, changed


def clean_public(text, hosts):
    cleaned, changes = sanitize(text, hosts)
    changes = Counter(changes)
    for label, pattern, replacement in (
        ('host_field', HOST_FIELD, r'\1"[REDACTED_HOST]"'),
        ('url_authority', URL_HOST, r'\1[REDACTED_HOST]'),
        ('contact', EMAIL, '[REDACTED_CONTACT]'),
        ('jwt', JWT, '[REDACTED_CREDENTIAL]'),
        ('ipv6', IPV6, '[REDACTED_ADDRESS]'),
        ('escaped_secret', ESCAPED_SECRET, r'\1[REDACTED_SECRET]\2'),
        ('extra_token', EXTRA_TOKEN, '[REDACTED_CREDENTIAL]'),
        ('credential_assignment', ASSIGNMENT, r'\1\2[REDACTED_SECRET]\4'),
    ):
        cleaned, count = pattern.subn(replacement, cleaned)
        changes[label] += count
    return cleaned, {key: value for key, value in changes.items() if value}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--worktree', type=Path, required=True)
    args = parser.parse_args()
    root, worktree = args.root.resolve(), args.worktree.resolve()
    publication = worktree / 'research_loop/workers/rohin206_code_preservation_20260918'
    report = json.loads((publication / 'PRESERVATION_RECEIPT.json').read_text())
    if 'complete_utc' not in report:
        raise SystemExit('worker_snapshot_not_complete')
    hosts = host_tokens(root)
    scanned, removed, rewritten = 0, 0, 0
    omissions, cache, published = Counter(), {}, {}
    manifests = []
    for directory in report['directories']:
        manifest = worktree / 'research_loop/workers' / directory['directory'] / 'PRESERVATION_MANIFEST_20260918.jsonl'
        records = [json.loads(line) for line in manifest.read_text().splitlines()]
        for entry in records:
            if 'published_sha256' not in entry:
                continue
            reason, changed = audit_entry(entry, worktree, hosts, cache)
            if reason:
                entry.pop('published_sha256', None)
                entry.pop('published_bytes', None)
                entry['omitted_reason'] = reason
                omissions[reason] += 1
                removed += 1
            else:
                rewritten += int(changed)
                scanned += 1
                published[entry['path']] = dict(sha256=entry['published_sha256'], bytes=entry['published_bytes'])
        clean_manifest = clean_public(''.join(json.dumps(entry, sort_keys=True) + '\n' for entry in records), hosts)[0]
        atomic_text(manifest, clean_manifest)
        directory['manifest_sha256'] = digest_file(manifest)
        manifests.append(str(manifest.relative_to(worktree)))
        print(json.dumps(dict(audited_directory=directory['directory'], scanned=scanned, omitted=removed)), flush=True)
    coordinate = worktree / 'research_loop/COORDINATION.md'
    clean, changes = clean_public(coordinate.read_text(), hosts)
    atomic_text(coordinate, clean)
    report['coordinate']['published_sha256'] = digest_file(coordinate)
    report['coordinate']['final_safety_redactions'] = changes
    report['publication_safety_audit'] = dict(utc=datetime.now(timezone.utc).isoformat(), scanned_files=scanned,
        additional_redacted_files=rewritten, explicit_private_files_removed=removed,
        checks=['known_hosts', 'host_fields', 'IPv4', 'IPv6', 'URL_authority', 'email',
                'private_key_blocks', 'token_prefixes', 'Bearer', 'secret_fields', 'JWT'],
        original_files_modified=False, manifests_rebound_to_published_bytes=True,
        audit_script_sha256=digest_file(Path(__file__)), omissions=dict(omissions),
        staging_policy='positive_hash_bound_paths_only; omitted derivatives never staged',
        source_totals_are_capture_totals_not_final_publication_counts=True,
        limitation='Conservative pattern and structure audit, not proof against undisclosed or encoded secrets.')
    allowlist = publication / 'PUBLICATION_ALLOWLIST.json'
    write_json(allowlist, dict(complete_utc=report['complete_utc'], files=published, manifests=manifests,
                              coordinate_sha256=report['coordinate']['published_sha256']))
    report['publication_safety_audit']['allowlist_sha256'] = digest_file(allowlist)
    write_json(publication / 'PRESERVATION_RECEIPT.json', report)
    write_json(publication / 'PRESERVATION_PROGRESS.json', report)
    print(json.dumps(report['publication_safety_audit']))


if __name__ == '__main__':
    main()
