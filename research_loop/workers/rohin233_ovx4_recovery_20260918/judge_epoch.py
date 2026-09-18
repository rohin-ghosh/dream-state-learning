"""Durable per-player primary/shadow epoch accounting; no model or life controls."""

import hashlib
import json
import os
from pathlib import Path
import time


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_once(path,value):
    path=Path(path)
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
    if path.exists():
        if path.read_bytes()!=raw:
            raise ValueError('immutable_epoch_receipt_collision')
        return
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def verified_source(directory,receipt_sha256,adapter_sha256,config_sha256):
    directory=Path(directory).resolve()
    references={}
    for relative,expected in [('COMPLETE.json',receipt_sha256),('adapter/adapter_model.safetensors',adapter_sha256),
        ('adapter/adapter_config.json',config_sha256)]:
        path=directory/relative
        if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('exact_completed_checkpoint_bytes')
        references[relative]=dict(sha256=expected,bytes=path.stat().st_size)
    complete=json.loads((directory/'COMPLETE.json').read_bytes())
    config=json.loads((directory/'adapter/adapter_config.json').read_bytes())
    if complete['optimizer_step']!=15625 or config['r']!=8:
        raise ValueError('rank8_step15625_not_selected_warm146')
    return dict(schema='R233_SCENE_JUDGE_SOURCE_V1',optimizer_step=15625,rank=8,artifacts=references)


class EpochLedger:
    def __init__(self,root,binding):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.binding=binding
        if binding['primary_step']!=15625 or binding['primary_rank']!=8 or binding['shadow_step']!=6250:
            raise ValueError('explicit_requested_judge_pair')
        if not binding.get('player') or binding['shadow_seconds']!=3600:
            raise ValueError('per_player_one_hour_transition')
        for field in ('previous_session_sha256','new_judge_manifest_sha256','old_judge_manifest_sha256'):
            if len(binding[field])!=64:
                raise ValueError('bound_source_and_state')
        write_once(self.root/'BINDING.json',binding)
        self.epoch_sha256=digest(binding)

    def activate(self,first_origin,unix=None):
        unix=time.time() if unix is None else unix
        path=self.root/'ACTIVE.json'
        if path.exists():
            return json.loads(path.read_bytes())
        record=dict(epoch_sha256=self.epoch_sha256,first_new_origin=first_origin,
            actual_first_score_unix=unix,shadow_end_unix=unix+3600,previous_counters_retained=True)
        write_once(path,record)
        return record

    def admit(self,origin_sha256,contest_id,caption,*,cached=False,historical=False,unix=None):
        if len(origin_sha256)!=64 or not isinstance(caption,str) or not caption:
            raise ValueError('actual_authenticated_source_and_string_required')
        if cached or historical:
            return dict(admitted=False,reason='inherited_cache_or_historical_not_new_sample')
        unix=time.time() if unix is None else unix
        active=self.activate(origin_sha256,unix)
        caption_sha256=hashlib.sha256(caption.encode()).hexdigest()
        key=digest(dict(epoch=self.epoch_sha256,contest=contest_id,caption_sha256=caption_sha256))
        path=self.root/(key+'.json')
        if path.exists():
            previous=json.loads(path.read_bytes())
            return dict(admitted=False,reason='duplicate_string_not_new_comparison',record=previous)
        record=dict(epoch_sha256=self.epoch_sha256,player=self.binding['player'],origin_sha256=origin_sha256,
            contest_id=contest_id,caption_sha256=caption_sha256,admitted_unix=unix,
            shadow_due=unix<active['shadow_end_unix'],phase='ADMITTED',shadow_counted_as_player_discovery=False,
            private_caption_payload_included=False)
        write_once(path,record)
        return dict(admitted=True,key=key,record=record)

    def completed(self,key,primary,shadow,raw_receipt_sha256):
        admitted=json.loads((self.root/(key+'.json')).read_bytes())
        if admitted['shadow_due'] and shadow is None:
            shadow_status='PENDING_OR_FAILED_NOT_A_ZERO_SCORE'
        else:
            shadow_status='COMPLETE' if shadow is not None else 'OUTSIDE_FIRST_HOUR'
        fields=('rank','accepted','status','relevance_score','top_k','reference_count')
        record=dict(admission_sha256=digest(admitted),raw_receipt_sha256=raw_receipt_sha256,
            primary={field:primary[field] for field in fields if field in primary},
            shadow={field:shadow[field] for field in fields if field in shadow} if shadow is not None else None,
            shadow_status=shadow_status,shadow_counted_as_player_discovery=False,
            interpretation='RAW_ACCEPTANCE_NOT_CERTIFIED_LITERAL_CAPTION_OR_HUMOR')
        write_once(self.root/(key+'.COMPLETE.json'),record)
        return record
