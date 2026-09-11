#!/bin/bash
# Pretest P1 — write A/B/C on ONE GPU from ONE finished life (PRETESTS_2026-09-11 P1; Astra memo 1 2.4).
# Cells (defaults; every one is a knob below):
#   A       = P1's literal W0: the recorded sleep_<N>/corpus.json (held-out ids filtered by the compile) trained
#             with the FROZEN v1 trainer (train_adapter.py: bare-text loss, lr 1e-4, 3 epochs, bsz 4, max_len 512,
#             no seed). WRITE_AB_A_TRAINER=v3 trains A with the v3 trainer instead.
#   A_v3    = the same A corpus through the v3 trainer at B's settings (rank / lr / epochs / seed / max-len) — the
#             matched-TRAINER comparator (Astra memo 2.4: identical base, optimizer).
#   B       = two-scale + neighbourhood write (sleep_compile_v3: episode windows sized in tokens + local views),
#             every child chunk a target, gym lines masked, no filter, no principles.
#   Bs      = scale 1 alone (episode view only; P1's W1s cell, decision rule ii).
#   B_match = B drawn down to A's supervised-token budget (--token-budget = A's target tokens; newest rows in
#             full, the rest uniform — mechanism 2.3), so the write is also compared at MATCHED tokens.
#   C       = TMEM-format QA pairs (deterministic extraction; outputs = the child's NOTEs, EXECUTED moves,
#             reflections), v3 trainer with the chat template at B's settings.
#   C_tmem  = the C pairs with TMEM's LoRA shape and optimizer settings (r=6 on gate/up/down of the last 4 layers,
#             SVD-init frozen A, SGD 5e-4, 5 epochs, batch 16, alpha=r so Delta = B A, dropout 0). NOT the paper's
#             schedule (one offline pass, not per-trigger online SFT) — every deviation is named in C's compile
#             manifest (params.tmem_deviations) and in the trainer manifest note.
#   OFF     = the frozen model; brief = frozen + the life's FINAL brief (gpu/brief_baseline.sh output, referenced);
#   brief_mid = frozen + sleep_<N>/waking_brief.txt (the horizon-matched text-memory cell, probed HERE).
# Training defaults = P1's primary cell: rank 32, lr 1e-4, 1 epoch, max length 7,168, seed 0; every adapter and
# OFF probed on the 8-panel and the disjoint panel (2 seeded reps, gen seed 4242, budget 16). After each v3
# training the manifest is checked: target tokens dropped must be 0 and packing must be block4d_by_group
# (isolated); WRITE_AB_STRICT=1 turns the warnings into failures.
#   Output: $OUT/<life>/{corpora,adapters,probes,summary.json,table.md,estimate.json,timings.jsonl}.
# Usage (on a node, from ~/dream-state):  bash gpu/write_ab.sh <gpu> <life_dir> [max_episodes=512]
# Knobs (env): WRITE_AB_OUT (~/v6_out/pretest_write_ab) WRITE_AB_CELLS (A,B,C) WRITE_AB_A_TRAINER (v1 | v3)
#   WRITE_AB_A_V3 (1) WRITE_AB_SCALE1 (1 = Bs) WRITE_AB_MATCH (1 = B_match) WRITE_AB_TMEM (1 = C_tmem)
#   WRITE_AB_BRIEF_MID (1) WRITE_AB_RANK (32) WRITE_AB_LR (1e-4) WRITE_AB_EPOCHS (1) WRITE_AB_SEED (0)
#   WRITE_AB_A_LR (1e-4) WRITE_AB_A_EPOCHS (3) [the v1 trainer's own recipe for the literal W0 cell]
#   WRITE_AB_MAXLEN (7168) WRITE_AB_REPS (2) WRITE_AB_GEN_SEED (4242) WRITE_AB_BUDGET (16)
#   WRITE_AB_TOKENIZER (auto = $V6_MODEL from the HF cache; none = chars/3 estimates) WRITE_AB_LOCAL_TOKENS (768)
#   WRITE_AB_OVERLAP_TOKENS (1024) WRITE_AB_TOKEN_BUDGET (0 = whole corpus for B) WRITE_AB_BRIEF_DIR
#   (~/v6_out/brief_baseline) WRITE_AB_PROBE_OFF (1) WRITE_AB_STRICT (0) WRITE_AB_DRY (1 = print only)
# Idempotent: every step leaves a marker under $OUT/<life>/markers and is skipped on rerun.
set -u
G="${1:?gpu index}"; LIFE="${2:?life dir}"; MAXEP="${3:-512}"
cd ~/dream-state || exit 1
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python
LIFE="${LIFE%/}"; L=$(basename "$LIFE")
OUT="${WRITE_AB_OUT:-$HOME/v6_out/pretest_write_ab}/$L"
CELLS="${WRITE_AB_CELLS:-A,B,C}"; TMEM="${WRITE_AB_TMEM:-1}"; A_V3="${WRITE_AB_A_V3:-1}"
SCALE1="${WRITE_AB_SCALE1:-1}"; MATCH="${WRITE_AB_MATCH:-1}"; BRIEF_MID="${WRITE_AB_BRIEF_MID:-1}"
RANK="${WRITE_AB_RANK:-32}"; LR="${WRITE_AB_LR:-1e-4}"; EPOCHS="${WRITE_AB_EPOCHS:-1}"; SEED="${WRITE_AB_SEED:-0}"
MAXLEN="${WRITE_AB_MAXLEN:-7168}"; REPS="${WRITE_AB_REPS:-2}"; GEN_SEED="${WRITE_AB_GEN_SEED:-4242}"; BUDGET="${WRITE_AB_BUDGET:-16}"
A_TRAINER="${WRITE_AB_A_TRAINER:-v1}"; BRIEF_DIR="${WRITE_AB_BRIEF_DIR:-$HOME/v6_out/brief_baseline}"
TOKENIZER="${WRITE_AB_TOKENIZER:-auto}"; LOCAL_TOKENS="${WRITE_AB_LOCAL_TOKENS:-768}"
OVERLAP_TOKENS="${WRITE_AB_OVERLAP_TOKENS:-1024}"; TOKEN_BUDGET="${WRITE_AB_TOKEN_BUDGET:-0}"
STRICT="${WRITE_AB_STRICT:-0}"; DRY="${WRITE_AB_DRY:-0}"
mkdir -p "$OUT"/{corpora,adapters,probes,markers}
echo "[write_ab] life=$L gpu=$G max_episodes=$MAXEP cells=$CELLS a_trainer=$A_TRAINER a_v3=$A_V3 scale1=$SCALE1 match=$MATCH tmem=$TMEM brief_mid=$BRIEF_MID rank=$RANK lr=$LR epochs=$EPOCHS seed=$SEED max_len=$MAXLEN tokenizer=$TOKENIZER out=$OUT"

