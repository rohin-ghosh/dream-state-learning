"""Scripted CPU tests for the recurrent microdream driver."""

from __future__ import annotations

import hashlib

from research_loop.microdream_contract import validate_trace
from research_loop.microdream_runner import run_recurrent_life
from research_loop.microdream_world import export_rows


def _world(count: int = 3) -> dict:
    rows = tuple(
        f"[obs_{index} | episode_{index}] During episode {index}, state-token token{index}."
        for index in range(count)
    )
    return export_rows(rows, world_seed=11, skin="aligned", life_tag="life-scripted")


def _add(cites: str, claim: str = "one local public connection", *,
         left: str = "episode", right: str = "pattern") -> str:
    return (
        f"ADD | KIND=similarity | LEFT={left} | RELATION=shows | RIGHT={right} | "
        f"CLAIM={claim} | CITES={cites} | PREDICTION=NONE | CONFIDENCE=0.8"
    )


def test_depth_growth_uses_earlier_node_and_one_wake_per_episode():
    completions = {
        "episode_0": _add("episode_0", left="token0", right="pattern"),
        "episode_1": _add("episode_1,node_00000", left="pattern", right="token1"),
        "episode_2": "PASS",
    }

    def generate(prompt, max_tokens, temperature, seed):
        assert max_tokens > 0 and temperature == 0.0
        if prompt.startswith("You are performing"):
            trigger = prompt.split("TRIGGER: ", 1)[1].split("\n", 1)[0]
            return completions[trigger.split("(", 1)[1].rstrip(")")], {}
        raise AssertionError("unexpected self-check prompt")

    result = run_recurrent_life(_world(), generate, condition="no_gate_no_drift")
    trace = result["trace"]
    assert validate_trace(trace) == []
    assert [cycle["trigger"]["kind"] for cycle in trace["cycles"]] == ["WAKE"] * 3
    assert [event["depth"] for event in trace["events"]] == [1, 2]
    assert len(trace["episodes"]) == 3
    assert all(
        cycle["model_prompt_sha256"]
        == hashlib.sha256(cycle["model_prompt"].encode("utf-8")).hexdigest()
        for cycle in trace["cycles"]
    )


def test_self_check_corpus_contains_only_supported_nodes():
    wake_outputs = [
        _add("episode_0", left="token0", right="pattern0"),
        _add("episode_1", left="token1", right="pattern1"),
        _add("episode_2", left="token2", right="pattern2"),
    ]
    wake_index = 0
    check_index = 0
    verdicts = ("SUPPORTED", "UNRESOLVED", "CONTRADICTED")

    def generate(prompt, max_tokens, temperature, seed):
        nonlocal wake_index, check_index
        if prompt.startswith("You are performing"):
            output = wake_outputs[wake_index]
            wake_index += 1
            return output, {"prompt_tokens": 10, "output_tokens": 4}
        verdict = verdicts[check_index]
        cite = f"episode_{check_index}"
        check_index += 1
        return f"VERDICT={verdict} | REASON=public evidence only | CITES={cite}", {}

    result = run_recurrent_life(_world(), generate, condition="self_check_no_drift")
    trace = result["trace"]
    assert validate_trace(trace) == []
    assert [line["node_ids"] for line in result["corpus"]["lines"]] == [["node_00000"]]
    assert [event["status"] for event in trace["events"] if event["type"] == "STATUS_CHANGE"] == [
        "supported", "unresolved", "contradicted"
    ]


def test_malformed_completion_is_preserved_without_fake_memory_event():
    raw = "ADD | this is not a strict one-edge operation"
    outputs = iter((raw, "PASS", "PASS"))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(_world(), generate, condition="no_gate_no_drift")
    trace = result["trace"]
    assert validate_trace(trace) == []
    malformed = trace["cycles"][0]["operation"]
    assert malformed["kind"] == "MALFORMED"
    assert malformed["raw_completion"] == raw
    assert trace["cycles"][0]["event_ids"] == []


