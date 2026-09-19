"""Bounded original-byte TRAIN capture; no collection, grading or review generation."""

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from gpu import orch_r158_train_gym as gym
from organism_v6 import orch_r159_train_eligibility as eligibility


SCHEMA = 'R159_TRAIN_CAPTURE_V1'
FORBIDDEN = re.compile(r'(^|[_ .-])(held(?:out)?|final|readout|sealed|eval(?:uation)?)([0-9]|[_ .-]|$)',
                       re.IGNORECASE)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n'


def decode(raw):
    def invalid(value):
        raise ValueError('nonfinite_JSON')
    try:
        value = json.loads(raw, object_pairs_hook=eligibility.unique_object, parse_constant=invalid)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('invalid_bounded_JSON') from error
    require(type(value) is dict, 'JSON_object_required')
    return value


def canonical(path):
    value = os.fspath(path)
    require(type(value) is str and Path(value).is_absolute() and str(Path(value)) == value
            and '..' not in Path(value).parts, 'canonical_absolute_path_required')
    require(not any(FORBIDDEN.search(part) for part in Path(value).parts), 'held_or_evaluation_path_forbidden')
    return Path(value)


def signature(metadata):
    return (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns,
            metadata.st_ctime_ns, metadata.st_mode)


@dataclass(frozen=True)
class Limits:
    max_files: int = 48
    max_file_bytes: int = 16 * 1024**2
    max_read_bytes: int = 128 * 1024**2
    max_output_bytes: int = 128 * 1024**2

    def __post_init__(self):
        for value in (self.max_files, self.max_file_bytes, self.max_read_bytes, self.max_output_bytes):
            require(type(value) is int and value > 0, 'positive_integer_budget_required')
        require(self.max_files <= 128 and self.max_file_bytes <= 64 * 1024**2
                and self.max_read_bytes <= 512 * 1024**2 and self.max_output_bytes <= 512 * 1024**2,
                'hard_capture_budget_ceiling')


class Reader:
    def __init__(self, limits):
        self.limits, self.read_bytes, self.reads = limits, 0, 0
        self.paths = set()

    def read(self, path):
        path = canonical(path)
        self.paths.add(str(path))
        require(len(self.paths) <= self.limits.max_files, 'capture_file_budget')
        self.reads += 1
        require(self.reads <= 4 * self.limits.max_files, 'capture_read_count_budget')
        with gym.console._directory(path.parent) as directory:
            descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                                 dir_fd=directory)
            with os.fdopen(descriptor, 'rb') as stream:
                before = os.fstat(stream.fileno())
                require(stat.S_ISREG(before.st_mode), 'regular_capture_file_required')
                require(0 < before.st_size <= self.limits.max_file_bytes, 'capture_file_byte_budget')
                require(self.read_bytes + before.st_size + 1 <= self.limits.max_read_bytes,
                        'capture_total_read_budget')
                raw = stream.read(before.st_size + 1)
                self.read_bytes += len(raw)
                after = os.fstat(stream.fileno())
                current = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
                require(signature(before) == signature(after) == signature(current)
                        and len(raw) == before.st_size, 'capture_changed_during_read')
        return raw, signature(before)


