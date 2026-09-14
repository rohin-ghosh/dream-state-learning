import copy
import unittest

from tools import astra_corrective_replay_reduce as reduce


class CorrectiveReducerTests(unittest.TestCase):
    def fixture(self, arm, selected=(0, 2)):
        masks = []
        for index in range(116):
            targets = [7] * (1 + index % 3) + [151645]
            masks.append(dict(input_ids=[151644] + targets + [198],
                              labels=[-100] + targets + [-100], target_ids=targets))
        losses = []
        for update in range(1, 101):
            actual, reference = reduce.indexes(update, arm, selected)
            actual_count = sum(len(masks[index]["target_ids"]) for index in actual)
            reference_count = sum(len(masks[index]["target_ids"]) for index in reference)
            scale = actual_count / reference_count
            losses.append(dict(update=update, row_indexes=actual, reference_row_indexes=reference,
                               actual_label_count=actual_count, active_label_count=actual_count,
                               reference_label_count=reference_count, original_label_count=reference_count,
                               loss_scale=scale, actual_mean_loss=0.5, loss=0.5 * scale))
        return masks, losses

    def test_exact_schedule_endpoints_and_wrapper_major_selected_rows(self):
        self.assertEqual(reduce.indexes(1, "CHILD_CORRECTIVE", [0, 2]), ([0, 64, 84, 88], [0, 64, 84, 85]))
        self.assertEqual(reduce.indexes(100, "CHILD_CORRECTIVE", [0, 2]), ([35, 83, 108, 112], [35, 83, 90, 91]))
        self.assertEqual(reduce.indexes(100, "UNIFORM_REPLAY", [0, 2]), ([35, 83, 90, 91], [35, 83, 90, 91]))

    def test_doses_and_distinct_actual_reference_denominators(self):
        for arm, expected in (("CHILD_CORRECTIVE", [104, 0, 96, 0]), ("UNIFORM_REPLAY", [50] * 4)):
            masks, losses = self.fixture(arm)
            result = reduce.audit_schedule(masks, losses, arm, [0, 2])
            self.assertEqual(result["new_event_presentations"], expected)
            self.assertEqual(list(result["budgets"].values()), [100, 100, 200, 64, 36])
        self.assertEqual(result["actual_supervised_tokens"], result["reference_supervised_tokens"])

    def test_duplicate_source_choices_are_not_deduplicated(self):
        masks, losses = self.fixture("CHILD_CORRECTIVE", [0, 0, 2])
        result = reduce.audit_schedule(masks, losses, "CHILD_CORRECTIVE", [0, 0, 2])
        self.assertEqual(result["new_event_presentations"], [136, 0, 64, 0])

    def test_source_bounds_fail_closed(self):
        for update, arm, selected in ((0, "CHILD_CORRECTIVE", [0]), (101, "CHILD_CORRECTIVE", [0]),
                                      (1, "other", [0]), (1, "CHILD_CORRECTIVE", []),
                                      (1, "CHILD_CORRECTIVE", [4]), (1, "CHILD_CORRECTIVE", [True])):
            with self.subTest(update=update, selected=selected), self.assertRaises(ValueError):
                reduce.indexes(update, arm, selected)

    def test_partial_masks_or_losses_cannot_be_terminal_results(self):
        masks, losses = self.fixture("CHILD_CORRECTIVE")
        for incomplete_masks, incomplete_losses in ((masks[:-1], losses), (masks, losses[:-1])):
            with self.assertRaises(ValueError):
                reduce.audit_schedule(incomplete_masks, incomplete_losses, "CHILD_CORRECTIVE", [0, 2])

    def test_mask_schedule_denominator_and_nonfinite_tampering_rejected(self):
        for kind in ("prefix", "target", "reference", "actual", "scale", "labels", "nan"):
            masks, losses = self.fixture("CHILD_CORRECTIVE")
            if kind == "prefix":
                masks[0]["labels"][0] = 151644
            elif kind == "target":
                masks[84]["target_ids"][0] = 9
            elif kind == "reference":
                losses[0]["reference_row_indexes"] = losses[0]["row_indexes"]
            elif kind == "actual":
                losses[0]["row_indexes"] = losses[0]["reference_row_indexes"]
            elif kind == "scale":
                losses[0]["loss_scale"] = 99
            elif kind == "labels":
                losses[0]["actual_label_count"] += 1
            else:
                losses[0]["actual_mean_loss"] = float("nan")
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                reduce.audit_schedule(masks, losses, "CHILD_CORRECTIVE", [0, 2])

    def test_driver_request_helper_result_hash_difference_is_intentional(self):
        request = dict(runner_sha256="driver", arguments={"phase": "train_corrective"})
        result = dict(request, runner_sha256="helper")
        reduce.check_request(request, result, "driver", "helper")
        with self.assertRaises(ValueError):
            reduce.check_request(request, result, "driver")
        changed = copy.deepcopy(result)
        changed["arguments"]["phase"] = "other"
        with self.assertRaises(ValueError):
            reduce.check_request(request, changed, "driver", "helper")


if __name__ == "__main__":
    unittest.main()
