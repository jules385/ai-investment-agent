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
      .map((item) => `${item.tier || ""} ${item.name || ""}`.trim())
      .join(" / ");
    const cagr = industry.tam_cagr && (industry.tam_cagr.cagr || industry.tam_cagr.market_size)
      ? `\nTAM/CAGR: ${industry.tam_cagr.market_size || ""} ${industry.tam_cagr.cagr || ""}`.trim()
      : "";
    container.appendChild(createMiniCard(name, `${stockNames || "No stocks"}\n${chainSummary || "No chain data"}${cagr}`));
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
  const stock = (data.stocks || {})[selectedKey] || {};
  if (stock.errors && (stock.errors.investment_thesis || stock.errors.industry_knowledge)) {
    container.appendChild(createMiniCard("AI extraction", stock.errors.investment_thesis || stock.errors.industry_knowledge));
  }

  const bullText = (thesis.bull_theses || thesis.bull || [])
    .slice(0, 4)
    .map((item) => typeof item === "string" ? item : `${item.statement || ""}\n${item.evidence || ""}`)
    .join("\n\n");
  const bearText = (thesis.bear_theses || thesis.bear || [])
    .slice(0, 4)
    .map((item) => typeof item === "string" ? item : `${item.statement || ""}\nTrigger: ${item.trigger_condition || ""}`)
    .join("\n\n");
  const signals = thesis.signals || {};
  const signalText = Array.isArray(signals)
    ? signals.map((signal) => `${signal.dimension || signal["维度"] || "Signal"}: ${signal.direction || signal["方向"] || ""}`).join("\n")
    : Object.entries(signals)
      .map(([name, signal]) => `${name}: ${signal.direction || ""} ${signal.strength || ""} ${signal.score || ""}`.trim())
      .join("\n");
  const assumptions = (thesis.key_assumptions || [])
    .slice(0, 4)
    .map((item) => `${item.assumption || ""}: ${item.verification_status || ""}`)
    .join("\n");

  container.appendChild(createMiniCard("Signals", signalText || "No signals"));
  container.appendChild(createMiniCard("Bull Case", bullText || "No bull case"));
  container.appendChild(createMiniCard("Bear Case", bearText || "No bear case"));
  container.appendChild(createMiniCard("Key Assumptions", assumptions || "No assumptions"));
}

function statusClass(status) {
  if (status === "red" || status === "triggered" || status === "critical") {
    return "status-red";
  }
  if (status === "yellow" || status === "warning" || status === "major") {
    return "status-yellow";
  }
  if (status === "green" || status === "normal" || status === "minor") {
    return "status-green";
  }
  return "";
}

function statusLight(status) {
  if (status === "triggered" || status === "critical" || status === "red") {
    return "RED";
  }
  if (status === "warning" || status === "major" || status === "yellow") {
    return "YELLOW";
  }
  if (status === "normal" || status === "minor" || status === "green") {
    return "GREEN";
  }
  return "INFO";
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

  const stock = (data.stocks || {})[selectedKey] || {};
  if (stock.errors && stock.errors.tracking_data) {
    container.appendChild(createMiniCard("AI extraction", stock.errors.tracking_data));
  }

  const indicators = (tracking[selectedKey] || {}).indicators || [];
  indicators.slice(0, 8).forEach((indicator) => {
    const card = createMiniCard(
      `${statusLight(indicator.status)} ${indicator.name || "Indicator"}`,
      `${indicator.latest_value || ""}\n${indicator.frequency || ""} ${indicator.threshold || ""}`.trim()
    );
    card.classList.add(statusClass(indicator.status));
    container.appendChild(card);
  });

  if (indicators.length === 0) {
    container.appendChild(createMiniCard(selectedKey, "No indicators"));
  }

  const events = (tracking[selectedKey] || {}).events || [];
  if (events.length > 0) {
    container.appendChild(createMiniCard("Event Timeline", events
      .slice(0, 6)
      .map((event) => `${statusLight(event.severity)} ${event.date || ""} ${event.description || ""}`)
      .join("\n")));
  }
}
