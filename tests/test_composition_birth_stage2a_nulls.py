"""Synthetic bytes only: no material generator, model, or held-run evidence."""

from hashlib import sha256
from itertools import combinations
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_nulls as nulls


def token(kind, serial):
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    return f"M2A{kind}_" + "B" * 10 + alphabet[serial // 32] + alphabet[serial % 32]


START = token("N", 1)
GOAL = token("N", 2)
CURRENT = token("N", 3)
OTHER = token("N", 4)
QUERIES = tuple(token("Q", serial) for serial in range(55, 31, -1))
PORTS = tuple(token("P", serial) for serial in (44, 12, 33, 7))
EVENTS = tuple(token("E", serial) for serial in range(20, 24))
RECOVER = tuple(token("Q", serial) for serial in range(100, 104))
GOT = tuple(token("N", serial) for serial in range(70, 74))
PAIR_NAMES = nulls.PairNameBinding(tuple(name.encode("ascii") for name in nulls.NULL_NAMES))


def message(role, content):
    return nulls.PublicMessage(role, content.encode("ascii") if type(content) is str else content)


def initial(*, current=CURRENT, goal=GOAL):
    return (message("system", wire.SYSTEM_MESSAGE),
            message("user", f"TASK\nSTART {START}\nGOAL {goal}\nCURRENT {current}"))


def routes(skin=0, *, queries=QUERIES, current=CURRENT, goal=GOAL):
    rows = []
    for index, query in enumerate(queries):
        route = token("I", index)
        fields = (f"AT {current} FOR {goal} QUERY {query}" if skin == 0
                  else f"FOR {goal} QUERY {query} AT {current}")
        rows.append(f"ROUTE {route} {fields}")
    return "ROUTES\n" + "\n".join(rows)


def events(skin=0, *, ports=PORTS, current=CURRENT, goal=GOAL, relevant=2, got=GOT):
    rows = []
    for index, port in enumerate(ports):
        row_goal = goal if index == relevant else OTHER
        fields = (f"AT {current} FOR {row_goal} DID {port} GOT {got[index]}" if skin == 0
                  else f"FOR {row_goal} AT {current} GOT {got[index]} DID {port}")
        rows.append(f"EVENT {EVENTS[index]} {fields} RECOVER {RECOVER[index]} "
                    f"EVIDENCE {token('R', index)}")
    return "EVENTS\n" + "\n".join(rows)


def turn(prefix, action, response):
    return prefix + (message("assistant", action), message("user", response))


def panel_prefix(phase, skin=0):
    prefix = initial()
    if phase == "SEEK":
        return turn(prefix, f"READ INDEX {CURRENT}", "SERVICE\n" + routes(skin))
    if phase in ("PROSPECT", "CHECK"):
        prefix = turn(prefix, f"READ RELATION {QUERIES[0]}", "SERVICE\n" + events(skin))
    if phase == "CHECK":
        prefix = turn(prefix, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {GOT[2]}")
    return prefix


def expected_candidates(phase):
    if phase == "SEEK":
        actions = tuple(f"READ RELATION {query}".encode("ascii") for query in QUERIES)
    elif phase == "PROSPECT":
        actions = tuple(f"STEP {port}".encode("ascii") for port in PORTS)
    elif phase == "CHECK":
        actions = tuple(f"THINK {verb} {EVENTS[2]}".encode("ascii") for verb in ("KEEP", "REVISE"))
    else:
        actions = (b"STOP", f"READ INDEX {CURRENT}".encode("ascii"))
    sentinel = {
        "SEEK": b"READ RELATION M2AQ_AAAAAAAAAAAA",
        "PROSPECT": b"STEP M2AP_AAAAAAAAAAAA",
        "CHECK": b"THINK KEEP M2AE_AAAAAAAAAAAA",
        "CONTINUE": b"READ INDEX M2AN_AAAAAAAAAAAA",
    }[phase]
    return actions + (sentinel,)


def reference_rank(index, candidates, goal, current):
    if index == 0:
        return candidates[-1:] + candidates[:-1]
    if index == 1:
        return candidates
    if index == 2:
        return candidates[-2::-1] + candidates[-1:]
    if index in (3, 4):
        return tuple(sorted(candidates, reverse=index == 4))
    if index == 5:
        return tuple(sorted(candidates, key=lambda action: (len(action), action)))
    if index in (6, 7):
        public_node = goal if index == 6 else current
        return tuple(sorted(candidates, key=lambda action: sha256(public_node + b"\0" + action).digest()))
    def columns(action):
        operand = b"" if action == b"STOP" else action.split(b" ")[-1]
        return tuple(operand[position] if len(operand) > position else 0 for position in (0, 5)) + (
            operand[-1] if operand else 0, action)
    return tuple(sorted(candidates, key=columns))


class PublicRankingTests(unittest.TestCase):
    def test_exact_nine_names_and_36_unordered_pairs(self):
        self.assertEqual(nulls.NULL_NAMES, (
            "sentinel_first", "display_first", "display_last", "lexical_first",
            "lexical_last", "shortest_first", "goal_digest", "current_digest", "character_columns"))
        self.assertEqual(nulls.NULL_PAIRS, tuple(combinations(nulls.NULL_NAMES, 2)))
        self.assertEqual(len(nulls.NULL_PAIRS), 36)

    def test_all_rankings_exact_and_total_in_every_phase_and_skin(self):
        for phase in ("SEEK", "PROSPECT", "CHECK", "CONTINUE"):
            for skin in (0, 1):
                prefix = panel_prefix(phase, skin)
                panel = nulls.public_candidates(prefix, phase=phase, skin=skin)
                candidates = expected_candidates(phase)
                self.assertEqual(panel.candidates, candidates)
                self.assertEqual(panel.current, (GOT[2] if phase == "CHECK" else CURRENT).encode("ascii"))
                for index, name in enumerate(nulls.NULL_NAMES):
                    with self.subTest(phase=phase, skin=skin, name=name):
                        ranking = nulls.rank_null(name, prefix, phase=phase, skin=skin)
                        expected = reference_rank(index, candidates, GOAL.encode("ascii"), panel.current)
                        self.assertEqual(ranking, expected)
                        self.assertEqual(set(ranking), set(candidates))
                        self.assertEqual(len(ranking), len(set(ranking)))
                        self.assertEqual(ranking.count(nulls.SENTINELS[phase]), 1)
                        for action in ranking:
                            wire.parse_action(action.decode("ascii"))

    def test_every_pair_uses_exact_sum_max_digest_and_is_order_independent(self):
        for phase in ("SEEK", "PROSPECT", "CHECK", "CONTINUE"):
            for skin in (0, 1):
                prefix = panel_prefix(phase, skin)
                candidates = expected_candidates(phase)
                current = (GOT[2] if phase == "CHECK" else CURRENT).encode("ascii")
                for index_a, index_b in combinations(range(9), 2):
                    name_a, name_b = nulls.NULL_NAMES[index_a], nulls.NULL_NAMES[index_b]
                    ranks_a = {action: rank for rank, action in enumerate(reference_rank(
                        index_a, candidates, GOAL.encode("ascii"), current))}
                    ranks_b = {action: rank for rank, action in enumerate(reference_rank(
                        index_b, candidates, GOAL.encode("ascii"), current))}
                    def key(action):
                        raw = b"NPAIR\0" + name_a.encode("ascii") + b"\0" + name_b.encode("ascii") + b"\0" + action
                        return (ranks_a[action] + ranks_b[action],
                                max(ranks_a[action], ranks_b[action]), sha256(raw).digest())
                    expected = tuple(sorted(candidates, key=key))
                    forward = nulls.rank_pair(name_a, name_b, prefix, phase=phase, skin=skin, pair_names=PAIR_NAMES)
                    reverse = nulls.rank_pair(name_b, name_a, prefix, phase=phase, skin=skin, pair_names=PAIR_NAMES)
                    self.assertEqual(forward, expected)
                    self.assertEqual(reverse, expected)
                    self.assertEqual(nulls.rank_pair(name_a, name_b, prefix, phase=phase, skin=skin), expected)
                    self.assertEqual(nulls.rank_pair(name_b, name_a, prefix, phase=phase, skin=skin), expected)
                    for action in candidates:
                        raw = b"NPAIR\0" + name_a.encode("ascii") + b"\0" + name_b.encode("ascii") + b"\0" + action
                        self.assertEqual(nulls.pair_tie_preimage(name_a, name_b, action), raw)
                        self.assertEqual(nulls.pair_tie_preimage(name_b, name_a, action), raw)

    def test_pair_preimage_exact_nul_name_order_no_master_or_final_separator(self):
        action = b"STOP"
        actual = nulls.pair_tie_preimage("display_last", "sentinel_first", action, pair_names=PAIR_NAMES)
        self.assertEqual(actual, b"NPAIR\0sentinel_first\0display_last\0STOP")
        self.assertEqual(nulls.pair_tie_preimage("display_last", "sentinel_first", action), actual)
        with self.assertRaises(TypeError):
            nulls.pair_tie_preimage("display_last", "sentinel_first", action,
                                    pair_names=PAIR_NAMES, master=b"synthetic-only")

    def test_null_clarification_pin_and_canonical_default(self):
        expected = "c24451dd86493537d5e152a9560d7cb8c7cc331d3dfba052726671051b9d8919"
        self.assertEqual(nulls.NULL_CLARIFICATION_SHA256, expected)
        self.assertEqual(nulls.SPEC_SHA256["null_clarification"], expected)
        self.assertEqual(nulls.CANONICAL_PAIR_NAME_BINDING, PAIR_NAMES)
        for function in (nulls.rank_pair, nulls.pair_tie_preimage):
            self.assertIs(function.__kwdefaults__["pair_names"], nulls.CANONICAL_PAIR_NAME_BINDING)

    def test_noncanonical_pair_names_are_rejected_not_available_as_alternatives(self):
        for bad in (tuple(b"answer" for _ in range(9)), list(PAIR_NAMES.names),
                    tuple(b"salt\0" + name for name in PAIR_NAMES.names),
                    tuple(f"N{index}".encode("ascii") for index in range(9)),
                    tuple(f"N{index} {name}".encode("ascii") for index, name in enumerate(nulls.NULL_NAMES)),
                    tuple(f"N{index}{name}".encode("ascii") for index, name in enumerate(nulls.NULL_NAMES)),
                    tuple(name + b"\n" for name in PAIR_NAMES.names),
                    tuple(reversed(PAIR_NAMES.names)), tuple(sorted(PAIR_NAMES.names))):
            with self.subTest(binding=bad):
                with self.assertRaisesRegex(ValueError, "canonical_descriptive"):
                    nulls.PairNameBinding(bad)
        for bad in (None, PAIR_NAMES.names, {"names": PAIR_NAMES.names}):
            with self.assertRaisesRegex(ValueError, "canonical_descriptive"):
                nulls.pair_tie_preimage("sentinel_first", "display_first", b"STOP", pair_names=bad)
            with self.assertRaisesRegex(ValueError, "canonical_descriptive"):
                nulls.rank_pair("sentinel_first", "display_first", initial(), phase="CONTINUE", skin=0,
                                pair_names=bad)

    def test_digest_and_operand_key_preimages(self):
        action = b"READ INDEX " + CURRENT.encode("ascii")
        self.assertEqual(nulls.digest_preimage(GOAL.encode("ascii"), action),
                         GOAL.encode("ascii") + b"\0" + action)
        self.assertEqual(nulls.character_columns(b"STOP"), (0, 0, 0, b"STOP"))
        self.assertEqual(nulls.character_columns(action), (ord("M"), ord("B"), ord(CURRENT[-1]), action))
        with self.assertRaises(ValueError):
            nulls.character_columns(b"STEP M")

    def test_sentinel_not_forced_last_in_lexical_or_digest_rankings(self):
        prefix = panel_prefix("SEEK")
        ranking = nulls.rank_null("lexical_first", prefix, phase="SEEK", skin=0)
        self.assertEqual(ranking[0], nulls.SENTINELS["SEEK"])
        self.assertEqual(nulls.rank_null("display_last", prefix, phase="SEEK", skin=0)[-1],
                         nulls.SENTINELS["SEEK"])

    def test_display_mutation_changes_display_not_lexical_ranking(self):
        before = panel_prefix("SEEK")
        after = turn(initial(), f"READ INDEX {CURRENT}", "SERVICE\n" + routes(queries=QUERIES[::-1]))
        self.assertNotEqual(nulls.rank_null("display_first", before, phase="SEEK", skin=0),
                            nulls.rank_null("display_first", after, phase="SEEK", skin=0))
        self.assertEqual(nulls.rank_null("lexical_first", before, phase="SEEK", skin=0),
                         nulls.rank_null("lexical_first", after, phase="SEEK", skin=0))

    def test_relational_relevance_never_selects_one_turn_candidate(self):
        before = panel_prefix("PROSPECT")
        after = turn(initial(), f"READ RELATION {QUERIES[0]}", "SERVICE\n" + events(relevant=0))
        for name in nulls.NULL_NAMES:
            self.assertEqual(nulls.rank_null(name, before, phase="PROSPECT", skin=0),
                             nulls.rank_null(name, after, phase="PROSPECT", skin=0))

    def test_check_implication_uses_selected_did_not_matching_goal_row(self):
        prefix = turn(panel_prefix("PROSPECT"), f"STEP {PORTS[0]}", f"WORLD\nCURRENT {OTHER}")
        panel = nulls.public_candidates(prefix, phase="CHECK", skin=0)
        self.assertEqual(panel.candidates[:2], tuple(f"THINK {verb} {EVENTS[0]}".encode("ascii")
                                                    for verb in ("KEEP", "REVISE")))

    def test_latest_world_authoritative_not_start_task_or_predicted_got(self):
        prefix = turn(panel_prefix("PROSPECT"), f"STEP {PORTS[2]}", f"WORLD\nCURRENT {OTHER}")
        check = nulls.public_candidates(prefix, phase="CHECK", skin=0)
        self.assertEqual(check.current, OTHER.encode("ascii"))
        prefix = turn(prefix, f"THINK REVISE {EVENTS[2]}", "ACK")
        panel = nulls.public_candidates(prefix, phase="CONTINUE", skin=0)
        self.assertEqual(panel.candidates[1], f"READ INDEX {OTHER}".encode("ascii"))
        atom = initial(current=OTHER)
        for name in nulls.NULL_NAMES:
            self.assertEqual(nulls.rank_null(name, prefix, phase="CONTINUE", skin=0),
                             nulls.rank_null(name, atom, phase="CONTINUE", skin=0))

    def test_check_outcome_changes_current_digest_not_candidate_id(self):
        before = panel_prefix("CHECK")
        after = before[:-1] + (message("user", f"WORLD\nCURRENT {OTHER}"),)
        self.assertEqual(nulls.public_candidates(before, phase="CHECK", skin=0).candidates,
                         nulls.public_candidates(after, phase="CHECK", skin=0).candidates)
        self.assertEqual(nulls.rank_null("display_first", before, phase="CHECK", skin=0),
                         nulls.rank_null("display_first", after, phase="CHECK", skin=0))

    def test_goal_digest_uses_task_goal_not_route_for(self):
        prefix = panel_prefix("SEEK")
        changed = initial(goal=OTHER) + prefix[2:]
        candidates = expected_candidates("SEEK")
        actual = nulls.rank_null("goal_digest", changed, phase="SEEK", skin=0)
        self.assertEqual(actual, reference_rank(6, candidates, OTHER.encode("ascii"), CURRENT.encode("ascii")))
        self.assertNotEqual(actual, nulls.rank_null("goal_digest", prefix, phase="SEEK", skin=0))

    def test_digest_collision_is_reported_not_silently_tie_broken(self):
        with patch.object(nulls, "sha256") as digest:
            digest.return_value.digest.return_value = b"\0" * 32
            with self.assertRaisesRegex(nulls.SpecificationAmbiguity, "digest_collision"):
                nulls.rank_null("goal_digest", initial(), phase="CONTINUE", skin=0)
            with self.assertRaisesRegex(nulls.SpecificationAmbiguity, "pair_digest_collision"):
                nulls.rank_pair("display_first", "display_last", initial(),
                                phase="CONTINUE", skin=0, pair_names=PAIR_NAMES)


class PrefixMutationTests(unittest.TestCase):
    def test_wire_mutations_never_trim_repair_or_ignore(self):
        prefix = panel_prefix("PROSPECT")
        mutations = (
            prefix[:-1] + (message("user", prefix[-1].content + b"\n"),),
            prefix[:-1] + (message("user", prefix[-1].content.replace(b"\n", b"\r\n")),),
            prefix[:-1] + (message("user", prefix[-1].content + b"\0"),),
            prefix[:-1] + (message("user", prefix[-1].content + b"\xff"),),
            prefix[:-1] + (message("user", prefix[-1].content + b"\noracle next=STEP"),),
            prefix[:-1] + (message("user", "SERVICE\nMISS\n"),),
            prefix[:-1] + (message("user", "ACK"),),
            prefix[:2] + (message("assistant", prefix[2].content + b"\n"), prefix[3]),
            (message("system", wire.SYSTEM_MESSAGE + "\n"),) + prefix[1:],
            prefix[:-1] + (message("assistant", prefix[-1].content),),
            prefix + (message("assistant", f"STEP {PORTS[2]}"),),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated[-1]):
                with self.assertRaises(ValueError):
                    nulls.public_candidates(mutated, phase="PROSPECT", skin=0)

    def test_no_metadata_mapping_answers_or_hidden_registry_input(self):
        with self.assertRaises(ValueError):
            nulls.public_candidates([{"role": "user", "content": b"TASK", "oracle": "STEP"}] * 2,
                                    phase="CONTINUE", skin=0)
        with self.assertRaises(TypeError):
            nulls.rank_null("display_first", initial(), phase="CONTINUE", skin=0, answer=b"STOP")
        with self.assertRaises(TypeError):
            nulls.rank_null("display_first", initial(), phase="CONTINUE", skin=0, registry={})
        prefix = (message("system", wire.SYSTEM_MESSAGE), nulls.PublicMessage("user", "TASK"))
        with self.assertRaisesRegex(ValueError, "exact_public_bytes"):
            nulls.public_candidates(prefix, phase="CONTINUE", skin=0)

    def test_phase_skin_and_name_validation(self):
        for skin in (True, -1, 2, "0"):
            with self.assertRaises(ValueError):
                nulls.public_candidates(initial(), phase="CONTINUE", skin=skin)
        for name in ("N0", "direct_goal", "oracle", None):
            with self.assertRaises(ValueError):
                nulls.rank_null(name, initial(), phase="CONTINUE", skin=0)
        for phase in ("STOP", "STEP_CHECK", "oracle", None):
            with self.assertRaises(ValueError):
                nulls.public_candidates(initial(), phase=phase, skin=0)
        with self.assertRaises(ValueError):
            nulls.rank_pair("display_first", "display_first", initial(), phase="CONTINUE", skin=0,
                            pair_names=PAIR_NAMES)
        with self.assertRaises(ValueError):
            nulls.public_candidates(panel_prefix("PROSPECT", 1), phase="PROSPECT", skin=0)

    def test_wrong_phase_stale_block_and_mismatched_service_rejected(self):
        for phase in ("SEEK", "PROSPECT", "CHECK"):
            with self.assertRaises(ValueError):
                nulls.public_candidates(initial(), phase=phase, skin=0)
        with self.assertRaises(ValueError):
            nulls.public_candidates(panel_prefix("SEEK"), phase="CONTINUE", skin=0)
        stale = turn(panel_prefix("SEEK"), f"THINK REVISE {QUERIES[0]}", "ACK")
        with self.assertRaises(ValueError):
            nulls.public_candidates(stale, phase="SEEK", skin=0)
        wrong = turn(initial(), f"READ INDEX {CURRENT}", "SERVICE\n" + events())
        with self.assertRaisesRegex(ValueError, "service_action_kind"):
            nulls.public_candidates(wrong, phase="PROSPECT", skin=0)

    def test_duplicate_candidates_and_ambiguous_step_implication_fail_closed(self):
        queries = (QUERIES[1],) + QUERIES[1:]
        prefix = turn(initial(), f"READ INDEX {CURRENT}", "SERVICE\n" + routes(queries=queries))
        with self.assertRaisesRegex(nulls.SpecificationAmbiguity, "duplicate_public"):
            nulls.public_candidates(prefix, phase="SEEK", skin=0)
        ports = (PORTS[2],) + PORTS[1:]
        prefix = turn(initial(), f"READ RELATION {QUERIES[0]}", "SERVICE\n" + events(ports=ports))
        with self.assertRaisesRegex(nulls.SpecificationAmbiguity, "duplicate_public"):
            nulls.public_candidates(prefix, phase="PROSPECT", skin=0)
        prefix = turn(prefix, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {GOT[2]}")
        with self.assertRaisesRegex(nulls.SpecificationAmbiguity, "uniquely_implicated"):
            nulls.public_candidates(prefix, phase="CHECK", skin=0)

    def test_sentinel_cannot_be_in_public_allocated_rows_or_accepted_history(self):
        prefix = panel_prefix("SEEK")
        bad = prefix[:-1] + (message("user", prefix[-1].content.replace(
            QUERIES[0].encode("ascii"), b"M2AQ_AAAAAAAAAAAA")),)
        with self.assertRaisesRegex(ValueError, "reserved_identifier"):
            nulls.public_candidates(bad, phase="SEEK", skin=0)
        bad = turn(initial(), "READ RELATION M2AQ_AAAAAAAAAAAA", "SERVICE\nMISS")
        with self.assertRaisesRegex(ValueError, "sentinel_in_accepted"):
            nulls.public_candidates(bad, phase="CHECK", skin=0)

    def test_query_check_unsupported_outside_registered_held_panels(self):
        for service in ("MISS", events(relevant=-1)):
            prefix = turn(initial(), f"READ RELATION {QUERIES[0]}", "SERVICE\n" + service)
            with self.assertRaisesRegex(ValueError, "unsupported_query_check_not_in_held_panels") as caught:
                nulls.public_candidates(prefix, phase="CHECK", skin=0)
            self.assertNotIsInstance(caught.exception, nulls.SpecificationAmbiguity)
            with self.assertRaises(ValueError):
                wire.parse_action(f"THINK KEEP {QUERIES[0]}")

    def test_prefix_bounds_and_host_action_pairing(self):
        oversized = initial() + (message("assistant", f"READ INDEX {CURRENT}"),
                                 message("user", "SERVICE\n" + routes())) * 30
        with self.assertRaisesRegex(ValueError, "bounded_public_prefix"):
            nulls.public_candidates(oversized, phase="SEEK", skin=0)
        over_read = initial() + (message("assistant", f"READ INDEX {CURRENT}"),
                                 message("user", "SERVICE\n" + routes())) * 13
        with self.assertRaisesRegex(ValueError, "over_budget"):
            nulls.public_candidates(over_read, phase="SEEK", skin=0)
        bad_ack = turn(initial(), f"THINK KEEP {EVENTS[0]}", "ACK\n")
        with self.assertRaisesRegex(ValueError, "exact_ack"):
            nulls.public_candidates(bad_ack, phase="CONTINUE", skin=0)


class ScheduleTests(unittest.TestCase):
    def advance(self, policy, action, response):
        raw = action.encode("ascii") if type(action) is str else action
        self.assertEqual(policy.next_action().action, raw)
        self.assertEqual(policy.next_action().action, raw)
        policy.observe(response.encode("ascii") if type(response) is str else response)

    def test_all_six_names_and_initial_action(self):
        self.assertEqual(nulls.SCHEDULE_NAMES, (
            "S_DISPLAY0", "S_LEXICAL", "S_POSITION", "S_READ_ALL12", "S_STOP1", "S_STOP2"))
        for name in nulls.SCHEDULE_NAMES:
            policy = nulls.BoundedSchedule(name, initial(), skin=0)
            self.assertEqual(policy.next_action().action, f"READ INDEX {CURRENT}".encode("ascii"))
            self.assertFalse(any(policy.counts.values()))
            self.assertEqual(policy.next_action().status, "UNEXECUTED_INCOMPLETE")

    def test_five_surface_schedules_exact_choices_keep_and_stop_count(self):
        for skin in (0, 1):
            for name in nulls.SCHEDULE_NAMES:
                if name == "S_READ_ALL12":
                    continue
                policy = nulls.BoundedSchedule(name, initial(), skin=skin)
                route_index = event_index = 0
                if name == "S_LEXICAL":
                    route_index, event_index = QUERIES.index(min(QUERIES)), PORTS.index(min(PORTS))
                if name == "S_POSITION":
                    digest_byte = sha256(GOAL.encode("ascii")).digest()[0]
                    route_index, event_index = digest_byte % 24, digest_byte % 4
                stop_after = 1 if name == "S_STOP1" else 2
                current = CURRENT
                for _ in range(stop_after):
                    self.advance(policy, f"READ INDEX {current}", "SERVICE\n" + routes(skin, current=current))
                    self.advance(policy, f"READ RELATION {QUERIES[route_index]}",
                                 "SERVICE\n" + events(skin, current=current))
                    self.advance(policy, f"STEP {PORTS[event_index]}", f"WORLD\nCURRENT {OTHER}")
                    self.advance(policy, f"THINK KEEP {EVENTS[event_index]}", "ACK")
                    current = OTHER
                self.advance(policy, b"STOP", b"")
                self.assertEqual(policy.next_action().terminal_reason, "stop_emitted_unscored")
                self.assertEqual(policy.counts["STEP"], stop_after)
                self.assertEqual(policy.counts["THINK"], stop_after)
                self.assertEqual(policy.trace[-1], message("assistant", b"STOP"))
                self.assertNotIn(message("user", b""), policy.trace)

    def test_read_all12_index_spends_one_read_no_twelfth_relation(self):
        policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=0)
        self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes())
        for query in QUERIES[:11]:
            self.advance(policy, f"READ RELATION {query}", "SERVICE\nMISS")
        self.assertEqual(policy.counts["READ"], 12)
        self.assertEqual(policy.next_action().terminal_reason, "action_cap")
        self.assertNotIn(message("assistant", f"READ RELATION {QUERIES[11]}"), policy.trace)

    def test_read_all12_matching_last_permitted_read_can_still_step(self):
        policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=0)
        self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes())
        for query in QUERIES[:10]:
            self.advance(policy, f"READ RELATION {query}", "SERVICE\nMISS")
        self.advance(policy, f"READ RELATION {QUERIES[10]}", "SERVICE\n" + events())
        self.advance(policy, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {GOT[2]}")
        self.advance(policy, f"THINK KEEP {EVENTS[2]}", "ACK")
        self.assertEqual(policy.next_action().terminal_reason, "action_cap")
        self.assertEqual(policy.counts["STEP"], 1)

    def test_read_all12_skips_irrelevance_and_uses_public_recovery_only(self):
        policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=1)
        self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes(1))
        self.advance(policy, f"READ RELATION {QUERIES[0]}", "SERVICE\n" + events(1, relevant=-1))
        self.advance(policy, f"READ RELATION {QUERIES[1]}", "SERVICE\n" + events(1))
        self.advance(policy, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {OTHER}")
        self.advance(policy, f"THINK REVISE {EVENTS[2]}", "ACK")
        self.advance(policy, f"READ RELATION {RECOVER[2]}",
                     "SERVICE\n" + events(1, current=OTHER, relevant=1))
        self.advance(policy, f"STEP {PORTS[1]}", f"WORLD\nCURRENT {GOT[1]}")
        self.advance(policy, f"THINK KEEP {EVENTS[1]}", "ACK")
        self.assertEqual(policy.next_action().action, f"READ INDEX {GOT[1]}".encode("ascii"))

    def test_read_all12_does_not_reuse_old_directory_on_recovery_miss(self):
        policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=0)
        self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes())
        self.advance(policy, f"READ RELATION {QUERIES[0]}", "SERVICE\n" + events())
        self.advance(policy, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {OTHER}")
        self.advance(policy, f"THINK REVISE {EVENTS[2]}", "ACK")
        self.advance(policy, f"READ RELATION {RECOVER[2]}", "SERVICE\nMISS")
        self.assertEqual(policy.next_action().terminal_reason, "no_candidate")

    def test_read_all12_reports_multiple_matches(self):
        policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=0)
        self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes())
        ambiguous = events().replace(f"FOR {OTHER}", f"FOR {GOAL}")
        self.advance(policy, f"READ RELATION {QUERIES[0]}", "SERVICE\n" + ambiguous)
        self.assertIn("multiple_matching_public_events", policy.next_action().terminal_reason)

    def after_public_check(self, predicted, actual, *, skin, ack=b"ACK"):
        policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=skin)
        self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes(skin))
        predictions = GOT[:2] + (predicted,) + GOT[3:]
        self.advance(policy, f"READ RELATION {QUERIES[0]}", "SERVICE\n" + events(skin, got=predictions))
        self.advance(policy, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {actual}")
        verb = "KEEP" if predicted == actual else "REVISE"
        self.assertNotIn(message("assistant", b"STOP"), policy.trace)
        self.advance(policy, f"THINK {verb} {EVENTS[2]}", ack)
        self.assertEqual(policy.counts["THINK"], 1)
        return policy

    def test_read_all12_reached_matched_stops_after_keep_ack(self):
        for skin in (0, 1):
            policy = self.after_public_check(GOAL, GOAL, skin=skin)
            self.assertEqual(policy.trace[-1], message("user", b"ACK"))
            self.advance(policy, b"STOP", b"")
            self.assertEqual(policy.next_action().terminal_reason, "stop_emitted_unscored")
            self.assertEqual(policy.counts["READ"], 2)

    def test_read_all12_reached_unexpected_stops_after_revise_ack_not_recovery(self):
        for skin in (0, 1):
            policy = self.after_public_check(GOT[2], GOAL, skin=skin)
            self.assertEqual(policy.trace[-1], message("user", b"ACK"))
            self.advance(policy, b"STOP", b"")
            self.assertEqual(policy.next_action().terminal_reason, "stop_emitted_unscored")
            self.assertEqual(policy.counts["READ"], 2)
            self.assertNotIn(message("assistant", f"READ RELATION {RECOVER[2]}"), policy.trace)

    def test_read_all12_unresolved_matched_indexes_actual_current_after_keep_ack(self):
        for skin in (0, 1):
            policy = self.after_public_check(GOT[2], GOT[2], skin=skin)
            self.assertEqual(policy.next_action().action, f"READ INDEX {GOT[2]}".encode("ascii"))
            self.assertIsNone(policy.next_action().terminal_reason)
            self.assertEqual(policy.counts["STOP"], 0)

    def test_read_all12_unresolved_mismatch_recovers_after_revise_ack_not_predicted_goal(self):
        for skin in (0, 1):
            policy = self.after_public_check(GOAL, OTHER, skin=skin)
            self.assertEqual(policy.next_action().action, f"READ RELATION {RECOVER[2]}".encode("ascii"))
            self.assertIsNone(policy.next_action().terminal_reason)
            self.assertEqual(policy.counts["STOP"], 0)

    def test_read_all12_arrival_with_malformed_ack_terminates_without_stop(self):
        for predicted in (GOAL, GOT[2]):
            policy = self.after_public_check(predicted, GOAL, skin=0, ack=b"ACK\n")
            self.assertTrue(policy.next_action().terminal_reason.startswith("malformed_host_response"))
            self.assertIsNone(policy.next_action().action)
            self.assertEqual(policy.counts["STOP"], 0)
            self.assertNotIn(message("assistant", b"STOP"), policy.trace)

    def test_read_all12_arrival_on_final_permitted_read_still_checks_then_stops(self):
        for predicted in (GOAL, GOT[2]):
            policy = nulls.BoundedSchedule("S_READ_ALL12", initial(), skin=0)
            self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes())
            for query in QUERIES[:10]:
                self.advance(policy, f"READ RELATION {query}", "SERVICE\nMISS")
            predictions = GOT[:2] + (predicted,) + GOT[3:]
            self.advance(policy, f"READ RELATION {QUERIES[10]}", "SERVICE\n" + events(got=predictions))
            self.advance(policy, f"STEP {PORTS[2]}", f"WORLD\nCURRENT {GOAL}")
            verb = "KEEP" if predicted == GOAL else "REVISE"
            self.advance(policy, f"THINK {verb} {EVENTS[2]}", "ACK")
            self.advance(policy, b"STOP", b"")
            self.assertEqual(policy.next_action().terminal_reason, "stop_emitted_unscored")
            self.assertEqual(policy.counts["READ"], 12)
            self.assertEqual(policy.counts["THINK"], 1)

    def test_five_fixed_step_actors_do_not_gain_arrival_stop_predicate(self):
        for name in nulls.SCHEDULE_NAMES:
            if name == "S_READ_ALL12":
                continue
            policy = nulls.BoundedSchedule(name, initial(), skin=0)
            route_index = event_index = 0
            if name == "S_LEXICAL":
                route_index, event_index = QUERIES.index(min(QUERIES)), PORTS.index(min(PORTS))
            if name == "S_POSITION":
                digest_byte = sha256(GOAL.encode("ascii")).digest()[0]
                route_index, event_index = digest_byte % 24, digest_byte % 4
            self.advance(policy, f"READ INDEX {CURRENT}", "SERVICE\n" + routes())
            self.advance(policy, f"READ RELATION {QUERIES[route_index]}", "SERVICE\n" + events())
            self.advance(policy, f"STEP {PORTS[event_index]}", f"WORLD\nCURRENT {GOAL}")
            self.advance(policy, f"THINK KEEP {EVENTS[event_index]}", "ACK")
            expected = b"STOP" if name == "S_STOP1" else f"READ INDEX {GOAL}".encode("ascii")
            self.assertEqual(policy.next_action().action, expected)

    def test_malformed_no_candidate_and_host_termination_preserve_trace(self):
        for response, reason in ((b"SERVICE\nMISS", "no_candidate"), (b"", "host_terminated_unscored"),
                                 (b"ACK", "malformed_host_response"),
                                 (b"SERVICE\nMISS\n", "malformed_host_response"),
                                 (b"\xff", "malformed_host_response")):
            policy = nulls.BoundedSchedule("S_DISPLAY0", initial(), skin=0)
            self.advance(policy, f"READ INDEX {CURRENT}", response)
            self.assertTrue(policy.next_action().terminal_reason.startswith(reason))
            if response:
                self.assertEqual(policy.trace[-1].content, response)
            else:
                self.assertEqual(policy.trace[-1], message("assistant", f"READ INDEX {CURRENT}"))
                self.assertNotIn(message("user", b""), policy.trace)
            with self.assertRaises(ValueError):
                policy.observe(b"ACK")

    def test_schedule_does_not_accept_partial_history_or_unsolicited_response(self):
        with self.assertRaisesRegex(ValueError, "initial_public_prefix"):
            nulls.BoundedSchedule("S_DISPLAY0", panel_prefix("SEEK"), skin=0)
        with self.assertRaises(ValueError):
            nulls.BoundedSchedule("S_ORACLE", initial(), skin=0)
        policy = nulls.BoundedSchedule("S_DISPLAY0", initial(), skin=0)
        with self.assertRaisesRegex(ValueError, "no_pending"):
            policy.observe(b"SERVICE\nMISS")
        policy.next_action()
        with self.assertRaisesRegex(ValueError, "exact_public_bytes"):
            policy.observe("SERVICE\nMISS")
        self.assertEqual(policy.next_action().terminal_reason, "malformed_host_response")

    def test_partial_status_and_immutable_false_science_gates(self):
        self.assertEqual(nulls.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertEqual(nulls.EXECUTION_STATUS, "UNEXECUTED_INCOMPLETE")
        self.assertEqual(set(nulls.SCIENCE_GATES), {
            "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"})
        self.assertFalse(any(nulls.SCIENCE_GATES.values()))
        with self.assertRaises(TypeError):
            nulls.SCIENCE_GATES["GO_CLAIM"] = True


if __name__ == "__main__":
    unittest.main()
