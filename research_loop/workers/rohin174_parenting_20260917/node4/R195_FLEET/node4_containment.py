"""Bind the existing strict R188 containment to the seven assigned node4 UUIDs."""

import argparse
from pathlib import Path

from gpu import orch_r188_node4_rehome_containment as original


original.DEVICES = {
    0: 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d',
    1: 'GPU-4b071167-a06a-773c-f947-60cb8c2f7512',
    2: 'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8',
    3: 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14',
    5: 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30',
    6: 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397',
    7: 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'}
existing_command = original.device_containment_command


def command(*arguments):
    result = existing_command(*arguments)
    return ['gpu.r203_node4_containment' if item == 'gpu.orch_r188_node4_rehome_containment'
            else item for item in result]


original.device_containment_command = command


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('contained-supervise', 'contained-native'))
    parser.add_argument('--config', type=Path, required=True)
    options = parser.parse_args()
    {'contained-supervise': original.contained_supervise,
     'contained-native': original.contained_native}[options.action](options.config)
