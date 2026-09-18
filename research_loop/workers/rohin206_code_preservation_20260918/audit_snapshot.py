"""Bounded caption-code audit; never execute candidates or open private datasets."""

import ast
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
WORKER = REPO / 'research_loop/workers/r177_caption_game_stage1_20260917'
DENIED_DIRECTORIES = {
    'private', 'portable', 'data', 'payload', 'payloads', 'rows', 'weights',
    '.git', '.ssh', '.venv', 'venv', '__pycache__', 'site-packages',
    'node_modules', 'credentials', 'secrets', 'modelcfg', 'model_cfg',
    'reference_panels', 'reference_panel', 'sealed', 'final',
}
PUBLIC_REPORTS = {
    'data_judge/rank200_reference_v3/PUBLIC_DIAGNOSTIC.json',
    'generation_profile/PUBLIC_SOURCE_RECEIPTS.json',
    'similarity_runtime/PUBLIC_READINESS_20260917.json',
    'similarity_runtime/PUBLIC_INTEGRATION_HANDOFF1.json',
    'similarity_runtime/campaign1/PREPARATION_PUBLIC.json',
    'similarity_runtime/campaign1/ANNOTATION_PUBLIC.json',
    'similarity_runtime/campaign1/VERIFIER_SMOKES_PUBLIC.json',
    'similarity_runtime/campaign1/calibration1/PUBLIC_METADATA.json',
    'similarity_runtime/encoder_acquisition1/PUBLIC_MODEL_METADATA.json',
    'similarity_runtime/encoder_cpu_proof1/PUBLIC_METADATA.json',
}
RULES = {
    'private_key_material': r'-----BEGIN (?:(?:OPENSSH|RSA|EC|DSA|ENCRYPTED|PGP) )?PRIVATE KEY-----',
    'provider_token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,}|hf_[A-Za-z0-9]{25,}|xox[baprs]-[A-Za-z0-9-]{20,})\b',
    'aws_access_key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'jwt': r'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b',
    'url_user_password': r'https?://[^\s/:]+:[^\s/@]+@',
    'literal_credential_assignment': r'(?i)\b(?:[a-z0-9_]+_)?(?:password|passwd|api_key|access_token|auth_token|client_secret|secret_key)\b[\s\x22\x27]*[:=]\s*[\x22\x27][^\x22\x27\r\n]{8,}[\x22\x27]',
    'literal_authorization_header': r'(?i)(?:authorization[\x22\x27]?\s*[:=]\s*[\x22\x27]?\s*bearer|bearer)\s+[A-Za-z0-9_.-]{24,}',
    'large_encoded_blob': r'(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{256,}={0,2}',
}
PRIVATE_JSON_KEYS = {
    'caption', 'captions', 'caption_text', 'caption_rows', 'rows', 'payload',
    'payloads', 'reference_panel', 'reference_panels', 'reference_captions',
    'panel_captions', 'reference_texts', 'contest_ids', 'caption_ids',
    'private_key', 'password', 'api_key', 'access_token', 'client_secret',
}


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.write('\n')


def candidates():
    result = list((REPO/'gpu').glob('ny_caption*.py'))
    result.extend((REPO/'tests').glob('test_ny_caption*.py'))
    excluded_counts = Counter()
    for directory, subdirectories, names in os.walk(WORKER, followlinks=False):
        kept = []
        for name in subdirectories:
            path = Path(directory)/name
            if name.lower() in DENIED_DIRECTORIES or path.is_symlink():
                excluded_counts[name.lower()] += 1
            else:
                kept.append(name)
        subdirectories[:] = kept
        for name in names:
            path = Path(directory)/name
            relative = path.relative_to(WORKER).as_posix()
            if path.suffix in {'.py', '.sh', '.md'} or relative in PUBLIC_REPORTS:
                result.append(path)
    return sorted(set(result)), dict(excluded_counts)


