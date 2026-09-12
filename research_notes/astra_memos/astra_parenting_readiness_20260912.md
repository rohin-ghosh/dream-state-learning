# Provenance / parenting readiness sidecar — 2026-09-12

Read-only engineering audit. Started 06:15:40 UTC (September 11, 23:15 Pacific).
Only owned persistent output: this file. No repository edits, launch, SSH,
dependency installation, Git mutation, or external communication. Temporary
CPU-fixture directories are created under /tmp and removed on exit. No seven
archived checks were rerun. Other agents' changes are not reverted.

Inspected AGENTS.md, CLAUDE.md, launch §15, HANDOFF_2026-09-12.md, the archived
04:18 checkpoint and /tmp/astra_20260912_HANDOFF.md, plus relevant ancestry
notebook entries and the prior preschool read-only audit. Old STOP/ratification
requirements are superseded by §15; scientific invariants remain. This task's
explicit no-edit/no-launch restriction takes precedence over builder latitude.

## Decision and early blockers

**No currently verified clean fresh-base slot / lesson / sham trio.**
CompilerGym preschool is a disposable, task-exposed engineering scout, never
a clean nursery ancestor or H1 evidence. Fresh weights do not erase exposure.

1. **Ancestry is not fail closed.** run_life_v2.validate_adapter_states checks
   staging/verdict markers, not ancestry. run_life.latest_adapter trusts DONE.
   Fresh, unknown, quarantined and DEV_UNVERIFIED fixtures all reach a mocked
   model constructor; only fresh has adapter_path=None. No real model loads.
2. **Gate scores leak to agentic parents.** agentic_parent.ChildView's public
   gate_decisions tool returns candidate/base/floor for a supposedly disjoint
   gate panel. This violates §15 even when report scores are hidden. Existing
   test_agentic_parent_mock.py:335 positively expects this obsolete behavior.
3. **reasoning_gym preschool is not portable as implemented.** Its valid
   feedback `attempt 1: verifier score 1.00 (accepted)` becomes status=failure
   with no numerical facts in preschool.parse_outcome. The slot says
   Instructions before/after/reduction, records become no-measurement, and
   enforce cannot learn ordinary reasoning-gym records. The fixed lesson has
   real compiler passes; the target-blind prompt scanner finds them. The sham
   does not trigger this lexical scan, which is not proof of sourced ancestry.
4. **Lesson exclusion is routing, not a byte-level guarantee.** The compiler
   ignores raw kind=lesson rows, but an exact lesson example echoed into a
   child's thought preceding a win enters the compiled corpus verbatim.
   Prior corpus strings are also accepted without provenance validation.
5. **Record provenance is not verified.** A note_after with plausible embedded
   measurement but NO matching ACT is admitted by enforce (min_items=1 in the
   negative fixture, zero executions, one admitted record, training not skipped).
   ProvenanceLedger uses setdefault and accepts conflicting supplied gym/domain.
6. **Scan holes.** note_after.text is ignored by deployment scanning; the split
   guard also only checks act/thought/note, not note_after. A copied dirty
   artifact, contaminated sibling brief or shared society memory need not be
   caught by a clean-looking current ledger.
7. **Rank default is 16**, both runner and v1 trainer. Explicitly pass rank 8
   in every future launch and standalone trainer invocation. No rank-16
   matched-joint-test qualification was established here.

## Runnable routes and exact commands (PROPOSALS ONLY — NOT EXECUTED)

Current development-only route, from the node's existing ~/dream-state checkout
and ~/v2/venv; choose a genuinely new life directory and already-cleared GPU.
Lease, occupancy, CPU/provenance receipts and notebook logging remain builder
preconditions. The command below does not perform those gates itself.

```bash
CUDA_VISIBLE_DEVICES="$GPU" HF_HUB_OFFLINE=1 V6_MODEL=Qwen/Qwen2.5-7B-Instruct \
  "$HOME/v2/venv/bin/python" -m organism_v6.run_life_v2 \
  --life-dir "$HOME/v6_out/dev_preschool_slot_seed${SEED}_${RUN_ID}" \
  --gym compiler --arm B --seed "$SEED" --episodes 32 --sleep-every 32 \
  --probe-every 32 --budget-ticks 16 --wake-batch 8 --rank 8 \
  --note-after --note-after-max-tokens 100 --artifact-lesson none \
  --articulation-gate shadow --neutral-probes
```

