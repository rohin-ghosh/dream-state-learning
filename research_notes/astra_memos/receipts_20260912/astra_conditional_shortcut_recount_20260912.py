"""CPU-only frozen-corpus shortcut recount. No model outcomes or repo imports."""
from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


CANDIDATE = Path("/tmp/astra_conditional_native_preps_20260912/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material/candidate.json")
PIN = "5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c"
MAPS = ("AUTH", "DERANGED")
PROJECTIONS = {
    "REVISE": ((), ("instance",), ("square",), ("observed",), ("prior",), ("observed", "prior"),
               ("instance", "observed"), ("instance", "prior"), ("instance", "observed", "prior"),
               ("square", "observed"), ("square", "prior"), ("square", "observed", "prior"),
               ("square_bucket", "observed", "prior")),
    "PROSPECT": ((), ("instance",), ("square",), ("goal",), ("belief",),
                 ("instance", "goal"), ("instance", "belief"), ("square", "goal"), ("square", "belief"),
                 ("belief", "goal"), ("belief_dax", "goal")),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_candidate(path=CANDIDATE):
    payload = path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == PIN, "not exact frozen attempt2 candidate")
    candidate = json.loads(payload)
    require(candidate["root"] == 0 and candidate["spellings"] == dict(actions=["dax", "wug"], outcomes=["fep", "nup"]), "wrong root/spellings")
    return candidate


def one(pattern, text):
    matches = re.findall(pattern, text)
    require(len(matches) == 1, f"public field not unique: {pattern}")
    return matches[0]


