"""Per-receiver paths for the unchanged node4 observation and withdrawal helpers."""

import hashlib
import json
import os
from pathlib import Path
import socket
import time


HOME = Path(__file__).resolve().parent
SOURCE = HOME / 'source'
PYTHON = Path('/localhome/local-rohing/v2/venv/bin/python')
WALL = 1789754400


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def host():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() ==
        'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b', 'exact_node4')
    require(os.getuid() == 2524 and time.time() < WALL, 'same_owner_and_wall')
