import ast
import inspect
import hashlib
import pytest

from gpu import ny_caption_data as data
from research_loop.workers.rohin221_continuous_caption_20260918.controller import digest

from research_loop.workers.rohin233_ovx4_recovery_20260918 import historical_recheck


def test_recheck_has_no_game_submit_or_parent_native_control():
    tree=ast.parse(inspect.getsource(historical_recheck))
    called={node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    assert not called.intersection({'submit_caption','restore','publish_inbox','send_message','kill','Popen','system'})
    assert 'seed_history' in inspect.getsource(historical_recheck.main)


def test_seed_uses_original_unicode_generation_hash_contract(tmp_path):
    text='Synthetic café caption.'
    document=dict(request={'message':'场景1'},generated={'raw':text})
    request_sha=digest(document['request'])
    assert request_sha!=data.digest(document['request'])
    generation=data.private_write(tmp_path/(request_sha+'.json'),document)
    text_sha=hashlib.sha256(text.encode()).hexdigest()
    example=dict(seed_id='synthetic',caption=text,caption_sha256=text_sha,historical_result={'rank':1},
        scene={'contest_id':'dev','description':'Synthetic scene.'},source=dict(request_sha256=request_sha,
        response_sha256=digest(document['generated']),generation_file_sha256=generation['sha256'],
        literal_span=dict(start=0,end=len(text),text_sha256=text_sha)))
    packet=data.private_write(tmp_path/'packet.json',{'examples':[example]})
    assert historical_recheck.seed_history(packet,tmp_path)[0]['caption']==text
    example['source']['response_sha256']='0'*64
    forged=data.private_write(tmp_path/'forged.json',{'examples':[example]})
    with pytest.raises(ValueError):
        historical_recheck.seed_history(forged,tmp_path)
