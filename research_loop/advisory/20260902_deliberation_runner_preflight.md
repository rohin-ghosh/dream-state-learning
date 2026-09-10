# Architecture-deliberation runner preflight

Date: 2026-09-02  
Change: `chg_20260902_pcfl_compose_self_revision_text_dev_v1`

This is a process preflight only. No change-directory or science artifact was
edited.

## Current bytes and state

The manually authored canonical proposal exists at
`research_loop/changes/chg_20260902_pcfl_compose_self_revision_text_dev_v1/change.json`.
Its current byte SHA-256 is:

```text
290ab8933a38f1bb95ab65dab083dd42f33c7c165e6f0bfe28a5a2d29af77833
```

The following are absent:

```text
research_loop/changes/chg_20260902_pcfl_compose_self_revision_text_dev_v1/intake.state.json
.research_loop/intake/chg_20260902_pcfl_compose_self_revision_text_dev_v1.deliberation.state.json
research_loop/workflows/chg_20260902_pcfl_compose_self_revision_text_dev_v1.json
```

The proposal parses against the architecture-change schema and declares 19
acceptance tests, but `validate_change` fails before structural completion:

```text
IntakeError: context hash mismatch for
research_loop/changes/chg_20260902_pcfl_compose_self_revision_text_dev_v1/experiment_spec.md
```

The runner and intake implementation bytes inspected here are respectively
`4f5c3f3601a1e19fc687fa4ab04d3dd973a8ed035f063b15637f0631ed096d65` and
`62d29dfa6f34b8093f686615c13dc192bb82c58bb789100be3ff78c91dc9fbea`.

All 11 declared/current context SHA-256 mismatches observed in this checkout are:

```text
experiment_spec.md       declared f9607df97eaaff9d2e89082895b77d51b2285db52978dea6971a8ac803a6a060
                         actual   8554dca807ecf1d378ce39058380d4050ec64e9626c1035b27e18d0fa4ea7f0b
semantic_dsl.schema.json declared 50b6578b657e9fe0065445ac79145ca2e50832c270eb8b9cc6ccf94d132e79cf
                         actual   e87e034763c329ddfa08f812999e1d731be3ff62bd856085906065831a1f1965
generic_dream1.txt      declared 2991d6fb479cb1ba3279519fa94c19996cc7c2bfd6feaec89ce53106328aa7f4
                         actual   b6988e0c8a56799c7f96fd68c49b80c06fa0ac7964c3641fa868263ced47ff4c
generic_dream2.txt      declared 89032603532c39fea84ed09d3e67974e45e54bc231ae1194b08d4e5f0cce9f84
                         actual   3ad651859424611ee136908b39282dde4453be6c8ee7e6e5344081ac803791b7
neutral_dream1.txt      declared 6242e692cae3e49f25ad56948a3bbe609bcab025245d6630d76f3067d5a4ee3e
                         actual   5c2ee847e353de238d26484c575254eb75e43d97beec0ae917b2cdab10ac6fbc
neutral_dream2.txt      declared e36db9afbe76bd350c1c59acbd651f42275e2bd6f43cc66a2fa58269f47c944f
                         actual   c1f726b71df1510f9d3dac4bd4c42f86ab9fee2aefe40457528e9f821a728c39
class_informed_dream1.txt declared 1f88e5fd960e4400a2c775400f5b7f0ca26e85f8bd3af2ba0ed897ddbee71769
                           actual   8834b2acb160417c41a1e49e0eebe72453005f796b11b928349b0f3677172e40
class_informed_dream2.txt declared fa68afebb4d536531f418e81bcbcf9fe7d4cf43564cbc74688cfe6d481321e36
                           actual   d4f973a7d2f839e2f93ff29e86516866c113a392c614588c4e4f888b12c61bef
one_shot_dream1.txt     declared e51e8818d76653e8f2743f0fac25bdab8812b28d8a7835cbc8bc958425ea142a
                         actual   957fd57d2b2ca7f3e327a2aa56c0522be85cb4c1590c874d81616f925f01b267
one_shot_dream2.txt     declared ffd5923d82b198b527ede100b5aa8beeb400870a7c460ca7059b59992eacf307
                         actual   d08aee4d0969d5bc567af91d80dceb68bb99413897f317c5335e3842bf517a56
iterative_thinker.txt   declared 50ccc1e8e4c5dbd18653a0b8f9dbdf56a9199db23ff0cbc80592aa3ffc0f5978
                         actual   049a7e899bf806aab0f7db6dfdca5154a2f390dbd08e08aaf9423285dac056dd
```

## Safe command sequence in the current checkout

Use only read-only checks until the bytes are reconciled and the runner
supports explicit adoption. From `/Users/rohing/dream-state`:

```bash
ID=chg_20260902_pcfl_compose_self_revision_text_dev_v1
CHANGE=research_loop/changes/$ID/change.json
STATE=.research_loop/intake/$ID.deliberation.state.json
INTAKE=research_loop/changes/$ID/intake.state.json
WORKFLOW=research_loop/workflows/$ID.json

test -f "$CHANGE"
test ! -e "$STATE" && test ! -e "$INTAKE" && test ! -e "$WORKFLOW"
shasum -a 256 "$CHANGE"
python3 -m research_loop.architecture_intake --root . status --state "$INTAKE"
```

The final command is expected to return status 1 with a missing-state error.
Do not run `architecture_intake ... init` first: it would create the mutable
intake state, but `architecture_deliberation ... init` would still reject the
combination of an existing intake state and canonical artifacts. Do not run
the deliberation `status` command as a supposedly read-only probe: its current
implementation calls `initialize_deliberation` and creates runner state on a
clean workflow.

After a workflow has been deliberately authored from
`research_loop/workflows/architecture_deliberation_v1.template.json` with
`output_dir` set to the existing change directory, the currently implemented
command is predictably blocked:

```bash
python3 -m research_loop.architecture_deliberation "$WORKFLOW" init
```

It returns `DeliberationError: deliberation artifacts exist without runner
state; refuse ambiguous adoption` and writes no runner state. There is no safe
successful command sequence for this case in the current implementation.

## Runner defect and required behavior

`initialize_deliberation` rejects `any(canonical_path.exists())` whenever the
runner state is absent. This makes the valid manual-proposal branch in
`_advance_advocate` (validate the exact canonical proposal, then initialize
intake) unreachable on first initialization. A fresh output directory cannot
adopt the existing proposal without copying/re-serializing it, which would
break the exact-byte binding.

The runner needs an explicit, fail-closed existing-proposal adoption path. It
should require exactly one existing canonical advocate artifact, no downstream
artifacts or intake state, validate the proposal and all of its context hashes,
bind its literal file SHA-256 into the new runner state, and never rewrite the
proposal. The first run may then create intake state against that same path.
Any conflicting downstream artifact, malformed proposal, stale context, or
pre-existing intake state must continue to stop before model execution.

The target proposal currently cannot pass that stricter adoption check until
the declared context bytes are restored or a new proposal chain is authored.
Neither action was taken here because both change bound bytes.

## Test gaps

`test_existing_unowned_artifacts_are_not_adopted` covers only an invalid `{}`
artifact and therefore does not test the required distinction between a valid
manually authored proposal and an unowned/conflicting artifact. Add tests for:

1. valid canonical `change.json` + no runner state: adoption succeeds, intake
   enters `collecting_interpretations`, and the proposal SHA-256 is identical
   before and after;
2. canonical proposal plus any downstream artifact or conflicting intake:
   adoption fails closed without an agent call or byte mutation;
3. stale proposal context hash: adoption fails before any agent call; and
4. `status` on a clean workflow is observational and does not create state.
