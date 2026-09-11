## Verdict

**Do not execute this as written.** It is a scientific priority list, not a schedulable GPU plan. The biggest problems are oversized reservations for short jobs, an uncosted struggle-test implementation, treating a proposed retrieval system as an available fallback, and no admission rule tied to node 1’s death.

**Evidence boundary:** No lettered attachments, notebook file, repository, or live process list were supplied. I cite the draft’s sections and its reported SEQ mappings; those mappings are **not independently verified**. The hardware and runtime measurements below come from your request, **without supplied SEQ attribution**. Calculations are explicitly derived from those measurements. I cannot establish that a particular function is absent from the repository; I can identify functionality the plan depends on but does not establish exists.

## Runtime arithmetic to use

For every job:

> **GPU-hours = elapsed hours × GPUs actually allocated to that job.**

Do not multiply by the whole node unless the job actually reserves the whole node. Conversely, do not quote single-GPU costs for a job that occupies every GPU.

The following costs assume **one allocated GPU per job**, which must be verified:

| Work | Measured or derived cost |
|---|---|
| Probe panel | **10–25 minutes per panel**; **0.17–0.42 GPU-hours per panel**, derived |
| Rank-8 car-test fit | **2.5–4.5 minutes per fit**; **0.042–0.075 GPU-hours per fit**, derived |
| Reported larger car-test fit | Approximately **10 minutes per fit at 250,000 tokens**; approximately **0.17 GPU-hours per fit**, derived |
| v3 processing **250,000 token presentations** | At **390–1,640 tokens/second**, **2.5–10.7 minutes**, derived; excludes unmeasured loading, evaluation, and saving overhead |

The training numerator must be **tokens actually processed across all epochs and packed windows**, not corpus-piece count or only supervised answer tokens. Do not extrapolate rank-8 fit timings directly to the proposed rank-32 memory write.

---

## Audit: quote / problem / fix / severity

### 1. Replication reservation is not a runtime estimate

**Quote:** “Finish the already-running different-life write replications — **96 GPU-hours**.”

**Problem:** The listed evaluation consists of frozen, A, A_v3, B, and brief on both panels. That is **10 panels per replicated life**. Across the pending `seed7` and `seed8` replications, a completely unfinished evaluation would require **20 panels**, or **200–500 minutes of aggregate probe execution**.

At one GPU per probe, that is **3.3–8.3 GPU-hours**, excluding fitting and overhead—not **96 GPU-hours**. If a probe genuinely occupies all **8 GPUs**, the same workload costs **26.7–66.7 GPU-hours**. GPU occupancy is therefore a blocking measurement. [Draft, “Replication requirements” and “GPU plan”; reported SEQ-034–035.]

**Fix:** Separate **remaining life generation**, **remaining fits**, and **remaining panels**. Harvest completed artifacts first. Replace the reservation with the unfinished-job manifest and actual GPU count per executable.

**Severity: High.** A large reservation can strand GPUs while a small serial evaluator runs.

### 2. F ceilings are unsupported and likely inflated for fitting alone

**Quote:** “Corrected exposure-matched F comparison — **16 GPU-hours**”; “high-exposure F condition … — **8 GPU-hours**.”

**Problem:** Together these reserve **24 GPU-hours**, but the supplied fit measurements are measured in minutes. The draft never provides remaining fit count, processed tokens, scorer cost, or allocated GPU count. These are ceilings, so they are not mathematically false; they are **not justified runtime estimates**.

Rank, repetitions, and additional scoring could increase cost. Their actual contribution is unverified. [Draft, “F run-manifest check” and “GPU plan”; execution status attributed to SEQ-035, specification to an unavailable unnumbered note.]

**Fix:** Calculate each unfinished fit from processed token presentations, then time the completion scorer separately. Run queued F work immediately after the manifest/scorer check; release each GPU on completion. Do not reserve the F ceiling as a dedicated lane.

**Severity: High.**

### 3. Crossed A cells have a loose budget and an unverified implementation

**Quote:** “**4 GPU-hours per cell**, including evaluation.”

**Problem:** The matched panel evaluations account for only **20–50 minutes per cell**, or **0.33–0.83 GPU-hours per cell** at one GPU per probe. Training cost cannot be recovered from the reported **856 corpus pieces**: packed token counts are missing.

