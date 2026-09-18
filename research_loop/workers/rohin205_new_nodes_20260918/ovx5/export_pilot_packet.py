"""Stream a private TRAIN-only packet; never print rows or expose FINAL data."""

import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile

SOURCE = Path('/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_v2')
sys.path.insert(0, str(SOURCE))
from gpu import ny_caption_data as data


def main():
    os.umask(0o077)
    config = json.loads((SOURCE / 'TRAIN_CONFIG.json').read_bytes())
    plan = data.load_development_plan(config['development_plan'], config['development_source_manifest'])
    keys = plan['subsets']['judge_train']
    data.require(len(keys) == 180, 'same_frozen180_training_contests')
    with tempfile.TemporaryDirectory(prefix='r207_training_export_') as directory:
        output = Path(directory)
        rows_path = output / 'TRAIN_ROWS.private.jsonl'
        count = 0
        with rows_path.open('x') as stream:
            for row in data.evaluator_rows(config['data_manifest'], 'judge_train', contest_ids=keys):
                if len(row['caption'].split()) > 50:
                    continue
                stream.write(json.dumps(row, separators=(',', ':'), ensure_ascii=False) + '\n')
                count += 1
        files = {}
        sources = []
        for name in ['gpu', 'research_loop']:
            sources += [(path, str(path.relative_to(SOURCE))) for path in (SOURCE / name).rglob('*.py') if path.is_file() and not path.is_symlink()]
        for name in ['adapter_config.json', 'adapter_model.safetensors']:
            sources.append((SOURCE / 'training/checkpoints/step_006250' / name, 'warmstart6250/' + name))
        sources.append((rows_path, rows_path.name))
        for path, relative in sources:
            with path.open('rb') as stream:
                files[relative] = dict(sha256=hashlib.file_digest(stream, 'sha256').hexdigest(), bytes=path.stat().st_size)
        base = data.bound(config['base_model'])
        receipt = dict(schema='R207_PRIVATE_TRAIN_ONLY_PILOT_PACKET_V1', source_root=str(SOURCE),
            source_train_config_sha256=hashlib.sha256((SOURCE / 'TRAIN_CONFIG.json').read_bytes()).hexdigest(),
            source_data_manifest=config['data_manifest'], source_development_plan=config['development_plan'],
            training_contests=180, training_rows=count, original_base_manifest=config['base_model'],
            model_revision=base['revision'], warmstart_step=6250, files=files,
            private_rows_displayed=False, judge_dev_rows_included=False, FINAL_rows_opened=False,
            max_length=config['max_length'], seed=config['seed'], vote_cap=config['vote_cap'], learning_rate=config['learning_rate'])
        (output / 'PACKET.json').write_text(json.dumps(receipt, indent=2, sort_keys=True))
        with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz') as archive:
            for path, relative in sources:
                archive.add(path, arcname=relative, recursive=False)
            archive.add(output / 'PACKET.json', arcname='PACKET.json', recursive=False)


if __name__ == '__main__':
    main()
