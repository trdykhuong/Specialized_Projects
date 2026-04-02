const API_BASE = "http://localhost:5000/api";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }

  return response.json();
}

export const api = {
  getOverview: () => request("/dashboard/overview"),
  getJobs: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/jobs${query ? `?${query}` : ""}`);
  },
  analyzeJob: (payload) =>
    request("/jobs/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  batchAnalyze: (jobs) =>
    request("/jobs/batch-analyze", {
      method: "POST",
      body: JSON.stringify({ jobs }),
    }),
  recommend: (payload) =>
    request("/personalization/recommend", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getBlacklist: () => request("/blacklist"),
  updateBlacklist: (payload) =>
    request("/blacklist/update", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  checkBlacklist: (job) =>
    request("/blacklist/check", {
      method: "POST",
      body: JSON.stringify({ job }),
    }),
};
