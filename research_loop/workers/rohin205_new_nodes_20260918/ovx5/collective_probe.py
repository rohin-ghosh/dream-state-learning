"""Finite engineering collective only; no candidate model or dataset access."""

import datetime
import json
import os
import torch
import torch.distributed as distributed

rank = int(os.environ['LOCAL_RANK'])
torch.cuda.set_device(rank)
distributed.init_process_group('nccl', timeout=datetime.timedelta(seconds=45), device_id=torch.device('cuda', rank))
value = torch.tensor(float(rank + 1), device='cuda:' + str(rank))
distributed.all_reduce(value)
assert value.item() == 10.0
if rank == 0:
    print(json.dumps(dict(status='ACTUAL_FOUR_RANK_COLLECTIVE_PASS', world_size=4, candidate_optimizer_updates=0)), flush=True)
distributed.destroy_process_group()
