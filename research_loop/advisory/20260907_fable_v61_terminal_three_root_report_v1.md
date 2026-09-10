# Fable v6.1 terminal three-root report v1

Date: 2026-09-07

Status: exploratory, post-hoc, read-only analysis of completed legacy
CompilerGym artifacts. No model, tokenizer, compiler, adapter, benchmark,
process, or GPU operation was launched, stopped, or changed by this analysis.
This report supports no confirmatory parenting, continual-learning, discovery,
or superiority claim.

## Bottom line

All three sleep-v2 roots reached episode 1,024 and have complete paired
adapter-on and adapter-off probe artifacts at all sixteen checkpoints from
episode 64 through 1,024.

The terminal result is a stability--plasticity failure distribution:

- roots 0 and 1 finish above their contemporaneous adapter-off probes and
  have positive lifetime AUC differences, but concentrate almost completely
  on one supplied six-pass routine and plateau rather than continue improving;
- root 2 suffers a typed-interface collapse, finishing far below adapter off
  even though prior post-hoc extraction showed that useful compiler-action
  content remained in its prose; and
- the resulting terminal mean is negative while the median is positive.
  Reporting only either summary would hide the mechanism.

The defensible result is therefore that repeated LoRA writes can strongly and
persistently alter action selection, sometimes transporting a useful taught
procedure and sometimes destroying the executable action channel. This run
does not establish that the architecture learns better over lifetime.

## Exact terminal endpoints

The registered strict parser and saved best-of-panel scores give:

| root | adapter on | adapter off | on - off | on actions | on dominant share | off actions | fixed first-action delta |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `0.523262` | `0.486184` | `+0.037078` | 163 | 161/163 (`98.8%`) | 62 | `+0.063425` |
| 1 | `0.529087` | `0.470193` | `+0.058894` | 156 | 145/156 (`92.9%`) | 71 | `+0.067999` |
| 2 | `0.051111` | `0.485945` | `-0.434834` | 1 | 1/1 | 75 | `-0.408726` |

Across the three roots, terminal on-minus-off has mean `-0.112954`, median
`+0.037078`, two positive roots, and one negative root. With only three
exploratory roots and one catastrophic channel failure, neither a t interval
nor a pooled positive-effect claim is meaningful.

The adapter-on dominant terminal routines in roots 0 and 1 were respectively:

```text
-mem2reg,-sroa,-gvn,-simplifycfg,-licm,-instcombine
-mem2reg,-sroa,-gvn,-simplifycfg,-instcombine,-constprop
```

Both extend the four-pass opening explicitly supplied in the birth prompt.
Their value is compatible with reinforcement and cross-program transport of a
taught routine; it is not evidence of novel strategy discovery.

## Lifetime summaries

Normalized trapezoidal AUC over the sixteen paired checkpoints is:

| root | on AUC | off AUC | on - off | positive / negative checkpoints |
|---:|---:|---:|---:|---:|
| 0 | `0.510645` | `0.477639` | `+0.033005` | 15 / 1 |
| 1 | `0.519027` | `0.472473` | `+0.046554` | 16 / 0 |
| 2 | `0.183621` | `0.474366` | `-0.290745` | 2 / 14 |

At fixed best-of-first action caps over all 48 paired checkpoints, the
on-minus-off means for caps 1/2/4/8/16 are respectively
`-0.060701/-0.057438/-0.062206/-0.067432/-0.068639`; the corresponding
medians are `+0.027956/+0.030553/+0.028402/+0.024267/+0.024057`.
Thirty-three to thirty-five of 48 pairs are positive, but root 2's large
post-collapse negatives dominate every mean. This rules out a universal
action-volume explanation while reinforcing, rather than resolving, the
between-root instability.

## Saved-corpus channel evidence

At the first sleep, all three cumulative corpora had strict `ACT:` marker
fractions of `1.0`. At sleep 1,024 the fractions were:

| root | strict / all ACT-like lines | strict fraction | decorated lines | hash-prefixed lines |
|---:|---:|---:|---:|---:|
| 0 | 1261 / 1343 | `0.938943` | 82 | 34 |
| 1 | 1005 / 1149 | `0.874674` | 144 | 0 |
| 2 | 352 / 1449 | `0.242926` | 1097 | 354 |

Root 2's terminal corpus therefore contains a qualitatively different action
dialect. Together with the earlier strict-parser versus post-hoc permissive
extraction assay, this localizes the catastrophic registered-score failure to
self-reinforcing serialization drift. It does not rescue the endpoint: the
world accepts typed actions, not prose that a later analyst can reinterpret.

## Causal and scope limits

This legacy run cannot answer the one-parent/one-child paper question:

1. Generation and training realizations were not fully seeded or
   common-random across paired probes.
2. Each nominal 1,024-episode life repeated only 67 unique programs 15--16
   times.
3. Arm B received waking briefs during life; the adapter-off probe isolates a
   mounted adapter at a B-history checkpoint, not a never-learning twin.
4. The exact live prompt ancestry is incomplete because source files changed
   beneath long-lived processes and thought rows lack the needed prompt bytes.
