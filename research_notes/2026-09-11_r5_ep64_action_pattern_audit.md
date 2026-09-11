# R5 seed 701 episode-64 action-pattern audit

Date: 2026-09-11

Status: **exploratory mechanism diagnostic only.** This is one life, one
checkpoint, and eight report programs. R5's numerical score gate is disjoint
from the report panel, but its format canary uses old report programs; the
report panel is therefore not untouched by every commit decision. R5 also
uses a permissive score tolerance. These results do not establish
experiential strategy learning.

## Receipts and method

The adapter-ON and adapter-OFF ledgers were emitted at the same episode-64
probe and contain the same eight program identities:

- adapter ON SHA-256
  `db8b5a68d139a5fd20e1481f268f90e9bf724112220f95acadf58a295b8a7d10`;
- adapter OFF SHA-256
  `db76f422f39fdba70ad566ee0ed14d5d616974128e2d4393a784b5110a117008`.

Those hashes exactly match the remote files named
`R5_B_seed701/probe_ep0064.ledger.jsonl` and
`R5_B_seed701/probe_ep0064_adapterOFF.ledger.jsonl`. The remaining bound
remote byte targets are:

- `R5_B_seed701/probe_ep0064.json`:
  `98f93d4d1720d6d6e3dcecc31072b17bbb61f339c548b25b439fab147c04c6d7`;
- `R5_B_seed701/probe_ep0064_adapterOFF.json`:
  `d63fe6deed4ce290816546e5609643bae508fe4f7113b3deee784f454b2fc144`;
- `R5_B_seed701/sleep_0064/gate.json`:
  `9467e64df48bbd1cc9afc2b2f6b7490adc1486a8555abc26398b33e77c710faa`;
- `R5_B_seed701/sleep_0064/adapter/adapter_model.safetensors`:
  `12c535baabea0ae3d756459badb79ea86be4886b36c12a891f1542e273f41b7f`;
- `R5_B_seed701/sleep_0064/corpus.json`:
  `543a932de607acd2ca84ddec3ee8173a69e9f1bfe313381a4fc1dd0103e66cfa`.

The adapter receipt above binds the specific safetensors file, not an
unhashed directory.

The read-only analyzer is `organism_v6/r5_action_pattern.py`. It uses only
authoritative `kind=act` rows. For each fixed action cap `k`, it takes the
best score among the first `k` ACT rows for each program, then
averages the eight paired program scores. This is a retrospective prefix-cap
diagnostic, not an equal-action-budget intervention. ACT-like prose is never
counted as execution. Action normalization strips comma whitespace and drops
empty comma fields.

The bootstrap exposes the exact action string
`-mem2reg,-sroa,-gvn,-simplifycfg` at birth (`organism_v6/bootstrap.txt`,
line 11) as an ACT syntax example. Its utility is not demonstrated there.
The string is therefore prompt-supplied, not a discovery made from the R5
life.

## What changed at episode 64

| Measure | Adapter ON | Adapter OFF | ON - OFF |
|---|---:|---:|---:|
| Mean best score | 0.5070 | 0.4629 | +0.0440 |
| Authoritative ACT rows | 318 | 38 | -- |
| Nonempty actions | 317 | 38 | -- |
| Mean ACT rows per program | 39.75 | 4.75 | +35.00 |
| Normalized unique nonempty actions | 31 | 20 | -- |
| Programs beginning with the birth routine | 8/8 | 4/8 | +4/8 |
| All actions equal to the birth routine | 123/318 | 9/38 | -- |

One ON row is an empty/no-op ACT at `patricia` tick 13; it is retained in ACT
row and score accounting but excluded from nonempty-action diversity. The
equal 16-thought-chunk allowance did not equalize executed actions: one
model output can contain multiple valid ACT markers. Adapter ON therefore
began with the prompt-supplied string on 8/8 programs versus 4/8 for OFF and
issued substantially more ACT rows in this checkpoint.

The fixed-action-cap comparison shows how the realized panel gap changes when
each recorded trajectory is scored through at most `k` ACT rows:

| Maximum ACT rows scored | ON programs reaching cap | OFF programs reaching cap | Adapter ON | Adapter OFF | ON - OFF |
|---:|---:|---:|---:|---:|---:|
| 1 | 8/8 | 8/8 | 0.4878 | 0.4606 | +0.0272 |
| 2 | 8/8 | 8/8 | 0.4925 | 0.4606 | +0.0319 |
| 4 | 8/8 | 4/8 | 0.4962 | 0.4629 | +0.0333 |
| 8 | 8/8 | 1/8 | 0.4962 | 0.4629 | +0.0333 |
| 16 | 8/8 | 0/8 | 0.4962 | 0.4629 | +0.0333 |
| 32 | 6/8 | 0/8 | 0.5070 | 0.4629 | +0.0440 |

The one- and two-action caps are reached by every trajectory; only the
one-action row isolates the first executed choice. The two-action row
additionally mixes second-action identity and ordering, while caps of four or
more also mix endogenous stopping. None identifies the causal return to
issuing more actions.

The first-action difference is concentrated in the four programs where OFF
used a two- or three-pass prefix of the prompt-exposed four-pass string. The
paired first-action deltas were +0.0187 on `susan`, +0.0200 on `dijkstra`,
+0.1451 on `patricia`, and +0.0339 on `gsm`; the other four programs used the
same first routine in both conditions and had zero first-action delta.

This first-action mean is concentrated: `patricia` contributes 0.0181 of the
0.0272 panel mean (about two thirds), and four of eight programs contribute
zero. In the full realized trajectories, `patricia` and `gsm` together
contribute about 75% of the +0.0440 mean gap. This is one seeded generation
probe with no across-replicate uncertainty interval. The program identities
were absent from waking and training ledgers, but four report programs entered
format-canary commit decisions; the panel was therefore not fully held out.
On this panel, the prompt-supplied string also has favorable first-action
scores. The action content itself was not held out.

## Bounded reading

At this checkpoint, a +0.0272 mean advantage was already present when every
trajectory was scored at one action. That advantage coincides exactly with ON
emitting the prompt-supplied four-pass string on 8/8 programs rather than
4/8. The full realized trajectories differ by +0.0440, but the additional
gap cannot be attributed solely to action count.

The supported statement is therefore:

> At R5 seed 701 episode 64, adapter activation coincided with high-frequency
> emission of a prompt-supplied routine and 318 ACT rows versus 38 with the
> adapter off.
> This produced an exploratory +0.044 mean best-score difference on the
> eight-program report panel; +0.027 was already present at a fixed one-action
> cap. The checkpoint does not show invention or conditional selection of a
> strategy learned from lived experience.

This single checkpoint is consistent with adapter activation amplifying a
prompt-visible action string into high-frequency emission. It does not
establish general writer capability, strategy learning, or interface safety.
It nevertheless sharpens the next test: remove useful action content from the
birth example, then require the written policy to select different actions
under different observable situations. The conditional writer canary is
designed for that distinction; the full C11 guard remains parked until the
final paper-grade run.
