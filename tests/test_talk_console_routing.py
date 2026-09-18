import ast
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'gpu/talk.sh'


def response_reader():
    script = SCRIPT.read_text()
    embedded = script.split("py=$(cat <<'EOF'\n", 1)[1].split('\nEOF\n)', 1)[0]
    parsed = ast.parse(embedded)
    selected = [node for node in parsed.body
                if isinstance(node, ast.FunctionDef) and node.name in ('doc', 'response_text')]
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SCRIPT), 'exec'), namespace)
    return namespace['response_text']


class ReplyTextTests(unittest.TestCase):
    def test_short_raw_is_not_replaced_by_long_hash_metadata(self):
        read = response_reader()
        for text in ('ne', '-ne', 'Ne', '_ne', '', 'a' * 64):
            with self.subTest(text=text):
                record = {'sha256': 'b' * 64, 'document': {
                    'source_sha256': 'c' * 64,
                    'response': {'raw': text, 'raw_text_sha256': 'd' * 64}}}
                self.assertEqual(read(record), text)

    def test_missing_raw_does_not_guess_from_other_strings(self):
        read = response_reader()
        for document in ({'sha256': 'e' * 64}, {'response': None},
                         {'response': {'raw': None}}, {'response': {'text': 'not raw'}}):
            with self.subTest(document=document):
                self.assertIsNone(read({'document': document}))

    def test_unnested_document_keeps_exact_response(self):
        self.assertEqual(response_reader()({'response': {'raw': 'Exact\nreply.'}}), 'Exact\nreply.')


class CurrentNode3RoutingTests(unittest.TestCase):
    def dry_run(self, alias):
        return subprocess.run(['bash', str(SCRIPT), alias, 'routing check only', '--no-wait'],
                              cwd=ROOT, env={**os.environ, 'DRY_RUN': '1'},
                              capture_output=True, text=True, timeout=5)

    def test_eight_current_aliases_address_distinct_receipted_roots(self):
        expected = {
            'S_envoy': 'r213_siege_envoy_fork',
            'S_scout': 'r213_siege_scout_fork',
            'S_negotiator': 'r213_siege_negotiator_fork',
            'S_quartermaster': 'r213_siege_quartermaster_fork',
            'S_challenger': 'r213_siege_challenger_fork',
            'M_a': 'r213_math_a', 'M_b': 'r213_math_b_fork', 'M_c': 'r213_math_c',
        }
        for alias, basename in expected.items():
            with self.subTest(alias=alias):
                result = self.dry_run(alias)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'node=ovx2 root=/localhome/local-rohing/orch_r205_node3_20260918/{basename}/raw', result.stdout)

    def test_ended_aliases_fail_without_redirecting_to_new_identities(self):
        for alias in ('S_conv', 'S_lr03', 'S_lr3', 'S_p32', 'S_repo'):
            with self.subTest(alias=alias):
                result = self.dry_run(alias)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Retired node3 alias', result.stderr)
                self.assertNotIn('DELIVERED_TO_INBOX', result.stdout)

    def test_list_advertises_current_siege_and_math_aliases(self):
        result = subprocess.run(['bash', str(SCRIPT), '--list'], cwd=ROOT,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('S_envoy -> ovx2', result.stdout)
        self.assertIn('M_b -> ovx2', result.stdout)
        self.assertNotIn('S_conv ->', result.stdout)


if __name__ == '__main__':
    unittest.main()
