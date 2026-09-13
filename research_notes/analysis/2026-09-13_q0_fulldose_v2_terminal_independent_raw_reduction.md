# Q0-FULLDOSE-v2 terminal independent raw reduction

**Date:** 2026-09-13 UTC  
**Role:** fresh, read-only watcher reduction  
**Frozen implementation:** `gpu/astra_pairwise_q0_fulldose.py`, SHA-256
`f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca`  
**Predeclared map sidecar:** commit `5695d65a`, memo SHA-256
`2cee7e3757d31903d31fea9afee45a4c716dbd360d712e6e077842fd4a91d15b`

## Terminal verdict

`R0` and `R2` are complete, replayable
`Q0_V2_FULL_DOSE_ENDPOINT_FAIL` roots. `R1` is a replayable
`NONREPORTABLE_RUNTIME_ABORT`: both fits and their 32/64/128 snapshots exist,
but the final `P_DERANGED/128` readout never began because the worker's
pre-load `nvidia-smi` identity query timed out after 15 seconds. It is missing,
not zero, and the prospective no-retry rule is preserved.

Therefore the campaign cannot support the registered all-three-root success:
two complete roots already fail every acquisition cell and broad locality, and
the third has no endpoint. This is not a three-root statistical failure rate;
it is two scientific endpoint failures plus one infrastructure-incomplete
root.

The strongest supported finding is narrower and more informative than “more
dose did not help.” In both complete root/learner-seed-confounded instances,
128 pairwise updates substantially lowered the fitted loss and preserved
strict action syntax/copying, but did **not** acquire the complementary
tool-by-mode policy. Instead, both independently trained opposite-map adapters
moved the shared `mem2reg - gvn` output surface in almost the same global
direction (`cosine=.9961/.9973` at update 128), while keyed XOR separation
remained tiny. The same updates caused large changes on panels that were never
trained. Under this rank-8/pairwise/128-update recipe, the writer is a broad
common action-bias writer, not the required conditional and scoped writer.

This is supervised excluded-DEV evidence only. It does not test or establish
child-authored sleep, parenting, clean lineage, retention, H1/H2, recurrence,
or the integrated Dream–LoRA–Think organism.

## Custody before score access

I first checked the node-2 Python process table: no Q0 controller or worker was
present. I then reran the external custody memo's exact command from inside
each root:

```text
find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
```

All three digests and file counts matched the hashes recorded before any root
was scientifically interpreted:

| root | complete-root stream SHA-256 | files | custody |
|---|---|---:|---|
| R0 | `52c21a6e1ba5fa786a652998eacb91b348ab1da685a335e7b90494ca1383097d` | 18,153 | exact match |
| R1 | `006c21d38b763953e5a59ef5641d3fe7683e3e32f71a84bb879c7de667a9db87` | 17,567 | exact match |
| R2 | `350befebaa2a31768b05254c98443435c58d5d8610c6f1515e89218afd2a14dc` | 18,153 | exact match |

The principal internal bindings are:

| root | manifest | prepared | seal | finalized | reduction |
|---|---|---|---|---|---|
| R0 | `b21fba8b93130a24d95164b87ec45448d4f20b28c0079dcb018479d707d3b01e` | `44cb464002a7e477e876d5bbd0ea57d7602bfedd2c334e1a0facc5dcbec222f0` | `cbd1bbdd9767bc296508714063a45ed6a14b9ef5b6d5b19185066bf119128f4a` | `5cecfd81ef81b5d72179c11ff681356ae95b19dd24931fb22b96c83fdf9bcdf8` | `258e0a87179445d6e256f890cf31b7c2f5c843978693369f7bcb823daa47194a` |
| R1 | `509fd3ba6900e4bac6bcf071e187db5b98e3e81f1ce96561be0a8fb9480df2d3` | `1abdd31d538653916abd636a2683ed9743d628a635bb7a1ea2612f8ecb0ae615` | `d3a7fa5b18b74821955d06c5e4b28c88fd92586479fbd6d284e6c2ba8885ab87` | `ec1c4212ff93b5bfb4b20963a83dfc61c9ffa731944968b6f77568762d5e3eb0` | `512052da829d6ac0eebd1ee4be2975b8aacb0de9206bdcb56edd261ebfdf5e1d` |
| R2 | `eafe1e55b61e34bc48754cf94aebd4f04b7d22631fda2ab0da0933ae86428b4d` | `64419ef1fe6629c017b6465761d78daf320edc18dbe6bbcade3911b8ef75223c` | `73eff0eafa7dd4f136db2a29e706e3657aeb85ee55b51eab61981651acfb02a6` | `c2882a24e36ff4826e85b9997acec9b6bdf68753eef7e55cb75a178bf901ac78` | `281a8ef4bd20bf032da35e73dd78888864ebe06740814e75880084894efeb6cd` |

