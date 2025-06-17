# API参考文档

本文档详细介绍了PPT智能更新助手的Python API接口。

## 核心类

### PPTUpdateAgent

主要的PPT更新代理类，负责协调整个更新流程。

#### 初始化

```python
from PPT_update_agent.ppt_update_agent_full import PPTUpdateAgent

agent = PPTUpdateAgent(
    config_file="browser_mcp.json",  # MCP配置文件路径
    llm_model="deepseek-chat"        # 语言模型名称
)
```

#### 方法

##### `async initialize()`
初始化MCP客户端和语言模型。

```python
await agent.initialize()
```

##### `load_ppt(ppt_file: str) -> bool`
加载PPT文件。

**参数:**
- `ppt_file`: PPT文件路径

**返回:**
- `bool`: 是否成功加载

```python
success = agent.load_ppt("presentation.pptx")
```

##### `async analyze_content(content: str) -> Dict[str, Any]`
分析内容并确定需要更新的部分。

**参数:**
- `content`: PPT中的文本内容

**返回:**
- `Dict[str, Any]`: 分析结果，包含需要更新的部分

##### `async search_latest_info(keywords: str) -> str`
使用MCP搜索最新信息。

**参数:**
- `keywords`: 搜索关键词

**返回:**
- `str`: 搜索结果摘要

##### `async generate_update(original_content: str, search_results: str) -> str`
生成更新内容。

**参数:**
- `original_content`: 原始内容
- `search_results`: 搜索结果

**返回:**
- `str`: 更新后的内容

##### `async process_slide(slide_index: int) -> Dict[str, Any]`
处理单个幻灯片。

**参数:**
- `slide_index`: 幻灯片索引（从1开始）

**返回:**
- `Dict[str, Any]`: 处理结果

##### `async process_ppt(ppt_file: str, slides: List[int] = None) -> Dict[str, Any]`
处理整个PPT。

**参数:**
- `ppt_file`: PPT文件路径
- `slides`: 要处理的幻灯片列表，如果为None则处理所有幻灯片

**返回:**
- `Dict[str, Any]`: 处理结果

##### `async close()`
关闭Agent和客户端连接。

```python
await agent.close()
```

### PPTParser

PPT文件解析器，用于提取PPT中的内容。

#### 初始化

```python
from PPT_update_agent.ppt_parser import PPTParser

parser = PPTParser("presentation.pptx")
```

#### 方法

##### `parse() -> List[Dict[str, Any]]`
解析PPT文件，提取每一页的内容。

**返回:**
- `List[Dict[str, Any]]`: 包含所有幻灯片内容的列表

##### `get_slide_text_content(slide_index: int = None) -> str`
获取指定幻灯片或所有幻灯片的文本内容。

**参数:**
- `slide_index`: 幻灯片索引（从1开始），如果为None则返回所有幻灯片内容

**返回:**
- `str`: 幻灯片文本内容

##### `save_as_text(output_file: str) -> None`
将PPT内容保存为文本文件。

**参数:**
- `output_file`: 输出文件路径

## 使用示例

### 基本使用

```python
import asyncio
from PPT_update_agent.ppt_update_agent_full import PPTUpdateAgent

async def main():
    # 初始化Agent
    agent = PPTUpdateAgent("browser_mcp.json")
    await agent.initialize()
    
    try:
        # 处理PPT
        result = await agent.process_ppt("presentation.pptx")
        
        # 打印结果
        print("处理结果:")
        for slide_result in result.get("结果", []):
            slide_num = slide_result.get("幻灯片", 0)
            updates = slide_result.get("更新内容", [])
            print(f"幻灯片 {slide_num}: {len(updates)} 个更新项")
            
    finally:
        # 关闭连接
        await agent.close()

asyncio.run(main())
```

### 处理特定幻灯片

```python
# 只处理第1、3、5张幻灯片
result = await agent.process_ppt("presentation.pptx", slides=[1, 3, 5])
```

### 单独使用PPT解析器

```python
from PPT_update_agent.ppt_parser import PPTParser

# 解析PPT
parser = PPTParser("presentation.pptx")
slide_contents = parser.parse()

# 获取特定幻灯片内容
slide_1_content = parser.get_slide_text_content(1)
print(slide_1_content)

# 保存为文本文件
parser.save_as_text("presentation.txt")
```

## 错误处理

所有异步方法都可能抛出异常，建议使用try-catch块进行错误处理：

```python
try:
    result = await agent.process_ppt("presentation.pptx")
except FileNotFoundError:
    print("PPT文件不存在")
except Exception as e:
    print(f"处理过程中出错: {str(e)}")
```

## 配置选项

### MCP配置文件格式

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

### 环境变量

- `DEEPSEEK_API_KEY`: DeepSeek API密钥（必需）
- `TAVILY_API_KEY`: Tavily搜索API密钥（可选）
- `LOG_LEVEL`: 日志级别（DEBUG, INFO, WARNING, ERROR）

## 返回数据格式

### process_ppt 返回格式

```python
{
    "文件": "presentation.pptx",
    "处理的幻灯片": [1, 2, 3],
    "结果": [
        {
            "幻灯片": 1,
            "分析结果": {...},
            "更新内容": [
                {
                    "原内容": "原始内容",
                    "更新内容": "更新后的内容", 
                    "搜索关键词": "搜索关键词",
                    "搜索结果": "搜索结果详情"
                }
            ]
        }
    ],
    "执行日志": [...]
}
```

### PPTParser.parse() 返回格式

```python
[
    {
        "slide_number": 1,
        "texts": [
            {
                "text": "文本内容",
                "type": "title" | "normal_text"
            }
        ],
        "tables": [
            {
                "dataframe": pandas.DataFrame,
                "raw_data": [[...]]
            }
        ],
        "images": [
            {
                "type": "image",
                "description": "图片描述"
            }
        ],
        "notes": "备注内容"
    }
]
```
