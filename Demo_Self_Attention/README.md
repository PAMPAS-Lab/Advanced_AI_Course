# 自注意力机制演示项目

这是一个用于演示和可视化自注意力机制（Self-Attention）的教学项目，帮助理解Transformer模型核心组件的工作原理。

## 项目介绍

自注意力机制是Transformer架构的核心组件，也是现代大语言模型的基础。本项目提供了两个清晰的示例来帮助理解自注意力机制的计算过程以及多头注意力的工作原理。通过交互式可视化和代码实现，可以直观地了解注意力机制如何在序列数据中捕捉元素间的依赖关系。

## 文件结构

- `self_attention.ipynb`：自注意力机制的基础实现，以Jupyter笔记本形式展示核心计算步骤
- `multihead_self_attention_demo.py`：多头自注意力机制的交互式演示应用，使用Streamlit构建

## 功能特点

### self_attention.ipynb

- 详细展示自注意力机制的基本计算流程
- 实现了输入向量、权重矩阵初始化
- 展示键(Key)、查询(Query)、值(Value)向量的计算过程
- 演示注意力分数的计算及softmax转换
- 计算最终的注意力输出

### multihead_self_attention_demo.py

- 基于Streamlit构建的交互式Web应用
- 可视化展示多头注意力机制的工作原理
- 支持自定义序列长度、嵌入维度和注意力头数量
- 实时显示每个注意力头的Q、K、V矩阵
- 可视化注意力权重和最终输出

## 使用方法

### 运行Jupyter笔记本

```bash
jupyter notebook self_attention.ipynb
```

### 启动多头注意力演示应用

```bash
streamlit run multihead_self_attention_demo.py
```

## 环境依赖

```bash
pip install numpy torch matplotlib streamlit
```

## 可视化演示

多头注意力演示应用提供了丰富的可视化功能：

1. **动态调整参数**：用户可以调整序列长度、嵌入维度和注意力头数量
2. **矩阵可视化**：以热力图形式展示各种矩阵计算结果
3. **注意力权重展示**：可视化不同注意力头的权重分布
4. **逐步计算过程**：展示从输入嵌入到最终输出的完整计算流程

## 扩展学习

理解本项目后，建议进一步学习：

- Transformer完整架构
- 位置编码机制
- 多层Transformer结构
- 预训练语言模型原理

## 参考资源

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Transformer原始论文
- [The Illustrated Transformer](http://jalammar.github.io/illustrated-transformer/) - Transformer图解
- [The Annotated Transformer](http://nlp.seas.harvard.edu/2018/04/03/attention.html) - 带注释的Transformer实现