All three bind campaign SHA-256
`1f29967875bb7e84fd479c25a1a54aed59405675c9bccc74305be8449d7884df`,
the expected allocations `R0=(501,1)`, `R1=(502,2)`, `R2=(503,3)`, and
the same rank-8, alpha-16, dropout-.05, LR-`3e-5` recipe. The root and learner
seed move together and are not independently identified.

For every accepted stage I independently matched each receipt's `DONE`, log,
and cleanup hashes; matched every raw-event filename/hash to the corresponding
`DONE` inventory; and checked `owned_group_empty`, `gpu_processes_absent`, and
`reservation_release_verified`. Every accepted check passed. I did not use
`reduction.json` or a `FINALIZED` flag to calculate any count below.

## Exact work and replay

Both arms in every root received all 128 registered updates, 512 training-row
forwards, and snapshots exactly at updates 32/64/128. Their per-forward RNG
receipts were byte-equal within each root.

| root | accepted stages | updates | train rows | eval prefix events | generations | generated tokens | natural forwards | model forward calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R0 | 10 | 256 | 1,024 | 1,632 | 888 | 5,914 | 3,072 | 8,986 |
| R1 | 9 | 256 | 1,024 | 1,344 | 592 | 3,877 | 2,784 | 6,661 |
| R2 | 10 | 256 | 1,024 | 1,632 | 888 | 5,909 | 3,072 | 8,981 |

R1's last line is independently counted partial work, not scientific endpoint
accounting; its producer abort correctly reports empty scientific counters.

The native replay initially fails if run with the watcher's default
multithreaded CPU environment at exact raw-logit equality. With the launcher's
pinned `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1`, all roots replay exactly:

| root | replay result | report SHA-256 |
|---|---|---|
| R0 | `Q0_V2_FULL_DOSE_ENDPOINT_FAIL`, claim-bearing root | `7e3cd8644ba7643992a2331921ed2b1060593ade2860ff4536acb044e8a7e96b` |
| R1 | `NONREPORTABLE_RUNTIME_ABORT`, not claim-bearing | `c6a5b07549d8cefe12f40492f7b4b8f83d8e8b6532d1e8ad02ab91ab694715de` |
| R2 | `Q0_V2_FULL_DOSE_ENDPOINT_FAIL`, claim-bearing root | `e59900a2ea66f0b04f260a07b2b7e9540b258467893ceaf8e7bf8d6665b87694` |

This is not evidence mutation: the launch explicitly pinned the two thread
variables, and the custody digests match. It is a real replay-portability
qualification: exact replay must bind the numerical threading environment.

## Independent endpoint counts

The exact gate requires at least `116/128` total, `56/64` for each class,
`14/16` keys, positive median signed gain for both classes, `122/128` valid,
and no multiple action. The held gate requires at least `52/64`, `24/32` per
class, `12/16` keys, `61/64` valid, and no multiple action.

| root/arm | exact correct | exact class recall | exact keys | exact gain medians | held correct | held class recall | held keys |
|---|---:|---:|---:|---:|---:|---:|---:|
| R0 AUTH | 71/128 | 60/64, 11/64 | 7/16 | -5.3125, +5.2500 | 37/64 | 15/32, 22/32 | 9/16 |
| R0 DERANGED | 70/128 | 30/64, 40/64 | 1/16 | -5.6875, +5.8750 | 31/64 | 4/32, 27/32 | 8/16 |
| R2 AUTH | 65/128 | 46/64, 19/64 | 3/16 | -5.4375, +5.3750 | 31/64 | 7/32, 24/32 | 8/16 |
| R2 DERANGED | 72/128 | 45/64, 27/64 | 1/16 | -5.5000, +5.6250 | 32/64 | 4/32, 28/32 | 8/16 |

