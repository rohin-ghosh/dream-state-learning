from research_loop.microdream_prompts import (
    canonical_question,
    local_edge_errors,
    parse_microdream,
    parse_self_check,
    render_microdream_prompt,
    render_self_check_prompt,
)


def test_parse_add_and_one_line_only():
    raw = (
        "ADD | KIND=similarity | LEFT=fox | RELATION=resembles | RIGHT=cow "
        "| CLAIM=The fox and cow recur in the same local pattern. "
        "| CITES=episode:2,node:1 | PREDICTION=Their next local outcome may agree. "
        "| CONFIDENCE=0.6"
    )
    parsed = parse_microdream(raw)
    assert parsed is not None
    assert parsed.operation == "add"
    assert parsed.cites == ("episode:2", "node:1")
    assert parsed.confidence == 0.6
    assert parse_microdream(raw + "\nPASS") is None


def test_revision_requires_supersedes():
    without = (
        "REVISE | KIND=exception | LEFT=fox | RELATION=differs | RIGHT=cow "
        "| CLAIM=The fox differs here. | CITES=node:1 "
        "| PREDICTION=NONE | CONFIDENCE=0.7"
    )
    assert parse_microdream(without) is None
    parsed = parse_microdream(without + " | SUPERSEDES=node:1")
    assert parsed is not None
    assert parsed.supersedes == ("node:1",)


def test_prompt_distinguishes_wake_and_reactivation():
    wake = render_microdream_prompt(
        trigger="wake",
        trigger_id="episode:1",
        current_episode_rows=("[obs:1 | episode:1] public row",),
        retrieved_nodes=("[node:0] earlier",),
        agenda=(),
    )
    assert "WAKE(episode:1)" in wake
    assert "complete multi-source explanation" in wake
    reactivate = render_microdream_prompt(
        trigger="reactivate",
        trigger_id="node:0",
        current_episode_rows=(),
        retrieved_nodes=("[node:0] earlier",),
        agenda=("What recurs?",),
    )
    assert "REACTIVATE(node:0)" in reactivate
    try:
        render_microdream_prompt(
            trigger="reactivate",
            trigger_id="node:0",
            current_episode_rows=("invented row",),
            retrieved_nodes=(),
            agenda=(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("reactivation accepted a fabricated episode")


def test_open_question_and_self_check_are_strict():
    parsed = parse_microdream(
        "OPEN_QUESTION | KIND=causal | LEFT=fox | RELATION=may-cause | "
        "RIGHT=crimson | CITES=node:2"
    )
    assert parsed is not None and parsed.operation == "open_question"
    assert parsed.question == canonical_question(parsed)
    assert parsed.question == (
        "OPEN_QUESTION | KIND=causal | LEFT=fox | RELATION=may-cause | "
        "RIGHT=crimson | CITES=node:2"
    )
    assert parse_microdream(
        "OPEN_QUESTION | QUESTION=Does this recur elsewhere? | CITES=node:2"
    ) is None
    verdict = parse_self_check(
        "VERDICT=UNRESOLVED | REASON=Only one observation supports it. "
        "| CITES=episode:2"
    )
    assert verdict == (
        "unresolved", "Only one observation supports it.", ("episode:2",)
    )
    assert parse_self_check(
        "VERDICT=SUPPORTED | REASON=Looks right. | CITES=episode:2\nextra"
    ) is None


def test_open_question_obeys_the_same_one_edge_syntax_as_memory_nodes():
    parsed = parse_microdream(
        "OPEN_QUESTION | KIND=causal | LEFT=fox,cow | RELATION=may-cause | "
        "RIGHT=crimson | CITES=node:2"
    )
    assert parsed is not None
    assert any("left" in error for error in local_edge_errors(parsed))


def test_self_check_prompt_accepts_only_typed_edge_not_rationale_fields():
    prompt = render_self_check_prompt(
        canonical_typed_edge=(
            "KIND=causal | LEFT=fox | RELATION=may-cause | RIGHT=crimson"
        ),
        cited_public_material=("[obs:1] fox was followed by crimson",),
    )
    assert "CANONICAL TYPED EDGE" in prompt
    assert "CLAIM=" not in prompt and "PREDICTION=" not in prompt
    try:
        render_self_check_prompt(
            canonical_typed_edge=(
                "KIND=causal | LEFT=fox | RELATION=may-cause | RIGHT=crimson | "
                "CLAIM=smuggled rationale"
            ),
            cited_public_material=("[obs:1] public",),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("self-check accepted a free-form rationale field")


if __name__ == "__main__":
    test_parse_add_and_one_line_only()
    test_revision_requires_supersedes()
    test_prompt_distinguishes_wake_and_reactivation()
    test_open_question_and_self_check_are_strict()
    test_open_question_obeys_the_same_one_edge_syntax_as_memory_nodes()
    test_self_check_prompt_accepts_only_typed_edge_not_rationale_fields()