class Capture:
    def __init__(self, root, limits):
        self.root, self.reader, self.artifacts, self.identities = root, Reader(limits), {}, {}

    def file(self, path):
        path = canonical(path)
        require(path.is_relative_to(self.root), 'capture_outside_exact_life')
        key = str(path)
        if key not in self.artifacts:
            raw, identity = self.reader.read(path)
            decode(raw)
            self.artifacts[key] = eligibility.capture(key, raw)
            self.identities[key] = identity
        return self.artifacts[key]

    def document(self, path):
        return decode(self.file(path)['raw'])

    def independently_hash(self):
        pins = {}
        for path, artifact in self.artifacts.items():
            raw, identity = self.reader.read(path)
            require(identity == self.identities[path] and raw == artifact['raw'], 'capture_changed_between_passes')
            pins[path] = sha(raw)
        return pins

    def publication(self, source, field):
        source_path = Path(source['path'])
        intent = self.document(source_path.parent / 'PUBLICATION_INTENT.json')
        require(intent == {field: source['sha256'], 'replay_allowed': False}, 'publication_intent_join')
        publication = self.file(source_path.parent / 'PUBLICATION.json')
        value = decode(publication['raw'])
        require(set(value) == {'id', 'path', 'sha256'} and type(value['id']) is str
                and re.fullmatch('[0-9a-f]{32}', value['id']) is not None, 'exact_publication_identity')
        expected = self.root / 'stream/inbox' / (value['id'] + '.json')
        require(value['path'] == str(expected), 'publication_path_outside_exact_inbox')
        message = self.file(expected)
        payload = decode(message['raw'])
        require(value['sha256'] == message['sha256'] and set(payload) == {
            'schema', 'id', 'text', 'split', 'actor', 'speaker', 'source_receipt'}
            and payload['schema'] == 'R127_ATTRIBUTED_INBOX_V1' and payload['id'] == value['id']
            and payload['split'] == 'TRAIN' and payload['actor'] == 'environment'
            and payload['speaker'] == 'Tool'
            and payload['source_receipt'] == dict(path=source['path'], sha256=source['sha256']),
            'published_original_source_join')
        return dict(publication=publication, message=message)

    def triple(self, index, journal):
        require(type(index) is int and 0 < index < 10**12, 'explicit_bounded_response_index')
        records = []
        for number in (index - 1, index, index + 1):
            artifact = self.file(self.root / 'stream/records' / f'{number:020d}.json')
            value = decode(artifact['raw'])
            require(value.get('index') == number and value.get('journal_id') == journal['journal_id'],
                    'exact_journal_index_identity')
            if number == index - 1:
                require(value.get('kind') == 'REQUEST' and value['document'].get('split') == 'TRAIN',
                        'TRAIN_request_required_before_response_read')
            records.append(artifact)
        response = decode(records[1]['raw'])
        require(response.get('kind') == 'RESPONSE', 'exact_response_record_required')
        generation = response['document']['response']
        require(generation.get('terminal') is True and generation.get('truncated') is False,
                'complete_nontruncated_capture_required')
        require(decode(records[2]['raw']).get('kind') == 'COMMITTED', 'committed_capture_required')
        return records

    def attempt(self, task_directory, index, journal):
        records = self.triple(index, journal)
        directory = task_directory / f'answer_{index:020d}'
        evidence = dict(records=records, intent=self.file(directory / 'INTENT.json'),
                        result=self.file(directory / 'RESULT.json'))
        evidence.update(self.publication(evidence['result'], 'result_sha256'))
        result = decode(evidence['result']['raw'])
        require(type(result.get('accepted')) is bool and eligibility.finite_number(result.get('score')),
                'actual_result_score_required')
        text = ('Training puzzle check: ' + ('accepted' if result['accepted'] else 'not accepted')
                + f"; verifier score {result['score']:.3f}. This is a real check of your submitted answer."
                + ' The reference answer is not shown.')
        require(decode(evidence['message']['raw'])['text'] == text, 'exact_result_publication_text')
        return evidence


