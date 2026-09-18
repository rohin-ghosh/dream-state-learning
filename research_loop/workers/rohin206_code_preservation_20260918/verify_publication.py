"""Independent, fail-closed check of the completed derivative allowlist."""

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from audit_publication import atomic_text, clean_public, path_omission
from preserve_latest import digest_bytes, digest_file, host_tokens, write_json


PREFIX = Path('research_loop/workers/rohin206_code_preservation_20260918')
RULES = {
    'private_key_header': re.compile(r'-----BEGIN (?:(?:OPENSSH|RSA|EC|DSA|ENCRYPTED|PGP) )?PRIVATE KEY-----'),
    'ssh_key_material': re.compile(r'\bssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/]{40,}'),
    'encoded_blob': re.compile(r'(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{256,}={0,2}'),
    'provider_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|hf_[A-Za-z0-9]{25,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b'),
    'url_user_password': re.compile(r'(?:https?|ssh)://[^\s/:]+:[^\s/@]+@'),
}
LITERAL_SECRET = re.compile(r'''(?i)\b(?:[a-z0-9]+_)*(?:password|passwd|api_key|access_token|auth_token|client_secret|secret_key|refresh_token)\b["']?\s*[:=]\s*(?P<quote>["'])(?P<value>[^"'\r\n]{8,})(?P=quote)''')
UNQUOTED_SECRET = re.compile(r'(?im)\b(?:[a-z0-9]+_)*(?:password|passwd|api_key|access_token|auth_token|client_secret|secret_key|refresh_token)\b\s*[:=]\s*[A-Za-z0-9_+/.=-]{16,}(?=[\s,;}]|$)')
EMBEDDED_PRIVATE = re.compile(r'(?i)(?:reference_panels?|reference_captions|panel_captions|reference_texts|heldout_rows|calibration_curves?)[\\"]+\s*:\s*(?:\[(?!\s*\])|\{(?!\s*\}))')
CAPTION_KEYS = {'caption', 'captions', 'caption_text', 'caption_rows', 'rows', 'payload', 'payloads',
                'reference_panel', 'reference_panels', 'reference_captions', 'panel_captions',
                'reference_texts', 'contest_ids', 'caption_ids', 'calibration_curve', 'calibration_curves'}


