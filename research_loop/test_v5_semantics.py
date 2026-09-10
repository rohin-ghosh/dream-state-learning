from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import patch

from alchemy.backend import VLLMBackend
from alchemy.run_lands_v02_dreamladder import (
    candidate_lines_with_budget,
    canonical_candidate,
    canonical_surface_role_truth,
    parent_prefix_snapshot,
    observation_evidence_records,
    public_role_check,
    role_discovery_prompt,
)
from alchemy.run_lands_v02_organism import (
    canonical_label_answer,
    exact_token_usage,
    parse_thinker_operation,
    public_canonical_labels,
    score_canonical_answer,
)
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02


LANDS = ["Candyland", "Mandyland", "Randyland"]


def record(parents, sample, hits, n_obs=2):
    return {
        "raw": "test",
        "parents": sorted(parents),
        "predictions": {"fox": "red", "cow": "blue"},
        "sample": sample,
        "hits": hits,
        "n_obs": n_obs,
    }


def test_candidate_parser_canonicalizes_parent_order() -> None:
    parsed = canonical_candidate(
        "CANDIDATE: Blendyland <- Randyland, Candyland | "
        "predicted: fox=red, cow=blue",
        LANDS,
        "Blendyland",
        ["fox", "cow"],
    )
    assert parsed is not None
    assert parsed["parents"] == ["Candyland", "Randyland"]


def test_candidate_parser_rejects_unknown_duplicate_and_malformed() -> None:
    assert canonical_candidate(
        "CANDIDATE: X <- Candyland, Nowhere | predicted: fox=red",
        LANDS, "X", ["fox"],
    ) is None
    assert canonical_candidate(
        "CANDIDATE: X <- Candyland, Candyland | predicted: fox=red",
        LANDS, "X", ["fox"],
    ) is None
    assert canonical_candidate(
        "CANDIDATE: not parseable", LANDS, "X", ["fox"]
    ) is None


def test_candidate_parser_rejects_wrong_target_missing_predictions_and_six_parents() -> None:
    six_lands = [f"L{i}" for i in range(6)]
    assert canonical_candidate(
        "CANDIDATE: Other <- L0, L1 | predicted: fox=red, cow=blue",
        six_lands, "Target", ["fox", "cow"],
    ) is None
    assert canonical_candidate(
        "CANDIDATE: Target <- L0, L1 | predicted: fox=red",
        six_lands, "Target", ["fox", "cow"],
    ) is None
    assert canonical_candidate(
        "CANDIDATE: Target <- L0, L1, L2, L3, L4, L5 | "
        "predicted: fox=red, cow=blue",
        six_lands, "Target", ["fox", "cow"],
    ) is None


def test_candidate_budget_marks_overflow_without_making_it_eligible() -> None:
    text = "\n".join(
        f"CANDIDATE: T <- A, B | predicted: fox=c{i}, cow=d{i}"
        for i in range(8)
    )
    eligible, overflow = candidate_lines_with_budget(text, 6, sample=2)
    assert len(eligible) == 6
    assert len(overflow) == 2
    assert all(item["eligible"] for item in eligible)
    assert all(not item["eligible"] for item in overflow)
    assert all(item["reason"] == "over_candidate_budget"
               for item in overflow)


def test_parent_snapshot_deduplicates_sets() -> None:
    scored = [
        record(["Candyland", "Randyland"], 0, 2),
        record(["Randyland", "Candyland"], 0, 2),
    ]
    snapshot = parent_prefix_snapshot(scored, 0)
    assert len(snapshot["proposals"]) == 1
    assert len(snapshot["supported"]) == 1
    assert len(snapshot["retained"]) == 1


def test_parent_snapshot_is_prefix_isolated() -> None:
    scored = [
        record(["Candyland", "Mandyland"], 0, 0),
        record(["Candyland", "Randyland"], 1, 2),
    ]
    prefix_zero = parent_prefix_snapshot(scored, 0)
    prefix_one = parent_prefix_snapshot(scored, 1)
    assert [x["parents"] for x in prefix_zero["proposals"]] == [
        ["Candyland", "Mandyland"]
    ]
    assert ["Candyland", "Randyland"] not in [
        x["parents"] for x in prefix_zero["proposals"]
    ]
    assert ["Candyland", "Randyland"] in [
        x["parents"] for x in prefix_one["proposals"]
    ]


