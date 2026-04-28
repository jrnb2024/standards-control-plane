"""MCP server scaffold for the Standards Control Plane."""

from standards_control_plane import __version__

from .server import ScpMcpServer

__all__ = ["ScpMcpServer", "__version__"]
