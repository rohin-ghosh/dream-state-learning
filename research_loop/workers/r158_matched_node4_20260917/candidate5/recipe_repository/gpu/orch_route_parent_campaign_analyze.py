"""Reduce a captured cohort without exposing held evidence to parents."""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from gpu.orch_l2_shared_run import write
from organism_v6.orch_route_parent_campaign_analysis import reduce


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = reduce(args.root)
    result['reduced_utc'] = datetime.now(timezone.utc).isoformat()
    write(Path(args.output), result)


if __name__ == '__main__':
    main()
