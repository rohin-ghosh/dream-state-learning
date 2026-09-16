# F1 prospective Astra choice: consumer incompatibility

[Builder / Main] September 16, 2026, 02:10 UTC.

The 02:05Z clarification is accepted: Astra is a prospective parent-model
choice for NEW turns, not a retry or reassignment of a refused historical turn.
There is no policy objection to that bounded prospective choice. The prior
entry's broader refusal interpretation was incorrect.

The remaining obstacle is the running consumer. F1's live
`R121_INDEPENDENT_PLAN_V2.json`, SHA256
`9a5537780508ac451125d9bc4afde85a45a021fb762498efdf05c070513b884e`,
retains its Fable provider/substitution contract. An honestly labelled Astra
response does not meet it. The resident loads its plan at startup; rewriting a
broker config cannot update the resident's in-memory parent binding.

At 02:10 UTC, Main ran the new forward-only preparation check against the exact
node-5 root and verified old config/retirement/child-plan provenance. It exited
at `consumer_Astra_authorization_required_before_broker`, BEFORE creating a
switch directory, claiming any request, or calling a provider. The check leaves
the running child and historical captures untouched. Earlier observed high-water
115 / C52 is not an activated boundary; a real switch must snapshot anew.

The prospective broker draft reuses A1's existing Astra HTTP call with low
effort, 512 output tokens, 20-second timeout and one attempt. It filters out
historical sequence IDs, old claims, old responses and pre-boundary requests;
preserves total original call allowance; records actual model identity; and
uses a separate prospective ledger. Raw scratch would be on `/data` outside
the repository and archived on the node. **It is NOT staged or launch-ready**
because consumer compatibility is required before preparation or dispatch.

Main CPU tests: 11 forward-switch tests plus 4 unchanged A1 fast-provider tests
PASS. These cover the prospective boundary and the incompatibility guard, not
a successful native handoff. They do not establish delivered parenting.

Requested next authorization: checkpoint-preserving consumer process handoff
at a safe completed-sleep boundary, preserving the adapter, AdamW/RNG, saved
context/history, ledger and budgets, with no logical-life reset or replay.
F2 needs the same consumer authorization; F4 needs its completed-episode state
preserved. No handoff is implemented or executed by this receipt.
