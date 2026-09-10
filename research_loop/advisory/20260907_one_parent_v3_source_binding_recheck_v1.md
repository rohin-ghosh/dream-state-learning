# One-parent headline v3 source-binding recheck v1

Date: 2026-09-07

Status: local, read-only integrity check. This grants no deliberation,
implementation, model/tokenizer, benchmark, adapter, external execution, GPU,
or claim authority.

The initialized v3 architecture-deliberation state contains 30 source
bindings: one directive plus the 29 workflow context files. Every path was
read from the current worktree and recomputed with SHA-256. Result:

```text
bindings checked: 30
mismatches:       0
```

Bound control-object receipts:

| object | SHA-256 |
|---|---|
| `research_loop/workflows/one_parent_child_headline_v3.deliberation.json` | `deb896c6a9aa96491c712d5d64f71a341e15d01fe4caf0aa82417c37053a7274` |
| `research_loop/changes/chg_20260907_one_parent_child_headline_v3/source_binding_manifest.json` | `18bcbe31550e4f31e90bdd445d20d017d43c17dd0a828ee34fca51b57262d186` |
| `.research_loop/intake/chg_20260907_one_parent_child_headline_v3.deliberation.state.json` | `1e69856fd3da8ba7f6b834b70c0aea0a1a0ab1687f5645765c09992b43c43a5c` |

The initialized state remains at `advocate_pending`, with zero attempts for
all five roles and `implementation_authorized=false`. The user's conceptual
agreement on the one-parent topology is bound in the directive, but it is not
silently promoted into permission to transmit the packet to external models.
That still requires explicit approval of these exact bytes.

Recheck logic:

```text
for each row in state.source_bindings:
    assert sha256(read(row.path)) == row.sha256
```

Any later source mismatch invalidates this receipt and must fail closed rather
than being repaired after deliberation begins.
