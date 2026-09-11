# F_r16k16_neg64 operational resume receipt

Date: 2026-09-11

Status: exploratory mechanism scout; no scientific result is reported here.

The registered `F_r16k16_neg64` abstention cell first stopped before training
on node 2 because its intended content occupied 263,872 tokens while the
launcher had been given a 250,000-token corpus cap. The failed receipt was
preserved as:

- `logs/corpus_bank0__F_r16k16_neg64__across__sleep4.budget250000.failed.out`
- `logs/chain_neg64_gpu0.budget250000.failed.out`

The cell was resumed at a 265,000-token cap. This is the smallest round-number
cap above the observed content size. It is 6% above the 250,000-token positive
cell and that dose difference must remain disclosed in any comparison. No
cell definition, owner/binding bank, rank, epoch count, learning rate, or
measurement was changed.

Two workers were launched on node-2 GPUs 0 and 1, split as banks `(0, 2)` and
bank `1`. Both initially entered the shared bank-0 throughput precheck. The
bank-1 worker completed that precheck and proceeded; the other process failed
closed on the temporary-file race. The produced bank-0 JSON was parsed and
checked before the bank-0/2 worker was restarted. Its recorded statistics
were 12,688 items, 264,986 tokens, 263,872 content tokens, 1,792 negative
items, `over_budget=false`, corpus SHA prefix `632a62ef85dd5c0c`, and items SHA
prefix `c7faca84e7ade75a`. The race failure is preserved as
`logs/corpus_bank0__F_r16k16_neg64__across__sleep4.race.failed.out`.

At the post-restart check, bank 0 and bank 1 were both training independently;
bank 2 remained queued behind bank 0. The measured projection was 22.8 minutes
per fit at 612.4 tokens/s. Current experiments otherwise remained untouched.

