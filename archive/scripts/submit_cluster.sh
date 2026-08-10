#!/bin/bash
#SBATCH --job-name=dream-state
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# ---------------------------------------------------------------------------
# NVIDIA Colossus cluster submission script for Dream-State Learning experiments
#
# Usage:
#   sbatch submit_cluster.sh <config> <script> [args...]
#
# Examples:
#   sbatch submit_cluster.sh configs/base.yaml scripts/run_baselines.py --baseline naive_ft
#   sbatch submit_cluster.sh configs/base.yaml scripts/run_ablations.py --ablation full_system
#   sbatch submit_cluster.sh configs/base.yaml scripts/run_baselines.py \
#       --baseline ewc --ordering interleaved --seed 123 --output-dir outputs/baselines/
#
# Credentials (set in your shell before calling sbatch):
#   export HF_TOKEN=hf_...
#   export WANDB_API_KEY=...
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------- Positional arguments -------------------------------------------
if [[ $# -lt 2 ]]; then
    echo "ERROR: Usage: sbatch submit_cluster.sh <config> <script> [args...]" >&2
    exit 1
fi

CONFIG=$1
SCRIPT=$2
shift 2
EXTRA_ARGS=("$@")

# ---------- Modules -----------------------------------------------------------
module load cuda/12.1
module load python/3.10

# ---------- Environment -------------------------------------------------------
# Propagate credentials exported before sbatch was called.
# These variables are forwarded automatically when set in the submitting shell;
# the checks below surface a clear error rather than a silent auth failure.
if [[ -z "${HF_TOKEN:-}" ]]; then
    echo "WARNING: HF_TOKEN is not set. Hugging Face model downloads may fail." >&2
fi
if [[ -z "${WANDB_API_KEY:-}" ]]; then
    echo "WARNING: WANDB_API_KEY is not set. W&B logging will be disabled." >&2
fi

export HF_TOKEN="${HF_TOKEN:-}"
export WANDB_API_KEY="${WANDB_API_KEY:-}"

# Disable tokenizer parallelism warnings inside SLURM workers
export TOKENIZERS_PARALLELISM=false

# ---------- Working directory -------------------------------------------------
cd "${SLURM_SUBMIT_DIR}"

# Ensure project root is on PYTHONPATH so dream_state package is importable
export PYTHONPATH="${SLURM_SUBMIT_DIR}:${PYTHONPATH:-}"

# Create log directory if it doesn't exist (SLURM needs it before job starts,
# but guard here for safety)
mkdir -p logs

# ---------- Run ---------------------------------------------------------------
echo "============================================================"
echo "Job:        ${SLURM_JOB_NAME} (${SLURM_JOB_ID})"
echo "Node:       $(hostname)"
echo "Config:     ${CONFIG}"
echo "Script:     ${SCRIPT}"
echo "Extra args: ${EXTRA_ARGS[*]:-<none>}"
echo "Start time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

python "${SCRIPT}" --config "${CONFIG}" "${EXTRA_ARGS[@]:-}"

echo "============================================================"
echo "End time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"