5. The writer trained all tokens of bare compiled prose rather than exact
   native response continuations and had no typed-interface canary.
6. The useful opening was present in the birth prompt, so transport cannot be
   relabeled as invention.
7. The fixed-action analysis, corpus-dialect analysis, and lifetime AUC were
   defined post hoc and are mechanism diagnostics only.

The result does justify three prospective gates already present in the
one-parent design: native-response writer validation, separate proposal and
routing endpoints, and a commit canary that rejects an adapter which damages
the typed action interface. It also supports treating independent roots as
the unit of uncertainty and requiring directional benefit within roots before
large confirmatory spending.

## Reproducer

Read-only analyzer SHA-256:
`6eea666a0de0e34bcf1655acfe7d3be84a76bcb48fc39ba589982f63e55a633b`.

```text
python3 research_loop/advisory/analyze_fable_v61_probe_actions.py \
  --root /localhome/local-rohing/v6_out --compact-final
```

The script excludes episode zero because those probes used the pre-context-fix
harness. It reads only complete adapter-on/off ledger pairs and saved sleep
corpora.

## Terminal artifact receipts

Remote root: `/localhome/local-rohing/v6_out`.

| root | artifact | SHA-256 |
|---:|---|---|
| 0 | `probe_ep1024.json` | `05c4d55efec3f6d9a9981749a26b3adc260c3044db1a5470b0f51d4014a7a13b` |
| 0 | `probe_ep1024.ledger.jsonl` | `7069bcdb5d81b964194d8cd954a59e77058337d19e4f5aacf5af6892ac88290b` |
| 0 | `probe_ep1024_adapterOFF.json` | `e1c8f53b15e4943de636b1f8d591f6e57a15efc8ed0747675fda51481aee96eb` |
| 0 | `probe_ep1024_adapterOFF.ledger.jsonl` | `8344b774fe52d36ba215b4cc14f19380d21746a41f68a7e01f753f72e89e83b2` |
| 0 | `sleep_1024/corpus.json` | `d0abb341df83a81e5ec694cf7efd4aefa923cd53e1bea4af7782e84b9282a73d` |
| 0 | `sleep_1024/adapter/adapter_config.json` | `74d63dacee7bec50a010526a145eb6a6fe065008cf33f4e9cb8caeaac1b874ff` |
| 0 | `sleep_1024/adapter/adapter_model.safetensors` | `cd47e6987244d9999b95b24932b3268c6c8452024b2581133537e51ef8d75137` |
| 1 | `probe_ep1024.json` | `3657745de874af988ca89c3ab81ac62e033d591fa4bd4fd864ee6962e48261e0` |
| 1 | `probe_ep1024.ledger.jsonl` | `86c6616aea7c303d37752d41152cae71431a73e56c2b95c6553ce83cfca779c1` |
| 1 | `probe_ep1024_adapterOFF.json` | `3c4c7df8ec32d2fe8d1b7bdb6e3cb9f2940f1685d9ffc3136af069d0584781c6` |
| 1 | `probe_ep1024_adapterOFF.ledger.jsonl` | `028b4ce4ffff28bf8defd42c5a45d89f80004904b79fe99446ce39ef89fb3fa4` |
| 1 | `sleep_1024/corpus.json` | `77057a5e4da688b84c0651d608afc861c1210fa4f0e67a1c043385b12a75695a` |
| 1 | `sleep_1024/adapter/adapter_config.json` | `f3b0fb8edf5651da464ef188d028c27cc21d4824980ceebae112ddc9f50b8228` |
| 1 | `sleep_1024/adapter/adapter_model.safetensors` | `a90a977b8192184691024eba696f2d14508c7c08815a24c5881c757ad4ef0655` |
| 2 | `probe_ep1024.json` | `d18037533e31c89da3dadc0afd52e51f89d3c18868ca0d93fa54015eb8d20cdf` |
| 2 | `probe_ep1024.ledger.jsonl` | `b5c4758ac4f0a871a15a7c1c2f632a50e704461d8146e3d057b7ba16e089fb00` |
| 2 | `probe_ep1024_adapterOFF.json` | `a84662e5cde59417e48015d06eb29ebefa69d414af4de1f3bbb877bf7a2c9ff2` |
| 2 | `probe_ep1024_adapterOFF.ledger.jsonl` | `60dd667a933c7ff0954033759c6bb5987dc7edede6b68ed95402b86465d9077b` |
| 2 | `sleep_1024/corpus.json` | `50d4289c6c065d75d4ac97a24b45f222ed5a9716f78b2c0728b1e6071550150f` |
| 2 | `sleep_1024/adapter/adapter_config.json` | `e195bf37283aeccd5568687be383e4b9a8b05b8ad823520d9754d71fd85368f6` |
| 2 | `sleep_1024/adapter/adapter_model.safetensors` | `856ae03cbc7f2932f074090873a06d707d6df981475ed965e38cbae7082bf3e0` |

The earlier source/runtime ancestry, collapse recovery, and control audit is
`20260906_fable_v61_longrun_independent_audit_v1.md`. Episode-704 and
episode-960 follow-ups are retained as contemporaneous partial reports rather
than overwritten.
