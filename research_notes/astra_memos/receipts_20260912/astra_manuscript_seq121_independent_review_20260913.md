# SEQ121 retrospective manuscript consistency review — EDITSTOP

## Bounded verdict

**PASS for consequential counts, evidence cut, abstract parity and scientific
claim boundaries, with two small wording findings for Main.** No numerical
correction, rescoring, new experiment or claim promotion is supported or needed
by this review. The six reviewed manuscripts were not edited. Main owns fixes.
This is retrospective manuscript consistency review, not a GPU gate, independent
scientific proof, native verification or launch authorization.

### F1 — name the conditional thresholds, not generic operation thresholds

Locations: `paper_prototype/main.tex:430`, `paper_prototype/README.md:39`,
`paper_prototype/astra_sprint_draft_20260912.tex:2411`,
`research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:2614`.

“AUTH passes operation-level thresholds” is supported only for conditional
PROSPECT32/32 against29/32 and REVISE58/64 against58/64. Addition15/16 fails its
16/16 floor. The nearby tables/prose explicitly report this failure, so this is
an avoidable scope ambiguity, not a concealed conjunction pass or wrong count.

**Minimal fix:** “AUTH passes the conditional PROSPECT and REVISE thresholds,
but fails the revision-twin and addition criteria.” Preserve all numbers and
the full-conjunction FAIL. This clarifies the supplied skim flag without
broadening the review or changing any criterion.

### F2 — qualify tokenizer verification as the independent review's scope

Locations: `paper_prototype/main.tex:468`, `paper_prototype/README.md:79`,
`paper_prototype/astra_sprint_draft_20260912.tex:2440`,
`paper_prototype/astra_sprint_abstract_20260912.md:10` and `:236`,
`research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:16`,
`research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:39`.

The grouped wording “native tokenizer decoding ... remain unverified” can be
read as claiming no verification anywhere. Ampere explicitly reports that its
independent recount did not independently decode token IDs or authenticate
weights/origin. That establishes a limitation of that review, not absence of
any native-capture tokenizer audit. The detailed C64 paragraph at claim-map2644
already uses the correctly scoped “No independent tokenizer decode”.

**Minimal fix:** “Ampere did not independently verify native token decoding;
official model origin and clean ancestry remain unresolved.” Apply equivalent
scope to the short status summaries. Do not imply an independent tensor audit,
and do not erase the genuine unresolved-origin/NOT CLEAN caveats. I have not
reopened original native receipts to assert either presence or absence of their
own decode checks; that broader assertion is unnecessary for this wording fix.

## Consequential consistency checks

- **TRAINED versus learned:** externally authored supervised birth fits, not
  child-generated learning experience or demonstrated self-learning. Companion
  C63 explicitly does not deny supervised parameter learning. Two128-update fits,
 256 total,11,648 target-token presentations each/23,296 total agree with the
  canonical design and terminal fit ledger. Same256 contexts, rank8, seed0,
  LR1e-4, four epochs, batch8 are consistent. Zero truncation/nonfinite training
  counts are attributed to the manifests, not independently rerun here.
- **Birth conjunction FAIL both:** all10 table rows and four numeric columns in
  README, claim map and companion TeX match the canonical birth memo exactly.
  OFF/AUTH/DERANGED strict PROSPECT0/32,32/32,32/32; REVISE0/64,58/64,56/64;
  belief/goal twins0/16,16/16,16/16 each; all three revision families0/32,26/32,
  24/32 each. Floors29/32,58/64,15/16,29/32 remain unchanged. Addition8/16,15/16,
  15/16 and copy8/16,16/16,16/16 require16/16. No anchor tag spill does not rescue
  either conjunction. DERANGED own-map counts are not AUTH truth; its AUTH-truth
  conditional joint counts remain zero. No threshold or control substitution.
- **Arithmetic/truncation caveats retained:** both trained cells'0097 emit89 for
  31+48=79; OFF's16 correct numeric sums are attributed to Ampere's descriptive
  manual inspection, not registered replacement scores. No arithmetic-improvement
  inference from trained15/16 compliance. OFF96/128 capped responses versus zero
  trained cap hits do not establish absent base reasoning. Trained128/128 raw EOS
  counts and the missing exact-train-form panel are stated without claiming a
  fresh tokenizer audit or locating acquisition versus access failure.
- **Formation0/4, NO WRITE:**28 calls=17 wake+4 parent+4 restatement+3 record;
  6/8 protocol-invalid tasks,1/3 faithful records, zero of four prescribed rows
  eligible, zero training calls agree with the canonical formation memo and
  SEQ121 terminal ledger. P lesson0 missing TRY, P lesson1 call0012 missing explicit
  forecast, both A slots missing canonical ACT;0011 faithful and0013/0015 wrong
  null-to-matched relation are consistent. No padding, later selection, target
  rewrite, corpus export, downstream fit or parent-free descendant comparison.
