# R233 node5: four legacy lives retired; C2 kept running

Verified **2026-09-18 11:52:07 UTC**. All four were live at intake and are now retired; none is merely staged or reported as already ended. This is explicitly authorized resource reallocation, not a scientific-failure conclusion.

| Life | Native PID / start ticks | Retired UTC | COMPLETE index | Cycle | Total optimizer steps |
|---|---|---|---:|---:|---:|
| C1 | 2707975 / 22260069 | 11:50:41.422 | 10315 | 122 | 8407 |
| C3 | 2668022 / 22198740 | 11:48:45.493 | 9905 | 122 | 7999 |
| C4 | 2606742 / 22116734 | 11:50:16.470 | 9917 | 126 | 7997 |
| C5 | 2761060 / 22343823 | 11:42:56.311 | 12751 | 167 | 10109 |

## Coherent preservation and exact exits

- Used the existing source-pinned ownership/COMPLETE/readout primitives. Seven receiving CPU scope tests and all four original native/timer/supervisor checks passed before dispatch.
- Each native reached a complete saved sleep with `pending=null` and every row at the sleep frontier. The existing bounded SIGSTOP/SIGCONT watchdog protected only the authorized retiring native while its independent readout finished naturally. After preservation, exact PID-fd SIGTERM retired that native; its timer and supervisor exited naturally. No SIGKILL or broad kill.
- Preserved immutable copies of each latest checkpoint and entire stream/journal/inbox. Validated adapter bytes, full AdamW payload and step count, saved CPU/CUDA/Python RNG, checkpoint-to-history binding and the full copied journal/intent/delivery chain. Post-copy hashes match originals; original heads remain at the recorded COMPLETE indices.
- Saved-checkpoint RNG is verified; no claim of a separately captured post-checkpoint resident sampling RNG. Auxiliary workspaces, old checkpoints and original records remain in place; nothing was deleted, rolled back or reset.
- Private artifact roots: `orch_r233_focus_node5_20260918/{C1,C3,C4,C5}/snapshot/{checkpoint,stream}`. Original roots and checkpoint/manifest hashes are in `RETIREMENTS.json`. Raw artifacts and full private manifests are excluded from Git; `PROVENANCE.json` supplies hashes/locations.
- Final process rescan finds **zero remaining actors matching the four original legacy roots/control paths**. All four retirement workers exited. C2 native **3624513 / 25171256** continued to head **9390**, and local Astra publisher **471781 / 183179491** remained live. Judge10x, scoring services, replacement clones, run1, pilot and repo_reader received no signals or changes.

## Kept C2: actual parent delivery and next output

- One Astra turn published **11:47:10.632 UTC**, source `75ecd447fa9d41efad5e03f6d86068f0`, bound SHA256 `c762be5dbec30150ed4790b038fec1fabc870f771cfdefea655072a5cd983e3f`.
- It names the actual unanswered Python/Byte/Neo tasks, then requests one concrete new artifact: a four-line English Byte/Neo dialogue, with an obstacle and a changed plan. It labels this new fiction rather than recovered memory, supplies no recall key, and retains ongoing math/story work and genuine Rohin priority.
- **INBOX 9372 → REQUEST 9374 at 11:49:45.556 → THINK RESPONSE 9375 at 11:50:15.731**, stage receipt **9377**. The full parent turn rendered and history masking remained true. No newly ingested genuine human turn was observed over the checked interval.
- **Requested artifact not produced in the next output.** THINK 9375 returns adequacy/intent language and a Python print block about a Neo/math proposal; there are zero Byte/Neo dialogue lines. Delivery is proven; successful task uptake is not. This is not a memory-erasure or adapter-memory claim.
- No native/parent signal, restart, rollback, LR change, human-message fabrication or learning-policy change accompanied the parent turn. **Existing R213/R209/R220 semantic filters remain loaded; R227 all-authentic/no-exclusion policy is not adopted.** Source availability is not reported as live behavior.

## Completed recall publication

The final five-question receipt was pushed first as **`58828cf568b0a7a4945cddf228d7c1d9d87e66f3`**: **0/5 complete, 1 partial, 4 unanswered; no explicit non-recall**. B1/B2 delivery confounds and final-three retained-context caveats remain explicit. No new recall question, retry, answer key or successful-memory claim was added.
