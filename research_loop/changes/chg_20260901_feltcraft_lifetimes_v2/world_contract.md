# FeltCraft-Lifetimes exact CPU world contract v2

**Status:** proposal only. This contract defines a finite falsification
instrument; it does not establish model usability or authorize execution.

## 1. Registered finite population

```text
protocol_id = "feltcraft_lifetimes_cpu_v2"
super_seed q = integer 0..127 inclusive
twin b = 0 or 1
regime r = RANDOM or MOTIF
source instances e = 0..15
family f(e) = floor(e / 2)
cuts after instance counts = [2,4,8,16]
targets per cut/cell = A2:4, A3:4, S:4
```

All 128 super-seeds are included. There is no target/world rejection,
replacement, favorable seed selection, or variance resizing in CPU v2. Any
failed structural invariant invalidates the complete generator version.
Consequently the accepted-deck event is the constant `A=1`; posterior code
must still represent it explicitly.

## 2. Typed recipe template

```text
raw roles:          R0 R1 R2 R3
intermediate roles: I0 I1
top roles:          T0 T1

I0 <- R0 + R1
I1 <- R2 + R3
T0 <- I0 + R2
T1 <- I1 + R0
```

Descriptor pools are `DR0..DR3`, `DI0..DI1`, and `DT0..DT1`. Public type is
visible; role index and graph depth are not. Permutations are type preserving,
so the legal alignment space has `4! * 2! * 2! = 96` elements.

Every family `f=0..7` samples a type-preserving role-to-internal-slot
permutation `alpha[q,f,0]`. Twin 1 is:

```text
tau = (R0 R2)(R1 R3), with I0,I1,T0,T1 fixed
alpha[q,f,1](role) = alpha[q,f,0](tau(role))
```

`tau` is involutive, type preserving, and a non-automorphism of the labeled
template. It changes every decisive recipe/plan while preserving role counts,
topology, and shortest-path lengths.

Each source or target instance creates fresh internal slots and fresh opaque
public handles. Handle rendering is independently permuted from slot identity,
but the same rendered handle is used in all four matched cells. Hidden recipes
are induced from `alpha` and the fixed template.

## 3. Regime manipulation

For each `(q,f)`, sample one public descriptor-to-slot attachment
`delta_base[q,f]`, shared across twins.

- MOTIF source instances of family `f` use `delta_base[q,f]`.
- RANDOM source instances independently sample a type-preserving
  `delta_random[q,e]`.
- Every fresh S target instance uses `delta_base[q,f]` in both regimes.

Within `(q,b)`, RANDOM and MOTIF therefore have identical handles, sites,
hidden handle recipes, source action arguments, inventories, budgets, action
outcomes, and target correct actions. Descriptor attachments in source public
state are the only treatment. Target pre-action bytes are identical across
regimes and twins. Source bytes necessarily differ in descriptor fields; this
is the registered treatment, not an uncontrolled confound.

Methods see one cell only. They do not see `r`, `b`, paired-cell artifacts,
generator addresses, internal slots, or matching metadata.

## 4. Deterministic randomness and bytes

The 32-byte seed is big-endian unsigned `q` left-padded with zeros. A raw block
is:

```text
SHA256(
  ASCII("FCL2/RNG") || 0x00 ||
  seed32 ||
  u32be(len(namespace)) || ASCII(namespace) ||
  u32be(len(address_bytes)) || address_bytes ||
  u32be(draw_index)
)
```

`namespace` is one registered ASCII constant. `address_bytes` is RFC-8785/JCS
UTF-8 for a closed-key object with NFC strings and integers only. Lists have
declared semantic order. No floats, nulls, maps with unknown keys, timestamps,
filesystem paths, process IDs, or host entropy enter scientific generation.

`U(n)` reads the first big-endian 64-bit word and rejects values at or above
`floor(2^64/n)*n`, incrementing `draw_index`. Permutations use descending
Fisher--Yates with `U`. Handles are a public type prefix plus the first 96 PRNG
bits encoded as uppercase Crockford base32. Any handle collision invalidates
the protocol version, not an individual seed.

Every record is RFC-8785/JCS, NFC, UTF-8, with exactly one trailing LF. Hashes
cover the raw bytes. Golden vectors are required for `q in {0,1,127}` for RNG,
permutations, handles, tau, one source instance, every target family, and the
posterior certificate.

## 5. Public action kernel

Every action costs one step. Unknown handles or wrong types return
`INVALID_PUBLIC_ACTION`; hidden mismatch never returns that code.

```text
MOVE(site)
```

Moves to a declared site and returns the public raw handle present or `EMPTY`.

```text
GATHER(raw)
```

At the raw's site, adds one unit and returns `GATHERED`; otherwise returns
`NOT_PRESENT` without changing inventory.

```text
TRY_CRAFT(output,a,b)
```

