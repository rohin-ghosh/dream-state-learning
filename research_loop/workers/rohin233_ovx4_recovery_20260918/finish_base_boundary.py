"""Operator-side handoff; privileged unit control never runs inside NNP service."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.base_boundary import finalize_pending
from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import put


def finish(root):
    root=Path(root)
    config=json.loads((root/'BOUNDARY_CONFIG.private.json').read_bytes())
    original=Path(config['original_root'])
    boundary=json.loads((root/'BOUNDARY_RESPONSE.private.json').read_bytes())
    saved=(original/'player/private/state.json').read_bytes()
    state=json.loads(saved)
    identifier=state['pending']['request']['request_id']
    assert state['pending']['kind']=='SCORE' and boundary['request']['origin']['request_id']==identifier
    response=boundary['response']
    assert response['request_id']==identifier
    result_path=original/'scorer/attempts'/identifier/'RESULT.json'
    assert hashlib.sha256(result_path.read_bytes()).hexdigest()==response['receipt_sha256']
    assert json.loads(result_path.read_bytes())['origin']==boundary['request']['origin']
    old_alive=Path('/proc',str(config['player_pid'])).exists()
    if old_alive:
        assert Path('/proc',str(config['player_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]==config['player_start_ticks']
        unit='orch-r233-recovery-attempt3-base-player-20260918.service'
        assert unit in Path('/proc',str(config['player_pid']),'cgroup').read_text()
        subprocess.run(['sudo','-n','systemctl','stop',unit],check=True,capture_output=True,timeout=20)
    assert not Path('/proc',str(config['player_pid'])).exists()
    assert (original/'player/private/state.json').read_bytes()==saved
    complete=finalize_pending(root/'finalized',state,response)
    scorer_path=original/'scorer/SESSION_STATE.private.json'
    scorer_raw=scorer_path.read_bytes();scorer=json.loads(scorer_raw)
    assert scorer['phase']=='COMPLETE' and set(scorer['seen'])=={item['source']['request_id'] for item in complete['events']}
    scorer_pid=config['scorer_pid']
    assert Path('/proc',str(scorer_pid),'stat').read_text().rsplit(')',1)[1].split()[19]==config['scorer_start_ticks']
    unit='orch-r233-recovery-attempt3-base-scorer-20260918.service'
    assert unit in Path('/proc',str(scorer_pid),'cgroup').read_text()
    subprocess.run(['sudo','-n','systemctl','stop',unit],check=True,capture_output=True,timeout=20)
    assert not Path('/proc',str(scorer_pid)).exists() and scorer_path.read_bytes()==scorer_raw
    put(root/'PRESERVED_CONTROLLER.private.json',complete)
    (root/'PRESERVED_SCORER.private.json').write_bytes(scorer_raw)
    receipt=dict(unix=time.time(),previous_pid=config['player_pid'],ACT_request_id=identifier,
        actual_result_sha256=response['receipt_sha256'],previous_ACT_count=len(state['events']),
        preserved_ACT_count=len(complete['events']),preserved_generated_tokens=complete['total_generated_tokens'],
        pending_score_finalized_once=True,scoring_calls=0,generation_calls=0,native_signals=[],
        prior_player_alive_at_operator_handoff=old_alive,
        recovery_cause='NNP blocked service-side sudo; authentic score retained before socket closure',
        confinement_unchanged=True,privileged_actions_operator_only=True)
    put(root/'BOUNDARY_READY.json',receipt)
    return receipt