def test_provisional_upgrade_is_append_only() -> None:
    scored = [
        record(["Candyland", "Randyland"], 0, 1),
        record(["Candyland", "Randyland"], 1, 2),
        record(["Mandyland", "Randyland"], 2, 2),
    ]
    s0 = parent_prefix_snapshot(scored, 0)
    s1 = parent_prefix_snapshot(scored, 1)
    s2 = parent_prefix_snapshot(scored, 2)
    assert s0["retained"][0]["status"] == "contradicted"
    assert (s0["retained"][0]["retention_reason"]
            == "legacy_fallback_before_support")
    assert s1["retained"][0]["status"] == "supported"
    assert s1["retained"][0]["hits"] == 2
    assert s1["retained"][0]["sample"] == 1
    assert s1["retained"][0]["first_retained_sample"] == 0
    assert len(s1["retained"]) == 1
    assert {tuple(x["parents"]) for x in s1["retained"]}.issubset(
        {tuple(x["parents"]) for x in s2["retained"]}
    )
    assert len(s2["retained"]) == 2


def test_offline_role_truth_is_surface_canonical() -> None:
    world = SemanticWorldV02(WorldConfig(seed=0))
    skin = make_skin("aligned", world.animal_ids, world.source_land_ids)
    truth = canonical_surface_role_truth(world, skin)
    assert len(truth) == 30
    assert all(pair == tuple(sorted(pair)) for pair in truth)


def test_role_check_uses_every_jointly_observed_public_land() -> None:
    cells = {
        ("fox", "A"): "red", ("cow", "A"): "red",
        ("fox", "B"): "blue", ("cow", "B"): "blue",
        ("fox", "C"): "green", ("cow", "C"): "yellow",
    }
    shared, passed = public_role_check(
        "fox", "cow", ["A", "B", "C"], cells
    )
    assert shared == ["A", "B", "C"]
    assert not passed


def test_role_prompt_is_invariant_to_target_outcome_changes() -> None:
    by_animal = {
        "fox": {"SourceA": "red", "SourceB": "blue", "Target": "green"},
        "cow": {"SourceA": "red", "SourceB": "blue", "Target": "yellow"},
    }
    evidence = {
        ("fox", "SourceA"): ["s1"], ("fox", "SourceB"): ["s2"],
        ("cow", "SourceA"): ["s3"], ("cow", "SourceB"): ["s4"],
        ("fox", "Target"): ["t1"], ("cow", "Target"): ["t2"],
    }
    prompt_before, ids_before = role_discovery_prompt(
        by_animal, evidence, ["SourceA", "SourceB"]
    )
    by_animal["fox"]["Target"] = "ochre"
    by_animal["cow"]["Target"] = "plum"
    prompt_after, ids_after = role_discovery_prompt(
        by_animal, evidence, ["SourceA", "SourceB"]
    )
    assert prompt_before == prompt_after
    assert ids_before == ids_after == ["s1", "s2", "s3", "s4"]
    assert "Target=" not in prompt_before
    assert "t1" not in ids_before and "t2" not in ids_before


def test_blind_comparison_evidence_records_exact_ids_and_tokens() -> None:
    records = observation_evidence_records(
        "Target", [("fox", "Ochre"), ("cow", "Blue")], {
            ("fox", "Target"): ["t2", "t1"],
            ("cow", "Target"): ["t3"],
            ("fox", "Source"): ["s1"],
        },
    )
    assert records == [
        {"evidence_id": "t3", "entity": "cow", "land": "Target",
         "observed_token": "blue"},
        {"evidence_id": "t1", "entity": "fox", "land": "Target",
         "observed_token": "ochre"},
        {"evidence_id": "t2", "entity": "fox", "land": "Target",
         "observed_token": "ochre"},
    ]


def test_thinker_answer_scoring_requires_one_exact_canonical_label() -> None:
    labels = {"red", "blue-green"}
    assert canonical_label_answer("red", labels) == "red"
    assert canonical_label_answer("RED", labels) == "red"
    assert canonical_label_answer("red.", labels) is None
    assert canonical_label_answer("not red", labels) is None
    assert canonical_label_answer("the answer is red", labels) is None


def test_public_token_absent_from_answer_key_is_valid_but_wrong() -> None:
    rows = [
        "[lab] In the color workshop, a mixture is labeled ochre.",
        "[obs] Its coat is red.",
    ]
    public_labels = public_canonical_labels(rows)
    assert public_labels == {"ochre", "red"}
    score = score_canonical_answer("ochre", public_labels, expected="red")
    assert score == {
        "parsed_answer": "ochre", "malformed": False, "correct": False
    }


