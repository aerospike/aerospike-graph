from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GremlinConfig:
    host: str = "localhost"
    port: int = 8182
    traversal_source: str = "g"

    @classmethod
    def from_env(cls) -> GremlinConfig:
        return cls(
            host=os.environ.get("GREMLIN_HOST", "localhost"),
            port=int(os.environ.get("GREMLIN_PORT", "8182")),
            traversal_source=os.environ.get("GREMLIN_TRAVERSAL_SOURCE", "g"),
        )

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}/gremlin"


@dataclass(frozen=True)
class TenantConfig:
    tenant_id: str
    name: str
    root_path: str
    languages: list[str] = field(default_factory=lambda: ["python"])

    @classmethod
    def from_dict(cls, data: dict) -> TenantConfig:
        return cls(
            tenant_id=data["tenant_id"],
            name=data["name"],
            root_path=data["root_path"],
            languages=data.get("languages", ["python"]),
        )


@dataclass(frozen=True)
class ServerConfig:
    gremlin: GremlinConfig = field(default_factory=GremlinConfig.from_env)
    transport: str = "stdio"
    http_port: int = 8000

    @classmethod
    def from_env(cls) -> ServerConfig:
        return cls(
            gremlin=GremlinConfig.from_env(),
            transport=os.environ.get("MCP_TRANSPORT", "stdio"),
            http_port=int(os.environ.get("MCP_HTTP_PORT", "8000")),
        )
