const page = document.body.dataset.page || "";
const token = localStorage.getItem("acd_token") || "";

const authStatus = document.getElementById("auth-status");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

const safeJson = async (response) => {
  const text = await response.text();
  return text ? JSON.parse(text) : {};
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    ...options,
    headers: {
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
  if (!authStatus) return;
  authStatus.textContent = message;
  authStatus.classList.toggle("success", success);
};

const redirectTo = (path) => {
  if (window.location.pathname !== path) {
    window.location.assign(path);
  }
};

const verifyExistingSession = async () => {
  if (!token) return;
  try {
    const response = await fetch("/api/auth/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.ok) {
      redirectTo("/home");
    }
  } catch {
    localStorage.removeItem("acd_token");
  }
};

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    const body = new URLSearchParams();
    body.set("username", form.get("email"));
    body.set("password", form.get("password"));
    try {
      const result = await api("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      localStorage.setItem("acd_token", result.access_token);
      setStatus("Signed in. Redirecting...", true);
      redirectTo("/home");
    } catch (error) {
      setStatus(error.message);
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    try {
      await api("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      setStatus("Account created. Redirecting to login...", true);
      event.target.reset();
      setTimeout(() => redirectTo("/login"), 500);
    } catch (error) {
      setStatus(error.message);
    }
  });
}

if (page === "login" || page === "register") {
  verifyExistingSession();
}