step() { # step NAME cmd...  (marker + wall-clock into timings.jsonl)
  local name="$1"; shift
  if [ -f "$OUT/markers/$name" ]; then echo "[write_ab] skip $name"; return 0; fi
  echo "[write_ab] $name: $*"
  if [ "$DRY" = 1 ]; then return 0; fi
  local t0=$(date +%s)
  "$@" > "$OUT/$name.out" 2>&1; local rc=$?
  local dt=$(( $(date +%s) - t0 ))
  echo "{\"step\": \"$name\", \"seconds\": $dt, \"rc\": $rc}" >> "$OUT/timings.jsonl"
  if [ $rc -ne 0 ]; then echo "[write_ab] FAIL $name rc=$rc (see $OUT/$name.out)"; tail -20 "$OUT/$name.out"; return $rc; fi
  touch "$OUT/markers/$name"; echo "[write_ab] done $name in ${dt}s"
}
warn_or_fail() { # message
  echo "[write_ab] WARNING $1"
  if [ "$STRICT" = 1 ]; then echo "[write_ab] WRITE_AB_STRICT=1: stopping"; exit 3; fi
}
check_compile() { # cell: token measure exact? head present? leak refused?
  local m="$OUT/corpora/$1/compile_manifest.json"
  [ -f "$OUT/corpora/$1/LEAK_REFUSED" ] && { echo "[write_ab] $1: LEAK_REFUSED (parent/brief text in the spans; see $OUT/corpora/$1/LEAK_REFUSED)"; exit 4; }
  [ -f "$m" ] || return 0
  $P - "$m" "$1" <<'EOF' || warn_or_fail "compile check failed for $1 (see above)"
import json, sys
m = json.load(open(sys.argv[1])); cell = sys.argv[2]; bad = []
if m.get("token_measure_kind") != "exact": bad.append(f"token_measure={m.get('token_measure')} (windows sized by estimate; pass WRITE_AB_TOKENIZER=<name/path>)")
c = m.get("conditioning") or {}
if c.get("items_head_missing"): bad.append(f"head_missing items={c['items_head_missing']} instances={c['instances_head_missing']} (no stored prompt: the local view has no GOAL/METRIC)")
if m.get("max_item_tokens", 0) > int(m.get("params", {}).get("max_seq_tokens") or 10**9): bad.append(f"max_item_tokens={m['max_item_tokens']} > max_seq_tokens")
print(f"[write_ab] {cell}: items={m.get('n_items')} target_tokens={m.get('est_target_tokens')} total={m.get('est_tokens_total')} max_item={m.get('max_item_tokens')} measure={m.get('token_measure')} exposures={m.get('effective_exposures')} truncation={m.get('truncation')}")
for b in bad: print("[write_ab]   -", b)
sys.exit(1 if bad else 0)
EOF
}
check_train() { # cell: no target tokens dropped; packing isolated when requested
  local m="$OUT/adapters/$1/train_manifest.json"; [ -f "$m" ] || return 0
  $P - "$m" "$1" <<'EOF' || warn_or_fail "train check failed for $1 (see above)"
import json, sys
m = json.load(open(sys.argv[1])); cell = sys.argv[2]; bad = []
tr = m.get("truncation") or {}; pk = m.get("packing") or {}; iso = (pk.get("isolation_check") or {}).get("verdict")
if tr.get("target_tokens_dropped"): bad.append(f"target_tokens_dropped={tr['target_tokens_dropped']} (the compile-time 'each target once' guarantee is void)")
if (m.get("config") or {}).get("pack") and pk.get("mode") != "block4d_by_group": bad.append(f"packing={pk.get('mode')} isolation={iso} (fell back to one item per sequence)")
print(f"[write_ab] {cell}: steps={m.get('steps')} target_tokens={(m.get('tokens') or {}).get('target')} total={(m.get('tokens') or {}).get('total')} tok/s={m.get('tokens_per_s')} train_s={m.get('train_seconds')} packing={pk.get('mode')} isolation={iso} items_split={tr.get('items_split')} truncation={tr}")
for b in bad: print("[write_ab]   -", b)
sys.exit(1 if bad else 0)
EOF
}
train_v3() { # cell corpus extra-args...
  local cell="$1" corp="$2"; shift 2
  step "train_$cell" env CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.train_adapter_v3 --corpus "$corp" --out "$OUT/adapters/$cell" \
    --rank "$RANK" --lr "$LR" --epochs "$EPOCHS" --seed "$SEED" --max-len "$MAXLEN" --manifest-note "cell $cell" "$@" || exit 1
  check_train "$cell"
}