def test_full_solution_or_source_set_claim_is_malformed_not_a_memory_node():
    raw = (
        "ADD | KIND=causal | LEFT=target | RELATION=has | RIGHT=source-set | "
        "CLAIM=all parents and complete solution | CITES=episode_0 | "
        "PREDICTION=NONE | CONFIDENCE=0.9"
    )

    def generate(prompt, max_tokens, temperature, seed):
        return raw, {}

    result = run_recurrent_life(_world(1), generate, condition="no_gate_no_drift")
    assert validate_trace(result["trace"]) == []
    operation = result["trace"]["cycles"][0]["operation"]
    assert operation["kind"] == "MALFORMED"
    assert operation["raw_completion"] == raw


def test_slash_list_self_pair_and_duplicate_do_not_become_memory_nodes():
    outputs = iter((
        "ADD | KIND=causal | LEFT=target | RELATION=uses | "
        "RIGHT=Candyland/Randyland/Dandyland | CLAIM=one local connection | "
        "CITES=episode_0 | PREDICTION=NONE | CONFIDENCE=0.8",
        "ADD | KIND=role | LEFT=fox | RELATION=matches | RIGHT=fox | "
        "CLAIM=the same entity matches itself | CITES=episode_1 | "
        "PREDICTION=NONE | CONFIDENCE=0.8",
        _add("episode_2", left="fox", right="crimson"),
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(_world(), generate, condition="no_gate_no_drift")
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "MALFORMED", "MALFORMED", "ADD"
    ]
    assert len(result["trace"]["events"]) == 1


def test_repeated_edge_is_logged_but_cannot_create_false_depth():
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        _add("episode_1,node_00000", left="fox", right="crimson",
             claim="a paraphrase of the same edge"),
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(_world(2), generate, condition="no_gate_no_drift")
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "ADD", "MALFORMED"
    ]
    assert [event["depth"] for event in result["trace"]["events"]] == [1]


def test_revision_is_append_only_but_corpus_uses_latest_node():
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        "REVISE | KIND=similarity | LEFT=fox | RELATION=shows | RIGHT=crimson | "
        "CLAIM=the edge is retained with a narrower interpretation | "
        "CITES=episode_1,node_00000 | PREDICTION=NONE | CONFIDENCE=0.7 | "
        "SUPERSEDES=node_00000",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(_world(2), generate, condition="no_gate_no_drift")
    events = result["trace"]["events"]
    assert [event["type"] for event in events] == ["ADD_NODE", "REVISE_NODE"]
    assert [event["depth"] for event in events] == [1, 1]
    assert events[1]["supersedes"] == ["node_00000"]
    assert [line["node_ids"] for line in result["corpus"]["lines"]] == [["node_00001"]]


def test_gated_revision_only_supersedes_after_supported_self_check():
    def run(verdict: str):
        outputs = iter((
            _add("episode_0", left="fox", right="crimson"),
            "VERDICT=SUPPORTED | REASON=the cited row supports it | CITES=episode_0",
            "REVISE | KIND=similarity | LEFT=fox | RELATION=shows | RIGHT=azure | "
            "CLAIM=a local corrected edge | CITES=episode_1,node_00000 | "
            "PREDICTION=NONE | CONFIDENCE=0.7 | SUPERSEDES=node_00000",
            f"VERDICT={verdict.upper()} | REASON=the cited material yields this verdict | "
            "CITES=episode_1,node_00000",
        ))

        def generate(prompt, max_tokens, temperature, seed):
            return next(outputs), {}

        return run_recurrent_life(
            _world(2), generate, condition="self_check_no_drift"
        )

    supported = run("supported")
    assert [line["node_ids"] for line in supported["corpus"]["lines"]] == [
        ["node_00001"]
    ]

    contradicted = run("contradicted")
    assert [line["node_ids"] for line in contradicted["corpus"]["lines"]] == [
        ["node_00000"]
    ]


