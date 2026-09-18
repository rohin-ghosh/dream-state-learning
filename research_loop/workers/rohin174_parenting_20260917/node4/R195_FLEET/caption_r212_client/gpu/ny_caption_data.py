"""Stage1 caption data: private contest partitions and bounded public retrieval."""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
import unicodedata
import urllib.parse
import urllib.request


DATASET = 'yguooo/newyorker_caption_ranking'
AUTHOR_REPOSITORY = 'yguooo/cartoon-caption-generation'
DOWNLOAD_CAP = 2 * 1024 ** 3
POOLS = ('judge_train', 'judge_dev', 'judge_validation', 'agent_development', 'final')
EXPOSED_TRAIN_ONLY = frozenset({'530'})
DESCRIPTION_POLICY = 'IMAGE_ONLY_FACTUAL_NO_CAPTIONS_NO_UNCANNY_NO_JOKE_SUGGESTIONS_V1'
RELEASED_JUDGE_SCENE_POLICY = 'R167_RELEASED_CANNY_LOCATION_ENTITIES_JUDGE_ONLY_V1'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def private_write(path, value):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve(), 'canonical_private_artifact_path')
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    raw = value if isinstance(value, bytes) else canonical(value)
    with path.open('xb') as stream:
        os.chmod(path, 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def file_ref(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and path.is_file(), 'canonical_regular_artifact')
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for raw in iter(lambda: stream.read(1024 ** 2), b''):
            checksum.update(raw)
    return dict(path=str(path), sha256=checksum.hexdigest(), bytes=path.stat().st_size)


def bound(reference):
    actual = file_ref(reference['path'])
    require(actual['sha256'] == reference['sha256'], 'artifact_hash_mismatch')
    return json.loads(Path(reference['path']).read_bytes())


def commit_revision(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{40}', value), 'immutable_full_commit_required')
    return value


class DownloadStore:
    """Persistent pre-I/O byte reservations; failed downloads are never refunded."""

    def __init__(self, root, cap=DOWNLOAD_CAP):
        self.root = Path(root).resolve()
        require(type(cap) is int and 0 < cap <= DOWNLOAD_CAP, 'bounded_public_download_cap')
        self.cap = cap
        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)

    def fetch(self, url, relative, maximum_bytes, expected_bytes=None, expected_sha256=None):
        import fcntl
        parsed = urllib.parse.urlparse(url)
        require(parsed.scheme == 'https' and parsed.hostname in
            ('huggingface.co', 'raw.githubusercontent.com', 'api.github.com'), 'public_primary_origin_only')
        require(type(maximum_bytes) is int and 0 < maximum_bytes <= self.cap, 'finite_download_reservation')
        target = self.root / relative
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts and target == target.resolve(),
            'download_relative_path')
        operation = self.root / 'download_ledger' / (hashlib.sha256(relative.encode()).hexdigest() + '.json')
        completed = Path(str(operation) + '.complete')
        if completed.exists():
            previous = json.loads(operation.read_bytes())
            require(previous['url'] == url and previous['expected_bytes'] == expected_bytes
                and previous['expected_sha256'] == expected_sha256, 'changed_download_request')
            result = json.loads(completed.read_bytes())
            require(file_ref(target)['sha256'] == result['sha256'], 'changed_completed_download')
            return result
        with (self.root / 'download.lock').open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            rows = [json.loads(path.read_bytes()) for path in (self.root / 'download_ledger').glob('*.json')]
            require(all(type(row['reserved_bytes']) is int and row['reserved_bytes'] >= 0 for row in rows),
                'valid_download_ledger')
            require(sum(row['reserved_bytes'] for row in rows) + maximum_bytes <= self.cap, 'aggregate_public_download_cap')
            require(not operation.exists() and not target.exists(), 'download_consumed_no_automatic_retry')
            private_write(operation, dict(url=url, target=str(target), reserved_bytes=maximum_bytes,
                expected_bytes=expected_bytes, expected_sha256=expected_sha256,
                status='RESERVED_BEFORE_IO_NO_REFUND', started_unix=time.time()))
        target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        checksum, total = hashlib.sha256(), 0
        request = urllib.request.Request(url, headers={'User-Agent': 'Stage1-bounded-public-data-audit', 'Accept-Encoding': 'identity'})
        try:
            with urllib.request.urlopen(request, timeout=90) as response, target.open('xb') as destination:
                os.chmod(target, 0o600)
                length = response.headers.get('Content-Length')
                require(length is not None and 0 <= int(length) <= maximum_bytes, 'bounded_content_length_required')
                length = int(length)
                require(expected_bytes is None or length == expected_bytes, 'advertised_size_mismatch')
                while total < length:
                    raw = response.read(min(1024 ** 2, length-total))
                    require(bool(raw), 'truncated_public_download')
                    checksum.update(raw)
                    destination.write(raw)
                    total += len(raw)
                destination.flush()
                os.fsync(destination.fileno())
            require(expected_sha256 is None or checksum.hexdigest() == expected_sha256, 'public_download_hash_mismatch')
            result = dict(path=str(target), sha256=checksum.hexdigest(), bytes=total, source_url=url)
            private_write(Path(str(operation) + '.complete'), result)
            return result
        except BaseException as error:
            private_write(Path(str(operation) + '.failed'), dict(error_type=type(error).__name__, received_bytes=total))
            raise


