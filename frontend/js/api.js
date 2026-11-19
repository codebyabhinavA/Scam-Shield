// Scam Shield - API Client & Session Management
const API_BASE = (function () {
  const h = window.location.hostname;
  if (h === "127.0.0.1" || h === "localhost") return "http://127.0.0.1:8000";
  return "https://PLACEHOLDER-API.onrender.com";
})();
const TOKEN_KEY = "scamshield_token";
const USER_KEY = "scamshield_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setUser(user) {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function isAuthenticated() {
  return !!getToken();
}

export function logout() {
  clearToken();
  window.location.href = "login.html";
}

// Turns FastAPI error responses into human-readable text
export function errorMessage(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail) && data.detail.length > 0) {
    const first = data.detail[0];
    const field = first.loc ? first.loc[first.loc.length - 1] : "input";
    return `Invalid ${field}: ${first.msg}`;
  }
  return `Something went wrong (error ${status}).`;
}

// Core Fetch Utility
export async function apiFetch(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error("Can't reach the server right now. If it was idle, wait up to a minute and try again.");
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch (err) {
    /* No json response */
  }

  if (response.status === 401 && auth) {
    clearToken();
    if (!window.location.pathname.endsWith("login.html") && !window.location.pathname.endsWith("signup.html")) {
      window.location.href = "login.html";
    }
    throw new Error("Please log in again.");
  }

  if (!response.ok) {
    throw new Error(errorMessage(data, response.status));
  }

  return data;
}

export async function requireLogin() {
  if (!getToken()) {
    window.location.href = "login.html";
    return null;
  }
  try {
    const user = await apiFetch("/auth/me");
    setUser(user);
    return user;
  } catch {
    return null;
  }
}

export function requireAuth() {
  if (!getToken()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

// Authentication Service
export const authApi = {
  async signup(email, password) {
    return apiFetch("/auth/signup", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
  },

  async login(email, password) {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    if (data?.access_token) {
      setToken(data.access_token);
      try {
        const user = await apiFetch("/auth/me");
        setUser(user);
      } catch {
        setUser({ email });
      }
    }
    return data;
  },

  async getMe() {
    const user = await apiFetch("/auth/me");
    setUser(user);
    return user;
  },
};

// Checks Analysis & History Service
export const checksApi = {
  async createCheck(messageText) {
    return apiFetch("/checks", {
      method: "POST",
      body: { message_text: messageText },
    });
  },

  async listChecks() {
    return apiFetch("/checks");
  },

  async getCheck(checkId) {
    return apiFetch(`/checks/${checkId}`);
  },

  async deleteCheck(checkId) {
    return apiFetch(`/checks/${checkId}`, {
      method: "DELETE",
    });
  },

  async setFeedback(checkId, feedback) {
    return apiFetch(`/checks/${checkId}/feedback`, {
      method: "PATCH",
      body: { feedback },
    });
  },
};
