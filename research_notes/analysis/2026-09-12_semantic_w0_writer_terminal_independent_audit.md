# Semantic W0 writer: independent terminal raw-artifact audit

Date: 2026-09-12 UTC

Scope: fresh, read-only terminal audit of node-3 run
`/localhome/local-rohing/astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1`,
its frozen `d160e0b2` source, its sealed raw records/adapters/receipts, and the
related committed preparation, launch, OFF-only, and ceiling receipts. I first
read `AGENTS.md` in full, then the complete prelaunch watcher audit and the
relevant Builder entries in `research_loop/COORDINATION.md`. I did not edit or
run builder code, use a GPU, launch or stop a job, or change the notebook. This
memo is the only file I created.

## Verdict

**The run is terminal, intact, and exactly replayable. Its registered result is
`OPTIMIZATION_INCONCLUSIVE`, with combined gates `oracle=true`,
`optimization=false`, `binding=false`, `interface=true`, `spill=false`. It is
not a selective-writer result.**

The most defensible scientific reading is stronger and more specific than the
priority-ordered label:

- Four fresh-base LoRA fits really executed for 256 steps each, made distinct
  nonzero adapter updates, lowered the repeated online training loss, and
  produced large effects after fresh adapter reload.
- The learned effect was dominated by a broad exact-action-sequence habit and
  coarse map-dependent action bias, not the required held-form conditional
  policy. Held generation stayed near chance (`0.5000`--`0.5781` balanced
  accuracy) and every registered binding cell failed.
- Locality failed decisively even under the registered, incomplete binary-TV
  reducer: all 16 cell/family means were `0.2752`--`0.6597`, versus the `.05`
  ceiling. Direct raw-score analysis additionally finds a pervasive unregistered
  common-mode effect: both complete action strings gained probability on every
  one of the 384 locality item/adapter pairs, and the log probability of their
  summed exact-sequence mass rose by at least `21.5762` nats on every item.
- The optimization gate cannot diagnose learner failure: the OFF scores make
  its half-nat requirement mathematically impossible for 30/64 key-map groups,
  including at least seven in every cell. The adapters passed that requirement
  on 29/34 groups that had enough OFF headroom, but the all-16 conjunction was
  impossible before ON existed.
- Exact-train post-fit scoring is absent (`0/128` fit rows scored in every
  cell). Therefore row-level storage after reload versus held-paraphrase
  extraction remains unidentified. Streaming loss and the broad persisted
  action habit prove that training changed the adapters; they do not prove the
  intended 16-key associations were stored.

This is evidence about four deterministic, root/seed-confounded supervised
seen-key instances. It is not evidence of unseen-key generalization, compiler
semantics, population reliability, clean lineage, official model provenance,
parenting, retention, H1/H2 closure, or substrate incapacity.

## Authoritative identities and replay

| Item | Identity |
|---|---|
| Frozen source commit | `d160e0b26405a7e40eb7de0dca23cfcb94cdbf37` |
| Frozen writer module | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| Manifest | `f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830` |
| **Terminal `report.json`** | **`31ea19f9d0c8807a30252340dc0582e829bb4ac6d1c438f712e590a909ad31af`** |
| Prepared capsule | `b9e424534a2a288732dcba7c512d807c931dea9a9f9ea5897ddd32036157e689` |
| OFF-only partial capsule | `efc63f9aa17113dd4a7fc4431847b999d9de5004d18ffd03be36aa11fe03e192` |
| Launch script | `af439aa230489a008a55a715d6c3b80ffbc26040e7d3d808f9c55d1b8cfb0ce3` |
| Original controller stdout | `9e4480d176da221c1f16f9915aa13dcf78014d76bcaa100102ce56d7e2cd57eb` |

The terminal `SEAL.json` binds 1,864 files other than itself, including the
report, all 1,712 per-request raw JSON records, four adapter directories, all
four 256-line step streams, and every stage receipt. There are no missing or
extra raw requests, exactly 1,024 step rows, and no `FAILED.json`.

I ran the frozen source's CPU-only replay from the immutable node-3 checkout:

```text
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. CUDA_VISIBLE_DEVICES= \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  -m organism_v6.semantic_writer_diagnostic replay \
  --run /localhome/local-rohing/astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1
```

It exited `0` in 6.51 seconds. The replay regenerated the material, requests,
and fits under the pinned tokenizer; checked all 1,864 sealed hashes; checked
the 14 unique worker identities, stage ordering, deadlines, load/model/source/
adapter bindings, four distinct adapter hashes, all cleanup receipts, raw tree
hashes, and complete response-token accounting; reran the reducer; and required
exact object equality with the sealed `report.json`. Its compact stdout hash was
`9e4480d1...d57eb`, exactly the original controller-log hash.

