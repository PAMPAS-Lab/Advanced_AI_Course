# 古诗词 nanoGPT

基于nanoGPT架构的中国古诗词生成模型，包含模型训练、可视化展示及交互式生成功能。

## 项目概述

本项目基于Andrej Karpathy的nanoGPT框架，专门针对中国古诗词数据进行训练，构建了一个能够生成古诗词的语言模型。项目特色在于不仅实现了古诗词的生成功能，还开发了基于Streamlit的可视化界面，使用户能够直观地观察Transformer模型内部的注意力机制和token生成过程。

### 主要特点

- 使用nanoGPT架构训练古诗词生成模型
- 字符级别的tokenization，适合中文古诗词处理
- 使用Streamlit构建交互式可视化界面
- 直观展示模型内部的注意力矩阵和多头注意力机制
- 实时可视化token生成概率分布
- 支持自定义输入进行诗词续写生成

## 安装与环境配置

```bash
# 克隆项目
git clone https://github.com/yourusername/nanoGPT-Poetry.git
cd nanoGPT-Poetry

# 安装依赖
pip install torch numpy transformers datasets tiktoken wandb tqdm streamlit plotly
```

## 项目结构

```
├── data/                     # 数据目录
│   └── shakespeare_char/     # 字符级别的古诗词数据
│       ├── combined_poetry.txt # 古诗词原始文本
│       ├── train.bin         # 训练数据
│       ├── val.bin           # 验证数据
│       ├── poetry_meta.pkl   # 词汇表元数据
│       └── prepare.py        # 数据预处理脚本
├── config/                   # 配置文件目录
│   └── train_shakespeare_char.py  # 训练配置
├── out-shakespeare-char/     # 模型输出目录
│   └── poetry_ckpt.pt        # 训练好的古诗词模型
├── model.py                  # 增强版GPT模型定义
├── ori_model.py              # 原始GPT模型定义
├── train.py                  # 训练脚本
├── sample.py                 # 文本生成脚本
├── test_sample.py            # 带详细输出的生成测试脚本
├── GPT_show.py               # Streamlit可视化界面
└── README.md                 # 项目文档
```

## 使用方法

### 数据准备

如需使用自己的古诗词数据集：

```bash
# 将你的古诗词文本放入combined_poetry.txt文件
python data/shakespeare_char/prepare.py
```
运行后会生成训练train.bin和测试test.bin

### 训练模型

```bash
# 使用默认配置进行训练
python train.py config/train_shakespeare_char.py

# 自定义参数训练
python train.py config/train_shakespeare_char.py --batch_size=32 --n_layer=8 --n_head=8 --n_embd=512
```

### 下载预训练模型

你可以从以下百度云链接下载预训练的模型权重：

```
链接：https://pan.baidu.com/s/11tCOCI_gmzi_MLDSR4NzTg?pwd=ai2a
提取码：ai2a
```

下载完成后，请将模型文件（poetry_ckpt.pt）放置在项目根目录的 `out-shakespeare-char` 文件夹中。如果该文件夹不存在，请手动创建。

### 生成古诗词

```bash
# 使用训练好的模型生成古诗词
python sample.py --out_dir=out-shakespeare-char --start="白玉为堂金作马" --num_samples=5
```

### 启动可视化界面

```bash
# 启动Streamlit可视化界面
streamlit run GPT_show.py
```

## 可视化界面功能

项目的核心亮点是提供了基于Streamlit的可视化界面，让用户能够直观理解Transformer模型的工作原理：

1. **参数设置**：用户可以设置输入提示语、调整温度参数、选择Top K值等
2. **注意力可视化**：展示模型各层、各头的注意力矩阵(Q、K、V、Attention Weights)
3. **概率分布**：显示下一个token的预测概率分布
4. **生成控制**：逐步生成并可视化每个token的生成过程
5. **Transformer教程**：内置Transformer模型的教程资源

## 模型架构

本项目使用的是基于Transformer的GPT架构：

- 6层Transformer层
- 6个注意力头
- 384维隐藏状态
- 字符级别的tokenization
- 添加了详细中间状态输出的功能，便于可视化分析

