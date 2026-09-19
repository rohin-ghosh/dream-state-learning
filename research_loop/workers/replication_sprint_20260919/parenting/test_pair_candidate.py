import ast
import copy
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import paired_curriculum_policy as policy
from test_candidate import HERE, REPO, isolated_function, source_bytes


BRIEF = (HERE / 'PAIR_MIXED_CURRICULUM_BRIEF.md').read_text()


def patched_service(patch_name='PAIR_INTEGRATION.patch'):
    original = source_bytes('pair_service').decode().splitlines(keepends=True)
    patch_lines = (HERE / patch_name).read_text().splitlines(keepends=True)
    output, cursor, offset = [], 0, 0
    while offset < len(patch_lines):
        header = re.match(r'@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@', patch_lines[offset])
        if header is None:
            offset += 1
            continue
        start = int(header.group(1)) - 1
        output.extend(original[cursor:start])
        cursor = start
        offset += 1
        while offset < len(patch_lines) and not patch_lines[offset].startswith('@@'):
            line = patch_lines[offset]
            if line.startswith((' ', '-')):
                if original[cursor] != line[1:]:
                    raise ValueError('integration_patch_source_context_changed')
                if line.startswith(' '):
                    output.append(original[cursor])
                cursor += 1
            elif line.startswith('+'):
                output.append(line[1:])
            else:
                raise ValueError('unsupported_patch_line')
            offset += 1
    output.extend(original[cursor:])
    result = ''.join(output)
    ast.parse(result)
    return result


def isolated_source_parent(arm, state, patch_name='PAIR_INTEGRATION.patch'):
    original_generate = Mock(return_value={'sentinel': 'mock provider only'})
    original = REPO / 'research_loop/workers/rohin231_curriculum_birth_20260918'
    base_instruction = 'original paired schema\n' + (original / 'BIRTH_SPEC_SOURCE.md').read_text()
    original_module = SimpleNamespace(instruction=Mock(return_value=base_instruction), generate=original_generate)

    def spec_from_file_location(name, path):
        if name == 'reused_pair_parent':
            return SimpleNamespace(module=original_module, loader=SimpleNamespace(exec_module=lambda module: None))
        if name == 'paired_curriculum_policy' and path == HERE / 'paired_curriculum_policy.py':
            return SimpleNamespace(module=policy, loader=SimpleNamespace(exec_module=lambda module: None))
        raise ValueError('unexpected_module_load')

    namespace = dict(sys=SimpleNamespace(path=[]), ORIGINAL=original, REPO=REPO,
        CANDIDATE=HERE, GAP_PREFIX='My parent publisher was offline; you kept running.',
        write=Mock(), remote=Mock(),
        importlib=SimpleNamespace(util=SimpleNamespace(spec_from_file_location=spec_from_file_location,
            module_from_spec=lambda spec: spec.module)))
    tree = ast.parse(patched_service(patch_name))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'source_parent')
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(module, 'isolated_paired_source_parent_candidate', 'exec'), namespace)
    parent = namespace['source_parent'](arm, state, 9999, Path('synthetic_output_not_created'))
    return parent, original_generate, namespace