More importantly, A uses the production trainer and A_v3 uses the v3 trainer. The draft has not established that whole-text versus target-only supervision can be switched **within the same trainer**. Otherwise the proposed crossing still confounds trainer implementation with supervision. [Draft, “Corrected comparison” and “Conditional causal check”; reported SEQ-031.]

**Fix:** Verify an executable loss-mask switch with identical packing, optimizer, schedule, and checkpoint handling. Then budget `processed tokens / measured throughput + panel time + measured overhead`. If that switch requires new code, label the experiment an implementation task before promising a causal result.

**Severity: High.**

### 4. The struggle ceiling does not buy an arbitrary acquisition run

**Quote:** “**144 GPU-hour ceiling** for collection, writes, controls, and evaluation combined.”

**Problem:** A life takes **30 hours**. If it reserves a complete **8-GPU node**, acquisition alone costs **240 GPU-hours**, already above the ceiling. If it occupies one GPU, acquisition costs **30 GPU-hours**, but still consumes **30 hours** of the requested **48-hour window**.

The draft explicitly says no qualifying struggle family is verified. Collection therefore cannot be treated as a small, known prefix to evaluation. [Draft, “Struggle test—Select and freeze,” “Compute and stopping rule”; motivation attributed to SEQ-034.]

**Fix:** Make this a **record-first diagnostic**. Before GPU collection, identify a qualifying child-authored correction and establish that the existing runner can collect the necessary instances without a full life. Otherwise mark the struggle test blocked; do not quietly launch a life inside this allowance.

**Severity: Critical.**

### 5. Block attribution depends on an unverified adapter execution path

**Quote:** “Behaviour only; memory only; combined”; “Keep … rank-8 behaviour block and rank-32 memory block.”

**Problem:** A design ruling does not establish working code for:

- constructing and training the separate blocks;
- routing the appropriate corpus and gradients to each block;
- loading both blocks together without overwriting one;
- independently disabling either block;
- preserving those semantics across save/load;
- substituting scrambled memory while keeping behaviour fixed.

The draft itself says module allocation is unverified. A standard single-adapter trainer does not establish this capability. [Draft, “Sleep write” and “Paired evaluation”; reported SEQ-033–035.]

**Fix:** Treat the **dual-block trainer/loader/toggle path** as a build dependency until demonstrated. Require a save/load smoke test and independent block activation check before launching the attribution matrix. Meanwhile, run already-supported single-adapter comparisons.

**Severity: Critical.**

### 6. Retrieved-text fallback is a new system, not the measured brief baseline

**Quote:** “Persistent retrieved text”; “contradiction/supersession links”; “Atomic deployment.”

**Problem:** The supplied evidence establishes a **same-sleep brief baseline**, not a provenance-aware retrieval service. The fallback assumes an index, retrieval policy, gym integration, context-budget handling, versioned text/adapter snapshots, and rollback plumbing. None is evidenced as implemented.

Likewise, an existing collapse gate does not establish atomic rollback of a newly introduced text store. [Draft, “Fallback architecture”; brief evidence attributed to SEQ-034–035.]

**Fix:** Use the **existing brief-in-context path** as the deadline fallback, after confirming that it runs. Keep the full retrieved-text system out of the critical path. Do not describe brief conditioning as evaluated retrieval infrastructure.

**Severity: Critical.**

### 7. “Run the struggle test in parallel” hides substantial CPU-side work

**Quote:** “Launch the struggle diagnostic and implement retrieved-text fallback.”

**Problem:** The struggle specification needs a provenance audit, task-family selector, acquisition gate, controlled sampling, held-out instance manifests, trigger-action labels, canonical-span extraction, scrambled-binding generation, and paired scoring. Existing panel probes do not establish these capabilities.

Allocating GPUs to this lane while someone builds the harness leaves them idle. [Draft, “Struggle test—one-page execution specification”; proposed work motivated by SEQ-034.]

**Fix:** Put these on a **CPU/developer readiness checklist**, not a GPU reservation. Admit struggle jobs only when the data manifest and runnable evaluation command exist. Stop expansion if the existing records do not support the test.

**Severity: High.**

### 8. Node 1’s export deadline is not a scheduling policy

**Quote:** “Export node 1 before **2026-09-14 at 23:00 UTC**.”