Separately, I reconstructed the numerical endpoints directly from the sealed
requests, material, step streams, and raw token-logprob/generation JSON using a
standalone standard-library script, without importing the project reducer. All
reported scalar values matched within `1.78e-15`; differences were floating
summation order only.

The two committed tarballs are not terminal capsules. The first contains only
the prepared seven-file root, and the second only the two OFF stages. The
complete authoritative terminal evidence is the still-present sealed node-3
root. No separately committed complete terminal capsule existed at this audit
cut.

## Execution terminality and cleanup

The external launch receipt records controller PID 98756 at
`2026-09-12T13:08:31.866379Z`. The sealed controller `STARTED.json` records
`13:08:31.994031Z`. `RESOURCE.json` records 1,414.695 seconds through
`13:32:06.694598Z`; the report and resource receipt were written at that time,
the seal at `13:32:07.219655Z`, and the successful controller output at
`13:32:09.360669Z`.

Every one of the 14 stage costs has return code zero. Every corresponding
`CLEANUP.json` says `owned_group_empty=true`, with null error and null
cancellation signal. At `13:36:13Z`, I independently observed controller
98756 and every recorded supervisor/worker identity absent. A fresh all-GPU
compute-process query returned no process. No process was killed during this
audit.

There is one custody limitation. `RESOURCE.json` is written before sealing and
replay, so its duration and `wall_finish` omit the last roughly 2.67 seconds.
The launcher used a detached `Popen`, not an independent outer timeout, and
there is no sealed post-replay controller-exit or final GPU-release receipt.
Thus terminality and release are well supported by stage receipts, the complete
controller output, present process absence, and live GPU inspection, but the
complete controller lifetime/cleanup is not self-bound by the run seal. This is
the exact controller-lifetime defect anticipated in the prelaunch audit.

## Denominators and fit evidence

The sealed raw evidence contains exactly the registered 1,712 requests:

- OFF: 208 generation plus 192 scoring = 400;
- each fitted adapter: 168 generation plus 160 scoring = 328;
- total generation 880; total scoring 832; two candidate forwards per scoring
  request = 1,664;
- the two complete candidates contain respectively eight and seven scored
  response tokens, including LF and EOS;
- four fits, each 128 fixed-order rows over two epochs, batch size one, exactly
  256 optimizer steps, and 1,920 supervised target tokens.

All 880 generation records are legal exact actions with zero truncations and
zero multiple-`ACT` outputs. Formal primary validity is `1.0` in every cell and
every stratum. Native-copy canaries are `8/8` for OFF and for each compatible
adapter (`48/48` unique copy requests overall).

Training evidence from the sealed step streams is:

| Fit | Epoch-0 mean loss | Epoch-1 mean loss | First-32 -> last-32 | Repeated rows lower in epoch 2 | LoRA update norm |
|---|---:|---:|---:|---:|---:|
| root0/W+ | 0.391477 | 0.102662 | 1.195708 -> 0.096589 | 87/128 | 1.852419 |
| root0/W- | 0.405064 | 0.099415 | 1.276739 -> 0.093614 | 85/128 | 1.862776 |
| root1/W+ | 0.389810 | 0.097436 | 1.225395 -> 0.094316 | 73/128 | 1.885763 |
| root1/W- | 0.431020 | 0.103306 | 1.344267 -> 0.100843 | 72/128 | 1.789289 |

Replay also verifies that every evaluation started from a fresh base and loaded
the intended saved adapter with the expected LoRA tensor digest. This proves a
real, persisted update and a functioning execution path. It does not substitute
for missing exact-train row scoring.

## Primary and map metrics

The following table is reconstructed from raw records. “Headroom/pass” means
the number of 16 key groups whose OFF ceiling permits a half-nat gain, followed
by the number actually at or above half a nat. Action counts are
`[-mem2reg,-gvn]`.

| Cell | BA | OFF gain | Opposite BA | Mean target conditional gain (nats) | Headroom / half-nat pass | Target margin >= .5 | Stratum correct / strong-margin keys | Raw target-sequence gain (nats) | Action counts |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| root0/W+ | 0.578125 | 0.078125 | 0.421875 | 0.879937 | 8 / 7 | 0/16 | 17/32, 0/8; 20/32, 0/8 | 26.460999 | 47, 17 |
| root0/W- | 0.515625 | 0.015625 | 0.484375 | 1.001103 | 8 / 8 | 8/16 | 16/32, 4/8; 17/32, 4/8 | 26.604368 | 3, 61 |
| root1/W+ | 0.500000 | 0.015625 | 0.500000 | 0.664463 | 9 / 8 | 3/16 | 15/32, 0/8; 17/32, 3/8 | 26.007159 | 2, 62 |
| root1/W- | 0.531250 | 0.015625 | 0.468750 | 0.570680 | 9 / 6 | 3/16 | 18/32, 2/8; 16/32, 1/8 | 25.922419 | 54, 10 |