def pin_dataset(store):
    metadata = store.fetch(f'https://[REDACTED_HOST]/api/datasets/{DATASET}?blobs=true',
        'private/hf_metadata.json', 2 * 1024 ** 2)
    document = bound(metadata)
    revision = commit_revision(document['sha'])
    files = []
    for entry in document['siblings']:
        name = entry['rfilename']
        size = entry.get('size', entry.get('lfs', {}).get('size'))
        require(type(size) is int and size >= 0, 'dataset_file_size_metadata_required')
        files.append(dict(name=name, bytes=size, lfs_sha256=entry.get('lfs', {}).get('sha256')))
    result = dict(schema='NY_DATASET_PIN_V1', dataset=DATASET, revision=revision, metadata=metadata,
        files=files, academic_noncommercial_only=True, created_unix=time.time())
    reference = private_write(store.root / 'private/DATASET_PIN.json', result)
    return dict(status='DATASET_REVISION_PINNED_NOT_RELEASED', revision=revision, file_count=len(files),
        declared_bytes=sum(row['bytes'] for row in files), pin=reference)


def download_dataset(store, pin_ref):
    pin = bound(pin_ref)
    require(pin['dataset'] == DATASET, 'exact_dataset')
    revision = commit_revision(pin['revision'])
    selected = [row for row in pin['files'] if Path(row['name']).suffix in ('.jpg', '.csv')
        or row['name'].startswith('gpt4o_description/') or row['name'] in ('README.md', 'LICENSE')]
    require(sum(row['bytes'] for row in selected) <= DOWNLOAD_CAP, 'dataset_exceeds_download_scope')
    def retrieve(row):
        reference = store.fetch(f'https://[REDACTED_HOST]/datasets/{DATASET}/resolve/{revision}/'
            + urllib.parse.quote(row['name'], safe='/'), 'private/dataset/' + row['name'],
            max(row['bytes'], 1), row['bytes'], row['lfs_sha256'])
        return dict(name=row['name'], reference=reference)
    with ThreadPoolExecutor(max_workers=4) as executor:
        files = list(executor.map(retrieve, selected))
    return private_write(store.root / 'private/DOWNLOADED.json',
        dict(schema='NY_DOWNLOADED_V1', dataset_pin=pin_ref, files=files))


def contest_key(value):
    require(type(value) in (str, int) and re.fullmatch('[0-9]{1,8}', str(value)), 'canonical_contest_id_required')
    return str(int(value))


def filename_contest(name):
    numbers = re.findall('[0-9]+', Path(name).stem)
    require(len(numbers) == 1, 'unambiguous_contest_filename_required')
    return contest_key(numbers[0])


def normalize_caption(text):
    require(type(text) is str and 0 < len(text) <= 8192, 'bounded_caption_text_required')
    text = ' '.join(unicodedata.normalize('NFKC', text).split())
    require(bool(text) and not any(unicodedata.category(char) == 'Cc' for char in text), 'nonempty_caption_required')
    return text


def rating_record(row, contest, mean_tolerance=0.000001):
    counts = []
    for name in ('not_funny', 'somewhat_funny', 'funny'):
        value = row[name]
        require(type(value) in (str, int) and re.fullmatch('[0-9]+', str(value)), 'nonnegative_integer_rating_counts')
        counts.append(int(value))
    require(type(row['votes']) in (str, int) and re.fullmatch('[0-9]+', str(row['votes'])), 'integer_votes')
    votes = int(row['votes'])
    require(votes > 0 and sum(counts) == votes, 'rating_counts_sum_to_positive_votes')
    mean = float(row['mean'])
    reconstructed = sum((index+1)*count for index, count in enumerate(counts))/votes
    require(math.isfinite(mean) and abs(mean-reconstructed) <= mean_tolerance, 'rating_mean_encoding_mismatch')
    caption = normalize_caption(row['caption'])
    return dict(contest_id=contest_key(contest), caption=caption, counts=counts, votes=votes,
        mean=reconstructed, caption_family_sha256=hashlib.sha256(caption.casefold().encode()).hexdigest())


def image_features(reference):
    from PIL import Image
    require(file_ref(reference['path'])['sha256'] == reference['sha256'], 'image_hash_mismatch')
    with Image.open(reference['path']) as image:
        require(image.width*image.height <= 40_000_000, 'bounded_image_dimensions')
        width, height = image.size
        thumbnail = image.convert('L').resize((9, 8))
        pixels = [thumbnail.getpixel((column, row)) for row in range(8) for column in range(9)]
        value = 0
        for row in range(8):
            for column in range(8):
                value = (value << 1) | int(pixels[row*9+column] > pixels[row*9+column+1])
    return dict(width=width, height=height, dhash=f'{value:016x}')


