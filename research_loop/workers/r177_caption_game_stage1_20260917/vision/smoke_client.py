"""One-shot two-image factual smoke against an already admitted LOCAL service."""

import argparse
import json
from pathlib import Path
import time

from gpu.ny_caption_vision import ImagePacket, LocalHTTPProvider, ReceiptWriter, require


QUESTION = 'What people, objects, and spatial relationships are clearly visible? State what cannot be determined.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--endpoint', default='http://[REDACTED_ADDRESS]:8177')
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    packet = ImagePacket.load(arguments.packet)
    handles = list(packet.images)[:2]
    require(len(handles) == 2, 'two_released_development_images_required')
    arguments.output.mkdir(mode=0o700)
    (arguments.output / 'REQUEST_ONCE').mkdir()
    receipts = []
    writer = ReceiptWriter(arguments.output / 'receipts')

    def record(receipt):
        writer(receipt)
        receipts.append(receipt)

    provider = LocalHTTPProvider(arguments.endpoint, packet, receipt_sink=record)
    report = dict(schema='R177_TWO_IMAGE_LOCAL_VISION_SMOKE_V1', status='STARTED',
        question=QUESTION, selection='first_two_handles_in_released_packet_order', results=[],
        factual_accuracy_independently_graded=False, model_launched_by_client=False,
        started_unix=time.time())
    try:
        for handle in handles:
            visual = provider(handle, QUESTION)
            report['results'].append(dict(image=handle, observations=visual.observations,
                uncertainty=visual.uncertainty, actual_service_receipt=receipts[-1]))
        report['status'] = 'TWO_ACTUAL_LOCAL_TOOL_RESULTS_RECEIVED'
    except Exception as error:
        report.update(status='FAILED_NO_REPAIR_NO_RETRY', error_type=type(error).__name__)
        raise
    finally:
        report['completed_unix'] = time.time()
        with (arguments.output / 'SMOKE_RECEIPT.json').open('x') as handle:
            json.dump(report, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write('\n')


if __name__ == '__main__':
    main()