There are 33/64 positive median conditional gains and 29/64 at least half a
nat. All 29 half-nat successes lie among the 34 groups for which the threshold
is mathematically reachable.

The complementary-map adapters often reversed their preferred action, but not
in a key-correct way. On the 64 identical held prompts per root, root 0's W+ and
W- adapters changed the greedy action on 44 prompts and both maps were correct
on only 25; root 1 changed on 52 and both were correct on only 27. Scored
two-candidate winners flipped on 44/64 and 58/64 respectively. Together with
the severe cell-level action imbalances in the table, this is consistent with
coarse adapter/map action bias plus partial conditional score movement, not
reliable carriage of the 16 tool-mode policy.

The registered binding rule requires, in every cell, BA at least `.80`, OFF
gain at least `.20`, BA-minus-opposite-BA at least `.50`, at least 12/16 strong
key margins, and both strata at least `.75` accuracy with at least 6/8 strong
margins. Every cell misses all of those requirements. Therefore
`binding_ok=false` is independently decisive and is not an artifact of the
impossible optimization gate.

## Registered spill metrics and the two false-pass defects

Each entry below is registered mean binary TV, followed by the reported item
maximum in parentheses:

| Cell | Missing | Unsupported | Neighbour | Wrong root |
|---|---:|---:|---:|---:|
| root0/W+ | .3104 (.3962) | .3190 (.4368) | .3759 (.4803) | .2752 (.5640) |
| root0/W- | .5189 (.7055) | .6061 (.7182) | .6597 (.7916) | .3807 (.6978) |
| root1/W+ | .6056 (.7293) | .6339 (.7390) | .6110 (.6968) | .5087 (.7288) |
| root1/W- | .3261 (.4766) | .3530 (.4166) | .3224 (.4486) | .3088 (.5714) |

Every registered mean exceeds the `.05` threshold by a large margin, so all
four cells and the combined `spill_ok` gate fail. This conclusion survives both
known reducer defects.

### Common-mode action probability

The registered TV renormalizes only the two candidate strings and is invariant
to a shared increase in both complete-sequence log probabilities. I therefore
computed, for each locality item, the change in
`log(exp(S_mem2reg) + exp(S_gvn))` from the same-prompt OFF record to the fitted
record. This is a diagnostic reconstruction, not a retrospectively invented
pass threshold.

| Cell | Items | Mean change (nats) | Minimum | Maximum | Both candidate totals increased |
|---|---:|---:|---:|---:|---:|
| root0/W+ | 96 | 26.2331 | 21.6072 | 31.8410 | 96/96 |
| root0/W- | 96 | 26.2416 | 21.5762 | 31.7017 | 96/96 |
| root1/W+ | 96 | 26.7990 | 22.9738 | 30.9505 | 96/96 |
| root1/W- | 96 | 26.7815 | 23.0240 | 31.0147 | 96/96 |

Even the smallest change is a factor of approximately `2.35e9` in the summed
probability of the two exact action sequences. The effect covers missing-mode,
unsupported-mode, neighbour-key, and wrong-root prompts, not merely the held
primary panel. Thus the common-mode blind spot did not manufacture a false pass
here—the binary TV already failed—but it hid an additional, pervasive global
action-sequence propensity that directly answers the motivating “global action
habit” concern in the negative.

### Signed legal-rate cancellation

The registered legality endpoint is `abs(mean(signed item transitions))`, which
can falsely report zero when valid-to-invalid and invalid-to-valid items cancel.
That implementation defect remains real. It was not active in this particular
run: all 880 generated outputs were valid, and for each adapter all 96 locality
pairs were valid both OFF and ON. Direct directional counts are zero
valid-to-invalid and zero invalid-to-valid in every cell. The reported zero
legal-rate changes therefore represent no transitions here, not cancellation.

## Impossible optimization gate

For target `t`, the registered conditional gain is
`log q_ON(t) - log q_OFF(t)`. Since `log q_ON(t) <= 0`, its maximum is
`-log q_OFF(t)`. Applying the exact median-of-four key reducer to the sealed OFF
scores yields:

| Cell | Half-nat-impossible keys | Headroom-feasible keys | Actual half-nat passes |
|---|---:|---:|---:|
| root0/W+ | 8 | 8 | 7 |
| root0/W- | 8 | 8 | 8 |
| root1/W+ | 7 | 9 | 8 |
| root1/W- | 7 | 9 | 6 |
| Total | 30 | 34 | 29 |

