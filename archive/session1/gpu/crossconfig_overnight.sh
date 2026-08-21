#!/bin/bash
# Cross-config generalization (runs ON THE NODE): fresh worlds at UNSEEN
# generator configs, frozen head trained on the original depth-4 worlds.
# Pre-registered: graceful AUC degradation (high-0.8s+) + felt still beats
# surprise in S3 => salience is a property of value-training, not of the
# generator config. Cliff to ~0.5 => head learned generator quirks (report).
set -e
PY="$HOME/miniconda3/envs/felt/bin/python"
cd "$HOME/dream-state-learning"
export PYTHONPATH=.

for CFG in "xc_d3:--depth 3 --branching 3 --seed 101" \
           "xc_d5b4:--depth 5 --branching 4 --seed 202"; do
    NAME="${CFG%%:*}"; ARGS="${CFG#*:}"
    echo "=== [$NAME] rollouts ==="
    $PY gpu/rollouts.py --model Qwen/Qwen2.5-7B-Instruct --episodes 400 \
        --par 32 --max-steps 120 --n-worlds 2 $ARGS \
        --out "gpu_artifacts/$NAME" --skip-states
    echo "=== [$NAME] fact cache ==="
    $PY gpu/rollouts.py --model Qwen/Qwen2.5-7B-Instruct --cache-fact \
        --out "gpu_artifacts/$NAME"
    echo "=== [$NAME] frozen-head eval + salience dump ==="
    $PY gpu/train_head_fact.py --in gpu_artifacts/s1 \
        --eval-in "gpu_artifacts/$NAME" \
        --dump-salience "gpu_artifacts/salience_$NAME.npz"
    echo "=== [$NAME] S3 ==="
    $PY gpu/probe_eval_real.py --in "gpu_artifacts/$NAME" \
        --fact-salience-npz "gpu_artifacts/salience_$NAME.npz" \
        --out "gpu_artifacts/s3_$NAME.json"
done
echo "=== CROSS-CONFIG COMPLETE ==="
