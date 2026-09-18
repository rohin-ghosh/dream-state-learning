"""Explicit R210 continuation; earlier screen records remain immutable."""

import argparse
import r209_filter_resume as repair


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'apply'))
    parser.add_argument('arm', choices=('conversational', 'peer_math', 'peer_repo', 'p32', 'lr03', 'lr3'))
    arguments = parser.parse_args()
    repair.PHASE = 'r210_enrichment'
    repair.ENRICH = True
    globals_function = getattr(repair, arguments.mode)
    globals_function(arguments.arm)
