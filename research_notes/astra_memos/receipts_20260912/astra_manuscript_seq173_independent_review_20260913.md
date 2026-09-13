# C100 / SEQ169–173 independent manuscript review

2026-09-13. **Verdict: engineering-only integration supported; no blocking evidentiary discrepancy or scientific-success inflation found. One low-severity caption correction below.** Scope is only the new C100 edits and preservation of C99 restrictions, not a fresh full-manuscript audit or assay qualification. Collaborator remains **UNSENT**.

## Exact reviewed pins

All six current files match the author handoff AND committed patch `7fdcc127` byte-for-byte. Compared that patch with its parent; no other source changes reviewed.

| File | SHA256 |
| --- | --- |
| `paper_prototype/README.md` | `8fb3c4f7460a2ac6c5972e86a7b854cba9d05711b522e7c8a916e85cb7cdc458` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `7e6411063ddb1a96362f36ddf33eae766f790d5f6509d858e145bc42b94ae08d` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `f39f8264e3226e6e1118db9984221d7b05edf4817eb291dfa7d03e2f434274e8` |
| `paper_prototype/main.tex` | `d61d5954d18d4af7e78c9ca7b35e7d3c5f38bd5004bf7eeb8ebc5f8554e3d154` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `f0c2bdbf3076d60259a3d4a07eef12b1e77970af00ef418f91ac63665972cc23` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `8eb38e0db065946d5e19017f43e63ce09ba4a9f5abd6de87816f6887afba467f` |

Binding handoff `/tmp/astra_manuscript_seq173_handoff_20260913.md`: SHA256 `6f6aa1e5a140b140820cd01a75b0179efa20c8286e5d7f45f1235ffd5ed0030b`.

## Raw archive trace

Read the five bound local tar archives in memory, without extraction or importing experiment/scorer code. Independently recomputed all five archive and report-file hashes; they match C100/handoff. Recomputed canonical report-body seals and matched the five stored seals. Counts were cross-checked against individual slot attempts/admissions, not just copied from report summaries.

| SEQ | Archive SHA256 | Calls/20; EVENT/8; LINK/4 | Uncalled slots |
| --- | --- | --- | --- |
| 169 | `acdd9c2cf6ec4b5a3bbd28a6c7d1a58159442a89e74461112c42e37b73c9694c` | 2; 0; 0 | 18 |
| 170 | `8d1e220e7918377a4f189a033fd7f02b27a7d51749cb87292ed1d6946c0f1424` | 2; 0; 0 | 18 |
| 171 | `bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869` | 17; 8; 0 | 3 |
| 172 | `dbe951af5823959c1172f70ab5e7163aecf54b89d55ad291a883cce819120cf4` | 19; 8; 2 | 1 |
| 173 | `8c2215eefef9f0f6ad546164688dd1b128e36191642bda603c77b133f56a1079` | 19; 8; 2 | 1 |

- Every report retains FORMATION_FAILED, zero fits/updates, null writer payload and false native-custody/full-contract flags. No fit/readout directories occur in these archives. All configs retain seed0, root `disposable/0`, and stored planner `plan_sha256=2bccd6b24a15496d1d1cf70c29c1a3849d0e3269f4a4118e225c751ec79f2d7b`. This stored plan identifier is not the hash of the entire serialized planner dictionary.
- SEQ169/170 terminal raw EVENT strings are identical, lack LF, and hash to `5a4eaded0470de4324c6248692c2c09c785592fdd75bc5e313ecc8c3f2c95472`. The archived SEQ170 request adds explicit LF disclosure; the strict rejection remains unchanged.
- SEQ171 terminal raw LINK selects `E_B46SKGEBDB` then `E_NVKV6RDQ27`, whereas the first planned pair is `E_BRFFHBSD7R` then `E_QL4Q3BQTIY`. The admitted EVENT fields support its stated shared node and receipt pairing. The SEQ171 Builder entry at 14:42 UTC explicitly records an independent semantic check, without admission to the failed original bank. This review did not rerun that judge or retroactively score/admit the LINK.
- SEQ172/173 terminal raw LINK strings are identical, SHA256 `9c39be42cb233bed4fe1ad2ad7564d8c85eb3feb58a79b2be8382d45c7dafd78`. The requested pair matches the response; VIA is `N_CL7WGIYEOT`, the first EVENT's source, not the shared `N_RLE2UQCILI`. The latter is both the first EVENT's destination and second EVENT's source in the admitted rows. Both reports reject the third LINK.
- Selected terminal captures all record `finish_reason=stop`. Archived sampling confirms the exact target-blind regex `[^\r\n]+\n` for scaffolded EVENT/LINK outputs. Configs and terminal request/sampling captures confirm external format assistance from SEQ171, public prescribed pairs from SEQ172, and generic VIA/EVIDENCE explanation in SEQ173. These are adaptive interface changes, not five independent learners or learned formatting.

## Preserved boundaries

The only removed lines in each six-file patch are the two common draft-cut/status lines advanced from SEQ167 to SEQ173. C99's existing content is retained, including failed once-only finalization, engineering-only exclusion, all eight failed positive interval checks, required-panel counts, READ-response rather than READ-line units, two sampled ACTIVE prompts lacking the allowed dialect, 30-case sample limits, RA/RB token asymmetry and no learning/full-assay qualification. C100 does not rescue those results.

Both TeX abstract environments compare byte-identically with the patch parent. The companion abstract file changes only its opening status/pointer, leaving its actual abstract unchanged; no C100 numbers enter an abstract. New C100 tables preserve planned denominators and accepted EVENT/LINK counts, disclose external scaffold/public-pair assistance, and retain all five failures. EVENT-prefix import and READ/THINK remain implementation/prospective work at the SEQ173 cut, not native acquisition/readout success. No parenting, H1/H2, general G3, clean-lineage, mission or freeze qualification is introduced. UNSENT is explicit.

## Smallest correction — low severity, caption wording only

`paper_prototype/main.tex:2015` and `paper_prototype/astra_sprint_draft_20260912.tex:4254` say “Counts are strictly accepted raw records within planned slots.” That is accurate for EVENT/LINK columns but not Calls: Calls includes EXPLORE and the rejected terminal generation (e.g. SEQ169 has two calls and zero accepted records).

Replace that sentence only with: **“Calls count attempted model generations; EVENT and LINK counts are strictly accepted raw records within planned slots, not learned capability.”** Numeric tables and substantive interpretation require no correction. No manuscript edit performed here; a correction would require fresh author file hashes, not reuse of this exact-byte review as if the files were unchanged.

Local byte/metadata consistency is not native execution replay, hardware authenticity, a causal scaffold-benefit estimate or formal scientific qualification. No tests, builds, native/model/tokenizer calls, GPU, network, remote operations, commits, or later outcome inspection were performed. Only this review artifact was written. **EDITSTOP.**
