import asyncio
import os
from dotenv import load_dotenv
#from langchain_openai import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_qwq import ChatQwQ
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage
from mcp_use_new import MCPAgent, MCPClient
import os

os.environ["DEEPSEEK_API_KEY"] = ""
async def main():
    # Load environment variables
    load_dotenv()

    # Create MCPClient from config file
    client = MCPClient.from_config_file(
        os.path.join(r"./browser_mcp.json")
    )

    # Create LLM
    llm = ChatDeepSeek(model="deepseek-chat")
    # Alternative models:
    # llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
    # llm = ChatGroq(model="llama3-8b-8192")

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run the query
    result = await agent.run(
        r"请帮我查找五篇deepresearch的论文?",
        max_steps=30,
    )
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())