# 0. the disjoint panel as a JSON list (probe_adapter --panel wants a list file)
PANEL="$OUT/panel_v1.json"
if [ ! -f "$PANEL" ] && [ "$DRY" != 1 ]; then
  if [ -f ~/v6_out/disjoint_panel/panel_v1.json ]; then cp ~/v6_out/disjoint_panel/panel_v1.json "$PANEL"
  else $P -c "import json;json.dump(json.load(open('research_notes/disjoint_panel_v1.json'))['panel'],open('$PANEL','w'))"; fi
fi

# 1. corpora from the SAME rows (held-out gate/exam ids excluded per row; horizon = first MAXEP episode instances;
#    windows sized in tokens so nothing is truncated by the trainer; leak scan refuses parent/brief text)
SLEEP="$LIFE/sleep_$(printf %04d "$MAXEP")"; REC="$SLEEP/corpus.json"; RECARG=()
[ -f "$REC" ] && RECARG=(--recorded-a "$REC") || echo "[write_ab] no recorded corpus at $REC: A is compile_sleep with --think none (no principles, no brief)"
COMPILE_COMMON=(--ledger "$LIFE/ledger.jsonl" --gym compiler --exclude-panels default --max-episodes "$MAXEP" --think none
  --tokenizer "$TOKENIZER" --max-seq-tokens "$MAXLEN" --window-overlap-tokens "$OVERLAP_TOKENS" --local-context-tokens "$LOCAL_TOKENS" --life-dir "$LIFE")
