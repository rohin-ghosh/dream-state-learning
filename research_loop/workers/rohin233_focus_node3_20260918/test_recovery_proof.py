import unittest

from recovery_proof import wall_projection


class WallProjectionTests(unittest.TestCase):
    def test_only_bounded_evidence_not_raw_state_or_config_inference(self):
        value = dict(index=12, sha256='source', document=dict(schema='R131_WALL_EXTENDED_V1',
            authorization=dict(previous_deadline_unix=100, new_deadline_unix=200, safety_margin_seconds=21600),
            state=dict(sha256='state-source', state=dict(deadline_unix=200, private_raw='never_publish'))))
        projection = wall_projection(value, 200)
        self.assertEqual(projection['index'], 12)
        self.assertNotIn('state', projection)
        self.assertNotIn('private_raw', str(projection))
        with self.assertRaisesRegex(ValueError, 'working_state_wall'):
            wall_projection(value, 300)


if __name__ == '__main__':
    unittest.main()
