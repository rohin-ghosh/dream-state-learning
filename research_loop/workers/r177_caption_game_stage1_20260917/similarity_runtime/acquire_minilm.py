"""Once-only public sentence-encoder acquisition with a finite byte envelope."""

import hashlib
import json
import os
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
FILES = ['config.json', 'model.safetensors', 'tokenizer.json', 'tokenizer_config.json',
    'vocab.txt', 'special_tokens_map.json', 'modules.json', 'sentence_bert_config.json', '1_Pooling/config.json']


def main():
    os.umask(0o077)
    root = ROOT / 'encoder_acquisition1'
    root.mkdir(mode=0o700, exist_ok=False)
    (root / 'PRE_IO_SCOPE.json').write_text(json.dumps(dict(public_download_cap_bytes=128 * 1024 * 1024,
        model=MODEL, metadata_cap_bytes=1024 * 1024, files=FILES, private_inputs_sent=False, retries=0)))
    with urllib.request.urlopen('https://huggingface.co/api/models/' + MODEL, timeout=30) as response:
        raw = response.read(1024 * 1024 + 1)
    assert len(raw) <= 1024 * 1024
    (root / 'PUBLIC_MODEL_METADATA.json').write_bytes(raw)
    metadata = json.loads(raw)
    revision = metadata['sha']
    assert len(revision) == 40 and all(char in '0123456789abcdef' for char in revision)
    model_root = root / 'model'
    model_root.mkdir(mode=0o700)
    hashes = {}
    total = len(raw)
    for index, name in enumerate(FILES):
        cap = 96 * 1024 * 1024 if name == 'model.safetensors' else 2 * 1024 * 1024
        url = 'https://huggingface.co/' + MODEL + '/resolve/' + revision + '/' + name
        (root / (str(index) + '.RESERVED.json')).write_text(json.dumps(dict(path=name, url=url, cap_bytes=cap)))
        target = model_root / name
        target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(url, timeout=60) as response, target.open('xb') as stream:
            while True:
                chunk = response.read(min(1024 * 1024, cap - size + 1))
                if not chunk:
                    break
                assert size + len(chunk) <= cap and total + len(chunk) <= 128 * 1024 * 1024
                stream.write(chunk)
                size += len(chunk)
                total += len(chunk)
                digest.update(chunk)
        hashes[name] = digest.hexdigest()
    manifest = dict(model_id=MODEL, revision=revision, root=str(model_root), files=hashes,
        source_metadata_sha256=hashlib.sha256(raw).hexdigest(), source_kind='PUBLIC_SENTENCE_TRAINED_PRETRAINED',
        downloaded_bytes=total, provider_calls=0, GPU_calls=0)
    manifest_raw = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    (root / 'ENCODER_MANIFEST.json').write_bytes(manifest_raw)
    print(json.dumps(dict(status='PINNED_PUBLIC_SENTENCE_ENCODER_ACQUIRED', model_id=MODEL, revision=revision,
        bytes=total, manifest_path=str(root / 'ENCODER_MANIFEST.json'), manifest_sha256=hashlib.sha256(manifest_raw).hexdigest())))


if __name__ == '__main__':
    main()