def scan(path, data):
    findings = []
    text = data.decode('utf-8')
    for label, expression in RULES.items():
        for match in re.finditer(expression, text):
            findings.append(dict(rule=label, line=text.count('\n', 0, match.start())+1))
    if path.suffix == '.py':
        tree = ast.parse(text, filename=str(path.relative_to(REPO)))
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and len(node.elts) > 20:
                if all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in node.elts):
                    findings.append(dict(rule='review_large_string_literal_collection', line=node.lineno, count=len(node.elts)))
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value in {'reference_panel','reference_captions','panel_captions','reference_texts'}:
                        if isinstance(value, (ast.List, ast.Tuple)) and value.elts:
                            findings.append(dict(rule='review_literal_reference_panel', line=node.lineno))
    if path.suffix == '.json':
        def inspect(value):
            if isinstance(value, dict):
                for key, nested in value.items():
                    if key.lower() in PRIVATE_JSON_KEYS and nested not in (None, False, [], {}):
                        findings.append(dict(rule='private_payload_key_in_public_report', key=key))
                    inspect(nested)
            elif isinstance(value, list):
                for nested in value:
                    inspect(nested)
        inspect(json.loads(text))
    if path.suffix == '.md':
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r'(?i)(?:caption|reference text|scene description)\s*[:=]\s*[\x22\x27\u201c]', line):
                findings.append(dict(rule='review_possible_quoted_dataset_text', line=number))
    return findings


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    assert mode in {'scan', 'snapshot'}
    paths, exclusions = candidates()
    metadata = []
    findings = []
    blobs = {}
    for path in paths:
        relative = path.relative_to(REPO).as_posix()
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 2_000_000:
            findings.append(dict(path=relative, rule='nonprivate_regular_file_or_size_check_failed'))
            continue
        if any(part.lower() in DENIED_DIRECTORIES for part in path.relative_to(REPO).parts):
            raise AssertionError('excluded_directory_reached')
        data = path.read_bytes()
        after = path.stat()
        assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns), relative
        results = scan(path, data)
        findings.extend(dict(path=relative, **finding) for finding in results)
        metadata.append(dict(path=relative, sha256=checksum(data), bytes=len(data), mode=oct(stat.S_IMODE(before.st_mode))))
        blobs[relative] = data
    observed = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = dict(observed_utc=observed, scanner_sha256=checksum(Path(__file__).read_bytes()), candidates=len(paths), scanned_files=len(metadata),
        scanned_bytes=sum(item['bytes'] for item in metadata), excluded_directory_counts=exclusions,
        rules=RULES, findings=findings, private_dataset_files_opened=0, raw_matches_logged=False,
        candidate_code_executed=False, files=metadata,
        limitation='Pattern and structure scan, not a guarantee against all possible secret encodings or undisclosed data provenance.')
    if mode == 'scan':
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        write_json(OWN/('SCAN_PRELIMINARY_'+stamp+'.json'), report)
        print(json.dumps({key:value for key,value in report.items() if key not in {'files','rules'}}, sort_keys=True, indent=2))
        return
    decisions = json.loads((OWN/'REVIEW_DECISIONS.json').read_bytes())
    withheld = decisions['withheld_paths']
    approved = decisions['approved_findings']
    for finding in findings:
        if finding['path'] in withheld:
            continue
        identity = {key:finding[key] for key in ('path','rule','line','key') if key in finding}
        assert any(entry['finding'] == identity and entry['sha256'] == checksum(blobs[finding['path']]) for entry in approved), identity
    metadata = [item for item in metadata if item['path'] not in withheld]
    assert all(checksum((REPO/item['path']).read_bytes()) == item['sha256'] for item in metadata), 'candidate_changed_during_scan'
    snapshot = OWN/'snapshot'
    snapshot.mkdir(mode=0o700)
    for item in metadata:
        destination = snapshot/item['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as output:
            output.write(blobs[item['path']])
        destination.chmod(int(item['mode'], 8) & 0o777)
        assert checksum(destination.read_bytes()) == item['sha256']
        assert destination.stat().st_nlink == 1 and destination.stat().st_ino != (REPO/item['path']).stat().st_ino
    git_head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO, text=True).strip()
    manifest = dict(schema='R206_CAPTION_CODE_ONLY_ALLOWLIST_V1', observed_utc=observed,
        working_tree_head=git_head, scope='Caption implementation/tests/R177 source and audited public notes/reports only',
        files=metadata, files_count=len(metadata), total_bytes=sum(item['bytes'] for item in metadata),
        withheld_paths=withheld, excluded_directories=sorted(DENIED_DIRECTORIES),
        no_commit=True, no_push=True, no_git_index_mutation=True, no_original_edits=True,
        no_private_eval_payloads=True, no_live_learner_access=True,
        operator='Main imports explicit manifest paths into a separate detached worktree; never git add the R177 tree wholesale.')
    write_json(OWN/'MANIFEST.json', manifest)
    report.update(status='PASS_WITH_RECORDED_REVIEWS_AND_EXCLUSIONS', allowlisted_files=len(metadata),
        review_decisions_sha256=checksum((OWN/'REVIEW_DECISIONS.json').read_bytes()),
        findings_on_allowlisted_files=sum(finding['path'] not in withheld for finding in findings),
        reviewed_findings=approved, withheld_paths=withheld)
    write_json(OWN/'SECRET_SCAN.json', report)
    with (OWN/'ALLOWLIST.txt').open('x') as output:
        output.write(''.join(item['path']+'\n' for item in metadata))
    with tarfile.open(OWN/'CODE_ONLY.tar', 'x') as archive:
        for item in metadata:
            archive.add(snapshot/item['path'], arcname=item['path'], recursive=False)
    with tarfile.open(OWN/'CODE_ONLY.tar') as archive:
        actual = {member.name:checksum(archive.extractfile(member).read()) for member in archive.getmembers() if member.isfile()}
        assert actual == {item['path']:item['sha256'] for item in metadata}
        assert len(archive.getmembers()) == len(metadata)
    hashes = {name:checksum((OWN/name).read_bytes()) for name in ('MANIFEST.json','SECRET_SCAN.json','ALLOWLIST.txt','CODE_ONLY.tar','REVIEW_DECISIONS.json')}
    write_json(OWN/'ARTIFACT_SHA256.json', hashes)
    print(json.dumps(dict(files_count=len(metadata),total_bytes=manifest['total_bytes'],sha256=hashes,withheld_count=len(withheld),committed=False,pushed=False),sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
