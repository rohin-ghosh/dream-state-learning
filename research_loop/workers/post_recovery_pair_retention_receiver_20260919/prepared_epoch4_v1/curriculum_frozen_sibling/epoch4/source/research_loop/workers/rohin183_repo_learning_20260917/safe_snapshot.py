"""Broad, conservative source/document snapshot; reject data before content I/O."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import stat


MAX_FILE = 2*1024**2
MAX_TOTAL = 256*1024**2
ROOTS = {'gpu','organism_v6','research_notes','research_loop','analysis','tests','docs'}
EXTENSIONS = {'.py','.md','.rst','.toml','.sh'}
BLOCKED_PARTS = {'private','sealed','final','held','heldout','evaluation','evaluations','eval',
    'credentials','secrets','captures','capture','journals','journal','records','readouts','readout',
    'scores','checkpoints','checkpoint','adapters','optimizer','venv','node_modules','__pycache__',
    'payload','portable','evidence','source','remote_source','local_source','source_work','recipe_repository',
    'snapshot','snapshots','forwarded','spool','inbox','outbox','logs','artifacts','outputs','results'}
BLOCKED_FAMILIES = ('r130','r159','r172','r176','r177','rohin183_repo_learning')
SECRET = re.compile(rb'(-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:sk-|nvapi-)[A-Za-z0-9_-]{20,}|\bAKIA[A-Z0-9]{16}\b|(?i:api[_-]?key|access[_-]?token)\s*[=:]\s*[\"\x27][A-Za-z0-9_-]{24,}[\"\x27])')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path=Path(path)
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    with path.open('xb') as stream:
        os.chmod(path,0o600)
        stream.write(raw)
    return dict(path=str(path.resolve()),bytes=len(raw),sha256=digest(raw))


def permitted_directory(relative):
    parts=Path(relative).parts
    return all(not part.startswith('.') and part.lower() not in BLOCKED_PARTS
        and not part.lower().startswith(BLOCKED_FAMILIES)
        and not re.search(r'(?i)(?:^|[_-])(held|sealed|eval|evaluation|final|private|r130|r159|r172|r176|r177|readout|scores|caption|judge)(?:$|[_-])',part)
        and not re.match(r'(?i)(candidate|attempt|exposure|final_|held_|sealed_|private_|run\d)',part)
        for part in parts)


def permitted_path(relative):
    path=Path(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts or not permitted_directory(path.parent):
        return False
    if len(path.parts)>1 and path.parts[0] not in ROOTS:
        return False
    name=path.name.lower()
    if path.suffix.lower() not in EXTENSIONS or name.startswith('.'):
        return False
    if re.search(r'(?i)(hosts|credential|secret|api_key|answer|condition.?map|sealed|heldout|private|final|\.env|r130|r159|r172|r176|r177|caption|judge|readout|benchmark|evaluation)',name):
        return False
    if path.suffix.lower() != '.py' and re.search(r'(?i)(coordination|notebook|score|result|report|receipt|readout|audit|transcript|caption|inventory|binding|history|response|request|capture)',name):
        return False
    return True


def build(repository, destination, resume=False):
    repository, destination=Path(repository).resolve(),Path(destination).resolve()
    require(not destination.exists() or resume and not (destination/'MANIFEST.json').exists(), 'immutable_new_snapshot')
    destination.mkdir(mode=0o700,parents=True,exist_ok=resume)
    entries, excluded, total={},Counter(),0
    for directory, folders, files in os.walk(repository,topdown=True,followlinks=False):
        relative=Path(directory).relative_to(repository)
        kept=[]
        for name in sorted(folders):
            child=relative/name
            if (Path(directory)/name).is_symlink() or not permitted_directory(child) or len(child.parts)==1 and name not in ROOTS:
                excluded['directory_metadata_policy']+=1
            else:
                kept.append(name)
        folders[:]=kept
        for name in sorted(files):
            relative_file=relative/name
            if not permitted_path(relative_file):
                excluded['file_metadata_policy']+=1
                continue
            path=repository/relative_file
            captured=destination/relative_file
            if resume and captured.exists():
                require(captured.is_file() and not captured.is_symlink(), 'regular_preserved_snapshot_file')
                size=captured.stat().st_size
                require(size<=MAX_FILE and total+size<=MAX_TOTAL,'aggregate_snapshot_budget_before_IO')
                raw=captured.read_bytes()
                require(len(raw)==size and not SECRET.search(raw),'unchanged_safe_capture')
                total+=size
                entries[str(relative_file)]=dict(bytes=size,sha256=digest(raw))
                continue
            metadata=path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size>MAX_FILE:
                excluded['nonregular_or_oversize']+=1
                continue
            require(total+metadata.st_size<=MAX_TOTAL,'aggregate_snapshot_budget_before_IO')
            descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            with os.fdopen(descriptor,'rb') as stream:
                raw=stream.read(MAX_FILE+1)
                after=os.fstat(stream.fileno())
            require(len(raw)==metadata.st_size and (metadata.st_dev,metadata.st_ino,metadata.st_mtime_ns)==
                (after.st_dev,after.st_ino,after.st_mtime_ns), 'stable_source_bytes')
            total+=len(raw)
            if SECRET.search(raw):
                excluded['credential_pattern_no_disclosure']+=1
                continue
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError:
                excluded['non_UTF8']+=1
                continue
            reference=write(destination/relative_file,raw)
            entries[str(relative_file)]=dict(bytes=reference['bytes'],sha256=reference['sha256'])
    counts=Counter(name.split('/')[0] if '/' in name else 'root' for name in entries)
    require({str(path.relative_to(destination)) for path in destination.rglob('*') if path.is_file()}==set(entries),
        'no_unmanifested_snapshot_files')
    require(all(counts[name]>0 for name in ('gpu','organism_v6','research_notes','research_loop')), 'broad_code_and_research_coverage')
    manifest=dict(schema='R183_SAFE_WORKING_TREE_SNAPSHOT_V1',files=entries,coverage=dict(counts),
        excluded_counts=dict(excluded),source_read_bytes=total,snapshot_bytes=sum(item['bytes'] for item in entries.values()),
        policy_source_sha256=digest(Path(__file__).read_bytes()),raw_data_artifacts_included=False,
        resumed_preserving_existing_files=resume,atomic_repository_commit_claim=False,
        metadata_excluded_contents_opened=False,content_pattern_exclusions=excluded['credential_pattern_no_disclosure'],
        credentials_included=False,FINAL_included=False,private_evaluation_included=False,
        scope='BROAD_SAFE_SOURCE_AND_DOCUMENTS_NOT_ALL_EXPERIMENT_RESULTS',excluded_names_disclosed=False)
    return write(destination/'MANIFEST.json',manifest)
