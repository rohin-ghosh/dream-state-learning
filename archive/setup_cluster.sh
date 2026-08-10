#!/bin/bash
set -e
echo "Setting up Dream-State Learning environment..."

# Install conda env (assumes conda available)
conda create -n dream-state python=3.10 -y
conda activate dream-state

# Install alfworld (text mode)
pip install alfworld[full]
alfworld-download

# Install AI2-THOR
pip install ai2thor

# Install project
pip install -e ".[dev]"

# Download embedding model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

# Download base LLM (requires HF_TOKEN)
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
tok = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', token=os.environ['HF_TOKEN'])
print('Tokenizer downloaded successfully')
"

echo "Setup complete! Run: python scripts/run_baselines.py --config configs/base.yaml --baseline frozen_episodic"