step compile $P -m organism_v6.sleep_compile_v3 "${COMPILE_COMMON[@]}" --out "$OUT/corpora" --variants "$CELLS" --token-budget "$TOKEN_BUDGET" ${RECARG[@]+"${RECARG[@]}"} || exit 1
IFS=',' read -ra CELL_ARR <<< "$CELLS"
for C in "${CELL_ARR[@]}"; do check_compile "$C"; done
if [ "$SCALE1" = 1 ] && [[ ",$CELLS," == *",B,"* ]]; then
  step compile_Bs $P -m organism_v6.sleep_compile_v3 "${COMPILE_COMMON[@]}" --out "$OUT/corpora" --variants B --views episode --cell-name Bs --token-budget "$TOKEN_BUDGET" || exit 1
  check_compile Bs
fi
if [ "$MATCH" = 1 ] && [[ ",$CELLS," == *",A,"* ]] && [[ ",$CELLS," == *",B,"* ]]; then
  if [ -f "$OUT/corpora/A/compile_manifest.json" ]; then
    TA=$($P -c "import json;print(int(json.load(open('$OUT/corpora/A/compile_manifest.json'))['est_target_tokens']))")
    echo "[write_ab] B_match: B drawn to A's supervised-token budget = $TA target tokens"
    step compile_B_match $P -m organism_v6.sleep_compile_v3 "${COMPILE_COMMON[@]}" --out "$OUT/corpora" --variants B --cell-name B_match --token-budget "$TA" || exit 1
    check_compile B_match
  else echo "[write_ab] B_match skipped: no A manifest (DRY run or A not compiled)"; fi
fi

# 2. GPU-hour estimate from the corpus sizes (exact tokens when the compile had the tokenizer; assumed 1200 tok/s)
step estimate $P -m organism_v6.write_ab_report estimate --corpora "$OUT/corpora" --epochs "$EPOCHS" --reps "$REPS" --out "$OUT/estimate.json" || exit 1
[ -f "$OUT/estimate.json" ] && echo "[write_ab] estimate: $(grep -o '"total_gpu_hours": [0-9.]*' "$OUT/estimate.json") (C_tmem at 5 epochs and the A/A_v3 cells are extra; see estimate.json per cell)"

# 3. adapters
ALL_CELLS=()
for C in "${CELL_ARR[@]}"; do
  CORP="$OUT/corpora/$C/corpus.json"
  if [ -f "$OUT/corpora/$C/EMPTY_CORPUS" ]; then echo "[write_ab] $C: EMPTY_CORPUS (no write — logged, not a failure)"; continue; fi
  if [ "$C" = A ]; then
    ACORP="$OUT/corpora/A/legacy/corpus.json"   # the recorded (or compiled) exemplars, held-out ids filtered, v1-shaped
    if [ "$A_TRAINER" = v1 ]; then
      # P1's literal W0: the frozen v1 trainer (bare-text loss, bsz 4, max_len 512, no seed) at ITS recipe
      # (lr 1e-4, 3 epochs by default; WRITE_AB_A_LR / WRITE_AB_A_EPOCHS give P1's W0 (5e-5, 2) cell)
      step train_A env CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.train_adapter --corpus "$ACORP" --out "$OUT/adapters/A" \
        --rank "$RANK" --lr "${WRITE_AB_A_LR:-1e-4}" --epochs "${WRITE_AB_A_EPOCHS:-3}" || exit 1
      ALL_CELLS+=(A)
      if [ "$A_V3" = 1 ]; then train_v3 A_v3 "$CORP"; ALL_CELLS+=(A_v3); fi
    else
      train_v3 A "$CORP"; ALL_CELLS+=(A)
    fi
  elif [ "$C" = C ]; then
    train_v3 C "$CORP" --chat-template; ALL_CELLS+=(C)
  else
    train_v3 "$C" "$CORP"; ALL_CELLS+=("$C")
  fi
done
for X in Bs B_match; do
  [ -f "$OUT/corpora/$X/corpus.json" ] && [ ! -f "$OUT/corpora/$X/EMPTY_CORPUS" ] || continue
  train_v3 "$X" "$OUT/corpora/$X/corpus.json"; ALL_CELLS+=("$X")
