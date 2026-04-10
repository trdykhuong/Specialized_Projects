const API_BASE = "http://localhost:5000/api";
const TOKEN_KEY = "jobtrust_access_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  if (!token) {
    localStorage.removeItem(TOKEN_KEY);
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
}

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    const message = data?.error || data?.message || `API error ${response.status}`;
    const apiError = new Error(message);
    apiError.status = response.status;
    apiError.payload = data;
    throw apiError;
  }

  return data;
}

function withQuery(endpoint, params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return `${endpoint}${query ? `?${query}` : ""}`;
}

export const authStorage = {
  tokenKey: TOKEN_KEY,
  getToken,
  setToken,
  clear() {
    localStorage.removeItem(TOKEN_KEY);
  },
};

export const api = {
  register(payload) {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  login(payload) {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getProfile() {
    return request("/auth/profile");
  },
  getOverview() {
    return request("/dashboard/overview");
  },
  updateProfile(payload) {
    return request("/auth/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  getJobs(params = {}) {
    return request(withQuery("/jobs", params));
  },
  analyzeJob(payload) {
    return request("/jobs/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  batchAnalyze(payload) {
    return request("/jobs/batch-analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  recommend(payload) {
    return request("/jobs/recommend", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getSavedJobs(params = {}) {
    return request(withQuery("/saved-jobs", params));
  },
  createSavedJob(payload) {
    return request("/saved-jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateSavedJob(id, payload) {
    return request(`/saved-jobs/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteSavedJob(id) {
    return request(`/saved-jobs/${id}`, {
      method: "DELETE",
    });
  },
  applySavedJob(id, payload = {}) {
    return request(`/saved-jobs/${id}/apply`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getApplications(params = {}) {
    return request(withQuery("/applications", params));
  },
  createApplication(payload) {
    return request("/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateApplication(id, payload) {
    return request(`/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteApplication(id) {
    return request(`/applications/${id}`, {
      method: "DELETE",
    });
  },
  getStatistics() {
    return request("/statistics/overview");
  },
  getRiskSummary() {
    return request("/statistics/risk-summary");
  },
  getBlacklist() {
    return request("/jobs/blacklist");
  },
  updateBlacklist(payload) {
    return request("/jobs/blacklist/update", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  checkBlacklist(job) {
    return request("/jobs/blacklist/check", {
      method: "POST",
      body: JSON.stringify({ job }),
    });
  },
};
