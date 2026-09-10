"""Prompt and parse boundary for recurrent one-edge micro-dreams.

This module contains no world scorer and no hidden-state access.  It only
renders temporally available public material and parses one strict operation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Literal


TriggerKind = Literal["wake", "reactivate"]
OperationKind = Literal["add", "revise", "open_question", "pass"]

CLAIM_KINDS = frozenset({
    "witnessed",
    "similarity",
    "difference",
    "role",
    "operator",
    "causal",
    "exception",
    "abstraction",
})

_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")
_FIELD = re.compile(r"([A-Z_]+)=([^|\r\n]+)")
_ATOM = re.compile(r"[A-Za-z0-9_.:-]+")
_RELATION = re.compile(r"[A-Za-z0-9_.:-]+(?: [A-Za-z0-9_.:-]+){0,5}")
_LIST_SYNTAX = re.compile(
    r"[,;/\\&+]|\b(?:and|or|plus|along with|together with)\b", re.I
)


@dataclass(frozen=True)
class ParsedMicrodream:
    operation: OperationKind
    claim_kind: str | None = None
    left: str | None = None
    relation: str | None = None
    right: str | None = None
    claim: str | None = None
    cites: tuple[str, ...] = ()
    prediction: str | None = None
    confidence: float | None = None
    supersedes: tuple[str, ...] = ()
    question: str | None = None


def canonical_question(parsed: ParsedMicrodream) -> str | None:
    """Render the sole durable/agenda representation of a typed question."""
    if parsed.operation != "open_question":
        return None
    assert parsed.claim_kind is not None
    assert parsed.left is not None and parsed.relation is not None and parsed.right is not None
    values = (
        parsed.claim_kind.casefold(),
        " ".join(parsed.left.casefold().split()),
        " ".join(parsed.relation.casefold().split()),
        " ".join(parsed.right.casefold().split()),
    )
    return (
        f"OPEN_QUESTION | KIND={values[0]} | LEFT={values[1]} | "
        f"RELATION={values[2]} | RIGHT={values[3]} | CITES={','.join(parsed.cites)}"
    )


def canonical_edge(parsed: ParsedMicrodream) -> tuple[str, str, str, str] | None:
    """Return a normalized one-edge identity, or ``None`` for non-edge ops."""
    if parsed.operation not in {"add", "revise", "open_question"}:
        return None
    assert parsed.claim_kind is not None
    assert parsed.left is not None and parsed.relation is not None and parsed.right is not None
    return tuple(
        " ".join(value.casefold().split())
        for value in (parsed.claim_kind, parsed.left, parsed.relation, parsed.right)
    )  # type: ignore[return-value]


def local_edge_errors(parsed: ParsedMicrodream) -> tuple[str, ...]:
    """Enforce the syntax-level one-edge boundary without consulting truth.

    This deliberately does not decide whether an edge is correct. Held-out
    answer equivalence is audited only after the live memory commits.
    """
    if parsed.operation not in {"add", "revise", "open_question"}:
        return ()
    errors: list[str] = []
    values = {
        "left": parsed.left or "",
        "relation": parsed.relation or "",
        "right": parsed.right or "",
    }
    for name, value in values.items():
        grammar = _RELATION if name == "relation" else _ATOM
        if not grammar.fullmatch(" ".join(value.split())):
            errors.append(f"{name} is not one canonical atom/relation")
        if _LIST_SYNTAX.search(value):
            errors.append(f"{name} contains list/coordination syntax")
    normalized_left = " ".join((parsed.left or "").casefold().split())
    normalized_right = " ".join((parsed.right or "").casefold().split())
    if parsed.claim_kind in {"similarity", "difference", "role"}:
        if normalized_left == normalized_right:
            errors.append("self-edge is invalid for similarity/difference/role")
    return tuple(errors)


def _fields(raw: str, prefix: str) -> dict[str, str] | None:
    if "\n" in raw or "\r" in raw or not raw.startswith(prefix + " | "):
        return None
    pieces = raw.split(" | ")
    if pieces[0] != prefix:
        return None
    parsed: dict[str, str] = {}
    for piece in pieces[1:]:
        match = _FIELD.fullmatch(piece)
        if match is None or match.group(1) in parsed:
            return None
        parsed[match.group(1)] = match.group(2).strip()
    return parsed


def _ids(value: str) -> tuple[str, ...] | None:
    material = tuple(part.strip() for part in value.split(",") if part.strip())
    if not material or any(_ID.fullmatch(item) is None for item in material):
        return None
    if len(set(material)) != len(material):
        return None
    return material


def parse_microdream(raw_completion: str) -> ParsedMicrodream | None:
    """Parse exactly one complete micro-dream operation.

    Semantic locality, temporal citation validity, and per-life isolation are
    separate contract checks because they require the current public state.
    """
    raw = (raw_completion or "").strip()
    if raw == "PASS":
        return ParsedMicrodream(operation="pass")

    for prefix, operation in (("ADD", "add"), ("REVISE", "revise")):
        values = _fields(raw, prefix)
        if values is None:
            continue
        required = {
            "KIND", "LEFT", "RELATION", "RIGHT", "CLAIM", "CITES",
            "PREDICTION", "CONFIDENCE",
        }
        if operation == "revise":
            required.add("SUPERSEDES")
        if set(values) != required or values["KIND"].lower() not in CLAIM_KINDS:
            return None
        cites = _ids(values["CITES"])
        supersedes = (
            _ids(values["SUPERSEDES"]) if operation == "revise" else ()
        )
        try:
            confidence = float(values["CONFIDENCE"])
        except ValueError:
            return None
        if (cites is None or supersedes is None or not 0.0 <= confidence <= 1.0
                or any(not values[key] for key in (
                    "LEFT", "RELATION", "RIGHT", "CLAIM", "PREDICTION"
                ))):
            return None
        return ParsedMicrodream(
            operation=operation,  # type: ignore[arg-type]
            claim_kind=values["KIND"].lower(),
            left=values["LEFT"],
            relation=values["RELATION"],
            right=values["RIGHT"],
            claim=values["CLAIM"],
            cites=cites,
            prediction=values["PREDICTION"],
            confidence=confidence,
            supersedes=supersedes,
        )

    values = _fields(raw, "OPEN_QUESTION")
    if values is not None:
        if (set(values) != {"KIND", "LEFT", "RELATION", "RIGHT", "CITES"}
                or values["KIND"].lower() not in CLAIM_KINDS):
            return None
        cites = _ids(values["CITES"])
        if cites is None or any(not values[key] for key in ("LEFT", "RELATION", "RIGHT")):
            return None
        parsed = ParsedMicrodream(
            operation="open_question", claim_kind=values["KIND"].lower(),
            left=values["LEFT"], relation=values["RELATION"], right=values["RIGHT"],
            cites=cites,
        )
        return ParsedMicrodream(**{
            **parsed.__dict__, "question": canonical_question(parsed),
        })
    return None


def render_microdream_prompt(
    *,
    trigger: TriggerKind,
    trigger_id: str,
    current_episode_rows: Iterable[str],
    retrieved_nodes: Iterable[str],
    agenda: Iterable[str],
) -> str:
    """Render one target-blind, one-edge cognitive step."""
    episode_rows = tuple(current_episode_rows)
    nodes = tuple(retrieved_nodes)
    agenda_items = tuple(agenda)
    if trigger == "wake" and not episode_rows:
        raise ValueError("WAKE requires one current public episode")
    if trigger == "reactivate" and episode_rows:
        raise ValueError("REACTIVATE cannot fabricate a current episode")
    if trigger not in {"wake", "reactivate"}:
        raise ValueError(f"unknown trigger {trigger!r}")
    public_block = "\n".join(episode_rows) if episode_rows else "(none)"
    node_block = "\n".join(nodes) if nodes else "(none)"
    agenda_block = "\n".join(agenda_items) if agenda_items else "(none)"
    trigger_label = "WAKE" if trigger == "wake" else "REACTIVATE"
    return f"""You are performing one local memory-growth step, not solving an
