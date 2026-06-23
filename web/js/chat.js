async function sendMessage(message, history = []) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message, history })
  });

  if (!response.ok) {
    throw new Error(`Chat API returned ${response.status}`);
  }

  return response.json();
}

function renderMessage(role, content) {
  const list = document.querySelector("#chatMessages");
  const item = document.createElement("article");
  item.className = `message ${role}`;

  const roleNode = document.createElement("div");
  roleNode.className = "message-role";
  roleNode.textContent = role === "user" ? "你" : "AI";

  const body = document.createElement("div");
  body.className = "message-body";
  if (window.marked && role !== "user") {
    body.innerHTML = marked.parse(content);
  } else {
    body.textContent = content;
  }

  item.append(roleNode, body);
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#chatForm");
  const input = document.querySelector("#chatInput");
  const history = [];

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) {
      return;
    }

    input.value = "";
    renderMessage("user", message);
    history.push({ role: "user", content: message });

    try {
      const result = await sendMessage(message, history);
      const content = result.response || "收到。";
      renderMessage("assistant", content);
      history.push({ role: "assistant", content });
    } catch (error) {
      renderMessage("assistant", `对话服务暂不可用：${error.message}`);
    }
  });
});
