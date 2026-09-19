# Paired-parent HTTP401: bounded read-only diagnosis

September 19, 2026. Inspection window: 13:34:34–13:36:11 UTC; report assembled
immediately afterward. No API calls, credential inspection/comparison, parent
publications, signals, guard edits, provider changes or retries were performed.

## Conclusion

**No demonstrated local provider/endpoint/configuration mismatch. Live parenting
remains blocked on authentication/authorization for the ORIGINAL provider.**

The evidence does not distinguish expiry, revocation, an invalid credential or
account/model entitlement. A valid authorized credential or provider-side
authorization restoration is required; a local route patch is not supported by
this read. Main reports that its current environment and the running pair use
the same credential and that no renewed credential is available. I did not repeat
that comparison or inspect/copy another life's credential.

## Exact intended route

`PARENT_SOURCE.py:generate` calls the existing
`gpu.orch_route_parent_campaign_providers.strong`, with `reasoning_effort='low'`.
The shared provider function reads `~/.codex/nvidia-astra.config.toml` and requires:

- Provider configuration: `nvidia`, wire API `responses`.
- Model: `openai/openai/gpt-6-astra`.
- POST endpoint: `https://inference-api.nvidia.com/v1/responses`.
- Credential source: the process's inherited `NVIDIA_API_KEY`, used as Bearer
  authorization. It is not taken from another parent, a source file, or the
  interactive Main environment after the process was launched.
- No redirects; explicit empty proxy configuration; one dispatch and no provider
  function retry. Output cap 4,096; no tools; no storage.

The selected non-secret fields in the current local configuration all match
these requirements. No credential values or credential hashes were read from
the environment, printed, persisted or compared. Both process receipts' recorded
Python-source identities match the corresponding current code files, including
the provider function. No configuration files were modified or hashed here.

## Actual paired attempts, September 19 UTC

| Arm | Last preceding successful turn | Success dispatch | Blocked turn | Failed dispatch | Error |
|---|---|---|---|---|---|
| Learner | `turn_000103_1789793374442350991` | 04:49:34.474044 | `turn_000104_1789794006756564934` | 05:00:06.791085 | 401 / auth_error |
| Frozen | `turn_000133_1789793798431912135` | 04:56:38.487334 | `turn_000134_1789794506916730728` | 05:08:26.977778 | 401 / auth_error |

Each preceding success has a completed model response and a publication receipt.
Each failure has a DISPATCH and error body, but no stdout, RESULT or PUBLICATION.
Failed dispatches used the original model, low effort, empty tool list, one
attempt and zero retries. Existing receipts show **the same configuration
identity** for each preceding success and failure; no config-hash values are
reproduced here. Changing effort or model is not an evidence-based auth repair.

Paths are rooted at
`research_loop/workers/post_reboot_pair_parents_20260919/private/{learner,frozen}/`.
These facts do not authorize retrying or erasing either rejected attempt.

## Successful C2 comparison

A bounded known-success reference, not a claim about C2's latest status:

`post_reboot_c2_p7_20260919/c2_session1/parent/parent_000064/` contains:

- `stdout.json`: completed response from the same model, provider `created_at`
  corresponding to **2026-09-19 08:06:33 UTC**, after the pair's failures.
- `OUTBOUND_ROUTE.json`: the exact same POST URL and model;
  `route_changed=false`, inherited-key presence and header-match booleans true,
  one HTTP attempt, no retry or redirect.
- `DISPATCH.json`: configuration identity matches both failed pair dispatches.

C2 adds `node5/provider_route.py:routed`, but inspection shows that wrapper
**verifies and records the existing request; it does not rewrite the URL, replace
the key, change the model, or select another provider**. Adding it to the pair
would improve route observability, not remedy this 401. No such change was made.

The common environment-variable name does NOT prove that C2 and the pair use
equal credential values, principals, authorizations, or expiry state. This read
did not compare those values or borrow C2's credential. Its success rules out
calling the endpoint/config intrinsically broken, not a pair-specific auth
problem. No claim that an already authorized replacement secret is available.

## P3 check and bound of this read

The inspected `post_reboot_p3_parent_20260919/runner.py` preserves the original
strong-parent provider through `p3_lease_parent.load_on_renewed_wall` and wraps
it for activity accounting/429 backoff with xhigh effort. It provides no evidence
of an alternate pair credential source or a safe auth bypass. C2 already supplies
the concrete successful route comparison, so this workstream did not expand
into a P3 history/environment audit.

## Safe restoration proposal

1. **External prerequisite:** the owner renews or restores authorization through
   the existing provider's approved account/secret workflow for the same endpoint
   and model. Do not paste a secret into chat, the repo, a receipt, shell command
   history or Git. Do not extract a key from C2/P3 or change provider/model as a
   workaround. If the provider reports an entitlement issue, resolve that with
   the authorized account rather than guessing at code changes.
2. Until that change, leave authentication guards and existing attempts intact.
   This candidate cannot restore parenting. Keep natives untouched; Main's
   independent parent-free GPU probes can proceed under their own authorization.
3. After valid authorization and a separate owner-approved recovery step, the
   pair's exact CPU-service owners may use their existing secure inherited-env
   launch path. Merely changing Main's environment cannot renew an already
   running process's inherited environment. Verify CPU identities/locks and keep
   native493500/native471737 untouched. Preserve model, low effort, budgets,
   source bindings, all pending/provider ledgers and original rejected attempts.
4. Do not manually clear `provider_blocked`, silently retry the old turn, or
   reset cumulative counts. The owner must first record terminal disposition of
   the known auth-rejected attempts through an explicit audited reconciliation
   transition. If the current service has no such supported transition, design
   and CPU-test that narrowly **as separate recovery work**; no ad-hoc STATE edit.
5. Only after that owner-authorized auth recovery may a new current source-bound
   parent request be considered. A subsequent authentication check/request is
   outside this read-only assignment. Do not assume success from process uptime.
   Require completed provider evidence, attributed publication, authenticated
   INBOX, ACT-request visibility and committed ACT, independently on both arms.
6. Parenting refinement is a separate prospective policy epoch. Both candidates
   remain offline; restored original parenting and actual feedback come first.
   Do not fabricate parent turns while waiting for external authorization.

## Code/tests

No non-secret local defect was established, so no provider/config repair or new
repair test is justified here. Read-only checks covered selected configuration
fields, actual failure bodies, preceding pair successes, code-source identity,
and C2's successful outbound route. The previously recorded 34 candidate CPU
tests do not validate credentials or prove parent delivery. Machine-readable
findings and exact references are in `AUTH_DIAGNOSIS.json`.