For a later matched developmental trio, use separate fresh directories,
`--episodes 128 --probe-every 64` and artifact-lesson `none`, `lesson`, or `sham`;
all other parameters, seeds and measurement schedule matched. No dynamic
parent flags, clone group, bootstrap copy, plasticity, or report-based
`--probe-gate`. These are NOT three clean arms. The existing fixed lesson
violates the strict byte-exclusion guarantee when echoed; fix that before
claiming invariant compliance, even for a development lesson/sham comparison.
Shadow logs NOTE_AFTER but does not train those new records: legacy v1 sleep
trains pathways/anchors/principles from the other ledger rows. Do not describe
this route as a learned-record mechanism. Enforce is not a drop-in remedy.

Candidate nondeployment **slot plumbing only**, not presently a valid clean
preschool acquisition experiment, is:

```bash
CUDA_VISIBLE_DEVICES="$GPU" HF_HUB_OFFLINE=1 V6_MODEL=Qwen/Qwen2.5-7B-Instruct \
  "$HOME/v2/venv/bin/python" -m organism_v6.run_life_v2 \
  --life-dir "$HOME/v6_out/rg_slot_plumbing_seed${SEED}_${RUN_ID}" \
  --gym reasoning_gym --arm B --seed "$SEED" --episodes 32 --sleep-every 32 \
  --probe-every 32 --budget-ticks 16 --wake-batch 8 --rank 8 \
  --note-after --artifact-lesson none --articulation-gate shadow
```

Do not add the current lesson or default neutral probes to that candidate:
`preschool.NEUTRAL_PANEL_DEFAULT` contains compiler benchmark URIs, incompatible
with reasoning-gym IDs. A custom trait-only panel also needs split/ancestry
validation; numeric articulation remains unsupported. Reasoning gym configuration
is organism_v6/reasoning_gym_families.json and its birth text is
organism_v6/bootstrap_reasoning_gym.txt (verify actual constant below if renamed).
The runner has no --init-adapter option. Do NOT use
gpu/launch_bootstrapped_life.sh for fresh base: it copies an adapter into
sleep_0000/adapter, touches DONE and checks only the source TRAINED marker.

## Visibility, provenance and artifacts

- Parent brief mode receives training-thought samples, ritual metrics, previous
  brief and reflection handling; no direct probe reader was found there.
  Agentic mode is unsafe until gate score removal. Its report/neutral/final
  filenames are denied by the allow-list; symlink aliases resolving to a report
  filename are denied. This is path isolation, not proof arbitrary allowed
  content is untainted. Sibling summaries and society playbooks lack clean
  ancestry admission (agentic_parent.py:1080,1098,1170).
- Slot events have kind, episode_id, tick, execution_id, action, outcome,
  before/after/reduction/status and child text (preschool.py:221). Execution IDs
  omit visit index; repeated visits collide. Compiler standalone uses plain
  Ledger; trait/group ledgers stamp gym/exposure_domain (not source hashes).
- lesson_deliveries.jsonl records version, mode, phase and full text; it is not
  a sourced parent/person receipt. Idempotence keys only sleeps_done: a same-life
  mode change can deliver new bytes without a new receipt. New dirs per cell.
- Outputs: ledger.jsonl, lesson_deliveries.jsonl, sleep_0032/corpus.json,
  waking_brief.txt, articulation_shadow.json, articulation_state.json;
  enforce preserves corpus_legacy.json and may write
  SLEEP_SKIPPED_INSUFFICIENT_RECORDS. Compiler/trait probes use separate
  probe_*.ledger.jsonl; neutral probes use neutral_probe_pre/post_*.json and
  their own ledgers, not the life training ledger.
- Sleep train path is adapter.train -> adapter/CANDIDATE -> DONE or REJECTED_*.
  Candidate format canary is reloaded through VLLMBackend; final accepted path
  reload uses latest_adapter. DONE/REJECTED ambiguity is rejected, but a lone
  trainer/forged DONE with missing model bytes is not ancestry verification.

## Trainability and persistent reload

