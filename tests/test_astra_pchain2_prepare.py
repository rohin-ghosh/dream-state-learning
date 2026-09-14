"""Synthetic CPU-only preparation tests; identifiers are not scientific roots."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import astra_pchain2_prepare as source


def synthetic_chains(offset):
    return tuple(source.Chain(*(f"fixture{offset + 3 * index + position:04d}" for position in range(3)))
                 for index in range(16))


def synthetic_skills():
    junction = tuple(source.Chain(*(f"fixture{1000 + 3 * index + position:04d}" for position in range(3)))
                     for index in range(32))
    return source.build_matched_skills(junction)


def synthetic_tape():
    return tuple(batch.row_ids for batch in source.build_presentation_tape()[:384])


def synthetic_candidates(chains):
    return tuple(tuple(chain.endpoint for chain in chains[start:start + 8])
                 for start in (0, 8) for _ in range(8))


class PChainPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = synthetic_chains(0)
        cls.prompts = synthetic_chains(100)
        cls.permutation = tuple(index ^ 1 for index in range(16))
        cls.junction, cls.local = synthetic_skills()
        cls.batches = synthetic_tape()
        cls.training_inputs = dict(fact_chains=cls.facts, permutation=cls.permutation,
                                   junction_examples=cls.junction, local_examples=cls.local, batches=cls.batches)
        cls.evaluation_inputs = dict(fact_chains=cls.facts, permutation=cls.permutation, prompt_chains=cls.prompts,
                                     fact_candidates=synthetic_candidates(cls.facts),
                                     prompt_candidates=synthetic_candidates(cls.prompts))
        cls.training = source.prepare_training(**cls.training_inputs)
        cls.evaluation = source.prepare_evaluation(**cls.evaluation_inputs)

    def test_exact_protocol_pins_and_fail_closed_drift(self):
        directory = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        successor = (directory / source.SUCCESSOR_FILE).read_bytes()
        original = (directory / source.ORIGINAL_FILE).read_bytes()
        self.assertEqual(source.verify_protocol_bytes(successor, original), source.build_d1_plan()["protocol"])
        for arguments in ((successor + b"\n", original), (successor, original + b"\n")):
            with self.assertRaisesRegex(ValueError, "protocol_hash_mismatch"):
                source.verify_protocol_bytes(*arguments)

    def test_exact_D1_fit_and_readout_budget(self):
        plan = source.build_d1_plan()
        self.assertEqual(plan["budget"], dict(fit_invocations=4, optimizer_updates=1536, presentations=6144,
                                             model_calls=448, generated_tokens_max=83968, external_reader_calls=0))
        self.assertEqual([fit["updates"] for fit in plan["fit_invocations"]], [384] * 4)
        self.assertEqual(Counter(slot.state for slot in source.d1_readout_slots()),
                         Counter(dict(zip(source.STATES, (80, 80, 96, 112, 80)))))
        self.assertEqual(plan["fit_invocations"][-1]["release"], "selected_D1_only")
        self.assertTrue(all(value is False for value in plan["gates"].values()))
        self.assertTrue(all(value == 0 for value in plan["executed"].values()))
        self.assertIsNone(plan["fit_invocations"][0]["recipe"]["optimizer"])
        self.assertEqual(plan["fit_invocations"][0]["recipe"]["learning_rate"], "0")
        self.assertEqual(plan["fit_invocations"][1]["recipe"]["learning_rate"], "0.00003")
        self.assertEqual(len(plan["open_bindings"]), 2)
        self.assertEqual(plan["prospective_bindings"]["material_master"], "ASTRA-PCHAIN2-DEV-20260914-A1")
        self.assertEqual(plan["prospective_bindings"]["presealed_updates"], 768)

    def test_plan_is_fresh_and_CLI_only_prints_symbolic_JSON(self):
        plan = source.build_d1_plan()
        plan["gates"]["GO_GPU"] = True
        plan["fit_invocations"].clear()
        self.assertFalse(source.build_d1_plan()["gates"]["GO_GPU"])
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            source.main(["--plan"])
        self.assertEqual(json.loads(output.getvalue()), source.build_d1_plan())

    def test_all_training_rows_doses_and_loss_roles(self):
        self.assertEqual(tuple(state.name for state in self.training.states), source.STATES[1:])
        for state in self.training.states:
            self.assertEqual(len(state.rows), 64)
            self.assertEqual(len(state.batches), 384)
            self.assertEqual(Counter(row for batch in state.batches for row in batch),
                             Counter({row: 40 if row < 32 else 8 for row in range(64)}))
            for row in state.rows:
                self.assertEqual([message["role"] for message in row.messages()], ["system", "user", "assistant"])
                for message in row.messages():
                    text = message["content"]
                    self.assertTrue(text.endswith("\n"))
                    self.assertFalse(text.endswith("\n\n"))
                    self.assertFalse(text.startswith("\n"))
                    self.assertTrue(all(line == line.rstrip() for line in text.splitlines()))
            self.assertEqual(state.trainer_manifest()["recipe"]["loss"], "assistant_content_plus_terminal_eot")

    def test_exact_atomic_junction_and_local_rendering(self):
        local_state, junction_state = self.training.states[1:3]
        row = junction_state.rows[0]
        self.assertEqual(row.user, "OBSERVED RELATION\nNEXT fixture0000 => fixture0001\nTASK\nStore exactly this one relation.\n")
        self.assertEqual(row.assistant, "MEMORY NEXT fixture0000 => fixture0001\n")
        self.assertEqual(junction_state.rows[32].assistant,
                         "MEMORY NEXT fixture1000 => fixture1001\nMEMORY NEXT fixture1001 => fixture1002\nANSWER fixture1002\n")
        self.assertEqual(local_state.rows[32].assistant,
                         "MEMORY NEXT fixture1001 => fixture1004\nMEMORY NEXT fixture1000 => fixture1002\nANSWER fixture1002\n")
        self.assertIn("Starting at fixture1000, apply NEXT exactly once.\n", local_state.rows[32].user)
        self.assertIn("Starting at fixture1000, apply NEXT exactly twice.\n", junction_state.rows[32].user)
        self.assertEqual(local_state.rows[:32], junction_state.rows[:32])

    def test_deranged_changes_only_second_hop_binding(self):
        authentic, deranged = self.training.states[2:]
        self.assertEqual(authentic.batches, deranged.batches)
        self.assertEqual(authentic.rows[32:], deranged.rows[32:])
        for index, chain in enumerate(self.facts):
            self.assertEqual(authentic.rows[2 * index], deranged.rows[2 * index])
            expected = f"MEMORY NEXT {chain.middle} => {self.facts[self.permutation[index]].endpoint}\n"
            self.assertEqual(deranged.rows[2 * index + 1].assistant, expected)
        for batch in authentic.batches:
            self.assertEqual(Counter(identifier for row in batch for identifier in authentic.rows[row].assistant_identifiers),
                             Counter(identifier for row in batch for identifier in deranged.rows[row].assistant_identifiers))

    def test_primary_skill_target_marginals_match_without_native_claim(self):
        local, junction = self.training.states[1:3]
        self.assertEqual(Counter(identifier for row in local.rows[32:] for identifier in row.assistant_identifiers),
                         Counter(identifier for row in junction.rows[32:] for identifier in row.assistant_identifiers))
        self.assertFalse(local.trainer_manifest()["native_ready"])
        changed = self.local[:-1] + (self.local[0],)
        with self.assertRaisesRegex(ValueError, "bound_matched_local"):
            source.prepare_training(**{**self.training_inputs, "local_examples": changed})

    def test_reject_bad_permutations(self):
        for permutation in (tuple(range(16)), tuple((index + 1) % 8 + index // 8 * 8 for index in range(16)),
                            tuple((index + 8) % 16 for index in range(16)), (True,) + self.permutation[1:]):
            with self.subTest(permutation=permutation), self.assertRaises(ValueError):
                source.prepare_training(**{**self.training_inputs, "permutation": permutation})

    def test_reject_same_batch_paired_atoms(self):
        batches = ((0, 1, 2, 3),) + self.batches[1:]
        with self.assertRaisesRegex(ValueError, "same_or_adjacent_update"):
            source.prepare_training(**{**self.training_inputs, "batches": batches})

    def test_reject_adjacent_update_paired_atoms(self):
        batches = (self.batches[0], self.batches[4]) + self.batches[2:]
        with self.assertRaisesRegex(ValueError, "same_or_adjacent_update"):
            source.prepare_training(**{**self.training_inputs, "batches": batches})

    def test_reject_split_counterfactual_shard(self):
        batches = self.batches[:4] + ((1, 5, 9, 13),) + self.batches[5:]
        with self.assertRaisesRegex(ValueError, "batch_shard"):
            source.prepare_training(**{**self.training_inputs, "batches": batches})

    def test_reject_wrong_tape_counts_length_ids_and_types(self):
        for batches in (self.batches[:-1], self.batches[:-1] + ((32, 33, 34, 35),),
                        ((64, 2, 4, 6),) + self.batches[1:], ((False, 2, 4, 6),) + self.batches[1:]):
            with self.subTest(batches=batches[:1]), self.assertRaises(ValueError):
                source.prepare_training(**{**self.training_inputs, "batches": batches})

    def test_reject_injected_identifiers_and_non_disjoint_skills(self):
        for bad in ("bad\nQUERY", "has space", "<target>", "é", "", "short"):
            facts = (replace(self.facts[0], source=bad),) + self.facts[1:]
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                source.prepare_training(**{**self.training_inputs, "fact_chains": facts})
        for changed in ((self.facts[0],) + self.junction[1:],
                        (replace(self.junction[0], middle=self.junction[0].source),) + self.junction[1:]):
            with self.assertRaises(ValueError):
                source.prepare_training(**{**self.training_inputs, "junction_examples": changed})
        local = (replace(self.local[0], query_source=self.local[0].first_target),) + self.local[1:]
        with self.assertRaisesRegex(ValueError, "must_not_join"):
            source.prepare_training(**{**self.training_inputs, "local_examples": local})

    def test_readout_counts_common_prompts_and_candidate_free_atoms(self):
        calls = self.evaluation.calls
        self.assertEqual(len(calls), 448)
        self.assertEqual(sum(call.user is None for call in calls), 48)
        base = [call for call in calls if call.slot.state == "BASE"]
        lr0 = [call for call in calls if call.slot.state == "LR0"]
        self.assertEqual([call.actor_messages() for call in base], [call.actor_messages() for call in lr0])
        one_hop = [call for call in base if call.slot.panel == "one_hop"]
        self.assertEqual(one_hop[0].user,
                         "QUERY\nRecall NEXT for fixture0000.\nOUTPUT\nReturn exactly one MEMORY line.\n")
        self.assertEqual(one_hop[16].expected, b"MEMORY NEXT fixture0001 => fixture0002\n")
        self.assertTrue(all("CANDIDATES" not in call.user for call in one_hop))
        for call in calls:
            if call.user is not None:
                self.assertEqual(len(call.actor_messages()), 2)
                self.assertNotIn(call.slot.state, call.user)

    def test_same_prompt_counterfactual_redirection_and_direct_format(self):
        index = {(call.slot.state, call.slot.panel, call.slot.index): call for call in self.evaluation.calls}
        for ordinal in range(16):
            for panel in ("eval_trace", "eval_direct"):
                authentic = index["ATOM-JUNCTION", panel, ordinal]
                deranged = index["DERANGED-JUNCTION", panel, ordinal]
                self.assertEqual(authentic.user, deranged.user)
                self.assertNotEqual(authentic.expected, deranged.expected)
                self.assertTrue(deranged.expected.endswith(f"ANSWER {self.facts[self.permutation[ordinal]].endpoint}\n".encode()))
                if panel == "eval_trace":
                    self.assertEqual(authentic.expected.splitlines()[0], deranged.expected.splitlines()[0])
                else:
                    self.assertEqual(len(authentic.expected.splitlines()), 1)
        self.assertTrue(index["BASE", "prompt_trace", 0].user.startswith("AVAILABLE RELATIONS\nNEXT fixture0100"))
        self.assertTrue(index["BASE", "prompt_empty", 0].user.startswith("AVAILABLE RELATIONS\nNONE\nQUERY\n"))

    def test_reject_bad_candidate_membership_duplicates_or_balance(self):
        orders = self.evaluation_inputs["fact_candidates"]
        bad = (self.facts[0].middle,) + orders[0][1:]
        rotated = (orders[1][1], orders[1][0]) + orders[1][2:]
        for changed in ((bad,) + orders[1:], ((orders[0][0],) * 8,) + orders[1:],
                        orders[:1] + (rotated,) + orders[2:]):
            with self.assertRaises(ValueError):
                source.prepare_evaluation(**{**self.evaluation_inputs, "fact_candidates": changed})

    def test_separate_trainer_projection_and_unresolved_canaries(self):
        receipt = source.check_cross_corpus(self.training, self.evaluation)
        self.assertEqual(receipt["unbound_canary_calls"], 48)
        self.assertFalse(receipt["native_ready"])
        for state in self.training.states:
            manifest = state.trainer_manifest()
            self.assertEqual(set(manifest), {"status", "state", "dose", "recipe", "rows", "batches",
                                             "dropout_seeds", "learner_seed", "native_ready"})
            raw = source.canonical_json(manifest)
            for forbidden in ("ENDPOINT CANDIDATES", "fact_binding_sha256", "evaluation", "expected", "score"):
                self.assertNotIn(forbidden.encode(), raw)
            self.assertTrue(all(identifier.encode() not in raw for identifier in self.evaluation.prompt_identifiers))
        canary = next(call for call in self.evaluation.calls if call.slot.panel == "canary")
        with self.assertRaisesRegex(ValueError, "unbound_canary"):
            canary.actor_messages()
        with self.assertRaisesRegex(ValueError, "bound_readout"):
            source.strict_match(canary, b"anything", terminal=True, truncated=False)

    def test_cross_corpus_rejects_mismatched_facts_and_prompt_skill_overlap(self):
        with self.assertRaisesRegex(ValueError, "fact_bindings_differ"):
            source.check_cross_corpus(replace(self.training, fact_binding_sha256="0" * 64), self.evaluation)
        with self.assertRaisesRegex(ValueError, "prompt_identifiers_in_training"):
            source.check_cross_corpus(replace(self.training, skill_identifiers=self.evaluation.prompt_identifiers), self.evaluation)

    def test_strict_bytes_do_not_accept_nonterminal_or_repair(self):
        call = next(call for call in self.evaluation.calls if call.slot.panel == "eval_trace")
        self.assertTrue(source.strict_match(call, call.expected, terminal=True, truncated=False))
        for raw in (None, call.expected.decode(), call.expected.rstrip(), b" " + call.expected,
                    call.expected + b"\n", call.expected.replace(b"\n", b"\r\n"), b"```\n" + call.expected):
            self.assertFalse(source.strict_match(call, raw, terminal=True, truncated=False))
        self.assertFalse(source.strict_match(call, call.expected, terminal=False, truncated=False))
        self.assertFalse(source.strict_match(call, call.expected, terminal=True, truncated=True))

    def test_bound_constructor_matches_explicit_inputs(self):
        prepared = source.prepare_training(fact_chains=self.facts, junction_examples=self.junction)
        self.assertEqual(prepared, self.training)
        for state in prepared.states:
            self.assertEqual(len(state.dropout_seeds), 384)
            self.assertEqual(state.dropout_seeds, prepared.states[0].dropout_seeds)
            self.assertEqual(state.trainer_manifest()["learner_seed"], 0)

    def test_matched_skill_pairs_and_full_identifier_role_marginals(self):
        junction, local = source.build_matched_skills(self.junction)
        self.assertIs(junction, self.junction)
        for index, (chain, example) in enumerate(zip(junction, local)):
            self.assertEqual(example.identifiers, (chain.middle, junction[index ^ 1].middle,
                                                   chain.source, chain.endpoint))
            self.assertEqual(len(set(example.identifiers)), 4)
        local_state, junction_state = self.training.states[1:3]
        for attribute, expected in (("assistant", (1, 2, 2)), ("user", (2, 2, 1))):
            for state in (local_state, junction_state):
                corpus = "".join(getattr(row, attribute) for row in state.rows[32:])
                for chain in junction:
                    self.assertEqual(tuple(corpus.count(identifier) for identifier in chain.identifiers), expected)
        for state in (local_state, junction_state):
            corpus = "".join(row.user + row.assistant for row in state.rows[32:])
            for chain in junction:
                self.assertEqual(tuple(corpus.count(identifier) for identifier in chain.identifiers), (3, 4, 3))

    def test_bound_skill_constructor_rejects_duplicate_or_short_rosters(self):
        for junction in (self.junction[:-1], (self.junction[1],) + self.junction[1:]):
            with self.assertRaises(ValueError):
                source.build_matched_skills(junction)

    def test_every_round_order_skill_insertion_and_stage_counts(self):
        tape = source.build_presentation_tape()
        self.assertEqual(len(tape), 768)
        self.assertEqual(tuple(batch.update_number for batch in tape), tuple(range(1, 769)))
        self.assertEqual(tuple(batch.row_ids for batch in tape[:384]), tuple(batch.row_ids for batch in tape[384:]))
        for round_number in range(1, 81):
            within_stage = (round_number - 1) % 40 + 1
            batches = [batch for batch in tape if batch.round_number == round_number]
            self.assertEqual(len(batches), 16 if within_stage % 5 == 0 else 8)
            first_groups = (1, 0, 3, 2) if within_stage > 30 else (0, 1, 2, 3)
            second_groups = (1, 0, 3, 2) if 21 <= within_stage <= 30 else (0, 1, 2, 3)
            self.assertEqual(tuple(batch.row_ids for batch in batches[:4]),
                             tuple(tuple(8 * group + 2 * offset for offset in range(4)) for group in first_groups))
            self.assertEqual(tuple(batch.row_ids for batch in batches[4:8]),
                             tuple(tuple(8 * group + 2 * offset + 1 for offset in range(4)) for group in second_groups))
            if within_stage % 5 == 0:
                self.assertEqual(tuple(batch.row_ids for batch in batches[8:]),
                                 tuple(tuple(range(start, start + 4)) for start in range(32, 64, 4)))
        for stage in ("D1", "D2"):
            selected = [batch for batch in tape if batch.stage == stage]
            self.assertEqual(len(selected), 384)
            self.assertEqual(Counter(row for batch in selected for row in batch.row_ids),
                             Counter({row: 40 if row < 32 else 8 for row in range(64)}))

    def test_each_chain_has_exact_10_20_10_lags_and_never_adjacent(self):
        tape = source.build_presentation_tape()
        for stage in ("D1", "D2"):
            selected = [batch for batch in tape if batch.stage == stage]
            for chain in range(16):
                first = {batch.round_number: batch.update_number for batch in selected if 2 * chain in batch.row_ids}
                second = {batch.round_number: batch.update_number for batch in selected if 2 * chain + 1 in batch.row_ids}
                self.assertEqual(Counter(second[round_number] - first[round_number] for round_number in first),
                                 Counter({3: 10, 4: 20, 5: 10}))
        previous = set()
        for batch in tape:
            for row in batch.row_ids:
                if row < 32:
                    self.assertNotIn(row ^ 1, batch.row_ids)
                    self.assertNotIn(row ^ 1, previous)
            previous = set(batch.row_ids)

    def test_dropout_preimages_and_distinct_D2_seeds(self):
        tape = source.build_presentation_tape()
        self.assertEqual(len({batch.dropout_seed for batch in tape}), 768)
        self.assertTrue(set(batch.dropout_seed for batch in tape[:384]).isdisjoint(
            batch.dropout_seed for batch in tape[384:]))
        for batch in tape:
            expected = int.from_bytes(sha256(b"ASTRA-PCHAIN2-DEV-20260914-A1\0dropout\0"
                                             + batch.update_number.to_bytes(4, "big")).digest()[-8:], "big")
            self.assertEqual(batch.dropout_seed, expected)
        self.assertEqual(source.presentation_tape_sha256(tape), source.presentation_tape_sha256(source.build_presentation_tape()))
        for update in (0, 769, True):
            with self.assertRaises(ValueError):
                source.dropout_seed(update)
        with self.assertRaisesRegex(ValueError, "bound_material_master"):
            source.build_presentation_tape(master=b"different-root")

    def test_legacy_order_and_other_valid_transpositions_are_rejected(self):
        batches = list(self.batches)
        batches[0], batches[1] = batches[1], batches[0]
        with self.assertRaisesRegex(ValueError, "bound_D1_presentation_order"):
            source.prepare_training(**{**self.training_inputs, "batches": tuple(batches)})
        with self.assertRaisesRegex(ValueError, "bound_xor_one_permutation"):
            source.prepare_training(**{**self.training_inputs, "permutation": tuple(index ^ 2 for index in range(16))})


if __name__ == "__main__":
    unittest.main()
