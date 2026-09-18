"""Fresh kernel0 preparation after an unconsumed exact-source seam mismatch."""

import argparse
import hashlib
from pathlib import Path


HOME = Path(__file__).resolve().parent
ORIGINAL_SHA = 'fed364d875736d2d2e690eb70729124c3c8a096d9ab4e2bb7cb30b79fcf90ae2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'launch'))
    arguments = parser.parse_args()
    source = (HOME / 'r188_recover_node4.py').read_text()
    if hashlib.sha256(source.encode()).hexdigest() != ORIGINAL_SHA:
        raise ValueError('exact_original_recovery_operator')
    before = "output = ROOT / f'recovery{physical}'"
    if source.count(before) != 2:
        raise ValueError('exact_two_output_paths')
    source = source.replace(before, "output = ROOT / f'recovery{physical}_attempt2'")
    namespace = dict(__file__=str(Path(__file__).resolve()), __name__='r188_kernel0_attempt2')
    exec(compile(source, str(HOME / 'r188_recover_node4.py'), 'exec'), namespace)
    namespace[arguments.action](0)


if __name__ == '__main__':
    main()
