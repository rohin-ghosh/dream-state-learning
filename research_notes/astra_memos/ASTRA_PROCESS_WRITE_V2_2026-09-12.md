# SEQ-115: own-wake process-v2 writes — September 12, 2026

**Two finite writes completed; behavioral utility is not established.** Each
arm independently fits a fresh-base rank8 LoRA on two original child wake
continuations. Neither starts from the earlier record-write adapter. The
parent-free readout launched at22:58:48.818483UTC and remains a separate result.

| Arm | Updates / epochs | Input / supervised presentations | Final training loss |
|---|---:|---:|---:|
| Process P |12 /12|9120 /384|0.000196301334654|
| Active-neutral A |12 /12|9096 /372|0.000449771119747|

Both use seed2, rank8, alpha16, dropout.05, AdamW LR1e-4, batch2, and a
frozen Qwen2.5-7B-Instruct base. Each saves392 finite LoRA tensors and trains
20,185,088 LoRA parameters. All24 observed forwards have finite losses;
there are no split, dropped or skipped rows. Weight finiteness is attested by
the native collector; the metadata capsule does not contain weight tensors.
The falling in-sample losses do not demonstrate useful learning decisions.

## Material and limitations

The four fixed source slots are P calls0009/0024 and A calls0039/0054 from
interaction_v3. Complete original wake text, including wrong predictions,
remains unchanged. Only the source-bound temporary-restatement block is
removed from conditioning; earlier child history and public outcomes remain.
This is explicit context distillation, not unchanged native conditioning or
proof of scaffold-free cognition. No future target outcome or RECORD text is
inserted into the target.

V1 rejected A0's executed `TRY:` alias because it required literal `ACT:`.
The preserved V1 shortage was followed by an explicitly exploratory V2
amendment accepting the existing interaction_v3 action grammar. No slot was
replaced and no target was corrected or selected for correctness. V1 remains
the exporter default; this experiment explicitly selects V2.

Native labels mask context and padding with-100 and include exactly one EOS
after the unchanged raw target. P has32 target tokens per epoch; A31. Both
execute9120 padded input positions, but unpadded input and target exposure are
unequal. This is update-matched, not token-matched. Finite parameter writing
does not establish parenting efficacy, P1, G5, H1/H2 or a mechanism freeze.
Model origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`; no clean-lineage
promotion. Formal guard enforcement remains reserved for final C11.

## Custody and cost

Source `4c3064c1c3eef068951e9c3b2ca46630754564e7`; plan
`67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44`.
Root `~/astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1`.
Former node3GPU2 controller248787 completed; native collector confirmed full
process/session/GPU/queue release before subsequent readout allocation.

Supervised workers251.878129s are nested within controller484.619945s.
Collection68.362955s overlaps the912.231957s launch-to-final-observed-vacancy
interval, which includes waiting and CPU gaps. Do not add these clocks or
call the full interval active GPU compute. Timing asymmetry is unexplained.

The68-member metadata capsule SHA256 is
`9db826c86b306ba5a92bcfc2902e0baaaed83318f1c70b029cb0ca062ec17e5a`.
Validation SHA256 is
`fbc01b2979003948869cc25f5ae00ecae12a357681791706089658e11eed62db`.
Main reran the offline synthesis successfully, checking every capsule member,
native preflight/forward joins, source slots, masks, exposures and finite
receipt losses. Arendt authored the writer/collector and this synthesis;
this is author-side verification, not an independent raw behavioral audit.

Detailed script, JSON, synthesis, collector tests and capsule are archived in
`receipts_20260912/`. The next decisive observation is the already-running
parent-free decision readout; a completed write alone supplies no utility claim.