def test_public_vocabulary_covers_all_scored_ladder_answers() -> None:
    world = SemanticWorldV02(WorldConfig(seed=0))
    public_labels = public_canonical_labels(world.render_lifetime("aligned"))
    semantic_answers = {
        goal["answer"].lower()
        for goal in world.render_goals("aligned", include_answers=True)
    }
    base_answers = {
        goal.answer.lower()
        for goal in world.base.render("aligned", include_answers=True).goals
    }
    assert semantic_answers | base_answers <= public_labels


def test_thinker_operation_parser_rejects_embedded_and_multiline_answers() -> None:
    assert parse_thinker_operation("ANSWER: red") == ("ANSWER", "red")
    assert parse_thinker_operation("preamble ANSWER: red") is None
    assert parse_thinker_operation("ANSWER: red\nTHINK: because") is None
    assert parse_thinker_operation("MEMORY: x ANSWER: blue") is None
    assert parse_thinker_operation("THINK: x MEMORY: y") is None
    assert parse_thinker_operation("MEMORY: x THINK: y ANSWER: red") is None
    assert parse_thinker_operation("ANSWER: red\n") == ("ANSWER", "red")
    assert parse_thinker_operation("ANSWER: red.") == ("ANSWER", "red.")
    assert canonical_label_answer("red.", {"red"}) is None


def test_exact_token_usage_records_ids_and_truncation_metadata() -> None:
    usage = exact_token_usage(
        [1, 2, 3], [7, 8], prompt_truncated=True,
        original_prompt_tokens=9,
    )
    assert usage == {
        "prompt_tokens": 3,
        "output_tokens": 2,
        "original_prompt_tokens": 9,
        "prompt_truncated": True,
        "token_count_source": "model_token_ids",
    }


def test_vllm_usage_counts_exact_supplied_and_generated_token_ids() -> None:
    class FakeTokenizer:
        def apply_chat_template(self, messages, tokenize, add_generation_prompt,
                                return_dict=False):
            assert tokenize and add_generation_prompt
            assert return_dict is False
            content = messages[0]["content"]
            return [101] + [ord(char) for char in content] + [102]

        def __call__(self, text, add_special_tokens=False):
            return {"input_ids": [ord(char) for char in text]}

        def decode(self, ids, skip_special_tokens=True):
            return "".join(chr(value) for value in ids)

    class FakeSamplingParams:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeLLM:
        def __init__(self):
            self.received = None

        def generate(self, prompts, sampling, lora_request=None):
            self.received = prompts
            return [SimpleNamespace(
                prompt_token_ids=list(item["prompt_token_ids"]),
                # Keep the convenience text consistent with the authoritative
                # generated token ids. The backend deliberately decodes and
                # returns those ids rather than trusting a parallel text field.
                outputs=[SimpleNamespace(text="ok", token_ids=[111, 107])],
            ) for item in prompts]

    backend = VLLMBackend.__new__(VLLMBackend)
    backend.tok = FakeTokenizer()
    backend.llm = FakeLLM()
    backend.max_len = 10
    backend._lora_ids = {}
    backend.last_usage = []
    fake_vllm = SimpleNamespace(SamplingParams=FakeSamplingParams)
    with patch.dict(sys.modules, {"vllm": fake_vllm}):
        assert backend.generate(["abcdefghijkl"], max_tokens=2) == ["ok"]
    supplied = backend.llm.received[0]["prompt_token_ids"]
    usage = backend.last_usage[0]
    assert len(supplied) <= 8
    assert usage["prompt_tokens"] == len(supplied)
    assert usage["output_tokens"] == 2
    assert usage["original_prompt_tokens"] == 14
    assert usage["prompt_truncated"] is True
    assert usage["source"] == "model"
    assert usage["token_count_source"] == "model_token_ids"


def test_vllm_chat_ids_force_flat_integer_contract() -> None:
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            assert messages == [{"role": "user", "content": "probe"}]
            assert kwargs["tokenize"] is True
            assert kwargs["return_dict"] is False
            return [11, 22, 33]

    backend = object.__new__(VLLMBackend)
    backend.tok = Tokenizer()
    assert backend._chat_ids("probe") == [11, 22, 33]
