const state = {
  token: localStorage.getItem("acd_token") || "",
  currentUser: null,
  projects: [],
  activeProject: null,
  activeFileId: null,
};

const elements = {
  uploadStatus: document.getElementById("upload-status"),
  uploadForm: document.getElementById("upload-form"),
  githubForm: document.getElementById("github-form"),
  projectList: document.getElementById("project-list"),
  treeRoot: document.getElementById("tree-root"),
  projectTitle: document.getElementById("project-title"),
  projectMeta: document.getElementById("project-meta"),
  docTitle: document.getElementById("doc-title"),
  docBody: document.getElementById("doc-body"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  chatLog: document.getElementById("chat-log"),
  speakButton: document.getElementById("speak-button"),
  voiceButton: document.getElementById("voice-button"),
  logoutButton: document.getElementById("logout-button"),
  userEmail: document.getElementById("user-email"),
};

const safeJson = async (response) => {
  const text = await response.text();
  return text ? JSON.parse(text) : {};
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${state.token}`,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const payload = await safeJson(response);
    throw new Error(payload.detail || "Request failed");
  }
  return safeJson(response);
};

const setStatus = (message, success = false) => {
  elements.uploadStatus.textContent = message;
  elements.uploadStatus.classList.toggle("success", success);
};

const redirectTo = (path) => {
  if (window.location.pathname !== path) {
    window.location.assign(path);
  }
};

const escapeHtml = (value) =>
  value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

const markdownToHtml = (source) =>
  escapeHtml(source)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n```[\w-]*\n([\s\S]*?)\n```/g, "<pre>$1</pre>")
    .replace(/\n- (.*)/g, "<br>&bull; $1")
    .replace(/\n/g, "<br>");

const renderProjectList = () => {
  elements.projectList.innerHTML = "";
  if (!state.projects.length) {
    elements.projectList.innerHTML = `<p class="subtle">No projects yet. Upload a ZIP or import a GitHub repository.</p>`;
    return;
  }
  state.projects.forEach((project) => {
    const item = document.createElement("li");
    item.className = "project-item";
    const button = document.createElement("button");
    button.innerHTML = `<strong>${project.name}</strong><br><span class="mini">${new Date(project.created_at).toLocaleString()}</span>`;
    button.onclick = () => loadProject(project.id);
    item.appendChild(button);
    elements.projectList.appendChild(item);
  });
};

const renderTree = (node, container, parentPath = "") => {
  (node.children || []).forEach((child) => {
    const item = document.createElement("li");
    item.className = "tree-node";
    const currentPath = parentPath ? `${parentPath}/${child.name}` : child.name;
    const button = document.createElement("button");
    button.textContent = child.type === "directory" ? `[Dir] ${child.name}` : child.name;
    item.appendChild(button);

    if (child.type === "file") {
      const file = state.activeProject.files.find((entry) => entry.path === currentPath);
      if (file?.id === state.activeFileId) {
        button.classList.add("active");
      }
      button.onclick = () => {
        state.activeFileId = file?.id || null;
        renderProjectDetail();
      };
    } else {
      const nested = document.createElement("ul");
      nested.className = "tree-group";
      renderTree(child, nested, currentPath);
      button.onclick = () => nested.classList.toggle("hidden");
      item.appendChild(nested);
    }
    container.appendChild(item);
  });
};

const renderProjectDetail = () => {
  elements.treeRoot.innerHTML = "";
  if (!state.activeProject) {
    elements.projectTitle.textContent = "Choose a project";
    elements.projectMeta.textContent = "Upload a ZIP or import a GitHub repository.";
    elements.docTitle.textContent = "Repository Overview";
    elements.docBody.innerHTML = `<div class="doc-block">Documentation will appear here once a project is loaded.</div>`;
    elements.chatLog.innerHTML = "";
    return;
  }

  const project = state.activeProject;
  const sourceLabel = project.source_type === "github" ? "GitHub" : "ZIP";
  elements.projectTitle.textContent = project.name;
  elements.projectMeta.textContent = `${project.metadata.file_count} files | ${project.metadata.languages.join(", ")} | ${sourceLabel}`;
  renderTree(project.tree, elements.treeRoot);

  const file = project.files.find((entry) => entry.id === state.activeFileId);
  if (!file) {
    elements.docTitle.textContent = "Repository Overview";
    elements.docBody.innerHTML = `
      <div class="pill">Project Summary</div>
      <div class="doc-block">${markdownToHtml(project.overview_markdown)}</div>
    `;
    return;
  }

  const symbols = file.symbols?.length
    ? `<div class="doc-block"><strong>Extracted symbols</strong><pre>${escapeHtml(JSON.stringify(file.symbols, null, 2))}</pre></div>`
    : "";
  elements.docTitle.textContent = file.path;
  elements.docBody.innerHTML = `
    <div class="pill">${file.language}</div>
    <div class="doc-block">${markdownToHtml(file.summary_markdown)}</div>
    ${symbols}
  `;
};

const render = () => {
  elements.userEmail.textContent = state.currentUser?.email || "Signed in";
  renderProjectList();
  renderProjectDetail();
};

const appendChat = (role, content) => {
  const entry = document.createElement("div");
  entry.className = `chat-entry ${role}`;
  entry.textContent = content;
  elements.chatLog.appendChild(entry);
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
};

const speak = (text) => {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
};

const loadProject = async (projectId) => {
  state.activeProject = await api(`/api/projects/${projectId}`);
  state.activeFileId = null;
  render();
};

const initialize = async () => {
  if (!state.token) {
    redirectTo("/login");
    return;
  }
  try {
    state.currentUser = await api("/api/auth/me");
    state.projects = await api("/api/projects");
    render();
  } catch {
    localStorage.removeItem("acd_token");
    redirectTo("/login");
  }
};

elements.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    setStatus("Uploading ZIP and generating documentation...");
    state.activeProject = await api("/api/projects/upload", {
      method: "POST",
      body: form,
    });
    state.projects = await api("/api/projects");
    state.activeFileId = null;
    render();
    setStatus("Documentation generated successfully.", true);
    event.target.reset();
  } catch (error) {
    setStatus(error.message);
  }
});

elements.githubForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    setStatus("Fetching GitHub repository and generating documentation...");
    state.activeProject = await api("/api/projects/import-github", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        repo_url: form.get("repo_url"),
      }),
    });
    state.projects = await api("/api/projects");
    state.activeFileId = null;
    render();
    setStatus("GitHub repository documented successfully.", true);
    event.target.reset();
  } catch (error) {
    setStatus(error.message);
  }
});

elements.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.activeProject) return;
  const question = elements.chatInput.value.trim();
  if (!question) return;
  appendChat("user", question);
  elements.chatInput.value = "";
  try {
    const reply = await api(`/api/projects/${state.activeProject.id}/chat`, {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    appendChat("assistant", reply.answer_markdown);
    speak(reply.answer_markdown);
  } catch (error) {
    appendChat("assistant", `Error: ${error.message}`);
  }
});

elements.speakButton.addEventListener("click", () => {
  const activeText =
    state.activeProject?.files.find((entry) => entry.id === state.activeFileId)?.summary_markdown ||
    state.activeProject?.overview_markdown ||
    "Load a project first.";
  speak(activeText);
});

elements.voiceButton.addEventListener("click", () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    appendChat("assistant", "Speech recognition is not supported in this browser. Try Chrome or Edge.");
    return;
  }
  const recognition = new Recognition();
  recognition.lang = "en-US";
  recognition.onstart = () => {
    elements.voiceButton.textContent = "Listening...";
  };
  recognition.onend = () => {
    elements.voiceButton.textContent = "Ask By Voice";
  };
  recognition.onresult = (event) => {
    elements.chatInput.value = event.results[0][0].transcript;
  };
  recognition.start();
});

elements.logoutButton.addEventListener("click", () => {
  localStorage.removeItem("acd_token");
  redirectTo("/login");
});

initialize();