def review_template(context, label, prior=None, feedback_text=None):
    sources = dict(target=context['row']['target'], prefix=json.dumps(context['row']['prefix'],
        sort_keys=True, separators=(',', ':'), allow_nan=False), task=context['task']['text'],
        result=context['result_artifact']['raw'].decode('utf-8'))
    axes = list(eligibility.AXES)
    if prior is not None:
        sources.update(prior_target=prior['row']['target'], feedback=feedback_text)
        axes.append('feedback_use')
    if 'anchor' in context:
        sources.update(anchor_target=context['anchor']['row']['target'],
            anchor_result=context['anchor']['result_artifact']['raw'].decode('utf-8'),
            anchor_feedback=context['anchor_feedback_text'])
        axes.extend(eligibility.REFLECTION_AXES)
    judgments = {axis: dict(status=None, substantive=None, reason=None, evidence=[]) for axis in axes}
    if label == 'feedback_use':
        judgments['feedback_use'].update(changed_action_known=None, changed_action_or_expectation=None)
    return dict(schema='R159_UNJUDGED_REVIEW_TEMPLATE_V1', judgments_generated=False,
        sources={name: dict(text=text, sha256=eligibility.text_sha256(text),
                           full_source_span=dict(source=name, start=0, end=len(text), quote=text))
                 for name, text in sources.items()}, span_units='Python Unicode code-point indices; end exclusive',
        review_envelope_template=dict(schema=eligibility.REVIEW_SCHEMA, binding=deepcopy(context['binding']),
            reviewer_id=None, principal_id=None, session_id=None, full_text_read=None, full_context_read=None,
            review_text=None, status=None, axes=judgments))


def assemble(root, task_index, response_index, *, target_kind, label, generator_binding,
             excluded_task_ids, anchor_response_index=None, feedback_response_index=None, limits=Limits()):
    root = canonical(root)
    require(root.parent.name.startswith('orch_r158_') and root.name in (
        'parented_learning', 'parented_frozen', 'unparented_learning'), 'exact_R158_matched_life_required')
    require(target_kind in eligibility.TARGET_KINDS and label in eligibility.LABELS, 'explicit_candidate_kind_and_label')
    require((anchor_response_index is not None) == (target_kind == 'POST_FEEDBACK_REFLECTION'),
            'explicit_reflection_anchor_only')
    require((feedback_response_index is not None) == (label == 'feedback_use'), 'explicit_feedback_chain_only')
    require(type(excluded_task_ids) in (list, tuple, set, frozenset)
            and all(type(value) is str for value in excluded_task_ids), 'caller_exclusions_required')
    identifier = gym.task_id(task_index)
    require(identifier not in excluded_task_ids, 'caller_excluded_task')
    capture = Capture(root, limits)
    task_directory = root / 'train_environment' / f'task_{task_index:06d}'
    task = capture.file(task_directory / 'TASK.json')
    task_document = decode(task['raw'])
    require(task_document.get('binding') == generator_binding and type(generator_binding) is dict,
            'caller_generator_authority_mismatch')
    require(task_document.get('split') == 'TRAIN' and task_document.get('task_index') == task_index
            and task_document.get('task_id') == identifier, 'exact_requested_TRAIN_task')
    task_publication = capture.publication(task, 'receipt_sha256')
    journal = capture.document(root / 'stream/JOURNAL.json')
    require(set(journal) == {'schema', 'journal_id'} and journal['schema'] == 'R125_STREAM_JOURNAL_V1'
            and type(journal['journal_id']) is str and re.fullmatch('[0-9a-f]{32}', journal['journal_id']),
            'original_journal_manifest')
    packet = dict(target_kind=target_kind, label=label, task=task,
                  task_publication=task_publication['publication'], task_message=task_publication['message'], reviews=[])
    if target_kind == 'ANSWER':
        attempt = capture.attempt(task_directory, response_index, journal)
        packet.update({key: attempt[key] for key in ('records', 'intent', 'result')})
    else:
        require(type(anchor_response_index) is int and anchor_response_index < response_index,
                'earlier_explicit_anchor_required')
        packet['anchor_attempt'] = capture.attempt(task_directory, anchor_response_index, journal)
        packet['records'] = capture.triple(response_index, journal)
    if feedback_response_index is not None:
        require(type(feedback_response_index) is int and feedback_response_index < response_index,
                'earlier_explicit_feedback_required')
        packet['feedback'] = capture.attempt(task_directory, feedback_response_index, journal)
    pins = capture.independently_hash()
    compiler = eligibility.Compiler(pins, {}, deepcopy(generator_binding), excluded_task_ids)
    context = compiler.context(packet)
    prior, feedback_text = None, None
    if label == 'feedback_use':
        prior, feedback_text = compiler.feedback(packet['feedback'], context)
        context['binding'].update(earlier_target_sha256=eligibility.text_sha256(prior['row']['target']),
            earlier_result_sha256=prior['result_artifact']['sha256'],
            feedback_message_sha256=packet['feedback']['message']['sha256'])
    return dict(schema=SCHEMA, status='CAPTURED_UNREVIEWED_NOT_ELIGIBLE', packet=packet,
                artifacts=capture.artifacts, observed_path_hashes=pins,
                authority=dict(generator_binding=deepcopy(generator_binding), excluded_task_ids=sorted(excluded_task_ids)),
                review_template=review_template(context, label, prior, feedback_text),
                budgets=dict(files=len(capture.artifacts), reads=capture.reader.reads,
                             read_bytes=capture.reader.read_bytes), limits=limits)


