const chatState = {
  history: [],
  isStreaming: false
};

function renderMarkdown(node, content) {
  if (window.marked) {
    node.innerHTML = marked.parse(content || "");
    return;
  }
  node.textContent = content || "";
}

function createMessage(role, content = "") {
  const list = document.querySelector("#chatMessages");
  const item = document.createElement("article");
  item.className = `message ${role} ${role === "user" ? "msg-user" : "msg-claude"}`;

  const roleNode = document.createElement("div");
  roleNode.className = "message-role";
  roleNode.textContent = role === "user" ? "You" : "Claude";

  const body = document.createElement("div");
  body.className = "message-body";
  renderMarkdown(body, content);

  item.append(roleNode, body);
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;

  return { item, body };
}

function renderMessage(role, content) {
  return createMessage(role, content).item;
}

function appendToolCall(messageNode, detail) {
  const card = document.createElement("details");
  card.className = "tool-call-card";

  const summary = document.createElement("summary");
  const status = detail.status || "running";
  const icon = status === "success" ? "OK" : status === "error" ? "ERR" : "...";
  summary.textContent = `${icon} ${detail.name || "tool"} (${status})`;

  const pre = document.createElement("pre");
  pre.textContent = typeof detail.detail === "string"
    ? detail.detail
    : JSON.stringify(detail.detail || {}, null, 2);

  card.append(summary, pre);
  messageNode.appendChild(card);
}

function scrollMessagesToBottom() {
  const list = document.querySelector("#chatMessages");
  list.scrollTop = list.scrollHeight;
}

function parseSseChunk(buffer, onEvent) {
  const events = buffer.split("\n\n");
  const remainder = events.pop() || "";

  events.forEach((rawEvent) => {
    let eventName = "message";
    const dataLines = [];

    rawEvent.split("\n").forEach((line) => {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      }
      if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    });

    if (dataLines.length === 0) {
      return;
    }

    try {
      onEvent(eventName, JSON.parse(dataLines.join("\n")));
    } catch (error) {
      onEvent("error", { message: `Invalid stream event: ${error.message}` });
    }
  });

  return remainder;
}

async function sendMessage(message, history = []) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message, history })
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat API returned ${response.status}`);
  }

  return response;
}

async function streamAssistantMessage(message, history) {
  const response = await sendMessage(message, history);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const assistant = createMessage("assistant", "");
  assistant.item.classList.add("streaming");

  let buffer = "";
  let fullText = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    buffer = parseSseChunk(buffer, (eventName, data) => {
      if (eventName === "token") {
        fullText += data.text || "";
        renderMarkdown(assistant.body, fullText);
      }
      if (eventName === "tool_call") {
        appendToolCall(assistant.item, data);
      }
      if (eventName === "error") {
        fullText += `\n\n> ${data.message || "Chat service is unavailable."}`;
        renderMarkdown(assistant.body, fullText);
      }
      if (eventName === "done") {
        assistant.item.classList.remove("streaming");
      }
      scrollMessagesToBottom();
    });
  }

  assistant.item.classList.remove("streaming");
  return fullText.trim();
}

function setChatDisabled(disabled) {
  const input = document.querySelector("#chatInput");
  const button = document.querySelector("#chatForm button[type='submit']");
  input.disabled = disabled;
  button.disabled = disabled;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#chatForm");
  const input = document.querySelector("#chatInput");

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || chatState.isStreaming) {
      return;
    }

    input.value = "";
    renderMessage("user", message);
    chatState.history.push({ role: "user", content: message });
    chatState.isStreaming = true;
    setChatDisabled(true);

    try {
      const content = await streamAssistantMessage(message, chatState.history);
      chatState.history.push({ role: "assistant", content });
    } catch (error) {
      renderMessage("assistant", `Chat service is unavailable: ${error.message}`);
    } finally {
      chatState.isStreaming = false;
      setChatDisabled(false);
      input.focus();
    }
  });
});