def caption_payload(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() in CAPTION_KEYS and nested not in (None, False, [], {}, ''):
                return True
            if caption_payload(nested):
                return True
    elif isinstance(value, list):
        return any(caption_payload(nested) for nested in value)
    return False


def findings(relative, raw, hosts):
    text = raw.decode('utf-8')
    found = [label for label, rule in RULES.items() if rule.search(text)]
    if any(not match.group('value').startswith('[REDACTED_') for match in LITERAL_SECRET.finditer(text)):
        found.append('literal_credential_assignment')
    if UNQUOTED_SECRET.search(text):
        found.append('unquoted_credential_assignment')
    if clean_public(text, hosts)[0] != text:
        found.append('residual_redaction_required')
    if relative.suffix.lower() not in {'.py', '.sh'} and EMBEDDED_PRIVATE.search(text):
        found.append('embedded_private_payload')
    caption_scope = any(word in str(relative).lower() for word in ('caption', 'data_judge', 'contrast', 'similarity_runtime'))
    if relative.suffix.lower() == '.py' and caption_scope:
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and key.value in CAPTION_KEYS:
                            if isinstance(value, (ast.List, ast.Tuple, ast.Set)) and value.elts:
                                found.append('literal_caption_payload_in_source')
                            elif isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value:
                                found.append('literal_caption_payload_in_source')
        except (SyntaxError, ValueError):
            found.append('unparseable_caption_source')
    if relative.suffix.lower() in {'.json', '.jsonl'} and caption_scope:
        try:
            values = [json.loads(text)] if relative.suffix.lower() == '.json' else [json.loads(line) for line in text.splitlines() if line.strip()]
            if any(caption_payload(value) for value in values):
                found.append('caption_payload_not_public_aggregate')
        except (ValueError, RecursionError):
            found.append('unparseable_public_json')
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--worktree', type=Path, required=True)
    parser.add_argument('--prune', action='store_true')
    args = parser.parse_args()
    worktree = args.worktree.resolve()
    publication = worktree / PREFIX
    receipt_path = publication / 'PRESERVATION_RECEIPT.json'
    allow_path = publication / 'PUBLICATION_ALLOWLIST.json'
    report = json.loads(receipt_path.read_text())
    allow = json.loads(allow_path.read_text())
    if not report.get('complete_utc') or not report.get('publication_safety_audit'):
        raise SystemExit('completed_snapshot_and_safety_audit_required')
    if digest_file(allow_path) != report['publication_safety_audit']['allowlist_sha256']:
        raise SystemExit('allowlist_hash_mismatch')
    hosts = host_tokens(args.root.resolve())
    cache, rejections, unique = {}, {}, {}
    total_bytes = 0
    for index, (name, expected) in enumerate(allow['files'].items(), 1):
        relative = Path(name)
        path = worktree / relative
        if path_omission(relative) or path.is_symlink() or path.resolve() != path:
            raise SystemExit('unsafe_allowlisted_path')
        raw = path.read_bytes()
        checksum = digest_bytes(raw)
        if checksum != expected['sha256'] or len(raw) != expected['bytes']:
            raise SystemExit('derivative_changed_after_audit')
        sensitive_path = any(word in name.lower() for word in ('caption', 'data_judge', 'contrast', 'similarity_runtime'))
        key = checksum, relative.suffix.lower(), sensitive_path
        if key not in cache:
            cache[key] = findings(relative, raw, hosts)
        if cache[key]:
            rejections[name] = list(cache[key])
        if clean_public(name, hosts)[0] != name:
            rejections.setdefault(name, []).append('sensitive_publication_path')
        if name not in rejections:
            total_bytes += len(raw)
            unique[checksum] = len(raw)
        if index % 20000 == 0:
            print(json.dumps(dict(verified=index, rejected=len(rejections))), flush=True)
    if rejections and not args.prune:
        raise SystemExit('residual_findings_require_explicit_prune')
    manifest_updates, represented = [], set()
    for directory in report['directories']:
        path = worktree / 'research_loop/workers' / directory['directory'] / 'PRESERVATION_MANIFEST_20260918.jsonl'
        if digest_file(path) != directory['manifest_sha256']:
            raise SystemExit('manifest_hash_mismatch')
        lines = []
        for line in path.open():
            entry = json.loads(line)
            if entry['path'] in rejections and 'published_sha256' in entry:
                entry.pop('published_sha256')
                entry.pop('published_bytes', None)
                entry['omitted_reason'] = 'final_content_screen_manifest_only'
                entry['publication_omission_rules'] = rejections[entry['path']]
            elif 'published_sha256' in entry:
                expected = allow['files'].get(entry['path'])
                if expected is None:
                    entry.pop('published_sha256')
                    entry.pop('published_bytes', None)
                    entry['omitted_reason'] = 'sanitized_manifest_path_unbound_manifest_only'
                elif expected['sha256'] != entry['published_sha256']:
                    raise SystemExit('manifest_derivative_binding_mismatch')
                else:
                    represented.add(entry['path'])
            lines.append(json.dumps(entry, sort_keys=True) + '\n')
        text = ''.join(lines)
        if findings(path.relative_to(worktree), text.encode(), hosts):
            raise SystemExit('manifest_content_screen_failed')
        manifest_updates.append((path, text))
        directory['manifest_sha256'] = digest_bytes(text.encode())
    for name in rejections:
        del allow['files'][name]
    if represented != set(allow['files']):
        raise SystemExit('allowlist_manifest_coverage_mismatch')
    coordinate = worktree / allow.get('coordinate_path', 'research_loop/COORDINATION.md')
    if digest_file(coordinate) != allow['coordinate_sha256'] or findings(coordinate.relative_to(worktree), coordinate.read_bytes(), hosts):
        raise SystemExit('coordinate_content_or_hash_screen_failed')
    coordinate_destination = publication / 'COORDINATION_SNAPSHOT_DERIVED.md'
    scripts = ['audit_publication.py', 'preserve_latest.py', 'audit_snapshot.py', 'test_audit_publication.py', 'verify_publication.py']
    explicit_files = {}
    for name in scripts:
        path = publication / name
        raw = path.read_bytes()
        if findings(path.relative_to(worktree), raw, hosts):
            raise SystemExit('publisher_script_content_screen_failed:' + name)
        explicit_files[str(PREFIX / name)] = dict(sha256=digest_bytes(raw), bytes=len(raw))
    counts = Counter(rule for rules in rejections.values() for rule in rules)
    result = dict(utc=datetime.now(timezone.utc).isoformat(), status='PASS', snapshot_complete_utc=report['complete_utc'],
        files=len(allow['files']), derivative_bytes=total_bytes, unique_blobs=len(unique), unique_derivative_bytes=sum(unique.values()),
        duplicate_blob_paths=len(allow['files'])-len(unique), omitted_files=len(rejections), omission_rule_counts=dict(counts),
        independent_scanner_sha256=digest_file(Path(__file__)), publisher_scripts=explicit_files,
        scope='finished sanitized snapshot only; no source recapture, learner access, or private match output',
        coordinate_path=str(coordinate_destination.relative_to(worktree)),
        coordinate_sha256=allow['coordinate_sha256'],
        limitation='Conservative path, pattern and structure screening; not proof against undisclosed encodings or mislabeled data.')
    for path, text in manifest_updates:
        atomic_text(path, text)
    atomic_text(coordinate_destination, coordinate.read_text())
    allow['coordinate_path'] = str(coordinate_destination.relative_to(worktree))
    report['coordinate']['published_path'] = allow['coordinate_path']
    write_json(allow_path, allow)
    report['publication_safety_audit']['allowlist_sha256'] = digest_file(allow_path)
    report['publication_safety_audit']['final_content_screen'] = result
    write_json(receipt_path, report)
    write_json(publication / 'PRESERVATION_PROGRESS.json', report)
    write_json(publication / 'PUBLICATION_CONTENT_AUDIT.json', result)
    print(json.dumps({key: value for key, value in result.items() if key != 'publisher_scripts'}), flush=True)


if __name__ == '__main__':
    main()
