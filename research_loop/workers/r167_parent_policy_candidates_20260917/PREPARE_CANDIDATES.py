"""Create-only local prompt candidates, never a rollout or clean-custody assertion."""

import hashlib
import json
from pathlib import Path
import time

from gpu import orch_r166_parent_policy as policy


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[2]
METADATA = REPOSITORY/'research_loop/workers/r166_parenting_update_20260917/LOCAL_PARENT_METADATA.json'


def reference(path):
    return dict(path=str(path.resolve()), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    metadata = json.loads(METADATA.read_bytes())
    entries = []
    for observed in metadata['parents']:
        original = observed['config']
        identifier = original['branch'] + '_' + str(observed['pid'])
        directory = ROOT/identifier
        directory.mkdir(mode=0o700)
        receipt = dict(schema='R167_PROMPT_ONLY_CANDIDATE_V1', candidate=identifier,
            prepared_unix=time.time(), root=original['root'], node=original['node'],
            prior_observation_unix=metadata['observed_unix'], prior_metadata=reference(METADATA),
            parent_output=observed['output'], prior_parent_pid=observed['pid'],
            original_config=observed['config_ref'], original_source=observed['source_ref'],
            child_untouched=True, no_publication=True, no_process_signals=True,
            clean_custody_confirmed=False, rollout_authorized=False)
        try:
            policy.require('unparented' not in original['root'].lower()
                and 'unparented' not in original['branch'].lower(), 'labelled_unparented_excluded')
            original_path = Path(observed['config_ref']['path'])
            policy.require(original_path.stat().st_size <= policy.MAX_RECEIPT_BYTES, 'bounded_config')
            raw = original_path.read_bytes()
            policy.require(hashlib.sha256(raw).hexdigest() == observed['config_ref']['sha256']
                and json.loads(raw) == original, 'original_config_changed_since_audit')
            principles = Path(original['principles_path'])
            policy.require(principles.stat().st_size <= policy.MAX_RECEIPT_BYTES, 'bounded_principles')
            old_bytes = principles.read_bytes()
            policy.require(hashlib.sha256(old_bytes).hexdigest() == original['principles_sha256'],
                           'original_principles_changed')
            new_path = directory/'PRINCIPLES.md'
            with new_path.open('xb') as output:
                output.write(policy.prompt_policy_bytes(old_bytes))
            candidate = policy.prompt_only_config(original, principles_ref=reference(new_path),
                                                   existing_parented=True)
            changed = sorted(key for key in candidate if candidate[key] != original[key])
            policy.require(changed == ['principles_path', 'principles_sha256'], 'two_fields_only')
            policy.community.write(directory/'CONFIG.json', candidate)
            instruction, unused = policy.parent.prompt(candidate,
                dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[]))
            policy.require(policy.PROMPT_POLICY_MARKER in instruction, 'instruction_transport_inclusion')
            source_path = Path(observed['source_ref']['path'])
            source_matches = source_path.is_file() and source_path.stat().st_size <= policy.MAX_RECEIPT_BYTES
            source_matches = source_matches and reference(source_path)['sha256'] == observed['source_ref']['sha256']
            process = dict(observed_unix=time.time(), same_identity=False)
            try:
                process_dir = Path('/proc')/str(observed['pid'])
                process_stat = (process_dir/'stat').read_text().rsplit(')', 1)[1].split()
                argv_raw = (process_dir/'cmdline').read_bytes()
                policy.require(len(argv_raw) <= 65536, 'bounded_parent_argv')
                argv = argv_raw.rstrip(b'\0').decode().split('\0')
                process.update(state=process_stat[0], start_ticks=process_stat[19],
                    same_identity=argv == observed['argv'] and process_stat[19] == observed['start_ticks'],
                    argv_sha256=hashlib.sha256(argv_raw).hexdigest())
            except (OSError, ValueError, IndexError) as error:
                process.update(error_type=type(error).__name__)
            receipt.update(status='PREPARED_NOT_ADMITTED', candidate_config=reference(directory/'CONFIG.json'),
                principles=reference(new_path), changed_fields=changed, source_still_matches_audit=source_matches,
                parent_identity_observation=process, blockers=[
                    'Main fresh child/parent custody and no inflight/unknown-publication reconciliation',
                    'Preserve existing output cursor/ledger via runner-specific successor handoff',
                    'Main scoped GO and runner-specific fresh source/config gate before activation'])
        except (OSError, ValueError, KeyError) as error:
            receipt.update(status='REFUSED_NOT_ADMITTED', error_type=type(error).__name__, error=str(error))
        policy.community.write(directory/'OWNERSHIP_CANDIDATE.json', receipt)
        entries.append(dict(candidate=identifier, status=receipt['status'], receipt=reference(directory/'OWNERSHIP_CANDIDATE.json')))
    policy.community.write(ROOT/'INDEX.json', dict(schema='R167_LOCAL_PROMPT_CANDIDATES_V1',
        finished_unix=time.time(), metadata=reference(METADATA), candidates=entries,
        policy=reference(Path(policy.__file__)), no_remote_calls=True, no_provider_calls=True,
        no_child_changes=True, no_parent_activation=True))
    print(json.dumps(dict(total=len(entries), prepared=sum(entry['status'] == 'PREPARED_NOT_ADMITTED'
        for entry in entries), refused=sum(entry['status'] == 'REFUSED_NOT_ADMITTED' for entry in entries))))


if __name__ == '__main__':
    main()
