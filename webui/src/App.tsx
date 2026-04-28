import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, EyeOff, Loader2, Send, Settings2, User } from "lucide-react";

type Role = "user" | "assistant" | "system";

type Message = {
  id: string;
  role: Role;
  content: string;
  status?: "error";
};

type ModelConfig = {
  provider: string;
  base_url: string;
  model: string;
  api_key: string;
  toolsets: string[];
  max_tokens: number;
  temperature: number;
  enable_thinking: boolean;
  hide_thinking: boolean;
};

type ConfigResponse = {
  default_provider: string;
  provider: {
    id: string;
    base_url: string;
    model: string;
    has_api_key: boolean;
  };
};

type ChatResponse = {
  status: string;
  output: string;
  error?: string | null;
};

const defaultConfig: ModelConfig = {
  provider: "minimax",
  base_url: "https://api.minimaxi.com/v1",
  model: "MiniMax-M2.1",
  api_key: "",
  toolsets: [],
  max_tokens: 1024,
  temperature: 0.2,
  enable_thinking: false,
  hide_thinking: true
};

export function App() {
  const [config, setConfig] = useState<ModelConfig>(defaultConfig);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "Helm Agent is ready."
    }
  ]);
  const [prompt, setPrompt] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [health, setHealth] = useState("checking");
  const [configuredKey, setConfiguredKey] = useState(false);

  useEffect(() => {
    fetch("/health")
      .then((response) => response.json())
      .then((data) => setHealth(`${data.status} ${data.version}`))
      .catch(() => setHealth("offline"));

    fetch("/api/config")
      .then((response) => response.json() as Promise<ConfigResponse>)
      .then((data) => {
        setConfiguredKey(data.provider.has_api_key);
        setConfig((current) => ({
          ...current,
          provider: data.default_provider || current.provider,
          base_url: data.provider.base_url || current.base_url,
          model: data.provider.model || current.model
        }));
      })
      .catch(() => undefined);
  }, []);

  const renderedMessages = useMemo(
    () =>
      messages.map((message) => ({
        ...message,
        content:
          config.hide_thinking && message.role === "assistant"
            ? stripThinking(message.content)
            : message.content
      })),
    [config.hide_thinking, messages]
  );

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = prompt.trim();
    if (!text || isSending) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text
    };
    setMessages((current) => [...current, userMessage]);
    setPrompt("");
    setIsSending(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: config.provider,
          base_url: config.base_url,
          model: config.model,
          api_key: config.api_key,
          prompt: text,
          toolsets: config.toolsets,
          max_tokens: config.max_tokens,
          temperature: config.temperature,
          enable_thinking: config.enable_thinking
        })
      });
      const payload = (await response.json()) as ChatResponse;
      const failed = !response.ok || payload.status !== "completed";
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: failed ? payload.error || payload.output || "Request failed." : payload.output,
          status: failed ? "error" : undefined
        }
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: String(error),
          status: "error"
        }
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="shell">
      <aside className="settings">
        <div className="brand">
          <Settings2 size={20} aria-hidden="true" />
          <div>
            <h1>Helm Agent</h1>
            <span>{health}</span>
          </div>
        </div>

        <label>
          Provider
          <input
            value={config.provider}
            onChange={(event) => setConfig({ ...config, provider: event.target.value })}
          />
        </label>
        <label>
          Base URL
          <input
            value={config.base_url}
            onChange={(event) => setConfig({ ...config, base_url: event.target.value })}
          />
        </label>
        <label>
          Model
          <input
            value={config.model}
            onChange={(event) => setConfig({ ...config, model: event.target.value })}
          />
        </label>
        <label>
          API Key
          <input
            type="password"
            placeholder={configuredKey ? "Using .env key" : "Paste key for this session"}
            value={config.api_key}
            onChange={(event) => setConfig({ ...config, api_key: event.target.value })}
          />
        </label>

        <div className="field-row">
          <label>
            Max Tokens
            <input
              type="number"
              min={1}
              max={8192}
              value={config.max_tokens}
              onChange={(event) =>
                setConfig({ ...config, max_tokens: Number(event.target.value) })
              }
            />
          </label>
          <label>
            Temperature
            <input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={config.temperature}
              onChange={(event) =>
                setConfig({ ...config, temperature: Number(event.target.value) })
              }
            />
          </label>
        </div>

        <label className="toggle">
          <input
            type="checkbox"
            checked={config.enable_thinking}
            onChange={(event) =>
              setConfig({ ...config, enable_thinking: event.target.checked })
            }
          />
          Enable thinking
        </label>
        <div className="toolset-group" aria-label="Allowed tools">
          <span>Tools</span>
          {["filesystem", "git", "shell"].map((toolset) => (
            <label className="toggle" key={toolset}>
              <input
                type="checkbox"
                checked={config.toolsets.includes(toolset)}
                onChange={(event) => {
                  const nextToolsets = event.target.checked
                    ? [...config.toolsets, toolset]
                    : config.toolsets.filter((item) => item !== toolset);
                  setConfig({ ...config, toolsets: nextToolsets });
                }}
              />
              {toolset}
            </label>
          ))}
        </div>
        <label className="toggle">
          <input
            type="checkbox"
            checked={config.hide_thinking}
            onChange={(event) => setConfig({ ...config, hide_thinking: event.target.checked })}
          />
          Hide thinking
        </label>
      </aside>

      <main className="chat">
        <div className="messages">
          {renderedMessages.map((message) => (
            <article className={`message ${message.role} ${message.status || ""}`} key={message.id}>
              <div className="avatar">
                {message.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>
              <p>{message.content || "(empty)"}</p>
            </article>
          ))}
          {isSending && (
            <article className="message assistant">
              <div className="avatar">
                <Loader2 className="spin" size={16} />
              </div>
              <p>Thinking...</p>
            </article>
          )}
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Message Helm Agent"
            rows={3}
          />
          <button type="submit" disabled={isSending || !prompt.trim()} title="Send">
            <Send size={18} />
          </button>
        </form>
        <div className="hint">
          <EyeOff size={14} aria-hidden="true" />
          API keys entered here are sent only to the local Helm backend for this request.
        </div>
      </main>
    </div>
  );
}

function stripThinking(value: string): string {
  return value.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
}
