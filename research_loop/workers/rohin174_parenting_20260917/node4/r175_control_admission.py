"""Fail-closed V2 exclusion, not a grant of authority to parent other targets."""

import hashlib
import json
from pathlib import Path
import posixpath
import re


HOME = Path(__file__).resolve().parent
V2_PATH = HOME.parent / 'ASSIGNMENTS_CONTROL_AMENDMENT_V2.json'
V2_SHA = 'be536327a062b1e104f76e3adfae4b6957e71dc932bce1768b21677348acbf6f'
V1_SHA = '25b45432bebb388e920d5cc8dc8fed6c705cd54156cbfd530828e1520a9174b2'
CONTROL_ROOT = '/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1'
REFUSAL = 'V2_EXCLUDED_ORIGINAL_RAW_CONTROL_NO_PARENTING_OR_REPUBLISH'


def read(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1048576:
        raise ValueError('V2_bounded_regular_admission_metadata')
    return json.loads(path.read_bytes())


def authority():
    document = read(V2_PATH)
    if hashlib.sha256(V2_PATH.read_bytes()).hexdigest() != V2_SHA:
        raise ValueError('V2_exact_amendment_required_no_V1_fallback')
    overrides = document.get('overrides')
    if document.get('base_assignment_sha256') != V1_SHA or not isinstance(overrides, list) or len(overrides) != 1:
        raise ValueError('V2_exact_control_exclusion_required')
    control = overrides[0]
    if not (control.get('node') == 'a40r' and control.get('gpu') == 1
            and control.get('arm') == 'UNPARENTED_CONTROL_EXCLUDED'
            and control.get('parenting_authorized') is False and control.get('revoke_arm') == 'H'):
        raise ValueError('V2_control_exclusion_must_not_be_weakened')
    return dict(amendment_sha256=V2_SHA, excluded_root=CONTROL_ROOT,
        excluded_physical=1, other_authorization_and_provenance_gates_still_required=True)


def target(physical=None, root=None):
    receipt = authority()
    if physical is not None and type(physical) is not int:
        raise ValueError('V2_integer_physical_required')
    if physical == 1:
        raise ValueError(REFUSAL)
    if root is not None:
        if not isinstance(root, str) or not root.startswith('/') or len(root) > 4096 or any(char in root for char in ('\0', '\n', '\r')):
            raise ValueError('V2_absolute_target_root_required')
        normalized = posixpath.normpath('/' + root.lstrip('/'))
        if normalized == CONTROL_ROOT or normalized.startswith(CONTROL_ROOT + '/'):
            raise ValueError(REFUSAL)
    if physical is None and root is None:
        raise ValueError('V2_known_parenting_target_required')
    return receipt


def lane(path):
    path = Path(path)
    match = re.fullmatch(r'(?:physical|lane)([0-7])', path.name)
    identified = False
    if match:
        target(physical=int(match.group(1)))
        identified = True
    for name in ('PLAN.json', 'CONFIG.json', 'INPUTS.json'):
        candidate = path / name
        if candidate.exists():
            document = read(candidate)
            target(document.get('physical'), document.get('root'))
            identified = True
    if not identified:
        raise ValueError('V2_no_identified_parenting_target')
    return authority()
