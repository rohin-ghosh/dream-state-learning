"""Bind exactly three released scenes to actual hash-verified local vision calls."""

import argparse
import json
from pathlib import Path
import time

from gpu import ny_caption_vision as vision
from gpu.ny_caption_game import DevelopmentManifest
from research_loop.workers.rohin206_games_20260918.vision.service import QUESTION, once


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--endpoint', required=True)
    options = parser.parse_args()
    packet_path = options.root / 'IMAGE_PACKET.json'
    packet = vision.ImagePacket.load(packet_path)
    vision.require(len(packet.images) == 3, 'exactly_three_released_development_images')
    output = options.root / 'game_receipts'
    output.mkdir(mode=0o700)
    receipts = []

    def record(receipt):
        once(output / (receipt['request_id'] + '.json'), receipt)
        receipts.append(receipt)

    provider = vision.LocalHTTPProvider(options.endpoint, packet, receipt_sink=record)
    contests = []
    evidence = []
    for handle in packet.images:
        try:
            result = provider(handle, QUESTION)
        except Exception as error:
            once(output / ('FAILED_' + handle + '.json'), dict(image=handle,
                observed_unix=time.time(), error=getattr(error, 'code', type(error).__name__),
                successful_manifest_claimed=False))
            raise
        receipt = receipts[-1]
        contests.append(dict(contest_id=handle, image=handle, split='agent_development',
            canonical_scene=result.observations))
        evidence.append(dict(image=handle, receipt=str(output / (receipt['request_id'] + '.json')),
            receipt_sha256=vision.file_digest(output / (receipt['request_id'] + '.json')),
            observed_unix=receipt['observed_unix'], image_sha256=receipt['image_sha256'],
            scene_sha256=vision.digest(result.observations.encode()),
            code_sha256=receipt['code_sha256'], input_tokens=receipt['input_tokens'],
            generated_tokens=receipt['generated_tokens'], canonicalization=receipt['canonicalization']))
        print(json.dumps(dict(status='ACTUAL_HTTP_IMAGE_TO_SCENE', image=handle,
            request_id=receipt['request_id'], generated_tokens=receipt['generated_tokens'])), flush=True)
    manifest = dict(mode='DEVELOPMENT', development_contest_ids=list(packet.images), contests=contests)
    DevelopmentManifest.from_mapping(manifest)
    once(options.root / 'GAME_MANIFEST.json', manifest)
    summary = dict(status='THREE_ACTUAL_RELEASED_IMAGE_SCENES', observed_unix=time.time(),
        game_manifest=str(options.root / 'GAME_MANIFEST.json'),
        game_manifest_sha256=vision.file_digest(options.root / 'GAME_MANIFEST.json'),
        image_packet=str(packet_path), image_packet_sha256=vision.file_digest(packet_path),
        endpoint=options.endpoint, route='/v1/inspect', evidence=evidence,
        model_revision=vision.REVISION, independent_scene_accuracy_verified=False,
        private_judge_data_read=False, captions_or_judge_references_sent_to_parents=False)
    once(options.root / 'GAME_MANIFEST_RECEIPT.json', summary)
    print(json.dumps({key: value for key, value in summary.items() if key != 'evidence'}), flush=True)


if __name__ == '__main__':
    main()
