# Existing-trace mechanism audit: world14, SHARD7 PROBE-A

Measured2026-09-15T01:32:33UTC. Author read-only analysis, not independent
reader verification. No actor/provider/model calls, optimizer updates,
new evaluations, world regeneration, modified labels or held repair.
Only the specified failing world14 and immediately adjacent frozen indices
13/15 were inspected across the five already-complete A100/baseline states.
The saved three-pair batch and held denominators remain unchanged.

## Direct answer

The underlying two-hop graph and actual source action receipts are internally
consistent, and both goals are reachable by legal two-port paths. The supplied
OWN_TEXT evidence is **incomplete**: only3/4source EVENTs were accepted. The
root edge leading toward the failed goal lost a character during actual child
EVENT emission and was correctly rejected. The reader consequently returns
`MEMORY UNAVAILABLE` at that advertised address.

The observed policy failure is real: on both layouts, changing GOAL to the
opposite destination leaves the entire command sequence unchanged. However,
this behavior is identical in original37ec, FULL7801, OFF7801, FULL7802 and
OFF7802. It is not newly introduced by training, and does not establish failure
on fully documented public evidence. Source availability and policy handling
of that missing evidence are both implicated; no causal repair experiment was
performed. Both original world-gate failures remain FAIL.

## Exact source bytes and static path check

All relative paths below are under the immutable extracted root
`gpu_artifacts_local/orch_terse_breadth_20260914_attempt1/terminal_a100/`.
The archive SHA is461f291aac312782cf98a41aed9fac2a33d2b06f11c203b4e09d7296c895f818.

`collection1/shard7/COLLECTION_08.json`, record1, actual action:

```text
ROUTE P_SQ7P2Z2RPW
```

Its actual public receipt, in record1.event.messages:

```text
RECEIPT R_6AJ5S4SFBX AT N_DHILK7OM7N DID P_SQ7P2Z2RPW GOT N_CHO6AFOOSL
```

Actual child EVENT, also bound by native `collection1/CALL_0329.json`:

```text
EVENT E_WBUMM5YVBC AT N_DHILK7OM7N DID P_SQ7P2ZRPW GOT N_CHO6AFOOSL EVIDENCE R_6AJ5S4SFBX
```

The emitted port is`P_SQ7P2ZRPW`, not actual`P_SQ7P2Z2RPW`: one`2`is
missing. This was terminal=true/truncated=false, not an unfinished decode.
Saved record1 has accepted=false and error`ValueError: not exact EVENT`;
collection status`COLLECTION_INCOMPLETE_NO_FIT`, accepted_events3/4,
ready=false. It is not a later typo correction or relabeling.

The other three accepted EVENT lines exactly match their captured edge and
receipt identifiers. Two-hop paths mechanically enumerated from the saved
world (not an actor rollout):

- To`N_LID6KJWEWI`: `P_5CAFUWR7I7`then`P_TXODAZFI7H`; both EVENTs available.
- To`N_GTB3VW2K5L`: `P_SQ7P2Z2RPW`then`P_UKWQHLOGG5`; root EVENT unavailable,
  second EVENT available.

The accepted second-branch destination memory is:

```text
EVENT E_ZGK5QQTZJB AT N_CHO6AFOOSL DID P_UKWQHLOGG5 GOT N_GTB3VW2K5L EVIDENCE R_NBBGVRJHAG
```

Thus the failed goal itself is named in valid memory; the missing information
is specifically the connection from CURRENT through the offered root port
to`N_CHO6AFOOSL`. The correct first port is in the public PORTS list, so this
is not a nonexistent goal or an unavailable action. The available literal
public evidence alone does not explicitly state that port's destination.
Topology-family inference might recover it; impossibility is not established.

## Exact readout behavior

`after0/PROBE_14_OWN_TEXT_2.json`, initial public task:

```text
ROUTE TASK
CURRENT N_DHILK7OM7N
GOAL N_GTB3VW2K5L
PORTS P_5CAFUWR7I7,P_SQ7P2Z2RPW
EVENTS E_63FEHWSC4P,E_WBUMM5YVBC,E_XSIWLN2RAR,E_ZGK5QQTZJB
```

