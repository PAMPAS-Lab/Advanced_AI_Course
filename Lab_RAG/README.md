# RAG实验项目
## 项目简介

本实验项目聚焦于三种先进的检索增强生成（RAG）技术：反馈循环RAG、自适应RAG和层次化RAG。通过简洁、直接的代码实现，本项目旨在帮助学生和研究人员深入理解这些高级RAG技术的核心原理和实践应用。
与使用LangChain或FAISS等框架不同，本项目使用基础的Python库（openai、numpy等）实现核心功能，确保代码简洁易读，便于学习和修改。

## 文件结构

Lab_RAG/
├── 11_feedback_loop_rag.ipynb       # 反馈循环RAG实验
├── 12_adaptive_rag.ipynb            # 自适应RAG实验
├── 18_hierarchy_rag.ipynb           # 层次化RAG实验
├── requirements.txt                 # Python依赖库
├── README.md                        # 项目介绍
└── data/
    └── AI_Information.pdf           # 实验数据集

## 主要功能

1. **反馈循环RAG**：
   - 通过用户反馈持续优化RAG系统
   关键特点：自我学习能力，持续改进

2. **自适应RAG**：
   - 根据查询类型动态选择最佳检索策略
   关键特点：智能决策，资源优化

3. **层次化RAG**：
   - 构建多层次索引实现高效检索
   关键特点：高效检索，上下文保留


## 技术要点

- **基础架构**：纯Python实现（非框架依赖）
- **嵌入模型**：BAAI/bge-en-icl  bge-multilingual-gemma2     采用Nebius API 
- **生成模型**：Qwen/Qwen2.5-Coder-7B  google/gemma-2-2b-it  采用Nebius API 
- **评估方法**：余弦相似度、人工评估

## 使用方法

1. **环境配置**：
   ```bash
   git clone https://github.com/PAMPAS-Lab/Advanced_AI_Course.git
   cd Lab_RAG
   pip install -r requirements.txt
   ```

2. **配置API密钥**：
  ```python
  import os
  os.environ["OPENAI_API_KEY"] = "xxx"
  ```
  配置OpenAI API密钥。将"xxx"替换成您的密钥。

## 实验结果

通过与简单RAG的回答对比，理解三种RAG技术之间的差异。

## 参考资料

- [github源码](https://github.com/FareedKhan-dev/all-rag-techniques#)
- [Adaptive-RAG](https://arxiv.org/abs/2403.14403)
- [API申请](https://nebius.com/)

