# Helm Agent

Helm Agent is a private-deployment, Hermes-inspired agent framework backbone.

Current version: `0.0.1`.

The first version focuses on a small extensible core:

- `runtime`: shared Hermes-style agent loop.
- `context`: prompt and context assembly.
- `taskgraph`: lightweight run/task DAG.
- `profiles`: file-defined agent identities.
- `skills`: on-demand capability packages.
- `providers`: model provider abstraction.
- `tools`: callable tool registry and toolsets.
- `web`: FastAPI Web test interface.
- `store`: persistence skeleton.

For design history and continuation context, read [HANDOFF.md](HANDOFF.md).

## Requirements

- Python 3.11+
- Windows PowerShell examples are shown below.
- A local or remote OpenAI-compatible model endpoint.

The development endpoint used so far:

```yaml
providers:
  minimax:
    base_url: https://api.minimaxi.com/v1
    model: MiniMax-M2.1
    api_key_env: HELM_MINIMAX_API_KEY
```

Provider configuration lives in `helm.yaml`. Local secrets belong in `.env`,
which is ignored by git. See `.env.example`.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

If PowerShell activation is blocked, use the venv Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected current result:

```text
14 passed
```

## Local Model Smoke Test

```powershell
.\.venv\Scripts\python.exe examples\local_model_smoke.py
```

Expected output:

```text
status=completed
The local OpenAI-compatible provider is working.
```

## Start The Web Test Page

Build the TypeScript Web UI:

```powershell
cd webui
npm install
npm run build
cd ..
```

Start the FastAPI backend, which serves `webui/dist`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn helm.web.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The page currently provides:

- A chat box.
- Model configuration for provider, base URL, model, API key, max tokens, and temperature.
- A hide-thinking toggle for models that return `<think>...</think>` blocks.

## Example Web Test

Use:

```text
Profile: executor
Skills: code-execution
Toolsets: filesystem
Prompt: Use an available tool to list the files in the current project directory, then summarize them.
```

The execution log should include a call like:

```text
tool: filesystem_list
ok: true
arguments: {"path":"."}
```

## Main Project Structure

```text
helm/
  runtime/
  context/
  taskgraph/
  profiles/
  skills/
  providers/
  tools/
  web/
  store/
  config/

examples/
tests/
HANDOFF.md
README.md
pyproject.toml
```

## Built-in Profiles

Built-in profiles live in:

```text
helm/profiles/builtin/
```

Current profiles:

- `default`
- `planner`
- `executor`
- `reviewer`

## Built-in Skills

Built-in skills live in:

```text
helm/skills/builtin/
```

Current skills:

- `task-planning`
- `code-execution`
- `code-review`
- `private-deployment`

## Current Tools

Current internal tool names:

- `filesystem.list`
- `filesystem.read`
- `filesystem.write`
- `shell.run`
- `git.status`
- `git.diff`
- `delegate_task`

OpenAI-compatible model-facing names use underscores:

- `filesystem_list`
- `filesystem_read`
- `filesystem_write`
- `shell_run`
- `git_status`
- `git_diff`

## Migration To Another Computer

Commit the repo:

```powershell
git init
git add .
git commit -m "Initial Helm Agent v0.0.1 backbone"
```

Push it to a private Git repository, then clone it on the other computer.

After cloning:

```powershell
cd helm-agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m pytest -q
```

To continue the development conversation, ask the assistant to read:

```text
HANDOFF.md
README.md
```
