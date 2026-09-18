"""A separate process and journal for the separately registered publisher."""

import argparse
from pathlib import Path

from gpu.orch_combined_l1_native_feed_watch import main


SOURCE = '/localhome/local-rohing/orch_combined_l1_exhaustion_receiver_20260915_segment1'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    main(args.repository, args.output, args.once,
         exporter=f'CUDA_VISIBLE_DEVICES= PYTHONPATH={SOURCE} python3 -B -m gpu.orch_combined_l1_exhaustion_feed',
         validation=SOURCE, receiver_module='gpu.orch_combined_l1_exhaustion_node')
