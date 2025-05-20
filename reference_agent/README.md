# Reference Agent

Reference Agent 是一个用于学术论文引用核查与文献下载的智能工具。它能够自动分析 Word 文档中的参考文献引用情况，自动从 arXiv 检索并下载文献，并结合大模型自动核查引文与文献内容的对应关系。

## 主要功能

1. **引文核查**：自动统计文档中参考文献的引用情况，检测未被引用或重复引用的文献。
2. **文献下载**：根据文档参考文献列表，自动从 arXiv 检索并下载对应的 PDF 文献。
3. **引文内容核查**：利用大模型自动比对文档中的引文内容与实际文献内容，判断引用是否准确。

## 工作原理

- 解析 Word 文档，提取正文和参考文献部分。
- 统计和分析文献引用情况。
- 调用 arXiv API 检索并下载参考文献。
- 结合大模型（如智谱AI）自动核查引文内容。

## 安装与环境准备

1. **Python 版本**：需要 Python 3.12 及以上。
2. **依赖安装**：
   ```bash
   pip install -r requirements.txt
   ```
   或使用 uv：
   ```bash
   uv pip install -r requirements.txt
   ```
3. **环境变量**：在项目根目录下创建 `.env` 文件，写入：
   ```env
   ZHIPUAI_API_KEY=你的智谱AI密钥
   ```

## 使用方法

### 1. 准备数据
- 准备待检测的 Word 文档（.docx 格式）。
- 创建用于存放下载文献的目录（如 `data/references`）。
- 准备提示词模板（如 `prompts/verify_citation.txt`）。

### 2. 运行命令

```bash
python -m reference_agent.agent \
  --model "glm-4" \
  --prompt "prompts/verify_citation.txt" \
  --doc "你的文档路径.docx" \
  --ref "参考文献目录路径"
```

参数说明：
- `--model`：使用的大模型名称（如 "glm-4"）
- `--prompt`：提示词模板文件路径
- `--doc`：待检测的 Word 文档路径
- `--ref`：参考文献 PDF 存放目录

### 3. 输出结果
- 程序会依次输出：
  - 文献引用统计与异常提示
  - 文献下载情况
  - 引文与文献内容核查结果

## 依赖说明
- arxiv：学术论文检索
- gradio：Web 界面（预留）
- openai/zhipuai：大模型 API
- pymupdf：PDF 处理
- python-docx：Word 处理
- python-dotenv：环境变量

## 适用场景
- 学术论文写作与引用核查
- 期刊/会议论文初审
- 学术不端检测辅助

