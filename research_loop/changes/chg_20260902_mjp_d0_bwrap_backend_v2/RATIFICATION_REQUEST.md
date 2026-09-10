# Exact ratification request: minimal J/P D0 CPU instrument

## Decision

Ratify two already-adjudicated artifacts together:

- scientific consensus `647cc06be22142d983e691c8e14ebd183b215af3c53ef89bd8dbfd03271d4624`
- scientific paused-state `9491b8646568a7fce084316b2c6d0c6ab6da653b9e2ce997ff7b38afe7644005`
- Bubblewrap backend consensus `c3cfa3e4304836cc64c7a4a8be7d95678252ac4ab820294ad65885251ee2c34c`
- Bubblewrap paused-state `83c00cbeaffcba668aee6fb3c13c13afa5453704e225556d703a1a1c3777e4e9`

This releases only the CPU implementation and conformance work below. It does
not release a model call, GPU run, G1, or a scientific claim.

The science is the minimal 384-world J/P causal instrument. The backend is a
one-host, reviewed-code interface-hygiene boundary labeled only
`BWRAP_CPU_INTERFACE_ISOLATION`. It uses a public-only batch controller whose
action transcript freezes before any hidden-state execution or scoring.

## Exact authorized scope

1. `analysis:rml_minimal_jp_d0_cpu_conformance_evidence`
2. `implementation:rml_minimal_jp_d0_384world_cpu_instrument`
3. `remote:a4u8g_0105_cpu_only_bwrap_conformance`
4. `testing:rml_minimal_jp_d0_bwrap_oracle_and_pre_g1_cpu_gate`

## Exact forbidden scope

1. `claim:learning_memory_lora_benchmark_scaling_paper_or_oci_conformance`
2. `external:publication_outreach_submission_or_unrelated_remote_action`
3. `gpu:any_kernel_model_training_or_inference`
4. `host:lease_credential_quota_system_package_or_runtime_change`
5. `implementation:archived_candidate_b_or_existing_g1g2_science_bytes`
6. `model:any_provider_tokenizer_or_generation_call`
7. `network:any_payload_or_science_process_access`
8. `science:automatic_g1_g2_g3_dispatch_threshold_repair_or_claim_promotion`

The same four authorized-scope atoms and eight forbidden-scope atoms apply
separately and identically to each of the two human-ratification artifacts.

## Exact reply to authorize

Copy and send this paragraph without changing it:

> I, Rohin Ghosh, ratify scientific consensus SHA-256 647cc06be22142d983e691c8e14ebd183b215af3c53ef89bd8dbfd03271d4624 and Bubblewrap backend consensus SHA-256 c3cfa3e4304836cc64c7a4a8be7d95678252ac4ab820294ad65885251ee2c34c. I authorize exactly the four requested CPU scopes in scope_proposal SHA-256 bede2e7e1a95598372aa9bb84f1b0510c6bcbb756379c95ebd5df875cc50b087 and retain exactly its eight forbidden scopes. I accept the 384-world J/P design, the deterministic public-only batch boundary, the two-stage freeze, immutable staged runtime and input closure, one-way bounded pipes, two-monitor cgroup accounting, exact BWRAP_CPU_INTERFACE_ISOLATION-only claim, and preservation of every other parent scientific ruling. This does not authorize any model call, GPU use, G1/G2/G3, host or lease change, automatic successor, threshold repair, or scientific or paper claim.

## Paper-ROI stop rule

This backend receives one implementation attempt under the existing ten-working-day
and two-calendar-week outer bound. A second backend redesign, a resource-bound
miss, or pressure to build a general sandbox terminates this route rather than
delaying the semantic-use experiment.

After a green CPU instrument, a separate exact decision is required for the
four-pair G1 DEV screen. Even a green G1 is only a spending decision; the first
potentially paper-usable result is a prospectively powered held-out lifetime
experiment comparing target-blind dreamed text, the identical corpus in a
per-life LoRA, and strong context/RAG/direct-trajectory controls as lifetime and
dependency depth grow.