## 模型代码差异

本项目包含两个模型文件：`model.py`（增强版）和`ori_model.py`（原始版），主要差异如下：

### 1. 注意力机制（CausalSelfAttention类）
- 增强版添加了`return_details`参数，可返回Q、K、V矩阵和注意力权重等中间计算结果
- 增强版改进了因果掩码（causal mask）处理逻辑，支持动态处理超出预定义大小的序列
- 增强版简化了注意力计算，专注于可视化所需的中间状态

### 2. Transformer块（Block类）
- 增强版采用更模块化的结构，分别存储注意力层和MLP层的输入输出
- 增强版添加了`return_details`参数，可返回每个模块的中间计算结果
- 增强版保留了每一步的残差连接计算结果，便于可视化分析

### 3. GPT模型前向传播（forward方法）
- 增强版始终计算所有位置的logits，原始版在推理时仅计算最后位置的logits
- 增强版添加了详细的中间状态输出，包括每层的输出和下一个token的预测概率分布
- 增强版设计了层次化的返回结构，便于可视化界面提取并展示模型内部状态

这些增强功能主要是为了支持`GPT_show.py`中的可视化界面，使用户能够直观地观察模型内部的计算过程，特别是注意力机制的工作原理。这些修改不影响模型的基本功能和生成能力，但大大提高了模型的可解释性和教学价值。

## 示例输出

输入提示：`白玉为堂金作马`

生成结果：
```
白玉为堂金作马，
黄金为殿玉为堂。
高楼十二青云里，
楼上琼花一夜香。
```

## 未来计划

- 增加更多古诗词数据集
- 优化模型参数和训练方法
- 添加更多可视化功能
- 支持多种诗词风格的生成控制
- 实现在线部署与分享

## 致谢