def test_all_four_conditions_have_explicit_wake_and_reactivation_schedules():
    expected_cycles = {
        "no_gate_no_drift": ["WAKE", "WAKE", "WAKE"],
        "self_check_no_drift": ["WAKE", "WAKE", "WAKE"],
        "no_gate_drift": ["WAKE", "WAKE", "REACTIVATE", "WAKE", "REACTIVATE"],
        "self_check_drift": ["WAKE", "WAKE", "REACTIVATE", "WAKE", "REACTIVATE"],
    }
    for condition, expected in expected_cycles.items():
        added = False

        def generate(prompt, max_tokens, temperature, seed):
            nonlocal added
            if prompt.startswith("Assess one proposed memory"):
                return "VERDICT=SUPPORTED | REASON=the cited row supports it | CITES=episode_0", {}
            if "TRIGGER: WAKE(episode_0)" in prompt and not added:
                added = True
                return _add("episode_0", left="token0", right="pattern0"), {}
            return "PASS", {}

        result = run_recurrent_life(
            _world(), generate, condition=condition, reactivate_every=2,
        )
        assert result["trace"]["condition"] == condition
        assert [cycle["trigger"]["kind"] for cycle in result["trace"]["cycles"]] == expected


def test_freeform_rationale_is_audit_only_not_retrieved_or_serialized():
    private_rationale = "This rationale considers Candyland Randyland together"
    prompts: list[str] = []
    outputs = iter((
        _add("episode_0", claim=private_rationale, left="fox", right="crimson"),
        "PASS",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        prompts.append(prompt)
        return next(outputs), {}

    result = run_recurrent_life(_world(2), generate, condition="no_gate_no_drift")
    assert private_rationale in result["trace"]["events"][0]["claim"]
    assert private_rationale not in result["corpus"]["lines"][0]["text"]
    assert private_rationale not in prompts[1]


def test_reactivate_has_no_fabricated_current_episode_and_keeps_trigger_node():
    prompts: list[str] = []
    wake_outputs = iter((
        _add("episode_0", left="token0", right="pattern0"),
        _add("episode_1", left="token1", right="pattern1"),
    ))
    reactivation_index = 0

    def generate(prompt, max_tokens, temperature, seed):
        nonlocal reactivation_index
        prompts.append(prompt)
        if "TRIGGER: WAKE(" in prompt:
            return next(wake_outputs), {}
        # Every reactivation extends the triggering node by one local edge.
        trigger = prompt.split("TRIGGER: REACTIVATE(", 1)[1].split(")", 1)[0]
        chain = {
            "node_00000": ("pattern0", "extension0"),
            "node_00002": ("pattern1", "extension1"),
            "node_00003": ("extension1", "extension2"),
        }
        left, right = chain[trigger]
        output = _add(
            trigger,
            left=left,
            right=right,
        )
        reactivation_index += 1
        return output, {}

    result = run_recurrent_life(
        _world(2), generate, condition="no_gate_drift", reactivate_every=1,
    )
    trace = result["trace"]
    assert validate_trace(trace) == []
    reactivations = [cycle for cycle in trace["cycles"] if cycle["trigger"]["kind"] == "REACTIVATE"]
    assert reactivations
    for cycle in reactivations:
        trigger = cycle["trigger"]["id"]
        assert cycle["episode_id"] is None
        assert cycle["experience_ids"] == []
        assert trigger in cycle["retrieved_node_ids"]
    reactivate_prompts = [prompt for prompt in prompts if "TRIGGER: REACTIVATE(" in prompt]
    assert reactivate_prompts
    assert all("CURRENT PUBLIC EPISODE (none during reactivation):\n(none)" in prompt
               for prompt in reactivate_prompts)


def test_public_parent_bundles_hidden_by_punctuation_or_concatenation_are_rejected():
    world = export_rows(
        tuple(
            f"[obs_{index} | episode_{index}] Alpha and Beta remain publicly visible."
            for index in range(4)
        ),
        world_seed=12, skin="aligned", life_tag="atom-controls",
    )
    outputs = iter((
        _add("episode_0", left="target", right="Alpha-Beta"),
        _add("episode_1", left="target", right="Alpha_Beta"),
        _add("episode_2", left="target", right="AlphaBeta"),
        _add("episode_3", left="target", right="zephyr-quorum"),
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(world, generate, condition="no_gate_no_drift")
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "MALFORMED", "MALFORMED", "MALFORMED", "ADD",
    ]
    assert result["trace"]["events"][0]["right"] == "zephyr-quorum"


def test_exact_public_hyphenated_state_token_remains_one_legal_atom():
    world = export_rows(
        (
            "[obs_0 | episode_0] The visible state-token is blue-green.",
            "[obs_1 | episode_1] The visible place is Candyland and Randyland.",
        ),
        world_seed=13, skin="aligned", life_tag="hyphen-atom-controls",
    )
    outputs = iter((
        _add("episode_0", left="token0", right="blue-green"),
        _add("episode_1", left="target", right="Candyland-Randyland"),
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(world, generate, condition="no_gate_no_drift")
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "ADD", "MALFORMED",
    ]
    assert result["trace"]["events"][0]["right"] == "blue-green"


def test_prefixed_one_character_and_relation_bundles_are_rejected():
    world = export_rows(
        (
            "[obs_0 | episode_0] Alpha and Beta are visible public identifiers.",
            "[obs_1 | episode_1] state-token x and state-token y are visible.",
            "[obs_2 | episode_2] state-token 1 and state-token 2 are visible.",
            "[obs_3 | episode_3] Alpha and Beta remain visible.",
        ),
        world_seed=14, skin="aligned", life_tag="bundle-bypass-controls",
    )
    outputs = iter((
        _add("episode_0", left="target", right="pairAlphaBeta"),
        _add("episode_1", left="target", right="pairXY"),
        _add("episode_2", left="target", right="pair12"),
        "ADD | KIND=causal | LEFT=target | RELATION=Alpha-Beta | RIGHT=outcome | "
        "CLAIM=one local connection | CITES=episode_3 | PREDICTION=NONE | "
        "CONFIDENCE=0.8",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(world, generate, condition="no_gate_no_drift")
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "MALFORMED", "MALFORMED", "MALFORMED", "MALFORMED",
    ]
    assert result["trace"]["events"] == []


def test_kind_relabel_cannot_duplicate_a_semantic_triple_or_inflate_depth():
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        "ADD | KIND=causal | LEFT=fox | RELATION=shows | RIGHT=crimson | "
        "CLAIM=a kind-only relabel | CITES=episode_1,node_00000 | "
        "PREDICTION=NONE | CONFIDENCE=0.8",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(_world(2), generate, condition="no_gate_no_drift")
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "ADD", "MALFORMED",
    ]
    assert [event["depth"] for event in result["trace"]["events"]] == [1]


def test_reactivation_must_locally_extend_its_trigger():
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        "PASS",
        _add("node_00000", left="wolf", right="azure"),
        "PASS",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(
        _world(2), generate, condition="no_gate_drift", reactivate_every=2,
    )
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "ADD", "PASS", "MALFORMED", "PASS",
    ]
    assert len(result["trace"]["events"]) == 1


def test_reactivation_open_question_must_locally_extend_its_trigger():
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        "PASS",
        "OPEN_QUESTION | KIND=causal | LEFT=wolf | RELATION=may-cause | "
        "RIGHT=azure | CITES=node_00000",
        "PASS",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(
        _world(2), generate, condition="no_gate_drift", reactivate_every=2,
    )
    assert [cycle["operation"]["kind"] for cycle in result["trace"]["cycles"]] == [
        "ADD", "PASS", "MALFORMED", "PASS",
    ]
    assert all(not cycle["next_state"]["agenda"] for cycle in result["trace"]["cycles"])


def test_failed_gated_revision_does_not_hide_or_reactivate_over_the_old_memory():
    prompts: list[str] = []
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        "VERDICT=SUPPORTED | REASON=the cited row supports it | CITES=episode_0",
        "REVISE | KIND=similarity | LEFT=fox | RELATION=shows | RIGHT=azure | "
        "CLAIM=a proposed correction | CITES=episode_1,node_00000 | "
        "PREDICTION=NONE | CONFIDENCE=0.7 | SUPERSEDES=node_00000",
        "VERDICT=CONTRADICTED | REASON=the cited material contradicts replacement | "
        "CITES=episode_1,node_00000",
        "PASS",
        "PASS",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        prompts.append(prompt)
        return next(outputs), {}

    result = run_recurrent_life(
        _world(2), generate, condition="self_check_drift", reactivate_every=2,
    )
    reactivate_prompts = [prompt for prompt in prompts if "TRIGGER: REACTIVATE" in prompt]
    assert len(reactivate_prompts) == 2
    assert all("REACTIVATE(node_00000)" in prompt for prompt in reactivate_prompts)
    assert all("node_00001" not in prompt for prompt in reactivate_prompts)
    revision_check = next(prompt for prompt in prompts if "THIS IS A REVISION" in prompt)
    assert "KIND=similarity | LEFT=fox | RELATION=shows | RIGHT=crimson" in revision_check
    assert [line["node_ids"] for line in result["corpus"]["lines"]] == [["node_00000"]]


def test_open_question_is_typed_and_agenda_never_stores_freeform_prose():
    outputs = iter((
        "OPEN_QUESTION | KIND=causal | LEFT=token0 | RELATION=may-cause | "
        "RIGHT=afterglow | CITES=episode_0",
        "PASS",
    ))
    prompts: list[str] = []

    def generate(prompt, max_tokens, temperature, seed):
        prompts.append(prompt)
        return next(outputs), {}

    result = run_recurrent_life(_world(2), generate, condition="no_gate_no_drift")
    first = result["trace"]["cycles"][0]
    operation = first["operation"]
    expected = (
        "OPEN_QUESTION | KIND=causal | LEFT=token0 | RELATION=may-cause | "
        "RIGHT=afterglow | CITES=episode_0"
    )
    assert operation["kind"] == "OPEN_QUESTION"
    assert "question" not in operation
    assert (operation["claim_kind"], operation["left"], operation["relation"],
            operation["right"]) == ("causal", "token0", "may-cause", "afterglow")
    assert first["public_state"]["agenda"] == []
    assert first["next_state"]["agenda"] == [expected]
    assert expected in prompts[1]
    assert "Does this" not in prompts[1]


def test_claim_and_prediction_cannot_change_the_self_check_prompt():
    check_prompts: list[str] = []

    def one_run(claim: str) -> None:
        def generate(prompt, max_tokens, temperature, seed):
            if prompt.startswith("You are performing"):
                return _add("episode_0", claim=claim, left="token0", right="afterglow"), {}
            check_prompts.append(prompt)
            return (
                "VERDICT=SUPPORTED | REASON=the cited row supports it | CITES=episode_0",
                {},
            )

        run_recurrent_life(_world(1), generate, condition="self_check_no_drift")

    one_run("first private rationale")
    one_run("entirely different private rationale")
    assert check_prompts[0] == check_prompts[1]
    assert "first private rationale" not in check_prompts[0]
    assert "CLAIM=" not in check_prompts[0] and "PREDICTION=" not in check_prompts[0]


def test_revision_requires_cited_local_lineage_and_hides_superseded_retrieval():
    outputs = iter((
        _add("episode_0", left="fox", right="crimson"),
        "REVISE | KIND=similarity | LEFT=fox | RELATION=shows | RIGHT=azure | "
        "CLAIM=a local corrected edge | CITES=episode_1,node_00000 | "
        "PREDICTION=NONE | CONFIDENCE=0.7 | SUPERSEDES=node_00000",
        "PASS",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {}

    result = run_recurrent_life(_world(3), generate, condition="no_gate_no_drift")
    events = result["trace"]["events"]
    assert [event["depth"] for event in events] == [1, 1]
    third = result["trace"]["cycles"][2]
    assert "node_00000" not in third["retrieved_node_ids"]
    assert "node_00001" in third["retrieved_node_ids"]
    assert "supersedes=node_00000" in third["model_prompt"]
    assert "status=provisional" in third["model_prompt"]
    assert "conflicts=node_00000" in third["model_prompt"]


def test_unrelated_or_uncited_revision_is_malformed():
    cases = (
        "REVISE | KIND=similarity | LEFT=wolf | RELATION=shows | RIGHT=azure | "
        "CLAIM=unrelated replacement | CITES=episode_1,node_00000 | "
        "PREDICTION=NONE | CONFIDENCE=0.7 | SUPERSEDES=node_00000",
        "REVISE | KIND=similarity | LEFT=fox | RELATION=shows | RIGHT=azure | "
        "CLAIM=uncited replacement | CITES=episode_1 | "
        "PREDICTION=NONE | CONFIDENCE=0.7 | SUPERSEDES=node_00000",
    )
    for revision in cases:
        outputs = iter((_add("episode_0", left="fox", right="crimson"), revision))

        def generate(prompt, max_tokens, temperature, seed):
            return next(outputs), {}

        result = run_recurrent_life(_world(2), generate, condition="no_gate_no_drift")
        assert result["trace"]["cycles"][1]["operation"]["kind"] == "MALFORMED"
        assert len(result["trace"]["events"]) == 1


def test_exact_call_records_cover_pass_open_malformed_and_malformed_self_check():
    outputs = iter((
        "PASS",
        "OPEN_QUESTION | KIND=causal | LEFT=token1 | RELATION=may-cause | "
        "RIGHT=afterglow | CITES=episode_1",
        "not a protocol operation",
        _add("episode_3", left="token3", right="afterglow"),
        "not a self-check verdict",
    ))

    def generate(prompt, max_tokens, temperature, seed):
        return next(outputs), {"fixture_note": f"seed={seed}"}

    result = run_recurrent_life(
        _world(4), generate, condition="self_check_no_drift",
        seed=23, max_tokens=77, temperature=0.25,
    )
    trace = result["trace"]
    assert [cycle["operation"]["kind"] for cycle in trace["cycles"]] == [
        "PASS", "OPEN_QUESTION", "MALFORMED", "ADD",
    ]
    assert [call["kind"] for call in trace["model_calls"]] == [
        "proposal", "proposal", "proposal", "proposal", "self_check",
    ]
    for call in trace["model_calls"]:
        assert call["prompt_sha256"] == hashlib.sha256(call["prompt"].encode()).hexdigest()
        assert call["output_sha256"] == hashlib.sha256(call["output"].encode()).hexdigest()
        assert call["max_tokens"] == 77 and call["temperature"] == 0.25
        assert call["usage"]["source"] == "scripted_fallback"
        assert call["usage"]["raw_usage"] == {"fixture_note": f"seed={call['seed']}"}
    assert [cycle["proposal_call"]["output"] for cycle in trace["cycles"]] == [
        "PASS",
        "OPEN_QUESTION | KIND=causal | LEFT=token1 | RELATION=may-cause | "
        "RIGHT=afterglow | CITES=episode_1",
        "not a protocol operation",
        _add("episode_3", left="token3", right="afterglow"),
    ]
    assert trace["cycles"][3]["operation"]["self_check_call"]["output"] == (
        "not a self-check verdict"
    )
