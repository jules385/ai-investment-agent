function objectEntries(data) {
  return Object.entries(data || {});
}

function setCount(selector, count) {
  const node = document.querySelector(selector);
  if (node) {
    node.textContent = String(count);
  }
}

function clearAs(container, className) {
  container.className = className;
  container.innerHTML = "";
}

function emptyNode(container, text) {
  clearAs(container, "empty-state");
  container.textContent = text;
}

function createMiniCard(title, bodyText, className = "") {
  const card = document.createElement("div");
  card.className = `mini-card ${className}`.trim();

  const titleNode = document.createElement("strong");
  titleNode.textContent = title;

  const body = document.createElement("span");
  body.textContent = bodyText || "No data";

  card.append(titleNode, body);
  return card;
}

function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

function stockOptions(data) {
  return objectEntries(data.stocks || {}).map(([key, stock]) => ({
    key,
    label: `${stock.code || ""}-${stock.name || key}`.replace(/^-/, "")
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
}

function statusClass(status) {
  if (["red", "triggered", "critical", "high"].includes(status)) {
    return "status-red";
  }
  if (["yellow", "warning", "major", "medium"].includes(status)) {
    return "status-yellow";
  }
  if (["green", "normal", "minor", "low"].includes(status)) {
    return "status-green";
  }
  return "";
}

function statusLight(status) {
  if (["triggered", "critical", "red", "high"].includes(status)) {
    return "RED";
  }
  if (["warning", "major", "yellow", "medium"].includes(status)) {
    return "YELLOW";
  }
  if (["normal", "minor", "green", "low"].includes(status)) {
    return "GREEN";
  }
  return "INFO";
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

  clearAs(container, "workspace-list industry-grid");
  entries.forEach(([name, industry]) => {
    const card = createMiniCard(
      name,
      `${normalizeArray(industry.stocks).length} stocks\n${normalizeArray(industry.chain).length} chain nodes`,
      "industry-card"
    );
    card.tabIndex = 0;
    card.addEventListener("click", () => renderIndustryDetail(name, industry));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        renderIndustryDetail(name, industry);
      }
    });
    container.appendChild(card);
  });

  renderIndustryDetail(entries[0][0], entries[0][1]);
}

function renderIndustryDetail(name, industry) {
  const container = document.querySelector("#knowledgeBase");
  const oldDetail = container.querySelector(".industry-detail");
  if (oldDetail) {
    oldDetail.remove();
  }

  const detail = document.createElement("section");
  detail.className = "industry-detail";
  detail.appendChild(createMiniCard("Industry", name));

  const chain = document.createElement("div");
  chain.className = "chain-tree";
  const chainTitle = document.createElement("strong");
  chainTitle.textContent = "Industry Chain";
  chain.appendChild(chainTitle);
  normalizeArray(industry.chain).forEach((node) => {
    const item = document.createElement("div");
    item.className = "chain-node";
    item.textContent = `${node.tier || "node"} / ${node.name || ""} / ${node.companies || ""}`;
    chain.appendChild(item);
  });
  if (normalizeArray(industry.chain).length === 0) {
    const item = document.createElement("div");
    item.className = "chain-node";
    item.textContent = "No chain data";
    chain.appendChild(item);
  }
  detail.appendChild(chain);

  const tam = industry.tam_cagr || {};
  detail.appendChild(createMiniCard("TAM / CAGR", `${tam.market_size || ""}\n${tam.cagr || ""}\n${tam.forecast_year || ""}`.trim()));
  detail.appendChild(renderBenchmarks(industry.financial_benchmarks || {}));
  container.appendChild(detail);
}

