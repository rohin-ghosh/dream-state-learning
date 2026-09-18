"""Post only verified first per-life REQUEST milestones from owned metadata."""

from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from inventory_node1 import HERE, digest, require
from parent_custody import write
from record_status import status


REPO = HERE.parents[3]


def stamp(seconds):
    return datetime.fromtimestamp(seconds, ZoneInfo('America/Los_Angeles')).isoformat()


def render_post(row, published, exposure, exposure_reference):
    cursor = exposure['cursor']
    actual = cursor['exposure']
    require(exposure['rendered'] is True and actual is not None
            and actual['exact_visible_history_and_rendered_message'] is True,
            'verified_REQUEST_only')
    require(exposure['root'] == row['root'] == published['root']
            and exposure['publication'] == published['publication'], 'same_life_and_publication')
    return ('\n## [Builder/node1 — R175 first actual RENDERED ' + row['label'] + '] ' + stamp(time.time()) + '\n\n'
        + 'First actual new-policy REQUEST exposure: **' + row['label'] + ' / assigned ' + row['arm'] + '**, inbox `'
        + published['publication']['id'] + '`. Publication origin `' + published['origin']
        + '`, acknowledged ' + stamp(published['observed_unix']) + '.\n\n'
        + 'Exact REQUEST record index `' + str(actual['record_index']) + '`, SHA `' + actual['record_sha256']
        + '`. REQUEST record filesystem mtime ' + stamp(actual['filesystem_mtime_ns'] / 1e9)
        + ' (filesystem evidence, NOT an invented inference start time); first verified observation '
        + stamp(exposure['observed_unix']) + '. Exact visible-history membership AND rendered-message match verified.\n\n'
        + 'Publication receipt `' + published['receipt']['path'] + '`, SHA `' + published['receipt']['sha256']
        + '`; exposure receipt `' + exposure_reference['path'] + '`, SHA `' + exposure_reference['sha256']
        + '`. This starts the prospective exposure-bound +3 completed-sleep clock; no behavioral PASS, LoRA effect '
        + 'or completed-cycle result is inferred. No child action or frozen-control change by this metadata reporter.\n')


def main():
    directory = HERE / 'FIRST_RENDER_REPORTER'
    directory.mkdir(exist_ok=True, mode=0o700)
    descriptor = os.open(directory / 'LOCK', os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source_paths = [Path(__file__), HERE / 'record_status.py']
    pins = {str(path): digest(path.read_bytes()) for path in source_paths}
    write(directory / ('STARTED_' + str(time.time_ns()) + '.json'), dict(pid=os.getpid(), source_pins=pins,
          observed_unix=time.time(), metadata_only=True, provider_calls=0, child_actions=0))
    while True:
        require(all(digest(Path(path).read_bytes()) == expected for path, expected in pins.items()), 'unchanged_reporter_source')
        try:
            current = status()
            for row in current['rows']:
                marker = directory / (row['label'] + '_ONCE.json')
                if marker.exists():
                    continue
                choices = [item for item in current['exposure_observations'] if item['root'] == row['root'] and item['rendered']]
                if not choices:
                    continue
                documents = [(reference, json.loads(Path(reference['path']).read_text())) for reference in choices]
                reference, exposure = min(documents, key=lambda item: item[1]['cursor']['exposure']['record_index'])
                require(digest(Path(reference['path']).read_bytes()) == reference['sha256'], 'exact_exposure_receipt_pin')
                published = next(item for item in current['actual_publications'] if item['publication'] == exposure['publication'])
                if 'origin' not in published:
                    published = dict(published, origin='ACTUAL_PROVIDER_OUTPUT', observed_unix=published['publication_returned_unix'])
                text = render_post(row, published, exposure, reference)
                write(marker, dict(status='COORD_POST_INTENT', exposure=reference, text_sha256=digest(text.encode()),
                                   observed_unix=time.time()))
                with (REPO / 'research_loop/COORDINATION.md').open('ab', buffering=0) as output:
                    require(output.write(text.encode()) == len(text.encode()), 'complete_append')
                    os.fsync(output.fileno())
                write(directory / (row['label'] + '_POSTED.json'), dict(exposure=reference,
                      observed_unix=time.time(), status='ACTUAL_RENDERED_POSTED'))
            if len(list(directory.glob('*_POSTED.json'))) == 6:
                break
            walls = [json.loads(Path(json.loads((Path(row['directory']) / 'SPEC.json').read_text())['config']).read_text())['hard_end_unix']
                     for row in current['rows']]
            if walls and time.time() >= min(walls):
                break
        except Exception as error:
            write(directory / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error_type=type(error).__name__,
                  reason=str(error), observed_unix=time.time(), no_delivery_inferred=True))
        time.sleep(60)
    os.close(descriptor)


if __name__ == '__main__':
    main()
