"""Synthetic CPU fixtures only; no released captions or reserved identities."""

from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from gpu import ny_caption_data as data


def rating(caption='Synthetic fixture words only', counts=(6, 3, 1)):
    return dict(caption=caption, not_funny=str(counts[0]), somewhat_funny=str(counts[1]), funny=str(counts[2]),
        votes=str(sum(counts)), mean=str(sum((index+1)*value for index, value in enumerate(counts))/sum(counts)),
        precision='uninterpreted fixture field')


@pytest.fixture
def manifest_fixture(tmp_path):
    root = tmp_path.resolve()
    groups = [[str(index)] for index in range(1000, 1060)]+[['530', '999']]
    pools = data.allocate_pools(groups, 'synthetic-test-seed')
    contests = {}
    for group in groups:
        for name in group:
            image = data.private_write(root/'images'/f'{name}.fixture', b'not a real cartoon')
            rows = data.write_rows(root/'rows'/f'{name}.jsonl', [data.rating_record(rating(f'Fixture words {name}'), name)])
            contests[name] = dict(image=image, rows=rows, canonical_scene=None)
    manifest = dict(schema='NY_PRIVATE_DATA_MANIFEST_V1', revision='a'*40, pools=pools, contests=contests,
        scene_groups=groups, judge_dev_subpools=data.dev_subpools(groups, pools, 'synthetic-test-seed'),
        description_policy=data.DESCRIPTION_POLICY, historical_captions_agent_parent_access=False,
        final_release_authorized=False)
    reference = data.private_write(root/'manifest.json', manifest)
    return root, manifest, reference


def producer_item(root, contest_id, image, scene):
    model = data.private_write(root/'model.json', dict(model_family='Qwen', local_model=True, frozen=True,
        status='SYNTHETIC_FIXTURE_NOT_MODEL_EXECUTION'))
    producer = dict(input_kinds=['image'], image=image, policy=data.DESCRIPTION_POLICY,
        historical_captions_used=False, uncanny_used=False, parent_history_used=False,
        output_sha256=hashlib.sha256(scene.encode()).hexdigest(), local_model=True, model_family='Qwen',
        hosted_provider=False, model_manifest=model)
    reference = data.private_write(root/'producer.json', producer)
    return dict(contest_id=contest_id, scene=scene, producer_receipt=reference), producer


def released_fixture(manifest_fixture, mutation=None):
    root, manifest, unused = manifest_fixture
    moved = manifest['judge_dev_subpools']['model_selection'].pop()
    manifest['judge_dev_subpools']['threshold_selection'].append(moved)
    records = [dict(contest_number=int(name), canny=f'A synthetic room numbered {name} contains a desk and two standing figures.',
        location='An office', entities=['desk', 'figures'], uncanny='PRIVATE_EXPLANATION_DO_NOT_COPY')
        for name in manifest['pools']['judge_train'] + manifest['pools']['judge_dev']]
    if mutation:
        mutation(records, manifest)
    source = data.private_write(root/'released_train.jsonl', b''.join(data.canonical(row)+b'\n' for row in records))
    pin = data.private_write(root/'dataset_pin.json', dict(revision=manifest['revision']))
    downloaded = data.private_write(root/'downloaded.json', dict(dataset_pin=pin,
        files=[dict(name='gpt4o_description/train.jsonl', reference=source)]))
    reference = data.private_write(root/'released_manifest.json', dict(manifest, downloaded=downloaded, dataset_pin=pin))
    return root, manifest, reference, source


def test_released_all_available_build_uses_no_caption_or_image_files(manifest_fixture):
    root, manifest, reference, unused = released_fixture(manifest_fixture)
    original = Path.open
    def bounded_open(path, *args, **kwargs):
        assert path.parent.name not in ('rows', 'images')
        return original(path, *args, **kwargs)
    with patch.object(Path, 'open', bounded_open):
        status = data.build_released_development(reference, root/'released')
    plan = data.load_development_plan(status['development_plan'], reference)
    assert set(plan['subsets']['judge_train']) == set(manifest['pools']['judge_train'])
    assert sum(status['selected_contests'].values()) == len(manifest['pools']['judge_train'])+len(manifest['pools']['judge_dev'])
    catalog = data.bound(status['scene_catalog'])
    assert 'PRIVATE_EXPLANATION' not in json.dumps(catalog)
    assert status['missing_or_invalid_contests'] == {'judge_train': 0, 'judge_dev': 0}
    with pytest.raises(FileExistsError):
        data.build_released_development(reference, root/'released')


