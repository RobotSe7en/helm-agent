from __future__ import annotations

from pydantic import BaseModel, Field

from helm import __version__
from helm.app import create_runtime
from helm.config.settings import ProviderConfig, Settings
from helm.runtime.invocation import RuntimeInvocation


class ModelTestRequest(BaseModel):
    provider: str = Field(default="minimax")
    base_url: str = Field(default="http://192.168.1.18:16666/v1")
    model: str = Field(default="qwen3")
    api_key: str = Field(default="EMPTY")
    profile: str = Field(default="default")
    skills: list[str] = Field(default_factory=list)
    toolsets: list[str] = Field(default_factory=list)
    prompt: str = Field(default="Reply with a short confirmation.")
    max_tokens: int = Field(default=256, ge=1, le=8192)
    temperature: float = Field(default=0.2, ge=0, le=2)
    enable_thinking: bool = False


def create_app():
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
    except ImportError as exc:
        raise RuntimeError("Install helm-agent[web] to use the web app") from exc

    app = FastAPI(title="Helm Agent", version=__version__)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return INDEX_HTML

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.post("/api/model/test")
    async def test_model(request: ModelTestRequest) -> dict[str, object]:
        try:
            settings = Settings(
                default_provider=request.provider,
                providers={
                    request.provider: ProviderConfig(
                        id=request.provider,
                        base_url=request.base_url,
                        api_key=request.api_key,
                        model=request.model,
                    )
                },
            )
            runtime = create_runtime(settings)
            result = await runtime.invoke(
                RuntimeInvocation(
                    run_id="web_model_test",
                    task_id="web_model_test_task",
                    profile=request.profile,
                    goal="Web model test",
                    instructions=request.prompt,
                    provider=request.provider,
                    skills=request.skills,
                    toolsets=request.toolsets,
                    metadata={
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                        "extra_body": {
                            "chat_template_kwargs": {
                                "enable_thinking": request.enable_thinking,
                            }
                        },
                    },
                )
            )
        except Exception as exc:
            return {
                "status": "failed",
                "output": "",
                "events": [
                    {
                        "type": "runtime.failed",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                ],
                "error": f"{type(exc).__name__}: {exc}",
                "effective_config": {
                    "provider": request.provider,
                    "base_url": request.base_url,
                    "model": request.model,
                    "profile": request.profile,
                    "skills": request.skills,
                    "toolsets": request.toolsets,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "enable_thinking": request.enable_thinking,
                },
            }
        return {
            "status": result.status,
            "output": result.output,
            "events": result.events,
            "error": result.error,
            "effective_config": {
                "provider": request.provider,
                "base_url": request.base_url,
                "model": request.model,
                "profile": request.profile,
                "skills": request.skills,
                "toolsets": request.toolsets,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "enable_thinking": request.enable_thinking,
            },
        }

    return app


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Helm Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --text: #18202f;
      --muted: #667085;
      --line: #d9deea;
      --accent: #1677ff;
      --accent-dark: #0f5fd2;
      --ok: #087443;
      --bad: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    .brand {
      font-size: 16px;
      font-weight: 700;
    }
    .status {
      font-size: 13px;
      color: var(--muted);
    }
    main {
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      grid-template-columns: minmax(320px, 420px) 1fr;
      gap: 20px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    h1, h2 {
      margin: 0 0 14px;
      font-size: 16px;
    }
    label {
      display: block;
      margin: 14px 0 6px;
      font-size: 13px;
      font-weight: 600;
    }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      background: #fff;
      color: var(--text);
    }
    textarea {
      min-height: 132px;
      resize: vertical;
      line-height: 1.45;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      font-size: 13px;
      color: var(--text);
    }
    .toggle input {
      width: 16px;
      height: 16px;
    }
    .checks {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
    }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-weight: 500;
      color: var(--text);
    }
    .check input {
      width: 16px;
      height: 16px;
    }
    button {
      margin-top: 18px;
      width: 100%;
      height: 40px;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }
    button:hover { background: var(--accent-dark); }
    button:disabled {
      cursor: wait;
      opacity: .65;
    }
    pre {
      min-height: 220px;
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      line-height: 1.5;
      font-size: 13px;
      background: #111827;
      color: #e5e7eb;
      border-radius: 6px;
      padding: 14px;
    }
    .log {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }
    .log-item {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: #fbfcff;
      font-size: 13px;
    }
    .log-title {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .log-meta {
      color: var(--muted);
      line-height: 1.5;
      overflow-wrap: anywhere;
    }
    .tool-content {
      margin-top: 8px;
      padding: 10px;
      border-radius: 6px;
      background: #111827;
      color: #e5e7eb;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      max-height: 260px;
      overflow: auto;
    }
    .result-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }
    .badge {
      font-size: 12px;
      padding: 4px 8px;
      border-radius: 999px;
      background: #eef2f7;
      color: var(--muted);
    }
    .badge.ok { color: var(--ok); background: #ecfdf3; }
    .badge.bad { color: var(--bad); background: #fef3f2; }
    @media (max-width: 820px) {
      main { grid-template-columns: 1fr; padding: 16px; }
      header { padding: 0 16px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">Helm Agent</div>
    <div class="status" id="health">checking</div>
  </header>
  <main>
    <section>
      <h1>Model Test</h1>
      <form id="form">
        <label for="provider">Provider</label>
        <input id="provider" name="provider" value="minimax" />

        <label for="baseUrl">Base URL</label>
        <input id="baseUrl" name="base_url" value="http://192.168.1.18:16666/v1" />

        <label for="model">Model</label>
        <input id="model" name="model" value="qwen3" />

        <label for="apiKey">API Key</label>
        <input id="apiKey" name="api_key" value="EMPTY" />

        <label for="profile">Profile</label>
        <select id="profile" name="profile">
          <option value="default">default</option>
          <option value="planner">planner</option>
          <option value="executor">executor</option>
          <option value="reviewer">reviewer</option>
        </select>

        <label for="skills">Skills</label>
        <input id="skills" name="skills" placeholder="task-planning, code-execution, code-review" />

        <label>Toolsets</label>
        <div class="checks">
          <label class="check"><input type="checkbox" name="toolsets" value="filesystem" /> filesystem</label>
          <label class="check"><input type="checkbox" name="toolsets" value="git" /> git</label>
          <label class="check"><input type="checkbox" name="toolsets" value="shell" /> shell</label>
          <label class="check"><input type="checkbox" name="toolsets" value="delegation" /> delegation</label>
        </div>

        <div class="row">
          <div>
            <label for="maxTokens">Max Tokens</label>
            <input id="maxTokens" name="max_tokens" type="number" min="1" max="8192" value="256" />
          </div>
          <div>
            <label for="temperature">Temperature</label>
            <input id="temperature" name="temperature" type="number" min="0" max="2" step="0.1" value="0.2" />
          </div>
        </div>

        <label class="toggle" for="enableThinking">
          <input id="enableThinking" name="enable_thinking" type="checkbox" />
          Enable thinking
        </label>

        <label class="toggle" for="showToolResults">
          <input id="showToolResults" name="show_tool_results" type="checkbox" />
          Show tool results
        </label>

        <label for="prompt">Prompt</label>
        <textarea id="prompt" name="prompt">Reply with one short sentence confirming Helm Agent can reach this model.</textarea>

        <button id="submit" type="submit">Run Test</button>
      </form>
    </section>

    <section>
      <div class="result-head">
        <h2>Result</h2>
        <span class="badge" id="badge">idle</span>
      </div>
      <pre id="output">Waiting for a test run.</pre>
      <div class="result-head" style="margin-top: 18px;">
        <h2>Execution Log</h2>
        <span class="badge" id="logCount">0 events</span>
      </div>
      <div class="log" id="log"></div>
    </section>
  </main>
  <script>
    const form = document.getElementById("form");
    const output = document.getElementById("output");
    const badge = document.getElementById("badge");
    const log = document.getElementById("log");
    const logCount = document.getElementById("logCount");
    const submit = document.getElementById("submit");
    const health = document.getElementById("health");

    fetch("/health")
      .then((r) => r.json())
      .then((data) => { health.textContent = `${data.status} · ${data.version}`; })
      .catch(() => { health.textContent = "offline"; });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submit.disabled = true;
      badge.className = "badge";
      badge.textContent = "running";
      output.textContent = "Running...";
      log.innerHTML = "";
      logCount.textContent = "0 events";

      const data = {
        provider: form.provider.value.trim(),
        base_url: form.base_url.value.trim(),
        model: form.model.value.trim(),
        api_key: form.api_key.value,
        profile: form.profile.value,
        skills: splitList(form.skills.value),
        toolsets: Array.from(form.querySelectorAll('input[name="toolsets"]:checked')).map((item) => item.value),
        prompt: form.prompt.value,
        max_tokens: Number(form.max_tokens.value),
        temperature: Number(form.temperature.value),
        enable_thinking: form.enable_thinking.checked,
      };

      try {
        const response = await fetch("/api/model/test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        const payload = await readPayload(response);
        if (!response.ok) {
          throw new Error(JSON.stringify(payload, null, 2));
        }
        badge.className = payload.status === "completed" ? "badge ok" : "badge bad";
        badge.textContent = payload.status;
        output.textContent = [
          payload.output || "",
          "",
          "Effective config:",
          JSON.stringify(payload.effective_config, null, 2),
        ].join("\n");
        renderLog(payload.events || [], form.show_tool_results.checked);
      } catch (error) {
        badge.className = "badge bad";
        badge.textContent = "failed";
        output.textContent = String(error);
      } finally {
        submit.disabled = false;
      }
    });

    function splitList(value) {
      return value.split(",").map((item) => item.trim()).filter(Boolean);
    }

    async function readPayload(response) {
      const text = await response.text();
      try {
        return text ? JSON.parse(text) : {};
      } catch (error) {
        return {
          status: "failed",
          output: "",
          events: [{ type: "http.failed", status: response.status, body: text }],
          error: text || String(error),
        };
      }
    }

    function renderLog(events, showToolResults) {
      logCount.textContent = `${events.length} events`;
      log.innerHTML = "";
      for (const event of events) {
        const item = document.createElement("div");
        item.className = "log-item";
        const title = document.createElement("div");
        title.className = "log-title";
        const left = document.createElement("span");
        left.textContent = event.type || "event";
        const right = document.createElement("span");
        right.textContent = event.ok === false ? "failed" : event.ok === true ? "ok" : "";
        title.append(left, right);

        const meta = document.createElement("div");
        meta.className = "log-meta";
        const summary = summarizeEvent(event, showToolResults);
        meta.innerHTML = summary.meta.map(escapeHtml).join("<br>");
        item.append(title, meta);

        if (summary.toolContent) {
          const content = document.createElement("div");
          content.className = "tool-content";
          content.textContent = summary.toolContent;
          item.append(content);
        }
        log.append(item);
      }
    }

    function summarizeEvent(event, showToolResults) {
      if (event.type === "runtime.started") {
        return {
          meta: [
            `profile: ${event.profile}`,
            `skills: ${(event.skills || []).join(", ") || "(none)"}`,
            `toolsets: ${(event.toolsets || []).join(", ") || "(none)"}`,
            `tools: ${(event.tools || []).join(", ") || "(none)"}`,
          ],
        };
      }
      if (event.type === "provider.completed") {
        return {
          meta: [
            `provider: ${event.provider}`,
            `profile: ${event.profile}`,
            `tool calls: ${event.tool_call_count ?? 0}`,
            event.phase ? `phase: ${event.phase}` : "",
          ].filter(Boolean),
        };
      }
      if (event.type === "tool.completed") {
        return {
          meta: [
            `tool: ${event.tool}`,
            `ok: ${event.ok}`,
            `arguments: ${JSON.stringify(event.arguments || {})}`,
          ],
          toolContent: showToolResults ? String(event.content || "") : "",
        };
      }
      if (event.type === "runtime.failed" || event.type === "http.failed") {
        return {
          meta: [
            `error: ${event.error || event.body || "(empty)"}`,
            event.error_type ? `type: ${event.error_type}` : "",
            event.status ? `status: ${event.status}` : "",
          ].filter(Boolean),
        };
      }
      return { meta: [JSON.stringify(event)] };
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  </script>
</body>
</html>"""
