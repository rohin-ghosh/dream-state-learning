"""Read-only admission checks for a future external supervisor, never a launcher."""

import math
import time
from uuid import UUID

from gpu import ny_caption_generation_profile as profile
from gpu import orch_r153_community_runtime as containment
from research_loop.workers.rohin172_c2_pilot_20260917.continuation import custody


require = custody.require


def validate_pair(assignments, *, now, pins):
    custody.verify_pins(pins)
    require(type(now) in (int, float) and math.isfinite(now), 'finite_admission_time')
    require(set(assignments) == set(custody.ARMS), 'both_matched_arms_required')
    require({item['physical'] for item in assignments.values()} == {6, 7}, 'only_physical6_and7')
    require(len({item['minor'] for item in assignments.values()}) == 2
            and len({item['gpu_uuid'] for item in assignments.values()}) == 2, 'disjoint_UUID_minor_slots')
    for arm, item in assignments.items():
        require(item['host_sha256'] == profile.HOST_SHA256 and item['node'] == 'node4', 'exact_node4')
        require(type(item['minor']) is int and 0 <= item['minor'] < 8
                and item['capacity_physical'] == item['physical'], 'actual_physical_and_minor_mapping')
        require(item['wrapper'] == 'gpu/a40r_ssh.sh', 'wrapper_only_no_raw_ssh')
        require(item['lease_sha256'] == profile.LEASE_SHA256 and item['lease_extended'] is False
                and now < item['hard_end_unix'] <= min(now + 14400, profile.HARD_END,
                    item['lease_end_unix'] - 300), 'unchanged_lease_and_four_hour_ceiling')
        require(0 <= now - item['observed_unix'] <= 30, 'fresh_admission_not_historical_profiler_release')
        require(item['fd_scan_privileged'] is True and item['fd_scan_unreadable'] == []
                and item['fd_owners'] == [] and item['compute_pids'] == []
                and item['memory_used_mib'] == 0 and item['utilization_percent'] == 0,
                'fresh_empty_capacity_and_complete_privileged_FD_scan')
        require(item['policy'] == 'strict' and item['nonroot_uid'] > 0
                and item['denied_foreign_minors'] == sorted(set(range(8)) - {item['minor']})
                and item['inherited_gpu_fds'] == [] and item['allowed_device_open_succeeded'] is True,
                'actual_strict_device_opens_not_CVD_only')
        raw = item['cuda_uuid_bytes']
        require(type(raw) is list and len(raw) == 16
                and all(type(value) is int and 0 <= value <= 255 for value in raw), 'exact16_byte_CUDA_UUID')
        require('GPU-' + str(UUID(bytes=bytes(raw))) == item['gpu_uuid']
                == item['kernel_uuid'] == item['capacity_uuid']
                and item['kernel_minor'] == item['minor'], 'actual_UUID_kernel_minor_capacity_join')
        if item['physical'] == 6:
            require(item['gpu_uuid'] == profile.GPU_UUID, 'known_physical6_UUID_not_minor6_assumption')
    return dict(status='RECEIPT_VALIDATION_ONLY_NOT_LAUNCH_AUTHORITY', arm_count=2,
                source_pins_sha256=custody.digest(pins), checked_unix=now)


def fresh_privileged_fd_scan(minor):
    require(type(minor) is int and 0 <= minor < 8, 'actual_minor_required')
    return profile.scan_owners(minor)


def check_current_containment(config, plan):
    require(plan['physical'] in (6, 7), 'assigned_C2_physical_only')
    result = containment.verify_containment(config, plan)
    require(profile.command(['systemctl', 'show', config['device_containment']['unit'],
                             '--property=DevicePolicy', '--value']) == 'strict', 'actual_strict_systemd_policy')
    return dict(result, checked_unix=time.time(), GPU_model_loaded=False)
