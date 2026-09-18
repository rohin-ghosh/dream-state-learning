"""CPU-only installed-API probe; its timings are never throughput evidence."""

import os
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'source'))

import torch
import transformers
from peft import LoraConfig, get_peft_model
from gpu import ny_caption_generation_profile as profile

torch.set_num_threads(2)
torch.manual_seed(profile.SEED)
tokenizer = transformers.AutoTokenizer.from_pretrained(profile.MODEL, local_files_only=True, trust_remote_code=False)
sizes = []
for target in (2048, 12288):
    messages = profile.synthetic_messages(tokenizer, target)
    sizes.append(len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)))
config = transformers.Qwen2Config(vocab_size=100, hidden_size=16, intermediate_size=32,
                                 num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2)
model = transformers.Qwen2ForCausalLM(config)
model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0,
                      task_type='CAUSAL_LM', target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj']))
model.requires_grad_(False)
model.eval()
inputs = torch.tensor([[12, 13], [14, 15]])
generation = transformers.GenerationConfig(do_sample=True, num_beams=1, use_cache=True,
    max_new_tokens=4, eos_token_id=99, pad_token_id=0, **profile.DECODER)
with torch.inference_mode():
    output = model.generate(input_ids=inputs, attention_mask=torch.ones_like(inputs), generation_config=generation)
profile.require(not torch.cuda.is_initialized(), 'CPU_only_no_CUDA_initialization')
profile.receipt(root, 'CPU_COMPATIBILITY.json', passed=True, prompt_sizes=sizes,
    toy_output_shape=list(output.shape), cuda_initialized=False, cpu_fixture_is_not_throughput=True,
    source_pins_sha256=profile.file_hash(root / 'SOURCE_PINS.json'),
    fixture='One-layer random CPU Qwen2 + seed-created rank8; no public GPU model inference')
print('CPU API/tokenizer compatibility passed; no GPU inference, no throughput measurement.')
