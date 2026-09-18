---
{}
---

# Reward Model Overview

<!-- Provide a quick summary of what the model is/does. -->

The reward model is trained from the base model [mistralai/Mistral-7B-Instruct-v0.2](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2). 

The training script is available at https://github.com/WeiXiongUST/RLHF-Reward-Modeling .

Also see a short blog for the training details (data mixture, parameters...): https://www.notion.so/Reward-Modeling-for-RLHF-abe03f9afdac42b9a5bee746844518d0


## Model Details

If you have any question with this reward model and also any question about reward modeling, feel free to drop me an email with wx13@illinois.edu. I would be happy to chat!

### Dataset preprocessing

<!-- Provide a longer summary of what this model is. -->

The model is trained on a mixture of the following datasets. We also provide the mixture in [weqweasdas/preference_dataset_mixture2_and_safe_pku](https://huggingface.co/datasets/weqweasdas/preference_dataset_mixture2_and_safe_pku).
- [HH-RLHF](https://huggingface.co/datasets/Anthropic/hh-rlhf)
- [SHP](https://huggingface.co/datasets/stanfordnlp/SHP)
- [UltraFeedback](https://huggingface.co/datasets/openbmb/UltraFeedback)
- [Capybara](argilla/distilabel-capybara-dpo-7k-binarized)
- [HelpSteer](https://huggingface.co/datasets/nvidia/HelpSteer)
- [Orca](argilla/distilabel-intel-orca-dpo-pairs)

Difference between this mixture and the original dataset

- HH-RLHF: we only use the helpful subset and we delete the noisy samples where chosen_response == rejected_response;
- SHP: we only use the samples with score ratio > 2, for each prompt, we take 5 comparison at most, leading to 109526;
- Ultrafeedback: similar to UltraFeedback-Binarized, we use the fine-grained score instead of the overall one to rank samples. Meanwhile, for each prompt, we take all possible 6 pairs of comparisons. Finally, we delete the selected pairs with equal scores, leading to 267416.
- HelpSteer: we use the mean of helpfulness and correctness to rank samples. Meanwhile, we take all possible 6 pairs of comparisons. Finally, we delete the selected pairs with equal scores, leading to 21576;


### Training

We train the model for one epoch with a learning rate of 5e-6, batch size 512, cosine learning rate decay with a warmup ratio 0.03.



