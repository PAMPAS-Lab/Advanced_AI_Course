# 快速开始指南

本指南将帮助您在5分钟内快速上手PPT智能更新助手。

## 🚀 快速安装

### 1. 环境准备
确保您的系统满足以下要求：
- Python 3.8 或更高版本
- Windows 10/11 (推荐) 或 Linux/macOS
- 至少4GB可用内存
- 稳定的网络连接

### 2. 下载项目
```bash
git clone <your-repository-url>
cd PPT_Update_Agent
```

### 3. 安装依赖
```bash
# 创建虚拟环境 (推荐)
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置API密钥
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加您的API密钥
# DEEPSEEK_API_KEY=your_actual_api_key_here
```

## 🎯 第一次使用

### 方式一：Web界面 (最简单)

1. **启动Web应用**
```bash
cd PPT_update_agent
streamlit run streamlit_app.py
```

2. **打开浏览器**
访问 `http://localhost:8501`

3. **上传PPT文件**
- 点击"选择PPT文件"按钮
- 选择您的.pptx文件
- 等待文件解析完成

4. **开始分析**
- 选择要分析的幻灯片（或选择"全部幻灯片"）
- 点击"🚀 开始分析"按钮
- 等待分析完成

5. **查看结果**
- 在"分析结果"部分查看更新建议
- 可以导出JSON格式的详细报告

### 方式二：命令行 (适合批处理)

```bash
cd PPT_update_agent
python ppt_update_agent_full.py --ppt "your_presentation.pptx"
```

## 📝 示例演示

### 准备测试文件
如果您没有现成的PPT文件，可以创建一个包含以下内容的测试文件：

**幻灯片1 - 标题页**
```
标题: 2023年市场分析报告
副标题: 基于最新数据的行业趋势
```

**幻灯片2 - 数据页**
```
标题: 市场数据概览
内容: 
- 2023年第一季度销售额达到1000万
- 用户增长率为15%
- 市场份额占比20%
```

### 预期结果
系统会识别出：
- "2023年"相关的时间敏感信息
- 可能需要更新的市场数据
- 过时的统计数字

并提供基于最新搜索结果的更新建议。

## 🔧 常见配置

### 自定义MCP服务器
编辑 `PPT_update_agent/browser_mcp.json`：

```json
{
  "mcpServers": {
    "fetch": {
      "type": "sse",
      "url": "http://localhost:3000"
    },
    "tavily-mcp": {
      "type": "sse",
      "url": "http://localhost:3001"
    }
  }
}
```

### 调整分析参数
在代码中可以调整以下参数：
- `max_steps`: 最大分析步数 (默认: 5)
- `llm_model`: 使用的语言模型 (默认: "deepseek-chat")
- `verbose`: 是否显示详细日志 (默认: False)

## 🐛 常见问题解决

### 问题1: API密钥错误
**错误信息**: `401 Unauthorized`
**解决方案**: 
1. 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. 确认API密钥有效且有足够余额

### 问题2: 文件解析失败
**错误信息**: `解析PPT文件时出错`
**解决方案**:
1. 确保文件格式为 `.pptx`
2. 检查文件是否损坏
3. 尝试用PowerPoint重新保存文件

### 问题3: MCP连接失败
**错误信息**: `MCP服务器连接失败`
**解决方案**:
1. 检查网络连接
2. 验证 `browser_mcp.json` 配置
3. 确认MCP服务器正在运行

### 问题4: 依赖安装失败
**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 单独安装问题依赖
pip install python-pptx
pip install streamlit
pip install langchain-deepseek

# 如果仍有问题，尝试使用conda
conda install -c conda-forge python-pptx
```

## 📚 下一步

现在您已经成功运行了PPT智能更新助手！接下来可以：

1. **阅读完整文档**: 查看 [README.md](../README.md) 了解所有功能
2. **API参考**: 查看 [API_REFERENCE.md](API_REFERENCE.md) 学习编程接口
3. **自定义配置**: 根据需要调整MCP服务器和模型参数
4. **集成到工作流**: 将工具集成到您的日常工作流程中

## 💡 使用技巧

1. **批量处理**: 使用命令行界面可以批量处理多个PPT文件
2. **选择性分析**: 只分析需要更新的特定幻灯片以节省时间和API调用
3. **定期更新**: 建议定期（如每月）运行分析以保持内容时效性
4. **备份原文件**: 在应用更新前务必备份原始PPT文件

## 🆘 获取帮助

如果遇到问题：
1. 查看本文档的常见问题部分
2. 检查项目的 [GitHub Issues](https://github.com/your-repo/issues)
3. 提交新的Issue描述您的问题

祝您使用愉快！🎉
