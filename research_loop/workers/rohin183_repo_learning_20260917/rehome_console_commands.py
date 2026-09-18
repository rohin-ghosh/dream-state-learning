"""Generate only: read-only follow and explicitly Rohin-attributed publication."""

from pathlib import Path
import shlex


BASE = Path('/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
PUBLISH_SOURCE_SHA = 'be7cfab563dcfe31590329e930b73238e26d39c7b03eb16c1859cc3e91f0b683'
FOLLOW_SOURCE_SHA = '35697239e89a6b9dd49505b3556eb2c149b214fdb5ad3116677712d9b4231b75'


def commands(original, ready, text='YOUR MESSAGE'):
    if type(original) is not int or original not in (1, 4, 7):
        raise ValueError('only_assigned_receivers')
    root = BASE / ('receiving' + str(original)) / 'root'
    source = BASE / ('receiving' + str(original)) / 'preserved' / ('physical' + str(original)) / 'source'
    if ready['raw_root'] != str(root) or ready['source_root'] != str(source):
        raise ValueError('actual_physical_receiving_root_and_source_required')
    pins = ready['source_pins']
    if pins.get('gpu/orch_r127_pilot_console.py') != PUBLISH_SOURCE_SHA or \
            pins.get('gpu/orch_r125_stream_console.py') != FOLLOW_SOURCE_SHA:
        raise ValueError('help_verified_frozen_console_sources_required')
    if type(text) is not str:
        raise ValueError('explicit_message_text_required')
    prefix = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(source), PYTHON, '-B', '-m']
    follow = prefix + ['gpu.orch_r125_stream_console', '--root', str(root), '--follow']
    publish = prefix + ['gpu.orch_r127_pilot_console', 'parent', '--root', str(root), '--speaker', 'Rohin', '--text', text]
    wrap = lambda argv: shlex.join(['bash', 'gpu/ovx_ssh.sh', shlex.join(argv)])
    return dict(follow_command=wrap(follow), rohin_publish_command=wrap(publish),
        publish_speaker='Rohin', publish_for_actual_Rohin_messages_only=True,
        default_stdin_publication_prohibited=True, command_execution=False)
