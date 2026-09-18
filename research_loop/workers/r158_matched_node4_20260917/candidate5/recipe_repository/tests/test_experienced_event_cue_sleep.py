"""CPU-only cue-source replay, final-target masking and 2+2 schedule tests."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_experienced_event_cue_collect as collector
from organism_v6 import experienced_event_cue_collection as cue
from organism_v6 import experienced_event_cue_sleep as sleep
from organism_v6 import experienced_event_microloop as micro


ACTOR_SHA = "a" * 64
BASE_SHA = "b" * 64


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(collector.source.native._json_bytes(value))


def read(path):
    return json.loads(path.read_text())


class ReadingEngine:
    def __init__(self, *, one_read_bank=None, two_read_bank=None, fail_first=False):
        self.banks = collector.training_banks()
        self.one_read_nodes = {fact["node"] for fact in self.banks[one_read_bank]} if one_read_bank is not None else set()
        self.two_read_nodes = {fact["node"] for fact in self.banks[two_read_bank]} if two_read_bank is not None else set()
        self.fail_first = fail_first
        self.calls = 0

    def generate(self, messages):
        public = deepcopy(messages)
        for message in public:
            message["content"] = message["content"].split(cue.PUBLIC_FEEDBACK_PREFIX)[0]
        task = dict(line.split(" ", 1) for line in public[1]["content"].splitlines()[1:])
        memories = [micro.parse_event_line(micro.canonical_event(message["content"][14:]))
                    for message in public if message["role"] == "user"
                    and message["content"].startswith("MEMORY RESULT\n")]
        read_addresses = [message["content"].rstrip("\n").split()[2] for message in public
                          if message["role"] == "assistant" and message["content"].startswith("READ EVENT ")]
        if self.fail_first and self.calls == 0:
            fact = next(fact for bank in self.banks for fact in bank if fact["outcome"] == task["GOAL"])
            raw = "ROUTE " + next(port for port in fact["public_ports"] if port != fact["port"])
        elif memories and task["NODE"] in self.one_read_nodes:
            raw = "ROUTE " + memories[-1]["port"]
        elif task["NODE"] in self.two_read_nodes and len(memories) < 2:
            addresses = task["EVENTS"].split(",")
            if not memories:
                address = next(fact["event"] for bank in self.banks for fact in bank
                               if fact["event"] in addresses and fact["outcome"] != task["GOAL"])
            else:
                address = next(address for address in addresses if address not in read_addresses)
            raw = "READ EVENT " + address
        else:
            matching = next((event for event in memories if event["source"] == task["NODE"]
                             and event["destination"] == task["GOAL"]), None)
            raw = "ROUTE " + matching["port"] if matching else "READ EVENT " + next(
                address for address in task["EVENTS"].split(",") if address not in read_addresses)
        self.calls += 1
        return dict(raw=raw, terminal=True, truncated=False, messages=deepcopy(messages))


def fixture(parent, *, mode=cue.PUBLIC_FEEDBACK_MODE, **engine_options):
    original = parent / "original"
    original.mkdir()
    base_metadata = dict(schema="DEV_GUIDED_EXTERNAL_EVENT_CUE_COLLECTION_V1", master=collector.MASTER,
        arguments=dict(expected_base_sha256=BASE_SHA, phase="collect", adapter_dir=None))
    write(original / "REQUEST.json", base_metadata)
    write(original / "RESULT.json", dict(base_metadata, status="COLLECTION_COMPLETE_NO_FIT",
        banks=2, admitted_events=8, event_denominator=8, cue_task_denominator=8, fits=0, frozen_base_unchanged=True))
    for bank_index, bank in enumerate(collector.training_banks()):
        directory = original / f"BANK_{bank_index:02d}"
        write(directory / "BANK.json", bank)
        experiences = []
        for index, fact in enumerate(bank, 1):
            exploration = dict(raw="EXPLORE " + fact["node"] + " " + fact["port"], terminal=True, truncated=False)
            event = dict(raw=micro._event(fact) + "\n", terminal=True, truncated=False)
            experience = dict(fact=fact, exploration=exploration, event=event, admitted=True, error=None)
            experiences.append(experience)
            write(directory / f"EXPERIENCE_{index:02d}.json", experience)
        write(directory / "EXPERIENCES.json", experiences)
    reused = collector.load_reused_experiences(original, expected_base_sha256=BASE_SHA)
    root = parent / "cue"
    root.mkdir()
    arguments = dict(phase="readout", cue_adapter_dir="selected/adapter", adapter_dir="selected/adapter",
        adapter_collection="selected/collection", reuse_experiences=str(original.resolve()),
        explicit_cue_strategy=True, public_feedback=mode == cue.PUBLIC_FEEDBACK_MODE,
        last_turn_feedback=mode == cue.LAST_TURN_FEEDBACK_MODE, expected_base_sha256=BASE_SHA)
    metadata = dict(schema="DEV_GUIDED_EXTERNAL_EVENT_CUE_REUSE_V1", master=collector.MASTER,
        arguments=arguments, guidance=collector.EXPLICIT_GUIDANCE,
        guidance_sha256=sha256(collector.EXPLICIT_GUIDANCE.encode()).hexdigest(), teaching_mode=mode)
    write(root / "REQUEST.json", metadata)
    with patch.object(cue, "GUIDANCE", collector.EXPLICIT_GUIDANCE):
        collected = collector.collect(ReadingEngine(**engine_options), root,
            reused_experiences=reused, teaching_mode=mode)
    write(root / "RESULT.json", dict(metadata, **collected, status="COLLECTION_COMPLETE_NO_FIT",
        actor_kind="FROZEN_SAVED_MEMORY_LEARNER", actor_adapter_file_sha256=ACTOR_SHA,
        actor_adapter_state_before="c" * 64, actor_adapter_state_after="c" * 64,
        actor_training_result_sha256="d" * 64, frozen_base_unchanged=True))
    return root


class Tokenizer:
    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token_id = 0
    all_special_ids = [0, 1]

    def encode(self, text, **kwargs):
        return [1 if part == self.eos_token else ord(part) + 1000
                for part in re.findall(r"<\|im_end\|>|.", text, flags=re.S)]

    def decode(self, values, **kwargs):
        return "".join(self.eos_token if value == 1 else chr(value - 1000) for value in values)

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, **kwargs):
        text = "".join("<" + message["role"] + ">\n" + message["content"] + self.eos_token + "\n"
                       for message in messages)
        if add_generation_prompt:
            text += "<assistant>\n"
        return self.encode(text) if tokenize else text


class SourceTests(unittest.TestCase):
    def test_both_modes_replay_all_banks_and_restore_guidance(self):
        for mode in sleep.TEACHING_MODES:
            with self.subTest(mode=mode), TemporaryDirectory() as temporary:
                root = fixture(Path(temporary), mode=mode)
                with patch.object(cue, "GUIDANCE", "restore-this-guidance"):
                    rows, provenance = sleep.load_cue_rows(root, expected_actor_sha256=ACTOR_SHA)
                    self.assertEqual(cue.GUIDANCE, "restore-this-guidance")
                self.assertEqual(len(rows), 20)
                self.assertEqual(provenance["teaching_mode"], mode)
                self.assertEqual(provenance["physical_actor_calls"], 20)
                self.assertEqual([entry["successful_one_reads"] for entry in provenance["coverage"]], [2, 2])
                self.assertEqual([entry["successful_mismatch_second_reads"] for entry in provenance["coverage"]], [2, 2])
                self.assertEqual(provenance["result_sha256"], sha256((root / "RESULT.json").read_bytes()).hexdigest())
                self.assertEqual(len(provenance["row_origins"]), 20)
                for origin, row in zip(provenance["row_origins"], rows):
                    call = read(root / f"CALL_{origin['global_call_index']:03d}.json")
                    self.assertEqual(row["assistant"], call["response"]["raw"])
                    self.assertNotIn(cue.PUBLIC_FEEDBACK_PREFIX, str(row["prefix"]))
                    self.assertNotIn(collector.EXPLICIT_GUIDANCE, str(row["prefix"]))

    def test_requires_both_branches_in_each_bank(self):
        for bank in (0, 1):
            for keyword, error in (("one_read_bank", "successful_mismatch_second_read"),
                                   ("two_read_bank", "successful_one_read")):
                with self.subTest(bank=bank, keyword=keyword), TemporaryDirectory() as temporary:
                    root = fixture(Path(temporary), **{keyword: bank})
                    previous = cue.GUIDANCE
                    with self.assertRaisesRegex(ValueError, error):
                        sleep.load_cue_rows(root, expected_actor_sha256=ACTOR_SHA)
                    self.assertEqual(cue.GUIDANCE, previous)

    def test_saved_actor_mode_and_terminal_binding(self):
        faults = ("actor_kind", "actor_hash", "actor_drift", "mode", "flags", "empty", "failed", "wrong_expected")
        for fault in faults:
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                root = fixture(Path(temporary))
                result, request = read(root / "RESULT.json"), read(root / "REQUEST.json")
                if fault == "actor_kind":
                    result["actor_kind"] = "FROZEN_BASE"
                elif fault == "actor_hash":
                    result["actor_adapter_file_sha256"] = "e" * 64
                elif fault == "actor_drift":
                    result["actor_adapter_state_after"] = "e" * 64
                elif fault == "mode":
                    result["teaching_mode"] = request["teaching_mode"] = cue.DEFAULT_TEACHING_MODE
                elif fault == "flags":
                    result["arguments"]["public_feedback"] = request["arguments"]["public_feedback"] = False
                elif fault == "empty":
                    result["student_rows"] = 0
                elif fault == "failed":
                    write(root / "FAILED.json", dict(error="failed"))
                write(root / "RESULT.json", result)
                write(root / "REQUEST.json", request)
                with self.assertRaises(ValueError):
                    sleep.load_cue_rows(root, expected_actor_sha256="e" * 64 if fault == "wrong_expected" else ACTOR_SHA)

    def test_every_native_call_including_unselected_is_replayed(self):
        with TemporaryDirectory() as temporary:
            root = fixture(Path(temporary), fail_first=True)
            rows, unused = sleep.load_cue_rows(root, expected_actor_sha256=ACTOR_SHA)
            self.assertLess(len(rows), 20)
            call = read(root / "CALL_000.json")
            call["messages"][0]["content"] += "unrecorded feedback"
            call["response"]["messages"] = deepcopy(call["messages"])
            write(root / "CALL_000.json", call)
            previous = cue.GUIDANCE
            with self.assertRaisesRegex(ValueError, "replay_mismatch"):
                sleep.load_cue_rows(root, expected_actor_sha256=ACTOR_SHA)
            self.assertEqual(cue.GUIDANCE, previous)

    def test_report_rows_memory_hash_and_inventory_corruption_rejected(self):
        for fault in ("target", "public", "combined", "memory", "extra", "missing", "response"):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                root = fixture(Path(temporary), mode=cue.LAST_TURN_FEEDBACK_MODE)
                report_path = root / "BANK_01/CUE_COLLECTION.json"
                report = read(report_path)
                if fault == "target":
                    report["student_rows"][0]["assistant"] = "ROUTE P_AAAAAAAAAA"
                elif fault == "public":
                    report["student_rows"][0]["prefix"][-1]["content"] += cue.PUBLIC_FEEDBACK_PREFIX
                elif fault == "combined":
                    write(root / "BANK_RESULTS.json", [])
                elif fault == "memory":
                    memory_path = root / "BANK_01/EXPERIENCE_01.json"
                    experience = read(memory_path)
                    experience["event"]["raw"] += "\n"
                    write(memory_path, experience)
                elif fault == "extra":
                    write(root / "CALL_999.json", read(root / "CALL_000.json"))
                elif fault == "missing":
                    (root / "CALL_000.json").unlink()
                elif fault == "response":
                    call = read(root / "CALL_000.json")
                    call["response"]["raw"] = "ROUTE P_AAAAAAAAAA"
                    write(root / "CALL_000.json", call)
                write(report_path, report)
                with self.assertRaises(ValueError):
                    sleep.load_cue_rows(root, expected_actor_sha256=ACTOR_SHA)


class EncodingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = fixture(Path(self.temporary.name), mode=cue.LAST_TURN_FEEDBACK_MODE)
        self.rows, unused = sleep.load_cue_rows(self.root, expected_actor_sha256=ACTOR_SHA)

    def test_all_prior_assistant_and_memory_tokens_masked(self):
        tokenizer = Tokenizer()
        original = deepcopy(self.rows)
        encoded = sleep.encode_cue_rows(self.rows, tokenizer)
        self.assertEqual(self.rows, original)
        self.assertIsInstance(encoded, tuple)
        self.assertTrue(any(len(row["prefix"]) == 6 for row in self.rows))
        for row, tokens in zip(self.rows, encoded):
            self.assertIsInstance(tokens, sleep.native.EncodedRow)
            prefix = tokenizer.apply_chat_template(row["prefix"], tokenize=True, add_generation_prompt=True)
            expected = tuple(tokenizer.encode(row["assistant"])) + (tokenizer.eos_token_id,)
            self.assertEqual(tokens.target_ids, expected)
            self.assertEqual(tokens.labels[:len(prefix)], (-100,) * len(prefix))
            self.assertEqual(tuple(label for label in tokens.labels if label != -100), expected)
            self.assertEqual(tokens.labels[-1], -100)
            self.assertEqual(tokenizer.decode(tokens.target_ids), row["assistant"] + "<|im_end|>")
        indexes = sleep.mixed_indexes(1, len(encoded))
        combined = (encoded[0],) * 32 + encoded
        batch = sleep.native.collate([combined[index] for index in indexes], pad_id=0)
        self.assertTrue(all(label == -100 for labels, attention in zip(batch["labels"], batch["attention_mask"])
                            for label, mask in zip(labels, attention) if mask == 0))

    def test_teacher_wrong_policy_grammar_and_length_rejected(self):
        for fault in ("feedback", "guide", "system", "policy", "eot", "action", "long"):
            with self.subTest(fault=fault):
                rows = deepcopy(self.rows[:1])
                if fault == "feedback":
                    rows[0]["prefix"][-1]["content"] += cue.PUBLIC_FEEDBACK_PREFIX + "READ"
                elif fault == "guide":
                    rows[0]["prefix"][-1]["content"] += collector.EXPLICIT_GUIDANCE
                elif fault == "system":
                    rows[0]["prefix"][0]["content"] = "other system"
                elif fault == "policy":
                    rows[0]["loss_policy"]["prefix"] = "TRAIN"
                elif fault == "eot":
                    rows[0]["target_eot"] = "<eot>"
                elif fault == "action":
                    rows[0]["assistant"] = "THINK KEEP E_AAAAAAAAAA"
                elif fault == "long":
                    rows[0]["prefix"][-1]["content"] += "x" * 3000
                with self.assertRaises(ValueError):
                    sleep.encode_cue_rows(rows, Tokenizer())

    def test_nonroundtripping_and_template_mismatch_rejected(self):
        tokenizer = Tokenizer()
        with patch.object(tokenizer, "decode", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "roundtrip"):
                sleep.encode_cue_rows(self.rows[:1], tokenizer)
        original = tokenizer.apply_chat_template

        def wrong_template(messages, **kwargs):
            value = original(messages, **kwargs)
            return value + [1000] if kwargs["tokenize"] else value

        with patch.object(tokenizer, "apply_chat_template", side_effect=wrong_template):
            with self.assertRaisesRegex(ValueError, "token_ids_mismatch"):
                sleep.encode_cue_rows(self.rows[:1], tokenizer)


class ScheduleTests(unittest.TestCase):
    def test_fixed_400_memory_and_400_cue_presentations(self):
        for count in (1, 7, 20, 24):
            with self.subTest(count=count):
                presentations = Counter()
                for update in range(1, 201):
                    indexes = sleep.mixed_indexes(update, count)
                    start = 2 * (update - 1)
                    self.assertEqual(indexes, (start % 32, (start + 1) % 32,
                        32 + start % count, 32 + (start + 1) % count))
                    presentations.update(indexes)
                self.assertEqual(sum(value for index, value in presentations.items() if index < 32), 400)
                self.assertEqual(sum(value for index, value in presentations.items() if index >= 32), 400)
                self.assertEqual(Counter({event: sum(value for index, value in presentations.items()
                    if index < 32 and index % 4 == event) for event in range(4)}), Counter({event: 100 for event in range(4)}))
        for update, count in ((0, 3), (201, 3), (True, 3), (1, 0), (1, 25), (1, True)):
            with self.assertRaises(ValueError):
                sleep.mixed_indexes(update, count)

    def test_import_has_no_native_library_or_model_execution(self):
        script = """
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'peft', 'transformers', 'tokenizers'}:
        raise AssertionError('native import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import organism_v6.experienced_event_cue_sleep
"""
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