function renderBenchmarks(benchmarks) {
  const wrap = document.createElement("div");
  wrap.className = "benchmark-table";
  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th>Company</th><th>Revenue</th><th>Net Profit</th><th>GM</th><th>PE</th></tr></thead>";
  const tbody = document.createElement("tbody");
  objectEntries(benchmarks).forEach(([company, item]) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${company}</td><td>${item.revenue || ""}</td><td>${item.net_profit || ""}</td><td>${item.gross_margin || ""}</td><td>${item.pe || ""}</td>`;
    tbody.appendChild(row);
  });
  if (tbody.children.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan=\"5\">No benchmarks</td>";
    tbody.appendChild(row);
  }
  table.appendChild(tbody);
  wrap.appendChild(table);
  return wrap;
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
  clearAs(container, "workspace-list thesis-board");
  ensureStockSelect(container, options, selectedKey, (nextKey) => {
    window.selectedStock = nextKey;
    renderTheses(window.workspaceData.theses || {});
    renderTracking(window.workspaceData.tracking || {});
  });

  const stock = (data.stocks || {})[selectedKey] || {};
  if (stock.errors && (stock.errors.investment_thesis || stock.errors.industry_knowledge)) {
    container.appendChild(createMiniCard("AI extraction", stock.errors.investment_thesis || stock.errors.industry_knowledge));
  }

  const thesis = theses[selectedKey] || {};
  renderSignalDashboard(container, thesis.signals || {});
  renderThesisCards(container, "Bull Case", thesis.bull_theses || [], "bull-card");
  renderThesisCards(container, "Bear Case", thesis.bear_theses || [], "bear-card");
  renderDecisions(container, (window.workspaceData.tracking || {})[selectedKey] || {});
}

function renderSignalDashboard(container, signals) {
  const dashboard = document.createElement("div");
  dashboard.className = "signal-dashboard";
  const labels = {
    fundamental: "Fundamental",
    chip_flow: "Chip Flow",
    technical: "Technical",
    sentiment: "Sentiment"
  };
  Object.entries(labels).forEach(([key, label]) => {
    const signal = signals[key] || {};
    const card = createMiniCard(
      `${statusLight(signal.direction)} ${label}`,
      `${signal.direction || ""}\n${signal.strength || ""}\nScore: ${signal.score || "--"}`,
      "signal-card"
    );
    dashboard.appendChild(card);
  });
  container.appendChild(dashboard);
}

function renderThesisCards(container, title, items, className) {
  const group = document.createElement("div");
  group.className = "thesis-card-grid";
  normalizeArray(items).forEach((item) => {
    group.appendChild(createMiniCard(
      item.status || item.severity || title,
      `${item.statement || ""}\n${item.evidence || item.trigger_condition || ""}`,
      className
    ));
  });
  if (group.children.length === 0) {
    group.appendChild(createMiniCard(title, "No data", className));
  }
  container.appendChild(group);
}

function renderDecisions(container, tracking) {
  const decisions = normalizeArray(tracking.decisions);
  const body = decisions.length
    ? decisions.map((item) => `${item.date || ""} ${item.rating || ""} ${item.action || ""}\n${item.rationale || ""}`).join("\n\n")
    : "No decisions";
  container.appendChild(createMiniCard("Decision Log", body));
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
  clearAs(container, "workspace-list tracking-board");

  const stock = (data.stocks || {})[selectedKey] || {};
  if (stock.errors && stock.errors.tracking_data) {
    container.appendChild(createMiniCard("AI extraction", stock.errors.tracking_data));
  }

  const selectedTracking = tracking[selectedKey] || {};
  const indicatorGrid = document.createElement("div");
  indicatorGrid.className = "indicator-grid";
  normalizeArray(selectedTracking.indicators).slice(0, 12).forEach((indicator) => {
    const card = createMiniCard(
      `${statusLight(indicator.status)} ${indicator.name || "Indicator"}`,
      `${indicator.latest_value || ""}\nThreshold: ${indicator.threshold || "--"}\n${indicator.frequency || ""}`,
      `indicator-card ${statusClass(indicator.status)}`
    );
    indicatorGrid.appendChild(card);
  });
  if (indicatorGrid.children.length === 0) {
    indicatorGrid.appendChild(createMiniCard(selectedKey, "No indicators", "indicator-card"));
  }
  container.appendChild(indicatorGrid);

  container.appendChild(renderEventTimeline(selectedTracking.events || []));
  container.appendChild(renderResearchForm(selectedKey));
}

function renderEventTimeline(events) {
  const timeline = document.createElement("div");
  timeline.className = "event-timeline";
  const sorted = normalizeArray(events).slice().sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
  sorted.slice(0, 10).forEach((event) => {
    const item = document.createElement("details");
    item.className = `event-item ${statusClass(event.severity)}`;
    const summary = document.createElement("summary");
    summary.textContent = `${statusLight(event.severity)} ${event.date || ""} ${event.description || "Event"}`;
    const body = document.createElement("pre");
    body.textContent = JSON.stringify(event, null, 2);
    item.append(summary, body);
    timeline.appendChild(item);
  });
  if (timeline.children.length === 0) {
    timeline.appendChild(createMiniCard("Event Timeline", "No events"));
  }
  return timeline;
}

function renderResearchForm(symbol) {
  const form = document.createElement("form");
  form.className = "research-note-form";
  const input = document.createElement("textarea");
  input.rows = 4;
  input.placeholder = "Add research note...";
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Submit";
  const status = document.createElement("span");
  status.className = "research-note-status";

  form.append(input, button, status);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const note = input.value.trim();
    if (!note) {
      return;
    }
    button.disabled = true;
    status.textContent = "Submitting...";
    try {
      const response = await fetch("/api/research-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, note })
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.message || `HTTP ${response.status}`);
      }
      window.workspaceData.tracking[symbol] = result.tracking;
      input.value = "";
      status.textContent = result.error ? `Saved with fallback: ${result.error}` : "Saved";
      renderTracking(window.workspaceData.tracking || {});
    } catch (error) {
      status.textContent = `Failed: ${error.message}`;
    } finally {
      button.disabled = false;
    }
  });
  return form;
}
