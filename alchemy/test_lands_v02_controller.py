"""Deterministic integrity tests for the v0.2 model-controller boundary."""

from alchemy.run_lands_v02_branchsearch import (
    canonical_ordinary_cells,
    canonical_workshop,
    parse_parents,
    parse_verdict,
)
from alchemy.run_lands_v02_finish import public_workshop_map
from alchemy.run_lands_v02_recipe_recheck import parse_component_ledger
from alchemy.run_lands_v02_topk import parse_candidate_sets, unique_model_match


LANDS = ["Candy Land", "Mandy Land", "Dandy Land", "Randy Land"]


def test_ranked_candidate_parser_is_strict_canonical_and_deduplicated():
    text = """scratch
CANDIDATE 1: Randy Land, Candy Land
CANDIDATE 2: candy land, randy land
CANDIDATE 3: Mandy Land, Unknown Land
CANDIDATE 4: Dandy Land
CANDIDATE 5: Mandy Land, Dandy Land, Candy Land
"""
    assert parse_candidate_sets(text, LANDS, 10) == [
        ("Candy Land", "Randy Land"),
        ("Candy Land", "Mandy Land", "Dandy Land"),
    ]


def test_unique_self_selection_uses_only_committed_model_verdicts():
    records = [
        {"candidate": ["Candy Land", "Randy Land"], "verdict": "MATCH"},
        {"candidate": ["Mandy Land", "Dandy Land"], "verdict": "MISMATCH"},
        {"candidate": ["Candy Land", "Dandy Land"], "verdict": "MATCH"},
    ]
    assert unique_model_match(records, 1) == {"candy land", "randy land"}
    assert unique_model_match(records, 2) == {"candy land", "randy land"}
    assert unique_model_match(records, 3) == set()


def test_public_memory_canonicalizers_are_lossless():
    workshop_row = (
        "[v02_lab_1] The workshop jar labeled ember-glass contains "
        "2 parts red, 1 part yellow, and 0 parts blue."
    )
    assert canonical_workshop([workshop_row]) == "ember-glass=(2,1,0) [v02_lab_1]"
    assert public_workshop_map([workshop_row]) == {(2, 1, 0): "ember-glass"}
    cell_row = (
        "[v02_obs_1] On a visit to Candy Land, you see the fox. "
        "Its coat is orange."
    )
    assert canonical_ordinary_cells([cell_row]) == (
        "CELL [v02_obs_1] | animal=fox | land=Candy Land | "
        "color=orange | recipe=(1, 1, 0)"
    )


def test_output_parsers_use_committed_final_fields():
    assert parse_verdict("VERDICT: MATCH") == "MATCH"
    assert parse_verdict("VERDICT: MATCH\nVERDICT: MISMATCH") == "MISMATCH"
    assert parse_parents("PARENTS: Candy Land, Randy Land") == {
        "candy land",
        "randy land",
    }
    assert parse_parents("PARENTS: AMBIGUOUS") == set()
    assert parse_component_ledger("The sums are 2, 4, and 6.") == (2, 4, 6)


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_"):
            function()
            print(f"ok {name}")
