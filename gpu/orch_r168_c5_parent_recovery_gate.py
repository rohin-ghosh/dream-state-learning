"""Validate Main-pinned C5 recovery evidence for parent custody only."""

from gpu.orch_r125_stream_journal import _digest, require


def child_binding(continuity):
    require(continuity['status']=='ACTUAL_LOADED_SAVED28_CONTINUITY_VERIFIED','actual_C5_recovery_required')
    native=continuity['native']
    loaded=continuity['loaded']
    record=loaded['content']
    require(record['kind']=='LOADED' and record['index']==2900,'exact_C5_loaded_record')
    require(record['sha256']==_digest({key:value for key,value in record.items() if key!='sha256'}),'loaded_record_hash')
    document=record['document']
    require(native['pid']==4018497 and native['start_ticks']=='17068304'
        and document['pid']==native['pid'] and document['resume'] is True
        and document['optimizer_steps']==2478,'exact_Main_C5_recovery_identity_state')
    require(native['cwd']=='/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2/source',
        'exact_C5_recovered_native_source')
    require(loaded['path']=='/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life/stream/records/00000000000000002900.json',
        'same_C5_journal')
    return dict(pid=native['pid'],start_ticks=native['start_ticks'],argv=native['argv'],cwd=native['cwd'],
        root='/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life',
        config_ref=continuity['config'],plan_ref=continuity['plan'],
        loaded_ref=dict(path=loaded['path'],sha256=loaded['sha256'],record_sha256=record['sha256']))
