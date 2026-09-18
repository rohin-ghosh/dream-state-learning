# Rohin168 judge proposal: sources and observation

Recorded September 17, 2026, 12:47 PDT. This is a proposal, not a GPU launch,
model-admission receipt, production-judge change, or measured throughput result.

The web tool returned no usable source body or citation identifier. The three
official documents below were then successfully retrieved directly with bounded
HTTPS requests. Their downloaded bytes are preserved in `sources/`; the URLs
use moving upstream branches, so these hashes identify the actual documents
read, not pinned model weights or a reproducible future training installation.

| Primary document | Local file | SHA-256 |
| --- | --- | --- |
| Qwen's 3B vision-language model card | `sources/QWEN_3B_MODEL_CARD.md` | `0b6da5a154b923da4dc66e416140c9b7f235f9b08fbbcc27fd9df7b586e3150d` |
| Qwen's official fine-tuning guide | `sources/QWEN_FINETUNE.md` | `cba2c1d8286c348f1d63511d7b82fbecff5ec41c1a6093f7d9398d7cf15e9c41` |
| OpenAI's CLIP repository README | `sources/CLIP_README.md` | `f82c5c75e140532eb37a7d943921e1bdd57d740c6b40d0030985bc5b5d11d6f1` |

Source URLs, in the same order:

```text
https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/raw/main/README.md
https://raw.githubusercontent.com/QwenLM/Qwen2.5-VL/main/qwen-vl-finetune/README.md
https://raw.githubusercontent.com/openai/CLIP/main/README.md
```

Qwen's card identifies the 3B checkpoint and controllable image-token budget.
Its training guide exposes LoRA and independent vision/language/projector
training controls. CLIP exposes separate image/text feature encoders. These
establish available components, not cartoon-humor accuracy, single-A40 training
success, or the proposed time estimate. The estimate and recommendation in
COORDINATION are engineering judgments. No historical contest captions, ratings,
private similarity labels, locked-test data, or R176 sealed outputs were read
for this proposal.

Read-only node4 observation through `bash gpu/a40r_ssh.sh` at
2026-09-17 12:43:47 PDT: every card is an A40 with 46,068 MiB reported memory.
Physical2 used0 MiB (reserved text-judge slot); physical5 used19,289 MiB
(local Qwen tool); physical6 and7 used0 MiB. Physical6 UUID is
`GPU-06b31c8f-7a96-d812-23f3-df3444d95397`; physical7 UUID is
`GPU-6eac3b9d-551a-d786-f598-04ef6d701c98`. Physical6/7 are earmarked for the
not-yet-launched development pair, not unconditionally available. Physical3's
temporary zero use does not release its existing child's allocation. This
observation is not a device-confinement or capacity admission for a new run.

The current text-judge conclusion comes from
`../FIRST_SCORING_REPORT_20260917.md`,
`../data_judge/NEXT_CANDIDATE_V7.md`, and
`../data_judge/evidence/RECEIVING_V7_OBSERVATION_1789674188114523534.json`.
The last records a receiving CPU-test dependency failure before any V7 GPU
load. Main requested its owner repair the packaged test support in a fresh
attempt; no shared environment, child, checkpoint, or scoring configuration was
edited for this response.
