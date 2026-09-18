import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile


def capture(helper, output):
    freeze_path = helper.CAMPAIGN / 'audit_generation1' / 'FREEZE.json'
    assert helper.sha(freeze_path) == 'f84ab3117a6abe9861d98ce7c3ec0b3bdf01199fbe5f9cd644c7ab0a1080c1c8'
    freeze = helper.read(freeze_path)
    reader = helper.BoundedReader(helper.ROOT.parent, 8 * 1024 ** 3 - freeze['adapter_bytes'])
    entries = {}
    with tarfile.open(output, 'x') as archive:
        def add(name, raw):
            assert name not in entries
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(raw), 0o600
            archive.addfile(info, io.BytesIO(raw))
            entries[name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        private_refs = [helper.ref(freeze_path), freeze['methods'], freeze['fingerprints'], freeze['witnesses'],
                        *freeze['commits'].values()]
        for reference in private_refs:
            path = helper.regular(reference['path'])
            assert path.parent == freeze_path.parent and helper.sha(path) == reference['sha256']
            add(str(path.relative_to(helper.CAMPAIGN)), path.read_bytes())
        for milestone in helper.ORDER:
            label = 'initial' if milestone == 0 else f'sleep_{milestone:06d}'
            directory = helper.ROOT / 'checkpoints' / label
            raw = reader.raw(directory / 'COMMIT.json')
            assert hashlib.sha256(raw).hexdigest() == freeze['commits'][str(milestone)]['sha256']
            commit = helper.parse(raw)
            add(f'inputs/{label}/COMMIT.json', raw)
            for name, checksum in commit['adapter_files'].items():
                assert name in {'README.md', 'adapter_config.json', 'adapter_model.safetensors'}
                raw = reader.raw(directory / 'adapter' / name)
                assert hashlib.sha256(raw).hexdigest() == checksum
                add(f'inputs/{label}/adapter/{name}', raw)
            manifest = dict(schema='R130_CHECKPOINT_MANIFEST_V1', adapter_path='adapter', commit_path='COMMIT.json',
                            commit_sha256=freeze['commits'][str(milestone)]['sha256'])
            add(f'inputs/{label}/manifest.json', helper.canonical(manifest) + b'\n')
        inventory = dict(schema='R167_EXACT_ADAPTER_ONLY_ARCHIVE_V1', entries=entries,
                         original_freeze=helper.ref(freeze_path), source_read_bytes=reader.bytes,
                         source_mutated=False, optimizer_rng_read=False, model_calls=0)
        add('INPUT_INVENTORY.json', helper.canonical(inventory) + b'\n')
    return dict(status='EXACT_ADAPTER_ONLY_ARCHIVE', archive=helper.ref(output), files=len(entries),
                source_read_bytes=reader.bytes, model_calls=0)


def receive(helper, archive, checksum):
    assert helper.sha(archive) == checksum
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        names = [member.name for member in members]
        assert len(names) == len(set(names))
        for member in members:
            path = Path(member.name)
            assert member.isfile() and not path.is_absolute() and '..' not in path.parts
            assert path.parts[0] in ('inputs', 'audit_generation1', 'INPUT_INVENTORY.json')
            assert not (helper.CAMPAIGN / path).exists()
        inventory = helper.parse(stream.extractfile('INPUT_INVENTORY.json').read())
        assert set(names) == set(inventory['entries']) | {'INPUT_INVENTORY.json'}
        for member in members:
            raw = stream.extractfile(member).read()
            if member.name != 'INPUT_INVENTORY.json':
                expected = inventory['entries'][member.name]
                assert len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256']
            path = helper.CAMPAIGN / member.name
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            helper.write(path, raw)
    return dict(status='INPUTS_HASH_VERIFIED', files=len(names), archive_sha256=checksum,
                checkpoints=19, model_calls=0, optimizer_rng_read=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('capture', 'receive'))
    parser.add_argument('--helper', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('r167', args.helper)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    result = capture(helper, args.archive) if args.action == 'capture' else receive(helper, args.archive, args.sha256)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
