"""CPU synthetic spans only; not actual child generations or execution proof."""

import copy
import importlib.util
from pathlib import Path
import unittest

from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_formation_plan as planner
from organism_v6 import pcfl_vertical_prepare as prepare


def choices(cell, first_left=None, first_right="f0", reverse_links=False):
    root = cell.root
    first_left = f"a{cell.old}" if first_left is None else first_left
    second_left = "a1" if first_left == "a0" else "a0"
    second_right = "f1" if first_right == "f0" else "f0"
    ports = [first_left, "b", "c", "d", first_right, "u", second_left, second_right]
    actions = [f"EXPLORE {root.lookup('node', source)} {root.lookup('port', port)}"
               for source, port in zip(core.OLD_SOURCES, ports)]
    left_index = 0 if first_left == f"a{cell.old}" else 6
    pairs = [(left_index, 1), (1, 2), (3, 4), (3, 7)]
    if reverse_links:
        pairs.reverse()
    links = [[root.lookup("event", f"e{index}") for index in pair] for pair in pairs]
    return actions, links


def synthetic_child_spans(cell, actions, links):
    """Make test-only spans independently from actual public CPU receipts."""
    session = core.WorldSession(cell, "OLD")
    fields_by_handle, event_raw, link_raw = {}, [], []
    for index, action in enumerate(actions):
        result = session.explore(action)
        if not result["ok"]:
            raise AssertionError(result)
        receipt = result["receipt"]
        fields = {"event": cell.root.lookup("event", f"e{index}"),
                  **{key: receipt[key] for key in ("source", "port", "destination", "receipt")}}
        fields_by_handle[fields["event"]] = fields
        event_raw.append(core.EVENT_WIRE.format(**fields))
    for index, pair in enumerate(links):
        first, second = (fields_by_handle[handle] for handle in pair)
        fields = {"link": cell.root.lookup("link", f"l{index}"), "first": first["event"],
                  "second": second["event"], "via": first["destination"],
                  "receipt_first": first["receipt"], "receipt_second": second["receipt"]}
        link_raw.append(core.LINK_WIRE.format(**fields))
    return event_raw, link_raw


def synthetic_contract(plan):
    fixture_path = Path(__file__).with_name("test_pcfl_vertical_prepare.py")
    spec = importlib.util.spec_from_file_location("formation_prepare_test_fixture", fixture_path)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    bindings = fixtures.synthetic_bindings()
    corpus = bindings["slot_registry"][0]
    first = planner.first_block_slots(plan, plan["plan_sha256"])
    replay = [{**copy.deepcopy(first[0]), "id": f"s{index:02}", "source": first[0]["id"]}
              for index in range(17, 20)]
    corpus["slots"] = first + replay
    fixtures._synthetic_replays(bindings)
    fixtures._synthetic_batches(bindings)
    return prepare.build_execution_contract(bindings, fixtures.synthetic_tokenizer(bindings)), corpus["id"]


class FormationPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell = core.WorldCell(core.build_root("disposable/0"), 0, 0, 0)
        cls.actions, cls.links = choices(cls.cell)
        cls.plan = planner.build_plan(cls.cell, cls.actions, cls.links)
        cls.seal = cls.plan["plan_sha256"]
        cls.event_raw, cls.link_raw = synthetic_child_spans(cls.cell, cls.actions, cls.links)
        cls.contract, cls.corpus_id = synthetic_contract(cls.plan)

    def bind(self, **overrides):
        arguments = {"plan": self.plan, "preoutput_sha256": self.seal, "actions": self.actions,
                     "event_raw": self.event_raw, "link_raw": self.link_raw,
                     "contract": self.contract, "corpus_id": self.corpus_id}
        arguments.update(overrides)
        return planner.bind_child(**arguments)

    def test_real_old_chronology_not_ideal_edge_numbering(self):
        root = self.cell.root
        bank = self.plan["expected_bank"]
        self.assertEqual(self.plan["old_sources"], ["S_L", "A", "H", "S_R", "B", "Z", "S_L", "B"])
        fifth = bank[root.lookup("event", "e5")]
        seventh = bank[root.lookup("event", "e7")]
        self.assertEqual([fifth[key] for key in ("source", "port", "destination", "receipt")],
                         [root.lookup("node", "Z"), root.lookup("port", "u"),
                          root.lookup("node", "Y"), root.lookup("receipt", "r5")])
        self.assertEqual([seventh[key] for key in ("source", "port", "destination", "receipt")],
                         [root.lookup("node", "B"), root.lookup("port", "f1"),
                          root.lookup("node", "G_R1"), root.lookup("receipt", "r7")])
        self.assertNotEqual(fifth["source"], self.cell.edges[5].source)
        self.assertNotEqual(seventh["source"], self.cell.edges[7].source)
        self.assertEqual(bank[root.lookup("link", "l3")]["second"], root.lookup("event", "e7"))

    def test_free_alternate_actions_and_link_order(self):
        for old_bit in (0, 1):
            cell = core.WorldCell(core.build_root("dev/1"), old_bit, 1, 1)
            actions, links = choices(cell, f"a{1-old_bit}", "f1", True)
            plan = planner.build_plan(cell, actions, links)
            event_raw, link_raw = synthetic_child_spans(cell, actions, links)
            bound = planner.bind_child(plan, plan["plan_sha256"], actions, event_raw, link_raw)
            self.assertTrue(bound["formation"]["formation_complete"])
            self.assertEqual(plan["expected_bank"][cell.root.lookup("event", "e7")]["port"],
                             cell.root.lookup("port", "f0"))
            self.assertEqual(plan["links"][-1]["events"][0], cell.root.lookup("event", "e6"))

    def test_deterministic_seal_and_no_target_material(self):
        self.assertEqual(self.plan, planner.build_plan(self.cell, self.actions, self.links))
        self.assertTrue(planner.validate_plan(self.plan, self.seal))
        text = core.canonical(self.plan)
        for forbidden in ('"target":', '"raw":', '"training":', '"target_sha256":'):
            self.assertNotIn(forbidden, text)
        self.assertEqual(self.plan["purpose"], planner.PURPOSE)
        self.assertEqual(set(self.plan["source_pins"]), {"planner", "core", "preparer"})
        self.assertFalse(self.plan["execution_contract_valid"])

    def test_seal_changes_for_caller_choices(self):
        changed = planner.build_plan(self.cell, self.actions, list(reversed(self.links)))
        self.assertNotEqual(changed["plan_sha256"], self.seal)
        with self.assertRaisesRegex(ValueError, "seal mismatch"):
            planner.validate_plan(changed, self.seal)

    def test_resealed_field_or_source_mutation_rejected(self):
        for field in ("expected_bank", "source_pins"):
            plan = copy.deepcopy(self.plan)
            if field == "source_pins":
                plan[field]["core"] = "0" * 64
            else:
                plan[field][self.cell.root.lookup("event", "e5")]["port"] = self.cell.root.lookup("port", "f1")
            plan["plan_sha256"] = core.digest({key: value for key, value in plan.items() if key != "plan_sha256"})
            with self.assertRaisesRegex(ValueError, "source/expected structure mismatch"):
                planner.validate_plan(plan, plan["plan_sha256"])

    def test_first_blocks_are_detached_preparer_skeleton_only(self):
        slots = planner.first_block_slots(self.plan, self.seal)
        self.assertEqual(len(slots), 17)
        self.assertEqual(sum(slot["row_type"] == "EVENT" for slot in slots), 14)
        self.assertTrue(all(set(slot) == set(prepare.SLOT_FIELDS) and slot["source"] is None for slot in slots))
        self.assertTrue(all(slot["support"] == sorted(slot["support"]) for slot in slots))
        slots[0]["bank"].clear()
        self.assertTrue(self.plan["first_blocks"][0]["bank"])

    def test_actual_bytes_bind_via_real_admission_and_preparer(self):
        before = prepare.canonical([self.plan, self.contract, self.actions, self.event_raw, self.link_raw])
        bound = self.bind()
        self.assertTrue(bound["formation"]["formation_complete"])
        self.assertTrue(bound["preparer_binding"]["formation_binding_valid"])
        self.assertFalse(bound["native_custody_verified"])
        self.assertEqual([row["raw"] for row in bound["rows"]], self.event_raw + self.link_raw)
        self.assertEqual(bound["queries"], core.materialize_queries(bound["rows"]))
        self.assertEqual(before, prepare.canonical([self.plan, self.contract, self.actions, self.event_raw, self.link_raw]))

    def test_missing_extra_and_nonstring_spans_fail_without_repair(self):
        for field, original in (("event_raw", self.event_raw), ("link_raw", self.link_raw)):
            for invalid in (original[:-1], original + [original[0]], [False] + original[1:]):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    self.bind(**{field: invalid})

    def test_ideal_numbered_fields_and_fenced_child_fail(self):
        for index in (5, 7):
            spans = self.event_raw[:]
            edge = self.cell.edges[index]
            spans[index] = core.EVENT_WIRE.format(event=edge.event, source=edge.source, port=edge.port,
                                                 destination=edge.destination, receipt=edge.receipt)
            with self.assertRaisesRegex(ValueError, "not exact own executed receipt"):
                self.bind(event_raw=spans)
        for field, spans in (("event_raw", self.event_raw), ("link_raw", self.link_raw)):
            changed = ["```\n" + spans[0] + "```\n"] + spans[1:]
            with self.assertRaises(ValueError):
                self.bind(**{field: changed})

    def test_actual_action_and_link_choice_cannot_be_remapped(self):
        actions = self.actions[:]
        actions[0] += "\n"
        with self.assertRaisesRegex(ValueError, "actual actions differ"):
            self.bind(actions=actions)
        changed = self.link_raw[:]
        changed[0], changed[1] = changed[1], changed[0]
        with self.assertRaises(ValueError):
            self.bind(link_raw=changed)

    def test_invalid_predeclared_choices_rejected(self):
        for actions, links in ((self.actions[:-1], self.links),
                               (self.actions, self.links[:3]),
                               (self.actions, [self.links[0]] * 4),
                               (self.actions, [["e0", "e1"]] + self.links[1:]),
                               (self.actions, [list(reversed(self.links[0]))] + self.links[1:])):
            with self.subTest(actions=actions, links=links), self.assertRaises(ValueError):
                planner.build_plan(self.cell, actions, links)
        actions = self.actions[:]
        actions[7] = actions[4]
        with self.assertRaisesRegex(ValueError, "previously tried"):
            planner.build_plan(self.cell, actions, self.links)

    def test_real_preparer_rejects_missing_extra_and_incorrect_bank(self):
        bound = self.bind()
        queries, rows = bound["queries"], bound["rows"]
        missing_queries = copy.deepcopy(queries)
        missing_queries.pop(next(iter(missing_queries)))
        extra_queries = copy.deepcopy(queries)
        extra_queries["READ EVENT extra"] = next(iter(queries.values()))
        wrong_rows = copy.deepcopy(rows)
        wrong_rows[5]["fields"]["destination"] = self.cell.root.lookup("node", "G_R1")
        wrong_rows[5]["raw"] = core.EVENT_WIRE.format(**wrong_rows[5]["fields"])
        wrong_rows[5]["sha256"] = core.byte_hash(wrong_rows[5]["raw"])
        for bad_queries, bad_rows in ((missing_queries, rows), (extra_queries, rows),
                                      (queries, rows[:-1]), (queries, rows + [rows[0]]),
                                      (core.materialize_queries(wrong_rows), wrong_rows)):
            with self.subTest(count=len(bad_rows)), self.assertRaisesRegex(
                    prepare.ExecutionContractError, "VS_FORMATION_BANK_MISMATCH"):
                prepare.validate_formation_binding(self.contract, self.corpus_id, bad_queries, bad_rows)

    def test_unbound_or_different_contract_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError, "paired"):
            self.bind(corpus_id=None)
        with self.assertRaisesRegex(ValueError, "first blocks differ"):
            self.bind(corpus_id="dev/0/S1_AUTH")
        self.assertEqual(self.plan["stage"], "OLD")
        self.assertTrue(all(item["expected_receipt"]["kind"] == "EXPLORE"
                            and item["expected_receipt"]["fixture_only"] is False
                            for item in self.plan["opportunities"]))


if __name__ == "__main__":
    unittest.main()