The actual second read and response:

```text
READ EVENT E_WBUMM5YVBC
MEMORY RESULT
MEMORY UNAVAILABLE
```

After reading all four addresses, the two actual route commands are:

```text
ROUTE P_5CAFUWR7I7
ROUTE P_TXODAZFI7H
```

They legally arrive at`N_LID6KJWEWI`, not requested`N_GTB3VW2K5L`;
saved terminal_reason=`dead_end`. The first commit already selects the wrong
branch; this is not an illegal identifier or insufficient remaining call
budget. All affected episodes use four READs and two ROUTEs within six calls,
with no callback error or truncation.

Every task-index command list is exactly equal across all five saved states.
Within each state, task0 versus2 (same layout, opposite GOAL) has the same
commands; likewise task1 versus3. The other layout reverses public port/event
order, but all states still choose the same fully documented branch rather
than simply the first displayed port. Tasks0/1 succeed; tasks2/3 fail. All
five states therefore have2/4goals and0/2opposite-goal pairs on this world.

## Fixed adjacent-world comparison, not held mining

Indices13 and15 are immediate neighbors in the already-frozen ordering, not
selected by their outcome. Both have4/4accepted source EVENTs.

| World | Source accepted | Baseline pairs/goals | FULL7801 | OFF7801 | FULL7802 | OFF7802 |
|---|---|---|---|---|---|---|
|13: SHARD6 PROBE-B|4/4|0/2,1/4|2/2,4/4|0/2,1/4|2/2,4/4|0/2,1/4|
|14: SHARD7 PROBE-A|3/4|0/2,2/4|0/2,2/4|0/2,2/4|0/2,2/4|0/2,2/4|
|15: SHARD7 PROBE-B|4/4|0/2,2/4|2/2,4/4|0/2,2/4|2/2,4/4|0/2,2/4|

FULL can select opposite goal branches on the neighboring complete-evidence
worlds, while controls do not. These are different worlds/identifiers, not
a randomized removal experiment, so the comparison is suggestive rather
than a causal estimate of the missing EVENT's effect.

## Implication for dose16 and next NEW-TRAIN discriminator

Further training cannot repair the frozen reader store: the rejected record
will remain absent in every dose16 readout. Higher dose could nevertheless
alter goal sensitivity, uncertainty handling or topology-based inference.
Its residual value is that already-declared policy/dose comparison, not
testing whether repetitions restore source evidence. Training-source quality
filtering admits complete sources, so extra repetitions do not directly
teach the missing-source case. No claim of a guaranteed ceiling is warranted.
Node3physical6/7 remain running; no stop, code fix or reallocation was made.

Cheapest proposed causal discriminator is the NEW-TRAIN-only, two-world,
intact-versus-predeclared-root-bridge-withheld contrast in `SEQ281.md`:
zero fits, maximum304model calls for37ec/FULL7801dose4/OFF7801dose4, including
16new actual source calls. Balance withheld root branch across the two worlds;
reuse genuine unmodified child-native EVENTs, preserve failed collection
attempts, freeze masks/states/goals/order/caps before outcomes. No reuse of
these held identifiers or reconstruction of world14. Main may instead
predeclare both dose16states too (496call cap) for a direct dose test.
This is a proposal only, not authorization or implementation of another run.

## Reproducibility and limits

`failure_mechanism.py` reads existing artifacts only, hashes inputs, verifies
the emitted typo against the native CALL, verifies accepted lines against
saved edges, checks the single missing reader response and exact command
equality, and enumerates static two-edge paths. It never calls an actor,
generation API, replay engine, scorer, optimizer or world builder.
`FAILURE_MECHANISM_VALIDATION.txt` records passing assertions over60existing
episodes; `FAILURE_MECHANISM.json` preserves exact quotes and raw-file hashes.
This author analysis does not modify scientific labels, certify an independent
reader verdict, promote a checkpoint, or finish the pending third pair.
