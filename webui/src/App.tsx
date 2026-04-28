import { FormEvent, useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  Bot,
  CheckCircle2,
  ChevronRight,
  KeyRound,
  Loader2,
  MessageSquare,
  Send,
  Settings2,
  User,
  Wrench
} from "lucide-react";

type Page = "chat" | "settings";
type Role = "user" | "assistant";

type ToolEvent = {
  type: string;
  tool?: string;
  arguments?: Record<string, unknown>;
  ok?: boolean;
  content?: string;
  iteration?: number;
};

type Message = {
  id: string;
  role: Role;
  content: string;
  tools?: ToolEvent[];
  status?: "streaming" | "error";
};

type ModelConfig = {
  provider: string;
  base_url: string;
  model: string;
  api_key: string;
  profile: string;
  toolsets: string[];
  max_tokens: number;
  temperature: number;
  enable_thinking: boolean;
  hide_thinking: boolean;
};

type ConfigResponse = {
  version: string;
  default_provider: string;
  provider: {
    id: string;
    base_url: string;
    model: string;
    has_api_key: boolean;
  };
};

type StreamEvent =
  | { type: "status"; status: string }
  | { type: "tool"; event: ToolEvent }
  | { type: "delta"; content: string }
  | { type: "done"; status: string; error?: string | null };

const defaultConfig: ModelConfig = {
  provider: "minimax",
  base_url: "https://api.minimaxi.com/v1",
  model: "MiniMax-M2.1",
  api_key: "",
  profile: "default",
  toolsets: [],
  max_tokens: 1024,
  temperature: 0.2,
  enable_thinking: false,
  hide_thinking: true
};

const toolsetOptions = ["filesystem", "git", "shell"];

