"""Verify receiving dependencies and rebind only the three released image paths."""

import json
import os
from pathlib import Path
import subprocess
import time

from gpu import ny_caption_vision as vision
from research_loop.workers.rohin206_games_20260918.vision.service import HOME, PYTHON, once, source_pins, validate_host


validate_host()
packet = vision.strict_json((HOME / 'released_images/IMAGE_PACKET.json').read_bytes())
original_packet_sha = vision.file_digest(HOME / 'released_images/IMAGE_PACKET.json')
vision.require(original_packet_sha == 'b897b91143f18212ff280f2773c84cd01dfecab25e89b13e9ce0b6b7b2aae211', 'exact_existing_released_development_images')
for entry in packet['images']:
    entry['path'] = str(HOME / 'released_images' / Path(entry['path']).name)
images = vision.ImagePacket(packet)
for handle in images.images:
    unused, pixels = images.verified_image(handle)
    pixels.close()
once(HOME / 'IMAGE_PACKET.json', packet)
with (HOME / 'RECEIVING_CPU.log').open('x') as output:
    for directory, pattern in (('tests', 'test_ny_caption_vision.py'),
            ('research_loop/workers/rohin206_games_20260918/vision', 'test_service.py')):
        subprocess.run([PYTHON, '-B', '-m', 'unittest', 'discover', '-s', directory, '-p', pattern, '-v'],
            cwd=HOME / 'source', env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''),
            stdout=output, stderr=subprocess.STDOUT, check=True, timeout=45)
once(HOME / 'CPU_RECEIPT.json', dict(status='PASS', observed_unix=time.time(), tests=41,
    source_pins=source_pins(), original_image_packet_sha256=original_packet_sha,
    packet_sha256=vision.file_digest(HOME / 'IMAGE_PACKET.json'), actual_released_image_hashes_verified=3,
    gpu_model_loaded=False, smoke_status='ACTUAL_IMAGE_TO_SCENE_STILL_REQUIRED', no_judge_or_game_edits=True))
print(json.dumps(dict(status='RECEIVING_CPU_PASS_NOT_MODEL_LOADED', tests=41, released_images_verified=3)), flush=True)
