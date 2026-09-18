"""One frozen backbone, isolated rank8 adapters, actual new-string diagnostics."""

from dataclasses import asdict
import hashlib
from pathlib import Path
import threading
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_game import RelativeJudgeResult
from gpu.ny_caption_scalar_judge import ScalarJudge, relative_position
from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import EpochLedger, digest, write_once


class DualScalar:
    def __init__(self,old_config,primary_config):
        from peft.utils.save_and_load import get_peft_model_state_dict
        from safetensors.torch import load_file
        from gpu.ny_caption_scalar_judge import read_config
        self.scalar=ScalarJudge(old_config,batch_size=8)
        self.primary_config,primary_base,self.reference=read_config(primary_config)
        self.old_reference=self.scalar.reference
        old_config_data,old_base,unused=read_config(old_config)
        data.require(primary_base==old_base and self.primary_config['config']['max_length']==self.scalar.max_length,
            'same_frozen_backbone_and_scalar_input_contract')
        self.tokenizer=self.scalar.tokenizer
        self.max_length=self.scalar.max_length
        self.model_id='Qwen/Qwen2.5-7B-Instruct'
        self.lock=threading.RLock()
        self.scalar.model.load_adapter(self.primary_config['selected_adapter_root'],adapter_name='r210_15625',
            is_trainable=False,local_files_only=True)
        self.weight_proofs={}
        for alias,config in [('default',old_config_data),('r210_15625',self.primary_config)]:
            expected=load_file(config['adapter']['adapter_model.safetensors']['path'],device='cpu')
            actual=get_peft_model_state_dict(self.scalar.model,adapter_name=alias,save_embedding_layers=False)
            data.require(set(expected)==set(actual),'complete_named_adapter_and_classifier_keys')
            data.require(all(self.scalar.torch.equal(actual[key].detach().cpu(),expected[key].to(actual[key].dtype))
                for key in expected),'exact_loaded_adapter_and_classifier_values')
            self.weight_proofs[alias]=dict(tensors=len(expected),artifact_sha256=config['adapter']['adapter_model.safetensors']['sha256'],
                classifier_present=any('score' in key or 'classifier' in key for key in expected),exact_values_after_declared_dtype=True)
        self.select('r210_15625')

    def select(self,alias):
        self.scalar.model.set_adapter(alias,inference_mode=True)
        self.scalar.model.eval()
        for parameter in self.scalar.model.parameters():
            parameter.requires_grad_(False)
        data.require(not any(parameter.requires_grad for parameter in self.scalar.model.parameters()),'no_learning_during_dual_inference')

    def token_count(self,scene,caption):
        return self.scalar.token_count(scene,caption)

    def score_as(self,rows,alias):
        with self.lock:
            self.select(alias)
            try:
                return self.scalar.score(rows)
            finally:
                self.select('r210_15625')

    def score(self,rows):
        return self.score_as(rows,'r210_15625')


class EpochJudge:
    def __init__(self,dual,primary_panels,old_panels,relevance,scenes):
        self.dual,self.primary_panels,self.old_panels,self.relevance=dual,primary_panels,old_panels,relevance
        self.contests={item.canonical_scene:item.contest_id for item in scenes.contests}
        self.ledger=None
        self.origin=None
        self.pending=[]

    def __call__(self,scene,caption):
        data.require(self.ledger is not None and self.origin is not None,'actual_source_validated_request_epoch')
        result=relative_position(self.dual.score([dict(scene=scene,caption=caption)])[0],self.primary_panels[scene],50)
        relevance=dict(relevance_score=self.relevance.score(scene,caption),relevance_threshold=self.relevance.threshold)
        primary=RelativeJudgeResult(**{key:result[key] for key in ('raw_score','rank','reference_count','top_k')},**relevance)
        admitted=self.ledger.admit(self.origin,self.contests[scene],caption)
        if admitted['admitted']:
            shadow=None
            error=None
            if admitted['record']['shadow_due']:
                try:
                    prior=relative_position(self.dual.score_as([dict(scene=scene,caption=caption)],'default')[0],self.old_panels[scene],50)
                    shadow_judgment=RelativeJudgeResult(**{key:prior[key] for key in ('raw_score','rank','reference_count','top_k')},**relevance)
                    shadow=dict(asdict(shadow_judgment),accepted=shadow_judgment.accepted,status='SCORE_ONLY_NO_PIXEL_MUTATION')
                except Exception as fault:
                    error=type(fault).__name__
            self.pending.append(dict(key=admitted['key'],contest_id=self.contests[scene],caption=caption,
                shadow=shadow,shadow_error=error))
        return primary


class EpochSessionMixin:
    def process_verified(self,request,raw,*,identifier,think_resolver=None,active_scene=None):
        data.require(identifier not in self.seen,'duplicate_ACT_no_automatic_resubmit')
        judge=self.game._judge
        origin=request['origin'].get('record_sha256') or request['origin'].get('request_sha256')
        data.require(isinstance(origin,str) and len(origin)==64,'actual_generation_or_journal_origin_hash')
        judge.ledger=self.epoch_ledger
        judge.origin=origin
        judge.pending=[]
        reply=super().process_verified(request,raw,identifier=identifier,think_resolver=think_resolver,active_scene=active_scene)
        for item in judge.pending:
            primary=self.game._submissions.get((item['contest_id'],item['caption']),dict(status='UNCOMMITTED_SCORING_ERROR'))
            self.epoch_ledger.completed(item['key'],primary,item['shadow'],reply['receipt_sha256'])
        feedback=reply['report'].get('feedback',[])
        scored=[item['result'] for item in feedback if item.get('result',{}).get('ok') and not item['result'].get('replayed')]
        inherited=[item['result'] for item in feedback if item.get('result',{}).get('replayed')]
        active_path=self.epoch_ledger.root/'ACTIVE.json'
        active=data.bound(data.file_ref(active_path)) if active_path.exists() else {}
        receipt=dict(unix=time.time(),epoch_sha256=self.epoch_ledger.epoch_sha256,origin=request['origin'],
            raw_result_sha256=reply['receipt_sha256'],primary_step=15625,primary_rank=8,shadow_step=6250,
            shadow_end_unix=active.get('shadow_end_unix'),new_scored=len(scored),raw_accepted=sum(item.get('accepted') is True for item in scored),
            new_pixels=sum(item.get('status')=='new_pixel' for item in scored),inherited_cached=len(inherited),
            cached_results_keep_original_judge_not_new_exploration=True,raw_payload_included=False,
            legacy_protocol_rule_is_not_current_judge_weight_identity=True)
        write_once(self.epoch_ledger.root/('ACT_'+origin+'.json'),receipt)
        reply['judge_epoch']=receipt
        return reply


def attach_epoch(session,root,player,previous,primary_reference,old_reference):
    binding=dict(player=player,primary_step=15625,primary_rank=8,shadow_step=6250,shadow_seconds=3600,
        previous_session_sha256=previous['sha256'],new_judge_manifest_sha256=primary_reference['sha256'],
        old_judge_manifest_sha256=old_reference['sha256'],choice='HUMAN_DIRECTED_NOT_PREDECLARED_WINNER',
        previous_seen_count=len(session.seen),previous_game_sha256=data.digest(session.game.snapshot()),
        previous_policy_sha256=data.digest(session.policy.snapshot()),top_k=50,novelty_preserved=True,
        old_attempts_rescored=False,unchanged_parent_and_learning_policy=True)
    session.epoch_ledger=EpochLedger(root,binding)
    return binding
