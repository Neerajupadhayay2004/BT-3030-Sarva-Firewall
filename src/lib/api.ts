// API Configuration and Integration
const API_BASE_URL = '';

/**
 * Helper to get the JWT token from localStorage
 */
const getAuthToken = () => localStorage.getItem("token");

/**
 * Generic fetch wrapper to include auth headers
 */
export const secureFetch = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  const normalizedUrl = url.startsWith('/api') ? url : `/api${url}`;
  const response = await fetch(`${API_BASE_URL}${normalizedUrl}`, { ...options, headers });

  if (!response.ok) {
    const errText = await response.text().catch(() => response.statusText);
    return { error: true, status: response.status, message: errText };
  }

  // Handle unauthorized globally
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("isAuthenticated");
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  try {
    return await response.json();
  } catch {
    return { error: true, message: 'Invalid JSON response', status: response.status };
  }
};

// Auth APIs
export const authAPI = {
  login: async (credentials: Record<string, string>) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    return response.json();
  }
};

// Dashboard APIs
export const dashboardAPI = {
  getStats: async () => secureFetch('/dashboard/stats'),
  getAttacks: async (limit = 50, offset = 0) => secureFetch(`/dashboard/attacks?limit=${limit}&offset=${offset}`),
  getRequests: async (limit = 100, offset = 0) => secureFetch(`/dashboard/requests?limit=${limit}&offset=${offset}`),
  getTimeline: async (hours = 24) => secureFetch(`/dashboard/timeline?hours=${hours}`),
  getTopIPs: async (limit = 10) => secureFetch(`/dashboard/top-ips?limit=${limit}`),
  getGeoData: async () => secureFetch('/dashboard/geo-data')
};

// Other APIs
export const threatAPI = {
  getRecentThreats: async (limit = 10) => secureFetch(`/threats/recent?limit=${limit}`),
  getStats: async () => secureFetch('/threats/stats'),
  getTimeline: async (hours = 24) => secureFetch(`/threats/timeline?hours=${hours}`),
  getThreatTimeline: async (hours = 24) => secureFetch(`/threats/timeline?hours=${hours}`)
};

export const blockchainAPI = { getThreatHistory: async (limit = 50) => secureFetch(`/blockchain/history?limit=${limit}`) };

export const osintAPI = { investigateIP: async (ip: string) => secureFetch('/osint/investigate/ip', { method: 'POST', body: JSON.stringify({ ip }) }) };

export default { authAPI, threatAPI, osintAPI, dashboardAPI, blockchainAPI };
