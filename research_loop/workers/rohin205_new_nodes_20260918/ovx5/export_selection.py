"""Export only declared non-FINAL model-selection rows as private JSONL bytes."""

import json
from pathlib import Path
import sys

ROOT = Path('/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_v2')
sys.path.insert(0, str(ROOT))
from gpu import ny_caption_data as data

config = json.loads((ROOT / 'TRAIN_CONFIG.json').read_bytes())
plan = data.load_development_plan(config['development_plan'], config['development_source_manifest'])
for row in data.evaluator_rows(config['data_manifest'], 'judge_dev', contest_ids=plan['subsets']['model_selection']):
    if len(row['caption'].split()) <= 50:
        sys.stdout.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
