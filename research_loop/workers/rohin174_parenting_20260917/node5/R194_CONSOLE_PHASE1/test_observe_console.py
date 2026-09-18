"""CPU regression for the observer's actual checkpoint envelope."""

import ast
import hashlib
import json
import unittest

from observe_console import REMOTE


class CheckpointEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        definitions = [node for node in ast.parse(REMOTE).body
            if isinstance(node, ast.FunctionDef) and node.name in ('digest', 'checkpoint_state')]
        namespace = dict(hashlib=hashlib, json=json)
        exec(compile(ast.Module(body=definitions, type_ignores=[]), '<observer helpers>', 'exec'), namespace)
        cls.decode = staticmethod(namespace['checkpoint_state'])
        cls.digest = staticmethod(namespace['digest'])

    def test_context_and_training_commit_envelopes(self):
        state = dict(rows=[dict(segment=0)], history=dict(events=[]), pending=None)
        for kind in ('CONTEXT_INPUT', 'COMMITTED', 'CONTEXT_COMMITTED'):
            with self.subTest(kind=kind):
                document = dict(kind=kind, state=dict(state=state, sha256=self.digest(state)))
                self.assertEqual(self.decode(document), state)

    def test_corrupt_state_digest_rejected(self):
        with self.assertRaises(AssertionError):
            self.decode(dict(state=dict(state=dict(rows=[]), sha256='incorrect')))

    def test_raw_unwrapped_state_rejected(self):
        with self.assertRaises(KeyError):
            self.decode(dict(state=dict(rows=[])))


if __name__ == '__main__':
    unittest.main()
