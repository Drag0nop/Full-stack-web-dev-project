const state = {
  token: localStorage.getItem("acd_token") || "",
  currentUser: null,
  projects: [],
  activeProject: null,
  activeFileId: null,
};

const elements = {
  authSection: document.getElementById("auth-section"),
  appSection: document.getElementById("app-section"),
  authStatus: document.getElementById("auth-status"),
  uploadStatus: document.getElementById("upload-status"),
  registerForm: document.getElementById("register-form"),
  loginForm: document.getElementById("login-form"),
  uploadForm: document.getElementById("upload-form"),
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
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const payload = await safeJson(response);
    throw new Error(payload.detail || "Request failed");
  }
  return safeJson(response);
};

const setStatus = (node, message, success = false) => {
  node.textContent = message;
  node.classList.toggle("success", success);
};

const persistToken = (token) => {
  state.token = token;
  localStorage.setItem("acd_token", token);
};

const clearSession = () => {
  state.token = "";
  state.currentUser = null;
  state.projects = [];
  state.activeProject = null;
  state.activeFileId = null;
  localStorage.removeItem("acd_token");
  render();
};

const markdownToHtml = (source) =>
  escapeHtml(source)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n```[\w-]*\n([\s\S]*?)\n```/g, "<pre>$1</pre>")
    .replace(/\n- (.*)/g, "<br>• $1")
    .replace(/\n/g, "<br>");

const escapeHtml = (value) =>
  value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

const render = () => {
  const authenticated = Boolean(state.token && state.currentUser);
  elements.authSection.classList.toggle("hidden", authenticated);
  elements.appSection.classList.toggle("hidden", !authenticated);
  elements.userEmail.textContent = state.currentUser?.email || "Sign in to start";
  renderProjectList();
  renderProjectDetail();
};

const renderProjectList = () => {
  elements.projectList.innerHTML = "";
  if (!state.projects.length) {
    elements.projectList.innerHTML = `<p class="subtle">No projects yet. Upload a ZIP to generate docs.</p>`;
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
    elements.projectMeta.textContent = "Upload a ZIP or open an existing run.";
    elements.docTitle.textContent = "Repository Overview";
    elements.docBody.innerHTML = `<div class="doc-block">Documentation will appear here once a project is loaded.</div>`;
    elements.chatLog.innerHTML = "";
    return;
  }
  const project = state.activeProject;
  elements.projectTitle.textContent = project.name;
  elements.projectMeta.textContent = `${project.metadata.file_count} files • ${project.metadata.languages.join(", ")}`;
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

const loadSession = async () => {
  if (!state.token) {
    render();
    return;
  }
  try {
    state.currentUser = await api("/api/auth/me");
    state.projects = await api("/api/projects");
  } catch {
    clearSession();
  }
  render();
};

const loadProject = async (projectId) => {
  state.activeProject = await api(`/api/projects/${projectId}`);
  state.activeFileId = null;
  render();
};

elements.registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email: form.get("email"),
        password: form.get("password"),
      }),
    });
    setStatus(elements.authStatus, "Account created. You can sign in now.", true);
    event.target.reset();
  } catch (error) {
    setStatus(elements.authStatus, error.message);
  }
});

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const body = new URLSearchParams();
  body.set("username", form.get("email"));
  body.set("password", form.get("password"));
  try {
    const token = await api("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    persistToken(token.access_token);
    await loadSession();
    setStatus(elements.authStatus, "Signed in.", true);
  } catch (error) {
    setStatus(elements.authStatus, error.message);
  }
});

elements.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    setStatus(elements.uploadStatus, "Uploading and generating documentation...");
    state.activeProject = await api("/api/projects/upload", {
      method: "POST",
      body: form,
    });
    state.projects = await api("/api/projects");
    state.activeFileId = null;
    render();
    setStatus(elements.uploadStatus, "Documentation generated successfully.", true);
    event.target.reset();
  } catch (error) {
    setStatus(elements.uploadStatus, error.message);
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

elements.logoutButton.addEventListener("click", clearSession);

loadSession();
