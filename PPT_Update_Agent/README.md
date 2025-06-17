# PPT智能更新助手 (PPT Update Agent)

一个基于LLM和MCP的PowerPoint演示文稿智能更新系统，能够自动检测PPT中过时的内容并通过网络搜索获取最新信息进行更新建议。

## 🌟 项目特色

- **智能内容分析**: 使用大语言模型自动识别PPT中可能过时的新闻、数据和事实
- **实时信息搜索**: 通过MCP (Model Context Protocol) 框架集成多种搜索工具
- **可视化界面**: 基于Streamlit的用户友好界面，支持文件上传和结果展示
- **多格式支持**: 支持.pptx格式的PowerPoint文件解析
- **详细报告**: 生成包含原内容、更新建议和搜索来源的详细报告

## 🏗️ 项目架构

```
PPT_Update_Agent/
├── PPT_update_agent/           # 主要应用模块
│   ├── streamlit_app.py        # Streamlit Web界面
│   ├── ppt_update_agent_full.py # 核心更新Agent
│   ├── ppt_parser.py           # PPT文件解析器
│   ├── ppt_update_apply.py     # 更新应用模块
│   ├── browser_mcp.json        # MCP服务器配置
│   └── mcp_test.py            # MCP测试脚本
├── mcp_use_new/               # MCP框架实现
│   ├── agents/                # Agent相关模块
│   ├── adapters/              # 适配器模块
│   ├── connectors/            # 连接器模块
│   ├── task_managers/         # 任务管理器
│   └── client.py              # MCP客户端
├── requirements.txt           # 项目依赖
└── README.md                 # 项目文档
```

## 🚀 核心功能

### 1. PPT内容解析
- 提取幻灯片中的文本、表格、图片信息
- 支持标题、正文、备注的分类识别
- 将表格数据转换为Pandas DataFrame格式

### 2. 智能内容分析
- 使用DeepSeek大语言模型分析内容时效性
- 识别包含日期、数据、新闻等可能过时的信息
- 生成针对性的搜索关键词

### 3. 实时信息搜索
- 基于MCP框架集成多种搜索服务
- 支持Tavily搜索、ArXiv学术搜索等
- 获取最新、可靠的信息来源

### 4. 更新建议生成
- 基于搜索结果生成适合PPT展示的更新内容
- 保持原有格式和风格的一致性
- 提供详细的更新理由和信息来源

## 📋 系统要求

- Python 3.8+
- Windows 10/11 (支持pywin32)
- 至少4GB RAM
- 网络连接 (用于API调用和信息搜索)

## 🛠️ 安装指南

### 1. 克隆项目
```bash
git clone <repository-url>
cd PPT_Update_Agent
```

### 2. 创建虚拟环境
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置API密钥
创建`.env`文件并添加以下配置：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # 可选
```

### 5. 配置MCP服务器
编辑`PPT_update_agent/browser_mcp.json`文件，配置所需的MCP服务器：
```json
{
  "mcpServers": {
    "fetch": {
      "type": "sse",
      "url": "your_fetch_server_url"
    },
    "tavily-mcp": {
      "type": "sse",
      "url": "your_tavily_server_url"
    }
  }
}
```

## 🎯 使用方法

### 方法一：Web界面 (推荐)
```bash
cd PPT_update_agent
streamlit run streamlit_app.py
```

然后在浏览器中访问 `http://localhost:8501`

#### Web界面功能：
1. **文件上传**: 拖拽或选择.pptx文件
2. **内容预览**: 查看PPT的文本、表格、图片内容
3. **智能分析**: 选择要分析的幻灯片并开始分析
4. **结果查看**: 查看原内容与更新建议的对比
5. **报告导出**: 导出JSON格式的详细分析报告

### 方法二：命令行界面
```bash
cd PPT_update_agent
python ppt_update_agent_full.py --ppt "path/to/your/presentation.pptx" --slides 1,2,3
```

#### 命令行参数：
- `--ppt`: PPT文件路径 (必需)
- `--slides`: 要处理的幻灯片编号，用逗号分隔 (可选，默认处理所有)
- `--config`: MCP配置文件路径 (可选)
- `--output`: 结果输出文件路径 (可选)


## 📊 输出格式

系统会生成包含以下信息的详细报告：

```json
{
  "文件": "presentation.pptx",
  "分析时间": "2024-01-01 12:00:00",
  "处理的幻灯片": [1, 2, 3],
  "结果": [
    {
      "幻灯片": 1,
      "更新内容": [
        {
          "原内容": "2023年的市场数据显示...",
          "更新内容": "2024年最新市场数据显示...",
          "搜索关键词": "2024年市场数据 最新统计",
          "搜索结果": "详细的搜索结果和来源信息..."
        }
      ]
    }
  ]
}
```

## 🔧 配置说明

### DeepSeek API配置
1. 访问 [DeepSeek官网](https://platform.deepseek.com/) 注册账户
2. 获取API密钥
3. 在`.env`文件中设置`DEEPSEEK_API_KEY`

### MCP服务器配置
项目使用MCP (Model Context Protocol) 框架集成外部工具：

- **Fetch服务器**: 用于网页内容获取
- **Tavily搜索**: 提供实时搜索功能
- **ArXiv服务器**: 用于学术论文搜索

## 🧪 测试

### 运行单元测试
```bash
python -m pytest tests/
```

### 测试PPT解析功能
```bash
cd PPT_update_agent
python ppt_parser.py sample.pptx
```

### 测试MCP连接
```bash
cd PPT_update_agent
python mcp_test.py
```

## 🐛 故障排除

### 常见问题

1. **API余额不足**
   - 错误信息：`Insufficient Balance`
   - 解决方案：登录DeepSeek官网充值账户

2. **MCP服务器连接失败**
   - 检查`browser_mcp.json`配置是否正确
   - 确认网络连接正常
   - 验证服务器URL是否有效

3. **PPT文件解析失败**
   - 确保文件格式为.pptx
   - 检查文件是否损坏
   - 确认文件路径正确

4. **依赖安装失败**
   - 使用管理员权限运行命令提示符
   - 更新pip：`python -m pip install --upgrade pip`
   - 单独安装问题依赖：`pip install package_name`

### 日志调试
启用详细日志输出：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本项目
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

### 代码规范
- 使用Python PEP 8编码规范
- 添加适当的注释和文档字符串
- 编写单元测试覆盖新功能
- 确保所有测试通过

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件

## 🙏 致谢

- [DeepSeek](https://platform.deepseek.com/) - 提供强大的大语言模型API
- [LangChain](https://langchain.com/) - 提供LLM应用开发框架
- [Streamlit](https://streamlit.io/) - 提供快速Web应用开发框架
- [python-pptx](https://python-pptx.readthedocs.io/) - 提供PowerPoint文件处理能力
- [mcp-use](https://github.com/mcp-use/mcp-use) - mcp便携搭建


**注意**: 本项目仅用于学习和研究目的。使用时请遵守相关API服务的使用条款和限制。
