"""Native CPU-only regression for Transformers methods versus tuner flags."""
import importlib.util
import json
import sys

from peft import LoraConfig, get_peft_model
from peft.tuners.tuners_utils import BaseTunerLayer
from transformers import Qwen2Config, Qwen2ForCausalLM


spec = importlib.util.spec_from_file_location("probe", sys.argv[1])
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
config = Qwen2Config(vocab_size=64, hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                    num_attention_heads=2, num_key_value_heads=2)
base = Qwen2ForCausalLM(config)
probe.require(callable(base.disable_adapters), "fixture must reproduce Transformers method")
model = get_peft_model(base, LoraConfig(r=2, lora_alpha=4, target_modules=["q_proj", "v_proj"],
                                      task_type="CAUSAL_LM"))
layers = probe.verify_adapter_routes(model, BaseTunerLayer)
probe.require(layers == 2 and all(parameter.device.type == "cpu" for parameter in model.parameters()), "CPU fixture scope")
with model.disable_adapter():
    try:
        probe.verify_adapter_routes(model, BaseTunerLayer)
    except ValueError:
        rejected = True
    else:
        rejected = False
probe.require(rejected, "real disabled tuner must reject")
probe.verify_adapter_routes(model, BaseTunerLayer)
print(json.dumps(dict(status="PASS_NATIVE_CPU_ROUTE_FIXTURE", tuner_layers=layers,
                      disabled_rejected=rejected, forwards=0, updates=0), sort_keys=True))
