### Reward Modeling
You can use the following command to finetune a reward model. Since generating humorous texts typically is not in the training dataset of public reward model, we need to finetune the reward model ourselves.
```
python humor_reward_modeling.py --dataset_dir /your/dataset/dir/ --model_name weqweasdas/RM-Mistral-7B --run_name rm --do_train  --do_eval --output_dir /your/output/dir/ --max_steps 5000
```
You can also choose custom reward model from [reward bench](https://[REDACTED_HOST]/spaces/allenai/reward-bench) to finetune different reward models.


## Download Checkpoints
Since the finetune procedure can take from 1 day up to a week on an A100, we provide all model checkpoints for finetuned models. Model checkpoints can be found [here](https://[REDACTED_HOST]/drive/folders/1udogiALKZ-3JDGsvWKXu7F6VcnckcDMr?usp=sharing).It incluces: 
- `reward`
- `sft`
- `dpo`
- `ppo`
- `llava_sft`

