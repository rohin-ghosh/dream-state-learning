# G1 control-validity and governance-context recovery

Date: 2026-09-04
Status: architecture-change evidence; not ratification or execution authority

## Why the first amendment is not sufficient

The unratified `chg_20260904_rml_g1_control_ceiling_repair_v1` correctly repairs
the structural-capacity claim, but deliberately preserves the original
empirical `P ATOMS_REC = 0/2` stop rule.  Exact capacity analysis now proves
that one deterministic policy over the complete authorized visible history can
legitimately solve one of the two P sides.  A pinned model result of `1/2` can
therefore be capacity-attaining without leakage.  Treating it as failure would
be a false stop caused by the invalid structural premise that created the old
threshold.

The capacity result is independently supported by the complete-success-trace
compatibility construction in
`chg_20260904_rml_g1_control_ceiling_repair_v1/policy_certifier_design.md`:
`K_NONE = 1/4` and `K_P_ATOMS = 1/2`.  Production still needs the executable
certificate and independent checker specified there.

## Missing original context bytes

The original G1 architecture-change artifacts bind
`rml_d0/stage_a_report.json` at SHA-256
`346bd091e9d037b1e51c8ed735ba5ecfbee50a42d10988d02ebc28c87532855b`.
Those exact bytes are not present in the repository or the searched local
temporary review copies.  The sole committed/current report is SHA-256
`e36be91f7244dd483a274a1cf350e383011a707d053a02fe753c6f982e9b47c0`.

This is consistent with a generated-receipt drift: the report transitively
hashes `gate_values.resource_record`, whose `wall_ms` and `peak_rss_bytes`
change on each otherwise identical CPU run, and stores the resulting
`resource_hash`.  It is not legitimate to silently substitute the current
file for the missing bound bytes.

This change therefore re-grounds the G1 decision in the current exact D0 code,
the current exact report, and a stable semantic projection.  The projection is
defined as canonical JSON after deleting exactly:

```text
/gate_values/resource_record
/resource_hash
```

from the current report.  Its SHA-256 is
`c496535e08b72d9eb1ff0ba8f6bca4b1f42545a855a6d368e479e99a76a12b0d`
and its byte length is `110366`.  A checker must recompute both values and must
reject any other exclusion.  Volatile resource receipts remain preserved and
reported, but cannot serve as the stable semantic context identity.

Current exact D0 authorities are:

```text
rml_d0/world.py        7b3911dac851c9c1614287e2af7f46c6a656ae26c4e24a9c172b70f2fb91eb52
rml_d0/targets.py      d0430a3b999d4429f1895973a33f487cd2e8978d6f460ffbfd1c1156f4528406
rml_d0/planner.py      6cf63009ba50c4f29d50f9e47d83d52395c184a8e24b48be4671d491443fe812
rml_d0/source.py       89c3bde38e93f26e198dccaf2c2040a3d9e94b4c2dd9a031581fdb97fdc3797f
rml_d0/run_cpu_gate.py 40f8322434f23343379ffac8caa9e8e26accb74da41993edcc5a535ebc4f23d4
```

Fresh interpretations and review must evaluate these available bytes rather
than claiming to have replayed the missing report.

## Narrow proposed empirical repair

Keep the two registered P ATOMS trajectories and all typed validity rules.
Require both to be `SCIENTIFIC_VALID`.  Interpret their exact observed success
count as:

- `0/2`: strict control-clean;
- `1/2`: capacity-attaining qualified control, permitted to proceed;
- `2/2`: impossible under the certified shared visible-policy capacity and
  therefore a predeclared stop for leakage, determinism, runtime, or
  certificate investigation.

Retain P GOLD `2/2`, total GOLD `4/4`, NONE at most `1/4`, every
AUTH/SHAM/CUT/TWIN requirement, the exact 18-trajectory roster, 234 registered
opportunities, no retries, all resource limits, and the single-fixture claim
firewall.  `1/2` is not credited as evidence for the proposed memory; it is
merely not allowed to invalidate a construct gate whose control has exact
capacity `1/2`.

No target, condition, prompt, or threshold may change after any scientific
call.  This repair is prospective: zero G1 scientific calls have occurred.
