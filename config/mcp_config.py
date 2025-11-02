from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class MCPServerConfig(BaseModel):
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None

class MCPClientConfig(BaseModel):
    mcp_servers: Dict[str, MCPServerConfig] = Field(..., alias="mcpServers")

    class Config:
        allow_population_by_field_name = True
