from __future__ import annotations

import asyncio
import json

import mcp.types as mcp_types
from mcp.server.lowlevel import server as lowlevel_server
from mcp.shared.context import RequestContext

from .conftest import commit_file


class _FakeSession:
    def __init__(self) -> None:
        self.updated_uris: list[str] = []

    async def send_resource_updated(self, uri) -> None:
        self.updated_uris.append(str(uri))


def test_resource_update_notifications_are_emitted_on_commit(resource_repo, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import register_resources
    from standards_control_plane.mcp_server.server import _load_fastmcp

    async def exercise() -> None:
        fast_mcp = _load_fastmcp()
        server = fast_mcp(name="test-notifications")
        register_resources(server, repo_root=resource_repo, now_func=lambda: fixed_now)

        options = server._mcp_server.create_initialization_options()
        assert options.capabilities.resources is not None
        assert options.capabilities.resources.subscribe is True
        assert options.capabilities.resources.listChanged is True

        session = _FakeSession()
        request_context = RequestContext(
            request_id=1,
            meta=None,
            session=session,
            lifespan_context=None,
        )
        token = lowlevel_server.request_ctx.set(request_context)
        try:
            subscribe_handler = server._mcp_server.request_handlers[mcp_types.SubscribeRequest]
            await subscribe_handler(
                mcp_types.SubscribeRequest(
                    params=mcp_types.SubscribeRequestParams(uri="scp://rules/registry"),
                )
            )
        finally:
            lowlevel_server.request_ctx.reset(token)

        before = json.loads((await server.read_resource("scp://rules/registry"))[0].content)
        commit_file(
            resource_repo,
            "standards/governance/index.json",
            json.dumps(
                {
                    "domain": "governance",
                    "version": "1.1.0",
                    "status": "active",
                    "rules": [
                        {
                            "rule_id": "GOV-001",
                            "domain": "governance",
                            "title": "Governance rule updated",
                            "summary": "Governance summary",
                            "path": "rules/GOV-001.md",
                            "severity_default": "high",
                            "scope": ["all"],
                            "signals": ["missing review evidence"],
                            "exceptions": [],
                            "related_patterns": [],
                            "version": "1.1.0",
                            "status": "active",
                            "applies_to": ["docs/**/*.md", "docs/DECISIONS.md"],
                        }
                    ],
                    "patterns": [],
                },
                indent=2,
            )
            + "\n",
            "WP-SCP-022 notification coverage",
        )
        after = json.loads((await server.read_resource("scp://rules/registry"))[0].content)
        await asyncio.sleep(0)

        assert before["registry"]["domains"]["governance"]["rules"][0]["title"] == "Governance rule"
        assert after["registry"]["domains"]["governance"]["rules"][0]["title"] == "Governance rule updated"
        assert session.updated_uris == ["scp://rules/registry"]