export function App() {
  const [page, setPage] = useState<Page>("chat");
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

    const assistantId = crypto.randomUUID();
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: text },
      { id: assistantId, role: "assistant", content: "", tools: [], status: "streaming" }
    ]);
    setPrompt("");
    setIsSending(true);

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: config.provider,
          base_url: config.base_url,
          model: config.model,
          api_key: config.api_key,
          profile: config.profile,
          prompt: text,
          toolsets: config.toolsets,
          max_tokens: config.max_tokens,
          temperature: config.temperature,
          enable_thinking: config.enable_thinking
        })
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed: ${response.status}`);
      }

      await readNdjson(response, (item) => {
        if (item.type === "delta") {
          updateAssistant(assistantId, (message) => ({
            ...message,
            content: message.content + item.content
          }));
        }
        if (item.type === "tool") {
          updateAssistant(assistantId, (message) => ({
            ...message,
            tools: [...(message.tools || []), item.event]
          }));
        }
        if (item.type === "done") {
          updateAssistant(assistantId, (message) => ({
            ...message,
            content: item.error ? item.error : message.content,
            status: item.status === "completed" ? undefined : "error"
          }));
        }
      });
    } catch (error) {
      updateAssistant(assistantId, (message) => ({
        ...message,
        content: String(error),
        status: "error"
      }));
    } finally {
      setIsSending(false);
    }
  }

  function updateAssistant(id: string, updater: (message: Message) => Message) {
    setMessages((current) =>
      current.map((message) => (message.id === id ? updater(message) : message))
    );
  }

  return (
    <div className="app-shell">
      <nav className="nav">
        <div className="nav-brand">
          <Bot size={22} />
          <div>
            <strong>Helm Agent</strong>
            <span>{health}</span>
          </div>
        </div>
        <button className={page === "chat" ? "active" : ""} onClick={() => setPage("chat")}>
          <MessageSquare size={18} />
          Chat
          <ChevronRight size={16} />
        </button>
        <button
          className={page === "settings" ? "active" : ""}
          onClick={() => setPage("settings")}
        >
          <Settings2 size={18} />
          Model Config
          <ChevronRight size={16} />
        </button>
      </nav>

      {page === "chat" ? (
        <ChatPage
          config={config}
          messages={renderedMessages}
          prompt={prompt}
          isSending={isSending}
          onPromptChange={setPrompt}
          onSend={sendMessage}
        />
      ) : (
        <SettingsPage
          config={config}
          configuredKey={configuredKey}
          onConfigChange={setConfig}
        />
      )}
    </div>
  );
}

function ChatPage(props: {
  config: ModelConfig;
  messages: Message[];
  prompt: string;
  isSending: boolean;
  onPromptChange: (value: string) => void;
  onSend: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <main className="page chat-page">
      <header className="page-header">
        <div>
          <h1>Chat</h1>
          <span>
            {props.config.provider} / {props.config.model}
          </span>
        </div>
        <div className="tool-badges">
          {props.config.toolsets.length ? (
            props.config.toolsets.map((toolset) => <span key={toolset}>{toolset}</span>)
          ) : (
            <span>no tools</span>
          )}
        </div>
      </header>

      <section className="messages">
        {props.messages.map((message) => (
          <article className={`message ${message.role} ${message.status || ""}`} key={message.id}>
            <div className="avatar">
              {message.role === "user" ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className="bubble">
              {message.tools?.map((tool, index) => (
                <ToolCallCard event={tool} key={`${tool.tool}-${index}`} />
              ))}
              {message.content ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : message.status === "streaming" ? (
                <p className="muted">
                  <Loader2 className="spin inline-icon" size={14} />
                  Waiting for response...
                </p>
              ) : (
                <p className="muted">(empty)</p>
              )}
            </div>
          </article>
        ))}
      </section>

      <form className="composer" onSubmit={props.onSend}>
        <textarea
          value={props.prompt}
          onChange={(event) => props.onPromptChange(event.target.value)}
          placeholder="Message Helm Agent"
          rows={3}
        />
        <button type="submit" disabled={props.isSending || !props.prompt.trim()} title="Send">
          <Send size={18} />
        </button>
      </form>
    </main>
  );
}

function SettingsPage(props: {
  config: ModelConfig;
  configuredKey: boolean;
  onConfigChange: (config: ModelConfig) => void;
}) {
  const { config, configuredKey, onConfigChange } = props;
  return (
    <main className="page settings-page">
      <header className="page-header">
        <div>
          <h1>Model Config</h1>
          <span>Provider settings for new chat requests</span>
        </div>
        <CheckCircle2 size={20} />
      </header>

      <section className="settings-panel">
        <label>
          Provider
          <input
            value={config.provider}
            onChange={(event) => onConfigChange({ ...config, provider: event.target.value })}
          />
        </label>
        <label>
          Base URL
          <input
            value={config.base_url}
            onChange={(event) => onConfigChange({ ...config, base_url: event.target.value })}
          />
        </label>
        <label>
          Model
          <input
            value={config.model}
            onChange={(event) => onConfigChange({ ...config, model: event.target.value })}
          />
        </label>
        <label>
          API Key
          <input
            type="password"
            placeholder={configuredKey ? "Using .env key" : "Paste key for this session"}
            value={config.api_key}
            onChange={(event) => onConfigChange({ ...config, api_key: event.target.value })}
          />
        </label>
        <label>
          Profile
          <input
            value={config.profile}
            onChange={(event) => onConfigChange({ ...config, profile: event.target.value })}
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
                onConfigChange({ ...config, max_tokens: Number(event.target.value) })
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
                onConfigChange({ ...config, temperature: Number(event.target.value) })
              }
            />
          </label>
        </div>

        <div className="toolset-group">
          <strong>Allowed Tools</strong>
          {toolsetOptions.map((toolset) => (
            <label className="toggle" key={toolset}>
              <input
                type="checkbox"
                checked={config.toolsets.includes(toolset)}
                onChange={(event) => {
                  const nextToolsets = event.target.checked
                    ? [...config.toolsets, toolset]
                    : config.toolsets.filter((item) => item !== toolset);
                  onConfigChange({ ...config, toolsets: nextToolsets });
                }}
              />
              {toolset}
            </label>
          ))}
        </div>

        <label className="toggle">
          <input
            type="checkbox"
            checked={config.enable_thinking}
            onChange={(event) =>
              onConfigChange({ ...config, enable_thinking: event.target.checked })
            }
          />
          Enable thinking
        </label>
        <label className="toggle">
          <input
            type="checkbox"
            checked={config.hide_thinking}
            onChange={(event) =>
              onConfigChange({ ...config, hide_thinking: event.target.checked })
            }
          />
          Hide thinking blocks
        </label>

        <p className="key-note">
          <KeyRound size={14} />
          API keys entered here are sent only to the local Helm backend for each request.
        </p>
      </section>
    </main>
  );
}

function ToolCallCard({ event }: { event: ToolEvent }) {
  return (
    <details className="tool-card" open>
      <summary>
        <Wrench size={14} />
        <span>{event.tool || "tool"}</span>
        <strong>{event.ok === false ? "failed" : "ok"}</strong>
      </summary>
      <pre>{JSON.stringify(event.arguments || {}, null, 2)}</pre>
      {event.content ? <pre>{event.content}</pre> : null}
    </details>
  );
}

async function readNdjson(response: Response, onEvent: (event: StreamEvent) => void) {
  const reader = response.body?.getReader();
  if (!reader) {
    return;
  }
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.trim()) {
        onEvent(JSON.parse(line) as StreamEvent);
      }
    }
  }
  if (buffer.trim()) {
    onEvent(JSON.parse(buffer) as StreamEvent);
  }
}

function stripThinking(value: string): string {
  return value.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
}
