import copy
from types import SimpleNamespace
import unittest

from gpu.prepare_memory_mask_run import derive_corpus
from organism_v6 import memory_dose as memory


class CharacterTokenizer:
    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        if return_offsets_mapping:
            return {"offset_mapping": [(index, index + 1) for index in range(len(text))]}
        return SimpleNamespace(input_ids=[ord(character) for character in text])


class MaskRunTests(unittest.TestCase):
    def fixture(self):
        rows = [dict(context=context, target=target, kind=kind, weight=1.0,
                     mask_context=False, chat=False, event_ids=[kind]) for kind, context, target in (
                         ("fact", "Saw a car. ", "Its paint is red."),
                         ("lesson", "", "Press ARM."),
                         ("filler", "", "Six screws."),
                         ("filler_colour", "", "Door blue."))]
        return dict(corpus=rows, sha="original", items_sha="original-items",
                    stats=dict(supervised_tokens=99, by_kind={row["kind"]: 1 for row in rows}))

    def test_only_selected_mask_bytes_change(self):
        original = self.fixture()
        snapshot = copy.deepcopy(original)
        result, counts = derive_corpus(original, CharacterTokenizer())
        self.assertEqual(original, snapshot)
        for before, after in zip(original["corpus"], result["corpus"]):
            restored = dict(after, mask_context=False)
            self.assertEqual(before, restored)
            self.assertEqual(after["mask_context"], before["kind"] in ("fact", "lesson"))
        self.assertEqual(counts["changed_masks"], 2)
        self.assertEqual(counts["changed_label_items"], 1)
        self.assertEqual(counts["removed_labels"], len(original["corpus"][0]["context"]) - 1)

    def test_identities_and_shifted_token_accounting(self):
        result, counts = derive_corpus(self.fixture(), CharacterTokenizer())
        self.assertEqual(result["items_sha"], memory.items_sha(result["corpus"]))
        self.assertEqual(result["sha"], memory.sha_of([
            (memory.render_item(row), row["weight"], row["mask_context"]) for row in result["corpus"]]))
        self.assertEqual(result["stats"]["supervised_tokens"], counts["supervised_per_epoch"])
        self.assertFalse(result["mask_ablation"]["clean_lineage_eligible"])

    def test_refuse_existing_mask_or_chat(self):
        for field in ("mask_context", "chat"):
            original = self.fixture()
            original["corpus"][0][field] = True
            with self.assertRaisesRegex(ValueError, "whole-text"):
                derive_corpus(original, CharacterTokenizer())

    def test_refuse_truncation(self):
        original = self.fixture()
        original["corpus"][0]["context"] *= 1000
        with self.assertRaisesRegex(ValueError, "truncation"):
            derive_corpus(original, CharacterTokenizer())

    def test_refuse_no_supervision_change(self):
        original = self.fixture()
        original["corpus"][0]["context"] = ""
        with self.assertRaisesRegex(ValueError, "no supervision"):
            derive_corpus(original, CharacterTokenizer())


if __name__ == "__main__":
    unittest.main()
