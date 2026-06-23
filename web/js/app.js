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
  document.querySelectorAll(".tab-btn").forEach((button) => {
    button.addEventListener("click", () => activateTab(button.dataset.tab));
  });

  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.querySelector("#chatInput");
      input.value = button.dataset.prompt;
      input.focus();
    });
  });

  loadWorkspaceData();
});
