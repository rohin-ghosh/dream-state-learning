"""Pure transition classification shared by the runner and trace auditor.

Parsing a completion is not enough to authorize a state transition.  A
syntactically valid operation can still cite unavailable material, pack several
public entities into one endpoint, duplicate an existing edge, or jump away
from a reactivation trigger.  Keeping those checks here prevents the live
runner and the deterministic audit from assigning different meanings to the
same model bytes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

from .microdream_prompts import (
    ParsedMicrodream,
    canonical_edge,
    canonical_question,
    local_edge_errors,
    parse_microdream,
    parse_self_check,
)


_UNSAFE_VISIBLE = re.compile(
    r"(?:hidden[_ -]?(?:truth|answer|parent|role)|ground[_ -]?truth|"
    r"final[_ -]?answer\s*:|answer[_ -]?key\s*:|proof[_ -]?graph|"
    r"factor[_ -]?solver|(?:evaluator|scorer|checker)[_ -]?"
    r"(?:label|verdict|score)\s*:|offline[_ -]?truth\s*:)", re.I
)
_NONLOCAL_EDGE = re.compile(
    r"(?:source[_ -]?set|candidate[_ -]?(?:set|parents?)|all (?:parents|causes|solutions)|"
    r"complete (?:parent|solution)|full solution|final answer|answer key)", re.I
)
_PUBLIC_BLOCK = re.compile(
    r"CURRENT PUBLIC EPISODE \(none during reactivation\):\n(.*?)\n\n"
    r"RETRIEVED EARLIER MEMORY NODES \(provisional and possibly wrong\):",
    re.S,
)


@dataclass(frozen=True)
class ProposalContext:
    """Truth-free state needed to classify one proposal completion."""

    visible_ids: frozenset[str]
    episode_ids: frozenset[str]
    experience_ids: frozenset[str]
    node_ids: frozenset[str]
    retrieved_node_ids: tuple[str, ...]
    nodes: Mapping[str, Mapping[str, Any]]
    public_tokens: frozenset[str]
    trigger_node_id: str | None = None


@dataclass(frozen=True)
class ProposalDecision:
    parsed: ParsedMicrodream | None
    kind: str
    error: str | None = None
    cited_episode_ids: tuple[str, ...] = ()
    cited_experience_ids: tuple[str, ...] = ()
    cited_node_ids: tuple[str, ...] = ()
    edge: tuple[str, str, str, str] | None = None
    question: str | None = None

    @property
    def valid(self) -> bool:
        return self.kind != "MALFORMED"


@dataclass(frozen=True)
class SelfCheckDecision:
    verdict: tuple[str, str, tuple[str, ...]] | None
    valid: bool
    error: str | None = None
    cited_episode_ids: tuple[str, ...] = ()
    cited_experience_ids: tuple[str, ...] = ()
    cited_node_ids: tuple[str, ...] = ()


def public_tokens(rows: Iterable[str]) -> frozenset[str]:
    """Return endpoint-control tokens from exact public rows."""
    tokens: set[str] = set()
    for row in rows:
        for explicit in re.findall(
            r"(?:state-token|visit to|see the|coat is|is labeled)\s+"
            r"([A-Za-z0-9][A-Za-z0-9-]*)",
            row,
            flags=re.I,
        ):
            tokens.add(explicit.casefold())
        for literal in re.findall(r"[A-Za-z][A-Za-z0-9-]*", row):
            if len(literal) >= 2:
                tokens.add(literal.casefold())
            tokens.update(
                piece.casefold()
                for piece in re.findall(r"[A-Za-z][A-Za-z0-9]*", literal)
                if len(piece) >= 2
            )
    return frozenset(tokens)


def public_rows_from_prompt(prompt: Any) -> tuple[str, ...]:
    """Recover the exact WAKE public block for audit-side token controls.

    Publication separately re-renders and byte-compares this prompt against the
    committed public export.  This extractor only gives the standalone trace
    audit the same cumulative endpoint controls as the live runner.
    """
    if not isinstance(prompt, str):
        return ()
    match = _PUBLIC_BLOCK.search(prompt)
    if match is None or match.group(1) == "(none)":
        return ()
    return tuple(match.group(1).splitlines())


def _classify_citations(
    cites: Sequence[str], *, context: ProposalContext,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]] | None:
    if not cites or any(cite not in context.visible_ids for cite in cites):
        return None
    groups = (context.episode_ids, context.experience_ids, context.node_ids)
    if any(sum(item in group for group in groups) != 1 for item in cites):
        return None
    return (
        tuple(item for item in cites if item in context.episode_ids),
        tuple(item for item in cites if item in context.experience_ids),
        tuple(item for item in cites if item in context.node_ids),
    )


def _single_edge(parsed: ParsedMicrodream) -> bool:
    if parsed.operation not in {"add", "revise", "open_question"}:
        return True
    if local_edge_errors(parsed):
        return False
    values = (parsed.left, parsed.relation, parsed.right, parsed.claim, parsed.prediction)
    return not any(_NONLOCAL_EDGE.search(value or "") for value in values)


def _is_public_atom_bundle(atom: str, tokens: frozenset[str]) -> bool:
    if atom.casefold() in tokens:
        return False
    normalized = re.sub(r"[^A-Za-z0-9]", "", atom).casefold()
    if not normalized:
        return False
    candidates = {token for token in tokens if token and token in normalized}
    spans: list[tuple[int, int, str]] = []
    for token in candidates:
        compact = re.sub(r"[^A-Za-z0-9]", "", token)
        start = normalized.find(compact)
        while start >= 0:
            spans.append((start, start + len(compact), token))
            start = normalized.find(compact, start + 1)
    return any(
        first_token != second_token
        and (first_end <= second_start or second_end <= first_start)
        for first_start, first_end, first_token in spans
        for second_start, second_end, second_token in spans
    )


def _controlled_atoms(parsed: ParsedMicrodream, tokens: frozenset[str]) -> bool:
    if parsed.operation not in {"add", "revise", "open_question"}:
        return True
    return not any(
        _is_public_atom_bundle(value or "", tokens)
        for value in (parsed.left, parsed.relation, parsed.right)
    )


def _proposal_line(parsed: ParsedMicrodream) -> str:
    if parsed.operation in {"add", "revise"}:
        return (
            f"{parsed.operation.upper()} | KIND={parsed.claim_kind} | LEFT={parsed.left} | "
            f"RELATION={parsed.relation} | RIGHT={parsed.right} | CLAIM={parsed.claim} | "
            f"CITES={','.join(parsed.cites)} | PREDICTION={parsed.prediction} | "
            f"CONFIDENCE={parsed.confidence}"
        )
    question = canonical_question(parsed)
    return question or ""


def classify_proposal(raw_completion: Any, context: ProposalContext) -> ProposalDecision:
    """Classify the exact proposal bytes exactly as the runner may act on them."""
    parsed = parse_microdream(raw_completion) if isinstance(raw_completion, str) else None
    if parsed is None:
        return ProposalDecision(
            parsed=None, kind="MALFORMED",
            error="completion did not match one strict operation",
        )
    if parsed.operation == "pass":
        return ProposalDecision(parsed=parsed, kind="PASS")

    classified = _classify_citations(parsed.cites, context=context)
    edge = canonical_edge(parsed)
    local_reactivation = True
    if context.trigger_node_id is not None and classified is not None:
        trigger = context.nodes.get(context.trigger_node_id)
        trigger_edge = tuple(trigger.get("edge", ())) if trigger is not None else ()
        local_reactivation = (
            context.trigger_node_id in classified[2]
            and edge is not None
            and len(trigger_edge) == 4
            and bool({edge[1], edge[3]}.intersection({trigger_edge[1], trigger_edge[3]}))
        )

    base_valid = (
        classified is not None
        and edge is not None
        and _single_edge(parsed)
        and _controlled_atoms(parsed, context.public_tokens)
        and not _UNSAFE_VISIBLE.search(_proposal_line(parsed))
        and local_reactivation
    )
    if parsed.operation == "open_question":
        question = canonical_question(parsed)
        if not base_valid or question is None:
            return ProposalDecision(
                parsed=parsed, kind="MALFORMED",
                error="OPEN_QUESTION cites unavailable or unsafe material",
            )
        assert classified is not None
        return ProposalDecision(
            parsed=parsed, kind="OPEN_QUESTION", question=question, edge=edge,
            cited_episode_ids=classified[0], cited_experience_ids=classified[1],
            cited_node_ids=classified[2],
        )

    duplicate_ids = [
        node_id for node_id, node in context.nodes.items()
        if edge is not None and tuple(node.get("edge", ()))[1:] == edge[1:]
    ]
    duplicate_edge = bool(duplicate_ids)
    if parsed.operation == "revise" and len(parsed.supersedes) == 1:
        duplicate_edge = any(node_id != parsed.supersedes[0] for node_id in duplicate_ids)
    valid = base_valid and not duplicate_edge
    if parsed.operation == "revise":
        valid = (
            valid
            and len(parsed.supersedes) == 1
            and parsed.supersedes[0] in context.retrieved_node_ids
            and classified is not None
            and parsed.supersedes[0] in classified[2]
        )
        if valid:
            old_edge = tuple(context.nodes[parsed.supersedes[0]].get("edge", ()))
            valid = len(old_edge) == 4 and (
                edge == old_edge
                or bool({old_edge[1], old_edge[3]}.intersection({edge[1], edge[3]}))
            )
    if not valid:
        return ProposalDecision(
            parsed=parsed, kind="MALFORMED",
            error=(
                "duplicate semantic edge does not create a new node"
                if duplicate_edge else
                "operation violates local citation or one-edge boundary"
            ),
        )
    assert classified is not None and edge is not None
    return ProposalDecision(
        parsed=parsed, kind=parsed.operation.upper(), edge=edge,
        cited_episode_ids=classified[0], cited_experience_ids=classified[1],
        cited_node_ids=classified[2],
    )


def classify_self_check(
    raw_completion: Any, *, proposal_cites: Sequence[str],
    supersedes: Sequence[str], context: ProposalContext,
) -> SelfCheckDecision:
    """Authorize only a verdict whose cited ids were in its evidence prompt."""
    verdict = parse_self_check(raw_completion) if isinstance(raw_completion, str) else None
    if verdict is None:
        return SelfCheckDecision(
            verdict=None, valid=False,
            error="self-check was not a cited-material verdict",
        )
    cited = verdict[2]
    classified = _classify_citations(cited, context=context)
    valid = (
        set(cited).issubset(set(proposal_cites))
        and classified is not None
        and not _UNSAFE_VISIBLE.search(verdict[1])
    )
    if len(supersedes) == 1:
        valid = valid and supersedes[0] in cited
    if not valid or classified is None:
        return SelfCheckDecision(
            verdict=verdict, valid=False,
            error="self-check was not a cited-material verdict",
        )
    return SelfCheckDecision(
        verdict=verdict, valid=True,
        cited_episode_ids=classified[0], cited_experience_ids=classified[1],
        cited_node_ids=classified[2],
    )


__all__ = [
    "ProposalContext", "ProposalDecision", "SelfCheckDecision",
    "classify_proposal", "classify_self_check", "public_rows_from_prompt",
    "public_tokens",
]
