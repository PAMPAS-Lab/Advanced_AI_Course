# HIAS高级人工智能课程

本仓库包含HIAS高级人工智能系统课程的各种实验和示例代码，旨在帮助学习者深入理解现代人工智能技术，特别是大型语言模型和注意力机制等核心概念。

## 仓库结构

本仓库包含以下主要模块：

### 1. Lab_GRPO
GRPO实验，包含：
- `GRPO_reward.xlsx`: GRPO奖励数据
- `Qwen2.5_3B_GRPO_modelscope.ipynb`: 使用Qwen2.5 3B模型进行GRPO实验的Jupyter笔记本

### 2. Lab_LLMs_Represent_Space
大语言模型空间表示实验，研究LLM如何理解和表示空间信息。

### 3. Demo_Self_Attention
自注意力机制示例代码：
- `multihead_self_attention_demo.py`: 多头自注意力机制的Python实现
- `self_attention.ipynb`: 自注意力机制的详细教学笔记本

### 4. Demo_nanoGPT_Poetry
基于nanoGPT的中文古诗生成项目：
- 包含完整的模型训练代码、配置文件和示例数据
- 实现了基于Transformer架构的诗歌生成系统
- 提供了多个Jupyter笔记本用于模型缩放研究和Transformer参数配置

### 5. Reference_Agent
Reference Agent：用于学术论文引用核查与文献下载的智能体。
- 主要文件结构：
  - `reference_agent/agent.py`：核心代理逻辑
  - `reference_agent/utils.py`：工具函数
  - `reference_agent/app.py`：应用入口（预留Web界面）
  - `reference_agent/prompts/`：提示词模板
  - `examples/`：示例目录

## 使用方法

每个实验目录包含独立的代码和数据，可以按照以下步骤运行：

1. 进入相应的实验目录
2. 对于Jupyter笔记本(.ipynb文件)，使用Jupyter Lab或Notebook打开
3. 对于Python脚本，直接使用Python解释器运行

## 环境需求

- Python 3.8+
- PyTorch 1.12+
- Jupyter
- 其他依赖项（请参考各实验目录中的说明）

## 学习资源

本仓库的实验和示例是高级人工智能课程的实践部分，建议结合课程讲义和相关理论学习材料一起使用，以获得最佳学习效果。

## 贡献

欢迎通过Issue或Pull Request提出改进建议或贡献代码。 
