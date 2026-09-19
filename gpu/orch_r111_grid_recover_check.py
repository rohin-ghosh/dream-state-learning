"""Replay the actual interrupted prefix on CPU with all scientific writes forbidden."""

import json
from pathlib import Path
from types import SimpleNamespace

import orch_r111_grid_recover as recovery
from gpu import orch_r109_grid_run as old


class DryComplete(BaseException):
    pass


class DryReplay(recovery.Replay):
    def spend(self,root,kind,detail):
        if self.cursor==len(self.cached):
            raise DryComplete('all_saved_reservations_reconstructed_before_new_charge')
        return super().spend(root,kind,detail)

    def write(self,path,value):
        if path.name=='FAILED.json':
            recovery.require(value['error_type']=='DryComplete','unexpected_dry_failure:'+value['error_type'])
            return
        recovery.require(path.exists(),'dry_replay_would_write_new_evidence:'+str(path))
        return super().write(path,value)


def check():
    root=recovery.ROOT
    before=recovery.ref(root/'LEDGER.jsonl')
    replay=DryReplay(root,old,'segment',2)
    recovery.install(old,replay)
    loaded=recovery.read(root/'segment/cycle02/train/LOADED.json')
    ready=old.validate(root,'ovx')
    tokenizer=old.portable.source.native.load_local_tokenizer(ready['model_dir'])
    engine=SimpleNamespace(no_adapter=loaded['no_adapter'],loaded_base_sha256=loaded['base_sha256'],
        runtime=loaded['runtime'],tokenizer=tokenizer)
    engine.generate=lambda messages,**kwargs:replay.generate(None,messages,**kwargs)
    try:
        old.run(root,'ovx','segment',2,'train',shared_engine=engine)
        raise ValueError('expected_new_call_boundary')
    except DryComplete:
        pass
    recovery.require(before==recovery.ref(root/'LEDGER.jsonl'),'zero_charge_replay')
    import torch
    recovery.require(not torch.cuda.is_initialized(),'CPU_no_GPU_initialized')
    return dict(passed=True,cached_records_reconstructed=replay.cursor,
        original_native_charged=replay.initial_native,original_parent_charged=replay.initial_parent,
        cuda_initialized=False,model_loaded=False,ledger=before,new_native_calls=0,new_parent_calls=0)


if __name__=='__main__':
    print(json.dumps(check(),sort_keys=True))