organism_v6/train_adapter.py:38-70 loads base anew for each cumulative refit,
uses PEFT LoRA q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj,
alpha=2r, dropout=.05, bias=none, AdamW over requires_grad parameters, default
3 epochs / lr 1e-4 / batch 4 / truncation 512, bare-text next-token loss with
padding masked. It does not continue the prior adapter optimizer. The intended
trainables are only lora_A/lora_B matrices on those modules; numerical count,
base freeze and gradient flow were NOT measured (torch/PEFT absent). No separate
note/parent weights or trainable base are intended. V6_MODEL can override both
backend/trainer model identities today; the ancestry boundary must bind the
allowed base snapshot and reject mismatches, not trust this environment variable.

Required real-weight check after dependencies/approval: enumerate trainable
names/count; assert all are intended LoRA matrices and base tensors are frozen;
record finite nonzero LoRA gradients and before/after tensor hashes; save and
close writer; reopen identical frozen snapshot + exact adapter in fresh process;
compare deterministic held-out logits/output and ON/OFF/second-reload behavior
with no lesson/brief/ledger retrieval. Bind tokenizer, model, adapter config,
weights, corpus, code, split, seed and inference settings to receipts. Changed
output alone is instrumentation, not H1. Controls must match settings/budget.

Existing neutral probe JSON caches are filename-only. A new CPU fixture proves
an old payload is returned unchanged with a different adapter argument: there
is no cached hash/config validation. This does not establish an actual run was
corrupted; it is a missing persistent-reload safeguard. Real model save/load
and behavioral persistence could not be tested here.

## Smallest proposed disjoint next assignment — NO implementation yet

**A: ancestry boundary (non-material invariant-enforcing repair).** Own only
new organism_v6/provenance.py and tests/test_ancestry_guard.py; coordinate one
small integration hunk in organism_v6/run_life_v2.py immediately after CLI
parsing and BEFORE directory/log mutation, parent initialization, gym/model
construction, or resume. Do not also edit preschool/compiler/parent modules.

Boundary contract: explicit clean-vs-development status, fresh-base birth or
admitted-resume receipt; never infer clean from missing tags, directory name,
empty scan results, TRAINED or DONE. Fresh base must have zero inherited
weights/rows/briefs/corpora/society inputs and bind base snapshot/runtime config.
Any existing nonempty life without a verified receipt refuses a clean/parented
entry. All inherited inputs require content-addressed, recursively verified
source receipts rooted in trusted recorded evidence; reject missing/invalid
receipts, cycles, missing sources, digest/config mismatches, unknown domains,
QUARANTINE_TASK_EXPOSED anywhere in closure, and unresolved
DEV_UNVERIFIED_PROVENANCE. Recheck canonical symlink targets and BOOTSTRAP_SOURCE,
not only local marker names. Verification must precede mount/use and bind the
bytes actually consumed. Write a birth/admission receipt atomically without
overwriting evidence. Use explicit runtime file list, not whole-tree Git SHA.

**Smallest safe first slice:** accept only an attested empty fresh-base trait
birth (and exactly bound resume if implemented); refuse ALL inherited adapter
and text/society inputs until recursive admission is ready. Keep development
scouts explicitly task-exposed, never reinterpret them as clean. A tiny check
for two marker filenames is insufficient and must not be called the guard.
The runner hook is mandatory; a standalone utility no caller invokes protects
nothing. Do not advertise a new guard CLI before it exists.

New focused CPU test proposal for A:
1. Fresh approved-base empty trait birth succeeds; compiler birth is development
   only; wrong model/rank policy or unexpected inherited files fail before any
   parent, subprocess or backend call.
2. Unknown DONE-only adapter; each quarantine/unverified marker; missing source;
   copied adapter after marker removal; invalid/tampered receipt; ancestor cycle;
   symlinked dirty ancestor; any digest mismatch all fail closed.
3. Dirty weights, rows, parent note, society/playbook, ranking or selection
   receipt each poison closure independently; an allegedly clean leaf cannot
   launder a dirty ancestor. Recursively verified trait-only chain succeeds.
4. Resume with same bytes/config succeeds; changed lesson/mode, base, corpus,
   ancestor, runtime file, adapter or split fails. Atomic receipt crash injection
   cannot leave something interpreted as admitted.