def scene_groups(contests, near_distance):
    require(type(near_distance) is int and 0 <= near_distance <= 8, 'declared_near_scene_distance')
    names = sorted(contests)
    parents = {name: name for name in names}
    def find(name):
        while parents[name] != name:
            name = parents[name]
        return name
    for position, left in enumerate(names):
        for right in names[position+1:]:
            first, second = contests[left], contests[right]
            exact = first['image']['sha256'] == second['image']['sha256']
            similar = (int(first['image_features']['dhash'], 16) ^ int(second['image_features']['dhash'], 16)).bit_count() <= near_distance
            if exact or similar:
                parents[find(right)] = find(left)
    grouped = defaultdict(list)
    for name in names:
        grouped[find(name)].append(name)
    return list(grouped.values())


def allocate_pools(groups, salt, fractions=(0.70, 0.15, 0.10, 0.05)):
    require(len(fractions) == 4 and all(0 < value < 1 for value in fractions)
        and abs(sum(fractions)-1) < 1e-9, 'four_nonfinal_split_fractions')
    all_names = [name for group in groups for name in group]
    require(len(set(all_names)) == len(all_names), 'unique_whole_contest_groups')
    forced = [group for group in groups if EXPOSED_TRAIN_ONLY.intersection(group)]
    eligible = sorted((group for group in groups if group not in forced),
        key=lambda group: digest(dict(salt=salt, group=sorted(group))))
    chosen = {0: []}
    for group in eligible:
        for size, prior in list(chosen.items())[::-1]:
            if size+len(group) <= 3 and size+len(group) not in chosen:
                chosen[size+len(group)] = prior+[group]
    require(3 in chosen, 'three_whole_contest_final_reservation_unavailable')
    final_groups = chosen[3]
    pools = {name: [] for name in POOLS}
    pools['final'] = [name for group in final_groups for name in group]
    pools['judge_train'] = [name for group in forced for name in group]
    remaining = [group for group in eligible if group not in final_groups]
    require(len(remaining) >= 6, 'insufficient_independent_scene_groups')
    target_total = len(all_names)-3
    for group in remaining:
        destination = min(POOLS[:4], key=lambda name: len(pools[name])/fractions[POOLS.index(name)])
        pools[destination].extend(group)
    require(all(pools[name] for name in POOLS) and len(pools['judge_dev']) >= 3, 'nonempty_held_contest_pools')
    require(sum(map(len, pools.values())) == target_total+3 and len(set.union(*(set(names) for names in pools.values()))) == len(all_names),
        'disjoint_exhaustive_contest_splits')
    require(EXPOSED_TRAIN_ONLY.intersection(all_names) <= set(pools['judge_train']), 'exposed_contest_training_only')
    return pools


def dev_subpools(groups, pools, salt):
    names = ('model_selection', 'probability_calibration', 'threshold_selection')
    selected = sorted((group for group in groups if set(group) <= set(pools['judge_dev'])),
        key=lambda group: digest(dict(salt=salt, dev=group)))
    require(len(selected) >= 3, 'three_held_dev_scene_groups_required')
    result = {name: [] for name in names}
    for group in selected:
        result[min(names, key=lambda name: len(result[name]))].extend(group)
    return result


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    checksum, count = hashlib.sha256(), 0
    with path.open('xb') as destination:
        os.chmod(path, 0o600)
        for row in rows:
            raw = canonical(row)+b'\n'
            destination.write(raw)
            checksum.update(raw)
            count += 1
        destination.flush()
        os.fsync(destination.fileno())
    return dict(path=str(path), sha256=checksum.hexdigest(), bytes=path.stat().st_size, rows=count)


