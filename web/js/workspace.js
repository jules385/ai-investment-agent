function objectEntries(data) {
  return Object.entries(data || {});
}

function setCount(selector, count) {
  const node = document.querySelector(selector);
  if (node) {
    node.textContent = String(count);
  }
}

function renderCollection(containerSelector, emptyText, data) {
  const container = document.querySelector(containerSelector);
  const entries = objectEntries(data);

  if (!container) {
    return;
  }

  if (entries.length === 0) {
    container.className = "empty-state";
    container.textContent = emptyText;
    return;
  }

  container.className = "workspace-list";
  container.innerHTML = "";
  entries.forEach(([name, value]) => {
    const card = document.createElement("div");
    card.className = "mini-card";

    const title = document.createElement("strong");
    title.textContent = name;

    const body = document.createElement("span");
    body.textContent = typeof value === "string" ? value : JSON.stringify(value);

    card.append(title, body);
    container.appendChild(card);
  });
}

function renderKnowledgeBase(industries) {
  const entries = objectEntries(industries);
  setCount("#industryCount", entries.length);
  renderCollection("#knowledgeBase", "暂无行业数据", industries);
}

function renderTheses(theses) {
  const entries = objectEntries(theses);
  setCount("#thesisCount", entries.length);
  renderCollection("#thesesBoard", "暂无投资逻辑", theses);
}

function renderTracking(tracking) {
  const entries = objectEntries(tracking);
  setCount("#trackingCount", entries.length);
  renderCollection("#trackingBoard", "暂无追踪事项", tracking);
}