**Separate owners, disjoint implementations:** B owns agentic_parent.py and its
test file: remove score scalars AND raw score-bearing read paths, provide only
decision projection, include disjoint/unrecognized trait gate sentinel tests,
and ancestry-admit society/sibling sources. C owns preschool.py/batch_loop.py
and NEW preschool provenance tests: gym-neutral facts, visit IDs, actual ACT
join, lesson byte rejection, resume/config binding. D owns sleep_compile.py
and dedicated compiler evidence tests: reject unsourced replay/principles and
lesson echo across all corpus routes. Builder alone coordinates shared runner
hooks. A does not claim to fix B/C/D or authorize clean lesson launches.

## New CPU evidence — executable reproduction

The following probes assert observed safety behavior OR deliberately reproduce
unsafe behavior. `REPRODUCED` is a failing safety property, not a readiness pass.
No archived test functions or GPU/backend implementations are executed.

Exact command from /data/home/rohing/dream-state:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
report = Path('/tmp/astra_parenting_readiness_20260912.md').read_text()
source = report.split('```python\n', 1)[1].split('\n```', 1)[0]
exec(compile(source, 'parenting_readiness_cpu_probes', 'exec'))
PY
```

```python
import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from organism_v6 import agentic_parent, model_backend, preschool, run_life_v2, sleep_compile
from organism_v6.clone_coordinator import ProvenanceLedger

class ReachedBackend(Exception):
    pass

class StubGym:
    name = 'compiler'
    def training_schedule(self, *args):
        return []
    def gate_set(self):
        return None

for dependency in ('pytest', 'torch', 'peft', 'transformers', 'vllm', 'reasoning_gym'):
    print('DEPENDENCY', dependency, bool(importlib.util.find_spec(dependency)))