- **No causal birth harm:** exploratory AUTH child/base-only parents are explicit;
  no contemporaneous OFF formation exists. Teacher errors prevent neutral-parent
  purity claims. P's3/6 quizzes are descriptive in-context results, not retained
  parenting utility. The independent birth recount does not certify formation.
- **Ampere v2 accurately bounded:** metadata status FINAL_BOUNDED_COMPARISON_COMPLETE,
  comparison after384 outputs,10 explained differences, zero unexplained. Same
  two malformed dual-NEXT rows0007/0055 underlie the differences; not ten distinct
  failures or repaired successes. DERANGED AUTH-NEXT6/64 supersedes v1's8/64;
  assigned COMPARE/POLICY64/64 versus frozen62/64 remains an explained field-
  retention convention, with strict/joint failures unchanged. V1 is historical.
- **Cost and custody not overpromoted:** fit488.560991s plus readout949.620845s
  equals1438.181836s/23.969697 A40-min, excluding the inter-phase gap; formation
  379.776464s/6.329608 A40-min. Nested collection/controller/call spans are not
  added. Main's39/814/80 member checks are attributed custody, not my rehash of
  capsules or authentication of native weights/model origin.
- **Claim cut:** NOT CLEAN and UNRESOLVED_LOCAL_HASHES_ONLY retained; no full birth
  qualification, G3/P1/G5/H1/H2, clean-lineage, useful-self-learning or mechanism-
  freeze promotion. Collaborator stays UNSENT. No clarification-probe outcomes
  or live status were inspected or used as manuscript evidence. Earlier evidence
  was reviewed for preservation, not independently re-adjudicated.

## Exact six manuscript hashes reviewed

All six matched Singer's final-v2 handoff hashes and remained unchanged through
the last read-only hash check.

| File | SHA256 |
| --- | --- |
| `paper_prototype/main.tex` | `5204792206d1d0138cfe81035bad1501cd84b3742248c517e5f0f9026a37df11` |
| `paper_prototype/README.md` | `e0de867b35b1b8854c1684ab8672e34391b4e0fb1e7a5243e5f4356e6a64355b` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `e0d5a79595fc7e6185c79b9c6879e20ce9ff0336eccdb73c51a7ae63f753a276` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `ce984a99fcba2da451ef7cbfb7a0e432180987ace287ffb52fd2c40b320b9f60` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `603b95bccd7542bf70c598bb97888d9240b0649dafe5fb154bc3bbd120745e81` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `8eb1a1ef731825e8dbbf07ec1e9e93fdee7ffad49eef31fa1658f2c86971bc67` |

## Supporting evidence read, not independently regenerated

- Singer handoff `/tmp/astra_manuscript_seq121_handoff_20260913.md`:
  `f644a82ef01db74d054d1daabe79667e56722caac908d7507eb78606eeba02b5`.
- Canonical birth memo `research_notes/astra_memos/ASTRA_BIRTH_COMPONENT_RESULT_2026-09-13.md`:
  `57d1045632d6284b6c14f05abe736f5bc27735403b01227a279e3cedb4824991`.
  This current memo includes its v2 addendum; C63 labels its older
  `d6c6d836...` binding as a read-snapshot hash. I do not claim those different
  snapshots have equal bytes or that I reconstructed the earlier memo.
- Canonical formation memo `research_notes/astra_memos/ASTRA_BORN_PARENTING_FORMATION_2026-09-13.md`:
  `f8d1f838ae2e290fd9c33c0fda4cb05fec11ac9eb0e01a3ce95cf9ab053f30de`.
- Ampere v1 Markdown `/tmp/astra_birth_readout_independent_review_20260913.md`:
  `b07f63bb104412c70cf2471584428379bbc3d8770c12706288c13434091b2e35`.
- Ampere v2 Markdown `/tmp/astra_birth_readout_independent_review_v2_20260913.md`:
  `a7f75c27eeb6ddc4f5bc25f47e93e4405565ac9f619a4d8997699a2760318a03`.
- Ampere v2 JSON `/tmp/astra_birth_readout_independent_review_v2_20260913.json`:
  `2b70eb7fb3cae1554d445599caf13ba0b972631644bf8a12ea785d09a247afcb`.
  Only comparison metadata was inspected, not a second384-output recount.
- Ledger `research_notes/astra_memos/ASTRA_RUNS_2026-09-12.jsonl`, byte-snapshot hash
  `86a465acaf31fc98eab2bde7664134fc8b124144c59e43e279f5957d850f7446`;
  semantic reads restricted to these terminal events (line hashes exclude newline):
  - SEQ119-birth-conditional-seed0-fit-terminal, line190:
    `4751e9e84961f49e705a86358c564e5d158ed0f3853780e3bc65f37552f6c94f`.
  - SEQ120-birth-conditional-seed0-readout-terminal, line192:
    `a67c699137e8af1db26a14f26f0c06d612e26994717d5c7490f367a8556fcdf7`.
  - SEQ121-born-auth-formation-source-shortage, line194:
    `a6d1936154c6498850f24405b04605f1a4c99805492f790f06ad537be54ce65d`.
  The historical ledger's pending raw-review status is superseded by v2 only
  within its stated comparison scope, not silently treated as a new verdict.

