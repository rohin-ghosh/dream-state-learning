"""Pinned, reviewed repository excerpts read through the actual R127 file tool."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

from gpu.orch_r127_pilot_console import (
    WORKSPACE_SCHEMA, _bytes, _directory, _read, _stage, publish_tool,
)


SOURCES = {
    'research_notes/CONTINUAL_LEARNER_R127_STARTUP_FILLED_2026-09-16.md':
        '4764742ec49cc1a4d6b7e84c15e1a2ade9e9c8be0cd5883800d6e63264380666',
    'research_notes/analysis/orch_r125_native_continuity_20260916/R127_CONTINUITY_AUDIT.json':
        '17f9d6651864cd3b865b0a25de91b2b44a1f5a43de10eb54d3979f39a54af378',
}
DOCUMENTS = {
    'overview.md': '''# Public-facing runtime overview

This is a reviewed excerpt, not access to the full repository.
The continual learner uses frozen Qwen2.5-7B-Instruct base weights and a
trainable rank-8 LoRA adapter. The ongoing history continues across generation
boundaries. Two generated segments precede a free distillation segment and
sleep. New eligible child segments receive 16 presentations, older ones one;
ordinary capability examples have objective weight 0.25 and child targets 0.75.
Only the child's target tokens are trained. Parent messages and environment
results are masked, although they can influence subsequent child generation.
The visible context has 16,384 tokens; each generation has at most 512 tokens.
At sleep, nonempty distillation replaces earlier visible history with the
child's summary. This is lossy; raw history is retained separately.
Adapter, optimizer, random-generator state and history/summary are checkpointed.

Astra is a conversational parent. Initiative, questions and useful silence are
welcome. No recurring thought format is required. A generation end is not an
instruction to forget. Reading a document does not itself train that document.
Separate capability checks do not supply their prompts or results to TRAIN.
Neither a successful update nor file access establishes improved learning.

Source: reviewed factual R127 startup. Old pilot paths, budget and connected
capability claims are intentionally omitted; this child's own startup governs.
''',
    'continuity.md': '''# Published continuity audit: limited aggregate digest

The published R127 continuity audit reports PASS for an existing native life,
not for the fresh R127 pilot or this REPO-READER child. At its recorded audit
time (Unix 1789548770.2961397), it counted 1,343 records, 163 history extensions,
17 sleeps, 39 plain requests, 75 verified assistant messages and 49 cases of
end-of-sequence followed by another request. It reported 127 raw events and
18 compaction operations. Initial and sleep-17 checkpoint verifications list
0 and 1,104 optimizer steps, respectively.

Scope: raw history retained; visible summaries are lossy; CPU tests cover task
boundaries. These are continuity/engineering counts, NOT benchmark scores,
evidence of capability gain, consciousness or general learning improvement.
No evaluator item, answer, per-item result or sealed readout is included.
No claim is made about later checkpoints or all experiment results.
Scientific comparisons require matched controls and separate held evaluation.

Source: the reviewed published R127_CONTINUITY_AUDIT aggregate fields only.
Internal run paths and artifact identifiers are deliberately removed.
''',
    'access.md': '''# Repository reader: connection and coverage

When this actual file arrives as a Tool environment result, the read-only
repository reader has performed a real file read. To request another read,
write exactly one of these lines in your generated response:
repo_read overview.md
repo_read continuity.md
repo_read access.md
Use one request at a time; your next generation need not wait for delivery.
The dispatcher binds a request to your actual recorded TRAIN response.
Results are actual UTF-8 file bytes with source and content hashes in retained
receipts. Predictions and proposed contents are not execution results.

This snapshot contains ONLY the three short reviewed documents listed here.
It is not all repository results. Full research directories, the coordination
notebook, credentials, host/provider configuration, held/FINAL material,
answer keys, raw evaluations and the R130 corpus/outputs are excluded.
Source hashes and a pinned manifest bind the limited exposed bytes.
No absolute paths, subdirectories, symlinks, writes, shell, network or GPU
execution are available through this reader. Ask Astra about omitted public
context; safe coverage may expand only through a newly reviewed snapshot.
An operator may supply the initial access-file read; that is not your request.
The programme parent sees your TRAIN conversation, never sealed readouts.
''',
}
SCHEMA = 'R136_REVIEWED_REPO_SNAPSHOT_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest(commit):
    require(type(commit) is str and re.fullmatch(r'[0-9a-f]{40}', commit), 'source_commit')
    return dict(schema=SCHEMA, source_commit=commit, sources=SOURCES,
                review='Explicit human-readable excerpts reviewed by builder; no directory copy',
                coverage='Three documents only; not all experiment results',
                files={name: dict(sha256=digest(text.encode()), bytes=len(text.encode()))
                       for name, text in DOCUMENTS.items()})


def build(repository, commit, snapshot):
    document = manifest(commit)
    for name, expected in SOURCES.items():
        result = subprocess.run(['git', 'show', commit + ':' + name], cwd=repository,
                                capture_output=True, check=True)
        require(digest(result.stdout) == expected, 'reviewed_source_changed')
    snapshot = Path(snapshot)
    require(snapshot.is_absolute() and '..' not in snapshot.parts, 'absolute_snapshot')
    with _directory(snapshot.parent) as parent:
        os.mkdir(snapshot.name, mode=0o700, dir_fd=parent)
    with _directory(snapshot) as directory:
        for name, text in DOCUMENTS.items():
            require(len(text.encode()) <= 2048, 'untruncated_pilot_result')
            _stage(directory, name, text.encode())
        raw = _bytes(document)
        _stage(directory, 'MANIFEST.json', raw)
        os.fchmod(directory, 0o500)
    return dict(manifest_sha256=digest(raw), manifest=document)


def verify(snapshot, expected):
    snapshot = Path(snapshot)
    require(snapshot.is_absolute() and '..' not in snapshot.parts, 'absolute_snapshot')
    require(type(expected) is str and re.fullmatch(r'[0-9a-f]{64}', expected), 'manifest_pin')
    with _directory(snapshot) as directory:
        require(set(os.listdir(directory)) == set(DOCUMENTS) | {'MANIFEST.json'}, 'exact_allowlist')
        raw = _read(directory, 'MANIFEST.json', 16384)
        require(digest(raw) == expected, 'manifest_changed')
        document = json.loads(raw)
        require(document == manifest(document['source_commit']), 'reviewed_manifest_only')
        for name, entry in document['files'].items():
            data = _read(directory, name, 2048)
            require(digest(data) == entry['sha256'] and len(data) == entry['bytes'], 'snapshot_changed')
    return document


def read_file(snapshot, expected, name, receipts, operation='read-note', request=None):
    require(operation == 'read-note', 'read_only')
    require(type(name) is str and name in DOCUMENTS, 'explicit_allowlist_only')
    document = verify(snapshot, expected)
    with _directory(snapshot) as directory:
        raw = _read(directory, name, 2048)
    require(digest(raw) == document['files'][name]['sha256'], 'read_source_hash')
    identifier = uuid.uuid4().hex
    result = dict(schema=WORKSPACE_SCHEMA, id=identifier, operation='read-note', status='COMPLETE',
                  path=str(Path(snapshot) / name), content=raw.decode('utf-8'), sha256=digest(raw))
    proof = dict(schema='R136_ACTUAL_FILE_PROVENANCE_V1', manifest_sha256=expected,
                 source_commit=document['source_commit'], sources=document['sources'],
                 file=name, file_sha256=digest(raw), receipt_sha256=digest(_bytes(result)),
                 request=request, operation='read-note', fabricated=False)
    with _directory(receipts) as directory:
        _stage(directory, identifier + '.provenance.json', _bytes(proof))
        _stage(directory, identifier + '.json', _bytes(result))
    return dict(result_path=str(Path(receipts) / (identifier + '.json')),
                provenance_path=str(Path(receipts) / (identifier + '.provenance.json')),
                file_sha256=digest(raw), manifest_sha256=expected)


def deliver(root, snapshot, expected, name, receipts, request):
    result = read_file(snapshot, expected, name, receipts, request=request)
    result['publication'] = publish_tool(root, result['result_path'])
    return result


def requests(text):
    require(type(text) is str, 'actual_response_text')
    found = re.findall(r'^repo_read ([^\r\n]+)\r?$', text, flags=re.MULTILINE)
    require(len(found) <= 1, 'one_read_per_response')
    require(all(name in DOCUMENTS for name in found), 'explicit_allowlist_only')
    return found


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    print(json.dumps(build(**vars(parser.parse_args())), sort_keys=True))
