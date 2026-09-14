# Stage2A full metadata integration — September 14, 2026 UTC

Builder-owned source integration; no new scientific result or GPU authorization.
This records actual failures as well as CPU passes. The mission remains active.
Initial evidence cut:02:25UTC. The final disposition below supersedes the
initial implementation/readiness statements; original failures remain recorded.

## Resource relay disposition

The queued Q0 occupancy relay is historical, not a reason to resurrect terminal
Q0/E0 or the superseded M1 proposal. The prior live node2 read at
2026-09-14T02:08:42.180461Z reported all eight GPUs at zero MiB, no compute
applications and no same-user CUDA_VISIBLE_DEVICES entries. The two persistent
unreadable environments belonged to systemd and sd-pam; a third PID disappeared.
This is a bounded snapshot, not a reservation or permanent availability claim.
This increment has made no GPU reservation, launch, kill or remote write.
GPUs3–7 remain untouched; independent source integration and the reduced-screen
reducer proceed without waiting for any Q0 result. Q0/E0 never supply authentic
lineage rows, weights or selection decisions.

Kepler's read-only 02:18–02:20Z preservation audit found no demonstrated missing
Builder-owned node1 payload within the documented scope. Existing baseline/delta
custody on node2 and newer Level1 capsules on VM/node3 are distinct evidence.
The full baseline union, freshness of all owners' data, a particular node2
resume environment and permanent off-lease storage are not certified. Node1
expires September14 23:14UTC; the September13 23:14UTC preservation target is
already past. Do not run migrate_node1_to_node2.sh blindly: it includes kills
and extraction into native output paths.

The 02:25Z pull advanced main to f2d92389. Its watcher entry supersedes the
earlier no-new-rsync observation: an incremental node1-to-node2 mirror started
02:22Z, with native log ~/mirror_incremental_20260914.log; verification is
pending. That report is not a completed content verification. Do not duplicate
the in-progress mirror or claim that the entire node is safely disposable.

## Implemented and tested

The separately named birth_full_v1 profile admits larger semantic objects only;
legacy defaults and public/target/field/hit bounds remain unchanged. Both source
scan APIs propagate and receipt the explicitly selected profile. The original
alias derivation, substring matching and every rejection category are unchanged.

Executed on VM with PYTHONDONTWRITEBYTECODE=1:

```
python3 -m unittest tests.test_composition_birth_stage2a_scan_inputs tests.test_composition_birth_stage2a_scan_profiles tests.test_composition_birth_stage2a_semantic_profiles tests.test_composition_birth_stage2a_scanner -q
Ran 96 tests in 20.356s — OK
python3 -m unittest tests.test_composition_birth_stage2a_inventory -q
Ran 4 tests in 5.803s — OK
```

The 96 includes the earlier 61 and 8-test subsets; do not add repeated runs.
The initial new-profile test invocation had two failed assertions because it
incorrectly expected a synthetic 5000-element alias list to scan clear. Inspection
showed numeric array-index aliases576/635/762 inside opaque public IDs. Tests
now preserve that rejection; no production matcher was changed to make them pass.

The new inventory adapter builds complete source metadata itself, then joins
semantic/future checks and mandatory finite typed-route matching at the same
source provenance and retained boundary. It does not accept fabricated metadata
or exemption receipts. The generic scanner's literal route list is unused
because the finite route matcher handles raw/normalized/compact registered
action, row, mixed and ordered-ID forms without enumerating cyclic paths. That
matcher remains mandatory; unknown prose is not certified safe. This is not
held/core, native-template or full scientific source qualification.

## Real integration failures, not model failures

The first complete p00/m0/CLOSED/SEEK object failed birth_full_v1's leaf bound
before matching. No field was dropped or packed differently to force passage.
The complete-envelope measurement remains in progress; capacity changes must
preserve schema/aliases and be prospectively recorded from measured sizes.

The p02/m0/CLOSED/SEEK object did fit and actually scanned:

| Quantity | Observed |
|---|---:|
| canonical bytes | 1661198 |
| nodes / scalar leaves / depth | 73783 / 56639 / 8 |
| protected roots | 12 |
| services / EVENT rows / ROUTE rows | 175 / 672 / 168 |
| effective edges / route transitions | 672 / 672 |
| role bindings / all targets | 3079 / 4 |
| candidate / disclosed / future IDs | 2232 / 48 / 2184 |
| aliases / rejected occurrences | 119580 / 18 |

Rejected values were246,545,632,722,goal,service,start. Registered typed-route
matching was clear. The combined result correctly remains rejected. These are
synthetic source fixtures, not training results, independent learner seeds or
evidence of successful learning.

