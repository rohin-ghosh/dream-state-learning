"""Prepare two isolated R209 candidates from the retained private received packet."""

import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from ddp_pilot import require, sha, write
from expand_rank import main as expand_rank


SOURCE = Path('/localhome/local-rohing/orch_r207_ovx5_widegap1m_20260918_candidate1')
STAGE = Path(__file__).resolve().parent


def main():
    os.umask(0o077)
    require(os.uname().nodename == '[REDACTED_HOST]', 'exact_games_host')
    packet = json.loads((SOURCE / 'PACKET.json').read_bytes())
    require(sha(SOURCE / 'PACKET.json') == '43d90b0530324b554d216c648d93e677aa02eaf4e19b9bcda815c9b4a06a5d91', 'frozen_source_packet')
    old = json.loads((SOURCE / 'preload_collective_attempt1/PILOT_CONFIG.json').read_bytes())
    devices = {}
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        devices[int(fields['Device Minor'])] = (fields['GPU UUID'].strip(), path.parent.name)
    selection = STAGE / 'SELECTION_ROWS.private.jsonl'
    require(selection.is_file() and selection.stat().st_size > 0, 'nonempty_declared_selection_packet')
    hard_end = datetime.datetime(2026, 9, 18, 23, tzinfo=datetime.timezone.utc).timestamp()
    for rank, physical in [(8, [0, 1, 2, 3]), (16, [4, 5, 6, 7])]:
        root = Path(f'/localhome/local-rohing/orch_r209_ovx5_allpair1m_rank{rank}_20260918_candidate1')
        root.mkdir(mode=0o700)
        for relative, reference in packet['files'].items():
            origin = SOURCE / relative
            require(sha(origin) == reference['sha256'], 'frozen_packet_file')
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(origin, target)
        for name in ['PACKET.json', 'BASE_MANIFEST.source.json']:
            shutil.copy2(SOURCE / name, root / name)
        for name in ['ddp_pilot.py', 'four_gpu_admission.py', 'test_ddp_pilot.py', 'expand_rank.py']:
            shutil.copy2(STAGE / name, root / name)
        os.link(selection, root / selection.name)
        if rank == 8:
            shutil.copytree(root / 'warmstart6250', root / 'warmstart')
        else:
            expand_rank(root / 'warmstart6250', root / 'warmstart')
        pinned = ['PACKET.json', 'BASE_MANIFEST.source.json', 'ddp_pilot.py', 'four_gpu_admission.py',
            selection.name, 'warmstart/adapter_config.json', 'warmstart/adapter_model.safetensors']
        config = dict(old, schema='R209_ALLPAIR_FOUR_GPU_CANDIDATE_V1', physical=physical,
            device_uuids=[devices[minor][0] for minor in physical], pci=[devices[minor][1] for minor in physical],
            lora_rank=rank, lora_alpha=rank * 2, pilot_end_unix=time.time() + 3600,
            training_end_unix=hard_end, runtime_max_seconds=int(hard_end - time.time()),
            unit_prefix=f'orch-r209-ovx5-allpair-rank{rank}-candidate1-',
            source_pin={name: sha(root / name) for name in pinned},
            candidate_count_in_registered_experiment=2, global_batch=64, local_batch=16,
            gradient_accumulation=1, comparisons=1000000, optimizer_updates=15625,
            sampling='balanced180contests_uniform_distinct_rows_with_replacement_across_draws',
            tie_target=0.5, weighting='capped_min_vote_reliability_no_gap_weight',
            selection='max_macro_within_contest_Spearman_against_mean_rating_earliest_tie',
            selection_steps=[8, 3907, 7813, 11719, 15625], selection_rows_per_contest=256,
            fresh_optimizer_at_candidate_birth=True, warmstart_step=6250,
            rank_expansion='none' if rank == 8 else 'A_original_prefix_plus_seed209_Kaiming_B_original_prefix_plus_zero_alpha_over_rank2',
            prelaunch_eta=dict(single_GPU_historical_pairs_per_second=8.423,
                ideal_four_GPU_fitting_hours=1000000 / (8.423 * 4) / 3600,
                measured_four_GPU_rate=False, selection_seconds=None,
                caveat='rank16_and_shared_host_cost_unmeasured_actual_300s_pilot_updates_ETA'))
        write(root / 'PILOT_CONFIG.json', config)
        result = subprocess.run([sys.executable, '-B', str(root / 'test_ddp_pilot.py')], cwd=root, check=False, capture_output=True, text=True)
        require(result.returncode == 0, 'receiving_focused_CPU_tests')
        write(root / 'RECEIVING_CPU.json', dict(passed=True, six_focused_tests=True,
            observed_unix=time.time(), config_sha256=sha(root / 'PILOT_CONFIG.json'),
            source_pin=config['source_pin'], model_manifest_previously_verified=True,
            private_selection_bytes=selection.stat().st_size, no_GPU_initialized=True))
        print(json.dumps(dict(root=str(root), status='CPU_READY_NOT_DISPATCHED', rank=rank,
            physical=physical, config_sha256=sha(root / 'PILOT_CONFIG.json'), prelaunch_eta=config['prelaunch_eta'])), flush=True)


if __name__ == '__main__':
    main()
