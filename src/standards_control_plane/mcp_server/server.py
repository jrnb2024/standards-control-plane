"""MCP server scaffold for the Standards Control Plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from standards_control_plane import __version__

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class MissingMcpDependencyError(RuntimeError):
    """Raised when the optional MCP runtime dependencies are unavailable."""


def _load_fastmcp() -> type["FastMCP"]:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:  # pragma: no cover - exercised without extras only
        raise MissingMcpDependencyError(
            "The MCP server requires the optional 'mcp' extra. "
            "Install standards-control-plane[mcp]."
        ) from error
    return FastMCP


def _serialise_listing(items: list[Any]) -> list[Any]:
    payload: list[Any] = []
    for item in items:
        if hasattr(item, "model_dump"):
            payload.append(item.model_dump(mode="json"))
        else:
            payload.append(item)
    return payload


@dataclass(slots=True)
class ScpMcpServer:
    """Stdio MCP server scaffold with empty tools and resources for slice 021B."""

    name: str = "standards-control-plane"
    package_version: str = __version__
    instructions: str = (
        "Standards Control Plane MCP scaffold. Tools and resources are introduced "
        "in later implementation slices."
    )
    _server: "FastMCP" = field(init=False, repr=False)

    def __post_init__(self) -> None:
        fast_mcp = _load_fastmcp()
        self._server = fast_mcp(
            name=self.name,
            instructions=self.instructions,
        )
        from .resources import register_resources
        from .tools import register_tools

        register_tools(self._server)
        register_resources(self._server)

    @property
    def server(self) -> "FastMCP":
        return self._server

    async def handshake_payload(self) -> dict[str, Any]:
        tools = await self.server.list_tools()
        resources = await self.server.list_resources()
        return {
            "server": {
                "name": self.name,
                "version": self.package_version,
            },
            "tools": _serialise_listing(tools),
            "resources": _serialise_listing(resources),
        }

    def run_stdio(self) -> None:
        self.server.run(transport="stdio")
