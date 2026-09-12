# Interleaved-memory seeds 1/2: independent raw review

**2026-09-12 — PASS (custody/recount); both prespecified FOUR thresholds met. EDIT-STOP.**

Both complete capsules were supplied before this reduction. Recounted **448 new calls**: two seeds × SINGLE/FOUR × (dev48 + exact16 + lexical48). Additionally recounted the 96 archived original-parent dev calls; these are inherited observations, not new evaluations. No omitted panels, invalid-case exclusions, scientific retries, or outcome-dependent selection. Counts agree with every stored panel reduction; **zero contradiction flags**.

## Raw results and threshold decision

| Seed / arm | Dev memory /16 | Exact /16 | Lexical families 0 / 1 / 2, each /16 | Habit adherence /32 | ACT correct /32 |
|---|---:|---:|---|---:|---:|
| 1 SINGLE | 16 | 15 | 16 / 15 / 16 | 32 | 32 |
| 1 FOUR | 15 | 15 | 15 / 15 / 15 | 32 | 32 |
| 2 SINGLE | 4 | 5 | 4 / 4 / 4 | 0 | 0 |
| 2 FOUR | 16 | 16 | 16 / 16 / 16 | 32 | 32 |

FOUR requirements were **dev memory ≥15, exact ≥15, each lexical family ≥15, habit adherence ≥30, ACT correctness ≥31**, plus technical completion. Seed1 passes at the memory boundaries; seed2 passes all criteria. SINGLE results do not determine this gate. This review reports the decision implied by fixed criteria; it launches/promotes nothing.

**Important error distinctions:** Seed1 FOUR answers `blue` instead of `green` for device-011 on dev, exact, and all three lexical families. Seed1 SINGLE is correct on dev; device-004 is `blue` instead of `green` on exact and `red` instead of `green` on lexical family1. Thus equal exact totals do not mean equal errors. Seed2 FOUR has no errors. Seed2 SINGLE answers `green` throughout dev memory (4/16); exact answers are ten `yellow`, six `green` (5/16). Its lexical families have green/red counts 15/1, 16/0, 13/3, each yielding 4/16. Full case IDs, labels, prompts, and unaltered outputs are in the JSON.

Seed2 SINGLE's arithmetic is **not absent formatting**: all32 responses contain one valid PREDICT before one valid ACT. They are numerically wrong on all32 ACT targets. Output patterns are `PREDICT: 15 / ACT: 12` ×12, `12 / 12` ×3, `11 / 12` ×7, `32 / 12` ×2, `32 / 22` ×8. “Habit adherence” here requires correctness as well as ordering; its 0/32 must not be renamed pure protocol loss. All other cells have correct predictions/actions and ordering32/32.

Every new response is parser-valid, finishes with `stop`, and stays below its64-token cap: **0/448 cap hits**. Paired identical text/token sequences are seed1 dev47/48, exact14/16, lexical44/48; seed2 dev4/48, exact5/16, lexical12/48. Same scores never substitute for checking raw texts.

## Material, lineage, and isolation

Reconstructed both corpus JSONs byte-for-byte against sealed hashes from the original seed0 material anchor: **the same16 authored memory facts and first16 original arithmetic rows**, four presentations per source per epoch. SINGLE repeats the original question; FOUR uses four training phrasings. Dev, exact-original-training-prefix, and three held-out lexical phrasings all address those same16 facts, not80 independent facts or novel fact acquisition. Original labels, arithmetic sums, chat rendering, captured native prefixes, and all panel identities were checked independently of stored aggregate scores.

Each arm forks its corresponding **original80-update teach adapter**, not another interleaved child or the other arm. Seed1 inherited dev memory **7/16**, seed2 **3/16**, with habit/ACT32/32 each; raw recount matches sealed parent inventories. No new OFF run: original OFF4/16 remains inherited context, not a matched fresh control here. Original seed0 and older positive controls are not replacement parents.

Recipe per child: rank8, LR0.0003, matching optimizer seed1 or2, fresh optimizer with zero initial state entries, one carried adapter, frozen base; **10 epochs ×32 batches =320 new updates,400 cumulative**. Each scheduled batch has two distinct memories and two additions. Independently reconstructed epoch shuffles reproduce each selected-seed schedule hash and40 presentations/source. Receipt inventories show initialized state equal to parent, no dtype conversion, parent unchanged, all392 tensor hashes changed after fit, and20,185,088 trainable parameters. This verifies recorded write/state provenance, not utility by tensor change alone.

Native-accounting receipts and unchanged spans give per child **10,000 target tokens:1,280 memory +8,720 addition**, including the configured EOS handling. SINGLE input/context presentations66,160/56,160; FOUR67,120/57,120; padded slots76,960 each. No target/context drops, splits, or truncated items. Across four children:1,280 new updates,266,560 input tokens,40,000 target tokens,307,840 padded slots. Input tokens are **not matched**, even though padded slots and update/target budgets match. The selected schedule is reconstructed; no independent per-step execution trace or tokenizer rerun is claimed.

