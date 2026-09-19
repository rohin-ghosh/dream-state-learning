"""Generate v4 candidates from hash-sealed v3; never overwrite inputs."""

import argparse
import hashlib
import importlib.util
from pathlib import Path


WORKER = Path(__file__).resolve().parent
V3 = WORKER.parent
V3_HELPER_SHA = 'e635da49cafa94507b3f9bc7f68afae18e0cb9cb6512742d76849f11196a912b'
V3_READER_SHA = '733671a1d73d67f1d8b6616ee4a4b449fb957997c6dd04e2052a1a7a5cb8b0de'
V3_CLI_SHA = '7a3652992c51f6dc72fe8df9198cae39e0109bb1f49a5f2a36c631bec12893ea'


def edit(original, expected, edits):
    if hashlib.sha256(original).hexdigest() != expected:
        raise ValueError('consumer_context_port_requires_sealed_v3_source')
    candidate = original
    for before, after in edits:
        if candidate.count(before.encode()) != 1:
            raise ValueError('consumer_context_port_requires_one_exact_seam: ' + before)
        candidate = candidate.replace(before.encode(), after.encode(), 1)
    return candidate


def port_reader(original):
    return edit(original, V3_READER_SHA, (
        ('def scan(journal, selection, *, prefix_proof=None):\n',
         'def scan(journal, selection, *, prefix_proof=None, prefix_admission=None):\n'
         "    require(prefix_proof is not None or prefix_admission is None, 'prefix_admission_requires_proof')\n"),
        ('        verified_prefix = prepare(journal, selection, prefix_proof)\n',
         '        verified_prefix = prepare(journal, selection, prefix_proof, admission=prefix_admission)\n'),
    ))


def port_helper(original):
    candidate = edit(original, V3_HELPER_SHA, (
        ("SCHEMA = 'R233_IMMUTABLE_PREFIX_PROOF_V1'\nGUARD_SCHEMA = 'R233_IMMUTABLE_PREFIX_OPERATOR_GUARD_V1'\n",
         "SCHEMA = 'R233_IMMUTABLE_PREFIX_PROOF_V2'\nGUARD_SCHEMA = 'R233_IMMUTABLE_PREFIX_OPERATOR_GUARD_V2'\n"
         "SAME_NAMESPACE = 'SAME_MOUNT_NAMESPACE'\n"
         "CROSS_NAMESPACE = 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'\n"
         "CONTEXT_ADMISSION_SCHEMA = 'R233_PREFIX_CONSUMER_CONTEXT_ADMISSION_V1'\n"
         'MINIMUM_QUIET_NS = 3_000_000_000\n'),
        ('        environment=environment(), trust=TRUST)\n',
         '        environment=environment(), trust=TRUST, metadata_policy=metadata_policy())\n'),
        ('def _validate_binding(journal, selection, binding):\n',
         'def _validate_binding(journal, selection, binding, consumer_context=None):\n'),
        ("    _fields(binding, ('selection', 'source', 'journal_type', 'environment', 'trust'), 'binding_schema')\n",
         "    _fields(binding, ('selection', 'source', 'journal_type', 'environment', 'trust', 'metadata_policy'), 'binding_schema')\n"
         "    require(binding['metadata_policy'] == metadata_policy(), 'exact_quiet_age_policy')\n"),
        ("    require(binding['trust'] == TRUST and binding['environment'] == environment(), 'same_trusted_environment')\n",
         "    require(binding['trust'] == TRUST, 'same_trust_model_required')\n"
         '    check_consumer_environment(binding, consumer_context)\n'),
        ('    locations = _locations(journal)\n',
         '    locations = _locations(journal)\n    sealing_started = clock_ns()\n'
         "    aged_pairs = metadata_preflight(journal, binding['selection']['complete_index'], sealing_started)\n"
         '    objects = source_objects(source)\n    require_quiet_source(objects, sealing_started)\n'),
        ("    for index in range(binding['selection']['complete_index'] + 1):\n        identities = _pair(journal, index)\n",
         "    for index in range(binding['selection']['complete_index'] + 1):\n        identities = aged_pairs[index]\n"),
        ('    proof = dict(schema=SCHEMA, binding=binding, locations=locations, records=records)\n',
         '    proof = dict(schema=SCHEMA, binding=binding, locations=locations, records=records, source_objects=objects,\n'
         '        sealing_clock=dict(started_wall_ns=sealing_started, finished_wall_ns=clock_ns()))\n'),
        ("    validate_source(source)\n    require(len(encoded(proof)) <= MAX_PROOF_BYTES, 'proof_size_bound')\n",
         "    validate_source(source)\n    recheck_source_objects(source, objects)\n"
         "    proof['sealing_clock']['finished_wall_ns'] = clock_ns()\n    validate_sealing_clock(proof)\n"
         "    require(len(encoded(proof)) <= MAX_PROOF_BYTES, 'proof_size_bound')\n"),
        ('        max_advance_records=0, max_advance_bytes=0):\n',
         '        max_advance_records=0, max_advance_bytes=0, consumer_context_mode=SAME_NAMESPACE):\n'),
        ('    return dict(schema=GUARD_SCHEMA, proof_path=proof_path, proof_sha256=proof_sha256,\n',
         "    require(consumer_context_mode in (SAME_NAMESPACE, CROSS_NAMESPACE), 'known_consumer_context_mode')\n"
         '    return dict(schema=GUARD_SCHEMA, consumer_context_mode=consumer_context_mode,\n'
         '        proof_path=proof_path, proof_sha256=proof_sha256,\n'),
        ('    def __init__(self, journal, selection, authority):\n',
         '    def __init__(self, journal, selection, authority, admission=None):\n'),
        ("        _fields(guard, ('schema', 'proof_path', 'proof_sha256', 'binding', 'resume'), 'guard_schema')\n",
         "        _fields(guard, ('schema', 'proof_path', 'proof_sha256', 'binding', 'resume',\n"
         "            'consumer_context_mode'), 'guard_schema')\n"),
        ("        _fields(proof, ('schema', 'binding', 'locations', 'records'), 'proof_schema')\n",
         "        _fields(proof, ('schema', 'binding', 'locations', 'records', 'source_objects', 'sealing_clock'), 'proof_schema')\n"),
        ("        _validate_binding(journal, guard['binding']['selection'], guard['binding'])\n",
         '        self.consumer_context, admission_snapshots = authorize_consumer_context(guard, authority, admission)\n'
         "        _validate_binding(journal, guard['binding']['selection'], guard['binding'], self.consumer_context)\n"),
        ('        self.snapshots = (guard_snapshot, proof_snapshot)\n',
         '        self.snapshots = (guard_snapshot, proof_snapshot, *admission_snapshots)\n'),
        ('    def recheck(self):\n',
         "    def recheck(self):\n        validate_sealing_clock(self.proof)\n"
         "        recheck_source_objects(self.guard['binding']['source'], self.proof['source_objects'])\n"),
        ("        require(environment() == self.guard['binding']['environment'], 'environment_changed_during_scan')\n",
         "        check_consumer_environment(self.guard['binding'], self.consumer_context)\n"),
        ("                proof_sha256=self.guard['proof_sha256'], trust=TRUST,\n",
         "                proof_sha256=self.guard['proof_sha256'], trust=TRUST,\n"
         '                consumer_context=deepcopy(self.consumer_context),\n'),
        ('def prepare(journal, selection, authority):\n    return VerifiedPrefix(journal, selection, authority)\n',
         'def prepare(journal, selection, authority, *, admission=None):\n'
         '    return VerifiedPrefix(journal, selection, authority, admission=admission)\n'),
    ))
    return candidate + b'\n\n' + (WORKER / 'context_extension.py').read_bytes()


