"""Read-only R137 parent snapshots; no provider, inbox publication or launches.

snapshot(native_root, publications=[{id, path, sha256}, ...], speaker='Astra')
returns R133_TRAIN_PARENT_SNAPSHOT_V1 with events[-8:], response_count,
record_count, head_sha256, consumed_inbox, boundaries and parent_consumptions.
request_count and latest_request_index include every validated TRAIN REQUEST,
including the inflight request, independently of committed response_count.
Only verified TRAIN REQUEST -> RESPONSE -> COMMITTED responses count. The
R134 classroom relay supplies the journal reader and child-source validator.

publications are R127 publish_parent return values supplied in memory: their
paths are compared, NEVER opened. None selects speaker-only exposure (not
programme ownership); [] credits nobody. A supplied ID must match the exact
path/hash and canonical R127 message bytes. No provider receipts are read.

publications_from_results(branch_output, programme=..., branch=...) reads only
parent_NNNNNN/RESULT.json in that explicitly selected output directory. It
returns the publication list plus exact result_receipt path/hash bindings;
only PUBLISHED results with matching programme/branch/speaker and matching
canonical published message hashes qualify. No provider transcripts, dispatch
intents, prompts, held files or arbitrary receipt references are opened.
Pass its result to snapshot; a read-only auditor needs no parent restart.

consumed_inbox means first verified REQUEST exposure, NOT INBOX registration
or successful inference. parent_exposures includes these exposures; the legacy
parent_consumptions list contains only exposures in their actual RESPONSE ->
next REQUEST interval, so the existing boundary helper cannot retro-credit a
registration exposed later. Birth exposure can be consumed without covering a
response boundary. Retained context never earns a second intervention credit.

request_exposes(request_document, event) is the relay's visible-history plus
exact-rendered-message predicate, generalized to parents. It assumes the caller
has validated the request and event provenance; snapshot does that first.

Limits raise SnapshotLimitExceeded rather than return misleading partial
coverage. Incomplete source tails return only the validated prefix, explicitly
marked PENDING_TAIL. A REQUEST awaiting RESPONSE is valid exposure evidence;
uncommitted child output is neither shown nor counted. No files are written,
no journal writer lock is taken, and no directory tree is searched. snapshot
reads only stream/JOURNAL.json and numbered stream/records records/intents;
the optional publications loader reads only explicitly selected RESULT files.
Snapshot references bind the observed prefix, not an atomic future live head.
"""

from contextlib import ExitStack
from dataclasses import asdict
import os
from pathlib import Path
import re

from gpu.orch_r134_classroom_relay import (
    ClassroomRelay, _Budget, _JournalView, _PollLimit, _exists, _sha, inbox_api,
)
from gpu.orch_r125_stream_journal import _decode, require
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import SCHEMA as STREAM_SCHEMA
from organism_v6.orch_r125_plain_context import event_message


SCHEMA = 'R133_TRAIN_PARENT_SNAPSHOT_V1'
EXPOSURE_SCHEMA = 'R137_PARENT_REQUEST_EXPOSURE_V1'


class SnapshotLimitExceeded(ValueError):
    """Increase explicit read limits; no partial snapshot was returned."""


def request_exposes(request, event):
    """Require the exact event in visible history AND its exact user message."""
    checkpoint = request['resume_state']['state']
    history = checkpoint['history']
    frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
    if event.actor != 'parent' or event.split != 'TRAIN' or asdict(event) not in history['events'][frontier:]:
        return False
    rendered = event_message(event) if checkpoint.get('presentation') else TrainHistory._message(event)
    return rendered is not None and rendered in request['messages']


def _publications(root, publications, max_records):
    if publications is None:
        return None
    require(type(publications) in (list, tuple) and len(publications) <= max_records, 'bounded_publication_list')
    result = {}
    for publication in publications:
        require(type(publication) is dict and set(publication) in (
            {'id', 'path', 'sha256'}, {'id', 'path', 'sha256', 'result_receipt'}),
            'exact_R127_publication_fields')
        identifier, path, digest = publication['id'], publication['path'], publication['sha256']
        require(type(identifier) is str and re.fullmatch(r'[0-9a-f]{32}', identifier), 'R127_publication_id')
        require(type(path) is str and path == str(root / 'stream' / 'inbox' / (identifier + '.json')),
            'publication_exact_inbox_path')
        require(type(digest) is str and re.fullmatch(r'[0-9a-f]{64}', digest), 'publication_sha256')
        require(identifier not in result, 'duplicate_publication_id')
        if 'result_receipt' in publication:
            receipt = publication['result_receipt']
            require(type(receipt) is dict and set(receipt) == {'path', 'sha256'}
                and type(receipt['path']) is str and Path(receipt['path']).is_absolute()
                and '..' not in Path(receipt['path']).parts and type(receipt['sha256']) is str
                and re.fullmatch(r'[0-9a-f]{64}', receipt['sha256']), 'result_receipt_binding')
        result[identifier] = dict(publication)
    return result