The largest impossible ceiling is `0.487578124203`; the smallest nonexcluded
ceiling is `0.511044663858`, so no classification is a rounding edge. The root
mean-gain asymmetries, `0.121166` and `0.093783`, satisfy their `.25` ceiling,
but cannot rescue an all-16 condition that is impossible in every cell.

Accordingly, `optimization_ok=false` and the priority label
`OPTIMIZATION_INCONCLUSIVE` exactly follow the frozen code, but they do not show
that optimization or learning failed. The held binding and spill failures are
separate observed negatives and remain scientifically interpretable.

## Exact-train scoring and what remains unidentified

The fit manifests contain 128 rows per adapter. Comparing every fit row's exact
rendered prompt with every score request in its fitted state gives:

| Fit | Exact fit rows | Rows with a post-fit score request |
|---|---:|---:|
| root0/W+ | 128 | 0 |
| root0/W- | 128 | 0 |
| root1/W+ | 128 | 0 |
| root1/W- | 128 | 0 |

There is no canonical train-form OFF/ON endpoint and no exact-train generation
endpoint. The only post-reload evaluations use held or locality forms. The
training-loss decrease shows that the online supervised objective became
easier, while post-reload raw scores show a persisted broad action habit. They
cannot distinguish exact row-level associative storage plus failed held-form
extraction from failure to store the intended row-level associations in the
first place. A successor needs prospectively frozen exact-train scoring as a
diagnostic; it must never rescue a failed held-form W0 gate.

## Gate-by-gate disposition

| Gate | Terminal value | Disposition |
|---|---:|---|
| `oracle_ok` | true | Bound external carrier prerequisite: all four exact-row cells were 16/16 generation and 16/16 scoring, with 32/32 complementary swaps, 16/16 native copies, zero truncation/multiple outputs, and zero optimizer steps. This is inference-only surface eligibility, not a writer score. |
| `optimization_ok` | false | Exact replay. Per-cell half-nat key counts are 7, 8, 8, and 6 of 16. The all-key gate was already impossible on 30/64 groups, so this gate is non-diagnostic about learner effectiveness. |
| `binding_ok` | false | Exact replay and independent reconstruction. All four BA, OFF-gain, map contrast, key-margin, and stratum requirements fail. |
| `interface_ok` | true | Exact replay. Primary and stratum validity are 1.0, multiple rate and truncations are zero, and every native-copy cell is 8/8. In fact, all 880 generation requests are valid. |
| `spill_ok` | false | Exact replay and independent reconstruction. All 16 registered mean-TV endpoints exceed `.05`; common-mode absolute action-sequence growth is also enormous. |

Because `classify()` checks optimization before interface, binding, or spill,
the public label names only `OPTIMIZATION_INCONCLUSIVE`. Any terminal summary
must also report the independent `binding=false` and `spill=false` facts; the
label alone obscures the dominant observed failure mode.

## Preparation and provenance limitations

The committed external node CPU log says 48 tests passed in 21.617 seconds,
and the prepared capsule and native-preparation JSON match the manifest/counts.
Those receipts are not incorporated into `manifest.json` or `SEAL.json`.
`builder_preflight_reference` is only a dated free-text string, and no sealed
native compiler/header/Triton receipt or exact CPU command/stdout/stderr hash is
present. Successful completion of 1,024 optimizer steps establishes that the
node's training path worked for this run, but it does not repair the missing
prelaunch provenance binding.

The manifest does bind the frozen source set, package versions, driver/GPU,
local model/tokenizer inventory, requests, material, fits, carrier proof, and
protocol. Its own boundary correctly states `clean_lineage=false`,
`official_model_authentication=UNRESOLVED_LOCAL_HASHES_ONLY`,
`training_run_replication=false`, and `root_seed_confounded=true`.

## Maximum defensible claim

This execution establishes that, in four deterministic fresh-base rank-8 LoRA
fits on the pinned local Qwen2.5-7B-Instruct snapshot, the recipe produced real
and persisted weight updates and made exact native action strings vastly more
probable. The two complementary training maps often drove opposite coarse
action preferences. They did **not** yield the preregistered 16-key conditional
policy on four held paraphrases: generation remained near chance, binding
failed in every cell, and large changes spread to every locality family. The
result is most consistent with a broad action-format/action-prior update plus
partial conditional score movement, not a selective semantic writer.

What failed is this recipe/assay instance's held-form binding and locality, not
the substrate in general. What remains unidentified is whether the intended
exact training associations were stored after reload but failed extraction,
or were never stored as row-level associations; exact-train scoring was not
run. The impossible half-nat gate also prevents an optimization-failure claim.
No automatic successor, qualification, parenting, retention, compiler-utility,
or H1/H2 promotion follows.
