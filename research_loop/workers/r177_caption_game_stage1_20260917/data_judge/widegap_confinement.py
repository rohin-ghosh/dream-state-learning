"""Versioned six-hour experiment wall; original strict device policy unchanged."""

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import physical2_confinement as original


DEVICE = original.DEVICE
MODULE = original.MODULE
verify = original.verify


def command(root, inventory_sha256, mode, max_seconds):
    data.require(type(max_seconds) is int and max_seconds == 20400, 'exact_frozen_widegap_runtime')
    arguments = original.command(root, inventory_sha256, mode, 7200)
    if mode == 'train':
        index = arguments.index('--property=RuntimeMaxSec=7200')
        arguments[index] = '--property=RuntimeMaxSec=20400'
    return arguments