Requires distinct declared ingredients present in inventory. Missing
inventory returns `MISSING_INPUT` without naming which input. Otherwise it
consumes one unit of both. The exact unordered hidden recipe returns `CRAFTED`
and adds the output; every other pair returns `INCOMPATIBLE`. No failure names
a correct ingredient, distance, role, edge, or partial match.

```text
STOP
```

Ends the episode. Success also ends it when all registered goal handles are in
inventory. Resets restore raw resources and clear location/inventory only;
they never change the hidden instance.

## 6. Open-loop source deck

Each full source instance has exactly 88 one-action reset episodes in this
order:

1. four `MOVE(site)` surveys in canonical site-handle byte order;
2. for each of the four public crafted-output handles in canonical byte order,
   all `C(7,2)=21` unordered ingredient pairs in canonical `(a,b)` byte order.

Each assay episode preloads exactly one unit of `a` and `b`, then executes one
`TRY_CRAFT(output,a,b)`. The collector never branches on observations. Thus
each instance has exactly four `CRAFTED` and eighty `INCOMPATIBLE` assay
outcomes plus four site observations. The complete source cuts contain exactly
`176,352,704,1408` action events.

Actions, action arguments, and outcome codes are byte-identical between
RANDOM and MOTIF within each twin. The collector cannot read descriptors,
hidden recipes, roles, target registries, scores, posterior state, or future
events. A taint test must show that changing only descriptor attachment leaves
the action sequence unchanged.

The immutable public log records typed pre-state, action, observation,
post-state, monotone event index, instance, family, and source scope. Hidden
state is used only by the transition function.

## 7. Targets

All target clones are disposable and read-only with respect to the life.
Evaluation actions/outcomes, calibration events, queries, paths, caches, and
RNG never enter later source or memory.

At cut `n`, define `e_old=0`, `e_new=n-1`, `f_old=0`, and
`f_new=floor(e_new/2)`.

### A2: exact constructive recall

Four targets are the Cartesian product of `{e_old,e_new}` and `{I0,I1}`.
Descriptors are omitted. The target begins at `NONE` with empty inventory and
budget 5. The unique shortest plan is two `MOVE/GATHER` pairs and one craft.

### A3: old+new constructive join

Four targets are `(T_old,T_new)` in `{T0,T1} x {T0,T1}` for instances
`e_old` and `e_new`. The goal requires both outputs. Inventories and namespaces
are separate but share one operation budget of 16. Each top output requires
exactly eight actions; no failed action is recoverable. This target requires
old and new lifetime relations in one plan.

### S: prospective sparse-instance schema

Four targets are `{f_old,f_new} x {T0,T1}`; if `f_old=f_new`, two distinct
fresh nuisance instance IDs are used. Before the decision snapshot, a fixed
item-local calibration performs four site surveys and all 42 assays for the
two intermediate output handles. No top-output recipe is assayed. The clone is
then reset and sealed with empty inventory and budget 8.

The target descriptor attachment is `delta_base[q,f]` in both regimes. Any
schema used by the tested memory must have been committed before target clone
creation. Target-time schema synthesis is a separately labeled leaked ceiling.
Calibration atoms may be used by the ATOM controller but are destroyed with
the clone.

Exact enumeration over all 96 type-preserving alignments, conditioned on the
legal lifetime prefix, calibration prefix, target bytes, and `A=1`, must show:

- MOTIF: the missing top recipe posterior is a point mass;
- RANDOM: the maximum posterior mass for the decisive recipe is exactly 1/4;
- other-instance descriptor evidence has zero conditional mutual information
  with the decisive recipe in RANDOM.

The 1/4 ambiguity is top-role identity (two possibilities) times the unresolved
raw identity within the relevant intermediate pair (two possibilities).

## 8. Target certificates and isolation

Every target independently requires:

- replayable hidden-oracle shortest-path success exactly 1;
- exact legal SOURCE success exactly 1 for A2/A3 and MOTIF-S;
- target-only, brute-force, passive-signature, and RANDOM SOURCE action value
  at most .35 where registered;
- byte-identical target pre-action records across all four cells;
- equal budgets, candidate counts, path lengths, and public grammar;
- twin decisive action/plan difference with tau round-trip;
- no source event matching the target state, goal, or complete plan.

Run-versus-skip evaluation must yield identical later source events, all
non-evaluation RNG counters, and a CPU suffix-state hash containing only the
source cursor/state, deck cursor, persistent controller fixture state, and
bound manifest hashes. Scientific DREAM, SLEEP, corpus, reader, tokenizer,
model, adapter, and optimizer state do not exist in CPU v2 and are not hashed.

## 9. What CPU v2 can establish

A passing receipt establishes only determinism, coupling, finite-world
identifiability, target solvability, exact leakage/headroom bounds, and
eligibility for a separately authorized known-good model gate. It cannot
establish learned dreaming, compiled-text value, LoRA transport, post-native
scaling, compression, baseline saturation, causal mediation, or the on-policy
flywheel.
