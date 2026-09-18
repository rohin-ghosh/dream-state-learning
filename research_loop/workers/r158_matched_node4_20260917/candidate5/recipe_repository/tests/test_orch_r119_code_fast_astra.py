import inspect
from pathlib import Path
import subprocess

from gpu import orch_r119_code_fast_astra as fast


def test_existing_HTTP_rebound_to_low512_no_new_transport():
    runner = fast.fast_runner(fast.inherited.astra, 'task')
    assert runner.__code__.co_name == 'strong'
    assert 512 in runner.__code__.co_consts and 'low' in runner.__code__.co_consts
    assert 4096 not in runner.__code__.co_consts
    assert runner.__globals__['urllib'] is fast.inherited.astra.existing.urllib


def test_pending_listing_never_returns_previously_published_request(tmp_path):
    queue = tmp_path / 'parent_queue'
    queue.mkdir()
    for name in ('old.request.json', 'old.response.json', 'next.request.json'):
        (queue / name).write_text('{}')
    result = subprocess.run(fast.pending_listing(tmp_path), shell=True, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == 'next.request.json'
    assert len(list(queue.iterdir())) == 3


def test_fixed_prompt_builder_HTTP_slot_and_scope_remain_original():
    source = inspect.getsource(fast.serve)
    assert 'PER_EPISODE_ONLY_NO_PROVIDER' in source
    assert 'runner=fast_runner' in source
    assert 'build_system =' not in source
    assert fast.inherited.astra.http_slots.__name__ == 'gpu.orch_r118_astra_slots'