@pytest.mark.parametrize('mutation', ['missing', 'malformed', 'duplicate'])
def test_released_missing_invalid_excludes_whole_group(manifest_fixture, mutation):
    def change(records, manifest):
        target = records[0]
        if mutation == 'missing':
            records.remove(target)
        elif mutation == 'malformed':
            target['entities'] = {'not': 'a list'}
        else:
            records.append(dict(target))
    root, manifest, reference, unused = released_fixture(manifest_fixture, change)
    status = data.build_released_development(reference, root/'released')
    assert status['missing_or_invalid_contests']['judge_train'] >= 1
    assert status['selected_contests']['judge_train'] < len(manifest['pools']['judge_train'])
    data.load_development_plan(status['development_plan'], reference)


@pytest.mark.parametrize('field,value', [('canny', ''), ('location', 42), ('entities', []), ('entities', [None])])
def test_released_factual_schema_rejects_malformed(field, value):
    facts = dict(canny='A synthetic room contains a desk and two standing figures.', location='Office', entities=['desk'])
    facts[field] = value
    with pytest.raises(ValueError, match='valid_released_factual_fields'):
        data.released_judge_scene(facts)


def test_released_scene_policy_cannot_release_to_game_or_locked_pool(manifest_fixture):
    root, manifest, reference, unused = released_fixture(manifest_fixture)
    status = data.build_released_development(reference, root/'released')
    rows = list(data.evaluator_rows(status['data_manifest'], 'judge_train'))
    assert rows and all('PRIVATE_EXPLANATION' not in row['scene'] for row in rows)
    assert all(item['canonical_scene'] is None for item in data.load_manifest(status['data_manifest'])['contests'].values())
    with pytest.raises(ValueError, match='released_scenes_development_only'):
        list(data.evaluator_rows(status['data_manifest'], 'judge_validation'))
    with pytest.raises(ValueError):
        data.development_packet(status['data_manifest'], root/'packet.json')


def test_released_source_hash_tamper_rejected(manifest_fixture):
    root, unused, reference, source = released_fixture(manifest_fixture)
    Path(source['path']).write_bytes(b'{}\n')
    with pytest.raises(ValueError, match='released_description_hash_mismatch'):
        data.build_released_development(reference, root/'released')


def test_released_judge_preflight_only_opens_selected_train_dev_rows(manifest_fixture):
    from gpu import ny_caption_judge as judge
    root, manifest, reference, unused = released_fixture(manifest_fixture)
    status = data.build_released_development(reference, root/'released')
    config = dict(data_manifest=status['data_manifest'], development_plan=status['development_plan'],
        development_source_manifest=reference, per_contest_per_band=2, heldout_per_contest=2, seed=177)
    allowed = {Path(manifest['contests'][name]['rows']['path']) for pool in ('judge_train', 'judge_dev') for name in manifest['pools'][pool]}
    original = Path.open
    def bounded_open(path, *args, **kwargs):
        if path.parent.name == 'rows':
            assert path in allowed
        assert path.parent.name != 'images'
        return original(path, *args, **kwargs)
    with patch.object(Path, 'open', bounded_open):
        training, held, audit = judge.prepare_training_data(config)
    assert training and audit and all(held.values())


@pytest.mark.parametrize('revision', ['main', 'a'*39, 'a'*41, 'G'*40, 1])
def test_revision_must_be_full_immutable_commit(revision):
    with pytest.raises(ValueError, match='immutable_full_commit'):
        data.commit_revision(revision)


