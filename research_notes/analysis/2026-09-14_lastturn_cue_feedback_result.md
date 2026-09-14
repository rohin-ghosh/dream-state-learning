# Last-user-turn versus system public feedback: terminal cue result

Scope: read-only capture of node2 `/tmp/astra_cue_lastturn_20260914_attempt1/run` and `/tmp/astra_cue_feedback_20260914_attempt1/run`. New local evidence is confined to `gpu_artifacts_local/astra_lastturn_cue_feedback_result_20260914/`. The saved-actor memo scope is released. No current sleep2-fit access, model/tokenizer/scorer loads, GPU actions, launches, remote writes, notebook or project-code edits. Main's native-helper full replay is not repeated or independently recertified here.

## Bottom line

**Last-turn placement produces8/8 selected, read-containing GOAL arrivals and20 actual student rows. System placement produces2/8 selected and4 rows, although it reaches GOAL on4/8 tasks.** Two system-feedback arrivals contain no READ and correctly remain unselected. The frozen selection rule is unchanged.

The last-turn actor follows the exact public-feedback command on **20/20 calls**, versus **2/12** under system placement. It covers both branches: four matching first READs followed by ROUTE, and four mismatching first READs followed by the second READ and then ROUTE. This is a strong **coached collection** result. The teacher explicitly supplies the next action after computing the public comparison; the result does not yet establish unassisted learner use of that comparison or successful learning from the stripped rows.

| Quantity | System feedback | Last-user-turn feedback |
|---|---:|---:|
| Source commit | `3400fd1970f4f8f55e877b1809357710a18264f9` | `e840a2430f9203fc4d67d435a81f6fe5510c9586` |
| Teaching mode | `public_feedback_v1` | `last_turn_feedback_v1` |
| Terminal UTC | 2026-09-14 09:28:39.0346417 | 2026-09-14 09:32:48.2722192 |
| Tasks / retained EVENTs | 8 /8 | 8 /8 |
| Native actor calls | 12 | 20 |
| Zero /one /two READ paths | 4 /4 /0 | 0 /4 /4 |
| External READs | 4 | 12 |
| GOAL arrivals | 4/8 | 8/8 |
| Selected read-containing arrivals | 2/8 | 8/8 |
| Selected rows | 4 | 20 |
| Selected READ /ROUTE targets | 2 /2 | 12 /8 |
| Complete selected two-GOAL pairs | 0/4 | 4/4 |
| Fits /new exploration-EVENT calls | 0 /0 | 0 /0 |

Both terminals are `COLLECTION_COMPLETE_NO_FIT`, using the same saved actor, fixed explicit strategy, source-memory bindings and task corpus. This sidecar evaluates no current or subsequent fit.

## Exact bytes moved, not a new feedback rule

The two frozen `public_feedback(messages)` function source segments are **byte-identical**; segment SHA256 is `1986fca8443d35b18ea4770c4aa0bc38d799b3342c59085a9065e702c41e2bbc`. The fixed explicit GUIDANCE is also identical, SHA256 `fc16a673dd0eacad94582818096424bc9e8cae40515824ab9969a19b7e899eac`, and remains appended to the **system message in both arms**.

For each actual public history, let `F` be the exact public-feedback suffix. Its common leading bytes are:

```text
"\n\nPublic-feedback teacher inference (not compiler or autonomous child inference): "
```

The quotation marks delimit the string, the `\n` notation denotes two literal LF bytes, and the prefix ends with one space. The complete suffix then supplies an initial READ instruction, a match-directed ROUTE, or a mismatch-directed READ. Exact examples from last-turn calls0,1,3 are:

```text
Initial instruction: READ EVENT E_5HCRPPRJEI
Returned EVENT AT matches NODE and GOT matches GOAL. Use that record DID: ROUTE P_FHXBVFTMPD
Mismatch: GOT N_PUYT3FQUOG does not match GOAL N_ZGTZAZYGEF. Read unread listed address: READ EVENT E_DM7QH4AQSU
```

Actual transformations verified against all32 outer CALL prompts:

