from contextlib import ExitStack
from pathlib import Path
import tempfile
import time
import unittest

from gpu import orch_r118_astra_slots as slots


class HttpSlotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'slots'

    def test_four_parallel_and_fifth_bounded_without_provider_attempt(self):
        with ExitStack() as stack:
            receipts = [stack.enter_context(slots.acquire(time.time()+60, root=self.root))
                        for index in range(4)]
            self.assertEqual({item['slot'] for item in receipts}, set(range(4)))
            self.assertTrue(all(item['provider_attempts'] == 0 for item in receipts))
            elapsed = [0]
            def advance(seconds):
                elapsed[0] += seconds
            with self.assertRaisesRegex(TimeoutError, 'preserves_provider_margin'):
                with slots.acquire(21, root=self.root, clock=lambda: elapsed[0], pause=advance):
                    self.fail('fifth request admitted')
            self.assertEqual(elapsed[0], 1)

    def test_exception_releases_slot(self):
        with self.assertRaisesRegex(RuntimeError, 'provider failed'):
            with slots.acquire(time.time()+60, root=self.root):
                raise RuntimeError('provider failed')
        with slots.acquire(time.time()+60, root=self.root) as receipt:
            self.assertEqual(receipt['slot'], 0)

    def test_deadline_never_admits_even_free_slot(self):
        with self.assertRaises(TimeoutError):
            with slots.acquire(100, root=self.root, clock=lambda: 81):
                self.fail('past provider margin')

    def test_untrusted_shared_directory_rejected(self):
        self.root.mkdir(mode=0o777)
        self.root.chmod(0o777)
        with self.assertRaisesRegex(ValueError, 'private_owned'):
            with slots.acquire(time.time()+60, root=self.root):
                self.fail('untrusted lock directory')

    def test_symlink_slot_is_not_followed(self):
        self.root.mkdir(mode=0o700)
        target = self.root.parent / 'untouched'
        target.write_text('unchanged')
        (self.root / '0').symlink_to(target)
        with self.assertRaises(OSError):
            with slots.acquire(time.time()+60, root=self.root):
                self.fail('symlink followed')
        self.assertEqual(target.read_text(), 'unchanged')


if __name__ == '__main__':
    unittest.main()