def port_cli(original):
    return edit(original, V3_CLI_SHA, (
        ("        bootstrap._fields(guard, ('schema', 'proof_path', 'proof_sha256', 'binding', 'resume'), 'guard_schema')\n",
         "        bootstrap._fields(guard, ('schema', 'proof_path', 'proof_sha256', 'binding', 'resume',\n"
         "            'consumer_context_mode'), 'guard_schema')\n"),
        ("        bootstrap._fields(proof, ('schema', 'binding', 'locations', 'records'), 'proof_schema')\n",
         "        bootstrap._fields(proof, ('schema', 'binding', 'locations', 'records', 'source_objects', 'sealing_clock'), 'proof_schema')\n"),
        ('            max_advance_bytes=arguments.max_advance_bytes)\n',
         '            max_advance_bytes=arguments.max_advance_bytes, consumer_context_mode=arguments.consumer_context_mode)\n'),
        ('        state = scan(journal, selection, prefix_proof=authority)\n',
         '        admission = None\n'
         '        if arguments.admission is not None:\n'
         '            admission = dict(path=arguments.admission, sha256=arguments.admission_sha256,\n'
         '                field_path=json.loads(arguments.admission_field_path))\n'
         '        state = scan(journal, selection, prefix_proof=authority, prefix_admission=admission)\n'),
        ("    bind = commands.add_parser('bind-resume')\n",
         "    for name in ('admission', 'admission-sha256', 'admission-field-path'):\n"
         "        probe.add_argument('--' + name)\n"
         "    bind = commands.add_parser('bind-resume')\n"
         "    bind.add_argument('--consumer-context-mode', default=bootstrap.SAME_NAMESPACE,\n"
         '        choices=(bootstrap.SAME_NAMESPACE, bootstrap.CROSS_NAMESPACE))\n'),
    ))


def candidates():
    return {
        'checkpoint_tail_runtime.candidate.py': port_reader((V3 / 'checkpoint_tail_runtime.candidate.py').read_bytes()),
        'immutable_prefix_proof.py': port_helper((V3 / 'immutable_prefix_proof.py').read_bytes()),
        'prefix_cli.py': port_cli((V3 / 'prefix_cli.py').read_bytes()),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_directory', type=Path)
    arguments = parser.parse_args()
    outputs = candidates()
    for name, content in outputs.items():
        compile(content, name, 'exec')
        if (arguments.output_directory / name).exists():
            raise ValueError('candidate_output_must_not_exist')
    for name, content in outputs.items():
        with (arguments.output_directory / name).open('xb') as destination:
            destination.write(content)
        print(hashlib.sha256(content).hexdigest(), name)