def visible(context, operation):
    instance, square = one(r"\b(r[0-9]+-(?:train|dev)-(?:prospect|revise)-([0-9]{2}))\b", context)
    fields = dict(instance=instance, square=int(square), square_bucket=(int(square) // 2) % 2)
    if operation == "REVISE":
        fields["observed"] = one(r"\bOBSERVED:\s*([a-z]+)\.", context)
        fields["prior"] = one(r"\bPRIOR:\s*PREDICT\s+([a-z]+)\s*->", context)
    else:
        require(operation == "PROSPECT", "unknown operation")
        fields["goal"] = one(r"\bGOAL:\s*([a-z]+)\.", context)
        card = one(r"\bBELIEF:\s*([^\.]+)\.", context)
        bindings = re.findall(r"([a-z]+)\s*->\s*([a-z]+)", card)
        require(len(bindings) == 2 and {action for action, _ in bindings} == {"dax", "wug"}, "not binary public card")
        fields["belief"] = tuple(sorted(bindings))
        fields["belief_dax"] = dict(bindings)["dax"]
    return fields


def target(case, assigned_map):
    inputs = case["inputs"]
    if case["operation"] == "REVISE":
        keep = (inputs["expected"] == inputs["observed"]) == (assigned_map == "AUTH")
        action = inputs["prior_action"] if keep else next(action for action in inputs["actions"] if action != inputs["prior_action"])
        return ("MATCH" if keep else "MISMATCH", "KEEP" if keep else "SWITCH", action)
    eligible = [action for action in inputs["actions"] if (inputs["belief"][action] == inputs["goal"]) == (assigned_map == "AUTH")]
    require(len(eligible) == 1, "not a unique map target")
    action = eligible[0]
    return action, inputs["belief"][action], action


def render(operation, fields):
    if operation == "REVISE":
        return f"COMPARE: {fields[0]}\nPOLICY: {fields[1]}\nNEXT: {fields[2]}"
    return f"PREDICT: {fields[0]} -> {fields[1]}\nACT: {fields[2]}"


def key_for(case, projection):
    fields = visible(case["context"], case["operation"])
    return tuple(fields[name] for name in projection)


def cells(cases, assigned_map, projection):
    groups = defaultdict(Counter)
    for case in cases:
        groups[key_for(case, projection)][target(case, assigned_map)] += 1
    return groups


def ceiling(groups):
    total = sum(sum(counts.values()) for counts in groups.values())
    correct = sum(max(counts.values()) for counts in groups.values())
    shape = Counter((sum(counts.values()), len(counts), max(counts.values())) for counts in groups.values())
    return dict(rows=total, cells=len(groups), correct=correct, ceiling=correct / total,
        component_correct=[sum(max(Counter({value: sum(count for label, count in counts.items() if label[index] == value)
                                          for value in {label[index] for label in counts}}).values())
                               for counts in groups.values()) for index in range(3)],
        cell_shapes=[dict(rows_per_cell=rows, distinct_targets=targets, majority_count=majority, cells=count)
                     for (rows, targets, majority), count in sorted(shape.items())])


def fit_train_lookup(train, assigned_map, projection):
    return {key: min(counts, key=lambda label: (-counts[label], label)) for key, counts in cells(train, assigned_map, projection).items()}


def transfer(lookup, dev, assigned_map, projection):
    covered = correct = 0
    unseen = []
    for case in dev:
        key = key_for(case, projection)
        if key not in lookup:
            unseen.append(case["id"])
            continue
        covered += 1
        correct += lookup[key] == target(case, assigned_map)
    return dict(total=len(dev), covered=covered, unseen=len(dev) - covered, correct=correct,
        correct_over_all_rows=correct / len(dev), accuracy_on_covered=correct / covered if covered else None,
        unseen_case_ids=unseen, tie_break="train majority; lexicographically smallest target tuple on ties; unseen keys abstain")


def recount(candidate):
    report = dict(candidate_sha256=PIN, root=0, source="FROZEN_CORPUS_ONLY_NO_MODEL_OUTCOMES", operations={}, revise_square_cells={})
    for operation in ("REVISE", "PROSPECT"):
        train = [case for case in candidate["train"]["AUTH"] if case["operation"] == operation]
        dev = [case for case in candidate["dev"] if case["operation"] == operation]
        require((len(train), len(dev)) == (64, 32), "unexpected registered cell counts")
        report["operations"][operation] = dict(train_rows=64, dev_rows=32, maps={})
        for assigned_map in MAPS:
            require(all(case["response"] == render(operation, target(case, assigned_map))
                        for case in candidate["train"][assigned_map] if case["operation"] == operation), "training response differs from independent rule")
            reports = report["operations"][operation]["maps"][assigned_map] = {}
            for projection in PROJECTIONS[operation]:
                name = "+".join(projection) or "constant"
                train_cells = cells(train, assigned_map, projection)
                dev_cells = cells(dev, assigned_map, projection)
                reports[name] = dict(train=ceiling(train_cells), dev=ceiling(dev_cells),
                    train_only_lookup_dev=transfer(fit_train_lookup(train, assigned_map, projection), dev, assigned_map, projection))
                if projection == ("square", "observed", "prior"):
                    reports[name]["train_lookup_cells"] = [dict(key=list(key), labels=[dict(target=list(label), count=count)
                        for label, count in sorted(counts.items())]) for key, counts in sorted(train_cells.items())]
                    lookup = fit_train_lookup(train, assigned_map, projection)
                    indexed = {case["id"]: case for case in dev}
                    reports[name]["dev_twin_passes"] = {family: dict(total=len(candidate["twins"]["dev"][family]),
                        both_targets_correct=sum(all(lookup[key_for(indexed[case_id], projection)] == target(indexed[case_id], assigned_map)
                                                     for case_id in pair) for pair in candidate["twins"]["dev"][family]))
                        for family in ("outcome", "prior_action")}
        if operation == "REVISE":
            for split, panel in (("train", train), ("dev", dev)):
                by_square = defaultdict(list)
                for case in panel:
                    by_square[visible(case["context"], operation)["square"]].append(case)
                report["revise_square_cells"][split] = [dict(square=square, rows=len(rows),
                    public_expected_histogram=dict(Counter(one(r"\bPRIOR:\s*PREDICT\s+[a-z]+\s*->\s*([a-z]+);", case["context"]) for case in rows)),
                    observed_prior_cells=len(cells(rows, "AUTH", ("observed", "prior"))),
                    rows_per_observed_prior_cell=sorted(set(sum(counts.values()) for counts in cells(rows, "AUTH", ("observed", "prior")).values())))
                    for square, rows in sorted(by_square.items())]
    return report


class RecountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = load_candidate()
        cls.report = recount(cls.candidate)

    def test_frozen_panel_counts(self):
        self.assertEqual((len(self.candidate["train"]["AUTH"]), len(self.candidate["train"]["DERANGED"]), len(self.candidate["dev"])), (128, 128, 64))

    def test_visible_projection_excludes_expected_and_hidden_metadata(self):
        case = next(case for case in self.candidate["dev"] if case["operation"] == "REVISE")
        fields = visible(case["context"], "REVISE")
        self.assertNotIn("expected", fields)
        altered = dict(case, id="unread", factors=None, inputs=None, instance_id="unread")
        self.assertEqual(key_for(case, ("square", "observed", "prior")), key_for(altered, ("square", "observed", "prior")))

    def test_ignores_literal_expected_when_it_changes(self):
        for case in self.candidate["dev"]:
            if case["operation"] != "REVISE":
                continue
            original = visible(case["context"], "REVISE")
            changed = re.sub(r"(PRIOR:\s*PREDICT\s+[a-z]+\s*->\s*)([a-z]+)(;)",
                             lambda match: match[1] + ("nup" if match[2] == "fep" else "fep") + match[3], case["context"])
            self.assertEqual(original, visible(changed, "REVISE"))

    def test_actual_public_id_matches_exposed_instance_not_full_hidden_id(self):
        for case in self.candidate["train"]["AUTH"] + self.candidate["dev"]:
            self.assertEqual(visible(case["context"], case["operation"])["instance"], case["instance_id"])
            self.assertNotIn(case["id"], case["context"])

    def test_revise_both_maps_perfect_train_and_dev_ceiling(self):
        for assigned_map in MAPS:
            result = self.report["operations"]["REVISE"]["maps"][assigned_map]["square+observed+prior"]
            self.assertEqual((result["train"]["correct"], result["train"]["cells"]), (64, 32))
            self.assertEqual((result["dev"]["correct"], result["dev"]["cells"]), (32, 32))
            self.assertEqual(result["train"]["cell_shapes"], [dict(rows_per_cell=2, distinct_targets=1, majority_count=2, cells=32)])

    def test_revise_train_only_lookup_perfect_dev_without_dev_fitting(self):
        for assigned_map in MAPS:
            result = self.report["operations"]["REVISE"]["maps"][assigned_map]["square+observed+prior"]["train_only_lookup_dev"]
            self.assertEqual((result["correct"], result["covered"], result["unseen"]), (32, 32, 0))

    def test_literal_id_lookup_does_not_transfer(self):
        result = self.report["operations"]["REVISE"]["maps"]["AUTH"]["instance+observed+prior"]
        self.assertEqual(result["dev"]["ceiling"], 1.)
        self.assertEqual(result["train_only_lookup_dev"]["covered"], 0)
        self.assertIsNone(result["train_only_lookup_dev"]["accuracy_on_covered"])

    def test_compressed_square_bucket_also_transfers(self):
        for assigned_map in MAPS:
            result = self.report["operations"]["REVISE"]["maps"][assigned_map]["square_bucket+observed+prior"]
            self.assertEqual(result["train"]["cells"], 8)
            self.assertEqual(result["dev"]["cells"], 8)
            self.assertEqual(result["train_only_lookup_dev"]["correct"], 32)

    def test_no_id_revise_baseline_is_half(self):
        for assigned_map in MAPS:
            result = self.report["operations"]["REVISE"]["maps"][assigned_map]["observed+prior"]
            self.assertEqual((result["train"]["correct"], result["dev"]["correct"]), (32, 16))

    def test_shortcut_passes_registered_revise_twins(self):
        for assigned_map in MAPS:
            result = self.report["operations"]["REVISE"]["maps"][assigned_map]["square+observed+prior"]["dev_twin_passes"]
            self.assertEqual(result, {family: dict(total=16, both_targets_correct=16) for family in ("outcome", "prior_action")})

    def test_prospect_omitted_factor_ceiling_half(self):
        for assigned_map in MAPS:
            for projection in ("instance+goal", "instance+belief", "square+goal", "square+belief"):
                result = self.report["operations"]["PROSPECT"]["maps"][assigned_map][projection]
                self.assertEqual((result["train"]["ceiling"], result["dev"]["ceiling"]), (.5, .5))

    def test_prospect_valid_card_and_goal_transfers(self):
        for assigned_map in MAPS:
            for projection in ("belief+goal", "belief_dax+goal"):
                result = self.report["operations"]["PROSPECT"]["maps"][assigned_map][projection]
                self.assertEqual(result["train_only_lookup_dev"]["correct"], 32)

    def test_prospect_square_lookup_has_unseen_dev_keys(self):
        result = self.report["operations"]["PROSPECT"]["maps"]["AUTH"]["square+goal"]["train_only_lookup_dev"]
        self.assertEqual((result["correct"], result["covered"], result["unseen"]), (8, 16, 16))

    def test_known_majority_ceiling_not_number_of_keys(self):
        result = ceiling({("one",): Counter({("A", "B", "C"): 3, ("D", "E", "F"): 1})})
        self.assertEqual(result["ceiling"], .75)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    parser.add_argument("--json", action="store_true", help="full cell histograms and train lookup cells to stdout; writes no files")
    parser.add_argument("--self-test", action="store_true", help="run embedded CPU tests on the fixed default candidate")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(RecountTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    report = recount(load_candidate(args.candidate))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0
    print(f"Frozen candidate {PIN}; corpus only; no model outcomes")
    for operation, panels in report["operations"].items():
        for assigned_map, projections in panels["maps"].items():
            print(f"\n{operation} {assigned_map}: projection | train correct/64 cells | dev ceiling correct/32 cells | TRAIN-only dev correct/covered unseen")
            for name, result in projections.items():
                train, dev, lookup = result["train"], result["dev"], result["train_only_lookup_dev"]
                print(f"{name:30} | {train['correct']:2}/64 {train['cells']:2} | {dev['correct']:2}/32 {dev['cells']:2} | {lookup['correct']:2}/{lookup['covered']:2} unseen={lookup['unseen']}")
    print("\nREVISE square cells:")
    print(json.dumps(report["revise_square_cells"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
