import argparse
import hashlib
import json
from pathlib import Path
import statistics
import tarfile


ARCHIVE = Path('/data/home/rohing/dream-state/gpu_artifacts_local/parented_record_20260913_attempt1/evidence.tar')
ARCHIVE_SHA = 'c69caf2c80a682fac26048d351d6f148216161dde7ee5b1ad847dacd0ee8b439'


def percentile(values, fraction):
    ordered = sorted(values)
    assert ordered and 0 <= fraction <= 1
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def profile():
    assert hashlib.file_digest(ARCHIVE.open('rb'), 'sha256').hexdigest() == ARCHIVE_SHA
    rows = []
    with tarfile.open(ARCHIVE) as archive:
        members = {member.name: member for member in archive.getmembers()}
        assert len(members) == len(archive.getmembers())

        def read(name):
            member = members[name]
            assert member.isfile() and member.size < 20000000
            return json.loads(archive.extractfile(member).read())

        for seed in range(3):
            root = f'parented_record_seed{seed}_20260913_attempt1'
            launch = read(root + '.launcher/launched.json')
            controller = read(root + '.launcher/controller.json')
            controller_exit = read(root + '.launcher/controller_exit.json')
            collector = read(root + '.launcher/collector.json')
            collector_exit = read(root + '.launcher/collector_exit.json')
            exited = read(root + '.launcher/exit.json')
            assert controller_exit['returncode'] == collector_exit['returncode'] == exited['returncode'] == 0
            plan = read(root + '/plan.json')
            assert launch['seed'] == seed and len(plan['stages']) == 9
            responses = [read(name) for name in members if name.startswith(root + '/run/') and name.endswith('.response.json')]
            assert len(responses) == 300
            durations = [response['ended'] - response['started'] for response in responses]
            assert all(duration >= 0 for duration in durations)
            fits = [read(root + f'/arms/{arm}/run/WRITE_fit/fit.json') for arm in ('P', 'N')]
            fit_seconds = sum(fit['elapsed_seconds'] for fit in fits)
            controller_seconds = controller_exit['completed_unix'] - controller['started_unix']
            generation_seconds = sum(durations)
            assert controller_seconds >= fit_seconds + generation_seconds
            rows.append(dict(seed=seed, calls=len(responses), fits=2,
                             updates=sum(fit['updates'] for fit in fits),
                             launched_unix=launch['started_unix'], exited_unix=exited['completed_unix'],
                             controller_seconds=controller_seconds,
                             launch_to_collection_seconds=exited['completed_unix'] - launch['started_unix'],
                             collection_seconds=collector_exit['completed_unix'] - collector['started_unix'],
                             fit_elapsed_seconds=fit_seconds, generation_seconds=generation_seconds,
                             other_controller_seconds=controller_seconds - fit_seconds - generation_seconds,
                             generation_p50_seconds=statistics.median(durations), generation_p95_seconds=percentile(durations, .95)))
    mean = statistics.mean(row['launch_to_collection_seconds'] for row in rows)
    return dict(archive_sha256=ARCHIVE_SHA, rows=rows,
                three_gpu_makespan_seconds=max(row['exited_unix'] for row in rows) - min(row['launched_unix'] for row in rows),
                measured_mean_pair_seconds=mean,
                scenario_four_repeated_identical_blocks_seconds=4 * mean,
                scenario_scope='Arithmetic forecast only: four sequential copies of this exact nine-worker block per learner pair; not a measured four-cycle run or a prediction for a different curriculum/model.',
                limitations=['Three measured paired learners on node2 A40; different admitted doses.',
                             'Timing spans are wrapper/per-request receipts, not GPU-active time or peak-memory measurements.',
                             'Fit elapsed includes native model loading inside fit; generation excludes serving startup.',
                             'Other controller time includes checks, startup, teardown and gaps; do not label it all cold-start overhead.',
                             'Preparation and prelaunch queue time excluded; no ideal fleet-wide scaling assumption.',
                             'No adaptation/retention/parenting success inferred from throughput.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    options = parser.parse_args()
    result = profile()
    with Path(options.out).open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(result, indent=2))
