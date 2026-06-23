async function loadWorkspaceData() {
  setWorkspaceLoading(true);
  try {
    const response = await fetch("/api/workspace");
    if (!response.ok) {
      throw new Error(`Workspace API returned ${response.status}`);
    }
    const data = await response.json();
    window.workspaceData = data;
    renderKnowledgeBase(data.industries || {});
    renderTheses(data.theses || {});
    renderTracking(data.tracking || {});
  } catch (error) {
    showToast(`Workspace data is unavailable: ${error.message}`);
    renderKnowledgeBase({});
    renderTheses({});
    renderTracking({});
  } finally {
    setWorkspaceLoading(false);
  }
}

function showToast(message) {
  let toast = document.querySelector("#appToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "appToast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(toast.hideTimer);
  toast.hideTimer = window.setTimeout(() => toast.classList.remove("show"), 4200);
}

function setWorkspaceLoading(isLoading) {
  document.querySelectorAll("#knowledgeBase, #thesesBoard, #trackingBoard").forEach((node) => {
    node.classList.toggle("loading", isLoading);
    if (isLoading && node.children.length === 0) {
      node.textContent = "Loading...";
    }
  });
}

function activateTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });

  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabName);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const commands = ["/analyze-initial", "/analyze-weekly", "/analyze-quarterly", "/beautify-report", "/help"];

  document.querySelectorAll(".tab-btn").forEach((button) => {
    button.addEventListener("click", () => activateTab(button.dataset.tab));
  });

  document.querySelectorAll("[data-prompt]").forEach((button, index) => {
    const command = commands[index] || button.dataset.prompt;
    button.dataset.prompt = command;
    button.textContent = command;
    button.addEventListener("click", () => {
      const input = document.querySelector("#chatInput");
      input.value = button.dataset.prompt;
      input.focus();
    });
  });

  const commandGrid = document.querySelector(".command-grid");
  if (commandGrid && commandGrid.children.length < commands.length) {
    commands.slice(commandGrid.children.length).forEach((command) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.prompt = command;
      button.textContent = command;
      button.addEventListener("click", () => {
        const input = document.querySelector("#chatInput");
        input.value = command;
        input.focus();
      });
      commandGrid.appendChild(button);
    });
  }

  loadWorkspaceData();
});

window.addEventListener("unhandledrejection", (event) => {
  showToast(event.reason && event.reason.message ? event.reason.message : "Unexpected network error");
});
