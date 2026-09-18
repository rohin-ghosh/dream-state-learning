import copy
import unittest

from batch import complete_source


class CompletionTests(unittest.TestCase):
    def documents(self):
        identity = dict(base_sha256='base', adapter_state_sha256='adapter', all_parameters_frozen=True)
        complete = dict(actual_generated_tokens=6144, cells=[dict(generated_tokens=1024) for index in range(6)],
            judge_epoch_sha256='new', source_age=dict(absolute_sleep=24), parent_tokens=0,
            training_updates=0, unchanged_identity=identity)
        loaded = dict(judge_epoch_sha256='new', source_age=dict(absolute_sleep=24), identity=identity)
        return complete, loaded

    def test_requires_actual_frozen_equal_budget_completion(self):
        complete, loaded = self.documents()
        self.assertTrue(complete_source(complete, loaded))
        for change in (dict(actual_generated_tokens=6143), dict(cells=[]),
                dict(judge_epoch_sha256='old'), dict(source_age=dict(absolute_sleep=25)),
                dict(parent_tokens=1), dict(training_updates=1)):
            with self.assertRaises(ValueError):
                complete_source(dict(complete, **change), loaded)
        changed = copy.deepcopy(complete)
        changed['unchanged_identity']['adapter_state_sha256'] = 'updated'
        with self.assertRaises(ValueError):
            complete_source(changed, loaded)


if __name__ == '__main__':
    unittest.main()