def publications_from_results(output, *, programme, branch, speaker='Astra', max_entries=4096,
        max_receipts=1000, max_receipt_bytes=1024 * 1024, max_bytes=16 * 1024 * 1024):
    """Read one explicit branch output, never traverse into provider captures."""
    require(type(programme) is str and programme and type(branch) is str and branch, 'explicit_programme_branch')
    require(speaker in ('Astra', 'Fable', 'Rohin'), 'known_parent_speaker')
    require(all(type(value) is int and value > 0 for value in
        (max_entries, max_receipts, max_receipt_bytes, max_bytes)), 'positive_result_limits')
    output = Path(output).absolute()
    budget = _Budget(dict(max_scan_bytes_per_poll=max_bytes, max_record_bytes=max_receipt_bytes))
    publications, identifiers, names = [], set(), []
    with inbox_api._directory(output) as directory:
        with os.scandir(directory) as entries:
            for count, entry in enumerate(entries, 1):
                if count > max_entries:
                    raise SnapshotLimitExceeded('result_directory_entry_limit')
                if re.fullmatch(r'parent_[0-9]{6,12}', entry.name):
                    require(entry.is_dir(follow_symlinks=False), 'regular_parent_result_directory')
                    names.append(entry.name)
        count = 0
        for name in sorted(names):
            with inbox_api._directory(output / name) as result_directory:
                if not _exists(result_directory, 'RESULT.json'):
                    continue
                count += 1
                if count > max_receipts:
                    raise SnapshotLimitExceeded('result_receipt_count_limit')
                try:
                    raw = budget.read(result_directory, 'RESULT.json')
                except _PollLimit as error:
                    raise SnapshotLimitExceeded('result_byte_limit') from error
                result = _decode(raw)
                require(type(result) is dict, 'result_object')
                if result.get('status') != 'PUBLISHED':
                    continue
                require(result.get('programme') == programme and result.get('branch') == branch
                    and result.get('speaker') == speaker, 'result_programme_branch_speaker')
                publication = result.get('inbox_publication')
                require(type(publication) is dict and set(publication) == {'id', 'path', 'sha256'},
                    'exact_R127_publication_fields')
                require(type(publication['id']) is str and re.fullmatch(r'[0-9a-f]{32}', publication['id']),
                    'R127_publication_id')
                require(type(publication['path']) is str and Path(publication['path']).is_absolute()
                    and '..' not in Path(publication['path']).parts
                    and Path(publication['path']).name == publication['id'] + '.json'
                    and Path(publication['path']).parent.name == 'inbox', 'R127_publication_path')
                response = result.get('response')
                require(type(response) is dict and response.get('speak') is True
                    and type(response.get('message')) is str, 'published_result_message')
                message = dict(schema=inbox_api.SCHEMA, id=publication['id'], text=response['message'],
                    split='TRAIN', actor='parent', speaker=speaker, source_receipt=None)
                require(publication['sha256'] == _sha(inbox_api._bytes(message)), 'result_publication_text_hash')
                require(type(publication['id']) is str and publication['id'] not in identifiers,
                    'duplicate_result_publication_id')
                identifiers.add(publication['id'])
                publications.append(dict(publication, result_receipt=dict(
                    path=str(output / name / 'RESULT.json'), sha256=_sha(raw))))
    return publications


