"""CPU-only attempt2 API regression; no throughput measurement or CUDA use."""

import ast
from pathlib import Path
import sys
from types import SimpleNamespace

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


class CPUTorchProxy:
    def tensor(self, values, **arguments):
        profile.require(arguments.pop('device') == 'cuda:0', 'CPU_fixture_redirects_only_explicit_native_device')
        return torch.tensor(values, **arguments)

    def __getattr__(self, name):
        return getattr(torch, name)


class ToyTokenizer:
    eos_token_id = 99
    pad_token_id = 0
    all_special_ids = [99]

    def apply_chat_template(self, messages, **arguments):
        return [12, 13]

    def decode(self, tokens, **arguments):
        return ' '.join(str(token) for token in tokens)


native_source = root / 'source/gpu/orch_r125_continual_native.py'
tree = ast.parse(native_source.read_text())
owner = next(node.name for node in tree.body if isinstance(node, ast.ClassDef) and
             any(getattr(part, 'name', None) == 'generate' for part in node.body))
native_generate = profile.extracted(native_source, 'generate', parent=owner,
    namespace=dict(require=profile.require, digest=profile.digest, BASE_SHA256='0' * 64))
encode_own = profile.extracted(native_source, 'encode_own', remove_import=True,
    namespace=dict(require=profile.require, EncodedRow=profile.EncodedRow))
life = SimpleNamespace(torch=CPUTorchProxy(), tokenizer=ToyTokenizer(),
    engine=SimpleNamespace(model=model, transformers=transformers),
    plan=dict(hard_end_unix=1, context_limit=32, decoder=profile.DECODER),
    adapter_hash=lambda: profile.fixture_hash(model, torch), check=lambda label: None)
response = native_generate(life, [], max_new_tokens=4, deadline_unix=1)
own = encode_own(dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
    prefix=[], token_ids=response['token_ids'], terminal=response['terminal'], target=response['raw']), life.tokenizer, 32)
profile.require(own.labels[:2] == (-100, -100) and 0 < len(own.target_ids) <= 4, 'native_CPU_target_contract')
profile.require(not torch.cuda.is_initialized(), 'CPU_only_no_CUDA_initialization')
profile.receipt(root, 'CPU_COMPATIBILITY.json', passed=True, prompt_sizes=sizes,
    toy_output_shape=list(output.shape), native_generate_target_count=len(own.target_ids),
    actual_native_generate_and_encode_executed_with_CPU_device_proxy=True,
    cuda_initialized=False, cpu_fixture_is_not_throughput=True,
    source_pins_sha256=profile.file_hash(root / 'SOURCE_PINS.json'),
    fixture='One-layer random CPU Qwen2 + seed-created rank8; explicit CPU device proxy; no GPU model inference')
print('CPU API, native generate/encode, and exact prompt-size checks passed. No GPU inference or throughput measurement.')
