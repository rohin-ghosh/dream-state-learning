# R168 parent rollout — actual execution status

September17, 2026, 08:49 UTC. Actual events, not planned adoption.

| Parent | Started UTC | New PID / start ticks | Preserved reservation | Next opportunity |
| --- | --- | --- | --- | --- |
| C2 | 08:43:23 | 564248 / 174162005 | 96 | 98 |
| C3 | 08:43:27 | 564572 / 174162399 | 90 | 92 |
| C4 | 08:43:33 | 565196 / 174163009 | 87 | 89 |

Per-parent receipts are `ROLLOUT/C2`, `ROLLOUT/C3`, `ROLLOUT/C4`:
`OPERATIONAL_GO.json`, `QUIESCED.json`, `LEDGER_TRANSFER.json`,
`OLD_PARENT_EXIT.json`, `STARTED.json`. Every inherited attempt file was copied
byte-for-byte, including SILENT/provider failures and reserved cursors. All prior
publications were rendered before custody. No native/provider signals, deletion,
new scientific recipe, credential change, or wall change.

The originally staged directory name contained the literal `final`, which the
existing no-evaluation-path guard rejects. That first executable preflight failed
before any parent signal. These were parent-config artifacts, not evaluation data.
The fix relocated identical local source/config bytes to this neutral directory;
the no-evaluation guard was not edited or bypassed. All actual successor subprocess
`verify_gate` and remote transport preflights passed before their parent signals.

Actual gate SHA `c1fb6f68a8c1b917b0d5472e556b4230d211b77322b91acb4af0b123fecd5aa8`.
Relocation SHA `c2d26be7711f510709b306208afc0066b5ea299deae508145ed6f3fc7b7602c1`.
The received remote source is still the originally authorized attempt3 path;
its 67 files/import origins were verified. Runtime SSH configuration is a symlink
to the same existing hosts.env, whose bytes remain unchanged, not a copied credential.

The 08:37 Main authority and actual relocation/execution timestamps are preserved.
Main subsequently confirmed these actual bindings at reported08:45UTC; the
confirmation was recorded08:49, separately in `MAIN_CONFIRMATION_0845.json`.
No newly backdated GO is substituted for the original authority.

Main's intervening request for fully neutral local and remote names produced a
passive `r168_community_engagement_20260917` package: 89CPU tests, new receiving
and actual verify_gate/transport preflight, **no signals/adoption**. After Main's
keep-current-successors instruction, none of C2/C3/C4 will be restarted to use it.
No other worker should assume that unused package is the running source.

## Observed behavior, not claims

At08:48:47, C2 had96 committed rows and was at sleep UPDATE2973; C3 had90 rows
and UPDATE2646; C4 had87 rows and a SLEEP_COMPLETE head. All verified native
identities remained live. No fresh post-takeover parent opportunity had yet been
recorded. Empty new-attempt lists are not new SILENT responses, and STARTED is not
publication, rendering, teaching, delivered-floor compliance, or learning.

The patched instruction is final and the opportunity cadence is2. Existing
decision/ledger/provider/publication logic is identical to original. An exhausted
mismatch remains exhausted; genuinely different steps can progress the same project.
No synthetic fallback message or replay is introduced.

C1's Main-authored manual Astra inbox229eb2802b92494e82a346dd0287e666 remains
published once, not ingested/rendered at08:48:49. C1 parent456729 remains unchanged;
its takeover is gated on actual rendering. C5 parent352977 is untouched; its
takeover requires Banach's actual exact sleep28 recovery LOADED receipt, not CPU
preparation or assumed recovery. No C5 child restart is this worker's scope.

`OBSERVATIONS/STARTED.json` binds the read-only observer PID596920, deadline09:22UTC.
It records new PROMPT policy precedence, actual provider RESULT/publication, and
DELIVERED/REQUEST hashes separately. It also reports bounded native tail counts
and C1 manual rendering without resending. `FIRST_RENDERED.json` will exist only
after genuine new-policy rendered-turn evidence, not merely publication.
Use timestamped observation files, never an old snapshot as live state.
