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
    """Stdio MCP server scaffold with tools and resources registered."""

    name: str = "standards-control-plane"
    package_version: str = __version__
    profile: str = "legacy"
    instructions: str = field(init=False)
    _server: "FastMCP" = field(init=False, repr=False)

    _LEGACY_INSTRUCTIONS = (
        "Standards Control Plane MCP server. "
        "Tools: consult_rules, check_waiver, list_open_decisions, check_finding, "
        "audit_changed, resolve_domain, propose, consult_scorecard. "
        "Resources (11 URI types): scp://rules/registry, scp://rules/domain-map, "
        "scp://decisions, scp://findings/open, scp://waivers, scp://status, "
        "scp://rule/<id>, scp://waiver/<id>, scp://finding/<id>, "
        "scp://decision/<D-NNN>, scp://security/signing-keys. "
        "All resources reflect committed state only. Errors follow the SCP-MCP-E0NN "
        "catalogue at docs/integrations/mcp-error-codes.md."
    )
    _ESTATE_INSTRUCTIONS = (
        "Standards Control Plane Estate read-only MCP profile. Tools are restricted to "
        "consult_rules, check_waiver, list_open_decisions, check_finding, resolve_domain, "
        "and consult_scorecard. propose and audit_changed are unavailable. Committed-state "
        "resources are read-only. This profile has no action authority and cannot mutate, "
        "admit, merge, deploy, or administer anything."
    )

    def __post_init__(self) -> None:
        if self.profile == "legacy":
            self.instructions = self._LEGACY_INSTRUCTIONS
        elif self.profile == "estate-read-only":
            self.instructions = self._ESTATE_INSTRUCTIONS
        else:
            raise ValueError(f"unsupported SCP MCP profile: {self.profile}")
        fast_mcp = _load_fastmcp()
        self._server = fast_mcp(
            name=self.name,
            instructions=self.instructions,
        )
        from .resources import register_resources
        from .tools import register_tools

        register_tools(self._server, profile=self.profile)
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
                "profile": self.profile,
            },
            "tools": _serialise_listing(tools),
            "resources": _serialise_listing(resources),
        }

    def run_stdio(self) -> None:
        self.server.run(transport="stdio")
