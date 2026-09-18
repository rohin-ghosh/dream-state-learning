import json
from pathlib import Path
import time

from inventory_node1 import HERE, digest, identity, unchanged
from parent_custody import write
from observe_publications import publications as collect_publications


def latest_observation(paths):
    return max(paths, key=lambda path: int(path.stem.rsplit('_', 1)[1])) if paths else None


def status():
    rows = []
    for path in sorted(HERE.glob('lane*_activation_*/PARENT_ACTIVATED.json')):
        activation = json.loads(path.read_text())
        directory = path.parent
        spec = json.loads((directory / 'SPEC.json').read_text())
        config = json.loads(Path(spec['config']).read_text())
        expected = activation['actor']
        try:
            current = identity(Path('/proc') / str(expected['pid']))
            live = unchanged(expected, current) and current['state'] not in ('Z', 'X')
        except (ProcessLookupError, FileNotFoundError):
            current, live = None, False
        attempts = []
        for attempt in sorted((directory / 'parent').glob('parent_*')):
            if not attempt.is_dir():
                continue
            item = dict(path=str(attempt), status='IN_FLIGHT')
            source_path = attempt / 'SOURCE.json'
            if source_path.exists():
                source = json.loads(source_path.read_text())
                item.update(source_response_count=source['response_count'], source_head_sha256=source['head_sha256'],
                            source_record_count=source['record_count'], source_sha256=digest(source_path.read_bytes()))
            result_path = attempt / 'RESULT.json'
            if result_path.exists():
                result = json.loads(result_path.read_text())
                item.update(status=result['status'], error_type=result.get('error_type'),
                            started_unix=result['started_unix'], finished_unix=result['finished_unix'],
                            retry=result['retry'], result_sha256=digest(result_path.read_bytes()))
            marker = attempt / 'ARM_PUBLISHED.json'
            if marker.exists():
                item['publication'] = json.loads(marker.read_text())
                item['marker_sha256'] = digest(marker.read_bytes())
            attempts.append(item)
        rows.append(dict(label=activation['label'], arm=spec['arm'], root=spec['root'],
            live=live, actor=current, directory=str(directory), activation_sha256=digest(path.read_bytes()),
            config_sha256=digest(Path(spec['config']).read_bytes()), reserved_response_count=spec['reserved_response_count'],
            first_new_response_threshold=spec['reserved_response_count'] + config['cadence_responses'],
            cadence=config['cadence_responses'], word_limit=config['r175_word_limit'], attempts=attempts,
            next_turn_no_retry=True, preserved_pending_publications=spec['preserved_pending_publications']))
    published = collect_publications()
    observed = []
    for entry in published:
        path = latest_observation(list(HERE.glob('EXPOSURE_OBSERVER_*/' + entry['publication']['id'] + '_*.json')))
        if path:
            receipt = json.loads(path.read_text())
            observed.append(dict(root=entry['root'], publication=entry['publication'],
                registered=receipt['registered'], rendered=receipt['rendered'],
                completed_sleeps_after_exposure=receipt['completed_sleeps_after_exposure'],
                path=str(path), sha256=digest(path.read_bytes())))
    return dict(schema='ROHIN175_NODE1_ACTIVATION_METADATA_V1', observed_unix=time.time(), rows=rows,
                loaded_live=sum(row['live'] for row in rows), publications=len(published),
                published_lives=len({entry['root'] for entry in published}),
                rendered_lives=len({entry['root'] for entry in observed if entry['rendered']}),
                actual_publications=published, exposure_observations=observed,
                rendering_status='SEPARATE_EXPOSURE_RECEIPTS', child_actions=0,
                frozen_controls='NOT_TARGETED', peer_publications=0)


if __name__ == '__main__':
    document = status()
    output = HERE / ('ACTIVATION_STATUS_' + str(time.time_ns()) + '.json')
    write(output, document)
    print(json.dumps(dict(path=str(output), sha256=digest(output.read_bytes()),
                          loaded_live=document['loaded_live'], publications=document['publications'])))
