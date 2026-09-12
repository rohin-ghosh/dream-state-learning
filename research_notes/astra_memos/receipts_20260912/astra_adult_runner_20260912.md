# Separate bounded adult runner — September 12, 2026

Owned files: `organism_v6/run_adult_v1.py`, `tests/test_run_adult_v1.py`.
No existing source edits; no GPU/network/Git activity or actual life launches.

## Frozen for main's review — September 12, 2026

Runner and test source are frozen; this follow-up changes only this handoff.
Focused CPU tests rerun against the current shared checkout: **12 runner tests
passed**, **37 adult-control tests passed**, **49 total in these two suites**.
Main separately reports actual clean selection integration committed as
`116b49a3` with **388 tests passing**. That broader count and commit association
are main's report, not a 388-test rerun performed by this agent.

Frozen SHA256 values (unchanged before/after the focused rerun):

```text
653ddd1be60dfd050e2bd4233ef03f7776460d000d31be53bde2d3e28e989d04  organism_v6/run_adult_v1.py
04e071072ef7cb3318834cde27da34b125c29d6b11ea070ade0334d9958c9b54  tests/test_run_adult_v1.py
```

## Implemented vertical slice

`run_adult(AdultRunSpec(...), gym=..., backend_factory=..., trainer=...)` runs
a finite fresh parent-free life. Only the backend context-manager and trainer
execution boundaries are injectable. Admission, label-evidence verification,
canary execution and running/shadow decisions use the real existing helpers.
There is no injected acceptance boolean, fabricated trainer receipt, or new
lineage manifest. Source hashes do not authenticate base origin.

Caller supplies the actual `lineage_root/birth/model` runtime path, official
model ID, exact expected runtime file hashes, trusted initial child manifest
pin, initial adapter and corpus. Those external pins must be authenticated
independently; the runner never selects its own supposedly official pins.
The existing adult startup contract and base-inventory verifier fail closed.

Fresh `ledger.jsonl` contains only adult activity. Bootstrap is precisely
`gym.birth_prompt()`; no parent endpoint, lessons, childhood notes/briefs,
reflection, retrieval, cloning or scoring feedback to a parent. The existing
post-outcome NOTE_AFTER instrumentation produces child-authored records.
Occurrence reservation starts above the pinned childhood maximum, without
copying or inventing childhood events in the adult ledger. This small slot
subclass is needed because the existing slot has no initial occurrence offset;
it otherwise inherits the unchanged source-bound generation and admission path.

The real nursery gate runs under `admission_runs/sleep_N/` on cumulative adult
rows, with its unchanged 64-item minimum and child-only recipe. Below that
minimum, training is skipped, evidence retained, and the selected adapter is
unchanged. Initial items do not waive the minimum for new adult admissions.

`sleep_N/training_source_audit.jsonl` is **audit-only**, never context/retrieval:
it concatenates the pinned initial source snapshot and the new adult snapshot.
The replay assembler validates both existing receipts using `_admissions`,
rebases their physical-line indices (hashes and row bytes unchanged), retains
the entire initial child corpus, and includes cumulative admitted adult items.
It revalidates the resulting source-bound union. It does not judge new items,
invent eligible rows, relabel generic corpus items or copy parent text into
training targets. Identity collisions/duplicate replay items fail closed.
Historical parent text, if present in the pinned initial provenance snapshot,
remains audit-only. No parent is instantiated or consulted.

Both modes use rank 8, three epochs, identical caller-selected learning rate
(default 1e-4), explicit training seed, frozen-base replay and the same existing
child-body-only writer. Warm-start training from the selected adapter is not
used: the existing nursery trainer rebuilds from pinned base plus cumulative
replay. The runner checks actual row-linked trainer evidence, metadata,
adapter files, supervision masks and all input hashes; aggregate metadata alone
is insufficient. Training stages must produce their own DONE, which the real
staging helper converts to CANDIDATE, never a waking DONE.

**Replay-from-base is not sequential parameter retention.** Running mode
retains the selected adapter for subsequent waking, but each training call
starts again from the pinned base and replays admitted child targets. This
tests that implemented mechanism, not continued optimizer/parameter learning
from the previous selected adapter.

