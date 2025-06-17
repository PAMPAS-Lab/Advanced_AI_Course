"""
Client for managing MCP servers and sessions.

This module provides a high-level client that manages MCP servers, connectors,
and sessions from configuration.
"""

import json
import time
from typing import Any

from .config import create_connector_from_config, load_config_file
from .logging import logger
from .session import MCPSession


class MCPClient:
    """Client for managing MCP servers and sessions.

    This class provides a unified interface for working with MCP servers,
    handling configuration, connector creation, and session management.
    """

    def __init__(
        self,
        config: str | dict[str, Any] | None = None,
        verbose: bool = False,
    ) -> None:
        """Initialize a new MCP client.

        Args:
            config: Either a dict containing configuration or a path to a JSON config file.
                   If None, an empty configuration is used.
            verbose: Whether to enable verbose logging for this client.
        """
        self.config: dict[str, Any] = {}
        self.sessions: dict[str, MCPSession] = {}
        self.active_sessions: list[str] = []
        self.verbose = verbose
        self.request_counter = 0
        self.start_time = time.time()

        # Load configuration if provided
        if config is not None:
            if isinstance(config, str):
                logger.info(f"🔄 从配置文件加载MCP客户端: {config}")
                self.config = load_config_file(config)
                if self.verbose:
                    logger.info(f"📄 配置详情: {json.dumps(self.config, ensure_ascii=False, indent=2)}")
            else:
                logger.info("🔄 从字典加载MCP客户端配置")
                self.config = config
                if self.verbose:
                    logger.info(f"📄 配置详情: {json.dumps(self.config, ensure_ascii=False, indent=2)}")
            
            # 打印已配置的服务器
            servers = self.config.get("mcpServers", {})
            logger.info(f"ℹ️ 已配置 {len(servers)} 个MCP服务器: {', '.join(servers.keys())}")

    @classmethod
    def from_dict(cls, config: dict[str, Any], verbose: bool = False) -> "MCPClient":
        """Create a MCPClient from a dictionary.

        Args:
            config: The configuration dictionary.
            verbose: Whether to enable verbose logging.
        """
        logger.info("🔄 从字典创建MCPClient实例")
        return cls(config=config, verbose=verbose)

    @classmethod
    def from_config_file(cls, filepath: str, verbose: bool = False) -> "MCPClient":
        """Create a MCPClient from a configuration file.

        Args:
            filepath: The path to the configuration file.
            verbose: Whether to enable verbose logging.
        """
        logger.info(f"🔄 从配置文件创建MCPClient实例: {filepath}")
        return cls(config=load_config_file(filepath), verbose=verbose)

    def add_server(
        self,
        name: str,
        server_config: dict[str, Any],
    ) -> None:
        """Add a server configuration.

        Args:
            name: The name to identify this server.
            server_config: The server configuration.
        """
        logger.info(f"➕ 添加服务器配置: {name}")
        if self.verbose:
            logger.info(f"📄 服务器配置详情: {json.dumps(server_config, ensure_ascii=False, indent=2)}")
            
        if "mcpServers" not in self.config:
            self.config["mcpServers"] = {}

        self.config["mcpServers"][name] = server_config

    def remove_server(self, name: str) -> None:
        """Remove a server configuration.

        Args:
            name: The name of the server to remove.
        """
        logger.info(f"➖ 移除服务器配置: {name}")
        if "mcpServers" in self.config and name in self.config["mcpServers"]:
            del self.config["mcpServers"][name]

            # If we removed an active session, remove it from active_sessions
            if name in self.active_sessions:
                self.active_sessions.remove(name)
                logger.info(f"ℹ️ 已从活动会话列表中移除 {name}")

    def get_server_names(self) -> list[str]:
        """Get the list of configured server names.

        Returns:
            List of server names.
        """
        servers = list(self.config.get("mcpServers", {}).keys())
        logger.info(f"ℹ️ 已配置的服务器: {', '.join(servers)}")
        return servers

    def save_config(self, filepath: str) -> None:
        """Save the current configuration to a file.

        Args:
            filepath: The path to save the configuration to.
        """
        logger.info(f"💾 保存配置到文件: {filepath}")
        with open(filepath, "w") as f:
            json.dump(self.config, f, indent=2)
        logger.info("✅ 配置已保存")

    async def create_session(self, server_name: str, auto_initialize: bool = True) -> MCPSession:
        """Create a session for the specified server.

        Args:
            server_name: The name of the server to create a session for.

        Returns:
            The created MCPSession.

        Raises:
            ValueError: If no servers are configured or the specified server doesn't exist.
        """
        logger.info(f"🔌 创建 {server_name} 的会话")
        start_time = time.time()
        
        # Get server config
        servers = self.config.get("mcpServers", {})
        if not servers:
            logger.error("❌ 配置中未定义MCP服务器")
            raise ValueError("No MCP servers defined in config")

        if server_name not in servers:
            logger.error(f"❌ 配置中未找到服务器 '{server_name}'")
            raise ValueError(f"Server '{server_name}' not found in config")

        server_config = servers[server_name]
        if self.verbose:
            logger.info(f"📄 服务器 {server_name} 配置: {json.dumps(server_config, ensure_ascii=False, indent=2)}")
            
        logger.info(f"🔄 正在为 {server_name} 创建连接器")
        connector = create_connector_from_config(server_config)

        # Create the session
        logger.info(f"🔄 正在为 {server_name} 创建会话")
        session = MCPSession(connector)
        if auto_initialize:
            logger.info(f"🔄 正在初始化 {server_name} 会话")
            await session.initialize()
            logger.info(f"✅ {server_name} 会话初始化完成")
        self.sessions[server_name] = session

        # Add to active sessions
        if server_name not in self.active_sessions:
            self.active_sessions.append(server_name)
            logger.info(f"➕ 已将 {server_name} 添加到活动会话列表")

        elapsed = time.time() - start_time
        logger.info(f"⏱️ 创建会话耗时: {elapsed:.2f}秒")
        return session

    async def create_all_sessions(
        self,
        auto_initialize: bool = True,
    ) -> dict[str, MCPSession]:
        """Create a session for the specified server.

        Args:
            auto_initialize: Whether to automatically initialize the session.

        Returns:
            The created MCPSession. If server_name is None, returns the first created session.

        Raises:
            ValueError: If no servers are configured or the specified server doesn't exist.
        """
        logger.info("🔄 创建所有服务器的会话")
        start_time = time.time()
        
        # Get server config
        servers = self.config.get("mcpServers", {})
        if not servers:
            logger.error("❌ 配置中未定义MCP服务器")
            raise ValueError("No MCP servers defined in config")

        # Create sessions for all servers
        for name in servers:
            logger.info(f"🔄 创建 {name} 的会话")
            session = await self.create_session(name, auto_initialize)
            if auto_initialize:
                logger.info(f"✅ {name} 会话初始化完成")

        elapsed = time.time() - start_time
        logger.info(f"⏱️ 创建所有会话耗时: {elapsed:.2f}秒")
        logger.info(f"✅ 共创建了 {len(servers)} 个会话")
        return self.sessions

    def get_session(self, server_name: str) -> MCPSession:
        """Get an existing session.

        Args:
            server_name: The name of the server to get the session for.
                        If None, uses the first active session.

        Returns:
            The MCPSession for the specified server.

        Raises:
            ValueError: If no active sessions exist or the specified session doesn't exist.
        """
        if server_name not in self.sessions:
            logger.error(f"❌ 服务器 '{server_name}' 不存在会话")
            raise ValueError(f"No session exists for server '{server_name}'")

        logger.info(f"ℹ️ 获取 {server_name} 的会话")
        return self.sessions[server_name]

    def get_all_active_sessions(self) -> dict[str, MCPSession]:
        """Get all active sessions.

        Returns:
            Dictionary mapping server names to their MCPSession instances.
        """
        active_sessions = {name: self.sessions[name] for name in self.active_sessions if name in self.sessions}
        logger.info(f"ℹ️ 获取所有活动会话，共 {len(active_sessions)} 个: {', '.join(active_sessions.keys())}")
        return active_sessions

    async def close_session(self, server_name: str) -> None:
        """Close a session.

        Args:
            server_name: The name of the server to close the session for.
                        If None, uses the first active session.

        Raises:
            ValueError: If no active sessions exist or the specified session doesn't exist.
        """
        # Check if the session exists
        if server_name not in self.sessions:
            logger.warning(f"⚠️ 服务器 '{server_name}' 不存在会话，无需关闭")
            return

        logger.info(f"🔌 正在关闭 {server_name} 的会话")
        start_time = time.time()
        
        # Get the session
        session = self.sessions[server_name]

        try:
            # Disconnect from the session
            logger.info(f"🔄 正在断开 {server_name} 的连接")
            await session.disconnect()
            logger.info(f"✅ {server_name} 断开连接成功")
        except Exception as e:
            logger.error(f"❌ 关闭 {server_name} 会话时出错: {e}")
        finally:
            # Remove the session regardless of whether disconnect succeeded
            del self.sessions[server_name]
            logger.info(f"🗑️ 已移除 {server_name} 的会话实例")

            # Remove from active_sessions
            if server_name in self.active_sessions:
                self.active_sessions.remove(server_name)
                logger.info(f"➖ 已从活动会话列表中移除 {server_name}")
            
            elapsed = time.time() - start_time
            logger.info(f"⏱️ 关闭会话耗时: {elapsed:.2f}秒")

    async def close_all_sessions(self) -> None:
        """Close all active sessions.

        This method ensures all sessions are closed even if some fail.
        """
        logger.info("🔌 正在关闭所有活动会话")
        start_time = time.time()
        
        # Get a list of all session names first to avoid modification during iteration
        server_names = list(self.sessions.keys())
        errors = []

        for server_name in server_names:
            try:
                logger.info(f"🔄 正在关闭 {server_name} 的会话")
                await self.close_session(server_name)
                logger.info(f"✅ {server_name} 会话已关闭")
            except Exception as e:
                error_msg = f"Failed to close session for server '{server_name}': {e}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)

        # Log summary if there were errors
        if errors:
            logger.error(f"❌ 关闭会话时遇到 {len(errors)} 个错误")
        else:
            elapsed = time.time() - start_time
            logger.info(f"⏱️ 关闭所有会话耗时: {elapsed:.2f}秒")
            logger.info("✅ 所有会话已成功关闭")
            
        # 记录客户端使用统计
        total_time = time.time() - self.start_time
        logger.info(f"📊 MCP客户端使用统计:")
        logger.info(f"   - 总运行时间: {total_time:.2f}秒")
        logger.info(f"   - 请求计数: {self.request_counter}")
        if self.request_counter > 0:
            logger.info(f"   - 平均每个请求耗时: {total_time/self.request_counter:.2f}秒")
