"""
Base connector for MCP implementations.

This module provides the base connector interface that all MCP connectors
must implement.
"""

from abc import ABC, abstractmethod
from typing import Any
import json
import time

from mcp import ClientSession
from mcp.types import CallToolResult, Tool

from ..logging import logger
from ..task_managers import ConnectionManager


class BaseConnector(ABC):
    """Base class for MCP connectors.

    This class defines the interface that all MCP connectors must implement.
    """

    def __init__(self):
        """Initialize base connector with common attributes."""
        self.client: ClientSession | None = None
        self._connection_manager: ConnectionManager | None = None
        self._tools: list[Tool] | None = None
        self._connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the MCP implementation."""
        pass

    async def disconnect(self) -> None:
        """Close the connection to the MCP implementation."""
        if not self._connected:
            logger.debug("Not connected to MCP implementation")
            return

        logger.debug("Disconnecting from MCP implementation")
        await self._cleanup_resources()
        self._connected = False
        logger.debug("Disconnected from MCP implementation")

    async def _cleanup_resources(self) -> None:
        """Clean up all resources associated with this connector."""
        errors = []

        # First close the client session
        if self.client:
            try:
                logger.debug("Closing client session")
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                error_msg = f"Error closing client session: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
            finally:
                self.client = None

        # Then stop the connection manager
        if self._connection_manager:
            try:
                logger.debug("Stopping connection manager")
                await self._connection_manager.stop()
            except Exception as e:
                error_msg = f"Error stopping connection manager: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
            finally:
                self._connection_manager = None

        # Reset tools
        self._tools = None

        if errors:
            logger.warning(f"Encountered {len(errors)} errors during resource cleanup")

    async def initialize(self) -> dict[str, Any]:
        """Initialize the MCP session and return session information."""
        if not self.client:
            raise RuntimeError("MCP client is not connected")

        logger.debug("Initializing MCP session")

        # Initialize the session
        result = await self.client.initialize()

        # Get available tools
        tools_result = await self.client.list_tools()
        self._tools = tools_result.tools

        logger.debug(f"MCP session initialized with {len(self._tools)} tools")

        return result

    @property
    def tools(self) -> list[Tool]:
        """Get the list of available tools."""
        if not self._tools:
            raise RuntimeError("MCP client is not initialized")
        return self._tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Call an MCP tool with the given arguments."""
        if not self.client:
            raise RuntimeError("MCP client is not connected")

        logger.debug(f"Calling tool '{name}' with arguments: {arguments}")
        result = await self.client.call_tool(name, arguments)
        logger.debug(f"Tool '{name}' called with result: {result}")
        return result

    async def list_resources(self) -> list[dict[str, Any]]:
        """List all available resources from the MCP implementation."""
        if not self.client:
            raise RuntimeError("MCP client is not connected")

        logger.debug("Listing resources")
        resources = await self.client.list_resources()
        return resources

    async def read_resource(self, uri: str) -> tuple[bytes, str]:
        """Read a resource by URI."""
        if not self.client:
            raise RuntimeError("MCP client is not connected")

        logger.debug(f"Reading resource: {uri}")
        resource = await self.client.read_resource(uri)
        return resource.content, resource.mimeType

    async def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a raw request to the MCP implementation."""
        if not self.client:
            raise RuntimeError("MCP client is not connected")

        logger.debug(f"Sending request: {method} with params: {params}")
        # 直接发送JSON-RPC请求对象到客户端
        request_obj = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": str(id(self)) + "-" + str(time.time())
        }
        # 使用_write_stream发送请求，通过_read_stream接收响应
        if hasattr(self.client, "_write_stream") and hasattr(self.client, "_read_stream"):
            await self.client._write_stream.write(json.dumps(request_obj))
            response_text = await self.client._read_stream.readline()
            return json.loads(response_text).get("result", {})
        else:
            # 尝试使用ClientSession的一些可能存在的方法
            try:
                if hasattr(self.client, "send"):
                    return await self.client.send(request_obj)
                elif hasattr(self.client, "call"):
                    return await self.client.call(method, params or {})
                else:
                    raise NotImplementedError("找不到合适的方法发送请求")
            except Exception as e:
                logger.error(f"发送请求失败: {e}")
                raise
