from datetime import datetime
import hashlib
import json
from pathlib import Path
import time


DIRECTORY = Path(__file__).resolve().parent
WORKER = DIRECTORY.parent
REPOSITORY = WORKER.parents[2]
REMOTE = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
TEMPLATES = WORKER / 'candidate5_initial3_templates'
AUTHORITY = WORKER / 'MAIN_INITIAL3_SOURCE_COPY_AUTHORITY_20260917.json'
OBSERVATION = WORKER / 'observation_20260917_generation2'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


def main():
    authority_raw = AUTHORITY.read_bytes()
    assert sha(authority_raw) == '254067adeef94d3947953bf6f45db8218f2135fbdd502925951a656139396f26'
    authority = json.loads(authority_raw)
    assert time.time() < authority['source_read_end_unix']
    allowlist_raw = (TEMPLATES / 'COPY_ALLOWLIST.template.json').read_bytes()
    assert sha(allowlist_raw) == authority['copy_allowlist_template']['sha256']
    allowlist = json.loads(allowlist_raw)
    observation, summary = read(OBSERVATION / 'OBSERVATION.json'), read(OBSERVATION / 'SUMMARY.json')
    cutoff = observation['started_unix']
    assert cutoff > authority['enrollment_authorized_unix']
    assert observation['cohort']['sha256'] == authority['cohort_sha256']
    metadata = DIRECTORY / 'metadata'
    metadata.mkdir(mode=0o700, exist_ok=False)
    files = {}

    def install(relative, raw):
        path = metadata / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o400)
        reference = dict(path=str(REMOTE / 'inputs/candidate5' / relative), sha256=sha(raw))
        files[relative] = dict(local_path=str(path), **reference, bytes=len(raw))
        return reference

    main_ref = install('shared/MAIN_SOURCE_COPY_AUTHORITY.json', authority_raw)
    observation_ref = install('shared/SOURCE_OBSERVATION.json', (OBSERVATION / 'OBSERVATION.json').read_bytes())
    admission_ref = install('shared/ADMISSION_WITNESSES.json', (OBSERVATION / 'ADMISSION_WITNESSES.json').read_bytes())
    for item in allowlist['shared_metadata']:
        raw = (REPOSITORY / item['local_verified_archive']).read_bytes()
        assert sha(raw) == item['sha256']
        relative = str(Path(item['destination']).relative_to(REMOTE / 'inputs/candidate5'))
        install(relative, raw)
    exposures = {}
    for arm, evidence in summary['arms'].items():
        assert evidence['initial_commit_sha256'] == authority['initial_commits'][arm]
        assert evidence['retained_journal_status'] == 'VERIFIED_RETAINED_PREFIX'
        assert evidence['journal_listing_stable'] and evidence['all_intents_paired']
        assert evidence['initial_readout_bindings_verified'] and evidence['initial_readout_completion_marker_present']
        assert not evidence['initial_readout_failure_marker_present']
        exposures[arm] = {}
        intervals = dict(birth=evidence['birth_bracket_utc'],
            train=[evidence['first_train_request_utc'], evidence['first_train_response_utc']],
            evaluation=[evidence['first_readout_open_utc'], evidence['first_readout_closed_utc']])
        for kind, interval in intervals.items():
            earliest, latest = [datetime.fromisoformat(value).timestamp() for value in interval]
            assert 1789620776.0605557 < earliest <= latest <= cutoff
            event = dict(schema='R159_FIRST_EXPOSURE_V1', cohort_sha256=authority['cohort_sha256'],
                arm=arm, kind=kind, coverage_complete=True, observed_unix=cutoff, status='OBSERVED_INTERVAL',
                first_earliest_unix=earliest, first_latest_unix=latest,
                source_evidence=[observation_ref, admission_ref, main_ref])
            exposures[arm][kind] = install(f'exposures/{arm}_{kind}.json', encoded(event))
    timing = read(TEMPLATES / 'TIMESTAMP_CUSTODY.template.json')
    timing.update(status='TRUSTED_SOURCE_OWNER_ATTESTED', arm_exposures=exposures,
        enrollment_unix=authority['enrollment_authorized_unix'], observed_unix=cutoff,
        saved_initial_generation_calls=0, saved_initial_optimizer_updates=0,
        saved_initial_training_exposure=False, saved_initial_evaluation_exposure=False)
    timing_ref = install('TIMESTAMP_CUSTODY.json', encoded(timing))
    owner = read(TEMPLATES / 'SOURCE_OWNER_AUTHORITY.template.json')
    owner.update(status='SOURCE_OWNER_ADMITTED', read_end_unix=authority['source_read_end_unix'],
        timestamp_custody=timing_ref, main_source_copy_authority=main_ref,
        source_observation=observation_ref, admission_witnesses=admission_ref,
        attestation_scope='Main exclusive candidate5 run namespaces and retained contiguous custody history; not machine-wide absence',
        observed_unix=cutoff)
    owner_ref = install('SOURCE_OWNER_AUTHORITY.json', encoded(owner))
    byte_count = sum(item['bytes'] for item in files.values())
    assert byte_count < authority['metadata_copy_bytes_maximum']
    output = dict(status='MAIN_SCOPED_CUSTODY_FINALIZED_BEFORE_ADAPTER_COPY', created_unix=time.time(),
        metadata_files=files, metadata_bytes=byte_count, common_observation_cutoff_unix=cutoff,
        source_owner_authority=owner_ref, timestamp_custody=timing_ref, main_authority=main_ref,
        gpu_execution_authorized=False, enrollment_reserved=False, original_unknown_unchanged=True)
    with (DIRECTORY / 'CUSTODY_PREPARED.json').open('xb') as stream:
        stream.write(encoded(output))
    print(json.dumps({key: value for key, value in output.items() if key != 'metadata_files'}, sort_keys=True))


if __name__ == '__main__':
    main()