## Command checks and limitations

Used `sha256sum`, bounded `sed`/`rg` reads and ordinary `diff -u` against
`/tmp/astra_manuscript_seq121_baseline_20260913/`; no Git command. In-memory
Python standard-library text/JSON checks imported no repository or experiment
code and wrote no files. Results:

- Exact companion TeX/Markdown abstract equality after whitespace normalization
  and TeX underscore decoding; **242 whitespace-delimited words**, within250.
- Canonical main abstract and entire appendix byte-preserved against baseline.
- All previously present tables preserved verbatim:14 canonical TeX tables,
  32 companion TeX tables,36 README Markdown tables,32 claim-map Markdown tables.
- All10 birth-table rows/four numeric columns in README, claim map and companion
  TeX exactly match canonical birth-memo values. Source-only TeX environment
  nesting and unescaped brace balance pass in both TeX files.
- V2 status, ten difference entries and zero unexplained confirmed from metadata.
  An initial checker incorrectly expected compared_after_raw_outputs to be a
  Boolean; inspection showed it is the count384. The corrected metadata check
  passes. This was a checker assumption error, not an artifact discrepancy.
- `command -v pdflatex latexmk tectonic bibtex` checked individually: all unavailable.
  **No TeX build, PDF/layout validation or page-count verification was performed
  or claimed.** Source checks are not compilation. Singer's Git checks are its
  reported work, not mine.

Baseline hashes (same relative paths/order as the six-file table above):

```text
da02ed9ed93f6c404e1f1f4b73765cddb94e71853b902ea89524261517f276a4
83f26fd5073d5a907b71fc7a3f86c79f6e1e29d10f8b0d6a5c56c645024c56cb
5269acba54843613728fd7509f7c89c5bbfeba79f957c5ea48574a4dad9bb805
09b680aac43929057a7ee668eb509a7532e360e5917c56fc4e978a2185602681
af1d573dd04ea530f8a83aa17c3cfa872dce25963ae616ca388b459a4dcfbdb6
630482de130ef661fdcd6f73c22f4a8572baaa63d503ee6cb120620ea57f7b87
```

## Reviewer disclosure

I previously authored downstream birth-conditioned writer bindings and the
learning execution sidecar, reviewed protocol-probe material, and authored the
probe-runtime CPU fixture tests. I did not author these six manuscript updates
or Ampere's birth recount, and did not duplicate the raw birth/formation audits
here. Prior helper involvement, expected-count exposure and Main's supplied
skim flags make this **non-blinded and not wholly independent of the project**.
“Independent” denotes a separate manuscript consistency pass, not independent
experimental replication or original-source/tensor authentication.

No source/helper edits, experiment execution, native/GPU/model/tokenizer calls,
network, Git, external communication or live-probe inspection. This report is
the sole written artifact. Main may apply F1/F2's minimal prose clarifications;
no new C11 process, scientific gate or launch decision is requested.
**EDITSTOP.**

## Fix-verification addendum — F1/F2 closed

**PASS.** Main's wording now explicitly limits AUTH's passing thresholds to
conditional PROSPECT/REVISE, with failed addition/twin criteria preserved. The
token-decoding limitation is explicitly Ampere's lack of independent verification;
official model origin and clean ancestry remain unresolved. Checked the affected
wording across all six files; no expanded evidence or scientific review.

One source-text check confirms exact normalized companion TeX/Markdown abstract
parity and **242 whitespace-delimited words**. No TeX build performed. This
addendum changes no manuscript and preserves the original review verbatim.

| File | Post-fix SHA256 |
| --- | --- |
| `paper_prototype/main.tex` | `74b5f56f4ed759ded14ce3058f5408c4317cba3766e617a9c9374d2dd613c110` |
| `paper_prototype/README.md` | `ae8386822e5d09e4af6071f05c2fad79f81b24040edd012fc5f2706413a108dc` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `a2ae7b55c242787ce2de10d0878fac1a7b811029a9e17f360656486225f60d70` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `b51fe00c66c4c26d94d3493213f1d469014c11812f9a1a1522ba0dafe337cb3c` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `c8ba77c537aab623dac212910c4170401c5b84c6ff955e519086e6337474bd6c` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `84912ab74e980fa5cd51f7bbb7c9722c33c9c0454060d3af89b51d3fad3ae177` |

Original review SHA256 before this append:
`067ab43399520a440ec28118288daac918913d61891986d72ad62924544e339c`.
All original scope/disclosure limitations remain. **EDITSTOP.**
