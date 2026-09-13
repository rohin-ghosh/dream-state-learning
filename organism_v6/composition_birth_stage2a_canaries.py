"""Source-only strict-copy canaries over explicit identifiers, not composition."""

from collections.abc import Mapping
from dataclasses import dataclass
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))


@dataclass(frozen=True)
class Canary:
    index: int
    user_text: str
    target: str
    system_text: str = wire.SYSTEM_MESSAGE


def _kind(index):
    if index < 2:
        return "node"
    if index < 4:
        return "query"
    if index < 8:
        return "port"
    return "event"


def canary_roles():
    return tuple(f"generic_canary/c{index:02d}/canary/-/target/-/{_kind(index)}"
                 for index in range(12))


def build_canaries(*, role_tokens):
    if not isinstance(role_tokens, Mapping):
        raise ValueError("explicit_role_tokens_required")
    roles = canary_roles()
    tokens = dict(role_tokens)
    if set(tokens) != set(roles):
        raise ValueError("canary_role_roster_mismatch")
    seen = set()
    for index, role in enumerate(roles):
        token = tokens[role]
        if (type(token) is not str or re.fullmatch(wire.IDENTIFIERS[_kind(index)], token) is None
                or token.endswith("_AAAAAAAAAAAA") or token in seen):
            raise ValueError("invalid_or_duplicate_canary_token")
        seen.add(token)
    result = []
    for index in range(16):
        if index < 2:
            target = "READ INDEX " + tokens[roles[index]]
        elif index < 4:
            target = "READ RELATION " + tokens[roles[index]]
        elif index < 8:
            target = "STEP " + tokens[roles[index]]
        elif index < 10:
            target = "THINK KEEP " + tokens[roles[index]]
        elif index < 12:
            target = "THINK REVISE " + tokens[roles[index]]
        else:
            target = "STOP"
        wire.parse_action(target)
        result.append(Canary(index, "CANARY\nCOPY EXACTLY\n" + target, target))
    return tuple(result)


def exact_copy_match(canary, raw_output):
    """Score raw text only; transport/termination qualification is external."""
    if type(canary) is not Canary:
        raise ValueError("canary_required")
    try:
        wire.parse_action(raw_output)
    except ValueError:
        return False
    return raw_output == canary.target