- 感谢Andrej Karpathy提供的[nanoGPT](https://github.com/karpathy/nanoGPT)框架
- 感谢[chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)仓库提供的中华诗词数据库，本项目的训练过程是先将该仓库的数据进行筛选合并，再经过后续训练流程
- 可视化界面部分参考了[bbycroft的LLM可视化](https://bbycroft.net/llm)

---

# Chinese Ancient Poetry nanoGPT

A Chinese ancient poetry generation model based on the nanoGPT architecture, including model training, visualization, and interactive generation features.

## Project Overview

This project is based on Andrej Karpathy's nanoGPT framework, specifically trained on Chinese ancient poetry data to build a language model capable of generating classical Chinese poetry. The project's highlight is not only the poetry generation functionality but also a Streamlit-based visualization interface that allows users to intuitively observe the attention mechanisms and token generation process within the Transformer model.

### Key Features

- Uses nanoGPT architecture trained for Chinese poetry generation
- Character-level tokenization suitable for Chinese poetry processing
- Interactive visualization interface built with Streamlit
- Intuitive display of model's internal attention matrices and multi-head attention mechanisms
- Real-time visualization of token generation probability distribution
- Support for custom input prompts for poetry continuation

## Installation and Setup

```bash
# Clone the project
git clone https://github.com/yourusername/nanoGPT-Poetry.git
cd nanoGPT-Poetry

# Install dependencies
pip install torch numpy transformers datasets tiktoken wandb tqdm streamlit plotly
```

## Project Structure

```
├── data/                     # Data directory
│   └── shakespeare_char/     # Character-level poetry data
│       ├── combined_poetry.txt  # Original poetry text
│       ├── train.bin         # Training data
│       ├── val.bin           # Validation data
│       ├── poetry_meta.pkl   # Vocabulary metadata
│       └── prepare.py        # Data preprocessing script
├── config/                   # Configuration files
│   └── train_shakespeare_char.py  # Training configuration
├── out-shakespeare-char/     # Model output directory
│   └── poetry_ckpt.pt        # Trained poetry model
├── model.py                  # Enhanced GPT model definition
├── ori_model.py              # Original GPT model definition
├── train.py                  # Training script
├── sample.py                 # Text generation script
├── test_sample.py            # Generation test script with detailed output
├── GPT_show.py               # Streamlit visualization interface
└── README.md                 # Project documentation
```

## Usage

### Data Preparation

To use your own poetry dataset:

```bash
# Place your poetry text in input.txt file
python data/shakespeare_char/prepare.py
```
And you will get train.bin and test.bin

### Training the Model

```bash
# Train with default configuration
python train.py config/train_shakespeare_char.py

# Train with custom parameters
python train.py config/train_shakespeare_char.py --batch_size=32 --n_layer=8 --n_head=8 --n_embd=512
```

### Download Pre-trained Model

You can download the pre-trained model weights from the following Baidu Cloud link:

```
链接：https://pan.baidu.com/s/11tCOCI_gmzi_MLDSR4NzTg?pwd=ai2a
提取码：ai2a
```

After downloading, please place the model files (poetry_ckpt.pt) in the `out-shakespeare-char` folder in the project root directory. If the folder does not exist, please create it manually.

### Generating Poetry

```bash
# Generate poetry using the trained model
python sample.py --out_dir=out-shakespeare-char --start="白玉为堂金作马" --num_samples=5
```

### Starting the Visualization Interface

```bash
# Launch the Streamlit visualization interface
streamlit run GPT_show.py
```

## Visualization Interface Features

The core highlight of the project is the Streamlit-based visualization interface that allows users to intuitively understand how the Transformer model works:

1. **Parameter Settings**: Users can set input prompts, adjust temperature parameters, select Top K values, etc.
2. **Attention Visualization**: Displays attention matrices (Q, K, V, Attention Weights) for each layer and head
3. **Probability Distribution**: Shows the prediction probability distribution for the next token
4. **Generation Control**: Step-by-step generation with visualization of each token's generation process
5. **Transformer Tutorial**: Built-in tutorial resources for the Transformer model

## Model Architecture

This project uses a GPT architecture based on the Transformer:

- 6 Transformer layers
- 6 attention heads
- 384-dimensional hidden state
- Character-level tokenization
- Added detailed intermediate state output functionality for visualization analysis

## Model Code Differences

This project includes two model files: `model.py` (enhanced version) and `ori_model.py` (original version), with the following main differences:

### 1. Attention Mechanism (CausalSelfAttention class)
- The enhanced version adds the `return_details` parameter, which can return Q, K, V matrices and attention weights from intermediate calculations
- The enhanced version improves the causal mask (causal mask) processing logic, supporting dynamic processing for sequences exceeding the predefined size
- The enhanced version simplifies attention calculation, focusing on intermediate states required for visualization

### 2. Transformer Block (Block class)
- The enhanced version uses a more modular structure, storing input and output for attention layers and MLP layers separately
- The enhanced version adds the `return_details` parameter, which can return intermediate calculation results for each module
- The enhanced version retains residual connection calculation results for each step, making it easier to visualize and analyze

### 3. GPT model forward propagation (forward method)
- The enhanced version always calculates logits for all positions, while the original version calculates logits only for the last position during inference
- The enhanced version adds detailed intermediate state output, including output for each layer and prediction probability distribution for the next token
- The enhanced version designs a hierarchical return structure, making it easier for visualization interface to extract and display model internal state

These enhanced features are mainly for supporting visualization interface in `GPT_show.py`, allowing users to intuitively observe model internal calculation process, especially attention mechanism working principle. These modifications do not affect model basic functionality and generation ability, but greatly improve model explainability and educational value.

## Example Output

Input prompt: `白玉为堂金作马`

Generated result:
```
白玉为堂金作马，
黄金为殿玉为堂。
高楼十二青云里，
楼上琼花一夜香。
```

## Future Plans

- Add more ancient poetry datasets
- Optimize model parameters and training methods
- Add more visualization features
- Support generation control for various poetry styles
- Implement online deployment and sharing

## Acknowledgements

- Thanks to Andrej Karpathy for the [nanoGPT](https://github.com/karpathy/nanoGPT) framework
- Thanks to the [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) repository for providing the Chinese poetry database. The training process of this project first involves filtering and merging data from this repository before proceeding with the subsequent training workflow
- The visualization interface is inspired by [bbycroft's LLM visualization](https://bbycroft.net/llm)
