"""Bounded filesystem metadata and growth samples; no reserve or source changes."""

import json
from pathlib import Path
import subprocess

from verify_completed_canary import HERE, frozen


PROGRAM = '''
import json,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
root='/localhome/local-rohing'
def sample():
    value=os.statvfs(root)
    return dict(utc=datetime.now(timezone.utc).isoformat(),monotonic=time.monotonic(),
        blocks=value.f_blocks,bfree=value.f_bfree,bavail=value.f_bavail,frsize=value.f_frsize,
        owner_available_bytes=value.f_bavail*value.f_frsize,
        free_bytes_including_reserved=value.f_bfree*value.f_frsize,
        bfree_minus_bavail_bytes=(value.f_bfree-value.f_bavail)*value.f_frsize,
        free_inodes=value.f_ffree,owner_available_inodes=value.f_favail)
first=sample()
mount=subprocess.run(['findmnt','-J','-T',root,'-o','SOURCE,FSTYPE,TARGET'],capture_output=True,text=True,timeout=10)
mount_info=json.loads(mount.stdout)['filesystems'][0] if mount.returncode==0 else dict(error='findmnt_failed')
reserve=dict(status='UNKNOWN')
device=mount_info.get('source','')
if mount_info.get('fstype') in ('ext4','ext3','ext2') and device.startswith('/dev/'):
    result=subprocess.run(['sudo','-n','tune2fs','-l',device],capture_output=True,text=True,timeout=15)
    if result.returncode==0:
        fields=dict(line.split(':',1) for line in result.stdout.splitlines() if ':' in line)
        chosen={key:int(fields[key].strip()) for key in ['Block count','Reserved block count','Block size']}
        reserve=dict(status='READ_ONLY_SUPERBLOCK_RESERVE_REPORTED',fields=chosen,
            reserved_bytes=chosen['Reserved block count']*chosen['Block size'])
    else:
        reserve=dict(status='READ_ONLY_SUPERBLOCK_QUERY_FAILED',returncode=result.returncode)
time.sleep(5)
second=sample()
elapsed=second['monotonic']-first['monotonic']
consumed=first['free_bytes_including_reserved']-second['free_bytes_including_reserved']
report=dict(utc=second['utc'],host=os.uname().nodename,uid=os.getuid(),mount=mount_info,reserve=reserve,
    samples=[first,second],sample_seconds=elapsed,net_bytes_consumed=consumed,
    net_consumption_bytes_per_second=consumed/elapsed,
    growth_is_short_window_net_filesystem_change_not_attributed_to_a_process=True,
    bfree_minus_bavail_is_not_total_reserve_deficit_when_bavail_zero=True,
    no_reserved_block_use=True,no_changes=True)
if reserve['status']=='READ_ONLY_SUPERBLOCK_RESERVE_REPORTED':
    deficit=max(0,reserve['reserved_bytes']-second['free_bytes_including_reserved'])
    report.update(superblock_reserved_threshold_bytes=reserve['reserved_bytes'],
        superblock_reserve_deficit_bytes=deficit,
        remaining_selected_allocated_relief_bytes=1831120896,
        optimistic_owner_bytes_after_remaining=max(0,1831120896-deficit)+second['owner_available_bytes'],
        c0_required_bytes=2981136864,
        optimistic_c0_shortfall_after_remaining=max(0,2981136864-(max(0,1831120896-deficit)+second['owner_available_bytes'])),
        estimate_excludes_additional_allocator_reserves_quotas_and_future_writes=True)
print(json.dumps(report,sort_keys=True))
'''


def main():
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    result = subprocess.run(['bash', str(repo / 'gpu/ovx_ssh.sh'), frozen.encoded_command(PROGRAM)],
                            check=True, capture_output=True, text=True, timeout=50)
    print(json.dumps(json.loads(result.stdout), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
