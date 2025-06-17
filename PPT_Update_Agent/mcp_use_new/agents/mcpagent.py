"""
MCP: Main integration module with customizable system prompt.

This module provides the main MCPAgent class that integrates all components
to provide a simple interface for using MCP tools with different LLMs.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.globals import set_debug
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain.schema.language_model import BaseLanguageModel
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain_core.tools import BaseTool
from langchain_core.utils.input import get_color_mapping

from mcp_use_new.client import MCPClient
from mcp_use_new.connectors.base import BaseConnector
from mcp_use_new.session import MCPSession

from ..adapters.langchain_adapter import LangChainAdapter
from ..logging import logger
from .prompts.system_prompt_builder import create_system_message
from .prompts.templates import DEFAULT_SYSTEM_PROMPT_TEMPLATE, SERVER_MANAGER_SYSTEM_PROMPT_TEMPLATE
from .server_manager import ServerManager

set_debug(logger.level == logging.DEBUG)


class MCPAgent:
    """Main class for using MCP tools with various LLM providers.

    This class provides a unified interface for using MCP tools with different LLM providers
    through LangChain's agent framework, with customizable system prompts and conversation memory.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        client: MCPClient | None = None,
        connectors: list[BaseConnector] | None = None,
        server_name: str | None = None,
        max_steps: int = 5,
        auto_initialize: bool = False,
        memory_enabled: bool = True,
        system_prompt: str | None = None,
        system_prompt_template: str | None = None,  # User can still override the template
        additional_instructions: str | None = None,
        disallowed_tools: list[str] | None = None,
        use_server_manager: bool = False,
        verbose: bool = False,
    ):
        """Initialize a new MCPAgent instance.

        Args:
            llm: The LangChain LLM to use.
            client: The MCPClient to use. If provided, connector is ignored.
            connectors: A list of MCP connectors to use if client is not provided.
            server_name: The name of the server to use if client is provided.
            max_steps: The maximum number of steps to take.
            auto_initialize: Whether to automatically initialize the agent when run is called.
            memory_enabled: Whether to maintain conversation history for context.
            system_prompt: Complete system prompt to use (overrides template if provided).
            system_prompt_template: Template for system prompt with {tool_descriptions} placeholder.
            additional_instructions: Extra instructions to append to the system prompt.
            disallowed_tools: List of tool names that should not be available to the agent.
            use_server_manager: Whether to use server manager mode instead of exposing all tools.
        """
        self.llm = llm
        self.client = client
        if client and hasattr(client, 'verbose'):
            client.verbose = verbose  # 设置client的verbose属性
        self.connectors = connectors or []
        self.server_name = server_name
        self.max_steps = max_steps
        self.auto_initialize = auto_initialize
        self.memory_enabled = memory_enabled
        self._initialized = False
        self._conversation_history: list[BaseMessage] = []
        self.disallowed_tools = disallowed_tools or []
        self.use_server_manager = use_server_manager
        self.verbose = verbose
        # System prompt configuration
        self.system_prompt = system_prompt  # User-provided full prompt override
        # User can provide a template override, otherwise use the imported default
        self.system_prompt_template_override = system_prompt_template
        self.additional_instructions = additional_instructions
        
        # 添加执行计时和跟踪
        self.execution_stats = {
            "total_runs": 0,
            "total_steps": 0,
            "tool_calls": {},
            "start_time": time.time(),
            "execution_times": []
        }

        # Either client or connector must be provided
        if not client and len(self.connectors) == 0:
            raise ValueError("Either client or connector must be provided")

        # Create the adapter for tool conversion
        self.adapter = LangChainAdapter(disallowed_tools=self.disallowed_tools)

        # Initialize server manager if requested
        self.server_manager = None
        if self.use_server_manager:
            if not self.client:
                raise ValueError("Client must be provided when using server manager")
            self.server_manager = ServerManager(self.client, self.adapter)

        # State tracking
        self._agent_executor: AgentExecutor | None = None
        self._sessions: dict[str, MCPSession] = {}
        self._system_message: SystemMessage | None = None
        self._tools: list[BaseTool] = []
        
        logger.info(f"🚀 初始化MCP Agent，使用模型: {llm.__class__.__name__}")
        logger.info(f"⚙️ 配置: max_steps={max_steps}, memory_enabled={memory_enabled}, verbose={verbose}")

    async def initialize(self) -> None:
        """Initialize the MCP client and agent."""
        logger.info("🚀 Initializing MCP agent and connecting to services...")
        # If using server manager, initialize it
        if self.use_server_manager and self.server_manager:
            await self.server_manager.initialize()
            # Get server management tools
            management_tools = await self.server_manager.get_server_management_tools()
            self._tools = management_tools
            logger.info(
                f"🔧 Server manager mode active with {len(management_tools)} management tools"
            )

            # Create the system message based on available tools
            await self._create_system_message_from_tools(self._tools)
        else:
            # Standard initialization - if using client, get or create sessions
            if self.client:
                # First try to get existing sessions
                self._sessions = self.client.get_all_active_sessions()
                logger.info(f"🔌 Found {len(self._sessions)} existing sessions")

                # If no active sessions exist, create new ones
                if not self._sessions:
                    logger.info("🔄 No active sessions found, creating new ones...")
                    self._sessions = await self.client.create_all_sessions()
                    logger.info(f"✅ Created {len(self._sessions)} new sessions")

                # Create LangChain tools directly from the client using the adapter
                self._tools = await self.adapter.create_tools(self.client)
                logger.info(f"🛠️ Created {len(self._tools)} LangChain tools from client")
            else:
                # Using direct connector - only establish connection
                # LangChainAdapter will handle initialization
                connectors_to_use = self.connectors
                logger.info(f"🔗 Connecting to {len(connectors_to_use)} direct connectors...")
                for connector in connectors_to_use:
                    if not hasattr(connector, "client") or connector.client is None:
                        await connector.connect()

                # Create LangChain tools using the adapter with connectors
                self._tools = await self.adapter._create_tools_from_connectors(connectors_to_use)
                logger.info(f"🛠️ Created {len(self._tools)} LangChain tools from connectors")

            # Get all tools for system message generation
            all_tools = self._tools
            logger.info(f"🧰 Found {len(all_tools)} tools across all connectors")

            # Create the system message based on available tools
            await self._create_system_message_from_tools(all_tools)

        # Create the agent
        self._agent_executor = self._create_agent()
        self._initialized = True
        logger.info("✨ Agent initialization complete")

    async def _create_system_message_from_tools(self, tools: list[BaseTool]) -> None:
        """Create the system message based on provided tools using the builder."""
        # Use the override if provided, otherwise use the imported default
        default_template = self.system_prompt_template_override or DEFAULT_SYSTEM_PROMPT_TEMPLATE
        # Server manager template is now also imported
        server_template = SERVER_MANAGER_SYSTEM_PROMPT_TEMPLATE

        # Delegate creation to the imported function
        self._system_message = create_system_message(
            tools=tools,
            system_prompt_template=default_template,
            server_manager_template=server_template,  # Pass the imported template
            use_server_manager=self.use_server_manager,
            disallowed_tools=self.disallowed_tools,
            user_provided_prompt=self.system_prompt,
            additional_instructions=self.additional_instructions,
        )

        # Update conversation history if memory is enabled
        if self.memory_enabled:
            history_without_system = [
                msg for msg in self._conversation_history if not isinstance(msg, SystemMessage)
            ]
            self._conversation_history = [self._system_message] + history_without_system

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with the configured system message.

        Returns:
            An initialized AgentExecutor.
        """
        logger.debug(f"Creating new agent with {len(self._tools)} tools")

        system_content = "You are a helpful assistant"
        if self._system_message:
            system_content = self._system_message.content

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_content),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        tool_names = [tool.name for tool in self._tools]
        logger.info(f"🧠 Agent ready with tools: {', '.join(tool_names)}")

        # Use the standard create_tool_calling_agent
        agent = create_tool_calling_agent(llm=self.llm, tools=self._tools, prompt=prompt)

        # Use the standard AgentExecutor
        executor = AgentExecutor(
            agent=agent, tools=self._tools, max_iterations=self.max_steps, verbose=self.verbose
        )
        logger.debug(f"Created agent executor with max_iterations={self.max_steps}")
        return executor

    def get_conversation_history(self) -> list[BaseMessage]:
        """Get the current conversation history.

        Returns:
            The list of conversation messages.
        """
        return self._conversation_history

    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self._conversation_history = []

        # Re-add the system message if it exists
        if self._system_message and self.memory_enabled:
            self._conversation_history = [self._system_message]

    def add_to_history(self, message: BaseMessage) -> None:
        """Add a message to the conversation history.

        Args:
            message: The message to add.
        """
        if self.memory_enabled:
            self._conversation_history.append(message)

    def get_system_message(self) -> SystemMessage | None:
        """Get the current system message.

        Returns:
            The current system message, or None if not set.
        """
        return self._system_message

    def set_system_message(self, message: str) -> None:
        """Set a new system message.

        Args:
            message: The new system message content.
        """
        self._system_message = SystemMessage(content=message)

        # Update conversation history if memory is enabled
        if self.memory_enabled:
            # Remove old system message if it exists
            history_without_system = [
                msg for msg in self._conversation_history if not isinstance(msg, SystemMessage)
            ]
            self._conversation_history = history_without_system

            # Add new system message
            self._conversation_history.insert(0, self._system_message)

        # Recreate the agent with the new system message if initialized
        if self._initialized and self._tools:
            self._agent_executor = self._create_agent()
            logger.debug("Agent recreated with new system message")

    def set_disallowed_tools(self, disallowed_tools: list[str]) -> None:
        """Set the list of tools that should not be available to the agent.

        This will take effect the next time the agent is initialized.

        Args:
            disallowed_tools: List of tool names that should not be available.
        """
        self.disallowed_tools = disallowed_tools
        self.adapter.disallowed_tools = disallowed_tools

        # If the agent is already initialized, we need to reinitialize it
        # to apply the changes to the available tools
        if self._initialized:
            logger.debug(
                "Agent already initialized. Changes will take effect on next initialization."
            )
            # We don't automatically reinitialize here as it could be disruptive
            # to ongoing operations. The user can call initialize() explicitly if needed.

    def get_disallowed_tools(self) -> list[str]:
        """Get the list of tools that are not available to the agent.

        Returns:
            List of tool names that are not available.
        """
        return self.disallowed_tools

    async def run(
        self,
        query: str,
        max_steps: int | None = None,
        manage_connector: bool = True,
        external_history: list[BaseMessage] | None = None,
    ) -> str:
        """Run a query using the MCP tools with unified step-by-step execution.

        This method handles connecting to the MCP server, initializing the agent,
        running the query, and then cleaning up the connection.

        Args:
            query: The query to run.
            max_steps: Optional maximum number of steps to take.
            manage_connector: Whether to handle the connector lifecycle internally.
                If True, this method will connect, initialize, and disconnect from
                the connector automatically. If False, the caller is responsible
                for managing the connector lifecycle.
            external_history: Optional external history to use instead of the
                internal conversation history.

        Returns:
            The result of running the query.
        """
        self.execution_stats["total_runs"] += 1
        run_id = self.execution_stats["total_runs"]
        run_start_time = time.time()
        
        logger.info(f"='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='")
        logger.info(f"🚀 执行MCP Agent 运行 #{run_id}: {query[:50]}{'...' if len(query) > 50 else ''}")
        logger.info(f"='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='")
        
        result = ""
        initialized_here = False
        step_times = []

        try:
            # Initialize if needed
            if manage_connector and not self._initialized:
                logger.info("🔄 Agent未初始化，正在初始化...")
                await self.initialize()
                initialized_here = True
                logger.info("✅ Agent初始化完成")
            elif not self._initialized and self.auto_initialize:
                logger.info("🔄 自动初始化Agent...")
                await self.initialize()
                initialized_here = True
                logger.info("✅ Agent初始化完成")

            # Check if initialization succeeded
            if not self._agent_executor:
                logger.error("❌ MCP agent初始化失败")
                raise RuntimeError("MCP agent failed to initialize")

            steps = max_steps or self.max_steps
            if self._agent_executor:
                self._agent_executor.max_iterations = steps
                logger.info(f"⚙️ 设置最大步数为: {steps}")

            display_query = (
                query[:50].replace("\n", " ") + "..."
                if len(query) > 50
                else query.replace("\n", " ")
            )
            logger.info(f"💬 收到查询: '{display_query}'")

            # Add the user query to conversation history if memory is enabled
            if self.memory_enabled:
                self.add_to_history(HumanMessage(content=query))
                logger.info("📝 已将用户查询添加到对话历史")

            # Use the provided history or the internal history
            history_to_use = (
                external_history if external_history is not None else self._conversation_history
            )
            
            if self.verbose:
                logger.info(f"📚 对话历史中有 {len(history_to_use)} 条消息")

            # Convert messages to format expected by LangChain agent input
            # Exclude the main system message as it's part of the agent's prompt
            langchain_history = []
            for msg in history_to_use:
                if isinstance(msg, HumanMessage):
                    langchain_history.append(msg)
                elif isinstance(msg, AIMessage):
                    langchain_history.append(msg)

            intermediate_steps: list[tuple[AgentAction, str]] = []
            inputs = {"input": query, "chat_history": langchain_history}

            # Construct a mapping of tool name to tool for easy lookup
            name_to_tool_map = {tool.name: tool for tool in self._tools}
            color_mapping = get_color_mapping(
                [tool.name for tool in self._tools], excluded_colors=["green", "red"]
            )
            
            tool_names = [tool.name for tool in self._tools]
            logger.info(f"🧰 可用工具: {', '.join(tool_names)}")
            logger.info(f"🏁 开始Agent执行，最大步数={steps}")

            for step_num in range(steps):
                step_start_time = time.time()
                logger.info(f"\n----- 步骤 {step_num + 1}/{steps} -----")
                self.execution_stats["total_steps"] += 1
                
                # --- Check for tool updates if using server manager ---
                if self.use_server_manager and self.server_manager:
                    current_tools = await self.server_manager.get_all_tools()
                    current_tool_names = {tool.name for tool in current_tools}
                    existing_tool_names = {tool.name for tool in self._tools}

                    if current_tool_names != existing_tool_names:
                        logger.info(
                            f"🔄 步骤 {step_num + 1} 前工具发生变化，更新Agent。"
                            f"新工具: {', '.join(current_tool_names)}"
                        )
                        self._tools = current_tools
                        # Regenerate system message with ALL current tools
                        await self._create_system_message_from_tools(self._tools)
                        # Recreate the agent executor with the new tools and system message
                        self._agent_executor = self._create_agent()
                        self._agent_executor.max_iterations = steps
                        # Update maps for this iteration
                        name_to_tool_map = {tool.name: tool for tool in self._tools}
                        color_mapping = get_color_mapping(
                            [tool.name for tool in self._tools], excluded_colors=["green", "red"]
                        )

                # --- Plan and execute the next step ---
                try:
                    # Use the internal _atake_next_step which handles planning and execution
                    # This requires providing the necessary context like maps and intermediate steps
                    logger.info("🤔 Agent正在思考下一步行动...")
                    next_step_output = await self._agent_executor._atake_next_step(
                        name_to_tool_map=name_to_tool_map,
                        color_mapping=color_mapping,
                        inputs=inputs,
                        intermediate_steps=intermediate_steps,
                        run_manager=None,
                    )
                    
                    # Process the output
                    if isinstance(next_step_output, AgentFinish):
                        logger.info(f"✅ Agent在步骤 {step_num + 1} 完成任务")
                        result = next_step_output.return_values.get("output", "No output generated")
                        logger.info(f"📋 最终结果: {result[:50]}{'...' if len(result) > 50 else ''}")
                        break

                    # If it's actions/steps, add to intermediate steps
                    intermediate_steps.extend(next_step_output)

                    # Log tool calls
                    for action, output in next_step_output:
                        tool_name = action.tool
                        tool_input_str = str(action.tool_input)
                        
                        # 记录工具使用统计
                        if tool_name not in self.execution_stats["tool_calls"]:
                            self.execution_stats["tool_calls"][tool_name] = {
                                "count": 0,
                                "total_time": 0
                            }
                        self.execution_stats["tool_calls"][tool_name]["count"] += 1
                        
                        # 详细记录工具调用
                        tool_call_start = time.time()
                        
                        # Truncate long inputs for readability
                        if len(tool_input_str) > 50:
                            log_input = tool_input_str[:47] + "..."
                        else:
                            log_input = tool_input_str
                            
                        logger.info(f"🔧 工具调用: {tool_name}")
                        logger.info(f"📥 输入参数: {log_input}")
                        
                        # 记录完整参数（如果verbose模式）
                        if self.verbose and len(tool_input_str) > 100:
                            try:
                                # 尝试解析为JSON以便格式化输出
                                if isinstance(action.tool_input, dict):
                                    logger.info(f"📄 完整参数: {json.dumps(action.tool_input, ensure_ascii=False, indent=2)}")
                                else:
                                    logger.info(f"📄 完整参数: {tool_input_str}")
                            except:
                                logger.info(f"📄 完整参数: {tool_input_str}")
                        
                        # Truncate long outputs for readability
                        output_str = str(output)
                        if len(output_str) > 100:
                            log_output = output_str[:97] + "..."
                        else:
                            log_output = output_str
                            
                        log_output = log_output.replace("\n", " ")
                        logger.info(f"📤 工具结果: {log_output}")
                        
                        # 记录完整结果（如果verbose模式）
                        if self.verbose and len(output_str) > 100:
                            logger.info(f"📄 完整结果: {output_str[:100]}{'...' if len(output_str) > 100 else ''}")
                        
                        tool_call_time = time.time() - tool_call_start
                        self.execution_stats["tool_calls"][tool_name]["total_time"] += tool_call_time
                        logger.info(f"⏱️ 工具调用耗时: {tool_call_time:.2f}秒")

                    # Check for return_direct on the last action taken
                    if len(next_step_output) > 0:
                        last_step: tuple[AgentAction, str] = next_step_output[-1]
                        tool_return = self._agent_executor._get_tool_return(last_step)
                        if tool_return is not None:
                            logger.info(f"🏆 工具在步骤 {step_num + 1} 直接返回结果")
                            result = tool_return.return_values.get("output", "No output generated")
                            logger.info(f"📋 最终结果: {result[:100]}{'...' if len(result) > 100 else ''}")
                            break
                
                except OutputParserException as e:
                    logger.error(f"❌ 步骤 {step_num + 1} 输出解析错误: {e}")
                    result = f"Agent stopped due to a parsing error: {str(e)}"
                    break
                except Exception as e:
                    logger.error(f"❌ 步骤 {step_num + 1} 执行错误: {e}")
                    import traceback
                    traceback.print_exc()
                    result = f"Agent stopped due to an error: {str(e)}"
                    break
                
                # 记录步骤时间
                step_time = time.time() - step_start_time
                step_times.append(step_time)
                logger.info(f"⏱️ 步骤 {step_num + 1} 耗时: {step_time:.2f}秒")

            # --- Loop finished ---
            if not result:
                logger.warning(f"⚠️ Agent到达最大步数 ({steps}) 后停止")
                result = f"Agent stopped after reaching the maximum number of steps ({steps})."

            # Add the final response to conversation history if memory is enabled
            if self.memory_enabled:
                self.add_to_history(AIMessage(content=result))
                logger.info("📝 已将Agent响应添加到对话历史")

            # 记录运行统计
            run_time = time.time() - run_start_time
            self.execution_stats["execution_times"].append(run_time)
            
            logger.info(f"\n----- 执行统计 -----")
            logger.info(f"🕒 总运行时间: {run_time:.2f}秒")
            if step_times:
                avg_step_time = sum(step_times) / len(step_times)
                logger.info(f"🕒 平均每步耗时: {avg_step_time:.2f}秒")
            
            # 记录工具调用统计
            if self.execution_stats["tool_calls"]:
                logger.info(f"🔧 工具调用统计:")
                for tool_name, stats in self.execution_stats["tool_calls"].items():
                    avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
                    logger.info(f"  - {tool_name}: 调用 {stats['count']} 次，平均耗时 {avg_time:.2f}秒")
            
            logger.info("🎉 Agent执行完成")
            logger.info(f"='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='")
            return result

        except Exception as e:
            logger.error(f"❌ 执行查询时出错: {e}")
            if initialized_here and manage_connector:
                logger.info("🧹 初始化错误后清理资源")
                await self.close()
            raise

        finally:
            # Clean up if necessary (e.g., if not using client-managed sessions)
            if manage_connector and not self.client and not initialized_here:
                logger.info("🧹 查询完成后关闭Agent")
                await self.close()

    async def close(self) -> None:
        """Close the MCP connection with improved error handling."""
        logger.info("🔌 Closing agent and cleaning up resources...")
        try:
            # Clean up the agent first
            self._agent_executor = None
            self._tools = []

            # If using client with session, close the session through client
            if self.client:
                logger.info("🔄 Closing sessions through client")
                await self.client.close_all_sessions()
                self._sessions = {}
            # If using direct connector, disconnect
            elif self.connectors:
                for connector in self.connectors:
                    logger.info("🔄 Disconnecting connector")
                    await connector.disconnect()

            # Clear adapter tool cache
            if hasattr(self.adapter, "_connector_tool_map"):
                self.adapter._connector_tool_map = {}

            self._initialized = False
            logger.info("👋 Agent closed successfully")

        except Exception as e:
            logger.error(f"❌ Error during agent closure: {e}")
            # Still try to clean up references even if there was an error
            self._agent_executor = None
            self._tools = []
            self._sessions = {}
            self._initialized = False
