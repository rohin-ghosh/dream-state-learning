# Q0-FULLDOSE-v2 external terminal custody

**Purpose:** independent read-only hashes recorded immediately after each
controller exits, because the implementation's internal `SEAL.json` excludes
the later `FINALIZED.json` / `FINALIZATION_ABORT.json` eligibility files.
These hashes do not reinterpret the registered result. They bind the complete
root contents observed from the laptop-side watcher before scientific
reduction.

The digest procedure is run inside each terminal root:

```sh
find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
```

The digest therefore covers every regular file's relative pathname and bytes
through the sorted inner `sha256sum` stream. A controller/process absence check
precedes each record.

## R1

- root: `/localhome/local-rohing/astra_diagnostics/q0_fulldose_R1_20260913_attempt1`
- observed terminal and controller absent: `2026-09-13T05:30:34Z`
- complete-root stream SHA-256:
  `006c21d38b763953e5a59ef5641d3fe7683e3e32f71a84bb879c7de667a9db87`
- regular files: `17,567`
- terminal marker was present before hashing; its scientific meaning was not
  inspected while the other registered roots remained live.

## R0

- root: `/localhome/local-rohing/astra_diagnostics/q0_fulldose_R0_20260913_attempt1`
- observed terminal and controller absent: `2026-09-13T05:37:04Z`
- complete-root stream SHA-256:
  `52c21a6e1ba5fa786a652998eacb91b348ab1da685a335e7b90494ca1383097d`
- regular files: `18,153`
- scientific status was not interpreted while R2 remained live.

## R2

- root: `/localhome/local-rohing/astra_diagnostics/q0_fulldose_R2_20260913_attempt1`
- observed terminal and controller absent: `2026-09-13T05:39:23Z`
- complete-root stream SHA-256:
  `350befebaa2a31768b05254c98443435c58d5d8610c6f1515e89218afd2a14dc`
- regular files: `18,153`
- scientific status was not interpreted before this external binding.

All three predeclared roots are now externally bound. This watcher-side
record supplements but does not replace the producer's internal replay and
independent result reduction.
