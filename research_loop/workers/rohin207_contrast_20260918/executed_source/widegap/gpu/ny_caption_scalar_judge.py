"""Development-only scalar BT inference, independent of vote calibration and tau."""

import math
from pathlib import Path

from gpu import ny_caption_data as data
from gpu.ny_caption_judge import canonical_input


SCHEMAS = frozenset(('NY_BT_SCALAR_JUDGE_CONFIG_V1', 'NY_WIDEGAP100K_SCALAR_JUDGE_CONFIG_V2'))
MODEL_ID = 'Qwen/Qwen2.5-7B-Instruct'
REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'


def read_config(path):
    reference = data.file_ref(Path(path).resolve())
    config = data.bound(reference)
    data.require(config.get('schema') in SCHEMAS, 'supported_scalar_judge_schema')
    base = data.bound(config['base_model'])
    data.require(base['model_id'] == MODEL_ID and base['revision'] == REVISION,
                 'frozen_scalar_backbone_identity')
    adapter_root = Path(config['selected_adapter_root']).resolve()
    for name in ('adapter_config.json', 'adapter_model.safetensors'):
        artifact = config['adapter'][name]
        data.require(Path(artifact['path']).resolve() == adapter_root / name,
                     'selected_adapter_path_matches_manifest')
        data.require(data.file_ref(adapter_root / name)['sha256'] == artifact['sha256'],
                     'selected_adapter_hash_matches_manifest')
    data.require(type(config['config']['max_length']) is int
                 and 0 < config['config']['max_length'] <= 2048, 'bounded_scalar_input_length')
    return config, base, reference


def relative_position(score, reference_scores, top_k):
    data.require(math.isfinite(score) and reference_scores
                 and all(math.isfinite(value) for value in reference_scores), 'finite_relative_scores')
    data.require(type(top_k) is int and 1 <= top_k <= len(reference_scores), 'bounded_relative_top_k')
    rank = 1 + sum(value >= score for value in reference_scores)
    return dict(raw_score=score, rank=rank, reference_count=len(reference_scores),
                top_k=top_k, accepted=rank <= top_k, ties='REFERENCE_WINS')


class ScalarJudge:
    def __init__(self, config_path, device='cuda:0', batch_size=8):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        data.require(type(batch_size) is int and 1 <= batch_size <= 64, 'bounded_inference_batch')
        self.config, base, self.reference = read_config(config_path)
        self.max_length = self.config['config']['max_length']
        self.batch_size, self.device, self.torch = batch_size, device, torch
        self.tokenizer = AutoTokenizer.from_pretrained(base['root'], local_files_only=True, trust_remote_code=False)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = 'right'
        backbone, info = AutoModelForSequenceClassification.from_pretrained(
            base['root'], num_labels=1, pad_token_id=self.tokenizer.pad_token_id,
            local_files_only=True, trust_remote_code=False, use_safetensors=True,
            dtype=torch.bfloat16, device_map={'': device}, attn_implementation='sdpa',
            output_loading_info=True)
        data.require(not info.get('mismatched_keys') and not info.get('error_msgs')
                     and all(name.startswith('score.') for name in info.get('missing_keys', [])),
                     'pretrained_backbone_not_randomly_reinitialized')
        self.model = PeftModel.from_pretrained(backbone, self.config['selected_adapter_root'],
                                             is_trainable=False, local_files_only=True)
        self.model.eval()
        data.require(not any(parameter.requires_grad for parameter in self.model.parameters()),
                     'inference_has_no_trainable_parameters')

    def token_count(self, scene, caption):
        return len(self.tokenizer(canonical_input(scene, caption), truncation=False)['input_ids'])

    def score(self, rows):
        scores = []
        for start in range(0, len(rows), self.batch_size):
            batch = rows[start:start + self.batch_size]
            encoded = self.tokenizer([canonical_input(row['scene'], row['caption']) for row in batch],
                                     padding=True, truncation=False, return_tensors='pt')
            data.require(encoded['input_ids'].shape[1] <= self.max_length, 'scalar_input_not_truncated')
            with self.torch.inference_mode():
                values = self.model(**encoded.to(self.device)).logits[:, 0].float().cpu().tolist()
            data.require(len(values) == len(batch) and all(math.isfinite(value) for value in values),
                         'finite_scalar_outputs')
            scores.extend(values)
        return scores