evaluation question. Connect the current trigger to prior experience when a
small reusable relation is supported. A later thinker will assemble long
chains; do not do its whole task now.

TRIGGER: {trigger_label}({trigger_id})

CURRENT PUBLIC EPISODE (none during reactivation):
{public_block}

RETRIEVED EARLIER MEMORY NODES (provisional and possibly wrong):
{node_block}

OPEN QUESTIONS / AGENDA:
{agenda_block}

Emit exactly one single-line operation. ADD/REVISE may encode ONE semantic
edge only: one left item, one relation, one right item/property. Never emit a
set/list of candidate causes, a complete multi-source explanation, a target
answer, or an evaluation question. Cite only ids shown above.

Use one atomic identifier for LEFT and RIGHT. Never hide several visible
public entities in one field using punctuation, underscores, hyphens, slashes,
or concatenation. An opaque coined concept is allowed only when it does not
combine visible public entities.

ADD | KIND=<witnessed|similarity|difference|role|operator|causal|exception|abstraction> | LEFT=<one item> | RELATION=<one relation> | RIGHT=<one item/property> | CLAIM=<one local sentence> | CITES=<ids> | PREDICTION=<one local prediction or NONE> | CONFIDENCE=<0..1>
REVISE | KIND=<kind> | LEFT=<one item> | RELATION=<one relation> | RIGHT=<one item/property> | CLAIM=<one corrected local sentence> | CITES=<ids> | PREDICTION=<one local prediction or NONE> | CONFIDENCE=<0..1> | SUPERSEDES=<one prior node id>
OPEN_QUESTION | KIND=<kind> | LEFT=<one item> | RELATION=<one relation> | RIGHT=<one item/property> | CITES=<ids>
PASS"""


def render_self_check_prompt(
    *, canonical_typed_edge: str, cited_public_material: Iterable[str],
    superseded_typed_edge: str | None = None,
) -> str:
    """Render model self-reflection using only the proposal's cited material."""
    cited = tuple(cited_public_material)
    if not cited:
        raise ValueError("self-check requires cited public/memory material")
    match = re.fullmatch(
        r"KIND=([a-z]+) \| LEFT=[^|\r\n]+ \| RELATION=[^|\r\n]+ \| RIGHT=[^|\r\n]+",
        canonical_typed_edge,
    )
    if match is None or match.group(1) not in CLAIM_KINDS:
        raise ValueError("self-check requires exactly one canonical typed edge")
    revision_block = ""
    if superseded_typed_edge is not None:
        prior_match = re.fullmatch(
            r"KIND=([a-z]+) \| LEFT=[^|\r\n]+ \| RELATION=[^|\r\n]+ \| RIGHT=[^|\r\n]+",
            superseded_typed_edge,
        )
        if prior_match is None or prior_match.group(1) not in CLAIM_KINDS:
            raise ValueError("revision self-check requires one prior canonical typed edge")
        revision_block = (
            "\n\nTHIS IS A REVISION OF THE PRIOR TYPED EDGE:\n"
            f"{superseded_typed_edge}\n"
            "Judge whether the cited evidence supports replacing that prior edge."
        )
    return f"""Assess one proposed memory using only the cited material below.
This is not an answer key and you have no hidden world state. Do not invent
missing evidence. A plausible idea without enough support is UNRESOLVED.

CANONICAL TYPED EDGE:
{canonical_typed_edge}{revision_block}

CITED MATERIAL:
{chr(10).join(cited)}

Emit exactly one line:
VERDICT=<SUPPORTED|CONTRADICTED|UNRESOLVED> | REASON=<one sentence> | CITES=<ids used>"""


def parse_self_check(raw_completion: str) -> tuple[str, str, tuple[str, ...]] | None:
    values = _fields((raw_completion or "").strip(), "VERDICT")
    # Self-check uses VERDICT=<...> as its first field, rather than an operation
    # prefix. Parse it explicitly to keep the accepted language one line.
    if values is not None:
        return None
    match = re.fullmatch(
        r"VERDICT=(SUPPORTED|CONTRADICTED|UNRESOLVED) \| "
        r"REASON=([^|\r\n]+) \| CITES=([^|\r\n]+)",
        (raw_completion or "").strip(),
    )
    if match is None:
        return None
    cites = _ids(match.group(3).strip())
    if cites is None:
        return None
    return match.group(1).lower(), match.group(2).strip(), cites
