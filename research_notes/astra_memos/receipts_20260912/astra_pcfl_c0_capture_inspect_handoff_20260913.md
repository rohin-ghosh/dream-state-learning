# MainAPI — C0 capture inspector ownership / early notice

2026-09-13: implementing only NEW `gpu/astra_pcfl_c0_capture_inspect.py` and
`tests/test_astra_pcfl_c0_capture_inspect.py`; no commits or other repository edits.
Non-material, separately labeled unfinalized capture inspection only. Frozen
analyzer and its finalization/collection requirements stay untouched. No native
or archive outcomes read; no GPU/model/network/remote operations. Main retains
archive collection and current hardware/release observations. This session has
no callable MainAPI messaging tool; this handoff is the available early notice.

## Pre-outcome implementation/test freeze — 2026-09-13 13:51:13 UTC

Complete: **194-line inspector**, 27 new synthetic CPU tests, 26 existing
frozen-analyzer/replay tests passing. No native or archive outcome inspection
has occurred in this session. No GPU, model, tokenizer loading, network,
remote, finalization, collection, or hardware-release operation was performed.
No commits. Only the two assigned new repository files and this requested
handoff were written; concurrent changes by others were preserved.

Exact frozen SHA-256 bytes:

```text
e4b72705de80f742b7e55ddf9f06834ac4fefa86d73c5bb01edc11bcba5504e8  gpu/astra_pcfl_c0_capture_inspect.py
0cca10b5986853062b4de99b807f51917cf1b93552e41a47960d153975c055ad  tests/test_astra_pcfl_c0_capture_inspect.py
a84f677e1b41512c0eabfd3865eafb55ec85584e53e99796175334e1bf1db00e  gpu/astra_pcfl_zero_fit_analyze.py
```

The frozen analyzer is untouched (`git diff --exit-code` clean for that file).
Its collection/finalization requirement is not bypassed: a synthetic
unfinalized archive still fails its entry point. The inspector never calls
`analyze`, substitutes its lineage, or synthesizes finalization evidence.

## Main's post-freeze offline use (NOT executed here)

Supply independently recorded **FILE** hashes, not manifest object seals or
hashes newly trusted solely from a collected archive. Use absolute unaliased
paths to relocated diagnostic and outer evidence, and a fresh output directory
outside both archives with an existing unaliased parent.

```bash
python3 -B gpu/astra_pcfl_c0_capture_inspect.py \
  --diagnostic /ABSOLUTE/RELOCATED/diagnostic \
  --outer /ABSOLUTE/RELOCATED/outer \
  --manifest-sha256 INDEPENDENT_MANIFEST_FILE_SHA256 \
  --capture-sha256 INDEPENDENT_ORIGINAL_CAPTURE_FILE_SHA256 \
  --output /ABSOLUTE/FRESH/inspection
```

Writes only `inspection.json` and `inspection.md`, only after validation.
Always labeled `UNFINALIZED_CAPTURE_REPLAY_MATCH`, `diagnostic_usable=false`,
`finalization_failed=true`, `full_v22_release=false`; no H1/H2, learning, C11,
ancestry, full-assay, or causal claim. Failure/negative scores are not repaired.

## Boundaries and checks

- Exact captured diagnostic inventory and captured outer-file hashes;
  manifest/report seals, report byte pin, context/worker bindings, zero worker
  exit, owned-group release, capture GPU observation and visibility limitations.
- Only the original single finalizer's observed unreadable-PID CVD failure,
  at either first or post-GPU CVD scan; exact failure type/message and prior
  successful observations must agree. No hard-coded real PID or fabricated
  current-PID observation. Reject missing failure, extra/unbound files, retries,
  collection/final/release artifacts, stale bytes, symlinks, duplicates and
  inconsistent clocks. Preserve original failure bytes and output inventory pins.
- `Replay` and frozen raw scorers recompute ordered tasks, compare task files
  and report, rebuild the pinned 800-task plan, compare source pins and
  measurements, and retain fixed panel denominators. Counts include all/root/
  panel/projection/render strata, syntax/READ errors, truncations, token counts,
  and recorded elapsed costs (not GPU-active time).
- Does not prove current reservation release. Main owns archive authenticity
  and hardware/current-release observations. The capture format does not store
  its original outer-directory path, so outer relocation is caller-supplied;
  diagnostic relocation is checked. No live paths from context are followed.
- CPU fixtures intentionally cover **partial paths**, raw replay/score tamper
  guards and fixed-denominator rejection; they do not pretend to certify an
  800-row native run. The tiny counter-math test explicitly substitutes panels;
  the production entry point has no such substitution or test mode.

Validation completed without dependencies/installations or bytecode/cache writes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_astra_pcfl_c0_capture_inspect.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_astra_pcfl_zero_fit_analyze.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/astra_pcfl_c0_capture_inspect.py --help
git diff --check
```

Results: **27 + 26 = 53 tests passed**, CLI help passed, whitespace check clean.
`python` is absent and system `python3` has no pytest; stdlib unittest was used.
MainAPI direct notification remains unavailable in this session; this handoff
contains the early notice and final frozen interface for Main.
