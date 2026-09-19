"""Synthetic CPU-only recovery metadata; not actual LOADED evidence."""

import copy
import pytest

from gpu import orch_r168_c5_parent_recovery_gate as gate
from gpu.orch_r125_stream_journal import _digest


def receipt():
    record=dict(kind='LOADED',index=2900,document=dict(pid=4018497,resume=True,optimizer_steps=2478))
    record['sha256']=_digest(record)
    return dict(status='ACTUAL_LOADED_SAVED28_CONTINUITY_VERIFIED',
        native=dict(pid=4018497,start_ticks='17068304',argv=['CPU_ONLY'],
            cwd='/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2/source'),
        loaded=dict(content=record,sha256='a'*64,
            path='/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life/stream/records/00000000000000002900.json'),
        config=dict(path='/CPU_CONFIG',sha256='b'*64),plan=dict(path='/CPU_PLAN',sha256='c'*64))


def test_exact_recovery_binding_no_mutation():
    source=receipt()
    before=copy.deepcopy(source)
    result=gate.child_binding(source)
    assert result['pid']==4018497 and result['loaded_ref']['sha256']=='a'*64
    assert source==before


@pytest.mark.parametrize('mutation',['not_loaded','pid','ticks','source','index','hash','resume','steps','root'])
def test_other_or_unverified_recovery_refused(mutation):
    source=receipt()
    if mutation=='not_loaded':source['status']='PREPARED'
    elif mutation=='pid':source['native']['pid']=4018498
    elif mutation=='ticks':source['native']['start_ticks']='other'
    elif mutation=='source':source['native']['cwd']='/other'
    elif mutation=='root':source['loaded']['path']='/other/2900.json'
    elif mutation=='index':source['loaded']['content']['index']=2899
    elif mutation=='hash':source['loaded']['content']['sha256']='0'*64
    else:
        source['loaded']['content']['document'][{'resume':'resume','steps':'optimizer_steps'}[mutation]]=False if mutation=='resume' else 2477
        source['loaded']['content']['sha256']=_digest({key:value for key,value in source['loaded']['content'].items() if key!='sha256'})
    with pytest.raises(ValueError):gate.child_binding(source)