- System mode: `system = public_system + GUIDANCE + F`; last user turn stays public.
- Last-turn mode: `system = public_system + GUIDANCE`; `last_user = public_last_user + F`.
- Every other message, message role, and the underlying public bytes are unchanged by the placement transform. No new message is inserted. After a READ, F is appended after the actual MEMORY RESULT text, preserving that text's original LF bytes.

The eight actual public histories shared between arms are the initial tasks, and their feedback suffixes match exactly. Later histories diverge because the actors choose different READs/actions, so the audit **does not claim equal advice text across different histories**. Instead it derives both placements for each of the32 captured histories using the unchanged frozen function and requires equality with that call's actual guided prompt. Each exact suffix and SHA is retained in `ANALYSIS.json`.

The feedback function reads only the public TASK and returned EVENTs. It checks AT/NODE and GOT/GOAL, then writes the correct next command into the teacher text. The observed contrast is therefore placement/role/recency of explicit public-derived coaching, not a newly learned comparison rule. A single run per placement does not establish a general mechanism or broader task success.

## Outcomes and branch coverage

Bank/task indices are zero-based. `I` denotes a first-address READ; `R2` denotes the distinct second-address READ after a mismatch. All last-turn paths start with the first listed address and terminate at the requested GOAL.

| Bank/task | System-feedback outcome | Last-turn branch | Last-turn global calls |
|---|---|---|---|
| 0/0 | GOAL without READ; unselected | first record matches → ROUTE | 0,1 |
| 0/1 | malformed command; failure | first record mismatches → R2 → ROUTE | 2,3,4 |
| 0/2 | read-containing GOAL; selected | first record mismatches → R2 → ROUTE | 5,6,7 |
| 0/3 | one READ → wrong GOAL | first record matches → ROUTE | 8,9 |
| 1/0 | GOAL without READ; unselected | first record matches → ROUTE | 10,11 |
| 1/1 | no READ → wrong GOAL | first record mismatches → R2 → ROUTE | 12,13,14 |
| 1/2 | one READ → wrong GOAL | first record matches → ROUTE | 15,16 |
| 1/3 | read-containing GOAL; selected | first record mismatches → R2 → ROUTE | 17,18,19 |

The four second-read targets are respectively `E_DM7QH4AQSU`, `E_CNHE5GRD6W`, `E_U2VS57WTI2`, `E_XP42SCQHJM`. Each follows a real first-record GOT/GOAL mismatch and yields the matching record used for commitment. The **four one-READ episodes contribute8 rows total**, and the **four two-READ episodes contribute12 rows total**, totaling20. Both banks contribute10 rows; all four two-GOAL pairs are selected on both members.

System mode's selected identities are only0/2 and1/3, with selected global calls2,3,10,11. Its apparent4/8 arrival count must not be substituted for2/8 read-containing selection. The malformed0/1 output is an echoed partial ROUTE TASK, not an observed wrong destination. Raw actions and terminal reasons for every task are preserved in `ANALYSIS.json`; no new selection or scoring rule was applied.

## Twenty actual, teacher-stripped rows

**`EXACT_FEEDBACK_PLACEMENT_AND_STRIPPED_ROW_JOINS_PASSED`.** This is a narrow prompt/row audit, not another collection replay or a replacement for Main's native sleep-admission helper.

For every last-turn row, the audit requires:

1. The source bank-local call index resolves to its recorded actor call and actual outer global CALL; the assistant target equals that actual raw generation, not an authored replacement label.
2. The row prefix equals the recorded **public** messages, and those messages equal the corresponding actor trace history. The guided view equals the actual outer CALL prompt after exactly the transformation above.
3. Both the fixed GUIDANCE and the entire feedback-prefix marker are absent from every student-prefix message. Genuine raw reader replies remain and match the address-keyed retained EVENT bytes.
4. The source episode is selected and the row's call index lies within that episode. Every selected episode contributes exactly its actual calls; no failed or no-read episode supplies extra rows.
5. Row policy remains prefix=`MASK_ALL`, assistant/EOT=`TRAIN`, target EOT=`<|im_end|>`. These are recorded row policies, not an independent tokenization or tensor-mask audit.

