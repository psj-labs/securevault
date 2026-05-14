const API_BASE = window.location.origin;

async function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const token = localStorage.getItem("access_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  let data;
  try { data = await res.json(); } catch { data = null; }
  return { ok: res.ok, status: res.status, data };
}

async function apiRegister(username, password, email) {
  return apiFetch("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, email }),
  });
}

async function apiLogin(username, password) {
  const result = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  if (result.ok && result.data?.user) {
    localStorage.setItem("user", JSON.stringify(result.data.user));
    localStorage.setItem("auth_type", "session");
  }

  return result;
}

function apiKeycloakLogin() {
  window.location.href = `${API_BASE}/api/auth/keycloak/login`;
}

async function apiLogout() {
  const authType = localStorage.getItem("auth_type");
  await apiFetch("/api/auth/logout", { method: "POST" });
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  localStorage.removeItem("auth_type");
  if (authType === "keycloak") {
    window.location.href = "http://192.168.11.15:8080/realms/pentest-realm/protocol/openid-connect/logout?post_logout_redirect_uri=http://192.168.11.12/login.html&client_id=pentest-client";
    return;
  }
  window.location.href = "/login.html";
}

async function apiGetMe() {
  return apiFetch("/api/users/me");
}

async function apiUpdateMe(payload) {
  return apiFetch("/api/users/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

function getToken() {
  return localStorage.getItem("access_token");
}