Before the actual three-round canary, the runner persists the exact
`adult_controls.candidate_key`. The existing SelectionRecorder captures
prompts/outputs/seeds and verifies the actual parseable-ACT verdict. A boundary
check rejects short generation batches rather than accepting a reduced
denominator. The original key must still match after evaluation. Only accepted
running decisions create a separate promoted adapter; shadow trains/evaluates
but never changes waking weights. All waking loads and the final reload use
`adult_controls.select_adapter`, not candidate/DONE scans. No evaluation rows
enter the adult training ledger. Raw candidates stay CANDIDATE.

## Unsupported / not claimed

- **Compiler or task-exposed deployment:** current nursery admission and trainer
  receipts require UNEXPOSED ancestry/influences and reasoning source records.
  This runner supports only strict ReasoningGymGym training-family adult work
  preserving that boundary; it rejects other gyms before loading a backend.
  Supporting exposed deployment needs a separately authorized compatible
  receipt/admission API; no relabelling or new clean ancestry is manufactured.
- Resume/cache repair and concurrent execution into one life: unsupported;
  existing/partial output is preserved and rejected. Use a new empty life.
- Admission and trainer/custody helpers include private existing APIs. Changes
  to their contracts fail closed; do not relax them to force compatibility.
- No task-score gate, strategy/H2 inference, manuscript claim, or neutral ON/OFF
  comparison. The only selection gate here is the nursery's actual format
  canary. Genuine ON/OFF neutral probes remain separate later integration.
- **Training-family adult execution is not unseen-task H2 evidence.** CPU
  success establishes software contracts, not learned transfer or scientific
  performance. No unseen-task evaluation or H2 acceptance criterion is wired.
- GPU execution, memory release between in-process training and vLLM loading,
  installed dependency compatibility and actual official model origin have
  **not** been validated by CPU fixtures. The local backend close helper is
  reused; shared-node GPU launch/lease rules still apply outside this task.

## Commands / integration

CPU tests (synthetic model/trainer boundaries, real helper verification):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_run_adult_v1.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_adult_controls.py -q
```

API: create `AdultRunSpec` with all required path/pin fields, `mode` running or
shadow, explicit training `episode_ids`, `seed`, `train_seed`, `sleep_every`,
`budget_ticks`, `wake_batch`; optional `note_after_max_tokens=100`,
`min_items=64`, `base_lr=1e-4`. Both modes must receive the same schedule and
budgets for comparison. The supplied backend factory is a context manager;
the supplied trainer consumes the immutable `TrainingRequest`.

Future local execution command, **not executed in this task**:

```sh
python3 -m organism_v6.run_adult_v1 --config /absolute/pinned-adult-spec.json --execute
```

The config JSON must match AdultRunSpec exactly (unknown parent/lesson options
are rejected). CLI execution is explicit, sets offline model-loading flags,
and calls the existing trainer itself rather than constructing receipts.
No default paths/pins or implicit launch are provided.

### Exact CLI/config recipe for main (documented only; not executed)

Run from the repository root with a Python environment containing the actual
local inference/training dependencies. The CLI has only `--config PATH` and
`--execute` (plus `--help`); mode, seeds, cadence and provenance belong in JSON,
not additional CLI flags. `--execute` starts real execution; it is not a dry run.
No remote command or launch is performed as part of this handoff.

Main must first supply these shell variables from independently verified
provenance and the selected local run plan:

| Variable | Required value |
| --- | --- |
| `ADULT_LINEAGE_ROOT` | Absolute, canonical, nonsymlink initial lineage bundle directory. |
| `ADULT_INITIAL_MANIFEST_REL` | Recorded child sleep path relative to that bundle, e.g. the selected `sleep_NNNN/manifest.json`. |
| `ADULT_INITIAL_MANIFEST_SHA256` | Independently trusted SHA256 of that exact initial manifest. |
| `ADULT_MODEL_FILES_JSON` | Absolute path to JSON object mapping **every runtime model filename** to its externally verified official-file SHA256; no wrapper object. |
| `ADULT_EPISODE_IDS_JSON` | Absolute path to JSON array of unique caller-selected reasoning **training** IDs; not gate/canary/exam IDs. |
| `ADULT_RUNNING_LIFE`, `ADULT_SHADOW_LIFE` | Different absolute, canonical, nonsymlink fresh life directories with existing parents. |
| `ADULT_RUNNING_SPEC`, `ADULT_SHADOW_SPEC` | Different new absolute JSON output paths, outside both life directories, with existing parents. |

Do not manufacture the expected manifest/model pins by hashing arbitrary local
files and treating those newly calculated values as authentication. The model
inventory must match the actual `ADULT_LINEAGE_ROOT/birth/model` files exactly,
and the initial snapshot must include its bound corpus, ledger, admission,
trainer and selection evidence. The recipe below chooses the pinned snapshot
adapter/corpus themselves rather than unverified alternate copies.

After supplying those values, this shell recipe creates two complete specs
without inventing provenance. The numeric schedule below is an explicit example
(128 caller-selected IDs, 64 episodes per sleep, one tick, wake batches of 8,
100-token post-outcome cap, rank 8/three epochs fixed in code). Main must use the
same externally chosen IDs and budgets across both modes. At least 64 distinct
admissible adult records are needed before a candidate is trained; these
settings do not guarantee that the child produces them.

```sh
set -eu
: "${ADULT_LINEAGE_ROOT:?supply verified lineage bundle}"
: "${ADULT_INITIAL_MANIFEST_REL:?supply selected child manifest path}"
: "${ADULT_INITIAL_MANIFEST_SHA256:?supply externally trusted manifest pin}"
: "${ADULT_MODEL_FILES_JSON:?supply externally verified runtime file pins}"
: "${ADULT_EPISODE_IDS_JSON:?supply selected training episode array}"
: "${ADULT_RUNNING_LIFE:?supply fresh running life path}"
: "${ADULT_SHADOW_LIFE:?supply fresh shadow life path}"
: "${ADULT_RUNNING_SPEC:?supply new running config path}"
: "${ADULT_SHADOW_SPEC:?supply new shadow config path}"

