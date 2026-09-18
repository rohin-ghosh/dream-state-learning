import json
from pathlib import Path
import tempfile
import unittest
from gpu import orch_r109_l1_boundary_hold as guard


class BoundaryHoldTests(unittest.TestCase):
    def test_never_holds_pending_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'PROGRESS.json').write_text(json.dumps({'calls':2}))
            (root/'CALL_000002.json').write_text('{}')
            self.assertTrue(guard.complete(root)[0])
            (root/'INTENT_000003.json').write_text('{}')
            self.assertFalse(guard.complete(root)[0])


if __name__=='__main__':unittest.main()
