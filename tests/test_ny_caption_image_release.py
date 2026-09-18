import hashlib
from pathlib import Path
import tempfile
import unittest

from gpu.ny_caption_image_release import project


class ImageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        raw = b'\x89PNG\r\n\x1a\nfixture_only'
        image = self.root/'image.png'
        image.write_bytes(raw)
        reference = dict(path=str(image), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), source_url='fixture')
        self.document = dict(schema='NY_LOCAL_QWEN_IMAGE_TASKS_V1', pool='agent_development', local_Qwen_only=True,
            FINAL_included=False, historical_captions_included=False, ratings_included=False,
            source_manifest_sha256='b'*64, tasks=[dict(contest_id=str(index), image=dict(reference), policy='fixture')
                                                for index in range(19)])

    def test_exact_first_three_images_without_source_urls_or_prompts(self):
        packet, mapping, payload = project(self.document, '/localhome/local-rohing/fixture')
        self.assertEqual([row['contest_id'] for row in mapping['contests']], ['0', '1', '2'])
        self.assertEqual(len(packet['images']), 3)
        self.assertEqual(len(payload), 5)
        self.assertTrue(all(set(row) == {'handle', 'path', 'sha256', 'bytes'} for row in packet['images']))
        self.assertFalse(mapping['canonical_scenes_available'])

    def test_no_final_judge_or_caption_release(self):
        for changes in (dict(pool='judge_train'), dict(pool='final'), dict(FINAL_included=True),
                        dict(historical_captions_included=True), dict(ratings_included=True)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                project(dict(self.document, **changes), '/localhome/local-rohing/fixture')

    def test_unpinned_image_fails(self):
        self.document['tasks'][0]['image']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'exact_released_image_bytes'):
            project(self.document, '/localhome/local-rohing/fixture')

    def test_injected_caption_field_is_rejected(self):
        self.document['tasks'][0]['caption'] = 'must not release'
        with self.assertRaisesRegex(ValueError, 'no_extra_task_content'):
            project(self.document, '/localhome/local-rohing/fixture')

    def test_actual_source_size_checked_before_reading(self):
        self.document['tasks'][0]['image']['bytes'] = 1
        with self.assertRaisesRegex(ValueError, 'bounded_regular_source_image'):
            project(self.document, '/localhome/local-rohing/fixture')

    def test_duplicate_selection_and_path_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'absolute_receiving_image_root'):
            project(self.document, '/tmp/../outside')
        self.document['tasks'][1]['contest_id'] = '0'
        with self.assertRaisesRegex(ValueError, 'three_distinct_contests'):
            project(self.document, '/localhome/local-rohing/fixture')


if __name__ == '__main__':
    unittest.main()
