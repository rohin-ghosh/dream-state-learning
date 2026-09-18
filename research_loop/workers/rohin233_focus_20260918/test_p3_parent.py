import types
import unittest

import p3_parent
import p3_handoff


class P3ParentTests(unittest.TestCase):
    def test_preserves_payload_and_passes_highest_supported_effort(self):
        calls = []
        def strong(*arguments, **keywords):
            calls.append((arguments, keywords))
            return 'actual_result'
        policy = types.SimpleNamespace(prompt=lambda *args: ('old', 'unaltered source payload'),
            parent=types.SimpleNamespace(strong=strong))
        result = p3_parent.bind(policy, 'new brief')
        self.assertIs(result, policy)
        self.assertEqual(result.prompt({}, {}, {}), ('old\n\nnew brief', 'unaltered source payload'))
        self.assertEqual(result.parent.strong('source', reasoning_effort='low'), 'actual_result')
        self.assertEqual(calls, [(('source',), {'reasoning_effort': 'xhigh'})])

    def test_brief_preserves_evidence_and_no_exclusion(self):
        brief = (p3_parent.HERE / 'P3_BRIEF.md').read_text()
        for requirement in ('three cycles', 'Rank<=50', '160-word', 'exclude child training rows',
                            'examples', 'actual attributed Tool', 'without a fresh reminder'):
            self.assertIn(requirement.casefold(), brief.casefold())

    def test_handoff_accepts_only_exact_P3_CPU_publisher(self):
        manifest = {'predecessor_config_sha256': 'a' * 64}
        command = ['/usr/bin/python3', '-B', str(p3_parent.PREDECESSOR / 'parent.py'),
                   'serve', '--physical', '3', '--reviewed-config-sha256', 'a' * 64]
        p3_handoff.exact_parent(command, manifest)
        for index, replacement in ((2, 'native.py'), (5, '7'), (7, 'b' * 64)):
            changed = list(command)
            changed[index] = replacement
            with self.assertRaises(ValueError):
                p3_handoff.exact_parent(changed, manifest)


if __name__ == '__main__':
    unittest.main()