def test_private_artifacts_are_immutable_and_hash_bound(tmp_path):
    reference = data.private_write(tmp_path.resolve()/'pin.json', {'value': 1})
    assert data.bound(reference) == {'value': 1}
    assert Path(reference['path']).stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        data.private_write(Path(reference['path']), {'value': 2})
    Path(reference['path']).write_bytes(b'{"value":2}')
    with pytest.raises(ValueError, match='hash_mismatch'):
        data.bound(reference)


def test_symlink_reference_rejected(tmp_path):
    data.private_write(tmp_path.resolve()/'actual.json', {})
    alias = tmp_path.resolve()/'alias.json'
    alias.symlink_to('actual.json')
    with pytest.raises(ValueError, match='canonical_regular'):
        data.file_ref(alias)


def test_ratings_reconstruct_mean_and_ignore_precision():
    row = data.rating_record(rating(), '00012')
    assert row['contest_id'] == '12'
    assert row['counts'] == [6, 3, 1] and row['votes'] == 10 and row['mean'] == 1.5
    assert 'precision' not in row


@pytest.mark.parametrize('change', [dict(votes='0'), dict(votes='11'), dict(not_funny='-1'),
    dict(funny=True), dict(mean='nan'), dict(mean='2.0'), dict(caption=' '), dict(caption='bad\x00fixture')])
def test_invalid_ratings_rejected(change):
    with pytest.raises(ValueError):
        data.rating_record(dict(rating(), **change), '12')


def test_normalization_groups_duplicate_families():
    first = data.rating_record(rating(' Fixture   TEXT '), '12')
    second = data.rating_record(rating('fixture text'), '13')
    assert first['caption_family_sha256'] == second['caption_family_sha256']


def test_pool_allocation_is_disjoint_whole_contest_and_exposed_train_only(manifest_fixture):
    unused, manifest, unused_ref = manifest_fixture
    pools = manifest['pools']
    assert len(pools['final']) == 3
    assert {'530', '999'} <= set(pools['judge_train'])
    assert pools == data.allocate_pools(manifest['scene_groups'], 'synthetic-test-seed')
    names = [name for pool in pools.values() for name in pool]
    assert len(names) == len(set(names)) == len(manifest['contests'])
    for group in manifest['scene_groups']:
        assert sum(set(group) <= set(pool) for pool in pools.values()) == 1


def test_final_requires_exact_three_without_splitting_groups():
    with pytest.raises(ValueError, match='three_whole_contest'):
        data.allocate_pools([[str(index), str(index+100)] for index in range(12)], 'seed')


def test_transitive_near_duplicate_scenes_stay_together():
    contests = {name: dict(image=dict(sha256=name), image_features=dict(dhash=dhash))
        for name, dhash in [('1001', '0'), ('1002', '1'), ('1003', '3'), ('1004', 'ff')]}
    groups = data.scene_groups(contests, 1)
    assert sorted(map(sorted, groups)) == [['1001', '1002', '1003'], ['1004']]
    contests['1004']['image']['sha256'] = '1001'
    assert len(data.scene_groups(contests, 1)) == 1


def test_actual_pillow_image_features(tmp_path):
    from PIL import Image
    path = tmp_path.resolve()/'fixture.png'
    Image.new('RGB', (19, 13), 'white').save(path)
    features = data.image_features(data.file_ref(path))
    assert features == dict(width=19, height=13, dhash='0000000000000000')


@pytest.mark.parametrize('mutation', ['overlap', 'final_in_dev_subset', 'cross_pool_scene', 'exposed_development', 'final_authorized'])
def test_invalid_manifest_cannot_release_or_train_rows(manifest_fixture, mutation):
    root, original, unused_ref = manifest_fixture
    manifest = deepcopy(original)
    if mutation == 'overlap':
        manifest['pools']['agent_development'].append(manifest['pools']['final'][0])
    elif mutation == 'final_in_dev_subset':
        manifest['judge_dev_subpools']['threshold_selection'].append(manifest['pools']['final'][0])
    elif mutation == 'cross_pool_scene':
        manifest['scene_groups'].append([manifest['pools']['final'][0], manifest['pools']['judge_train'][0]])
    elif mutation == 'exposed_development':
        manifest['pools']['judge_train'].remove('530')
        manifest['pools']['agent_development'].append('530')
    else:
        manifest['final_release_authorized'] = True
    reference = data.private_write(root/'bad.json', manifest)
    with pytest.raises(ValueError):
        data.description_tasks(reference, 'agent_development')
    with pytest.raises(ValueError):
        list(data.evaluator_rows(reference, 'judge_train'))


