const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const resetButton = document.querySelector("#resetButton");
const promptButtons = document.querySelectorAll(".prompt-chip");

let isSending = false;

function track(eventName, properties = {}) {
  if (window.cascadiaAnalytics) {
    window.cascadiaAnalytics.capture(eventName, properties);
  }
}

function addMessage(role, text, options = {}) {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "agent-message"}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "You" : "CA";

  const bubble = document.createElement("div");
  bubble.className = `bubble${options.error ? " error" : ""}`;
  renderText(bubble, text);

  article.append(avatar, bubble);
  if (role === "agent" && Array.isArray(options.traces) && options.traces.length > 0) {
    article.append(renderTracePanel(options.traces));
  }
  messages.append(article);
  scrollToBottom();
  return article;
}

function addTyping() {
  const article = document.createElement("article");
  article.className = "message agent-message typing";
  article.innerHTML = `
    <div class="avatar" aria-hidden="true">CA</div>
    <div class="bubble" aria-label="Cascadia Agent is thinking">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  `;
  messages.append(article);
  scrollToBottom();
  return article;
}

function renderText(container, text) {
  const paragraphs = text
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (paragraphs.length === 0) {
    const p = document.createElement("p");
    p.textContent = "";
    container.append(p);
    return;
  }

  for (const paragraph of paragraphs) {
    const p = document.createElement("p");
    appendInlineContent(p, paragraph);
    container.append(p);
  }
}

function appendInlineContent(element, text) {
  const lines = text.split("\n");
  lines.forEach((line, index) => {
    if (index > 0) {
      element.append(document.createElement("br"));
    }
    appendInlineLine(element, line);
  });
}

function appendInlineLine(element, text) {
  const pattern = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|(https?:\/\/[^\s<>)]+)/g;
  let cursor = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      element.append(document.createTextNode(text.slice(cursor, match.index)));
    }

    const label = match[1] || match[3];
    const url = match[2] || trimTrailingPunctuation(match[3]);
    const trailing = match[3] ? match[3].slice(url.length) : "";
    element.append(createSafeLink(label, url));
    if (trailing) {
      element.append(document.createTextNode(trailing));
    }
    cursor = pattern.lastIndex;
  }

  if (cursor < text.length) {
    element.append(document.createTextNode(text.slice(cursor)));
  }
}

function trimTrailingPunctuation(url) {
  return url.replace(/[.,;:!?]+$/, "");
}

function createSafeLink(label, url) {
  const anchor = document.createElement("a");
  anchor.textContent = label;
  anchor.href = url;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  return anchor;
}

function renderTracePanel(traces) {
  const panel = document.createElement("div");
  panel.className = "trace-panel";

  const title = document.createElement("div");
  title.className = "trace-title";
  title.textContent = "Agent actions";
  panel.append(title);

  traces.forEach((trace) => {
    const item = document.createElement("details");
    item.className = `trace-item trace-${trace.status || "ok"}`;
    item.addEventListener("toggle", () => {
      if (item.open) {
        track("trace_opened", {
          tool_name: trace.name || "unknown",
          status: trace.status || "ok",
          source_count: Array.isArray(trace.sources) ? trace.sources.length : 0,
        });
      }
    });

    const summary = document.createElement("summary");
    const name = document.createElement("span");
    name.className = "trace-name";
    name.textContent = trace.label || trace.name || "Tool call";
    const result = document.createElement("span");
    result.className = "trace-result";
    result.textContent = trace.summary || "";
    summary.append(name, result);
    item.append(summary);

    const meta = document.createElement("div");
    meta.className = "trace-meta";
    meta.append(renderTraceInput(trace.input || {}));
    if (Array.isArray(trace.sources) && trace.sources.length > 0) {
      meta.append(renderTraceSources(trace.sources));
    }
    item.append(meta);
    panel.append(item);
  });

  return panel;
}

function renderTraceInput(input) {
  const inputLine = document.createElement("div");
  inputLine.className = "trace-input";
  inputLine.textContent = `Input: ${JSON.stringify(input)}`;
  return inputLine;
}

function renderTraceSources(sources) {
  const sourceLine = document.createElement("div");
  sourceLine.className = "trace-sources";
  sourceLine.append(document.createTextNode("Sources: "));
  sources.forEach((source, index) => {
    if (index > 0) {
      sourceLine.append(document.createTextNode(" · "));
    }
    sourceLine.append(createSafeLink(source.label || "source", source.url));
  });
  return sourceLine;
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function autosizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 170)}px`;
}

async function sendMessage(text) {
  const message = text.trim();
  if (!message || isSending) return;

  isSending = true;
  const startedAt = performance.now();
  sendButton.disabled = true;
  track("chat_message_sent", {
    message_length: message.length,
  });
  addMessage("user", message);
  input.value = "";
  autosizeInput();
  const typing = addTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    typing.remove();

    if (!response.ok) {
      addMessage("agent", data.detail || data.error || "Something went wrong.", { error: true });
      track("chat_error", {
        status: response.status,
        has_detail: Boolean(data.detail),
      });
      return;
    }

    addMessage("agent", data.reply, { traces: data.traces });
    track("agent_reply_received", {
      duration_ms: Math.round(performance.now() - startedAt),
      reply_length: data.reply ? data.reply.length : 0,
      trace_count: Array.isArray(data.traces) ? data.traces.length : 0,
      tool_names: Array.isArray(data.traces) ? data.traces.map((trace) => trace.name) : [],
    });
  } catch (error) {
    typing.remove();
    addMessage("agent", "I could not reach the local chat server. Is `python web.py` still running?", { error: true });
    track("chat_network_error", {
      message: error instanceof Error ? error.message : "unknown",
    });
  } finally {
    isSending = false;
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", autosizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

resetButton.addEventListener("click", async () => {
  if (isSending) return;
  await fetch("/api/reset", { method: "POST" });
  messages.innerHTML = "";
  addMessage("agent", "Fresh start. What are you thinking about getting after?");
  track("conversation_reset");
  input.focus();
});

promptButtons.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent.trim();
    autosizeInput();
    track("example_prompt_selected", {
      prompt_length: input.value.length,
    });
    input.focus();
  });
});

autosizeInput();
