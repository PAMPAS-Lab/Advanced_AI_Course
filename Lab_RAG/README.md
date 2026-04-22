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


- 使用 OpenAI 兼容接口调用嵌入模型和对话模型
- 当前 notebook 已改为默认使用硅基流动兼容接口

## 使用方法

### 1. 环境配置

```bash
git clone https://github.com/PAMPAS-Lab/Advanced_AI_Course.git
cd Advanced_AI_Course/Lab_RAG
pip install -r requirements.txt
```



### 2. 添加硅基流动 API

在对应notebook输入自己的api-key



- [项目参考实现](https://github.com/FareedKhan-dev/all-rag-techniques)
- [Adaptive-RAG](https://arxiv.org/abs/2403.14403)
- [硅基流动文档](https://docs.siliconflow.cn/)
