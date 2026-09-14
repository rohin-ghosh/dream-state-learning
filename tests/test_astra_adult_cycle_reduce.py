import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller
from organism_v6 import pcfl_vertical_dev as world
from tools import astra_adult_cycle_reduce as reduce


class AdultReducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.runtime = SimpleNamespace(adult=adult, micro=micro, controller=controller, world=world,
                                       source=adult.source, development=adult.cue_sleep)
        self.bank = adult.build_bank()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def generate(self, messages):
        fact = next(fact for fact in self.bank if fact["port"] in messages[1]["content"])
        raw = "EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2 else micro._event(fact)
        return dict(raw=raw, terminal=True, truncated=False, messages=messages, token_ids=[7, 151645], prompt_tokens=10)

    def mixture(self, arm, old_count=32):
        masks = [dict(input_ids=[151644, 7, 151645, 198], labels=[-100, 7, 151645, -100],
                      target_ids=[7, 151645]) for unused in range(old_count + 52)]
        active = 8 if arm == "CUE_REPLAY" else 6
        losses = [dict(update=update, row_indexes=list(adult.adult_indexes(update, 20, old_count=old_count)), loss=0.1,
                       original_label_count=8, active_label_count=active, loss_scale=active / 8)
                  for update in range(1, 401)]
        return masks, losses

    def test_cycle2_116_masks_schedule_and_nonuniform_old_dose(self):
        for arm in reduce.ARMS:
            masks, losses = self.mixture(arm, 64)
            summary = reduce.audit_mixture(masks, losses, arm, adult.adult_indexes, 64)
            self.assertEqual(losses[0]["row_indexes"], [0, 64, 84, 85])
            self.assertEqual(losses[-1]["row_indexes"], [15, 83, 114, 115])
            self.assertEqual((summary["mask_count"], summary["original_memory_presentations"],
                              summary["prior_adult_presentations"]), (116, 208, 192))
            self.assertEqual([summary["row_counts"][index] for index in range(64)], [7] * 16 + [6] * 48)
            with self.assertRaises(ValueError):
                reduce.audit_mixture(masks[:-1], losses, arm, adult.adult_indexes, 64)
            masks[84]["labels"][0] = 151644
            with self.assertRaises(ValueError):
                reduce.audit_mixture(masks, losses, arm, adult.adult_indexes, 64)

    def test_legacy_schedule_callback_needs_no_old_count_keyword(self):
        masks, losses = self.mixture("CUE_REPLAY")
        summary = reduce.audit_mixture(masks, losses, "CUE_REPLAY",
                                       lambda update, cue: adult.adult_indexes(update, cue))
        self.assertEqual(summary["mask_count"], 84)

    def test_cycle2_collection_replays_and_rejects_cycle_drift(self):
        self.bank = adult.build_bank(2)
        record = adult.collect(self.generate, cycle=2)
        self.write("COLLECTION.json", record)
        result = dict(status="COLLECTION_COMPLETE", accepted_events=4, model_calls=8,
                      collection_sha256=reduce.digest(self.root / "COLLECTION.json"))
        self.assertEqual(reduce.collection_summary(self.root, result, self.runtime)[0]["rows"], 32)
        record["cycle"] = 1
        self.write("COLLECTION.json", record)
        result["collection_sha256"] = reduce.digest(self.root / "COLLECTION.json")
        with self.assertRaises(ValueError):
            reduce.collection_summary(self.root, result, self.runtime)

    def test_training_rejects_changed_prior_rows_before_mask_replay(self):
        prior = adult.collect(self.generate)
        self.bank = adult.build_bank(2)
        current = adult.collect(self.generate, cycle=2)
        original = prior["rows"]
        rows = dict(old_memory=original + copy.deepcopy(prior["rows"]), cue=[{}] * 20,
                    new_memory=current["rows"])
        rows["old_memory"][32]["messages"][-1]["content"] = "forged prior target"
        self.write("TRAINING_ROWS.json", rows)
        self.write("MASKS.json", [])
        result = dict(memory_source=dict(compiled_rows_sha256=reduce.hashlib.sha256(
                      reduce.canonical(original) + b"\n").hexdigest()))
        with self.assertRaisesRegex(ValueError, "prior_adult_rows_drift"):
            reduce.training_summary(self.root, result, current, self.runtime, prior_collection=prior)

    def test_prior_binding_authenticates_receipt_chain_and_rejects_drift(self):
        record = adult.collect(self.generate)
        prefix = "CUE_REPLAY/"
        self.write(prefix + "collect/COLLECTION.json", record)
        shared = dict(development_arm="CUE_REPLAY", master=adult.MASTER, memory_source={}, cue_source={},
                      tokenizer={}, frozen_base_unchanged=True, initial_training_result_sha256="S2",
                      started_unix=1, finished_unix=2)
        prior = dict(shared, status="COLLECTION_COMPLETE", accepted_events=4, model_calls=8,
                     arguments=dict(output="/prior/collect", expected_base_sha256="base"),
                     collection_sha256=reduce.digest(self.root / prefix / "collect/COLLECTION.json"))
        self.write(prefix + "collect/RESULT.json", prior)
        provenance = dict(path="/prior/collect", collection_sha256=prior["collection_sha256"],
                          result_sha256=reduce.digest(self.root / prefix / "collect/RESULT.json"))
        training = dict(shared, status="COMPLETE", adult_source=provenance, adapter_state_after="trained",
                        arguments=dict(output="/prior/train", expected_base_sha256="base"),
                        adapter_files={"adapter_model.safetensors": "adapter-file"})
        self.write(prefix + "train/RESULT.json", training)
        receipt = reduce.digest(self.root / prefix / "train/RESULT.json")
        current = dict(shared, prior_adult_source=provenance, prior_master=adult.MASTER,
                       initial_training_result_sha256=receipt, prior_adult_training_result_sha256=receipt,
                       phase="collect", state="BEFORE", loaded_adapter_state_sha256="trained",
                       arguments=dict(prior_adult_collection="/prior/collect", initial_adapter_dir="/prior/train/adapter",
                                      expected_initial_adapter_sha256="adapter-file", expected_base_sha256="base"))
        self.assertEqual(reduce.prior_binding(self.root, "CUE_REPLAY", current, self.runtime), record)
        for key in ("prior_master", "initial_training_result_sha256", "loaded_adapter_state_sha256"):
            changed = copy.deepcopy(current)
            changed[key] = "drift"
            with self.subTest(key=key), self.assertRaises(ValueError):
                reduce.prior_binding(self.root, "CUE_REPLAY", changed, self.runtime)
        with self.assertRaises(ValueError):
            reduce.prior_binding(None, "CUE_REPLAY", current, self.runtime)

    def test_partial_files_are_never_scored(self):
        self.write("PANELS.json", {"correct": 100})
        self.write("LOSSES.jsonl", ["partial"])
        self.assertEqual(reduce.terminal(self.root), {"status": "PENDING", "request_present": False})
        self.write("REQUEST.json", {})
        self.assertTrue(reduce.terminal(self.root)["request_present"])

    def test_failed_receipt_overrides_complete_and_preserves_error(self):
        self.write("RESULT.json", {"status": "COMPLETE"})
        failure = {"status": "FAILED", "error": "RuntimeError: CUDA failed"}
        self.write("FAILED.json", failure)
        self.assertEqual(reduce.terminal(self.root), {"status": "FAILED", "failure": failure})

    def test_unknown_status_and_nonregular_files_fail_closed(self):
        self.write("RESULT.json", {"status": "RUNNING"})
        with self.assertRaises(ValueError):
            reduce.terminal(self.root)
        (self.root / "alias").symlink_to(self.root / "RESULT.json")
        with self.assertRaises(ValueError):
            reduce.read(self.root / "alias")

    def test_collection_recomputes_actual_rows_and_counts(self):
        record = adult.collect(self.generate)
        self.write("COLLECTION.json", record)
        result = dict(status="COLLECTION_COMPLETE", accepted_events=4, model_calls=8,
                      collection_sha256=reduce.digest(self.root / "COLLECTION.json"))
        summary, replayed = reduce.collection_summary(self.root, result, self.runtime)
        self.assertEqual((summary["accepted_events"], summary["rows"], summary["model_calls"]), (4, 32, 8))
        self.assertFalse(summary["parent_present"])
        self.assertEqual(replayed, record)
        for mutate in (lambda record: record["rows"][0]["messages"][-1].update(content="forged"),
                       lambda record: record["captures"][0]["messages"][1].update(content="teacher"),
                       lambda record: record.update(parent_present=True)):
            changed = copy.deepcopy(record)
            mutate(changed)
            self.write("COLLECTION.json", changed)
            result["collection_sha256"] = reduce.digest(self.root / "COLLECTION.json")
            with self.assertRaises(ValueError):
                reduce.collection_summary(self.root, result, self.runtime)

    def test_collection_hash_and_reported_counts_cannot_drift(self):
        record = adult.collect(self.generate)
        self.write("COLLECTION.json", record)
        for digest, count in (("0" * 64, 8), (reduce.digest(self.root / "COLLECTION.json"), 7)):
            result = dict(status="COLLECTION_COMPLETE", accepted_events=4, model_calls=count, collection_sha256=digest)
            with self.assertRaises(ValueError):
                reduce.collection_summary(self.root, result, self.runtime)

    def test_mixture_controls_share_original_denominator(self):
        for arm, active in (("CUE_REPLAY", 3200), ("CUE_LOSS_OFF", 2400)):
            masks, losses = self.mixture(arm)
            summary = reduce.audit_mixture(masks, losses, arm, adult.adult_indexes)
            self.assertEqual(summary["original_supervised_tokens"], 3200)
            self.assertEqual(summary["supervised_tokens"], active)
            self.assertEqual([summary[key] for key in ("old_memory_presentations", "old_cue_presentations",
                                                       "new_memory_presentations")], [400, 400, 800])

    def test_mixture_rejects_partial_source_mask_index_and_scale_drift(self):
        for kind in ("partial", "prefix", "target", "order", "denominator", "scale", "nan"):
            masks, losses = self.mixture("CUE_LOSS_OFF")
            if kind == "partial":
                losses.pop()
            elif kind == "prefix":
                masks[0]["labels"][0] = 151644
            elif kind == "target":
                masks[52]["target_ids"][0] = 99
            elif kind == "order":
                losses[0]["row_indexes"] = [32, 0, 52, 53]
            elif kind == "denominator":
                losses[0]["original_label_count"] = 6
            elif kind == "scale":
                losses[0]["loss_scale"] = 1
            else:
                losses[0]["loss"] = float("nan")
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                reduce.audit_mixture(masks, losses, "CUE_LOSS_OFF", adult.adult_indexes)

    def test_raw_probes_do_not_repair_miss_newlines(self):
        rows = []
        for fact in self.bank:
            response = dict(raw="MISS", terminal=True, truncated=False,
                            messages=reduce.memory_messages(self.runtime, fact["event"], 8))
            rows.append(dict(generation=response, correct=False))
        summary = reduce.audit_probes(rows, self.bank, 8, lambda response, messages: None, self.runtime, miss=True)
        self.assertEqual(summary["correct"], 0)
        rows[0]["correct"] = True
        with self.assertRaises(ValueError):
            reduce.audit_probes(rows, self.bank, 8, lambda response, messages: None, self.runtime, miss=True)

    def make_route_panel(self):
        records, calls = [], []
        name = "OWN_READER_OFF"
        for number, fact in enumerate(self.bank, 1):
            def actor(messages):
                response = dict(raw="ROUTE " + fact["public_ports"][0], terminal=True, truncated=False,
                                messages=messages, token_ids=[7, 151645], prompt_tokens=10)
                calls.append(response)
                return response
            transitions = {other["port"]: other["outcome"] for other in self.bank if other["node"] == fact["node"]}
            episode = controller.run_episode(controller.public_task(fact), actor,
                                             lambda address: dict(raw="MISS", terminal=True, truncated=False),
                                             transitions.__getitem__)
            record = dict(event=fact["event"], episode=episode)
            records.append(record)
            self.write(name + "_EPISODE_%02d.json" % number, record)
        return dict(denominator=4, reached_goal=2, with_reads=0, second_reads=0, episodes=records), calls

    def test_raw_route_replay_retains_wrong_goals(self):
        panel, calls = self.make_route_panel()
        consumed = []
        def consume(name, role, response, messages, disabled):
            self.assertEqual(response, calls[len(consumed)])
            self.assertEqual(response["messages"], messages)
            self.assertEqual((name, role, disabled), ("OWN_READER_OFF", "actor", False))
            consumed.append(response)
            return response
        summary = reduce.audit_route_panel(self.root, "OWN_READER_OFF", self.bank, panel, consume, self.runtime)
        self.assertEqual(summary["reached_goal"], 2)
        self.assertEqual(len(consumed), 4)
        self.assertEqual(sum(episode["terminal_reason"] == "wrong_outcome" for episode in summary["episodes"]), 2)

    def test_actual_reader_uses_recorded_w0_not_legacy_w8(self):
        records = []
        for number, fact in enumerate(self.bank, 1):
            commands = iter(["READ EVENT " + fact["event"], "ROUTE " + fact["port"]])
            def actor(messages):
                return dict(raw=next(commands), terminal=True, truncated=False, messages=messages)
            def reader(address):
                return dict(raw=micro._event(fact), terminal=True, truncated=False,
                            messages=reduce.memory_messages(self.runtime, address, 0))
            episode = controller.run_episode(controller.public_task(fact), actor, reader,
                                             lambda port: fact["outcome"])
            record = dict(event=fact["event"], episode=episode)
            records.append(record)
            self.write("OWN_PARAMETRIC_EPISODE_%02d.json" % number, record)
        panel = dict(denominator=4, reached_goal=4, with_reads=4, second_reads=0, episodes=records)
        def consume(name, role, response, messages, disabled):
            reduce.require(response["messages"] == messages, "reader_prefix_drift")
            return response
        summary = reduce.audit_route_panel(self.root, "OWN_PARAMETRIC", self.bank, panel,
                                           consume, self.runtime, reader_wrapper=0)
        self.assertEqual(summary["reached_goal"], 4)
        with self.assertRaises(ValueError):
            reduce.audit_route_panel(self.root, "OWN_PARAMETRIC", self.bank, panel, consume, self.runtime)

    def test_coherent_panel_score_tampering_fails_raw_replay(self):
        panel, unused = self.make_route_panel()
        failed = next(record for record in panel["episodes"] if not record["episode"]["reached_goal"])
        failed["episode"]["reached_goal"] = True
        number = panel["episodes"].index(failed) + 1
        self.write("OWN_READER_OFF_EPISODE_%02d.json" % number, failed)
        panel["reached_goal"] = 3
        with self.assertRaises(ValueError):
            reduce.audit_route_panel(self.root, "OWN_READER_OFF", self.bank, panel,
                                     lambda name, role, response, messages, disabled: response, self.runtime)

    def test_full_readout_joins_nested_calls_and_old_retention(self):
        self.check_full_readout()

    def test_cycle2_readout_retains_eight_old_facts_and_w0(self):
        self.check_full_readout(cycle2=True)

    def check_full_readout(self, cycle2=False):
        panels, calls = {}, []
        def capture(panel, role, messages, raw):
            response = dict(raw=raw, messages=messages, terminal=True, truncated=False,
                            prompt_tokens=10, token_ids=[7, 151645])
            calls.append(dict(panel=panel, role=role, reader_adapter_disabled=False, generation=response))
            return response
        banks = {"OWN_PARAMETRIC": self.bank, "OWN_READER_OFF": self.bank}
        banks.update({"HELD_TEXT_" + str(index): micro.build_bank(adult.cue_sleep.HELD_MASTER + "-" + str(index))
                      for index in range(2)})
        for name, bank in banks.items():
            records = []
            for number, fact in enumerate(bank, 1):
                transitions = {other["port"]: other["outcome"] for other in bank if other["node"] == fact["node"]}
                episode = controller.run_episode(controller.public_task(fact),
                    lambda messages: capture(name, "actor", messages, "ROUTE " + fact["public_ports"][0]),
                    lambda address: None, transitions.__getitem__)
                record = dict(event=fact["event"], episode=episode)
                records.append(record)
                self.write("new_task/" + name + "_EPISODE_%02d.json" % number, record)
            panels[name] = dict(denominator=4, reached_goal=2, with_reads=0, second_reads=0, episodes=records)
        unseen = micro.build_bank(adult.source.MASTER + "-UNSEEN-MISS")
        for name, wrapper, bank in (("RECALL_W0", 0, self.bank), ("RECALL_W8", 8, self.bank), ("UNSEEN_MISS", 8, unseen)):
            rows = []
            for fact in bank:
                expected = "MISS\n" if name == "UNSEEN_MISS" else micro._event(fact)
                row = dict(correct=True, generation=capture(name, "memory_probe",
                           reduce.memory_messages(self.runtime, fact["event"], wrapper), expected))
                if name != "UNSEEN_MISS":
                    row.update(event=fact["event"], expected=expected)
                rows.append(row)
            panels[name] = dict(denominator=4, correct=4, rows=rows)
        self.write("new_task/PANELS.json", panels)
        for number, call in enumerate(calls, 1):
            self.write("new_task/CALL_%03d.json" % number, call)
        prior = adult.collect(self.generate) if cycle2 else None
        old_bank = micro.build_bank(adult.source.MASTER) + (prior["bank"] if cycle2 else [])
        for wrapper in (0, 8):
            name, rows = "OLD_RECALL_W" + str(wrapper), []
            for number, fact in enumerate(old_bank, 1):
                expected = micro._event(fact)
                row = dict(event=fact["event"], expected=expected, correct=True,
                           generation=dict(raw=expected, terminal=True, truncated=False, prompt_tokens=10,
                                           token_ids=[7, 151645], messages=reduce.memory_messages(self.runtime, fact["event"], wrapper)))
                rows.append(row)
                self.write(name + "_%02d.json" % number, row)
            panels[name] = dict(denominator=len(old_bank), correct=len(old_bank), rows=rows)
        result = dict(parent_present=False, fits=0, panels=panels, model_calls=28 + 2 * len(old_bank),
                      reader_wrapper=0 if cycle2 else 8)
        summary = reduce.readout_summary(self.root, result, {"bank": self.bank}, self.runtime, prior)
        self.assertEqual(summary["model_calls"], 28 + 2 * len(old_bank))
        self.assertEqual(summary["panels"]["OLD_RECALL_W8"]["correct"], len(old_bank))
        self.assertEqual(summary["roles"]["old_memory_probe"], 2 * len(old_bank))
        if cycle2:
            self.assertEqual(summary["panels"]["OLD_RECALL_W8"]["prior_adult_correct"], 4)
            self.assertEqual(summary["reader_wrapper"], 0)
        changed = reduce.read(self.root / "new_task/CALL_001.json")
        changed["generation"]["raw"] = "MISS"
        self.write("new_task/CALL_001.json", changed)
        with self.assertRaises(ValueError):
            reduce.readout_summary(self.root, result, {"bank": self.bank}, self.runtime, prior)


if __name__ == "__main__":
    unittest.main()
