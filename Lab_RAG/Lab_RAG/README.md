# RAG实验项目

## 项目简介

本实验项目聚焦于三种先进的检索增强生成（RAG）技术：反馈循环 RAG、自适应 RAG 和层次化 RAG。通过简洁、直接的代码实现，帮助学习者理解这些方法的核心原理和实际使用方式。

## 文件结构

- `11_feedback_loop_rag.ipynb`：反馈循环 RAG 实验
- `12_adaptive_rag.ipynb`：自适应 RAG 实验
- `18_hierarchy_rag.ipynb`：层次化 RAG 实验
- `requirements.txt`：Python 依赖
- `data/AI_Information.pdf`：实验数据
- `data/val.json`：英文问答评估数据
- `data/val_cn.json`：中文问答评估数据

## 主要功能

1. **反馈循环 RAG**
   - 通过用户反馈持续优化 RAG 系统

2. **自适应 RAG**
   - 根据查询类型动态选择检索策略

3. **层次化 RAG**
   - 构建多层索引，实现更高效的检索

## 技术要点

- 纯 Python 实现，不依赖 LangChain 或 FAISS
- 使用 OpenAI 兼容接口调用嵌入模型和对话模型
- 当前 notebook 已改为默认使用硅基流动兼容接口

## 使用方法

### 1. 环境配置

```bash
git clone https://github.com/PAMPAS-Lab/Advanced_AI_Course.git
cd Advanced_AI_Course/Lab_RAG
pip install -r requirements.txt
```

如果你使用 `conda`，建议先创建独立环境后再安装依赖。

### 2. 添加硅基流动 API

这几个 notebook 现在默认读取下面这些环境变量：

- `SILICONFLOW_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`

最小配置方式如下：

```bash
export SILICONFLOW_API_KEY="your_siliconflow_api_key"
```

如需显式指定接口地址和模型，可以继续设置：

```bash
export OPENAI_BASE_URL="https://api.siliconflow.cn/v1"
export CHAT_MODEL="Qwen/Qwen3-8B"
export EMBEDDING_MODEL="BAAI/bge-m3"
```

说明：

- 默认兼容接口地址是 `https://api.siliconflow.cn/v1`
- 默认对话模型是 `Qwen/Qwen3-8B`
- 默认嵌入模型是 `BAAI/bge-m3`
- 如果已经设置了 `SILICONFLOW_API_KEY`，一般不需要再改 notebook 里的初始化代码

### 3. 启动 Jupyter

在 `Lab_RAG` 目录下执行：

```bash
jupyter notebook
```

然后打开对应 notebook：

- `11_feedback_loop_rag.ipynb`
- `12_adaptive_rag.ipynb`
- `18_hierarchy_rag.ipynb`

## 运行说明

- `11_feedback_loop_rag.ipynb` 中包含 `input()`，更适合在 Jupyter 页面中交互运行
- notebook 默认会读取 `data/AI_Information.pdf`
- 如果出现 API 401，优先检查当前 shell 中的 `SILICONFLOW_API_KEY` 是否有效

## 参考资料

- [项目参考实现](https://github.com/FareedKhan-dev/all-rag-techniques)
- [Adaptive-RAG](https://arxiv.org/abs/2403.14403)
- [硅基流动文档](https://docs.siliconflow.cn/)
