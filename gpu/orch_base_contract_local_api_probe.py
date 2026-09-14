"""No-language-model CPU reproduction of PEFT gradient-flag restoration."""

import hashlib
import inspect
import json

import peft
import torch
from peft.tuners.tuners_utils import BaseTunerLayer

from organism_v6.orch_base_contract import readonly_condition


def main():
    torch.manual_seed(0)
    model = peft.get_peft_model(torch.nn.Sequential(torch.nn.Linear(2, 2, bias=False)),
                               peft.LoraConfig(r=1, target_modules=['0']))
    model.requires_grad_(False)

    def state_hash():
        digest = hashlib.sha256()
        for name, parameter in model.named_parameters():
            digest.update(name.encode())
            digest.update(parameter.detach().numpy().tobytes())
        return digest.hexdigest()

    before = state_hash()
    with model.disable_adapter():
        assert not any(parameter.requires_grad for parameter in model.parameters())
    raw_restoration_enables_grad = any(parameter.requires_grad for parameter in model.parameters())
    assert raw_restoration_enables_grad
    assert state_hash() == before
    model.requires_grad_(False)
    with readonly_condition(model, 'BASE'):
        pass
    assert not any(parameter.requires_grad for parameter in model.parameters())
    assert state_hash() == before
    print(json.dumps(dict(status='PASS', device='cpu', language_model_calls=0,
          raw_restoration_enables_grad=raw_restoration_enables_grad,
          repair_restores_frozen_flags=True, parameter_bytes_unchanged=True,
          fixture_state_sha256=before, peft_version=peft.__version__,
          enable_adapters_source=inspect.getsource(BaseTunerLayer.enable_adapters),
          set_adapter_source=inspect.getsource(BaseTunerLayer.set_adapter)), indent=2))


if __name__ == '__main__':
    main()