def compile_reviewed(packet, reviews, *, trusted_artifacts, reviewer_provenance, generator_binding,
                     excluded_task_ids):
    require(type(reviews) is list and len(reviews) >= 2 and type(reviewer_provenance) is dict
            and len(reviewer_provenance) >= 2, 'supplied_review_envelopes_and_provenance_required')
    require(type(packet) is dict and packet.get('reviews') == [], 'unreviewed_capture_packet_required')
    for artifact in reviews:
        require(type(artifact) is dict and set(artifact) == {'path', 'sha256', 'raw'}
                and type(artifact['raw']) is bytes and sha(artifact['raw']) == artifact['sha256'],
                'supplied_original_review_capture_required')
        review = decode(artifact['raw'])
        require(review.get('schema') == eligibility.REVIEW_SCHEMA and review.get('status') in eligibility.STATUSES
                and review.get('full_text_read') is True and review.get('full_context_read') is True
                and eligibility.nonempty(review.get('review_text')), 'completed_review_not_blank_template_required')
    candidate = deepcopy(packet)
    candidate['reviews'] = deepcopy(reviews)
    return eligibility.compile_candidate(candidate, trusted_artifacts=trusted_artifacts,
        reviewer_provenance=reviewer_provenance, generator_binding=generator_binding,
        excluded_task_ids=excluded_task_ids)


