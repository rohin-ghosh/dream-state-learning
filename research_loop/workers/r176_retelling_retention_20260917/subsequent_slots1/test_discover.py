from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import discover


class DiscoveryTests(unittest.TestCase):
    def pointer(self):
        root = discover.SOURCE
        record = root/'stream/records/00000000000000004123.json'
        return dict(life_id='C2',sleep=34,source_root=str(root),
            commit=dict(path=str(root/'checkpoints/sleep_000034/COMMIT.json'),sha256='a'*64),
            record=dict(path=str(record),sha256='b'*64),
            intent=dict(path=str(record.with_suffix('.intent.json')),sha256='c'*64))

    def test_exact_fixed_pointer(self):
        self.assertEqual(discover.validate_pointer(self.pointer(),34),self.pointer())

    def test_not_later_or_replacement_checkpoint(self):
        for sleep in (0,33,39):
            with self.assertRaises(ValueError):
                discover.validate_pointer(self.pointer(),sleep)

    def test_other_record_root_refused(self):
        document = self.pointer()
        document['record']['path'] = '/outside/00000000000000004123.json'
        with self.assertRaises(ValueError):
            discover.validate_pointer(document,34)


if __name__=='__main__':
    unittest.main()