@pytest.mark.parametrize('pool', ['final', 'agent_development'])
def test_evaluator_training_refuses_agent_and_final_pools(manifest_fixture, pool):
    unused, unused_manifest, reference = manifest_fixture
    with pytest.raises(ValueError, match='evaluator_training_pool'):
        list(data.evaluator_rows(reference, pool))


def test_image_tasks_are_caption_and_rating_free(manifest_fixture):
    unused, manifest, reference = manifest_fixture
    tasks = data.description_tasks(reference, 'agent_development')
    assert tasks
    assert all(set(task) == {'contest_id', 'image', 'policy'} for task in tasks)
    assert not set(task['contest_id'] for task in tasks).intersection(manifest['pools']['final'])
    with pytest.raises(ValueError, match='FINAL_DESCRIPTION_ACCESS_FORBIDDEN'):
        data.description_tasks(reference, 'final')


def test_description_requires_bound_local_image_only_provenance(manifest_fixture):
    root, manifest, reference = manifest_fixture
    name = manifest['pools']['agent_development'][0]
    scene = 'A synthetic room contains a table and two standing figures.'
    item, unused = producer_item(root, name, manifest['contests'][name]['image'], scene)
    updated = data.attach_descriptions(reference, [item], root/'updated.json')
    assert data.load_manifest(updated)['contests'][name]['canonical_scene'] == scene
    assert data.load_manifest(reference)['contests'][name]['canonical_scene'] is None
    with pytest.raises(ValueError, match='description_version_change'):
        data.attach_descriptions(updated, [item], root/'again.json')


@pytest.mark.parametrize('change', [dict(local_model=False), dict(model_family='hosted'), dict(hosted_provider=True),
    dict(historical_captions_used=True), dict(input_kinds=['image', 'caption']), dict(uncanny_used=True),
    dict(parent_history_used=True), dict(output_sha256='0'*64)])
def test_bad_description_provenance_rejected(manifest_fixture, change):
    root, manifest, reference = manifest_fixture
    name = manifest['pools']['agent_development'][0]
    item, producer = producer_item(root, name, manifest['contests'][name]['image'],
        'A synthetic room contains a table and two standing figures.')
    item['producer_receipt'] = data.private_write(root/'bad-producer.json', dict(producer, **change))
    with pytest.raises(ValueError):
        data.attach_descriptions(reference, [item], root/'bad-attachment.json')
    assert not (root/'bad-attachment.json').exists()


def test_final_description_attachment_refused(manifest_fixture):
    root, manifest, reference = manifest_fixture
    with pytest.raises(ValueError, match='unreleased_or_unknown'):
        data.attach_descriptions(reference, [dict(contest_id=manifest['pools']['final'][0])], root/'forbidden.json')


def test_development_requires_descriptions_and_omits_private_rows(manifest_fixture):
    root, manifest, reference = manifest_fixture
    with pytest.raises(ValueError, match='description_not_ready'):
        data.development_packet(reference, root/'early.json')
    for name in manifest['pools']['agent_development']:
        scene = f'A purely synthetic factual room, fixture number {name}.'
        item, unused = producer_item(root/name, name, manifest['contests'][name]['image'], scene)
        manifest['contests'][name].update(canonical_scene=scene, description_producer=item['producer_receipt'])
    ready = data.private_write(root/'ready.json', manifest)
    result = data.bound(data.development_packet(ready, root/'development.json'))
    assert all(set(scene) == {'contest_id', 'image', 'scene'} for scene in result['scenes'])
    assert not result['human_captions_included'] and not result['final_included']