def write_capture(bundle, destination):
    destination = canonical(destination)
    task_root = Path(bundle['packet']['task']['path']).parents[2]
    require(not destination.is_relative_to(task_root), 'capture_output_outside_live_life_required')
    files = {}
    for artifact in bundle['artifacts'].values():
        require(sha(artifact['raw']) == artifact['sha256'], 'output_capture_hash')
        files[artifact['sha256'] + '.bin'] = artifact['raw']

    def wire(value):
        if type(value) is dict and set(value) == {'path', 'sha256', 'raw'}:
            require(value['path'] in bundle['observed_path_hashes']
                    and bundle['observed_path_hashes'][value['path']] == value['sha256'], 'output_observed_pin')
            return dict(path=value['path'], sha256=value['sha256'], blob=value['sha256'] + '.bin')
        if type(value) is dict:
            return {key: wire(item) for key, item in value.items()}
        if type(value) is list:
            return [wire(item) for item in value]
        return value

    files.update({'PACKET.json': encoded(wire(bundle['packet'])),
                  'OBSERVED_PATH_HASHES.json': encoded(bundle['observed_path_hashes']),
                  'REVIEW_TEMPLATE.json': encoded(bundle['review_template']),
                  'AUTHORITY_INPUT.json': encoded(bundle['authority'])})
    manifest = dict(schema=SCHEMA, status=bundle['status'], capture_budgets=bundle['budgets'],
                    files={name: sha(raw) for name, raw in files.items()}, trust_established=False,
                    verifier_replayed=False, reviews_generated=False, eligibility_decided=False)
    files['MANIFEST.json'] = encoded(manifest)
    require(len(files) <= bundle['limits'].max_files
            and all(len(raw) <= bundle['limits'].max_file_bytes for raw in files.values()),
            'capture_output_file_budget')
    require(sum(map(len, files.values())) <= bundle['limits'].max_output_bytes, 'capture_output_byte_budget')
    with gym.console._directory(destination.parent) as parent:
        os.mkdir(destination.name, mode=0o700, dir_fd=parent)
        directory = os.open(destination.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            for name, raw in files.items():
                gym.console._stage(directory, name, raw)
            os.fsync(parent)
        finally:
            os.close(directory)
    return dict(path=str(destination / 'MANIFEST.json'), sha256=sha(files['MANIFEST.json']))


def load_packet(directory, *, expected_manifest_sha256, limits=Limits()):
    directory = canonical(directory)
    reader = Reader(limits)
    raw, _ = reader.read(directory / 'MANIFEST.json')
    require(sha(raw) == expected_manifest_sha256, 'externally_pinned_capture_manifest_required')
    manifest = decode(raw)
    require(manifest['schema'] == SCHEMA and type(manifest['files']) is dict, 'capture_manifest_schema')
    blobs = {}
    for name, expected in manifest['files'].items():
        require(type(name) is str and Path(name).name == name and name not in ('.', '..'), 'flat_capture_blob_name')
        value, _ = reader.read(directory / name)
        require(sha(value) == expected, 'captured_bundle_file_hash')
        blobs[name] = value
    observed = decode(blobs['OBSERVED_PATH_HASHES.json'])

    def restore(value):
        if type(value) is dict and set(value) == {'path', 'sha256', 'blob'}:
            canonical(value['path'])
            require(value['blob'] == value['sha256'] + '.bin' and observed.get(value['path']) == value['sha256'],
                    'capture_descriptor_pin_join')
            artifact = eligibility.capture(value['path'], blobs[value['blob']])
            require(artifact['sha256'] == value['sha256'], 'capture_descriptor_original_bytes')
            return artifact
        if type(value) is dict:
            return {key: restore(item) for key, item in value.items()}
        if type(value) is list:
            return [restore(item) for item in value]
        return value

    packet = restore(decode(blobs['PACKET.json']))
    require(packet.get('reviews') == [], 'captured_packet_has_no_generated_reviews')
    return packet


def integration():
    reader = Reader(Limits())
    return dict(schema=SCHEMA, compiler_schema=eligibility.SCHEMA, review_schema=eligibility.REVIEW_SCHEMA,
                target_kinds=list(eligibility.TARGET_KINDS), labels=list(eligibility.LABELS),
                modules={module.__name__: dict(path=str(Path(module.__file__).absolute()),
                    sha256=sha(reader.read(Path(module.__file__).absolute())[0])) for module in (eligibility, gym)},
                dataset_loaded=False, installed_distribution_authenticated=False,
                separate_JSON_schema_file=None, schema_authority='loaded compiler implementation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('capture', 'schema'))
    parser.add_argument('--root')
    parser.add_argument('--task-index', type=int)
    parser.add_argument('--response-index', type=int)
    parser.add_argument('--target-kind', choices=eligibility.TARGET_KINDS)
    parser.add_argument('--label', choices=eligibility.LABELS)
    parser.add_argument('--anchor-response-index', type=int)
    parser.add_argument('--feedback-response-index', type=int)
    parser.add_argument('--authority')
    parser.add_argument('--output')
    options = parser.parse_args()
    if options.action == 'schema':
        result = integration()
    else:
        require(all(value is not None for value in (options.root, options.task_index, options.response_index,
                    options.target_kind, options.label, options.authority, options.output)), 'explicit_capture_arguments')
        authority = decode(Reader(Limits()).read(options.authority)[0])
        require(set(authority) == {'generator_binding', 'excluded_task_ids'}, 'Main_authority_input_fields')
        bundle = assemble(options.root, options.task_index, options.response_index, target_kind=options.target_kind,
            label=options.label, anchor_response_index=options.anchor_response_index,
            feedback_response_index=options.feedback_response_index, **authority)
        result = write_capture(bundle, options.output)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
