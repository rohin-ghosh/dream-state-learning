import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r108_broker as broker
from gpu import orch_math_feedback_uptake_r108_run as runner
from gpu import orch_math_feedback_uptake_stopped as integration
from organism_v6 import orch_math_feedback_uptake_r108 as policy
import orch_math_feedback_uptake_base_test as fixture


class Node3BaseTests(unittest.TestCase):
    def test_cohorts_are_mutually_disjoint_and_exclude_whole_prior_pool(self):
        prior=fixture.tasks()
        ids={task['id'] for task in prior}
        hashes={policy.base.history.text_sha(task['question']) for task in prior}
        cohorts=policy.distinct_cohorts(ids,hashes)
        all_ids=set(ids)
        all_questions=set(hashes)
        for index in (4,5):
            tasks=[task for group in cohorts[index]['train']+cohorts[index]['held'] for task in group]
            self.assertEqual(len(tasks),20)
            for task in tasks:
                self.assertNotIn(task['id'],all_ids)
                self.assertNotIn(task['question_sha256'],all_questions)
                all_ids.add(task['id']); all_questions.add(task['question_sha256'])

    def test_reflection_multi_angle_does_not_change_original_or_readout(self):
        task=fixture.tasks()[0]
        for index in (4,5):
            scope=policy.configured(index)
            self.assertEqual(scope.messages(task),policy.base.messages(task))
            held=fixture.tasks('HELD')[0]
            self.assertEqual(scope.messages(held,purpose='held'),policy.base.messages(held,purpose='held'))
            self.assertIn(policy.REFLECTION,scope.messages(task,purpose='revision')[0]['content'])
            self.assertNotIn('quota',policy.REFLECTION)

    def test_negative_and_missing_behavior_are_not_relabelled(self):
        tasks=fixture.tasks()
        original=policy.base.history.record(tasks[0],'experience',dict(fixture.response(),raw='FINAL: 987654321'))
        self.assertFalse(original['outcome']['correct'])
        checked=policy.base.history.record(tasks[0],'check',fixture.response())
        records={tasks[0]['id']:[original,checked]}
        triples=policy.lineage_triples(4,1,records,{1:dict(sha256='a'*64)},dict(adapter=None))
        self.assertEqual(len(triples),2)
        self.assertEqual(triples[0]['child_state']['outcome'],original['outcome'])
        self.assertEqual(triples[0]['subsequent_behavior']['outcome'],checked['outcome'])
        self.assertEqual(triples[1]['subsequent_behavior']['status'],'MISSING_OR_PENDING')
        self.assertTrue(all(item['helpfulness']=='UNKNOWN_AUTHOR_REVIEW' for item in triples))
        self.assertTrue(all(item['causal_effect_claim'] is False for item in triples))
        with self.assertRaises(ValueError):
            policy.lineage_triples(4,1,{'INVALID_HELD_ID':[original]}, {}, {})

    def test_both_prior_question_hash_schemas_are_preserved(self):
        documents=[dict(excluded_question_sha256=['a'*64],nested=dict(excluded_question_hashes=['b'*64],
            question_sha256='c'*64))]
        self.assertEqual(policy.add_declared_question_hashes(documents,{'d'*64}),{letter*64 for letter in 'abcd'})

    def test_only_own_slots_and_no_adapter(self):
        for index in (4,5):
            options=policy.configured(index).options('/fixture')
            self.assertIsNone(options.adapter_dir)
            self.assertEqual(options.gpu_uuid,policy.DEVICES[index])
        for index in (0,1,2,3,6,7):
            with self.assertRaises(ValueError):
                policy.configured(index)

    def test_strong_styles_and_blind_payloads(self):
        tasks=fixture.tasks()
        records={task['id']:[policy.base.history.record(task,'experience',fixture.response())] for task in tasks}
        for index in (4,5):
            scope=policy.configured(index)
            payload=scope.parent_payload(tasks,records,1,1)
            scope.validate_parent_payload(payload)
            self.assertEqual(payload['parenting']['strength'],policy.base.STRONG)
            self.assertEqual(payload['parenting']['style'],policy.STYLES[index][0])
            self.assertNotIn('gold',json.dumps(payload))
            payload['parenting']['style']='wrong'
            with self.assertRaises(ValueError):
                scope.validate_parent_payload(payload)

    def test_node3_broker_never_routes_to_a100(self):
        store=broker.Store(Path('/repository'),Path('/node'))
        with patch.object(broker.subprocess,'run',return_value=SimpleNamespace(stdout='',returncode=0)) as run:
            store.shell('read metadata')
            self.assertIn('ovx2_ssh.sh',str(run.call_args))
            store.copy('/tmp/prefix','NODE:/node/lineage')
            self.assertIn('ovx2_scp.sh',str(run.call_args))

    def test_full_two_cycle_native_seam_on_each_pinned_style(self):
        for index in (4,5):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                original=Path(temporary).resolve()
                lane=original/f'campaign_node3_style{index}'
                lane.mkdir()
                (lane/'base_parent_queue_r107').mkdir()
                write,read=runner.common.write,runner.common.read
                write(lane/'READY.json',dict(source_files={},files={}))
                write(lane/'ACTIVATION.json',dict(native_deadline_unix=9999999999))
                write(lane/'PREVIOUS_CARRY.json',None)
                write(lane/'COHORT.json',dict(train=[fixture.tasks(),fixture.tasks()],held=[fixture.tasks('HELD')*4,fixture.tasks('HELD')*4]))
                process=['fixture',1,10]
                class Direct(fixture.FakeEngine):
                    def __init__(self,model_dir,tokenizer,device,check):
                        super().__init__(SimpleNamespace(adapter_dir=None,phase='readout'),tokenizer,check)
                    def generate(self,messages,max_new_tokens):
                        response=super().generate(messages,max_new_tokens)
                        response.pop('input_truncated')
                        response['prompt_tokens']=len(self.tokenizer.apply_chat_template(messages))
                        return response
                def deliver(unused):
                    for path in (lane/'base_parent_queue_r107').glob('*.request.json'):
                        destination=path.with_name(path.name.replace('.request.','.response.'))
                        if destination.exists():continue
                        request=read(path)
                        policy.configured(index).validate_parent_payload(request['payload'])
                        directory=original/'parent_transcripts'/lane.name/path.stem
                        directory.mkdir(parents=True)
                        write(directory/'RAW_RESPONSE.json',fixture.envelope())
                        write(directory/'PLAN.json',fixture.plan())
                        write(destination,dict(status='COMPLETE',plan=fixture.plan(),request_sha256=runner.common.sha(path),
                            archive=dict(remote_root=str(directory),files={file.name:runner.common.sha(file) for file in directory.iterdir()})))
                previous=(runner.driver.policy,runner.driver.common,runner.driver.seam)
                try:
                    with patch.dict(os.environ,CUDA_VISIBLE_DEVICES=policy.DEVICES[index]), \
                        patch.object(Path,'read_bytes',autospec=True,side_effect=lambda path:('CUDA_VISIBLE_DEVICES='+policy.DEVICES[index]).encode() if str(path)=='/proc/self/environ' else fixture.original_read_bytes(path)), \
                        patch.object(runner,'validate',return_value=dict(bundle='/fixture',model_dir='/fixture')), \
                        patch.object(runner.reuse.seam.portable,'verify_base_files',return_value=dict(expected_base_sha256=policy.base.BASE_SHA)), \
                        patch.object(runner.reuse.seam.native.source.native,'load_local_tokenizer',return_value=fixture.Tokenizer()), \
                        patch.object(runner.direct,'Engine',Direct), \
                        patch.object(integration,'engine_class',side_effect=lambda engine:engine), \
                        patch.object(runner.reuse.seam.native,'process_identity',side_effect=lambda:tuple(process)), \
                        patch.object(runner.driver.time,'sleep',side_effect=deliver):
                        for cycle in (1,2):
                            for phase in ('experience','readout'):
                                process[1]+=1
                                runner.native(original,index,cycle,phase)
                                self.assertEqual(read(lane/f'cycle{cycle}'/phase/'COMPLETE.json')['status'],'COMPLETE')
                        self.assertEqual(len(list(lane.glob('cycle*/*/CALL_*.json'))),28)
                        self.assertEqual(len(list((lane/'base_parent_queue_r107').glob('*.request.json'))),4)
                        self.assertFalse(list(lane.rglob('optimizer*')))
                        self.assertFalse(list(lane.rglob('ROWS.json')))
                        for cycle in (1,2):
                            triples=read(lane/f'cycle{cycle}/experience/R108_LINEAGE_TRIPLES.json')
                            self.assertEqual(len(triples['triples']),4)
                            self.assertTrue(all(row['parent_intervention']['binding'] for row in triples['triples']))
                            self.assertTrue(all(row['subsequent_behavior']['status']=='RECORDED' for row in triples['triples']))
                finally:
                    runner.driver.policy,runner.driver.common,runner.driver.seam=previous


if __name__=='__main__':
    unittest.main()
