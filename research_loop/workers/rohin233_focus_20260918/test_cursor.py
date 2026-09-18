import json
from pathlib import Path
import tempfile
import unittest

from advance_p3_cursor import select_cursor


class CursorTests(unittest.TestCase):
    def test_only_same_root_journal_forward_operator_cursor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = root / 'cursors'
            store.mkdir()
            life = root / 'life'
            for name, frontier, journal, target in [('good', 40, 'one', life),
                    ('wrongjournal', 99, 'two', life), ('wronglife', 98, 'one', root / 'other'),
                    ('older', 10, 'one', life)]:
                (store / (name + '.json')).write_text(json.dumps(dict(schema='R166_VERIFIED_TRAIN_CURSOR_V1',
                    root=str(target.resolve()), next_index=frontier, journal_id=journal)))
            selected = select_cursor(store, life, 'one', 20)
            self.assertEqual(selected[0], 40)
            self.assertEqual(selected[1].name, 'good.json')
            with self.assertRaises(ValueError):
                select_cursor(store, life, 'one', 41)


if __name__ == '__main__':
    unittest.main()
