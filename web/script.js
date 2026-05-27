const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const resetButton = document.querySelector("#resetButton");
const promptButtons = document.querySelectorAll(".prompt-chip");

let isSending = false;

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
    p.textContent = paragraph;
    container.append(p);
  }
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
  sendButton.disabled = true;
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
      return;
    }

    addMessage("agent", data.reply);
  } catch (error) {
    typing.remove();
    addMessage("agent", "I could not reach the local chat server. Is `python web.py` still running?", { error: true });
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
  input.focus();
});

promptButtons.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent.trim();
    autosizeInput();
    input.focus();
  });
});

autosizeInput();
