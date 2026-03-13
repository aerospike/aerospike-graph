"""
Abstract retriever interface.

Designed so graph-based retrieval works now and vector-based
retrieval can be plugged in later without changing callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievalResult:
    entity_id: str
    label: str
    name: str
    qualified_name: str = ""
    path: str = ""
    score: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    relationships: list[dict[str, str]] = field(default_factory=list)

    def to_context_string(self) -> str:
        parts = [f"[{self.label}] {self.qualified_name or self.name}"]
        if self.path:
            parts.append(f"  file: {self.path}")
        if self.properties.get("signature"):
            parts.append(f"  signature: {self.properties['signature']}")
        if self.properties.get("docstring"):
            doc = self.properties["docstring"][:200]
            parts.append(f"  docstring: {doc}")
        if self.properties.get("content"):
            content = self.properties["content"][:300]
            parts.append(f"  content: {content}")
        for rel in self.relationships[:5]:
            parts.append(f"  -> {rel['edge']} -> {rel['target']}")
        return "\n".join(parts)


class Retriever(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        tenant_id: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        ...

    @abstractmethod
    def get_dependencies(
        self,
        entity_name: str,
        tenant_id: str,
        direction: str = "both",
        depth: int = 2,
    ) -> list[RetrievalResult]:
        ...

    @abstractmethod
    def get_file_context(
        self,
        file_path: str,
        tenant_id: str,
    ) -> list[RetrievalResult]:
        ...

    @abstractmethod
    def get_architecture(
        self,
        tenant_id: str,
        module: str | None = None,
    ) -> list[RetrievalResult]:
        ...

    @abstractmethod
    def get_call_graph(
        self,
        function_name: str,
        tenant_id: str,
        depth: int = 3,
    ) -> list[RetrievalResult]:
        ...

    @abstractmethod
    def get_related(
        self,
        entity_name: str,
        tenant_id: str,
        limit: int = 20,
    ) -> list[RetrievalResult]:
        ...
