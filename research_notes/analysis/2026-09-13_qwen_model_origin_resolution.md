# Resolve the model identity for future paper-grade runs

Date: 2026-09-13 UTC  
Scope: read-only provenance check; no model, tokenizer, adapter, job, or prior
receipt changed.

## Result

The cached base used by SEQ-120 is identifiable as:

```text
Qwen/Qwen2.5-7B-Instruct
revision a09a35458c702b33eeacc393d103063234e8bc28
```

Evidence checked directly on node 3:

- cache namespace:
  `models--Qwen--Qwen2.5-7B-Instruct`;
- `refs/main` contains exactly
  `a09a35458c702b33eeacc393d103063234e8bc28`;
- that is the only directory under `snapshots/`;
- its model card names `Qwen2.5-7B-Instruct` and Apache-2.0;
- `config.json` reports `model_type=qwen2` and
  `architectures=["Qwen2ForCausalLM"]`;
- SEQ-120's immutable plan points to that exact snapshot directory and pins
  SHA-256 values for the four safetensor shards, index, config, generation
  config, tokenizer, vocabulary, merges, model card and license.

The upstream Hugging Face repository exposes the same verified revision:
<https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/commit/a09a35458c702b33eeacc393d103063234e8bc28>.

## Ruling

Future plans should bind both the public model identity/revision above and the
already recorded local file-hash map.  This is enough to name and reproduce the
base used by the experiment; `UNRESOLVED_LOCAL_HASHES_ONLY` should not remain a
blanket label on future runs.

Do **not** rewrite historical receipts or retroactively call SEQ-120 clean.  Its
original plan did not predeclare the cache-ref/upstream-revision check, and its
separate authored-data/lineage limitations remain.  Record this as a post-hoc
identity resolution, then make the binding prospective for Q0, clean birth,
Level 2, and the final paper run.

