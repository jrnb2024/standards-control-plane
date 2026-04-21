# WP-SCP-020 — Research citations

Primary-source evidence underpinning D-022 (federation-primitive adoption)
and D-023 (proposal-queue adoption; chat-forum rejection). Compiled from
the 2026-04-21 multi-agent strategy research session.

## Multi-agent SDLC architecture patterns

- Anthropic engineering, *How we built our multi-agent research system* —
  <https://www.anthropic.com/engineering/multi-agent-research-system>.
  Supervisor/worker pattern; reports ~15× token cost vs single-turn and
  explicit coordination-error compounding without heavy prompt discipline.
- Anthropic research, *Building effective agents* —
  <https://www.anthropic.com/research/building-effective-agents>.
- InfoQ, *Anthropic three-agent harness (April 2026)* —
  <https://www.infoq.com/news/2026/04/anthropic-three-agent-harness-ai/>.
- InfoQ, *Anthropic Managed Agents* —
  <https://www.infoq.com/news/2026/04/anthropic-managed-agents/>.
- LangGraph supervisor —
  <https://github.com/langchain-ai/langgraph-supervisor-py>.
- Databricks, *Supervisor Agent architecture* —
  <https://www.databricks.com/blog/multi-agent-supervisor-architecture-orchestrating-enterprise-ai-scale>.

## Agent protocols (MCP + A2A)

- Google, *Announcing A2A* —
  <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/>.
- `a2aproject/A2A` GitHub —
  <https://github.com/a2aproject/A2A>.
- byteiota, *Microsoft Agent Framework 1.0, MCP + A2A converge* —
  <https://byteiota.com/microsoft-agent-framework-1-0-ships-mcp-a2a-converge/>.
- philippdubach, *MCP vs A2A in 2026* —
  <https://philippdubach.com/posts/mcp-vs-a2a-in-2026-how-the-ai-protocol-war-ends/>.

**Relevance to D-022:** MCP is the stable vertical agent-to-tool protocol.
SCP's MCP server (WP-SCP-021) sits cleanly in this ecosystem.

## Policy-as-code (D-022 mechanism)

- Open Policy Agent, *CI/CD docs* —
  <https://www.openpolicyagent.org/docs/cicd>.
- `open-policy-agent/setup-opa` —
  <https://github.com/open-policy-agent/setup-opa>.
- OPA Action (Marketplace) —
  <https://github.com/marketplace/actions/opa-action>.
- Teleport, *Benchmarking policy languages (Rego, Cedar, OpenFGA)* —
  <https://goteleport.com/blog/benchmarking-policy-languages/>. Rego is
  expressive but error-prone; stricter alternatives faster but narrower.
- TachTech, *Sentinel and OPA policies (2025-10)* —
  <https://engineering.tachtech.net/devsecops/2025/10/15/sentinel-and-opa-policies.html>.
- policyascode.dev, *OPA vs Sentinel* —
  <https://policyascode.dev/guides/opa-vs-sentinel-enterprise/>.
- Permit.io, *OPA vs Cedar* — <https://www.permit.io/blog/opa-vs-cedar>.
- StrongDM, *Cedar Policy Language 2026 guide* —
  <https://www.strongdm.com/cedar-policy-language>.

## Pre-merge gate shape (D-022 mechanism)

- `palantir/policy-bot` — <https://github.com/palantir/policy-bot>.
  Rejected in D-022: requires GitHub App per org, HCL-not-Rego, no
  Renovate cascade, no native waiver-overlay.

## Standards propagation across polyrepo (D-022 cascade)

- Renovate, *bot comparison / presets* —
  <https://docs.renovatebot.com/bot-comparison/>. Shared preset
  propagation primitive.
- Backstage, *Tech Insights plugin* (Roadie) —
  <https://roadie.io/backstage/plugins/tech-insights/>.
- Backstage community Tech Insights —
  <https://github.com/backstage/community-plugins/blob/main/workspaces/tech-insights/plugins/tech-insights/README.md>.
- Port, *Top 5 Backstage plugins 2025* —
  <https://www.port.io/blog/top-5-backstage-plugins>.
- Backstage, *Scaffolder template propagation issue #31361* —
  <https://github.com/backstage/backstage/issues/31361>. Scaffolder is
  static post-scaffold — do not rely for ongoing drift control.
- OpenSSF Scorecard — <https://scorecard.dev/>.
- `ossf/scorecard` — <https://github.com/ossf/scorecard>.

## Agent debate and the chat-forum rejection (D-023)

- Du et al., *Improving factuality and reasoning in language models
  through multiagent debate* (ICML 2024, arXiv 2305.14325) —
  <https://arxiv.org/abs/2305.14325>. Agents converge to consensus fast
  *including when the consensus is wrong*.
- Du et al. project page —
  <https://composable-models.github.io/llm_debate/>.
- AutoGen paper (arXiv 2308.08155) —
  <https://arxiv.org/abs/2308.08155>.
- AutoGen, *Multi-agent Conversation Framework docs* —
  <https://microsoft.github.io/autogen/docs/Use-Cases/agent_chat/>.

## Human-on-the-loop (D-023 adjudication pattern)

- ByteBridge, *Human-in-the-loop to Human-on-the-loop* —
  <https://bytebridge.medium.com/from-human-in-the-loop-to-human-on-the-loop-evolving-ai-agent-autonomy-c0ae62c3bf91>.
- Thoughtworks, *Cybernetics and the human-on-the-loop in agentic coding* —
  <https://www.thoughtworks.com/insights/blog/generative-ai/cybernetics-and-human-on-the-loop-in-agentic-coding>.
- MindStudio, *Iterative Kanban pattern for AI agents* —
  <https://www.mindstudio.ai/blog/iterative-kanban-pattern-ai-agents-feedback-loop>.

## Guardrails

- NVIDIA NeMo Guardrails —
  <https://developer.nvidia.com/nemo-guardrails>.
- HyperFRAME, *NVIDIA NemoClaw analysis* —
  <https://hyperframeresearch.com/2026/03/24/nvidia-nemoclaw-engineering-autonomy-within-enterprise-guardrails/>.

## Claude Code agent-enforcement surface (WP-SCP-021 foundation)

- Claude Code, *Hooks guide* —
  <https://code.claude.com/docs/en/hooks-guide>. Client-side pre-commit
  enforcement; pairs with server-side required status check for belt +
  braces.