class PairedPolicyTests(unittest.TestCase):
    def test_short_treatment_uses_same_active_hook_and_original_schema(self):
        state = dict(first_turn=False, stage=0, native={'pid': 1})
        short = (HERE / 'PAIR_TASK_CHECK_BRIEF.md').read_text()
        instructions = []
        for arm in ('learner', 'frozen'):
            parent, provider, namespace = isolated_source_parent(arm, copy.deepcopy(state),
                'PAIR_TASK_CHECK_INTEGRATION.patch')
            instructions.append(parent.instruction())
            self.assertIn(short, instructions[-1])
            self.assertNotIn(BRIEF, instructions[-1])
            parent.generate(Path('synthetic_not_written'), {'stage': 0})
            provider.assert_called_once_with(Path('synthetic_not_written'), policy.bind_payload({'stage': 0}, short))
            namespace['remote'].assert_not_called()
        self.assertEqual(instructions[0], instructions[1])
        self.assertLess(len(short.split()), 240)

    def test_short_patch_differs_only_in_selected_brief(self):
        expected = patched_service().replace('PAIR_MIXED_CURRICULUM_BRIEF.md', 'PAIR_TASK_CHECK_BRIEF.md')
        self.assertEqual(patched_service('PAIR_TASK_CHECK_INTEGRATION.patch'), expected)

    def test_identical_policy_for_matched_current_stages(self):
        state = dict(first_turn=False, stage=0, native={'pid': 1})
        learner, _, _ = isolated_source_parent('learner', copy.deepcopy(state))
        frozen, _, _ = isolated_source_parent('frozen', copy.deepcopy(state))
        self.assertEqual(learner.instruction(), frozen.instruction())
        self.assertIn('Keep proposed_stage at 0', learner.instruction())
        self.assertIn('90-word budget', learner.instruction())

    def test_new_payload_bound_without_mutation_or_lost_events(self):
        payload = dict(actual_committed_child_ACTs=[{'raw': 'failed 鸟 child output'}],
            prior_parent_assessments=[], actual_previous_parent_messages=['earlier parent'], stage=0)
        before = copy.deepcopy(payload)
        result = policy.bind_payload(payload, BRIEF)
        self.assertEqual(payload, before)
        self.assertIs(result['actual_committed_child_ACTs'], payload['actual_committed_child_ACTs'])
        self.assertEqual(result['parent_policy_epoch'], policy.policy_binding(BRIEF))

    def test_do_not_rebind_prior_policy_or_pending_payload(self):
        payload = dict(parent_policy_epoch={'policy_id': 'old'})
        before = copy.deepcopy(payload)
        with self.assertRaisesRegex(ValueError, 'must_not_overwrite'):
            policy.bind_payload(payload, BRIEF)
        self.assertEqual(payload, before)

    def test_original_provider_invoked_once_only_for_explicit_generate(self):
        state = dict(first_turn=False, stage=0, native={'pid': 1},
            provider_blocked={'reason': 'preserved'}, pending_turn='old turn', provider_inflight='old')
        before = copy.deepcopy(state)
        parent, provider, namespace = isolated_source_parent('learner', state)
        provider.assert_not_called()
        parent.instruction()
        provider.assert_not_called()
        parent.generate(Path('synthetic_turn_not_created'), {'stage': 0})
        provider.assert_called_once_with(Path('synthetic_turn_not_created'),
            policy.bind_payload({'stage': 0}, BRIEF))
        namespace['write'].assert_not_called()
        namespace['remote'].assert_not_called()
        self.assertEqual(state, before)

    def test_first_outage_acknowledgment_preserved(self):
        parent, _, _ = isolated_source_parent('frozen', dict(first_turn=True, stage=0, native={}))
        self.assertIn('Your FIRST new message MUST begin exactly:', parent.instruction())
        self.assertIn('My parent publisher was offline; you kept running.', parent.instruction())

    def test_stage_and_brief_validation_no_automatic_taper(self):
        for stage in range(6):
            self.assertIn('Keep proposed_stage at ' + str(stage), policy.extend_instruction('old', stage, BRIEF))
        for stage in (-1, 6, True, '0'):
            with self.subTest(stage=stage), self.assertRaises(ValueError):
                policy.extend_instruction('old', stage, BRIEF)
        with self.assertRaises(ValueError):
            policy.policy_binding(' ')

    def test_patch_leaves_transport_ledger_assessment_and_due_logic_exact(self):
        original = ast.parse(source_bytes('pair_service'))
        proposed = ast.parse(patched_service())
        functions = ('remote', 'write', 'save', 'ref', 'seed', 'consume', 'assess', 'turn_due',
            'provider_failure', 'unresolved_provider_attempts')
        for name in functions:
            with self.subTest(function=name):
                before = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == name)
                after = next(node for node in proposed.body if isinstance(node, ast.FunctionDef) and node.name == name)
                self.assertEqual(ast.dump(before), ast.dump(after))

    def test_run_loop_only_changes_process_source_receipts(self):
        functions = []
        for source in (source_bytes('pair_service').decode(), patched_service()):
            tree = ast.parse(source)
            function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run')
            assignment = next(node for node in function.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'process' for target in node.targets))
            sources = next(keyword for keyword in assignment.value.keywords if keyword.arg == 'sources')
            sources.value = ast.Constant(value='source_receipt_only')
            functions.append(ast.dump(function))
        self.assertEqual(functions[0], functions[1])

    def test_parent_cadence_remains_original(self):
        due = isolated_function('pair_service', 'turn_due', {})
        state = dict(first_turn=False, stage=0, last_parent_cycle=10,
            events=[dict(cycle=11, response=dict(document=dict(response=dict(raw='actual artifact'))))])
        self.assertTrue(due(state))
        state['stage'] = 3
        self.assertFalse(due(state))
        state['events'][0]['cycle'] = 12
        self.assertTrue(due(state))

    def test_provider_generation_body_unchanged_and_no_new_credentials(self):
        tree = ast.parse(source_bytes('pair_provider'))
        generate = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'generate')
        calls = [node for node in ast.walk(generate) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == 'strong']
        self.assertEqual(len(calls), 1)
        self.assertEqual(next(keyword.value.value for keyword in calls[0].keywords
            if keyword.arg == 'reasoning_effort'), 'low')
        proposed = patched_service()
        original = source_bytes('pair_service').decode()
        self.assertEqual(proposed.count('NVIDIA_API_KEY'), original.count('NVIDIA_API_KEY'))

    def test_novel_passage_is_short_answer_free_training_input_not_old_recall(self):
        passage = ' '.join(line[2:] for line in BRIEF.splitlines() if line.startswith('> '))
        turn = 'Read this new passage: ' + passage + ' What detail stands out to you, and why?'
        self.assertLessEqual(len(turn.split()), 90)
        self.assertIn('not a memory test or a prior', BRIEF)
        self.assertIn('do not imply one is', BRIEF)


if __name__ == '__main__':
    unittest.main()