Every listed cell generated `128/128` or `64/64` legal single actions, no
multiple action, and copied `8/8`; OFF also copied `8/8`. Thus syntax and the
copy surface are not the endpoint bottleneck. The legal branch mass at update
128 stayed about `.99998`, also ruling out probability escaping the two action
tokens. The negative gain for one class and equally large positive gain for
the other is the signature of one global shift, not a learned conditional map.

Complementarity and wrong-root controls also fail by wide margins:

| root | exact opposite-and-correct (need >=112/128) | held (need >=48/64) | wrong-root opposites (need <=3/64) |
|---|---:|---:|---:|
| R0 | 39 | 10 | 14 |
| R2 | 28 | 4 | 8 |

All 16 complete-root arm/family locality cells fail. The mean absolute change
in conditional action probability `q` ranges `.2320..6120` (allowed `<=.05`),
and maxima range `.3199..8906` (allowed `<=.10`). Legal-pair mass changes are
tiny (`<4.1e-5`), so this is not vocabulary leakage; it is broad movement of
the chosen action within the correct two-token surface. Wrong-root generated
identity changes are `41/53` for R0 AUTH/DERANGED and `44/50` for R2. The
trained action mapping is severely unscoped.

R1 has only a partial endpoint: AUTH at 128 scored `67/128` exact and `31/64`
held and failed locality, but DERANGED/128 is absent. These values are
diagnostic only and never enter a paired root label.

## Optimization occurred; conditional acquisition did not

Mean pairwise loss over the first versus last 32 updates was:

| root/arm | first 32 | last 32 |
|---|---:|---:|
| R0 AUTH | 1.2116 | .7218 |
| R0 DERANGED | 1.1884 | .7025 |
| R1 AUTH | 1.0176 | .6994 |
| R1 DERANGED | 1.0526 | .7028 |
| R2 AUTH | 1.0831 | .7106 |
| R2 DERANGED | 1.0494 | .7121 |

This rejects “the optimizer did nothing.” It learned an easier common action
prior that lowered pairwise loss without learning the balanced XOR keying.

## Predeclared zero-cost map-dynamics sidecar

I reduced `Q1_MAP_DYNAMICS_SIDECAR_v1` only after all three fixed roots were
terminal. `R1` is `SIDECAR_INCOMPLETE`; R0 and R2 classify
`MIXED_OR_UNRESOLVED_DYNAMICS`, not `COMMON_THEN_KEYED` or
`KEYED_AT_FIRST_UPDATE`. Only R1 met the strict common-mode-dominates condition
at update 1, so common-first replication is unsupported (`1/3`) under the
predeclared rule. R0's first AUTH step was tool-component-dominant; R2's first
steps were XOR-dominant but DERANGED moved in the wrong XOR direction.

Nevertheless, the later complete surfaces converge on an extremely clear
common-motion diagnosis:

| root/update | median shared-global C | median split-XOR | delta cosine | both adapters choose their own opposite branch |
|---|---:|---:|---:|---:|
| R0/32 | -4.6719 | .0000 | .9919 | 7/128 |
| R0/64 | -5.6484 | .0000 | .9956 | 22/128 |
| R0/128 | -5.3125 | .0312 | .9961 | 42/128 |
| R1/32 | -4.9609 | .0156 | .9933 | 15/128 |
| R1/64 | -5.3438 | .0312 | .9957 | 29/128 |
| R2/32 | -4.6641 | -.0156 | .9918 | 9/128 |
| R2/64 | -6.1406 | .0000 | .9974 | 11/128 |
| R2/128 | -5.5156 | .0625 | .9973 | 28/128 |

The shared-global component is negative on all `32/32` quartets at every
listed checkpoint: both opposite maps strongly push from the base model's
`mem2reg` preference toward `gvn`. The required split-XOR median remains near
zero, and final own-map prefix-margin correctness is only `64/128` AUTH and
`53/128` DERANGED on R0, and `56/128` / `51/128` on R2.

For exact reproducibility, the final matched-vector hashes are:

| root/update | C-shared SHA-256 | X-split SHA-256 |
|---|---|---|
| R0/32 | `2eebd09a4f53937b611d60d1b36272fb9d147e1af3f22e13ec56785ac709ee32` | `a5b58671a978792679c824e9ee46c588fd6332c26d7db3fc4e7c3404ba60b6db` |
| R0/64 | `fd6131f2b98c159dc41fbb0d3b586f6afa8a81e296c3be3ef3473eee86a5a118` | `6a347697d1414af6072defbf7e99eb02cadd86ccc553e39b82a5f8c6f0f6fe71` |
| R0/128 | `7fc692e810094d06b2a3d01d5449796376c8631dd9263ddc985ad9342a00f568` | `1f2a53aa78fb00d5d27d7c45069e6538d63655a191c2ceeb43383bee48d48bb1` |
| R1/32 | `6ac6cb3bd830bcfd7b228f31beb0f614926696ace388fb045f0ae11bc62d78ae` | `7ac946aa2f3da36ea04654179fdf8474b409271e5fbd799dfad87c9ab5684538` |
| R1/64 | `6794737ad7615d8a0e80264eafbd46c451d077018d29ec84385dfe3ce5e21a8f` | `d6b20c0aaebab3c612f515f3cbc337854580bd492de40e381bb2ed24c6ce15da` |
| R2/32 | `0506d70ca15e833d7c5e21cd925500321b35517b94003e82f37b291e439bd308` | `6f6aba4f2a584431456e55e6a43f4e5ce3a5e3ceb37b36a06726354bb03821de` |
| R2/64 | `bd4ad8f78017e6becc599f6128cd5c4c797e6a34cb5b1825304a26e6bd28d3c9` | `3c0183cd124910f1cda1c97553ee29d617065f9798b75644f098a2322289c734` |
| R2/128 | `38916c7681b0b918fad6172b28cf281543c0ceb3021cc371960c13dc947c1763` | `1ef219ec4b207ea4cfd65db7deb2637e13f2ce98eff80d13cec9c28ad3cf5e70` |

The literal map-distance hypothesis is still false: AUTH and DERANGED disagree
on all 128 exact and 64 held targets and reside in separate adapters. The
evidence supports the revised mechanism—common-mode learning on a shared
output surface before/without the required keyed interaction—not cross-map
blending.

## R1 failure taxonomy and disposition

The final worker failed before model load in `gpu_identity()`:

```text
subprocess.TimeoutExpired: Command ['nvidia-smi', '-i',
'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4', ...] timed out after 15 seconds
```

The failure log SHA-256 is
`e2365c706d14944c9c172e277bf57e2ef2a38267ebd1a315f164046354e54702`;
the job, claim, process and cleanup hashes are respectively
`57206da1a0d46410059c0f340daaa8d5acaed4d79403005ba2fc73c6ea648cdb`,
`65df14c7785cb3e7f8ac0ea15955b450f15750f337140874b1fa13ca13f45ece`,
`051320f221a5d316270e52f3d0000dc61b74939f785ff48c245ffa9000a78fc7`,
and `7ba358f845ea2fcc4f04799dd6165299ef1d0f541e6d5708cb09f9564d694dac`.
Cleanup proves the owned group empty and the reservation
released. No DERANGED/128 raw readout exists. This is an infrastructure
failure, not model evidence, and the frozen no-retry policy means it stays
missing.

## Claim and next-design consequence

The old one-update stop was indeed too early to say what full-dose optimization
would do. Full dose now answers that narrower question: it learns strongly,
but mostly in the wrong functional basis. More repetitions of the same
balanced first-divergent-token loss are therefore low-value. The next writer
must make the conditionally keyed structure itself easier or more explicit
while preserving a strong scope/locality control; changing only rank, dose, or
the action vocabulary would not address the observed common-mode solution.

The result is useful negative mechanism evidence, not the requested paper's
headline. It rules out this direct pairwise writer recipe and sharpens the
release requirement for the authentic child-authored two-sleep bridge: the
writer must demonstrate both keyed separation and controlled locality before
any lifetime-learning claim can depend on it.

## Method boundary

I read the frozen protocol, exact source, independent static audit,
predeclared sidecar, and external custody memo. I used a standalone temporary
Python reducer streamed over SSH; it imported no producer module, read raw
`prepared.json` plus per-stage event/receipt/cleanup files directly, and was
deleted afterward. Only after completing the independent counts did I compare
them with sealed `reduction.json`; all common fields agree exactly. I did not
run a model or tokenizer, use a GPU, mutate a remote root, edit builder-owned
paths, retry R1, or inspect one root early to change another.
