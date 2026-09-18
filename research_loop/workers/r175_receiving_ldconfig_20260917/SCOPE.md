# R175 — non-material receiving CPU harness repair

Main's explicit user scope, September 17, 2026: preserve R173/R174 unchanged;
copy the R174 harness here with a fresh create-only R175 scratch/latch, add only
the exact read-only `/sbin/ldconfig -p` subprocess permission, test locally,
then execute ONE new actual CPU-only receiving attempt via `gpu/ovx2_ssh.sh`.
No automatic retries or repeating consumed attempts. Preserve all failures.

The sole added subprocess permission is the exact absolute executable and
argument vector `/sbin/ldconfig`, `-p`, resolving to a verified root-owned,
non-group/world-writable system binary. Use an explicit clean child environment
and standard PATH. No shell=True or shell-command permission, alternate flag/path, gcc, ld, compiler/linker
fallback, arbitrary subprocess, signal, network, provider, model, GPU job,
learner state mutation, or lifecycle operation is authorized. The R174 exact
`uname -p` permission is inherited unchanged, not broadened. Record all allowed
and denied operation metadata; never record inherited environment secrets.

A bounded read-only wrapper preflight may inspect the canonical ldconfig
metadata/hash and installed ctypes invocation code. Because the node's ldconfig
is a 387-byte script, one additional exact-script/target inspection is needed
before treating that command as harmless. These are not candidate attempts,
do not run ldconfig, and write nothing remotely. The candidate run
gets a distinct create-only scratch and one local consumed-attempt latch.

Observed command chain: `/sbin/ldconfig` resolves to `/usr/sbin/ldconfig`, a
387-byte root-owned mode0755 script, SHA256 `bfd5df90c7f070feab584435f106f254ffffaa268a04de5b5c3bd61d59c092f3`.
With the one literal `-p` argument its zero-argument dpkg-trigger branch is not
entered; the script execs `/sbin/ldconfig.real "$@"`. That resolves to the
1,051,280-byte root-owned mode0755 ELF `/usr/sbin/ldconfig.real`, SHA256
`aa6de6d24c9223de013f6294c1db270c0c5247741a35127a0e058bf386725666`.
Both paths/hashes are reverified before each permitted probe. Calling the
`.real` binary directly is not permitted by the Python subprocess allowance.
The child environment is exactly PATH=/usr/bin:/bin, LC_ALL=C, LANG=C; no
loader/package-manager/inherited secret environment reaches this probe.

All R174 source/test/fixture pins and limits remain unchanged: guard `8bbb6c...`,
native `cdb542...`, actual plain-context `b3859e...`, 1,854 original Python files
plus only the three frozen R168 runtime helpers. Preserve all 85 test methods
and assertions. R174's two pinned suffix helpers remain separately identified
negative-test support outside candidate source, never learner/runtime additions.
No newer plain-context, STARTUP, model weights, saved-life state, journals or
evaluator artifacts are read/copied. The original bound-input reader remains
64 MiB total / 2 MiB per input; optional Torch uses only the existing tiny CPU
optimizer test, not a model. Candidate inventory/library reads are separate
from that existing bound-input counter.

This repairs the CPU harness only. It changes no scientific claims, recipe,
learner visibility, numerical assertions, ownership or admission requirements.
No GO, handoff, assembly approval, wall/lease change, human-ratification artifact,
or Main assembly/coordination write is authorized. Godel must independently
review the actual result; author-side CPU success is not that review.
