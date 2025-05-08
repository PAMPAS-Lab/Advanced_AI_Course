# GRPO实验项目

这个项目包含了使用GRPO技术对Qwen2.5-3B模型进行微调的完整实验代码和数据。

## 项目简介

GRPO是一种基于奖励函数的强化学习方法，用于优化语言模型的输出以满足特定要求。本项目利用GRPO技术在GSM8K数学问题上对Qwen2.5-3B模型进行了微调，使模型能够按照指定格式（XML标记）输出推理过程和答案。

## 文件结构

- **Qwen2.5_3B_GRPO_modelscope.ipynb**：完整的实验代码，包括模型加载、数据准备、GRPO训练和评估等
- **GRPO_reward.xlsx**：记录了不同奖励函数设置下的训练结果和性能指标

## 主要功能

1. **多种奖励函数设计**：
   - 正确性奖励（correctness_reward_func）：根据答案是否正确提供奖励
   - 整数奖励（int_reward_func）：检查答案是否为整数
   - 格式奖励（strict_format_reward_func、soft_format_reward_func）：检查输出是否符合XML格式要求
   - XML计数奖励（xmlcount_reward_func）：根据XML标签使用的正确性提供部分奖励

2. **模型微调与训练**：
   - 基于Unsloth框架加速训练
   - 使用GRPO算法对模型进行强化学习训练
   - 支持多种训练参数配置

3. **评估与结果分析**：
   - 对微调前后的模型性能进行对比评估
   - 分析不同奖励函数对模型行为的影响

## 技术要点

- **基础模型**：Qwen2.5-3B
- **微调技术**：GRPO (Generative Reward Proximal Optimization)
- **加速框架**：Unsloth
- **数据集**：GSM8K数学问题集
- **输出格式**：XML格式的推理过程和答案

## 使用方法

1. **环境配置**：
   ```bash
   pip install unsloth vllm
   pip install --upgrade pillow
   ```

2. **下载模型**：
   ```bash
   git lfs install
   git clone https://www.modelscope.cn/Qwen/Qwen2.5-3B-Instruct.git
   ```

3. **运行Notebook**：
   在支持GPU的环境中运行Qwen2.5_3B_GRPO_modelscope.ipynb文件

## 实验结果

通过GRPO训练，模型学会了：
1. 按照XML格式输出推理过程和答案
2. 提高了数学问题的解答准确率
3. 增强了模型对指定格式的遵循能力

详细的实验结果和性能指标可以在GRPO_reward.xlsx文件中查看。

## 参考资料

- [GRPO论文](https://arxiv.org/abs/2404.08793)
- [Unsloth框架](https://github.com/unslothai/unsloth)
- [Qwen2.5模型](https://github.com/QwenLM/Qwen2.5)

## 注意事项

- 实验需要较大的GPU内存（至少16GB）
- 完整训练可能需要数小时，根据GPU性能有所不同
- 可以通过调整batch_size和num_generations参数来适应不同的硬件环境
