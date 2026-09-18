"""Use the tested no-signal parent publisher for distinct new C2 forks."""

import argparse

import r213_parent as publisher
from r213_fork_policy import ASSIGNMENTS, FORKS, prompt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('arm', choices=FORKS)
    publisher.ASSIGNMENTS = ASSIGNMENTS
    publisher.prompt = prompt
    publisher.main(parser.parse_args().arm)