def test_evaluator_rows_hash_and_contest_join_checked(manifest_fixture):
    root, manifest, unused_ref = manifest_fixture
    names = manifest['pools']['judge_train']
    for name in names:
        scene = f'A purely synthetic factual room, fixture number {name}.'
        item, unused = producer_item(root/name, name, manifest['contests'][name]['image'], scene)
        manifest['contests'][name].update(canonical_scene=scene, description_producer=item['producer_receipt'])
    reference = data.private_write(root/'ready.json', manifest)
    rows = list(data.evaluator_rows(reference, 'judge_train'))
    assert len(rows) == len(names) and all('scene_group_sha256' in row for row in rows)
    Path(manifest['contests'][names[0]]['rows']['path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='private_caption_rows_changed'):
        list(data.evaluator_rows(reference, 'judge_train'))


def test_download_reserves_before_io_and_caches_only_exact_completed_bytes(tmp_path):
    store = data.DownloadStore(tmp_path.resolve(), cap=20)
    def response(unused_request, timeout):
        assert timeout == 90
        assert sum(json.loads(path.read_bytes())['reserved_bytes'] for path in (tmp_path/'download_ledger').glob('*.json')) == 10
        result = io.BytesIO(b'fixture')
        result.headers = {'Content-Length': '7'}
        return result
    with patch.object(data.urllib.request, 'urlopen', side_effect=response) as network:
        result = store.fetch('https://huggingface.co/fixture', 'private/fixture', 10, 7)
        assert result == store.fetch('https://huggingface.co/fixture', 'private/fixture', 10, 7)
        assert network.call_count == 1
        Path(result['path']).write_bytes(b'changed')
        with pytest.raises(ValueError, match='changed_completed'):
            store.fetch('https://huggingface.co/fixture', 'private/fixture', 10, 7)


def test_failed_download_consumes_reservation_and_cannot_retry(tmp_path):
    store = data.DownloadStore(tmp_path.resolve(), cap=10)
    with patch.object(data.urllib.request, 'urlopen', side_effect=OSError('synthetic network failure')) as network:
        with pytest.raises(OSError):
            store.fetch('https://huggingface.co/fixture', 'private/fixture', 8)
        with pytest.raises(ValueError):
            store.fetch('https://huggingface.co/fixture', 'private/fixture', 8)
        with pytest.raises(ValueError, match='aggregate_public_download_cap'):
            store.fetch('https://huggingface.co/other', 'private/other', 3)
        assert network.call_count == 1
    assert len(list((tmp_path/'download_ledger').glob('*.failed'))) == 1


def test_cross_contest_duplicates_are_quarantined_before_partition(tmp_path):
    root = tmp_path.resolve()
    pin = data.private_write(root/'pin.json', dict(revision='a'*40))
    files = []
    for index in range(80):
        name = str(1000+index)
        image = data.private_write(root/'inputs'/f'{name}.jpg', name.encode())
        csv_path = root/'inputs'/f'{name}.csv'
        rows = [rating(f'Unique synthetic fixture {name}'), rating('Cross contest synthetic duplicate')]
        if index == 0:
            rows.extend([rating('Conflicting synthetic duplicate'), rating('Conflicting synthetic duplicate', (1, 2, 7))])
        with csv_path.open('x', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        files.extend([dict(name=f'images/{name}.jpg', reference=image), dict(name=f'ratings/{name}.csv', reference=data.file_ref(csv_path))])
    downloaded = data.private_write(root/'downloaded.json', dict(dataset_pin=pin, files=files))
    with patch.object(data, 'image_features', side_effect=lambda reference: dict(width=10, height=10,
            dhash=f'{int(Path(reference["path"]).stem):016x}')):
        public = data.build_manifest(downloaded, root/'prepared', near_distance=0)
    assert public['contest_count'] == 80 and public['rating_rows'] == 80
    assert public['audit']['cross_contest_duplicate_rows_quarantined'] == 80
    assert public['audit']['conflicting_duplicate_families_quarantined'] == 1
    assert 'contests' not in public and public['description_ready_count'] == 0
    data.load_manifest(public['private_manifest'])


def development_fixture(manifest_fixture):
    root, manifest, unused = manifest_fixture
    moved = manifest['judge_dev_subpools']['model_selection'].pop()
    manifest['judge_dev_subpools']['threshold_selection'].append(moved)
    reference = data.private_write(root/'development-source.json', manifest)
    plan_ref = data.build_development_plan(reference, root/'development-plan.json', training_contests=8, held_contests=2)
    return root, manifest, reference, plan_ref


def test_development_plan_uses_metadata_only_and_keeps_locked_pools_closed(manifest_fixture):
    root, manifest, reference, plan_ref = development_fixture(manifest_fixture)
    plan = data.load_development_plan(plan_ref, reference)
    selected = [name for names in plan['subsets'].values() for name in names]
    assert len(selected) == len(set(selected))
    assert not set(selected).intersection(manifest['pools']['final']+manifest['pools']['judge_validation']+manifest['pools']['agent_development'])
    assert data.bound(data.build_development_plan(reference, root/'same-plan.json', training_contests=8, held_contests=2)) == plan
    packet = data.bound(data.development_description_packet(reference, plan_ref, root/'tasks.json'))
    assert all(set(task) == {'contest_id', 'image', 'policy'} for task in packet['tasks'])
    assert len(packet['tasks']) == len(selected) and not packet['ratings_included']


@pytest.mark.parametrize('mutation', ['validation', 'overlap', 'final'])
def test_development_plan_refuses_pool_escape_or_reused_audit(manifest_fixture, mutation):
    root, manifest, reference, plan_ref = development_fixture(manifest_fixture)
    plan = data.bound(plan_ref)
    if mutation == 'overlap':
        plan['subsets']['development_audit'] = plan['subsets']['threshold_selection']
    else:
        plan['subsets']['development_audit'] = manifest['pools']['judge_validation' if mutation == 'validation' else 'final'][:2]
    bad = data.private_write(root/'bad-plan.json', plan)
    with pytest.raises(ValueError):
        data.load_development_plan(bad, reference)


def test_description_bundle_join_and_development_train_read_only_selected_rows(manifest_fixture):
    from gpu import ny_caption_judge as judge
    root, manifest, reference, plan_ref = development_fixture(manifest_fixture)
    packet_ref = data.development_description_packet(reference, plan_ref, root/'tasks.json')
    packet = data.bound(packet_ref)
    descriptions = []
    for task in packet['tasks']:
        name = task['contest_id']
        item, unused = producer_item(root/'producers'/name, name, task['image'],
            f'A purely synthetic factual room, fixture number {name}.')
        descriptions.append(item)
    bundle = dict(schema='NY_LOCAL_QWEN_DESCRIPTION_BUNDLE_V1', source_manifest_sha256=reference['sha256'],
        task_packet_sha256=packet_ref['sha256'], descriptions=descriptions)
    incomplete = data.private_write(root/'incomplete.json', dict(bundle, descriptions=descriptions[:-1]))
    with pytest.raises(ValueError, match='complete_exact_requested_description_join'):
        data.attach_description_bundle(reference, packet_ref, incomplete, root/'refused.json')
    bundle_ref = data.private_write(root/'bundle.json', bundle)
    ready = data.attach_description_bundle(reference, packet_ref, bundle_ref, root/'described.json')
    config = dict(data_manifest=ready, development_plan=plan_ref, development_source_manifest=reference,
        per_contest_per_band=2, heldout_per_contest=2, seed=177)
    original = data.evaluator_rows
    touched = []
    def observed(manifest_ref, pool, **options):
        assert pool in ('judge_train', 'judge_dev')
        touched.extend(options['contest_ids'])
        return original(manifest_ref, pool, **options)
    with patch.object(data, 'evaluator_rows', side_effect=observed):
        training, held, audit = judge.prepare_training_data(config)
    assert training and all(held.values()) and audit
    assert set(touched) == {task['contest_id'] for task in packet['tasks']}
    assert {row['contest_id'] for row in audit}.isdisjoint(row['contest_id'] for rows in held.values() for row in rows)


def test_selected_row_reader_refuses_partial_image_group(manifest_fixture):
    unused_root, unused_manifest, reference = manifest_fixture
    with pytest.raises(ValueError, match='whole_scene_group_selection_required'):
        list(data.evaluator_rows(reference, 'judge_train', contest_ids=['530']))
