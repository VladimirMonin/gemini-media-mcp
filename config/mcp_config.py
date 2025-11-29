"""Конфигурация MCP сервера и клиента.

Классы:
    MCPServerConfig
        Конфигурация сервера MCP.

    MCPClientConfig
        Конфигурация клиента MCP с серверами.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class MCPServerConfig(BaseModel):
    """Конфигурация MCP сервера.

    Attributes:
        command: Команда для запуска сервера.
        args: Аргументы командной строки.
        env: Переменные окружения.
    """

    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPClientConfig(BaseModel):
    """Конфигурация MCP клиента.

    Attributes:
        mcp_servers: Словарь серверов MCP.
    """

    mcp_servers: Dict[str, MCPServerConfig] = Field(..., alias="mcpServers")

    class Config:
        allow_population_by_field_name = True
