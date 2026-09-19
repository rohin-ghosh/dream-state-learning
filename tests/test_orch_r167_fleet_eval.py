from contextlib import contextmanager
from copy import deepcopy
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r167_fleet_eval as evaluator


protocol = evaluator.protocol


class FleetTests(unittest.TestCase):
    def fixture(self):
        plan = dict(life_id='life', source_root='/original/life', birth_plan=dict(path='/birth', sha256='bound'),
            sleep_count=3, first_sleep=41, model_call_cap=24, generated_token_cap=12288)
        config = dict(life_id='life', sleep=41, condition='LORA_ON')
        pipeline = dict(lives=[dict(life_id='life', storage_root='/original/life',
            birth_plan=plan['birth_plan'], status='SOURCE_CANDIDATE')])
        slots = [dict(key=evaluator.queue.key('life', sleep, condition), life_id='life', sleep=sleep,
            condition=condition, model_calls=3) for sleep in (0,41,42,43) for condition in evaluator.queue.CONDITIONS]
        return config, pipeline, dict(slots=slots), plan

    def test_one_ready_life_not_blocked_by_missing_peer(self):
        config, pipeline, registration, plan = self.fixture()
        pipeline['lives'].append(dict(life_id='repo_reader', status='MISSING_CUSTODY_NOT_NEGATIVE'))
        key, life = evaluator.registered_cell(config, pipeline, registration, plan)
        self.assertEqual(life['life_id'], 'life')
        self.assertEqual(key, evaluator.queue.key('life',41,'LORA_ON'))

    def test_wrong_life_birth_or_source_refused(self):
        config, pipeline, registration, original = self.fixture()
        for field in ('life_id','source_root','birth_plan'):
            plan = dict(original, **{field:'wrong'})
            with self.subTest(field=field), self.assertRaises(ValueError):
                evaluator.registered_cell(config,pipeline,registration,plan)

    def test_wrong_or_unregistered_checkpoint_refused(self):
        config, pipeline, registration, plan = self.fixture()
        for sleep in (1,40,44):
            with self.subTest(sleep=sleep), self.assertRaisesRegex(ValueError,'exact_registered_cell'):
                evaluator.registered_cell(dict(config,sleep=sleep),pipeline,registration,plan)

    def test_control_completeness_and_duplicates(self):
        config, pipeline, registration, plan = self.fixture()
        for slots in (registration['slots'][:-1],registration['slots']+[registration['slots'][0]]):
            with self.assertRaises(ValueError):
                evaluator.registered_cell(config,pipeline,dict(slots=slots),plan)

    def test_missing_life_cannot_be_admitted(self):
        config,pipeline,registration,plan = self.fixture()
        pipeline['lives'][0]['status']='MISSING_CUSTODY_NOT_NEGATIVE'
        with self.assertRaisesRegex(ValueError,'registered_custody_candidate'):
            evaluator.registered_cell(config,pipeline,registration,plan)

    def test_prompt_context_only_original_birth(self):
        context=dict(system_prompt='system',birth_prompt='birth')
        for prompt in evaluator.queue.PROBES:
            messages=protocol.messages(context,prompt)
            self.assertEqual([item['content'] for item in messages],['system','birth',prompt])
        with self.assertRaises(ValueError):
            protocol.messages(dict(context,TRAIN='do not inject'),evaluator.queue.PROBES[0])

    def test_separate_conditions_fresh_contexts_and_frozen_weights(self):
        from gpu import orch_r130_checkpoint_benchmark as native
        from gpu import orch_r107_capability_run as conditions
        context=dict(system_prompt='system',birth_prompt='birth')
        observed=[]
        active=[]
        @contextmanager
        def readonly(model, condition):
            active.append(condition)
            yield
            active.pop()
        class Engine:
            model=object()
            tokenizer=SimpleNamespace(eos_token_id=0,apply_chat_template=lambda *args,**kwargs:[1,2])
            def generate(self,messages,max_new_tokens):
                observed.append((deepcopy(messages),max_new_tokens,tuple(active)))
                return dict(private='synthetic')
        with tempfile.TemporaryDirectory() as temporary, patch.object(native,'_snapshot',return_value={'unchanged':True}), \
                patch.object(native,'_require_readonly'),patch.object(native,'_validate_response'), \
                patch.object(conditions,'readonly_condition',readonly):
            evaluator.generate_probes(Engine(),'LORA_OFF',context,Path(temporary),{}, {},lambda label:None)
        self.assertEqual(len(observed),3)
        self.assertTrue(all(item[1:]==(512,('LORA_OFF',)) for item in observed))
        self.assertEqual([item[0][-1]['content'] for item in observed],list(evaluator.queue.PROBES))

    def test_fixed_budget_charge_before_invocation_and_no_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);config_path=root/'config.json';protocol.write(config_path,{})
            config=dict(root=str(root),pipeline=dict(sha256='fixed'),physical=0,max_job_seconds=900)
            with patch.object(evaluator.time,'time',return_value=1789638000):
                evaluator.reserve(config_path,config,dict(hard_end_unix=1789659000),'cell')
                with self.assertRaises(FileExistsError):
                    evaluator.reserve(config_path,config,dict(hard_end_unix=1789659000),'cell')
            self.assertEqual(evaluator.budget(root,'fixed')['calls_charged'],3)

    def test_budget_cap_cannot_expand(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'ledger').mkdir()
            for index in range(168):
                protocol.write(root/'ledger'/f'{index}.RESERVED.json',dict(key=str(index),pipeline_sha256='fixed',calls_charged=3,tokens_charged=1536))
            config=dict(root=str(root),pipeline=dict(sha256='fixed'),physical=0,max_job_seconds=900)
            with self.assertRaisesRegex(ValueError,'fixed_aggregate_budget'):
                evaluator.reserve(root/'config.json',config,dict(hard_end_unix=1789659000),'extra')

    def test_wall_full_window_and_not_before(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);config=dict(root=str(root),pipeline=dict(sha256='fixed'),physical=0,max_job_seconds=900)
            for now in (1789637399,1789658085,1789659000):
                with patch.object(evaluator.time,'time',return_value=now),self.assertRaisesRegex(ValueError,'full_job'):
                    evaluator.reserve(root/'config.json',config,dict(hard_end_unix=1789659000),'cell')

    def test_methods_preserve_noncoverage_truncation_and_visibility(self):
        self.assertEqual(evaluator.METHODS['max_new_tokens'],512)
        self.assertIn('NOT_NEGATIVE',evaluator.METHODS['lexical'])
        self.assertIn('NOT_ABSENT',evaluator.METHODS['truncation'])
        self.assertFalse(evaluator.METHODS['evidence_in_prompt'])
        self.assertTrue(evaluator.METHODS['private_outputs'])


if __name__ == '__main__':
    unittest.main()