test "$ADULT_RUNNING_LIFE" != "$ADULT_SHADOW_LIFE"
test "$ADULT_RUNNING_SPEC" != "$ADULT_SHADOW_SPEC"
initial_checkpoint=$(dirname -- "$ADULT_INITIAL_MANIFEST_REL")
umask 077
set -C
jq -n \
  --arg life_dir "$ADULT_RUNNING_LIFE" \
  --arg lineage_root "$ADULT_LINEAGE_ROOT" \
  --arg manifest_path "$ADULT_INITIAL_MANIFEST_REL" \
  --arg manifest_pin "$ADULT_INITIAL_MANIFEST_SHA256" \
  --arg initial_adapter "$ADULT_LINEAGE_ROOT/$initial_checkpoint/adapter" \
  --arg initial_corpus "$ADULT_LINEAGE_ROOT/$initial_checkpoint/corpus.json" \
  --arg model_dir "$ADULT_LINEAGE_ROOT/birth/model" \
  --slurpfile model_files "$ADULT_MODEL_FILES_JSON" \
  --slurpfile episodes "$ADULT_EPISODE_IDS_JSON" '
  if ($model_files | length) != 1 or ($episodes | length) != 1
     or ($model_files[0] | type) != "object"
     or ($episodes[0] | type) != "array"
     or ($episodes[0] | length) != 128
  then error("expected one model-file pin object and one 128-ID array")
  else {
    life_dir: $life_dir,
    mode: "running",
    lineage_root: $lineage_root,
    manifest_path: $manifest_path,
    expected_manifest_sha256: $manifest_pin,
    initial_adapter_dir: $initial_adapter,
    initial_corpus_path: $initial_corpus,
    model_dir: $model_dir,
    expected_model_id: "Qwen/Qwen2.5-7B-Instruct",
    expected_model_files: $model_files[0],
    episode_ids: $episodes[0],
    seed: 9,
    train_seed: 23,
    sleep_every: 64,
    budget_ticks: 1,
    wake_batch: 8,
    note_after_max_tokens: 100,
    min_items: 64,
    base_lr: 0.0001
  } end' > "$ADULT_RUNNING_SPEC"

jq --arg life_dir "$ADULT_SHADOW_LIFE" \
  '.mode = "shadow" | .life_dir = $life_dir' \
  "$ADULT_RUNNING_SPEC" > "$ADULT_SHADOW_SPEC"
```

Future local commands for main, subject to its independent review, environment
checks and GPU/lease rules; **do not run as part of this review**:

```sh
python3 -m organism_v6.run_adult_v1 --config "$ADULT_RUNNING_SPEC" --execute
python3 -m organism_v6.run_adult_v1 --config "$ADULT_SHADOW_SPEC" --execute
```

These are different local processes/lives, but **not** adapter ON/OFF neutral
probes. Both start waking from the pinned initial adapter; shadow never changes
that selection. This configuration does not enable compiler deployment,
sequential warm-start training, held-out H2 measurement, or remote execution.