done
# 3b. C_tmem: TMEM's LoRA shape and optimizer settings on the C pairs (Sec. 5.1 / 3.2 of arXiv 2606.04536);
#     alpha = r (scaling 1.0, Delta = B A as in eq. 7), dropout 0; the schedule (one offline pass) is ours.
if [ "$TMEM" = 1 ] && [ -f "$OUT/corpora/C/corpus.json" ] && [ ! -f "$OUT/corpora/C/EMPTY_CORPUS" ]; then
  step train_C_tmem env CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.train_adapter_v3 --corpus "$OUT/corpora/C/corpus.json" --out "$OUT/adapters/C_tmem" \
    --rank 6 --alpha 6 --dropout 0 --target-modules gate_proj,up_proj,down_proj --layers last4 --svd-init --svd-scale sigma --freeze-a \
    --optimizer sgd --lr 5e-4 --epochs 5 --batch-size 16 --no-pack --chat-template --max-len 2048 --seed "$SEED" \
    --manifest-note "C_tmem: TMEM LoRA shape (r=6 FFN last4, SVD-init frozen A, alpha=r, dropout 0) + SGD 5e-4 x 5 epochs x batch 16; DEVIATIONS: one offline pass over all pairs of the horizon (TMEM: per-trigger online SFT within an episode), EOS as a target token, chat template + answer-only loss (TMEM: NOT FOUND), max-len 2048 and the seed are ours" || exit 1
  check_train C_tmem; ALL_CELLS+=(C_tmem)
fi

# 4. probes: adapter ON per cell, OFF, and the mid-life brief, on both panels, 2 seeded reps
probe() { # tag adapter(optional) panel(optional) brief(optional)
  local tag="$1" ad="$2" pn="$3" bf="${4:-}"; local o="$OUT/probes/$tag.json"
  local args=(--out "$o" --reps "$REPS" --gen-seed "$GEN_SEED" --budget-ticks "$BUDGET")
  [ -n "$ad" ] && args+=(--adapter "$ad"); [ -n "$pn" ] && args+=(--panel "$pn"); [ -n "$bf" ] && args+=(--brief-file "$bf")
  step "probe_$tag" env CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter "${args[@]}"
}
for C in "${ALL_CELLS[@]}"; do
  AD="$OUT/adapters/$C"; [ -f "$AD/DONE" ] || { echo "[write_ab] no adapter for $C (skipped)"; continue; }
  probe "${C}_report" "$AD" ""; probe "${C}_disjoint" "$AD" "$PANEL"
done
if [ "${WRITE_AB_PROBE_OFF:-1}" = 1 ]; then probe OFF_report "" ""; probe OFF_disjoint "" "$PANEL"; fi
if [ "$BRIEF_MID" = 1 ]; then
  if [ -f "$SLEEP/waking_brief.txt" ]; then
    BF="$SLEEP/waking_brief.txt"; [ -f "$SLEEP/parent_brief.txt" ] && BF="$BF,$SLEEP/parent_brief.txt"
    probe brief_mid_report "" "" "$BF"; probe brief_mid_disjoint "" "$PANEL" "$BF"
  else echo "[write_ab] brief_mid MISSING: no $SLEEP/waking_brief.txt"; fi
fi

# 5. the FINAL-brief text-memory cell (brief_baseline.sh output, referenced, not re-run)
for tag in report disjoint; do
  b="$BRIEF_DIR/${L}_brief_$tag.json"
  [ -f "$b" ] && echo "[write_ab] final-brief cell $tag: $b $(grep -o '"mean": [0-9.]*' "$b" | tail -1)" \
              || echo "[write_ab] final-brief cell $tag MISSING: run 'bash gpu/brief_baseline.sh $G' (writes $b)"
done

# 6. table: every cell, OFF, brief, brief_mid; ritual metrics from the probe ledgers; tokens / steps / GPU-hours measured
CELL_LIST=$(IFS=,; echo "${ALL_CELLS[*]:-$CELLS}")
step summarize $P -m organism_v6.write_ab_report summarize --out-dir "$OUT" --life "$LIFE" --brief-dir "$BRIEF_DIR" --cells "$CELL_LIST" || exit 1
rm -f "$OUT/markers/summarize"   # always re-summarise on rerun (cheap; picks up late brief cells)
[ -f "$OUT/table.md" ] && cat "$OUT/table.md"
echo "WRITE_AB_DONE $OUT"
