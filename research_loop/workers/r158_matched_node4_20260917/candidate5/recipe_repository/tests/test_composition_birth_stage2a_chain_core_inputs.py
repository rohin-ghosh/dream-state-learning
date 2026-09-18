"""Complete held-chain source checks, without birth separation or native calls."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import unittest

from organism_v6 import composition_birth_stage2a_chain_core_inputs as source
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_held as held
from tests.test_composition_birth_stage2a_held import fixtures


class ChainCoreInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokens = fixtures("dose_chain")
        cls.chains = {world: held.build_chain_world(world=world, role_tokens=tokens)
                      for world, tokens in cls.tokens.items()}

    def test_binding_is_prospectively_pinned(self):
        self.assertEqual(sha256((Path(__file__).resolve().parents[1] / source.BINDING_PATH).read_bytes()).hexdigest(),
                         source.BINDING_SHA256)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_all_32_complete_chains_and_every_witness_boundary(self):
        members = set()
        for world, chain in self.chains.items():
            result = source.build_chain_core_inputs(chain_world=chain, role_tokens=self.tokens[world])
            self.assertFalse(result.native_ready)
            self.assertFalse(result.held_birth_separation_checked)
            self.assertEqual(len(result.boundaries), sum(len(member.expected_trace) for member in chain.members))
            for boundary in result.boundaries:
                with self.subTest(world=world, member=boundary.member, decision=boundary.decision_index):
                    member = chain.members[int(boundary.member[1:])]
                    members.add((world, boundary.member))
                    core = json.loads(boundary.core_bytes)
                    envelope = json.loads(boundary.checker_payload)
                    binding = json.loads(boundary.binding_receipt_bytes)
                    witness = member.expected_trace
                    prior_steps = [turn for turn in witness[:boundary.decision_index]
                                   if turn.action.startswith("STEP ")]
                    self.assertEqual(core["actual_route_depth"], 2)
                    self.assertEqual(envelope["step_outcome_observed"], bool(prior_steps))
                    self.assertEqual(boundary.target_bytes, witness[boundary.decision_index].action.encode("ascii"))
                    self.assertEqual(core["goal_side"], ("LEFT", "RIGHT")[int(member.member[1:])])
                    self.assertEqual(core["terminal_class"], "REACHED" if boundary.target_bytes == b"STOP" else "UNRESOLVED")
                    self.assertEqual(boundary.signature_bytes, graph.signature_bytes(envelope["world_graph"]))
                    self.assertEqual(boundary.signature_sha256, graph.signature_hash(envelope["world_graph"]))
                    self.assertEqual(json.loads(boundary.receipt_bytes), checker.check_graph_core_json(boundary.checker_payload))
                    self.assertEqual(binding["source_sha256"], sha256(result.source_bytes).hexdigest())
                    self.assertEqual(binding["prefix_sha256"], sha256(boundary.prefix_bytes).hexdigest())
                    self.assertEqual(binding["target_sha256"], sha256(boundary.target_bytes).hexdigest())
                    if not prior_steps:
                        self.assertIsNone(core["predicted_actual_match"])
                    elif len(prior_steps) == 1:
                        self.assertEqual(core["predicted_actual_match"], not chain.mismatch)
                    else:
                        self.assertIs(core["predicted_actual_match"], True)
        self.assertEqual(len(members), 32)

    def test_modified_witness_response_and_target_rejected(self):
        chain = self.chains["h00"]
        member = chain.members[0]
        for changed in (replace(member.expected_trace[0], response="SERVICE\nMISS"),
                        replace(member.expected_trace[0], action="STOP")):
            bad_member = replace(member, expected_trace=(changed,) + member.expected_trace[1:])
            with self.assertRaisesRegex(source.ChainCoreInputError, "exact_constructor_chain_mismatch"):
                source.build_chain_core_inputs(chain_world=replace(chain, members=(bad_member, chain.members[1])),
                                               role_tokens=self.tokens["h00"])

    def test_foreign_roles_and_missing_edges_rejected(self):
        chain = self.chains["h00"]
        with self.assertRaises(source.ChainCoreInputError):
            source.build_chain_core_inputs(chain_world=chain, role_tokens=self.tokens["h01"])
        edges = dict(chain.world_edges)
        edges.pop(next(iter(edges)))
        with self.assertRaisesRegex(source.ChainCoreInputError, "exact_constructor_chain_mismatch"):
            source.build_chain_core_inputs(chain_world=replace(chain, construction=replace(chain.construction, world_edges=edges)),
                                           role_tokens=self.tokens["h00"])

    def test_replay_rejects_false_reached_witness(self):
        chain = self.chains["h00"]
        member = chain.members[0]
        with self.assertRaises(source.ChainCoreInputError):
            source._replay(chain, replace(member, expected_trace=member.expected_trace[:3]))

    def test_replay_rejects_unowned_think_and_wrong_destination(self):
        chain = self.chains["h04"]
        member = chain.members[0]
        for index, changed in ((3, replace(member.expected_trace[3], action="THINK KEEP " + "M2AE_AAAAAAAAAAAA")),
                               (2, replace(member.expected_trace[2], current_after=member.task.goal))):
            trace = list(member.expected_trace)
            trace[index] = changed
            with self.assertRaises(source.ChainCoreInputError):
                source._replay(chain, replace(member, expected_trace=tuple(trace)))


if __name__ == "__main__":
    unittest.main()