**Problem:** Exporting only at closure risks losing running state, local-only artifacts, and the ability to finish matched evaluations. With a **30-hour life**, the latest mathematical start that finishes before death is **2026-09-13 at 17:00 UTC**, with **no allowance** for saving, export, or failure.

A job that finishes just before death is also useless for a result requiring further same-node controls. [Draft, “Closing work”; deadline and life runtime supplied by user. Node dependence attributed to SEQ-032 correction and SEQ-033.]

**Fix:** Replicate artifacts off node 1 **now and after every completed job**. Admit work only if its conservative runtime **plus measured export time** fits before death. Finish each candidate’s same-node controls there, or rerun the candidate and controls together on the surviving node.

**Severity: Critical.**

### 9. Global canaries and audits can unnecessarily serialize the fleet

**Quote:** “Blocking prerequisite”; “First: harvest … audit … run interface canaries, and select the struggle family.”

**Problem:** Only some dependencies are global. An F scoring audit need not block A replication; selecting a struggle family need not block either. A failed combined-adapter canary should not stop established frozen or brief evaluations.

The **8 GPU-hour canary ceiling** also does not specify a runnable workload. Export, manifest checks, and much of the scoring audit are CPU/I/O work. [Draft, “Execution order” and “GPU plan”; interface failure attributed to SEQ-033.]

**Fix:** Use **per-candidate gates**: validate that candidate, run its interface check, then enqueue its panels. Let unrelated ready jobs proceed. Perform exports and audits concurrently, subject to I/O contention.

**Severity: High.**

### 10. The closure lane duplicates work and obscures unused capacity

**Quote:** “Protected closure lane — **48 GPU-hours**.”

**Problem:** Same-node controls are already included in replication and struggle requirements. The draft does not identify which closure evaluations are additional. Paper writing, manifest inspection, and artifact checks should not reserve GPU capacity by default.

The listed ceilings sum to **328 GPU-hours**, including the crossed A cells and counting the struggle ceiling only once. With both **8-GPU nodes** available throughout **48 hours**, gross capacity would be **768 GPU-hours**, leaving **440 GPU-hours** outside the listed ceilings before subtracting current jobs. Node 1’s death reduces that capacity, but the window’s starting timestamp is missing.

Unused capacity is not itself a scientific failure. **Unacknowledged idle reservations are a scheduling failure.**

**Fix:** Give every pending job a unique identity and charge it once. Keep a small ready-job queue rather than exclusive oversized lanes. Publish intentional spare capacity separately from blocked capacity.

**Severity: Medium.**

---

## Replacement 48-hour operating plan

These are **proposed checkpoints**, not notebook runtimes.

### Opening 2 hours: establish runnable work

- Record current time, occupied GPUs, job commands, completed artifacts, and remaining work.
- Export node 1 artifacts and verify they load on the surviving node.
- Measure GPU count and peak memory for a fit and a panel; do not assume independent single-GPU execution.
- Identify which pending replications already have usable sleep corpora and checkpoints.
- Demonstrate or mark blocked: dual-block loading, F scoring, and struggle-harness execution.
- Start ready replication panels immediately; do not wait for every audit.

### Through elapsed hour 12: close existing experiments

Use a **work-conserving queue**, not reserved lanes:

1. Finish missing matched replication panels and inspect interface/action outputs.
2. Finish the already-running F jobs and validated completion scoring.
3. Recover missing Bs-unseen and genuinely missing same-node references.
4. Run crossed A cells only if the trainer switch is verified.

Put **short, portable jobs with complete control bundles** on node 1. Keep new implementation work and anything likely to cross its deadline on the surviving node.

### Through elapsed hour 36: run only a ready struggle diagnostic

Proceed only if acquisition evidence, a runnable paired harness, and the necessary adapter controls exist. Reuse audited records. If those prerequisites fail, report the specific blocker and finish the established recipe/memory results instead.

Use the existing brief path for the deadline fallback. Do not make a new retrieval service a submission dependency.

### Final 12 hours: close, do not expand

Complete missing matched controls, freeze result manifests, verify exported checkpoints, and produce claim-ready tables. Apply node 1’s admission cutoff independently of these relative checkpoints.

**Bottom line:** The plan’s scarce resource is not obviously GPU-hours. It is verified runnable code, qualified experience, and deadline-safe evaluation bundles. Budget those explicitly; otherwise oversized “lanes” will sit idle while the implementation critical path consumes the sprint.