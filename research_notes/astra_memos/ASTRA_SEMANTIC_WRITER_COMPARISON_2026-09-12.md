# Fresh semantic Q0 writer — prospective implementation specification

Main selection, September12,2026,12:50UTC. Prerequisite SEQ-080's complete
carrier pass and original-source replay are satisfied. No fit has launched.
This is a new DEV assay, not repair/promotion of the old W0 artifacts or final
C11 custody. Cicero owns only `semantic_writer_diagnostic.py` and its new test.

Namespace `semantic-writer-Q0-20260912-v1`; fresh opaque identifiers disjoint
from old W0 and the carrier. Preserve old orientations,16keys/root, two roots,
W+/W- mappings, paired order seeds100/200/300/400 and root fit seeds0/1.
Use old literal eight train/four held templates with the carrier's exact
response instruction plus one newline, in the pinned Qwen chat wrapper.
These are reused DEV grammar forms, not globally unseen templates. No binding
row, answer table, carrier output or oracle answer enters primary/locality
prefixes. Supervised action targets are real `ACT: -mem2reg\n` or
`ACT: -gvn\n` plus EOS. Audit coordinates never reach model prefixes.

Four separately initialized clean-base rank8/alpha16/dropout0.05 LoRAs;
frozen Qwen2.5-7B base; all seven projection modules; exact original
`EXECUTION_RECIPE`: AdamW3e-5,128rows,256steps/two epochs/fit, batch1,
masked context, BF16/eager, deterministic flags, no packing/SVD/gradient
checkpointing/scheduler/clipping or extra fitting. Preserve token-mean training
loss; score full unequal-length LF+EOS continuations without normalization.
Step8profiling is within the256steps. No checkpoint/outcome selection.

| Physical requests | Generation | Scoring | Total |
|---|---:|---:|---:|
| Own-root held:2roots×3states×64 | 384 | 384 | 768 |
| Missing/unsupported/neighbour:2×3×32 | 192 | 192 | 384 |
| Native copy:2×3×8 | 48 | 0 | 48 |
| Wrong-root ON:4adapters×64 | 256 | 256 | 512 |
| Total | 880 | 832 | 1712 |

States are OFF and each root's two adapters. Wrong-root OFF references reuse
the other root's exact OFF primary records; no duplicated baseline calls.
OFF400requests, each adapter328. Scoring entails1664candidate forwards.
The separate144carrier records are excluded. No old full-table oracle,
binary scoring of copy prompts, or extra train-form diagnostic is included.

Preserve the old primary conditional-log-q gain arithmetic and numerical
thresholds, including each of16key gains≥0.5, map mean-gain asymmetry≤0.25,
balanced accuracy≥0.8, OFF improvement≥0.2, opposite-map contrast≥0.5,
at least12key margins≥0.5, stratum accuracy≥0.75 and6margin keys,
validity≥0.95/stratum≥0.875 and zero multiple ACTs. Report raw full-target
sequence gains separately; do not call conditional log-q a raw NLL measure.
All four root/map cells must pass; no pooling or majority rescue.

Locality independently requires mean binary TV≤0.05 and ABSOLUTE legal-ACT
rate change≤0.05 for each missing, unsupported, neighbour and wrong-root
family. The signed-rate loophole is not carried over. Copy is separate exact
generation: all eight registered canaries must remain correct per state.
Wrong-root adapter owner and probed root must remain distinct in metadata.
Old result labels and the old1504denominator cannot be silently reused.

Actual full-panel native tokenizer preflight and CPU tests precede Main's
source/resource selection. Runtime bound: one continuously reserved A40,
≤3hours and the reported lease's six-hour finish margin; expected30–45minutes
is an unverified forecast until the step8and evaluation profile. No resources
reserved yet. Main pins actual deadline/source/commands and verified carrier
proof before launch. Reuse existing HF/LoRA/math/supervision primitives, not
new C11 machinery or monkeypatched old alphabet globals. Preserve every
failed attempt and raw record. Passing this finite synthetic test would not
establish general learning, parent removal, retention or clean ancestry.
