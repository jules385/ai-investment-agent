async function loadWorkspaceData() {
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
    console.warn("Workspace data is unavailable:", error);
    renderKnowledgeBase({});
    renderTheses({});
    renderTracking({});
  }
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