## Custody and nested costs

Verified both user-supplied capsule SHA256s and **548 unique regular metadata files each**, exact validation inventory/hashes, no unsafe paths, links, duplicate members, or weight/bytecode payloads. Verified plan seals, original-parent pins/inventories, panel/capture hashes, source/driver bindings, warm-state/fit receipts, and eight sequential successful worker windows per seed. Release JSON/XML hashes, launch PID/device/UUID, and watchdog launch bindings reconcile. Both watchdogs observed controller exit before deadline with **no signals attempted**. Their `gpu_release_verified:false` is explicitly controller-only scope, not a release failure; separate Main full-release receipts supply GPU cleanup evidence.

| Seed | Worker windows s | Controller s | Launch→full-release s | Through collection s | Full release UTC |
|---|---:|---:|---:|---:|---|
| 1 / GPU0 | 989.668 | 1175.048 | 1210.147 | 1210.574 | 23:03:37.296976 |
| 2 / GPU1 | 949.613 | 1164.114 | 1220.484 | 1220.903 | 23:04:22.219692 |

These are **nested, not additive**. Aggregate two-GPU through-collection reservation is **2431.477s =40.525 A40-min**, not elapsed concurrent wall time. Each is within its1800s controller +300s external-custody envelope, with140s cleanup reserved; no late observations/overruns. Four fit train times are101.9/89.0s (seed1 SINGLE/FOUR),79.0/103.1s (seed2); recorded trainer walls118.7/96.2/84.4/107.8s are nested too. Readouts total19,596 input and2,408 output tokens versus28,672 output-token ceiling; summed raw call intervals115.330s. Those calls/training are already inside worker/controller/full costs. No prior root0/parent training cost is added here.

## Claims and limitations

FOUR meets the stated joint memory/behavior endpoints on both additional roots. Seed2 shows a large within-root observed FOUR–SINGLE difference; seed1 is not a FOUR advantage (SINGLE is better on dev and two lexical families). Together with the previously accepted root0 tie, these are heterogeneous paired outcomes, **not general FOUR superiority or a mechanism/capacity proof**. No latent arithmetic erasure, separate-adapter necessity, operational parenting, freeze, G3/P1/H2 promotion, or seed selection follows.

Source bound in both plans is `22b7e528f6f62358981ed2264d30ee7242926160`; the local driver pin is verified. Preserve the literal provenance qualification: plans say `UNRESOLVED_LOCAL_HASHES_ONLY`, and native audit `native_origin_authenticated` is false despite its recorded native-tokenizer re-audit status. This review checks internally bound evidence, not independent source-origin authentication or rehashing native weight bytes (excluded from capsules). GPU vacancy and tensor/native-token evidence are receipt-level checks, not fresh GPU/model/native execution.

**Independence:** I authored older related replay code and the root0 raw audit, whose hash-pinned pure scoring helpers are reused. This is an independent reduction of raw replication captures against source labels, not a blind or fresh-author audit. No SSH/network/GPU/model/native/tokenizer/Git operations or changes to other owners' files. Preparation fixtures:17 PASS; both real-capsule runs and inherited raw-baseline checks PASS.

### Exact principal pins

- Seed1 capsule: `e3014e7b362c983e6bba053fa91605a3307959861f2838ec35cf3637f4e6b60d`
- Seed2 capsule: `0a46c83632af87b3988bfd685d2ebde9f4682dfa56d9ff68861c65774d924447`
- Watch capsule: `2f09fc740c78edd8ea4acf0bd7c3bf875bcd8b12d7f9500a1e3f9d746a8953fc`
- Seed1/2 plans: `0cb346c44656c4ecea1adc8f2cd969c5442f465453a0926813bc37c70a2f22bd` / `cafc5822aa32f917ef971720ba0a3a9244a0162b02f836da5128519216077a58`
- Seed1/2 original parent weights (receipt hashes): `97328c5aad9c8df9d98f336e19f2ad4682f4c88e662d61a9a30c3de4c2aed3cb` / `03955472524928e723800074660baac0aac7a4c2e2d8fec74c27b17639726bd2`
- Seed1/2 reconstructed schedules: `636fcf880d046300b9451713e6e151fb05baeac809d98630e3a3b9e79a77d164` / `6b7ddde68a08471209e7cc84c9763133b6f4649ed01dea1702fd296159305b42`
- Full raw/result JSON: `/tmp/astra_interleaved_replications_independent_review_20260912.json`, SHA256 `5e8d8e1b4cf3c2f82510c4566b8a4fca14d62807c7925a329c952bdd93312718`.

The JSON also retains all child/base/source/material hashes, baseline rows, selected update schedules, threshold booleans, and watch receipts. Script default refuses replacing a completed review; explicit extension requires unchanged input pins and raw arm results. No root0 artifacts were modified.
