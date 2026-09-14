# Independent result: self-critique versus repeat, this attempt only

2026-09-14, Schrodinger; local read-only reduction20:13UTC, primary comparison20:14UTC.
**Evidence verdict: the terminal counts and shared-initial pairing check out.
Critique has6/16 goal outcomes versus repeat4/16; both have1/8 successful
goal pairs and zero six-turn candidate episodes/rows.** This is not a content,
fit, learned-reflection or general critique-efficacy pass. No model imports,
tokenizer, network, GPU operations, phase reruns or code changes were used.

Counts were independently derived from DATA/CALL/episode records before
reading CPU_REDUCTION.json or the primary. The subsequently published
`2026-09-14_self_critique_repeat_collection_first_result.md` (SHA256
`78fc04189aafd12bc9553b9401fd0c1bbfb47666ac9e6e1857abcb09906ef1a3`)
agrees on denominators, all outcome/candidate counts, callback causes, invalid
interventions, shared input identity and unequal actual spend. **No discrepancy
found in the requested terminal-result scope.** Its no-fit/no-generalization
interpretation is warranted. I did not independently re-execute its CPU gate,
remote launch/exit checks or publication procedure; those are outside this
local reduction, not additional certified claims.

## Fixed denominators and three distinct gates

The same four original rich shard0 TRAIN worlds, each tasks0–3 in fixed order,
appear in all three phases. Every phase attempts16/16 tasks; none is missing
or replaced. Each has eight fixed same-display opposite-goal pairs: tasks0&2
and1&3 within each world. Failed tasks remain in these denominators.

|Phase|Goals /16|Pairs /8|Six-turn eligible /16|Candidate rows|Actual calls /ceiling|
|---|---:|---:|---:|---:|---:|
|COMMON_INITIAL|4|0|0|0|25 /96|
|SELF_CRITIQUE_REVISE|6|1|0|0|54 /112|
|REPEAT_NO_FEEDBACK|4|1|0|0|48 /112|

I reconstructed legal committed transitions and source-correct first ports
from the four actual captured EVENT records per world, then checked endpoints
against each task. Goal success here is arrival via two legal commits. A pair
also requires both goals and distinct source-correct first ports. Both final
arms' single successful pair is worldD/tasks0&2. These are outcome gates,
**not** the six-turn candidate gate.

Candidate eligibility additionally requires four actual reads and six actual
captured/projected actor targets. All four initial successes use zero reads.
Five of six critique successes use zero reads; worldB/task2 uses three. Three
repeat successes use zero reads; worldD/task2 uses one. None qualifies. The
repeat worldB/task2 attempt does use four reads/six actor calls but ends at a
dead end, so it also contributes zero rows. No outcome-only shortcut was
silently converted into a training trajectory. All fit/semantic flags are false.

Relative to the shared initial, critique retains its four successes and adds
worldB/task2 and worldD/task2. Repeat gains three and loses three, leaving its
goal total unchanged. Directly between arms, four tasks succeed only under
critique and two only under repeat. The pair count ties. These fixed correlated
instances and one run per arm do not establish a general effect or a learned
capability; no fit happened.

## Common initial and intervention information

Both arms bind exactly the same COMMON_INITIAL RESULT file SHA256:
`6ce60c01e4a7400c55d4f2153cdd2f34b64f7c81f0c1b68cb0e29c5ac8becef8`.
Their initial document seal is identical:
`48fe601663b8c9a11e948765e2be023352a721a30c311d0022d2557a8ef09061`.
Collection bytes, old-ID exclusions, episode ordering, task identities, source
hashes and native input bindings match the common initial in both arms.

For all16 paired intervention calls I independently reconstructed the public
history object from the initial task/messages/stop and actual child raw outputs
and errors. Both arms have byte-identical serialized histories and identical
intervention system messages; only the final critique-versus-plan instruction
differs. Every final actor receives the actual corresponding advice, marked
fallible, or the declared unavailable marker when that advice is invalid.
Actor messages after the system match the actual current episode trace: no
future observation or researcher source-plan input was substituted.

Thus REPEAT_NO_FEEDBACK does **not** mean blindness to previous public failures
or outcomes: both arms see them. The comparison is critique-prompting versus
independent repeat-planning, not feedback access versus no history or extra
thinking versus none. Content of the advice remains unreviewed.

## Ceilings match; actual spend does not

