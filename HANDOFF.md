# Helm Agent Handoff

## Project Goal

Helm Agent is intended to become a private-deployment, human-in-the-loop, multi-agent collaboration framework inspired by Hermes Agent and harness engineering.

The current implementation is version `0.0.1`: a small but extensible backbone that can be continued on another machine.

## Design Direction

The project should start simple, borrowing the strongest parts of Hermes Agent rather than building a heavy multi-agent platform immediately.

Core positioning:

```text
Helm Agent v0.0.1
= Private Agent Workbench
+ Hermes-style Runtime Loop
+ Lightweight TaskGraph
+ Profile-based Agents
+ Ad-hoc Delegation
+ Web Human Feedback
```

Key principles:

- `runtime` owns the agent loop.
- `context` owns prompt/context assembly.
- `profiles` define who an agent is.
- `skills` define what capabilities can be loaded.
- `tools` define what actions the model can call.
- `taskgraph` structures work.
- `web` is the only first-class interface for v0.
- Human-in-the-loop means key checkpoints and feedback, not approval for every tiny step.

## Architecture Decisions

### Runtime Instead of Agent Module

The Hermes-style `AIAgent` idea is represented as `helm/runtime`.

`runtime` runs a generic agent loop:

- build messages through `context`
- call a provider
- pass OpenAI-compatible tool schemas
- execute tool calls
- feed tool results back to the model
- return a `RuntimeResult`

Agent identities are not classes. They are profile files.

### Context Owns Prompt Assembly

`helm/context` currently has both:

- `prompt_builder.py`
- `context_builder.py`

They are intentionally kept separate for now:

- `PromptBuilder` builds the system prompt from profile/soul/memory/skills.
- `ContextBuilder` resolves profile and skills, then creates provider messages.

### Profiles Define Agents

Built-in profiles live under:

```text
helm/profiles/builtin/
```

Current built-ins:

- `default`
- `planner`
- `executor`
- `reviewer`

Each profile may have:

```text
config.yaml
profile.md
soul.md
memory.md
```

Users should eventually be able to add project-level custom profiles under:

```text
profiles/<agent-id>/
```

### Skills Are Capability Packages

Skills are not just prompt snippets. They are intended to become capability packages, like a future `pptx` skill that can create, edit, render, and verify PowerPoint files.

Current built-in skills:

- `task-planning`
- `code-execution`
- `code-review`
- `private-deployment`

Skills are loaded into the prompt when activated by a profile, task, delegation, or Web request.

### Tools Are Callable Actions

Tools are registered in `helm/tools`.

Current tools:

- `filesystem.list`
- `filesystem.read`
- `filesystem.write`
- `shell.run`
- `git.status`
- `git.diff`
- `delegate_task`

OpenAI-compatible tool names use underscores:

```text
filesystem.read -> filesystem_read
filesystem.list -> filesystem_list
shell.run       -> shell_run
```

The registry maps external names back to internal names.

### Delegation

The intended design supports two delegation modes:

1. Profile-based delegation:
   use a user-defined child profile.

2. Hermes-style ad-hoc delegation:
   spawn a temporary isolated child agent from a goal/context without requiring a user-defined profile.

The v0 skeleton exists in:

```text
helm/runtime/delegation.py
helm/tools/delegate.py
```

This is not yet deeply exercised in the Web UI.

### TaskGraph

TaskGraph is included in v0 as a lightweight DAG, not a workflow engine.

Files:

```text
helm/taskgraph/models.py
helm/taskgraph/planner.py
helm/taskgraph/executor.py
helm/taskgraph/serializer.py
```

Current planner is intentionally simple and creates a two-step plan:

1. Clarify execution plan
2. Execute user goal

## Current Implementation Status

Implemented:

- Python package skeleton
- FastAPI Web test page
- OpenAI-compatible local model provider
- Official OpenAI SDK integration
- `trust_env=False` HTTP client to avoid local-network requests going through proxy
- Profile injection
- Skill injection
- Tool schema injection
- Tool call execution
- Tool result feedback into model
- Execution log in Web UI
- Optional display of tool return content
- Lightweight TaskGraph
- Built-in profiles and skills
- Filesystem, shell, git tools
- Local model smoke test
- Pytest test suite

Current local model used during development:

```text
base_url: http://192.168.1.18:16666/v1
model: qwen3
api_key: EMPTY
```

For qwen3, the Web page and smoke script pass:

```json
{
  "chat_template_kwargs": {
    "enable_thinking": false
  }
}
```

through `extra_body`.

## Current Web Behavior

The Web test page is served at:

```text
http://127.0.0.1:8000
```

It supports configuring:

- Base URL
- Model
- API key
- Profile
- Skills
- Toolsets
- Max tokens
- Temperature
- Enable thinking
- Prompt
- Show tool results

The response shows:

- final model output
- effective config
- execution log

Execution log includes:

- runtime start
- active profile
- active skills
- active toolsets
- tools passed to model
- provider completions
- tool calls
- tool arguments
- tool success/failure

## Important Recent Fixes

### Local OpenAI-compatible Provider

The official OpenAI SDK initially returned 502 against the local model because environment proxy settings affected LAN traffic.

Fix:

```python
httpx.AsyncClient(trust_env=False)
```

is passed to `AsyncOpenAI`.

### Tool Call Failure

The model originally called `shell_run` with `ls`, which failed on Windows.

Fixes:

- Added `filesystem.list`.
- Improved Windows `shell.run` to use PowerShell.
- Tool failures are fed back to the model instead of immediately failing the runtime.

### Web JSON Error

The page once showed:

```text
SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON
```

Cause:

The frontend tried to parse FastAPI's plain-text `Internal Server Error` as JSON.

Fixes:

- `/api/model/test` catches exceptions and returns JSON failure payloads.
- Frontend now handles non-JSON HTTP responses gracefully.

## Key Files

```text
helm/web/api/app.py
helm/runtime/loop.py
helm/runtime/tool_dispatcher.py
helm/providers/openai_compatible.py
helm/context/context_builder.py
helm/context/prompt_builder.py
helm/tools/registry.py
helm/tools/filesystem.py
helm/tools/shell.py
helm/taskgraph/models.py
helm/run_service.py
examples/local_model_smoke.py
tests/
```

## Verification Commands

From the repo root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected current result:

```text
11 passed
```

Local model smoke:

```powershell
.\.venv\Scripts\python.exe examples\local_model_smoke.py
```

Start Web:

```powershell
.\.venv\Scripts\python.exe -m uvicorn helm.web.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

## Suggested Next Steps

Good next tasks:

1. Add proper project-level custom profile and skill directories.
2. Persist Web configuration instead of per-request only.
3. Add a real run/session history page.
4. Add human approval policy for risky tools.
5. Improve tool-call loop to support multiple rounds, not just one tool-call phase.
6. Add browser tool or MCP tool integration.
7. Build a proper TaskGraph Web view.
8. Add authentication before any remote/private deployment.
9. Make delegation visible in execution logs.
10. Add structured config through `.env` or `helm.yaml`.

## How To Continue In A New Conversation

On another computer, after cloning the project, tell Codex:

```text
Please read HANDOFF.md and README.md first, then continue developing Helm Agent.
```

This file contains the design decisions and current state from the original conversation.