All20 last-turn calls become rows; global indices0–19 occur once. Targets are12 READ EVENT and8 ROUTE. Source call/episode indices reset by bank, so bank provenance is retained. Public-prefix lengths are eight2-message initial contexts, eight4-message post-first-read contexts, and four6-message post-second-read contexts. Feedback is never copied into the student's public history, even when it was appended to the actor's last user message.

Canonical selected-row hashes match the complete recorded bank reports:

- Bank0,10 rows: `2c1eda3922ec66f0d5e626f503244c63914b0110f54c522a3e3c9e34a2086981`.
- Bank1,10 rows: `de9baa281f0d0e2d2086399c83bf3286b1732507cad782e76c23d13157cf717f`.

The four system-feedback selected rows also pass the same direct joins. Frozen `_failure_kind`, `_rows_from_success`, and `run_collection` source segments are unchanged between the two sources; only the supported placement transform/option is added. Thus the8/8 result is not produced by loosening selection or manufacturing target rows.

## Bindings and limits

Both runs record identical task/master, raw-memory input bindings, saved-adapter file hash, original adapter-training RESULT hash, actor collection provenance and before/after adapter-state hashes. All eight raw address-keyed memories and public tasks compare exactly between the captured reports. Both record zero new exploration/EVENT calls, fits0 and unchanged frozen base/adapter state. This bounded audit does not revisit live adapter bytes or the current fit; those broader bindings were addressed by the prior saved-actor audit.

The seven captured source files match their declared immutable Git snapshots, including the e840a243 last-turn wrapper and pure collector. Only the frozen pure prompt functions/parsers are imported. Import guards exclude native GPU/model/tokenizer libraries and scorer modules. `run_collection` and its episode replay are not invoked. No mutable current wrapper or sleep2 path is inspected.

These are coached, external-memory, training-corpus successes with teacher-free **stored inputs**. They establish a useful source corpus and a prompt-placement contrast, not that an unassisted student already acquired the policy. Native admission and any subsequent fitting/readout remain Main's scope.

## Bounded capture receipt

Root **L** = `gpu_artifacts_local/astra_lastturn_cue_feedback_result_20260914/`.

- **81 payload files,985,233 bytes**, remote/local/remote-after hashes verified. Includes both complete terminal runs, six launch/source-binding receipts and seven frozen source files. No weights, caches, process state, current-fit files or unrelated roots; no old-local or remote overwrite.
- `L/evidence.tar.gz`:95,901 bytes; remote/local SHA256 **`a68184dca5a8480c64f862004db67e108698ada89630f3a2ac4bdaf536a12e4b`**. Archive includes81 payload files plus its remote manifest.
- `L/capture/REMOTE_MANIFEST.json`: remote/local SHA256 **`4bab5a18e3ce204e82503d121b5302b64132bcaf991699c5ec068304ef3a4c19`**.
- `L/MANIFEST.json`: enriched local SHA256 **`0fadc6889d553b14a954aeeb2652c50a615ca034f5810cbaf62f2eb9b6346049`**; per-file remote paths, byte counts and three-way hashes.
- `L/ANALYSIS.json`: exact prompt/suffix comparisons, actual student rows, source snapshots and branch/outcome diagnostics; SHA256 **`df046bef3c3ab1dbd121920ae04983007c6079a1a8d0ce5f34178f717adfb42a`**.

| Source file under captured arm/run | SHA256 |
|---|---|
| feedback/RESULT.json | `684ccd7af347d1333f7e2eafd62034c41ce596d420b12d079f8999d3198acc94` |
| lastturn/RESULT.json | `020d98483aaa150f288e2a330dfb8e0a8683210a6b3b6065eff08f230b086c99` |
| feedback/BANK_RESULTS.json | `06b357453fe2148e303e9872181f164ccdceaf8be407c01d0153711165e27c1b` |
| lastturn/BANK_RESULTS.json | `e331d9a70d552ba88d8e854634553483562559c1c242795d37462eb1d656a65a` |

`L/LOCAL_SHA256SUMS` seals the narrow analysis utility, receipts, archive and this memo. Main's current fit is not part of this capture or conclusion.
