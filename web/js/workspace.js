function objectEntries(data) {
  return Object.entries(data || {});
}

function setCount(selector, count) {
  const node = document.querySelector(selector);
  if (node) {
    node.textContent = String(count);
  }
}

function emptyNode(container, text) {
  container.className = "empty-state";
  container.textContent = text;
}

function createMiniCard(title, bodyText) {
  const card = document.createElement("div");
  card.className = "mini-card";

  const titleNode = document.createElement("strong");
  titleNode.textContent = title;

  const body = document.createElement("span");
  body.textContent = bodyText || "No data";

  card.append(titleNode, body);
  return card;
}

function renderKnowledgeBase(industries) {
  const container = document.querySelector("#knowledgeBase");
  const entries = objectEntries(industries);
  setCount("#industryCount", entries.length);

  if (!container) {
    return;
  }
  if (entries.length === 0) {
    emptyNode(container, "No industry data");
    return;
  }

  container.className = "workspace-list industry-grid";
  container.innerHTML = "";
  entries.forEach(([name, industry]) => {
    const stockNames = (industry.stocks || []).map((stock) => stock.stock).join(", ");
    const chainSummary = (industry.chain || [])
      .slice(0, 3)
      .map((item) => item.name)
      .join(" / ");
    container.appendChild(createMiniCard(name, `${stockNames || "No stocks"}\n${chainSummary || "No chain data"}`));
  });
}

function stockOptions(data) {
  return objectEntries(data.stocks || {}).map(([key, stock]) => ({
    key,
    label: `${stock.code || ""}-${stock.name || key}`
  }));
}

function ensureStockSelect(container, options, selectedKey, onChange) {
  const wrap = document.createElement("div");
  wrap.className = "workspace-control";

  const select = document.createElement("select");
  options.forEach((option) => {
    const item = document.createElement("option");
    item.value = option.key;
    item.textContent = option.label;
    item.selected = option.key === selectedKey;
    select.appendChild(item);
  });
  select.addEventListener("change", () => onChange(select.value));

  wrap.appendChild(select);
  container.appendChild(wrap);
  return select;
}

function renderTheses(theses) {
  const data = window.workspaceData || {};
  const options = stockOptions(data);
  const entries = objectEntries(theses);
  setCount("#thesisCount", entries.length);

  const container = document.querySelector("#thesesBoard");
  if (!container) {
    return;
  }
  if (entries.length === 0 || options.length === 0) {
    emptyNode(container, "No thesis data");
    return;
  }

  const selectedKey = window.selectedStock || options[0].key;
  window.selectedStock = selectedKey;
  container.className = "workspace-list";
  container.innerHTML = "";
  ensureStockSelect(container, options, selectedKey, (nextKey) => {
    window.selectedStock = nextKey;
    renderTheses(window.workspaceData.theses || {});
    renderTracking(window.workspaceData.tracking || {});
  });

  const thesis = theses[selectedKey] || {};
  container.appendChild(createMiniCard("Summary", thesis.summary || "No summary"));

  const signalText = (thesis.signals || [])
    .slice(0, 4)
    .map((signal) => `${signal["维度"] || signal.dimension || "Signal"}: ${signal["方向"] || signal.direction || ""}`)
    .join("\n");
  container.appendChild(createMiniCard("Signals", signalText || "No signals"));

  const bullText = (thesis.bull || []).slice(0, 3).join("\n");
  const bearText = (thesis.bear || []).slice(0, 3).join("\n");
  container.appendChild(createMiniCard("Bull Case", bullText || "No bull case"));
  container.appendChild(createMiniCard("Bear Case", bearText || "No bear case"));
}

function statusClass(status) {
  if (status === "red") {
    return "status-red";
  }
  if (status === "yellow") {
    return "status-yellow";
  }
  if (status === "green") {
    return "status-green";
  }
  return "";
}

function renderTracking(tracking) {
  const data = window.workspaceData || {};
  const options = stockOptions(data);
  const entries = objectEntries(tracking);
  setCount("#trackingCount", entries.length);

  const container = document.querySelector("#trackingBoard");
  if (!container) {
    return;
  }
  if (entries.length === 0 || options.length === 0) {
    emptyNode(container, "No tracking data");
    return;
  }

  const selectedKey = window.selectedStock || options[0].key;
  window.selectedStock = selectedKey;
  container.className = "workspace-list";
  container.innerHTML = "";

  const indicators = (tracking[selectedKey] || {}).indicators || [];
  if (indicators.length === 0) {
    container.appendChild(createMiniCard(selectedKey, "No indicators"));
    return;
  }

  indicators.slice(0, 8).forEach((indicator) => {
    const card = createMiniCard(indicator.name, `${indicator.frequency || ""} ${indicator.threshold || ""}`.trim());
    card.classList.add(statusClass(indicator.status));
    container.appendChild(card);
  });
}
