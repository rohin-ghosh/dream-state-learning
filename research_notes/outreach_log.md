# Outreach log
| date | who | channel | status | notes |
|---|---|---|---|---|
| 2026-08 | Jeremy Jordan | internal | meeting scheduled | SAE-probe compaction; hook = internal-repr vs task-outcome salience |
| 2026-08-18 | Yaosheng Fu | internal | MEETING (Aug 18) | systems/arch, RocketKV/SparDA; hook = eviction≈write policy; ask = inference-cost feedback + one agents-team intro |
| earlier | Yu Sun | cold email (ext) | no reply | bump due via INTERNAL channel |

## Fu brief (2026-08-18 meeting)
- Who: NVIDIA Research architecture/systems (since 2017; Princeton PhD,
  Wentzlaff/OpenPiton). NOT an agents researcher. Recent: RocketKV
  (ICML'25, training-free 2-stage KV compression, 400x), SparDA (2606.04511,
  w/ Song Han), EMPIRIC, AutoScratch (MLSys'23).
- Overlap: memory-as-a-system. His eviction policy = my write policy at a
  different timescale. RocketKV's coarse PERMANENT eviction is an
  irreversible salience decision from attention heuristics — the untrained
  version of the felt head.
- Hooks: (1) eviction≈write — has anyone tried task-outcome signal (vs
  attention mass) for KV retention? (2) surprise-is-toxic result — KV
  methods keep high-attention/surprising tokens; contrarian datapoint.
  (3) benchmark hygiene — leakage gates ≈ oracle-top-k baselines.
- Ask (senior IC, not manager): technical feedback on the gist-LoRA
  inference-cost story (does consolidate-to-LoRA beat long-context+KV-
  compression at the systems level?) + ONE intro to an agents/GEAR person.
  Feedback-first; no referral/collab ask.