class _ExposureScan:
    _source = ClassroomRelay._source

    def __init__(self, view, publications, speaker):
        self.view, self.publications, self.speaker = view, publications, speaker
        self.events, self.boundaries, self.exposures, self.consumptions = [], [], [], []
        self.registrations, self.eligible, self.consumed = {}, {}, {}
        self.request_count = 0
        self.latest_request_index = self.latest_request = None

    def event(self, event):
        self.events.append(event)
        self.events = sorted(self.events, key=lambda item: item['record_index'])[-8:]

    def inbox(self, record, reference):
        document = record['document']
        message = document['message']
        identifier = message['id']
        self.registrations[identifier] = dict(record_index=record['index'], record_sha256=record['sha256'],
            registration=reference)
        self.event(dict(actor=message['actor'], speaker=message.get('speaker'), text=message['text'],
            record_index=record['index'], record_sha256=record['sha256'], registration_only=True, split='TRAIN'))
        supplied = self.publications.get(identifier) if self.publications is not None else None
        if supplied is not None:
            require(message.get('schema') == inbox_api.SCHEMA and message['actor'] == 'parent'
                and message.get('speaker') == self.speaker, 'publication_parent_speaker_binding')
            require(document['source_id'] == supplied['path']
                and document['source_sha256'] == supplied['sha256']
                and _sha(inbox_api._bytes(message)) == supplied['sha256'], 'publication_exact_bytes_binding')
        if message['actor'] != 'parent' or message.get('speaker') != self.speaker:
            return
        if self.publications is not None and supplied is None:
            return
        self.eligible[identifier] = document

    def request(self, record, reference):
        document = record['document']
        require(document.get('schema') == STREAM_SCHEMA, 'request_stream_schema')
        self.request_count += 1
        self.latest_request_index, self.latest_request = record['index'], reference
        self.view.request_ref = reference
        self.view.last_request = {key: value for key, value in document.items() if key != 'resume_state'}
        boundary = self.boundaries[-1] if self.boundaries else None
        if boundary is not None:
            require(boundary['next_request_index'] is None, 'unique_next_request')
            boundary['next_request_index'] = record['index']
            boundary['next_request'] = reference
        for identifier, registered in self.eligible.items():
            if identifier in self.consumed:
                continue
            event = self.view._inbox_event(registered['message'], registered['source_id'], registered['source_sha256'])
            if not request_exposes(document, event):
                continue
            exposure = dict(self.registrations[identifier], schema=EXPOSURE_SCHEMA, status='IN_REQUEST',
                inbox_id=identifier, speaker=self.speaker, request_index=record['index'], request=reference,
                publication=dict(id=identifier, path=registered['source_id'], sha256=registered['source_sha256']),
                publication_bound=self.publications is not None)
            if self.publications is not None and 'result_receipt' in self.publications[identifier]:
                exposure['programme_result_receipt'] = self.publications[identifier]['result_receipt']
            self.consumed[identifier] = exposure
            self.exposures.append(exposure)
            if boundary is not None and boundary['record_index'] < exposure['record_index'] < record['index']:
                self.consumptions.append(exposure)

    def accept(self, record, reference):
        kind, document = record['kind'], record['document']
        if kind == 'INBOX':
            self.inbox(record, reference)
        elif kind == 'REQUEST':
            self.request(record, reference)
        elif kind == 'RESPONSE':
            self.view.response_ref, self.view.last_response = reference, document
        elif kind == 'COMMITTED' and document['state']['state']['rows']:
            source = self._source(self.view, record, reference)
            response_index = int(Path(source['response']['path']).stem)
            self.boundaries.append(dict(response_count=len(self.boundaries) + 1, record_index=response_index,
                record_sha256=source['response']['record_sha256'], committed_index=record['index'],
                next_request_index=None, source_receipt=source))
            self.event(dict(actor='child', text=source['raw'], split='TRAIN', record_index=response_index,
                record_sha256=source['response']['record_sha256'], source_sha256=source['response_sha256'],
                terminal=source['terminal'], truncated=source['truncated']))
            self.view.request_ref = self.view.response_ref = None


def snapshot(root, *, publications=None, speaker='Astra', max_records=10000,
        max_bytes=128 * 1024 * 1024, max_record_bytes=16 * 1024 * 1024):
    """Return a compatible, verified snapshot; never open supplied receipt paths."""
    root = Path(root).absolute()
    require('..' not in root.parts, 'parent_path_component_forbidden')
    require(speaker in ('Astra', 'Fable', 'Rohin'), 'known_parent_speaker')
    require(all(type(value) is int and value > 0 for value in (max_records, max_bytes, max_record_bytes)),
        'positive_snapshot_limits')
    publications = _publications(root, publications, max_records)
    budget = _Budget(dict(max_scan_bytes_per_poll=max_bytes, max_record_bytes=max_record_bytes))
    with ExitStack() as stack:
        view = _JournalView('parent_exposure', root, stack)
        view.check_paths()
        scan = _ExposureScan(view, publications, speaker)
        try:
            require(_sha(budget.read(view.directory, 'JOURNAL.json')) == view.manifest_sha256, 'journal_manifest_changed')
            while view.state['index'] < max_records:
                result = view.next_record(budget)
                if result is None:
                    break
                scan.accept(*result)
            index = view.state['index']
            name = f'{index:020d}'
            if _exists(view.records, name + '.json') and _exists(view.records, name + '.intent.json'):
                raise SnapshotLimitExceeded('snapshot_record_limit')
            pending_tail = any(_exists(view.records, name + suffix)
                for suffix in ('.json', '.intent.json', '.json.partial', '.intent.json.partial'))
        except _PollLimit as error:
            raise SnapshotLimitExceeded('snapshot_byte_limit') from error
        view.check_paths()
        require(_sha(inbox_api._read(view.directory, 'JOURNAL.json', 4096)) == view.manifest_sha256,
            'journal_manifest_changed')
        return dict(schema=SCHEMA, exposure_schema=EXPOSURE_SCHEMA, journal_id=view.manifest['journal_id'],
            response_count=len(scan.boundaries), record_count=index, head_sha256=view.state['previous'],
            request_count=scan.request_count, latest_request_index=scan.latest_request_index,
            latest_request=scan.latest_request,
            events=scan.events, consumed_inbox=scan.consumed, boundaries=scan.boundaries,
            parent_consumptions=scan.consumptions, parent_exposures=scan.exposures,
            registered_inbox_count=len(scan.registrations), eligible_parent_inbox_count=len(scan.eligible),
            unexposed_parent_inbox_count=len(scan.eligible) - len(scan.consumed),
            attribution_scope='programme_publications' if publications is not None else 'speaker_only',
            coverage_basis='verified_parent_REQUEST_exposure_not_registration',
            scan_status='PENDING_TAIL' if pending_tail else 'AT_OBSERVED_HEAD',
            pending_request=view.state['request'] is not None,
            pending_response=view.state['response'] is not None,
            journal_bytes_read=max_bytes - budget.remaining)