def build_manifest(downloaded_ref, output, near_distance=2):
    downloaded = bound(downloaded_ref)
    pin = bound(downloaded['dataset_pin'])
    output = Path(output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    salt = secrets.token_hex(32)
    private_write(output / 'SPLIT_SEED.private.json', dict(salt=salt))
    files = {entry['name']: entry['reference'] for entry in downloaded['files']}
    images, tables, description_ids = {}, {}, set()
    for name, reference in files.items():
        require(file_ref(reference['path'])['sha256'] == reference['sha256'], 'downloaded_release_hash_mismatch')
        if name.endswith('.jpg'):
            key = filename_contest(name)
            require(key not in images, 'duplicate_image_contest')
            images[key] = reference
        elif name.endswith('.csv'):
            key = filename_contest(name)
            require(key not in tables, 'duplicate_rating_contest')
            tables[key] = reference
        elif name.startswith('gpt4o_description/'):
            with Path(reference['path']).open() as source:
                for line in source:
                    description_ids.add(contest_key(json.loads(line)['contest_number']))
    require(set(images) == set(tables), 'missing_image_or_rating_contest_join')
    audit = Counter()
    contests = {}
    quarantined = []
    database = output / 'caption_families.private.sqlite'
    connection = sqlite3.connect(database)
    os.chmod(database, 0o600)
    connection.execute('CREATE TABLE families (family TEXT, contest TEXT, UNIQUE(family, contest))')
    for key in sorted(images):
        try:
            features = image_features(images[key])
        except (OSError, ValueError):
            quarantined.append(dict(contest_id=key, reason='INVALID_IMAGE', image=images[key]))
            audit['invalid_image_contests_quarantined'] += 1
            continue
        rows = {}
        conflicts = set()
        with Path(tables[key]['path']).open(newline='') as source:
            for raw in csv.DictReader(source):
                audit['input_rows'] += 1
                try:
                    row = rating_record(raw, key)
                except (ValueError, KeyError, TypeError, OverflowError):
                    audit['invalid_rating_rows_quarantined'] += 1
                    continue
                family = row['caption_family_sha256']
                if family in rows:
                    audit['within_contest_duplicate_rows'] += 1
                    if rows[family]['counts'] != row['counts']:
                        conflicts.add(family)
                else:
                    rows[family] = row
        valid = [row for family, row in rows.items() if family not in conflicts]
        audit['conflicting_duplicate_families_quarantined'] += len(conflicts)
        require(bool(valid), 'contest_without_valid_ratings')
        connection.executemany('INSERT INTO families VALUES (?,?)', [(row['caption_family_sha256'], key) for row in valid])
        contests[key] = dict(image=images[key], image_features=features, canonical_scene=None,
            description_status='IMAGE_ONLY_DESCRIPTION_REQUIRED', dataset_description_present=key in description_ids,
            draft_rows=write_rows(output / 'draft_rows' / (key+'.jsonl'), valid))
    connection.commit()
    duplicated = {row[0] for row in connection.execute('SELECT family FROM families GROUP BY family HAVING COUNT(*) > 1')}
    connection.close()
    audit['cross_contest_caption_families_quarantined'] = len(duplicated)
    for key, contest in list(contests.items()):
        def filtered():
            with Path(contest['draft_rows']['path']).open() as source:
                for line in source:
                    row = json.loads(line)
                    if row['caption_family_sha256'] not in duplicated:
                        yield row
                    else:
                        audit['cross_contest_duplicate_rows_quarantined'] += 1
        contest['rows'] = write_rows(output / 'rows' / (key+'.jsonl'), filtered())
        if contest['rows']['rows'] == 0:
            quarantined.append(dict(contest_id=key, reason='NO_CROSS_CONTEST_UNIQUE_RATINGS', image=contest['image']))
            audit['no_unique_rating_contests_quarantined'] += 1
            del contests[key]
            continue
        del contest['draft_rows']
    quarantine = private_write(output / 'QUARANTINE.private.json', quarantined)
    groups = scene_groups(contests, near_distance)
    pools = allocate_pools(groups, salt)
    manifest = dict(schema='NY_PRIVATE_DATA_MANIFEST_V1', dataset=DATASET, revision=pin['revision'],
        dataset_pin=downloaded['dataset_pin'], downloaded=downloaded_ref, pools=pools,
        judge_dev_subpools=dev_subpools(groups, pools, salt), contests=contests,
        scene_groups=groups, near_duplicate_policy=dict(method='SHA256_OR_DHASH_HAMMING', distance=near_distance,
            independently_validated=False), description_policy=DESCRIPTION_POLICY,
        historical_captions_agent_parent_access=False, final_release_authorized=False,
        exposed_training_only=sorted(EXPOSED_TRAIN_ONLY), precision_used=False,
        mean_reconstruction_tolerance=0.000001, quarantine=quarantine, audit=dict(audit), created_unix=time.time())
    reference = private_write(output / 'DATA_MANIFEST.private.json', manifest)
    public = dict(schema='NY_PUBLIC_DATA_STATUS_V1', status='JOINED_SPLIT_AND_SEALED_IMAGE_DESCRIPTIONS_PENDING',
        dataset=DATASET, revision=pin['revision'], contest_count=len(contests), scene_group_count=len(groups),
        pool_counts={name: len(values) for name, values in pools.items()},
        rating_rows=sum(row['rows']['rows'] for row in contests.values()), audit=dict(audit),
        private_manifest=reference, description_ready_count=0, final_unused=True,
        historical_captions_released=False, precision_used=False, human_validated=False)
    private_write(output / 'PUBLIC_STATUS.json', public)
    return public


def load_manifest(manifest_ref):
    manifest = bound(manifest_ref)
    require(manifest['schema'] == 'NY_PRIVATE_DATA_MANIFEST_V1'
        and manifest['historical_captions_agent_parent_access'] is False
        and manifest['final_release_authorized'] is False
        and manifest['description_policy'] == DESCRIPTION_POLICY, 'private_stage1_manifest_required')
    commit_revision(manifest['revision'])
    pools = manifest['pools']
    require(set(pools) == set(POOLS) and all(type(names) is list and names for names in pools.values()),
        'five_nonempty_contest_pools_required')
    names = [name for pool in pools.values() for name in pool]
    require(len(names) == len(set(names)) and set(names) == set(manifest['contests'])
        and len(pools['final']) == 3, 'disjoint_exhaustive_three_FINAL_required')
    require(EXPOSED_TRAIN_ONLY.intersection(names) <= set(pools['judge_train']), 'exposed_contest_training_only')
    groups = manifest['scene_groups']
    grouped = [name for group in groups for name in group]
    require(len(grouped) == len(set(grouped)) and set(grouped) == set(names)
        and all(group and any(set(group) <= set(pool) for pool in pools.values()) for group in groups),
        'scene_groups_must_not_cross_pools')
    subsets = manifest['judge_dev_subpools']
    require(set(subsets) == {'model_selection', 'probability_calibration', 'threshold_selection'}
        and all(subsets.values()), 'three_nonempty_held_dev_subpools')
    dev_names = [name for subset in subsets.values() for name in subset]
    require(len(dev_names) == len(set(dev_names)) and set(dev_names) == set(pools['judge_dev'])
        and all(not set(group).intersection(dev_names) or any(set(group) <= set(subset)
            for subset in subsets.values()) for group in groups), 'disjoint_held_dev_scene_subpools')
    return manifest


def description_tasks(manifest_ref, pool):
    manifest = load_manifest(manifest_ref)
    require(pool in POOLS[:-1], 'FINAL_DESCRIPTION_ACCESS_FORBIDDEN')
    return [dict(contest_id=key, image=manifest['contests'][key]['image'], policy=DESCRIPTION_POLICY)
        for key in manifest['pools'][pool]]


def verify_scene_producer(contest, scene, producer_ref):
    require(type(scene) is str and 40 <= len(scene) <= 8000
        and not re.search(r'\b(uncanny|punchline|caption|humor|joke)\b', scene, re.I), 'factual_neutral_scene_required')
    producer = bound(producer_ref)
    require(producer.get('local_model') is True and producer.get('model_family') == 'Qwen'
        and producer.get('hosted_provider') is False, 'local_Qwen_image_description_only')
    model = bound(producer['model_manifest'])
    require(model['model_family'] == 'Qwen' and model['local_model'] is True and model['frozen'] is True,
        'frozen_local_Qwen_description_manifest')
    require(producer['input_kinds'] == ['image'] and producer['image'] == contest['image']
        and producer['policy'] == DESCRIPTION_POLICY and producer['historical_captions_used'] is False
        and producer['uncanny_used'] is False and producer['parent_history_used'] is False
        and producer['output_sha256'] == hashlib.sha256(scene.encode()).hexdigest(), 'image_only_description_provenance_required')
    require(file_ref(contest['image']['path'])['sha256'] == contest['image']['sha256'], 'description_image_changed')


def attach_descriptions(manifest_ref, descriptions, destination):
    manifest = load_manifest(manifest_ref)
    for item in descriptions:
        key = contest_key(item['contest_id'])
        require(key in manifest['contests'] and key not in manifest['pools']['final'], 'unreleased_or_unknown_description_contest')
        require(set(item) == {'contest_id', 'scene', 'producer_receipt'}, 'description_has_no_reference_caption_channel')
        scene = item['scene']
        verify_scene_producer(manifest['contests'][key], scene, item['producer_receipt'])
        require(manifest['contests'][key]['canonical_scene'] is None, 'description_version_change_requires_new_manifest')
        manifest['contests'][key].update(canonical_scene=scene, description_producer=item['producer_receipt'],
            description_status='IMAGE_ONLY_PROVENANCE_BOUND_NOT_HUMAN_VALIDATED')
    manifest['prior_manifest'] = manifest_ref
    return private_write(Path(destination).resolve(), manifest)


def development_packet(manifest_ref, destination):
    manifest = load_manifest(manifest_ref)
    scenes = []
    for key in manifest['pools']['agent_development']:
        contest = manifest['contests'][key]
        require(key not in EXPOSED_TRAIN_ONLY and contest['canonical_scene'] is not None, 'development_image_description_not_ready')
        verify_scene_producer(contest, contest['canonical_scene'], contest['description_producer'])
        scenes.append(dict(contest_id=key, image=contest['image'], scene=contest['canonical_scene']))
    return private_write(Path(destination).resolve(), dict(schema='NY_AGENT_DEVELOPMENT_PACKET_V1',
        mode='DEVELOPMENT', scenes=scenes, identical_for_both_lanes=True, human_captions_included=False,
        final_included=False, source_manifest_sha256=manifest_ref['sha256']))


def evaluator_rows(manifest_ref, pool, dev_subset=None, contest_ids=None):
    manifest = load_manifest(manifest_ref)
    require(pool in ('judge_train', 'judge_dev', 'judge_validation'), 'evaluator_training_pool_only_FINAL_FORBIDDEN')
    keys = manifest['pools'][pool]
    if dev_subset is not None:
        require(pool == 'judge_dev' and dev_subset in manifest['judge_dev_subpools'], 'declared_held_dev_subset')
        keys = manifest['judge_dev_subpools'][dev_subset]
    if contest_ids is not None:
        require(type(contest_ids) is list and contest_ids and len(contest_ids) == len(set(contest_ids))
            and set(contest_ids) <= set(keys), 'selected_contests_within_declared_pool')
        require(all(not set(group).intersection(contest_ids) or set(group) <= set(contest_ids)
            for group in manifest['scene_groups']), 'whole_scene_group_selection_required')
        keys = contest_ids
    groups = {key: digest(sorted(group)) for group in manifest['scene_groups'] for key in group}
    released = None
    if manifest.get('judge_scene_policy') == RELEASED_JUDGE_SCENE_POLICY:
        require(pool in ('judge_train', 'judge_dev'), 'released_scenes_development_only')
        released = bound(manifest['judge_scene_catalog'])
        require(released['policy'] == RELEASED_JUDGE_SCENE_POLICY
            and released['revision'] == manifest['revision']
            and released['source_name'] == 'gpt4o_description/train.jsonl'
            and released['fields'] == ['canny', 'location', 'entities']
            and released['uncanny_used'] is False, 'bound_released_factual_scene_catalog')
    for key in keys:
        contest = manifest['contests'][key]
        if released is None:
            require(contest['canonical_scene'] is not None, 'image_only_judge_description_not_ready')
            verify_scene_producer(contest, contest['canonical_scene'], contest['description_producer'])
            scene = contest['canonical_scene']
        else:
            facts = released['scenes'][key]['facts']
            scene = released_judge_scene(facts)
            require(digest(facts) == released['scenes'][key]['facts_sha256'], 'released_scene_projection_hash')
        require(file_ref(contest['rows']['path'])['sha256'] == contest['rows']['sha256'], 'private_caption_rows_changed')
        with Path(contest['rows']['path']).open() as source:
            for line in source:
                row = json.loads(line)
                require(row['contest_id'] == key, 'caption_contest_join_mismatch')
                yield dict(row, scene=scene, scene_group_sha256=groups[key])


def released_judge_scene(facts):
    require(set(facts) == {'canny', 'location', 'entities'}, 'exact_released_factual_fields')
    require(all(type(facts[name]) is str and facts[name].strip() for name in ('canny', 'location'))
        and type(facts['entities']) is list and facts['entities']
        and all(type(item) is str and item.strip() for item in facts['entities']), 'valid_released_factual_fields')
    scene = canonical(facts).decode()
    require(40 <= len(scene) <= 8000 and '\\u0000' not in scene, 'bounded_released_judge_scene')
    return scene


def build_released_development(manifest_ref, destination, *, seed=177):
    manifest = load_manifest(manifest_ref)
    require(type(seed) is int, 'integer_development_seed')
    downloaded = bound(manifest['downloaded'])
    require(downloaded['dataset_pin']['sha256'] == manifest['dataset_pin']['sha256'], 'released_dataset_pin_binding')
    pin = bound(manifest['dataset_pin'])
    require(pin['revision'] == manifest['revision'], 'released_dataset_revision_binding')
    matches = [entry['reference'] for entry in downloaded['files'] if entry['name'] == 'gpt4o_description/train.jsonl']
    require(len(matches) == 1, 'one_pinned_released_train_description_file')
    source_ref = matches[0]
    require(file_ref(source_ref['path'])['sha256'] == source_ref['sha256'], 'released_description_hash_mismatch')
    permitted = set(manifest['pools']['judge_train'] + manifest['pools']['judge_dev'])
    scenes, invalid, seen = {}, set(), set()
    with Path(source_ref['path']).open() as stream:
        for line in stream:
            row = json.loads(line)
            key = str(row['contest_number'])
            if key not in permitted:
                continue
            if key in seen:
                invalid.add(key)
            seen.add(key)
            try:
                facts = {name: row[name] for name in ('canny', 'location', 'entities')}
                released_judge_scene(facts)
                scenes[key] = dict(facts=facts, facts_sha256=digest(facts))
            except (KeyError, ValueError):
                invalid.add(key)
    eligible = set(scenes) - invalid
    groups = sorted(manifest['scene_groups'], key=lambda group: digest(dict(manifest=manifest_ref['sha256'], seed=seed, group=sorted(group))))
    def available(names):
        return [group for group in groups if set(group) <= set(names) and set(group) <= eligible]
    subsets = {'judge_train': [name for group in available(manifest['pools']['judge_train']) for name in group]}
    for name in ('model_selection', 'probability_calibration'):
        subsets[name] = [key for group in available(manifest['judge_dev_subpools'][name]) for key in group]
    threshold_groups = available(manifest['judge_dev_subpools']['threshold_selection'])
    for offset, name in enumerate(('threshold_selection', 'development_audit')):
        subsets[name] = [key for group in threshold_groups[offset::2] for key in group]
    require(all(sum(bool(set(group).intersection(names)) for group in groups) >= 2 for names in subsets.values()),
        'two_independent_scene_groups_per_development_subset')
    output = Path(destination).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    selected = {name for names in subsets.values() for name in names}
    catalog = private_write(output/'SCENE_CATALOG.private.json', dict(policy=RELEASED_JUDGE_SCENE_POLICY,
        revision=manifest['revision'], source_name='gpt4o_description/train.jsonl', source=source_ref,
        fields=['canny', 'location', 'entities'], scenes={name: scenes[name] for name in sorted(selected)},
        uncanny_used=False, candidate_or_reference_captions_read_during_scene_assembly=False,
        source_provenance='RELEASED_DATASET_NOT_NEW_LOCAL_QWEN_GENERATION', independently_image_verified=False))
    plan = private_write(output/'DEVELOPMENT_PLAN.private.json', dict(schema='NY_PREDECLARED_DEVELOPMENT_JUDGE_PLAN_V1',
        source_manifest=manifest_ref, seed=seed, subsets=subsets,
        selection='ALL_AVAILABLE_RELEASED_TRAIN_SCENES_WHOLE_GROUPS_HASH_SEEDED_DEV_AUDIT',
        permitted_pools=['judge_train', 'judge_dev'], locked_judge_validation_consumed=False,
        FINAL_consumed=False, adaptation_to_observed_scores=False, human_validated=False))
    ready = private_write(output/'DATA_MANIFEST.private.json', dict(manifest, prior_manifest=manifest_ref,
        judge_scene_policy=RELEASED_JUDGE_SCENE_POLICY, judge_scene_catalog=catalog))
    status = dict(schema='NY_RELEASED_DEVELOPMENT_ASSEMBLY_V1', source_manifest=manifest_ref, data_manifest=ready,
        development_plan=plan, scene_catalog=catalog, scene_source_sha256=source_ref['sha256'],
        selected_contests={name: len(names) for name, names in subsets.items()},
        missing_or_invalid_contests={name: len(set(manifest['pools'][name])-selected) for name in ('judge_train', 'judge_dev')},
        malformed_or_duplicate_count=len(invalid), locked_validation_consumed=False, FINAL_consumed=False,
        human_validated=False, provisional=True)
    private_write(output/'PUBLIC_STATUS.json', status)
    return status


def build_development_plan(manifest_ref, destination, *, seed=177, training_contests=32, held_contests=4):
    manifest = load_manifest(manifest_ref)
    require(type(seed) is int and type(training_contests) is int and type(held_contests) is int
        and 2 <= training_contests <= 262 and 2 <= held_contests <= 56, 'bounded_predeclared_development_contest_caps')
    groups = sorted(manifest['scene_groups'], key=lambda group: digest(dict(manifest=manifest_ref['sha256'], seed=seed, group=sorted(group))))
    selected = set()
    def select(available, cap):
        names, count = [], 0
        for group in groups:
            if set(group) <= set(available) and not set(group).intersection(selected) and len(names)+len(group) <= cap:
                names.extend(group)
                selected.update(group)
                count += 1
        require(count >= 2, 'two_independent_scene_groups_per_development_subset')
        return names
    subsets = dict(judge_train=select(manifest['pools']['judge_train'], training_contests))
    for name in ('model_selection', 'probability_calibration', 'threshold_selection'):
        subsets[name] = select(manifest['judge_dev_subpools'][name], held_contests)
    subsets['development_audit'] = select(manifest['judge_dev_subpools']['threshold_selection'], held_contests)
    plan = dict(schema='NY_PREDECLARED_DEVELOPMENT_JUDGE_PLAN_V1', source_manifest=manifest_ref, seed=seed,
        subsets=subsets, selection='SOURCE_HASH_SEED_WHOLE_GROUPS_BEFORE_CAPTION_OR_RATING_READ',
        permitted_pools=['judge_train', 'judge_dev'], locked_judge_validation_consumed=False,
        FINAL_consumed=False, adaptation_to_observed_scores=False, human_validated=False)
    return private_write(Path(destination).resolve(), plan)


def load_development_plan(plan_ref, manifest_ref):
    manifest, plan = load_manifest(manifest_ref), bound(plan_ref)
    require(plan['schema'] == 'NY_PREDECLARED_DEVELOPMENT_JUDGE_PLAN_V1'
        and plan['source_manifest']['sha256'] == manifest_ref['sha256']
        and plan['permitted_pools'] == ['judge_train', 'judge_dev']
        and plan['locked_judge_validation_consumed'] is False and plan['FINAL_consumed'] is False
        and plan['adaptation_to_observed_scores'] is False, 'bound_train_dev_only_development_plan')
    subsets = plan['subsets']
    require(set(subsets) == {'judge_train', 'model_selection', 'probability_calibration', 'threshold_selection', 'development_audit'},
        'exact_development_subsets')
    all_names = [name for names in subsets.values() for name in names]
    require(len(all_names) == len(set(all_names)), 'disjoint_development_subsets')
    for subset, names in subsets.items():
        available = manifest['pools']['judge_train'] if subset == 'judge_train' else manifest['judge_dev_subpools'][
            'threshold_selection' if subset == 'development_audit' else subset]
        require(names and set(names) <= set(available) and all(not set(group).intersection(names) or set(group) <= set(names)
            for group in manifest['scene_groups']), 'development_subset_pool_and_whole_group_binding')
        require(sum(bool(set(group).intersection(names)) for group in manifest['scene_groups']) >= 2,
            'two_independent_scene_groups_per_development_subset')
    return plan


def development_description_packet(manifest_ref, plan_ref, destination):
    manifest, plan = load_manifest(manifest_ref), load_development_plan(plan_ref, manifest_ref)
    names = [name for subset in plan['subsets'].values() for name in subset]
    return private_write(Path(destination).resolve(), dict(schema='NY_LOCAL_QWEN_IMAGE_TASKS_V1',
        source_manifest_sha256=manifest_ref['sha256'], development_plan_sha256=plan_ref['sha256'],
        local_Qwen_only=True, human_captions_included=False, ratings_included=False, FINAL_included=False,
        tasks=[dict(contest_id=name, image=manifest['contests'][name]['image'], policy=DESCRIPTION_POLICY) for name in names]))


def attach_description_bundle(manifest_ref, packet_ref, bundle_ref, destination):
    packet, bundle = bound(packet_ref), bound(bundle_ref)
    require(packet['schema'] == 'NY_LOCAL_QWEN_IMAGE_TASKS_V1' and packet['local_Qwen_only'] is True
        and packet['source_manifest_sha256'] == manifest_ref['sha256'], 'bound_image_only_description_packet')
    require(bundle['schema'] == 'NY_LOCAL_QWEN_DESCRIPTION_BUNDLE_V1'
        and bundle['source_manifest_sha256'] == manifest_ref['sha256']
        and bundle['task_packet_sha256'] == packet_ref['sha256'], 'description_bundle_source_and_task_binding')
    expected = {task['contest_id'] for task in packet['tasks']}
    actual = [contest_key(item['contest_id']) for item in bundle['descriptions']]
    require(len(actual) == len(expected) and set(actual) == expected, 'complete_exact_requested_description_join')
    return attach_descriptions(manifest_ref, bundle['descriptions'], destination)


def audit_author_source(store):
    metadata = store.fetch(f'https://[REDACTED_HOST]/repos/{AUTHOR_REPOSITORY}/commits/main',
        'private/author_commit.json', 2 * 1024 ** 2)
    revision = commit_revision(bound(metadata)['sha'])
    files = []
    for filename in ('finetuning/humor_reward_modeling.py', 'finetuning/preprocess.py'):
        files.append(store.fetch(f'https://[REDACTED_HOST]/{AUTHOR_REPOSITORY}/{revision}/{filename}',
            'private/author_source/' + filename, 2 * 1024 ** 2))
    return private_write(store.root / 'AUTHOR_SOURCE_PIN.json',
        dict(schema='NY_AUTHOR_SOURCE_PIN_V1', revision=revision, files=files,
            checkpoint_provenance_verified=False, audit_status='SOURCE_PINNED_INSPECTION_REQUIRED'))


def main():
    parser = argparse.ArgumentParser(description='Metadata-only Stage1 data handoff; private contents are never printed.')
    parser.add_argument('action', choices=('pin', 'download', 'author-source', 'build'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--pin-sha256')
    parser.add_argument('--download-sha256')
    parser.add_argument('--output')
    arguments = parser.parse_args()
    store = DownloadStore(arguments.root)
    if arguments.action == 'pin':
        result = pin_dataset(store)
    elif arguments.action == 'author-source':
        result = audit_author_source(store)
    elif arguments.action == 'download':
        require(arguments.pin_sha256 is not None, 'explicit_dataset_pin_required')
        result = download_dataset(store, dict(path=str(store.root / 'private/DATASET_PIN.json'), sha256=arguments.pin_sha256))
    else:
        require(arguments.download_sha256 and arguments.output, 'bound_download_and_new_output_required')
        result = build_manifest(dict(path=str(store.root / 'private/DOWNLOADED.json'),
            sha256=arguments.download_sha256), arguments.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='HELD_OR_FAILED_NOT_APPROVED', error_type=type(error).__name__)))
        raise SystemExit(1) from None
