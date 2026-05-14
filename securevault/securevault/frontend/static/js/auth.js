function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch {
    return null;
  }
}


function isLoggedIn() {
  const authType = localStorage.getItem("auth_type");
  if (authType === "session" && localStorage.getItem("user")) return true;
  if (authType === "keycloak" && localStorage.getItem("access_token")) return true;
  return false;
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "/login.html";
  }
}

function redirectIfLoggedIn() {
  if (isLoggedIn()) {
    window.location.href = "/dashboard.html";
  }
}

function renderNavUser() {
  const el = document.getElementById("nav-user");
  if (!el) return;

  const user = getCurrentUser();
  if (isLoggedIn()) {
    el.innerHTML = `
      <span class="text-muted text-sm">${user ? user.username : ""}</span>
      <button class="btn btn-outline btn-sm" onclick="handleLogout()">로그아웃</button>
    `;
  } else {
    el.innerHTML = `<a href="/login.html">로그인</a>`;
  }
}

async function handleLogout() {
  await apiLogout();
}

/**
 * alert 엘리먼트를 표시하는 공통 유틸
 * @param {string} id     - alert 요소의 id
 * @param {string} msg    - 표시할 메시지
 * @param {'error'|'success'} type
 */
function showAlert(id, msg, type = "error") {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert alert-${type} show`;
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = "alert";
}


document.addEventListener("DOMContentLoaded", renderNavUser);
