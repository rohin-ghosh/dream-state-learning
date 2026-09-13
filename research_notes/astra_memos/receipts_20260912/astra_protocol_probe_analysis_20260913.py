"""Readonly capsule verification and reproduction of fixed protocol-practice counts."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def analyze(archive):
    archive = Path(archive)
    validation = json.loads(Path(str(archive)+'.validation.json').read_text())
    assert sha(archive.read_bytes()) == validation['archive_sha256'], 'capsule hash mismatch'
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        assert all(member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts for member in members)
        assert len({member.name for member in members}) == len(members), 'duplicate archive member'
        files = {member.name:stream.extractfile(member).read() for member in members}
    assert {name:sha(data) for name,data in files.items()} == validation['files'], 'member hashes differ'
    plan, stored = json.loads(files['plan.json']), json.loads(files['audit.json'])
    material_path = Path('/tmp/astra_birth_protocol_probe_material_20260913.py')
    assert sha(material_path.read_bytes()) == '2799efda619f7686db88d7990b203a3c7ad39eb8577228a26402037de16cc66b'
    specification = importlib.util.spec_from_file_location('analysis_original_material', material_path)
    material = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(material)
    original = material.build_candidate()
    assert [{key:value for key,value in case.items() if key != 'context'} for case in plan['candidate']['cases']] == [
        {key:value for key,value in case.items() if key != 'context'} for case in original['cases']], 'case/label/source difference'
    outputs = {}
    summary = dict(archive=str(archive), archive_sha256=validation['archive_sha256'], verified_members=len(files), states={})
    for state in plan['states']:
        outputs[state] = {}
        totals = Counter()
        records = {}
        for request in plan['cells'][state]['requests']:
            prefix = f"run/{state}/data/calls/{request['call_id']}"
            sent, got = json.loads(files[prefix+'.request.json']), json.loads(files[prefix+'.response.json'])
            assert sent['request'] == request
            response = got['response']
            outputs[state][request['case_id']] = response['text']
            totals.update(calls=1, input_tokens=len(response['prompt_token_ids']), output_tokens=len(response['output_token_ids']),
                token_limits=int(len(response['output_token_ids']) >= request['max_tokens']),
                eos=int(plan['eos_token_id'] in response['output_token_ids']),
                explicit_stop_matches=int(response['stop_reason'] is not None), call_seconds=got['ended']-sent['started'])
            if request['role'] == 'record':
                records[request['case_id']] = dict(request=request, text=response['text'])
        summary['states'][state] = dict(totals=dict(totals), records=records)
    reproduced = material.check_outputs(original, outputs)
    assert reproduced == stored['scores'] and outputs == stored['raw_outputs'], 'stored scores/raw text differ'
    for state in plan['states']:
        summary['states'][state]['families'] = {}
        for family in material.FAMILIES:
            rows = [reproduced[state][case['id']] for case in original['cases'] if case['family'] == family]
            summary['states'][state]['families'][family] = dict(denominator=len(rows), **{
                metric:sum(row[metric] for row in rows) for metric in ('parser_valid','public_contract_correct','instruction_compliant')})
    launched = json.loads(files['launch/process.json'])['started_wall']
    summary.update(launch_to_exit_seconds=json.loads(files['launch/exit.json'])['ended_wall']-launched,
                   launch_to_recorded_gpu_release_seconds=json.loads(files['release.json'])['verified_wall']-launched,
                   limitation='Same frozen grader reproduced, not independent scientific review; formatting-sensitive contract; exposed practice.')
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archives', nargs='+')
    args = parser.parse_args()
    results = [analyze(archive) for archive in args.archives]
    output = dict(runs=results)
    if len(results) == 2:
        output['unchanged_record_controls'] = {}
        for state in ('OFF','AUTH'):
            before, after = [result['states'][state]['records'] for result in results]
            assert set(before) == set(after)
            assert all(before[key]['request'] == after[key]['request'] for key in before), 'record control input changed'
            output['unchanged_record_controls'][state] = dict(denominator=len(before), identical_outputs=sum(
                before[key]['text'] == after[key]['text'] for key in before))
    print(json.dumps(output, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