Descartes' read-only review finds an occurrence-local opaque-ID receipt
technically defensible only with exact original source spans and allocation
provenance; source reconstruction alone does not authenticate semantic-independent
ID selection. It also flags an explicit acceptance-contract boundary because
legacy partial-ID regressions reject such hits. No proposed ID exemption is
implemented here, no identifiers are reselected, and no stricter failure is
silently promoted to clearance. Any successor repair needs an explicit scope,
preserved raw findings and tests; the no-ID-suffix lexer alone is not authority
to waive substring findings. Lowercase structural-key collisions are also
unresolved, not omitted from the inventory.

## Next executable seam

Dirac identified and is implementing the missing pure reduced BASE/D1 reducer
over existing runtime captures/scorers. BASE is a distinct state identity;
both readouts use stage D1 and paired logical seeds. The initial subset is
560 reserved slots, not necessarily560 physical generations. The existing
thresholds and single ATOM_LOCAL256-update fit remain unchanged. No full-matrix,
new gate, new fit or D2 launch is implied by a CPU reducer.

After complete source/checker disposition, native preparation must bind actual
model/tokenizer/runtime pins, templates/masks, initialization and device/deadline
state, then compose the existing actor/trainer/checkpoint/custody components.
Actual qualified reduced readout precedes authentic same-adapter two-SLEEP.
Formal final-paper C11 remains deferred. No approval request occurred here.

## Final disposition —02:43UTC

The complete metadata producer is implemented, not merely specified. All64cases
and512records were measured in four nonoverlapping CPU shards; each took
413.095–415.312seconds. Counts/owners/logs are preserved in
receipts_20260912/astra_stage2a_metadata_envelope_20260914_attempt1/ under the
astra_memos directory. The interrupted earlier single-process measurement and
earlier test receipts remain alongside the completed shards. The envelope
measurement performed zero whole-prefix matcher passes; it is not a512-scan
clearance claim. Worker53testsPASS156.545s and the later7profile checksPASS40.544s
are separate commands, with overlaps not added to the Main total.

Maxima:5870321bytes,260563nodes,200244leaves, depth8,422196aliases. Explicit
birth_full_v2 raises only the leaf ceiling to262144. Both original legacy and
birth_full_v1 defaults/limits remain intact, as do all schema bytes and aliases.
V1's256family-A overflow results are not relabeled as passing.

The optional source-occurrence repair is now implemented under its separate
prospective scope note. Main adjudicated the two reviewers' differing scope
readings: preserve old default behavior, add exact original-source attribution
only; no blanket ID exception or invented human ratification. Explicit opt-in
receipts only whole original shared keyword tokens and contained original ID
hits; all other categories remain independent. No native allocator provenance
is inferred. Boole found an actual terminal-token suffix issue: appending X
after original ACK or an ID could preserve a receipt. Main fixed candidate-side
token boundaries, added both regressions and preserved appended-copy rejection.
Boole closed this narrow finding by static inspection, not a native/source-wide
approval. Neither reviewer has certified the entire metadata schema or campaign.

The complete B fixture retains119580aliases; its18strict failures become exact
source receipts only when explicitly enabled. The largest A fixture
p29/m0/u3/CLOSED, with capacity v2 and the same explicit source attribution,
also passes combined semantic/future/typed-route source projection checks with
422196aliases. Native/held/core/provenance/scientific flags stay false. This is
two representative complete-object scans, not all512combined scans.

Main's final suite:153testsPASS106.249s, then one new largest-case integration
testPASS12.676s. These are154unique covered tests across those commands, not a
single154-test invocation. The preceding152-test run had one stale test asserting
that the newly registered v2 name was unknown; it now uses an actually unknown
name. Failed attempt1 and passing attempt2 logs are both preserved. Production
scanner behavior was not changed to make that stale assertion pass.

The reduced BASE/D1 pure reducer is implemented and Main independently reran
its21testsPASS10.076s before the combined suite. It replays only captured outputs,
verifies exact280-slot/state identities/seed pairing/driver joins, retains failures
and UNUSED reservations, and applies the preexisting integer thresholds. It does
not accept caller green flags as persisted-custody or model authority. The
typed_steps label uses upstream strict per-chain typing, not an executed STEP
count; v2 section17 is the source definition. No native dose has been admitted.

NEXT: assemble held core/checker envelopes using existing graph packet builders,
then bind independent allocator provenance and native preparation/conductor.
Two local source conventions still need explicit disposition: intervention
constructors contain only start-state services, so a complete-to-GOAL depth
cannot be borrowed from autonomous depth2; initially-reached CONTINUE lacks
an obvious first irreversible root/LEFT-RIGHT specialization. These are Builder
source tasks, not an external-owner wait. Preserve complete-core/signature
disjointness and the required null checks. After actual readiness, run reduced
BASE+D1 and immediately enter qualified authentic same-adapter two-SLEEP.
No GPU launch, reservation, kill, native model/tokenizer load, node1 write or
approval request occurred in this increment. The full mission remains incomplete.
