"""Bounded, score-blind follow-on cohorts; first live snapshot stays untouched."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from gpu.orch_l2_shared_run import write
from organism_v6.orch_guided_bridge import file_sha256
from organism_v6 import orch_route_parent_campaign as policy


FIRST = '/tmp/orch_route_parent_campaign_20260915_attempt1'


def configurations(qualifications=None):
    configs = [dict(segment=index, root=f'/tmp/orch_route_parent_campaign_20260915_segment{index}',
        initial_state=policy.INITIAL_STATE, presentations=16,
        cell=dict(style=style, horizon=horizon, tone=tone, provider='existing_claude_cli'))
        for index, (style, horizon, tone) in enumerate((
            ('micromanaging', 'short', 'harsh-critical'),
            ('creative', 'long', 'supportive-positive'),
            ('training-wheels', 'long', 'harsh-critical')), 2)]
    if qualifications is not None:
        for config, model in zip(configs[1:], ('claude-haiku-4-5-20251001', 'openai/openai/gpt-6-astra')):
            receipt = qualifications[model]
            policy.require(receipt.get('verified') is True and receipt.get('actual_primary_model') == model
                and receipt.get('scope') == 'TRAIN_ONLY_READINESS_NOT_HELD'
                and bool(receipt.get('usage')) and bool(receipt.get('envelope_sha256')),
                'qualified_primary_receipt_required')
            config['cell']['provider'] = model
    return configs


def remote(host, command, timeout=60):
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', host, command], text=True, timeout=timeout)


def initialize(config_path, archive, previous):
    config = json.loads(Path(config_path).read_text())
    policy.activate(config)
    root = Path(policy.ROOT)
    policy.require(not root.exists(), 'fresh_segment_only')
    prior = Path(previous)
    terminal_path = prior / ('TERMINAL_REPAIR.json' if (prior / 'REPAIR_ACTIVE.json').exists() else 'TERMINAL.json')
    terminal = json.loads(terminal_path.read_text())
    policy.require(terminal['exit_codes'] == [0, 0, 0], 'all_three_predecessor_lanes_completed')
    first = Path(FIRST)
    root.mkdir()
    (root / 'source').mkdir()
    (root / 'parent_queue').mkdir()
    shutil.copyfile(config_path, root / 'CONFIG.json')
    subprocess.run(['tar', '-xf', archive, '-C', str(root / 'source')], check=True)
    shutil.copytree(first / 'initial_adapter', root / 'initial_adapter')
    for name in ('initial_source_receipt.json', 'LEGACY_MATERIAL.json', 'OLD_MASKS.json',
                 'LEGACY_READOUT.json', 'SERVICE_IDENTITY.json', 'PROVIDER.json', 'RELEASE.json'):
        shutil.copyfile(first / name, root / name)
    write(root / 'PREVIOUS_SEGMENT.json', dict(root=str(prior), terminal_sha256=file_sha256(terminal_path),
        input_policy='NEW_MATCHED_SIBLING_FROM_FIXED_LANE0_NOT_PREVIOUS_HELD_SCORE',
        previous_lineages_preserved=True, config=config))


def serve(host, local, deadline, qualifications_path=None):
    local.mkdir(parents=True, exist_ok=False)
    archive = local.parent / 'source_continuation.tar'
    policy.require(archive.is_file(), 'tested_frozen_continuation_source_required')
    tests = local.parent / 'CPU_CONTINUATION.txt'
    policy.require(tests.is_file() and tests.read_text().rstrip().endswith('OK'), 'own_tests_required')
    qualifications = json.loads(Path(qualifications_path).read_text()) if qualifications_path else None
    configs = configurations(qualifications)
    runtime = local / 'source_runtime'
    runtime.mkdir()
    subprocess.run(['tar', '-xf', str(archive.resolve()), '-C', str(runtime)], check=True)
    write(local / 'QUEUE.json', dict(configs=configs, deadline_unix=deadline,
        maximum_new_segments=3, maximum_new_gpu_hours=36, maximum_new_child_calls=7968,
        maximum_new_parent_invocations=768, maximum_new_provider_components=1536,
        maximum_new_updates=3072, held_selection=False,
        combined_fit='QUEUED_SEPARATELY_PENDING_EXACT_PROVENANCE_NOT_HELD_SCORES',
        qualified_strengths=qualifications or {},
        provider_selection='PROSPECTIVE_FIXED_ORDER_NOT_HELD_OUTCOMES',
        maximum_strong_output_tokens=256 * 4096 if qualifications else 0,
        maximum_direct_strong_http_attempts=256 if qualifications else 0,
        cli_http_attempts='NOT_OBSERVABLE; max128invocations per parented lane per segment',
        source_sha256=file_sha256(archive), cpu_sha256=file_sha256(tests)))
    remote_archive = '/tmp/orch_route_parent_campaign_20260915_continuation_source.tar'
    subprocess.run(['scp', '-q', str(archive), host + ':' + remote_archive], check=True)
    previous = FIRST
    for config in configs:
        segment = local / f'segment{config["segment"]}'
        segment.mkdir()
        config_path = segment / 'CONFIG.json'
        write(config_path, config)
        while True:
            policy.require(time.time() < deadline - 14700, 'bounded_campaign_no_new_four_hour_segment')
            status = remote(host, f'if test -f {previous}/REPAIR_ACTIVE.json; then '
                f'test ! -f {previous}/TERMINAL_REPAIR.json || cat {previous}/TERMINAL_REPAIR.json; '
                f'else test ! -f {previous}/TERMINAL.json || cat {previous}/TERMINAL.json; fi')
            if status.strip():
                policy.require(json.loads(status)['exit_codes'] == [0, 0, 0], 'predecessor_failure_requires_repair')
                break
            write(local / 'STATUS.json', dict(state='PREDECESSOR_RUNNING_NOT_IDLE_HOLD', previous=previous,
                  next_segment=config['segment'], time_unix=time.time()))
            time.sleep(15)
        root = config['root']
        checkpoint = segment / 'PREVIOUS_TERMINAL.tar.gz'
        with checkpoint.open('xb') as stream:
            subprocess.run(['ssh', '-o', 'BatchMode=yes', host,
                f'tar -C {previous} --exclude=source --exclude=initial_adapter --exclude=child '
                '--exclude="*.tar" --exclude="*.tar.gz" -czf - .'], stdout=stream, check=True, timeout=180)
        write(segment / 'PREVIOUS_ARCHIVE.json', dict(root=previous, archive_sha256=file_sha256(checkpoint),
              held_scores_inspected=False, all_runtime_transcripts_preserved=True,
              unchanged_initial_and_code_archives_preserved_separately=True))
        remote_config = '/tmp/orch_route_parent_campaign_20260915_config' + str(config['segment']) + '.json'
        subprocess.run(['scp', '-q', str(config_path), host + ':' + remote_config], check=True)
        bootstrap = '/tmp/orch_route_parent_campaign_20260915_queue_bootstrap'
        remote(host, f'mkdir -p {bootstrap}; tar -xf {remote_archive} -C {bootstrap}')
        remote(host, f'env PYTHONPATH={bootstrap} python3 -B -m gpu.orch_route_parent_campaign_queue '
            f'--initialize {remote_config} --archive {remote_archive} --previous {previous}')
        if config['cell']['provider'] != 'existing_claude_cli':
            provider_path = segment / 'PROVIDER.json'
            write(provider_path, qualifications[config['cell']['provider']])
            subprocess.run(['scp', '-q', str(provider_path), host + ':' + root + '/PROVIDER.json'], check=True)
        environment = (f'env CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 '
                       f'PYTHONPATH={root}/source ROUTE_PARENT_CONFIG={root}/CONFIG.json ')
        native = environment + '/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_route_parent_campaign_run'
        log = remote(host, native + ' --phase prepare', timeout=180)
        (segment / 'NATIVE_CPU.log').write_text(log)
        prepared_bytes = remote(host, f'cat {root}/PREPARE.json')
        (segment / 'PREPARE.json').write_text(prepared_bytes)
        prepared = json.loads(prepared_bytes)
        policy.require(prepared['verified_base']['verified'] and prepared['cpu_legacy_rows'] == 222,
                       'native_provenance_gate')
        receipt = (f'[Builder — ROUTE_PARENT_CAMPAIGN] {datetime.now(timezone.utc).isoformat()} '
            f'OWN preGPU PASS segment{config["segment"]}: frozen tested source {file_sha256(archive)}, '
            f'CPU {file_sha256(tests)}, nativeCPU base/tokenizer/222legacy/provenance PASS; '
            f'PREPARE {file_sha256(segment / "PREPARE.json")}; held prospectively frozen '
            f'{prepared["cohort_sha256"]}; fixed d13 route child, matched same-child twins, '
            f'cell={config["cell"]},16presentations,2cycles/max256updates per sleep, '
            f'4h/12GPUh/2656childcalls/256parentinvocations max512components. '
            'Previous segment completed; next launch requires fresh privileged0/1/2admission, '
            'lease minus6h; no Mainack, no held-based branch, all transcripts preserved.')
        for path in ('research_loop/COORDINATION.md', 'research_loop/workers/ROUTE_PARENT_CAMPAIGN.md'):
            with Path(path).open('a') as stream:
                stream.write('\n' + receipt + '\n')
        publication = segment / 'PUBLICATION.json'
        write(publication, dict(own_cpu_tests_passed=True, dated_builder_receipt=receipt,
            prepare_sha256=file_sha256(segment / 'PREPARE.json')))
        subprocess.run(['scp', '-q', str(publication), host + ':' + root + '/PUBLICATION.json'], check=True)
        with (segment / 'PARENT_BROKER.log').open('x') as broker_log:
            broker = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_route_parent_campaign_parent',
                '--host', host, '--local-root', str((segment / 'parent').resolve()), '--config', str(config_path),
                '--deadline', str(min(deadline, time.time() + 14500))], stdout=broker_log,
                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True,
                cwd=runtime.resolve(), env=dict(os.environ, PYTHONPATH=str(runtime.resolve())))
        launch = remote(host, f'nohup {native} --phase launch > {root}/CAMPAIGN_GUARDIAN.log 2>&1 < /dev/null & echo $!')
        write(segment / 'LAUNCH.json', dict(remote_guardian_pid=int(launch.strip()), broker_pid=broker.pid,
            started_unix=time.time(), root=root))
        previous = root
    write(local / 'DISPATCH_COMPLETE.json', dict(last=root, time_unix=time.time(),
        last_segment_still_guarded=True, research_claims='NO_OUTCOME_CLAIM_FROM_LAUNCH'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host')
    parser.add_argument('--local-root')
    parser.add_argument('--deadline', type=float)
    parser.add_argument('--initialize')
    parser.add_argument('--archive')
    parser.add_argument('--previous')
    parser.add_argument('--qualifications')
    args = parser.parse_args()
    if args.initialize:
        initialize(args.initialize, args.archive, args.previous)
    else:
        try:
            serve(args.host, Path(args.local_root).resolve(), args.deadline, args.qualifications)
        except BaseException as error:
            write(Path(args.local_root) / 'FAILED.json', dict(error=str(error), time_unix=time.time()))
            raise


if __name__ == '__main__':
    main()
