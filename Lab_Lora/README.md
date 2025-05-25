# Lora微调实验项目

这个项目包含了使用Lora技术对Qwen1.5-0.5B-Chat模型进行微调的完整实验代码和数据。

## 项目简介

Lora（Low-Rank Adaptation）是一种高效的大语言模型微调技术，通过在预训练模型的线性层中插入低秩矩阵来实现参数高效微调。本项目使用MS-Swift框架对Qwen1.5-0.5B-Chat模型进行Lora微调，使模型能够更好地处理天气查询相关的对话任务。

## 文件结构

- **25年Lora微调更正（终稿）.ipynb**：完整的实验代码，包括环境配置、模型加载、Lora微调训练和效果测试等
- **train-weather.jsonl**：天气查询对话训练数据集，包含1110条训练样本
- **README.md**：项目说明文档

## 主要功能

1. **环境配置与依赖安装**：
   - 下载并安装MS-Swift框架
   - 配置相关依赖包
   - 更新transformers库

2. **模型微调与训练**：
   - 基于MS-Swift框架进行Lora微调
   - 使用天气查询对话数据集进行训练
   - 支持多种训练参数配置和优化

3. **效果对比与评估**：
   - 微调前后模型性能对比
   - 天气查询任务的响应质量评估
   - 模型在特定领域任务上的改进效果分析

## 技术要点

- **基础模型**：Qwen1.5-0.5B-Chat
- **微调技术**：Lora (Low-Rank Adaptation)
- **训练框架**：MS-Swift
- **数据集**：天气查询对话数据集（1110条样本）
- **任务类型**：多轮对话、工具调用、天气查询

## 使用方法

1. **环境配置**：
   ```bash
   pip install unsloth vllm
   pip install --upgrade pillow
   ```

2. **下载模型**：
   ```bash
   git clone https://github.com/modelscope/ms-swift.git
   cd ms-swift
   pip install -e .
   ```

3. **运行Notebook**：
   在支持GPU的环境中运行Qwen2.5_3B_GRPO_modelscope.ipynb文件

## 实验结果

通过Lora微调训练，模型在天气查询任务上的表现得到了显著提升：
1. 更准确地理解用户的天气查询意图
2. 正确调用天气API并处理返回结果
3. 生成更自然、更符合用户期望的回复
4. 在保持模型通用能力的同时，增强了特定领域的表现

## 参考资料

- [MS-Swift框架](https://github.com/modelscope/ms-swift)
- [Lora论文](https://arxiv.org/abs/2106.09685)
- [Qwen1.5模型](https://modelscope.cn/models/Qwen/Qwen1.5-0.5B-Chat)

## 注意事项

- 实验需要较大的GPU内存（至少16GB）
- 完整训练可能需要半小时到一小时，根据GPU性能有所不同
- 可以通过调整batch_size和gradient_accumulation_steps参数来适应不同的硬件环境
- 训练过程中会自动保存checkpoint，可用于模型推理和进一步微调
