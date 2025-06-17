import asyncio
import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import pandas as pd
from langchain_core.messages import HumanMessage
from langchain_deepseek import ChatDeepSeek
import sys
# 添加上级目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_use_new import MCPAgent, MCPClient

# 导入PPT解析器
from ppt_parser import PPTParser

# 配置环境变量
os.environ["DEEPSEEK_API_KEY"] = "sk-9f92dd6f720b4cb0bb2820a0babb1643"

class PPTUpdateAgent:
    """PPT更新Agent，能够检测PPT中需要更新的内容并搜索最新信息"""
    
    def __init__(self, config_file: str, llm_model: str = "deepseek-chat"):
        """初始化Agent
        
        Args:
            config_file: MCP配置文件路径
            llm_model: 使用的语言模型
        """
        self.config_file = config_file
        self.llm_model = llm_model
        self.client = None
        self.agent = None
        self.llm = None
        self.parser = None
        self.execution_log = []
        
    async def initialize(self):
        """初始化MCP客户端和语言模型"""
        print("🚀 初始化PPT更新Agent...")
        load_dotenv()
        
        # 创建MCP客户端
        self.client = MCPClient.from_config_file(self.config_file)
        
        # 创建语言模型
        self.llm = ChatDeepSeek(model=self.llm_model)
        
        # 创建Agent
        self.agent = MCPAgent(
            llm=self.llm, 
            client=self.client, 
            max_steps=5,
            verbose=True
        )
        
        print("✅ 初始化完成")
    
    def load_ppt(self, ppt_file: str) -> bool:
        """加载PPT文件
        
        Args:
            ppt_file: PPT文件路径
            
        Returns:
            是否成功加载
        """
        try:
            self.parser = PPTParser(ppt_file)
            self.parser.parse()
            print(f"✅ 成功加载PPT文件: {ppt_file}")
            return True
        except Exception as e:
            print(f"❌ 加载PPT文件时出错: {str(e)}")
            return False
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """分析内容并确定需要更新的部分
        
        Args:
            content: PPT中的文本内容
            
        Returns:
            需要更新的内容和原因
        """
        self._log_step("分析内容", {"内容长度": len(content)})
        
        from datetime import datetime

        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""
        请分析以下PPT内容，找出其中可能需要更新的新闻、数据或事实，请注意，现在的时间是{current_time}，内容如下：
        
        {content}
        
        对于每一部分，请判断：
        1. 这部分内容是否包含可能已经过时的新闻、数据或事实？
        2. 为什么你认为它需要更新？（例如：包含过时的日期、有明确的时间标记、涉及快速变化的领域等）
        3. 应该搜索什么关键词来获取最新信息？
        4. 这部分内容在PPT中的哪个位置？（如幻灯片编号）
        
        请以JSON格式返回结果，格式如下：
        {{
            "需要更新的部分": [
                {{
                    "内容": "原文中需要更新的部分",
                    "原因": "判断为需要更新的原因",
                    "搜索关键词": "建议的搜索关键词",
                    "位置": "在PPT中的位置信息"
                }}
            ]
        }}
        """
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        # 提取JSON部分
        json_match = re.search(r'```json\s*(.*?)\s*```', response.content, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
        else:
            json_content = response.content
            
        try:
            # 尝试解析JSON
            result = json.loads(json_content)
            self._log_step("分析结果", result)
            return result
        except json.JSONDecodeError:
            # 如果解析失败，则尝试从文本中提取结构化信息
            print("⚠️ 无法解析JSON，将尝试从文本中提取信息")
            fallback_result = {"需要更新的部分": [{"内容": content[:200], "原因": "无法确定具体原因", "搜索关键词": "最新信息"}]}
            self._log_step("分析结果（回退）", fallback_result)
            return fallback_result
    
    async def search_latest_info(self, keywords: str) -> str:
        """使用MCP搜索最新信息
        
        Args:
            keywords: 搜索关键词
            
        Returns:
            搜索结果摘要
        """
        self._log_step("开始搜索", {"关键词": keywords})
        
        from datetime import datetime

        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建搜索查询
        query = f"""
        请搜索关于"{keywords}"的最新信息，特别注意：
        1. 寻找最新的数据、新闻和发展动态
        2. 确保信息来源可靠，优先选择官方网站、知名新闻媒体、学术论文等
        3. 记录信息的发布日期
        4. 总结主要观点和数据

        当前时间：{current_time}

        请返回搜索结果以及信息来源和日期。
        """
        
        # 使用MCP Agent进行搜索
        result = await self.agent.run(query, max_steps=5)
        
        self._log_step("搜索结果", {"结果长度": len(result)})
        return result
    
    async def generate_update(self, original_content: str, search_results: str) -> str:
        """生成更新内容
        
        Args:
            original_content: 原始内容
            search_results: 搜索结果
            
        Returns:
            更新后的内容
        """
        self._log_step("生成更新", {"原内容长度": len(original_content), "搜索结果长度": len(search_results)})
        
        prompt = f"""
        请基于以下最新的搜索结果，为PPT中的内容生成更新：
        
        原始内容：
        {original_content}
        
        最新搜索结果：
        {search_results}
        
        请生成适合在PPT中展示的更新内容，要求：
        1. 保持原有格式和风格，但使用最新的数据和事实
        2. 内容应该简洁、清晰，适合PPT展示
        3. 不允许有'更新后的PPT内容'等介绍内容，只能输出实质性内容！！不允许有任何符号、换行符等
        4. 保持与原PPT的一致性和连贯性
        """
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        self._log_step("更新内容", {"内容长度": len(response.content)})
        return response.content
    
    async def process_slide(self, slide_index: int) -> Dict[str, Any]:
        """处理单个幻灯片
        
        Args:
            slide_index: 幻灯片索引（从1开始）
            
        Returns:
            处理结果
        """
        if not self.parser:
            return {"错误": "请先加载PPT文件"}
        
        print(f"🔍 处理幻灯片 {slide_index}...")
        
        # 获取幻灯片内容
        slide_content = self.parser.get_slide_text_content(slide_index)
        
        # 分析内容
        analysis = await self.analyze_content(slide_content)
        
        # 处理每个需要更新的部分
        updates = []
        for item in analysis.get("需要更新的部分", []):
            # 搜索最新信息
            search_result = await self.search_latest_info(item.get("搜索关键词", ""))
            
            # 生成更新内容
            updated_content = await self.generate_update(item.get("内容", ""), search_result)
            
            # 记录更新
            updates.append({
                "原内容": item.get("内容", ""),
                "更新内容": updated_content,
                "搜索关键词": item.get("搜索关键词", ""),
                "搜索结果": search_result
            })
        
        return {
            "幻灯片": slide_index,
            "分析结果": analysis,
            "更新内容": updates
        }
    
    async def process_ppt(self, ppt_file: str, slides: List[int] = None) -> Dict[str, Any]:
        """处理整个PPT
        
        Args:
            ppt_file: PPT文件路径
            slides: 要处理的幻灯片列表，如果为None则处理所有幻灯片
            
        Returns:
            处理结果
        """
        # 重置执行日志
        self.execution_log = []
        
        # 加载PPT
        if not self.load_ppt(ppt_file):
            return {"错误": "加载PPT失败"}
        
        # 如果未指定幻灯片，则分析所有幻灯片
        if slides is None:
            # 获取所有PPT内容
            all_content = self.parser.get_slide_text_content()
            
            # 分析内容找出需要更新的部分
            analysis = await self.analyze_content(all_content)
            
            # 从分析结果中提取需要处理的幻灯片
            slides_to_process = []
            for item in analysis.get("需要更新的部分", []):
                # 尝试从位置信息中提取幻灯片编号
                position = item.get("位置", "")
                slide_match = re.search(r'幻灯片\s*(\d+)', position)
                if slide_match:
                    slide_num = int(slide_match.group(1))
                    if slide_num not in slides_to_process:
                        slides_to_process.append(slide_num)
            
            # 如果无法确定具体幻灯片，则默认处理前5张
            if not slides_to_process:
                slides_to_process = list(range(1, min(6, len(self.parser.slide_contents) + 1)))
        else:
            slides_to_process = slides
        
        # 处理选定的幻灯片
        print(f"🔄 将处理以下幻灯片: {slides_to_process}")
        results = []
        for slide_index in slides_to_process:
            slide_result = await self.process_slide(slide_index)
            results.append(slide_result)
        
        return {
            "文件": ppt_file,
            "处理的幻灯片": slides_to_process,
            "结果": results,
            "执行日志": self.execution_log
        }
    
    def _log_step(self, action: str, data: Dict[str, Any] = None) -> None:
        """记录执行步骤
        
        Args:
            action: 动作名称
            data: 相关数据
        """
        step = {
            "时间戳": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "动作": action,
            "数据": data or {}
        }
        self.execution_log.append(step)
    
    async def close(self):
        """关闭Agent和客户端连接"""
        if self.agent:
            await self.agent.close()

async def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="PPT更新Agent")
    parser.add_argument("--ppt", help="PPT文件路径", required=True)
    parser.add_argument("--slides", help="要处理的幻灯片编号列表，例如：1,3,5", default=None)
    parser.add_argument("--config", help="MCP配置文件路径", default=None)
    parser.add_argument("--output", help="结果输出文件路径", default=None)
    args = parser.parse_args()
    
    # 处理参数
    ppt_file = args.ppt
    slides = [int(x) for x in args.slides.split(",")] if args.slides else None
    
    # 设置配置文件路径
    if args.config:
        config_file = args.config
    else:
        config_file = os.path.join(os.path.dirname(__file__), "browser_mcp.json")
    
    # 设置输出文件路径
    if args.output:
        output_file = args.output
    else:
        output_file = os.path.splitext(ppt_file)[0] + "_update_report.json"
    
    # 检查文件是否存在
    if not os.path.exists(ppt_file):
        print(f"错误: PPT文件不存在: {ppt_file}")
        return
    
    if not os.path.exists(config_file):
        print(f"错误: 配置文件不存在: {config_file}")
        return
    
    # 初始化Agent
    agent = PPTUpdateAgent(config_file)
    await agent.initialize()
    
    try:
        # 处理PPT
        print(f"🔍 开始处理PPT: {ppt_file}")
        result = await agent.process_ppt(ppt_file, slides)
        
        # 保存结果
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {output_file}")
        
        # 打印摘要
        print("\n📊 处理摘要:")
        print(f"- 文件: {ppt_file}")
        print(f"- 处理的幻灯片: {result.get('处理的幻灯片', [])}")
        
        update_count = 0
        for slide_result in result.get("结果", []):
            update_count += len(slide_result.get("更新内容", []))
        
        print(f"- 找到的更新项目: {update_count}")
        print(f"- 详细结果已保存至: {output_file}")
        
    finally:
        # 关闭Agent
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 