Each final arm permits16 intervention calls and up to96 actor calls, all with
512-token generation and2048-context ceilings. All16 interventions and16 final
attempts occur in both arms. Common-initial cost is shared, not duplicated.

|Phase/role|Calls|Prompt tokens|Generated tokens|
|---|---:|---:|---:|
|Initial actor|25|7,560|2,048|
|Critique intervention|16|8,635|4,952|
|Critique actor|38|24,136|2,566|
|Repeat intervention|16|8,667|2,699|
|Repeat actor|32|17,230|2,775|

Totals:127 unique native calls,66,228 prompt tokens,15,040 generated tokens
including returned terminal tokens when present. The final arms spend54 versus
48 calls and7,518 versus5,474 generated tokens. Phase wall is171.305s initial,
429.908s critique and336.693s repeat; these durations include loading/checks,
not pure kernel time. Early stops are not padded. Equal ceilings are supported;
equal spent calls/tokens/compute is not. The +2 goal difference must not be
advertised as an equal-spend causal efficiency benefit.

## Callback stops are not native exceptions

|Phase|Actor callback stops|Callback causes|Other episode stops|
|---|---:|---|---|
|Initial|9|4 multiple ACTION delimiters;5 invalid whole-command parses|3 dead ends;4 goals|
|Critique|8|2 multiple ACTION delimiters;6 invalid whole-command parses|2 invalid routes;6 goals|
|Repeat|8|3 multiple ACTION delimiters;5 invalid whole-command parses|4 dead ends;4 goals|

All127 native capture `error` fields are null: zero Engine.generate exceptions.
The25 actor callback stops occur after actual returned text fails exact
projection/parsing; they are not25 failed native generations. For example,
initial CALL_004 contains two `ACTION` blocks/READ commands; repeat CALL_001
appends `END CHILD ADVICE` after a ROUTE. Both actual texts are preserved and
rejected, not stripped into usable commands. The generic `not exact short
ROUTE` message also covers a malformed whole READ/mixed-text output; it is not
by itself evidence that a syntactically valid route was committed and failed.

Separately, **two native intervention completions are nonterminal/truncated**:
critique CALL_037 (worldC/task3) and repeat CALL_011 (worldB/task0), each at512
tokens. These are one invalid advice completion per arm, not four failures
from separately counting terminal=False and truncated=True. Their actual raw
responses stay captured. Both final attempts still run with the explicit
`[CHILD ADVICE UNAVAILABLE]` marker; no invented replacement advice or task
drop. Therefore zero native exceptions does not mean every completion was valid.

## Scope of verification and evidence references

Source marker: `3b1b07c324d4841fbba48fe201069e3eaf9fc2b5`.
Frozen protocol SHA256:
`154b7642113e48068e7357efb6a1d4c956dc151e030472fcb3f6ac98e696883a`.
Local capsule:
`gpu_artifacts_local/astra_self_critique_repeat_terminal_20260914_attempt1/terminal.tar.gz`
SHA256 `23ddf8f02f802b5244d26657ca9f35f8f466ae9151f8654dffff0287fe9ccd76`;
its548,724,317bytes and recomputed hash match the staged transfer receipt.
All paths below are under the extracted
`astra_self_critique_repeat_20260914_attempt1/` directory.

RESULT hashes:
- `common_initial/RESULT.json`: `6ce60c01e4a7400c55d4f2153cdd2f34b64f7c81f0c1b68cb0e29c5ac8becef8`.
- `critique/SELF_CRITIQUE_REVISE/RESULT.json`: `dc50ef793da86f67c1e388cc2ef53c5c82d9a1c2178b4b2831a7ab9233c1b58d`.
- `repeat/REPEAT_NO_FEEDBACK/RESULT.json`: `36dfdf77a807d76e794e990a092733600b5413363ff7295d3683bb2bc2406109`.

Standard-library-only assertions verified all three document seals, every
native CALL join/hash and output inventory, fixed task ordering, shared initial
joins, public histories/advice inputs, command byte spans, actual source-edge
transitions, goal/pair/candidate gates and reported counts. Source driver/helper/
protocol hashes match their capsule bindings. Saved readonly state receipts
agree before/after on37ec3788, and results report frozen base unchanged and zero
fits/updates. This is bounded artifact consistency and independent reduction,
not independent tensor-state authentication, a full ancestry audit or a
semantic review of all generated advice. No collateral branch is evaluated.
