"""Prospective C3-to-C3 safe handoff; only scanner observation enrichment changes."""

import argparse
import importlib.util
import inspect
from pathlib import Path


def modern_handoff_source(source):
    replacements={
        "previous/'CONTINUATION.json'":"previous/'CAMPAIGN.json'",
        "request['continuation_sha256']":"request['campaign_sha256']",
        "            segment = heartbeat['segment']":"            segment = heartbeat['segment']\n            phase_root = previous/arm/('segment%03d'%segment)",
        "previous / ('%s_%d_readout_OFF_LAUNCH.json'%(arm,segment))":"phase_root/'readout_OFF_LAUNCH.json'",
        "previous/('%s_%d_PAIRED_COMPLETE.json'%(arm,segment))":"phase_root/'PAIRED_COMPLETE.json'",
        "readout_proof(trainer,previous,arm,segment,checkpoint)":"readout_proof(trainer,phase_root,arm,segment,checkpoint)",
        "previous/('%s_%d_train_None_LAUNCH.json'%(arm,segment+1))":"previous/arm/('segment%03d'%(segment+1))/'train_None_LAUNCH.json'",
        "assert metadata['update'] <= config['activation_update'], 'activation_boundary_already_passed'":
            "assert cohort_for(metadata['update'], config['activation_update']) == 'C3', 'existing_C3_continuation_only'",
    }
    for before,after in replacements.items():
        assert source.count(before)==1, 'exact_safe_handoff_seam:'+before
        source=source.replace(before,after)
    return source


def execute(root):
    spec=importlib.util.spec_from_file_location('frozen_C3',root/'orch_r119_l1_c3_consumer.py')
    consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
    frozen,config=consumer.configuration(root)
    receipt=frozen.trainer.read(root/'SCANNER_CONTINUATION.json')
    assert receipt['arm']=='FULL' and receipt['source_sha256']==frozen.trainer.sha(__file__)
    assert receipt['campaign_sha256']==frozen.trainer.sha(root/'CAMPAIGN.json')
    assert receipt['scan_manifest_sha256']==frozen.trainer.sha(root/'SCAN_MANIFEST.json')
    pre=frozen.trainer.read(root/'PRE_GPU.json')
    assert pre['cpu_passed'] and pre['builder_line'].startswith('[Builder]')
    context=dict(consumer.__dict__)
    exec(compile(modern_handoff_source(inspect.getsource(consumer.handoff)),__file__,'exec'),context)
    context['handoff'](root,'FULL')
    from gpu import orch_combined_l1_continual_run as admission
    import orch_r119_l1_c3_scan as enrichment
    admission.scan=lambda index,service:enrichment.scan_process(root,index,service)
    consumer.supervise(root,'FULL')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    execute(parser.parse_args().root)