with tempfile.TemporaryDirectory(prefix='astra_parenting_cpu_', dir='/tmp') as directory:
    root = Path(directory)
    for marker in ('fresh', 'unknown', 'QUARANTINE_TASK_EXPOSED', 'DEV_UNVERIFIED_PROVENANCE'):
        life = root / marker
        life.mkdir()
        if marker != 'fresh':
            adapter = life / 'sleep_0000' / 'adapter'
            adapter.mkdir(parents=True)
            (adapter / 'DONE').write_text('ok')
            if marker != 'unknown':
                (life / marker).write_text('deny')
        seen = []
        def intercept(*args, **kwargs):
            seen.append(kwargs.get('adapter_path'))
            raise ReachedBackend()
        with patch.object(run_life_v2, 'make_gym', return_value=StubGym()), patch.object(model_backend, 'VLLMBackend', side_effect=intercept), patch('sys.argv', ['run_life_v2', '--life-dir', str(life), '--arm', 'B', '--rank', '8']), contextlib.redirect_stdout(io.StringIO()):
            try:
                run_life_v2.main()
            except ReachedBackend:
                pass
        assert len(seen) == 1
        assert (seen[0] is None) == (marker == 'fresh')
        print('PASS' if marker == 'fresh' else 'REPRODUCED', 'startup_' + marker)

    life = root / 'visibility'
    life.mkdir()
    sleep = life / 'sleep_0032'
    sleep.mkdir()
    (sleep / 'gate.json').write_text(json.dumps(dict(candidate=.314159, base=.271828, floor=.271828, score_ok=True, brevity_ok=True)))
    (life / 'probe_gate0032.json').write_text(json.dumps(dict(results={'gate/new': .314159}, mean=.314159)))
    view = agentic_parent.ChildView(str(life), rows=[], society_dir=str(root / 'society'))
    result = view.call('gate_decisions')
    assert '0.3142' in result and 'candidate' in result
    print('REPRODUCED gate_score_tool_exposure')
    for forbidden in ('probe_ep0064.json', 'neutral_probe_post_0032.json', 'final_test.json'):
        (life / forbidden).write_text('{"sentinel": 97531}')
        try:
            view.read_json(forbidden)
        except agentic_parent.ForbiddenRead:
            pass
        else:
            raise AssertionError(forbidden)
    (sleep / 'waking_brief.txt').symlink_to(life / 'probe_ep0064.json')
    try:
        view.read_text('sleep_0032/waking_brief.txt')
    except agentic_parent.ForbiddenRead:
        pass
    else:
        raise AssertionError('report alias exposed')
    print('PASS report_neutral_final_paths_and_alias_denied')

    facts = preschool.parse_outcome('attempt 1: verifier score 1.00 (accepted)')
    assert facts['status'] == 'failure' and facts['before'] is None
    print('REPRODUCED reasoning_success_misparsed')
    assert run_life_v2.leak_scan_ledger([dict(kind='thought', prompt=preschool.lesson_block('lesson', 0))])['hits']
    assert not run_life_v2.leak_scan_ledger([dict(kind='thought', prompt=preschool.lesson_block('sham', 0))])['hits']
    print('REPRODUCED lesson_compiler_exposure_sham_lexically_clear')
    assert not run_life_v2.leak_scan_ledger([dict(kind='note_after', text='CompilerGym LLVM -mem2reg')])['hits']
    print('REPRODUCED note_after_text_scan_bypass')

    lesson = preschool.LESSON_EXAMPLES[0]
    rows = [dict(kind='thought', episode_id='train/one', tick=1, note=lesson), dict(kind='act', episode_id='train/one', tick=1, action='-mem2reg', outcome='instructions 100 -> 80 (20.0% reduction)', score=.2)]
    compiled = sleep_compile.compile_sleep(lambda *args, **kwargs: '', rows, str(root / 'compile_echo'), [])
    assert any(lesson in text for text in compiled['corpus'])
    print('REPRODUCED exact_lesson_echo_in_sleep_bytes')
    compiled = sleep_compile.compile_sleep(lambda *args, **kwargs: '', [dict(kind='lesson', text=lesson)], str(root / 'compile_direct'), [])
    assert compiled['corpus'] == []
    print('PASS direct_lesson_row_not_compiled')

    life = root / 'orphan'
    life.mkdir()
    sleep = life / 'sleep_0032'
    sleep.mkdir()
    row = dict(kind='note_after', episode_id='train/one', execution_id='nonexistent', tick=1, status='success', action='-mem2reg', outcome='instructions 100 -> 80 (20.0% reduction)', text='I ran -mem2reg. Instructions went from 100 to 80, a 20.0% reduction.')
    result = preschool.gate_sleep([row], str(life), str(sleep), 'enforce', min_items=1)
    assert result['n_executions'] == 0 and result['n_admitted_new'] == 1 and not result['training_skipped']
    print('REPRODUCED orphan_record_enters_enforced_corpus')
    ledger = ProvenanceLedger(str(root / 'provenance.jsonl'), gym='reasoning_gym', exposure_domain='reasoning_gym:train')
    ledger.append(dict(kind='note_after', gym='forged', exposure_domain='clean', text='x'))
    assert ledger.rows()[0]['gym'] == 'forged'
    print('REPRODUCED supplied_provenance_overrides_stamp')

    life = root / 'resume'
    life.mkdir()
    preschool.deliver_lesson(str(life), 'lesson', 0)
    delivered = preschool.deliver_lesson(str(life), 'sham', 0)
    receipts = [json.loads(line) for line in (life / 'lesson_deliveries.jsonl').read_text().splitlines()]
    assert len(receipts) == 1 and receipts[0]['mode'] == 'lesson' and delivered != receipts[0]['text']
    print('REPRODUCED changed_lesson_mode_unrecorded')
    cached = {'sentinel': 'old-adapter-hash'}
    Path(preschool.neutral_probe_path(str(life), 'post', 32)).write_text(json.dumps(cached))
    backend = object()
    result, reloaded = preschool.neutral_probe(backend, None, str(life), 'post', 32, 1, [], 16, lambda *args: None, '/different/adapter')
    assert result == cached and reloaded is backend
    print('REPRODUCED stale_neutral_cache_ignores_adapter_identity')
print('COMPLETE 16 probes; PASS=3; REPRODUCED=13; no GPU/scientific claim')
```

## Receipt

Initial inspected HEAD: a45baa2f77437a35e51ebe1034bf1c70deea4233. Source hashes:

- run_life_v2.py: 1ec9190162788c825d480f0d8ec4b40b574afe0a4bf313e72f245155b6e9c582
- preschool.py: 24a52274ce7b28890fd41114a1a81a41d3c6d7af9baa1954aa29c43267510fd1
- sleep_compile.py: 73879a6c7da41be11cb9419182d8ca52ca07071b3b7a34b02ce5f793c163cb18
- agentic_parent.py: 209e4bc19b95de87f98cbc9085058d348830e5192f336a84282bda2abcbcd98a

Execution result and final status to be filled after the embedded probes run.
